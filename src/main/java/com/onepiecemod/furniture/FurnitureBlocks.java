package com.onepiecemod.furniture;

import java.util.List;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

import net.fabricmc.fabric.api.registry.FlammableBlockRegistry;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.furniture.FurnitureBlock.Mount;

/**
 * Every furniture block. Each one lists: the block it copies (hardness and sound), its light, where it
 * mounts, its seat height in pixels (0 = not a seat), whether you bump into it, and the boxes of its
 * shape in pixels, facing north.
 *
 * This file is made by tools/furniture/gen_furniture.py from tools/furniture/props.py (together with
 * the models, recipes and loot tables). To add a block, add it there and run the script again.
 */
public class FurnitureBlocks {
	public static final Block OAK_TABLE = furniture("oak_table", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 13, 0, 16, 16, 16), b(1, 0, 1, 3, 13, 3), b(1, 0, 13, 3, 13, 15), b(13, 0, 1, 15, 13, 3), b(13, 0, 13, 15, 13, 15), b(1, 10, 2, 3, 11, 14), b(13, 10, 2, 15, 11, 14));
	public static final Block OAK_CHAIR = furniture("oak_chair", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 9, true,
			b(2, 7, 2, 14, 9, 14), b(2, 0, 2, 4, 7, 4), b(2, 0, 12, 4, 7, 14), b(12, 0, 2, 14, 7, 4), b(12, 0, 12, 14, 7, 14), b(2, 9, 12, 4, 16, 14), b(12, 9, 12, 14, 16, 14), b(4, 11, 12.5, 12, 15, 13.5));
	public static final Block OAK_STOOL = furniture("oak_stool", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 10, true,
			b(3, 8, 3, 13, 10, 13), b(3.5, 0, 3.5, 5.5, 8, 5.5), b(3.5, 0, 10.5, 5.5, 8, 12.5), b(10.5, 0, 3.5, 12.5, 8, 5.5), b(10.5, 0, 10.5, 12.5, 8, 12.5), b(4, 3, 5.5, 12, 4, 6.5), b(4, 3, 9.5, 12, 4, 10.5));
	public static final Block OAK_NIGHTSTAND = storage("oak_nightstand", 9, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(1, 0, 2, 15, 13, 15), b(0, 13, 1, 16, 15, 16), b(1.5, 0, 1.5, 3, 13, 2), b(13, 0, 1.5, 14.5, 13, 2), b(3, 7, 1, 13, 12, 2), b(3, 1, 1, 13, 6, 2), b(7, 9, 0.5, 9, 10, 1), b(7, 3, 0.5, 9, 4, 1));
	public static final Block OAK_BENCH = furniture("oak_bench", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 9, true,
			b(0, 7, 2, 16, 9, 12), b(1, 0, 3, 3, 7, 11), b(13, 0, 3, 15, 7, 11), b(1, 9, 11, 3, 13, 12), b(13, 9, 11, 15, 13, 12), b(0, 12, 11, 16, 15, 12.5));
	public static final Block OAK_WALL_SHELF = furniture("oak_wall_shelf", Blocks.OAK_PLANKS, 0, Mount.WALL, 0, true,
			b(0, 6, 9, 16, 8, 16), b(1, 3, 14, 3, 6, 16), b(13, 3, 14, 15, 6, 16), b(1.5, 8, 11, 2.5, 13, 15), b(2.5, 8, 11, 3.5, 12, 15), b(3.5, 8, 11, 4.5, 13.5, 15), b(4.5, 8, 11.5, 5.5, 12.5, 15), b(8, 8, 11, 11, 12, 14), b(8.5, 12, 11.5, 10.5, 13, 13.5), b(12, 8, 11.5, 14, 10, 13.5));
	public static final Block OAK_COUNTER = storage("oak_counter", 27, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 1, 16, 14, 16), b(0, 14, 0, 16, 16, 16), b(1.5, 2, 0.5, 7, 12, 1), b(9, 2, 0.5, 14.5, 12, 1), b(6, 6, 0, 7, 8, 0.5), b(9, 6, 0, 10, 8, 0.5));
	public static final Block OAK_CUPBOARD = storage("oak_cupboard", 27, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 1, 16, 16, 16), b(0.5, 1, 0.5, 7.75, 15, 1), b(8.25, 1, 0.5, 15.5, 15, 1), b(1.5, 2, 0.25, 6.75, 14, 0.5), b(9.25, 2, 0.25, 14.5, 14, 0.5), b(6.5, 7, 0, 7.25, 9, 0.25), b(8.75, 7, 0, 9.5, 9, 0.25));
	public static final Block OAK_BEAM = furniture("oak_beam", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(4, 8, 0, 12, 16, 16));
	public static final Block SPRUCE_TABLE = furniture("spruce_table", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 13, 0, 16, 16, 16), b(1, 0, 1, 3, 13, 3), b(1, 0, 13, 3, 13, 15), b(13, 0, 1, 15, 13, 3), b(13, 0, 13, 15, 13, 15), b(1, 10, 2, 3, 11, 14), b(13, 10, 2, 15, 11, 14));
	public static final Block SPRUCE_CHAIR = furniture("spruce_chair", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 9, true,
			b(2, 7, 2, 14, 9, 14), b(2, 0, 2, 4, 7, 4), b(2, 0, 12, 4, 7, 14), b(12, 0, 2, 14, 7, 4), b(12, 0, 12, 14, 7, 14), b(2, 9, 12, 4, 16, 14), b(12, 9, 12, 14, 16, 14), b(4, 11, 12.5, 12, 15, 13.5));
	public static final Block SPRUCE_STOOL = furniture("spruce_stool", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 10, true,
			b(3, 8, 3, 13, 10, 13), b(3.5, 0, 3.5, 5.5, 8, 5.5), b(3.5, 0, 10.5, 5.5, 8, 12.5), b(10.5, 0, 3.5, 12.5, 8, 5.5), b(10.5, 0, 10.5, 12.5, 8, 12.5), b(4, 3, 5.5, 12, 4, 6.5), b(4, 3, 9.5, 12, 4, 10.5));
	public static final Block SPRUCE_NIGHTSTAND = storage("spruce_nightstand", 9, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(1, 0, 2, 15, 13, 15), b(0, 13, 1, 16, 15, 16), b(1.5, 0, 1.5, 3, 13, 2), b(13, 0, 1.5, 14.5, 13, 2), b(3, 7, 1, 13, 12, 2), b(3, 1, 1, 13, 6, 2), b(7, 9, 0.5, 9, 10, 1), b(7, 3, 0.5, 9, 4, 1));
	public static final Block SPRUCE_BENCH = furniture("spruce_bench", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 9, true,
			b(0, 7, 2, 16, 9, 12), b(1, 0, 3, 3, 7, 11), b(13, 0, 3, 15, 7, 11), b(1, 9, 11, 3, 13, 12), b(13, 9, 11, 15, 13, 12), b(0, 12, 11, 16, 15, 12.5));
	public static final Block SPRUCE_WALL_SHELF = furniture("spruce_wall_shelf", Blocks.OAK_PLANKS, 0, Mount.WALL, 0, true,
			b(0, 6, 9, 16, 8, 16), b(1, 3, 14, 3, 6, 16), b(13, 3, 14, 15, 6, 16), b(1.5, 8, 11, 2.5, 13, 15), b(2.5, 8, 11, 3.5, 12, 15), b(3.5, 8, 11, 4.5, 13.5, 15), b(4.5, 8, 11.5, 5.5, 12.5, 15), b(8, 8, 11, 11, 12, 14), b(8.5, 12, 11.5, 10.5, 13, 13.5), b(12, 8, 11.5, 14, 10, 13.5));
	public static final Block SPRUCE_COUNTER = storage("spruce_counter", 27, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 1, 16, 14, 16), b(0, 14, 0, 16, 16, 16), b(1.5, 2, 0.5, 7, 12, 1), b(9, 2, 0.5, 14.5, 12, 1), b(6, 6, 0, 7, 8, 0.5), b(9, 6, 0, 10, 8, 0.5));
	public static final Block SPRUCE_CUPBOARD = storage("spruce_cupboard", 27, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 1, 16, 16, 16), b(0.5, 1, 0.5, 7.75, 15, 1), b(8.25, 1, 0.5, 15.5, 15, 1), b(1.5, 2, 0.25, 6.75, 14, 0.5), b(9.25, 2, 0.25, 14.5, 14, 0.5), b(6.5, 7, 0, 7.25, 9, 0.25), b(8.75, 7, 0, 9.5, 9, 0.25));
	public static final Block SPRUCE_BEAM = furniture("spruce_beam", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(4, 8, 0, 12, 16, 16));
	public static final Block BIRCH_TABLE = furniture("birch_table", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 13, 0, 16, 16, 16), b(1, 0, 1, 3, 13, 3), b(1, 0, 13, 3, 13, 15), b(13, 0, 1, 15, 13, 3), b(13, 0, 13, 15, 13, 15), b(1, 10, 2, 3, 11, 14), b(13, 10, 2, 15, 11, 14));
	public static final Block BIRCH_CHAIR = furniture("birch_chair", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 9, true,
			b(2, 7, 2, 14, 9, 14), b(2, 0, 2, 4, 7, 4), b(2, 0, 12, 4, 7, 14), b(12, 0, 2, 14, 7, 4), b(12, 0, 12, 14, 7, 14), b(2, 9, 12, 4, 16, 14), b(12, 9, 12, 14, 16, 14), b(4, 11, 12.5, 12, 15, 13.5));
	public static final Block BIRCH_STOOL = furniture("birch_stool", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 10, true,
			b(3, 8, 3, 13, 10, 13), b(3.5, 0, 3.5, 5.5, 8, 5.5), b(3.5, 0, 10.5, 5.5, 8, 12.5), b(10.5, 0, 3.5, 12.5, 8, 5.5), b(10.5, 0, 10.5, 12.5, 8, 12.5), b(4, 3, 5.5, 12, 4, 6.5), b(4, 3, 9.5, 12, 4, 10.5));
	public static final Block BIRCH_NIGHTSTAND = storage("birch_nightstand", 9, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(1, 0, 2, 15, 13, 15), b(0, 13, 1, 16, 15, 16), b(1.5, 0, 1.5, 3, 13, 2), b(13, 0, 1.5, 14.5, 13, 2), b(3, 7, 1, 13, 12, 2), b(3, 1, 1, 13, 6, 2), b(7, 9, 0.5, 9, 10, 1), b(7, 3, 0.5, 9, 4, 1));
	public static final Block BIRCH_BENCH = furniture("birch_bench", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 9, true,
			b(0, 7, 2, 16, 9, 12), b(1, 0, 3, 3, 7, 11), b(13, 0, 3, 15, 7, 11), b(1, 9, 11, 3, 13, 12), b(13, 9, 11, 15, 13, 12), b(0, 12, 11, 16, 15, 12.5));
	public static final Block BIRCH_WALL_SHELF = furniture("birch_wall_shelf", Blocks.OAK_PLANKS, 0, Mount.WALL, 0, true,
			b(0, 6, 9, 16, 8, 16), b(1, 3, 14, 3, 6, 16), b(13, 3, 14, 15, 6, 16), b(1.5, 8, 11, 2.5, 13, 15), b(2.5, 8, 11, 3.5, 12, 15), b(3.5, 8, 11, 4.5, 13.5, 15), b(4.5, 8, 11.5, 5.5, 12.5, 15), b(8, 8, 11, 11, 12, 14), b(8.5, 12, 11.5, 10.5, 13, 13.5), b(12, 8, 11.5, 14, 10, 13.5));
	public static final Block BIRCH_COUNTER = storage("birch_counter", 27, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 1, 16, 14, 16), b(0, 14, 0, 16, 16, 16), b(1.5, 2, 0.5, 7, 12, 1), b(9, 2, 0.5, 14.5, 12, 1), b(6, 6, 0, 7, 8, 0.5), b(9, 6, 0, 10, 8, 0.5));
	public static final Block BIRCH_CUPBOARD = storage("birch_cupboard", 27, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 1, 16, 16, 16), b(0.5, 1, 0.5, 7.75, 15, 1), b(8.25, 1, 0.5, 15.5, 15, 1), b(1.5, 2, 0.25, 6.75, 14, 0.5), b(9.25, 2, 0.25, 14.5, 14, 0.5), b(6.5, 7, 0, 7.25, 9, 0.25), b(8.75, 7, 0, 9.5, 9, 0.25));
	public static final Block BIRCH_BEAM = furniture("birch_beam", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(4, 8, 0, 12, 16, 16));
	public static final Block DARK_OAK_TABLE = furniture("dark_oak_table", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 13, 0, 16, 16, 16), b(1, 0, 1, 3, 13, 3), b(1, 0, 13, 3, 13, 15), b(13, 0, 1, 15, 13, 3), b(13, 0, 13, 15, 13, 15), b(1, 10, 2, 3, 11, 14), b(13, 10, 2, 15, 11, 14));
	public static final Block DARK_OAK_CHAIR = furniture("dark_oak_chair", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 9, true,
			b(2, 7, 2, 14, 9, 14), b(2, 0, 2, 4, 7, 4), b(2, 0, 12, 4, 7, 14), b(12, 0, 2, 14, 7, 4), b(12, 0, 12, 14, 7, 14), b(2, 9, 12, 4, 16, 14), b(12, 9, 12, 14, 16, 14), b(4, 11, 12.5, 12, 15, 13.5));
	public static final Block DARK_OAK_STOOL = furniture("dark_oak_stool", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 10, true,
			b(3, 8, 3, 13, 10, 13), b(3.5, 0, 3.5, 5.5, 8, 5.5), b(3.5, 0, 10.5, 5.5, 8, 12.5), b(10.5, 0, 3.5, 12.5, 8, 5.5), b(10.5, 0, 10.5, 12.5, 8, 12.5), b(4, 3, 5.5, 12, 4, 6.5), b(4, 3, 9.5, 12, 4, 10.5));
	public static final Block DARK_OAK_NIGHTSTAND = storage("dark_oak_nightstand", 9, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(1, 0, 2, 15, 13, 15), b(0, 13, 1, 16, 15, 16), b(1.5, 0, 1.5, 3, 13, 2), b(13, 0, 1.5, 14.5, 13, 2), b(3, 7, 1, 13, 12, 2), b(3, 1, 1, 13, 6, 2), b(7, 9, 0.5, 9, 10, 1), b(7, 3, 0.5, 9, 4, 1));
	public static final Block DARK_OAK_BENCH = furniture("dark_oak_bench", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 9, true,
			b(0, 7, 2, 16, 9, 12), b(1, 0, 3, 3, 7, 11), b(13, 0, 3, 15, 7, 11), b(1, 9, 11, 3, 13, 12), b(13, 9, 11, 15, 13, 12), b(0, 12, 11, 16, 15, 12.5));
	public static final Block DARK_OAK_WALL_SHELF = furniture("dark_oak_wall_shelf", Blocks.OAK_PLANKS, 0, Mount.WALL, 0, true,
			b(0, 6, 9, 16, 8, 16), b(1, 3, 14, 3, 6, 16), b(13, 3, 14, 15, 6, 16), b(1.5, 8, 11, 2.5, 13, 15), b(2.5, 8, 11, 3.5, 12, 15), b(3.5, 8, 11, 4.5, 13.5, 15), b(4.5, 8, 11.5, 5.5, 12.5, 15), b(8, 8, 11, 11, 12, 14), b(8.5, 12, 11.5, 10.5, 13, 13.5), b(12, 8, 11.5, 14, 10, 13.5));
	public static final Block DARK_OAK_COUNTER = storage("dark_oak_counter", 27, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 1, 16, 14, 16), b(0, 14, 0, 16, 16, 16), b(1.5, 2, 0.5, 7, 12, 1), b(9, 2, 0.5, 14.5, 12, 1), b(6, 6, 0, 7, 8, 0.5), b(9, 6, 0, 10, 8, 0.5));
	public static final Block DARK_OAK_CUPBOARD = storage("dark_oak_cupboard", 27, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 1, 16, 16, 16), b(0.5, 1, 0.5, 7.75, 15, 1), b(8.25, 1, 0.5, 15.5, 15, 1), b(1.5, 2, 0.25, 6.75, 14, 0.5), b(9.25, 2, 0.25, 14.5, 14, 0.5), b(6.5, 7, 0, 7.25, 9, 0.25), b(8.75, 7, 0, 9.5, 9, 0.25));
	public static final Block DARK_OAK_BEAM = furniture("dark_oak_beam", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(4, 8, 0, 12, 16, 16));
	public static final Block SAKURA_TABLE = furniture("sakura_table", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 13, 0, 16, 16, 16), b(1, 0, 1, 3, 13, 3), b(1, 0, 13, 3, 13, 15), b(13, 0, 1, 15, 13, 3), b(13, 0, 13, 15, 13, 15), b(1, 10, 2, 3, 11, 14), b(13, 10, 2, 15, 11, 14));
	public static final Block SAKURA_CHAIR = furniture("sakura_chair", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 9, true,
			b(2, 7, 2, 14, 9, 14), b(2, 0, 2, 4, 7, 4), b(2, 0, 12, 4, 7, 14), b(12, 0, 2, 14, 7, 4), b(12, 0, 12, 14, 7, 14), b(2, 9, 12, 4, 16, 14), b(12, 9, 12, 14, 16, 14), b(4, 11, 12.5, 12, 15, 13.5));
	public static final Block SAKURA_STOOL = furniture("sakura_stool", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 10, true,
			b(3, 8, 3, 13, 10, 13), b(3.5, 0, 3.5, 5.5, 8, 5.5), b(3.5, 0, 10.5, 5.5, 8, 12.5), b(10.5, 0, 3.5, 12.5, 8, 5.5), b(10.5, 0, 10.5, 12.5, 8, 12.5), b(4, 3, 5.5, 12, 4, 6.5), b(4, 3, 9.5, 12, 4, 10.5));
	public static final Block SAKURA_NIGHTSTAND = storage("sakura_nightstand", 9, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(1, 0, 2, 15, 13, 15), b(0, 13, 1, 16, 15, 16), b(1.5, 0, 1.5, 3, 13, 2), b(13, 0, 1.5, 14.5, 13, 2), b(3, 7, 1, 13, 12, 2), b(3, 1, 1, 13, 6, 2), b(7, 9, 0.5, 9, 10, 1), b(7, 3, 0.5, 9, 4, 1));
	public static final Block SAKURA_BENCH = furniture("sakura_bench", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 9, true,
			b(0, 7, 2, 16, 9, 12), b(1, 0, 3, 3, 7, 11), b(13, 0, 3, 15, 7, 11), b(1, 9, 11, 3, 13, 12), b(13, 9, 11, 15, 13, 12), b(0, 12, 11, 16, 15, 12.5));
	public static final Block SAKURA_WALL_SHELF = furniture("sakura_wall_shelf", Blocks.OAK_PLANKS, 0, Mount.WALL, 0, true,
			b(0, 6, 9, 16, 8, 16), b(1, 3, 14, 3, 6, 16), b(13, 3, 14, 15, 6, 16), b(1.5, 8, 11, 2.5, 13, 15), b(2.5, 8, 11, 3.5, 12, 15), b(3.5, 8, 11, 4.5, 13.5, 15), b(4.5, 8, 11.5, 5.5, 12.5, 15), b(8, 8, 11, 11, 12, 14), b(8.5, 12, 11.5, 10.5, 13, 13.5), b(12, 8, 11.5, 14, 10, 13.5));
	public static final Block SAKURA_COUNTER = storage("sakura_counter", 27, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 1, 16, 14, 16), b(0, 14, 0, 16, 16, 16), b(1.5, 2, 0.5, 7, 12, 1), b(9, 2, 0.5, 14.5, 12, 1), b(6, 6, 0, 7, 8, 0.5), b(9, 6, 0, 10, 8, 0.5));
	public static final Block SAKURA_CUPBOARD = storage("sakura_cupboard", 27, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 1, 16, 16, 16), b(0.5, 1, 0.5, 7.75, 15, 1), b(8.25, 1, 0.5, 15.5, 15, 1), b(1.5, 2, 0.25, 6.75, 14, 0.5), b(9.25, 2, 0.25, 14.5, 14, 0.5), b(6.5, 7, 0, 7.25, 9, 0.25), b(8.75, 7, 0, 9.5, 9, 0.25));
	public static final Block SAKURA_BEAM = furniture("sakura_beam", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(4, 8, 0, 12, 16, 16));
	public static final Block PALM_TABLE = furniture("palm_table", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 13, 0, 16, 16, 16), b(1, 0, 1, 3, 13, 3), b(1, 0, 13, 3, 13, 15), b(13, 0, 1, 15, 13, 3), b(13, 0, 13, 15, 13, 15), b(1, 10, 2, 3, 11, 14), b(13, 10, 2, 15, 11, 14));
	public static final Block PALM_CHAIR = furniture("palm_chair", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 9, true,
			b(2, 7, 2, 14, 9, 14), b(2, 0, 2, 4, 7, 4), b(2, 0, 12, 4, 7, 14), b(12, 0, 2, 14, 7, 4), b(12, 0, 12, 14, 7, 14), b(2, 9, 12, 4, 16, 14), b(12, 9, 12, 14, 16, 14), b(4, 11, 12.5, 12, 15, 13.5));
	public static final Block PALM_STOOL = furniture("palm_stool", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 10, true,
			b(3, 8, 3, 13, 10, 13), b(3.5, 0, 3.5, 5.5, 8, 5.5), b(3.5, 0, 10.5, 5.5, 8, 12.5), b(10.5, 0, 3.5, 12.5, 8, 5.5), b(10.5, 0, 10.5, 12.5, 8, 12.5), b(4, 3, 5.5, 12, 4, 6.5), b(4, 3, 9.5, 12, 4, 10.5));
	public static final Block PALM_NIGHTSTAND = storage("palm_nightstand", 9, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(1, 0, 2, 15, 13, 15), b(0, 13, 1, 16, 15, 16), b(1.5, 0, 1.5, 3, 13, 2), b(13, 0, 1.5, 14.5, 13, 2), b(3, 7, 1, 13, 12, 2), b(3, 1, 1, 13, 6, 2), b(7, 9, 0.5, 9, 10, 1), b(7, 3, 0.5, 9, 4, 1));
	public static final Block PALM_BENCH = furniture("palm_bench", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 9, true,
			b(0, 7, 2, 16, 9, 12), b(1, 0, 3, 3, 7, 11), b(13, 0, 3, 15, 7, 11), b(1, 9, 11, 3, 13, 12), b(13, 9, 11, 15, 13, 12), b(0, 12, 11, 16, 15, 12.5));
	public static final Block PALM_WALL_SHELF = furniture("palm_wall_shelf", Blocks.OAK_PLANKS, 0, Mount.WALL, 0, true,
			b(0, 6, 9, 16, 8, 16), b(1, 3, 14, 3, 6, 16), b(13, 3, 14, 15, 6, 16), b(1.5, 8, 11, 2.5, 13, 15), b(2.5, 8, 11, 3.5, 12, 15), b(3.5, 8, 11, 4.5, 13.5, 15), b(4.5, 8, 11.5, 5.5, 12.5, 15), b(8, 8, 11, 11, 12, 14), b(8.5, 12, 11.5, 10.5, 13, 13.5), b(12, 8, 11.5, 14, 10, 13.5));
	public static final Block PALM_COUNTER = storage("palm_counter", 27, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 1, 16, 14, 16), b(0, 14, 0, 16, 16, 16), b(1.5, 2, 0.5, 7, 12, 1), b(9, 2, 0.5, 14.5, 12, 1), b(6, 6, 0, 7, 8, 0.5), b(9, 6, 0, 10, 8, 0.5));
	public static final Block PALM_CUPBOARD = storage("palm_cupboard", 27, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 1, 16, 16, 16), b(0.5, 1, 0.5, 7.75, 15, 1), b(8.25, 1, 0.5, 15.5, 15, 1), b(1.5, 2, 0.25, 6.75, 14, 0.5), b(9.25, 2, 0.25, 14.5, 14, 0.5), b(6.5, 7, 0, 7.25, 9, 0.25), b(8.75, 7, 0, 9.5, 9, 0.25));
	public static final Block PALM_BEAM = furniture("palm_beam", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(4, 8, 0, 12, 16, 16));
	public static final Block RED_TABLECLOTH_TABLE = furniture("red_tablecloth_table", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 13, 0, 16, 15, 16), b(0, 15, 0, 16, 16, 16), b(0, 10, 0, 16, 15, 0.5), b(0, 10, 15.5, 16, 15, 16), b(0, 10, 0.5, 0.5, 15, 15.5), b(15.5, 10, 0.5, 16, 15, 15.5), b(1, 0, 1, 3, 13, 3), b(1, 0, 13, 3, 13, 15), b(13, 0, 1, 15, 13, 3), b(13, 0, 13, 15, 13, 15));
	public static final Block WHITE_TABLECLOTH_TABLE = furniture("white_tablecloth_table", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 13, 0, 16, 15, 16), b(0, 15, 0, 16, 16, 16), b(0, 10, 0, 16, 15, 0.5), b(0, 10, 15.5, 16, 15, 16), b(0, 10, 0.5, 0.5, 15, 15.5), b(15.5, 10, 0.5, 16, 15, 15.5), b(1, 0, 1, 3, 13, 3), b(1, 0, 13, 3, 13, 15), b(13, 0, 1, 15, 13, 3), b(13, 0, 13, 15, 13, 15));
	public static final Block BLUE_TABLECLOTH_TABLE = furniture("blue_tablecloth_table", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 13, 0, 16, 15, 16), b(0, 15, 0, 16, 16, 16), b(0, 10, 0, 16, 15, 0.5), b(0, 10, 15.5, 16, 15, 16), b(0, 10, 0.5, 0.5, 15, 15.5), b(15.5, 10, 0.5, 16, 15, 15.5), b(1, 0, 1, 3, 13, 3), b(1, 0, 13, 3, 13, 15), b(13, 0, 1, 15, 13, 3), b(13, 0, 13, 15, 13, 15));
	public static final Block LOW_TABLE = furniture("low_table", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(1, 5, 1, 15, 7, 15), b(2, 0, 2, 4, 5, 4), b(2, 0, 12, 4, 5, 14), b(12, 0, 2, 14, 5, 4), b(12, 0, 12, 14, 5, 14));
	public static final Block TAVERN_BAR = furniture("tavern_bar", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 2, 16, 14, 16), b(0, 14, 0, 16, 16, 16), b(1, 2, 1.5, 7, 12, 2), b(9, 2, 1.5, 15, 12, 2), b(0, 2, 0, 16, 3, 1));
	public static final Block BAR_STOOL = furniture("bar_stool", Blocks.LANTERN, 0, Mount.FLOOR, 14, true,
			b(7, 1, 7, 9, 11, 9), b(5, 0, 5, 11, 1, 11), b(5, 5, 7.5, 11, 6, 8.5), b(4, 11, 4, 12, 13, 12), b(4.5, 13, 4.5, 11.5, 14, 11.5));
	public static final Block RED_FLOOR_CUSHION = furniture("red_floor_cushion", Blocks.WOOL.white(), 0, Mount.FLOOR, 3, true,
			b(2, 0, 2, 14, 3, 14), b(7, 3, 7, 9, 3.5, 9), b(1.5, 0, 1.5, 2.5, 1, 2.5), b(1.5, 0, 13.5, 2.5, 1, 14.5), b(13.5, 0, 1.5, 14.5, 1, 2.5), b(13.5, 0, 13.5, 14.5, 1, 14.5));
	public static final Block BLUE_FLOOR_CUSHION = furniture("blue_floor_cushion", Blocks.WOOL.white(), 0, Mount.FLOOR, 3, true,
			b(2, 0, 2, 14, 3, 14), b(7, 3, 7, 9, 3.5, 9), b(1.5, 0, 1.5, 2.5, 1, 2.5), b(1.5, 0, 13.5, 2.5, 1, 14.5), b(13.5, 0, 1.5, 14.5, 1, 2.5), b(13.5, 0, 13.5, 14.5, 1, 14.5));
	public static final Block PURPLE_FLOOR_CUSHION = furniture("purple_floor_cushion", Blocks.WOOL.white(), 0, Mount.FLOOR, 3, true,
			b(2, 0, 2, 14, 3, 14), b(7, 3, 7, 9, 3.5, 9), b(1.5, 0, 1.5, 2.5, 1, 2.5), b(1.5, 0, 13.5, 2.5, 1, 14.5), b(13.5, 0, 1.5, 14.5, 1, 2.5), b(13.5, 0, 13.5, 14.5, 1, 14.5));
	public static final Block ARMCHAIR = furniture("armchair", Blocks.WOOL.white(), 0, Mount.FLOOR, 8, true,
			b(1, 0, 1, 15, 6, 15), b(2, 6, 1, 14, 8, 13), b(0, 0, 1, 2, 11, 15), b(14, 0, 1, 16, 11, 15), b(0, 11, 1, 2, 12, 15), b(14, 11, 1, 16, 12, 15), b(2, 6, 13, 14, 16, 15), b(2, 15, 15, 14, 16, 16), b(2, 0, 15, 14, 15, 16));
	public static final Block THRONE = furniture("throne", Blocks.LANTERN, 0, Mount.FLOOR, 7, true,
			b(1, 0, 1, 15, 4, 15), b(2, 4, 1, 14, 7, 13), b(0, 0, 1, 2, 11, 13), b(14, 0, 1, 16, 11, 13), b(2, 4, 13, 14, 15, 15), b(0, 0, 13, 2, 16, 16), b(14, 0, 13, 16, 16, 16), b(2, 0, 15, 14, 15, 16), b(5, 15, 13.5, 11, 16, 16));
	public static final Block CAPTAINS_CHAIR = furniture("captains_chair", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 8, true,
			b(2, 6, 2, 14, 8, 14), b(2, 0, 2, 4, 6, 4), b(2, 0, 12, 4, 6, 14), b(12, 0, 2, 14, 6, 4), b(12, 0, 12, 14, 6, 14), b(1, 8, 2, 3, 12, 13), b(13, 8, 2, 15, 12, 13), b(2, 8, 13, 14, 16, 15), b(2, 8, 15, 14, 16, 16));
	public static final Block RED_RUG = furniture("red_rug", Blocks.WOOL.white(), 0, Mount.FLOOR, 0, true,
			b(1, 0, 1, 15, 1, 15), b(0, 0, 0, 16, 1, 1), b(0, 0, 15, 16, 1, 16), b(0, 0, 1, 1, 1, 15), b(15, 0, 1, 16, 1, 15));
	public static final Block BLUE_RUG = furniture("blue_rug", Blocks.WOOL.white(), 0, Mount.FLOOR, 0, true,
			b(1, 0, 1, 15, 1, 15), b(0, 0, 0, 16, 1, 1), b(0, 0, 15, 16, 1, 16), b(0, 0, 1, 1, 1, 15), b(15, 0, 1, 16, 1, 15));
	public static final Block GREEN_RUG = furniture("green_rug", Blocks.WOOL.white(), 0, Mount.FLOOR, 0, true,
			b(1, 0, 1, 15, 1, 15), b(0, 0, 0, 16, 1, 1), b(0, 0, 15, 16, 1, 16), b(0, 0, 1, 1, 1, 15), b(15, 0, 1, 16, 1, 15));
	public static final Block STRAW_MAT = furniture("straw_mat", Blocks.WOOL.white(), 0, Mount.FLOOR, 0, true,
			b(0, 0, 0, 16, 1, 16));
	public static final Block RED_CURTAIN = furniture("red_curtain", Blocks.WOOL.white(), 0, Mount.FLOOR, 0, false,
			b(0, 0, 14.5, 2, 15, 16), b(2, 0, 13.5, 4, 15, 15), b(4, 0, 14.5, 6, 15, 16), b(6, 0, 13.5, 8, 15, 15), b(8, 0, 14.5, 10, 15, 16), b(10, 0, 13.5, 12, 15, 15), b(12, 0, 14.5, 14, 15, 16), b(14, 0, 13.5, 16, 15, 15), b(0, 15, 13, 16, 16, 16));
	public static final Block WHITE_CURTAIN = furniture("white_curtain", Blocks.WOOL.white(), 0, Mount.FLOOR, 0, false,
			b(0, 0, 14.5, 2, 15, 16), b(2, 0, 13.5, 4, 15, 15), b(4, 0, 14.5, 6, 15, 16), b(6, 0, 13.5, 8, 15, 15), b(8, 0, 14.5, 10, 15, 16), b(10, 0, 13.5, 12, 15, 15), b(12, 0, 14.5, 14, 15, 16), b(14, 0, 13.5, 16, 15, 15), b(0, 15, 13, 16, 16, 16));
	public static final Block BLUE_CURTAIN = furniture("blue_curtain", Blocks.WOOL.white(), 0, Mount.FLOOR, 0, false,
			b(0, 0, 14.5, 2, 15, 16), b(2, 0, 13.5, 4, 15, 15), b(4, 0, 14.5, 6, 15, 16), b(6, 0, 13.5, 8, 15, 15), b(8, 0, 14.5, 10, 15, 16), b(10, 0, 13.5, 12, 15, 15), b(12, 0, 14.5, 14, 15, 16), b(14, 0, 13.5, 16, 15, 15), b(0, 15, 13, 16, 16, 16));
	public static final Block GRAIN_SACK = furniture("grain_sack", Blocks.WOOL.white(), 0, Mount.FLOOR, 0, true,
			b(4, 0, 4, 12, 9, 12), b(5.5, 9, 5.5, 10.5, 11, 10.5), b(6, 11, 6, 10, 12, 10));
	public static final Block SACK_PILE = furniture("sack_pile", Blocks.WOOL.white(), 0, Mount.FLOOR, 0, true,
			b(1, 0, 1, 8, 7, 8), b(8, 0, 2, 15, 7, 9), b(4, 0, 8, 12, 7, 15), b(5, 7, 4, 11, 12, 10));
	public static final Block SMALL_CRATE = furniture("small_crate", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(3, 0, 3, 13, 8, 13), b(3, 0, 2.5, 13, 1, 3), b(3, 7, 2.5, 13, 8, 3), b(3, 0, 13, 13, 1, 13.5), b(3, 7, 13, 13, 8, 13.5));
	public static final Block CRATE_STACK = furniture("crate_stack", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 0, 10, 10, 10), b(0, 9, 0, 10, 10, 10), b(2, 10, 2, 9, 16, 9), b(10, 0, 7, 16, 6, 15), b(1, 0, 10, 9, 5, 16));
	public static final Block FISH_CRATE = furniture("fish_crate", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(2, 0, 2, 14, 6, 14), b(2, 0, 1.5, 14, 1, 2), b(2, 5, 1.5, 14, 6, 2), b(3, 5, 3.5, 6, 7, 12.5), b(6.5, 5, 3.5, 9.5, 7, 12.5), b(10, 5, 3.5, 13, 7, 12.5));
	public static final Block FRUIT_CRATE = furniture("fruit_crate", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(2, 0, 2, 14, 6, 14), b(2, 0, 1.5, 14, 1, 2), b(2, 5, 1.5, 14, 6, 2), b(3, 5, 3, 7, 8, 7), b(8, 5, 3.5, 12, 8, 7.5), b(3.5, 5, 8.5, 7.5, 8, 12.5), b(8.5, 5, 9, 12.5, 7.5, 13));
	public static final Block KEG = furniture("keg", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(2, 2, 1.5, 14, 14, 15), b(1, 0, 3, 15, 2, 5), b(1, 0, 11, 15, 2, 13), b(7.5, 5, 0, 8.5, 7, 1.5));
	public static final Block POWDER_KEG = furniture("powder_keg", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(3, 0, 3, 13, 12, 13), b(2.9, 5, 2.9, 13.1, 7, 13.1), b(7.5, 12, 7.5, 8.5, 15, 8.5));
	public static final Block CANNONBALL_PILE = furniture("cannonball_pile", Blocks.LANTERN, 0, Mount.FLOOR, 0, true,
			b(2, 0, 2, 7, 5, 7), b(9, 0, 2, 14, 5, 7), b(2, 0, 9, 7, 5, 14), b(9, 0, 9, 14, 5, 14), b(5.5, 4.5, 5.5, 10.5, 9.5, 10.5));
	public static final Block TREASURE_PILE = furniture("treasure_pile", Blocks.LANTERN, 0, Mount.FLOOR, 0, true,
			b(1, 0, 1, 15, 2, 15), b(3, 2, 3, 13, 4, 13), b(5, 4, 5, 11, 6, 11), b(11, 2, 2, 13, 7, 4), b(4, 2, 10, 6, 4, 12), b(10, 4, 4.5, 11.5, 5.5, 6));
	public static final Block PIRATE_CHEST = storage("pirate_chest", 27, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(1, 0, 2, 15, 9, 14), b(1, 9, 3, 15, 11, 13), b(1.5, 11, 4.5, 14.5, 12, 11.5), b(3, 0, 1.5, 4, 11, 14.5), b(12, 0, 1.5, 13, 11, 14.5), b(7, 5, 1.5, 9, 8, 2));
	public static final Block BARREL_TABLE = furniture("barrel_table", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(2, 0, 2, 14, 13, 14), b(0, 13, 0, 16, 15, 16));
	public static final Block WINE_RACK = furniture("wine_rack", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 4, 16, 16, 16), b(1.5, 1.5, 3.5, 4.5, 4.5, 4), b(1.5, 6.5, 3.5, 4.5, 9.5, 4), b(1.5, 11.5, 3.5, 4.5, 14.5, 4), b(6.5, 1.5, 3.5, 9.5, 4.5, 4), b(6.5, 6.5, 3.5, 9.5, 9.5, 4), b(6.5, 11.5, 3.5, 9.5, 14.5, 4), b(11.5, 1.5, 3.5, 14.5, 4.5, 4), b(11.5, 6.5, 3.5, 14.5, 9.5, 4), b(11.5, 11.5, 3.5, 14.5, 14.5, 4));
	public static final Block LIFE_RING = furniture("life_ring", Blocks.WOOL.white(), 0, Mount.WALL, 0, true,
			b(4, 12, 14, 12, 14, 16), b(4, 2, 14, 12, 4, 16), b(2, 4, 14, 4, 12, 16), b(12, 4, 14, 14, 12, 16), b(3, 3, 14, 5, 5, 16), b(11, 3, 14, 13, 5, 16), b(3, 11, 14, 5, 13, 16), b(11, 11, 14, 13, 13, 16));
	public static final Block ROPE_LADDER = furniture("rope_ladder", Blocks.WOOL.white(), 0, Mount.WALL, 0, false,
			b(1, 0, 15, 2, 16, 16), b(14, 0, 15, 15, 16, 16), b(2, 2, 14.5, 14, 3, 15.5), b(2, 6, 14.5, 14, 7, 15.5), b(2, 10, 14.5, 14, 11, 15.5), b(2, 14, 14.5, 14, 15, 15.5));
	public static final Block HANGING_ROPE = furniture("hanging_rope", Blocks.WOOL.white(), 0, Mount.CEILING, 0, false,
			b(7, 0, 7, 9, 16, 9));
	public static final Block FISHING_NET = furniture("fishing_net", Blocks.WOOL.white(), 0, Mount.WALL, 0, false,
			b(0, 0, 15.5, 16, 16, 15.5), b(3, 12, 14.5, 5, 14, 15.5), b(11, 5, 14.5, 13, 7, 15.5));
	public static final Block CAPSTAN = furniture("capstan", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(2, 0, 2, 14, 2, 14), b(4, 2, 4, 12, 12, 12), b(3, 12, 3, 13, 14, 13), b(0, 10, 7, 16, 11, 9), b(7, 10, 0, 9, 11, 16));
	public static final Block TELESCOPE = furniture("telescope", Blocks.LANTERN, 0, Mount.FLOOR, 0, true,
			b(3, 0, 7.5, 4, 9, 8.5), b(12, 0, 7.5, 13, 9, 8.5), b(7.5, 0, 12, 8.5, 9, 13), b(7, 9, 7, 9, 10, 9), b(7, 10, 2, 9, 12, 14));
	public static final Block GLOBE = furniture("globe", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(5, 0, 5, 11, 1, 11), b(7.5, 1, 7.5, 8.5, 4, 8.5), b(4, 4, 4, 12, 12, 12), b(7.5, 12, 7.5, 8.5, 13, 8.5));
	public static final Block CHART_TABLE = furniture("chart_table", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 13, 0, 16, 15, 16), b(1, 15, 1, 15, 15.5, 15), b(11, 15.5, 11, 13, 16, 13), b(1, 0, 1, 3, 13, 3), b(1, 0, 13, 3, 13, 15), b(13, 0, 1, 15, 13, 3), b(13, 0, 13, 15, 13, 15));
	public static final Block WEAPON_RACK = furniture("weapon_rack", Blocks.OAK_PLANKS, 0, Mount.WALL, 0, true,
			b(0, 3, 15, 16, 13, 16), b(3, 4, 14, 4, 15, 15), b(2, 4, 13.5, 5, 5, 15), b(3, 1, 14, 4, 4, 15), b(7.5, 4, 14, 8.5, 15, 15), b(6.5, 4, 13.5, 9.5, 5, 15), b(7.5, 1, 14, 8.5, 4, 15), b(12, 4, 14, 13, 15, 15), b(11, 4, 13.5, 14, 5, 15), b(12, 1, 14, 13, 4, 15));
	public static final Block KATANA_STAND = furniture("katana_stand", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(2, 0, 5, 14, 1, 11), b(3, 1, 7, 4, 8, 9), b(12, 1, 7, 13, 8, 9), b(1, 4, 7.5, 15, 5, 8.5), b(1, 6.5, 7.5, 15, 7.5, 8.5));
	public static final Block DISPLAY_PEDESTAL = furniture("display_pedestal", Blocks.STONE_BRICKS, 0, Mount.FLOOR, 0, true,
			b(2, 0, 2, 14, 2, 14), b(4, 2, 4, 12, 12, 12), b(2, 12, 2, 14, 14, 14), b(4, 14, 4, 12, 15, 12));
	public static final Block IRON_STOVE = furniture("iron_stove", Blocks.LANTERN, 10, Mount.FLOOR, 0, true,
			b(1, 0, 1, 15, 12, 15), b(4, 2, 0.5, 12, 8, 1), b(0, 12, 0, 16, 13, 16), b(10, 13, 11, 14, 16, 15));
	public static final Block HEARTH = furniture("hearth", Blocks.STONE_BRICKS, 13, Mount.FLOOR, 0, true,
			b(0, 0, 0, 3, 14, 16), b(13, 0, 0, 16, 14, 16), b(3, 0, 12, 13, 14, 16), b(0, 14, 0, 16, 16, 16), b(3, 0, 0, 13, 1, 12), b(4, 1, 4, 12, 3, 7), b(4, 1, 6, 12, 11, 6));
	public static final Block COOKING_POT = furniture("cooking_pot", Blocks.LANTERN, 0, Mount.FLOOR, 0, true,
			b(3, 0, 3, 13, 8, 13), b(1, 6, 7, 3, 7, 9), b(13, 6, 7, 15, 7, 9));
	public static final Block MEAT_PLATTER = furniture("meat_platter", Blocks.WOOL.white(), 0, Mount.FLOOR, 0, true,
			b(2, 0, 2, 14, 1, 14), b(4, 1, 5, 11, 6, 11), b(2, 2.5, 7, 4, 4, 9), b(11, 2.5, 7, 13.5, 4, 9));
	public static final Block FRUIT_BOWL = furniture("fruit_bowl", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(4, 0, 4, 12, 2, 12), b(5, 2, 5, 8, 5, 8), b(8, 2, 6, 11, 5, 9), b(6, 2, 8, 9, 4.5, 11));
	public static final Block BREAD_BASKET = furniture("bread_basket", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(3, 0, 3, 13, 4, 13), b(4, 3, 5, 12, 6, 8), b(5, 3, 8.5, 11, 5.5, 11.5), b(7.5, 4, 3.5, 8.5, 9, 12.5));
	public static final Block SAKE_SET = furniture("sake_set", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(2, 0, 3, 14, 1, 13), b(4, 1, 6, 7, 8, 9), b(5, 8, 7, 6, 10, 8), b(9, 1, 5, 11, 2.5, 7), b(11, 1, 8, 13, 2.5, 10));
	public static final Block BEER_MUGS = furniture("beer_mugs", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(3, 0, 3, 7, 6, 7), b(3, 6, 3, 7, 7, 7), b(7, 2, 4.5, 8, 5, 5.5), b(9, 0, 8, 13, 6, 12), b(9, 6, 8, 13, 7, 12), b(13, 2, 9.5, 14, 5, 10.5));
	public static final Block TEA_SET = furniture("tea_set", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(2, 0, 3, 14, 1, 13), b(4, 1, 5, 9, 5, 10), b(9, 3, 7, 11, 4, 8), b(6, 5, 7, 7, 6, 8), b(10, 1, 9, 12, 2.5, 11), b(11, 1, 4, 13, 2.5, 6));
	public static final Block BATHTUB = furniture("bathtub", Blocks.STONE_BRICKS, 0, Mount.FLOOR, 0, true,
			b(0, 1, 0, 16, 2, 16), b(0, 2, 0, 16, 9, 1), b(0, 2, 15, 16, 9, 16), b(0, 2, 1, 1, 9, 15), b(15, 2, 1, 16, 9, 15), b(1, 2, 1, 15, 7, 15), b(0.5, 0, 0.5, 2.5, 1, 2.5), b(0.5, 0, 13.5, 2.5, 1, 15.5), b(13.5, 0, 0.5, 15.5, 1, 2.5), b(13.5, 0, 13.5, 15.5, 1, 15.5));
	public static final Block WOODEN_TUB = furniture("wooden_tub", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 0, 16, 1, 16), b(0, 1, 0, 16, 10, 1.5), b(0, 1, 14.5, 16, 10, 16), b(0, 1, 1.5, 1.5, 10, 14.5), b(14.5, 1, 1.5, 16, 10, 14.5), b(1.5, 1, 1.5, 14.5, 8, 14.5), b(0, 3, 0, 16, 4, 0.2), b(0, 7, 0, 16, 8, 0.2));
	public static final Block TOOL_BENCH = furniture("tool_bench", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 12, 0, 16, 15, 16), b(1, 4, 1, 15, 5, 15), b(3, 15, 5, 9, 16, 6.5), b(5, 15, 6.5, 6.5, 16, 11), b(10, 15, 3, 14, 15.5, 9), b(0.5, 0, 0.5, 2.5, 12, 2.5), b(0.5, 0, 13.5, 2.5, 12, 15.5), b(13.5, 0, 0.5, 15.5, 12, 2.5), b(13.5, 0, 13.5, 15.5, 12, 15.5));
	public static final Block TOOL_RACK = furniture("tool_rack", Blocks.OAK_PLANKS, 0, Mount.WALL, 0, true,
			b(1, 4, 15, 15, 13, 16), b(3, 5, 14, 4, 12, 15), b(2, 10, 14, 5, 12, 15), b(7, 5, 14, 8, 12, 15), b(6.5, 10, 14, 9, 13, 15), b(11, 6, 14, 14, 12, 14.5));
	public static final Block DRAFTING_TABLE = furniture("drafting_table", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 11, 1, 16, 12, 15), b(1, 12, 2, 15, 12.2, 14), b(1, 0, 1, 3, 10, 3), b(1, 0, 13, 3, 10, 15), b(13, 0, 1, 15, 10, 3), b(13, 0, 13, 15, 10, 15));
	public static final Block BOOK_STACK = furniture("book_stack", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(3, 0, 3, 13, 2, 12), b(4, 2, 4, 12, 4, 11.5), b(3.5, 4, 3, 12.5, 6, 12), b(5, 6, 4, 11, 8, 11));
	public static final Block WRITING_DESK = furniture("writing_desk", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 12, 0, 16, 14, 16), b(11, 0, 1, 15, 12, 15), b(1, 0, 1, 3, 12, 3), b(1, 0, 13, 3, 12, 15), b(11.5, 6, 0.5, 14.5, 10, 1), b(2, 14, 3, 8, 14.2, 9), b(11, 14, 10, 13, 16, 12));
	public static final Block FILING_CABINET = storage("filing_cabinet", 27, Blocks.LANTERN, 0, Mount.FLOOR, 0, true,
			b(2, 0, 3, 14, 16, 16), b(3, 1, 2.5, 13, 7, 3), b(3, 8, 2.5, 13, 14, 3), b(7, 5, 2, 9, 5.5, 2.5), b(7, 12, 2, 9, 12.5, 2.5));
	public static final Block NOTICE_BOARD = furniture("notice_board", Blocks.OAK_PLANKS, 0, Mount.WALL, 0, true,
			b(0, 2, 15, 16, 14, 16), b(1, 3, 14.5, 15, 13, 15));
	public static final Block PIANO = furniture("piano", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 6, 16, 14, 16), b(0, 7, 2, 16, 8, 6), b(0.5, 8, 2, 15.5, 8.5, 6), b(0.5, 0, 2, 1.5, 7, 3), b(14.5, 0, 2, 15.5, 7, 3), b(0, 14, 5.5, 16, 15, 16));
	public static final Block FOLDING_SCREEN = furniture("folding_screen", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 12, 6, 16, 13), b(5, 0, 13, 11, 16, 14), b(10, 0, 12, 16, 16, 13), b(0, 15, 12, 6, 16, 13), b(5, 15, 13, 11, 16, 14), b(10, 15, 12, 16, 16, 13));
	public static final Block STONE_BALUSTRADE = furniture("stone_balustrade", Blocks.STONE_BRICKS, 0, Mount.FLOOR, 0, true,
			b(0, 13, 4, 16, 16, 12), b(0, 0, 4, 16, 3, 12), b(1.5, 3, 6, 4.5, 13, 10), b(6.5, 3, 6, 9.5, 13, 10), b(11.5, 3, 6, 14.5, 13, 10));
	public static final Block SANDSTONE_BALUSTRADE = furniture("sandstone_balustrade", Blocks.STONE_BRICKS, 0, Mount.FLOOR, 0, true,
			b(0, 13, 4, 16, 16, 12), b(0, 0, 4, 16, 3, 12), b(1.5, 3, 6, 4.5, 13, 10), b(6.5, 3, 6, 9.5, 13, 10), b(11.5, 3, 6, 14.5, 13, 10));
	public static final Block MARBLE_BALUSTRADE = furniture("marble_balustrade", Blocks.STONE_BRICKS, 0, Mount.FLOOR, 0, true,
			b(0, 13, 4, 16, 16, 12), b(0, 0, 4, 16, 3, 12), b(1.5, 3, 6, 4.5, 13, 10), b(6.5, 3, 6, 9.5, 13, 10), b(11.5, 3, 6, 14.5, 13, 10));
	public static final Block PET_BED = furniture("pet_bed", Blocks.WOOL.white(), 0, Mount.FLOOR, 0, true,
			b(1, 0, 1, 15, 2, 15), b(1, 2, 1, 15, 3, 2), b(1, 2, 14, 15, 6, 15), b(1, 2, 2, 2, 5, 14), b(14, 2, 2, 15, 5, 14), b(2, 2, 2, 14, 3.5, 14));
	public static final Block PET_BOWL = furniture("pet_bowl", Blocks.LANTERN, 0, Mount.FLOOR, 0, true,
			b(4, 0, 4, 12, 3, 12), b(5, 2.5, 5, 11, 3, 11));
	public static final Block DEN_DEN_MUSHI_PHONE = furniture("den_den_mushi_phone", Blocks.WOOL.white(), 0, Mount.FLOOR, 0, true,
			b(4, 0, 3, 12, 3, 13), b(5, 3, 6, 11, 8, 12), b(6, 3, 3, 7, 6, 4), b(9, 3, 3, 10, 6, 4), b(4, 8, 8, 12, 9.5, 10), b(6.5, 3, 4, 9.5, 5, 6));
	public static final Block MIKAN_TREE_POT = furniture("mikan_tree_pot", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(5, 0, 5, 11, 5, 11), b(7.5, 5, 7.5, 8.5, 9, 8.5), b(3, 9, 3, 13, 15, 13), b(4, 12, 2.5, 6, 14, 3), b(9, 10, 2.5, 11, 12, 3), b(12.5, 12, 6, 13.5, 14, 8), b(2.5, 10, 9, 3.5, 12, 11), b(7, 15, 7, 9, 16, 9));
	public static final Block LAMP_DIAL = furniture("lamp_dial", Blocks.STONE_BRICKS, 13, Mount.FLOOR, 0, true,
			b(5, 0, 5, 11, 4, 11), b(5.5, 0, 4.5, 10.5, 3, 5), b(6, 4, 6, 10, 6, 10));
	public static final Block MEDICINE_CABINET = storage("medicine_cabinet", 9, Blocks.LANTERN, 0, Mount.FLOOR, 0, true,
			b(1, 0, 4, 15, 14, 16), b(1.5, 1, 3.5, 7.75, 13, 4), b(8.25, 1, 3.5, 14.5, 13, 4), b(6.5, 9, 3.25, 9.5, 10, 3.5), b(7.5, 8, 3.25, 8.5, 11, 3.5));
	public static final Block KOTATSU = furniture("kotatsu", Blocks.WOOL.white(), 0, Mount.FLOOR, 0, true,
			b(0.5, 0, 0.5, 15.5, 6, 15.5), b(0.5, 0, 0.5, 15.5, 1, 15.5), b(0, 6, 0, 16, 7.5, 16));
	public static final Block ANDON_LANTERN = furniture("andon_lantern", Blocks.OAK_PLANKS, 14, Mount.FLOOR, 0, true,
			b(4, 0, 4, 12, 1, 12), b(4.5, 1, 4.5, 11.5, 13, 11.5), b(4, 13, 4, 12, 14, 12), b(7, 14, 7, 9, 15, 9));
	public static final Block JOLLY_ROGER_BANNER = furniture("jolly_roger_banner", Blocks.WOOL.white(), 0, Mount.WALL, 0, false,
			b(0, 14, 14, 16, 15.5, 16), b(1, 1, 15, 15, 14, 15.5));
	public static final Block COLA_BARREL = furniture("cola_barrel", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(2, 0, 2, 14, 13, 14), b(1.9, 3, 1.9, 14.1, 4.5, 14.1), b(1.9, 9, 1.9, 14.1, 10.5, 14.1));
	public static final Block TRAINING_WEIGHTS = furniture("training_weights", Blocks.LANTERN, 0, Mount.FLOOR, 0, true,
			b(1, 3, 7, 15, 4.5, 8.5), b(1, 0, 4, 4, 8, 11.5), b(12, 0, 4, 15, 8, 11.5));
	public static final Block HAMMOCK = furniture("hammock", Blocks.WOOL.white(), 0, Mount.FLOOR, 6, true,
			b(0, 0, 7, 1.5, 14, 9), b(14.5, 0, 7, 16, 14, 9), b(2, 4, 4, 14, 5.5, 12), b(1.5, 5, 7.5, 2.5, 12, 8.5), b(13.5, 5, 7.5, 14.5, 12, 8.5));
	public static final Block BONSAI = furniture("bonsai", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(4, 0, 5, 12, 3, 11), b(7.5, 3, 7.5, 8.5, 8, 8.5), b(5.5, 7, 7.5, 7.5, 8, 8.5), b(3, 8, 5, 9, 10, 10), b(8, 9.5, 6, 13, 11.5, 11), b(6, 11.5, 6.5, 10, 13, 10));
	public static final Block GALLEY_SINK = furniture("galley_sink", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 1, 16, 13, 16), b(1.5, 2, 0.5, 14.5, 12, 1), b(0, 13, 0, 16, 14, 16), b(0, 14, 0, 16, 16, 3), b(0, 14, 13, 16, 16, 16), b(0, 14, 3, 3, 16, 13), b(13, 14, 3, 16, 16, 13), b(3, 14, 3, 13, 14.5, 13), b(7.5, 16, 13.5, 8.5, 16, 14.5), b(7.5, 16, 11, 8.5, 16, 13.5));
	public static final Block GRAND_LINE_WALL_MAP = furniture("grand_line_wall_map", Blocks.OAK_PLANKS, 0, Mount.WALL, 0, false,
			b(0, 1, 15, 16, 15, 16), b(1, 2, 14.5, 15, 14, 15));
	public static final Block STRAW_HAT_STAND = furniture("straw_hat_stand", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(5, 0, 5, 11, 1, 11), b(7.5, 1, 7.5, 8.5, 10, 8.5), b(3, 10, 3, 13, 10.75, 13), b(5, 10.75, 5, 11, 13, 11), b(4.9, 10.75, 4.9, 11.1, 11.75, 11.1));
	public static final Block WANO_TANSU = storage("wano_tansu", 27, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 1, 16, 14, 16), b(0, 14, 0.5, 16, 16, 16), b(1, 1, 0.5, 15, 4.5, 1), b(1, 5.5, 0.5, 15, 9, 1), b(1, 10, 0.5, 7.5, 13, 1), b(8.5, 10, 0.5, 15, 13, 1), b(7, 2.5, 0, 9, 3.25, 0.5), b(7, 7, 0, 9, 7.75, 0.5), b(3.5, 11.25, 0, 5, 12, 0.5), b(11, 11.25, 0, 12.5, 12, 0.5));
	public static final Block ENGAWA_BENCH = furniture("engawa_bench", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 8, true,
			b(0, 6, 2, 16, 8, 14), b(1, 0, 3, 3, 6, 13), b(13, 0, 3, 15, 6, 13), b(3, 2, 7, 13, 3, 9));
	public static final Block GOLDEN_BYOBU = furniture("golden_byobu", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 12, 6, 16, 13), b(5, 0, 13, 11, 16, 14), b(10, 0, 12, 16, 16, 13), b(0, 15, 11.9, 6, 16, 13.1), b(5, 15, 12.9, 11, 16, 14.1), b(10, 15, 11.9, 16, 16, 13.1));
	public static final Block HIBACHI_BRAZIER = furniture("hibachi_brazier", Blocks.LANTERN, 13, Mount.FLOOR, 0, true,
			b(3, 0, 3, 13, 1, 13), b(3.5, 1, 3.5, 12.5, 6, 12.5), b(3, 6, 3, 13, 7, 13), b(4.5, 6, 4.5, 11.5, 6.75, 11.5));
	public static final Block KAKEJIKU_SCROLL = furniture("kakejiku_scroll", Blocks.WOOL.white(), 0, Mount.WALL, 0, false,
			b(2, 14, 15, 14, 15, 16), b(2, 1, 15, 14, 2, 16), b(3, 2, 15.5, 13, 14, 16), b(7, 5, 15.4, 9, 12, 15.5), b(9.5, 3, 15.4, 11, 4.5, 15.5));
	public static final Block ALABASTA_DIVAN = furniture("alabasta_divan", Blocks.WOOL.white(), 0, Mount.FLOOR, 7, true,
			b(0, 0, 2, 16, 5, 15), b(0.5, 5, 2.5, 15.5, 7, 13), b(0, 5, 13, 16, 12, 15.5), b(0, 5, 2, 2, 9, 13), b(14, 5, 2, 16, 9, 13), b(0, 11.5, 13, 16, 12.5, 15.5));
	public static final Block BRASS_OIL_LAMP = furniture("brass_oil_lamp", Blocks.LANTERN, 14, Mount.FLOOR, 0, true,
			b(6, 0, 6, 10, 1, 10), b(5, 1, 5, 11, 4, 11), b(10, 3, 7.5, 13, 4, 8.5), b(3.5, 2, 7.5, 5, 5, 8.5), b(7, 4, 7, 9, 5, 9), b(12, 4, 7.5, 13, 6, 8.5));
	public static final Block CLAY_WATER_JAR = furniture("clay_water_jar", Blocks.STONE_BRICKS, 0, Mount.FLOOR, 0, true,
			b(4, 0, 4, 12, 10, 12), b(5.5, 10, 5.5, 10.5, 13, 10.5), b(5, 13, 5, 11, 14, 11), b(3.9, 4, 3.9, 12.1, 5, 12.1), b(6, 13.5, 6, 10, 13.75, 10));
	public static final Block ALABASTA_RUG = furniture("alabasta_rug", Blocks.WOOL.white(), 0, Mount.FLOOR, 0, true,
			b(1, 0, 1, 15, 1, 15), b(0, 0, 0, 16, 1, 1), b(0, 0, 15, 16, 1, 16), b(0, 0, 1, 1, 1, 15), b(15, 0, 1, 16, 1, 15), b(7, 0.05, 7, 9, 1.05, 9));
	public static final Block SAND_FLOOR_PILLOW = furniture("sand_floor_pillow", Blocks.WOOL.white(), 0, Mount.FLOOR, 4, true,
			b(1, 0, 1, 15, 3, 15), b(2, 3, 2, 14, 4, 14), b(0.5, 0, 0.5, 1.5, 2, 1.5), b(14.5, 0, 0.5, 15.5, 2, 1.5), b(0.5, 0, 14.5, 1.5, 2, 15.5), b(14.5, 0, 14.5, 15.5, 2, 15.5));
	public static final Block CLOUD_SOFA = furniture("cloud_sofa", Blocks.WOOL.white(), 0, Mount.FLOOR, 7, true,
			b(0, 0, 2, 16, 6, 14), b(0, 6, 11, 16, 13, 15), b(0, 6, 2, 3, 10, 11), b(13, 6, 2, 16, 10, 11));
	public static final Block CLOUD_TABLE = furniture("cloud_table", Blocks.WOOL.white(), 0, Mount.FLOOR, 0, true,
			b(0, 12, 0, 16, 16, 16), b(5, 0, 5, 11, 12, 11), b(3, 0, 3, 13, 3, 13));
	public static final Block CLOUD_STOOL = furniture("cloud_stool", Blocks.WOOL.white(), 0, Mount.FLOOR, 8, true,
			b(3, 0, 3, 13, 8, 13), b(2, 5, 2, 14, 8, 14));
	public static final Block SHANDIAN_DRUM = furniture("shandian_drum", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(2, 0, 2, 14, 11, 14), b(2.5, 11, 2.5, 13.5, 11.5, 13.5), b(1.9, 2, 1.9, 14.1, 3, 14.1), b(1.9, 8, 1.9, 14.1, 9, 14.1), b(1.8, 4, 7.5, 2, 7, 8.5), b(14, 4, 7.5, 14.2, 7, 8.5));
	public static final Block SKY_SHELL_LAMP = furniture("sky_shell_lamp", Blocks.LANTERN, 14, Mount.FLOOR, 0, true,
			b(3, 0, 3, 13, 1, 13), b(4, 1, 4, 12, 3, 12), b(5, 3, 5, 11, 9, 11), b(6, 9, 6, 10, 10, 10));
	public static final Block CORAL_THRONE_CHAIR = furniture("coral_throne_chair", Blocks.STONE_BRICKS, 0, Mount.FLOOR, 9, true,
			b(2, 0, 2, 14, 7, 14), b(2, 7, 2, 14, 9, 14), b(2, 9, 12, 14, 16, 14), b(3, 16, 12.5, 5, 16, 13.5), b(7, 16, 12.5, 9, 16, 13.5), b(11, 16, 12.5, 13, 16, 13.5));
	public static final Block CORAL_TABLE = furniture("coral_table", Blocks.STONE_BRICKS, 0, Mount.FLOOR, 0, true,
			b(0, 13, 0, 16, 16, 16), b(5, 0, 5, 11, 13, 11), b(3, 0, 3, 13, 2, 13));
	public static final Block PEARL_LAMP = furniture("pearl_lamp", Blocks.STONE_BRICKS, 15, Mount.FLOOR, 0, true,
			b(5, 0, 5, 11, 3, 11), b(4, 3, 4, 12, 11, 12));
	public static final Block GIANT_CLAM_BASIN = furniture("giant_clam_basin", Blocks.STONE_BRICKS, 0, Mount.FLOOR, 0, true,
			b(1, 0, 1, 15, 4, 15), b(2, 3.5, 2, 14, 4.05, 14), b(7, 4, 7, 9, 6, 9), b(1, 4, 13, 15, 8, 15));
	public static final Block BUBBLE_DOME_LAMP = furniture("bubble_dome_lamp", Blocks.STONE_BRICKS, 15, Mount.FLOOR, 0, true,
			b(3, 0, 3, 13, 2, 13), b(6, 2, 6, 10, 6, 10), b(3.5, 2, 3.5, 12.5, 11, 12.5));
	public static final Block MARINE_DESK = storage("marine_desk", 9, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 14, 0, 16, 16, 16), b(0, 0, 1, 4, 14, 15), b(12, 0, 1, 16, 14, 15), b(4, 9, 14, 12, 14, 15), b(0.5, 9, 0.5, 3.5, 13, 1), b(12.5, 9, 0.5, 15.5, 13, 1), b(4, 11.5, 0.9, 12, 14, 1.4), b(7, 12, 0.7, 9, 13.5, 0.9), b(1.5, 10.75, 0.25, 2.5, 11.25, 0.5));
	public static final Block MARINE_LOCKER = storage("marine_locker", 27, Blocks.LANTERN, 0, Mount.FLOOR, 0, true,
			b(1, 0, 2, 15, 16, 15), b(1.5, 1, 1.5, 7.75, 15, 2), b(8.25, 1, 1.5, 14.5, 15, 2), b(2.5, 12, 1.25, 6.5, 12.5, 1.5), b(2.5, 13, 1.25, 6.5, 13.5, 1.5), b(9.5, 12, 1.25, 13.5, 12.5, 1.5), b(9.5, 13, 1.25, 13.5, 13.5, 1.5), b(1, 7, 1.4, 15, 8, 1.6));
	public static final Block MARINE_FLAG_STAND = furniture("marine_flag_stand", Blocks.LANTERN, 0, Mount.FLOOR, 0, true,
			b(5, 0, 5, 11, 1, 11), b(7.5, 1, 7.5, 8.5, 16, 8.5), b(8.5, 8, 7.75, 16, 15.5, 8.25), b(8.5, 11, 7.7, 16, 12.5, 8.3));
	public static final Block MARINE_OFFICE_CHAIR = furniture("marine_office_chair", Blocks.LANTERN, 0, Mount.FLOOR, 9, true,
			b(3, 7, 3, 13, 9, 13), b(3, 9, 12, 13, 16, 13.5), b(7, 1, 7, 9, 7, 9), b(2, 0, 7.5, 14, 1, 8.5), b(7.5, 0, 2, 8.5, 1, 14));
	public static final Block MARINE_SUPPLY_CRATE = furniture("marine_supply_crate", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 0, 16, 16, 16), b(0, 6, 0, 16, 10, 16), b(6.5, 6.5, 0, 9.5, 9.5, 0));
	public static final Block CANDY_CHAIR = furniture("candy_chair", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 9, true,
			b(2, 7, 2, 14, 9, 14), b(2, 0, 2, 4, 7, 4), b(12, 0, 2, 14, 7, 4), b(2, 0, 12, 4, 7, 14), b(12, 0, 12, 14, 7, 14), b(2, 9, 12, 14, 16, 14));
	public static final Block CAKE_TABLE = furniture("cake_table", Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(1, 0, 1, 15, 12, 15), b(0, 12, 0, 16, 16, 16), b(7, 16, 7, 9, 16, 9));
	public static final Block LOLLIPOP_LAMP = furniture("lollipop_lamp", Blocks.OAK_PLANKS, 14, Mount.FLOOR, 0, true,
			b(7.5, 0, 7.5, 8.5, 9, 8.5), b(4, 9, 7, 12, 16, 9), b(5, 10, 6.9, 11, 15, 9.1), b(6, 0, 6, 10, 1, 10));
	public static final Block COOKIE_CABINET = storage("cookie_cabinet", 27, Blocks.OAK_PLANKS, 0, Mount.FLOOR, 0, true,
			b(0, 0, 1, 16, 15, 16), b(0, 15, 0.5, 16, 16, 16), b(1, 1, 0.5, 7.75, 14, 1), b(8.25, 1, 0.5, 15, 14, 1), b(6.5, 7, 0, 7.25, 9, 0.5), b(8.75, 7, 0, 9.5, 9, 0.5));
	public static final Block CUPCAKE_STOOL = furniture("cupcake_stool", Blocks.WOOL.white(), 0, Mount.FLOOR, 8, true,
			b(3, 0, 3, 13, 5, 13), b(2.5, 5, 2.5, 13.5, 8, 13.5), b(7, 8, 7, 9, 9.5, 9));
	public static final Block WATER7_STREET_LAMP = furniture("water7_street_lamp", Blocks.LANTERN, 15, Mount.FLOOR, 0, true,
			b(5, 0, 5, 11, 2, 11), b(7, 2, 7, 9, 12, 9), b(5, 12, 5, 11, 13, 11), b(5.5, 13, 5.5, 10.5, 16, 10.5), b(5, 15.5, 5, 11, 16, 11));
	public static final Block CANAL_BENCH = furniture("canal_bench", Blocks.STONE_BRICKS, 0, Mount.FLOOR, 8, true,
			b(0, 6, 2, 16, 8, 12), b(1, 0, 3, 4, 6, 11), b(12, 0, 3, 15, 6, 11), b(0, 10, 11, 16, 14, 12.5), b(1, 8, 11, 3, 10, 12), b(13, 8, 11, 15, 10, 12));
	public static final Block BLUEPRINT_BOARD = furniture("blueprint_board", Blocks.OAK_PLANKS, 0, Mount.WALL, 0, false,
			b(0, 1, 15, 16, 15, 16), b(1, 2, 14.5, 15, 14, 15), b(3, 6, 14.4, 13, 6.5, 14.5), b(4, 6.5, 14.4, 12, 7, 14.5), b(7.75, 7, 14.4, 8.25, 12, 14.5), b(8.25, 8, 14.4, 11, 11, 14.5));
	public static final Block SHIPWRIGHT_TOOL_CHEST = storage("shipwright_tool_chest", 27, Blocks.LANTERN, 0, Mount.FLOOR, 0, true,
			b(1, 0, 2, 15, 13, 15), b(1.5, 1, 1.5, 14.5, 4, 2), b(1.5, 5, 1.5, 14.5, 8, 2), b(1.5, 9, 1.5, 14.5, 12, 2), b(6, 2.25, 1.25, 10, 2.75, 1.5), b(6, 6.25, 1.25, 10, 6.75, 1.5), b(6, 10.25, 1.25, 10, 10.75, 1.5), b(1, 13, 2, 15, 14, 15));
	public static final Block MOORING_BOLLARD = furniture("mooring_bollard", Blocks.STONE_BRICKS, 0, Mount.FLOOR, 0, true,
			b(4, 0, 4, 12, 10, 12), b(3, 10, 3, 13, 12, 13), b(3.9, 5, 3.9, 12.1, 7, 12.1));

	public static final List<Block> ALL = List.of(
			OAK_TABLE,
			OAK_CHAIR,
			OAK_STOOL,
			OAK_NIGHTSTAND,
			OAK_BENCH,
			OAK_WALL_SHELF,
			OAK_COUNTER,
			OAK_CUPBOARD,
			OAK_BEAM,
			SPRUCE_TABLE,
			SPRUCE_CHAIR,
			SPRUCE_STOOL,
			SPRUCE_NIGHTSTAND,
			SPRUCE_BENCH,
			SPRUCE_WALL_SHELF,
			SPRUCE_COUNTER,
			SPRUCE_CUPBOARD,
			SPRUCE_BEAM,
			BIRCH_TABLE,
			BIRCH_CHAIR,
			BIRCH_STOOL,
			BIRCH_NIGHTSTAND,
			BIRCH_BENCH,
			BIRCH_WALL_SHELF,
			BIRCH_COUNTER,
			BIRCH_CUPBOARD,
			BIRCH_BEAM,
			DARK_OAK_TABLE,
			DARK_OAK_CHAIR,
			DARK_OAK_STOOL,
			DARK_OAK_NIGHTSTAND,
			DARK_OAK_BENCH,
			DARK_OAK_WALL_SHELF,
			DARK_OAK_COUNTER,
			DARK_OAK_CUPBOARD,
			DARK_OAK_BEAM,
			SAKURA_TABLE,
			SAKURA_CHAIR,
			SAKURA_STOOL,
			SAKURA_NIGHTSTAND,
			SAKURA_BENCH,
			SAKURA_WALL_SHELF,
			SAKURA_COUNTER,
			SAKURA_CUPBOARD,
			SAKURA_BEAM,
			PALM_TABLE,
			PALM_CHAIR,
			PALM_STOOL,
			PALM_NIGHTSTAND,
			PALM_BENCH,
			PALM_WALL_SHELF,
			PALM_COUNTER,
			PALM_CUPBOARD,
			PALM_BEAM,
			RED_TABLECLOTH_TABLE,
			WHITE_TABLECLOTH_TABLE,
			BLUE_TABLECLOTH_TABLE,
			LOW_TABLE,
			TAVERN_BAR,
			BAR_STOOL,
			RED_FLOOR_CUSHION,
			BLUE_FLOOR_CUSHION,
			PURPLE_FLOOR_CUSHION,
			ARMCHAIR,
			THRONE,
			CAPTAINS_CHAIR,
			RED_RUG,
			BLUE_RUG,
			GREEN_RUG,
			STRAW_MAT,
			RED_CURTAIN,
			WHITE_CURTAIN,
			BLUE_CURTAIN,
			GRAIN_SACK,
			SACK_PILE,
			SMALL_CRATE,
			CRATE_STACK,
			FISH_CRATE,
			FRUIT_CRATE,
			KEG,
			POWDER_KEG,
			CANNONBALL_PILE,
			TREASURE_PILE,
			PIRATE_CHEST,
			BARREL_TABLE,
			WINE_RACK,
			LIFE_RING,
			ROPE_LADDER,
			HANGING_ROPE,
			FISHING_NET,
			CAPSTAN,
			TELESCOPE,
			GLOBE,
			CHART_TABLE,
			WEAPON_RACK,
			KATANA_STAND,
			DISPLAY_PEDESTAL,
			IRON_STOVE,
			HEARTH,
			COOKING_POT,
			MEAT_PLATTER,
			FRUIT_BOWL,
			BREAD_BASKET,
			SAKE_SET,
			BEER_MUGS,
			TEA_SET,
			BATHTUB,
			WOODEN_TUB,
			TOOL_BENCH,
			TOOL_RACK,
			DRAFTING_TABLE,
			BOOK_STACK,
			WRITING_DESK,
			FILING_CABINET,
			NOTICE_BOARD,
			PIANO,
			FOLDING_SCREEN,
			STONE_BALUSTRADE,
			SANDSTONE_BALUSTRADE,
			MARBLE_BALUSTRADE,
			PET_BED,
			PET_BOWL,
			DEN_DEN_MUSHI_PHONE,
			MIKAN_TREE_POT,
			LAMP_DIAL,
			MEDICINE_CABINET,
			KOTATSU,
			ANDON_LANTERN,
			JOLLY_ROGER_BANNER,
			COLA_BARREL,
			TRAINING_WEIGHTS,
			HAMMOCK,
			BONSAI,
			GALLEY_SINK,
			GRAND_LINE_WALL_MAP,
			STRAW_HAT_STAND,
			WANO_TANSU,
			ENGAWA_BENCH,
			GOLDEN_BYOBU,
			HIBACHI_BRAZIER,
			KAKEJIKU_SCROLL,
			ALABASTA_DIVAN,
			BRASS_OIL_LAMP,
			CLAY_WATER_JAR,
			ALABASTA_RUG,
			SAND_FLOOR_PILLOW,
			CLOUD_SOFA,
			CLOUD_TABLE,
			CLOUD_STOOL,
			SHANDIAN_DRUM,
			SKY_SHELL_LAMP,
			CORAL_THRONE_CHAIR,
			CORAL_TABLE,
			PEARL_LAMP,
			GIANT_CLAM_BASIN,
			BUBBLE_DOME_LAMP,
			MARINE_DESK,
			MARINE_LOCKER,
			MARINE_FLAG_STAND,
			MARINE_OFFICE_CHAIR,
			MARINE_SUPPLY_CRATE,
			CANDY_CHAIR,
			CAKE_TABLE,
			LOLLIPOP_LAMP,
			COOKIE_CABINET,
			CUPCAKE_STOOL,
			WATER7_STREET_LAMP,
			CANAL_BENCH,
			BLUEPRINT_BOARD,
			SHIPWRIGHT_TOOL_CHEST,
			MOORING_BOLLARD);

	/** The furniture you can store things in (props.py "storage"): cupboards, counters, nightstands, cabinets, chests. */
	public static final List<Block> STORAGE = List.of(
			OAK_NIGHTSTAND,
			OAK_COUNTER,
			OAK_CUPBOARD,
			SPRUCE_NIGHTSTAND,
			SPRUCE_COUNTER,
			SPRUCE_CUPBOARD,
			BIRCH_NIGHTSTAND,
			BIRCH_COUNTER,
			BIRCH_CUPBOARD,
			DARK_OAK_NIGHTSTAND,
			DARK_OAK_COUNTER,
			DARK_OAK_CUPBOARD,
			SAKURA_NIGHTSTAND,
			SAKURA_COUNTER,
			SAKURA_CUPBOARD,
			PALM_NIGHTSTAND,
			PALM_COUNTER,
			PALM_CUPBOARD,
			PIRATE_CHEST,
			FILING_CABINET,
			MEDICINE_CABINET,
			WANO_TANSU,
			MARINE_DESK,
			MARINE_LOCKER,
			COOKIE_CABINET,
			SHIPWRIGHT_TOOL_CHEST);

	public static void initialize() {
		FlammableBlockRegistry flammable = FlammableBlockRegistry.getDefaultInstance();
		flammable.add(OAK_TABLE, 5, 20);
		flammable.add(OAK_CHAIR, 5, 20);
		flammable.add(OAK_STOOL, 5, 20);
		flammable.add(OAK_NIGHTSTAND, 5, 20);
		flammable.add(OAK_BENCH, 5, 20);
		flammable.add(OAK_WALL_SHELF, 5, 20);
		flammable.add(OAK_COUNTER, 5, 20);
		flammable.add(OAK_CUPBOARD, 5, 20);
		flammable.add(OAK_BEAM, 5, 20);
		flammable.add(SPRUCE_TABLE, 5, 20);
		flammable.add(SPRUCE_CHAIR, 5, 20);
		flammable.add(SPRUCE_STOOL, 5, 20);
		flammable.add(SPRUCE_NIGHTSTAND, 5, 20);
		flammable.add(SPRUCE_BENCH, 5, 20);
		flammable.add(SPRUCE_WALL_SHELF, 5, 20);
		flammable.add(SPRUCE_COUNTER, 5, 20);
		flammable.add(SPRUCE_CUPBOARD, 5, 20);
		flammable.add(SPRUCE_BEAM, 5, 20);
		flammable.add(BIRCH_TABLE, 5, 20);
		flammable.add(BIRCH_CHAIR, 5, 20);
		flammable.add(BIRCH_STOOL, 5, 20);
		flammable.add(BIRCH_NIGHTSTAND, 5, 20);
		flammable.add(BIRCH_BENCH, 5, 20);
		flammable.add(BIRCH_WALL_SHELF, 5, 20);
		flammable.add(BIRCH_COUNTER, 5, 20);
		flammable.add(BIRCH_CUPBOARD, 5, 20);
		flammable.add(BIRCH_BEAM, 5, 20);
		flammable.add(DARK_OAK_TABLE, 5, 20);
		flammable.add(DARK_OAK_CHAIR, 5, 20);
		flammable.add(DARK_OAK_STOOL, 5, 20);
		flammable.add(DARK_OAK_NIGHTSTAND, 5, 20);
		flammable.add(DARK_OAK_BENCH, 5, 20);
		flammable.add(DARK_OAK_WALL_SHELF, 5, 20);
		flammable.add(DARK_OAK_COUNTER, 5, 20);
		flammable.add(DARK_OAK_CUPBOARD, 5, 20);
		flammable.add(DARK_OAK_BEAM, 5, 20);
		flammable.add(SAKURA_TABLE, 5, 20);
		flammable.add(SAKURA_CHAIR, 5, 20);
		flammable.add(SAKURA_STOOL, 5, 20);
		flammable.add(SAKURA_NIGHTSTAND, 5, 20);
		flammable.add(SAKURA_BENCH, 5, 20);
		flammable.add(SAKURA_WALL_SHELF, 5, 20);
		flammable.add(SAKURA_COUNTER, 5, 20);
		flammable.add(SAKURA_CUPBOARD, 5, 20);
		flammable.add(SAKURA_BEAM, 5, 20);
		flammable.add(PALM_TABLE, 5, 20);
		flammable.add(PALM_CHAIR, 5, 20);
		flammable.add(PALM_STOOL, 5, 20);
		flammable.add(PALM_NIGHTSTAND, 5, 20);
		flammable.add(PALM_BENCH, 5, 20);
		flammable.add(PALM_WALL_SHELF, 5, 20);
		flammable.add(PALM_COUNTER, 5, 20);
		flammable.add(PALM_CUPBOARD, 5, 20);
		flammable.add(PALM_BEAM, 5, 20);
		flammable.add(RED_TABLECLOTH_TABLE, 5, 20);
		flammable.add(WHITE_TABLECLOTH_TABLE, 5, 20);
		flammable.add(BLUE_TABLECLOTH_TABLE, 5, 20);
		flammable.add(LOW_TABLE, 5, 20);
		flammable.add(TAVERN_BAR, 5, 20);
		flammable.add(RED_FLOOR_CUSHION, 30, 60);
		flammable.add(BLUE_FLOOR_CUSHION, 30, 60);
		flammable.add(PURPLE_FLOOR_CUSHION, 30, 60);
		flammable.add(ARMCHAIR, 30, 60);
		flammable.add(CAPTAINS_CHAIR, 5, 20);
		flammable.add(RED_RUG, 30, 60);
		flammable.add(BLUE_RUG, 30, 60);
		flammable.add(GREEN_RUG, 30, 60);
		flammable.add(STRAW_MAT, 30, 60);
		flammable.add(RED_CURTAIN, 30, 60);
		flammable.add(WHITE_CURTAIN, 30, 60);
		flammable.add(BLUE_CURTAIN, 30, 60);
		flammable.add(GRAIN_SACK, 30, 60);
		flammable.add(SACK_PILE, 30, 60);
		flammable.add(SMALL_CRATE, 5, 20);
		flammable.add(CRATE_STACK, 5, 20);
		flammable.add(FISH_CRATE, 5, 20);
		flammable.add(FRUIT_CRATE, 5, 20);
		flammable.add(KEG, 5, 20);
		flammable.add(POWDER_KEG, 5, 20);
		flammable.add(PIRATE_CHEST, 5, 20);
		flammable.add(BARREL_TABLE, 5, 20);
		flammable.add(WINE_RACK, 5, 20);
		flammable.add(LIFE_RING, 30, 60);
		flammable.add(ROPE_LADDER, 30, 60);
		flammable.add(HANGING_ROPE, 30, 60);
		flammable.add(FISHING_NET, 30, 60);
		flammable.add(CAPSTAN, 5, 20);
		flammable.add(GLOBE, 5, 20);
		flammable.add(CHART_TABLE, 5, 20);
		flammable.add(WEAPON_RACK, 5, 20);
		flammable.add(KATANA_STAND, 5, 20);
		flammable.add(MEAT_PLATTER, 30, 60);
		flammable.add(FRUIT_BOWL, 5, 20);
		flammable.add(BREAD_BASKET, 5, 20);
		flammable.add(SAKE_SET, 5, 20);
		flammable.add(BEER_MUGS, 5, 20);
		flammable.add(TEA_SET, 5, 20);
		flammable.add(WOODEN_TUB, 5, 20);
		flammable.add(TOOL_BENCH, 5, 20);
		flammable.add(TOOL_RACK, 5, 20);
		flammable.add(DRAFTING_TABLE, 5, 20);
		flammable.add(BOOK_STACK, 5, 20);
		flammable.add(WRITING_DESK, 5, 20);
		flammable.add(NOTICE_BOARD, 5, 20);
		flammable.add(PIANO, 5, 20);
		flammable.add(FOLDING_SCREEN, 5, 20);
		flammable.add(PET_BED, 30, 60);
		flammable.add(DEN_DEN_MUSHI_PHONE, 30, 60);
		flammable.add(MIKAN_TREE_POT, 5, 20);
		flammable.add(KOTATSU, 30, 60);
		flammable.add(ANDON_LANTERN, 5, 20);
		flammable.add(JOLLY_ROGER_BANNER, 30, 60);
		flammable.add(COLA_BARREL, 5, 20);
		flammable.add(HAMMOCK, 30, 60);
		flammable.add(BONSAI, 5, 20);
		flammable.add(GALLEY_SINK, 5, 20);
		flammable.add(GRAND_LINE_WALL_MAP, 5, 20);
		flammable.add(STRAW_HAT_STAND, 5, 20);
		flammable.add(WANO_TANSU, 5, 20);
		flammable.add(ENGAWA_BENCH, 5, 20);
		flammable.add(GOLDEN_BYOBU, 5, 20);
		flammable.add(KAKEJIKU_SCROLL, 30, 60);
		flammable.add(ALABASTA_DIVAN, 30, 60);
		flammable.add(ALABASTA_RUG, 30, 60);
		flammable.add(SAND_FLOOR_PILLOW, 30, 60);
		flammable.add(CLOUD_SOFA, 30, 60);
		flammable.add(CLOUD_TABLE, 30, 60);
		flammable.add(CLOUD_STOOL, 30, 60);
		flammable.add(SHANDIAN_DRUM, 5, 20);
		flammable.add(MARINE_DESK, 5, 20);
		flammable.add(MARINE_SUPPLY_CRATE, 5, 20);
		flammable.add(CANDY_CHAIR, 5, 20);
		flammable.add(CAKE_TABLE, 5, 20);
		flammable.add(LOLLIPOP_LAMP, 5, 20);
		flammable.add(COOKIE_CABINET, 5, 20);
		flammable.add(CUPCAKE_STOOL, 30, 60);
		flammable.add(BLUEPRINT_BOARD, 5, 20);
	}

	private static double[] b(double x1, double y1, double z1, double x2, double y2, double z2) {
		return new double[] {x1, y1, z1, x2, y2, z2};
	}

	private static Block furniture(String name, Block copy, int light, Mount mount, double seat, boolean solid, double[]... boxes) {
		return make(name, 0, copy, light, mount, seat, solid, boxes);
	}

	/** Furniture that opens like a chest, with 9 or 27 slots. */
	private static Block storage(String name, int slots, Block copy, int light, Mount mount, double seat, boolean solid, double[]... boxes) {
		return make(name, slots, copy, light, mount, seat, solid, boxes);
	}

	private static Block make(String name, int slots, Block copy, int light, Mount mount, double seat, boolean solid, double[]... boxes) {
		VoxelShape shape = Shapes.empty();
		for (double[] b : boxes) {
			shape = Shapes.or(shape, Block.box(b[0], b[1], b[2], b[3], b[4], b[5]));
		}
		VoxelShape finalShape = shape.optimize();
		BlockBehaviour.Properties properties = BlockBehaviour.Properties.ofFullCopy(copy)
				.noOcclusion()
				.lightLevel(state -> light);
		if (!solid) {
			properties = properties.noCollision();
		}
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, OnePieceMod.id(name));
		Block block = Registry.register(BuiltInRegistries.BLOCK, key,
				slots > 0 ? new StorageFurnitureBlock(properties.setId(key), finalShape, mount, seat, solid, slots)
						: new FurnitureBlock(properties.setId(key), finalShape, mount, seat, solid));
		ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Registry.register(BuiltInRegistries.ITEM, itemKey, new BlockItem(block, new Item.Properties().useBlockDescriptionPrefix().setId(itemKey)));
		return block;
	}
}
