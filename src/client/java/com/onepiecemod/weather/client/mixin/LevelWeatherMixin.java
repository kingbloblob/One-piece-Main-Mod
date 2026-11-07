package com.onepiecemod.weather.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.world.level.Level;

import com.onepiecemod.weather.client.LocalStorm;

/** On the player's own game only: a nearby sea storm makes it rain and thunder there (see LocalStorm). */
@Mixin(Level.class)
public abstract class LevelWeatherMixin {
	@Inject(method = "getRainLevel", at = @At("RETURN"), cancellable = true)
	private void onepiece$stormRain(float partialTick, CallbackInfoReturnable<Float> cir) {
		if ((Object) this instanceof ClientLevel) {
			float storm = LocalStorm.strength();
			if (storm > cir.getReturnValueF()) {
				cir.setReturnValue(storm);
			}
		}
	}

	@Inject(method = "getThunderLevel", at = @At("RETURN"), cancellable = true)
	private void onepiece$stormThunder(float partialTick, CallbackInfoReturnable<Float> cir) {
		if ((Object) this instanceof ClientLevel) {
			float storm = LocalStorm.strength();
			if (storm > cir.getReturnValueF()) {
				cir.setReturnValue(storm);
			}
		}
	}
}
