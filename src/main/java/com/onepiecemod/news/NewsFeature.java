package com.onepiecemod.news;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.sea.SeaItems;

/**
 * News of the world, reaching the player:
 *  - NewsCoo + Newspaper: a paper every morning with the players' deeds and world events (/news).
 *  - NewsWatcher: notices boss wins, bounty jumps, new crews, titles... and writes them up (NewsLog).
 *  - WantedPosterBlock: wall posters that always show live bounties; PosterPlacer pins them in towns.
 *  - SnailCalls: incoming Den Den Mushi calls (boss taunts, Marine broadcasts, crew in trouble).
 * Stories, canon posters and taunts live in src/main/resources/onepiece/news.json.
 */
public class NewsFeature {
	public static final ResourceKey<Block> WANTED_POSTER_KEY = ResourceKey.create(Registries.BLOCK, OnePieceMod.id("wall_wanted_poster"));
	public static final Block WANTED_POSTER = Registry.register(BuiltInRegistries.BLOCK, WANTED_POSTER_KEY,
			new WantedPosterBlock(BlockBehaviour.Properties.of().mapColor(MapColor.SAND).strength(0.3f)
					.sound(SoundType.WOOL).noOcclusion().noCollision().setId(WANTED_POSTER_KEY)));

	public static final ResourceKey<Item> WANTED_POSTER_ITEM_KEY = ResourceKey.create(Registries.ITEM, OnePieceMod.id("wall_wanted_poster"));
	public static final Item WANTED_POSTER_ITEM = Registry.register(BuiltInRegistries.ITEM, WANTED_POSTER_ITEM_KEY,
			new BlockItem(WANTED_POSTER, new Item.Properties().useBlockDescriptionPrefix().setId(WANTED_POSTER_ITEM_KEY)));

	public static final BlockEntityType<WantedPosterBlockEntity> WANTED_POSTER_ENTITY = Registry.register(
			BuiltInRegistries.BLOCK_ENTITY_TYPE,
			OnePieceMod.id("wall_wanted_poster"),
			FabricBlockEntityTypeBuilder.create(WantedPosterBlockEntity::new, WANTED_POSTER).build()
	);

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("news")
	);

	public static void initialize() {
		NewsData.get(); // Read news.json now so a typo shows up at startup.
		NewsCoo.initialize();
		NewsWatcher.initialize();
		SnailCalls.initialize();
		PosterPlacer.initialize();
		NewsCommands.initialize();
		// Load the attachment class so it registers before any world loads.
		if (NewsLog.MOST_WANTED == null) {
			throw new IllegalStateException("News attachments missing");
		}

		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(WANTED_POSTER_ITEM))
				.title(Component.literal("One Piece: News"))
				.displayItems((params, output) -> {
					output.accept(WANTED_POSTER_ITEM);
					output.accept(SeaItems.DEN_DEN_MUSHI);
				})
				.build());
	}
}
