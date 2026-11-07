package com.onepiecemod.crewship;

import java.util.Set;
import java.util.function.Predicate;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.state.BlockState;

import com.onepiecemod.crew.CrewRole;

/**
 * The rooms a crew ship can have, like the Thousand Sunny: one workstation room for each crew job, plus a
 * captain's cabin, a garden on deck and a bath. A room is found when its main block (the "core") has enough
 * of the right blocks around it (within 4 blocks). A room with its crewmate stationed aboard gives a perk.
 */
public enum ShipRoom {
	HELM("Helm", CrewRole.HELMSMAN, "the Ship's Wheel", 0,
			ids("onepiece:ships_wheel"),
			block -> false,
			"Turns 15% faster; fish and Wreck Charts in the haul"),
	GALLEY("Galley", CrewRole.COOK, "a smoker, furnace, stove or Ship's Galley with 2 of: galley sink, counter, cupboard, barrel, cooking pot, crafting table", 2,
			ids("minecraft:smoker", "minecraft:furnace", "onepiece:iron_stove", "onepiece:hearth", "onepiece:ships_galley"),
			ids("onepiece:galley_sink", "onepiece:cooking_pot", "minecraft:barrel", "minecraft:crafting_table", "minecraft:cauldron",
					"onepiece:fruit_bowl", "onepiece:bread_basket", "onepiece:meat_platter", "onepiece:iron_stove", "minecraft:smoker")
					.or(suffix("_counter")).or(suffix("_cupboard")),
			"Keeps everyone aboard fed; dishes in the haul"),
	INFIRMARY("Infirmary", CrewRole.DOCTOR, "a brewing stand or medicine cabinet with a bed or hammock", 1,
			ids("minecraft:brewing_stand", "onepiece:medicine_cabinet"),
			ShipRoom::isBunk,
			"Heals the crew aboard when they're hurt; medicine in the haul"),
	CHART_ROOM("Chart Room", CrewRole.NAVIGATOR, "a cartography table, chart table, Navigator's Desk or wall map with a lectern, bookshelf, desk, globe or telescope", 1,
			ids("minecraft:cartography_table", "onepiece:chart_table", "onepiece:navigators_desk", "onepiece:grand_line_wall_map"),
			ids("minecraft:lectern", "minecraft:bookshelf", "onepiece:writing_desk", "onepiece:globe", "onepiece:drafting_table",
					"onepiece:telescope", "onepiece:chart_table", "minecraft:cartography_table", "onepiece:grand_line_wall_map", "onepiece:book_stack"),
			"Sails 10% faster; maps in the haul"),
	LIBRARY("Library", CrewRole.ARCHAEOLOGIST, "a lectern or writing desk with 4 bookshelves (or book stacks)", 4,
			ids("minecraft:lectern", "onepiece:writing_desk"),
			ids("minecraft:bookshelf", "minecraft:chiseled_bookshelf", "onepiece:book_stack"),
			"Gold, gems and old books in the haul"),
	WORKSHOP("Workshop", CrewRole.SHIPWRIGHT, "a Shipwright's Bench, smithing table or tool bench with an anvil, grindstone, tool rack or stonecutter", 1,
			ids("onepiece:shipwright_bench", "minecraft:smithing_table", "onepiece:tool_bench"),
			ids("minecraft:grindstone", "onepiece:tool_rack", "minecraft:stonecutter", "onepiece:drafting_table", "onepiece:cola_barrel")
					.or(state -> state.is(BlockTags.ANVIL)),
			"Patches the hull even mid-battle; cannonballs in the haul"),
	FACTORY("Weapons Factory", CrewRole.SNIPER, "a fletching table with a target, powder keg, cannonball pile, weapon rack or dispenser", 1,
			ids("minecraft:fletching_table"),
			ids("minecraft:target", "onepiece:powder_keg", "onepiece:cannonball_pile", "onepiece:weapon_rack", "minecraft:dispenser",
					"minecraft:crafting_table", "onepiece:tool_rack"),
			"Special cannon shot in the haul"),
	GYM("Training Room", CrewRole.SWORDSMAN, "training weights or a katana stand with another training weight, katana stand, weapon rack or target", 1,
			ids("onepiece:training_weights", "onepiece:katana_stand"),
			ids("onepiece:training_weights", "onepiece:katana_stand", "onepiece:weapon_rack", "minecraft:target"),
			"Strength I aboard; the crew trains (bonus crewmate XP)"),
	BAR("Music Bar", CrewRole.MUSICIAN, "a piano, jukebox or note block with a bar, bar stool, keg, sake set, mugs or wine rack", 1,
			ids("onepiece:piano", "minecraft:jukebox", "minecraft:note_block"),
			ids("onepiece:tavern_bar", "onepiece:bar_stool", "onepiece:keg", "onepiece:sake_set", "onepiece:beer_mugs",
					"onepiece:wine_rack", "onepiece:cola_barrel"),
			"Everyone's haul +20%"),
	CABIN("Captain's Cabin", null, "a captain's chair or throne with a bed, hammock or writing desk", 1,
			ids("onepiece:captains_chair", "onepiece:throne"),
			((Predicate<BlockState>) ShipRoom::isBunk).or(ids("onepiece:writing_desk")),
			"Needed for the Pirate Brig"),
	GARDEN("Garden", null, "Deck Lawn or Deck Soil with 4 plants on or around it (flowers, saplings, crops, mikan, a tree)", 4,
			ids("onepiece:deck_lawn", "onepiece:deck_soil", "onepiece:mikan_tree_pot"),
			ids("onepiece:mikan_bush", "onepiece:mikan_tree_pot", "onepiece:bonsai", "minecraft:flower_pot")
					.or(state -> state.is(BlockTags.FLOWERS) || state.is(BlockTags.SAPLINGS) || state.is(BlockTags.CROPS) || state.is(BlockTags.LEAVES)),
			"Mikan and herbs in the haul"),
	BATH("Bath", null, "a bathtub or wooden tub", 0,
			ids("onepiece:bathtub", "onepiece:wooden_tub"),
			block -> false,
			"A soak clears poison, hunger and other bad effects");

	/** How far from the core block the other room blocks may be. */
	public static final int RADIUS = 4;

	public final String title;
	/** The crew job that works here, or null for rooms anyone uses. */
	public final CrewRole role;
	/** What to build, for the report. */
	public final String hint;
	public final int partnersNeeded;
	private final Predicate<BlockState> core;
	private final Predicate<BlockState> partner;
	/** What the room does once its crewmate is stationed aboard (or always, for rooms without a job). */
	public final String perk;

	ShipRoom(String title, CrewRole role, String hint, int partnersNeeded, Predicate<BlockState> core, Predicate<BlockState> partner, String perk) {
		this.title = title;
		this.role = role;
		this.hint = hint;
		this.partnersNeeded = partnersNeeded;
		this.core = core;
		this.partner = partner;
		this.perk = perk;
	}

	public boolean isCore(BlockState state) {
		return core.test(state);
	}

	public boolean isPartner(BlockState state) {
		return partner.test(state);
	}

	/** The room where this job works, or null. */
	public static ShipRoom forRole(CrewRole role) {
		for (ShipRoom room : values()) {
			if (room.role == role) {
				return room;
			}
		}
		return null;
	}

	/** Rooms that belong to a crew job (the 9 workstations). */
	public static int jobRooms() {
		int count = 0;
		for (ShipRoom room : values()) {
			if (room.role != null) {
				count++;
			}
		}
		return count;
	}

	// ---- Block matching ----

	static String id(BlockState state) {
		return BuiltInRegistries.BLOCK.getKey(state.getBlock()).toString();
	}

	static boolean isBunk(BlockState state) {
		return state.getBlock() instanceof BedBlock || id(state).equals("onepiece:hammock");
	}

	private static Predicate<BlockState> ids(String... names) {
		Set<String> set = Set.of(names);
		return state -> set.contains(id(state));
	}

	private static Predicate<BlockState> suffix(String end) {
		return state -> id(state).endsWith(end);
	}
}
