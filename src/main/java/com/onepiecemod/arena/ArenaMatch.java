package com.onepiecemod.arena;

import com.onepiecemod.util.Motion;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.npc.NpcFeature;

/**
 * One running arena event for one player: a Corrida tournament or a Davy Back Fight.
 * ArenaFeature ticks it every server tick until tick() returns false, then calls cleanup().
 *
 * Matches live only in memory. Their fighters carry the tag onepiece_arena plus this server run's tag,
 * so any fighter left over after a restart is cleared away when it loads (see ArenaFeature).
 */
public abstract class ArenaMatch {
	public static final String TAG = "onepiece_arena";

	protected final UUID playerId;
	protected final ServerLevel level;
	protected final BlockPos center;
	protected final ServerBossEvent bar;
	protected final List<Entity> spawned = new ArrayList<>();
	protected int ticks = 0;
	private int awayTicks = 0;

	protected ArenaMatch(ServerPlayer player, BlockPos center, String title, BossEvent.BossBarColor color) {
		this.playerId = player.getUUID();
		this.level = (ServerLevel) player.level();
		this.center = center;
		this.bar = new ServerBossEvent(UUID.randomUUID(), Component.literal(title), color, BossEvent.BossBarOverlay.PROGRESS);
		this.bar.addPlayer(player);
	}

	/** Runs one tick. Returns false when the match is over. */
	protected abstract boolean tick(ServerPlayer player);

	/** The player ran out of health inside the arena. Called instead of dying. */
	protected abstract void playerDown(ServerPlayer player);

	/** The player logged out, left or gave up. */
	protected abstract void forfeit(ServerPlayer player, String why);

	/** Can the player's crewmates hurt this arena fighter? */
	protected boolean crewMayFight(Entity fighter) {
		return false;
	}

	/** How far the player may walk from the centre before the match counts as abandoned. */
	protected int leashRadius() {
		return 64;
	}

	public String name() {
		return bar.getName().getString();
	}

	/** Called by ArenaFeature. Returns false when the match should end. */
	final boolean run(MinecraftServer server) {
		ServerPlayer player = server.getPlayerList().getPlayer(playerId);
		if (player == null || player.level() != level) {
			if (player != null) {
				forfeit(player, "You left the arena.");
			}
			return false;
		}
		if (!player.isAlive()) {
			return false;
		}
		if (player.position().distanceTo(Vec3.atBottomCenterOf(center)) > leashRadius()) {
			if (++awayTicks > 100) {
				forfeit(player, "You wandered too far from the arena.");
				return false;
			}
			if (awayTicks == 1) {
				player.sendSystemMessage(Component.literal("Go back to the arena, or you forfeit!"), true);
			}
		} else {
			awayTicks = 0;
		}
		ticks++;
		if (ticks % 20 == 0) {
			calmOutsiders(player);
		}
		return tick(player);
	}

	/** Monsters that aren't part of the match leave the player alone while it runs. */
	private void calmOutsiders(ServerPlayer player) {
		for (Mob mob : level.getEntitiesOfClass(Mob.class, player.getBoundingBox().inflate(40),
				mob -> mob.getTarget() == player && !spawned.contains(mob))) {
			mob.setTarget(null);
		}
		// Residents (a boss who lives in the arena, a wandering guard) are nudged off the fighting floor.
		double clear = clearRadius();
		if (clear > 0) {
			for (Mob mob : level.getEntitiesOfClass(Mob.class, new net.minecraft.world.phys.AABB(center).inflate(clear, 6, clear),
					mob -> !spawned.contains(mob) && !(mob instanceof com.onepiecemod.crew.CrewmateEntity))) {
				double dx = mob.getX() - (center.getX() + 0.5);
				double dz = mob.getZ() - (center.getZ() + 0.5);
				double length = Math.max(0.1, Math.sqrt(dx * dx + dz * dz));
				if (length < clear) {
					mob.getNavigation().stop();
					mob.setDeltaMovement(dx / length * 0.9, 0.35, dz / length * 0.9);
					Motion.sync(mob);
				}
			}
		}
	}

	/** Outsiders inside this radius get nudged out every second (0 = leave them be). */
	protected double clearRadius() {
		return 0;
	}

	void cleanup() {
		bar.removeAllPlayers();
		for (Entity entity : spawned) {
			if (entity.isAlive()) {
				poof(entity);
				entity.discard();
			}
		}
		spawned.clear();
	}

	boolean owns(Entity entity) {
		return spawned.contains(entity);
	}

	// ---------- Helpers for subclasses ----------

	/** A free spot on solid ground near `angle` degrees around the centre, `radius` blocks out. */
	protected BlockPos spot(double angle, double radius) {
		int x = center.getX() + Mth.floor(Math.sin(Math.toRadians(angle)) * radius);
		int z = center.getZ() + Mth.floor(Math.cos(Math.toRadians(angle)) * radius);
		for (int dy = 4; dy >= -6; dy--) {
			BlockPos feet = new BlockPos(x, center.getY() + dy, z);
			if (level.getBlockState(feet.below()).isSolidRender() && level.getFluidState(feet).isEmpty()
					&& level.getBlockState(feet).getCollisionShape(level, feet).isEmpty()
					&& level.getBlockState(feet.above()).getCollisionShape(level, feet.above()).isEmpty()) {
				return feet;
			}
		}
		return radius > 2 ? spot(angle, radius * 0.6) : center;
	}

	/**
	 * How far the flat, dry floor reaches from the centre (checked in 16 directions), minus a block,
	 * between 6 and `max`. Keeps the ring on the arena sand instead of over a moat or into the stands.
	 */
	protected double floorRadius(double max) {
		double radius = max;
		for (int i = 0; i < 16; i++) {
			double angle = Math.PI * 2 * i / 16;
			for (int r = 2; r <= max + 1; r++) {
				BlockPos feet = BlockPos.containing(center.getX() + 0.5 + Math.sin(angle) * r, center.getY(), center.getZ() + 0.5 + Math.cos(angle) * r);
				boolean floor = level.getBlockState(feet.below()).isSolidRender() && level.getFluidState(feet).isEmpty()
						&& level.getBlockState(feet).getCollisionShape(level, feet).isEmpty()
						&& level.getBlockState(feet.above()).getCollisionShape(level, feet.above()).isEmpty();
				if (!floor) {
					radius = Math.min(radius, r - 1.5);
					break;
				}
			}
		}
		return Math.max(6, radius);
	}

	/** The top of the ground or water at x, z, for markers. */
	protected BlockPos surface(int x, int z) {
		return new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING, x, z), z);
	}

	/** Spawns a pirate NPC for the arena from an NPC kit. hp/damage are multipliers, or absolute when name != null. */
	protected HumanNpc fighter(String kit, BlockPos pos, String name, double health, double damage) {
		float yaw = (float) Math.toDegrees(Math.atan2(center.getX() - pos.getX(), pos.getZ() - center.getZ()));
		HumanNpc npc = NpcFeature.spawn(level, kit, pos, yaw);
		if (npc == null) {
			return null;
		}
		if (name != null) {
			setBase(npc, Attributes.MAX_HEALTH, health);
			setBase(npc, Attributes.ATTACK_DAMAGE, damage);
			npc.setCustomName(Component.literal(name).withStyle(ChatFormatting.GOLD));
		} else {
			setBase(npc, Attributes.MAX_HEALTH, npc.getAttributeBaseValue(Attributes.MAX_HEALTH) * health);
			setBase(npc, Attributes.ATTACK_DAMAGE, npc.getAttributeBaseValue(Attributes.ATTACK_DAMAGE) * damage);
		}
		npc.setHealth(npc.getMaxHealth());
		npc.setCustomNameVisible(true);
		mark(npc);
		return npc;
	}

	/** Tags an entity as ours, so it is cleared when the match ends or after a restart. */
	protected void mark(Mob mob) {
		mob.addTag(TAG);
		mob.addTag(ArenaFeature.runTag());
		mob.setPersistenceRequired();
		spawned.add(mob);
	}

	protected static void setBase(LivingEntity entity, net.minecraft.core.Holder<net.minecraft.world.entity.ai.attributes.Attribute> attribute,
			double value) {
		AttributeInstance instance = entity.getAttribute(attribute);
		if (instance != null) {
			instance.setBaseValue(value);
		}
	}

	/** Keeps an arena fighter inside the ring: anyone too far out is pulled back near the middle. */
	protected void keepInside(Mob mob, double radius) {
		if (mob.isAlive() && mob.position().distanceTo(Vec3.atBottomCenterOf(center)) > radius) {
			BlockPos back = spot(mob.getRandom().nextFloat() * 360, radius * 0.4);
			mob.teleportTo(back.getX() + 0.5, back.getY(), back.getZ() + 0.5);
			level.sendParticles(ParticleTypes.CLOUD, mob.getX(), mob.getY() + 1, mob.getZ(), 10, 0.3, 0.5, 0.3, 0.02);
		}
	}

	/** Draws the edge of the ring with particles, a few points each call. */
	protected void drawRing(double radius, ParticleOptions particle) {
		int points = (int) (radius * 2);
		for (int i = 0; i < points; i += 2) {
			double angle = (i + (ticks / 5) % 2) * Math.PI * 2 / points;
			double x = center.getX() + 0.5 + Math.sin(angle) * radius;
			double z = center.getZ() + 0.5 + Math.cos(angle) * radius;
			level.sendParticles(particle, x, center.getY() + 0.2, z, 1, 0.05, 0.05, 0.05, 0.0);
		}
	}

	private int outTicks = 0;

	/**
	 * Ring-out check for the player. Being knocked over the edge is fine for a moment:
	 * only staying outside for 2 seconds counts. Returns true when the player is out.
	 */
	protected boolean ringOut(ServerPlayer player, double radius) {
		if (distance(player) <= radius) {
			outTicks = 0;
			return false;
		}
		outTicks++;
		if (outTicks % 20 == 1) {
			player.sendSystemMessage(Component.literal("Get back in the ring! " + (2 - outTicks / 20) + "...").withStyle(ChatFormatting.RED), true);
		}
		return outTicks > 40;
	}

	protected double distance(Entity entity) {
		double dx = entity.getX() - (center.getX() + 0.5);
		double dz = entity.getZ() - (center.getZ() + 0.5);
		return Math.sqrt(dx * dx + dz * dz);
	}

	protected static void poof(Entity entity) {
		if (entity.level() instanceof ServerLevel serverLevel) {
			serverLevel.sendParticles(ParticleTypes.POOF, entity.getX(), entity.getY() + 1, entity.getZ(), 12, 0.3, 0.5, 0.3, 0.02);
		}
	}

	protected static void title(ServerPlayer player, String title, String subtitle) {
		player.connection.send(new ClientboundSetTitlesAnimationPacket(5, 40, 10));
		player.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal(subtitle).withStyle(ChatFormatting.YELLOW)));
		player.connection.send(new ClientboundSetTitleTextPacket(Component.literal(title).withStyle(ChatFormatting.GOLD)));
	}

	protected static void say(ServerPlayer player, String speaker, String line) {
		player.sendSystemMessage(Component.literal("[" + speaker + "] ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(line).withStyle(ChatFormatting.YELLOW)));
	}

	protected void sound(SoundEvent sound, float volume, float pitch) {
		level.playSound(null, center, sound, SoundSource.PLAYERS, volume, pitch);
	}

	protected static void giveBerries(ServerPlayer player, int amount) {
		while (amount > 0) {
			int count = Math.min(amount, 64);
			net.minecraft.world.item.ItemStack stack = new net.minecraft.world.item.ItemStack(CharacterFeature.BERRY, count);
			if (!player.getInventory().add(stack)) {
				player.drop(stack, false, net.minecraft.util.Prediction.SERVER_ONLY);
			}
			amount -= count;
		}
	}

	/** Puts the player back on their feet after a knock-out: a little health, no fire, a moment of rest. */
	protected static void revive(ServerPlayer player) {
		player.setHealth(Math.max(player.getHealth(), 6.0f));
		player.clearFire();
		player.removeAllEffects();
		player.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.REGENERATION, 100, 1));
		player.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.RESISTANCE, 100, 4));
	}
}
