package com.onepiecemod.seatrain.client;

import net.minecraft.client.renderer.entity.EntityRenderers;
import net.minecraft.client.renderer.entity.NoopRenderer;

import com.onepiecemod.seatrain.SeaTrainFeature;

/** The train's root draws nothing: the engine and carriages are block displays riding it. */
public class SeaTrainClient {
	public static void initialize() {
		EntityRenderers.register(SeaTrainFeature.SEA_TRAIN, NoopRenderer::new);
	}
}
