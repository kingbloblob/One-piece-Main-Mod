package com.onepiecemod.town.client;

import net.minecraft.client.renderer.entity.EntityRenderers;

import com.onepiecemod.town.TownFeature;

/** Client side of the towns: how townsfolk look. OnePieceModClient calls initialize() once. */
public class TownClient {
	public static void initialize() {
		EntityRenderers.register(TownFeature.TOWNSFOLK, TownsfolkRenderer::new);
	}
}
