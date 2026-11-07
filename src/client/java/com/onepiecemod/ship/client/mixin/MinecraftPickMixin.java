package com.onepiecemod.ship.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;

import com.onepiecemod.ship.client.ShipPick;

/**
 * After the game works out what the crosshair is on each frame, check for a ship it missed (see ShipPick): big ships
 * are only found by the game when their centre is near the player, which from their own deck it rarely is.
 */
@Mixin(Minecraft.class)
public abstract class MinecraftPickMixin {
	@Shadow public HitResult hitResult;
	@Shadow public Entity crosshairPickEntity;
	@Shadow public LocalPlayer player;

	@Shadow public abstract Entity getCameraEntity();

	@Inject(method = "pick(F)V", at = @At("TAIL"))
	private void onepiece$pickShip(float partialTick, CallbackInfo ci) {
		Entity camera = getCameraEntity();
		if (camera == null || player == null) {
			return;
		}
		HitResult picked = ShipPick.pick(camera, player, partialTick, hitResult);
		if (picked != null) {
			hitResult = picked;
			crosshairPickEntity = picked instanceof EntityHitResult entityHit ? entityHit.getEntity() : null;
		}
	}
}
