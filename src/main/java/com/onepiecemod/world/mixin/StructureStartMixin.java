package com.onepiecemod.world.mixin;

import com.onepiecemod.world.TerrainCut;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Clears and slopes the hill above our land and coast builds before their pieces go down (see TerrainCut). */
@Mixin(StructureStart.class)
public abstract class StructureStartMixin {
	@Inject(method = "placeInChunk", at = @At("HEAD"))
	private void onepiece$cutTerrain(WorldGenLevel level, StructureManager structures, ChunkGenerator generator,
			RandomSource random, BoundingBox chunkBox, ChunkPos chunkPos, CallbackInfo ci) {
		StructureStart self = (StructureStart) (Object) this;
		if (!self.isValid()) return;
		try {
			TerrainCut.before(self, level, chunkBox);
		} catch (RuntimeException e) {
			// never lose a chunk over the clean-up
		}
	}
}
