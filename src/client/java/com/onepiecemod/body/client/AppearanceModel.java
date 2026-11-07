package com.onepiecemod.body.client;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.util.Mth;

import net.fabricmc.fabric.api.client.rendering.v1.FabricRenderState;

/**
 * The player model with only the extra boxes from AppearanceModels drawn: the normal body is posed
 * (walking, swinging, crouching, body sliders) but not drawn, so the boxes move with the player.
 * Which boxes show comes from the groups AvatarRendererMixin puts on the render state.
 */
public class AppearanceModel extends PlayerModel {
	private final Map<String, List<ModelPart>> groups = new HashMap<>();
	private final List<ModelPart> all = new ArrayList<>();
	private final List<ModelPart> base;
	/** Wing parts that flap: {root, tip, side (+1 right, -1 left)}. */
	private final List<Object[]> wings = new ArrayList<>();
	private final List<ModelPart> flames = new ArrayList<>();
	/** true: only the "glow:" groups (drawn full bright), false: everything else. */
	private final boolean glow;

	public AppearanceModel(ModelPart root, Map<String, List<String>> groupParts, boolean glow) {
		super(root, false);
		this.glow = glow;
		Map<String, ModelPart> parents = Map.of("head", head, "body", body);
		Map<String, ModelPart> byName = new HashMap<>();
		groupParts.forEach((group, paths) -> {
			List<ModelPart> parts = new ArrayList<>();
			for (String path : paths) {
				// "body/sky_wing_r/sky_wing_r_tip": walk down from the head or body.
				String[] split = path.split("/");
				ModelPart part = parents.get(split[0]);
				for (int i = 1; i < split.length; i++) {
					part = part.getChild(split[i]);
				}
				parts.add(part);
				all.add(part);
				byName.put(split[split.length - 1], part);
			}
			groups.put(group, parts);
		});
		byName.forEach((name, part) -> {
			if (name.endsWith("_wing_r") || name.endsWith("_wing_l")) {
				ModelPart tip = byName.get(name + "_tip");
				wings.add(new Object[] {part, tip, name.endsWith("_r") ? 1f : -1f});
			} else if (name.equals("luna_flame") && glow) {
				flames.add(part);
			}
		});
		base = List.of(head, hat, body, jacket, leftArm, rightArm, leftLeg, rightLeg, leftSleeve, rightSleeve, leftPants, rightPants);
	}

	@Override
	public void setupAnim(AvatarRenderState state) {
		super.setupAnim(state);
		for (ModelPart part : base) {
			part.skipDraw = true; // Posed, but not drawn: the player's own skin is drawn by the normal model.
		}
		leftArm.visible = false;
		rightArm.visible = false;
		leftLeg.visible = false;
		rightLeg.visible = false;
		for (ModelPart part : all) {
			part.visible = false;
		}
		Set<String> shown = ((FabricRenderState) state).getData(AppearanceLayer.GROUPS_KEY);
		if (shown == null) {
			return;
		}
		for (String group : shown) {
			if (group.startsWith("glow:") != glow) {
				continue; // The glow model draws only the glowing groups, the others never draw them.
			}
			List<ModelPart> parts = groups.get(group);
			if (parts != null) {
				for (ModelPart part : parts) {
					part.visible = true;
				}
			}
		}
		animate(state);
	}

	/** Slow wing breathing when standing, real flaps when moving or gliding, a flickering back flame. */
	private void animate(AvatarRenderState state) {
		float t = state.ageInTicks;
		float flap = Mth.sin(t * 0.08f) * 0.06f;
		if (state.isFallFlying) {
			flap = -0.35f + Mth.sin(t * 0.5f) * 0.15f; // Spread wide while gliding.
		} else if (state.walkAnimationSpeed > 0.05f) {
			flap += Mth.sin(t * 0.45f) * 0.22f * Math.min(1f, state.walkAnimationSpeed * 1.5f);
		}
		for (Object[] wing : wings) {
			ModelPart root = (ModelPart) wing[0];
			ModelPart tip = (ModelPart) wing[1];
			float side = (float) wing[2];
			PartPose rest = root.getInitialPose();
			root.zRot = rest.zRot() + side * flap;
			root.yRot = rest.yRot() - side * flap * 0.5f;
			if (tip != null) {
				tip.zRot = tip.getInitialPose().zRot() + side * flap * 0.8f;
			}
		}
		for (ModelPart flame : flames) {
			flame.yScale = 1f + Mth.sin(t * 0.9f) * 0.08f + Mth.sin(t * 2.3f) * 0.05f;
			flame.xScale = 1f + Mth.sin(t * 1.3f) * 0.05f;
		}
	}
}
