package com.onepiecemod.jei;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;

import mezz.jei.api.gui.builder.IRecipeLayoutBuilder;
import mezz.jei.api.gui.drawable.IDrawable;
import mezz.jei.api.gui.ingredient.IRecipeSlotsView;
import mezz.jei.api.helpers.IGuiHelper;
import mezz.jei.api.recipe.IFocusGroup;
import mezz.jei.api.recipe.RecipeIngredientRole;
import mezz.jei.api.recipe.category.IRecipeCategory;
import mezz.jei.api.recipe.types.IRecipeType;

import com.onepiecemod.recipeview.client.ViewRecipe;

/**
 * One JEI page type that shows ViewRecipes: up to two rows of ingredients, an arrow, the result,
 * and the recipe's notes underneath (locks in gold). Station pages leave out the title, since the page is the station.
 */
public class ViewRecipeCategory implements IRecipeCategory<ViewRecipe> {
	private static final int WIDTH = 160, HEIGHT = 74, PER_ROW = 6;

	private final IRecipeType<ViewRecipe> type;
	private final Component title;
	private final IDrawable icon;
	private final IDrawable arrow;
	private final boolean station;

	public ViewRecipeCategory(IRecipeType<ViewRecipe> type, IGuiHelper guiHelper, Component title, ItemStack icon, boolean station) {
		this.type = type;
		this.title = title;
		this.icon = guiHelper.createDrawableItemStack(icon);
		this.arrow = guiHelper.getRecipeArrow();
		this.station = station;
	}

	@Override
	public IRecipeType<ViewRecipe> getRecipeType() {
		return type;
	}

	@Override
	public Component getTitle() {
		return title;
	}

	@Override
	public int getWidth() {
		return WIDTH;
	}

	@Override
	public int getHeight() {
		return HEIGHT;
	}

	@Override
	public IDrawable getIcon() {
		return icon;
	}

	private int top() {
		return station ? 1 : 12;
	}

	@Override
	public void setRecipe(IRecipeLayoutBuilder builder, ViewRecipe recipe, IFocusGroup focuses) {
		for (int i = 0; i < recipe.inputs.size() && i < PER_ROW * 2; i++) {
			ViewRecipe.Slot slot = recipe.inputs.get(i);
			var input = builder.addSlot(RecipeIngredientRole.INPUT, 1 + (i % PER_ROW) * 18, top() + (i / PER_ROW) * 18).setStandardSlotBackground();
			if (!slot.isEmpty()) {
				input.addItemStacks(slot.options);
			}
		}
		builder.addSlot(RecipeIngredientRole.OUTPUT, WIDTH - 19, top() + (recipe.inputs.size() > PER_ROW ? 9 : 0))
				.setOutputSlotBackground()
				.add(recipe.result);
	}

	@Override
	public void draw(ViewRecipe recipe, IRecipeSlotsView slots, GuiGraphicsExtractor graphics, double mouseX, double mouseY) {
		Font font = Minecraft.getInstance().font;
		if (!station) {
			graphics.text(font, recipe.title, 0, 0, 0xFF404040, false);
		}
		int rows = recipe.inputs.size() > PER_ROW ? 2 : 1;
		if (!recipe.inputs.isEmpty()) {
			arrow.draw(graphics, WIDTH - 46, top() + (rows == 2 ? 9 : 0));
		}
		int y = top() + rows * 18 + 3;
		for (String note : recipe.notes) {
			if (station && note.startsWith("Ingredients just")) {
				continue; // Every station recipe says this; JEI pages don't need it.
			}
			boolean gate = note.startsWith("Requires: ");
			for (var line : font.split(Component.literal(note), WIDTH)) {
				if (y > HEIGHT - 9) {
					return;
				}
				graphics.text(font, line, 0, y, gate ? 0xFFA86A00 : 0xFF606060, false);
				y += 9;
			}
		}
	}
}
