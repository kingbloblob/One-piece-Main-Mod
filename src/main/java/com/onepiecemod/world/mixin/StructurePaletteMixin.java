package com.onepiecemod.world.mixin;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Mutable;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;

/**
 * Template palettes cache their blocks in a plain HashMap. Location searches now run on their own thread
 * (see Locations.findLater) while chunks generate, so the same template can be read by two threads at once.
 */
@Mixin(StructureTemplate.Palette.class)
public abstract class StructurePaletteMixin {
	@Shadow @Final @Mutable private Map<Block, List<StructureTemplate.StructureBlockInfo>> cache;

	@Inject(method = "<init>", at = @At("RETURN"))
	private void onepiece$threadSafe(CallbackInfo ci) {
		cache = new ConcurrentHashMap<>(cache);
	}
}
