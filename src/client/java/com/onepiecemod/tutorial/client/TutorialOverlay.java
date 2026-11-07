package com.onepiecemod.tutorial.client;

import java.lang.reflect.Field;
import java.util.List;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.tooltip.ClientTooltipComponent;
import net.minecraft.client.gui.screens.inventory.tooltip.DefaultTooltipPositioner;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import com.mojang.blaze3d.platform.InputConstants;

import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;
import net.fabricmc.fabric.api.client.screen.v1.ScreenMouseEvents;

import com.onepiecemod.tutorial.TutorialFeature;
import com.onepiecemod.tutorial.TutorialStep;

/**
 * The First Voyage panel: the part ("Part 2: Set Sail"), "7/16", the current step and its hint.
 * It lives in the inventory screen (above the inventory, or below it if there's no room), not on the game screen,
 * so it never covers the world. The quest tree panel is on the left and JEI on the right, so it stays in the middle.
 * A Voyage Log book button sits under the crafting grid of the survival inventory (ryan asked 2026-10-29), and clicking
 * the panel opens the same book (TutorialBookScreen), so steps and tips are easy to read again.
 */
public class TutorialOverlay {
	private static final int PAD = 4;
	private static final int ROW = 10;
	/** Creative mode's tabs stick out this far above and below its inventory. */
	private static final int CREATIVE_TABS = 30;

	private static final int TRIM = 0xFFC9A04A;
	private static final int TRIM_DARK = 0xFF5A3F12;
	private static final int BG_TOP = 0xE0182A40;
	private static final int BG_BOTTOM = 0xE00E1828;
	private static final int GOLD = 0xFFFFD75E;
	private static final int WHITE = 0xFFFFFFFF;
	private static final int GRAY = 0xFFC8D0DA;
	private static final int GREEN = 0xFF7CE07C;

	/** The Voyage Log button, placed like the recipe book button: 20 x 18, under the crafting grid. */
	private static final int BUTTON_X = 136, BUTTON_Y = 60, BUTTON_W = 20, BUTTON_H = 18;
	private static ItemStack bookIcon = ItemStack.EMPTY;

	/** Where the panel was last drawn (x, y, width, height), for clicks; width 0 when hidden. */
	private static int panelX, panelY, panelW, panelH;

	static void initialize() {
		ScreenEvents.AFTER_INIT.register((client, screen, scaledWidth, scaledHeight) -> {
			if (screen instanceof InventoryScreen || screen instanceof CreativeModeInventoryScreen) {
				panelW = 0;
				ScreenEvents.afterExtract(screen).register((s, graphics, mouseX, mouseY, tick) -> {
					drawButton(s, graphics, mouseX, mouseY);
					draw(s, graphics);
				});
				ScreenMouseEvents.allowMouseClick(screen).register(TutorialOverlay::click);
			}
		});
	}

	private static boolean hasButton(Screen screen) {
		return screen instanceof InventoryScreen && TutorialClient.data() != null;
	}

	private static boolean overButton(Screen screen, double mouseX, double mouseY) {
		int x = field(screen, "leftPos", (screen.width - 176) / 2) + BUTTON_X;
		int y = field(screen, "topPos", (screen.height - 166) / 2) + BUTTON_Y;
		return mouseX >= x && mouseX < x + BUTTON_W && mouseY >= y && mouseY < y + BUTTON_H;
	}

	private static void drawButton(Screen screen, GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
		if (!hasButton(screen)) {
			return;
		}
		int x = field(screen, "leftPos", (screen.width - 176) / 2) + BUTTON_X;
		int y = field(screen, "topPos", (screen.height - 166) / 2) + BUTTON_Y;
		boolean over = overButton(screen, mouseX, mouseY);
		graphics.fill(x, y, x + BUTTON_W, y + BUTTON_H, over ? 0xFFFFFFFF : 0xFF373737);
		graphics.fill(x + 1, y + 1, x + BUTTON_W - 1, y + BUTTON_H - 1, over ? 0xFFE0C070 : 0xFF8B8B8B);
		if (bookIcon.isEmpty()) {
			bookIcon = new ItemStack(Items.WRITABLE_BOOK); // Made lazily: never build an ItemStack in a static initializer.
		}
		graphics.fakeItem(bookIcon, x + 2, y + 1);
		if (over) {
			// Drawn straight away (a tooltip "for next frame" comes too late in afterExtract, see QuestTreePanel).
			graphics.tooltip(Minecraft.getInstance().font, List.of(
							ClientTooltipComponent.create(Component.literal("Voyage Log").withColor(GOLD).getVisualOrderText()),
							ClientTooltipComponent.create(Component.literal("Your First Voyage steps and tips").withColor(GRAY).getVisualOrderText())),
					mouseX, mouseY, DefaultTooltipPositioner.INSTANCE, null, false);
		}
	}

	/** Returns false when the click was ours, so the inventory doesn't also get it. */
	private static boolean click(Screen screen, MouseButtonEvent event) {
		if (event.button() != InputConstants.MOUSE_BUTTON_LEFT) {
			return true;
		}
		boolean onPanel = panelW > 0 && event.x() >= panelX && event.x() < panelX + panelW && event.y() >= panelY && event.y() < panelY + panelH;
		if ((hasButton(screen) && overButton(screen, event.x(), event.y())) || onPanel) {
			Minecraft.getInstance().gui.setScreen(new TutorialBookScreen(screen));
			return false;
		}
		return true;
	}

	private static void draw(Screen screen, GuiGraphicsExtractor graphics) {
		Minecraft client = Minecraft.getInstance();
		TutorialFeature.Sync data = TutorialClient.data();
		panelW = 0;
		if (data == null || data.off() || client.player == null) {
			return;
		}
		TutorialStep step = TutorialStep.at(data.step());
		boolean finished = step == null;
		// The "complete" panel shows for a little while, then goes away for good.
		if (finished && TutorialClient.ticksOnStep() > 20 * 60) {
			return;
		}
		Font font = client.font;

		int left = field(screen, "leftPos", (screen.width - 176) / 2);
		int top = field(screen, "topPos", (screen.height - 166) / 2);
		int imageWidth = field(screen, "imageWidth", 176);
		int imageHeight = field(screen, "imageHeight", 166);
		int tabs = screen instanceof CreativeModeInventoryScreen ? CREATIVE_TABS : 0;
		int width = Math.max(imageWidth, 176);
		int textWidth = width - PAD * 2 - 2;

		String header = finished ? "⚓ First Voyage" : "⚓ Part " + (step.part.ordinal() + 1) + ": " + step.part.title;
		String count = finished ? "done!" : (data.step() + 1) + "/" + TutorialStep.COUNT;
		String title = finished ? "You know the ropes. Fair winds!" : step.title
				+ (data.progress().isEmpty() ? "" : " (" + data.progress() + ")");
		List<FormattedCharSequence> titleLines = font.split(Component.literal(title), textWidth);
		List<FormattedCharSequence> hintLines = finished ? List.of()
				: font.split(Component.literal(step.hintText(TutorialClient::keyName)), textWidth);

		// Room above the inventory, or else below it. Drop the hint first if it doesn't fit.
		// The bounty poster (BountyBadge) sits right next to the inventory; this panel goes past it.
		int posterAbove = com.onepiecemod.bounty.client.BountyBadge.reservedAbove(screen);
		int posterBelow = com.onepiecemod.bounty.client.BountyBadge.reservedBelow(screen);
		int above = top - tabs - 4 - posterAbove;
		int below = screen.height - (top + imageHeight + tabs) - 4 - posterBelow;
		int room = Math.max(above, below);
		int fullHeight = height(titleLines.size(), hintLines.size());
		if (fullHeight > room) {
			hintLines = List.of();
		}
		int height = height(titleLines.size(), hintLines.size());
		if (height > room) {
			return; // A tiny window: no space without covering the inventory.
		}
		int x = left + (imageWidth - width) / 2;
		int y = above >= height ? top - tabs - 2 - posterAbove - height : top + imageHeight + tabs + 2 + posterBelow;

		panelX = x;
		panelY = y;
		panelW = width;
		panelH = height;
		graphics.fill(x - 1, y - 1, x + width + 1, y + height + 1, TRIM_DARK);
		graphics.fill(x, y, x + width, y + height, TRIM);
		graphics.fillGradient(x + 1, y + 1, x + width - 1, y + height - 1, BG_TOP, BG_BOTTOM);

		// A thin progress bar along the top.
		int done = finished ? TutorialStep.COUNT : data.step();
		graphics.fill(x + 1, y + 1, x + width - 1, y + 3, 0xFF203040);
		graphics.fill(x + 1, y + 1, x + 1 + (width - 2) * done / TutorialStep.COUNT, y + 3, GREEN);

		int textX = x + PAD + 1;
		int textY = y + PAD + 1;
		graphics.text(font, header, textX, textY, GOLD, true);
		graphics.text(font, count, x + width - PAD - 1 - font.width(count), textY, finished ? GREEN : GOLD, true);
		textY += ROW;
		for (FormattedCharSequence line : titleLines) {
			graphics.text(font, line, textX, textY, finished ? GREEN : WHITE, true);
			textY += ROW;
		}
		if (!hintLines.isEmpty()) {
			textY += 2;
			for (FormattedCharSequence line : hintLines) {
				graphics.text(font, line, textX, textY, GRAY, false);
				textY += 9;
			}
		}
	}

	private static int height(int titleLines, int hintLines) {
		return PAD * 2 + ROW + titleLines * ROW + (hintLines > 0 ? 2 + hintLines * 9 : 0);
	}

	/** leftPos, topPos, imageWidth and imageHeight aren't public, so they're read by reflection (like the quest tree panel). */
	private static int field(Screen screen, String name, int fallback) {
		try {
			Field field = AbstractContainerScreen.class.getDeclaredField(name);
			field.setAccessible(true);
			return field.getInt(screen);
		} catch (ReflectiveOperationException | RuntimeException e) {
			return fallback;
		}
	}
}
