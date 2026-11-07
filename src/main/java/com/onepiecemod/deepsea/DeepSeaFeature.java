package com.onepiecemod.deepsea;

import java.util.function.Function;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.levelgen.structure.StructureType;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceType;
import net.minecraft.world.level.material.MapColor;

import net.fabricmc.fabric.api.event.Event;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipFeature;
import com.onepiecemod.ship.ShipItem;

/**
 * Submarines and the deep sea: the Ballast Tank that turns a sealed ship into a submarine, the Polar Tang, Sabaody's
 * ship coating, the water pressure of the deep, and the trenches that cut down into the dark under the Grand Line.
 * OnePieceMod calls initialize() after the ships and ship combat.
 *
 * The diving itself is ShipDive (ShipEntity calls it), the coating is ShipCoating, the pressure is DeepPressure and the
 * trenches are DeepTrenchStructure. The dry inside of a diving ship is ship.ShipHold.
 */
public final class DeepSeaFeature {
	private DeepSeaFeature() {
	}

	/** A ship with at least one of these and a sealed hull is a submarine. More tanks (up to 4) dive deeper. */
	public static final Block BALLAST_TANK = registerBlock("ballast_tank", Block::new,
			BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_YELLOW).strength(3.0f, 6.0f).sound(SoundType.COPPER));

	/** Sabaody's ship coating: right-click your ship with it near the Sabaody Archipelago. */
	public static final Item SHIP_COATING = registerItem("ship_coating",
			ShipCoatingItem::new, new Item.Properties().stacksTo(16).rarity(Rarity.UNCOMMON));

	/** Trafalgar Law's yellow submarine, launched like the Going Merry. */
	public static final Item POLAR_TANG = registerItem("polar_tang",
			properties -> new ShipItem("polar_tang", properties), new Item.Properties().stacksTo(1).rarity(Rarity.EPIC));

	public static final StructurePieceType TRENCH_PIECE = Registry.register(BuiltInRegistries.STRUCTURE_PIECE,
			OnePieceMod.id("deep_trench"), (StructurePieceType) (context, tag) -> new DeepTrenchPiece(tag));
	public static final StructureType<DeepTrenchStructure> TRENCH = Registry.register(BuiltInRegistries.STRUCTURE_TYPE,
			OnePieceMod.id("deep_trench"), () -> DeepTrenchStructure.CODEC);

	/** Runs before the ship's own right-click (which opens chests or boards), so coating a ship comes first. */
	private static final Identifier EARLY = OnePieceMod.id("deep_sea");

	public static void initialize() {
		ShipCoating.initialize();
		DeepPressure.initialize();

		UseEntityCallback.EVENT.addPhaseOrdering(EARLY, Event.DEFAULT_PHASE);
		UseEntityCallback.EVENT.register(EARLY, (player, level, hand, entity, hitResult) -> {
			if (hand != InteractionHand.MAIN_HAND || !(entity instanceof ShipEntity ship) || !player.getMainHandItem().is(SHIP_COATING)) {
				return InteractionResult.PASS;
			}
			if (level.isClientSide()) {
				return InteractionResult.SUCCESS;
			}
			ShipCoating.apply(ship, (net.minecraft.server.level.ServerPlayer) player);
			return InteractionResult.SUCCESS;
		});
	}

	// ---- Helpers ----

	private static Block registerBlock(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, OnePieceMod.id(name));
		Block block = Registry.register(BuiltInRegistries.BLOCK, key, factory.apply(properties.setId(key)));
		registerItem(name, itemProperties -> new BlockItem(block, itemProperties), new Item.Properties().useBlockDescriptionPrefix());
		return block;
	}

	private static Item registerItem(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = Registry.register(BuiltInRegistries.ITEM, key, factory.apply(properties.setId(key)));
		ShipFeature.addTabItem(item);
		return item;
	}
}
