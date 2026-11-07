package com.onepiecemod.body.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.entity.player.AvatarRenderer;
import net.minecraft.world.entity.Entity;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.LivingEntityRenderLayerRegistrationCallback;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.RenderStateDataKey;

import com.onepiecemod.body.Body;
import com.onepiecemod.body.Look;
import com.onepiecemod.body.BodyAttachments;
import com.onepiecemod.body.BodyFeature;

/**
 * Opens the body screen when the server asks, and tells the player renderer about body shapes.
 */
public class BodyClient {
	/** Carries a player's body shape from the renderer to the model each frame. */
	public static final RenderStateDataKey<Body> BODY_KEY = RenderStateDataKey.create(() -> "onepiece:body");

	/** While the body screen is open, your own player is drawn with the sliders' values instead of your saved ones. */
	static Body preview = null;

	/** While the body screen is open, your own player is drawn with the screen's hair, scar and outfit. */
	static Look previewLook = null;

	/** Set when the server asked for the screen while the world was still loading. */
	private static BodyFeature.OpenEditor wanted = null;

	@SuppressWarnings("unchecked")
	public static void initialize() {
		ModelLayerRegistry.registerModelLayer(AppearanceModels.FEATURES, AppearanceModels::features);
		ModelLayerRegistry.registerModelLayer(AppearanceModels.HAIR, AppearanceModels::hair);
		LivingEntityRenderLayerRegistrationCallback.EVENT.register((type, renderer, helper, context) -> {
			if (renderer instanceof AvatarRenderer<?> avatar) {
				helper.register(new AppearanceLayer((AvatarRenderer) avatar, context));
			}
		});

		ClientPlayNetworking.registerGlobalReceiver(BodyFeature.OpenEditor.TYPE, (payload, context) -> wanted = payload);

		// Wait until no other screen (loading, race picker) is open, then show the body screen.
		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			if (wanted != null && client.player != null && client.gui.screen() == null) {
				boolean firstTime = wanted.firstTime();
				wanted = null;
				client.gui.setScreen(new BodyEditorScreen(firstTime));
			}
		});
	}

	/** The body shape to draw this entity with, or null for a normal Minecraft body. */
	public static Body bodyFor(Entity entity) {
		if (preview != null && entity == Minecraft.getInstance().player) {
			return preview;
		}
		return BodyAttachments.get(entity);
	}

	/** The hair, scar and outfit to draw this entity with. */
	public static Look lookFor(Entity entity) {
		if (previewLook != null && entity == Minecraft.getInstance().player) {
			return previewLook;
		}
		return BodyAttachments.look(entity);
	}
}
