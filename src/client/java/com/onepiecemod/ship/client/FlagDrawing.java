package com.onepiecemod.ship.client;

import java.util.LinkedHashMap;
import java.util.Map;

import com.mojang.blaze3d.platform.NativeImage;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.DynamicTexture;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.Direction;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.ship.FlagDesign;

/**
 * Draws a painted Jolly Roger as a waving cloth. Used both for flags placed in the world (FlagRenderer)
 * and for flags on a sailing ship (ShipRenderer).
 *
 * Each different painting becomes a small texture the first time it is drawn, and is kept for next time.
 */
public class FlagDrawing {
	private static final int GRID = 8; // The cloth is split into 8x8 pieces so it can bend and wave.
	private static final int MAX_TEXTURES = 256;

	private static int nextTextureNumber = 0;
	private static final Map<FlagDesign, Identifier> TEXTURES = new LinkedHashMap<>(16, 0.75f, true) {
		@Override
		protected boolean removeEldestEntry(Map.Entry<FlagDesign, Identifier> eldest) {
			if (size() > MAX_TEXTURES) {
				Minecraft.getInstance().getTextureManager().release(eldest.getValue());
				return true;
			}
			return false;
		}
	};

	/** The texture for a painting, made on first use. */
	public static Identifier texture(FlagDesign design) {
		Identifier existing = TEXTURES.get(design);
		if (existing != null) {
			return existing;
		}
		int res = design.resolution();
		NativeImage image = new NativeImage(res, res, false);
		for (int y = 0; y < res; y++) {
			for (int x = 0; x < res; x++) {
				image.setPixel(x, y, design.argb(x, y));
			}
		}
		Identifier id = OnePieceMod.id("dynamic/flag_" + nextTextureNumber++);
		Minecraft.getInstance().getTextureManager().register(id, new DynamicTexture(() -> "One Piece flag " + id, image));
		TEXTURES.put(design, id);
		return id;
	}

	/**
	 * Draws a flag for the block at the current pose origin (the pose should be at the block's corner).
	 * time is in ticks and makes the cloth move.
	 */
	public static void submit(PoseStack poseStack, SubmitNodeCollector collector, FlagDesign design, Direction facing, int light, float time) {
		poseStack.pushPose();
		// Everything below is worked out for a flag facing north. Turn it to face the right way.
		poseStack.translate(0.5, 0, 0.5);
		poseStack.rotate(Axis.YP.rotationDegrees(-(facing.toYRot() + 180)));
		poseStack.translate(-0.5, 0, -0.5);

		int style = design.style();
		float size = design.size();

		collector.submitCustomGeometry(poseStack, RenderTypes.entityCutout(texture(design)), (pose, consumer) -> {
			for (int row = 0; row < GRID; row++) {
				for (int col = 0; col < GRID; col++) {
					float u0 = col / (float) GRID, u1 = (col + 1) / (float) GRID;
					float v0 = row / (float) GRID, v1 = (row + 1) / (float) GRID;
					float[] a = point(style, size, u0, v0, time);
					float[] b = point(style, size, u0, v1, time);
					float[] c = point(style, size, u1, v1, time);
					float[] d = point(style, size, u1, v0, time);
					vertex(consumer, pose, a, u0, v0, light);
					vertex(consumer, pose, b, u0, v1, light);
					vertex(consumer, pose, c, u1, v1, light);
					vertex(consumer, pose, d, u1, v0, light);
				}
			}
		});
		poseStack.popPose();
	}

	/**
	 * Where a point of the picture goes, for a flag facing north. u and v go from 0 to 1 across the picture
	 * (u = left to right, v = top to bottom).
	 */
	private static float[] point(int style, float size, float u, float v, float time) {
		float y = 1 - v * size; // Top edge at the top of the block, hanging down.
		switch (style) {
			case FlagDesign.STYLE_PLAQUE: {
				// Flat on the wall behind (the south side), centred on the block.
				float x = 0.5f + size / 2 - u * size;
				float yCentred = 0.5f + size / 2 - v * size;
				return new float[]{x, yCentred, 15.5f / 16f};
			}
			case FlagDesign.STYLE_SAIL: {
				// Hangs across the ship and puffs out toward the front, as if the wind is behind you.
				float x = 0.5f + size / 2 - u * size;
				float puff = Mth.sin(u * Mth.PI) * (0.55f + 0.45f * Mth.sin(v * Mth.PI)) * 0.18f * size;
				float flutter = Mth.sin(time * 0.08f + u * 4) * 0.02f;
				return new float[]{x, y, 0.5f - puff - flutter};
			}
			default: {
				// Sticks out north from the pole at the middle of the block, and waves more toward the end.
				float z = 0.5f - u * size;
				float wave = Mth.sin(time * 0.15f - u * 6) * 0.12f * u * size;
				return new float[]{0.5f + wave, y, z};
			}
		}
	}

	private static void vertex(VertexConsumer consumer, PoseStack.Pose pose, float[] p, float u, float v, int light) {
		consumer.addVertex(pose, p[0], p[1], p[2])
				.setColor(-1)
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(light)
				.setNormal(pose, 0, 0, -1);
	}
}
