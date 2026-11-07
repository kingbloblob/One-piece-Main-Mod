package com.onepiecemod.endgame;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.Difficulty;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.npc.NpcFeature;
import com.onepiecemod.stats.StatTraining;
import com.onepiecemod.worldevent.WorldNews;

/**
 * Runs the endgame raids (see RaidDef for the list). A raid happens around the spot where it was started:
 * everyone within 32 blocks joins, the waves come in one after another, and anyone who runs more than 64 blocks away
 * leaves the raid. Win the last wave and everyone still in the raid gets the treasure.
 *
 * Raids aren't saved: if the server stops mid-raid, the raid's enemies are removed the next time they load.
 */
public class Raids {
	/** Every enemy a raid spawns carries this tag. */
	public static final String TAG = "onepiece_endgame_raid";
	private static final int JOIN_RADIUS = 32;
	private static final int LEAVE_RADIUS = 64;
	/** Enemies that wander further than this from the raid's centre are pulled back. */
	private static final int LEASH = 40;
	private static final int COUNTDOWN_TICKS = 20 * 10;
	private static final int BETWEEN_WAVES_TICKS = 20 * 8;
	/** Everyone gone (dead and not back, or ran off) this long ends the raid. */
	private static final int EMPTY_TICKS = 20 * 45;
	/** 30 minutes (was 25: the Rocks and Roger raids could not be finished solo in time). */
	private static final int TIME_LIMIT_TICKS = 20 * 60 * 30;
	private static final Identifier RAID_DAMAGE = OnePieceMod.id("raid_damage");
	private static final Identifier RAID_HEALTH = OnePieceMod.id("raid_health");

	private static final List<Active> ACTIVE = new ArrayList<>();

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			Iterator<Active> it = ACTIVE.iterator();
			while (it.hasNext()) {
				Active raid = it.next();
				if (!raid.tick(server)) {
					raid.cleanUp();
					it.remove();
				}
			}
		});
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			for (Active raid : ACTIVE) {
				raid.cleanUp();
			}
			ACTIVE.clear();
		});
		// Raid enemies left over from a raid that is no longer running (the server stopped mid-raid).
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity.entityTags().contains(TAG) && ACTIVE.stream().noneMatch(raid -> raid.members.contains(entity.getUUID()))) {
				entity.discard();
			}
		});
		// An enemy that is gone for good (killed or removed) is beaten. One that only unloaded with its chunk
		// (everyone ran off or respawned far away) still counts: it is waiting there when the raiders come back.
		ServerEntityEvents.ENTITY_UNLOAD.register((entity, level) -> {
			if (!entity.entityTags().contains(TAG)) {
				return;
			}
			for (Active raid : ACTIVE) {
				if (raid.members.contains(entity.getUUID())) {
					// Killed, discarded or gone to another world. An unloading chunk first hides its entities (no reason yet),
					// then removes them as UNLOADED_TO_CHUNK: both mean the enemy is still out there.
					Entity.RemovalReason reason = entity.getRemovalReason();
					if (reason != null && reason != Entity.RemovalReason.UNLOADED_TO_CHUNK) {
						raid.gone.add(entity.getUUID());
					} else if (entity instanceof LivingEntity living) {
						raid.lastHealth.put(entity.getUUID(), living.getHealth());
					}
				}
			}
		});
	}

	/** The raid this player is in, or null. */
	public static Active raidOf(ServerPlayer player) {
		for (Active raid : ACTIVE) {
			if (raid.players.contains(player.getUUID())) {
				return raid;
			}
		}
		return null;
	}

	/** Starts a raid around the player. Returns a reason it can't start, or null if it started. */
	public static String start(ServerPlayer player, RaidDef def) {
		if (raidOf(player) != null) {
			return "You are already in a raid.";
		}
		ServerLevel level = (ServerLevel) player.level();
		for (Active raid : ACTIVE) {
			if (raid.level == level && raid.center.distSqr(player.blockPosition()) < 128 * 128) {
				return "Another raid is already being fought nearby.";
			}
		}
		if (level.getDifficulty() == Difficulty.PEACEFUL) {
			return "Raids can't be fought on Peaceful. Turn the difficulty up first.";
		}
		if (player.isInWater() || player.isPassenger()) {
			return "Stand on dry land first. Raids are fought on islands.";
		}
		Active raid = new Active(def, player);
		ACTIVE.add(raid);
		raid.announce();
		return null;
	}

	/** Ends every raid this player is in, with no rewards. */
	public static boolean stop(ServerPlayer player) {
		Active raid = raidOf(player);
		if (raid == null) {
			return false;
		}
		raid.cleanUp();
		ACTIVE.remove(raid);
		return true;
	}

	/** One raid being fought. */
	public static class Active {
		final RaidDef def;
		final ServerLevel level;
		final BlockPos center;
		final Set<UUID> players = new HashSet<>();
		final List<UUID> members = new ArrayList<>();
		/** Members that died or were removed: beaten for good. */
		final Set<UUID> gone = new HashSet<>();
		/** Health of members whose chunk unloaded, so the wave isn't counted as beaten while nobody is there. */
		final Map<UUID, Float> lastHealth = new HashMap<>();
		final ServerBossEvent bar;
		/** The highest New Game+ cycle among the raiders when it started. */
		final int cycle;
		int wave = 0; // Waves done so far; the one being fought is wave + 1 while countdown is 0.
		int countdown = COUNTDOWN_TICKS;
		int emptyTicks = 0;
		int age = 0;
		float waveHealth = 1;

		Active(RaidDef def, ServerPlayer starter) {
			this.def = def;
			this.level = (ServerLevel) starter.level();
			this.center = starter.blockPosition();
			int highest = 0;
			for (ServerPlayer player : level.players()) {
				if (!player.isSpectator() && player.distanceToSqr(Vec3.atCenterOf(center)) < JOIN_RADIUS * JOIN_RADIUS) {
					players.add(player.getUUID());
					highest = Math.max(highest, EndgameData.of(player).cycle());
				}
			}
			players.add(starter.getUUID());
			this.cycle = Math.max(highest, EndgameData.of(starter).cycle());
			this.bar = new ServerBossEvent(UUID.randomUUID(), Component.literal("Raid: " + def.name()),
					BossEvent.BossBarColor.RED, BossEvent.BossBarOverlay.NOTCHED_10);
			this.bar.setProgress(0);
		}

		void announce() {
			Component text = Component.literal("RAID: " + def.name() + " (" + def.crew() + ")! " + def.waves().size()
					+ " waves arrive in 10 seconds. Stay within " + LEAVE_RADIUS + " blocks.").withStyle(def.color(), ChatFormatting.BOLD);
			for (ServerPlayer player : raiders()) {
				player.sendSystemMessage(text);
			}
			if (players.size() > 1) {
				tell(Component.literal(players.size() + " raiders: the enemies are tougher and more numerous.").withStyle(ChatFormatting.GRAY));
			}
			if (cycle > 0) {
				tell(Component.literal("New Game+ " + cycle + ": the enemies are stronger.").withStyle(ChatFormatting.DARK_RED));
			}
			level.playSound(null, center, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 6.0f, 0.9f);
			bar.setName(Component.literal("Raid: " + def.name() + " is coming"));
		}

		/** Returns false when the raid is over (won, lost or abandoned). */
		boolean tick(MinecraftServer server) {
			age++;
			if (age % 10 == 0) {
				updatePlayers(server);
			}
			List<ServerPlayer> here = raiders();
			if (here.isEmpty()) {
				emptyTicks++;
				if (emptyTicks >= EMPTY_TICKS) {
					lose(server, "Every raider fell or fled. The raid is lost.");
					return false;
				}
			} else {
				emptyTicks = 0;
			}
			if (level.getDifficulty() == Difficulty.PEACEFUL) {
				lose(server, "The raid was called off: raids can't be fought on Peaceful.");
				return false;
			}
			if (age >= TIME_LIMIT_TICKS) {
				lose(server, "The enemy held out too long. The raid is lost.");
				return false;
			}

			if (countdown > 0) {
				countdown--;
				if (countdown == 0) {
					spawnWave(wave);
				}
				return true;
			}

			if (age % 20 == 0) {
				herd(here);
			}
			float health = 0;
			for (UUID id : members) {
				if (gone.contains(id)) {
					continue;
				}
				Entity entity = level.getEntity(id);
				if (entity instanceof LivingEntity living) {
					if (living.isAlive()) {
						health += living.getHealth();
					}
				} else {
					health += lastHealth.getOrDefault(id, 1.0f); // Unloaded, not beaten.
				}
			}
			bar.setProgress(Mth.clamp(health / waveHealth, 0, 1));
			if (health <= 0) {
				members.clear();
				gone.clear();
				lastHealth.clear();
				wave++;
				if (wave >= def.waves().size()) {
					win(server);
					return false;
				}
				bar.setName(Component.literal("Raid: " + def.name() + " - wave " + (wave + 1) + " is coming"));
				bar.setProgress(0);
				tell(Component.literal("Wave " + wave + " beaten! Next: " + def.waves().get(wave).title() + ".").withStyle(def.color()));
				countdown = BETWEEN_WAVES_TICKS;
			}
			return true;
		}

		/** Raiders still in the fight: alive, in the same world, close enough. */
		List<ServerPlayer> raiders() {
			List<ServerPlayer> list = new ArrayList<>();
			for (UUID id : players) {
				ServerPlayer player = level.getServer().getPlayerList().getPlayer(id);
				if (player != null && player.level() == level && player.isAlive()
						&& player.distanceToSqr(Vec3.atCenterOf(center)) < LEAVE_RADIUS * LEAVE_RADIUS) {
					list.add(player);
				}
			}
			return list;
		}

		private void updatePlayers(MinecraftServer server) {
			// Friends who walk up to the raid join it.
			for (ServerPlayer player : level.players()) {
				if (!player.isSpectator() && !players.contains(player.getUUID()) && raidOf(player) == null
						&& player.distanceToSqr(Vec3.atCenterOf(center)) < JOIN_RADIUS * JOIN_RADIUS) {
					players.add(player.getUUID());
					player.sendSystemMessage(Component.literal("You joined the raid on the " + def.name() + "!").withStyle(def.color()));
				}
			}
			List<ServerPlayer> here = raiders();
			for (ServerPlayer player : List.copyOf(bar.getPlayers())) {
				if (!here.contains(player)) {
					bar.removePlayer(player);
				}
			}
			for (ServerPlayer player : here) {
				bar.addPlayer(player);
			}
		}

		private void spawnWave(int index) {
			RaidDef.Wave w = def.waves().get(index);
			int raiders = Math.max(1, raiders().size());
			waveHealth = 0;
			for (String spawn : w.spawns()) {
				if (spawn.startsWith("boss:")) {
					String[] parts = spawn.substring(5).split("@");
					int difficulty = parts.length < 2 ? CharacterEntity.NORMAL
							: parts[1].equals("expert") ? CharacterEntity.EXPERT
							: parts[1].equals("hard") ? CharacterEntity.HARD : CharacterEntity.NORMAL;
					spawnBoss(parts[0], difficulty, raiders);
				} else {
					String[] parts = spawn.split("\\*");
					int count = parts.length < 2 ? 1 : Integer.parseInt(parts[1]);
					count = Math.round(count * (1 + 0.5f * (raiders - 1)));
					for (int i = 0; i < count; i++) {
						spawnNpc(parts[0], raiders);
					}
				}
			}
			waveHealth = Math.max(1, waveHealth);
			String name = "Raid: " + def.name() + " - wave " + (index + 1) + " of " + def.waves().size() + ": " + w.title();
			bar.setName(Component.literal(name));
			bar.setColor(index == def.waves().size() - 1 ? BossEvent.BossBarColor.PURPLE : BossEvent.BossBarColor.RED);
			bar.setProgress(1);
			level.playSound(null, center, SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 6.0f, 1.1f);
			tell(Component.literal("Here they come: " + w.title() + "!").withStyle(def.color(), ChatFormatting.BOLD));
			if (members.isEmpty()) {
				waveHealth = 1; // Nothing could spawn (no kits?): the wave counts as beaten.
			}
		}

		private CharacterEntity spawnBoss(String id, int difficulty, int raiders) {
			if (CharacterData.get(id) == null) {
				OnePieceMod.LOGGER.warn("Raid {}: no character {}", def.id(), id);
				return null;
			}
			BlockPos spot = spot(8, 14);
			CharacterEntity boss = CharacterFeature.CHARACTER.create(level, EntitySpawnReason.EVENT);
			if (boss == null) {
				return null;
			}
			boss.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
			boss.setCharacter(id, true);
			boss.setDifficulty(difficulty);
			// Friendly characters (Shanks, Roger, Rayleigh, Garp, Marco) are only 400-health quest givers in characters.json:
			// raids give them the health and damage of the legends they are.
			RaidDef.BossStats stats = RaidDef.bossStats(id);
			float scale = stats == null ? 1 : stats.health() * (float) com.onepiecemod.config.ModConfig.bossHealth() / boss.effectiveMaxHealth();
			if (stats != null) {
				boss.getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(stats.damage() * com.onepiecemod.config.ModConfig.bossDamage());
			}
			boss.setHealthScale(scale * (float) (1 + NewGamePlus.raidHealthBonus(cycle)));
			buff(boss, raiders, true);
			boss.addTag(NewGamePlus.CHECKED_TAG); // Raids apply New Game+ themselves.
			level.addFreshEntity(boss);
			boss.addTag(TAG);
			members.add(boss.getUUID());
			waveHealth += boss.getMaxHealth();
			return boss;
		}

		private void spawnNpc(String kit, int raiders) {
			BlockPos spot = spot(10, 18);
			HumanNpc npc = NpcFeature.spawn(level, kit, spot, level.getRandom().nextFloat() * 360);
			if (npc == null) {
				return;
			}
			npc.addTag(TAG);
			npc.setPersistenceRequired();
			buff(npc, raiders, false);
			members.add(npc.getUUID());
			waveHealth += npc.getMaxHealth();
		}

		/** More raiders and higher New Game+ cycles make the enemies hit harder and shrug off more damage. */
		private void buff(Mob mob, int raiders, boolean boss) {
			double damageBonus = 0.15 * (raiders - 1) + NewGamePlus.damageBonus(cycle);
			AttributeInstance damage = mob.getAttribute(Attributes.ATTACK_DAMAGE);
			if (damage != null && damageBonus > 0) {
				damage.addOrReplacePermanentModifier(new AttributeModifier(RAID_DAMAGE, damageBonus, AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
			}
			// Bosses get their New Game+ health in spawnBoss (most are past the 1024 health cap, where a modifier does nothing).
			double healthBonus = boss ? 0 : 0.25 * (raiders - 1) + NewGamePlus.raidHealthBonus(cycle);
			AttributeInstance health = mob.getAttribute(Attributes.MAX_HEALTH);
			if (health != null && healthBonus > 0) {
				health.addOrReplacePermanentModifier(new AttributeModifier(RAID_HEALTH, healthBonus, AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
				mob.setHealth(mob.getMaxHealth());
			}
			if (boss) {
				// Bosses are near the 1024 health cap already, so extra raiders mean Resistance instead (each level = 20% less damage).
				// New Game+ adds health and damage to raids but no Resistance: stacked on top, NG+5 raids ran 30-40 minutes solo.
				int resistance = Math.min(3, def.resistance() + (raiders - 1));
				if (resistance > 0) {
					mob.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, MobEffectInstance.INFINITE_DURATION, resistance - 1, false, false));
				}
			}
		}

		/** Keeps enemies near the raid and fighting the raiders. */
		private void herd(List<ServerPlayer> here) {
			for (UUID id : members) {
				if (!(level.getEntity(id) instanceof Mob mob) || !mob.isAlive()) {
					continue;
				}
				if (mob.distanceToSqr(Vec3.atCenterOf(center)) > LEASH * LEASH) {
					BlockPos spot = spot(6, 12);
					mob.teleportTo(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
					level.sendParticles(ParticleTypes.CLOUD, mob.getX(), mob.getY() + 1, mob.getZ(), 20, 0.5, 0.8, 0.5, 0.02);
				}
				LivingEntity target = mob.getTarget();
				if ((target == null || !target.isAlive() || !(target instanceof ServerPlayer)) && !here.isEmpty()) {
					ServerPlayer nearest = null;
					for (ServerPlayer player : here) {
						if (!player.isCreative() && (nearest == null || player.distanceToSqr(mob) < nearest.distanceToSqr(mob))) {
							nearest = player;
						}
					}
					if (nearest != null) {
						mob.setTarget(nearest);
					}
				}
			}
		}

		/** A dry spot on the ground some distance from the centre (the centre itself if none is found). */
		private BlockPos spot(int min, int max) {
			for (int tries = 0; tries < 16; tries++) {
				double angle = level.getRandom().nextDouble() * Math.PI * 2;
				double distance = min + level.getRandom().nextDouble() * (max - min);
				int x = center.getX() + (int) Math.round(Math.cos(angle) * distance);
				int z = center.getZ() + (int) Math.round(Math.sin(angle) * distance);
				int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
				BlockPos pos = new BlockPos(x, y, z);
				if (Math.abs(y - center.getY()) <= 12 && level.getFluidState(pos.below()).isEmpty() && level.getFluidState(pos).isEmpty()) {
					return pos;
				}
			}
			return center.above();
		}

		private void win(MinecraftServer server) {
			List<ServerPlayer> winners = raiders();
			// Raiders who fell in the last moments of the fight still share the treasure.
			for (UUID id : players) {
				ServerPlayer player = server.getPlayerList().getPlayer(id);
				if (player != null && player.level() == level && player.isDeadOrDying() && !winners.contains(player)) {
					winners.add(player);
				}
			}
			tell(Component.literal("VICTORY! You beat " + theName(def) + "!").withStyle(def.color(), ChatFormatting.BOLD));
			level.playSound(null, center, SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 2.0f, 1.0f);
			Finale.fireworks(level, center, 6, def.trophyColor());
			long now = server.overworld().getGameTime();
			for (ServerPlayer player : winners) {
				reward(server, player, now);
			}
		}

		private void reward(MinecraftServer server, ServerPlayer player, long now) {
			EndgameData data = EndgameData.of(player);
			List<String> openBefore = openRaids(player);
			boolean first = !data.cleared().contains(def.id());
			boolean full = now >= data.timer("raid:" + def.id());
			double ngShare = 1 + 0.5 * cycle;
			if (full) {
				give(player, new ItemStack(CharacterFeature.BERRY), (int) Math.round(def.berries() * ngShare));
				for (String entry : def.loot()) {
					String[] parts = entry.split("\\*");
					give(player, CharacterData.stack(parts[0], 1), parts.length < 2 ? 1 : Integer.parseInt(parts[1]));
				}
				StatTraining.addXp(player, def.statXp(), true);
				data = data.withTimer("raid:" + def.id(), now + RaidDef.FULL_LOOT_EVERY);
				player.sendSystemMessage(Component.literal("Raid treasure: " + Math.round(def.berries() * ngShare) + " Berries and the "
						+ def.crew() + " hoard. Full treasure again in 7 days.").withStyle(ChatFormatting.GOLD));
			} else {
				int berries = (int) Math.round(def.berries() * 0.15 * ngShare);
				give(player, new ItemStack(CharacterFeature.BERRY), berries);
				long days = Math.max(1, (data.timer("raid:" + def.id()) - now + 23999) / 24000);
				player.sendSystemMessage(Component.literal("You already took this crew's treasure this week: " + berries
						+ " Berries. Full treasure in " + days + (days == 1 ? " day." : " days.")).withStyle(ChatFormatting.GRAY));
			}
			if (first) {
				give(player, EndgameFeature.trophy(def.id()), 1);
				data = data.withCleared(def.id());
				player.sendSystemMessage(Component.literal("First victory! You earned " + def.trophyName() + ".").withStyle(ChatFormatting.LIGHT_PURPLE));
				WorldNews.report(server, def.id().equals("final_war")
						? player.getName().getString() + " won the Final War against the World Government!"
						: player.getName().getString() + " has crushed " + theName(def) + " at " + def.crew() + "!", def.color());
			}
			EndgameData.set(player, data);
			for (RaidDef other : RaidDef.all().values()) {
				if (!openBefore.contains(other.id()) && other.unlocked().test(player)) {
					player.sendSystemMessage(Component.literal("New raid unlocked: " + other.name() + "! Tune your Raid Den Den Mushi to it.")
							.withStyle(other.color(), ChatFormatting.BOLD));
				}
			}
		}

		private void lose(MinecraftServer server, String why) {
			tell(Component.literal(why).withStyle(ChatFormatting.RED));
			tell(Component.literal("You can try again: tune your Raid Den Den Mushi to " + def.name()
					+ " (right-click), then sneak + right-click to start it.").withStyle(ChatFormatting.GRAY));
		}

		void tell(Component text) {
			for (UUID id : players) {
				ServerPlayer player = level.getServer().getPlayerList().getPlayer(id);
				if (player != null) {
					player.sendSystemMessage(text);
				}
			}
		}

		void cleanUp() {
			bar.removeAllPlayers();
			for (UUID id : members) {
				Entity entity = level.getEntity(id);
				if (entity != null) {
					entity.discard();
				}
			}
			members.clear();
		}
	}

	/** "the Beasts Pirates", but "The Final War" stays as it is. */
	static String theName(RaidDef def) {
		return def.name().startsWith("The ") ? def.name() : "the " + def.name();
	}

	/** Ids of the raids this player can start. */
	static List<String> openRaids(ServerPlayer player) {
		List<String> list = new ArrayList<>();
		for (RaidDef def : RaidDef.all().values()) {
			if (def.unlocked().test(player)) {
				list.add(def.id());
			}
		}
		return list;
	}

	/** Gives any amount of an item, in full stacks; what doesn't fit is dropped at the player's feet. */
	static void give(ServerPlayer player, ItemStack kind, int count) {
		if (kind.isEmpty()) {
			return;
		}
		while (count > 0) {
			int amount = Math.min(count, kind.getMaxStackSize());
			ItemStack stack = kind.copyWithCount(amount);
			if (!player.getInventory().add(stack)) {
				player.drop(stack, false, net.minecraft.util.Prediction.SERVER_ONLY);
			}
			count -= amount;
		}
	}
}
