package com.onepiecemod.crewship;

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
import com.onepiecemod.crafting.CraftingFeature;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.cuisine.CuisineItems;
import com.onepiecemod.deco.DecoItems;
import com.onepiecemod.shipcombat.ShipCombatFeature;
import com.onepiecemod.treasure.TreasureFeature;
import com.onepiecemod.weapon.WeaponItems;

/**
 * The daily haul aboard a home ship: every stationed crewmate brings in something from their job, half as
 * much without their room, 1.5x with it. The ship's level, the crewmate's level and a Musician in the
 * Music Bar (+20%) make it bigger. A Garden grows mikan for everyone.
 */
final class CrewShipHaul {
	private static final Item[] DISHES = {CuisineItems.SEAFOOD_FRIED_RICE, CuisineItems.EEL_KABAYAKI, CuisineItems.SEA_BREAM_SASHIMI,
			CuisineItems.SWORDFISH_STEAK, CuisineItems.LOBSTER_BISQUE};
	private static final Item[] SHOT = {ShipCombatFeature.CHAIN_SHOT, ShipCombatFeature.FIRE_SHOT, ShipCombatFeature.GRAPESHOT};

	private CrewShipHaul() {
	}

	record Haul(List<ItemStack> items, List<String> lines) {}

	static Haul roll(CrewShipLife.Home home, RandomSource random) {
		List<ItemStack> items = new ArrayList<>();
		List<String> lines = new ArrayList<>();
		double boost = CrewShipLevels.haulBoost(home.shipLevel) * (home.has(ShipRoom.BAR) ? 1.2 : 1.0);

		for (CrewmateEntity crewmate : home.stationed) {
			ShipRoom room = ShipRoom.forRole(crewmate.getRole());
			boolean inRoom = room != null && home.survey.has(room);
			double scale = boost * (inRoom ? 1.5 : 0.5) * (1.0 + 0.05 * (crewmate.getCrewLevel() - 1));
			Map<Item, Integer> got = new LinkedHashMap<>();
			switch (crewmate.getRole()) {
				case COOK -> {
					add(got, CuisineItems.GRILLED_FISH, n(3, scale));
					if (inRoom) {
						add(got, DISHES[random.nextInt(DISHES.length)], home.shipLevel >= 3 ? 2 : 1);
					}
				}
				case NAVIGATOR -> {
					add(got, Items.PAPER, n(3, scale));
					if (random.nextFloat() < (inRoom ? 0.3f : 0.1f)) {
						add(got, TreasureFeature.TREASURE_MAP, 1);
					}
				}
				case SNIPER -> {
					add(got, Items.ARROW, n(8, scale));
					add(got, Items.GUNPOWDER, n(2, scale));
					if (inRoom) {
						add(got, SHOT[random.nextInt(SHOT.length)], n(2, scale));
					}
				}
				case SWORDSMAN -> {
					add(got, Items.IRON_INGOT, n(1, scale));
					add(got, Items.BONE, n(2, scale));
				}
				case DOCTOR -> {
					add(got, Items.GOLDEN_CARROT, n(2, scale));
					add(got, Items.POTION, 1); // A Potion of Healing, see below.
					if (inRoom) {
						add(got, CraftingFeature.HERBAL_TEA, 1);
					}
				}
				case SHIPWRIGHT -> {
					add(got, WeaponItems.CANNONBALL, n(3, scale));
					add(got, Items.OAK_PLANKS, n(8, scale));
					if (inRoom) {
						add(got, Items.IRON_NUGGET, n(6, scale));
					}
				}
				case ARCHAEOLOGIST -> {
					add(got, Items.GOLD_NUGGET, n(4, scale));
					if (random.nextFloat() < (inRoom ? 0.3f : 0.1f)) {
						add(got, Items.EMERALD, 1);
					}
					if (inRoom && random.nextFloat() < 0.2f) {
						add(got, Items.BOOK, 1);
					}
				}
				case HELMSMAN -> {
					add(got, Items.COD, n(2, scale));
					add(got, Items.SALMON, n(1, scale));
					if (random.nextFloat() < (inRoom ? 0.15f : 0.05f)) {
						add(got, TreasureFeature.WRECK_CHART, 1);
					}
				}
				case MUSICIAN -> {
				}
			}
			String name = crewmate.getDisplayName().getString();
			if (got.isEmpty()) {
				lines.add(name + ": " + (inRoom ? "played in the Music Bar all day (+20% to everyone's haul)" : "played on deck (build a Music Bar for a bonus)"));
				continue;
			}
			List<String> parts = new ArrayList<>();
			for (Map.Entry<Item, Integer> entry : got.entrySet()) {
				ItemStack stack = entry.getKey() == Items.POTION
						? PotionContents.createItemStack(Items.POTION, Potions.HEALING)
						: new ItemStack(entry.getKey(), entry.getValue());
				items.add(stack);
				parts.add(entry.getValue() + " " + stack.getHoverName().getString());
			}
			lines.add(name + (inRoom ? "" : " (no " + room.title + ")") + ": " + String.join(", ", parts));
		}
		if (home.survey.has(ShipRoom.GARDEN)) {
			int mikan = n(3, boost);
			items.add(new ItemStack(DecoItems.MIKAN, mikan));
			lines.add("Garden: " + mikan + " Mikan");
		}
		if (!home.stationed.isEmpty() && home.shipLevel > 0) {
			items.add(new ItemStack(CharacterFeature.BERRY, home.shipLevel * 3));
		}
		// Working in their own room teaches a crewmate a little.
		for (CrewmateEntity crewmate : home.stationed) {
			ShipRoom room = ShipRoom.forRole(crewmate.getRole());
			if (room != null && home.survey.has(room)) {
				crewmate.addXp(2);
			}
		}
		return new Haul(items, lines);
	}

	private static int n(int base, double scale) {
		return Math.max(1, (int) Math.round(base * scale));
	}

	private static void add(Map<Item, Integer> got, Item item, int count) {
		got.merge(item, count, Integer::sum);
	}
}
