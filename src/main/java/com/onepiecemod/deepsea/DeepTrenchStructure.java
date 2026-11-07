package com.onepiecemod.deepsea;

import java.util.List;
import java.util.Optional;

import com.mojang.serialization.MapCodec;

import net.minecraft.core.BlockPos;
import net.minecraft.util.Mth;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.WorldgenRandom;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureType;

import com.onepiecemod.world.StructureSpacing;

/**
 * A deep sea trench: a long, winding canyon cut down from the ocean floor almost to the bottom of the world, dark,
 * cold and full of glowing things, downward currents, Sea Pearl oysters, Krakens and sunken treasure.
 * Too deep to swim (see DeepPressure): you come down here in a submarine or a coated ship.
 *
 * Placed by data/onepiece/worldgen/structure_set/deep_trench_locations.json on deep open sea from Paradise outwards,
 * and kept clear of our other builds (StructureSpacing). The carving is DeepTrenchPiece.
 */
public class DeepTrenchStructure extends Structure {
	public static final MapCodec<DeepTrenchStructure> CODEC = simpleCodec(DeepTrenchStructure::new);

	/** The sea must be at least this deep all along the trench, so it never cuts through an island. */
	private static final int MIN_SEA_DEPTH = 10;

	public DeepTrenchStructure(StructureSettings settings) {
		super(settings);
	}

	@Override
	protected Optional<GenerationStub> findGenerationPoint(GenerationContext context) {
		ChunkPos chunk = context.chunkPos();
		int x = chunk.getMinBlockX() + 8;
		int z = chunk.getMinBlockZ() + 8;
		int sea = context.chunkGenerator().getSeaLevel();
		WorldgenRandom random = context.random();
		float angle = random.nextFloat() * Mth.TWO_PI;
		int halfLength = 70 + random.nextInt(45);
		int halfWidth = 13 + random.nextInt(8);
		int bottom = context.heightAccessor().getMinY() + 8 + random.nextInt(5);
		long seed = random.nextLong();

		// Open sea all along: sample the centre line.
		float cos = Mth.cos(angle), sin = Mth.sin(angle);
		int centreFloor = 0;
		for (int i = -3; i <= 3; i++) {
			int sx = x + Mth.floor(cos * halfLength * i / 3.0f);
			int sz = z + Mth.floor(sin * halfLength * i / 3.0f);
			int floor = context.chunkGenerator().getFirstOccupiedHeight(sx, sz, Heightmap.Types.OCEAN_FLOOR_WG,
					context.heightAccessor(), context.randomState());
			if (sea - floor < MIN_SEA_DEPTH) {
				return Optional.empty();
			}
			if (i == 0) {
				centreFloor = floor;
			}
		}
		if (centreFloor - bottom < 20) {
			return Optional.empty();
		}

		DeepTrenchPiece piece = new DeepTrenchPiece(x, z, angle, halfLength, halfWidth, bottom, sea, seed);
		BoundingBox box = piece.getBoundingBox();
		List<BoundingBox> blockers = StructureSpacing.blockers(this, context, box, false, 0);
		if (blockers == null || !StructureSpacing.clear(box, blockers)) {
			return Optional.empty();
		}
		return Optional.of(new GenerationStub(new BlockPos(x, centreFloor, z), builder -> builder.addPiece(piece)));
	}

	@Override
	public StructureType<?> type() {
		return DeepSeaFeature.TRENCH;
	}
}
