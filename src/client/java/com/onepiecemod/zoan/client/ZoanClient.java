package com.onepiecemod.zoan.client;

import java.util.HashMap;
import java.util.Map;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;

import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.FabricRenderState;
import net.fabricmc.fabric.api.client.rendering.v1.RenderStateDataKey;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.client.RenderGuard;
import com.onepiecemod.mesh.client.MeshForms;
import com.onepiecemod.power.ZoanForms;

/**
 * Draws players who are in a full-body Zoan form (see power.ZoanForms) as the animal instead of
 * as a person. ZoanRenderMixin hooks this into the normal player drawing.
 */
public final class ZoanClient {
	/** Noted on the player's render state when they are in a form. */
	public record Data(String form, float formAge, float attack, boolean flying) {
	}

	public static final RenderStateDataKey<Data> KEY = RenderStateDataKey.create(() -> "onepiece:zoan");

	/** How big each form is drawn, and whether it glows (the phoenix is made of blue fire). */
	private static final Map<String, Float> SCALE = Map.of("leopard", 1.15f, "heavy_point", 1.2f, "phoenix", 1.35f, "seiryu", 1.6f,
			"nidhogg", 1.3f, "nika_wild", 1.05f);

	/** Smooth-mesh forms (MeshForms) are modelled at their boss size; players are drawn this much of it. */
	private static final Map<String, Float> MESH_SIZE = Map.of("nidhogg", 0.3f);
	/** A lighter copy of a mesh for players: the 40-block boss model has far more faces than a player-sized form needs. */
	private static final Map<String, String> MESH_NAME = Map.of("nidhogg", "nidhogg_player");

	private static final Map<String, ModelLayerLocation> LAYERS = new HashMap<>();
	private static final Map<String, ZoanModel> MODELS = new HashMap<>();

	private ZoanClient() {
	}

	public static void initialize() {
		for (String form : ZoanModels.FORMS) {
			ModelLayerLocation layer = new ModelLayerLocation(OnePieceMod.id("zoan/" + form), "main");
			LAYERS.put(form, layer);
			ModelLayerRegistry.registerModelLayer(layer, () -> ZoanModels.layer(form));
		}
	}

	private static ZoanModel model(String form) {
		return MODELS.computeIfAbsent(form, f -> {
			ModelLayerLocation layer = LAYERS.get(f);
			return layer == null ? null : new ZoanModel(Minecraft.getInstance().getEntityModels().bakeLayer(layer),
					ZoanModels.animations(f), f.equals("seiryu"));
		});
	}

	/** Called while Minecraft reads the player for this frame. */
	public static void extract(LivingEntity entity, LivingEntityRenderState state, float partialTick) {
		FabricRenderState data = (FabricRenderState) state;
		ZoanForms.Active active = entity instanceof Player ? ZoanForms.get(entity) : null;
		if (active == null || !SCALE.containsKey(active.form())) {
			data.setData(KEY, null);
			return;
		}
		float age = entity.level().getGameTime() - active.since() + partialTick;
		float swing = entity.getSwingAnimation(partialTick);
		boolean flying = entity instanceof Player player && (player.getAbilities().flying || !player.onGround() && !player.isInWater());
		data.setData(KEY, new Data(active.form(), age, swing > 0 ? swing : -1, flying));
	}

	/** Draws the form instead of the player. Returns true when it did (so the normal player isn't drawn). */
	public static boolean submit(LivingEntityRenderState state, PoseStack poseStack, SubmitNodeCollector collector) {
		if (!(state instanceof AvatarRenderState avatar)) {
			return false;
		}
		Data data = ((FabricRenderState) state).getData(KEY);
		if (data == null || avatar.isInvisible && avatar.isInvisibleToPlayer) {
			return data != null;
		}
		MeshForms.Mesh mesh = MeshForms.get(MESH_NAME.getOrDefault(data.form(), data.form()));
		if (mesh != null) {
			RenderGuard.run("zoan mesh " + data.form(), poseStack, () -> {
				MeshForms.Input in = new MeshForms.Input();
				in.ageInTicks = avatar.ageInTicks;
				in.walkPos = avatar.walkAnimationPos;
				in.walkSpeed = avatar.walkAnimationSpeed;
				in.headYaw = avatar.yRot;
				in.headPitch = avatar.xRot;
				in.flying = data.flying();
				in.formAge = data.formAge();
				in.attack = data.attack();
				MeshForms.submit(mesh, in, poseStack, collector, avatar.bodyRot, MESH_SIZE.getOrDefault(data.form(), 1.0f), avatar.deathTime,
						avatar.lightCoords, OverlayTexture.pack(OverlayTexture.u(0.0f), OverlayTexture.v(avatar.hasRedOverlay)));
			});
			return true;
		}
		ZoanModel model = model(data.form());
		if (model == null) {
			return false;
		}
		RenderGuard.run("zoan form " + data.form(), poseStack, () -> {
			ZoanModel.Pose pose = new ZoanModel.Pose();
			pose.ageInTicks = avatar.ageInTicks;
			pose.walkPos = avatar.walkAnimationPos;
			pose.walkSpeed = avatar.walkAnimationSpeed;
			pose.headYaw = avatar.yRot;
			pose.headPitch = avatar.xRot;
			pose.flying = data.flying();
			pose.formAge = data.formAge();
			pose.attack = data.attack();
			model.setupAnim(pose);

			float size = SCALE.get(data.form());
			boolean glows = data.form().equals("phoenix");
			Identifier texture = OnePieceMod.id("textures/entity/zoan/" + data.form() + ".png");
			RenderType type = glows ? RenderTypes.entityTranslucentEmissive(texture) : RenderTypes.entityCutout(texture);
			int light = glows ? 0xF000F0 : avatar.lightCoords;
			int overlay = OverlayTexture.pack(OverlayTexture.u(0.0f), OverlayTexture.v(avatar.hasRedOverlay));

			poseStack.pushPose();
			poseStack.rotate(Axis.YP.rotationDegrees(180.0f - avatar.bodyRot));
			poseStack.scale(-size, -size, size);
			poseStack.translate(0.0f, -1.501f, 0.0f);
			collector.submitModel(model, pose, poseStack, type, light, overlay, avatar.outlineColor);
			poseStack.popPose();
		});
		return true;
	}
}
