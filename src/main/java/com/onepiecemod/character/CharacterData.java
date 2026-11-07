package com.onepiecemod.character;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/**
 * One One Piece character, read from src/main/resources/onepiece/characters.json.
 * To change a character (health, quest, what they sell), edit that JSON file, not this class.
 */
public class CharacterData {
	public static final String BOSS = "boss";
	public static final String QUEST = "quest";
	public static final String TRADER = "trader";

	public String id;
	public String name;
	/** "boss", "quest" or "trader": what this character is in the story. */
	public String role;
	/** 1 (East Blue) to 5 (Emperors and Admirals). */
	public int tier;
	public float health;
	public float damage;
	/** How many Berries this character drops when beaten as a boss. */
	public int bounty;
	/** Size compared to a player. Kaido is 2.5. */
	public float scale = 1.0f;
	/** Which special attack the boss version uses. See BossAbility. */
	public String power = "punch";
	/** The second special attack, used on Hard and Expert. */
	public String hardPower = "punch";
	/** Extra items dropped when beaten on Hard, and on Expert. */
	public List<String> hardRewards = List.of();
	public List<String> expertRewards = List.of();
	public String greeting = "";
	/** The Devil Fruit item this character drops as a boss, like "onepiece:mera_mera_no_mi". */
	public String fruitItem;
	public String heldItem;
	public String offhandItem;
	public String bonusDrop;
	/** The quest line: steps the player does one after another. */
	public List<Quest> quests = List.of();
	/** What a quest giver says once the whole quest line is done. */
	public String thanks = "";
	/** Trader levels, like villagers: Novice, Apprentice, Journeyman, Expert, Master. */
	public List<List<Trade>> levels = List.of();

	public static class Quest {
		/**
		 * "defeat" (beat a boss), "fetch" (bring items), "talk" (go talk to another character),
		 * "deliver" (carry the items you're given to the target character), "explore" (reach the target location)
		 * or "escort" (bring the target character safely to the location in "place").
		 */
		public String type;
		public String target;
		public String item;
		public int count = 1;
		public int berries;
		/** Pirate XP for finishing the step. Left out (-1) it is half the Berries. */
		public int xp = -1;
		public String rewardItem;
		public int rewardCount = 1;
		public String start = "";
		public String done = "";
		/** Escort steps: the location (like "ohara_library") to bring the character to. */
		public String place;
		/** "giver:step", filled in when the file is read (not in the JSON). */
		public transient String key;

		/** The Pirate XP this step pays. */
		public int xpReward() {
			return xp >= 0 ? xp : berries / 2;
		}
	}

	/** The player pays buyCount x buy and gets sellCount x sell. */
	public static class Trade {
		public String buy;
		public int buyCount = 1;
		public String sell;
		public int sellCount = 1;
		/** If set, the trader sells a Sea Chart to this location (a structure id) instead of the "sell" item. */
		public String chart;
		/** How many times you can make this trade before the trader restocks. */
		public int maxUses = 12;
		/** Trader XP per trade. Enough XP and the trader levels up. */
		public int xp = 2;
	}

	public boolean isBossRole() {
		return BOSS.equals(role);
	}

	// ---- Loading ----

	private static final Map<String, CharacterData> ALL = new LinkedHashMap<>();

	public static Map<String, CharacterData> all() {
		if (ALL.isEmpty()) {
			try (InputStream in = CharacterData.class.getResourceAsStream("/onepiece/characters.json")) {
				CharacterData[] list = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), CharacterData[].class);
				for (CharacterData character : list) {
					ALL.put(character.id, character);
					for (int step = 0; step < character.quests.size(); step++) {
						character.quests.get(step).key = character.id + ":" + step;
					}
				}
			} catch (Exception e) {
				throw new RuntimeException("Could not read onepiece/characters.json", e);
			}
		}
		return ALL;
	}

	public static CharacterData get(String id) {
		return all().get(id);
	}

	/** Looks up an item by id like "minecraft:diamond". Returns AIR if it doesn't exist (yet). */
	public static Item item(String id) {
		if (id == null) {
			return Items.AIR;
		}
		return BuiltInRegistries.ITEM.getValue(Identifier.parse(id));
	}

	public static ItemStack stack(String id, int count) {
		Item item = item(id);
		return item == Items.AIR ? ItemStack.EMPTY : new ItemStack(item, count);
	}

	/**
	 * The attack damage a held weapon adds on top of a mob's base damage. Data files give a mob's whole hit
	 * (kit "damage", character "damage"), so subtract this from the base or a stone axe turns a 3-damage bandit into 11.
	 */
	public static double weaponBonus(ItemStack weapon) {
		return weapon.getOrDefault(net.minecraft.core.component.DataComponents.ATTRIBUTE_MODIFIERS,
				net.minecraft.world.item.component.ItemAttributeModifiers.EMPTY)
				.compute(net.minecraft.world.entity.ai.attributes.Attributes.ATTACK_DAMAGE, 0.0, net.minecraft.world.entity.EquipmentSlot.MAINHAND);
	}
}
