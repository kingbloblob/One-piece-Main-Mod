package com.onepiecemod.recipeview.client;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.world.item.ItemStack;

/**
 * One way to get an item, as shown in the recipe viewer: a crafting recipe, a furnace recipe,
 * a station recipe, a trade or a boss drop. Only used for showing, never for crafting.
 */
public class ViewRecipe {
	/** Where you make it, like "Crafting Table" or "Shipwright's Bench (Tier 1)". */
	public final String title;
	/** The block or item shown next to the title. */
	public final ItemStack icon;
	/** 3 = a crafting grid (inputs fill rows of 3), 0 = a simple row of inputs. */
	public final int gridWidth;
	public final List<Slot> inputs = new ArrayList<>();
	public final ItemStack result;
	/** Extra lines under the recipe, like "Requires: Beat Smoker". */
	public final List<String> notes = new ArrayList<>();
	/** True for lines in notes that are progress gates (shown in gold). */
	public boolean locked;
	/** Which JEI page shows it: "station:<id>" for a crafting station, "source" for drops, trades and quests. Null = not shown in JEI (JEI has its own vanilla pages). */
	public String jeiCategory;

	public ViewRecipe(String title, ItemStack icon, int gridWidth, ItemStack result) {
		this.title = title;
		this.icon = icon;
		this.gridWidth = gridWidth;
		this.result = result;
	}

	/** One input slot. It can accept several items (a tag like "any planks"): the viewer cycles through them. */
	public static class Slot {
		public static final Slot EMPTY = new Slot(List.of(), null);

		public final List<ItemStack> options;
		/** A name for tag slots, like "Any Planks". Null shows the item's own name. */
		public final String name;

		public Slot(List<ItemStack> options, String name) {
			this.options = options;
			this.name = name;
		}

		public boolean isEmpty() {
			return options.isEmpty();
		}

		/** The item to draw right now. Tags change item once a second. */
		public ItemStack shown() {
			if (options.isEmpty()) {
				return ItemStack.EMPTY;
			}
			return options.get((int) ((System.currentTimeMillis() / 1000) % options.size()));
		}
	}
}
