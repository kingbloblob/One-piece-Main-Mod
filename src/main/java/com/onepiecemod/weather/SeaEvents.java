package com.onepiecemod.weather;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CopyOnWriteArrayList;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;

import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.sea.CalmBelt;
import com.onepiecemod.sea.SeaKingSpawner;
import com.onepiecemod.ship.ShipEntity;

/**
 * Starts, runs and ends the sea events. Every 30 seconds each player out at sea has a small chance
 * for something to happen near them. After an event, that player gets a few calm minutes.
 *
 * Events only happen in the Overworld, and they are forgotten if the server restarts.
 */
public class SeaEvents {
	// ---- Tune these to make events more or less common ----
	private static final int CHECK_EVERY_TICKS = 20 * 30;
	/** After an event, how long until the next one can start near the same player. */
	private static final int CALM_TICKS_AFTER_EVENT = 20 * 60 * 8;
	private static final float GRAND_LINE_CHANCE = 0.06f;
	private static final float NEW_WORLD_CHANCE = 0.09f;
	/** Chance the weather flips the moment you sail into the Grand Line or the New World (the first time each session it always does). */
	private static final float ENTRY_SWING_CHANCE = 0.35f;
	private static final float CALM_BELT_AMBUSH_CHANCE = 0.08f;
	private static final float BLUE_SEA_STORM_CHANCE = 0.015f;
	private static final float AQUA_LAGUNA_CHANCE = 0.007f;
	/** How long the warning lasts before the event starts, in seconds. A Navigator in your crew spots it sooner. */
	private static final int WARNING_SECONDS = 8;
	private static final int NAVIGATOR_WARNING_SECONDS = 30;
	private static final int AQUA_LAGUNA_WARNING_SECONDS = 45;
	private static final int MAX_EVENTS = 6;

	/** Every event happening right now, on the server. */
	public static final List<SeaEvent> ACTIVE = new CopyOnWriteArrayList<>();
	private static final Map<UUID, Long> CALM_UNTIL = new HashMap<>();
	/** The last sea each player was out on, to notice them sailing into the Grand Line. */
	private static final Map<UUID, CalmBelt.Sea> LAST_SEA = new HashMap<>();
	/** Players who already got their "welcome to the Grand Line" weather this session, per sea. */
	private static final Map<UUID, java.util.Set<CalmBelt.Sea>> WELCOMED = new HashMap<>();
	private static int nextId = 1;

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(SeaEvents::tick);
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> SeaEventSync.send(handler.getPlayer(), ACTIVE));
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
			UUID id = handler.getPlayer().getUUID();
			CALM_UNTIL.remove(id);
			LAST_SEA.remove(id);
			WELCOMED.remove(id);
		});
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			ACTIVE.clear();
			CALM_UNTIL.clear();
			LAST_SEA.clear();
			WELCOMED.clear();
		});
	}

	private static void tick(MinecraftServer server) {
		ServerLevel level = server.overworld();
		long time = level.getGameTime();
		boolean changed = false;

		for (SeaEvent event : ACTIVE) {
			if (time >= event.endTime) {
				ACTIVE.remove(event);
				finish(level, event);
				changed = true;
			} else if (!event.started && time >= event.startTime) {
				event.started = true;
				begin(level, event);
			}
		}

		for (SeaEvent event : ACTIVE) {
			tellNearbyPlayers(level, event, time);
			if (event.isActive(time)) {
				SeaEventEffects.tick(level, event, time);
			} else {
				SeaEventEffects.warningTick(level, event, time);
			}
		}

		if (server.getTickCount() % 20 == 0) {
			for (ServerPlayer player : level.players()) {
				if (checkGrandLineEntry(level, player)) {
					changed = true;
				}
			}
		}

		if (server.getTickCount() % CHECK_EVERY_TICKS == 0) {
			for (ServerPlayer player : level.players()) {
				if (rollForEvent(level, player)) {
					changed = true;
				}
			}
		}

		if (changed || server.getTickCount() % 40 == 0) {
			syncAll(server);
		}
	}

	public static void syncAll(MinecraftServer server) {
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			SeaEventSync.send(player, player.level().dimension() == Level.OVERWORLD ? ACTIVE : List.of());
		}
	}

	// ---- Picking what happens ----

	private static boolean rollForEvent(ServerLevel level, ServerPlayer player) {
		if (player.isSpectator() || level.getGameTime() < CALM_UNTIL.getOrDefault(player.getUUID(), 0L)
				|| ACTIVE.size() >= MAX_EVENTS || eventNear(player.getX(), player.getZ(), 40) != null) {
			return false;
		}
		RandomSource random = level.getRandom();
		CalmBelt.Sea sea = CalmBelt.seaAt(level, player.blockPosition());
		SeaEventType type = null;
		if (sea != null && sea.grandLine()) {
			if (random.nextFloat() < (sea == CalmBelt.Sea.NEW_WORLD ? NEW_WORLD_CHANCE : GRAND_LINE_CHANCE)) {
				type = pickGrandLineEvent(level, random);
			}
		} else if (sea == CalmBelt.Sea.CALM_BELT) {
			boolean atSea = ShipEntity.aboard(player) != null || player.isInWater();
			if (atSea && level.getDifficulty() != Difficulty.PEACEFUL && random.nextFloat() < CALM_BELT_AMBUSH_CHANCE) {
				type = SeaEventType.CALM_BELT_AMBUSH;
			}
		} else if (sea == CalmBelt.Sea.BLUE) {
			if (random.nextFloat() < BLUE_SEA_STORM_CHANCE) {
				// The calm East Blue still has its rough days.
				int roll = random.nextInt(10);
				type = roll < 6 ? SeaEventType.STORM : roll < 8 ? SeaEventType.HAILSTORM : SeaEventType.ROGUE_WAVE;
			}
		} else if (CalmBelt.seaByDistance(player.blockPosition()).grandLine() && random.nextFloat() < AQUA_LAGUNA_CHANCE) {
			// On land in the Grand Line: maybe Aqua Laguna, if this is a beach.
			type = SeaEventType.AQUA_LAGUNA;
		}
		return type != null && start(level, type, player) == null;
	}

	/**
	 * The Grand Line's weather is famous for changing the moment you arrive. When a player sails out of the Calm Belt
	 * (or the East Blue) into the Grand Line, or from the Grand Line into the New World, the sky may flip right away.
	 */
	private static boolean checkGrandLineEntry(ServerLevel level, ServerPlayer player) {
		CalmBelt.Sea sea = CalmBelt.seaAt(level, player.blockPosition());
		if (sea == null) {
			return false; // On land: remember the last sea we were on.
		}
		CalmBelt.Sea before = LAST_SEA.put(player.getUUID(), sea);
		boolean entered = before != null && before != sea && sea.grandLine()
				&& (!before.grandLine() || sea == CalmBelt.Sea.NEW_WORLD);
		if (!entered || player.isSpectator() || ACTIVE.size() >= MAX_EVENTS || eventNear(player.getX(), player.getZ(), 40) != null) {
			return false;
		}
		java.util.Set<CalmBelt.Sea> welcomed = WELCOMED.computeIfAbsent(player.getUUID(), id -> java.util.EnumSet.noneOf(CalmBelt.Sea.class));
		RandomSource random = level.getRandom();
		if (!welcomed.add(sea) && random.nextFloat() >= ENTRY_SWING_CHANCE) {
			return false;
		}
		int roll = random.nextInt(100);
		SeaEventType type = roll < 50 ? SeaEventType.STORM : roll < 75 ? SeaEventType.BLIZZARD : SeaEventType.HEAT_WAVE;
		if (start(level, type, player) != null) {
			return false;
		}
		player.sendSystemMessage(Component.literal(sea == CalmBelt.Sea.NEW_WORLD
				? "The sky changes in an instant. The New World's weather makes the Grand Line look gentle..."
				: "The sky changes in an instant. Welcome to the Grand Line, where the weather never makes sense!")
				.withStyle(ChatFormatting.GOLD, ChatFormatting.ITALIC));
		return true;
	}

	private static SeaEventType pickGrandLineEvent(ServerLevel level, RandomSource random) {
		int roll = random.nextInt(100);
		if (roll < 28) {
			return SeaEventType.STORM;
		}
		if (roll < 46) {
			return SeaEventType.WHIRLPOOL;
		}
		if (roll < 55) {
			return SeaEventType.BLIZZARD;
		}
		if (roll < 64) {
			return SeaEventType.HEAT_WAVE;
		}
		if (roll < 74) {
			return SeaEventType.WATERSPOUT;
		}
		if (roll < 83) {
			return SeaEventType.ROGUE_WAVE;
		}
		if (roll < 91) {
			return SeaEventType.HAILSTORM;
		}
		// The Florian Triangle's mist only rolls in at night.
		return level.isBrightOutside() ? SeaEventType.STORM : SeaEventType.FLORIAN_MIST;
	}

	/**
	 * Starts an event near a player. Returns null if it worked, or the reason it couldn't
	 * (for example "no deep water nearby"). The /seaevent command uses this too.
	 */
	public static String start(ServerLevel level, SeaEventType type, ServerPlayer player) {
		return start(level, type, player, null);
	}

	/** Like start, but a rogue wave or waterspout comes from this direction (radians, the way it travels). */
	public static String start(ServerLevel level, SeaEventType type, ServerPlayer player, Float heading) {
		if (level.dimension() != Level.OVERWORLD) {
			return "Sea events only happen in the Overworld.";
		}
		RandomSource random = level.getRandom();
		double x = player.getX();
		double z = player.getZ();
		float angle = random.nextFloat() * Mth.TWO_PI;

		switch (type) {
			case WATERSPOUT, ROGUE_WAVE -> {
				if (CalmBelt.seaAt(level, player.blockPosition()) == null) {
					return type == SeaEventType.WATERSPOUT ? "Waterspouts only form out at sea." : "Rogue waves only happen out at sea.";
				}
				if (heading != null) {
					angle = heading;
				}
				if (type == SeaEventType.WATERSPOUT) {
					// The funnel's path passes close to the player, not always right over them.
					x += (random.nextDouble() - 0.5) * 24;
					z += (random.nextDouble() - 0.5) * 24;
				}
			}
			case STORM, BLIZZARD, HEAT_WAVE, HAILSTORM -> {
				// Somewhere around the player, so they're inside it but not always in the middle.
				x += (random.nextDouble() - 0.5) * 60;
				z += (random.nextDouble() - 0.5) * 60;
			}
			case WHIRLPOOL -> {
				BlockPos spot = findWhirlpoolSpot(level, player, random);
				if (spot == null) {
					return "There isn't enough deep open water nearby for a whirlpool.";
				}
				x = spot.getX() + 0.5;
				z = spot.getZ() + 0.5;
			}
			case AQUA_LAGUNA -> {
				Vec3 fromSea = directionFromSea(level, player.blockPosition());
				if (fromSea == null) {
					return "Aqua Laguna needs a beach: stand on land close to the ocean.";
				}
				if (player.getY() > level.getSeaLevel() + 14) {
					return "You're already up high, safe from Aqua Laguna. Stand near the shore.";
				}
				angle = (float) Math.atan2(fromSea.z, fromSea.x);
			}
			default -> {
			}
		}

		CrewmateEntity navigator = findNavigator(level, player);
		int warning = type == SeaEventType.AQUA_LAGUNA ? AQUA_LAGUNA_WARNING_SECONDS
				: type == SeaEventType.ROGUE_WAVE ? (navigator != null ? 20 : 10)
				: navigator != null ? NAVIGATOR_WARNING_SECONDS : WARNING_SECONDS;
		long now = level.getGameTime();
		long startTime = now + warning * 20L;
		long endTime = type == SeaEventType.AQUA_LAGUNA || type == SeaEventType.ROGUE_WAVE
				? startTime + (long) ((type.radius * 2 - SeaEvent.WAVE_START) / SeaEvent.WAVE_SPEED)
				: startTime + type.seconds * 20L;
		SeaEvent event = new SeaEvent(nextId++, type, x, z, type.radius, startTime, endTime, angle);
		ACTIVE.add(event);

		if (navigator != null) {
			navigator.tellCaptain(navigatorWarning(event));
		}
		// Everyone nearby gets some calm time after this one.
		for (ServerPlayer nearby : level.players()) {
			if (event.distance(nearby.getX(), nearby.getZ()) < type.radius + 60) {
				CALM_UNTIL.put(nearby.getUUID(), endTime + CALM_TICKS_AFTER_EVENT);
			}
		}
		syncAll(level.getServer());
		return null;
	}

	/** Ends every event right away (the /seaevent stop command). */
	public static int stopAll(ServerLevel level) {
		int count = ACTIVE.size();
		for (SeaEvent event : ACTIVE) {
			ACTIVE.remove(event);
			finish(level, event);
		}
		syncAll(level.getServer());
		return count;
	}

	/** The first event within this many blocks of its edge, or null. */
	public static SeaEvent eventNear(double x, double z, double extra) {
		for (SeaEvent event : ACTIVE) {
			if (event.distance(x, z) <= event.radius + extra) {
				return event;
			}
		}
		return null;
	}

	// ---- Starting and ending ----

	private static void begin(ServerLevel level, SeaEvent event) {
		// A storm's rain and dark sky are drawn only near it, on each player's own game (weather/client/LocalStorm).
		// The world's weather is left alone, so on a server friends far away don't get a storm too.
		SeaEventEffects.begin(level, event);
	}

	private static void finish(ServerLevel level, SeaEvent event) {
		if (event.started) {
			SeaEventEffects.finish(level, event);
			for (ServerPlayer player : level.players()) {
				if (event.distance(player.getX(), player.getZ()) <= event.radius + 30) {
					player.sendSystemMessage(Component.literal(event.type.endMessage).withStyle(event.type.color));
				}
			}
		}
	}

	private static void tellNearbyPlayers(ServerLevel level, SeaEvent event, long time) {
		boolean active = event.isActive(time);
		for (ServerPlayer player : level.players()) {
			if (event.distance(player.getX(), player.getZ()) > event.radius + 30) {
				continue;
			}
			UUID id = player.getUUID();
			if (!active && event.told.add(id)) {
				player.sendSystemMessage(Component.literal(event.type.warning).withStyle(event.type.color, ChatFormatting.ITALIC));
			}
			if (active && event.toldStart.add(id)) {
				event.told.add(id);
				player.sendSystemMessage(Component.literal(event.type.startMessage).withStyle(event.type.color, ChatFormatting.BOLD));
				player.connection.send(new ClientboundSetActionBarTextPacket(
						Component.literal(event.type.title + "!").withStyle(event.type.color, ChatFormatting.BOLD)));
			}
			if (!active && event.type == SeaEventType.AQUA_LAGUNA && time % 20 == 0) {
				long seconds = (event.startTime - time) / 20;
				player.connection.send(new ClientboundSetActionBarTextPacket(
						Component.literal("Aqua Laguna in " + seconds + "s! Climb up high!").withStyle(ChatFormatting.BLUE, ChatFormatting.BOLD)));
			}
		}
	}

	// ---- Helpers ----

	/** A Navigator from this player's crew within 48 blocks, or null. They spot trouble early, like Nami. */
	private static CrewmateEntity findNavigator(ServerLevel level, ServerPlayer player) {
		List<CrewmateEntity> found = level.getEntitiesOfClass(CrewmateEntity.class, player.getBoundingBox().inflate(48),
				crewmate -> crewmate.getRole() == CrewRole.NAVIGATOR && player.getUUID().equals(crewmate.getCaptainId()));
		return found.isEmpty() ? null : found.get(0);
	}

	private static String navigatorWarning(SeaEvent event) {
		String from = compass(event.angle + Mth.PI);
		return switch (event.type) {
			case STORM -> "Captain! The air pressure is dropping fast. A storm is coming, with wind from the " + from + "! 30 seconds!";
			case WHIRLPOOL -> "Captain, the current is pulling strangely... a whirlpool is forming! Get the sails up!";
			case AQUA_LAGUNA -> "Captain! The tide is going way out. That means Aqua Laguna! Get everyone to high ground!";
			case CALM_BELT_AMBUSH -> "Captain... I don't like this calm. Something big is under us. Get ready to fight!";
			case BLIZZARD -> "Captain, it's getting cold fast. A blizzard is coming! Grab some warm clothes!";
			case HEAT_WAVE -> "Captain, the wind is dying and it's getting hot. Bring water and stay in the shade!";
			case FLORIAN_MIST -> "C-Captain... there's a mist ahead. Sailors say ghosts live in it!";
			case WATERSPOUT -> "Captain! A waterspout is forming. Watch where it goes and steer around it!";
			case ROGUE_WAVE -> "Captain! A rogue wave from the " + from + "! Turn the bow into it, now!";
			case HAILSTORM -> "Captain, those clouds mean hail. Everyone below deck or put a helmet on!";
		};
	}

	/** Turns an angle into north, south-east and so on. */
	private static String compass(float angle) {
		// Minecraft: +x is east, +z is south.
		String[] names = {"east", "south-east", "south", "south-west", "west", "north-west", "north", "north-east"};
		int index = Math.floorMod(Math.round(angle / (Mth.TWO_PI / 8)), 8);
		return names[index];
	}

	/** A deep water spot 25 to 40 blocks away, ahead of the player's ship if they're sailing. */
	private static BlockPos findWhirlpoolSpot(ServerLevel level, ServerPlayer player, RandomSource random) {
		double heading = ShipEntity.aboard(player) instanceof ShipEntity ship
				? Math.toRadians(ship.getYRot() + 90) : random.nextDouble() * Math.PI * 2;
		for (int attempt = 0; attempt < 12; attempt++) {
			double angle = heading + (random.nextDouble() - 0.5) * (attempt < 6 ? 1.2 : Math.PI * 2);
			double distance = 25 + random.nextDouble() * 15;
			BlockPos spot = BlockPos.containing(player.getX() + Math.cos(angle) * distance, level.getSeaLevel(),
					player.getZ() + Math.sin(angle) * distance);
			if (SeaKingSpawner.isDeepWater(level, spot) && CalmBelt.seaAt(level, spot) != null) {
				return spot;
			}
		}
		return null;
	}

	/** If this spot is near the ocean, the flat direction pointing from the sea toward it. Otherwise null. */
	private static Vec3 directionFromSea(ServerLevel level, BlockPos pos) {
		double sx = 0;
		double sz = 0;
		int found = 0;
		for (int i = 0; i < 16; i++) {
			double angle = i * Math.PI / 8;
			for (int distance = 12; distance <= 48; distance += 12) {
				BlockPos check = BlockPos.containing(pos.getX() + Math.cos(angle) * distance, level.getSeaLevel(),
						pos.getZ() + Math.sin(angle) * distance);
				if (level.isLoaded(check) && CalmBelt.isOcean(level.getBiome(check))) {
					sx += Math.cos(angle);
					sz += Math.sin(angle);
					found++;
					break;
				}
			}
		}
		if (found < 2 || found > 14 || (sx == 0 && sz == 0)) {
			return null; // Too far inland, or not really land at all.
		}
		return new Vec3(-sx, 0, -sz).normalize();
	}
}
