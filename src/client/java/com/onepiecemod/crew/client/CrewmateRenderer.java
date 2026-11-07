package com.onepiecemod.crew.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.ArmorModelSet;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.layers.HumanoidArmorLayer;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.item.BowItem;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.crew.CrewmateEntity;

/**
 * Draws a crewmate as a player-shaped mob. Each role has its own outfit:
 * assets/onepiece/textures/entity/crewmate/<role>.png, <role>_1.png and <role>_2.png
 * (one per kind of recruit, normal 64x64 Minecraft skins).
 * Armor the captain gives them shows on top, snipers draw their bow while fighting,
 * and a knocked-out crewmate lies on the ground.
 */
public class CrewmateRenderer extends HumanoidMobRenderer<CrewmateEntity, CrewmateRenderer.State, HumanoidModel<CrewmateRenderer.State>> {
	/** What the renderer needs to know about the crewmate this frame. */
	public static class State extends HumanoidRenderState {
		public String role = "swordsman";
		public int variant;
		public boolean knockedOut;
	}

	public CrewmateRenderer(EntityRendererProvider.Context context) {
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
	public void extractRenderState(CrewmateEntity entity, State state, float partialTick) {
		super.extractRenderState(entity, state, partialTick);
		state.role = entity.getRole().id();
		state.variant = entity.getVariantIndex();
		state.knockedOut = entity.isKnockedOut();
	}

	@Override
	protected HumanoidModel.ArmPose getArmPose(CrewmateEntity entity, HumanoidArm arm) {
		if (entity.isAggressive() && arm == entity.getMainArm() && entity.getMainHandItem().getItem() instanceof BowItem) {
			return HumanoidModel.ArmPose.BOW_AND_ARROW;
		}
		return super.getArmPose(entity, arm);
	}

	@Override
	protected void setupRotations(State state, PoseStack poseStack, float bodyRot, float scale) {
		super.setupRotations(state, poseStack, bodyRot, scale);
		if (state.knockedOut) {
			poseStack.rotateDegrees(Axis.ZP, getFlipDegrees()); // On their side, like a mob that fell over.
		}
	}

	@Override
	public Identifier getTextureLocation(State state) {
		// Kind 0 wears <role>.png, the other kinds <role>_1.png and <role>_2.png.
		String suffix = state.variant == 0 ? "" : "_" + state.variant;
		return OnePieceMod.id("textures/entity/crewmate/" + state.role + suffix + ".png");
	}
}
