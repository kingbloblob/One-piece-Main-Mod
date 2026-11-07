package com.onepiecemod.farm;

import java.util.EnumMap;
import java.util.Map;
import java.util.function.Function;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;

import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;

import com.onepiecemod.OnePieceMod;

/** The crop blocks, the Seed Vault, sprinklers, the Ranch Trough and the Straw Hat Scarecrow. */
public final class FarmBlocks {
	public static final Map<IslandCrop, IslandCropBlock> CROPS = new EnumMap<>(IslandCrop.class);

	static {
		for (IslandCrop crop : IslandCrop.values()) {
			CROPS.put(crop, (IslandCropBlock) register(crop.id + "_crop", p -> new IslandCropBlock(p, crop),
					BlockBehaviour.Properties.of().mapColor(MapColor.PLANT).noCollision().randomTicks().instabreak()
							.sound(SoundType.CROP).pushReaction(PushReaction.POPPED))); // Not a copy of wheat: its map colour reads wheat's 8-stage age.
		}
	}

	public static final Block SEED_VAULT = register("seed_vault", SeedVaultBlock::new,
			BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(2.5f).sound(SoundType.WOOD));

	/** Waters farmland 3 blocks around it and gives the crops there extra growth. Needs water next to it. */
	public static final Block SPRINKLER = register("sprinkler", p -> new SprinklerBlock(p, 3, true),
			BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_ORANGE).strength(1.5f).sound(SoundType.COPPER).noOcclusion());

	/** A Skypiea sprinkler: a dial shell stores the water, so it needs none nearby, and it reaches 5 blocks. */
	public static final Block DIAL_SPRINKLER = register("dial_sprinkler", p -> new SprinklerBlock(p, 5, false),
			BlockBehaviour.Properties.of().mapColor(MapColor.SAND).strength(1.5f).sound(SoundType.CALCITE).noOcclusion());

	public static final Block RANCH_TROUGH = register("ranch_trough", RanchTroughBlock::new,
			BlockBehaviour.Properties.of().mapColor(MapColor.WOOD).strength(2.0f).sound(SoundType.WOOD).noOcclusion());

	public static final Block SCARECROW = register("straw_hat_scarecrow", ScarecrowBlock::new,
			BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_YELLOW).strength(1.0f).sound(SoundType.GRASS).noOcclusion());

	public static final BlockEntityType<SprinklerBlockEntity> SPRINKLER_ENTITY = Registry.register(
			BuiltInRegistries.BLOCK_ENTITY_TYPE, OnePieceMod.id("sprinkler"),
			FabricBlockEntityTypeBuilder.create(SprinklerBlockEntity::new, SPRINKLER, DIAL_SPRINKLER).build());

	public static final BlockEntityType<RanchTroughBlockEntity> TROUGH_ENTITY = Registry.register(
			BuiltInRegistries.BLOCK_ENTITY_TYPE, OnePieceMod.id("ranch_trough"),
			FabricBlockEntityTypeBuilder.create(RanchTroughBlockEntity::new, RANCH_TROUGH).build());

	private FarmBlocks() {
	}

	public static IslandCropBlock crop(IslandCrop crop) {
		return CROPS.get(crop);
	}

	private static Block register(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, OnePieceMod.id(name));
		return Registry.register(BuiltInRegistries.BLOCK, key, factory.apply(properties.setId(key)));
	}
}
