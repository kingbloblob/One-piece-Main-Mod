package com.onepiecemod.furniture.client;

import net.minecraft.client.renderer.entity.EntityRenderers;
import net.minecraft.client.renderer.entity.NoopRenderer;

import com.onepiecemod.furniture.Furniture;

/** The seat you ride on a chair has nothing to draw. */
public class FurnitureClient {
	public static void initialize() {
		EntityRenderers.register(Furniture.SEAT, NoopRenderer::new);
	}
}
