package com.onepiecemod.season;

import java.util.List;
import java.util.Map;
import java.util.Set;

import org.jetbrains.annotations.Nullable;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BiomeTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.state.BlockState;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.farm.IslandCropBlock;
import com.onepiecemod.island.Islands;
import com.onepiecemod.sea.CalmBelt;
import com.onepiecemod.weather.SeaEventType;

/**
 * Seasons. The world turns spring, summer, autumn, winter, one season every DAYS_PER_SEASON in-game days
 * (sleeping skips days, so it skips season time too). What it changes:
 *
 *  - Crops (vanilla ones and the island crops): grow faster in spring, slowly outdoors in winter. A greenhouse beats
 *    winter: a crop with a roof over it, or lit by lanterns or torches (block light 12+), grows at nearly full speed.
 *    Each island crop also has a favourite season when it grows half again as fast (Frost Turnips love the winter).
 *  - Harvests: in autumn, a fully grown crop sometimes drops one extra piece of produce.
 *  - The sea: storm season in autumn (more sea events, and the Great Cyclone), blizzards and hail in winter,
 *    heat waves and waterspouts in summer, calmer seas in spring. SeaEvents asks seaChance and seasonalPick.
 *
 * In the Grand Line every island keeps its own season. Winter Islands (Drum) are always in winter, Summer Islands
 * (Alabasta) always in summer, the sky and undersea islands always in spring, and the rest are each shifted by a
 * fixed number of seasons from the world's, so the next island along may be in a different season.
 *
 * Players: /season. Operators: /season set <season>, /season next.
 */
public class Seasons {
	// ---- Tune these ----
	public static final int DAYS_PER_SEASON = 5;
	private static final float SPRING_GROWTH = 1.25f;
	private static final float AUTUMN_GROWTH = 0.9f;
	private static final float WINTER_GROWTH = 0.3f;
	private static final float GREENHOUSE_GROWTH = 0.9f;
	private static final float FAVOURITE_BONUS = 1.5f;
	private static final int GREENHOUSE_LIGHT = 12;
	private static final float AUTUMN_EXTRA_HARVEST = 0.35f;

	/** Saved on the Overworld: how many days the calendar was moved by /season set. */
	public static final AttachmentType<Integer> SHIFT = AttachmentRegistry.create(
			OnePieceMod.id("season_shift"),
			builder -> builder.persistent(Codec.INT)
	);

	/** Islands that are always in spring: the sky islands and the islands under the sea. */
	private static final Set<String> EVERSPRING = Set.of("onepiece:skypiea", "onepiece:fishman_reef", "onepiece:ryugu",
			"onepiece:weatheria", "onepiece:whole_cake", "onepiece:cacao_island");

	/** Each island crop's favourite season. */
	private static final Map<String, Season> FAVOURITE = Map.ofEntries(
			Map.entry("east_blue_cabbage", Season.SPRING), Map.entry("cloud_wheat", Season.SPRING),
			Map.entry("sea_grape", Season.SPRING), Map.entry("mink_tea", Season.SPRING),
			Map.entry("sand_melon", Season.SUMMER), Map.entry("snake_pepper", Season.SUMMER),
			Map.entry("dressrosa_tomato", Season.SUMMER), Map.entry("jungle_yam", Season.SUMMER),
			Map.entry("wano_rice", Season.AUTUMN), Map.entry("kibi_millet", Season.AUTUMN),
			Map.entry("elbaph_barley", Season.AUTUMN), Map.entry("ghost_pumpkin", Season.AUTUMN),
			Map.entry("totland_cacao", Season.AUTUMN),
			Map.entry("frost_turnip", Season.WINTER));

	/** The season somewhere, and why. fixed = this island never changes season. */
	public record Local(Season season, boolean fixed, String why) {
	}

	private static Season lastWorldSeason;

	public static void initialize() {
		SHIFT.identifier(); // Load the attachment.
		ServerTickEvents.END_SERVER_TICK.register(Seasons::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> lastWorldSeason = null);
		PlayerBlockBreakEvents.AFTER.register((level, player, pos, state, blockEntity) -> {
			if (level instanceof ServerLevel serverLevel) {
				autumnHarvest(serverLevel, pos, state);
			}
		});
		registerCommands();
	}

	// ---- The calendar ----

	/** Today's day number, counting the /season set shift. */
	public static long day(Level level) {
		int shift = level instanceof ServerLevel server ? server.getServer().overworld().getAttachedOrElse(SHIFT, 0) : 0;
		return Math.max(0, level.getOverworldClockTime() / 24000L + shift);
	}

	/** The world's own season (the East Blue's, and the base the Grand Line islands shift from). */
	public static Season world(Level level) {
		return Season.values()[(int) ((day(level) / DAYS_PER_SEASON) % 4)];
	}

	/** Whole days until the world's season changes (1 = it changes tonight). */
	public static int daysLeft(Level level) {
		return (int) (DAYS_PER_SEASON - day(level) % DAYS_PER_SEASON);
	}

	/** The season at a spot, or null where there are none (the Nether, the End, the mod's other dimensions). */
	@Nullable
	public static Local at(Level level, BlockPos pos) {
		if (level.dimension() != Level.OVERWORLD) {
			return null;
		}
		Holder<Biome> holder = level.getBiome(pos);
		String biome = holder.unwrapKey().map(key -> key.identifier().toString()).orElse("");
		Islands.Island island = Islands.byBiome(biome);
		if (island != null && island.climate() == Islands.Climate.WINTER) {
			return new Local(Season.WINTER, true, island.name + " is a Winter Island: it's always winter here.");
		}
		if (island != null && island.climate() == Islands.Climate.SUMMER) {
			return new Local(Season.SUMMER, true, island.name + " is a Summer Island: it's always summer here.");
		}
		if (EVERSPRING.contains(biome)) {
			return new Local(Season.SPRING, true, (island != null ? island.name : "This island") + " is always in spring.");
		}
		if (island == null && !holder.is(BiomeTags.IS_OCEAN) && !holder.is(BiomeTags.IS_RIVER) && holder.value().getBaseTemperature() < 0.1f) {
			return new Local(Season.WINTER, true, "These snowy lands stay frozen all year.");
		}
		Season world = world(level);
		if (island != null && CalmBelt.seaByDistance(pos).grandLine()) {
			// A fixed shift per island, from its name, so the same island is always in step with itself.
			int shift = Math.floorMod(biome.hashCode(), 4);
			Season here = Season.values()[(world.ordinal() + shift) % 4];
			return new Local(here, false, island.name + " has its own seasons, like every Grand Line island.");
		}
		return new Local(world, false, "The seas here follow the world's seasons.");
	}

	/** Just the season, or null outside the Overworld. */
	@Nullable
	public static Season seasonAt(Level level, BlockPos pos) {
		Local local = at(level, pos);
		return local == null ? null : local.season();
	}

	// ---- Crops ----

	/**
	 * How fast a crop grows here this season: 1 = normal, 0.3 = a third as fast, 1.5 = half again as fast.
	 * cropId is the island crop's id, or null for a vanilla crop.
	 */
	public static float growth(ServerLevel level, BlockPos pos, @Nullable String cropId) {
		Season season = seasonAt(level, pos);
		if (season == null) {
			return 1;
		}
		float factor = switch (season) {
			case SPRING -> SPRING_GROWTH;
			case SUMMER -> 1.0f;
			case AUTUMN -> AUTUMN_GROWTH;
			case WINTER -> WINTER_GROWTH;
		};
		if (cropId != null && FAVOURITE.get(cropId) == season) {
			factor = Math.max(factor, 1.0f) * FAVOURITE_BONUS;
		}
		if (factor < GREENHOUSE_GROWTH && greenhouse(level, pos)) {
			factor = GREENHOUSE_GROWTH;
		}
		return factor;
	}

	/** A roof overhead, or warm light from lanterns and torches. */
	public static boolean greenhouse(ServerLevel level, BlockPos pos) {
		return !level.canSeeSky(pos) || level.getBrightness(LightLayer.BLOCK, pos) >= GREENHOUSE_LIGHT;
	}

	@Nullable
	public static Season favourite(String cropId) {
		return FAVOURITE.get(cropId);
	}

	/**
	 * Called once per random tick of a crop. Returns how many growth ticks it should really get: 0 (skipped),
	 * 1 (normal) or 2 (a bonus one). Random rounding keeps the average right.
	 */
	public static int growthTicks(ServerLevel level, BlockPos pos, @Nullable String cropId, RandomSource random) {
		float factor = growth(level, pos, cropId);
		if (factor < 1) {
			return random.nextFloat() < factor ? 1 : 0;
		}
		return random.nextFloat() < factor - 1 ? 2 : 1;
	}

	private static void autumnHarvest(ServerLevel level, BlockPos pos, BlockState state) {
		if (!(state.getBlock() instanceof CropBlock crop) || !crop.isMaxAge(state) || seasonAt(level, pos) != Season.AUTUMN
				|| level.getRandom().nextFloat() >= AUTUMN_EXTRA_HARVEST) {
			return;
		}
		List<ItemStack> drops = Block.getDrops(state, level, pos, null);
		if (!drops.isEmpty() && !drops.get(0).isEmpty()) {
			Block.popResource(level, pos, drops.get(0).copyWithCount(1));
		}
	}

	// ---- Sea weather (asked by weather.SeaEvents) ----

	/** How much more (or less) often sea events happen in this season. */
	public static float seaChance(@Nullable Season season) {
		if (season == null) {
			return 1;
		}
		return switch (season) {
			case SPRING -> 0.8f;
			case SUMMER -> 1.0f;
			case AUTUMN -> 1.4f;
			case WINTER -> 1.1f;
		};
	}

	/** Sometimes the season picks the event instead of the usual table. Null = use the usual table. */
	@Nullable
	public static SeaEventType seasonalPick(@Nullable Season season, RandomSource random, boolean newWorld) {
		if (season == null || random.nextFloat() >= 0.35f) {
			return null;
		}
		return switch (season) {
			case SPRING -> null;
			case SUMMER -> random.nextBoolean() ? SeaEventType.HEAT_WAVE : SeaEventType.WATERSPOUT;
			case AUTUMN -> random.nextFloat() < (newWorld ? 0.4f : 0.25f) ? SeaEventType.CYCLONE : SeaEventType.STORM;
			case WINTER -> random.nextInt(3) == 0 ? SeaEventType.HAILSTORM : SeaEventType.BLIZZARD;
		};
	}

	// ---- Telling players ----

	private static void tick(MinecraftServer server) {
		if (server.getTickCount() % 100 != 0) {
			return;
		}
		Season now = world(server.overworld());
		if (lastWorldSeason != null && lastWorldSeason != now) {
			announce(server, now);
		}
		lastWorldSeason = now;
	}

	private static void announce(MinecraftServer server, Season season) {
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			player.sendSystemMessage(Component.literal("The seasons turn. " + season.blurb).withStyle(season.color));
			Local here = at(player.level(), player.blockPosition());
			if (here != null && here.season() != season) {
				player.sendSystemMessage(Component.literal("(Here it's still " + here.season().title.toLowerCase() + ": " + here.why() + ")")
						.withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
			}
			player.connection.send(new ClientboundSetActionBarTextPacket(Component.literal(season.title + " has come").withStyle(season.color, ChatFormatting.BOLD)));
		}
		com.onepiecemod.worldevent.WorldNews.remember(server, season.title + " has come to the seas.");
	}

	/** A short label for titles and the HUD, like "Autumn" or "Winter (always)". */
	public static Component label(Level level, BlockPos pos) {
		Local local = at(level, pos);
		if (local == null) {
			return Component.empty();
		}
		return Component.literal(local.season().title + (local.fixed() ? " (always)" : "")).withStyle(local.season().color);
	}

	private static void registerCommands() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("season")
						.executes(context -> {
							ServerPlayer player = context.getSource().getPlayerOrException();
							describe(player);
							return 1;
						})
						.then(Commands.literal("set")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.argument("season", StringArgumentType.word())
										.suggests((context, builder) -> SharedSuggestionProvider.suggest(
												java.util.Arrays.stream(Season.values()).map(s -> s.id), builder))
										.executes(context -> {
											Season wanted = Season.byId(StringArgumentType.getString(context, "season"));
											if (wanted == null) {
												context.getSource().sendFailure(Component.literal("Seasons: spring, summer, autumn, winter"));
												return 0;
											}
											set(context.getSource().getServer(), wanted);
											context.getSource().sendSuccess(() -> Component.literal("The world's season is now " + wanted.title + ".")
													.withStyle(wanted.color), true);
											return 1;
										})))
						.then(Commands.literal("next")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.executes(context -> {
									Season next = world(context.getSource().getServer().overworld()).next();
									set(context.getSource().getServer(), next);
									context.getSource().sendSuccess(() -> Component.literal("The world's season is now " + next.title + ".")
											.withStyle(next.color), true);
									return 1;
								}))));
	}

	/** Moves the calendar so the world's season is this one, at its first day. */
	public static void set(MinecraftServer server, Season wanted) {
		ServerLevel overworld = server.overworld();
		long realDay = Math.max(0, overworld.getOverworldClockTime() / 24000L);
		long year = DAYS_PER_SEASON * 4L;
		long target = wanted.ordinal() * (long) DAYS_PER_SEASON;
		int shift = (int) Math.floorMod(target - realDay, year);
		overworld.setAttached(SHIFT, shift);
	}

	private static void describe(ServerPlayer player) {
		Level level = player.level();
		Season world = world(level);
		int left = daysLeft(level);
		player.sendSystemMessage(Component.literal("World season: ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(world.title).withStyle(world.color, ChatFormatting.BOLD))
				.append(Component.literal(" (" + world.next().title.toLowerCase() + " in " + left + (left == 1 ? " day)" : " days)"))
						.withStyle(ChatFormatting.GRAY)));
		Local here = at(level, player.blockPosition());
		if (here == null) {
			player.sendSystemMessage(Component.literal("There are no seasons in this world.").withStyle(ChatFormatting.GRAY));
			return;
		}
		player.sendSystemMessage(Component.literal("Here: ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(here.season().title).withStyle(here.season().color, ChatFormatting.BOLD))
				.append(Component.literal(". " + here.why()).withStyle(ChatFormatting.GRAY)));
		player.sendSystemMessage(Component.literal(here.season().blurb).withStyle(here.season().color));

		// What a crop planted right here would do.
		ServerLevel server = (ServerLevel) level;
		BlockPos at = player.blockPosition();
		int percent = Math.round(growth(server, at, null) * 100);
		String greenhouse = here.season() == Season.WINTER
				? (greenhouse(server, at) ? " You're in a greenhouse, so the cold doesn't reach your crops." : " Build a roof or light lanterns around crops to keep them growing.")
				: "";
		player.sendSystemMessage(Component.literal("Crops here grow at " + percent + "% speed." + greenhouse).withStyle(ChatFormatting.GREEN));
		BlockState below = level.getBlockState(at);
		if (below.getBlock() instanceof IslandCropBlock crop) {
			Season favourite = favourite(crop.crop.id);
			player.sendSystemMessage(Component.literal(crop.crop.title + " grows at " + Math.round(growth(server, at, crop.crop.id) * 100)
					+ "% here" + (favourite != null ? " (it loves " + favourite.title.toLowerCase() + ")." : ".")).withStyle(ChatFormatting.GREEN));
		}
		StringBuilder loves = new StringBuilder();
		for (Map.Entry<String, Season> entry : FAVOURITE.entrySet()) {
			if (entry.getValue() == here.season()) {
				com.onepiecemod.farm.IslandCrop crop = com.onepiecemod.farm.IslandCrop.byId(entry.getKey());
				if (crop != null) {
					loves.append(loves.isEmpty() ? "" : ", ").append(crop.title);
				}
			}
		}
		if (!loves.isEmpty()) {
			player.sendSystemMessage(Component.literal("In season now (grow 50% faster): " + loves).withStyle(ChatFormatting.DARK_GREEN));
		}
	}
}
