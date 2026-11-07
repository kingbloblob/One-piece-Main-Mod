package com.onepiecemod.ship.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.ship.ShipDecks;

/**
 * After the game works out how far something can move before it bumps into blocks, also bump it into the blocks of
 * sailing ships, so people and mobs can walk on a ship's deck while she sails (see ShipDecks).
 */
@Mixin(Entity.class)
public abstract class EntityCollideMixin {
	@Inject(method = "collide(Lnet/minecraft/world/phys/Vec3;)Lnet/minecraft/world/phys/Vec3;", at = @At("RETURN"), cancellable = true)
	private void onepiece$collideWithShips(Vec3 movement, CallbackInfoReturnable<Vec3> cir) {
		Vec3 result = cir.getReturnValue();
		Vec3 withShips = ShipDecks.collide((Entity) (Object) this, result);
		if (withShips != result) {
			cir.setReturnValue(withShips);
		}
	}
}
