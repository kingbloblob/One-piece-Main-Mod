package com.onepiecemod.bounty.client;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.ArmorModelSet;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.layers.HumanoidArmorLayer;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.resources.Identifier;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.bounty.BountyHunterEntity;

/**
 * Draws a bounty hunter as a player-shaped mob, in one of a few outfits:
 * assets/onepiece/textures/entity/bounty_hunter/<number>.png (a normal 64x64 Minecraft skin).
 * Armor they wear is drawn on top (other mods, like One Piece Arsenal, can kit them out).
 */
public class BountyHunterRenderer extends HumanoidMobRenderer<BountyHunterEntity, BountyHunterRenderer.State, HumanoidModel<BountyHunterRenderer.State>> {
	/** What the renderer needs to know about the hunter this frame. */
	public static class State extends HumanoidRenderState {
		public int skin = 0;
	}

	public BountyHunterRenderer(EntityRendererProvider.Context context) {
		// The zombie model is the same shape as a player and uses the same skin layout.
		super(context, new HumanoidModel<>(context.bakeLayer(ModelLayers.ZOMBIE)), 0.5f);
		addLayer(new HumanoidArmorLayer<>(this,
				ArmorModelSet.bake(ModelLayers.ZOMBIE_ARMOR, context.getModelSet(), HumanoidModel::new),
				context.getEquipmentRenderer()));
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(BountyHunterEntity entity, State state, float partialTick) {
		super.extractRenderState(entity, state, partialTick);
		state.skin = entity.getSkin();
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return OnePieceMod.id("textures/entity/bounty_hunter/" + state.skin + ".png");
	}
}
