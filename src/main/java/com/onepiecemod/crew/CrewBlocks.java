package com.onepiecemod.crew;

import java.util.function.Function;

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

import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.item.ModItems;

/**
 * The Recruitment Board block and the Tavern Blueprint item.
 */
public class CrewBlocks {
	private static final ResourceKey<Block> BOARD_KEY = ResourceKey.create(Registries.BLOCK, OnePieceMod.id("recruitment_board"));

	public static final Block RECRUITMENT_BOARD = Registry.register(BuiltInRegistries.BLOCK, BOARD_KEY,
			new RecruitmentBoardBlock(BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(2.5f)
					.sound(SoundType.WOOD).ignitedByLava().setId(BOARD_KEY)));

	public static final Item RECRUITMENT_BOARD_ITEM = registerItem("recruitment_board",
			properties -> new BlockItem(RECRUITMENT_BOARD, properties), new Item.Properties().useBlockDescriptionPrefix());

	public static final Item TAVERN_BLUEPRINT = registerItem("tavern_blueprint", TavernBlueprintItem::new,
			new Item.Properties().stacksTo(1));

	public static void initialize() {
		CreativeModeTabEvents.modifyOutputEvent(ModItems.ONE_PIECE_TAB_KEY).register(output -> {
			output.accept(TAVERN_BLUEPRINT);
			output.accept(RECRUITMENT_BOARD_ITEM);
		});
	}

	private static Item registerItem(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		return item;
	}
}
