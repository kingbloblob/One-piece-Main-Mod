package com.onepiecemod.building.client;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.QuadInstance;

import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.block.dispatch.BlockStateModelPart;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.resources.model.geometry.BakedQuad;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderEvents;

import com.onepiecemod.building.GhostPayload;

/**
 * Draws a blueprint's missing blocks as see-through "ghost" blocks, like a schematic overlay.
 *
 * The server sends the list of ghost blocks (and sends it again whenever a block is placed).
 * Every frame we draw each ghost with the block's real model, faded and gently pulsing,
 * so the player can see exactly which block goes where.
 */
public class GhostRenderer {
	private static final int FULL_BRIGHT = 0xF000F0; // Ghosts glow a little, so they're easy to see at night.
	private static final double MAX_DISTANCE = 96.0;

	private static final Map<BlockPos, BlockState> GHOSTS = new HashMap<>();
	private static ClientLevel ghostLevel;

	public static void initialize() {
		ClientPlayNetworking.registerGlobalReceiver(GhostPayload.TYPE, (payload, context) -> {
			GHOSTS.clear();
			for (int i = 0; i < payload.positions().size(); i++) {
				GHOSTS.put(payload.positions().get(i), payload.state(i));
			}
			ghostLevel = context.client().level;
		});
		ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> GHOSTS.clear());
		LevelRenderEvents.COLLECT_SUBMITS.register(GhostRenderer::render);
	}

	private static void render(LevelRenderContext context) {
		Minecraft minecraft = Minecraft.getInstance();
		if (GHOSTS.isEmpty() || minecraft.level == null || minecraft.level != ghostLevel) {
			return;
		}
		Vec3 camera = context.levelState().cameraRenderState.pos;
		PoseStack poseStack = context.poseStack();
		SubmitNodeCollector collector = context.submitNodeCollector();
		RenderType renderType = RenderTypes.entityTranslucent(TextureAtlas.LOCATION_BLOCKS);

		// Fade in and out a little, about once every 2 seconds.
		float time = context.levelState().gameTime + context.levelState().worldPartialTicks;
		int alpha = (int) (125 + 30 * Math.sin(time * 0.15));

		RandomSource random = RandomSource.create();
		for (Map.Entry<BlockPos, BlockState> ghost : GHOSTS.entrySet()) {
			BlockPos pos = ghost.getKey();
			if (camera.distanceToSqr(Vec3.atCenterOf(pos)) > MAX_DISTANCE * MAX_DISTANCE) {
				continue;
			}
			BlockState state = ghost.getValue();
			List<BlockStateModelPart> parts = new ArrayList<>();
			random.setSeed(42L);
			minecraft.getModelManager().getBlockStateModelSet().get(state).collectParts(random, parts);
			if (parts.isEmpty()) {
				continue;
			}
			// If a wrong block is in the way, draw the ghost a tiny bit bigger so it shows on top of it.
			boolean blocked = !minecraft.level.getBlockState(pos).isAir();
			float scale = blocked ? 1.02f : 1.0f;

			poseStack.pushPose();
			poseStack.translate(pos.getX() - camera.x + 0.5, pos.getY() - camera.y + 0.5, pos.getZ() - camera.z + 0.5);
			poseStack.scale(scale, scale, scale);
			poseStack.translate(-0.5, -0.5, -0.5);
			collector.submitCustomGeometry(poseStack, renderType, (pose, consumer) -> {
				QuadInstance quad = new QuadInstance();
				quad.setLightCoords(FULL_BRIGHT);
				quad.setOverlayCoords(OverlayTexture.NO_OVERLAY);
				for (BlockStateModelPart part : parts) {
					for (Direction side : Direction.values()) {
						// Skip faces pressed against another ghost, so a ghost floor looks like one smooth sheet.
						if (GHOSTS.containsKey(pos.relative(side))) {
							continue;
						}
						for (BakedQuad baked : part.getQuads(side)) {
							quad.setColor(color(baked, alpha));
							consumer.putBakedQuad(pose, baked, quad);
						}
					}
					for (BakedQuad baked : part.getQuads(null)) {
						quad.setColor(color(baked, alpha));
						consumer.putBakedQuad(pose, baked, quad);
					}
				}
			});
			poseStack.popPose();
		}
	}

	/** Faded with a hint of blue, darker on the sides and bottom so the shape is easy to read. */
	private static int color(BakedQuad quad, int alpha) {
		float shade = switch (quad.direction()) {
			case UP -> 1.0f;
			case DOWN -> 0.55f;
			case NORTH, SOUTH -> 0.8f;
			case EAST, WEST -> 0.65f;
		};
		int red = (int) (240 * shade);
		int green = (int) (248 * shade);
		int blue = (int) (255 * shade);
		return alpha << 24 | red << 16 | green << 8 | blue;
	}
}
