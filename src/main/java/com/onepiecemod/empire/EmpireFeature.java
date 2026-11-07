package com.onepiecemod.empire;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;

import com.onepiecemod.OnePieceMod;

/**
 * Late-game titles (Emperor, Pirate King, King of the World) and pirate kingdoms.
 * OnePieceMod calls initialize() once at startup.
 *
 *  - Title, EmpireData, EmpireRanks: the titles, what they give, and how to earn them (/empire).
 *  - KingdomFlagBlock + KingdomFlagBlockEntity: plant a flag to found a kingdom; it collects taxes.
 *  - PirateGuardEntity: guards that move into your kingdom and defend it, like iron golems.
 *  - EmpireLoot: more loot for title holders.
 *  - BusterCall: the Navy's answer to an Emperor. Hunts and raids also come more often (see the bounty package).
 */
public class EmpireFeature {
	public static final ResourceKey<Block> KINGDOM_FLAG_KEY = ResourceKey.create(Registries.BLOCK, OnePieceMod.id("kingdom_flag"));
	public static final Block KINGDOM_FLAG = Registry.register(BuiltInRegistries.BLOCK, KINGDOM_FLAG_KEY,
			new KingdomFlagBlock(BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(5.0f, 1200.0f)
					.sound(SoundType.WOOD).noOcclusion().setId(KINGDOM_FLAG_KEY)));

	public static final ResourceKey<Item> KINGDOM_FLAG_ITEM_KEY = ResourceKey.create(Registries.ITEM, OnePieceMod.id("kingdom_flag"));
	public static final Item KINGDOM_FLAG_ITEM = Registry.register(BuiltInRegistries.ITEM, KINGDOM_FLAG_ITEM_KEY,
			new BlockItem(KINGDOM_FLAG, new Item.Properties().stacksTo(1).rarity(Rarity.EPIC)
					.useBlockDescriptionPrefix().setId(KINGDOM_FLAG_ITEM_KEY)));

	public static final BlockEntityType<KingdomFlagBlockEntity> KINGDOM_FLAG_ENTITY = Registry.register(
			BuiltInRegistries.BLOCK_ENTITY_TYPE,
			OnePieceMod.id("kingdom_flag"),
			FabricBlockEntityTypeBuilder.create(KingdomFlagBlockEntity::new, KINGDOM_FLAG).build()
	);

	public static final ResourceKey<EntityType<?>> PIRATE_GUARD_KEY = ResourceKey.create(Registries.ENTITY_TYPE, OnePieceMod.id("pirate_guard"));
	public static final EntityType<PirateGuardEntity> PIRATE_GUARD = Registry.register(
			BuiltInRegistries.ENTITY_TYPE,
			PIRATE_GUARD_KEY,
			EntityType.Builder.of(PirateGuardEntity::new, MobCategory.MISC)
					.sized(0.6f, 1.8f) // Same size as a player.
					.eyeHeight(1.62f)
					.clientTrackingRange(10)
					.build(PIRATE_GUARD_KEY)
	);

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("empire")
	);

	public static void initialize() {
		EmpireData.initialize();
		FabricDefaultAttributeRegistry.register(PIRATE_GUARD, PirateGuardEntity.createAttributes());
		EmpireRanks.initialize();
		EmpireLoot.initialize();
		BusterCall.initialize();
		EmpireCommands.initialize();

		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(KINGDOM_FLAG_ITEM))
				.title(Component.literal("One Piece: Empire"))
				.displayItems((params, output) -> output.accept(KINGDOM_FLAG_ITEM))
				.build());
	}
}
