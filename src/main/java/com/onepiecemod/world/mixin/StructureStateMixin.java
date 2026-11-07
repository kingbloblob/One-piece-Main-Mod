package com.onepiecemod.world.mixin;

import com.onepiecemod.world.StructureSpacing;
import net.minecraft.world.level.biome.BiomeSource;
import net.minecraft.world.level.chunk.ChunkGeneratorStructureState;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Hands each dimension's structure state to StructureSpacing, which needs it to find neighbouring structure starts. */
@Mixin(ChunkGeneratorStructureState.class)
public abstract class StructureStateMixin {
	@Shadow @Final private BiomeSource biomeSource;

	@Inject(method = "<init>", at = @At("TAIL"))
	private void onepiece$register(CallbackInfo ci) {
		StructureSpacing.register((ChunkGeneratorStructureState) (Object) this, biomeSource);
	}
}
