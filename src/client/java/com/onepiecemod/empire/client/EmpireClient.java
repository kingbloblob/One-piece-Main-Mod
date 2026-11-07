package com.onepiecemod.empire.client;

import net.minecraft.client.renderer.entity.EntityRenderers;

import com.onepiecemod.empire.EmpireFeature;

/**
 * Client-only setup for the empire feature. OnePieceModClient calls initialize().
 */
public class EmpireClient {
	public static void initialize() {
		EntityRenderers.register(EmpireFeature.PIRATE_GUARD, PirateGuardRenderer::new);
	}
}
