package com.onepiecemod.ship;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.tags.TagKey;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;

import com.onepiecemod.OnePieceMod;

/**
 * Registers everything for ships: the Ship's Wheel, the ship itself, Jolly Rogers and decorations.
 * OnePieceMod calls initialize() once while the game loads.
 */
public class ShipFeature {
	/** Blocks that never become part of a ship (stone, dirt, sand...). Edit data/onepiece/tags/block/not_ship.json to change it. */
	public static final TagKey<Block> NOT_SHIP = TagKey.create(Registries.BLOCK, OnePieceMod.id("not_ship"));

	/** The painting stored on a Jolly Roger item. */
	public static final DataComponentType<FlagDesign> FLAG_DESIGN = Registry.register(
			BuiltInRegistries.DATA_COMPONENT_TYPE,
			OnePieceMod.id("flag_design"),
			DataComponentType.<FlagDesign>builder()
					.persistent(FlagDesign.CODEC)
					.networkSynchronized(FlagDesign.STREAM_CODEC)
					.build()
	);

	private static final List<Item> TAB_ITEMS = new ArrayList<>();

	// ---- The Ship's Wheel and the ship ----

	public static final Block HELM = registerBlock("ships_wheel", HelmBlock::new,
			BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(2.0f).sound(SoundType.WOOD).noOcclusion());

	public static final ResourceKey<EntityType<?>> SHIP_KEY = ResourceKey.create(Registries.ENTITY_TYPE, OnePieceMod.id("ship"));
	public static final EntityType<ShipEntity> SHIP = Registry.register(
			BuiltInRegistries.ENTITY_TYPE,
			SHIP_KEY,
			EntityType.Builder.<ShipEntity>of(ShipEntity::new, MobCategory.MISC)
					.sized(1.0f, 1.0f) // The real size comes from the blocks, see ShipEntity.getDimensions.
					.fireImmune()
					.clientTrackingRange(16) // Ships are big, so players see them from far away.
					.updateInterval(1)
					.build(SHIP_KEY)
	);

	// ---- Jolly Rogers ----

	public static final Block JOLLY_ROGER = registerBlockOnly("jolly_roger", FlagBlock::new,
			BlockBehaviour.Properties.of().mapColor(MapColor.WOOL).strength(0.5f).sound(SoundType.WOOL).noCollision().noOcclusion());

	public static final Item JOLLY_ROGER_ITEM = registerItem("jolly_roger",
			properties -> new JollyRogerItem(JOLLY_ROGER, properties),
			new Item.Properties().stacksTo(16).useBlockDescriptionPrefix().component(FLAG_DESIGN, FlagDesign.blank()));

	public static final BlockEntityType<FlagBlockEntity> FLAG_BLOCK_ENTITY = Registry.register(
			BuiltInRegistries.BLOCK_ENTITY_TYPE,
			OnePieceMod.id("jolly_roger"),
			FabricBlockEntityTypeBuilder.create(FlagBlockEntity::new, JOLLY_ROGER).build()
	);

	// ---- Decorations ----

	private static BlockBehaviour.Properties wood() {
		return BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(1.5f).sound(SoundType.WOOD).noOcclusion();
	}

	private static BlockBehaviour.Properties metal() {
		return BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(3.0f).sound(SoundType.METAL).noOcclusion();
	}

	public static final Block FIGUREHEAD_MERRY = registerBlock("figurehead_merry",
			properties -> new DecorBlock(properties, Block.box(2, 0, 2, 14, 16, 14)), wood());
	public static final Block FIGUREHEAD_SUNNY = registerBlock("figurehead_sunny",
			properties -> new DecorBlock(properties, Block.box(1, 0, 1, 15, 16, 15)), wood());
	public static final Block FIGUREHEAD_MOBY = registerBlock("figurehead_moby",
			properties -> new DecorBlock(properties, Block.box(2, 2, 0, 14, 14, 16)), wood());
	public static final Block CANNON = registerBlock("cannon",
			CannonBlock::new, metal());
	public static final Block ANCHOR = registerBlock("anchor",
			properties -> new DecorBlock(properties, Block.box(2, 0, 6, 14, 16, 10)), metal());
	public static final Block PORTHOLE = registerBlock("porthole",
			properties -> new DecorBlock(properties), wood());
	public static final Block ROPE_COIL = registerBlock("rope_coil",
			properties -> new DecorBlock(properties, Block.box(2, 0, 2, 14, 4, 14)),
			BlockBehaviour.Properties.of().mapColor(MapColor.WOOL).strength(0.5f).sound(SoundType.WOOL).noOcclusion());

	// Grass and soil that count as part of a ship. Natural grass and dirt never do (see the not_ship tag), so the
	// Thousand Sunny's lawn and the Going Merry's mikan planters are made of these. They are in the minecraft:dirt
	// tag, so trees, flowers and bushes grow on them like on the real thing.
	public static final Block DECK_LAWN = registerBlock("deck_lawn", Block::new,
			BlockBehaviour.Properties.of().mapColor(MapColor.GRASS).strength(0.6f).sound(SoundType.GRASS));
	public static final Block DECK_SOIL = registerBlock("deck_soil", Block::new,
			BlockBehaviour.Properties.of().mapColor(MapColor.DIRT).strength(0.5f).sound(SoundType.GRAVEL));

	/**
	 * Franky's cola-powered engine. A ship carrying one can Coup de Burst (leap through the air) and, with the Thousand
	 * Sunny's lion figurehead at the bow, fire the Gaon Cannon. Both burn Cola Crates from the captain's pack.
	 */
	public static final Block COLA_ENGINE = registerBlock("cola_engine", Block::new, metal());

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("ships")
	);

	public static void initialize() {
		ShipPayloads.initialize();
		ShipInteractions.initialize();
		ShipDecks.initialize();

		// Right-clicking a ship: climb aboard, or (as captain) drop anchor.
		UseEntityCallback.EVENT.register((player, level, hand, entity, hitResult) ->
				entity instanceof ShipEntity ship ? ship.onRightClick(player, hand) : InteractionResult.PASS);

		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(HELM))
				.title(Component.literal("One Piece: Ships"))
				.displayItems((params, output) -> {
					for (Item item : TAB_ITEMS) {
						output.accept(item);
					}
				})
				.build());
	}

	/** Lets other ship classes (ShipModels: the Going Merry and Thousand Sunny items) put their items in the Ships tab. */
	public static void addTabItem(Item item) {
		TAB_ITEMS.add(item);
	}

	// ---- Helpers ----

	/** Registers a block and the item you hold to place it. */
	private static Block registerBlock(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
		Block block = registerBlockOnly(name, factory, properties);
		registerItem(name, itemProperties -> new BlockItem(block, itemProperties), new Item.Properties().useBlockDescriptionPrefix());
		return block;
	}

	private static Block registerBlockOnly(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, OnePieceMod.id(name));
		Block block = factory.apply(properties.setId(key));
		return Registry.register(BuiltInRegistries.BLOCK, key, block);
	}

	private static Item registerItem(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		TAB_ITEMS.add(item);
		return item;
	}
}
