package com.onepiecemod.hud.client;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import net.minecraft.client.KeyMapping;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.options.controls.KeyBindsScreen;
import net.minecraft.client.resources.language.I18n;
import net.minecraft.network.chat.Component;

/**
 * "One Piece Keys": every key the mod adds, grouped like in Options > Controls, with what it does.
 * It reads the real key binds, so keys added later show up by themselves. A key that another
 * key also uses is shown in red with the name of the other one. Opened from the pause menu.
 */
public class KeysScreen extends Screen {
	private static final int ROW = 12;
	private static final int MAX_WIDTH = 340;
	private static final int TOP = 32;

	private static final int GOLD = 0xFFFFD75E;
	private static final int WHITE = 0xFFF4EBDD;
	private static final int GRAY = 0xFFA8B0C0;
	private static final int RED = 0xFFFF6B6B;
	private static final int KEY = 0xFFC9A86A;

	/** A little extra help for keys whose name doesn't tell the whole story. */
	private static final Map<String, String> NOTES = Map.of(
			"key.onepiece.use_fruit_power", "Hold Sneak too for your second move",
			"key.onepiece.awaken_fruit", "Only once your fruit is awakened",
			"key.onepiece.conquerors_haki", "Only once you have Conqueror's Haki",
			"key.onepiece.fire_cannons", "While aboard a ship with cannons");

	private final Screen parent;
	private final List<Line> lines = new ArrayList<>();
	private int scroll;
	private int panelX;
	private int panelWidth;
	private int visibleRows;

	/** One row: a group heading, or a key with what it does. */
	private record Line(String heading, String key, String text, String note, boolean clash) {
	}

	public KeysScreen(Screen parent) {
		super(Component.literal("One Piece Keys"));
		this.parent = parent;
	}

	@Override
	protected void init() {
		lines.clear();
		KeyMapping[] all = minecraft.options.keyMappings.clone();
		java.util.Arrays.sort(all); // The same order as Options > Controls.
		KeyMapping.Category group = null;
		for (KeyMapping mapping : all) {
			if (!mapping.getCategory().id().getNamespace().startsWith("onepiece")) {
				continue;
			}
			if (!mapping.getCategory().equals(group)) {
				group = mapping.getCategory();
				lines.add(new Line(group.label().getString().replace("One Piece: ", ""), null, null, null, false));
			}
			String clashWith = null;
			if (!mapping.isUnbound()) {
				for (KeyMapping other : all) {
					// Debug keys only work while F3 is held, so sharing a letter with them is fine.
					if (other != mapping && other.getCategory() != KeyMapping.Category.DEBUG && other.same(mapping)) {
						clashWith = I18n.get(other.getName());
						break;
					}
				}
			}
			String note = clashWith != null ? "Also used by: " + clashWith : NOTES.get(mapping.getName());
			String key = mapping.isUnbound() ? "-" : keyName(mapping);
			lines.add(new Line(null, key, I18n.get(mapping.getName()), note, clashWith != null));
		}
		// Keys every player uses with the mod, from vanilla.
		lines.add(new Line("Also handy", null, null, null, false));
		lines.add(new Line(null, keyName(minecraft.options.keyUse), "Talk to characters, use guns and items", null, false));
		lines.add(new Line(null, keyName(minecraft.options.keyShift), "Sneak: hold with a move key for its other version", null, false));

		panelWidth = Math.min(MAX_WIDTH, width - 20);
		panelX = (width - panelWidth) / 2;
		visibleRows = Math.max(3, (height - TOP - 36) / ROW);
		scroll = Math.max(0, Math.min(scroll, maxScroll()));

		int half = Math.min(150, (panelWidth - 4) / 2);
		addRenderableWidget(Button.builder(Component.literal("Change keys..."),
				b -> minecraft.gui.setScreen(new KeyBindsScreen(this, minecraft.options)))
				.pos(width / 2 - half - 2, height - 26).size(half, 20).build());
		addRenderableWidget(Button.builder(Component.literal("Done"), b -> onClose())
				.pos(width / 2 + 2, height - 26).size(half, 20).build());
	}

	/** "Left Shift" becomes "Shift", like on the HUD. */
	private static String keyName(KeyMapping mapping) {
		return mapping.getTranslatedKeyMessage().getString().replaceAll("^(Left|Right) (Shift|Ctrl|Control|Alt)", "$2");
	}

	private int rowsUsed() {
		int rows = 0;
		for (Line line : lines) {
			rows += line.note != null ? 2 : 1;
		}
		return rows;
	}

	private int maxScroll() {
		return Math.max(0, rowsUsed() - visibleRows);
	}

	@Override
	public void onClose() {
		minecraft.gui.setScreen(parent);
	}

	@Override
	public boolean mouseScrolled(double mouseX, double mouseY, double scrollX, double scrollY) {
		scroll = Math.max(0, Math.min(maxScroll(), scroll - (int) Math.signum(scrollY)));
		return true;
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
		graphics.centeredText(font, "One Piece Keys", width / 2, 8, GOLD);
		graphics.centeredText(font, maxScroll() > 0 ? "Scroll for more. Red = two keys share one button."
				: "Red = two keys share one button.", width / 2, 19, GRAY);

		int top = TOP;
		int bottom = top + visibleRows * ROW;
		graphics.fill(panelX - 4, top - 4, panelX + panelWidth + 4, bottom + 2, 0xB0140E08);
		graphics.outline(panelX - 4, top - 4, panelWidth + 8, bottom - top + 6, 0xFFC8A040);

		int keyColumn = 0;
		for (Line line : lines) {
			if (line.key != null) {
				keyColumn = Math.max(keyColumn, font.width(line.key) + 8);
			}
		}
		keyColumn = Math.min(keyColumn, 80);

		graphics.enableScissor(panelX - 2, top - 2, panelX + panelWidth + 2, bottom);
		int y = top - scroll * ROW;
		for (Line line : lines) {
			if (line.heading != null) {
				graphics.text(font, line.heading, panelX, y + 2, GOLD, true);
				y += ROW;
				continue;
			}
			int w = Math.min(font.width(line.key) + 4, keyColumn - 4);
			graphics.fill(panelX + 4, y, panelX + 4 + w, y + 10, 0xFF3A2C10);
			graphics.outline(panelX + 4, y, w, 10, line.clash ? RED : KEY);
			graphics.text(font, font.plainSubstrByWidth(line.key, w - 4), panelX + 6, y + 1, line.clash ? RED : 0xFFFFE9B8, false);
			int textX = panelX + 4 + keyColumn + 2;
			int room = panelX + panelWidth - textX;
			graphics.text(font, font.plainSubstrByWidth(line.text, room), textX, y + 1, WHITE, false);
			y += ROW;
			if (line.note != null) {
				graphics.text(font, font.plainSubstrByWidth(line.note, room), textX, y, line.clash ? RED : GRAY, false);
				y += ROW;
			}
		}
		graphics.disableScissor();
	}
}
