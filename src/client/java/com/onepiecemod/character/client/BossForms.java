package com.onepiecemod.character.client;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;

import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;

import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.client.RenderGuard;
import com.onepiecemod.mesh.client.MeshForms;
import com.onepiecemod.zoan.client.ZoanModel;
import com.onepiecemod.zoan.client.ZoanModels;

/**
 * Draws a boss in its monster form (Kaido's dragon, Lucci's leopard, King's pteranodon, Magellan's Venom Demon,
 * Queen's brachiosaurus, Saturn's Gyuki, Imu's demon and beast forms, Loki's Nidhogg)
 * instead of as a person. The dragon and leopard are the players' Zoan models (zoan.client.ZoanModels);
 * the boss-only forms come from BossFormModels. CharacterRenderer calls submit() when a boss has a form.
 */
public final class BossForms {
	/** How big each form is drawn. The leopard is life-size for its character, the rest are giant. */
	private static final Map<String, Float> SIZE = Map.of("seiryu", 2.6f, "leopard", 1.15f, "pteranodon", 2.4f, "venom_demon", 2.4f,
			"brachiosaurus", 3.2f, "gyuki", 3.0f, "imu_demon", 2.6f, "imu_beast", 3.0f, "nidhogg", 4.4f);
	/** Forms that grow with the character's own size (a person-sized hybrid rather than a giant beast). */
	private static final java.util.Set<String> PERSON_SIZED = java.util.Set.of("leopard");

	private static final Map<String, ZoanModel> MODELS = new HashMap<>();
	/** Smooth-mesh forms (MeshForms) that fight in the air: their wings beat instead of resting folded. */
	private static final java.util.Set<String> MESH_FLIES = java.util.Set.of("imu_beast");

	/** The animation inputs for a smooth-mesh form or look. */
	/** How much bigger than its model a mesh form is drawn: ryan wants Nidhogg and Imu's last form 40 blocks tall. */
	private static final java.util.Map<String, Float> MESH_SIZE = java.util.Map.of("nidhogg", 40f / 11f, "imu_beast", 5.0f);

	static MeshForms.Input input(CharacterRenderer.State state, boolean flying) {
		MeshForms.Input in = new MeshForms.Input();
		in.ageInTicks = state.ageInTicks;
		in.walkPos = state.walkAnimationPos;
		in.walkSpeed = state.walkAnimationSpeed;
		in.headYaw = state.yRot;
		in.headPitch = state.xRot;
		in.flying = flying;
		in.formAge = state.formAge;
		in.attack = state.formAttack;
		return in;
	}

	private BossForms() {
	}

	/** Registers the boss-only forms' model layers. CharacterClient calls this. */
	public static void initialize() {
		for (String form : BossFormModels.FORMS) {
			ModelLayerRegistry.registerModelLayer(layer(form), () -> BossFormModels.layer(form));
		}
	}

	private static boolean bossOnly(String form) {
		return Arrays.asList(BossFormModels.FORMS).contains(form);
	}

	private static ModelLayerLocation layer(String form) {
		// The Zoan forms' layers are registered by ZoanClient under the same names.
		return new ModelLayerLocation(OnePieceMod.id((bossOnly(form) ? "boss_form/" : "zoan/") + form), "main");
	}

	private static ZoanModel model(String form) {
		return MODELS.computeIfAbsent(form, f -> {
			if (!SIZE.containsKey(f)) {
				return null;
			}
			var animations = bossOnly(f) ? BossFormModels.animations(f) : ZoanModels.animations(f);
			return new ZoanModel(Minecraft.getInstance().getEntityModels().bakeLayer(layer(f)), animations, f.equals("seiryu"));
		});
	}

	/** Draws the form. Returns false when there's no such form (then the boss is drawn as a person). */
	public static boolean submit(CharacterRenderer.State state, PoseStack poseStack, SubmitNodeCollector collector) {
		MeshForms.Mesh mesh = MeshForms.get(state.form);
		if (mesh != null) {
			if (!state.isInvisible) {
				float size = MESH_SIZE.getOrDefault(state.form, 1.0f);
				MeshForms.Input in = input(state, MESH_FLIES.contains(state.form));
				// A giant takes long, slow strides: without this its legs and robe flick as fast as a person's.
				in.walkPos /= size;
				RenderGuard.run("boss mesh " + state.form, poseStack, () -> {
					poseStack.pushPose();
					// Eased position (CharacterRenderer.smooth): the giant glides instead of jittering with each path step.
					poseStack.translate(state.smoothX, state.smoothY, state.smoothZ);
					MeshForms.submit(mesh, in, poseStack, collector, state.bodyRot, size, state.deathTime, state.lightCoords,
							OverlayTexture.pack(OverlayTexture.u(0.0f), OverlayTexture.v(state.hasRedOverlay)));
					poseStack.popPose();
				});
			}
			return true;
		}
		ZoanModel model = model(state.form);
		if (model == null) {
			return false;
		}
		if (state.isInvisible) {
			return true;
		}
		RenderGuard.run("boss form " + state.form, poseStack, () -> {
			boolean flies = state.form.equals("pteranodon"); // King fights on the wing.
			ZoanModel.Pose pose = new ZoanModel.Pose();
			pose.ageInTicks = state.ageInTicks;
			pose.walkPos = state.walkAnimationPos;
			pose.walkSpeed = state.walkAnimationSpeed;
			pose.headYaw = state.yRot;
			pose.headPitch = state.xRot;
			pose.flying = flies;
			pose.formAge = state.formAge;
			pose.attack = state.formAttack;
			model.setupAnim(pose);

			float size = SIZE.get(state.form) * (PERSON_SIZED.contains(state.form) ? state.scale : 1.0f);
			Identifier texture = OnePieceMod.id("textures/entity/" + (bossOnly(state.form) ? "boss_form/" : "zoan/") + state.form + ".png");
			int overlay = OverlayTexture.pack(OverlayTexture.u(0.0f), OverlayTexture.v(state.hasRedOverlay));

			poseStack.pushPose();
			if (flies) {
				poseStack.translate(0.0f, 1.2f + (float) Math.sin(state.ageInTicks * 0.1f) * 0.2f, 0.0f);
			}
			if (state.deathTime > 0) {
				// Topples over like any mob when beaten.
				float fall = Math.min(1.0f, (state.deathTime - 1.0f) / 20.0f * 1.6f);
				poseStack.rotate(Axis.ZP.rotationDegrees((float) Math.sqrt(Math.max(0.0f, fall)) * 90.0f));
			}
			poseStack.rotate(Axis.YP.rotationDegrees(180.0f - state.bodyRot));
			poseStack.scale(-size, -size, size);
			poseStack.translate(0.0f, -1.501f, 0.0f);
			collector.submitModel(model, pose, poseStack, RenderTypes.entityCutout(texture), state.lightCoords, overlay, state.outlineColor);
			poseStack.popPose();
		});
		return true;
	}
}
