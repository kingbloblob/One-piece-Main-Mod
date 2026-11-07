package com.onepiecemod.deepsea;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceKey;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.BubbleColumnBlock;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.KelpBlock;
import net.minecraft.world.level.block.SeaPickleBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceSerializationContext;
import net.minecraft.world.level.storage.loot.LootTable;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.resource.Resources;

/**
 * Carves one deep trench (see DeepTrenchStructure), one chunk at a time, straight from its numbers: every column
 * works out on its own whether it's in the trench and how deep, so chunks can generate in any order.
 *
 * Seen from above it's a long, winding canyon, rounded at both ends. In cross-section it has steep walls and a
 * rounded floor near the bottom of the world: dark gravel, sand and deepslate with Sea Pearl oysters, glowing sea
 * pickles and kelp, the odd sea lantern glinting in the walls, magma vents pulling swimmers down (the show's
 * downward currents), and a few sunken treasure chests along the bottom.
 */
public class DeepTrenchPiece extends StructurePiece {
	private static final ResourceKey<LootTable> TREASURE = ResourceKey.create(Registries.LOOT_TABLE, OnePieceMod.id("chests/treasure"));
	private static final float[] CHESTS = { -0.45f, 0.05f, 0.55f };

	private final int cx, cz, halfLength, halfWidth, bottom, sea;
	private final float angle;
	private final long seed;

	public DeepTrenchPiece(int cx, int cz, float angle, int halfLength, int halfWidth, int bottom, int sea, long seed) {
		super(DeepSeaFeature.TRENCH_PIECE, 0, box(cx, cz, halfLength, halfWidth, bottom, sea));
		this.cx = cx;
		this.cz = cz;
		this.angle = angle;
		this.halfLength = halfLength;
		this.halfWidth = halfWidth;
		this.bottom = bottom;
		this.sea = sea;
		this.seed = seed;
	}

	public DeepTrenchPiece(CompoundTag tag) {
		super(DeepSeaFeature.TRENCH_PIECE, tag);
		cx = tag.getIntOr("CX", 0);
		cz = tag.getIntOr("CZ", 0);
		angle = tag.getFloatOr("Angle", 0);
		halfLength = tag.getIntOr("HalfLength", 80);
		halfWidth = tag.getIntOr("HalfWidth", 16);
		bottom = tag.getIntOr("Bottom", -56);
		sea = tag.getIntOr("Sea", 63);
		seed = tag.getLongOr("Seed", 0);
	}

	@Override
	protected void addAdditionalSaveData(StructurePieceSerializationContext context, CompoundTag tag) {
		tag.putInt("CX", cx);
		tag.putInt("CZ", cz);
		tag.putFloat("Angle", angle);
		tag.putInt("HalfLength", halfLength);
		tag.putInt("HalfWidth", halfWidth);
		tag.putInt("Bottom", bottom);
		tag.putInt("Sea", sea);
		tag.putLong("Seed", seed);
	}

	/** The meander swings the centre line up to this far to the side. */
	private static final int MEANDER = 9;

	private static BoundingBox box(int cx, int cz, int halfLength, int halfWidth, int bottom, int sea) {
		int reach = halfLength + Mth.ceil(halfWidth * 1.3f) + MEANDER + 2;
		return new BoundingBox(cx - reach, bottom - 2, cz - reach, cx + reach, sea, cz + reach);
	}

	private double wave(double u, int salt, double frequency) {
		return Math.sin(u * frequency + ((seed >>> (salt * 7)) & 1023) / 163.0);
	}

	/** The centre line's sideways swing at this point along the trench. */
	private double meander(double u) {
		return MEANDER * wave(u, 1, 0.022);
	}

	@Override
	public void postProcess(WorldGenLevel level, StructureManager structures, ChunkGenerator generator, RandomSource random,
			BoundingBox chunkBox, ChunkPos chunkPos, BlockPos pivot) {
		float cos = Mth.cos(angle), sin = Mth.sin(angle);
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		BlockState water = Blocks.WATER.defaultBlockState();
		int x0 = Math.max(chunkBox.minX(), boundingBox.minX()), x1 = Math.min(chunkBox.maxX(), boundingBox.maxX());
		int z0 = Math.max(chunkBox.minZ(), boundingBox.minZ()), z1 = Math.min(chunkBox.maxZ(), boundingBox.maxZ());
		for (int x = x0; x <= x1; x++) {
			for (int z = z0; z <= z1; z++) {
				double dx = x - cx, dz = z - cz;
				double u = dx * cos + dz * sin;
				if (Math.abs(u) > halfLength) {
					continue;
				}
				double v = -dx * sin + dz * cos - meander(u);
				double t = u / halfLength;
				double width = halfWidth * Math.sqrt(1 - t * t * t * t) * (1 + 0.2 * wave(u, 2, 0.045) + 0.08 * wave(u, 3, 0.13));
				double side = Math.abs(v) / width;
				if (side >= 1) {
					continue;
				}
				// The sea floor here: the top solid block under the water.
				int floor = sea - 1;
				while (floor > bottom && level.getFluidState(pos.set(x, floor, z)).is(FluidTags.WATER)) {
					floor--;
				}
				if (floor >= sea - 4) {
					continue; // A shoal or an island: leave it.
				}
				int deepest = bottom + (int) Math.round(2.5 * wave(u, 4, 0.09) + 1.5 * wave(u, 5, 0.31));
				int base = deepest + (int) Math.floor((floor - deepest) * Math.pow(side, 2.4));
				if (base >= floor) {
					continue;
				}
				for (int y = base + 1; y <= floor; y++) {
					level.setBlock(pos.set(x, y, z), water, 2);
				}
				dress(level, random, pos, x, base, z, floor, side, u, chunkBox);
			}
		}
		// Sunken treasure along the bottom.
		for (int i = 0; i < CHESTS.length; i++) {
			double u = CHESTS[i] * halfLength;
			double v = meander(u) + ((seed >>> (i * 5)) & 7) - 3;
			int x = Mth.floor(cx + u * cos - v * sin), z = Mth.floor(cz + u * sin + v * cos);
			if (!chunkBox.isInside(x, bottom, z)) {
				continue;
			}
			int y = bottom + 12;
			while (y > bottom - 2 && level.getFluidState(pos.set(x, y - 1, z)).is(FluidTags.WATER)) {
				y--;
			}
			BlockState chest = Blocks.CHEST.defaultBlockState().setValue(ChestBlock.WATERLOGGED, true)
					.setValue(ChestBlock.FACING, net.minecraft.core.Direction.Plane.HORIZONTAL.getRandomDirection(random));
			createChest(level, chunkBox, random, new BlockPos(x, y, z), TREASURE, chest);
		}
	}

	/** The floor and walls of one carved column: what it's made of and what grows on it. */
	private void dress(WorldGenLevel level, RandomSource random, BlockPos.MutableBlockPos pos, int x, int base, int z, int floor,
			double side, double u, BoundingBox chunkBox) {
		pos.set(x, base, z);
		float roll = random.nextFloat();
		boolean bottomZone = side < 0.45;
		if (bottomZone) {
			BlockState ground;
			if (side < 0.2 && roll < 0.004) {
				// A magma vent: the downward current. A column of sinking bubbles all the way up to the rim.
				level.setBlock(pos, Blocks.MAGMA_BLOCK.defaultBlockState(), 2);
				BlockState column = Blocks.BUBBLE_COLUMN.defaultBlockState().setValue(BubbleColumnBlock.DRAG_DOWN, true);
				for (int y = base + 1; y <= floor; y++) {
					level.setBlock(pos.set(x, y, z), column, 2);
				}
				return;
			}
			if (roll < 0.10) {
				ground = Resources.OYSTER_GRAVEL.defaultBlockState();
			} else if (roll < 0.40) {
				ground = Blocks.GRAVEL.defaultBlockState();
			} else if (roll < 0.55) {
				ground = Blocks.SAND.defaultBlockState();
			} else if (roll < 0.62) {
				ground = Blocks.DEAD_BRAIN_CORAL_BLOCK.defaultBlockState();
			} else {
				ground = Blocks.DEEPSLATE.defaultBlockState();
			}
			level.setBlock(pos, ground, 2);
			pos.set(x, base + 1, z);
			float grow = random.nextFloat();
			if (grow < 0.035) {
				level.setBlock(pos, Blocks.SEA_PICKLE.defaultBlockState().setValue(SeaPickleBlock.PICKLES, 1 + random.nextInt(4))
						.setValue(BlockStateProperties.WATERLOGGED, true), 2);
			} else if (grow < 0.055) {
				int height = 2 + random.nextInt(9);
				for (int i = 0; i < height && base + 1 + i < floor; i++) {
					boolean top = i == height - 1 || base + 2 + i >= floor;
					level.setBlock(pos.set(x, base + 1 + i, z), top
							? Blocks.KELP.defaultBlockState().setValue(KelpBlock.AGE, 25) : Blocks.KELP_PLANT.defaultBlockState(), 2);
					if (top) {
						break;
					}
				}
			}
		} else if (roll < 0.006) {
			// A glint in the dark wall.
			level.setBlock(pos, Blocks.SEA_LANTERN.defaultBlockState(), 2);
		} else if (roll < 0.05 && base < 0) {
			level.setBlock(pos, Blocks.TUFF.defaultBlockState(), 2);
		}
	}
}
