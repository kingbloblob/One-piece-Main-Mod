package com.onepiecemod.anim.client.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;

import net.fabricmc.fabric.api.client.rendering.v1.FabricRenderState;

import com.onepiecemod.anim.client.AnimClient;
import com.onepiecemod.anim.client.Poses;

/**
 * After Minecraft poses a player-shaped model for this frame (walking, looking, swinging), bend it into
 * the custom animation, if one is playing. Runs for players, characters, NPCs, giants and their armor.
 */
@Mixin(HumanoidModel.class)
public abstract class HumanoidModelAnimMixin {
	@Inject(method = "setupAnim(Lnet/minecraft/client/renderer/entity/state/HumanoidRenderState;)V", at = @At("TAIL"))
	private void onepiece$applyAnim(HumanoidRenderState state, CallbackInfo ci) {
		AnimClient.Frame frame = ((FabricRenderState) state).getData(AnimClient.KEY);
		if (frame != null) {
			Poses.apply((HumanoidModel<?>) (Object) this, state, frame);
		}
	}
}
