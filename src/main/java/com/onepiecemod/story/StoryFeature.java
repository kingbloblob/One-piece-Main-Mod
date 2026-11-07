package com.onepiecemod.story;

import java.util.List;
import java.util.function.Function;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.Level;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;

import com.onepiecemod.OnePieceMod;

/**
 * The main story campaign: from Foosha Village to Laugh Tale in 26 chapters.
 * The chapters are in src/main/resources/onepiece/story.json. OnePieceMod calls initialize() once while the game loads.
 */
public class StoryFeature {
	/** Shows your chapter and goals. You get one the first time you join. */
	public static final Item CAPTAINS_LOG = registerItem("captains_log", properties -> new Item(properties) {
		@Override
		public Component getName(ItemStack stack) {
			return Component.literal("Captain's Log");
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			if (player instanceof net.minecraft.server.level.ServerPlayer serverPlayer) {
				StoryTracker.showLog(serverPlayer);
			}
			return InteractionResult.SUCCESS;
		}
	}, new Item.Properties().stacksTo(1));

	/** The four Road Poneglyph rubbings. Carry all four to open Laugh Tale. */
	public static final List<Item> RUBBINGS = List.of(
			rubbing("road_poneglyph_zou", "Road Poneglyph Rubbing (Zou)"),
			rubbing("road_poneglyph_whole_cake", "Road Poneglyph Rubbing (Whole Cake Island)"),
			rubbing("road_poneglyph_wano", "Road Poneglyph Rubbing (Wano)"),
			rubbing("road_poneglyph_hachinosu", "Road Poneglyph Rubbing (Hachinosu)")
	);

	/** Roger's treasure. A trophy for finishing the story. */
	public static final Item THE_ONE_PIECE = registerItem("the_one_piece", properties -> new Item(properties) {
		@Override
		public Component getName(ItemStack stack) {
			return Component.literal("The One Piece").withStyle(ChatFormatting.GOLD);
		}
	}, new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).fireResistant());

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("story")
	);

	public static void initialize() {
		StoryProgress.initialize();
		StoryTracker.initialize();
		StoryEvents.initialize();
		StoryRaids.initialize();
		StoryGates.initialize();
		StoryCommands.initialize();

		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(CAPTAINS_LOG))
				.title(Component.literal("One Piece: Story"))
				.displayItems((params, output) -> {
					output.accept(CAPTAINS_LOG);
					RUBBINGS.forEach(output::accept);
					output.accept(THE_ONE_PIECE);
				})
				.build());

		// Typos in story.json show up in the game log when a world starts.
		ServerLifecycleEvents.SERVER_STARTED.register(server -> {
			for (String problem : StoryData.problems()) {
				OnePieceMod.LOGGER.warn("Story problem: {}", problem);
			}
		});
	}

	private static Item rubbing(String id, String name) {
		return registerItem(id, properties -> new Item(properties) {
			@Override
			public Component getName(ItemStack stack) {
				return Component.literal(name);
			}
		}, new Item.Properties().stacksTo(1).rarity(Rarity.RARE));
	}

	private static Item registerItem(String name, Function<Item.Properties, Item> itemFactory, Item.Properties properties) {
		ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = itemFactory.apply(properties.setId(itemKey));
		Registry.register(BuiltInRegistries.ITEM, itemKey, item);
		return item;
	}
}
