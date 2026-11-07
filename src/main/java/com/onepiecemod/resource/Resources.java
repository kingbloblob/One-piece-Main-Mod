package com.onepiecemod.resource;

import net.minecraft.util.Prediction;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.TagKey;
import net.minecraft.util.valueproviders.UniformInt;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.ToolMaterial;
import net.minecraft.world.item.equipment.ArmorMaterial;
import net.minecraft.world.item.equipment.ArmorType;
import net.minecraft.world.item.equipment.EquipmentAsset;
import net.minecraft.world.item.equipment.EquipmentAssets;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.DropExperienceBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.levelgen.GenerationStep;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;
import net.minecraft.world.level.material.MapColor;

import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;

import com.onepiecemod.OnePieceMod;

/**
 * Things to mine and collect around the world, and what they turn into.
 *
 * Ores: Tamahagane (mountains, Wano), Wapometal (snowy peaks, Drum), Shandora Gold (badlands, jungles, Skypiea),
 * Sulfur (badlands, Punk Hazard, the Nether) and Kokuto black steel (deep underground, rare).
 * Collectables: Dial Shells (shell sand on beaches), Sea Pearls (oyster gravel on the sea floor),
 * Yarukiman Resin (use a glass bottle on a Yarukiman log), creature scales and ink, and Poneglyphs.
 *
 * Most items are made at the crafting stations (see onepiece/station_recipes.json).
 * Worldgen spots are biome tags: data/onepiece/tags/worldgen/biome/has_ore_<name>.json.
 */
public final class Resources {
	private static final List<Item> TAB_ITEMS = new ArrayList<>(); // stacks can't be made before registries are bound

	// ---------------- Ores and collectable blocks ----------------

	public static final Block TAMAHAGANE_ORE = ore("tamahagane_ore", Blocks.IRON_ORE, MapColor.STONE, 1, 3);
	public static final Block DEEPSLATE_TAMAHAGANE_ORE = ore("deepslate_tamahagane_ore", Blocks.DEEPSLATE_IRON_ORE, MapColor.DEEPSLATE, 1, 3);
	public static final Block WAPOMETAL_ORE = ore("wapometal_ore", Blocks.IRON_ORE, MapColor.STONE, 1, 3);
	public static final Block DEEPSLATE_WAPOMETAL_ORE = ore("deepslate_wapometal_ore", Blocks.DEEPSLATE_IRON_ORE, MapColor.DEEPSLATE, 1, 3);
	public static final Block SHANDORA_GOLD_ORE = ore("shandora_gold_ore", Blocks.GOLD_ORE, MapColor.GOLD, 1, 3);
	public static final Block SULFUR_ORE = ore("sulfur_ore", Blocks.COAL_ORE, MapColor.COLOR_YELLOW, 0, 2);
	public static final Block NETHER_SULFUR_ORE = ore("nether_sulfur_ore", Blocks.NETHER_QUARTZ_ORE, MapColor.NETHER, 1, 3);
	public static final Block DEEPSLATE_KOKUTO_ORE = ore("deepslate_kokuto_ore", Blocks.DEEPSLATE_DIAMOND_ORE, MapColor.COLOR_BLACK, 3, 7);

	/** Beach sand with Skypiea Dial shells in it. */
	public static final Block SHELL_SAND = block("shell_sand", Block::new,
			BlockBehaviour.Properties.ofFullCopy(Blocks.SAND).mapColor(MapColor.SAND));
	/** Sea-floor gravel full of oysters. Some hold a Sea Pearl. */
	public static final Block OYSTER_GRAVEL = block("oyster_gravel", Block::new,
			BlockBehaviour.Properties.ofFullCopy(Blocks.GRAVEL));
	/** An unbreakable stone block with ancient writing. Road Poneglyphs lead to Laugh Tale. */
	public static final Block PONEGLYPH = block("poneglyph", PoneglyphBlock::new,
			BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(-1.0f, 3600000.0f)
					.sound(SoundType.DEEPSLATE_BRICKS).noLootTable());

	// ---------------- Raw materials ----------------

	public static final Item RAW_TAMAHAGANE = item("raw_tamahagane");
	public static final Item TAMAHAGANE_INGOT = item("tamahagane_ingot");
	public static final Item RAW_WAPOMETAL = item("raw_wapometal");
	public static final Item WAPOMETAL_INGOT = item("wapometal_ingot");
	public static final Item RAW_SHANDORA_GOLD = item("raw_shandora_gold");
	public static final Item SHANDORA_GOLD_INGOT = item("shandora_gold_ingot");
	public static final Item SULFUR = item("sulfur");
	public static final Item RAW_KOKUTO = item("raw_kokuto", Rarity.UNCOMMON);
	public static final Item KOKUTO_INGOT = item("kokuto_ingot", Rarity.UNCOMMON);
	public static final Item DIAL_SHELL = item("dial_shell");
	public static final Item SEA_PEARL = item("sea_pearl", Rarity.UNCOMMON);
	public static final Item YARUKIMAN_RESIN = item("yarukiman_resin");
	public static final Item SEA_KING_SCALE = item("sea_king_scale", Rarity.UNCOMMON);
	public static final Item KRAKEN_INK = item("kraken_ink");
	public static final Item DRAGON_SCALE = item("dragon_scale", Rarity.RARE);

	// ---------------- What they make ----------------

	public static final Item FLASH_DIAL = register("flash_dial", p -> new DialItem(DialItem.Kind.FLASH, p),
			new Item.Properties().stacksTo(1).durability(32).rarity(Rarity.UNCOMMON));
	public static final Item BREATH_DIAL = register("breath_dial", p -> new DialItem(DialItem.Kind.BREATH, p),
			new Item.Properties().stacksTo(1).durability(32).rarity(Rarity.UNCOMMON));
	public static final Item BUBBLE_COATING = register("bubble_coating", BubbleCoatingItem::new,
			new Item.Properties().stacksTo(16));

	public static final Item TAMAHAGANE_KATANA = register("tamahagane_katana", Item::new,
			new Item.Properties().sword(ToolMaterial.IRON, 4.0f, -2.2f).rarity(Rarity.UNCOMMON));
	public static final Item KOKUTO_BLADE = register("kokuto_blade", Item::new,
			new Item.Properties().sword(ToolMaterial.NETHERITE, 4.5f, -2.3f).rarity(Rarity.EPIC).fireResistant());

	// Armor: tougher sets come later in the game.
	// Defense is helmet, chestplate, leggings, boots (iron is 2, 6, 5, 2 and diamond 3, 8, 6, 3).
	public static final ArmorMaterial WAPOMETAL = armor("wapometal", 22, new int[] {2, 7, 5, 2}, 10, 1.0f, 0.05f);
	public static final ArmorMaterial SEA_KING = armor("sea_king_scale", 30, new int[] {3, 8, 6, 3}, 12, 2.0f, 0.05f);
	public static final ArmorMaterial DRAGON = armor("dragon_scale", 40, new int[] {3, 8, 6, 3}, 15, 3.5f, 0.15f);
	public static final ArmorMaterial DIVING = armor("diving", 15, new int[] {2, 5, 4, 1}, 12, 0.0f, 0.0f);

	public static final Item[] WAPOMETAL_ARMOR = armorSet("wapometal", WAPOMETAL, Rarity.COMMON);
	public static final Item[] SEA_KING_ARMOR = armorSet("sea_king_scale", SEA_KING, Rarity.UNCOMMON);
	public static final Item[] DRAGON_ARMOR = armorSet("dragon_scale", DRAGON, Rarity.RARE);
	public static final Item DIVING_HELMET = register("diving_helmet", Item::new,
			new Item.Properties().humanoidArmor(DIVING, ArmorType.HELMET));

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("resources"));

	private Resources() {
	}

	public static void initialize() {
		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(TAMAHAGANE_INGOT))
				.title(Component.literal("One Piece: Resources"))
				.displayItems((params, output) -> TAB_ITEMS.forEach(output::accept))
				.build());

		// Ores and collectables, by biome tag. Overworld and Nether use the same tags.
		for (String ore : List.of("tamahagane", "wapometal", "shandora_gold", "sulfur", "nether_sulfur", "kokuto",
				"shell_sand", "oyster_gravel")) {
			TagKey<Biome> biomes = TagKey.create(Registries.BIOME, OnePieceMod.id("has_ore_" + ore));
			ResourceKey<PlacedFeature> feature = ResourceKey.create(Registries.PLACED_FEATURE, OnePieceMod.id("ore_" + ore));
			BiomeModifications.addFeature(BiomeSelectors.tag(biomes), GenerationStep.Decoration.UNDERGROUND_ORES, feature);
		}

		// Tap a Yarukiman log with a glass bottle to collect resin.
		UseBlockCallback.EVENT.register((player, level, hand, hitResult) -> {
			ItemStack stack = player.getItemInHand(hand);
			if (!stack.is(Items.GLASS_BOTTLE)) {
				return InteractionResult.PASS;
			}
			Block block = level.getBlockState(hitResult.getBlockPos()).getBlock();
			String id = BuiltInRegistries.BLOCK.getKey(block).getPath();
			if (!id.equals("yarukiman_log") && !id.equals("yarukiman_wood")) {
				return InteractionResult.PASS;
			}
			if (!level.isClientSide()) {
				if (!player.isCreative()) {
					stack.shrink(1);
				}
				ItemStack resin = new ItemStack(YARUKIMAN_RESIN);
				if (!player.getInventory().add(resin)) {
					player.drop(resin, false, Prediction.SERVER_ONLY);
				}
				level.playSound(null, hitResult.getBlockPos(), SoundEvents.BOTTLE_FILL, net.minecraft.sounds.SoundSource.BLOCKS, 1.0f, 1.0f);
			}
			return InteractionResult.SUCCESS;
		});

		// Armor bonuses, checked once a second.
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 20 != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				applyArmorBonuses(player);
			}
		});
	}

	/** Diving Helmet: breathe underwater. Full Sea King set: swim fast. Full Dragon set: immune to fire. */
	private static void applyArmorBonuses(Player player) {
		if (player.getItemBySlot(EquipmentSlot.HEAD).is(DIVING_HELMET) && player.isUnderWater()) {
			player.addEffect(new MobEffectInstance(MobEffects.WATER_BREATHING, 60, 0, true, false, true));
		}
		if (fullSet(player, SEA_KING_ARMOR) && player.isInWater()) {
			player.addEffect(new MobEffectInstance(MobEffects.DOLPHINS_GRACE, 60, 0, true, false, true));
		}
		if (fullSet(player, DRAGON_ARMOR)) {
			player.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 60, 0, true, false, true));
		}
	}

	private static boolean fullSet(Player player, Item[] set) {
		return player.getItemBySlot(EquipmentSlot.HEAD).is(set[0]) && player.getItemBySlot(EquipmentSlot.CHEST).is(set[1])
				&& player.getItemBySlot(EquipmentSlot.LEGS).is(set[2]) && player.getItemBySlot(EquipmentSlot.FEET).is(set[3]);
	}

	// ---------------- Registration helpers ----------------

	private static ArmorMaterial armor(String name, int durability, int[] defense, int enchantability, float toughness,
			float knockbackResistance) {
		ResourceKey<EquipmentAsset> asset = ResourceKey.create(EquipmentAssets.ROOT_ID, OnePieceMod.id(name));
		TagKey<Item> repair = TagKey.create(Registries.ITEM, OnePieceMod.id("repairs_" + name + "_armor"));
		return new ArmorMaterial(durability,
				Map.of(ArmorType.HELMET, defense[0], ArmorType.CHESTPLATE, defense[1], ArmorType.LEGGINGS, defense[2],
						ArmorType.BOOTS, defense[3], ArmorType.BODY, defense[1]),
				enchantability, SoundEvents.ARMOR_EQUIP_IRON, toughness, knockbackResistance, repair, asset);
	}

	private static Item[] armorSet(String name, ArmorMaterial material, Rarity rarity) {
		return new Item[] {
				register(name + "_helmet", Item::new, new Item.Properties().humanoidArmor(material, ArmorType.HELMET).rarity(rarity)),
				register(name + "_chestplate", Item::new, new Item.Properties().humanoidArmor(material, ArmorType.CHESTPLATE).rarity(rarity)),
				register(name + "_leggings", Item::new, new Item.Properties().humanoidArmor(material, ArmorType.LEGGINGS).rarity(rarity)),
				register(name + "_boots", Item::new, new Item.Properties().humanoidArmor(material, ArmorType.BOOTS).rarity(rarity))
		};
	}

	private static Block ore(String name, Block copy, MapColor color, int minXp, int maxXp) {
		return block(name, p -> new DropExperienceBlock(UniformInt.of(minXp, maxXp), p),
				BlockBehaviour.Properties.ofFullCopy(copy).mapColor(color));
	}

	private static Block block(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, OnePieceMod.id(name));
		Block block = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.BLOCK, key, block);
		register(name, p -> new BlockItem(block, p), new Item.Properties().useBlockDescriptionPrefix());
		return block;
	}

	private static Item item(String name) {
		return item(name, Rarity.COMMON);
	}

	private static Item item(String name, Rarity rarity) {
		return register(name, Item::new, new Item.Properties().rarity(rarity));
	}

	private static Item register(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		TAB_ITEMS.add(item);
		return item;
	}
}
