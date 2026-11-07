package com.onepiecemod.shipcombat;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;

import com.mojang.serialization.Codec;

import org.jetbrains.annotations.Nullable;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.Container;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipInteractions;
import com.onepiecemod.ship.ShipLayout;
import com.onepiecemod.ship.ShipPayloads;

/**
 * A ship's hull points. Every ship starts with more the bigger it is.
 *  - Cannonballs and explosions take hull points away and knock blocks off the ship.
 *  - At zero the ship sinks: everyone falls into the sea. Enemy ships spill their chests; a player's ship settles on
 *    the sea floor as a wreck with its chests still full (ShipWreck).
 *  - Patch the hull while sailing by right-clicking your ship holding planks (or iron ingots).
 *  - Docking and setting sail again gives a fresh, full hull (but knocked-off blocks stay gone until you rebuild them).
 */
public class ShipHull {
	// ---- Numbers to tune ----
	public static final float CANNONBALL_DAMAGE = 24f;
	private static final float PLANK_REPAIR = 6f;
	private static final float IRON_REPAIR = 20f;
	private static final int SINK_TICKS = 100; // 5 seconds from broken hull to gone

	/** Hull points left, saved on the ship. Missing means "full". */
	public static final AttachmentType<Float> HULL = AttachmentRegistry.create(
			OnePieceMod.id("ship_hull"), builder -> builder.persistent(Codec.FLOAT));
	/** The most hull points this ship can have. Worked out from its size the first time it is needed. */
	public static final AttachmentType<Float> MAX_HULL = AttachmentRegistry.create(
			OnePieceMod.id("ship_max_hull"), builder -> builder.persistent(Codec.FLOAT));

	private static final Map<ShipEntity, Integer> SINKING = new WeakHashMap<>();
	/** Chain shot in the rigging until this game time (ShipCrewHelp slows the ship). */
	private static final Map<ShipEntity, Long> CHAINED = new WeakHashMap<>();
	/** On fire (fire shot) until this game time. */
	private static final Map<ShipEntity, Long> BURNING = new WeakHashMap<>();
	private static final float BURN_PER_SECOND = 3f;

	/** Loading this class registers the attachments above. */
	static void initialize() {
	}

	public static float max(ShipEntity ship) {
		Float max = ship.getAttached(MAX_HULL);
		if (max == null) {
			max = sizeToHull(ship.getLayout().size()) * com.onepiecemod.ship.ShipUpgrades.hullBonus(com.onepiecemod.ship.ShipUpgrades.hull(ship.getLayout()));
			ship.setAttached(MAX_HULL, max);
		}
		return max;
	}

	/** A 100-block ship has 160 hull points (about 7 cannonball hits); a huge one tops out at 700. */
	public static float sizeToHull(int blocks) {
		return Mth.clamp(40f + blocks * 1.2f, 60f, 700f);
	}

	public static float get(ShipEntity ship) {
		Float hull = ship.getAttached(HULL);
		return hull == null ? max(ship) : hull;
	}

	public static void setMax(ShipEntity ship, float max) {
		ship.setAttached(MAX_HULL, max);
		ship.setAttached(HULL, max);
	}

	/** Called by ShipEntity.hurtServer: explosions (TNT, creepers, Devil Fruit blasts) hurt the hull. Punches don't. */
	public static boolean hurt(ShipEntity ship, ServerLevel level, DamageSource source, float amount) {
		if (ship.sinking || ship.isRemoved() || source.getDirectEntity() instanceof CannonballEntity) {
			return false; // A cannonball's own blast is already counted in its hit.
		}
		if (!source.is(DamageTypeTags.IS_EXPLOSION)) {
			return false;
		}
		ServerPlayer attacker = source.getEntity() instanceof ServerPlayer player ? player : null;
		damage(ship, amount * 0.6f, attacker, source.getSourcePosition() != null ? source.getSourcePosition() : ship.position(), null);
		return true;
	}

	/**
	 * Takes hull points off a ship and knocks a block or two off near where it was hit.
	 * attacker is the player who fired (for rewards), fromShip the ship the shot came from (or null).
	 */
	public static void damage(ShipEntity ship, float amount, @Nullable ServerPlayer attacker, Vec3 hitPos, @Nullable ShipEntity fromShip) {
		if (ship.sinking || ship.isRemoved() || !(ship.level() instanceof ServerLevel level)) {
			return;
		}
		if (fromShip != null && ShipBrain.sameSide(fromShip, ship)) {
			return; // Marines don't sink Marines.
		}
		if (!com.onepiecemod.multiplayer.SeaWars.allowHullDamage(ship, attacker, fromShip)) {
			return; // Another crew's ship: only in a sea battle (or with open-sea PvP on). Your own crew's and allies' never.
		}
		amount *= com.onepiecemod.ship.ShipUpgrades.damageTaken(com.onepiecemod.ship.ShipUpgrades.hull(ship.getLayout()));
		float hull = get(ship) - amount;
		ship.setAttached(HULL, hull);
		ShipCombat.noteHit(ship, attacker, fromShip);

		knockOffBlocks(ship, level, hitPos, amount >= 20 ? 2 : 1);
		level.playSound(null, BlockPos.containing(hitPos), com.onepiecemod.sound.WorldSounds.SHIP_HULL_HIT, SoundSource.NEUTRAL, 2.5f, 0.9f + level.getRandom().nextFloat() * 0.2f);

		if (hull <= 0) {
			startSinking(ship, level, attacker);
		}
	}

	/** Holding planks or iron ingots and right-clicking your own ship patches the hull. Returns true if it did. */
	public static boolean tryRepair(ShipEntity ship, ServerPlayer player, ItemStack stack) {
		float amount = stack.is(net.minecraft.tags.ItemTags.PLANKS) ? PLANK_REPAIR
				: stack.is(net.minecraft.world.item.Items.IRON_INGOT) ? IRON_REPAIR : 0;
		float max = max(ship);
		float hull = get(ship);
		if (amount <= 0 || hull >= max || ship.sinking) {
			return false;
		}
		hull = Math.min(max, hull + amount);
		ship.setAttached(HULL, hull);
		if (!player.isCreative()) {
			stack.shrink(1);
		}
		ship.level().playSound(null, player.blockPosition(), com.onepiecemod.sound.WorldSounds.SHIP_REPAIR, SoundSource.PLAYERS, 1.0f, 1.0f);
		player.sendOverlayMessage(Component.literal("Hull patched: " + Math.round(hull) + " / " + Math.round(max)).withStyle(ChatFormatting.GREEN));
		return true;
	}

	/** Patches the hull a little (a Shipwright aboard). Returns true if anything needed patching. */
	public static boolean mend(ShipEntity ship, float amount) {
		float max = max(ship);
		float hull = get(ship);
		if (ship.sinking || hull >= max) {
			return false;
		}
		ship.setAttached(HULL, Math.min(max, hull + amount));
		return true;
	}

	// ---- Chain shot and fire shot ----

	/** Tangles a ship's rigging for a while, like chain shot. Add-on shells can call it too (see CannonAddons). */
	public static void chain(ShipEntity ship, int ticks) {
		CHAINED.merge(ship, ship.level().getGameTime() + ticks, Math::max);
	}

	static boolean chained(ShipEntity ship) {
		return ship.level().getGameTime() < CHAINED.getOrDefault(ship, 0L);
	}

	/** Sets a ship burning for a while, like fire shot. Add-on shells can call it too (see CannonAddons). */
	public static void ignite(ShipEntity ship, int ticks) {
		BURNING.merge(ship, ship.level().getGameTime() + ticks, Math::max);
	}

	public static boolean burning(ShipEntity ship) {
		return ship.level().getGameTime() < BURNING.getOrDefault(ship, 0L);
	}

	/** Once a second while a ship burns: flames on deck, the hull chars, and the crew catches fire. Rain puts it out. */
	static void tickBurning(ShipEntity ship, ServerLevel level) {
		if (!burning(ship) || ship.sinking) {
			return;
		}
		if (level.isRainingAt(ship.blockPosition().above(ship.getLayout().max.getY() + 1))) {
			BURNING.remove(ship);
			return;
		}
		ShipLayout layout = ship.getLayout();
		var random = level.getRandom();
		for (int i = 0; i < 5 && layout.size() > 0; i++) {
			BlockPos p = layout.blocks.get(random.nextInt(layout.size())).pos();
			Vec3 at = ship.position().add(ship.rotate(new Vec3(p.getX(), p.getY() + 1, p.getZ()), 1.0f));
			level.sendParticles(ParticleTypes.FLAME, at.x, at.y, at.z, 6, 0.3, 0.3, 0.3, 0.02);
			level.sendParticles(ParticleTypes.LARGE_SMOKE, at.x, at.y + 0.5, at.z, 2, 0.2, 0.2, 0.2, 0.02);
		}
		for (var passenger : ship.getPassengers()) {
			if (random.nextInt(3) == 0) {
				passenger.igniteForSeconds(3);
			}
		}
		float hull = get(ship) - BURN_PER_SECOND;
		ship.setAttached(HULL, hull);
		if (hull <= 0) {
			startSinking(ship, level, ShipCombat.lastAttacker(ship, level));
		}
	}

	// ---- Knocking blocks off ----

	private static void knockOffBlocks(ShipEntity ship, ServerLevel level, Vec3 hitPos, int count) {
		ShipLayout layout = ship.getLayout();
		if (layout.size() < 12) {
			return;
		}
		// Turn the hit point into the ship's own unturned coordinates (the opposite of ShipEntity.rotate).
		float radians = -ship.rotationSinceBuilt(1.0f) * Mth.DEG_TO_RAD;
		float cos = Mth.cos(radians), sin = Mth.sin(radians);
		Vec3 rel = hitPos.subtract(ship.position());
		Vec3 local = new Vec3(rel.x * cos - rel.z * sin, rel.y, rel.x * sin + rel.z * cos);

		// The closest blocks to the hit, but never the wheel or anything holding items.
		List<ShipLayout.ShipBlock> candidates = new ArrayList<>();
		for (ShipLayout.ShipBlock block : layout.blocks) {
			if (!block.pos().equals(layout.helm) && block.nbt().isEmpty()
					&& Vec3.atCenterOf(block.pos()).subtract(0.5, 0, 0.5).distanceToSqr(local) < 9.0) {
				candidates.add(block);
			}
		}
		if (candidates.isEmpty()) {
			return;
		}
		candidates.sort(Comparator.comparingDouble(block -> Vec3.atCenterOf(block.pos()).subtract(0.5, 0, 0.5).distanceToSqr(local)));
		List<ShipLayout.ShipBlock> removed = candidates.subList(0, Math.min(count, candidates.size()));
		Set<BlockPos> gone = new java.util.HashSet<>();
		for (ShipLayout.ShipBlock block : removed) {
			gone.add(block.pos());
			Vec3 at = ship.position().add(ship.rotate(new Vec3(block.pos().getX(), block.pos().getY() + 0.5, block.pos().getZ()), 1.0f));
			level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, block.state()), at.x, at.y, at.z, 24, 0.4, 0.4, 0.4, 0.1);
		}

		// Block positions in the list shift, so close any chest screens first (ShipStorage remembers chests by position in the list).
		ShipInteractions.closeAll(ship, level);
		List<ShipLayout.ShipBlock> blocks = new ArrayList<>(layout.blocks);
		blocks.removeIf(block -> gone.contains(block.pos()));
		List<ShipLayout.FlagEntry> flags = layout.flags.stream().filter(flag -> !gone.contains(flag.pos())).toList();
		ship.setLayout(new ShipLayout(blocks, flags, layout.helm, layout.bow, layout.waterline));
		resendBlocks(ship);
	}

	/** Tells every player who can see the ship what it looks like now. */
	static void resendBlocks(ShipEntity ship) {
		ShipPayloads.ShipBlocks payload = new ShipPayloads.ShipBlocks(ship.getId(), ship.getLayout());
		for (ServerPlayer player : PlayerLookup.tracking(ship)) {
			ServerPlayNetworking.send(player, payload);
		}
	}

	// ---- Sinking ----

	static void startSinking(ShipEntity ship, ServerLevel level, @Nullable ServerPlayer attacker) {
		if (ship.sinking) {
			return;
		}
		ship.sinking = true;
		ship.aiForward = 0;
		ship.aiTurn = 0;
		ship.setAttached(HULL, 0f);
		SINKING.put(ship, 0);

		ShipInteractions.closeAll(ship, level);
		ship.ejectPassengers();
		if (ShipBrain.factionOf(ship) != null) {
			spillChests(ship, level); // A player's ship keeps its chests: they go down with the wreck (ShipWreck).
		}
		ShipCombat.rewardSinking(ship, level, attacker);

		Vec3 pos = ship.position();
		level.playSound(null, ship.blockPosition(), com.onepiecemod.sound.WorldSounds.SHIP_SINK, SoundSource.NEUTRAL, 4.0f, 1.0f);
		level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, pos.x, pos.y + 2, pos.z, 1, 0, 0, 0, 0);
		OnePieceMod.LOGGER.info("Ship '{}' sank at {}", ship.getName().getString(), ship.blockPosition().toShortString());
		Component news = Component.literal(ship.getName().getString() + " is sinking!").withStyle(ChatFormatting.DARK_AQUA);
		for (ServerPlayer player : level.players()) {
			if (player.distanceToSqr(ship) < 96 * 96) {
				player.sendSystemMessage(news);
			}
		}
	}

	/** Called every tick for a sinking ship: bubbles, creaking, and gone once it is under. */
	static void tickSinking(ShipEntity ship, ServerLevel level) {
		int ticks = SINKING.merge(ship, 1, Integer::sum);
		Vec3 pos = ship.position();
		float width = ship.getBbWidth() / 2;
		level.sendParticles(ParticleTypes.BUBBLE_COLUMN_UP, pos.x, pos.y + ship.getLayout().waterline, pos.z, 12, width, 0.5, width, 0.1);
		level.sendParticles(ParticleTypes.SPLASH, pos.x, pos.y + ship.getLayout().waterline + 0.5, pos.z, 16, width, 0.2, width, 0.1);
		if (ticks % 40 == 20) {
			level.playSound(null, ship.blockPosition(), com.onepiecemod.sound.WorldSounds.SHIP_BREAK, SoundSource.NEUTRAL, 2.0f, 0.8f + level.getRandom().nextFloat() * 0.3f);
		}
		if (ticks >= SINK_TICKS || ship.onGround()) {
			SINKING.remove(ship);
			if (ShipBrain.factionOf(ship) == null) {
				ShipWreck.settle(level, ship);
			}
			ship.discard();
		}
	}

	/** A ship marked as sunk (for example one that was sinking when the server stopped) goes down again. */
	static void resumeIfBroken(ShipEntity ship) {
		Float hull = ship.getAttached(HULL);
		if (hull != null && hull <= 0 && !ship.sinking) {
			ship.sinking = true;
			SINKING.put(ship, 0);
		}
	}

	/** Every chest, barrel and so on aboard throws its items into the sea, where they float up. */
	private static void spillChests(ShipEntity ship, ServerLevel level) {
		for (ShipLayout.ShipBlock block : ship.getLayout().blocks) {
			if (block.nbt().isEmpty()) {
				continue;
			}
			BlockEntity saved = BlockEntity.loadStatic(BlockPos.ZERO, block.state(), block.nbt().get(), level.registryAccess());
			if (!(saved instanceof Container container)) {
				continue;
			}
			Vec3 at = ship.position().add(ship.rotate(new Vec3(block.pos().getX(), block.pos().getY() + 1, block.pos().getZ()), 1.0f));
			for (int slot = 0; slot < container.getContainerSize(); slot++) {
				ItemStack stack = container.getItem(slot);
				if (!stack.isEmpty()) {
					drop(level, at, stack.copy());
				}
			}
		}
	}

	static void drop(ServerLevel level, Vec3 at, ItemStack stack) {
		ItemEntity item = new ItemEntity(level, at.x, at.y, at.z, stack);
		item.setDeltaMovement(level.getRandom().nextGaussian() * 0.1, 0.25, level.getRandom().nextGaussian() * 0.1);
		level.addFreshEntity(item);
	}
}
