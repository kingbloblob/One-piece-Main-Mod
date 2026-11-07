package com.onepiecemod.character;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.BiConsumer;
import java.util.function.Supplier;

import com.google.gson.Gson;
import com.mojang.datafixers.util.Pair;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.levelgen.structure.Structure;

import com.onepiecemod.OnePieceMod;

/**
 * Knows the mod's One Piece locations (the structures from the worldgen part of the mod) and where each
 * character lives. Read from src/main/resources/onepiece/locations.json. Used by Sea Charts and Vivre Cards.
 */
public class Locations {
	/** Every One Piece location. The list is in data/onepiece/tags/worldgen/structure/one_piece_locations.json. */
	public static final TagKey<Structure> ALL = TagKey.create(Registries.STRUCTURE, OnePieceMod.id("one_piece_locations"));
	/** How far to search, in chunks. Vanilla treasure maps use 50 to 100. */
	private static final int SEARCH_CHUNKS = 100;

	private static class Data {
		Map<String, String> locations = Map.of();
		Map<String, String> homes = Map.of();
		List<String> lastSeen = List.of();
	}

	private static Data data;

	private static Data data() {
		if (data == null) {
			try (InputStream in = Locations.class.getResourceAsStream("/onepiece/locations.json")) {
				data = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), Data.class);
			} catch (Exception e) {
				throw new RuntimeException("Could not read onepiece/locations.json", e);
			}
		}
		return data;
	}

	/** The nice name of a location, like "Foosha Village". */
	public static String name(String structureId) {
		return data().locations.getOrDefault(structureId, structureId);
	}

	/** Where a character lives (a structure id), or null. */
	public static String home(String characterId) {
		return data().homes.get(characterId);
	}

	/** True if the character has no real home and the place is only where they were last seen. */
	public static boolean onlyLastSeen(String characterId) {
		return data().lastSeen.contains(characterId);
	}

	/** A location that was found: where it is and its structure id. */
	public record Found(BlockPos pos, String id) {
	}

	/**
	 * Searching far for a rare place can take a long time (every possible spot is checked against the terrain and our
	 * other builds), long enough to freeze or even stop a server. So searches run on background threads and the answer
	 * comes back on the server thread. The answer is the same as a search on the server thread. (A thread per search, not
	 * one shared thread: a search cut off by the world closing must not hold up the searches of the next world.)
	 */
	private static final ExecutorService SEARCHER = Executors.newCachedThreadPool(runnable -> {
		Thread thread = new Thread(runnable, "One Piece location search");
		thread.setDaemon(true);
		return thread;
	});
	/** Players with a search under way: one at a time each, so spam-clicking a Vivre Card doesn't queue up dozens. */
	private static final Set<UUID> SEARCHING = ConcurrentHashMap.newKeySet();

	/**
	 * Finds the nearest copy of one location in the background, then calls `done` with the player (as they are now) on the
	 * server thread, unless they have left. Returns false (and calls nothing) if this player already has a search running.
	 */
	public static boolean findLater(ServerPlayer player, String structureId, BiConsumer<ServerPlayer, Optional<Found>> done) {
		ServerLevel level = (ServerLevel) player.level();
		BlockPos from = player.blockPosition();
		return later(player, () -> find(level, from, structureId), done);
	}

	/** {@link #findLater}, but only looks `maxBlocks` out: much quicker when anything further away is no use anyway. */
	public static boolean findLater(ServerPlayer player, String structureId, int maxBlocks, BiConsumer<ServerPlayer, Optional<Found>> done) {
		ServerLevel level = (ServerLevel) player.level();
		BlockPos from = player.blockPosition();
		int chunks = Math.max(1, Math.min(SEARCH_CHUNKS, maxBlocks / 16));
		return later(player, () -> {
			Registry<Structure> structures = level.registryAccess().lookupOrThrow(Registries.STRUCTURE);
			return structures.get(ResourceKey.create(Registries.STRUCTURE, OnePieceMod.id(structureId)))
					.flatMap(structure -> search(level, from, HolderSet.direct(structure), false, chunks));
		}, done);
	}

	/** {@link #findUnexplored} in the background, like {@link #findLater}. */
	public static boolean findUnexploredLater(ServerPlayer player, BiConsumer<ServerPlayer, Optional<Found>> done) {
		ServerLevel level = (ServerLevel) player.level();
		BlockPos from = player.blockPosition();
		return later(player, () -> findUnexplored(level, from), done);
	}

	private static boolean later(ServerPlayer player, Supplier<Optional<Found>> search, BiConsumer<ServerPlayer, Optional<Found>> done) {
		UUID id = player.getUUID();
		if (!SEARCHING.add(id)) {
			return false;
		}
		MinecraftServer server = ((ServerLevel) player.level()).getServer();
		SEARCHER.execute(() -> {
			Optional<Found> found;
			try {
				found = search.get();
			} catch (RuntimeException e) {
				OnePieceMod.LOGGER.warn("Location search failed", e);
				found = Optional.empty();
			} finally {
				SEARCHING.remove(id);
			}
			Optional<Found> result = found;
			server.execute(() -> {
				ServerPlayer now = server.getPlayerList().getPlayer(id);
				if (now != null && !now.isRemoved()) {
					done.accept(now, result);
				}
			});
		});
		return true;
	}

	/** Finds the nearest copy of one location. Slow for far, rare places: from game code, prefer {@link #findLater}. */
	public static Optional<Found> find(ServerLevel level, BlockPos from, String structureId) {
		Registry<Structure> structures = level.registryAccess().lookupOrThrow(Registries.STRUCTURE);
		Optional<Holder.Reference<Structure>> structure = structures.get(ResourceKey.create(Registries.STRUCTURE, OnePieceMod.id(structureId)));
		if (structure.isEmpty()) {
			return Optional.empty();
		}
		return search(level, from, HolderSet.direct(structure.get()), false);
	}

	/** Finds the nearest One Piece location that nobody has made a map of yet. */
	public static Optional<Found> findUnexplored(ServerLevel level, BlockPos from) {
		Registry<Structure> structures = level.registryAccess().lookupOrThrow(Registries.STRUCTURE);
		Optional<HolderSet.Named<Structure>> all = structures.get(ALL);
		if (all.isEmpty()) {
			return Optional.empty();
		}
		return search(level, from, all.get(), true);
	}

	private static Optional<Found> search(ServerLevel level, BlockPos from, HolderSet<Structure> wanted, boolean skipExplored) {
		return search(level, from, wanted, skipExplored, SEARCH_CHUNKS);
	}

	private static Optional<Found> search(ServerLevel level, BlockPos from, HolderSet<Structure> wanted, boolean skipExplored, int chunks) {
		Pair<BlockPos, Holder<Structure>> result = level.getChunkSource().getGenerator()
				.findNearestMapStructure(level, wanted, from, chunks, skipExplored);
		if (result == null) {
			return Optional.empty();
		}
		String id = result.getSecond().unwrapKey().map(key -> key.identifier().getPath()).orElse("");
		return Optional.of(new Found(result.getFirst(), id));
	}

	/** "north-east" and so on, from one place to another. */
	public static String direction(BlockPos from, BlockPos to) {
		double angle = Math.toDegrees(Math.atan2(to.getX() - from.getX(), from.getZ() - to.getZ()));
		String[] names = {"north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"};
		return names[(int) Math.floorMod(Math.round(angle / 45.0), 8)];
	}

	public static int distance(BlockPos from, BlockPos to) {
		double dx = to.getX() - from.getX();
		double dz = to.getZ() - from.getZ();
		return (int) Math.sqrt(dx * dx + dz * dz);
	}
}
