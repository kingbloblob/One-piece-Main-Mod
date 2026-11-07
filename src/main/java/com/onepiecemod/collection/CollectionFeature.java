package com.onepiecemod.collection;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import net.minecraft.ChatFormatting;
import com.mojang.brigadier.arguments.StringArgumentType;

import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.stats.Stats;
import net.minecraft.util.Prediction;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.structure.Structure;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.advancement.AdvancementFeature;
import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.cuisine.Fishing;
import com.onepiecemod.item.ModItems;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipItem;
import com.onepiecemod.stats.StatTraining;

/**
 * The Collector's Log: a book that keeps track of every fish you caught, every dish you tasted, every famous ship you
 * spotted, every legendary sword you held and every island you finished.
 *
 * Each tab pays Berries (and Pirate XP) at milestones, and more for filling it completely.
 * Each island has goals (set foot there, explore it, deal with the locals); finishing them all pays its own reward,
 * and finishing every island of a sea pays a big one.
 *
 * Nothing else needs a hook: fish come from Fishing.CAUGHT, food from the game's "used" statistic, swords from the
 * inventory, ships from the ships sailing near you, islands from the structure you stand in.
 * OnePieceMod calls initialize() once.
 */
public class CollectionFeature {
	private static final int CHECK_TICKS = 40;
	private static final int SHIP_SIGHT = 48;

	public static final AttachmentType<CollectionProgress> PROGRESS = AttachmentRegistry.create(
			OnePieceMod.id("collections"),
			builder -> builder.persistent(CollectionProgress.CODEC).copyOnDeath());

	public static final Item COLLECTORS_LOG = register("collectors_log", properties -> new Item(properties) {
		@Override
		public Component getName(ItemStack stack) {
			return Component.literal("Collector's Log");
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			if (player instanceof ServerPlayer serverPlayer) {
				open(serverPlayer);
			}
			return InteractionResult.SUCCESS;
		}
	}, new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON));

	private static Set<Item> swordItems;

	public static void initialize() {
		CollectionPayloads.initialize();
		CreativeModeTabEvents.modifyOutputEvent(ModItems.ONE_PIECE_TAB_KEY).register(output -> output.accept(COLLECTORS_LOG));
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % CHECK_TICKS != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				if (!player.isSpectator()) {
					check(player);
				}
			}
		});
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) ->
				dispatcher.register(Commands.literal("collections")
						.executes(context -> {
							open(context.getSource().getPlayerOrException());
							return 1;
						})
						// Operators, for testing: finish an island at once and get its reward.
						.then(Commands.literal("finish")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.argument("island", StringArgumentType.word())
										.suggests((context, builder) -> SharedSuggestionProvider.suggest(
												CollectionData.islands().stream().map(island -> island.id), builder))
										.executes(context -> finish(context.getSource().getPlayerOrException(),
												StringArgumentType.getString(context, "island")))))));
	}

	private static int finish(ServerPlayer player, String id) {
		CollectionData.Island island = CollectionData.island(id);
		if (island == null) {
			player.sendSystemMessage(Component.literal("No island called " + id + ".").withStyle(ChatFormatting.RED));
			return 0;
		}
		CollectionProgress progress = get(player).with("visited", id);
		if (!progress.has(CollectionData.ISLANDS, id)) {
			progress = completeIsland(player, progress, island);
		}
		player.setAttached(PROGRESS, checkMilestones(player, progress));
		return 1;
	}

	public static CollectionProgress get(Player player) {
		return player.getAttachedOrElse(PROGRESS, CollectionProgress.EMPTY);
	}

	// ---- What the player has collected ----

	public static List<String> fish(Player player) {
		return player.getAttachedOrElse(Fishing.CAUGHT, List.of());
	}

	public static List<String> food(ServerPlayer player) {
		List<String> tasted = new ArrayList<>();
		for (Item item : CollectionData.foods()) {
			if (player.getStats().getValue(Stats.ITEM_USED, item) > 0) {
				tasted.add(BuiltInRegistries.ITEM.getKey(item).toString());
			}
		}
		return tasted;
	}

	/** How many entries of a tab are collected. */
	public static int count(ServerPlayer player, String tab) {
		CollectionProgress progress = get(player);
		return switch (tab) {
			case CollectionData.FISH -> fish(player).size();
			case CollectionData.FOOD -> food(player).size();
			case CollectionData.SHIPS -> progress.list(CollectionData.SHIPS).size();
			case CollectionData.SWORDS -> progress.list(CollectionData.SWORDS).size();
			case CollectionData.ISLANDS -> progress.list(CollectionData.ISLANDS).size();
			default -> 0;
		};
	}

	/** Whether goal number index of an island is done. */
	public static boolean goalDone(ServerPlayer player, CollectionProgress progress, CollectionData.Island island, CollectionData.Goal goal) {
		return switch (goal.type) {
			case "visit" -> progress.has("visited", island.id);
			case "explore" -> progress.counter("explore:" + island.id) >= goal.seconds;
			case "boss" -> CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, goal.character);
			case "quest" -> CharacterAttachments.has(player, CharacterAttachments.QUESTS_DONE, goal.character + ":0");
			case "meet" -> CharacterAttachments.has(player, CharacterAttachments.MET, goal.character);
			default -> false;
		};
	}

	// ---- Every 2 seconds ----

	private static void check(ServerPlayer player) {
		CollectionProgress before = get(player);
		CollectionProgress progress = before;
		progress = checkSwordsAndShipItems(player, progress);
		progress = checkShips(player, progress);
		progress = checkPlace(player, progress);
		progress = checkFood(player, progress);
		progress = checkIslands(player, progress);
		progress = checkMilestones(player, progress);
		if (progress != before) {
			player.setAttached(PROGRESS, progress);
		}
	}

	private static Set<Item> swordItems() {
		if (swordItems == null) {
			Set<Item> items = new HashSet<>();
			for (CollectionData.Sword sword : CollectionData.swords()) {
				items.add(CollectionData.item(sword.item));
			}
			swordItems = items;
		}
		return swordItems;
	}

	private static CollectionProgress checkSwordsAndShipItems(ServerPlayer player, CollectionProgress progress) {
		var inventory = player.getInventory();
		for (int i = 0; i < inventory.getContainerSize(); i++) {
			ItemStack stack = inventory.getItem(i);
			if (stack.isEmpty()) {
				continue;
			}
			if (swordItems().contains(stack.getItem())) {
				String id = BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
				if (!progress.has(CollectionData.SWORDS, id)) {
					progress = progress.with(CollectionData.SWORDS, id);
					announce(player, "New blade in your Collector's Log: ", stack.getHoverName().getString(),
							progress.list(CollectionData.SWORDS).size(), CollectionData.SWORDS);
				}
			} else if (stack.getItem() instanceof ShipItem shipItem) {
				progress = spot(player, progress, shipItem.shipId());
			}
		}
		return progress;
	}

	private static CollectionProgress checkShips(ServerPlayer player, CollectionProgress progress) {
		ShipEntity aboard = ShipEntity.aboard(player);
		List<ShipEntity> near = player.level().getEntitiesOfClass(ShipEntity.class, player.getBoundingBox().inflate(SHIP_SIGHT));
		for (ShipEntity ship : near) {
			if (ship.getCustomName() == null) {
				continue;
			}
			String name = ship.getCustomName().getString();
			for (CollectionData.Ship entry : CollectionData.ships()) {
				if (name.contains(entry.name)) {
					progress = spot(player, progress, entry.id);
					if (ship == aboard && !progress.has("sailed", entry.id)) {
						progress = progress.with("sailed", entry.id);
						player.sendSystemMessage(Component.literal("Collector's Log: you've been aboard the " + entry.name + "!")
								.withStyle(ChatFormatting.AQUA));
					}
					break;
				}
			}
		}
		return progress;
	}

	private static CollectionProgress spot(ServerPlayer player, CollectionProgress progress, String shipId) {
		if (progress.has(CollectionData.SHIPS, shipId)) {
			return progress;
		}
		for (CollectionData.Ship entry : CollectionData.ships()) {
			if (entry.id.equals(shipId)) {
				progress = progress.with(CollectionData.SHIPS, shipId);
				announce(player, "Ship sighted for your Collector's Log: ", entry.name,
						progress.list(CollectionData.SHIPS).size(), CollectionData.SHIPS);
			}
		}
		return progress;
	}

	/** Which named place the player stands in, if any. */
	private static CollectionProgress checkPlace(ServerPlayer player, CollectionProgress progress) {
		ServerLevel level = (ServerLevel) player.level();
		BlockPos pos = player.blockPosition();
		Registry<Structure> structures = level.registryAccess().lookupOrThrow(Registries.STRUCTURE);
		for (Structure structure : level.structureManager().getAllStructuresAt(pos).keySet()) {
			Identifier key = structures.getKey(structure);
			if (key == null || !key.getNamespace().equals(OnePieceMod.MOD_ID)) {
				continue;
			}
			CollectionData.Island island = CollectionData.island(key.getPath());
			if (island == null || !level.structureManager().getStructureAt(pos, structure).isValid()) {
				continue;
			}
			if (!progress.has("visited", island.id)) {
				progress = progress.with("visited", island.id);
				player.sendSystemMessage(Component.literal("New island page: ").withStyle(ChatFormatting.AQUA)
						.append(Component.literal(island.name).withStyle(ChatFormatting.GOLD))
						.append(Component.literal(" (see its goals in your Collector's Log, /collections)").withStyle(ChatFormatting.GRAY)));
			}
			String counter = "explore:" + island.id;
			int seconds = progress.counter(counter);
			if (seconds < 600) {
				progress = progress.withCounter(counter, seconds + CHECK_TICKS / 20);
			}
			break;
		}
		return progress;
	}

	private static CollectionProgress checkFood(ServerPlayer player, CollectionProgress progress) {
		int tasted = food(player).size();
		int known = progress.counter(CollectionData.FOOD);
		if (tasted > known) {
			progress = progress.withCounter(CollectionData.FOOD, tasted);
			if (known > 0 || tasted == 1) {
				player.sendOverlayMessage(Component.literal("Collector's Log: new dish tasted (" + tasted + "/"
						+ CollectionData.size(CollectionData.FOOD) + ")").withStyle(ChatFormatting.GOLD));
			}
		}
		return progress;
	}

	private static CollectionProgress checkIslands(ServerPlayer player, CollectionProgress progress) {
		for (String visited : progress.list("visited")) {
			CollectionData.Island island = CollectionData.island(visited);
			if (island == null || progress.has(CollectionData.ISLANDS, island.id)) {
				continue;
			}
			boolean done = true;
			for (CollectionData.Goal goal : island.goals) {
				if (!goalDone(player, progress, island, goal)) {
					done = false;
					break;
				}
			}
			if (!done) {
				continue;
			}
			progress = completeIsland(player, progress, island);
		}
		return progress;
	}

	private static CollectionProgress completeIsland(ServerPlayer player, CollectionProgress progress, CollectionData.Island island) {
		progress = progress.with(CollectionData.ISLANDS, island.id);
		player.sendSystemMessage(Component.literal("Island complete: ").withStyle(ChatFormatting.GREEN, ChatFormatting.BOLD)
				.append(Component.literal(island.name).withStyle(ChatFormatting.GOLD)));
		give(player, island.reward);
		AdvancementFeature.grant(player, "journey/island_complete");
		return checkRegion(player, progress, island.region);
	}

	private static CollectionProgress checkRegion(ServerPlayer player, CollectionProgress progress, String regionId) {
		String claim = "region:" + regionId;
		if (progress.has("claimed", claim)) {
			return progress;
		}
		for (CollectionData.Island island : CollectionData.islands()) {
			if (island.region.equals(regionId) && !progress.has(CollectionData.ISLANDS, island.id)) {
				return progress;
			}
		}
		for (CollectionData.Region region : CollectionData.regions()) {
			if (region.id.equals(regionId)) {
				player.sendSystemMessage(Component.literal("Every island of " + region.title + " is complete! ")
						.withStyle(ChatFormatting.LIGHT_PURPLE, ChatFormatting.BOLD));
				give(player, region.reward);
				AdvancementFeature.grant(player, "journey/sea_" + regionId);
			}
		}
		return progress.with("claimed", claim);
	}

	private static CollectionProgress checkMilestones(ServerPlayer player, CollectionProgress progress) {
		for (String tab : CollectionData.TABS) {
			CollectionData.Tab data = CollectionData.tab(tab);
			int count = -1;
			for (Map.Entry<String, Integer> milestone : data.milestones.entrySet()) {
				String claim = tab + ":" + milestone.getKey();
				if (progress.has("claimed", claim)) {
					continue;
				}
				if (count < 0) {
					count = count(player, tab);
				}
				int need = CollectionData.threshold(tab, milestone.getKey());
				if (count < need) {
					continue;
				}
				progress = progress.with("claimed", claim);
				boolean all = need >= CollectionData.size(tab);
				CollectionData.Reward reward = new CollectionData.Reward();
				reward.berries = milestone.getValue();
				if (all) {
					reward.items = data.items;
					reward.xp = data.xp;
				}
				player.sendSystemMessage(Component.literal(all
						? "Collection complete: " + tabTitle(tab) + "! Every last one."
						: "Collector's Log milestone: " + count + " " + tabTitle(tab).toLowerCase() + ".")
						.withStyle(all ? ChatFormatting.LIGHT_PURPLE : ChatFormatting.GREEN));
				give(player, reward);
				if (all) {
					AdvancementFeature.grant(player, switch (tab) {
						case CollectionData.FISH -> "journey/every_fish";
						case CollectionData.FOOD -> "pirate/gourmet";
						case CollectionData.SHIPS -> "wonders/ship_spotter";
						case CollectionData.SWORDS -> "pirate/sword_collector";
						default -> "journey/every_island";
					});
				}
			}
		}
		return progress;
	}

	public static String tabTitle(String tab) {
		return switch (tab) {
			case CollectionData.FISH -> "Fish";
			case CollectionData.FOOD -> "Dishes";
			case CollectionData.SHIPS -> "Ships";
			case CollectionData.SWORDS -> "Swords";
			default -> "Islands";
		};
	}

	private static void announce(ServerPlayer player, String what, String name, int count, String tab) {
		player.sendSystemMessage(Component.literal(what).withStyle(ChatFormatting.AQUA)
				.append(Component.literal(name).withStyle(ChatFormatting.GOLD))
				.append(Component.literal(" (" + count + "/" + CollectionData.size(tab) + ")").withStyle(ChatFormatting.GRAY)));
		player.level().playSound(null, player.blockPosition(), SoundEvents.BOOK_PAGE_TURN, SoundSource.PLAYERS, 1.0f, 1.0f);
	}

	/** Pays a reward: Berries, items and Pirate XP. */
	private static void give(ServerPlayer player, CollectionData.Reward reward) {
		List<ItemStack> stacks = new ArrayList<>();
		if (reward.berries > 0) {
			stacks.add(new ItemStack(CharacterFeature.BERRY, reward.berries));
		}
		for (String spec : reward.items) {
			ItemStack stack = CollectionData.stack(spec);
			if (!stack.isEmpty()) {
				stacks.add(stack);
			}
		}
		StringBuilder text = new StringBuilder("Reward: ");
		for (int i = 0; i < stacks.size(); i++) {
			ItemStack stack = stacks.get(i);
			String name = stack.is(CharacterFeature.BERRY) ? "Berries" : stack.getHoverName().getString();
			text.append(i > 0 ? ", " : "").append(stack.getCount()).append(" ").append(name);
			if (!player.getInventory().add(stack.copy())) {
				player.drop(stack.copy(), false, Prediction.SERVER_ONLY);
			}
		}
		if (reward.xp > 0) {
			text.append(stacks.isEmpty() ? "" : ", ").append(reward.xp).append(" Pirate XP");
		}
		player.sendSystemMessage(Component.literal(text.toString()).withStyle(ChatFormatting.YELLOW));
		if (reward.xp > 0) {
			StatTraining.addXp(player, reward.xp, false);
		}
		player.level().playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 1.0f, 1.2f);
	}

	// ---- The book ----

	public static void open(ServerPlayer player) {
		if (!ServerPlayNetworking.canSend(player, CollectionPayloads.Open.TYPE)) {
			player.sendSystemMessage(Component.literal("Collector's Log: " + count(player, CollectionData.FISH) + " fish, "
					+ count(player, CollectionData.FOOD) + " dishes, " + count(player, CollectionData.SHIPS) + " ships, "
					+ count(player, CollectionData.SWORDS) + " swords, " + count(player, CollectionData.ISLANDS) + " islands."));
			return;
		}
		CollectionProgress progress = get(player);
		Map<String, List<String>> lists = new HashMap<>(progress.lists());
		lists.put(CollectionData.FISH, fish(player));
		lists.put(CollectionData.FOOD, food(player));
		List<String> goals = new ArrayList<>();
		for (CollectionData.Island island : CollectionData.islands()) {
			for (int i = 0; i < island.goals.size(); i++) {
				if (goalDone(player, progress, island, island.goals.get(i))) {
					goals.add(island.id + ":" + i);
				}
			}
		}
		lists.put("goals", goals);
		ServerPlayNetworking.send(player, new CollectionPayloads.Open(lists, new HashMap<>(progress.counters())));
	}

	private static Item register(String name, java.util.function.Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		return Registry.register(BuiltInRegistries.ITEM, key, factory.apply(properties.setId(key)));
	}
}
