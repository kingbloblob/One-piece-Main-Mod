package com.onepiecemod.creature.client;

import net.minecraft.client.animation.KeyframeAnimation;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

import com.onepiecemod.client.Keyframes;

/**
 * Moves the parts of any One Piece creature. The shapes come from CreatureModels; this class only looks at
 * the part names: legs walk, side legs scuttle, wings flap (or fins paddle), arms swing, tails wag,
 * jaws snap and gas puffs float.
 *
 * On top of that, three keyframe animations (Minecraft's own system, built in Keyframes) are made for
 * whatever parts the creature has: a strike when it attacks (lunge, bite, claw, wing beat, tail whip),
 * a flinch when it gets hurt, and now and then, while standing still, a look around with a tail flick.
 */
public class CreatureModel extends EntityModel<CreatureRenderer.State> {
	private final boolean swims;
	private final ModelPart root;
	private final ModelPart head;
	private final ModelPart jaw;
	private final ModelPart tail;
	private final ModelPart[] legs;
	private final ModelPart[] sideLegs;
	private final ModelPart[] wings;
	private final ModelPart[] arms;
	private final ModelPart[] puffs;

	public CreatureModel(ModelPart root, CreatureModels.Rig rig, boolean swims) {
		super(root);
		this.root = root;
		this.swims = swims;
		this.head = rig.head() ? root.getChild("head") : null;
		this.jaw = rig.jaw() ? head.getChild("jaw") : null;
		this.tail = rig.tail() ? root.getChild("tail") : null;
		this.legs = parts(root, "leg", rig.legs());
		this.sideLegs = parts(root, "sideleg", rig.sideLegs());
		this.wings = parts(root, "wing", rig.wings());
		this.arms = parts(root, "arm", rig.arms());
		this.puffs = parts(root, "puff", rig.puffs());
		this.attack = attackAnimation(rig).bake(root);
		this.flinch = flinchAnimation(rig).bake(root);
		this.lookAround = rig.head() || rig.tail() || rig.wings() > 0 ? lookAroundAnimation(rig).bake(root) : null;
	}

	private final KeyframeAnimation attack;
	private final KeyframeAnimation flinch;
	private final KeyframeAnimation lookAround;

	private static net.minecraft.client.animation.AnimationDefinition attackAnimation(CreatureModels.Rig rig) {
		Keyframes k = new Keyframes(0.5f);
		if (rig.head()) {
			k.rot("head", 0, 0, 0, 0).rot("head", 0.12f, 18, 0, 0).rot("head", 0.3f, -6, 0, 0).rot("head", 0.5f, 0, 0, 0);
			k.pos("head", 0, 0, 0, 0).pos("head", 0.12f, 0, 0, -2.5f).pos("head", 0.5f, 0, 0, 0);
		}
		if (rig.jaw()) {
			k.rot("jaw", 0, 0, 0, 0).rot("jaw", 0.1f, 45, 0, 0).rot("jaw", 0.2f, 0, 0, 0).rot("jaw", 0.5f, 0, 0, 0);
		}
		for (int i = 0; i < rig.arms(); i++) {
			float side = i == 0 ? 1 : -1;
			k.rot("arm" + i, 0, 0, 0, 0).rot("arm" + i, 0.1f + i * 0.08f, -110, 0, 20 * side).rot("arm" + i, 0.3f + i * 0.08f, -20, 0, 0)
					.rot("arm" + i, 0.5f, 0, 0, 0);
		}
		for (int i = 0; i < rig.wings(); i++) {
			float side = i == 0 ? 1 : -1;
			k.rot("wing" + i, 0, 0, 0, 0).rot("wing" + i, 0.15f, 0, 0, -50 * side).rot("wing" + i, 0.5f, 0, 0, 0);
		}
		if (rig.tail()) {
			k.rot("tail", 0, 0, 0, 0).rot("tail", 0.15f, 0, 35, 0).rot("tail", 0.3f, 0, -25, 0).rot("tail", 0.5f, 0, 0, 0);
		}
		if (rig.legs() >= 4) {
			// Four-legged animals rear up a little on their front legs as they strike.
			k.rot("leg0", 0, 0, 0, 0).rot("leg0", 0.12f, -30, 0, 0).rot("leg0", 0.5f, 0, 0, 0);
			k.rot("leg1", 0, 0, 0, 0).rot("leg1", 0.12f, -30, 0, 0).rot("leg1", 0.5f, 0, 0, 0);
		}
		return k.build();
	}

	private static net.minecraft.client.animation.AnimationDefinition flinchAnimation(CreatureModels.Rig rig) {
		Keyframes k = new Keyframes(0.4f);
		if (rig.head()) {
			k.rot("head", 0, 0, 0, 0).rot("head", 0.08f, -25, 12, 0).rot("head", 0.4f, 0, 0, 0);
		}
		if (rig.tail()) {
			k.rot("tail", 0, 0, 0, 0).rot("tail", 0.08f, 30, 0, 0).rot("tail", 0.4f, 0, 0, 0);
		}
		for (int i = 0; i < rig.wings(); i++) {
			float side = i == 0 ? 1 : -1;
			k.rot("wing" + i, 0, 0, 0, 0).rot("wing" + i, 0.08f, 0, 0, -30 * side).rot("wing" + i, 0.4f, 0, 0, 0);
		}
		return k.build();
	}

	/** Loops every 8 seconds; the first 3 seconds hold the movement, the rest is still. */
	private static net.minecraft.client.animation.AnimationDefinition lookAroundAnimation(CreatureModels.Rig rig) {
		Keyframes k = new Keyframes(8.0f).looping();
		if (rig.head()) {
			k.rot("head", 0, 0, 0, 0).rot("head", 0.6f, 5, 40, 0).rot("head", 1.4f, 5, 40, 0).rot("head", 2.0f, 5, -40, 0)
					.rot("head", 2.8f, 5, -40, 0).rot("head", 3.3f, 0, 0, 0).rot("head", 8.0f, 0, 0, 0);
		}
		if (rig.tail()) {
			k.rot("tail", 0, 0, 0, 0).rot("tail", 1.0f, 0, 0, 0).rot("tail", 1.2f, 0, 40, 0).rot("tail", 1.4f, 0, -40, 0)
					.rot("tail", 1.6f, 0, 0, 0).rot("tail", 8.0f, 0, 0, 0);
		}
		for (int i = 0; i < rig.wings(); i++) {
			float side = i == 0 ? 1 : -1;
			k.rot("wing" + i, 0, 0, 0, 0).rot("wing" + i, 2.4f, 0, 0, 0).rot("wing" + i, 2.6f, 0, 0, -45 * side)
					.rot("wing" + i, 2.8f, 0, 0, 0).rot("wing" + i, 3.0f, 0, 0, -45 * side).rot("wing" + i, 3.2f, 0, 0, 0)
					.rot("wing" + i, 8.0f, 0, 0, 0);
		}
		return k.build();
	}

	private static ModelPart[] parts(ModelPart root, String prefix, int count) {
		ModelPart[] parts = new ModelPart[count];
		for (int i = 0; i < count; i++) {
			parts[i] = root.getChild(prefix + i);
		}
		return parts;
	}

	@Override
	public void setupAnim(CreatureRenderer.State state) {
		super.setupAnim(state); // Puts every part back to its resting pose first.
		float time = state.ageInTicks;
		float walk = state.walkAnimationPos;
		float speed = Math.min(state.walkAnimationSpeed, 1.0f);

		if (swims) {
			// Tilt the whole body up or down while diving or rising.
			root.xRot += state.xRot * Mth.DEG_TO_RAD;
		}
		if (head != null) {
			head.yRot += state.yRot * Mth.DEG_TO_RAD;
			if (!swims) {
				head.xRot += state.xRot * Mth.DEG_TO_RAD;
			}
		}
		if (jaw != null) {
			jaw.xRot += state.aggressive ? 0.35f + Mth.sin(time * 0.4f) * 0.25f : 0.03f;
		}
		if (tail != null) {
			float wag = swims ? Mth.sin(time * 0.3f * (1.0f + speed)) * 0.45f : Mth.sin(time * 0.12f) * 0.12f + Mth.cos(walk * 0.6662f) * 0.3f * speed;
			tail.yRot += wag;
		}

		// Legs: front-right and back-left step together, like real animals.
		for (int i = 0; i < legs.length; i++) {
			float phase = ((i + i / 2) % 2) * Mth.PI;
			legs[i].xRot += Mth.cos(walk * 0.6662f + phase) * 1.2f * speed;
		}
		// Scorpion legs: scuttle back and forth.
		for (int i = 0; i < sideLegs.length; i++) {
			float side = i % 2 == 0 ? 1.0f : -1.0f;
			sideLegs[i].yRot += Mth.sin(walk * 1.3f + i * 1.1f) * 0.45f * speed * side;
			sideLegs[i].zRot += Mth.abs(Mth.cos(walk * 1.3f + i * 1.1f)) * 0.2f * speed * side;
		}
		// Wings: a lazy flutter on the ground, fast flapping in the air. Fins paddle in water.
		for (int i = 0; i < wings.length; i++) {
			float side = i == 0 ? 1.0f : -1.0f;
			float flap = swims ? Mth.sin(time * 0.25f) * 0.35f
					: state.onGround ? Mth.sin(time * 0.1f) * 0.05f : Mth.sin(time * 1.6f) * 0.9f;
			wings[i].zRot += flap * side;
		}
		// Arms: swing while walking, raised to punch when fighting.
		for (int i = 0; i < arms.length; i++) {
			float phase = i == 0 ? Mth.PI : 0.0f;
			arms[i].xRot += Mth.cos(walk * 0.6662f + phase) * speed + (state.aggressive ? -1.1f + Mth.sin(time * 0.5f + phase) * 0.4f : 0.0f);
		}
		// Gas puffs drift up and down around Smiley.
		for (int i = 0; i < puffs.length; i++) {
			puffs[i].y += Mth.sin(time * 0.12f + i * 1.7f) * 2.0f;
		}

		// Keyframe animations on top.
		if (lookAround != null && !state.aggressive && speed < 0.1f) {
			lookAround.apply((long) (time * 50.0f), 1.0f - speed * 10.0f);
		}
		if (state.attack >= 0) {
			attack.apply((long) (state.attack * 500.0f), 1.0f);
		}
		if (state.hurt >= 0) {
			flinch.apply((long) (state.hurt * 400.0f), 1.0f);
		}
	}
}
