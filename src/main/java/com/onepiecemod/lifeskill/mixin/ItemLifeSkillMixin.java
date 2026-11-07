package com.onepiecemod.lifeskill.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import com.onepiecemod.lifeskill.LifeSkillHooks;

/**
 * Smithing's durability bonus on crafted gear. Item.onCraftedBy runs before shift-click crafting moves
 * the stack into the inventory (ItemStack.onCraftedBy runs after), so the change sticks either way.
 */
@Mixin(Item.class)
public class ItemLifeSkillMixin {
	@Inject(method = "onCraftedBy(Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/entity/player/Player;)V", at = @At("HEAD"))
	private void onepiece$lifeSkillForge(ItemStack stack, Player player, CallbackInfo ci) {
		LifeSkillHooks.forge(player, stack);
	}
}
