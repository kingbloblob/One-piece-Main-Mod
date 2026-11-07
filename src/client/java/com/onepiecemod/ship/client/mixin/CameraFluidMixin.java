package com.onepiecemod.ship.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.minecraft.client.Camera;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.material.FogType;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.ship.ShipHold;

/** No underwater fog when the camera is in a ship's dry hold below the waterline, or at a diving ship's wheel (see ShipHold). */
@Mixin(Camera.class)
public abstract class CameraFluidMixin {
	@Shadow
	private Level level;

	@Shadow
	private Vec3 position;

	@Shadow
	private net.minecraft.world.entity.Entity entity;

	@Inject(method = "getFluidInCamera", at = @At("RETURN"), cancellable = true)
	private void onepiece$dryHold(CallbackInfoReturnable<FogType> cir) {
		if (cir.getReturnValue() == FogType.WATER && level != null
				&& (ShipHold.isDry(level, position) || entity != null && entity.getVehicle() != null && ShipHold.isDry(entity))) {
			cir.setReturnValue(FogType.NONE);
		}
	}
}
