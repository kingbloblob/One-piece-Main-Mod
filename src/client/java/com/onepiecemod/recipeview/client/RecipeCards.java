package com.onepiecemod.recipeview.client;

import java.util.List;

import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;

/**
 * Draws one recipe (a ViewRecipe) as a card: where it's made, the ingredients, an arrow and the result,
 * plus notes such as "Requires: Beat Smoker" in gold. Used by the Crafter's Journal.
 */
public class RecipeCards {
	public static final int HEIGHT = 84;
	private static final int TEXT = 0xFF3B2A1A, NOTE = 0xFF5A4630, GOLD = 0xFFA86A00, CARD = 0x30000000;

	/** The item under the mouse after the last draw, or EMPTY. */
	public static ItemStack hovered = ItemStack.EMPTY;

	public static void draw(GuiGraphicsExtractor graphics, Font font, ViewRecipe recipe, int x, int y, int w, int mouseX, int mouseY) {
		graphics.fill(x, y, x + w, y + HEIGHT - 4, CARD);
		graphics.fakeItem(recipe.icon, x + 2, y + 2);
		graphics.text(font, shorten(font, recipe.title, w - 24), x + 22, y + 6, recipe.locked ? GOLD : TEXT, false);

		int gridY = y + 21;
		int resultX;
		int perRow = recipe.gridWidth == 3 ? 3 : Math.max(1, Math.min(4, (w - 70) / 18));
		for (int i = 0; i < recipe.inputs.size() && i < 12; i++) {
			slot(graphics, font, recipe.inputs.get(i), x + 4 + (i % perRow) * 18, gridY + (i / perRow) * 18, mouseX, mouseY);
		}
		int columns = recipe.gridWidth == 3 ? 3 : Math.max(1, Math.min(perRow, recipe.inputs.size()));
		resultX = x + 4 + columns * 18 + 20;
		int arrowY = gridY + (recipe.gridWidth == 3 || recipe.inputs.size() > perRow ? 18 : 0) + 4;
		if (!recipe.inputs.isEmpty()) {
			graphics.text(font, "->", resultX - 15, arrowY, NOTE, false);
		} else {
			resultX = x + 4;
		}
		slot(graphics, font, new ViewRecipe.Slot(List.of(recipe.result), null), resultX, arrowY - 4, mouseX, mouseY);

		// Notes go to the right of the result when there's room, otherwise below it.
		int noteX = resultX + 22;
		int noteY = gridY;
		if (x + w - noteX < 60) {
			noteX = x + 4;
			noteY = gridY + (recipe.gridWidth == 3 ? 56 : 22);
		}
		for (String note : recipe.notes) {
			boolean gate = note.startsWith("Requires: ");
			for (var line : font.split(Component.literal(note), x + w - noteX - 2)) {
				if (noteY > y + HEIGHT - 14) {
					return;
				}
				graphics.text(font, line, noteX, noteY, gate ? GOLD : NOTE, false);
				noteY += 9;
			}
		}
	}

	/** One item slot, with its count, remembered as hovered if the mouse is on it. */
	public static void slot(GuiGraphicsExtractor graphics, Font font, ViewRecipe.Slot slot, int x, int y, int mouseX, int mouseY) {
		graphics.fill(x - 1, y - 1, x + 17, y + 17, 0xFF8B8B8B);
		graphics.fill(x, y, x + 17, y + 17, 0xFFFFFFFF);
		graphics.fill(x, y, x + 16, y + 16, 0xFF373737);
		ItemStack stack = slot.shown();
		if (stack.isEmpty()) {
			return;
		}
		graphics.fakeItem(stack, x, y);
		graphics.itemDecorations(font, stack, x, y);
		if (mouseX >= x && mouseX < x + 16 && mouseY >= y && mouseY < y + 16) {
			graphics.fill(x, y, x + 16, y + 16, 0x80FFFFFF);
			hovered = stack;
		}
	}

	public static String shorten(Font font, String text, int maxWidth) {
		if (font.width(text) <= maxWidth) {
			return text;
		}
		while (text.length() > 1 && font.width(text + "...") > maxWidth) {
			text = text.substring(0, text.length() - 1);
		}
		return text + "...";
	}
}
