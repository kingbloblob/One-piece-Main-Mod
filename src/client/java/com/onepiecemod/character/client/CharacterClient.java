package com.onepiecemod.character.client;

import net.minecraft.client.renderer.entity.EntityRenderers;

import com.onepiecemod.character.CharacterFeature;

/**
 * Client-only setup for characters. OnePieceModClient calls initialize().
 */
public class CharacterClient {
	public static void initialize() {
		GiantModels.register();
		CharacterRenderer.registerLayers();
		BossForms.initialize();
		QuestMarkerClient.initialize();
		EntityRenderers.register(CharacterFeature.CHARACTER, CharacterRenderer::new);
	}
}
