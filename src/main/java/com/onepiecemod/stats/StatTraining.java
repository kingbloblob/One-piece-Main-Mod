package com.onepiecemod.stats;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.TextColor;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;

import com.onepiecemod.character.CharacterEntity;

/**
 * How players earn training XP for their Pirate Level, and how they spend stat points.
 *
 * - Fights: beating hostile mobs (tougher mobs give more), other pirates, and above all story bosses.
 * - Training: taking a hit and staying on your feet, and sprinting or swimming long distances.
 *
 * Peaceful animals give nothing, so farming cows won't make you stronger.
 */
public class StatTraining {
	/** XP for a story boss, times its tier (1 to 5). Hard and Expert rematches give 50% and 100% more. */
	private static final int BOSS_XP_PER_TIER = 100;
	/** Biggest XP a normal mob can give, so a Wither doesn't hand out ten levels. */
	private static final int MAX_MOB_XP = 100;
	private static final int PLAYER_KILL_XP = 25;
	/** Taking a hit gives 1 XP, at most once every 2 seconds. */
	private static final int HIT_COOLDOWN_TICKS = 40;
	/** Blocks you need to sprint or swim for 2 XP. */
	private static final double TRAINING_RUN_BLOCKS = 100;
	private static final int TRAINING_RUN_XP = 2;
	/** Moving further than this in one second is a teleport or a ship, not running. */
	private static final double MAX_RUN_PER_SECOND = 12;

	/** Not saved: these only matter for a few seconds at a time. */
	private static final Map<UUID, Integer> NEXT_HIT_XP_TICK = new HashMap<>();
	private static final Map<UUID, Vec3> LAST_POSITION = new HashMap<>();
	private static final Map<UUID, Double> DISTANCE_RUN = new HashMap<>();

	public static void initialize() {
		// Fights: beating something that was a threat.
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (source.getEntity() instanceof ServerPlayer player && entity != player) {
				int xp = killXp(player, entity);
				if (xp > 0) {
					addXp(player, xp, true);
				}
			}
		});

		// Training: take a hit and keep standing.
		ServerLivingEntityEvents.AFTER_DAMAGE.register((entity, source, baseDamageTaken, damageTaken, blocked) -> {
			if (!(entity instanceof ServerPlayer player) || blocked || damageTaken <= 0 || !player.isAlive()) {
				return;
			}
			Entity attacker = source.getEntity();
			if (!(attacker instanceof LivingEntity) || attacker == player) {
				return;
			}
			int now = player.level().getServer().getTickCount();
			if (now >= NEXT_HIT_XP_TICK.getOrDefault(player.getUUID(), 0)) {
				NEXT_HIT_XP_TICK.put(player.getUUID(), now + HIT_COOLDOWN_TICKS);
				addXp(player, 1, false);
			}
		});

		// Training: sprint and swim. Checked once a second.
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 20 != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				trackRunning(player);
			}
		});

		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
			UUID id = handler.player.getUUID();
			NEXT_HIT_XP_TICK.remove(id);
			LAST_POSITION.remove(id);
			DISTANCE_RUN.remove(id);
		});
	}

	private static int killXp(ServerPlayer player, LivingEntity entity) {
		if (entity instanceof CharacterEntity character && character.isBoss()) {
			int xp = BOSS_XP_PER_TIER * Math.max(1, character.getData().tier);
			xp += xp * character.getDifficulty() / 2;
			// A rematch at a difficulty you've already won (Wanted Posters) pays a quarter, so posters aren't an XP farm.
			return character.isFirstWin() ? xp : xp / 4;
		}
		if (entity instanceof ServerPlayer) {
			return PLAYER_KILL_XP;
		}
		boolean threat = entity instanceof Enemy || (entity instanceof Mob mob && mob.getTarget() == player);
		if (!threat) {
			return 0;
		}
		return Math.max(2, Math.min(MAX_MOB_XP, Math.round(entity.getMaxHealth() / 2)));
	}

	private static void trackRunning(ServerPlayer player) {
		UUID id = player.getUUID();
		Vec3 now = player.position();
		Vec3 before = LAST_POSITION.put(id, now);
		if (before == null || player.isPassenger() || player.getAbilities().flying || player.isSpectator()
				|| !(player.isSprinting() || player.isSwimming())) {
			return;
		}
		double moved = Math.hypot(now.x - before.x, now.z - before.z);
		if (moved > MAX_RUN_PER_SECOND) {
			return;
		}
		double total = DISTANCE_RUN.getOrDefault(id, 0.0) + moved;
		if (total >= TRAINING_RUN_BLOCKS) {
			total -= TRAINING_RUN_BLOCKS;
			addXp(player, TRAINING_RUN_XP, false);
		}
		DISTANCE_RUN.put(id, total);
	}

	/**
	 * Gives a player training XP, and tells them when they level up.
	 * Other features can call this too, e.g. StatTraining.addXp(player, 50, true) as a quest reward.
	 *
	 * @param announce show "+N Pirate XP" above the hotbar
	 */
	public static void addXp(ServerPlayer player, int amount, boolean announce) {
		amount = com.onepiecemod.config.ModConfig.scale(amount, com.onepiecemod.config.ModConfig.pirateXp());
		StatsData before = StatsAttachments.get(player);
		int oldLevel = before.level();
		StatsData after = before.withXp((int) Math.min(Integer.MAX_VALUE, (long) before.xp() + amount));
		StatsAttachments.set(player, after);
		int newLevel = after.level();

		if (newLevel > oldLevel) {
			player.sendSystemMessage(Component.literal("Pirate Level " + newLevel + "! ")
					.withStyle(style -> style.withColor(TextColor.fromRgb(0xFFD75E)).withBold(true))
					.append(Component.literal("You have " + after.freePoints() + " stat point"
							+ (after.freePoints() == 1 ? "" : "s") + " to spend. Press K to open your stat tree.")
							.withStyle(style -> style.withColor(ChatFormatting.YELLOW).withBold(false))));
			player.level().playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.8f, 0.8f);
		} else if (announce && amount > 0) {
			String progress = newLevel >= StatsData.MAX_LEVEL ? "max level"
					: after.xpIntoLevel() + "/" + StatsData.xpForNextLevel(newLevel);
			player.sendOverlayMessage(Component.literal("+" + amount + " Pirate XP (" + progress + ")")
					.withStyle(ChatFormatting.GOLD));
		}
		StatsPayloads.sync(player);
	}

	/** Spends one point on a stat, if the player has a point and the stat isn't maxed. */
	public static boolean spend(ServerPlayer player, PlayerStat stat) {
		StatsData data = StatsAttachments.get(player);
		if (!data.canRaise(stat)) {
			player.sendSystemMessage(Component.literal(data.rank(stat) >= PlayerStat.MAX_RANK
					? stat.displayName + " is already maxed out."
					: "You have no stat points. Level up by fighting and training!").withStyle(ChatFormatting.RED));
			return false;
		}
		int rank = data.rank(stat) + 1;
		StatsAttachments.set(player, data.withRank(stat, rank));
		StatBonuses.apply(player);

		String milestone = rank == PlayerStat.FIRST_MILESTONE ? stat.firstMilestone
				: rank == PlayerStat.SECOND_MILESTONE ? stat.secondMilestone : null;
		if (milestone != null) {
			player.sendSystemMessage(Component.literal("Unlocked " + milestone)
					.withStyle(style -> style.withColor(TextColor.fromRgb(stat.color))));
			player.level().playSound(null, player.blockPosition(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 0.6f, 1.0f);
		} else {
			player.level().playSound(null, player.blockPosition(), SoundEvents.EXPERIENCE_ORB_PICKUP, SoundSource.PLAYERS, 0.6f, 1.2f);
		}
		StatsPayloads.sync(player);
		return true;
	}
}
