package com.onepiecemod.empire.client;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.ArmorModelSet;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.layers.HumanoidArmorLayer;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.resources.Identifier;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.empire.PirateGuardEntity;
import com.onepiecemod.npc.NpcSkins;

/**
 * Draws a pirate guard as a player-shaped mob. Each guard wears one of the pirate NPC outfits
 * (textures/entity/npc/deckhand_N.png, picked from the guard's id so it never changes).
 * Their armor and sword show on top, so better titles look tougher.
 */
public class PirateGuardRenderer extends HumanoidMobRenderer<PirateGuardEntity, PirateGuardRenderer.State, HumanoidModel<PirateGuardRenderer.State>> {
	public static class State extends HumanoidRenderState {
		public int look;
	}

	public PirateGuardRenderer(EntityRendererProvider.Context context) {
		super(context, new HumanoidModel<>(context.bakeLayer(ModelLayers.ZOMBIE)), 0.5f);
		// Draw their armor, like a zombie's.
		addLayer(new HumanoidArmorLayer<>(this,
				ArmorModelSet.bake(ModelLayers.ZOMBIE_ARMOR, context.getModelSet(), HumanoidModel::new),
				context.getEquipmentRenderer()));
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(PirateGuardEntity entity, State state, float partialTick) {
		super.extractRenderState(entity, state, partialTick);
		state.look = Math.floorMod(entity.getUUID().hashCode(), NpcSkins.COUNT.get("deckhand"));
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return OnePieceMod.id("textures/entity/npc/deckhand_" + state.look + ".png");
	}
}
