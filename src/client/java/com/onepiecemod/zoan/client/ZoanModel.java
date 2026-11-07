package com.onepiecemod.zoan.client;

import java.util.HashMap;
import java.util.Map;

import net.minecraft.client.animation.AnimationDefinition;
import net.minecraft.client.animation.KeyframeAnimation;
import net.minecraft.client.model.Model;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.util.Mth;

/**
 * One full-body Zoan form (shapes from ZoanModels). Every frame it starts from the resting pose and
 * layers Minecraft's keyframe animations on top: idle breathing, walking (or flying), the roar when
 * the form begins, and a strike whenever the player attacks.
 */
public class ZoanModel extends Model<ZoanModel.Pose> {
	/** What the model needs to know this frame. */
	public static class Pose {
		public float ageInTicks;
		public float walkPos;
		public float walkSpeed;
		public float headYaw;
		public float headPitch;
		public boolean flying;
		/** Ticks since the form began (the roar plays first). */
		public float formAge;
		/** 0 to 1 while an attack plays, otherwise -1. */
		public float attack = -1;
	}

	private final Map<String, KeyframeAnimation> anims = new HashMap<>();
	private final ModelPart head;
	private final boolean serpent;

	public ZoanModel(ModelPart root, Map<String, AnimationDefinition> definitions, boolean serpent) {
		super(root, RenderTypes::entityCutout);
		definitions.forEach((name, definition) -> anims.put(name, definition.bake(root)));
		this.head = root.hasChild("head") ? root.getChild("head")
				: root.hasChild("body") && root.getChild("body").hasChild("head") ? root.getChild("body").getChild("head") : null;
		this.serpent = serpent;
	}

	@Override
	public void setupAnim(Pose pose) {
		resetPose();
		long ms = (long) (pose.ageInTicks * 50.0f);

		KeyframeAnimation fly = anims.get("fly");
		if (pose.flying && fly != null) {
			fly.apply(ms, 1.0f);
		} else {
			anims.get("idle").apply(ms, 1.0f);
			anims.get("walk").applyWalk(pose.walkPos, pose.walkSpeed, 2.0f, 2.5f);
		}
		if (pose.formAge >= 0 && pose.formAge < 30) {
			anims.get("roar").apply((long) (pose.formAge * 50.0f), 1.0f);
		}
		if (pose.attack >= 0) {
			KeyframeAnimation attack = anims.get("attack");
			attack.apply((long) (pose.attack * 500.0f), 1.0f);
		}

		if (head != null) {
			// The dragon's long neck can't turn as far as a person's.
			float limit = serpent ? 35.0f : 70.0f;
			head.yRot += Mth.clamp(pose.headYaw, -limit, limit) * Mth.DEG_TO_RAD;
			head.xRot += Mth.clamp(pose.headPitch, -40.0f, 40.0f) * Mth.DEG_TO_RAD;
		}
	}
}
