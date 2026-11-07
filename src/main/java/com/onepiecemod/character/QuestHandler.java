package com.onepiecemod.character;

import net.minecraft.util.Prediction;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/**
 * What happens when you right-click a quest giver. Each one has a quest line of a few steps.
 * - A new step: they explain it. A "defeat" step comes with the boss's Wanted Poster and a Sea Chart to their lair,
 *   and a "talk" step comes with the other character's Vivre Card, which points the way to them.
 *   "deliver" gives you a package and the receiver's Vivre Card, "explore" a Sea Chart to the place,
 *   and "escort" a Sea Chart plus a character who follows you there (see QuestJourneys).
 * - Talk again once you've done it: you get the reward and the next step starts right away.
 * - Not done yet: they remind you what to do.
 */
public class QuestHandler {
	public static void say(Player player, CharacterData character, String text) {
		player.sendSystemMessage(Component.literal("<" + character.name + "> ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(text).withStyle(ChatFormatting.WHITE)));
	}

	/** Called whenever a player talks to any friendly character, so "go talk to X" steps can finish. */
	public static void meet(Player player, CharacterData character) {
		CharacterAttachments.add(player, CharacterAttachments.MET, character.id);
		// "Deliver" steps: hand over the package if this is who it's for.
		for (CharacterData giver : CharacterData.all().values()) {
			int step = currentStep(player, giver);
			if (step >= giver.quests.size()) {
				continue;
			}
			CharacterData.Quest quest = giver.quests.get(step);
			if ("deliver".equals(quest.type) && character.id.equals(quest.target) && isStarted(player, giver, step)
					&& !isComplete(player, quest)) {
				Item item = CharacterData.item(quest.item);
				if (player.getInventory().countItem(item) >= quest.count) {
					takeItems(player, item, quest.count);
					markProgress(player, quest);
					say(player, character, "For me? From " + giver.name + "? Thank you! Tell them it arrived safely.");
				} else {
					say(player, character, "Didn't " + giver.name + " give you something for me? Come back when you have it.");
				}
			}
		}
	}

	/** Marks a deliver, explore or escort step as done (the player still has to go back to the giver). */
	public static void markProgress(Player player, CharacterData.Quest quest) {
		CharacterAttachments.add(player, CharacterAttachments.MET, quest.type + ":" + quest.key);
	}

	/** Which step of this character's quest line the player is on (0 = the first one). */
	public static int currentStep(Player player, CharacterData character) {
		int step = 0;
		while (step < character.quests.size() && CharacterAttachments.has(player, CharacterAttachments.QUESTS_DONE, key(character, step))) {
			step++;
		}
		return step;
	}

	public static void talk(Player player, CharacterData character) {
		if (character.quests.isEmpty()) {
			say(player, character, character.greeting);
			return;
		}

		int step = currentStep(player, character);
		if (step >= character.quests.size()) {
			say(player, character, character.thanks); // The whole quest line is done.
			return;
		}

		CharacterData.Quest quest = character.quests.get(step);
		if (!CharacterAttachments.has(player, CharacterAttachments.QUESTS_STARTED, key(character, step))) {
			if (step == 0) {
				say(player, character, character.greeting);
			}
			startStep(player, character, step);
			return;
		}

		if (isComplete(player, quest)) {
			say(player, character, quest.done);
			handIn(player, character, step);
			if (step + 1 < character.quests.size()) {
				startStep(player, character, step + 1);
			}
		} else {
			say(player, character, label(character, step) + quest.start); // Reminder of what to do.
		}
	}

	/**
	 * Takes the items a finished step asked for, pays the reward and marks the step done.
	 * The character's "done" line is up to the caller (chat here, the dialogue screen in dialogue/).
	 */
	public static void handIn(Player player, CharacterData character, int step) {
		CharacterData.Quest quest = character.quests.get(step);
		if ("fetch".equals(quest.type)) {
			takeItems(player, CharacterData.item(quest.item), quest.count);
		}
		give(player, CharacterFeature.BERRY, quest.berries);
		give(player, CharacterData.item(quest.rewardItem), quest.rewardCount);
		int xp = quest.xpReward();
		if (xp > 0 && player instanceof net.minecraft.server.level.ServerPlayer serverPlayer) {
			com.onepiecemod.stats.StatTraining.addXp(serverPlayer, xp, true);
		}
		CharacterAttachments.add(player, CharacterAttachments.QUESTS_DONE, key(character, step));
		if (step + 1 >= character.quests.size()) {
			player.sendSystemMessage(Component.literal("Quest line complete: " + character.name + "!").withStyle(ChatFormatting.GREEN));
			com.onepiecemod.sound.ModSounds.play(player, com.onepiecemod.sound.ModSounds.QUEST_COMPLETE);
		}
	}

	private static void startStep(Player player, CharacterData character, int step) {
		say(player, character, label(character, step) + character.quests.get(step).start);
		beginStep(player, character, step);
	}

	/** Starts a step without saying anything: hands over its poster, chart or Vivre Card. */
	public static void beginStep(Player player, CharacterData character, int step) {
		CharacterData.Quest quest = character.quests.get(step);
		if ("defeat".equals(quest.type)) {
			give(player, CharacterData.stack("onepiece:wanted_poster_" + quest.target, 1));
			// And a chart to the boss's lair, if they have one.
			String lair = Locations.home(quest.target);
			if (lair != null) {
				give(player, SeaChartItem.forTarget(lair));
			}
		} else if ("talk".equals(quest.type)) {
			// Only count talks that happen from now on.
			CharacterAttachments.remove(player, CharacterAttachments.MET, quest.target);
			// Their Vivre Card shows the way to them.
			give(player, CharacterData.stack("onepiece:vivre_card_" + quest.target, 1));
		} else if ("deliver".equals(quest.type)) {
			// The package, and the Vivre Card of the one it's for.
			CharacterAttachments.remove(player, CharacterAttachments.MET, quest.type + ":" + quest.key);
			give(player, CharacterData.item(quest.item), quest.count);
			give(player, CharacterData.stack("onepiece:vivre_card_" + quest.target, 1));
		} else if ("explore".equals(quest.type)) {
			CharacterAttachments.remove(player, CharacterAttachments.MET, quest.type + ":" + quest.key);
			give(player, SeaChartItem.forTarget(quest.target));
		} else if ("escort".equals(quest.type)) {
			CharacterAttachments.remove(player, CharacterAttachments.MET, quest.type + ":" + quest.key);
			if (quest.place != null) {
				give(player, SeaChartItem.forTarget(quest.place));
			}
			if (player instanceof net.minecraft.server.level.ServerPlayer serverPlayer) {
				QuestJourneys.startEscort(serverPlayer, quest);
			}
		}
		CharacterAttachments.add(player, CharacterAttachments.QUESTS_STARTED, key(character, step));
	}

	/** "[Quest 2/4] " in front of the step's text. */
	public static String label(CharacterData character, int step) {
		return "[Quest " + (step + 1) + "/" + character.quests.size() + "] ";
	}

	public static String key(CharacterData character, int step) {
		return character.id + ":" + step;
	}

	public static boolean isStarted(Player player, CharacterData character, int step) {
		return CharacterAttachments.has(player, CharacterAttachments.QUESTS_STARTED, key(character, step));
	}

	public static boolean isComplete(Player player, CharacterData.Quest quest) {
		if ("defeat".equals(quest.type)) {
			return CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, quest.target);
		}
		if ("talk".equals(quest.type)) {
			return CharacterAttachments.has(player, CharacterAttachments.MET, quest.target);
		}
		if ("deliver".equals(quest.type) || "explore".equals(quest.type) || "escort".equals(quest.type)) {
			return CharacterAttachments.has(player, CharacterAttachments.MET, quest.type + ":" + quest.key);
		}
		return player.getInventory().countItem(CharacterData.item(quest.item)) >= quest.count;
	}

	private static void takeItems(Player player, Item item, int count) {
		Inventory inventory = player.getInventory();
		for (int slot = 0; slot < inventory.getContainerSize() && count > 0; slot++) {
			ItemStack stack = inventory.getItem(slot);
			if (stack.is(item)) {
				int taken = Math.min(count, stack.getCount());
				stack.shrink(taken);
				count -= taken;
			}
		}
	}

	/** Gives any amount of an item, split into full stacks (Berries stack to 64). */
	private static void give(Player player, Item item, int count) {
		while (count > 0 && item != Items.AIR) {
			int amount = Math.min(count, item.getDefaultMaxStackSize());
			give(player, new ItemStack(item, amount));
			count -= amount;
		}
	}

	private static void give(Player player, ItemStack stack) {
		if (stack.isEmpty()) {
			return;
		}
		if (!player.getInventory().add(stack)) {
			player.drop(stack, false, Prediction.SERVER_ONLY); // Inventory full: drop it at their feet.
		}
	}
}
