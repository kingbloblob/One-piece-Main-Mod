package com.onepiecemod.sea.client;

import net.minecraft.client.renderer.entity.EntityRenderers;

import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;

import com.onepiecemod.sea.SeaEntities;

/**
 * Client-only setup for the sea: how the Sea King looks. OnePieceModClient calls initialize().
 * The Log Pose and Eternal Pose needles need no code here: their item model files turn them.
 */
public class SeaClient {
	public static void initialize() {
		ModelLayerRegistry.registerModelLayer(SeaKingModel.LAYER, SeaKingModel::createBodyLayer);
		for (int i = 1; i < SeaKingModel.LAYERS.length; i++) {
			int style = i;
			ModelLayerRegistry.registerModelLayer(SeaKingModel.LAYERS[i], () -> SeaKingModel.createBodyLayer(style));
		}
		EntityRenderers.register(SeaEntities.SEA_KING, SeaKingRenderer::new);
	}
}
