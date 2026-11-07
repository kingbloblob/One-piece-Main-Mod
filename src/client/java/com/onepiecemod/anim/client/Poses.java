package com.onepiecemod.anim.client;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.Pose;

import com.onepiecemod.anim.Anim;
import com.onepiecemod.weapon.GunItem;

/**
 * Bends a person-shaped model into each animation's pose. Runs every frame right after Minecraft has posed
 * the model for walking and looking around, for players, bosses, characters, NPCs (and their armor).
 *
 * How the numbers work: angles are in radians (1.57 = a quarter turn). For an arm or leg, a negative
 * xRot swings it forward and up (-1.57 points straight ahead, -3.1 straight up); yRot swings a raised arm
 * outward (+) or across the chest (-); zRot lifts it out to the side (+). Everything here is written for
 * the right arm and leg (the "main" side) and mirrored for left-handed mobs and left punches.
 * "Twist" turns the upper body: + turns toward the main side, which pulls that shoulder back.
 * Each animation is a few keyframes: k(p, time, value, time, value...) with p going 0 -> 1.
 */
public final class Poses {
	private Poses() {
	}

	public static void apply(HumanoidModel<?> model, HumanoidRenderState state, AnimClient.Frame frame) {
		if (state.isFallFlying || state.isVisuallySwimming || state.hasPose(Pose.SLEEPING) || state.isPassenger) {
			return;
		}
		Anim anim = frame.anim();
		float p = frame.progress();
		float weight;
		if (anim != null) {
			// Ease in over the first few frames and back out at the end, so it never snaps.
			weight = Math.min(1, p / 0.12f) * Math.min(1, (1 - p) / 0.18f);
		} else if (frame.melee() != null && state.swingAnimation > 0) {
			anim = frame.melee();
			p = state.swingAnimation;
			weight = Math.min(1, (1 - p) / 0.25f);
		} else {
			weight = 0;
		}

		Rig rig = new Rig(model, state);
		if (frame.gun() != null && (anim == null || anim == Anim.SHOOT)) {
			// Holding a gun: its own hold and aim, with a kick on each shot. A melee swing (hitting someone
			// with the butt) briefly lets Minecraft's own swing through.
			rig.mirror = state.mainArm == HumanoidArm.LEFT;
			rig.w = state.swingAnimation > 0 ? 1 - Mth.sin(state.swingAnimation * Mth.PI) : 1;
			gun(rig, frame.gun(), smooth(frame.aim()), anim == Anim.SHOOT ? p : -1, state);
		} else if (anim != null) {
			rig.mirror = (state.mainArm == HumanoidArm.LEFT) != (anim == Anim.PUNCH_LEFT);
			rig.w = smooth(weight);
			pose(rig, anim, p, state.ageInTicks);
		} else if (frame.stance() != AnimClient.Stance.NONE) {
			rig.mirror = state.mainArm == HumanoidArm.LEFT;
			rig.w = 0.85f;
			stance(rig, frame.stance(), state.ageInTicks);
		} else if (frame.idle() != AnimClient.Idle.NONE && state.walkAnimationSpeed < 0.15f) {
			rig.mirror = state.mainArm == HumanoidArm.LEFT;
			rig.w = 1 - state.walkAnimationSpeed / 0.15f;
			idle(rig, frame.idle());
		}

		if (frame.hurt() > 0) {
			// A flinch when hit: thrown back a little, arms jerk out. Added on top of whatever else is playing.
			float h = frame.hurt();
			model.body.xRot -= 0.25f * h;
			model.head.xRot -= 0.35f * h;
			model.rightArm.xRot += 0.45f * h;
			model.leftArm.xRot += 0.45f * h;
			model.rightArm.zRot += 0.3f * h;
			model.leftArm.zRot -= 0.3f * h;
		}
	}

	// ---------- The animations ----------

	private static void pose(Rig r, Anim anim, float p, float age) {
		switch (anim) {
			case SLASH -> {
				r.arm(true, k(p, 0, -0.6f, .3f, -1.4f, .55f, -1.3f, 1, -1.0f), k(p, 0, 0.3f, .3f, 1.3f, .55f, -1.0f, 1, -0.9f),
						k(p, 0, 0.1f, .3f, 0.5f, .55f, 0.1f, 1, 0.1f));
				r.arm(false, -0.6f, -0.4f, 0.15f);
				r.legs(k(p, 0, 0, .55f, -0.35f, 1, -0.3f), k(p, 0, 0, .55f, 0.3f, 1, 0.25f));
				r.lean(k(p, 0, 0, .3f, 0, .55f, 0.15f, 1, 0.1f));
				r.twist(k(p, 0, 0, .3f, 0.55f, .55f, -0.6f, 1, -0.45f));
			}
			case CHOP -> {
				r.arm(true, k(p, 0, -0.8f, .35f, -3.0f, .55f, -0.4f, 1, -0.5f), -0.15f, 0.05f);
				r.arm(false, k(p, 0, -0.6f, .35f, -2.7f, .55f, -0.5f, 1, -0.5f), -0.5f, 0.05f);
				r.lean(k(p, 0, 0, .35f, -0.2f, .55f, 0.45f, 1, 0.35f));
				r.headPitch(k(p, 0, 0, .35f, -0.3f, .55f, 0.2f, 1, 0.1f));
				r.crouch(k(p, 0, 0, .35f, 0, .55f, 0.4f, 1, 0.3f));
			}
			case SPIN_SLASH -> {
				r.arm(true, -0.2f, 0, k(p, 0, 0.3f, .15f, 1.45f, .85f, 1.45f, 1, 0.5f));
				r.arm(false, -0.2f, 0, k(p, 0, 0.3f, .15f, 1.45f, .85f, 1.45f, 1, 0.5f));
				r.crouch(k(p, 0, 0, .15f, 0.3f, .85f, 0.3f, 1, 0));
				r.twist(k(p, 0, 0, .15f, 0.5f, .3f, 0, 1, 0));
				r.spin(-smooth(clamp((p - 0.15f) / 0.7f)) * Mth.TWO_PI);
			}
			case CROSS_SLASH -> {
				float x = k(p, 0, -1.0f, .35f, -2.7f, .6f, -0.8f, 1, -0.8f);
				float y = k(p, 0, 0, .35f, -0.6f, .6f, 1.0f, 1, 0.9f);
				r.arm(true, x, y, 0.1f);
				r.arm(false, x, y, 0.1f);
				r.lean(k(p, 0, 0, .35f, -0.15f, .6f, 0.35f, 1, 0.3f));
				r.crouch(k(p, 0, 0, .35f, 0, .6f, 0.35f, 1, 0.3f));
			}
			case THRUST -> {
				r.arm(true, k(p, 0, -0.9f, .35f, -1.3f, .55f, -1.6f, 1, -1.5f), k(p, 0, 0, .35f, 0.4f, .55f, 0, 1, 0), 0.05f);
				r.reach(true, k(p, 0, 0, .35f, 2.5f, .55f, -3.0f, 1, -2.5f));
				r.arm(false, 0.5f, 0, 0.2f);
				r.legs(k(p, 0, 0, .55f, -0.6f, 1, -0.5f), k(p, 0, 0, .55f, 0.5f, 1, 0.4f));
				r.lean(k(p, 0, 0, .55f, 0.3f, 1, 0.25f));
				r.twist(k(p, 0, 0, .35f, 0.5f, .55f, -0.45f, 1, -0.4f));
			}
			case PUNCH, PUNCH_LEFT -> {
				r.arm(true, k(p, 0, -0.9f, .3f, -1.0f, .5f, -1.62f, 1, -1.55f), k(p, 0, -0.1f, .3f, 0.35f, .5f, -0.12f, 1, -0.1f), 0.05f);
				r.reach(true, k(p, 0, 0, .3f, 2.5f, .5f, -3.0f, 1, -2.5f));
				r.arm(false, k(p, 0, -1.1f, .5f, -0.9f, 1, -0.9f), -0.6f, 0.05f);
				r.reach(false, k(p, 0, 0, .5f, 1.5f, 1, 1.5f));
				r.legs(k(p, 0, 0, .5f, 0.3f, 1, 0.25f), k(p, 0, 0, .5f, -0.35f, 1, -0.3f));
				r.lean(k(p, 0, 0, .5f, 0.2f, 1, 0.15f));
				r.twist(k(p, 0, 0.1f, .3f, 0.45f, .5f, -0.5f, 1, -0.45f));
			}
			case UPPERCUT -> {
				r.arm(true, k(p, 0, 0.2f, .35f, 0.45f, .6f, -2.9f, 1, -2.6f), -0.2f, 0.05f);
				r.reach(true, k(p, 0, 0, .35f, 1.0f, .6f, -1.0f, 1, -1.0f));
				r.arm(false, -1.0f, -0.6f, 0.05f);
				r.crouch(k(p, 0, 0, .35f, 0.6f, .6f, 0, 1, 0));
				r.lean(k(p, 0, 0, .35f, 0.3f, .6f, -0.25f, 1, -0.2f));
				r.lift(k(p, 0, 0, .35f, 1.0f, .6f, -1.5f, 1, -1.0f));
				r.twist(k(p, 0, 0, .35f, 0.4f, .6f, -0.3f, 1, -0.25f));
			}
			case BARRAGE -> {
				float beat = Mth.sin(p * Mth.PI * 12);
				r.arm(true, -1.55f, -0.15f, 0.05f);
				r.arm(false, -1.55f, -0.15f, 0.05f);
				r.reach(true, -2.5f * Math.max(0, beat) + 1.5f * Math.max(0, -beat));
				r.reach(false, -2.5f * Math.max(0, -beat) + 1.5f * Math.max(0, beat));
				r.legs(0.3f, -0.3f);
				r.lean(0.25f);
				r.twist(-0.25f * beat);
			}
			case KICK -> {
				r.leg(true, k(p, 0, 0, .3f, 0.6f, .55f, -1.75f, .75f, -1.6f, 1, -0.3f), 0, 0.1f);
				r.arm(true, -0.4f, 0, 0.7f);
				r.arm(false, -0.4f, 0, 0.7f);
				r.lean(k(p, 0, 0, .3f, 0.15f, .55f, -0.35f, 1, -0.15f));
			}
			case SPIN_KICK -> {
				r.leg(true, -0.3f, 0, k(p, 0, 0.3f, .2f, 1.35f, .8f, 1.35f, 1, 0.1f));
				r.arm(true, -0.2f, 0, 1.1f);
				r.arm(false, -0.2f, 0, 1.1f);
				r.lift(k(p, 0, 0, .2f, -1.2f, .8f, -1.2f, 1, 0));
				r.spin(-smooth(clamp((p - 0.1f) / 0.7f)) * Mth.TWO_PI);
			}
			case HEEL_DROP -> {
				r.leg(true, k(p, 0, 0, .4f, -2.7f, .6f, -0.2f, 1, 0), 0, 0.05f);
				float arms = k(p, 0, -0.3f, .4f, -0.6f, .6f, -1.2f, 1, -0.6f);
				r.arm(true, arms, 0, 0.8f);
				r.arm(false, arms, 0, 0.8f);
				r.lean(k(p, 0, 0, .4f, -0.35f, .6f, 0.35f, 1, 0.1f));
				r.lift(k(p, 0, 0, .4f, -4.0f, .6f, 0.5f, 1, 0));
			}
			case CAST -> {
				float x = k(p, 0, -0.3f, .25f, 0.35f, .45f, -1.6f, .85f, -1.6f, 1, -1.4f);
				r.arm(true, x, -0.22f, 0.05f);
				r.arm(false, x, -0.22f, 0.05f);
				float reach = k(p, 0, 0, .25f, 2.0f, .45f, -1.5f, .85f, -1.5f, 1, -1.0f);
				r.reach(true, reach);
				r.reach(false, reach);
				r.legs(k(p, 0, 0, .45f, 0.35f, 1, 0.3f), k(p, 0, 0, .45f, -0.35f, 1, -0.3f));
				r.lean(k(p, 0, 0, .25f, 0.2f, .45f, -0.12f, 1, -0.05f));
			}
			case POINT -> {
				r.arm(true, k(p, 0, -0.5f, .3f, -1.75f, .85f, -1.7f, 1, -1.4f), 0.05f, 0.05f);
				r.arm(false, 0.25f, 0, 0.35f);
				r.twist(k(p, 0, 0, .3f, -0.4f, .85f, -0.4f, 1, -0.2f));
			}
			case SUMMON -> {
				float x = k(p, 0, -0.6f, .35f, -3.0f, .6f, -3.0f, .75f, -1.3f, 1, -1.2f);
				float z = k(p, 0, 0.1f, .35f, 0.35f, .6f, 0.45f, .75f, 0.15f, 1, 0.1f);
				r.arm(true, x, 0, z);
				r.arm(false, x, 0, z);
				r.headPitch(k(p, 0, 0, .35f, -0.45f, .6f, -0.5f, .75f, 0.1f, 1, 0));
				r.lean(k(p, 0, 0, .35f, -0.2f, .6f, -0.2f, .75f, 0.2f, 1, 0.1f));
				r.lift(k(p, 0, 0, .35f, -0.5f, .6f, -0.5f, .75f, 0.5f, 1, 0));
			}
			case POWER_UP -> {
				float shake = p < 0.4f ? Mth.sin(age * 2.5f) * 0.04f : 0;
				float x = k(p, 0, -0.4f, .4f, -1.1f, .55f, 0.15f, 1, 0.1f) + shake;
				float y = k(p, 0, 0, .4f, -0.8f, .55f, 0, 1, 0);
				float z = k(p, 0, 0, .4f, 0, .55f, 1.1f, .85f, 1.0f, 1, 0.6f);
				r.arm(true, x, y, z);
				r.arm(false, x, y, z);
				r.crouch(k(p, 0, 0, .4f, 0.45f, .55f, 0, 1, 0));
				r.headPitch(k(p, 0, 0, .4f, 0.35f, .55f, -0.35f, 1, -0.2f));
				r.lean(k(p, 0, 0, .4f, 0.3f, .55f, -0.25f, 1, -0.15f));
				r.spread(k(p, 0, 0, .55f, 0.25f, 1, 0.2f));
			}
			case ROAR -> {
				float shake = Mth.sin(age * 3.1f) * 0.03f;
				r.arm(true, k(p, 0, 0, .25f, 0.5f, 1, 0.5f) + shake, 0.3f, k(p, 0, 0.1f, .25f, 0.9f, 1, 0.9f));
				r.arm(false, k(p, 0, 0, .25f, 0.5f, 1, 0.5f) - shake, 0.3f, k(p, 0, 0.1f, .25f, 0.9f, 1, 0.9f));
				r.lean(k(p, 0, 0, .25f, -0.3f, 1, -0.3f));
				r.headPitch(k(p, 0, 0, .25f, -0.55f, 1, -0.55f));
				r.spread(0.25f);
			}
			case GROUND_SLAM -> {
				float x = k(p, 0, -0.8f, .4f, -3.05f, .55f, -0.25f, .8f, -0.3f, 1, -0.4f);
				r.arm(true, x, -0.35f, 0.05f);
				r.arm(false, x, -0.35f, 0.05f);
				r.lean(k(p, 0, 0, .4f, -0.25f, .55f, 0.7f, .8f, 0.6f, 1, 0.2f));
				r.crouch(k(p, 0, 0, .4f, 0, .55f, 0.8f, .8f, 0.7f, 1, 0.1f));
				r.lift(k(p, 0, 0, .4f, -1.5f, .55f, 2.0f, .8f, 1.8f, 1, 0.5f));
				r.headPitch(k(p, 0, 0, .4f, -0.3f, .55f, 0.4f, 1, 0.1f));
				r.spread(k(p, 0, 0, .55f, 0.2f, 1, 0.1f));
			}
			case POUNCE -> {
				float x = k(p, 0, 0.3f, .35f, 0.7f, .55f, -2.4f, .8f, -2.2f, 1, -1.2f);
				r.arm(true, x, 0.25f, k(p, 0, 0, .55f, 0.35f, 1, 0.2f));
				r.arm(false, x, 0.25f, k(p, 0, 0, .55f, 0.35f, 1, 0.2f));
				r.crouch(k(p, 0, 0, .35f, 0.8f, .55f, 0, 1, 0.1f));
				r.lean(k(p, 0, 0, .35f, 0.4f, .55f, 0.5f, 1, 0.15f));
				r.lift(k(p, 0, 0, .35f, 1.5f, .55f, -2.5f, .8f, -1.5f, 1, 0));
				r.legs(k(p, 0, 0, .55f, 0.6f, 1, 0.1f), k(p, 0, 0, .55f, -0.4f, 1, -0.1f));
			}
			case CLAW -> {
				r.arm(true, k(p, 0, -1.2f, .3f, -2.6f, .55f, -0.5f, 1, -0.6f), k(p, 0, 0, .3f, 0.8f, .55f, -0.9f, 1, -0.8f),
						k(p, 0, 0.1f, .3f, 0.4f, .55f, 0, 1, 0));
				r.arm(false, -0.8f, 0.4f, 0.3f);
				r.lean(k(p, 0, 0, .55f, 0.25f, 1, 0.2f));
				r.twist(k(p, 0, 0, .3f, 0.45f, .55f, -0.5f, 1, -0.4f));
			}
			case DASH -> {
				r.arm(true, 1.1f, 0, 0.25f);
				r.arm(false, 1.1f, 0, 0.25f);
				r.legs(-0.5f, 0.45f);
				r.lean(0.75f);
				r.headPitch(-0.5f);
			}
			case THROW -> {
				r.arm(true, k(p, 0, -0.5f, .4f, -2.8f, .6f, -0.9f, 1, -0.7f), 0, 0.1f);
				r.reach(true, k(p, 0, 0, .4f, 3.0f, .6f, -1.0f, 1, -0.5f));
				r.arm(false, k(p, 0, -0.5f, .4f, -1.4f, .6f, -0.3f, 1, -0.2f), 0.3f, 0.1f);
				r.legs(k(p, 0, 0, .6f, 0.35f, 1, 0.3f), k(p, 0, 0, .6f, -0.45f, 1, -0.4f));
				r.lean(k(p, 0, 0, .4f, -0.2f, .6f, 0.35f, 1, 0.2f));
				r.twist(k(p, 0, 0, .4f, 0.55f, .6f, -0.5f, 1, -0.35f));
			}
			case FLICK -> {
				r.arm(true, -1.45f, k(p, 0, -0.7f, .35f, -0.9f, .5f, 0.6f, 1, 0.5f), k(p, 0, 0.1f, .35f, 0.3f, .5f, 0.1f, 1, 0.1f));
				r.arm(false, -0.3f, 0, 0.2f);
				r.twist(k(p, 0, 0, .35f, -0.35f, .5f, 0.3f, 1, 0.2f));
			}
			case SHOOT -> {
				float aim = -Mth.HALF_PI + r.model.head.xRot;
				float recoil = k(p, 0, 0, .6f, 0, .7f, -0.25f, 1, 0);
				r.arm(true, aim + recoil, -0.1f, 0);
				r.arm(false, aim + recoil, -0.5f, 0);
				r.reach(true, k(p, 0, 0, .55f, 3.0f, .62f, 0, 1, 0));
			}
			case GUARD -> {
				r.arm(true, -1.25f, -0.85f, 0.05f);
				r.arm(false, -1.15f, -0.85f, 0.05f);
				r.crouch(0.35f);
				r.spread(0.2f);
			}
		}
	}

	/**
	 * Holding a gun. aim: 0 = carrying it ready, 1 = aimed where the head looks. shot: 0 -> 1 through the recoil
	 * of a shot, or -1. The gun model points along the arm (see tools/guns), so pointing the arm points the gun.
	 */
	private static void gun(Rig r, GunItem.Hold hold, float aim, float shot, HumanoidRenderState state) {
		float pitch = r.model.head.xRot;
		float yaw = r.model.head.yRot * (r.mirror ? -1 : 1);
		float bob = Mth.sin(state.ageInTicks * 0.08f) * 0.03f * (1 - aim);
		// Recoil: a sharp kick up and back, then settle.
		float kick = shot < 0 ? 0 : k(shot, 0, 0, .1f, 1, .55f, 0.15f, 1, 0);
		float aimX = -Mth.HALF_PI + pitch;
		switch (hold) {
			case PISTOL -> {
				// One hand. Ready: low, pointing ahead at the ground. Aimed: arm straight out at the target.
				r.arm(true, Mth.lerp(aim, -0.85f + bob, aimX) - 0.45f * kick, Mth.lerp(aim, -0.15f, yaw - 0.05f), 0);
				r.reach(true, 1.5f * kick);
				if (aim > 0) {
					// Free hand drops back a little for balance.
					float w = r.w;
					r.w = w * aim;
					r.arm(false, 0.25f, 0, 0.15f);
					r.w = w;
				}
			}
			case RIFLE -> {
				// Both hands. Ready: held low across the body. Aimed: butt in the shoulder, off hand under the barrel.
				r.twist(0.3f * aim);
				r.arm(true, Mth.lerp(aim, -0.95f + bob, aimX + 0.05f) - 0.2f * kick, Mth.lerp(aim, -0.55f, yaw - 0.12f), 0);
				r.arm(false, Mth.lerp(aim, -1.2f + bob, aimX - 0.05f) - 0.2f * kick, Mth.lerp(aim, -0.75f, yaw - 0.75f), 0);
				r.reach(true, 2.5f * kick);
				r.reach(false, 2.5f * kick);
				r.lean(-0.08f * kick);
			}
			case SLINGSHOT -> {
				// Slingshot out front in the gun hand, the other hand draws the band back to the cheek.
				float draw = shot < 0 ? 1 : k(shot, 0, 1, .08f, 0, .6f, 0, 1, 1);
				r.arm(true, Mth.lerp(aim, -0.6f + bob, aimX), Mth.lerp(aim, -0.1f, yaw - 0.1f), 0);
				r.arm(false, Mth.lerp(aim, 0.1f, aimX), Mth.lerp(aim, 0, yaw - 0.55f * draw - 0.15f), 0);
				r.reach(false, 3.0f * draw * aim);
			}
		}
	}

	/** Fighting stance while a mob has a target. Added over the walk, so the legs still walk. */
	private static void stance(Rig r, AnimClient.Stance stance, float age) {
		float bob = Mth.sin(age * 0.2f) * 0.06f;
		if (stance == AnimClient.Stance.FISTS) {
			r.arm(true, -1.0f + bob, -0.45f, 0.05f);
			r.arm(false, -1.15f - bob, -0.45f, 0.05f);
			r.reach(false, -1.0f);
			r.crouch(0.15f);
		} else {
			r.arm(true, -0.75f + bob, 0.15f, 0.05f);
			r.arm(false, -0.5f, -0.3f, 0.1f);
			r.crouch(0.1f);
		}
	}

	/** Standing around: each character always uses the same one (see AnimClient). */
	private static void idle(Rig r, AnimClient.Idle idle) {
		switch (idle) {
			case ARMS_CROSSED -> {
				r.arm(true, -0.8f, -0.75f, 0);
				r.arm(false, -0.7f, -0.8f, 0);
			}
			case HANDS_ON_HIPS -> {
				r.arm(true, 0.15f, 0, 0.5f);
				r.arm(false, 0.15f, 0, 0.5f);
			}
			case SWORD_ON_SHOULDER -> r.arm(true, -2.4f, -0.45f, 0.1f);
			default -> {
			}
		}
	}

	// ---------- Helpers ----------

	/** One model plus how strongly (w, 0-1) the animation overrides Minecraft's own pose this frame. */
	private static final class Rig {
		final HumanoidModel<?> model;
		final HumanoidRenderState state;
		boolean mirror;
		float w = 1;

		Rig(HumanoidModel<?> model, HumanoidRenderState state) {
			this.model = model;
			this.state = state;
		}

		private ModelPart arm(boolean main) {
			return main != mirror ? model.rightArm : model.leftArm;
		}

		private ModelPart leg(boolean main) {
			return main != mirror ? model.rightLeg : model.leftLeg;
		}

		/** Sign that turns "outward" for the right side into outward for this part. */
		private float side(ModelPart part) {
			return part == model.leftArm || part == model.leftLeg ? -1 : 1;
		}

		void arm(boolean main, float x, float y, float z) {
			ModelPart part = arm(main);
			part.xRot = Mth.lerp(w, part.xRot, x);
			part.yRot = Mth.lerp(w, part.yRot, y * side(part));
			part.zRot = Mth.lerp(w, part.zRot, z * side(part));
		}

		void leg(boolean main, float x, float y, float z) {
			ModelPart part = leg(main);
			part.xRot = Mth.lerp(w, part.xRot, x);
			part.yRot = Mth.lerp(w, part.yRot, y * side(part));
			part.zRot = Mth.lerp(w, part.zRot, z * side(part));
		}

		void legs(float main, float off) {
			ModelPart a = leg(true);
			a.xRot = Mth.lerp(w, a.xRot, main);
			ModelPart b = leg(false);
			b.xRot = Mth.lerp(w, b.xRot, off);
		}

		/** Moves a shoulder forward (-) or back (+), in skin pixels. */
		void reach(boolean main, float z) {
			arm(main).z += z * w;
		}

		/** Leans the upper body forward (+) or back (-). It hangs from the neck, so the hips (and legs) move. */
		void lean(float x) {
			float before = model.body.xRot;
			model.body.xRot = Mth.lerp(w, before, x);
			float dz = 12 * (Mth.sin(model.body.xRot) - Mth.sin(before));
			float dy = 12 * (Mth.cos(model.body.xRot) - Mth.cos(before));
			// Keep the feet on the ground: the hips swing back, the upper body sinks to meet them.
			model.rightLeg.z += dz;
			model.leftLeg.z += dz;
			for (ModelPart part : new ModelPart[] {model.body, model.head, model.rightArm, model.leftArm}) {
				part.y -= dy;
			}
		}

		void headPitch(float x) {
			model.head.xRot += x * w;
		}

		/** Turns the upper body (+ = toward the main side), carrying the arms around with it. */
		void twist(float angle) {
			float a = angle * w * (mirror ? -1 : 1);
			model.body.yRot += a;
			model.head.yRot += a * 0.3f;
			for (ModelPart part : new ModelPart[] {model.rightArm, model.leftArm}) {
				float cos = Mth.cos(a);
				float sin = Mth.sin(a);
				float x = part.x;
				float z = part.z;
				part.x = x * cos + z * sin;
				part.z = -x * sin + z * cos;
				part.yRot += a;
			}
		}

		/** Bends down like sneaking (0 = standing, 1 = full crouch). */
		void crouch(float t) {
			t *= w;
			model.body.xRot += 0.5f * t;
			model.body.y += 3.2f * t;
			model.head.y += 4.2f * t;
			model.rightArm.y += 3.2f * t;
			model.leftArm.y += 3.2f * t;
			model.rightLeg.z += 4.0f * t;
			model.leftLeg.z += 4.0f * t;
			model.rightLeg.y += 0.2f * t;
			model.leftLeg.y += 0.2f * t;
		}

		/** Spreads the feet apart. */
		void spread(float z) {
			model.rightLeg.zRot = Mth.lerp(w, model.rightLeg.zRot, z);
			model.leftLeg.zRot = Mth.lerp(w, model.leftLeg.zRot, -z);
		}

		/** Moves the whole body up (-) or down (+), in skin pixels: hops and squats. */
		void lift(float y) {
			model.root().y += y * w;
		}

		/** Spins the whole body around (radians). */
		void spin(float angle) {
			model.root().yRot += angle * (mirror ? -1 : 1);
		}
	}

	/** Keyframes: k(p, t0, v0, t1, v1, ...), smoothly from one value to the next. */
	private static float k(float p, float... keys) {
		if (p <= keys[0]) {
			return keys[1];
		}
		for (int i = 2; i < keys.length; i += 2) {
			if (p <= keys[i]) {
				float t = (p - keys[i - 2]) / Math.max(1.0e-4f, keys[i] - keys[i - 2]);
				return Mth.lerp(smooth(t), keys[i - 1], keys[i + 1]);
			}
		}
		return keys[keys.length - 1];
	}

	private static float smooth(float t) {
		t = clamp(t);
		return t * t * (3 - 2 * t);
	}

	private static float clamp(float t) {
		return t < 0 ? 0 : t > 1 ? 1 : t;
	}
}
