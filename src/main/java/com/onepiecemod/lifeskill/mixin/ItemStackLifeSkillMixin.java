package com.onepiecemod.lifeskill.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

import com.onepiecemod.lifeskill.LifeSkillHooks;

/** Life skills: XP for taking crafted/smelted items, and Cooking perks when a meal is finished. */
@Mixin(ItemStack.class)
public class ItemStackLifeSkillMixin {
	@Inject(method = "onCraftedBy(Lnet/minecraft/world/entity/player/Player;I)V", at = @At("HEAD"))
	private void onepiece$lifeSkillCrafted(Player player, int amount, CallbackInfo ci) {
		LifeSkillHooks.onCrafted(player, (ItemStack) (Object) this, amount);
	}

	@Inject(method = "finishUsingItem", at = @At("HEAD"))
	private void onepiece$lifeSkillEat(Level level, LivingEntity entity, CallbackInfoReturnable<ItemStack> cir) {
		if (entity instanceof Player player) {
			LifeSkillHooks.onEat(level, player, (ItemStack) (Object) this);
		}
	}
}
