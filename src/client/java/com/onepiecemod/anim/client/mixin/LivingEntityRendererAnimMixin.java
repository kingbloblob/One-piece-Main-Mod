package com.onepiecemod.anim.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.client.renderer.entity.LivingEntityRenderer;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.world.entity.LivingEntity;

import com.onepiecemod.anim.client.AnimClient;

/**
 * When Minecraft gathers what it needs to draw a mob or player this frame, also note which custom
 * animation it's playing (see AnimClient), so HumanoidModelAnimMixin can pose the model.
 */
@Mixin(LivingEntityRenderer.class)
public abstract class LivingEntityRendererAnimMixin {
	@Inject(method = "extractRenderState(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/client/renderer/entity/state/LivingEntityRenderState;F)V", at = @At("TAIL"))
	private void onepiece$extractAnim(LivingEntity entity, LivingEntityRenderState state, float partialTick, CallbackInfo ci) {
		AnimClient.extract(entity, state, partialTick);
	}
}
