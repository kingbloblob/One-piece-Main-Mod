package com.onepiecemod.zoan.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import com.mojang.blaze3d.vertex.PoseStack;

import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.LivingEntityRenderer;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.world.entity.LivingEntity;

import com.onepiecemod.zoan.client.ZoanClient;

/** Players in a full-body Zoan form are drawn as the animal (ZoanClient) instead of as a person. */
@Mixin(LivingEntityRenderer.class)
public abstract class ZoanRenderMixin {
	@Inject(method = "extractRenderState(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/client/renderer/entity/state/LivingEntityRenderState;F)V", at = @At("TAIL"))
	private void onepiece$extractZoan(LivingEntity entity, LivingEntityRenderState state, float partialTick, CallbackInfo ci) {
		ZoanClient.extract(entity, state, partialTick);
	}

	@Inject(method = "submit(Lnet/minecraft/client/renderer/entity/state/LivingEntityRenderState;Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/SubmitNodeCollector;Lnet/minecraft/client/renderer/state/level/CameraRenderState;)V",
			at = @At("HEAD"), cancellable = true)
	private void onepiece$submitZoan(LivingEntityRenderState state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera, CallbackInfo ci) {
		if (ZoanClient.submit(state, poseStack, collector)) {
			ci.cancel();
		}
	}
}
