package com.onepiecemod.seatrain;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.building.BuildingRegistry;
import com.onepiecemod.building.Buildings;
import com.onepiecemod.building.Multiblock;
import com.onepiecemod.island.Islands;

/**
 * Every Sea Train stop in the world, and which ones each player has found.
 *
 * There are two kinds:
 * - Puffing Tom stops: the Galley-La dock (Water 7), the Tower of Justice (Enies Lobby) and every
 *   Sea Train Station structure. They get noted the first time anyone walks into them.
 * - Player stops: a finished Sea Train Station building (the Ticket Booth plus its platform, track and bell).
 *
 * You can only ride to stops you have stood at yourself, so the train never skips the sailing.
 */
public class Stations {
	public static final String KIND_PUFFING_TOM = "puffing_tom";
	public static final String KIND_BOOTH = "booth";

	/** The building id of the player-built station (its core block is onepiece:sea_train_booth). */
	public static final String BOOTH = "sea_train_booth";

	/**
	 * One stop.
	 *
	 * @param id      "galley_la_dock_12_-40" or "booth_100_64_-20"
	 * @param pos     where passengers step off (a spot someone stood on, so it's safe)
	 * @param dim     the dimension id, like "minecraft:overworld"
	 */
	public record Station(String id, String name, String kind, BlockPos pos, String dim) {
		public static final Codec<Station> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				Codec.STRING.fieldOf("id").forGetter(Station::id),
				Codec.STRING.fieldOf("name").forGetter(Station::name),
				Codec.STRING.fieldOf("kind").forGetter(Station::kind),
				BlockPos.CODEC.fieldOf("pos").forGetter(Station::pos),
				Codec.STRING.fieldOf("dim").forGetter(Station::dim)
		).apply(instance, Station::new));

		public boolean puffingTom() {
			return KIND_PUFFING_TOM.equals(kind);
		}

		public Station withName(String newName) {
			return new Station(id, newName, kind, pos, dim);
		}
	}

	/** All stops, saved with the Overworld (stops in other dimensions are listed there too). */
	public static final AttachmentType<Map<String, Station>> STATIONS = AttachmentRegistry.create(
			OnePieceMod.id("sea_train_stations"),
			builder -> builder.persistent(Codec.unboundedMap(Codec.STRING, Station.CODEC))
	);

	/** The stops one player has found. */
	public static final AttachmentType<List<String>> KNOWN = AttachmentRegistry.create(
			OnePieceMod.id("sea_train_known"),
			builder -> builder.persistent(Codec.STRING.listOf()).copyOnDeath()
	);

	/** Structures that are Puffing Tom stops, and what the stop is called. */
	private static final Map<String, String> PUFFING_TOM_STOPS = new LinkedHashMap<>();

	static {
		PUFFING_TOM_STOPS.put("galley_la_dock", "Water 7 (Blue Station)");
		PUFFING_TOM_STOPS.put("tower_of_justice", "Enies Lobby");
		PUFFING_TOM_STOPS.put("sea_train_station", "Sea Train Station");
	}

	public static void initialize() {
		// Loading this class registers the two attachments.
	}

	// ---------- Reading and writing ----------

	public static Map<String, Station> all(ServerLevel anyLevel) {
		return anyLevel.getServer().overworld().getAttachedOrElse(STATIONS, Map.of());
	}

	public static Station get(ServerLevel anyLevel, String id) {
		return all(anyLevel).get(id);
	}

	static void put(ServerLevel anyLevel, Station station) {
		Map<String, Station> map = new HashMap<>(all(anyLevel));
		map.put(station.id(), station);
		anyLevel.getServer().overworld().setAttached(STATIONS, map);
	}

	static void remove(ServerLevel anyLevel, String id) {
		Map<String, Station> map = new HashMap<>(all(anyLevel));
		if (map.remove(id) != null) {
			anyLevel.getServer().overworld().setAttached(STATIONS, map);
		}
	}

	public static List<String> known(ServerPlayer player) {
		return player.getAttachedOrElse(KNOWN, List.of());
	}

	public static boolean knows(ServerPlayer player, String id) {
		return known(player).contains(id);
	}

	/** Notes a stop for this player. Returns true if it was new to them. */
	static boolean learn(ServerPlayer player, String id) {
		List<String> list = known(player);
		if (list.contains(id)) {
			return false;
		}
		List<String> copy = new ArrayList<>(list);
		copy.add(id);
		player.setAttached(KNOWN, copy);
		return true;
	}

	static String dim(Level level) {
		return level.dimension().identifier().toString();
	}

	// ---------- Which stop is the player standing at? ----------

	/** The Puffing Tom structure the player is inside, or null. */
	static StructureStart puffingTomStructureAt(ServerLevel level, BlockPos pos) {
		if (level.dimension() != Level.OVERWORLD) {
			return null;
		}
		StructureStart start = level.structureManager().getStructureWithPieceAt(pos, Stations::isPuffingTomStop);
		return start != null && start.isValid() ? start : null;
	}

	private static boolean isPuffingTomStop(Holder<Structure> holder) {
		return holder.unwrapKey().map(key -> key.identifier().getNamespace().equals(OnePieceMod.MOD_ID)
				&& PUFFING_TOM_STOPS.containsKey(key.identifier().getPath())).orElse(false);
	}

	private static String structurePath(ServerLevel level, StructureStart start) {
		ResourceKey<Structure> key = level.registryAccess().lookupOrThrow(Registries.STRUCTURE)
				.getResourceKey(start.getStructure()).orElse(null);
		return key == null ? "sea_train_station" : key.identifier().getPath();
	}

	private static String idFor(String path, StructureStart start) {
		return path + "_" + start.getChunkPos().x() + "_" + start.getChunkPos().z();
	}

	/** The finished Sea Train Station building within 6 blocks, or null. */
	static BuildingRegistry.Entry boothNear(ServerLevel level, BlockPos pos, int range) {
		Multiblock booth = Buildings.get(BOOTH);
		BuildingRegistry.Entry best = null;
		double bestDistance = range * range + 1;
		for (BuildingRegistry.Entry entry : BuildingRegistry.all(level)) {
			if (!entry.type().equals(BOOTH)) {
				continue;
			}
			double distance = entry.pos().distSqr(pos);
			if (distance < bestDistance && level.getBlockState(entry.pos()).is(booth.core())
					&& booth.check(level, entry.pos()).complete()) {
				best = entry;
				bestDistance = distance;
			}
		}
		return best;
	}

	static String boothId(BlockPos pos) {
		return "booth_" + pos.getX() + "_" + pos.getY() + "_" + pos.getZ();
	}

	/**
	 * The stop the player is standing at right now (noting it if nobody had before), or null.
	 * Player-built stations win over Puffing Tom stops when both are close.
	 */
	public static Station here(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		BuildingRegistry.Entry booth = boothNear(level, player.blockPosition(), 6);
		if (booth != null) {
			String id = boothId(booth.pos());
			Station station = get(level, id);
			if (station == null) {
				station = new Station(id, "Station at " + booth.pos().getX() + ", " + booth.pos().getZ(), KIND_BOOTH,
						booth.pos(), dim(level));
				put(level, station);
			}
			return station;
		}
		StructureStart start = puffingTomStructureAt(level, player.blockPosition());
		if (start == null) {
			return null;
		}
		String path = structurePath(level, start);
		String id = idFor(path, start);
		Station station = get(level, id);
		if (station == null) {
			if (!player.onGround() || player.isInWater()) {
				return null; // Note the stop from a spot someone can stand on.
			}
			station = new Station(id, stopName(level, path, player.blockPosition()), KIND_PUFFING_TOM,
					player.blockPosition(), dim(level));
			put(level, station);
		}
		return station;
	}

	/** "Water 7 (Blue Station)", "Enies Lobby", or "Alabasta Station" for a station on a named island. */
	private static String stopName(ServerLevel level, String path, BlockPos pos) {
		if (!path.equals("sea_train_station")) {
			return PUFFING_TOM_STOPS.getOrDefault(path, "Sea Train Station");
		}
		String biome = level.getBiome(pos).unwrapKey().map(key -> key.identifier().toString()).orElse("");
		Islands.Island island = Islands.byBiome(biome);
		String base = island != null ? island.name + " Station" : "Sea Train Station";
		// Two stations on one island get told apart by where they are.
		for (Station other : all(level).values()) {
			if (other.name().equals(base)) {
				return base + " (" + pos.getX() + ", " + pos.getZ() + ")";
			}
		}
		return base;
	}

	// ---------- Noticing stops as players walk into them ----------

	/** Called every two seconds for each player. */
	static void notice(ServerPlayer player) {
		if (player.isSpectator() || player.isPassenger()) {
			return;
		}
		Station station = here(player);
		if (station == null || !learn(player, station.id())) {
			return;
		}
		if (station.puffingTom()) {
			player.sendSystemMessage(Component.literal("New Sea Train stop: " + station.name() + ".").withStyle(ChatFormatting.AQUA));
			if (Trips.puffingTomOpen(player)) {
				player.sendSystemMessage(timetableLink("The Puffing Tom stops here. "));
			} else {
				player.sendSystemMessage(Component.literal("The Puffing Tom only takes passengers who have made it to Water 7. "
						+ "It will remember this stop for when your story gets there.").withStyle(ChatFormatting.GRAY));
			}
		} else {
			player.sendSystemMessage(Component.literal("New Sea Train stop: " + station.name() + ". You can ride here from any station now.")
					.withStyle(ChatFormatting.AQUA));
		}
	}

	static Component timetableLink(String before) {
		return Component.literal(before).withStyle(ChatFormatting.GRAY)
				.append(Component.literal("[Timetable]").withStyle(style -> style.withColor(ChatFormatting.GREEN)
						.withClickEvent(new ClickEvent.RunCommand("/seatrain"))
						.withHoverEvent(new HoverEvent.ShowText(Component.literal("See where the train can take you")))));
	}
}
