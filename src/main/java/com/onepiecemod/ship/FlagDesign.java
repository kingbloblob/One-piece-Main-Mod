package com.onepiecemod.ship;

import java.nio.ByteBuffer;
import java.util.Arrays;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;

/**
 * A player-painted picture: a Jolly Roger, a sail or a wall plaque.
 *
 * The picture is a square grid of pixels. Each pixel is a number that points into {@link #PALETTE}.
 * Number 0 means "see-through", so players can paint torn edges, pennants or any shape they like.
 *
 * - resolution: pixels per side (16, 32 or 64)
 * - size: how many blocks wide it is when placed (1, 2 or 3)
 * - style: how it hangs (FLAG, SAIL or PLAQUE)
 */
public final class FlagDesign {
	public static final int STYLE_FLAG = 0;   // Sticks out sideways from a pole or mast and waves.
	public static final int STYLE_SAIL = 1;   // Hangs down from the block, facing forward, and puffs out.
	public static final int STYLE_PLAQUE = 2; // Lies flat against a wall, like a painting.

	public static final int[] RESOLUTIONS = {16, 32, 64};

	/** All the colours you can paint with, as 0xRRGGBB. Slot 0 is see-through. */
	public static final int[] PALETTE = buildPalette();

	public static final Codec<FlagDesign> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.INT.fieldOf("resolution").forGetter(FlagDesign::resolution),
			Codec.INT.fieldOf("size").forGetter(FlagDesign::size),
			Codec.INT.fieldOf("style").forGetter(FlagDesign::style),
			Codec.BYTE_BUFFER.fieldOf("pixels").forGetter(design -> ByteBuffer.wrap(design.pixels))
	).apply(instance, (resolution, size, style, buffer) -> {
		byte[] bytes = new byte[buffer.remaining()];
		buffer.duplicate().get(bytes);
		return new FlagDesign(resolution, size, style, bytes);
	}));

	public static final StreamCodec<ByteBuf, FlagDesign> STREAM_CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, FlagDesign::resolution,
			ByteBufCodecs.VAR_INT, FlagDesign::size,
			ByteBufCodecs.VAR_INT, FlagDesign::style,
			ByteBufCodecs.BYTE_ARRAY, design -> design.pixels,
			FlagDesign::new
	);

	private final int resolution;
	private final int size;
	private final int style;
	private final byte[] pixels;

	public FlagDesign(int resolution, int size, int style, byte[] pixels) {
		// Clean up whatever we were given, so a broken or hacked design can't crash anything.
		this.resolution = Arrays.stream(RESOLUTIONS).anyMatch(r -> r == resolution) ? resolution : 32;
		this.size = Math.clamp(size, 1, 3);
		this.style = Math.clamp(style, STYLE_FLAG, STYLE_PLAQUE);
		this.pixels = new byte[this.resolution * this.resolution];
		if (pixels != null) {
			System.arraycopy(pixels, 0, this.pixels, 0, Math.min(pixels.length, this.pixels.length));
		}
		for (int i = 0; i < this.pixels.length; i++) {
			if ((this.pixels[i] & 0xFF) >= PALETTE.length) {
				this.pixels[i] = 0;
			}
		}
	}

	/** A blank black flag, the classic starting point for a Jolly Roger. */
	public static FlagDesign blank() {
		byte[] pixels = new byte[32 * 32];
		Arrays.fill(pixels, (byte) BLACK);
		return new FlagDesign(32, 1, STYLE_FLAG, pixels);
	}

	public int resolution() {
		return resolution;
	}

	public int size() {
		return size;
	}

	public int style() {
		return style;
	}

	/** The colour slot at a pixel. x goes left to right, y goes top to bottom. */
	public int get(int x, int y) {
		return pixels[y * resolution + x] & 0xFF;
	}

	/** A copy of the pixel slots, for the paint screen to edit. */
	public byte[] copyPixels() {
		return pixels.clone();
	}

	/** The colour of a pixel as 0xAARRGGBB, ready to put in a texture. */
	public int argb(int x, int y) {
		int slot = get(x, y);
		return slot == 0 ? 0 : 0xFF000000 | PALETTE[slot];
	}

	// Two designs with the same picture count as the same, so they stack in your inventory.
	@Override
	public boolean equals(Object other) {
		return other instanceof FlagDesign design
				&& design.resolution == resolution
				&& design.size == size
				&& design.style == style
				&& Arrays.equals(design.pixels, pixels);
	}

	@Override
	public int hashCode() {
		return ((resolution * 31 + size) * 31 + style) * 31 + Arrays.hashCode(pixels);
	}

	// ---- The colour palette ----

	public static final int BLACK = 1;
	public static final int WHITE = 8;

	private static int[] buildPalette() {
		int[] grays = {0x000000, 0x1D1D21, 0x3A3A40, 0x5E5E66, 0x8A8A93, 0xB4B4BC, 0xDCDCE0, 0xF4F4F4, 0xFFFFFF};
		// Eight colour families, each from dark to light.
		int[][] families = {
				{0x5A0E0E, 0x8E1B1B, 0xC62828, 0xE85A4F, 0xF6A39A}, // red
				{0x6B3205, 0xA65410, 0xE07B16, 0xF5A341, 0xFBCD8C}, // orange
				{0x6E5806, 0xA88B0E, 0xE3C21B, 0xF3DD5A, 0xFAF0A8}, // yellow / gold
				{0x1E4A12, 0x2E7420, 0x46A033, 0x7FCB5E, 0xBFE8A8}, // green
				{0x0D4A4A, 0x157272, 0x22A3A0, 0x5BCFC9, 0xA6ECE7}, // teal
				{0x0F2A5C, 0x1B4596, 0x2E6BD1, 0x6A9CEB, 0xAECBF6}, // blue
				{0x3B1659, 0x5E2590, 0x8540C2, 0xB07DE0, 0xD9C0F3}, // purple
				{0x4A2A16, 0x6E4426, 0x9A6A44, 0xC9A07A, 0xF1D6B8}, // brown / skin
		};
		int[] palette = new int[grays.length + families.length * 5];
		// Slot 0 (see-through) shares the first gray value; it is never drawn.
		System.arraycopy(grays, 0, palette, 0, grays.length);
		int i = grays.length;
		for (int[] family : families) {
			for (int colour : family) {
				palette[i++] = colour;
			}
		}
		return palette;
	}
}
