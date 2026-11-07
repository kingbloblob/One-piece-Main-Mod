package com.onepiecemod.questtree.client;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;

import com.mojang.blaze3d.platform.InputConstants;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.inventory.tooltip.ClientTooltipComponent;
import net.minecraft.client.gui.screens.inventory.tooltip.DefaultTooltipPositioner;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;
import net.fabricmc.fabric.api.client.screen.v1.ScreenMouseEvents;

import com.onepiecemod.character.CharacterData;
import com.onepiecemod.questtree.QuestTreeFeature;

/**
 * The quest tree in the empty space to the left of the inventory (survival and creative).
 * The recipe viewer's item list is on the right, so the two never overlap.
 *
 * - "Story" and "Quests" at the top switch between the story and the character quest lines.
 * - Click a line to open it up (or close it). Scroll the mouse wheel over the tree to see more.
 * - Hover a line to see its details: the goals, the story text, rewards, where to find a character.
 * - "x" hides the panel; the "Quests" tab in the top left corner brings it back. J still opens the big screen.
 * - The quest book icon in the top left corner opens the big screen too (it stays there when the panel is hidden).
 *
 * Each time the inventory opens it asks the server for your latest progress. OnePieceModClient calls initialize()
 * (through QuestTreeClient).
 */
public class QuestTreePanel {
	private static final int TOP = 18;
	private static final int MAX_WIDTH = 180;
	private static final int MIN_WIDTH = 90;
	/** Width of the vanilla recipe book, which sits left of the survival inventory when it's open. */
	private static final int RECIPE_BOOK_WIDTH = 147;
	private static final int TOOLTIP_WIDTH = 200;
	private static final int TOOLTIP_LINES = 18;
	/** Room the quest book icon takes at the left of the header. */
	private static final int BOOK = 18;
	private static ItemStack bookIcon;

	private static boolean visible = true;
	private static QuestTree tree;
	/** The progress the panel shows, so the quest book can open the big screen straight away. */
	private static QuestTreeFeature.Open lastData;
	/** True while we wait for the server's answer, so it fills the panel instead of opening the big screen. */
	static boolean waiting = false;

	static void initialize() {
		ScreenEvents.AFTER_INIT.register((client, screen, scaledWidth, scaledHeight) -> {
			if (!(screen instanceof InventoryScreen || screen instanceof CreativeModeInventoryScreen)
					|| !com.onepiecemod.questlog.client.ClientConfig.inventoryQuestPanel()) { // Screen setting: inventory_quest_panel.
				return;
			}
			if (!waiting) {
				waiting = true;
				ClientPlayNetworking.send(QuestTreeFeature.Request.INSTANCE);
			}
			ScreenEvents.afterExtract(screen).register((s, graphics, mouseX, mouseY, tick) -> draw(s, graphics, mouseX, mouseY));
			ScreenMouseEvents.allowMouseClick(screen).register(QuestTreePanel::click);
			ScreenMouseEvents.allowMouseScroll(screen).register((s, mouseX, mouseY, h, v) -> scroll(s, mouseX, mouseY, v));
		});
	}

	/** The server's answer arrived. */
	static void receive(QuestTreeFeature.Open data) {
		waiting = false;
		lastData = data;
		QuestTree fresh = new QuestTree(data);
		if (tree != null) {
			fresh.scroll = tree.scroll; // Keep the place you scrolled to.
		}
		tree = fresh;
	}

	// ---- Where the panel goes: the space to the left of the inventory ----

	private record Layout(int x, int width) {}

	private static Layout layout(Screen screen) {
		int right = containerLeft(screen) - 6;
		int centered = (screen.width - imageWidth(screen)) / 2;
		if (screen instanceof InventoryScreen && containerLeft(screen) > centered + 20) {
			right -= RECIPE_BOOK_WIDTH; // The recipe book is open, on the left.
		}
		int width = Math.min(MAX_WIDTH, right - 4);
		return width < MIN_WIDTH ? null : new Layout(right - width, width);
	}

	private static Field leftPosField, imageWidthField;

	private static int containerLeft(Screen screen) {
		try {
			findFields();
			return leftPosField.getInt(screen);
		} catch (ReflectiveOperationException | RuntimeException e) {
			return (screen.width - imageWidth(screen)) / 2;
		}
	}

	private static int imageWidth(Screen screen) {
		try {
			findFields();
			return imageWidthField.getInt(screen);
		} catch (ReflectiveOperationException | RuntimeException e) {
			return screen instanceof CreativeModeInventoryScreen ? 195 : 176;
		}
	}

	/** leftPos and imageWidth aren't public, so we read them by reflection (like the recipe viewer does). */
	private static void findFields() throws ReflectiveOperationException {
		if (leftPosField == null) {
			leftPosField = AbstractContainerScreen.class.getDeclaredField("leftPos");
			leftPosField.setAccessible(true);
			imageWidthField = AbstractContainerScreen.class.getDeclaredField("imageWidth");
			imageWidthField.setAccessible(true);
		}
	}

	// ---- Drawing ----

	private static void draw(Screen screen, GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
		Font font = Minecraft.getInstance().font;
		if (!visible) {
			drawBook(graphics, font, 4, mouseX, mouseY);
			int w = font.width("Quests") + 8;
			boolean over = mouseX >= 4 + BOOK && mouseX < 4 + BOOK + w && mouseY >= 4 && mouseY < 18;
			graphics.fill(4 + BOOK, 4, 4 + BOOK + w, 18, over ? 0xC0403020 : 0xA0201A14);
			graphics.text(font, "Quests", 8 + BOOK, 7, over ? QuestTree.WHITE : QuestTree.YELLOW);
			return;
		}
		Layout layout = layout(screen);
		if (layout == null) {
			// No room for the panel, but the book still opens the big screen.
			drawBook(graphics, font, 4, mouseX, mouseY);
			return;
		}
		int right = layout.x + layout.width;

		// Header: the quest book, the two tabs and the hide button.
		drawBook(graphics, font, layout.x, mouseX, mouseY);
		boolean story = QuestTree.storyTab();
		int questsX = layout.x + BOOK + font.width("Story") + 8;
		graphics.text(font, "Story", layout.x + BOOK + 2, 6, story ? QuestTree.YELLOW : overStory(layout, font, mouseX, mouseY) ? QuestTree.WHITE : QuestTree.GREY);
		graphics.text(font, "Quests", questsX, 6, !story ? QuestTree.YELLOW : overQuests(layout, font, mouseX, mouseY) ? QuestTree.WHITE : QuestTree.GREY);
		graphics.fill(story ? layout.x + BOOK + 2 : questsX, 15, (story ? layout.x + BOOK + 2 + font.width("Story") : questsX + font.width("Quests")), 16, QuestTree.YELLOW);
		graphics.text(font, "x", right - 6, 6, overHide(layout, mouseX, mouseY) ? QuestTree.WHITE : QuestTree.GREY);

		int bottom = screen.height - 16;
		if (tree == null) {
			QuestTree.box(graphics, layout.x, TOP, layout.width, bottom - TOP);
			graphics.text(font, "Loading...", layout.x + 6, TOP + 6, QuestTree.GREY);
			return;
		}
		tree.drawTree(graphics, font, layout.x, TOP, layout.width, bottom - TOP, mouseX, mouseY);
		graphics.text(font, QuestTree.shorten(font, "Hover for details · J: big view", layout.width), layout.x + 2, bottom + 4, QuestTree.DARK);

		// Hovering a line shows its details.
		if (tree.hovered != null) {
			List<FormattedCharSequence> lines = new ArrayList<>();
			if (tree.hoveredCut) {
				// The line was cut off in the panel, so the tooltip starts with its full text.
				lines.addAll(font.split(Component.literal(tree.hovered.label).withColor(QuestTree.WHITE), TOOLTIP_WIDTH));
				lines.add(FormattedCharSequence.EMPTY);
			}
			lines.addAll(tree.detailLines(font, tree.hovered, TOOLTIP_WIDTH));
			if (lines.size() > TOOLTIP_LINES) {
				lines = lines.subList(0, TOOLTIP_LINES);
			}
			// Drawn straight away: a tooltip set "for next frame" here comes after the inventory has already drawn its tooltips, so it never showed.
			graphics.tooltip(font, lines.stream().map(ClientTooltipComponent::create).toList(), mouseX, mouseY,
					DefaultTooltipPositioner.INSTANCE, null, false);
		}
	}

	/** The quest book icon: a Captain's Log in a small frame. Clicking it opens the big quest tree screen. */
	private static void drawBook(GuiGraphicsExtractor graphics, Font font, int x, int mouseX, int mouseY) {
		if (bookIcon == null) {
			bookIcon = CharacterData.stack("onepiece:captains_log", 1);
			if (bookIcon.isEmpty()) {
				bookIcon = new ItemStack(Items.WRITABLE_BOOK);
			}
		}
		boolean over = overBook(x, mouseX, mouseY);
		graphics.fill(x, 0, x + BOOK - 1, BOOK - 1, over ? 0xC0604828 : 0xA0201A14);
		graphics.fill(x, BOOK - 2, x + BOOK - 1, BOOK - 1, over ? QuestTree.YELLOW : QuestTree.BORDER);
		graphics.fakeItem(bookIcon, x + 1, 0);
		if (over) {
			graphics.tooltip(font, List.of(
							ClientTooltipComponent.create(Component.literal("Quest Book").withColor(QuestTree.YELLOW).getVisualOrderText()),
							ClientTooltipComponent.create(Component.literal("Click to open the quest tree (J)").withColor(QuestTree.GREY).getVisualOrderText())),
					mouseX, BOOK + 14, DefaultTooltipPositioner.INSTANCE, null, false); // Below the icon, not over the tabs.
		}
	}

	private static boolean overBook(int x, double mx, double my) {
		return mx >= x && mx < x + BOOK - 1 && my >= 0 && my < BOOK - 1;
	}

	/** Swaps the inventory for the big quest tree screen, using the progress the panel already has. */
	private static void openBigScreen() {
		if (lastData != null) {
			// Next frame, so the inventory finishes handling this click first.
			QuestTreeFeature.Open data = lastData;
			Minecraft.getInstance().execute(() -> Minecraft.getInstance().gui.setScreen(new QuestTreeScreen(data)));
			return;
		}
		waiting = false;
		ClientPlayNetworking.send(QuestTreeFeature.Request.INSTANCE);
	}

	private static boolean overStory(Layout layout, Font font, double mx, double my) {
		return my >= 3 && my < 16 && mx >= layout.x + BOOK && mx < layout.x + BOOK + font.width("Story") + 6;
	}

	private static boolean overQuests(Layout layout, Font font, double mx, double my) {
		int x = layout.x + BOOK + font.width("Story") + 6;
		return my >= 3 && my < 16 && mx >= x && mx < x + font.width("Quests") + 6;
	}

	private static boolean overHide(Layout layout, double mx, double my) {
		int right = layout.x + layout.width;
		return my >= 3 && my < 16 && mx >= right - 9 && mx < right;
	}

	// ---- Mouse ----

	/** Returns false when the click was ours, so the inventory doesn't also get it. */
	private static boolean click(Screen screen, MouseButtonEvent event) {
		double mx = event.x(), my = event.y();
		Font font = Minecraft.getInstance().font;
		Layout layout = visible ? layout(screen) : null;
		if (event.button() == InputConstants.MOUSE_BUTTON_LEFT && overBook(layout != null ? layout.x : 4, mx, my)) {
			openBigScreen();
			return false;
		}
		if (!visible) {
			if (mx >= 4 + BOOK && mx < 12 + BOOK + font.width("Quests") && my >= 4 && my < 18) {
				visible = true;
				return false;
			}
			return true;
		}
		if (layout == null || mx < layout.x || mx >= layout.x + layout.width) {
			return true;
		}
		if (overHide(layout, mx, my)) {
			visible = false;
			return false;
		}
		if (tree != null && overStory(layout, font, mx, my)) {
			tree.switchTab(true);
			return false;
		}
		if (tree != null && overQuests(layout, font, mx, my)) {
			tree.switchTab(false);
			return false;
		}
		if (tree != null && event.button() == InputConstants.MOUSE_BUTTON_LEFT && tree.click(mx, my)) {
			return false;
		}
		return true;
	}

	private static boolean scroll(Screen screen, double mx, double my, double amount) {
		if (!visible || tree == null || amount == 0 || !tree.isOverTree(mx, my)) {
			return true;
		}
		tree.scroll(-(int) Math.signum(amount) * 3);
		return false;
	}
}
