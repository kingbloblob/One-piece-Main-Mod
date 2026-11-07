package com.onepiecemod.character.client;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * The model for giant characters (see GiantModels). Same as a player model, plus a 3D cape in three
 * hinged pieces (cape0 > cape1 > cape2, children of the body) that hangs, sways and flies back as they walk.
 */
public class GiantModel extends HumanoidModel<CharacterRenderer.State> {
	private final ModelPart cape0;
	private final ModelPart cape1;
	private final ModelPart cape2;
	/** Parts this character does not have (Shanks' left arm); see GiantModels.hidden. */
	private final List<ModelPart> hidden = new ArrayList<>();
	/** How far arms and legs swing (Chopper's short limbs swing less); see GiantModels.swing. */
	private final float swing;
	/** Extra leg length (Doflamingo, Aokiji...): everything above the hips is raised this much; see GiantModels.legs. */
	private final float legs;
	/** Shoulders moved out for very wide bodies (Big Mom), so held items clear the body; see GiantModels.armsOut. */
	private final float armsOut;

	public GiantModel(ModelPart root, String id) {
		super(root);
		for (String name : GiantModels.hidden(id)) {
			if (root.hasChild(name)) {
				hidden.add(root.getChild(name));
			}
		}
		// A reshaped body: the normal box of these parts is skipped, the character's own boxes (children) still draw.
		for (String name : GiantModels.stripped(id)) {
			if (root.hasChild(name)) {
				root.getChild(name).skipDraw = true;
			} else if (head.hasChild(name)) {
				head.getChild(name).skipDraw = true;
			}
		}
		this.swing = GiantModels.swing(id);
		this.legs = GiantModels.legs(id);
		this.armsOut = GiantModels.armsOut(id);
		this.cape0 = body.hasChild("cape0") ? body.getChild("cape0") : null;
		this.cape1 = cape0 != null && cape0.hasChild("cape1") ? cape0.getChild("cape1") : null;
		this.cape2 = cape1 != null && cape1.hasChild("cape2") ? cape1.getChild("cape2") : null;
	}

	@Override
	public void setupAnim(CharacterRenderer.State state) {
		super.setupAnim(state);
		for (ModelPart part : hidden) {
			part.visible = false;
		}
		if (legs > 0) {
			head.y -= legs;
			body.y -= legs;
			rightArm.y -= legs;
			leftArm.y -= legs;
			rightLeg.y -= legs;
			leftLeg.y -= legs;
		}
		if (armsOut > 0) {
			rightArm.x -= armsOut;
			leftArm.x += armsOut;
		}
		if (swing != 1.0F) {
			rightArm.xRot *= swing;
			leftArm.xRot *= swing;
			rightLeg.xRot *= swing;
			leftLeg.xRot *= swing;
		}
		if (cape0 == null) {
			return;
		}
		float speed = Math.min(1.0F, state.walkAnimationSpeed);
		float sway = Mth.sin(state.ageInTicks * 0.09F) * 0.04F;
		float step = Mth.sin(state.walkAnimationPos * 0.6662F) * 0.08F * speed;
		// Positive x rotation lifts the cape out behind the back.
		cape0.xRot = 0.05F + speed * 0.5F + sway + step;
		if (cape1 != null) {
			cape1.xRot = 0.04F + speed * 0.25F + sway * 1.4F + step;
		}
		if (cape2 != null) {
			cape2.xRot = 0.04F + speed * 0.2F + sway * 1.8F - step;
		}
	}
}
