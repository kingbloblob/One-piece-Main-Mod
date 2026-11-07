package com.onepiecemod.weapon.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.minecraft.client.player.AbstractClientPlayer;

import com.onepiecemod.weapon.client.WeaponClient;

/**
 * Zooms the view in while you aim (sneak) with the Senriku or a gun with a Scope, like a spyglass.
 * Minecraft eases the zoom in and out by itself.
 */
@Mixin(AbstractClientPlayer.class)
public abstract class GunZoomMixin {
	@Inject(method = "getFieldOfViewModifier(ZF)F", at = @At("RETURN"), cancellable = true)
	private void onepiece$gunZoom(boolean firstPerson, float effectScale, CallbackInfoReturnable<Float> cir) {
		float zoom = WeaponClient.zoom((AbstractClientPlayer) (Object) this, firstPerson);
		if (zoom < 1.0f) {
			cir.setReturnValue(cir.getReturnValueF() * zoom);
		}
	}
}
