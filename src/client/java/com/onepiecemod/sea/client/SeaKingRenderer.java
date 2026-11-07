package com.onepiecemod.sea.client;

import com.mojang.blaze3d.vertex.PoseStack;

import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.world.phys.AABB;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.sea.SeaKingEntity;

/**
 * Draws a Sea King 14 times the size of its model (each one is also 80-125% of that, see SeaKingEntity). Each color variant has its own texture:
 * assets/onepiece/textures/entity/sea_king/sea_king_<number>.png (128x128).
 */
public class SeaKingRenderer extends MobRenderer<SeaKingEntity, SeaKingRenderer.State, SeaKingModel> {
	private static final float SIZE = 14.0f; // show-sized: head about 9 blocks wide, about 75 blocks from snout to tail fin

	/** What the renderer needs to know about the Sea King this frame. */
	public static class State extends LivingEntityRenderState {
		public int variant;
		public int style;
		public boolean aggressive;
		/** 0 to 1 while it bites, otherwise -1. */
		public float attack = -1;
		/** 0 to 1 while it flinches from a hit, otherwise -1. */
		public float hurt = -1;
	}

	/** One model per body style; the renderer swaps to the right one before drawing each Sea King. */
	private final SeaKingModel[] styles = new SeaKingModel[com.onepiecemod.sea.SeaKingEntity.MODEL_STYLES];

	public SeaKingRenderer(EntityRendererProvider.Context context) {
		super(context, new SeaKingModel(context.bakeLayer(SeaKingModel.LAYER)), 8.0f);
		styles[0] = this.model;
		for (int i = 1; i < styles.length; i++) {
			styles[i] = new SeaKingModel(context.bakeLayer(SeaKingModel.LAYERS[i]));
		}
	}

	@Override
	public void submit(State state, com.mojang.blaze3d.vertex.PoseStack poseStack, net.minecraft.client.renderer.SubmitNodeCollector collector,
			net.minecraft.client.renderer.state.level.CameraRenderState camera) {
		this.model = styles[Math.floorMod(state.style, styles.length)];
		super.submit(state, poseStack, collector, camera);
	}

	// The model's tail reaches far behind the hitbox, so keep drawing it when only the tail is on screen.
	@Override
	protected AABB getBoundingBoxForCulling(SeaKingEntity entity, float partialTick) {
		return super.getBoundingBoxForCulling(entity, partialTick).inflate(entity.getBbWidth() * 10.0);
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(SeaKingEntity entity, State state, float partialTick) {
		super.extractRenderState(entity, state, partialTick);
		state.variant = entity.getVariant();
		state.style = entity.getStyle();
		state.aggressive = entity.isAggressive();
		float swing = entity.getSwingAnimation(partialTick);
		state.attack = swing > 0 ? swing : -1;
		state.hurt = entity.hurtTime > 0 ? 1.0f - (entity.hurtTime - partialTick) / Math.max(1, entity.hurtDuration) : -1;
	}

	@Override
	protected void scale(State state, PoseStack poseStack) {
		poseStack.scale(SIZE, SIZE, SIZE);
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return OnePieceMod.id("textures/entity/sea_king/sea_king_" + state.variant + ".png");
	}
}
