package com.onepiecemod.style;

import java.util.HashMap;
import java.util.Map;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;

/**
 * Style mastery: the more you fight with a style, the better you get at it.
 * Every technique you use gives 1 mastery point, or 2 if it hit an enemy. Each mastery level
 * makes that style's techniques 5% stronger and their cooldowns 4% shorter (up to +50% and -40% at level 10).
 * Slow on purpose: level 10 takes roughly 1,000 to 2,000 moves.
 */
public class StyleMastery {
	/** Points needed for levels 1 to 10. */
	private static final int[] LEVEL_POINTS = {25, 75, 150, 250, 400, 600, 850, 1150, 1500, 2000};
	public static final int MAX_LEVEL = LEVEL_POINTS.length;

	public static int points(Player player, FightingStyle style) {
		return player.getAttachedOrElse(StyleAttachments.MASTERY, Map.<String, Integer>of()).getOrDefault(style.id(), 0);
	}

	public static int level(Player player, FightingStyle style) {
		return levelFor(points(player, style));
	}

	private static int levelFor(int points) {
		int level = 0;
		while (level < MAX_LEVEL && points >= LEVEL_POINTS[level]) {
			level++;
		}
		return level;
	}

	/** Points still needed for the next level, or 0 at max level. */
	public static int pointsToNext(Player player, FightingStyle style) {
		int level = level(player, style);
		return level >= MAX_LEVEL ? 0 : LEVEL_POINTS[level] - points(player, style);
	}

	/** How much harder this style's techniques hit: x1.0 to x1.5. */
	public static float damageMultiplier(Player player, FightingStyle style) {
		return 1.0f + 0.05f * level(player, style);
	}

	/** A technique's cooldown for this player, after mastery. */
	public static int cooldownTicks(Player player, Technique technique) {
		float tempo = com.onepiecemod.progression.CombatPaths.has(player, technique.style(), 1, "b") ? 0.85f : 1.0f; // Path: Tempo.
		return Math.max(20, Math.round(technique.cooldownTicks() * (1.0f - 0.04f * level(player, technique.style())) * tempo
				* (float) com.onepiecemod.config.ModConfig.powerCooldowns()));
	}

	public static void add(ServerPlayer player, FightingStyle style, int amount) {
		Map<String, Integer> all = new HashMap<>(player.getAttachedOrElse(StyleAttachments.MASTERY, Map.<String, Integer>of()));
		int before = all.getOrDefault(style.id(), 0);
		int after = before + Math.max(0, com.onepiecemod.config.ModConfig.scale(amount, com.onepiecemod.config.ModConfig.hakiXp()));
		all.put(style.id(), after);
		player.setAttached(StyleAttachments.MASTERY, all);

		int oldLevel = levelFor(before);
		int newLevel = levelFor(after);
		if (newLevel > oldLevel) {
			String title = newLevel >= MAX_LEVEL ? style.title() + " mastered!" : style.title() + " mastery " + newLevel + "!";
			player.sendSystemMessage(Component.literal(title).withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
			player.sendSystemMessage(Component.literal("Techniques hit " + (5 * newLevel) + "% harder and recover "
					+ (4 * newLevel) + "% faster.").withStyle(ChatFormatting.YELLOW));
			player.level().playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.PLAYER_LEVELUP,
					SoundSource.PLAYERS, 0.8f, 1.0f);
		}
	}
}
