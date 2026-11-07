package com.onepiecemod.story;

import com.onepiecemod.sound.ModSounds;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Prediction;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.vehicle.boat.AbstractBoat;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;

import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.character.Locations;
import com.onepiecemod.character.SeaChartItem;
import com.onepiecemod.ship.ShipEntity;

/**
 * Moves each player through the story:
 * - The first time you join you get a Captain's Log and chapter 1 starts.
 * - Once a second it checks the goals of your chapter. When they're all done you get the reward and the next chapter starts.
 * - It also counts the things goals can't look up elsewhere: blocks sailed and mobs beaten at a place.
 */
public class StoryTracker {
	private static final int CHECK_EVERY_TICKS = 20;
	/** Where each player was a second ago, to count how far they sailed. */
	private static final Map<UUID, Vec3> lastPos = new HashMap<>();

	public static void initialize() {
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
			ServerPlayer player = handler.player;
			if (StoryProgress.of(player) == null) {
				StoryProgress.set(player, StoryProgress.START);
				give(player, new ItemStack(StoryFeature.CAPTAINS_LOG));
				startChapter(player, 0);
			}
		});
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> lastPos.remove(handler.player.getUUID()));

		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % CHECK_EVERY_TICKS != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				if (StoryProgress.of(player) == null || player.isSpectator()) {
					continue;
				}
				countSailing(player);
				check(player);
			}
		});

		// Mobs beaten inside a place, for goals like "clear out Arlong Park".
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (!(entity instanceof Enemy) || !(source.getEntity() instanceof ServerPlayer player)
					|| !(entity.level() instanceof ServerLevel level)) {
				return;
			}
			StoryProgress progress = StoryProgress.of(player);
			StoryData.Chapter chapter = progress == null ? null : StoryData.chapter(progress.chapter());
			if (chapter == null) {
				return;
			}
			for (StoryData.Goal goal : chapter.goals) {
				if ("kills".equals(goal.type) && StoryPlaces.isInside(level, entity.blockPosition(), goal.place)) {
					StoryProgress.set(player, progress.addCounter("kills:" + goal.place, 1));
					return;
				}
			}
		});
	}

	private static void countSailing(ServerPlayer player) {
		Entity vehicle = player.getVehicle();
		// The captain rides the ship; the rest of the crew walk her deck. Count how far the ship went, so the whole
		// crew sails just as far and pacing an anchored deck counts for nothing.
		ShipEntity aboard = ShipEntity.aboard(player);
		boolean ship = aboard != null;
		Vec3 now = ship ? aboard.position() : player.position();
		Vec3 before = lastPos.put(player.getUUID(), now);
		if (before == null || !(ship || vehicle instanceof AbstractBoat)) {
			return;
		}
		double dx = now.x - before.x;
		double dz = now.z - before.z;
		int blocks = (int) Math.round(Math.sqrt(dx * dx + dz * dz));
		if (blocks <= 0 || blocks > 40) {
			return; // Standing still, or a teleport.
		}
		StoryProgress progress = StoryProgress.of(player).addCounter("sail", blocks);
		if (ship) {
			progress = progress.addCounter("sail_ship", blocks);
		}
		StoryProgress.set(player, progress);
	}

	/** Checks the current chapter's goals, and finishes the chapter once they're all done. */
	public static void check(ServerPlayer player) {
		StoryProgress progress = StoryProgress.of(player);
		StoryData.Chapter chapter = StoryData.chapter(progress.chapter());
		if (chapter == null) {
			return; // The story is over.
		}
		boolean allDone = true;
		for (int i = 0; i < chapter.goals.size(); i++) {
			if (progress.goalDone(i)) {
				continue;
			}
			StoryData.Goal goal = chapter.goals.get(i);
			if (StoryGoals.isDone(player, progress, goal)) {
				progress = progress.withGoal(i);
				StoryProgress.set(player, progress);
				player.sendSystemMessage(Component.literal("✔ " + goal.text).withStyle(ChatFormatting.GREEN));
				player.level().playSound(null, player.blockPosition(), ModSounds.STORY_GOAL, SoundSource.PLAYERS, 0.8f, 1.0f);
			} else {
				allDone = false;
			}
		}
		if (allDone) {
			finishChapter(player, chapter);
		}
	}

	private static void finishChapter(ServerPlayer player, StoryData.Chapter chapter) {
		if (!chapter.outro.isEmpty()) {
			player.sendSystemMessage(Component.literal(chapter.outro).withStyle(ChatFormatting.ITALIC, ChatFormatting.GRAY));
		}
		player.sendSystemMessage(Component.literal("Chapter complete: " + chapter.title).withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
		giveReward(player, chapter.reward);
		StoryEvents.onChapterFinished(player, chapter);
		com.onepiecemod.endgame.VoidCentury.chapterDone(player, chapter.id); // Wano and Egghead write a page of the true history.
		if (StoryProgress.LAUGH_TALE.equals(chapter.id)) {
			StoryEvents.onStoryFinished(player);
		}
		player.level().playSound(null, player.blockPosition(), ModSounds.STORY_CHAPTER, SoundSource.PLAYERS, 1.0f, 1.0f);

		int next = chapter.index + 1;
		boolean newSaga = StoryData.chapter(next) == null || StoryData.chapter(next).saga != chapter.saga;
		if (newSaga) {
			player.sendSystemMessage(Component.literal(chapter.saga.title + " is over!").withStyle(ChatFormatting.LIGHT_PURPLE));
		}
		startChapter(player, next);
	}

	/** Starts a chapter: saves it, tells the story and hands out its Sea Charts. Also used by /story set. */
	public static void startChapter(ServerPlayer player, int index) {
		StoryProgress.set(player, StoryProgress.orStart(player).atChapter(index));
		StoryData.Chapter chapter = StoryData.chapter(index);
		if (chapter == null) {
			StoryEvents.onStoryFinished(player); // Only does something the first time (e.g. after /story set).
			player.sendSystemMessage(Component.literal("You finished every chapter, the post-game too. Legendary!").withStyle(ChatFormatting.GOLD));
			return;
		}
		boolean newSaga = index == 0 || StoryData.chapter(index - 1).saga != chapter.saga;
		title(player, newSaga ? chapter.saga.title : "Chapter " + (index + 1), chapter.title);
		player.sendSystemMessage(Component.literal(""));
		player.sendSystemMessage(Component.literal("Chapter " + (index + 1) + ": " + chapter.title).withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
		if (!chapter.intro.isEmpty()) {
			player.sendSystemMessage(Component.literal(chapter.intro).withStyle(ChatFormatting.ITALIC, ChatFormatting.GRAY));
		}
		for (String place : chapter.charts) {
			give(player, SeaChartItem.forTarget(place));
		}
		if (!chapter.charts.isEmpty()) {
			player.sendSystemMessage(Component.literal("You got a Sea Chart. Right-click it to see where to sail.").withStyle(ChatFormatting.AQUA));
		}
		player.sendSystemMessage(Component.literal("Open your Captain's Log (or type /story) to see your goals.").withStyle(ChatFormatting.DARK_AQUA));
		com.onepiecemod.cutscene.CutsceneFeature.onChapterStart(player, chapter.id); // Its flashback, if it has one.
	}

	/** What the Captain's Log and /story show. */
	public static void showLog(ServerPlayer player) {
		StoryProgress progress = StoryProgress.orStart(player);
		StoryData.Chapter chapter = StoryData.chapter(progress.chapter());
		if (chapter == null) {
			player.sendSystemMessage(Component.literal("Captain's Log: every chapter is done, the post-game too!").withStyle(ChatFormatting.GOLD));
			player.sendSystemMessage(Component.literal("Still to beat: Mihawk, Whitebeard, the Admirals, Rocks D. Xebec at God Valley, and Hard and Expert rematches with any Wanted Poster.")
					.withStyle(ChatFormatting.GRAY));
			return;
		}
		int total = StoryData.chapters().size();
		player.sendSystemMessage(Component.literal("=== Captain's Log: " + chapter.saga.title + " ===").withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal("Chapter " + (chapter.index + 1) + " of " + total + ": " + chapter.title).withStyle(ChatFormatting.YELLOW));
		if (!chapter.intro.isEmpty()) {
			player.sendSystemMessage(Component.literal(chapter.intro).withStyle(ChatFormatting.ITALIC, ChatFormatting.GRAY));
		}
		for (int i = 0; i < chapter.goals.size(); i++) {
			StoryData.Goal goal = chapter.goals.get(i);
			boolean done = progress.goalDone(i);
			String count = done ? null : StoryGoals.progressText(player, progress, goal);
			player.sendSystemMessage(Component.literal((done ? " ✔ " : " • ") + goal.text + (count != null ? " (" + count + ")" : ""))
					.withStyle(done ? ChatFormatting.GREEN : ChatFormatting.WHITE));
		}
		String reward = rewardText(chapter.reward);
		if (!reward.isEmpty()) {
			player.sendSystemMessage(Component.literal("Reward: " + reward).withStyle(ChatFormatting.DARK_AQUA));
		}
		for (String place : chapter.charts) {
			player.sendSystemMessage(Component.literal("Lost your chart? Type /story chart for a new one to " + Locations.name(place) + ".")
					.withStyle(ChatFormatting.DARK_GRAY));
			break;
		}
	}

	private static String rewardText(StoryData.Reward reward) {
		StringBuilder text = new StringBuilder();
		if (reward.berries > 0) {
			text.append(reward.berries).append(" Berries");
		}
		if (reward.xp > 0) {
			if (!text.isEmpty()) {
				text.append(", ");
			}
			text.append(reward.xp).append(" Pirate XP");
		}
		for (StoryData.ItemReward item : reward.items) {
			ItemStack stack = CharacterData.stack(item.item, item.count);
			if (stack.isEmpty()) {
				continue;
			}
			if (!text.isEmpty()) {
				text.append(", ");
			}
			text.append(item.count > 1 ? item.count + " " : "").append(stack.getHoverName().getString());
		}
		return text.toString();
	}

	private static void giveReward(ServerPlayer player, StoryData.Reward reward) {
		give(player, CharacterFeature.BERRY, reward.berries);
		if (reward.xp > 0) {
			com.onepiecemod.stats.StatTraining.addXp(player, reward.xp, true);
		}
		for (StoryData.ItemReward item : reward.items) {
			give(player, CharacterData.item(item.item), item.count);
		}
	}

	private static void title(ServerPlayer player, String title, String subtitle) {
		player.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal(subtitle).withStyle(ChatFormatting.YELLOW)));
		player.connection.send(new ClientboundSetTitleTextPacket(Component.literal(title).withStyle(ChatFormatting.GOLD)));
	}

	/** Gives any amount of an item, split into full stacks. */
	static void give(ServerPlayer player, Item item, int count) {
		while (count > 0 && item != Items.AIR) {
			int amount = Math.min(count, item.getDefaultMaxStackSize());
			give(player, new ItemStack(item, amount));
			count -= amount;
		}
	}

	static void give(ServerPlayer player, ItemStack stack) {
		if (stack.isEmpty()) {
			return;
		}
		if (!player.getInventory().add(stack)) {
			player.drop(stack, false, Prediction.SERVER_ONLY); // Inventory full: drop it at their feet.
		}
	}

	/** The places the current chapter gives Sea Charts to, for /story chart. */
	static List<String> currentCharts(ServerPlayer player) {
		StoryData.Chapter chapter = StoryData.chapter(StoryProgress.orStart(player).chapter());
		return chapter == null ? List.of() : chapter.charts;
	}
}
