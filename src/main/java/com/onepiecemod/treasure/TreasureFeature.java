package com.onepiecemod.treasure;

import java.util.List;
import java.util.function.Function;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.storage.loot.LootPool;
import net.minecraft.world.level.storage.loot.entries.LootItem;
import net.minecraft.world.level.storage.loot.predicates.LootItemRandomChanceCondition;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.loot.v3.LootTableEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.advancement.AdvancementFeature;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.item.ModItems;
import com.onepiecemod.news.NewsCoo;
import com.onepiecemod.news.NewsLog;
import com.onepiecemod.npc.HumanNpc;

/**
 * Treasure maps and buried loot.
 * - Where maps come from: tucked into the morning paper now and then (1 in 5), dropped by beaten bosses (a Captain's
 *   Hoard Map, always on the first win), pirate captains (sometimes), and the map chest of every sunken wreck.
 * - Right-click a map: it unfolds into a real map with a red X (TreasureMapItem). The treasure is built only when a
 *   player sails close (TreasureSites + TreasureBuilder).
 * - Open the chest: the treasure counts as found, and it makes tomorrow's paper.
 * /treasure give <kind> and /treasure list are for operators (testing).
 */
public final class TreasureFeature {
	/** The marked earth over buried treasure. */
	public static final Block DIG_SPOT = registerBlock("dig_spot", DigSpotBlock::new,
			BlockBehaviour.Properties.ofFullCopy(Blocks.COARSE_DIRT).sound(SoundType.ROOTED_DIRT).noLootTable());

	public static final Item TREASURE_MAP = registerItem("treasure_map", TreasureKind.BURIED);
	public static final Item WRECK_CHART = registerItem("wreck_chart", TreasureKind.WRECK);
	public static final Item HOARD_MAP = registerItem("hoard_map", TreasureKind.HOARD);
	public static final Item CASTAWAY_CHART = registerItem("castaway_chart", TreasureKind.CASTAWAY);

	/** The last newspaper day this player was checked for a map inside (copies NewsCoo's counter). */
	private static final AttachmentType<Long> PAPER_SEEN = AttachmentRegistry.create(
			OnePieceMod.id("treasure_paper_seen"),
			builder -> builder.persistent(Codec.LONG).copyOnDeath()
	);

	/** How many treasures from maps this player has found, for the Treasure Hunter achievement. */
	private static final AttachmentType<Integer> TREASURES_FOUND = AttachmentRegistry.create(
			OnePieceMod.id("treasures_found"),
			builder -> builder.persistent(Codec.INT).copyOnDeath()
	);

	private static final float PAPER_CHANCE = 0.2f;
	private static final float REMATCH_CHANCE = 0.25f;
	private static final float CAPTAIN_CHANCE = 0.12f;
	/** A hoard sometimes holds the Devil Fruit its captain never got round to eating. */
	private static final float HOARD_FRUIT_CHANCE = 0.1f;

	private TreasureFeature() {
	}

	/** How many buried treasures and hoards this player has dug up (story goal "treasure"). */
	public static int treasuresFound(net.minecraft.world.entity.player.Player player) {
		return player.getAttachedOrElse(TREASURES_FOUND, 0);
	}

	public static void initialize() {
		// Some list must touch the attachment so it is registered before levels load.
		OnePieceMod.LOGGER.debug("Treasure attachments: {}", TreasureSites.SITES);

		ServerTickEvents.END_LEVEL_TICK.register(level -> {
			if (level.dimension() == Level.OVERWORLD && level.getGameTime() % 20 == 11) {
				TreasureSites.tick(level);
			}
		});
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 40 == 21) {
				for (ServerPlayer player : server.getPlayerList().getPlayers()) {
					checkPaper(player);
				}
			}
		});

		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (!(entity.level() instanceof ServerLevel level)) {
				return;
			}
			if (entity instanceof CharacterEntity boss && boss.isBoss()) {
				// Whoever landed the last hit (crewmate, pet, cannon), the winners get the captain's map.
				if (boss.isFirstWin() || level.getRandom().nextFloat() < REMATCH_CHANCE) {
					entity.spawnAtLocation(level, new ItemStack(HOARD_MAP));
				}
			} else if (source.getEntity() instanceof ServerPlayer && entity instanceof HumanNpc npc && isCaptain(npc.getKitId())
					&& level.getRandom().nextFloat() < CAPTAIN_CHANCE) {
				entity.spawnAtLocation(level, new ItemStack(TREASURE_MAP));
			}
		});

		LootTableEvents.MODIFY.register((key, tableBuilder, source, registries) -> {
			if (key.equals(TreasureBuilder.HOARD_LOOT)) {
				LootPool.Builder pool = LootPool.lootPool().when(LootItemRandomChanceCondition.randomChance(HOARD_FRUIT_CHANCE));
				for (Item fruit : ModItems.DEVIL_FRUITS.values()) {
					pool.add(LootItem.lootTableItem(fruit));
				}
				tableBuilder.withPool(pool);
			}
		});

		// Next to the Sea Chart in the main One Piece tab.
		CreativeModeTabEvents.modifyOutputEvent(com.onepiecemod.character.CharacterFeature.TAB_KEY).register(output -> {
			output.accept(TREASURE_MAP);
			output.accept(WRECK_CHART);
			output.accept(HOARD_MAP);
			output.accept(CASTAWAY_CHART);
			output.accept(DIG_SPOT);
		});

		registerCommands();
	}

	private static boolean isCaptain(String kit) {
		return "pirate_captain".equals(kit) || "headliner".equals(kit);
	}

	/** A paper just arrived (NewsCoo moved its day counter): sometimes there's a map folded inside. */
	private static void checkPaper(ServerPlayer player) {
		Long paper = player.getAttached(NewsCoo.LAST_PAPER);
		if (paper == null) {
			return;
		}
		Long seen = player.getAttached(PAPER_SEEN);
		if (seen != null && seen >= paper) {
			return;
		}
		player.setAttached(PAPER_SEEN, paper);
		if (seen == null || player.getRandom().nextFloat() >= PAPER_CHANCE) {
			return; // First check for this player only starts the count.
		}
		Item map = player.getRandom().nextFloat() < 0.65f ? TREASURE_MAP : WRECK_CHART;
		ItemStack stack = new ItemStack(map);
		if (!player.getInventory().add(stack)) {
			player.drop(stack, false, net.minecraft.util.Prediction.SERVER_ONLY);
		}
		player.sendSystemMessage(Component.literal("Something was folded inside today's paper: a "
				+ ((TreasureMapItem) map).kind().closedName + "!").withStyle(ChatFormatting.GOLD));
	}

	/** Someone opened the chest of a treasure from a map. */
	public static void found(ServerLevel level, ServerPlayer player, TreasureKind kind, BlockPos pos) {
		String what = switch (kind) {
			case BURIED -> "buried treasure";
			case WRECK -> "the treasure of a sunken ship";
			case HOARD -> "a pirate captain's lost hoard";
			case CASTAWAY -> "a castaway's hidden cache";
		};
		player.sendSystemMessage(Component.literal("You found " + what + "!").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
		level.playSound(null, pos, SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.8f, 1.2f);

		// Achievements (tools/advancements/gen_advancements.py, journey tab).
		AdvancementFeature.grant(player, switch (kind) {
			case BURIED -> "journey/buried_treasure";
			case WRECK -> "journey/sunken_wreck";
			case HOARD -> "journey/captains_hoard";
			case CASTAWAY -> "journey/castaway_cache";
		});
		int found = player.getAttachedOrElse(TREASURES_FOUND, 0) + 1;
		player.setAttached(TREASURES_FOUND, found);
		if (found >= 10) {
			AdvancementFeature.grant(player, "journey/treasure_hunter");
		}
		String headline = switch (kind) {
			case BURIED -> "X MARKS THE SPOT";
			case WRECK -> "SUNKEN SHIP PLUNDERED";
			case HOARD -> "LEGENDARY HOARD DUG UP";
			case CASTAWAY -> "CASTAWAY'S CACHE FOUND ON LONELY SANDBAR";
		};
		NewsLog.report(level.getServer(), headline, player.getName().getString() + " has found " + what
				+ ". Treasure hunters are already sailing for the same waters.", false);
	}

	// ---------- /treasure (operators only) ----------

	private static void registerCommands() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("treasure")
						.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
						.then(Commands.literal("give")
								.then(Commands.argument("kind", StringArgumentType.word())
										.suggests((context, builder) -> SharedSuggestionProvider.suggest(
												List.of("buried", "wreck", "hoard", "castaway"), builder))
										.executes(context -> {
											ServerPlayer player = context.getSource().getPlayerOrException();
											Item item = switch (StringArgumentType.getString(context, "kind")) {
												case "wreck" -> WRECK_CHART;
												case "hoard" -> HOARD_MAP;
												case "castaway" -> CASTAWAY_CHART;
												default -> TREASURE_MAP;
											};
											player.getInventory().add(new ItemStack(item));
											return 1;
										})))
						.then(Commands.literal("list").executes(context -> {
							ServerLevel level = context.getSource().getServer().overworld();
							List<TreasureSites.Site> sites = TreasureSites.all(level);
							context.getSource().sendSuccess(() -> Component.literal(sites.size() + " treasure sites"), false);
							for (TreasureSites.Site site : sites) {
								context.getSource().sendSuccess(() -> Component.literal(site.kind() + " at " + site.x() + " "
										+ site.y() + " " + site.z() + (site.state() == TreasureSites.BUILT ? " (built)" : " (waiting)")), false);
							}
							return sites.size();
						}))));
	}

	// ---------- Registration ----------

	private static Item registerItem(String name, TreasureKind kind) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = new TreasureMapItem(kind, new Item.Properties().setId(key).stacksTo(16));
		return Registry.register(BuiltInRegistries.ITEM, key, item);
	}

	private static Block registerBlock(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties properties) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, OnePieceMod.id(name));
		Block block = Registry.register(BuiltInRegistries.BLOCK, key, factory.apply(properties.setId(key)));
		ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Registry.register(BuiltInRegistries.ITEM, itemKey, new BlockItem(block, new Item.Properties().setId(itemKey).useBlockDescriptionPrefix()));
		return block;
	}
}
