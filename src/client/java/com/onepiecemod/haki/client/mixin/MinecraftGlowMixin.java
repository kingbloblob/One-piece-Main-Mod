package com.onepiecemod.haki.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.Entity;

import com.onepiecemod.haki.client.HakiSenseClient;

/** Creatures sensed by your own Observation Haki get the glowing outline, on your screen only. */
@Mixin(Minecraft.class)
public abstract class MinecraftGlowMixin {
	@Inject(method = "shouldEntityAppearGlowing(Lnet/minecraft/world/entity/Entity;)Z", at = @At("HEAD"), cancellable = true)
	private void onepiece$hakiSense(Entity entity, CallbackInfoReturnable<Boolean> cir) {
		if (HakiSenseClient.isSensed(entity)) {
			cir.setReturnValue(true);
		}
	}
}
