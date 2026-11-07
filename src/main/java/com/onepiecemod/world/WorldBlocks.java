package com.onepiecemod.world;

import java.util.function.Function;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.util.valueproviders.UniformInt;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.ToolMaterial;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.DropExperienceBlock;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;

import com.onepiecemod.OnePieceMod;

/**
 * The new blocks and materials found around the world:
 * Seastone (Kairoseki), the wood of the Treasure Tree Adam, and Island Cloud from Skypiea.
 */
public class WorldBlocks {
	// ---- Seastone: the sea turned to stone. Devil Fruit users hate touching it. ----

	public static final Block SEASTONE_ORE = registerBlock("seastone_ore",
			properties -> new DropExperienceBlock(UniformInt.of(2, 5), properties),
			BlockBehaviour.Properties.ofFullCopy(Blocks.DIAMOND_ORE).mapColor(MapColor.WATER));

	public static final Block DEEPSLATE_SEASTONE_ORE = registerBlock("deepslate_seastone_ore",
			properties -> new DropExperienceBlock(UniformInt.of(2, 5), properties),
			BlockBehaviour.Properties.ofFullCopy(Blocks.DEEPSLATE_DIAMOND_ORE).mapColor(MapColor.WATER));

	public static final Block SEASTONE_BLOCK = registerBlock("seastone_block", Block::new,
			BlockBehaviour.Properties.ofFullCopy(Blocks.IRON_BLOCK).mapColor(MapColor.WATER).strength(6.0f, 12.0f));

	// ---- Adam wood: the toughest wood in the world (the Thousand Sunny is built from it). ----

	public static final Block ADAM_LOG = registerBlock("adam_log", RotatedPillarBlock::new,
			BlockBehaviour.Properties.ofFullCopy(Blocks.OAK_LOG).mapColor(MapColor.TERRACOTTA_BROWN)
					.strength(6.0f, 9.0f).ignitedByLava());

	public static final Block ADAM_PLANKS = registerBlock("adam_planks", Block::new,
			BlockBehaviour.Properties.ofFullCopy(Blocks.OAK_PLANKS).mapColor(MapColor.TERRACOTTA_BROWN)
					.strength(4.0f, 9.0f));

	// ---- Island Cloud: the soft white ground of the sky islands. ----

	public static final Block ISLAND_CLOUD = registerBlock("island_cloud", Block::new,
			BlockBehaviour.Properties.of().mapColor(MapColor.SNOW).strength(0.4f).sound(SoundType.WOOL));

	/** Sea Cloud: the milky White-White Sea round the sky islands. Solid and opaque (it used to be white stained
	 * glass, which you could see straight through to the ocean far below), a little slow to wade across. */
	public static final Block SEA_CLOUD = registerBlock("sea_cloud", Block::new,
			BlockBehaviour.Properties.of().mapColor(MapColor.SNOW).strength(0.4f).sound(SoundType.WOOL).speedFactor(0.8f));

	// ---- Items ----

	public static final Item RAW_SEASTONE = registerItem("raw_seastone", Item::new, new Item.Properties());
	public static final Item SEASTONE_INGOT = registerItem("seastone_ingot", Item::new, new Item.Properties());

	/** Smoker's weapon. Works like an iron sword, and drains the power of Devil Fruit users it hits. */
	public static final Item SEASTONE_JITTE = registerItem("seastone_jitte", Item::new,
			new Item.Properties().sword(ToolMaterial.IRON, 3.0f, -2.4f).rarity(Rarity.UNCOMMON));

	/** Right-click a Devil Fruit user to lock them down for 10 seconds. Used up after one go. */
	public static final Item SEASTONE_CUFFS = registerItem("seastone_cuffs", SeastoneCuffsItem::new,
			new Item.Properties().stacksTo(16).rarity(Rarity.UNCOMMON));

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("world")
	);

	public static void initialize() {
		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(SEASTONE_ORE))
				.title(Component.literal("One Piece: World"))
				.displayItems((params, output) -> {
					output.accept(SEASTONE_ORE);
					output.accept(DEEPSLATE_SEASTONE_ORE);
					output.accept(RAW_SEASTONE);
					output.accept(SEASTONE_INGOT);
					output.accept(SEASTONE_BLOCK);
					output.accept(SEASTONE_JITTE);
					output.accept(SEASTONE_CUFFS);
					output.accept(ADAM_LOG);
					output.accept(ADAM_PLANKS);
					output.accept(ISLAND_CLOUD);
					output.accept(SEA_CLOUD);
				})
				.build());
	}

	/** Registers a block and the item you hold to place it. */
	private static Block registerBlock(String name, Function<BlockBehaviour.Properties, Block> blockFactory, BlockBehaviour.Properties properties) {
		ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, OnePieceMod.id(name));
		Block block = blockFactory.apply(properties.setId(blockKey));
		Registry.register(BuiltInRegistries.BLOCK, blockKey, block);

		registerItem(name, itemProperties -> new BlockItem(block, itemProperties), new Item.Properties().useBlockDescriptionPrefix());
		return block;
	}

	private static Item registerItem(String name, Function<Item.Properties, Item> itemFactory, Item.Properties properties) {
		ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = itemFactory.apply(properties.setId(itemKey));
		Registry.register(BuiltInRegistries.ITEM, itemKey, item);
		return item;
	}
}
