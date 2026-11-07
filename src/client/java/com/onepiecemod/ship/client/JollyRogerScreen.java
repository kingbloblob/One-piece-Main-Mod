package com.onepiecemod.ship.client;

import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Deque;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.ship.FlagDesign;
import com.onepiecemod.ship.ShipPayloads;

/**
 * The Jolly Roger paint screen. Opens when you right-click the air holding a Jolly Roger.
 *
 * Left mouse paints with the chosen tool. Right mouse picks up the colour under the cursor.
 * The checkered colour is "see-through": paint with it to cut out any flag shape you like.
 */
public class JollyRogerScreen extends Screen {
	private static final int TOOL_BRUSH = 0, TOOL_FILL = 1, TOOL_PICK = 2;
	private static final String[] TOOL_NAMES = {"Brush", "Fill", "Pick colour"};
	private static final String[] STYLE_NAMES = {"Flag", "Sail", "Plaque"};
	private static final int SWATCH = 13;
	private static final int PALETTE_COLUMNS = 7;

	private final InteractionHand hand;
	private int resolution;
	private int size;
	private int style;
	private byte[] pixels;

	private int colour = FlagDesign.WHITE;
	private int tool = TOOL_BRUSH;
	private int brushSize = 1;
	private boolean mirror = false;
	private boolean grid = true;
	private int template = 0;
	private final Deque<byte[]> undo = new ArrayDeque<>();
	private boolean painting = false;

	// Where things are on screen. Worked out in init(), because it depends on the window size.
	private int canvasX, canvasY, cell;
	private int panelX, paletteY;

	public JollyRogerScreen(InteractionHand hand, FlagDesign design) {
		super(Component.literal("Jolly Roger"));
		this.hand = hand;
		this.resolution = design.resolution();
		this.size = design.size();
		this.style = design.style();
		this.pixels = design.copyPixels();
	}

	@Override
	protected void init() {
		int panelWidth = 2 * 74 + 2;
		int canvasSpace = Math.min(height - 36, width - panelWidth - 30);
		cell = Math.max(1, canvasSpace / resolution);
		int canvasSize = cell * resolution;
		canvasX = (width - canvasSize - 12 - panelWidth) / 2;
		canvasY = (height - canvasSize) / 2 + 6;
		panelX = canvasX + canvasSize + 12;
		paletteY = canvasY;

		clearWidgets();
		int rows = (FlagDesign.PALETTE.length + PALETTE_COLUMNS - 1) / PALETTE_COLUMNS;
		int y = paletteY + rows * SWATCH + 6;
		int left = panelX, right = panelX + 76, w = 74, h = 16, step = 18;

		addRenderableWidget(Button.builder(label("Tool", TOOL_NAMES[tool]), b -> {
			tool = (tool + 1) % TOOL_NAMES.length;
			b.setMessage(label("Tool", TOOL_NAMES[tool]));
		}).pos(left, y).size(w, h).build());
		addRenderableWidget(Button.builder(label("Brush", brushSize + "px"), b -> {
			brushSize = brushSize % 4 + 1;
			b.setMessage(label("Brush", brushSize + "px"));
		}).pos(right, y).size(w, h).build());
		y += step;

		addRenderableWidget(Button.builder(label("Mirror", mirror ? "On" : "Off"), b -> {
			mirror = !mirror;
			b.setMessage(label("Mirror", mirror ? "On" : "Off"));
		}).pos(left, y).size(w, h).build());
		addRenderableWidget(Button.builder(label("Grid", grid ? "On" : "Off"), b -> {
			grid = !grid;
			b.setMessage(label("Grid", grid ? "On" : "Off"));
		}).pos(right, y).size(w, h).build());
		y += step;

		addRenderableWidget(Button.builder(label("Style", STYLE_NAMES[style]), b -> {
			style = (style + 1) % STYLE_NAMES.length;
			b.setMessage(label("Style", STYLE_NAMES[style]));
		}).pos(left, y).size(w, h).build());
		addRenderableWidget(Button.builder(label("Size", size + "x" + size), b -> {
			size = size % 3 + 1;
			b.setMessage(label("Size", size + "x" + size));
		}).pos(right, y).size(w, h).build());
		y += step;

		addRenderableWidget(Button.builder(label("Detail", resolution + "px"), b -> {
			// Changing the detail stretches the current picture, and needs a new canvas layout.
			int next = nextResolution();
			saveUndo();
			pixels = FlagTemplates.resize(pixels, resolution, next);
			resolution = next;
			rebuildWidgets();
		}).pos(left, y).size(w, h).build());
		addRenderableWidget(Button.builder(label("Load", FlagTemplates.NAMES[template]), b -> {
			saveUndo();
			pixels = FlagTemplates.make(template, resolution);
			template = (template + 1) % FlagTemplates.NAMES.length;
			b.setMessage(label("Load", FlagTemplates.NAMES[template]));
		}).pos(right, y).size(w, h).build());
		y += step;

		addRenderableWidget(Button.builder(Component.literal("Undo"), b -> {
			if (!undo.isEmpty()) {
				byte[] previous = undo.pop();
				if (previous.length != pixels.length) {
					resolution = (int) Math.round(Math.sqrt(previous.length));
					pixels = previous;
					rebuildWidgets();
					return;
				}
				pixels = previous;
			}
		}).pos(left, y).size(w, h).build());
		addRenderableWidget(Button.builder(Component.literal("Clear"), b -> {
			saveUndo();
			Arrays.fill(pixels, (byte) colour);
		}).pos(right, y).size(w, h).build());
		y += step + 4;

		addRenderableWidget(Button.builder(Component.literal("Save"), b -> save())
				.pos(left, y).size(w, h + 2).build());
		addRenderableWidget(Button.builder(Component.literal("Cancel"), b -> onClose())
				.pos(right, y).size(w, h + 2).build());
	}

	private Component label(String name, String value) {
		return Component.literal(name + ": " + value);
	}

	private int nextResolution() {
		int[] options = FlagDesign.RESOLUTIONS;
		for (int i = 0; i < options.length; i++) {
			if (options[i] == resolution) {
				return options[(i + 1) % options.length];
			}
		}
		return 32;
	}

	private void save() {
		ClientPlayNetworking.send(new ShipPayloads.SaveDesign(hand == InteractionHand.OFF_HAND, new FlagDesign(resolution, size, style, pixels)));
		onClose();
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	// ---- Drawing the screen ----

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
		int canvasSize = cell * resolution;

		graphics.centeredText(font, "Paint your Jolly Roger  (left: paint, right: pick colour)", width / 2, 6, 0xFFFFFFFF);

		// See-through pixels show a checkerboard, like in paint programs.
		for (int y = 0; y < resolution; y++) {
			for (int x = 0; x < resolution; x++) {
				int px = canvasX + x * cell, py = canvasY + y * cell;
				int slot = pixels[y * resolution + x] & 0xFF;
				int argb = slot == 0 ? checker(x, y) : 0xFF000000 | FlagDesign.PALETTE[slot];
				graphics.fill(px, py, px + cell, py + cell, argb);
			}
		}
		if (grid && cell >= 4) {
			for (int i = 0; i <= resolution; i++) {
				graphics.fill(canvasX + i * cell, canvasY, canvasX + i * cell + 1, canvasY + canvasSize, 0x30FFFFFF);
				graphics.fill(canvasX, canvasY + i * cell, canvasX + canvasSize, canvasY + i * cell + 1, 0x30FFFFFF);
			}
		}
		if (mirror) {
			int middle = canvasX + canvasSize / 2;
			graphics.fill(middle, canvasY, middle + 1, canvasY + canvasSize, 0xA0FF4040);
		}
		// Show where the brush will paint.
		int[] hovered = pixelAt(mouseX, mouseY);
		if (hovered != null) {
			int offset = tool == TOOL_BRUSH ? (brushSize - 1) / 2 : 0;
			int span = tool == TOOL_BRUSH ? brushSize : 1;
			int px = canvasX + (hovered[0] - offset) * cell, py = canvasY + (hovered[1] - offset) * cell;
			outline(graphics, px, py, span * cell, span * cell, 0xFFFFFF00);
		}
		outline(graphics, canvasX - 1, canvasY - 1, canvasSize + 2, canvasSize + 2, 0xFF8B6B3D);

		// The colour palette.
		for (int slot = 0; slot < FlagDesign.PALETTE.length; slot++) {
			int sx = panelX + (slot % PALETTE_COLUMNS) * SWATCH;
			int sy = paletteY + (slot / PALETTE_COLUMNS) * SWATCH;
			if (slot == 0) {
				graphics.fill(sx, sy, sx + SWATCH - 1, sy + SWATCH - 1, 0xFFBFBFBF);
				graphics.fill(sx, sy, sx + 6, sy + 6, 0xFFFFFFFF);
				graphics.fill(sx + 6, sy + 6, sx + SWATCH - 1, sy + SWATCH - 1, 0xFFFFFFFF);
			} else {
				graphics.fill(sx, sy, sx + SWATCH - 1, sy + SWATCH - 1, 0xFF000000 | FlagDesign.PALETTE[slot]);
			}
			if (slot == colour) {
				outline(graphics, sx - 1, sy - 1, SWATCH + 1, SWATCH + 1, 0xFFFFFF00);
			}
		}
	}

	/** Draws a 1-pixel frame. */
	private static void outline(GuiGraphicsExtractor graphics, int x, int y, int w, int h, int colour) {
		graphics.fill(x, y, x + w, y + 1, colour);
		graphics.fill(x, y + h - 1, x + w, y + h, colour);
		graphics.fill(x, y + 1, x + 1, y + h - 1, colour);
		graphics.fill(x + w - 1, y + 1, x + w, y + h - 1, colour);
	}

	private static int checker(int x, int y) {
		return ((x + y) & 1) == 0 ? 0xFF9A9A9A : 0xFFC8C8C8;
	}

	// ---- Mouse ----

	@Override
	public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
		if (super.mouseClicked(event, doubleClick)) {
			return true;
		}
		double mx = event.x(), my = event.y();

		// Clicking the palette chooses a colour.
		int column = (int) Math.floor((mx - panelX) / SWATCH);
		int row = (int) Math.floor((my - paletteY) / SWATCH);
		int slot = row * PALETTE_COLUMNS + column;
		if (mx >= panelX && column < PALETTE_COLUMNS && row >= 0 && slot < FlagDesign.PALETTE.length) {
			colour = slot;
			return true;
		}

		int[] pixel = pixelAt(mx, my);
		if (pixel == null) {
			return false;
		}
		if (event.button() == 1 || tool == TOOL_PICK) {
			colour = pixels[pixel[1] * resolution + pixel[0]] & 0xFF;
			return true;
		}
		saveUndo();
		if (tool == TOOL_FILL) {
			fill(pixel[0], pixel[1]);
			if (mirror) {
				fill(resolution - 1 - pixel[0], pixel[1]);
			}
		} else {
			painting = true;
			paint(pixel[0], pixel[1]);
		}
		return true;
	}

	@Override
	public boolean mouseDragged(MouseButtonEvent event, double dragX, double dragY) {
		if (painting) {
			int[] pixel = pixelAt(event.x(), event.y());
			if (pixel != null) {
				paint(pixel[0], pixel[1]);
			}
			return true;
		}
		return super.mouseDragged(event, dragX, dragY);
	}

	@Override
	public boolean mouseReleased(MouseButtonEvent event) {
		painting = false;
		return super.mouseReleased(event);
	}

	/** The pixel under the mouse, or null if the mouse is not on the canvas. */
	private int[] pixelAt(double mx, double my) {
		int x = (int) Math.floor((mx - canvasX) / cell);
		int y = (int) Math.floor((my - canvasY) / cell);
		if (x < 0 || y < 0 || x >= resolution || y >= resolution) {
			return null;
		}
		return new int[]{x, y};
	}

	// ---- Painting ----

	private void saveUndo() {
		undo.push(pixels.clone());
		while (undo.size() > 40) {
			undo.removeLast();
		}
	}

	private void paint(int cx, int cy) {
		int offset = (brushSize - 1) / 2;
		for (int y = cy - offset; y < cy - offset + brushSize; y++) {
			for (int x = cx - offset; x < cx - offset + brushSize; x++) {
				set(x, y);
				if (mirror) {
					set(resolution - 1 - x, y);
				}
			}
		}
	}

	private void set(int x, int y) {
		if (x >= 0 && y >= 0 && x < resolution && y < resolution) {
			pixels[y * resolution + x] = (byte) colour;
		}
	}

	/** Paint bucket: recolour the whole patch of touching pixels that share a colour. */
	private void fill(int startX, int startY) {
		int target = pixels[startY * resolution + startX] & 0xFF;
		if (target == colour) {
			return;
		}
		Deque<int[]> toFill = new ArrayDeque<>();
		toFill.add(new int[]{startX, startY});
		while (!toFill.isEmpty()) {
			int[] p = toFill.poll();
			int x = p[0], y = p[1];
			if (x < 0 || y < 0 || x >= resolution || y >= resolution || (pixels[y * resolution + x] & 0xFF) != target) {
				continue;
			}
			pixels[y * resolution + x] = (byte) colour;
			toFill.add(new int[]{x + 1, y});
			toFill.add(new int[]{x - 1, y});
			toFill.add(new int[]{x, y + 1});
			toFill.add(new int[]{x, y - 1});
		}
	}
}
