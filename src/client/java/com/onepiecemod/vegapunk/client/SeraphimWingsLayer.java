package com.onepiecemod.vegapunk.client;

import java.util.ArrayList;
import java.util.List;

import com.mojang.blaze3d.vertex.PoseStack;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.body.client.AppearanceModels;
import com.onepiecemod.npc.client.NpcRenderer;

/**
 * The Seraphim's big black Lunarian wings and the flame on their back, drawn in 3D on any NPC wearing a Seraphim skin.
 * Reuses the Lunarian race wings the players have (body/client/AppearanceModels), so they look the same.
 */
public class SeraphimWingsLayer extends RenderLayer<NpcRenderer.State, HumanoidModel<NpcRenderer.State>> {
	private static final Identifier TEXTURE = OnePieceMod.id("textures/entity/appearance/features.png");
	private static final int FULL_BRIGHT = 0xF000F0;

	private final Wings wings;
	private final Wings flame;

	public SeraphimWingsLayer(RenderLayerParent<NpcRenderer.State, HumanoidModel<NpcRenderer.State>> parent, EntityRendererProvider.Context context) {
		super(parent);
		this.wings = new Wings(context.bakeLayer(AppearanceModels.FEATURES), AppearanceModels.FEATURE_GROUPS.get("race:lunarian"), false);
		this.flame = new Wings(context.bakeLayer(AppearanceModels.FEATURES), AppearanceModels.FEATURE_GROUPS.get("glow:lunarian"), true);
	}

	public static boolean isSeraphim(String skin) {
		return skin != null && skin.startsWith("seraphim");
	}

	@Override
	public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, NpcRenderer.State state, float yRot, float xRot) {
		if (state.isInvisible || !isSeraphim(state.skin)) {
			return;
		}
		renderColoredCutoutModel(wings, TEXTURE, poseStack, collector, light, state, -1, 1);
		renderColoredCutoutModel(flame, TEXTURE, poseStack, collector, FULL_BRIGHT, state, -1, 1);
	}

	/** The humanoid body, posed like the NPC but not drawn, carrying only the wing (or flame) boxes. */
	private static class Wings extends HumanoidModel<NpcRenderer.State> {
		private final List<ModelPart> shown = new ArrayList<>();
		private final List<ModelPart> hidden = new ArrayList<>();
		private final List<Object[]> roots = new ArrayList<>();
		private final boolean glow;

		Wings(ModelPart root, List<String> paths, boolean glow) {
			super(root);
			this.glow = glow;
			for (String path : paths) {
				String[] split = path.split("/");
				ModelPart part = split[0].equals("head") ? head : body;
				for (int i = 1; i < split.length; i++) {
					part = part.getChild(split[i]);
				}
				shown.add(part);
				String name = split[split.length - 1];
				if (name.endsWith("_wing_r") || name.endsWith("_wing_l")) {
					ModelPart tip = null;
					try {
						tip = part.getChild(name + "_arm").getChild(name + "_tip");
					} catch (RuntimeException e) {
						// No tip on this wing.
					}
					roots.add(new Object[] {part, tip, name.endsWith("_r") ? 1f : -1f});
				}
			}
			// Every other extra box in the shared mesh (ears, tails, horns...) stays hidden.
			collect(body, hidden);
			collect(head, hidden);
			hidden.removeAll(shown);
		}

		private static void collect(ModelPart part, List<ModelPart> out) {
			part.getAllParts().forEach(out::add);
		}

		@Override
		public void setupAnim(NpcRenderer.State state) {
			super.setupAnim(state);
			for (ModelPart part : hidden) {
				part.visible = false;
			}
			for (ModelPart part : List.of(head, hat, body, leftArm, rightArm, leftLeg, rightLeg)) {
				part.visible = true;
				part.skipDraw = true; // Posed with the NPC, but its own skin is drawn by the main model.
			}
			for (ModelPart part : shown) {
				part.visible = true;
				part.skipDraw = false;
			}
			leftArm.visible = false;
			rightArm.visible = false;
			leftLeg.visible = false;
			rightLeg.visible = false;
			float t = state.ageInTicks;
			float flap = Mth.sin(t * 0.08f) * 0.06f;
			if (state.walkAnimationSpeed > 0.05f) {
				flap += Mth.sin(t * 0.45f) * 0.22f * Math.min(1f, state.walkAnimationSpeed * 1.5f);
			}
			for (Object[] wing : roots) {
				ModelPart root = (ModelPart) wing[0];
				ModelPart tip = (ModelPart) wing[1];
				float side = (float) wing[2];
				root.zRot = root.getInitialPose().zRot() + side * flap;
				root.yRot = root.getInitialPose().yRot() - side * flap * 0.5f;
				if (tip != null) {
					tip.zRot = tip.getInitialPose().zRot() + side * flap * 0.8f;
				}
			}
			if (glow) {
				for (ModelPart part : shown) {
					part.yScale = 1f + Mth.sin(t * 0.9f) * 0.08f + Mth.sin(t * 2.3f) * 0.05f;
				}
			}
		}
	}
}
