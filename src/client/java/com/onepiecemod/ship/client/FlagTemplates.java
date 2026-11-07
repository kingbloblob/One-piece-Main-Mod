package com.onepiecemod.ship.client;

import java.util.Arrays;

import com.onepiecemod.ship.FlagDesign;

/**
 * Starting pictures for the paint screen. Each one is drawn at 32x32 with simple shapes,
 * then stretched to whatever size the player is painting at.
 */
public class FlagTemplates {
	public static final String[] NAMES = {"Straw Hat", "Skull & Bones", "Blank Black", "Blank White", "See-through"};

	// Palette slots used below (see FlagDesign.PALETTE).
	private static final int BLACK = FlagDesign.BLACK;
	private static final int WHITE = FlagDesign.WHITE;
	private static final int RED = 11;
	private static final int STRAW = 21;
	private static final int STRAW_DARK = 20;

	/** Makes the template with the given number, at the given resolution. */
	public static byte[] make(int template, int resolution) {
		byte[] small = new byte[32 * 32];
		switch (template) {
			case 0 -> {
				Arrays.fill(small, (byte) BLACK);
				crossbones(small);
				skull(small);
				strawHat(small);
			}
			case 1 -> {
				Arrays.fill(small, (byte) BLACK);
				crossbones(small);
				skull(small);
			}
			case 2 -> Arrays.fill(small, (byte) BLACK);
			case 3 -> Arrays.fill(small, (byte) WHITE);
			default -> Arrays.fill(small, (byte) 0);
		}
		return resize(small, 32, resolution);
	}

	/** Stretches or shrinks a picture to a new size, keeping the pixels sharp. */
	public static byte[] resize(byte[] pixels, int from, int to) {
		byte[] result = new byte[to * to];
		for (int y = 0; y < to; y++) {
			for (int x = 0; x < to; x++) {
				result[y * to + x] = pixels[(y * from / to) * from + (x * from / to)];
			}
		}
		return result;
	}

	private static void crossbones(byte[] p) {
		line(p, 5, 27, 26, 6, 1.6, WHITE);
		line(p, 5, 6, 26, 27, 1.6, WHITE);
		// Knobbly bone ends.
		for (int[] end : new int[][]{{5, 27}, {26, 6}, {5, 6}, {26, 27}}) {
			circle(p, end[0] - 1, end[1], 1.6, WHITE);
			circle(p, end[0] + 1, end[1] + (end[1] > 16 ? 1 : -1), 1.6, WHITE);
		}
	}

	private static void skull(byte[] p) {
		circle(p, 15.5, 15, 7.2, WHITE);
		rect(p, 12, 19, 19, 24, WHITE);
		// Eyes, nose and teeth.
		circle(p, 12.8, 15.5, 1.9, BLACK);
		circle(p, 18.2, 15.5, 1.9, BLACK);
		rect(p, 15, 18, 16, 19, BLACK);
		for (int x = 13; x <= 18; x += 2) {
			rect(p, x, 22, x, 24, BLACK);
		}
	}

	private static void strawHat(byte[] p) {
		rect(p, 5, 9, 26, 10, STRAW);      // brim
		rect(p, 6, 10, 25, 10, STRAW_DARK);
		rect(p, 10, 3, 21, 8, STRAW);      // crown
		rect(p, 11, 2, 20, 2, STRAW);
		rect(p, 10, 7, 21, 8, RED);        // the red band
	}

	private static void set(byte[] p, int x, int y, int colour) {
		if (x >= 0 && x < 32 && y >= 0 && y < 32) {
			p[y * 32 + x] = (byte) colour;
		}
	}

	private static void rect(byte[] p, int x0, int y0, int x1, int y1, int colour) {
		for (int y = y0; y <= y1; y++) {
			for (int x = x0; x <= x1; x++) {
				set(p, x, y, colour);
			}
		}
	}

	private static void circle(byte[] p, double cx, double cy, double r, int colour) {
		for (int y = 0; y < 32; y++) {
			for (int x = 0; x < 32; x++) {
				double dx = x + 0.5 - (cx + 0.5), dy = y + 0.5 - (cy + 0.5);
				if (dx * dx + dy * dy <= r * r) {
					set(p, x, y, colour);
				}
			}
		}
	}

	private static void line(byte[] p, double x0, double y0, double x1, double y1, double thickness, int colour) {
		int steps = 64;
		for (int i = 0; i <= steps; i++) {
			double t = i / (double) steps;
			circle(p, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, thickness, colour);
		}
	}
}
