package com.onepiecemod.bounty;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.util.RandomSource;

import com.onepiecemod.character.CharacterData;
import com.onepiecemod.power.DevilFruit;
import com.onepiecemod.power.DevilFruits;

/**
 * A Devil Fruit a bounty hunter can have, and the two moves it gives them.
 * The list is built from characters.json: every story character's fruit, with that character's boss moves
 * (so a hunter with the Mera Mera no Mi throws fire like Ace). Strong fruits only show up at high bounties.
 *
 * @param item   the fruit's item id, like "onepiece:mera_mera_no_mi"
 * @param name   shown in the hunter's name, like "Mera Mera no Mi"
 * @param power  main move (see BossAbility)
 * @param power2 second move, used every other time
 * @param tier   1 to 5, from the story character who owns it. Hunters only get fruits up to your threat level.
 */
public record HunterFruit(String item, String name, String power, String power2, int tier) {
	private static List<HunterFruit> all;

	public static List<HunterFruit> all() {
		if (all == null) {
			Map<String, HunterFruit> byItem = new LinkedHashMap<>();
			for (CharacterData character : CharacterData.all().values()) {
				if (character.fruitItem == null || character.fruitItem.isEmpty() || "rocks".equals(character.power)) {
					continue;
				}
				String id = character.fruitItem.substring(character.fruitItem.indexOf(':') + 1);
				DevilFruit fruit = DevilFruits.get(id);
				String name = fruit != null ? fruit.name() : id;
				HunterFruit candidate = new HunterFruit(character.fruitItem, name, character.power, character.hardPower,
						Math.max(1, Math.min(5, character.tier)));
				// If two characters share a fruit (Ace and Sabo), keep the easier one.
				HunterFruit existing = byItem.get(character.fruitItem);
				if (existing == null || candidate.tier < existing.tier) {
					byItem.put(character.fruitItem, candidate);
				}
			}
			all = new ArrayList<>(byItem.values());
		}
		return all;
	}

	/** A random fruit no stronger than maxTier. */
	public static HunterFruit random(RandomSource random, int maxTier) {
		List<HunterFruit> choices = new ArrayList<>();
		for (HunterFruit fruit : all()) {
			if (fruit.tier <= maxTier) {
				choices.add(fruit);
			}
		}
		if (choices.isEmpty()) {
			choices = all();
		}
		return choices.get(random.nextInt(choices.size()));
	}

	public static HunterFruit byItem(String item) {
		for (HunterFruit fruit : all()) {
			if (fruit.item.equals(item)) {
				return fruit;
			}
		}
		return null;
	}
}
