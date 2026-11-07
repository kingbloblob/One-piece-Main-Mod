package com.onepiecemod.zoan.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.FirstPersonHandsAndItemsRenderer;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.state.level.FirstPersonHandsAndItemsRenderState;
import net.minecraft.client.renderer.state.level.PlayerRenderState;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;

import com.onepiecemod.anim.client.AnimClient;
import com.onepiecemod.weapon.GunItem;

/** In first person, a gun kicks back and up when you fire it, then settles over a few ticks. */
@Mixin(FirstPersonHandsAndItemsRenderer.class)
public abstract class GunRecoilMixin {
	private static final float ONEPIECE$RECOIL_TICKS = 6.0f;

	@Inject(method = "submitArmWithItem", at = @At(value = "INVOKE", target = "Lcom/mojang/blaze3d/vertex/PoseStack;pushPose()V", ordinal = 0, shift = At.Shift.AFTER))
	private void onepiece$recoil(PlayerRenderState player, FirstPersonHandsAndItemsRenderState hands, float partialTick, float pitch,
			InteractionHand hand, float swing, ItemStack stack, float equip, PoseStack poseStack, SubmitNodeCollector collector, int light,
			CallbackInfo ci) {
		if (!(stack.getItem() instanceof GunItem) || Minecraft.getInstance().player == null) {
			return;
		}
		float since = AnimClient.ticksSinceShot(Minecraft.getInstance().player, partialTick);
		if (since < 0 || since >= ONEPIECE$RECOIL_TICKS) {
			return;
		}
		// Sharp kick at first, easing back to rest.
		float kick = 1.0f - since / ONEPIECE$RECOIL_TICKS;
		kick *= kick;
		poseStack.translate(0.0f, 0.03f * kick, 0.18f * kick);
		poseStack.rotate(Axis.XP.rotationDegrees(22.0f * kick));
	}
}
