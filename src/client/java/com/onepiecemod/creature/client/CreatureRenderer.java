package com.onepiecemod.creature.client;

import com.mojang.blaze3d.vertex.PoseStack;

import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.resources.Identifier;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.creature.CreatureEntity;
import com.onepiecemod.creature.CreatureSpecies;

/**
 * Draws a One Piece creature with its own model and texture:
 * assets/onepiece/textures/entity/creature/<id>.png
 */
public class CreatureRenderer extends MobRenderer<CreatureEntity, CreatureRenderer.State, CreatureModel> {
	private final float size;
	private final Identifier texture;

	/** What the renderer needs to know about the creature this frame. */
	public static class State extends LivingEntityRenderState {
		public boolean aggressive;
		public boolean onGround;
		/** 0 to 1 while it strikes, otherwise -1. */
		public float attack = -1;
		/** 0 to 1 while it flinches from a hit, otherwise -1. */
		public float hurt = -1;
	}

	public CreatureRenderer(EntityRendererProvider.Context context, CreatureSpecies species, ModelLayerLocation layer) {
		super(context, new CreatureModel(context.bakeLayer(layer), CreatureModels.rig(species.id()), species.swims()),
				species.width() * 0.5f);
		this.size = species.renderScale();
		this.texture = OnePieceMod.id("textures/entity/creature/" + species.id() + ".png");
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(CreatureEntity entity, State state, float partialTick) {
		super.extractRenderState(entity, state, partialTick);
		state.aggressive = entity.isAggressive();
		state.onGround = entity.onGround() || entity.isInWater();
		float swing = entity.getSwingAnimation(partialTick);
		state.attack = swing > 0 ? swing : -1;
		state.hurt = entity.hurtTime > 0 ? 1.0f - (entity.hurtTime - partialTick) / Math.max(1, entity.hurtDuration) : -1;
	}

	@Override
	protected void scale(State state, PoseStack poseStack) {
		poseStack.scale(size, size, size);
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return texture;
	}
}
