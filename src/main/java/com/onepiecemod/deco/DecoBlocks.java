package com.onepiecemod.deco;

import java.util.function.Function;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.ColorParticleOption;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.random.WeightedList;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.DoubleHighBlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.ButtonBlock;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.level.block.FenceBlock;
import net.minecraft.world.level.block.FenceGateBlock;
import net.minecraft.world.level.block.FlowerBedBlock;
import net.minecraft.world.level.block.IronBarsBlock;
import net.minecraft.world.level.block.LanternBlock;
import net.minecraft.world.level.block.PressurePlateBlock;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.SaplingBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.TallFlowerBlock;
import net.minecraft.world.level.block.TransparentBlock;
import net.minecraft.world.level.block.TrapDoorBlock;
import net.minecraft.world.level.block.UntintedParticleLeavesBlock;
import net.minecraft.world.level.block.WallBlock;
import net.minecraft.world.level.block.grower.TreeGrower;
import net.minecraft.world.level.block.sounds.AmbientLeavesBlockSoundPlayer;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockSetType;
import net.minecraft.world.level.block.state.properties.WoodType;

import net.fabricmc.fabric.api.registry.FlammableBlockRegistry;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.world.WorldBlocks;

/**
 * Building blocks, wood sets, lanterns and plants from the islands of One Piece.
 *
 * This file is made by tools/deco/gen_deco.py (together with the models, textures, loot tables,
 * tags and recipes). To add a block, add it to that script and run it again rather than editing here.
 */
public class DecoBlocks {
	// ---- Wood sets: Sakura (Wano), Yarukiman Mangrove (Sabaody), Palm (beaches), Gloom (Thriller Bark) ----

	public static final Block SAKURA_LOG = log("sakura_log", Blocks.CHERRY_LOG);
	public static final Block SAKURA_WOOD = log("sakura_wood", Blocks.CHERRY_WOOD);
	public static final Block STRIPPED_SAKURA_LOG = log("stripped_sakura_log", Blocks.STRIPPED_CHERRY_LOG);
	public static final Block STRIPPED_SAKURA_WOOD = log("stripped_sakura_wood", Blocks.STRIPPED_CHERRY_LOG);
	public static final Block SAKURA_PLANKS = cube("sakura_planks", Blocks.OAK_PLANKS);
	public static final Block SAKURA_STAIRS = stairs("sakura_stairs", SAKURA_PLANKS);
	public static final Block SAKURA_SLAB = slab("sakura_slab", SAKURA_PLANKS);
	public static final Block SAKURA_FENCE = fence("sakura_fence", SAKURA_PLANKS);
	public static final Block SAKURA_FENCE_GATE = fenceGate("sakura_fence_gate", SAKURA_PLANKS, WoodType.CHERRY);
	public static final Block SAKURA_DOOR = door("sakura_door", BlockSetType.CHERRY);
	public static final Block SAKURA_TRAPDOOR = trapdoor("sakura_trapdoor", BlockSetType.CHERRY);
	public static final Block SAKURA_BUTTON = button("sakura_button", BlockSetType.CHERRY);
	public static final Block SAKURA_PRESSURE_PLATE = pressurePlate("sakura_pressure_plate", BlockSetType.CHERRY);
	public static final Block SAKURA_LEAVES = leaves("sakura_leaves", ParticleTypes.CHERRY_LEAVES);
	public static final Block SAKURA_SAPLING = sapling("sakura_sapling", "sakura_tree", false);

	public static final Block YARUKIMAN_LOG = log("yarukiman_log", Blocks.CHERRY_LOG);
	public static final Block YARUKIMAN_WOOD = log("yarukiman_wood", Blocks.CHERRY_WOOD);
	public static final Block STRIPPED_YARUKIMAN_LOG = log("stripped_yarukiman_log", Blocks.STRIPPED_CHERRY_LOG);
	public static final Block STRIPPED_YARUKIMAN_WOOD = log("stripped_yarukiman_wood", Blocks.STRIPPED_CHERRY_LOG);
	public static final Block YARUKIMAN_PLANKS = cube("yarukiman_planks", Blocks.OAK_PLANKS);
	public static final Block YARUKIMAN_STAIRS = stairs("yarukiman_stairs", YARUKIMAN_PLANKS);
	public static final Block YARUKIMAN_SLAB = slab("yarukiman_slab", YARUKIMAN_PLANKS);
	public static final Block YARUKIMAN_FENCE = fence("yarukiman_fence", YARUKIMAN_PLANKS);
	public static final Block YARUKIMAN_FENCE_GATE = fenceGate("yarukiman_fence_gate", YARUKIMAN_PLANKS, WoodType.MANGROVE);
	public static final Block YARUKIMAN_DOOR = door("yarukiman_door", BlockSetType.MANGROVE);
	public static final Block YARUKIMAN_TRAPDOOR = trapdoor("yarukiman_trapdoor", BlockSetType.MANGROVE);
	public static final Block YARUKIMAN_BUTTON = button("yarukiman_button", BlockSetType.MANGROVE);
	public static final Block YARUKIMAN_PRESSURE_PLATE = pressurePlate("yarukiman_pressure_plate", BlockSetType.MANGROVE);
	public static final Block YARUKIMAN_LEAVES = leaves("yarukiman_leaves", ColorParticleOption.create(ParticleTypes.TINTED_LEAVES, 0xFF5F9C55));
	public static final Block YARUKIMAN_SAPLING = sapling("yarukiman_sapling", "yarukiman_tree", false);

	public static final Block PALM_LOG = log("palm_log", Blocks.CHERRY_LOG);
	public static final Block PALM_WOOD = log("palm_wood", Blocks.CHERRY_WOOD);
	public static final Block STRIPPED_PALM_LOG = log("stripped_palm_log", Blocks.STRIPPED_CHERRY_LOG);
	public static final Block STRIPPED_PALM_WOOD = log("stripped_palm_wood", Blocks.STRIPPED_CHERRY_LOG);
	public static final Block PALM_PLANKS = cube("palm_planks", Blocks.OAK_PLANKS);
	public static final Block PALM_STAIRS = stairs("palm_stairs", PALM_PLANKS);
	public static final Block PALM_SLAB = slab("palm_slab", PALM_PLANKS);
	public static final Block PALM_FENCE = fence("palm_fence", PALM_PLANKS);
	public static final Block PALM_FENCE_GATE = fenceGate("palm_fence_gate", PALM_PLANKS, WoodType.JUNGLE);
	public static final Block PALM_DOOR = door("palm_door", BlockSetType.JUNGLE);
	public static final Block PALM_TRAPDOOR = trapdoor("palm_trapdoor", BlockSetType.JUNGLE);
	public static final Block PALM_BUTTON = button("palm_button", BlockSetType.JUNGLE);
	public static final Block PALM_PRESSURE_PLATE = pressurePlate("palm_pressure_plate", BlockSetType.JUNGLE);
	public static final Block PALM_LEAVES = leaves("palm_leaves", ColorParticleOption.create(ParticleTypes.TINTED_LEAVES, 0xFF4C9A3A));
	public static final Block PALM_SAPLING = sapling("palm_sapling", "palm_tree", true);

	public static final Block GLOOM_LOG = log("gloom_log", Blocks.CHERRY_LOG);
	public static final Block GLOOM_WOOD = log("gloom_wood", Blocks.CHERRY_WOOD);
	public static final Block STRIPPED_GLOOM_LOG = log("stripped_gloom_log", Blocks.STRIPPED_CHERRY_LOG);
	public static final Block STRIPPED_GLOOM_WOOD = log("stripped_gloom_wood", Blocks.STRIPPED_CHERRY_LOG);
	public static final Block GLOOM_PLANKS = cube("gloom_planks", Blocks.OAK_PLANKS);
	public static final Block GLOOM_STAIRS = stairs("gloom_stairs", GLOOM_PLANKS);
	public static final Block GLOOM_SLAB = slab("gloom_slab", GLOOM_PLANKS);
	public static final Block GLOOM_FENCE = fence("gloom_fence", GLOOM_PLANKS);
	public static final Block GLOOM_FENCE_GATE = fenceGate("gloom_fence_gate", GLOOM_PLANKS, WoodType.PALE_OAK);
	public static final Block GLOOM_DOOR = door("gloom_door", BlockSetType.PALE_OAK);
	public static final Block GLOOM_TRAPDOOR = trapdoor("gloom_trapdoor", BlockSetType.PALE_OAK);
	public static final Block GLOOM_BUTTON = button("gloom_button", BlockSetType.PALE_OAK);
	public static final Block GLOOM_PRESSURE_PLATE = pressurePlate("gloom_pressure_plate", BlockSetType.PALE_OAK);
	public static final Block GLOOM_LEAVES = leaves("gloom_leaves", ParticleTypes.PALE_OAK_LEAVES);
	public static final Block GLOOM_SAPLING = sapling("gloom_sapling", "gloom_tree", false);

	// ---- Extra shapes for Adam wood (the log and planks are in world/WorldBlocks) ----
	public static final Block ADAM_STAIRS = stairs("adam_stairs", WorldBlocks.ADAM_PLANKS);
	public static final Block ADAM_SLAB = slab("adam_slab", WorldBlocks.ADAM_PLANKS);
	public static final Block ADAM_FENCE = fence("adam_fence", WorldBlocks.ADAM_PLANKS);
	public static final Block ADAM_FENCE_GATE = fenceGate("adam_fence_gate", WorldBlocks.ADAM_PLANKS, WoodType.OAK);
	public static final Block ADAM_DOOR = door("adam_door", BlockSetType.OAK);
	public static final Block ADAM_TRAPDOOR = trapdoor("adam_trapdoor", BlockSetType.OAK);
	public static final Block ADAM_BUTTON = button("adam_button", BlockSetType.OAK);
	public static final Block ADAM_PRESSURE_PLATE = pressurePlate("adam_pressure_plate", BlockSetType.OAK);

	// ---- Island building blocks ----
	public static final Block ALABASTA_SANDSTONE_BRICKS = cube("alabasta_sandstone_bricks", Blocks.SANDSTONE);
	public static final Block ALABASTA_SANDSTONE_BRICK_STAIRS = stairs("alabasta_sandstone_brick_stairs", ALABASTA_SANDSTONE_BRICKS);
	public static final Block ALABASTA_SANDSTONE_BRICK_SLAB = slab("alabasta_sandstone_brick_slab", ALABASTA_SANDSTONE_BRICKS);
	public static final Block ALABASTA_SANDSTONE_BRICK_WALL = wall("alabasta_sandstone_brick_wall", ALABASTA_SANDSTONE_BRICKS);
	public static final Block ALABASTA_TILES = cube("alabasta_tiles", Blocks.SMOOTH_SANDSTONE);
	public static final Block ALABASTA_TILE_STAIRS = stairs("alabasta_tile_stairs", ALABASTA_TILES);
	public static final Block ALABASTA_TILE_SLAB = slab("alabasta_tile_slab", ALABASTA_TILES);
	public static final Block WANO_ROOF_TILES = cube("wano_roof_tiles", Blocks.DEEPSLATE_TILES);
	public static final Block WANO_ROOF_TILE_STAIRS = stairs("wano_roof_tile_stairs", WANO_ROOF_TILES);
	public static final Block WANO_ROOF_TILE_SLAB = slab("wano_roof_tile_slab", WANO_ROOF_TILES);
	public static final Block WANO_LACQUER_PLANKS = cube("wano_lacquer_planks", Blocks.OAK_PLANKS);
	public static final Block WANO_LACQUER_STAIRS = stairs("wano_lacquer_stairs", WANO_LACQUER_PLANKS);
	public static final Block WANO_LACQUER_SLAB = slab("wano_lacquer_slab", WANO_LACQUER_PLANKS);
	public static final Block MARINE_BRICKS = cube("marine_bricks", Blocks.STONE_BRICKS);
	public static final Block MARINE_BRICK_STAIRS = stairs("marine_brick_stairs", MARINE_BRICKS);
	public static final Block MARINE_BRICK_SLAB = slab("marine_brick_slab", MARINE_BRICKS);
	public static final Block MARINE_BRICK_WALL = wall("marine_brick_wall", MARINE_BRICKS);
	public static final Block MARINE_TILES = cube("marine_tiles", Blocks.STONE_BRICKS);
	public static final Block MARINE_TILE_STAIRS = stairs("marine_tile_stairs", MARINE_TILES);
	public static final Block MARINE_TILE_SLAB = slab("marine_tile_slab", MARINE_TILES);
	public static final Block CANAL_BRICKS = cube("canal_bricks", Blocks.BRICKS);
	public static final Block CANAL_BRICK_STAIRS = stairs("canal_brick_stairs", CANAL_BRICKS);
	public static final Block CANAL_BRICK_SLAB = slab("canal_brick_slab", CANAL_BRICKS);
	public static final Block CANAL_BRICK_WALL = wall("canal_brick_wall", CANAL_BRICKS);
	public static final Block WATER7_COBBLES = cube("water7_cobbles", Blocks.COBBLESTONE);
	public static final Block WATER7_COBBLE_STAIRS = stairs("water7_cobble_stairs", WATER7_COBBLES);
	public static final Block WATER7_COBBLE_SLAB = slab("water7_cobble_slab", WATER7_COBBLES);
	public static final Block WATER7_COBBLE_WALL = wall("water7_cobble_wall", WATER7_COBBLES);
	public static final Block DRESSROSA_MOSAIC = cube("dressrosa_mosaic", Blocks.TERRACOTTA);
	public static final Block DRESSROSA_MOSAIC_STAIRS = stairs("dressrosa_mosaic_stairs", DRESSROSA_MOSAIC);
	public static final Block DRESSROSA_MOSAIC_SLAB = slab("dressrosa_mosaic_slab", DRESSROSA_MOSAIC);
	public static final Block DRESSROSA_TILES = cube("dressrosa_tiles", Blocks.TERRACOTTA);
	public static final Block DRESSROSA_TILE_STAIRS = stairs("dressrosa_tile_stairs", DRESSROSA_TILES);
	public static final Block DRESSROSA_TILE_SLAB = slab("dressrosa_tile_slab", DRESSROSA_TILES);
	public static final Block DRESSROSA_STUCCO = cube("dressrosa_stucco", Blocks.SMOOTH_SANDSTONE);
	public static final Block DRESSROSA_STUCCO_STAIRS = stairs("dressrosa_stucco_stairs", DRESSROSA_STUCCO);
	public static final Block DRESSROSA_STUCCO_SLAB = slab("dressrosa_stucco_slab", DRESSROSA_STUCCO);
	public static final Block DRESSROSA_STUCCO_WALL = wall("dressrosa_stucco_wall", DRESSROSA_STUCCO);
	public static final Block CORAL_BRICKS = cube("coral_bricks", Blocks.PRISMARINE_BRICKS);
	public static final Block CORAL_BRICK_STAIRS = stairs("coral_brick_stairs", CORAL_BRICKS);
	public static final Block CORAL_BRICK_SLAB = slab("coral_brick_slab", CORAL_BRICKS);
	public static final Block CORAL_BRICK_WALL = wall("coral_brick_wall", CORAL_BRICKS);
	public static final Block PEARL_BLOCK = cube("pearl_block", Blocks.QUARTZ_BLOCK);
	public static final Block PEARL_STAIRS = stairs("pearl_stairs", PEARL_BLOCK);
	public static final Block PEARL_SLAB = slab("pearl_slab", PEARL_BLOCK);
	public static final Block CLOUD_BRICKS = cube("cloud_bricks", Blocks.MOSS_BLOCK);
	public static final Block CLOUD_BRICK_STAIRS = stairs("cloud_brick_stairs", CLOUD_BRICKS);
	public static final Block CLOUD_BRICK_SLAB = slab("cloud_brick_slab", CLOUD_BRICKS);
	public static final Block SHANDORA_GOLD_BRICKS = cube("shandora_gold_bricks", Blocks.STONE_BRICKS);
	public static final Block SHANDORA_GOLD_BRICK_STAIRS = stairs("shandora_gold_brick_stairs", SHANDORA_GOLD_BRICKS);
	public static final Block SHANDORA_GOLD_BRICK_SLAB = slab("shandora_gold_brick_slab", SHANDORA_GOLD_BRICKS);
	public static final Block SHANDORA_GOLD_BRICK_WALL = wall("shandora_gold_brick_wall", SHANDORA_GOLD_BRICKS);
	public static final Block SHANDIAN_RUIN_STONE = cube("shandian_ruin_stone", Blocks.MOSSY_STONE_BRICKS);
	public static final Block SHANDIAN_RUIN_STONE_STAIRS = stairs("shandian_ruin_stone_stairs", SHANDIAN_RUIN_STONE);
	public static final Block SHANDIAN_RUIN_STONE_SLAB = slab("shandian_ruin_stone_slab", SHANDIAN_RUIN_STONE);
	public static final Block SHANDIAN_RUIN_STONE_WALL = wall("shandian_ruin_stone_wall", SHANDIAN_RUIN_STONE);
	public static final Block SNOW_BRICKS = cube("snow_bricks", Blocks.STONE_BRICKS);
	public static final Block SNOW_BRICK_STAIRS = stairs("snow_brick_stairs", SNOW_BRICKS);
	public static final Block SNOW_BRICK_SLAB = slab("snow_brick_slab", SNOW_BRICKS);
	public static final Block SNOW_BRICK_WALL = wall("snow_brick_wall", SNOW_BRICKS);
	public static final Block FROZEN_STONE = cube("frozen_stone", Blocks.STONE);
	public static final Block FROZEN_STONE_STAIRS = stairs("frozen_stone_stairs", FROZEN_STONE);
	public static final Block FROZEN_STONE_SLAB = slab("frozen_stone_slab", FROZEN_STONE);
	public static final Block FROZEN_STONE_WALL = wall("frozen_stone_wall", FROZEN_STONE);
	public static final Block SCORCHED_STONE = cube("scorched_stone", Blocks.BLACKSTONE);
	public static final Block SCORCHED_STONE_STAIRS = stairs("scorched_stone_stairs", SCORCHED_STONE);
	public static final Block SCORCHED_STONE_SLAB = slab("scorched_stone_slab", SCORCHED_STONE);
	public static final Block SCORCHED_STONE_WALL = wall("scorched_stone_wall", SCORCHED_STONE);
	public static final Block SEASTONE_BRICKS = cube("seastone_bricks", Blocks.DEEPSLATE_BRICKS);
	public static final Block SEASTONE_BRICK_STAIRS = stairs("seastone_brick_stairs", SEASTONE_BRICKS);
	public static final Block SEASTONE_BRICK_SLAB = slab("seastone_brick_slab", SEASTONE_BRICKS);
	public static final Block SEASTONE_BRICK_WALL = wall("seastone_brick_wall", SEASTONE_BRICKS);
	public static final Block LAB_PANEL = cube("lab_panel", Blocks.SMOOTH_STONE);
	public static final Block LAB_PANEL_STAIRS = stairs("lab_panel_stairs", LAB_PANEL);
	public static final Block LAB_PANEL_SLAB = slab("lab_panel_slab", LAB_PANEL);
	public static final Block CHOCOLATE_BLOCK = cube("chocolate_block", Blocks.PACKED_MUD);
	public static final Block CHOCOLATE_STAIRS = stairs("chocolate_stairs", CHOCOLATE_BLOCK);
	public static final Block CHOCOLATE_SLAB = slab("chocolate_slab", CHOCOLATE_BLOCK);
	public static final Block COOKIE_BRICKS = cube("cookie_bricks", Blocks.MUD_BRICKS);
	public static final Block COOKIE_BRICK_STAIRS = stairs("cookie_brick_stairs", COOKIE_BRICKS);
	public static final Block COOKIE_BRICK_SLAB = slab("cookie_brick_slab", COOKIE_BRICKS);
	public static final Block COOKIE_BRICK_WALL = wall("cookie_brick_wall", COOKIE_BRICKS);
	public static final Block FROSTING_BLOCK = cube("frosting_block", Blocks.MOSS_BLOCK);
	public static final Block FROSTING_STAIRS = stairs("frosting_stairs", FROSTING_BLOCK);
	public static final Block FROSTING_SLAB = slab("frosting_slab", FROSTING_BLOCK);
	public static final Block LAB_LIGHT = cube("lab_light", Blocks.SEA_LANTERN, 15);
	public static final Block BERRY_BLOCK = cube("berry_block", Blocks.GOLD_BLOCK);

	// ---- Pillars, barrels and crates (they turn like logs) ----
	public static final Block ALUBARNA_PILLAR = pillar("alubarna_pillar", Blocks.SANDSTONE);
	public static final Block MARINE_PILLAR = pillar("marine_pillar", Blocks.QUARTZ_PILLAR);
	public static final Block CANDY_CANE_BLOCK = pillar("candy_cane_block", Blocks.QUARTZ_PILLAR);
	public static final Block TATAMI = pillar("tatami", Blocks.HAY_BLOCK);
	public static final Block SAKE_BARREL = pillar("sake_barrel", Blocks.BARREL);
	public static final Block COLA_CRATE = pillar("cola_crate", Blocks.OAK_PLANKS);
	public static final Block MIKAN_CRATE = pillar("mikan_crate", Blocks.OAK_PLANKS);

	// ---- Glass, screens, bars and lanterns ----
	public static final Block BUBBLE_GLASS = glass("bubble_glass");
	public static final Block BUBBLE_GLASS_PANE = pane("bubble_glass_pane", Blocks.GLASS_PANE);
	public static final Block SHOJI_SCREEN = pane("shoji_screen", Blocks.GLASS_PANE);
	public static final Block PRISON_BARS = pane("prison_bars", Blocks.IRON_BARS);
	public static final Block PAPER_LANTERN = lantern("paper_lantern");
	public static final Block BUBBLE_LAMP = lantern("bubble_lamp");

	// ---- Flowers and plants. Flowers grow on grass, sand, snow, stone and Island Cloud (tag onepiece:deco_plant_soil). ----
	public static final Block CLOUD_PUFF = flower("cloud_puff", MobEffects.SLOW_FALLING, 7, 0);
	public static final Block SKY_LOTUS = flower("sky_lotus", MobEffects.JUMP_BOOST, 7, 0);
	public static final Block FIRE_LILY = flower("fire_lily", MobEffects.FIRE_RESISTANCE, 5, 10);
	public static final Block FROST_BLOOM = flower("frost_bloom", MobEffects.SLOWNESS, 5, 4);
	public static final Block SNOW_LILY = flower("snow_lily", MobEffects.REGENERATION, 4, 0);
	public static final Block GHOST_MUSHROOM = flower("ghost_mushroom", MobEffects.NIGHT_VISION, 5, 7);
	public static final Block DESERT_BLOOM = flower("desert_bloom", MobEffects.SATURATION, 1, 0);
	public static final Block CANDY_CANE_SPROUT = flower("candy_cane_sprout", MobEffects.SPEED, 5, 0);
	public static final Block LOLLIPOP_FLOWER = flower("lollipop_flower", MobEffects.SPEED, 5, 0);
	public static final Block AMAZON_FLOWER = tallPlant("amazon_flower");
	public static final Block GIANT_FERN = tallPlant("giant_fern");
	public static final Block SAKURA_PETALS = petals("sakura_petals");
	public static final Block MIKAN_BUSH = registerBlockOnly("mikan_bush", MikanBushBlock::new, BlockBehaviour.Properties.ofFullCopy(Blocks.SWEET_BERRY_BUSH));

	public static void initialize() {
		FlammableBlockRegistry flammable = FlammableBlockRegistry.getDefaultInstance();
		flammable.add(SAKURA_LOG, 5, 5);
		flammable.add(SAKURA_WOOD, 5, 5);
		flammable.add(STRIPPED_SAKURA_LOG, 5, 5);
		flammable.add(STRIPPED_SAKURA_WOOD, 5, 5);
		flammable.add(SAKURA_PLANKS, 5, 20);
		flammable.add(SAKURA_STAIRS, 5, 20);
		flammable.add(SAKURA_SLAB, 5, 20);
		flammable.add(SAKURA_FENCE, 5, 20);
		flammable.add(SAKURA_FENCE_GATE, 5, 20);
		flammable.add(SAKURA_LEAVES, 30, 60);
		flammable.add(YARUKIMAN_LOG, 5, 5);
		flammable.add(YARUKIMAN_WOOD, 5, 5);
		flammable.add(STRIPPED_YARUKIMAN_LOG, 5, 5);
		flammable.add(STRIPPED_YARUKIMAN_WOOD, 5, 5);
		flammable.add(YARUKIMAN_PLANKS, 5, 20);
		flammable.add(YARUKIMAN_STAIRS, 5, 20);
		flammable.add(YARUKIMAN_SLAB, 5, 20);
		flammable.add(YARUKIMAN_FENCE, 5, 20);
		flammable.add(YARUKIMAN_FENCE_GATE, 5, 20);
		flammable.add(YARUKIMAN_LEAVES, 30, 60);
		flammable.add(PALM_LOG, 5, 5);
		flammable.add(PALM_WOOD, 5, 5);
		flammable.add(STRIPPED_PALM_LOG, 5, 5);
		flammable.add(STRIPPED_PALM_WOOD, 5, 5);
		flammable.add(PALM_PLANKS, 5, 20);
		flammable.add(PALM_STAIRS, 5, 20);
		flammable.add(PALM_SLAB, 5, 20);
		flammable.add(PALM_FENCE, 5, 20);
		flammable.add(PALM_FENCE_GATE, 5, 20);
		flammable.add(PALM_LEAVES, 30, 60);
		flammable.add(GLOOM_LOG, 5, 5);
		flammable.add(GLOOM_WOOD, 5, 5);
		flammable.add(STRIPPED_GLOOM_LOG, 5, 5);
		flammable.add(STRIPPED_GLOOM_WOOD, 5, 5);
		flammable.add(GLOOM_PLANKS, 5, 20);
		flammable.add(GLOOM_STAIRS, 5, 20);
		flammable.add(GLOOM_SLAB, 5, 20);
		flammable.add(GLOOM_FENCE, 5, 20);
		flammable.add(GLOOM_FENCE_GATE, 5, 20);
		flammable.add(GLOOM_LEAVES, 30, 60);
		flammable.add(WANO_LACQUER_PLANKS, 5, 20);
		flammable.add(WANO_LACQUER_STAIRS, 5, 20);
		flammable.add(WANO_LACQUER_SLAB, 5, 20);
	}

	// ---------------------------------------------------------------- helpers

	private static Block cube(String name, Block copy) {
		return register(name, Block::new, BlockBehaviour.Properties.ofFullCopy(copy));
	}

	private static Block cube(String name, Block copy, int light) {
		return register(name, Block::new, BlockBehaviour.Properties.ofFullCopy(copy).lightLevel(state -> light));
	}

	private static Block pillar(String name, Block copy) {
		return register(name, RotatedPillarBlock::new, BlockBehaviour.Properties.ofFullCopy(copy));
	}

	private static Block log(String name, Block copy) {
		return pillar(name, copy);
	}

	private static Block stairs(String name, Block base) {
		return register(name, properties -> new StairBlock(base.defaultBlockState(), properties) {}, BlockBehaviour.Properties.ofFullCopy(base));
	}

	private static Block slab(String name, Block base) {
		return register(name, SlabBlock::new, BlockBehaviour.Properties.ofFullCopy(base));
	}

	private static Block wall(String name, Block base) {
		return register(name, WallBlock::new, BlockBehaviour.Properties.ofFullCopy(base).forceSolidOn());
	}

	private static Block fence(String name, Block planks) {
		return register(name, FenceBlock::new, BlockBehaviour.Properties.ofFullCopy(Blocks.OAK_FENCE).mapColor(planks.defaultMapColor()));
	}

	private static Block fenceGate(String name, Block planks, WoodType type) {
		return register(name, properties -> new FenceGateBlock(type, properties),
				BlockBehaviour.Properties.ofFullCopy(Blocks.OAK_FENCE_GATE).mapColor(planks.defaultMapColor()));
	}

	private static Block door(String name, BlockSetType type) {
		return registerTall(name, properties -> new DoorBlock(type, properties) {}, BlockBehaviour.Properties.ofFullCopy(Blocks.OAK_DOOR));
	}

	private static Block trapdoor(String name, BlockSetType type) {
		return register(name, properties -> new TrapDoorBlock(type, properties) {}, BlockBehaviour.Properties.ofFullCopy(Blocks.OAK_TRAPDOOR));
	}

	private static Block button(String name, BlockSetType type) {
		return register(name, properties -> new ButtonBlock(type, 30, properties) {}, BlockBehaviour.Properties.ofFullCopy(Blocks.OAK_BUTTON));
	}

	private static Block pressurePlate(String name, BlockSetType type) {
		return register(name, properties -> new PressurePlateBlock(type, properties) {}, BlockBehaviour.Properties.ofFullCopy(Blocks.OAK_PRESSURE_PLATE));
	}

	private static Block leaves(String name, ParticleOptions particle) {
		return register(name, properties -> new UntintedParticleLeavesBlock(0.01f, particle, AmbientLeavesBlockSoundPlayer.noAmbientSound(), properties),
				BlockBehaviour.Properties.ofFullCopy(Blocks.CHERRY_LEAVES));
	}

	/** A sapling that grows the tree in data/onepiece/worldgen/feature/<tree>.json. Palms also grow on sand. */
	private static Block sapling(String name, String tree, boolean growsOnSand) {
		ResourceKey<net.minecraft.world.level.levelgen.feature.Feature> feature = ResourceKey.create(Registries.FEATURE, OnePieceMod.id(tree));
		TreeGrower grower = new TreeGrower("onepiece_" + tree, WeightedList.of(feature), WeightedList.of(), WeightedList.of(), feature);
		return register(name, properties -> new SaplingBlock(grower, properties) {
			@Override
			protected boolean mayPlaceOn(BlockState state, BlockGetter level, BlockPos pos) {
				return super.mayPlaceOn(state, level, pos) || (growsOnSand && state.is(BlockTags.SAND));
			}
		}, BlockBehaviour.Properties.ofFullCopy(Blocks.CHERRY_SAPLING));
	}

	private static Block flower(String name, Holder<MobEffect> stewEffect, float seconds, int light) {
		return register(name, properties -> new DecoFlowerBlock(stewEffect, seconds, properties),
				BlockBehaviour.Properties.ofFullCopy(Blocks.POPPY).lightLevel(state -> light));
	}

	private static Block tallPlant(String name) {
		return registerTall(name, TallFlowerBlock::new, BlockBehaviour.Properties.ofFullCopy(Blocks.ROSE_BUSH));
	}

	private static Block petals(String name) {
		return register(name, properties -> new FlowerBedBlock(properties, 3) {}, BlockBehaviour.Properties.ofFullCopy(Blocks.PINK_PETALS));
	}

	private static Block glass(String name) {
		return register(name, properties -> new TransparentBlock(properties) {}, BlockBehaviour.Properties.ofFullCopy(Blocks.GLASS));
	}

	private static Block pane(String name, Block copy) {
		return register(name, properties -> new IronBarsBlock(properties) {}, BlockBehaviour.Properties.ofFullCopy(copy));
	}

	private static Block lantern(String name) {
		return register(name, LanternBlock::new, BlockBehaviour.Properties.ofFullCopy(Blocks.LANTERN));
	}

	/** Registers a block and the item you hold to place it. */
	private static Block register(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
		Block block = registerBlockOnly(name, factory, properties);
		registerItem(name, itemProperties -> new BlockItem(block, itemProperties));
		return block;
	}

	/** Doors and tall plants use an item that places both halves. */
	private static Block registerTall(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
		Block block = registerBlockOnly(name, factory, properties);
		registerItem(name, itemProperties -> new DoubleHighBlockItem(block, itemProperties));
		return block;
	}

	/** A block with no item of its own (the Mikan Bush is planted with a Mikan). */
	static Block registerBlockOnly(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, OnePieceMod.id(name));
		return Registry.register(BuiltInRegistries.BLOCK, key, factory.apply(properties.setId(key)));
	}

	private static void registerItem(String name, Function<Item.Properties, Item> factory) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Registry.register(BuiltInRegistries.ITEM, key, factory.apply(new Item.Properties().useBlockDescriptionPrefix().setId(key)));
	}
}
