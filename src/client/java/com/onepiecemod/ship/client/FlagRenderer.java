package com.onepiecemod.ship.client;

import com.onepiecemod.client.RenderGuard;

import com.mojang.blaze3d.vertex.PoseStack;

import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.core.Direction;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.ship.FlagBlock;
import com.onepiecemod.ship.FlagBlockEntity;
import com.onepiecemod.ship.FlagDesign;

/**
 * Draws the painting on a Jolly Roger block that is placed in the world.
 */
public class FlagRenderer implements BlockEntityRenderer<FlagBlockEntity, FlagRenderer.State> {
	public static class State extends BlockEntityRenderState {
		public FlagDesign design = FlagDesign.blank();
		public Direction facing = Direction.NORTH;
		public float time;
	}

	public FlagRenderer(BlockEntityRendererProvider.Context context) {
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(FlagBlockEntity flag, State state, float partialTick, Vec3 cameraPos, ModelFeatureRenderer.CrumblingOverlay crumbling) {
		BlockEntityRenderer.super.extractRenderState(flag, state, partialTick, cameraPos, crumbling);
		RenderGuard.run("flag state", () -> {
			state.design = flag.getDesign();
			state.facing = flag.getBlockState().getValue(FlagBlock.FACING);
			// Every flag waves a little differently, so a row of them doesn't move in lockstep.
			long seed = flag.getBlockPos().asLong();
			state.time = (flag.getLevel() != null ? flag.getLevel().getGameTime() : 0) + partialTick + (seed % 100);
		});
	}

	@Override
	public void submit(State state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
		RenderGuard.run("flag", poseStack, () -> {
			FlagDrawing.submit(poseStack, collector, state.design, state.facing, state.lightCoords, state.time);
		});
	}

	@Override
	public boolean shouldRenderOffScreen() {
		return true; // Big flags reach outside their block.
	}
}
