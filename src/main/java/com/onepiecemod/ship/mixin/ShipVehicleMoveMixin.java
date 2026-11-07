package com.onepiecemod.ship.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.phys.AABB;

import com.onepiecemod.ship.ShipEntity;

/**
 * When the captain's game moves a ship, the server checks that the ship's box didn't sail into any block it wasn't
 * already touching, and pulls it back if it did. A ship's box is a big square around the whole hull (masts too), so
 * sailing past a pier or along a beach failed that check and the ship stuck there. The captain's game already bumps
 * the real hull into the world (ShipEntity.sail), so ships skip the box check.
 */
@Mixin(ServerGamePacketListenerImpl.class)
public abstract class ShipVehicleMoveMixin {
	@Inject(method = "isEntityCollidingWithAnythingNew", at = @At("HEAD"), cancellable = true)
	private void onepiece$shipsUseTheirHull(LevelReader level, Entity entity, AABB oldBox, double x, double y, double z,
			CallbackInfoReturnable<Boolean> cir) {
		if (entity instanceof ShipEntity) {
			cir.setReturnValue(false);
		}
	}
}
