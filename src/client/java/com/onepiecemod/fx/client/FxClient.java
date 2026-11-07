package com.onepiecemod.fx.client;

import net.minecraft.client.renderer.entity.EntityRenderers;
import net.minecraft.client.renderer.entity.player.AvatarRenderer;

import net.fabricmc.fabric.api.client.rendering.v1.LivingEntityRenderLayerRegistrationCallback;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;

import com.onepiecemod.fx.FxFeature;

/**
 * Client-only setup for move effects: how they are drawn, and the black Armament Haki arms.
 * OnePieceModClient calls initialize().
 */
public class FxClient {
	@SuppressWarnings("unchecked")
	public static void initialize() {
		EntityRenderers.register(FxFeature.MOVE_EFFECT, MoveRenderer::new);

		ModelLayerRegistry.registerModelLayer(ArmamentLayer.WIDE, () -> ArmamentLayer.createLayer(false));
		ModelLayerRegistry.registerModelLayer(ArmamentLayer.SLIM, () -> ArmamentLayer.createLayer(true));
		ModelLayerRegistry.registerModelLayer(ElementLayer.WIDE, () -> ElementLayer.createLayer(false));
		ModelLayerRegistry.registerModelLayer(ElementLayer.SLIM, () -> ElementLayer.createLayer(true));
		LivingEntityRenderLayerRegistrationCallback.EVENT.register((type, renderer, helper, context) -> {
			if (renderer instanceof AvatarRenderer<?> avatar) {
				helper.register(new ArmamentLayer((AvatarRenderer) avatar, context));
				helper.register(new ElementLayer((AvatarRenderer) avatar, context));
			}
		});
	}
}
