package com.onepiecemod.lifeskill.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.world.inventory.FurnaceResultSlot;
import net.minecraft.world.item.ItemStack;

import com.onepiecemod.lifeskill.LifeSkillAccess;

/** Marks items taken from a furnace, smoker or blast furnace, so smelted ingots train Smithing (crafted ones don't). */
@Mixin(FurnaceResultSlot.class)
public class FurnaceResultSlotLifeSkillMixin {
	@Inject(method = "checkTakeAchievements", at = @At("HEAD"))
	private void onepiece$furnaceStart(ItemStack stack, CallbackInfo ci) {
		LifeSkillAccess.setTakingFromFurnace(true);
	}

	@Inject(method = "checkTakeAchievements", at = @At("RETURN"))
	private void onepiece$furnaceEnd(ItemStack stack, CallbackInfo ci) {
		LifeSkillAccess.setTakingFromFurnace(false);
	}
}
