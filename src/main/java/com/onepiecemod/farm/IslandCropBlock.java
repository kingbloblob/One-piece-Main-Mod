package com.onepiecemod.farm;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.ItemLike;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * An island crop on farmland: four stages like beetroot. On its home island it grows about as fast
 * as wheat; anywhere else only a third as fast. Sprinklers and the Watering Can speed it up (they
 * give extra growth ticks), and bone meal works as usual.
 */
public class IslandCropBlock extends CropBlock {
	public static final IntegerProperty AGE = BlockStateProperties.AGE_3;
	private static final VoxelShape[] SHAPES = {
			Block.box(0, 0, 0, 16, 3, 16), Block.box(0, 0, 0, 16, 7, 16),
			Block.box(0, 0, 0, 16, 11, 16), Block.box(0, 0, 0, 16, 14, 16)};

	public final IslandCrop crop;

	public IslandCropBlock(Properties properties, IslandCrop crop) {
		super(properties);
		this.crop = crop;
	}

	@Override
	protected IntegerProperty getAgeProperty() {
		return AGE;
	}

	@Override
	public int getMaxAge() {
		return 3;
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(AGE);
	}

	@Override
	protected ItemLike getBaseSeedId() {
		return FarmItems.seeds(crop);
	}

	@Override
	protected void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		// Four stages instead of wheat's eight, so skip half the ticks at home and five in six abroad.
		int chance = crop.isHome(level, pos) ? 2 : 6;
		if (random.nextInt(chance) == 0) {
			super.randomTick(state, level, pos, random);
		}
	}

	@Override
	protected int getBonemealAgeIncrease(Level level) {
		return 1;
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPES[state.getValue(AGE)];
	}
}
