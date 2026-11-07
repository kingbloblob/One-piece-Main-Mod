package com.onepiecemod.client;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.client.animation.AnimationChannel;
import net.minecraft.client.animation.AnimationDefinition;
import net.minecraft.client.animation.Keyframe;
import net.minecraft.client.animation.KeyframeAnimations;

/**
 * A short way to write Minecraft keyframe animations in code (the system the Warden and Camel use).
 * Every value is added to the part's resting pose: rotations in degrees, positions in pixels.
 *
 *   Keyframes anim = new Keyframes(0.5f);
 *   anim.rot("jaw", 0, 0, 0, 0).rot("jaw", 0.15f, 40, 0, 0).rot("jaw", 0.5f, 0, 0, 0);
 *   AnimationDefinition bite = anim.build();
 *
 * Only add parts the model really has: baking an animation for a missing part fails.
 */
public final class Keyframes {
	private final AnimationDefinition.Builder builder;
	private final java.util.Map<String, List<Keyframe>> rotations = new java.util.LinkedHashMap<>();
	private final java.util.Map<String, List<Keyframe>> positions = new java.util.LinkedHashMap<>();

	public Keyframes(float seconds) {
		this.builder = AnimationDefinition.Builder.withLength(seconds);
	}

	public Keyframes looping() {
		builder.looping();
		return this;
	}

	public Keyframes rot(String part, float time, float x, float y, float z) {
		rotations.computeIfAbsent(part, p -> new ArrayList<>())
				.add(new Keyframe(time, KeyframeAnimations.degreeVec(x, y, z), AnimationChannel.Interpolations.CATMULLROM));
		return this;
	}

	public Keyframes pos(String part, float time, float x, float y, float z) {
		positions.computeIfAbsent(part, p -> new ArrayList<>())
				.add(new Keyframe(time, KeyframeAnimations.posVec(x, y, z), AnimationChannel.Interpolations.CATMULLROM));
		return this;
	}

	public AnimationDefinition build() {
		rotations.forEach((part, keys) -> builder.addAnimation(part,
				new AnimationChannel(AnimationChannel.Targets.ROTATION, keys.toArray(Keyframe[]::new))));
		positions.forEach((part, keys) -> builder.addAnimation(part,
				new AnimationChannel(AnimationChannel.Targets.POSITION, keys.toArray(Keyframe[]::new))));
		return builder.build();
	}
}
