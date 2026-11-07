package com.onepiecemod.character;

import java.util.function.Function;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;

import com.onepiecemod.OnePieceMod;

/**
 * Registers everything for One Piece characters: the character mob, Berries,
 * a Wanted Poster for every character and a Vivre Card for every friendly one.
 * OnePieceMod calls initialize() once while the game loads.
 */
public class CharacterFeature {
	/** One mob type for all characters. Which character it is gets saved on the mob itself. */
	public static final ResourceKey<EntityType<?>> CHARACTER_KEY = ResourceKey.create(Registries.ENTITY_TYPE, OnePieceMod.id("character"));
	public static final EntityType<CharacterEntity> CHARACTER = Registry.register(
			BuiltInRegistries.ENTITY_TYPE,
			CHARACTER_KEY,
			EntityType.Builder.of(CharacterEntity::new, MobCategory.MISC)
					.sized(0.6f, 1.95f) // Same size as a player. Big characters use the scale attribute.
					.fireImmune()
					.clientTrackingRange(10)
					.build(CHARACTER_KEY)
	);

	/** The money of the One Piece world. Bosses drop it, traders take it. */
	public static final Item BERRY = registerItem("berry",
			properties -> new Item(properties) {
				@Override
				public Component getName(ItemStack stack) {
					return Component.literal("Berry");
				}
			},
			new Item.Properties());

	/** Turns into a treasure map to a One Piece location. See SeaChartItem. */
	public static final Item SEA_CHART = registerItem("sea_chart", SeaChartItem::new, new Item.Properties());

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("characters")
	);

	public static void initialize() {
		CharacterAttachments.initialize();
		QuestJourneys.initialize();
		TitanLadder.initialize();
		FabricDefaultAttributeRegistry.register(CHARACTER, CharacterEntity.createAttributes());

		// A poster for every character, and a Vivre Card for everyone who isn't a villain.
		for (CharacterData character : CharacterData.all().values()) {
			registerItem("wanted_poster_" + character.id,
					properties -> new CharacterSummonItem(character.id, true, properties),
					new Item.Properties().rarity(character.tier >= 4 ? Rarity.EPIC : Rarity.UNCOMMON));
			if (!character.isBossRole()) {
				registerItem("vivre_card_" + character.id,
						properties -> new CharacterSummonItem(character.id, false, properties),
						new Item.Properties());
			}
		}

		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(CharacterData.item("onepiece:wanted_poster_luffy")))
				.title(Component.literal("One Piece: Characters"))
				.displayItems((params, output) -> {
					output.accept(BERRY);
					output.accept(SEA_CHART);
					for (CharacterData character : CharacterData.all().values()) {
						if (!character.isBossRole()) {
							output.accept(CharacterData.item("onepiece:vivre_card_" + character.id));
						}
					}
					for (CharacterData character : CharacterData.all().values()) {
						output.accept(CharacterData.item("onepiece:wanted_poster_" + character.id));
					}
				})
				.build());
	}

	private static Item registerItem(String name, Function<Item.Properties, Item> itemFactory, Item.Properties properties) {
		ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = itemFactory.apply(properties.setId(itemKey));
		Registry.register(BuiltInRegistries.ITEM, itemKey, item);
		return item;
	}
}
