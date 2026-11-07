package com.onepiecemod.body.client;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;

import com.onepiecemod.body.Body;

/**
 * Turns the slider values into a player model shape, by stretching the model's parts
 * (body, arms, legs, head) wider or thinner. Sleeves, pants, jacket and hat layers are attached
 * to those parts, so they stretch along. Armor uses the same code, so it still fits.
 *
 * Model units are skin pixels: the body is 8 wide and 4 deep, arms and legs are 4 wide.
 */
public class BodyShape {
	public static void apply(HumanoidModel<?> model, Body body) {
		float weight = body.weight();

		// Torso: weight makes it wider and deeper, a big chest mostly makes it deeper.
		float torsoWidth = 1 + 0.2f * weight + 0.08f * body.chest();
		float torsoDepth = 1 + 0.3f * weight + 0.3f * body.chest();
		// Arms and legs: their own slider, plus a bit of weight.
		float armSize = 1 + 0.25f * body.arms() + 0.12f * weight;
		float legSize = 1 + 0.3f * body.legs() + 0.15f * weight;
		float headSize = 1 + 0.15f * body.head();

		scale(model.body, torsoWidth, 1, torsoDepth);
		scale(model.rightArm, armSize, 1, armSize);
		scale(model.leftArm, armSize, 1, armSize);
		scale(model.rightLeg, legSize, 1, legSize);
		scale(model.leftLeg, legSize, 1, legSize);
		scale(model.head, headSize, headSize, headSize);

		// Move the arms out (or in) so they still touch the sides of the wider (or thinner) torso.
		// The torso is 4 pixels either side of the middle; each arm reaches 1 pixel past its pivot towards it.
		float armShift = 4 * (torsoWidth - 1) + (armSize - 1);
		model.rightArm.x -= armShift;
		model.leftArm.x += armShift;
		// Legs are 2 pixels either side of their pivot, so thick legs move apart a little instead of overlapping.
		float legShift = 2 * (legSize - 1);
		model.rightLeg.x -= legShift;
		model.leftLeg.x += legShift;
	}

	private static void scale(ModelPart part, float x, float y, float z) {
		part.xScale *= x;
		part.yScale *= y;
		part.zScale *= z;
	}
}
