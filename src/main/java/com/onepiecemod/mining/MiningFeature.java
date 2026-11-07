package com.onepiecemod.mining;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.tags.TagKey;
import net.minecraft.util.valueproviders.UniformInt;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.ToolMaterial;
import net.minecraft.world.item.component.Consumables;
import net.minecraft.world.item.consume_effects.ApplyStatusEffectsConsumeEffect;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.DropExperienceBlock;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.levelgen.GenerationStep;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;
import net.minecraft.world.level.material.MapColor;

import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.world.SeastoneEffects;

/**
 * Mining in the Grand Line.
 *
 * - Three tool tiers, each better than the last: Adam Wood (iron level, very tough), Seastone (diamond level,
 *   drains Devil Fruit users it hits) and refined Sea Prism (above netherite). Sea Prism Veins deep underground
 *   need a Seastone pickaxe; Abyss Stone at the bottom of the deep mines needs Sea Prism.
 * - Island ores: every big island has a material found nowhere else (Alabasta amber, Zou electro crystal...).
 *   Wano, Kuri and Impel Down have extra-rich seastone veins.
 * - The Mining Drill: fuel it, fit a drill bit and it bores a 3x3 tunnel, dropping what it digs into an Ore Cart
 *   (or any chest, barrel or chest minecart) right beside it. Any crewmate set to Work next to a drill becomes
 *   its miner: keeps it fuelled, swaps worn bits and hauls full carts to the chests (see MinerWorkGoal).
 * - Deep mines (Impel Down style seastone quarries) are structure data, made by tools/mining/.
 *
 * Data (models, loot, ore features, tags, recipes) is made by tools/mining/gen_mining.py.
 */
public final class MiningFeature {
	private static final List<Item> TAB_ITEMS = new ArrayList<>();

	// ---------------- Tool tiers ----------------

	public static final TagKey<Block> NEEDS_SEASTONE_TOOL = blockTag("needs_seastone_tool");
	public static final TagKey<Block> NEEDS_SEA_PRISM_TOOL = blockTag("needs_sea_prism_tool");

	public static final ToolMaterial ADAM = new ToolMaterial(blockTag("incorrect_for_adam_tool"), 900, 7.0f, 2.5f, 18,
			itemTag("repairs_adam_tool"));
	public static final ToolMaterial SEASTONE = new ToolMaterial(blockTag("incorrect_for_seastone_tool"), 1900, 8.5f, 3.5f, 12,
			itemTag("repairs_seastone_tool"));
	public static final ToolMaterial SEA_PRISM = new ToolMaterial(blockTag("incorrect_for_sea_prism_tool"), 2800, 10.0f, 4.5f, 16,
			itemTag("repairs_sea_prism_tool"));

	// ---------------- Ores ----------------

	/** Deep in the rock under every island (below y -32): veins of pure sea prism. Needs a Seastone pickaxe. */
	public static final Block SEA_PRISM_VEIN = block("sea_prism_vein", p -> new DropExperienceBlock(UniformInt.of(4, 8), p),
			BlockBehaviour.Properties.ofFullCopy(Blocks.DEEPSLATE_DIAMOND_ORE).mapColor(MapColor.COLOR_LIGHT_BLUE)
					.strength(6.0f, 9.0f).lightLevel(s -> 3));
	/** The black rock at the very bottom of the deep mines. Only Sea Prism tools (or a Sea Prism drill bit) break it. */
	public static final Block ABYSS_STONE = block("abyss_stone", Block::new,
			BlockBehaviour.Properties.ofFullCopy(Blocks.DEEPSLATE).mapColor(MapColor.COLOR_BLACK).strength(8.0f, 1200.0f));
	public static final Block ABYSS_STONE_BRICKS = block("abyss_stone_bricks", Block::new,
			BlockBehaviour.Properties.ofFullCopy(Blocks.DEEPSLATE_BRICKS).mapColor(MapColor.COLOR_BLACK).strength(8.0f, 1200.0f));

	public static final Block DESERT_AMBER_ORE = ore("desert_amber_ore", MapColor.SAND); // Alabasta
	public static final Block SUN_CORAL_ORE = block("sun_coral_ore", p -> new DropExperienceBlock(UniformInt.of(1, 4), p),
			BlockBehaviour.Properties.ofFullCopy(Blocks.IRON_ORE).mapColor(MapColor.COLOR_ORANGE).lightLevel(s -> 9)); // Fishman Island
	public static final Block ROCK_CANDY_ORE = ore("rock_candy_ore", MapColor.COLOR_PINK); // Whole Cake, Cacao
	public static final Block GIANT_IRON_ORE = ore("giant_iron_ore", MapColor.RAW_IRON); // Elbaph, Little Garden
	public static final Block EGGHEAD_ALLOY_ORE = ore("egghead_alloy_ore", MapColor.METAL); // Egghead
	public static final Block GLOOM_CRYSTAL_ORE = block("gloom_crystal_ore", p -> new DropExperienceBlock(UniformInt.of(2, 5), p),
			BlockBehaviour.Properties.ofFullCopy(Blocks.IRON_ORE).mapColor(MapColor.COLOR_PURPLE).lightLevel(s -> 4)); // Thriller Bark, Kuraigana
	public static final Block ELECTRO_CRYSTAL_ORE = block("electro_crystal_ore", p -> new DropExperienceBlock(UniformInt.of(2, 5), p),
			BlockBehaviour.Properties.ofFullCopy(Blocks.IRON_ORE).mapColor(MapColor.COLOR_YELLOW).lightLevel(s -> 6)); // Zou
	public static final Block SNAKE_JADE_ORE = ore("snake_jade_ore", MapColor.EMERALD); // Amazon Lily

	// ---------------- Materials ----------------

	public static final Item SEA_PRISM_SHARD = item("sea_prism_shard", new Item.Properties().rarity(Rarity.UNCOMMON));
	public static final Item SEA_PRISM_INGOT = item("sea_prism_ingot", new Item.Properties().rarity(Rarity.RARE));
	public static final Item DESERT_AMBER = item("desert_amber", new Item.Properties());
	public static final Item SUN_CORAL = item("sun_coral", new Item.Properties());
	/** Sweet as Big Mom's islands. Crunch one for a burst of Haste. */
	public static final Item ROCK_CANDY = item("rock_candy", new Item.Properties()
			.food(new FoodProperties.Builder().nutrition(2).saturationModifier(0.2f).alwaysEdible().build(),
					Consumables.defaultFood().onConsume(new ApplyStatusEffectsConsumeEffect(List.of(
							new MobEffectInstance(MobEffects.HASTE, 1200, 1)))).build()));
	public static final Item RAW_GIANT_IRON = item("raw_giant_iron", new Item.Properties());
	public static final Item GIANT_IRON_INGOT = item("giant_iron_ingot", new Item.Properties());
	public static final Item EGGHEAD_ALLOY = item("egghead_alloy", new Item.Properties().rarity(Rarity.UNCOMMON));
	public static final Item GLOOM_CRYSTAL = register("gloom_crystal", GloomCrystalItem::new, new Item.Properties());
	public static final Item ELECTRO_CRYSTAL = item("electro_crystal", new Item.Properties());
	public static final Item SNAKE_JADE = item("snake_jade", new Item.Properties());

	// ---------------- Tools ----------------

	public static final Item ADAM_PICKAXE = register("adam_pickaxe", Item::new, new Item.Properties().pickaxe(ADAM, 1.0f, -2.8f));
	public static final Item ADAM_AXE = register("adam_axe", Item::new, new Item.Properties().axe(ADAM, 6.0f, -3.1f));
	public static final Item ADAM_SHOVEL = register("adam_shovel", Item::new, new Item.Properties().shovel(ADAM, 1.5f, -3.0f));
	public static final Item SEASTONE_PICKAXE = register("seastone_pickaxe", Item::new,
			new Item.Properties().pickaxe(SEASTONE, 1.0f, -2.8f).rarity(Rarity.UNCOMMON));
	public static final Item SEASTONE_AXE = register("seastone_axe", Item::new,
			new Item.Properties().axe(SEASTONE, 5.0f, -3.0f).rarity(Rarity.UNCOMMON));
	public static final Item SEASTONE_SHOVEL = register("seastone_shovel", Item::new,
			new Item.Properties().shovel(SEASTONE, 1.5f, -3.0f).rarity(Rarity.UNCOMMON));
	public static final Item SEA_PRISM_PICKAXE = register("sea_prism_pickaxe", Item::new,
			new Item.Properties().pickaxe(SEA_PRISM, 1.0f, -2.8f).rarity(Rarity.RARE).fireResistant());
	public static final Item SEA_PRISM_AXE = register("sea_prism_axe", Item::new,
			new Item.Properties().axe(SEA_PRISM, 5.0f, -3.0f).rarity(Rarity.RARE).fireResistant());
	public static final Item SEA_PRISM_SHOVEL = register("sea_prism_shovel", Item::new,
			new Item.Properties().shovel(SEA_PRISM, 1.5f, -3.0f).rarity(Rarity.RARE).fireResistant());

	// ---------------- Drill and cart ----------------

	public static final Item ADAM_DRILL_BIT = item("adam_drill_bit", new Item.Properties().stacksTo(4));
	public static final Item SEASTONE_DRILL_BIT = item("seastone_drill_bit", new Item.Properties().stacksTo(4).rarity(Rarity.UNCOMMON));
	public static final Item SEA_PRISM_DRILL_BIT = item("sea_prism_drill_bit", new Item.Properties().stacksTo(4).rarity(Rarity.RARE));

	public static final Block MINING_DRILL = block("mining_drill", MiningDrillBlock::new,
			BlockBehaviour.Properties.ofFullCopy(Blocks.BLAST_FURNACE).mapColor(MapColor.METAL).noOcclusion());
	public static final Block ORE_CART = block("ore_cart", OreCartBlock::new,
			BlockBehaviour.Properties.ofFullCopy(Blocks.BARREL).mapColor(MapColor.WOOD).noOcclusion());

	public static final BlockEntityType<MiningDrillBlockEntity> DRILL_ENTITY = Registry.register(
			BuiltInRegistries.BLOCK_ENTITY_TYPE, OnePieceMod.id("mining_drill"),
			FabricBlockEntityTypeBuilder.create(MiningDrillBlockEntity::new, MINING_DRILL).build());
	public static final BlockEntityType<OreCartBlockEntity> CART_ENTITY = Registry.register(
			BuiltInRegistries.BLOCK_ENTITY_TYPE, OnePieceMod.id("ore_cart"),
			FabricBlockEntityTypeBuilder.create(OreCartBlockEntity::new, ORE_CART).build());

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("mining"));

	/** Ore features (data/onepiece/worldgen/placed_feature/ore_<name>.json) and their biome tags has_ore_<name>. */
	private static final String[] ORES = {"sea_prism_vein", "desert_amber", "sun_coral", "rock_candy", "giant_iron",
			"egghead_alloy", "gloom_crystal", "electro_crystal", "snake_jade", "rich_seastone"};

	private MiningFeature() {
	}

	public static void initialize() {
		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(SEA_PRISM_PICKAXE))
				.title(Component.literal("One Piece: Mining"))
				.displayItems((params, output) -> TAB_ITEMS.forEach(output::accept))
				.build());

		for (String ore : ORES) {
			TagKey<Biome> biomes = TagKey.create(Registries.BIOME, OnePieceMod.id("has_ore_" + ore));
			ResourceKey<PlacedFeature> feature = ResourceKey.create(Registries.PLACED_FEATURE, OnePieceMod.id("ore_" + ore));
			BiomeModifications.addFeature(BiomeSelectors.tag(biomes), GenerationStep.Decoration.UNDERGROUND_ORES, feature);
		}

		// Seastone and Sea Prism tools are solid sea: a hit drains a Devil Fruit user's power for a moment.
		// (Their Adam wood grips keep the wielder safe.)
		AttackEntityCallback.EVENT.register((player, level, hand, target, hitResult) -> {
			if (!level.isClientSide() && target instanceof LivingEntity living && SeastoneEffects.isFruitUser(living)) {
				ItemStack held = player.getMainHandItem();
				if (held.is(SEA_PRISM_PICKAXE) || held.is(SEA_PRISM_AXE) || held.is(SEA_PRISM_SHOVEL)) {
					SeastoneEffects.drain(living, 80);
				} else if (held.is(SEASTONE_PICKAXE) || held.is(SEASTONE_AXE) || held.is(SEASTONE_SHOVEL)) {
					SeastoneEffects.drain(living, 40);
				}
			}
			return InteractionResult.PASS;
		});

		// Abyss Stone only gives way to Sea Prism.
		PlayerBlockBreakEvents.BEFORE.register((level, player, pos, state, blockEntity) -> {
			if ((state.is(ABYSS_STONE) || state.is(ABYSS_STONE_BRICKS)) && !player.isCreative()
					&& !player.getMainHandItem().is(SEA_PRISM_PICKAXE)) {
				player.sendOverlayMessage(Component.literal("Only a Sea Prism pickaxe can cut Abyss Stone."));
				return false;
			}
			return true;
		});

		OnePieceMod.LOGGER.info("Mining: {} ore kinds, drill and ore cart ready", ORES.length);
	}

	/** Which drill bit tier an item is: 1 Adam, 2 Seastone, 3 Sea Prism, 0 not a bit. */
	public static int bitTier(ItemStack stack) {
		if (stack.is(ADAM_DRILL_BIT)) {
			return 1;
		}
		if (stack.is(SEASTONE_DRILL_BIT)) {
			return 2;
		}
		return stack.is(SEA_PRISM_DRILL_BIT) ? 3 : 0;
	}

	public static Item bitItem(int tier) {
		return switch (tier) {
			case 1 -> ADAM_DRILL_BIT;
			case 2 -> SEASTONE_DRILL_BIT;
			case 3 -> SEA_PRISM_DRILL_BIT;
			default -> null;
		};
	}

	/** The pickaxe a drill bit cuts like (for which blocks it can break and what they drop). */
	public static Item bitPickaxe(int tier) {
		return switch (tier) {
			case 2 -> SEASTONE_PICKAXE;
			case 3 -> SEA_PRISM_PICKAXE;
			default -> ADAM_PICKAXE;
		};
	}

	private static TagKey<Block> blockTag(String name) {
		return TagKey.create(Registries.BLOCK, OnePieceMod.id(name));
	}

	private static TagKey<Item> itemTag(String name) {
		return TagKey.create(Registries.ITEM, OnePieceMod.id(name));
	}

	private static Block ore(String name, MapColor color) {
		return block(name, p -> new DropExperienceBlock(UniformInt.of(1, 4), p),
				BlockBehaviour.Properties.ofFullCopy(Blocks.IRON_ORE).mapColor(color));
	}

	private static Block block(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, OnePieceMod.id(name));
		Block block = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.BLOCK, key, block);
		register(name, p -> new BlockItem(block, p), new Item.Properties().useBlockDescriptionPrefix());
		return block;
	}

	private static Item item(String name, Item.Properties properties) {
		return register(name, Item::new, properties);
	}

	private static Item register(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		TAB_ITEMS.add(item);
		return item;
	}
}
