package com.onepiecemod.furnish;

import java.util.function.Function;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.deco.DecoFeature;

import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;

/**
 * Lights and planters that always hang on something, made so the big structures can be well lit without
 * floating lanterns or candles: wall lamps, candle sconces, chandeliers, candelabras, ceiling lamps and flower boxes.
 * They are also craftable for players' own builds (in the Deco tab).
 */
public final class Furnish {
	public static final Block WALL_LAMP = fixture("wall_lamp", FixtureBlock.Mount.WALL, 15, SoundType.LANTERN, 5, 1, 5, 11, 11, 16);
	public static final Block CANDLE_SCONCE = fixture("candle_sconce", FixtureBlock.Mount.WALL, 12, SoundType.LANTERN, 5, 2, 8, 11, 12, 16);
	public static final Block CHANDELIER = fixture("chandelier", FixtureBlock.Mount.CEILING, 15, SoundType.CHAIN, 1, 4, 1, 15, 16, 15);
	public static final Block IRON_CHANDELIER = fixture("iron_chandelier", FixtureBlock.Mount.CEILING, 15, SoundType.CHAIN, 1, 4, 1, 15, 16, 15);
	public static final Block CEILING_LAMP = fixture("ceiling_lamp", FixtureBlock.Mount.CEILING, 15, SoundType.WOOD, 2, 13, 2, 14, 16, 14);
	public static final Block CANDELABRA = fixture("candelabra", FixtureBlock.Mount.FLOOR, 13, SoundType.LANTERN, 2, 0, 2, 14, 14, 14);
	public static final Block FLOWER_BOX = fixture("flower_box", FixtureBlock.Mount.WALL, 0, SoundType.WOOD, 0, 0, 9, 16, 11, 16);

	private Furnish() {
	}

	public static void initialize() {
		CreativeModeTabEvents.modifyOutputEvent(DecoFeature.TAB_KEY).register(output -> {
			output.accept(WALL_LAMP);
			output.accept(CANDLE_SCONCE);
			output.accept(CHANDELIER);
			output.accept(IRON_CHANDELIER);
			output.accept(CEILING_LAMP);
			output.accept(CANDELABRA);
			output.accept(FLOWER_BOX);
		});
	}

	private static Block fixture(String name, FixtureBlock.Mount mount, int light, SoundType sound,
			double x0, double y0, double z0, double x1, double y1, double z1) {
		BlockBehaviour.Properties properties = BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(1.0f).sound(sound)
				.lightLevel(state -> light).noOcclusion().pushReaction(PushReaction.POPPED);
		return register(name, p -> new FixtureBlock(p, mount, x0, y0, z0, x1, y1, z1), properties);
	}

	private static Block register(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, OnePieceMod.id(name));
		Block block = Registry.register(BuiltInRegistries.BLOCK, key, factory.apply(properties.setId(key)));
		ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Registry.register(BuiltInRegistries.ITEM, itemKey, new BlockItem(block, new Item.Properties().useBlockDescriptionPrefix().setId(itemKey)));
		return block;
	}
}
