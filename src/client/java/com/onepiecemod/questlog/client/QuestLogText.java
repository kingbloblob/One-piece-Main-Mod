package com.onepiecemod.questlog.client;

import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;

import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.Locations;
import com.onepiecemod.questlog.QuestLogFeature;

/** Words for quest steps and islands, shared by the journal screen and the compass bar. Client only. */
final class QuestLogText {
	private QuestLogText() {
	}

	/** "Beat Buggy", "Talk to Koby" or "Bring 16 Cooked Beef". */
	static String summary(CharacterData.Quest quest) {
		return switch (quest.type) {
			case "defeat" -> "Beat " + name(quest.target);
			case "talk" -> "Talk to " + name(quest.target);
			case "deliver" -> "Deliver a package to " + name(quest.target);
			case "explore" -> "Explore " + Locations.name(quest.target);
			case "escort" -> "Escort " + name(quest.target) + " to " + Locations.name(quest.place);
			default -> {
				ItemStack stack = CharacterData.stack(quest.item, 1);
				yield "Bring " + quest.count + " " + (stack.isEmpty() ? quest.item : stack.getHoverName().getString());
			}
		};
	}

	/** The character who gave a step, from a key like "luffy:0". */
	static String giver(String key) {
		int colon = key.lastIndexOf(':');
		return name(colon < 0 ? key : key.substring(0, colon));
	}

	static String giverId(String key) {
		int colon = key.lastIndexOf(':');
		return colon < 0 ? key : key.substring(0, colon);
	}

	/** "Step 2 of 4". */
	static String stepOf(String key) {
		CharacterData character = CharacterData.get(giverId(key));
		int step = Integer.parseInt(key.substring(key.lastIndexOf(':') + 1));
		return "Step " + (step + 1) + " of " + (character != null ? character.quests.size() : "?");
	}

	/** Where to find the quest giver again, like "Foosha Village", or null if nobody knows. */
	static String home(String key) {
		String home = Locations.home(giverId(key));
		if (home == null) {
			return null;
		}
		return (Locations.onlyLastSeen(giverId(key)) ? "last seen at " : "") + Locations.name(home);
	}

	static String name(String characterId) {
		CharacterData character = CharacterData.get(characterId);
		return character != null ? character.name : characterId;
	}

	/** How many of a "bring" step's items you're carrying, like "5/16", or null for other kinds of step. */
	static String itemProgress(CharacterData.Quest quest) {
		Minecraft client = Minecraft.getInstance();
		if (!"fetch".equals(quest.type) || client.player == null || quest.count <= 0) {
			return null;
		}
		int have = client.player.getInventory().countItem(CharacterData.item(quest.item));
		return Math.min(have, quest.count) + "/" + quest.count;
	}

	/** The name of an island's biome id ("onepiece:alabasta" -> "Alabasta"), or Foosha Village. */
	static String island(String biome) {
		if (biome.equals("foosha")) {
			return "Foosha Village";
		}
		if (biome.equals("start")) {
			return "Castaway Island";
		}
		if (biome.isEmpty()) {
			return "an island";
		}
		return Component.translatable("biome." + biome.replace(':', '.')).getString();
	}

	/** Short sea names for the bar, from CalmBelt.Sea names. */
	static String sea(String sea) {
		return switch (sea) {
			case "BLUE" -> "East Blue";
			case "CALM_BELT" -> "Calm Belt";
			case "GRAND_LINE" -> "Grand Line";
			case "NEW_WORLD" -> "New World";
			default -> "";
		};
	}

	static int seaColour(String sea) {
		return switch (sea) {
			case "BLUE" -> 0xFF6FE3F0;
			case "CALM_BELT" -> 0xFFFF6B6B;
			case "GRAND_LINE" -> 0xFFF2C14E;
			case "NEW_WORLD" -> 0xFFFF8A3D;
			default -> 0xFFA8B0C0;
		};
	}

	static boolean isStory(String key) {
		return QuestLogFeature.STORY.equals(key);
	}
}
