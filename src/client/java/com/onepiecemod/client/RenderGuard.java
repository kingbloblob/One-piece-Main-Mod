package com.onepiecemod.client;

import java.util.HashSet;
import java.util.Set;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.mojang.blaze3d.vertex.PoseStack;

/**
 * Keeps one broken drawing from crashing the whole game. Minecraft turns any error inside a renderer
 * into a crash, so our renderers run their drawing through here: if something goes wrong, that thing
 * is simply not drawn and the log gets one line about it.
 */
public final class RenderGuard {
	private static final Logger LOGGER = LoggerFactory.getLogger("onepiece/render");
	private static final Set<String> REPORTED = new HashSet<>();

	private RenderGuard() {
	}

	/** Runs a drawing step that pushes and pops the pose stack. On an error, the stack is put back the way it was. */
	public static void run(String what, PoseStack poseStack, Runnable draw) {
		PoseStack.Pose before = poseStack.last();
		try {
			draw.run();
		} catch (RuntimeException e) {
			while (poseStack.last() != before && !poseStack.isEmpty()) {
				poseStack.popPose();
			}
			report(what, e);
		}
	}

	/** Runs a step that doesn't draw (like reading an entity's state for the next frame). */
	public static void run(String what, Runnable step) {
		try {
			step.run();
		} catch (RuntimeException e) {
			report(what, e);
		}
	}

	private static void report(String what, RuntimeException e) {
		// Log each broken renderer once, not 60 times a second.
		if (REPORTED.add(what)) {
			LOGGER.error("Skipped drawing {} after an error (it won't crash the game)", what, e);
		}
	}
}
