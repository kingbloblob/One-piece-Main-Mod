package com.onepiecemod.fx.client;

import com.onepiecemod.client.RenderGuard;

import com.mojang.blaze3d.vertex.PoseStack;

import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.PlayerModelType;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.fx.FxFeature;

/**
 * Coats a player's arms in shiny black while their Armament Haki is on.
 *
 * It draws a second, slightly bigger copy of just the arms over the normal ones, using a dark texture
 * (assets/onepiece/textures/entity/fx/armament.png) whose top edge is jagged, so the black seems to
 * creep up from the hands.
 */
public class ArmamentLayer extends RenderLayer<AvatarRenderState, PlayerModel> {
	public static final ModelLayerLocation WIDE = new ModelLayerLocation(OnePieceMod.id("armament_arms"), "wide");
	public static final ModelLayerLocation SLIM = new ModelLayerLocation(OnePieceMod.id("armament_arms"), "slim");
	private static final Identifier TEXTURE = OnePieceMod.id("textures/entity/fx/armament.png");

	private final ArmsModel wide;
	private final ArmsModel slim;

	public ArmamentLayer(RenderLayerParent<AvatarRenderState, PlayerModel> parent, EntityRendererProvider.Context context) {
		super(parent);
		this.wide = new ArmsModel(context.bakeLayer(WIDE), false);
		this.slim = new ArmsModel(context.bakeLayer(SLIM), true);
	}

	public static LayerDefinition createLayer(boolean slim) {
		// 0.3 bigger than the arm on every side: just over the sleeve layer (0.25), so it covers it.
		return LayerDefinition.create(PlayerModel.createMesh(new CubeDeformation(0.3f), slim), 64, 64);
	}

	@Override
	public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, AvatarRenderState state, float yRot, float xRot) {
		RenderGuard.run("armament arms", poseStack, () -> {
			if (state.isInvisible || state.isSpectator || Minecraft.getInstance().level == null) {
				return;
			}
			Entity player = Minecraft.getInstance().level.getEntity(state.id);
			if (player == null || !FxFeature.armamentVisible(player)) {
				return;
			}
			ArmsModel model = state.skin != null && state.skin.model() == PlayerModelType.SLIM ? slim : wide;
			renderColoredCutoutModel(model, TEXTURE, poseStack, collector, light, state, -1, 1);
		});
	}

	/** The player model with everything but the arms hidden. */
	static class ArmsModel extends PlayerModel {
		ArmsModel(ModelPart root, boolean slim) {
			super(root, slim);
		}

		@Override
		public void setupAnim(AvatarRenderState state) {
			super.setupAnim(state);
			head.visible = false;
			body.visible = false;
			leftLeg.visible = false;
			rightLeg.visible = false;
			leftSleeve.visible = false;
			rightSleeve.visible = false;
			leftArm.visible = true;
			rightArm.visible = true;
		}
	}
}
