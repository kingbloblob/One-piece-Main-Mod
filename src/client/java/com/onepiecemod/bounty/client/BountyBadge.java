package com.onepiecemod.bounty.client;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.client.gui.screens.inventory.tooltip.ClientTooltipComponent;
import net.minecraft.client.gui.screens.inventory.tooltip.DefaultTooltipPositioner;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;
import net.fabricmc.fabric.api.event.Event;

import com.onepiecemod.OnePieceMod;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.bounty.BountyFeature;
import com.onepiecemod.career.Career;
import com.onepiecemod.career.CareerPayloads;
import com.onepiecemod.career.client.CareerClient;
import com.onepiecemod.hud.HudPayload;
import com.onepiecemod.hud.client.HudClient;

/**
 * A small wanted poster in the inventory (ryan asked 2026-10-29): your bounty, Pirate Level and threat level, or your
 * rank for Marines (pardoned bounty) and Revolutionaries. Hover it for the details.
 * It sits under the inventory, or above it (between the inventory and the First Voyage panel) when there's no room below.
 * The quest tree is on the left and JEI on the right, so it stays in the middle like the guide panel.
 * The numbers come from the HUD payload, which the server sends twice a second even when the HUD is turned off.
 */
public class BountyBadge {
	public static final int HEIGHT = 24;
	private static final int WIDTH = 176;
	/** Creative mode's tabs stick out this far above and below its inventory. */
	private static final int CREATIVE_TABS = 30;

	private static final int BORDER = 0xFF4A2E12;
	private static final int PAPER_TOP = 0xFFF1E2B8;
	private static final int PAPER_BOTTOM = 0xFFD8BF88;
	private static final int INNER_LINE = 0xFFB08850;
	private static final int INK = 0xFF3B2410;
	private static final int BROWN = 0xFF6B4A22;
	private static final int RED = 0xFF9A1C14;
	private static final int MARINE_BLUE = 0xFF1F5A9A;
	private static final int REVOLUTIONARY_GREEN = 0xFF2E7D32;
	private static final int GOLD = 0xFFFFD75E;
	private static final int WHITE = 0xFFFFFFFF;
	private static final int GRAY = 0xFFC8D0DA;

	private static final Identifier LATE = OnePieceMod.id("bounty_badge_tooltip");
	private static ItemStack posterIcon = ItemStack.EMPTY;
	/** Where the poster was last drawn, for the hover text; width 0 when hidden. */
	private static int lastX, lastY, lastW, lastH;

	/** A one-line poster for small windows (creative's tabs leave little room at GUI scale 3). */
	public static final int SMALL_HEIGHT = 13;

	public enum Place {
		BELOW(false, HEIGHT), ABOVE(true, HEIGHT), BELOW_SMALL(false, SMALL_HEIGHT), ABOVE_SMALL(true, SMALL_HEIGHT), NONE(false, 0);

		final boolean above;
		final int height;

		Place(boolean above, int height) {
			this.above = above;
			this.height = height;
		}
	}

	static void initialize() {
		ScreenEvents.AFTER_INIT.register((client, screen, scaledWidth, scaledHeight) -> {
			if (screen instanceof InventoryScreen || screen instanceof CreativeModeInventoryScreen) {
				var event = ScreenEvents.afterExtract(screen);
				event.register((s, graphics, mouseX, mouseY, tick) -> draw(s, graphics, mouseX, mouseY));
				// The hover text goes last, so the quest tree panel (drawn after us) doesn't cover it.
				event.addPhaseOrdering(Event.DEFAULT_PHASE, LATE);
				event.register(LATE, (s, graphics, mouseX, mouseY, tick) -> drawTooltip(s, graphics, mouseX, mouseY));
			}
		});
	}

	private static boolean shown() {
		return HudClient.data() != null && Minecraft.getInstance().player != null;
	}

	/** Where the poster goes in this screen. The First Voyage panel asks too, so the two never overlap. */
	public static Place place(Screen screen) {
		if (!(screen instanceof InventoryScreen || screen instanceof CreativeModeInventoryScreen) || !shown()) {
			return Place.NONE;
		}
		int tabs = screen instanceof CreativeModeInventoryScreen ? CREATIVE_TABS : 0;
		int top = field(screen, "topPos", (screen.height - 166) / 2);
		int bottom = top + field(screen, "imageHeight", 166) + tabs;
		int below = screen.height - bottom - 2;
		int above = top - tabs - 2;
		for (Place place : Place.values()) {
			if (place != Place.NONE && (place.above ? above : below) >= place.height + 2) {
				return place;
			}
		}
		return Place.NONE;
	}

	/** Space the poster takes above the inventory (for the First Voyage panel). */
	public static int reservedAbove(Screen screen) {
		Place place = place(screen);
		return place != Place.NONE && place.above ? place.height + 2 : 0;
	}

	/** Space the poster takes below the inventory (for the First Voyage panel). */
	public static int reservedBelow(Screen screen) {
		Place place = place(screen);
		return place != Place.NONE && !place.above ? place.height + 2 : 0;
	}

	private static void draw(Screen screen, GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
		Place place = place(screen);
		lastW = 0;
		if (place == Place.NONE) {
			return;
		}
		Minecraft client = Minecraft.getInstance();
		Font font = client.font;
		HudPayload hud = HudClient.data();
		CareerPayloads.Sync careerData = CareerClient.data();
		Career career = careerData == null ? Career.PIRATE : Career.byId(careerData.career());
		Career.Rank rank = careerData == null ? null : career.rank(careerData.rank());
		boolean pardoned = career == Career.MARINE;

		int tabs = screen instanceof CreativeModeInventoryScreen ? CREATIVE_TABS : 0;
		int left = field(screen, "leftPos", (screen.width - 176) / 2);
		int top = field(screen, "topPos", (screen.height - 166) / 2);
		int imageWidth = field(screen, "imageWidth", 176);
		int imageHeight = field(screen, "imageHeight", 166);
		int x = left + (imageWidth - WIDTH) / 2;
		int height = place.height;
		int y = place.above ? top - tabs - 2 - height : top + imageHeight + tabs + 2;
		lastX = x;
		lastY = y;
		lastW = WIDTH;
		lastH = height;

		// Old paper with a dark edge and a thin inner line, like a wanted poster.
		graphics.fill(x, y, x + WIDTH, y + height, BORDER);
		graphics.fillGradient(x + 1, y + 1, x + WIDTH - 1, y + height - 1, PAPER_TOP, PAPER_BOTTOM);
		if (height == SMALL_HEIGHT) {
			drawSmall(graphics, font, hud, pardoned, x, y);
			return;
		}
		graphics.fill(x + 2, y + 2, x + WIDTH - 2, y + 3, INNER_LINE);
		graphics.fill(x + 2, y + height - 3, x + WIDTH - 2, y + height - 2, INNER_LINE);

		if (posterIcon.isEmpty()) {
			posterIcon = new ItemStack(BountyFeature.BOUNTY_POSTER); // Made lazily: never build an ItemStack in a static initializer.
		}
		graphics.fakeItem(posterIcon, x + 4, y + 4);

		int textX = x + 24;
		int right = x + WIDTH - 5;
		// Line 1: WANTED (drawn twice for bold), your name, and your Pirate Level on the right.
		String level = "Lv " + hud.pirateLevel();
		int levelX = right - font.width(level);
		graphics.text(font, "WANTED", textX, y + 4, INK, false);
		graphics.text(font, "WANTED", textX + 1, y + 4, INK, false);
		int nameX = textX + font.width("WANTED") + 5;
		String name = font.plainSubstrByWidth(client.player.getName().getString(), Math.max(0, levelX - nameX - 4));
		graphics.text(font, name, nameX, y + 4, BROWN, false);
		graphics.text(font, level, levelX, y + 4, INK, false);

		// Line 2: the bounty (or "Pardoned" for Marines), and the rank or threat level on the right.
		String tag;
		int tagColor;
		if (career == Career.MARINE && rank != null) {
			tag = rank.name();
			tagColor = MARINE_BLUE;
		} else if (career == Career.REVOLUTIONARY && rank != null) {
			tag = rank.name();
			tagColor = REVOLUTIONARY_GREEN;
		} else {
			tag = Bounty.levelName(Bounty.threatLevel(hud.bounty()));
			tagColor = BROWN;
		}
		int tagX = right - font.width(tag);
		String amount = pardoned ? "Pardoned" : Bounty.format(hud.bounty());
		if (textX + font.width(amount) + 4 > tagX) {
			amount = pardoned ? amount : String.format("%,d", hud.bounty()); // Drop the word "Berries" when it's crowded.
		}
		graphics.text(font, amount, textX, y + 14, pardoned ? MARINE_BLUE : RED, false);
		if (textX + font.width(amount) + 4 <= tagX) {
			graphics.text(font, tag, tagX, y + 14, tagColor, false);
		}

	}

	/** One line: WANTED, the bounty (or Pardoned) and the Pirate Level. Hover for the rest. */
	private static void drawSmall(GuiGraphicsExtractor graphics, Font font, HudPayload hud, boolean pardoned, int x, int y) {
		int textX = x + 5;
		graphics.text(font, "WANTED", textX, y + 3, INK, false);
		graphics.text(font, "WANTED", textX + 1, y + 3, INK, false);
		String level = "Lv " + hud.pirateLevel();
		graphics.text(font, level, x + WIDTH - 5 - font.width(level), y + 3, INK, false);
		String amount = pardoned ? "Pardoned" : Bounty.format(hud.bounty());
		int amountX = textX + font.width("WANTED") + 6;
		if (amountX + font.width(amount) + 4 > x + WIDTH - 5 - font.width(level)) {
			amount = String.format("%,d", hud.bounty());
		}
		graphics.text(font, amount, amountX, y + 3, pardoned ? MARINE_BLUE : RED, false);
	}

	private static void drawTooltip(Screen screen, GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
		if (place(screen) == Place.NONE || lastW == 0
				|| mouseX < lastX || mouseX >= lastX + lastW || mouseY < lastY || mouseY >= lastY + lastH) {
			return;
		}
		CareerPayloads.Sync careerData = CareerClient.data();
		Career career = careerData == null ? Career.PIRATE : Career.byId(careerData.career());
		Career.Rank rank = careerData == null ? null : career.rank(careerData.rank());
		// Drawn straight away (a tooltip "for next frame" comes too late in afterExtract, see QuestTreePanel).
		graphics.tooltip(Minecraft.getInstance().font, tooltip(HudClient.data(), career, rank), mouseX, mouseY,
				DefaultTooltipPositioner.INSTANCE, null, false);
	}

	private static List<ClientTooltipComponent> tooltip(HudPayload hud, Career career, Career.Rank rank) {
		List<Component> lines = new ArrayList<>();
		lines.add(Component.literal("Wanted Poster").withColor(GOLD));
		if (career == Career.MARINE) {
			lines.add(Component.literal("Bounty: pardoned (you're a Marine)").withColor(WHITE));
		} else {
			int threat = Bounty.threatLevel(hud.bounty());
			lines.add(Component.literal("Bounty: " + Bounty.format(hud.bounty())).withColor(WHITE));
			lines.add(Component.literal("Threat: " + Bounty.levelName(threat)).withColor(WHITE));
			lines.add(Component.literal(Bounty.levelDescription(threat)).withColor(GRAY));
		}
		lines.add(Component.literal("Pirate Level " + hud.pirateLevel()
				+ (hud.levelXpNeeded() > 0 ? " (" + hud.levelXp() + "/" + hud.levelXpNeeded() + " XP)" : "")).withColor(WHITE));
		if (career != Career.PIRATE && rank != null) {
			lines.add(Component.literal(career.displayName + ": " + rank.name()).withColor(career == Career.MARINE ? 0xFF55C8FF : 0xFF62E07A));
		}
		lines.add(Component.literal("/bounty for more").withColor(0xFF8A939E));
		List<ClientTooltipComponent> out = new ArrayList<>();
		for (Component line : lines) {
			out.add(ClientTooltipComponent.create(line.getVisualOrderText()));
		}
		return out;
	}

	/** leftPos, topPos, imageWidth and imageHeight aren't public, so they're read by reflection (like the guide panel). */
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
