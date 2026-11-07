package com.onepiecemod.hideout;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.util.RandomSource;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.alchemy.PotionContents;
import net.minecraft.world.item.alchemy.Potions;

import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.cuisine.CuisineItems;
import com.onepiecemod.treasure.TreasureFeature;
import com.onepiecemod.weapon.WeaponItems;

/**
 * The daily haul: once a day every crewmate living at the hideout brings in something from their job.
 * Amounts grow with the hideout's level and the crewmate's own level, and a Musician cheers everyone on (+20%).
 *
 *  Cook: grilled fish, and a proper dish from a Pirate Fort up    Navigator: paper, and sometimes a Treasure Map
 *  Sniper: arrows and gunpowder                                   Swordsman: what the patrols turn up (bones, iron)
 *  Doctor: a Potion of Healing and golden carrots                 Shipwright: cannonballs for the cannons, planks
 *  Archaeologist: gold nuggets, sometimes an emerald              Helmsman: fish, sometimes a Wreck Chart
 *  Musician: no items, but everyone else brings in more
 */
final class HideoutHaul {
	private static final Item[] DISHES = {CuisineItems.SEAFOOD_FRIED_RICE, CuisineItems.EEL_KABAYAKI, CuisineItems.SEA_BREAM_SASHIMI,
			CuisineItems.SWORDFISH_STEAK, CuisineItems.LOBSTER_BISQUE};

	private HideoutHaul() {
	}

	/** Result of one day. lines = "Cook Sora: 5 Grilled Fish" for the report. */
	record Haul(List<ItemStack> items, List<String> lines) {}

	static Haul roll(List<CrewmateEntity> residents, int hideoutLevel, RandomSource random) {
		List<ItemStack> items = new ArrayList<>();
		List<String> lines = new ArrayList<>();
		boolean musician = false;
		for (CrewmateEntity crewmate : residents) {
			musician |= crewmate.getRole() == CrewRole.MUSICIAN;
		}
		double boost = HideoutLevels.haulBoost(hideoutLevel) * (musician ? 1.2 : 1.0);

		for (CrewmateEntity crewmate : residents) {
			double scale = boost * (1.0 + 0.05 * (crewmate.getCrewLevel() - 1));
			Map<Item, Integer> got = new LinkedHashMap<>();
			switch (crewmate.getRole()) {
				case COOK -> {
					add(got, CuisineItems.GRILLED_FISH, n(3, scale));
					if (hideoutLevel >= 3) {
						add(got, DISHES[random.nextInt(DISHES.length)], 1);
					}
				}
				case NAVIGATOR -> {
					add(got, Items.PAPER, n(3, scale));
					if (hideoutLevel >= 2 && random.nextFloat() < 0.15f * scale) {
						add(got, TreasureFeature.TREASURE_MAP, 1);
					}
				}
				case SNIPER -> {
					add(got, Items.ARROW, n(10, scale));
					add(got, Items.GUNPOWDER, n(2, scale));
				}
				case SWORDSMAN -> {
					add(got, Items.BONE, n(3, scale));
					add(got, Items.STRING, n(2, scale));
					add(got, Items.IRON_INGOT, n(1, scale));
				}
				case DOCTOR -> {
					add(got, Items.GOLDEN_CARROT, n(2, scale));
					add(got, Items.POTION, 1); // Turned into a Potion of Healing below.
				}
				case SHIPWRIGHT -> {
					add(got, WeaponItems.CANNONBALL, n(3, scale));
					add(got, Items.OAK_PLANKS, n(8, scale));
				}
				case ARCHAEOLOGIST -> {
					add(got, Items.GOLD_NUGGET, n(4, scale));
					if (random.nextFloat() < 0.2f * scale) {
						add(got, Items.EMERALD, 1);
					}
				}
				case HELMSMAN -> {
					add(got, Items.COD, n(2, scale));
					add(got, Items.SALMON, n(1, scale));
					if (random.nextFloat() < 0.1f * scale) {
						add(got, TreasureFeature.WRECK_CHART, 1);
					}
				}
				case MUSICIAN -> {
				}
			}
			if (got.isEmpty()) {
				lines.add(name(crewmate) + ": played for the crew all day (+20% to everyone's haul)");
				continue;
			}
			List<String> parts = new ArrayList<>();
			for (Map.Entry<Item, Integer> entry : got.entrySet()) {
				ItemStack stack = new ItemStack(entry.getKey(), entry.getValue());
				if (entry.getKey() == Items.POTION) {
					stack = PotionContents.createItemStack(Items.POTION, Potions.HEALING);
				}
				items.add(stack);
				parts.add(entry.getValue() + " " + stack.getHoverName().getString());
			}
			lines.add(name(crewmate) + ": " + String.join(", ", parts));
		}
		// Dues: the crew pays into the hideout's coffers.
		if (!residents.isEmpty() && hideoutLevel > 0) {
			items.add(new ItemStack(CharacterFeature.BERRY, hideoutLevel * 2));
		}
		return new Haul(items, lines);
	}

	private static String name(CrewmateEntity crewmate) {
		return crewmate.getDisplayName().getString(); // On the server: "Cook Sora".
	}

	private static int n(int base, double scale) {
		return Math.max(1, (int) Math.round(base * scale));
	}

	private static void add(Map<Item, Integer> got, Item item, int count) {
		got.merge(item, count, Integer::sum);
	}
}
