package com.onepiecemod.underground;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.levelgen.GenerationStep;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;
import net.minecraft.world.level.material.MapColor;

import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.world.SeastoneEffects;

/**
 * Underground One Piece content: themed cave zones that appear in the caves of every Overworld (normal and
 * Grand Line worlds), plus the blocks they are made of.
 *
 * Cave zones (data/onepiece/worldgen/placed_feature/underground_*.json, made by tools/underground/gen_underground.py):
 * - Seastone Grottos (y 0 to 50): pale blue Sea Prism Stone with glowing crystal clusters. The stone is raw seastone,
 *   so Devil Fruit users who stand on it feel weak.
 * - Sulfur Vents (deep, below y -8): basalt and magma floors with hot, smoking vents.
 * - Sea King fossil beds: giant skeletons buried in the rock, with Fossil Rock that holds old scales.
 * The underground structures (treasure grotto, Void Century ruins, Marine bunker, SMILE factory) are pure data.
 */
public final class UndergroundFeature {
	private static final List<Item> TAB_ITEMS = new ArrayList<>();

	/** Pale blue cave rock found in Seastone Grottos. Unrefined seastone: it saps a Devil Fruit user's strength. */
	public static final Block SEA_PRISM_STONE = block("sea_prism_stone", Block::new,
			BlockBehaviour.Properties.ofFullCopy(Blocks.CALCITE).mapColor(MapColor.COLOR_LIGHT_BLUE).strength(1.8f, 6.0f)
					.requiresCorrectToolForDrops());
	/** Glowing crystals that grow on Sea Prism Stone. Mine them for raw seastone. */
	public static final Block SEA_PRISM_CRYSTAL = block("sea_prism_crystal", p -> new SeaPrismCrystalBlock(7.0f, 3.0f, p),
			BlockBehaviour.Properties.ofFullCopy(Blocks.AMETHYST_CLUSTER).mapColor(MapColor.COLOR_LIGHT_BLUE)
					.lightLevel(state -> 7).sound(SoundType.AMETHYST_CLUSTER));
	/** A hot crack in the deep rock that puffs sulfur smoke. Burns whoever stands on it (sneak to walk safely). */
	public static final Block SULFUR_VENT = block("sulfur_vent", SulfurVentBlock::new,
			BlockBehaviour.Properties.ofFullCopy(Blocks.MAGMA_BLOCK).mapColor(MapColor.COLOR_YELLOW).lightLevel(state -> 5));
	/** Rock with old bones in it, around the giant Sea King skeletons. Drops bones and sometimes a Sea King scale. */
	public static final Block FOSSIL_ROCK = block("fossil_rock", Block::new,
			BlockBehaviour.Properties.ofFullCopy(Blocks.STONE).mapColor(MapColor.TERRACOTTA_WHITE).requiresCorrectToolForDrops());
	/** Carved stone from the Void Century ruins: the same ancient script as the Poneglyphs, but breakable. */
	public static final Block ANCIENT_GLYPH_STONE = block("ancient_glyph_stone", Block::new,
			BlockBehaviour.Properties.ofFullCopy(Blocks.DEEPSLATE_BRICKS).mapColor(MapColor.COLOR_BLACK));

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("underground"));

	/** Cave zones, all placed in every Overworld biome (tag onepiece:has_underground_caves). */
	private static final String[][] FEATURES = {
			{"underground_grotto_floor", "VEGETAL_DECORATION"},
			{"underground_grotto_ceiling", "VEGETAL_DECORATION"},
			{"underground_grotto_pool", "VEGETAL_DECORATION"},
			{"underground_sulfur_floor", "VEGETAL_DECORATION"},
			{"underground_sulfur_ceiling", "VEGETAL_DECORATION"},
			{"underground_sea_king_fossil", "UNDERGROUND_STRUCTURES"},
			{"underground_fossil_rock", "UNDERGROUND_ORES"},
	};

	private UndergroundFeature() {
	}

	public static void initialize() {
		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(SEA_PRISM_CRYSTAL))
				.title(Component.literal("One Piece: Underground"))
				.displayItems((params, output) -> TAB_ITEMS.forEach(output::accept))
				.build());

		TagKey<Biome> caves = TagKey.create(Registries.BIOME, OnePieceMod.id("has_underground_caves"));
		for (String[] f : FEATURES) {
			ResourceKey<PlacedFeature> key = ResourceKey.create(Registries.PLACED_FEATURE, OnePieceMod.id(f[0]));
			BiomeModifications.addFeature(BiomeSelectors.tag(caves), GenerationStep.Decoration.valueOf(f[1]), key);
		}

		// Once a second: Devil Fruit users standing on Sea Prism Stone (or on its crystals) feel weak.
		ServerTickEvents.END_LEVEL_TICK.register(level -> {
			if (level.getGameTime() % 20 != 7) {
				return;
			}
			for (ServerPlayer player : level.players()) {
				if (!SeastoneEffects.isFruitUser(player)) {
					continue;
				}
				Block below = level.getBlockState(player.blockPosition().below()).getBlock();
				if (below == SEA_PRISM_STONE || level.getBlockState(player.blockPosition()).is(SEA_PRISM_CRYSTAL)) {
					player.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 40, 0, false, false, true));
					player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 0, false, false, true));
				}
			}
		});
	}

	private static Block block(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, OnePieceMod.id(name));
		Block block = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.BLOCK, key, block);
		ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = new BlockItem(block, new Item.Properties().setId(itemKey).useBlockDescriptionPrefix());
		Registry.register(BuiltInRegistries.ITEM, itemKey, item);
		TAB_ITEMS.add(item);
		return block;
	}
}
