package com.onepiecemod.npc.client;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.ArmorModelSet;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.layers.HumanoidArmorLayer;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.HumanoidArm;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.npc.CombatStyle;
import com.onepiecemod.npc.HumanNpc;

/**
 * Draws every pirate and Marine NPC as a player-shaped mob wearing its own skin:
 * assets/onepiece/textures/entity/npc/<skin>.png (painted by tools/npcs/gen_npc_skins.py).
 * Gunners raise their gun to aim while they're fighting.
 */
public class NpcRenderer<T extends HumanNpc> extends HumanoidMobRenderer<T, NpcRenderer.State, HumanoidModel<NpcRenderer.State>> {
	/** What the renderer needs to know about the NPC this frame. */
	public static class State extends HumanoidRenderState {
		public String skin = "deckhand_0";
	}

	public NpcRenderer(EntityRendererProvider.Context context) {
		// The zombie model is the same shape as a player and uses the same skin layout.
		super(context, new HumanoidModel<>(context.bakeLayer(ModelLayers.ZOMBIE)), 0.5f);
		addLayer(new HumanoidArmorLayer<>(this,
				ArmorModelSet.bake(ModelLayers.ZOMBIE_ARMOR, context.getModelSet(), HumanoidModel::new),
				context.getEquipmentRenderer()));
		addLayer(new com.onepiecemod.vegapunk.client.SeraphimWingsLayer(this, context)); // Seraphim: black wings + back flame.
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(T entity, State state, float partialTick) {
		super.extractRenderState(entity, state, partialTick);
		state.skin = HumanNpc.validSkin(entity.getSkin()) ? entity.getSkin() : "deckhand_0";
	}

	@Override
	protected HumanoidModel.ArmPose getArmPose(T entity, HumanoidArm arm) {
		CombatStyle style = entity.getStyle();
		if (entity.isAggressive() && arm == entity.getMainArm() && !entity.getMainHandItem().isEmpty()
				&& (style == CombatStyle.GUNNER || style == CombatStyle.SNIPER)) {
			return HumanoidModel.ArmPose.CROSSBOW_HOLD;
		}
		return super.getArmPose(entity, arm);
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return OnePieceMod.id("textures/entity/npc/" + state.skin + ".png");
	}
}
