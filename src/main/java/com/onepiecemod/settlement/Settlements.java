package com.onepiecemod.settlement;

import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import com.mojang.brigadier.arguments.StringArgumentType;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.BellBlock;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.BoundingBox;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.baseworks.PlanOutlines;
import com.onepiecemod.building.GhostPayload;
import com.onepiecemod.building.GhostPlan;
import com.onepiecemod.building.Parts;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.item.ModItems;
import com.onepiecemod.town.Town;
import com.onepiecemod.town.TownData;
import com.onepiecemod.town.Towns;

/**
 * Player towns. Hang a bell, use the Town Planner on it, and mark out plots around it. When a plot has what its
 * kind needs (a House: a bed, a door and a light), it's settled: townsfolk move in and live there like in Foosha
 * or Nanohana (daily routines, a bar in the evening, market stalls, festivals), and the town pays rent into
 * its treasury every day. Rent can be collected at the bell or spent on hideout upgrades in the Builder's Ledger.
 *
 * Under the hood a player town is an ordinary town of the town package (a Town with its own TownDef), handed to
 * Towns so all of its town life just works. It's re-made whenever its plots or their state change.
 */
public final class Settlements {
	public static final Item TOWN_PLANNER = register("town_planner");

	private static final String STRUCTURE_ID = "player_town";
	private static final int MAX_PLOTS = 40;
	private static final long TREASURY_CAP = 5000;

	static final List<String> CULTURES = List.of("east_blue", "grand_line", "alabasta", "water7", "sabaody", "wano", "totto", "kuja");
	private static final Map<String, String> FESTIVALS = Map.of("east_blue", "harvest_festival", "alabasta", "rain_festival",
			"wano", "fire_festival", "totto", "tea_party", "grand_line", "welcome_party", "water7", "welcome_party",
			"sabaody", "welcome_party", "kuja", "sakura_festival");
	static final String[] LEVEL_NAMES = {"Empty Lot", "Hamlet", "Village", "Town", "Port Town", "City"};

	/** Things the town can pay for out of its treasury. */
	enum TownUpgrade {
		MARKET("market_charter", "Market Charter", 150, 2, PlotKind.SHOP, "Market stalls open in the mornings and foreign trader ships call."),
		FESTIVAL("festival_grounds", "Festival Grounds", 120, 2, PlotKind.PLAZA, "Your town holds its culture's festival."),
		HARBOR("harbor_office", "Harbor Office", 200, 3, PlotKind.DOCK, "Sailors and a shipwright move in."),
		LAMPLIGHTERS("lamplighters", "Lamplighters", 250, 3, null, "Street lamps and a night watch: rent +25%.");

		final String id;
		final String title;
		final int cost;
		final int townLevel;
		final PlotKind needsPlot;
		final String effect;

		TownUpgrade(String id, String title, int cost, int townLevel, PlotKind needsPlot, String effect) {
			this.id = id;
			this.title = title;
			this.cost = cost;
			this.townLevel = townLevel;
			this.needsPlot = needsPlot;
			this.effect = effect;
		}

		static TownUpgrade byId(String id) {
			for (TownUpgrade upgrade : values()) {
				if (upgrade.id.equals(id)) {
					return upgrade;
				}
			}
			return null;
		}
	}

	/** What we know about a loaded player town (rebuilt from the blocks, never saved). */
	private static final class Live {
		final String key;
		final TownData.TownDef def = new TownData.TownDef();
		Town town;
		BoundingBox box;
		String state = "";
		List<List<String>> missing = new ArrayList<>();
		int level;
		int lastLevel = -1;

		Live(String key) {
			this.key = key;
		}
	}

	private static final Map<String, Live> LIVE = new HashMap<>();
	/** Players who see their town's plot outlines right now. */
	private static final Set<UUID> DRAWING = new HashSet<>();

	private Settlements() {
	}

	private static Item register(String name) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		return Registry.register(BuiltInRegistries.ITEM, key, new TownPlannerItem(new Item.Properties().stacksTo(1).setId(key)));
	}

	public static void initialize() {
		java.util.Objects.requireNonNull(PlayerTowns.TOWNS);
		CreativeModeTabEvents.modifyOutputEvent(ModItems.ONE_PIECE_TAB_KEY).register(output -> output.accept(TOWN_PLANNER));
		ServerTickEvents.END_SERVER_TICK.register(Settlements::tick);
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> {
			LIVE.clear();
			DRAWING.clear();
		});
		SettlementCommands.register();
		// A bell rings when you click it, before the item in your hand gets a turn: catch the planner first.
		UseBlockCallback.EVENT.register((player, world, hand, hit) -> {
			if (!player.getItemInHand(hand).is(TOWN_PLANNER) || !(world.getBlockState(hit.getBlockPos()).getBlock() instanceof BellBlock)) {
				return InteractionResult.PASS;
			}
			if (player instanceof ServerPlayer serverPlayer) {
				useOnBell(serverPlayer, hit.getBlockPos().immutable());
			}
			return InteractionResult.SUCCESS;
		});
	}

	// ---------- Running the towns ----------

	private static void tick(MinecraftServer server) {
		int now = server.getTickCount();
		if (now % 20 == 0) {
			drawOutlines(server);
		}
		if (now % 40 != 10) {
			return;
		}
		ServerLevel level = server.overworld();
		for (Map.Entry<String, PlayerTowns.PlayerTown> entry : PlayerTowns.all(server).entrySet()) {
			PlayerTowns.PlayerTown saved = entry.getValue();
			if (!level.isLoaded(saved.bell()) || !playerNear(level, saved.bell(), PlayerTowns.RADIUS + 48)) {
				continue;
			}
			UUID owner = UUID.fromString(entry.getKey());
			Live live = LIVE.computeIfAbsent(entry.getKey(), k -> new Live(STRUCTURE_ID + "@" + k.substring(0, 8)));
			if (live.town == null || now % 200 == 10) {
				evaluate(level, owner, saved, live);
			}
			if (Towns.byKey(live.key) != live.town && live.town != null) {
				Towns.putTown(live.town); // The town list was cleared (server restart): put it back.
			}
			if (live.town != null) {
				live.town.lastVisited = level.getGameTime();
			}
			payRent(server, owner, saved, live);
		}
	}

	private static boolean playerNear(ServerLevel level, BlockPos pos, double range) {
		for (ServerPlayer player : level.players()) {
			double dx = player.getX() - pos.getX();
			double dz = player.getZ() - pos.getZ();
			if (dx * dx + dz * dz <= range * range && !player.isSpectator()) {
				return true;
			}
		}
		return false;
	}

	/** Looks over every plot, updates who should live here, and re-makes the town if anything changed. */
	private static void evaluate(ServerLevel level, UUID owner, PlayerTowns.PlayerTown saved, Live live) {
		List<List<String>> missing = new ArrayList<>();
		StringBuilder state = new StringBuilder(saved.name()).append('|').append(saved.culture()).append('|').append(saved.upgrades());
		int houses = 0;
		int workplaces = 0;
		Set<PlotKind> settledKinds = EnumSet.noneOf(PlotKind.class);
		Map<String, Integer> jobs = new LinkedHashMap<>();
		for (PlayerTowns.Plot plot : saved.plots()) {
			List<String> needs = check(level, plot);
			missing.add(needs);
			boolean settled = needs.isEmpty();
			state.append(settled ? '1' : '0');
			if (!settled) {
				continue;
			}
			PlotKind kind = plot.type();
			settledKinds.add(kind);
			if (kind == PlotKind.HOUSE) {
				houses++;
			} else if (kind != PlotKind.PLAZA) {
				workplaces++;
				if (kind.job != null) {
					jobs.merge(kind.job, 1, Integer::sum);
				}
			}
		}
		int townLevel = levelFor(houses, workplaces, settledKinds);
		if (saved.upgrades().contains(TownUpgrade.HARBOR.id) && settledKinds.contains(PlotKind.DOCK)) {
			jobs.merge("sailor", 2, Integer::sum);
			jobs.merge("shipwright", 1, Integer::sum);
		}
		if (houses >= 2) {
			jobs.merge("elder", 1, Integer::sum);
		}
		if (houses >= 3) {
			jobs.merge("child", Math.min(3, houses / 3), Integer::sum);
		}
		TownData.TownDef def = live.def;
		def.name = saved.name();
		def.culture = saved.culture();
		def.population = Math.min(30, houses * 2);
		def.jobs = jobs;
		def.bar = settledKinds.contains(PlotKind.TAVERN);
		def.market = settledKinds.contains(PlotKind.SHOP) && saved.upgrades().contains(TownUpgrade.MARKET.id);
		def.festival = settledKinds.contains(PlotKind.PLAZA) && saved.upgrades().contains(TownUpgrade.FESTIVAL.id)
				? FESTIVALS.getOrDefault(saved.culture(), "welcome_party") : null;
		def.brawlChance = 1.0f;
		live.missing = missing;
		live.level = townLevel;

		BoundingBox box = boxFor(saved);
		String key = state.toString();
		if (live.town == null || !box.equals(live.box) || !key.equals(live.state)) {
			live.box = box;
			live.state = key;
			live.town = new Town(STRUCTURE_ID, def, level, box, live.key);
			Towns.putTown(live.town);
		}
		if (live.lastLevel >= 0 && townLevel > live.lastLevel) {
			announceLevel(level, owner, saved, townLevel);
		}
		live.lastLevel = townLevel;
	}

	private static void announceLevel(ServerLevel level, UUID owner, PlayerTowns.PlayerTown saved, int townLevel) {
		ServerPlayer player = level.getServer().getPlayerList().getPlayer(owner);
		if (player != null) {
			player.sendSystemMessage(Component.literal(saved.name() + " has grown into a " + LEVEL_NAMES[townLevel] + "!")
					.withStyle(ChatFormatting.GOLD));
			level.playSound(null, saved.bell(), SoundEvents.BELL_BLOCK, SoundSource.BLOCKS, 2.0f, 1.0f);
		}
	}

	/** What a plot still needs (empty = settled). */
	static List<String> check(ServerLevel level, PlayerTowns.Plot plot) {
		PlotKind kind = plot.type();
		int[] found = new int[kind.needs.size()];
		BlockPos from = plot.min().below(1);
		for (BlockPos pos : BlockPos.betweenClosed(from, plot.max())) {
			BlockState state = level.getBlockState(pos);
			if (state.isAir()) {
				continue;
			}
			for (int i = 0; i < found.length; i++) {
				if (found[i] < kind.needs.get(i).count() && kind.needs.get(i).matches().test(state)) {
					found[i]++;
				}
			}
		}
		List<String> missing = new ArrayList<>();
		for (int i = 0; i < found.length; i++) {
			PlotKind.Need need = kind.needs.get(i);
			if (found[i] < need.count()) {
				int left = need.count() - found[i];
				missing.add(left > 1 ? left + " more " + need.what() : need.what());
			}
		}
		return missing;
	}

	static int levelFor(int houses, int workplaces, Set<PlotKind> kinds) {
		boolean trade = kinds.contains(PlotKind.SHOP) || kinds.contains(PlotKind.TAVERN);
		boolean port = kinds.contains(PlotKind.DOCK) || kinds.contains(PlotKind.SHIPYARD);
		if (houses >= 15 && workplaces >= 10 && trade && port && kinds.contains(PlotKind.PLAZA)) {
			return 5;
		}
		if (houses >= 10 && workplaces >= 7 && trade && port) {
			return 4;
		}
		if (houses >= 6 && workplaces >= 4 && trade) {
			return 3;
		}
		if (houses >= 3 && workplaces >= 2) {
			return 2;
		}
		return houses >= 1 ? 1 : 0;
	}

	private static BoundingBox boxFor(PlayerTowns.PlayerTown saved) {
		BlockPos bell = saved.bell();
		int minX = bell.getX() - 8;
		int maxX = bell.getX() + 8;
		int minZ = bell.getZ() - 8;
		int maxZ = bell.getZ() + 8;
		int minY = bell.getY() - 4;
		int maxY = bell.getY() + 12;
		for (PlayerTowns.Plot plot : saved.plots()) {
			minX = Math.min(minX, plot.min().getX() - 3);
			maxX = Math.max(maxX, plot.max().getX() + 3);
			minZ = Math.min(minZ, plot.min().getZ() - 3);
			maxZ = Math.max(maxZ, plot.max().getZ() + 3);
			minY = Math.min(minY, plot.min().getY() - 4);
			maxY = Math.max(maxY, plot.max().getY() + 2);
		}
		return new BoundingBox(minX, minY, minZ, maxX, maxY, maxZ);
	}

	private static int rentPerDay(PlayerTowns.PlayerTown saved, Live live) {
		if (live == null || live.missing.size() != saved.plots().size()) {
			return 0;
		}
		int rent = 0;
		for (int i = 0; i < saved.plots().size(); i++) {
			if (live.missing.get(i).isEmpty()) {
				rent += saved.plots().get(i).type().rent;
			}
		}
		double boost = 1.0 + 0.25 * Math.max(0, live.level - 1);
		if (saved.upgrades().contains(TownUpgrade.LAMPLIGHTERS.id)) {
			boost *= 1.25;
		}
		return (int) Math.round(rent * boost);
	}

	/** Cheat for testing: the townsfolk pay one day's rent right now. Returns the amount. */
	static int payOneDayNow(ServerPlayer player) {
		MinecraftServer server = player.level().getServer();
		PlayerTowns.PlayerTown saved = PlayerTowns.of(server, player.getUUID());
		Live live = LIVE.get(player.getUUID().toString());
		if (saved == null || live == null) {
			return -1;
		}
		int rent = rentPerDay(saved, live);
		PlayerTowns.put(server, player.getUUID(), saved.withTreasury(Math.min(TREASURY_CAP, saved.treasury() + rent), saved.lastRentDay()));
		return rent;
	}

	private static void payRent(MinecraftServer server, UUID owner, PlayerTowns.PlayerTown saved, Live live) {
		long day = server.overworld().getGameTime() / 24000L;
		if (saved.lastRentDay() < 0) {
			PlayerTowns.put(server, owner, saved.withTreasury(saved.treasury(), day));
			return;
		}
		if (day <= saved.lastRentDay()) {
			return;
		}
		int days = (int) Math.min(3, day - saved.lastRentDay());
		int rent = rentPerDay(saved, live) * days;
		PlayerTowns.put(server, owner, saved.withTreasury(Math.min(TREASURY_CAP, saved.treasury() + rent), day));
		ServerPlayer player = server.getPlayerList().getPlayer(owner);
		if (player != null && rent > 0) {
			player.sendSystemMessage(Component.literal("[" + saved.name() + "] The townsfolk paid " + rent
					+ " Berries rent. Collect it at the town bell with the Town Planner.").withStyle(ChatFormatting.GOLD));
		}
	}

	// ---------- Planner actions ----------

	static void useOnBell(ServerPlayer player, BlockPos bell) {
		MinecraftServer server = player.level().getServer();
		UUID owner = PlayerTowns.ownerOfBell(server, bell);
		if (owner != null && owner.equals(player.getUUID())) {
			collect(player);
			report(player);
			return;
		}
		if (owner != null) {
			PlayerTowns.PlayerTown other = PlayerTowns.all(server).get(owner.toString());
			player.sendSystemMessage(Component.literal("This is the town bell of " + other.name() + ", founded by " + other.ownerName() + ".")
					.withStyle(ChatFormatting.YELLOW));
			return;
		}
		if (PlayerTowns.of(server, player.getUUID()) != null) {
			player.sendSystemMessage(Component.literal("You already founded a town. (/mytown abandon confirm gives it up.)")
					.withStyle(ChatFormatting.RED));
			return;
		}
		String problem = foundingProblem(player, bell);
		if (problem != null) {
			player.sendSystemMessage(Component.literal(problem).withStyle(ChatFormatting.RED));
			return;
		}
		String name = player.getName().getString() + "'s Town";
		PlayerTowns.put(server, player.getUUID(), new PlayerTowns.PlayerTown(player.getName().getString(), name, "east_blue", bell,
				List.of(), 0L, -1L, List.of()));
		((ServerLevel) player.level()).playSound(null, bell, SoundEvents.BELL_BLOCK, SoundSource.BLOCKS, 2.0f, 1.0f);
		player.sendSystemMessage(Component.literal("You founded " + name + "! This bell is its heart.").withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal("Mark out plots within " + PlayerTowns.RADIUS + " blocks of the bell: use the planner in the air "
				+ "to pick a kind (House, Shop, Tavern...), then click two opposite corners on the ground. "
				+ "Build what the plot needs inside it and townsfolk move in.").withStyle(ChatFormatting.YELLOW));
		player.sendSystemMessage(Component.literal("Rename it with /mytown name <name>. Pick its people's style with /mytown culture.")
				.withStyle(ChatFormatting.GRAY));
	}

	private static String foundingProblem(ServerPlayer player, BlockPos bell) {
		ServerLevel level = (ServerLevel) player.level();
		if (level != level.getServer().overworld()) {
			return "Towns can only be founded in the Overworld.";
		}
		if (Towns.at(level, bell, 32) != null) {
			return "There's already a town here. Find empty land for yours.";
		}
		for (PlayerTowns.PlayerTown other : PlayerTowns.all(level.getServer()).values()) {
			if (other.bell().distSqr(bell) < (double) PlayerTowns.SPACING * PlayerTowns.SPACING) {
				return other.name() + " is too close (towns need " + PlayerTowns.SPACING + " blocks between their bells).";
			}
		}
		return null;
	}

	static String canPlotAt(ServerPlayer player, BlockPos pos) {
		MinecraftServer server = player.level().getServer();
		PlayerTowns.PlayerTown town = PlayerTowns.of(server, player.getUUID());
		if (town == null) {
			return "Found a town first: hang or place a bell and use the Town Planner on it.";
		}
		if (player.level() != server.overworld() || !town.inRange(pos)) {
			return "That's outside " + town.name() + ". Plots must be within " + PlayerTowns.RADIUS + " blocks of the town bell.";
		}
		return null;
	}

	static void addPlot(ServerPlayer player, PlotKind kind, BlockPos a, BlockPos b) {
		String problem = canPlotAt(player, a);
		if (problem == null) {
			problem = canPlotAt(player, b);
		}
		MinecraftServer server = player.level().getServer();
		PlayerTowns.PlayerTown town = PlayerTowns.of(server, player.getUUID());
		int sizeX = Math.abs(a.getX() - b.getX()) + 1;
		int sizeZ = Math.abs(a.getZ() - b.getZ()) + 1;
		int maxSize = kind == PlotKind.PLAZA || kind == PlotKind.FARM || kind == PlotKind.SHIPYARD ? 24 : 20;
		if (problem == null && (sizeX < 2 || sizeZ < 2)) {
			problem = "A plot needs to be at least 2 by 2. Click two opposite corners.";
		}
		if (problem == null && (sizeX > maxSize || sizeZ > maxSize)) {
			problem = "That's " + sizeX + " by " + sizeZ + ". A " + kind.title + " can be at most " + maxSize + " by " + maxSize + ".";
		}
		if (problem == null && town.plots().size() >= MAX_PLOTS) {
			problem = "Your town already has " + MAX_PLOTS + " plots. Remove one first (sneak and use the planner on it).";
		}
		int floor = Math.min(a.getY(), b.getY()) + 1;
		PlayerTowns.Plot plot = new PlayerTowns.Plot(kind.name(),
				new BlockPos(Math.min(a.getX(), b.getX()), floor, Math.min(a.getZ(), b.getZ())),
				new BlockPos(Math.max(a.getX(), b.getX()), floor + 9, Math.max(a.getZ(), b.getZ())));
		if (problem == null) {
			for (PlayerTowns.Plot other : town.plots()) {
				if (other.overlaps(plot)) {
					problem = "That overlaps the " + other.type().title + " plot. Plots can't overlap.";
					break;
				}
			}
		}
		if (problem != null) {
			player.sendSystemMessage(Component.literal(problem).withStyle(ChatFormatting.RED));
			return;
		}
		List<PlayerTowns.Plot> plots = new ArrayList<>(town.plots());
		plots.add(plot);
		PlayerTowns.put(server, player.getUUID(), town.withPlots(plots));
		Live live = LIVE.get(player.getUUID().toString());
		if (live != null) {
			live.town = null; // Look it over again on the next tick.
		}
		List<String> needs = check((ServerLevel) player.level(), plot);
		player.sendSystemMessage(Component.literal(kind.title + " plot marked (" + sizeX + " by " + sizeZ + ").").withStyle(ChatFormatting.GREEN)
				.append(Component.literal(needs.isEmpty() ? " It already has everything: settled!" : " It still needs: " + String.join(", ", needs) + ".")
						.withStyle(ChatFormatting.YELLOW)));
	}

	static void removePlot(ServerPlayer player, BlockPos pos) {
		MinecraftServer server = player.level().getServer();
		PlayerTowns.PlayerTown town = PlayerTowns.of(server, player.getUUID());
		PlayerTowns.Plot plot = town == null ? null : town.plotAt(pos.above());
		if (plot == null && town != null) {
			plot = town.plotAt(pos);
		}
		if (plot == null) {
			player.sendSystemMessage(Component.literal("There's no plot of yours here.").withStyle(ChatFormatting.GRAY));
			return;
		}
		List<PlayerTowns.Plot> plots = new ArrayList<>(town.plots());
		plots.remove(plot);
		PlayerTowns.put(server, player.getUUID(), town.withPlots(plots));
		Live live = LIVE.get(player.getUUID().toString());
		if (live != null) {
			live.town = null;
		}
		player.sendSystemMessage(Component.literal(plot.type().title + " plot removed. (The blocks are still there.)").withStyle(ChatFormatting.YELLOW));
	}

	static void collect(ServerPlayer player) {
		MinecraftServer server = player.level().getServer();
		PlayerTowns.PlayerTown town = PlayerTowns.of(server, player.getUUID());
		if (town == null || town.treasury() <= 0) {
			return;
		}
		long amount = town.treasury();
		PlayerTowns.put(server, player.getUUID(), town.withTreasury(0, town.lastRentDay()));
		long left = amount;
		while (left > 0) {
			int stack = (int) Math.min(64, left);
			Parts.give(player, new ItemStack(CharacterFeature.BERRY, stack));
			left -= stack;
		}
		player.sendSystemMessage(Component.literal("Collected " + amount + " Berries of rent from the treasury.").withStyle(ChatFormatting.GOLD));
	}

	static void abandon(MinecraftServer server, UUID owner) {
		Live live = LIVE.remove(owner.toString());
		if (live != null && live.town != null) {
			for (com.onepiecemod.town.TownsfolkEntity person : Towns.residents(live.town)) {
				person.discard();
			}
			Towns.removeTown(live.key);
		}
		PlayerTowns.remove(server, owner);
	}

	// ---------- Reports ----------

	static void report(ServerPlayer player) {
		MinecraftServer server = player.level().getServer();
		PlayerTowns.PlayerTown town = PlayerTowns.of(server, player.getUUID());
		if (town == null) {
			player.sendSystemMessage(Component.literal("You haven't founded a town. Place a bell on empty land and use the Town Planner on it.")
					.withStyle(ChatFormatting.YELLOW));
			return;
		}
		Live live = LIVE.get(player.getUUID().toString());
		int level = live == null ? 0 : live.level;
		int residents = live == null || live.town == null ? 0 : Towns.residents(live.town).size();
		player.sendSystemMessage(Component.literal("=== " + town.name() + " (" + LEVEL_NAMES[level] + ") ===").withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal("Bell at " + town.bell().toShortString() + ". People: " + residents
				+ (live != null ? " of " + live.def.population : "") + ". Treasury: " + town.treasury() + " Berries, rent "
				+ rentPerDay(town, live) + " a day.").withStyle(ChatFormatting.YELLOW));
		if (live == null) {
			player.sendSystemMessage(Component.literal("Walk near the town to see how its plots are doing.").withStyle(ChatFormatting.GRAY));
		}
		for (int i = 0; i < town.plots().size(); i++) {
			PlayerTowns.Plot plot = town.plots().get(i);
			List<String> needs = live != null && i < live.missing.size() ? live.missing.get(i) : List.of("(not looked at yet)");
			int sizeX = plot.max().getX() - plot.min().getX() + 1;
			int sizeZ = plot.max().getZ() - plot.min().getZ() + 1;
			player.sendSystemMessage(Component.literal("  " + plot.type().title + " " + sizeX + "x" + sizeZ + ": ")
					.withStyle(ChatFormatting.WHITE)
					.append(needs.isEmpty() ? Component.literal("settled").withStyle(ChatFormatting.GREEN)
							: Component.literal("needs " + String.join(", ", needs)).withStyle(ChatFormatting.RED)));
		}
		player.sendSystemMessage(Component.literal(nextLevelHint(level)).withStyle(ChatFormatting.AQUA));
		MutableComponent culture = Component.literal("Style: " + town.culture() + " ").withStyle(ChatFormatting.GRAY);
		String next = CULTURES.get((CULTURES.indexOf(town.culture()) + 1) % CULTURES.size());
		culture.append(Component.literal("[next style]").withStyle(ChatFormatting.GREEN)
				.withStyle(style -> style.withClickEvent(new ClickEvent.RunCommand("/mytown culture " + next))
						.withHoverEvent(new HoverEvent.ShowText(Component.literal("Townsfolk who move in from now on dress and trade like " + next)))));
		player.sendSystemMessage(culture);
	}

	private static String nextLevelHint(int level) {
		return switch (level) {
			case 0 -> "Next: a Hamlet needs 1 settled House.";
			case 1 -> "Next: a Village needs 3 Houses and 2 workplaces (Shop, Farm, Dock...).";
			case 2 -> "Next: a Town needs 6 Houses and 4 workplaces, one of them a Shop or Tavern.";
			case 3 -> "Next: a Port Town needs 10 Houses and 7 workplaces, with a Dock or Shipyard.";
			case 4 -> "Next: a City needs 15 Houses, 10 workplaces and a Plaza.";
			default -> "Your town is a City: the biggest it gets.";
		};
	}

	// ---------- For the Builder's Ledger ----------

	public static long treasury(ServerPlayer player) {
		PlayerTowns.PlayerTown town = PlayerTowns.of(player.level().getServer(), player.getUUID());
		return town == null ? 0 : town.treasury();
	}

	public static void spendTreasury(ServerPlayer player, long amount) {
		MinecraftServer server = player.level().getServer();
		PlayerTowns.PlayerTown town = PlayerTowns.of(server, player.getUUID());
		if (town != null) {
			PlayerTowns.put(server, player.getUUID(), town.withTreasury(Math.max(0, town.treasury() - amount), town.lastRentDay()));
		}
	}

	/** The town part of the Builder's Ledger: its upgrades with [Build] buttons. */
	public static void ledgerLines(ServerPlayer player) {
		PlayerTowns.PlayerTown town = PlayerTowns.of(player.level().getServer(), player.getUUID());
		if (town == null) {
			player.sendSystemMessage(Component.literal("No town yet. A Town Planner used on a bell founds one; its rent can pay for all of this.")
					.withStyle(ChatFormatting.GRAY));
			return;
		}
		Live live = LIVE.get(player.getUUID().toString());
		int level = live == null ? 0 : live.level;
		player.sendSystemMessage(Component.literal("--- " + town.name() + " (" + LEVEL_NAMES[level] + ") ---").withStyle(ChatFormatting.GOLD));
		for (TownUpgrade upgrade : TownUpgrade.values()) {
			MutableComponent line = Component.literal(upgrade.title + "  ").withStyle(ChatFormatting.WHITE);
			String blocker = townUpgradeBlocker(town, live, upgrade);
			if (town.upgrades().contains(upgrade.id)) {
				line.append(Component.literal("done").withStyle(ChatFormatting.GREEN));
			} else if (blocker == null) {
				line.append(Component.literal("[Build: " + upgrade.cost + " Berries]").withStyle(ChatFormatting.GREEN)
						.withStyle(style -> style.withClickEvent(new ClickEvent.RunCommand("/mytown upgrade " + upgrade.id))
								.withHoverEvent(new HoverEvent.ShowText(Component.literal(upgrade.effect)))));
			} else {
				line.append(Component.literal(upgrade.cost + " Berries, " + blocker).withStyle(ChatFormatting.DARK_GRAY)
						.withStyle(style -> style.withHoverEvent(new HoverEvent.ShowText(Component.literal(upgrade.effect)))));
			}
			player.sendSystemMessage(line);
		}
	}

	private static String townUpgradeBlocker(PlayerTowns.PlayerTown town, Live live, TownUpgrade upgrade) {
		int level = live == null ? 0 : live.level;
		if (level < upgrade.townLevel) {
			return "needs a " + LEVEL_NAMES[upgrade.townLevel];
		}
		if (upgrade.needsPlot != null && !hasSettled(town, live, upgrade.needsPlot)) {
			return "needs a settled " + upgrade.needsPlot.title;
		}
		return null;
	}

	private static boolean hasSettled(PlayerTowns.PlayerTown town, Live live, PlotKind kind) {
		if (live == null || live.missing.size() != town.plots().size()) {
			return false;
		}
		for (int i = 0; i < town.plots().size(); i++) {
			if (town.plots().get(i).type() == kind && live.missing.get(i).isEmpty()) {
				return true;
			}
		}
		return false;
	}

	/** /mytown upgrade <id>. */
	static String buyUpgrade(ServerPlayer player, String id) {
		MinecraftServer server = player.level().getServer();
		PlayerTowns.PlayerTown town = PlayerTowns.of(server, player.getUUID());
		TownUpgrade upgrade = TownUpgrade.byId(id);
		if (town == null || upgrade == null) {
			return town == null ? "You haven't founded a town." : "There's no town upgrade called " + id + ".";
		}
		if (town.upgrades().contains(upgrade.id)) {
			return town.name() + " already has the " + upgrade.title + ".";
		}
		String blocker = townUpgradeBlocker(town, LIVE.get(player.getUUID().toString()), upgrade);
		if (blocker != null) {
			return upgrade.title + ": " + blocker + ".";
		}
		int carried = Parts.count(player, CharacterFeature.BERRY);
		if (carried + town.treasury() < upgrade.cost) {
			return upgrade.title + " costs " + upgrade.cost + " Berries (you have " + carried + ", the treasury " + town.treasury() + ").";
		}
		long fromTreasury = Math.min(town.treasury(), upgrade.cost);
		Parts.take(player, CharacterFeature.BERRY, (int) (upgrade.cost - fromTreasury));
		PlayerTowns.put(server, player.getUUID(), town.withTreasury(town.treasury() - fromTreasury, town.lastRentDay()).withUpgrade(upgrade.id));
		Live live = LIVE.get(player.getUUID().toString());
		if (live != null) {
			live.town = null;
		}
		player.sendSystemMessage(Component.literal(town.name() + " built the " + upgrade.title + "! " + upgrade.effect).withStyle(ChatFormatting.GREEN));
		return null;
	}

	// ---------- Plot outlines while holding the planner ----------

	/** True while this player sees town plot outlines (plan book ghosts wait until they put the planner away). */
	public static boolean drawingFor(ServerPlayer player) {
		return DRAWING.contains(player.getUUID());
	}

	private static boolean holdsPlanner(ServerPlayer player) {
		return player.getMainHandItem().is(TOWN_PLANNER) || player.getOffhandItem().is(TOWN_PLANNER);
	}

	private static void drawOutlines(MinecraftServer server) {
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			PlayerTowns.PlayerTown town = holdsPlanner(player) && player.level() == server.overworld()
					? PlayerTowns.of(server, player.getUUID()) : null;
			if (town == null || town.bell().distSqr(player.blockPosition()) > 120 * 120) {
				if (DRAWING.remove(player.getUUID()) && !PlanOutlines.resend(player)) {
					ServerPlayNetworking.send(player, GhostPayload.hide());
				}
				continue;
			}
			Live live = LIVE.get(player.getUUID().toString());
			List<GhostPlan.Ghost> ghosts = new ArrayList<>();
			for (int i = 0; i < town.plots().size() && ghosts.size() < 1000; i++) {
				PlayerTowns.Plot plot = town.plots().get(i);
				boolean settled = live != null && i < live.missing.size() && live.missing.get(i).isEmpty();
				outline(ghosts, plot, settled ? Blocks.GOLD_BLOCK.defaultBlockState() : Parts.block(plot.type().outline, Blocks.GLASS), settled);
			}
			ItemStack held = player.getMainHandItem().is(TOWN_PLANNER) ? player.getMainHandItem() : player.getOffhandItem();
			BlockPos corner = TownPlannerItem.corner(held);
			if (corner != null) {
				ghosts.add(new GhostPlan.Ghost(corner.above(), Parts.block("minecraft:lime_stained_glass", Blocks.GLASS)));
			}
			ghosts.add(new GhostPlan.Ghost(town.bell().above(), Blocks.GOLD_BLOCK.defaultBlockState()));
			ServerPlayNetworking.send(player, GhostPayload.of(ghosts));
			DRAWING.add(player.getUUID());
		}
	}

	/** The edge of a plot at floor height (just the corners once it's settled). */
	private static void outline(List<GhostPlan.Ghost> ghosts, PlayerTowns.Plot plot, BlockState state, boolean cornersOnly) {
		int y = plot.min().getY();
		int x0 = plot.min().getX();
		int x1 = plot.max().getX();
		int z0 = plot.min().getZ();
		int z1 = plot.max().getZ();
		for (int x = x0; x <= x1; x++) {
			for (int z = z0; z <= z1; z++) {
				boolean edge = x == x0 || x == x1 || z == z0 || z == z1;
				boolean corner = (x == x0 || x == x1) && (z == z0 || z == z1);
				if (corner || (edge && !cornersOnly)) {
					ghosts.add(new GhostPlan.Ghost(new BlockPos(x, y, z), state));
				}
			}
		}
	}
}
