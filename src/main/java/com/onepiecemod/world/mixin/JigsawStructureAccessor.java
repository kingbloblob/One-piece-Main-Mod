package com.onepiecemod.world.mixin;

import java.util.Optional;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.heightproviders.HeightProvider;
import net.minecraft.world.level.levelgen.structure.structures.JigsawStructure;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

@Mixin(JigsawStructure.class)
public interface JigsawStructureAccessor {
	@Accessor("projectStartToHeightmap")
	Optional<Heightmap.Types> onepiece$projectStartToHeightmap();

	@Accessor("startHeight")
	HeightProvider onepiece$startHeight();

	@Accessor("startJigsawName")
	Optional<Identifier> onepiece$startJigsawName();
}
