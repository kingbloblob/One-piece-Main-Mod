package com.onepiecemod.deco;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.vehicle.boat.Boat;
import net.minecraft.world.entity.vehicle.boat.ChestBoat;
import net.minecraft.world.item.BoatItem;
import net.minecraft.world.item.HangingSignItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.StandingAndWallBlockItem;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.CeilingHangingSignBlock;
import net.minecraft.world.level.block.StandingSignBlock;
import net.minecraft.world.level.block.WallHangingSignBlock;
import net.minecraft.world.level.block.WallSignBlock;
import net.minecraft.world.level.block.entity.BlockEntityTypes;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.properties.BlockSetType;
import net.minecraft.world.level.block.state.properties.NoteBlockInstrument;
import net.minecraft.world.level.block.state.properties.WoodType;
import net.minecraft.world.level.material.MapColor;

import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.object.builder.v1.block.type.WoodTypeBuilder;
import net.fabricmc.fabric.api.registry.FlammableBlockRegistry;

import com.onepiecemod.OnePieceMod;

/**
 * Signs, hanging signs, boats and chest boats for the island woods: Sakura, Yarukiman Mangrove, Palm, Gloom and Adam.
 * Their models, textures, recipes and loot are made by tools/deco/gen_signs_boats.py. The boat renderers are in
 * WoodExtrasClient. OnePieceMod calls initialize() once, after DecoFeature (it adds to the Building tab).
 */
public final class WoodExtras {
	/** One wood's set: its sign wood type, the four sign blocks and the two boats. */
	public record Wood(String name, WoodType type, Block sign, Block wallSign, Block hangingSign, Block wallHangingSign,
			EntityType<Boat> boat, EntityType<ChestBoat> chestBoat, Item boatItem, Item chestBoatItem, Item signItem,
			Item hangingSignItem) {
	}

	public static final List<Wood> ALL = new ArrayList<>();

	public static final Wood SAKURA = wood("sakura", BlockSetType.CHERRY, MapColor.COLOR_PINK, MapColor.COLOR_PINK);
	public static final Wood YARUKIMAN = wood("yarukiman", BlockSetType.MANGROVE, MapColor.COLOR_RED, MapColor.COLOR_RED);
	public static final Wood PALM = wood("palm", BlockSetType.JUNGLE, MapColor.SAND, MapColor.SAND);
	public static final Wood GLOOM = wood("gloom", BlockSetType.PALE_OAK, MapColor.COLOR_GRAY, MapColor.COLOR_GRAY);
	public static final Wood ADAM = wood("adam", BlockSetType.OAK, MapColor.COLOR_ORANGE, MapColor.COLOR_ORANGE);

	private WoodExtras() {
	}

	private static Wood wood(String name, BlockSetType setType, MapColor color, MapColor hangingColor) {
		WoodType type = WoodTypeBuilder.copyOf(WoodType.OAK).register(OnePieceMod.id(name), setType);

		Block sign = block(name + "_sign", p -> new StandingSignBlock(type, p), signProperties(color));
		Block wallSign = block(name + "_wall_sign", p -> new WallSignBlock(type, p), wallOf(sign, color));
		Block hanging = block(name + "_hanging_sign", p -> new CeilingHangingSignBlock(type, p), signProperties(hangingColor));
		Block wallHanging = block(name + "_wall_hanging_sign", p -> new WallHangingSignBlock(type, p), wallOf(hanging, hangingColor));
		BlockEntityTypes.SIGN.addValidBlock(sign);
		BlockEntityTypes.SIGN.addValidBlock(wallSign);
		BlockEntityTypes.HANGING_SIGN.addValidBlock(hanging);
		BlockEntityTypes.HANGING_SIGN.addValidBlock(wallHanging);
		for (Block block : List.of(sign, wallSign, hanging, wallHanging)) {
			FlammableBlockRegistry.getDefaultInstance().add(block, 5, 20);
		}

		Item signItem = item(name + "_sign", p -> new StandingAndWallBlockItem(sign, wallSign, Direction.DOWN, p),
				new Item.Properties().stacksTo(16).signText().useBlockDescriptionPrefix());
		Item hangingItem = item(name + "_hanging_sign", p -> new HangingSignItem(hanging, wallHanging, p),
				new Item.Properties().stacksTo(16).signText().useBlockDescriptionPrefix());

		// The boat items are made after their entity types, which need to know which item they drop.
		Item[] items = new Item[2];
		EntityType<Boat> boat = entity(name + "_boat", EntityType.Builder.<Boat>of(
				(entityType, level) -> new Boat(entityType, level, () -> items[0]), MobCategory.MISC));
		EntityType<ChestBoat> chestBoat = entity(name + "_chest_boat", EntityType.Builder.<ChestBoat>of(
				(entityType, level) -> new ChestBoat(entityType, level, () -> items[1]), MobCategory.MISC));
		items[0] = item(name + "_boat", p -> new BoatItem(boat, p), new Item.Properties().stacksTo(1));
		items[1] = item(name + "_chest_boat", p -> new BoatItem(chestBoat, p), new Item.Properties().stacksTo(1));

		Wood wood = new Wood(name, type, sign, wallSign, hanging, wallHanging, boat, chestBoat, items[0], items[1], signItem,
				hangingItem);
		ALL.add(wood);
		return wood;
	}

	private static BlockBehaviour.Properties signProperties(MapColor color) {
		return BlockBehaviour.Properties.of().mapColor(color).forceSolidOn().instrument(NoteBlockInstrument.BASS)
				.noCollision().strength(1.0f).ignitedByLava();
	}

	/** A wall sign drops and is named like its standing sign. */
	private static BlockBehaviour.Properties wallOf(Block standing, MapColor color) {
		return signProperties(color).overrideLootTable(standing.getLootTable()).overrideDescription(standing.getDescriptionId());
	}

	private static Block block(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, OnePieceMod.id(name));
		return Registry.register(BuiltInRegistries.BLOCK, key, factory.apply(properties.setId(key)));
	}

	private static Item item(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		return Registry.register(BuiltInRegistries.ITEM, key, factory.apply(properties.setId(key)));
	}

	private static <T extends net.minecraft.world.entity.Entity> EntityType<T> entity(String name, EntityType.Builder<T> builder) {
		ResourceKey<EntityType<?>> key = ResourceKey.create(Registries.ENTITY_TYPE, OnePieceMod.id(name));
		return Registry.register(BuiltInRegistries.ENTITY_TYPE, key,
				builder.noLootTable().sized(1.375f, 0.5625f).eyeHeight(0.5625f).clientTrackingRange(10).build(key));
	}

	public static void initialize() {
		CreativeModeTabEvents.modifyOutputEvent(DecoFeature.TAB_KEY).register(output -> {
			for (Wood wood : ALL) {
				output.accept(wood.signItem());
				output.accept(wood.hangingSignItem());
				output.accept(wood.boatItem());
				output.accept(wood.chestBoatItem());
			}
		});
	}
}
