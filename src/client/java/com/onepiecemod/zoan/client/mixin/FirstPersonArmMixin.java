package com.onepiecemod.zoan.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.ModifyArg;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import com.mojang.blaze3d.vertex.PoseStack;

import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.player.AvatarRenderer;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.client.RenderGuard;
import com.onepiecemod.fx.FxFeature;
import com.onepiecemod.power.ZoanForms;

/**
 * Your own arm in first person: furry, feathered or scaly while you're in a Zoan form, and coated
 * in black while your Armament Haki is on (the same look other players already see).
 */
@Mixin(AvatarRenderer.class)
public abstract class FirstPersonArmMixin {
	private static final Identifier ONEPIECE$ARMAMENT = OnePieceMod.id("textures/entity/fx/armament.png");

	@ModifyArg(method = "renderHand", at = @At(value = "INVOKE",
			target = "Lnet/minecraft/client/renderer/rendertype/RenderTypes;entityTranslucent(Lnet/minecraft/resources/Identifier;)Lnet/minecraft/client/renderer/rendertype/RenderType;"))
	private Identifier onepiece$zoanArmTexture(Identifier skin) {
		ZoanForms.Active form = Minecraft.getInstance().player != null ? ZoanForms.get(Minecraft.getInstance().player) : null;
		return form != null ? OnePieceMod.id("textures/entity/zoan/arm_" + form.form() + ".png") : skin;
	}

	@Inject(method = "renderHand", at = @At("TAIL"))
	private void onepiece$armamentHand(PoseStack poseStack, SubmitNodeCollector collector, int light, Identifier skin, ModelPart arm,
			boolean sleeve, CallbackInfo ci) {
		if (Minecraft.getInstance().player == null || !FxFeature.armamentVisible(Minecraft.getInstance().player)) {
			return;
		}
		RenderGuard.run("first-person armament", poseStack, () -> {
			// A slightly bigger copy of the arm in the black Armament texture, over the normal one.
			poseStack.pushPose();
			poseStack.scale(1.08f, 1.02f, 1.08f);
			collector.submitModelPart(arm, poseStack, RenderTypes.entityCutout(ONEPIECE$ARMAMENT), light, OverlayTexture.NO_OVERLAY, null);
			poseStack.popPose();
		});
	}
}
