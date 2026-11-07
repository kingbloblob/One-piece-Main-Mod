package com.onepiecemod.ship.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityFluidInteraction;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.Fluids;

import com.onepiecemod.ship.ShipHold;

/**
 * Someone standing in a ship's dry hold doesn't feel the sea around the ship: no swimming, drowning or being
 * pushed by water while below the waterline inside the hull (see ShipHold).
 */
@Mixin(EntityFluidInteraction.class)
public abstract class EntityFluidMixin {
	@Unique
	private boolean onepiece$inDryHold;

	@Inject(method = "update", at = @At("HEAD"))
	private void onepiece$checkHold(Entity entity, boolean ignoreCurrent, CallbackInfoReturnable<Boolean> cir) {
		onepiece$inDryHold = ShipHold.isDry(entity);
	}

	@Redirect(method = "update", at = @At(value = "INVOKE",
			target = "Lnet/minecraft/world/level/BlockGetter;getFluidState(Lnet/minecraft/core/BlockPos;)Lnet/minecraft/world/level/material/FluidState;"))
	private FluidState onepiece$dryHold(BlockGetter level, BlockPos pos) {
		return onepiece$inDryHold ? Fluids.EMPTY.defaultFluidState() : level.getFluidState(pos);
	}
}
