package com.onepiecemod.story;

import java.util.List;
import java.util.Locale;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.haki.HakiAttachments;
import com.onepiecemod.haki.HakiData;
import com.onepiecemod.power.Awakening;
import com.onepiecemod.race.RaceAttachments;
import com.onepiecemod.sea.CalmBelt;
import com.onepiecemod.sea.LogPoseTracker;
import com.onepiecemod.style.StyleAttachments;

/**
 * Checks whether a player has done one story goal. The goal types are listed in StoryData.Goal.
 * Every check reads what the other parts of the mod already save, so the story never has to be told twice.
 */
public class StoryGoals {
	public static boolean isDone(ServerPlayer player, StoryProgress progress, StoryData.Goal goal) {
		return switch (goal.type) {
			case "race" -> RaceAttachments.get(player) != null;
			case "reach" -> StoryPlaces.isInside((ServerLevel) player.level(), player.blockPosition(), goal.place);
			// A summoned character has to be talked to during this chapter (you may know Sanji from the Baratie already).
			case "talk" -> goal.summon ? progress.hasFlag(StoryRaids.metFlag(StoryData.chapter(progress.chapter()), goal.character))
					: CharacterAttachments.has(player, CharacterAttachments.MET, goal.character);
			case "quest" -> CharacterAttachments.has(player, CharacterAttachments.QUESTS_DONE, goal.character + ":" + (goal.step - 1));
			case "boss" -> bossDone(player, goal);
			case "crew" -> hasCrew(player, goal.role);
			case "item" -> player.getInventory().countItem(CharacterData.item(goal.item)) >= goal.count;
			case "sail" -> progress.counterThisChapter(goal.ship ? "sail_ship" : "sail") >= goal.count;
			case "bounty" -> com.onepiecemod.career.Careers.renown(player) >= goal.amount; // Marines count Merit.
			case "islands" -> LogPoseTracker.journey(player).visited().size() >= goal.count;
			case "sea" -> isInSea(player, goal.sea);
			case "haki" -> hakiLevel(player, goal.kind) >= goal.level;
			case "styles" -> knownStyles(player) >= goal.count;
			case "mastery" -> Awakening.getMastery(player) >= goal.amount;
			case "kills" -> progress.counter("kills:" + goal.place) >= goal.count;
			case "event" -> progress.hasFlag("event:" + goal.event);
			case "any" -> goal.of.stream().anyMatch(option -> isDone(player, progress, option));
			case "treasure" -> com.onepiecemod.treasure.TreasureFeature.treasuresFound(player) >= goal.count;
			case "fish" -> fishKinds(player) >= goal.count;
			case "colosseum" -> com.onepiecemod.arena.ArenaFeature.record(player).corridaBest() >= goal.level;
			case "davyback" -> davyBackFights(player) >= goal.count;
			case "history" -> com.onepiecemod.endgame.VoidCentury.pagesRead(player) >= goal.count;
			case "page" -> com.onepiecemod.endgame.VoidCentury.read(player).contains(goal.page);
			default -> false;
		};
	}

	/** "3/16" style progress for goals that count something, or null. */
	public static String progressText(ServerPlayer player, StoryProgress progress, StoryData.Goal goal) {
		return switch (goal.type) {
			case "item" -> Math.min(goal.count, player.getInventory().countItem(CharacterData.item(goal.item))) + "/" + goal.count;
			case "sail" -> Math.min(goal.count, progress.counterThisChapter(goal.ship ? "sail_ship" : "sail")) + "/" + goal.count + " blocks";
			case "islands" -> Math.min(goal.count, LogPoseTracker.journey(player).visited().size()) + "/" + goal.count;
			case "haki" -> Math.min(goal.level, hakiLevel(player, goal.kind)) + "/" + goal.level;
			case "styles" -> Math.min(goal.count, knownStyles(player)) + "/" + goal.count;
			case "mastery" -> Math.min(goal.amount, Awakening.getMastery(player)) + "/" + goal.amount;
			case "kills" -> Math.min(goal.count, progress.counter("kills:" + goal.place)) + "/" + goal.count;
			case "bounty" -> Bounty.format(Math.min(goal.amount, com.onepiecemod.career.Careers.renown(player))) + " / " + Bounty.format(goal.amount);
			case "treasure" -> Math.min(goal.count, com.onepiecemod.treasure.TreasureFeature.treasuresFound(player)) + "/" + goal.count;
			case "fish" -> Math.min(goal.count, fishKinds(player)) + "/" + goal.count + " kinds";
			case "davyback" -> Math.min(goal.count, davyBackFights(player)) + "/" + goal.count;
			case "history" -> Math.min(goal.count, com.onepiecemod.endgame.VoidCentury.pagesRead(player)) + "/" + goal.count + " pages";
			default -> null;
		};
	}

	/** In New Game+ it must be a win this cycle. A Hard or Expert goal needs that win (outside New Game+, which only counts bosses). */
	private static boolean bossDone(ServerPlayer player, StoryData.Goal goal) {
		if (goal.difficulty > 0 && com.onepiecemod.endgame.EndgameData.of(player).cycle() <= 0) {
			return CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED,
					goal.boss + (goal.difficulty >= 2 ? ":expert" : ":hard"));
		}
		return com.onepiecemod.endgame.NewGamePlus.bossGoalDone(player, goal.boss);
	}

	private static int fishKinds(ServerPlayer player) {
		return player.getAttachedOrElse(com.onepiecemod.cuisine.Fishing.CAUGHT, java.util.List.<String>of()).size();
	}

	/** Davy Back Fights played, won or lost. */
	private static int davyBackFights(ServerPlayer player) {
		com.onepiecemod.arena.ArenaRecord record = com.onepiecemod.arena.ArenaFeature.record(player);
		return record.dbfWins() + record.dbfLosses();
	}

	private static boolean hasCrew(ServerPlayer player, String roleId) {
		Crew crew = player.getAttached(CrewAttachments.CREW);
		if (crew == null) {
			return false;
		}
		if (roleId == null) {
			return true; // Just having a crew is enough.
		}
		CrewRole role = CrewRole.byId(roleId);
		return role != null && crew.member(role) != null;
	}

	private static boolean isInSea(ServerPlayer player, String sea) {
		CalmBelt.Sea here = CalmBelt.seaAt(player.level(), player.blockPosition());
		return here != null && here.name().equals(sea.toUpperCase(Locale.ROOT));
	}

	private static int hakiLevel(ServerPlayer player, String kind) {
		HakiData haki = HakiAttachments.get(player);
		return "observation".equals(kind) ? haki.observationLevel() : haki.armamentLevel();
	}

	private static int knownStyles(ServerPlayer player) {
		List<String> styles = player.getAttached(StyleAttachments.KNOWN_STYLES);
		return styles == null ? 0 : styles.size();
	}
}
