package com.onepiecemod.flora;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.tags.TagKey;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.BonemealSource;
import net.minecraft.world.level.block.BushBlock;
import net.minecraft.world.level.block.FlowerBedBlock;
import net.minecraft.world.level.block.FlowerBlock;
import net.minecraft.world.level.block.TallFlowerBlock;
import net.minecraft.world.level.block.TallGrassBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;

import com.onepiecemod.OnePieceMod;

/**
 * The plant block types of the islands. Each one is a vanilla plant that also grows on the island grounds of
 * One Piece (sand, snow, rock, ash, Island Cloud, Sugar Sand...): the block tag
 * data/onepiece/tags/block/flora_plant_soil.json lists what they may stand on.
 */
public final class FloraPlants {
	public static final TagKey<Block> SOIL = TagKey.create(Registries.BLOCK, OnePieceMod.id("flora_plant_soil"));

	private FloraPlants() {
	}

	/** A small flower (one block) with a suspicious-stew effect, like a poppy. */
	public static class Flower extends FlowerBlock {
		public Flower(Holder<MobEffect> stewEffect, float seconds, BlockBehaviour.Properties properties) {
			super(stewEffect, seconds, properties);
		}

		@Override
		protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
			return state.is(SOIL) || super.mayPlaceOn(state, level, pos);
		}
	}

	/** A two-block-tall plant, like a rose bush or large fern. */
	public static class Tall extends TallFlowerBlock {
		public Tall(BlockBehaviour.Properties properties) {
			super(properties);
		}

		@Override
		protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
			return state.is(SOIL) || super.mayPlaceOn(state, level, pos);
		}
	}

	/** A tuft of grass with its own fixed colour (not tinted by the biome). Bone meal does nothing to it. */
	public static class Grass extends TallGrassBlock {
		public Grass(BlockBehaviour.Properties properties) {
			super(properties);
		}

		@Override
		protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
			return state.is(SOIL) || super.mayPlaceOn(state, level, pos);
		}

		@Override
		public boolean isValidBonemealTarget(LevelReader level, BlockPos pos, BlockState state, BonemealSource source) {
			return false;
		}
	}

	/** A round shrub, like the vanilla bush. */
	public static class Shrub extends BushBlock {
		public Shrub(BlockBehaviour.Properties properties) {
			super(properties);
		}

		@Override
		protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
			return state.is(SOIL) || super.mayPlaceOn(state, level, pos);
		}
	}

	/** Ground cover placed in up to four segments per block, like pink petals or leaf litter. */
	public static class Cover extends FlowerBedBlock {
		public Cover(BlockBehaviour.Properties properties) {
			super(properties, 3);
		}

		@Override
		protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
			return state.is(SOIL) || super.mayPlaceOn(state, level, pos);
		}
	}
}
