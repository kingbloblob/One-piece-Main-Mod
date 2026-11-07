package com.onepiecemod.body.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;

import net.fabricmc.fabric.api.client.rendering.v1.FabricRenderState;

import com.onepiecemod.body.Body;
import com.onepiecemod.body.client.BodyClient;
import com.onepiecemod.body.client.BodyShape;

/**
 * After Minecraft poses a player-shaped model for this frame (walking, swinging, crouching...),
 * stretch it to the player's body shape. This runs for the player model and their armor.
 */
@Mixin(HumanoidModel.class)
public abstract class HumanoidModelMixin {
	@Inject(method = "setupAnim(Lnet/minecraft/client/renderer/entity/state/HumanoidRenderState;)V", at = @At("TAIL"))
	private void onepiece$applyBody(HumanoidRenderState state, CallbackInfo ci) {
		// Only players carry body data (see AvatarRendererMixin), so zombies and characters are left alone.
		Body body = ((FabricRenderState) state).getData(BodyClient.BODY_KEY);
		if (body != null) {
			BodyShape.apply((HumanoidModel<?>) (Object) this, body);
		}
	}
}
