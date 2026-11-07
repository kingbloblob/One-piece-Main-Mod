package com.onepiecemod.settlement;

import java.util.List;
import java.util.function.Predicate;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BedPart;

/**
 * The kinds of plot you can mark out with the Town Planner. Each plot is "settled" once it has what's listed
 * here somewhere inside it. A settled House gives the town 2 people; every other settled plot gives one job
 * (the townsperson who works there). Every settled plot pays a little rent into the town treasury each day.
 */
public enum PlotKind {
	HOUSE("House", "minecraft:white_stained_glass", null, 3,
			need("a bed", PlotKind::bedHead, 1), need("a door", s -> s.is(BlockTags.DOORS), 1), need("a light", PlotKind::light, 1)),
	SHOP("Shop", "minecraft:yellow_stained_glass", "merchant", 6,
			need("counters, barrels or chests", s -> has(s, "_counter", "barrel", "chest", "_crate", "crate_stack"), 2),
			need("a light", PlotKind::light, 1)),
	TAVERN("Tavern", "minecraft:orange_stained_glass", "bartender", 8,
			need("barrels or kegs", s -> has(s, "barrel", "keg", "wine_rack", "sake"), 2),
			need("seats (stools, chairs, stairs)", PlotKind::seat, 2), need("a light", PlotKind::light, 1)),
	RESTAURANT("Restaurant", "minecraft:red_stained_glass", "cook", 7,
			need("a smoker, furnace, campfire or cauldron", s -> has(s, "smoker", "furnace", "campfire", "cauldron", "stove"), 1),
			need("a table", s -> has(s, "_table", "kotatsu"), 1), need("seats (stools, chairs, stairs)", PlotKind::seat, 2)),
	FARM("Farm", "minecraft:lime_stained_glass", "farmer", 4,
			need("farmland", s -> has(s, "farmland"), 9), need("water", s -> s.getFluidState().is(FluidTags.WATER), 1),
			need("a composter or hay bale", s -> has(s, "composter", "hay_block"), 1)),
	DOCK("Dock", "minecraft:light_blue_stained_glass", "fisher", 5,
			need("planks or slabs", s -> s.is(BlockTags.PLANKS) || s.is(BlockTags.WOODEN_SLABS), 6),
			need("water", s -> s.getFluidState().is(FluidTags.WATER), 6)),
	SHIPYARD("Shipyard", "minecraft:brown_stained_glass", "shipwright", 6,
			need("planks or slabs", s -> s.is(BlockTags.PLANKS) || s.is(BlockTags.WOODEN_SLABS), 8),
			need("water", s -> s.getFluidState().is(FluidTags.WATER), 6),
			need("a crafting table or Shipwright's Bench", s -> has(s, "crafting_table", "shipwright_bench"), 1)),
	SMITHY("Smithy", "minecraft:gray_stained_glass", "smith", 6,
			need("anvils, smithing tables, grindstones or blast furnaces", s -> s.is(BlockTags.ANVIL)
					|| has(s, "smithing_table", "grindstone", "blast_furnace"), 2),
			need("a light", PlotKind::light, 1)),
	CLINIC("Clinic", "minecraft:pink_stained_glass", "doctor", 6,
			need("a brewing stand", s -> has(s, "brewing_stand", "medicine_cabinet"), 1), need("a bed", PlotKind::bedHead, 1)),
	LIBRARY("Library", "minecraft:purple_stained_glass", "scholar", 5,
			need("a lectern", s -> has(s, "lectern", "writing_desk"), 1), need("bookshelves", s -> has(s, "bookshelf", "book_stack"), 3)),
	PLAZA("Plaza", "minecraft:magenta_stained_glass", null, 2,
			need("lights", PlotKind::light, 2), need("benches or seats", PlotKind::seat, 1));

	/** One thing a plot needs. */
	public record Need(String what, Predicate<BlockState> matches, int count) {}

	public final String title;
	/** The see-through block that outlines this plot while you hold the planner. */
	public final String outline;
	/** The town job (see towns.json) of the townsperson who works here, or null. */
	public final String job;
	/** Berries a day into the treasury once settled. */
	public final int rent;
	public final List<Need> needs;

	PlotKind(String title, String outline, String job, int rent, Need... needs) {
		this.title = title;
		this.outline = outline;
		this.job = job;
		this.rent = rent;
		this.needs = List.of(needs);
	}

	public static PlotKind byName(String name) {
		for (PlotKind kind : values()) {
			if (kind.name().equalsIgnoreCase(name)) {
				return kind;
			}
		}
		return HOUSE;
	}

	public String needsText() {
		StringBuilder text = new StringBuilder();
		for (Need need : needs) {
			if (text.length() > 0) {
				text.append(", ");
			}
			text.append(need.count() > 1 ? need.count() + " " : "").append(need.what());
		}
		return text.toString();
	}

	private static Need need(String what, Predicate<BlockState> matches, int count) {
		return new Need(what, matches, count);
	}

	private static boolean has(BlockState state, String... parts) {
		String id = BuiltInRegistries.BLOCK.getKey(state.getBlock()).getPath();
		for (String part : parts) {
			if (id.contains(part)) {
				return true;
			}
		}
		return false;
	}

	static boolean bedHead(BlockState state) {
		return state.getBlock() instanceof BedBlock && state.getValue(BedBlock.PART) == BedPart.HEAD;
	}

	static boolean light(BlockState state) {
		return state.getLightEmission() >= 10 || state.is(BlockTags.CANDLES);
	}

	static boolean seat(BlockState state) {
		return state.is(BlockTags.WOODEN_STAIRS) || has(state, "_stool", "_chair", "_bench", "cushion", "armchair", "throne");
	}
}
