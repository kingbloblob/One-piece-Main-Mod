package com.onepiecemod.character;

import java.util.List;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/**
 * The Legend Ladder: rematches past Expert for the Four Emperors, Shanks and the Admirals.
 * Beat a titan on Expert and their Wanted Poster starts bringing them back at Legend I, then II... up to V.
 * Every rung has more health, harder hits, faster phase mechanics (and from Legend III the mechanics start
 * right away in phase 1), more Berries, and its own prizes the first time you clear it.
 * Progress is kept in the same BOSSES_DEFEATED list as everything else: "kaido:legend3".
 * /ladder shows your board and your title. Sneaking with the poster still gives a Normal fight.
 */
public class TitanLadder {
	public static final int MAX_RUNG = 5;
	/** Who is on the ladder, in the order the board lists them. */
	public static final List<String> BOSSES = List.of(
			"whitebeard", "big_mom", "kaido", "blackbeard", "shanks",
			"akainu", "kizaru", "aokiji", "fujitora", "ryokugyu", "saturn");
	private static final String[] ROMAN = {"", "I", "II", "III", "IV", "V"};
	/** First-clear prizes per rung, on top of the Expert prizes. "id*count". */
	private static final List<List<String>> REWARDS = List.of(
			List.of(),
			List.of("minecraft:diamond*4", "minecraft:experience_bottle*8"),
			List.of("minecraft:netherite_ingot", "minecraft:enchanted_golden_apple*2"),
			List.of("minecraft:nether_star", "minecraft:totem_of_undying", "minecraft:netherite_ingot"),
			List.of("minecraft:netherite_ingot*2", "minecraft:nether_star", "minecraft:enchanted_golden_apple*3"),
			List.of("minecraft:netherite_block", "minecraft:nether_star*2", "minecraft:totem_of_undying*2", "minecraft:heart_of_the_sea"));

	public static String rungName(int rung) {
		return "Legend " + ROMAN[Math.max(1, Math.min(MAX_RUNG, rung))];
	}

	public static String key(String bossId, int rung) {
		return bossId + ":legend" + rung;
	}

	public static boolean isLadderBoss(String bossId) {
		return BOSSES.contains(bossId);
	}

	/**
	 * Health per rung, on top of Expert. Balance pass 2026-11-01: was +40% per rung, which made Legend V a 10-13 minute
	 * health sponge for a maxed player. Now +15% (Legend V = 1.75x Expert, about 6-8 minutes); the danger comes from the
	 * harder hits and faster mechanics instead. Model: tools/balance/endgame_model.py.
	 */
	public static float healthFactor(int rung) {
		return 1.0f + 0.15f * rung;
	}

	public static float damageFactor(int rung) {
		return 1.0f + 0.15f * rung;
	}

	public static List<String> rewards(int rung) {
		return rung <= 0 ? List.of() : REWARDS.get(Math.min(MAX_RUNG, rung));
	}

	/** The highest rung this player has cleared against this boss (0 = none). */
	public static int bestRung(Player player, String bossId) {
		for (int rung = MAX_RUNG; rung >= 1; rung--) {
			if (CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, key(bossId, rung))) {
				return rung;
			}
		}
		return 0;
	}

	/** The rung their poster brings next: one above the best cleared (Legend V again once it's all done). */
	public static int nextRung(Player player, String bossId) {
		return Math.min(MAX_RUNG, bestRung(player, bossId) + 1);
	}

	/** Can this player climb the ladder against this boss? (Ladder boss, beaten on Expert.) */
	public static boolean unlocked(Player player, String bossId) {
		return isLadderBoss(bossId) && CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, bossId + ":expert");
	}

	/** All the rungs this player has cleared, out of BOSSES.size() * MAX_RUNG (55). */
	public static int score(Player player) {
		int total = 0;
		for (String boss : BOSSES) {
			total += bestRung(player, boss);
		}
		return total;
	}

	public static String title(int score) {
		if (score >= BOSSES.size() * MAX_RUNG) {
			return "Pirate King-class";
		}
		if (score >= 30) {
			return "Emperor-class";
		}
		if (score >= 15) {
			return "Warlord-class";
		}
		if (score >= 5) {
			return "Supernova";
		}
		return score > 0 ? "Challenger" : "Unranked";
	}

	/** Called for each player who shares a ladder win. newRung = first time clearing it. */
	static void onWin(ServerPlayer player, String bossId, int rung, boolean newRung) {
		if (!newRung) {
			player.sendSystemMessage(Component.literal(rungName(rung) + " again: just Berries this time.").withStyle(ChatFormatting.GRAY));
			return;
		}
		int score = score(player);
		String name = CharacterData.get(bossId).name;
		player.sendSystemMessage(Component.literal(rungName(rung) + " cleared! Ladder score " + score + "/" + BOSSES.size() * MAX_RUNG
				+ " (" + title(score) + ")").withStyle(ChatFormatting.LIGHT_PURPLE));
		if (rung < MAX_RUNG) {
			player.sendSystemMessage(Component.literal("Their Wanted Poster now brings " + rungName(rung + 1) + ".").withStyle(ChatFormatting.GRAY));
		} else {
			com.onepiecemod.news.NewsLog.report(player.level().getServer(), "LEGEND!",
					player.getName().getString() + " has beaten " + name + " at the top of the Legend Ladder!", true);
		}
		if (score == BOSSES.size() * MAX_RUNG) {
			com.onepiecemod.news.NewsLog.report(player.level().getServer(), "A NEW KING?!",
					player.getName().getString() + " has conquered every Emperor and Admiral at Legend V!", true);
		}
	}

	public static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(Commands.literal("ladder")
				.executes(context -> board(context.getSource().getPlayerOrException()))
				.then(Commands.literal("fight")
						.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
						.then(Commands.argument("boss", StringArgumentType.word())
								.suggests((context, builder) -> SharedSuggestionProvider.suggest(BOSSES, builder))
								.then(Commands.argument("rung", IntegerArgumentType.integer(0, MAX_RUNG))
										.executes(context -> fight(context.getSource().getPlayerOrException(),
												StringArgumentType.getString(context, "boss"), IntegerArgumentType.getInteger(context, "rung"))))))));
	}

	/** Your board: every titan, your best rung, and what's next. */
	private static int board(ServerPlayer player) {
		int score = score(player);
		player.sendSystemMessage(Component.literal("== Legend Ladder: " + score + "/" + BOSSES.size() * MAX_RUNG + " (" + title(score) + ") ==")
				.withStyle(ChatFormatting.LIGHT_PURPLE, ChatFormatting.BOLD));
		for (String boss : BOSSES) {
			String name = CharacterData.get(boss).name;
			int best = bestRung(player, boss);
			String status;
			ChatFormatting color;
			if (!unlocked(player, boss)) {
				status = "beat on Expert to unlock";
				color = ChatFormatting.DARK_GRAY;
			} else if (best >= MAX_RUNG) {
				status = "Legend V cleared!";
				color = ChatFormatting.GOLD;
			} else {
				status = (best == 0 ? "not started" : rungName(best) + " cleared") + ", next " + rungName(best + 1);
				color = ChatFormatting.WHITE;
			}
			String bar = "#".repeat(best) + "-".repeat(MAX_RUNG - best);
			player.sendSystemMessage(Component.literal("[" + bar + "] ").withStyle(ChatFormatting.LIGHT_PURPLE)
					.append(Component.literal(name + ": " + status).withStyle(color)));
		}
		return score;
	}

	/** Ops: spawns a ladder fight 4 blocks in front of you (rung 0 = plain Expert). */
	private static int fight(ServerPlayer player, String boss, int rung) {
		if (!isLadderBoss(boss)) {
			player.sendSystemMessage(Component.literal("Not on the ladder: " + boss).withStyle(ChatFormatting.RED));
			return 0;
		}
		ServerLevel level = (ServerLevel) player.level();
		CharacterEntity entity = CharacterFeature.CHARACTER.create(level, EntitySpawnReason.COMMAND);
		if (entity == null) {
			return 0;
		}
		Vec3 spot = player.position().add(player.getLookAngle().multiply(4, 0, 4));
		entity.setPos(spot.x, player.getY(), spot.z);
		entity.setCharacter(boss, true);
		entity.setLegendRung(rung);
		level.addFreshEntity(entity);
		return 1;
	}
}
