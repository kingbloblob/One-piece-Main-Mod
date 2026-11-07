package com.onepiecemod.world.mixin;

import com.onepiecemod.world.StructureSiteRules;
import com.onepiecemod.world.StructureSpacing;
import java.util.Optional;
import net.minecraft.world.level.levelgen.structure.Structure;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Adds our terrain check (see StructureSiteRules) after vanilla's biome check. */
@Mixin(Structure.class)
public abstract class StructureSiteMixin {
	/** Our structures: skip the costly jigsaw layout when the biome check that follows it is bound to fail. */
	@Inject(method = "findValidGenerationPoint", at = @At("HEAD"), cancellable = true)
	private void onepiece$quickBiome(Structure.GenerationContext ctx,
			CallbackInfoReturnable<Optional<Structure.GenerationStub>> cir) {
		Structure self = (Structure) (Object) this;
		if (StructureSiteRules.ours(self, ctx) && !StructureSpacing.startBiomeFits(self, ctx.chunkPos(), ctx)) cir.setReturnValue(Optional.empty());
	}

	@Inject(method = "findValidGenerationPoint", at = @At("RETURN"), cancellable = true)
	private void onepiece$checkSite(Structure.GenerationContext ctx,
			CallbackInfoReturnable<Optional<Structure.GenerationStub>> cir) {
		cir.setReturnValue(StructureSiteRules.filter((Structure) (Object) this, ctx, cir.getReturnValue()));
	}
}
