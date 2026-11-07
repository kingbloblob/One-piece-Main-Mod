package com.onepiecemod.deco;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.tags.TagKey;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.FlowerBlock;
import net.minecraft.world.level.block.state.BlockState;

import com.onepiecemod.OnePieceMod;

/**
 * A flower that also grows on sand, snow, stone and Island Cloud, so every island can have its own
 * flowers (Fire Lilies on Punk Hazard rock, Cloud Puffs on Skypiea). The list of ground is the block tag
 * data/onepiece/tags/block/deco_plant_soil.json.
 */
public class DecoFlowerBlock extends FlowerBlock {
	public static final TagKey<Block> SOIL = TagKey.create(Registries.BLOCK, OnePieceMod.id("deco_plant_soil"));

	public DecoFlowerBlock(Holder<MobEffect> stewEffect, float seconds, Properties properties) {
		super(stewEffect, seconds, properties);
	}

	@Override
	protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
		return state.is(SOIL) || super.mayPlaceOn(state, level, pos);
	}
}
