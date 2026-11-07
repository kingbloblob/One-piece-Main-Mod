package com.onepiecemod.town.client;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.resources.Identifier;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.town.TownsfolkEntity;

/**
 * Draws townsfolk as player-shaped people wearing their own skin:
 * assets/onepiece/textures/entity/townsfolk/<skin>.png (painted by tools/towns/gen_town_skins.py).
 * Kids are the same model at a smaller scale (the SCALE attribute does that by itself).
 */
public class TownsfolkRenderer extends HumanoidMobRenderer<TownsfolkEntity, TownsfolkRenderer.State, HumanoidModel<TownsfolkRenderer.State>> {
	public static class State extends HumanoidRenderState {
		public String skin = "villager_0";
	}

	public TownsfolkRenderer(EntityRendererProvider.Context context) {
		// The zombie model is the same shape as a player and uses the same skin layout.
		super(context, new HumanoidModel<>(context.bakeLayer(ModelLayers.ZOMBIE)), 0.5f);
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(TownsfolkEntity entity, State state, float partialTick) {
		super.extractRenderState(entity, state, partialTick);
		state.skin = TownsfolkEntity.validSkin(entity.getSkin()) ? entity.getSkin() : "villager_0";
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return OnePieceMod.id("textures/entity/townsfolk/" + state.skin + ".png");
	}
}
