package com.onepiecemod.furniture;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntityType;

import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;

import com.onepiecemod.OnePieceMod;

/**
 * Furniture and props for builds: tables, chairs, shelves, rugs, curtains, crates, ship and kitchen props.
 * OnePieceMod calls initialize() once. The blocks themselves are listed in FurnitureBlocks
 * (made by tools/furniture/gen_furniture.py, which also makes their models and recipes).
 */
public class Furniture {
	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("furniture"));

	private static final ResourceKey<EntityType<?>> SEAT_KEY = ResourceKey.create(Registries.ENTITY_TYPE, OnePieceMod.id("seat"));

	public static final EntityType<SeatEntity> SEAT = Registry.register(BuiltInRegistries.ENTITY_TYPE, SEAT_KEY,
			EntityType.Builder.<SeatEntity>of(SeatEntity::new, MobCategory.MISC)
					.sized(0.001f, 0.001f)
					.noSummon() // Not noSave(): a player can only ride an entity type that can be saved; the seat removes itself instead.
					.clientTrackingRange(10)
					.build(SEAT_KEY));

	/** The inventory behind every storage furniture block (cupboards, counters, nightstands...). Loading this class registers the blocks first. */
	public static final BlockEntityType<FurnitureStorageBlockEntity> STORAGE = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE,
			OnePieceMod.id("furniture_storage"),
			FabricBlockEntityTypeBuilder.create(FurnitureStorageBlockEntity::new, FurnitureBlocks.STORAGE.toArray(new Block[0])).build());

	public static void initialize() {
		FurnitureBlocks.initialize();

		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(FurnitureBlocks.OAK_CHAIR))
				.title(Component.translatable("itemGroup.onepiece.furniture"))
				.displayItems((params, output) -> {
					for (Block block : FurnitureBlocks.ALL) {
						output.accept(block);
					}
				})
				.build());
	}
}
