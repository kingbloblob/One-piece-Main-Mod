package com.onepiecemod.town;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import it.unimi.dsi.fastutil.longs.LongSet;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.phys.AABB;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.npc.NpcFeature;

/**
 * Keeps track of the towns players are in, and keeps them lived in.
 *
 * Every two seconds it checks which town structures each player is standing in (towns.json lists them by structure
 * id). A town a player visits learns its layout (Town.scanSome), then fills up with townsfolk one by one, up to its
 * population. Townsfolk are saved with the world, so the same people live there next time.
 * It also runs each visited town's market, bar brawls and festivals.
 */
public class Towns {
	private static final int CHECK_EVERY = 40;
	/** A town counts as busy for this long after a player was last inside it. */
	private static final int VISIT_MEMORY = 20 * 30;

	private static final Map<String, Town> BY_KEY = new LinkedHashMap<>();
	private static final Map<String, String> LAST_TOWN = new HashMap<>(); // player -> town key they were last in

	public static Town byKey(String key) {
		return key == null || key.isEmpty() ? null : BY_KEY.get(key);
	}

	/** The town a position is in (or within margin blocks of), if a player has been near it since the server started. */
	public static Town at(ServerLevel level, BlockPos pos, int margin) {
		for (Town town : BY_KEY.values()) {
			if (town.level == level && town.contains(pos, margin)) {
				return town;
			}
		}
		return null;
	}

	static void tick(MinecraftServer server) {
		long gameTime = server.overworld().getGameTime();
		if (gameTime % CHECK_EVERY == 0) {
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				if (!player.isSpectator()) {
					findTowns(player);
				}
			}
		}
		boolean scannedOne = false;
		for (Town town : BY_KEY.values()) {
			if (gameTime - town.lastVisited > VISIT_MEMORY) {
				continue;
			}
			if (!town.scanned) {
				if (!scannedOne) {
					town.scanSome();
					scannedOne = true; // One town's scan per tick keeps the server smooth.
				}
				continue;
			}
			if (gameTime % CHECK_EVERY == 20) {
				populate(town);
			}
			Markets.tick(town, town.level, gameTime);
			BarBrawls.tick(town, town.level, gameTime);
			Festivals.tick(town, town.level, gameTime);
		}
	}

	private static void findTowns(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		BlockPos pos = player.blockPosition();
		Map<Structure, LongSet> here = level.structureManager().getAllStructuresAt(pos);
		String inside = null;
		for (Map.Entry<Structure, LongSet> entry : here.entrySet()) {
			Identifier id = level.registryAccess().lookupOrThrow(Registries.STRUCTURE).getKey(entry.getKey());
			if (id == null || !OnePieceMod.MOD_ID.equals(id.getNamespace())) {
				continue;
			}
			TownData.TownDef def = TownData.town(id.getPath());
			if (def == null) {
				continue;
			}
			List<StructureStart> starts = new ArrayList<>();
			level.structureManager().fillStartsForStructure(entry.getKey(), entry.getValue(), starts::add);
			for (StructureStart start : starts) {
				if (!start.isValid()) {
					continue;
				}
				String key = id.getPath() + "@" + start.getChunkPos().x() + "," + start.getChunkPos().z();
				Town town = BY_KEY.computeIfAbsent(key, k -> new Town(id.getPath(), def, level, start.getBoundingBox(), k));
				town.lastVisited = level.getGameTime();
				if (town.contains(pos, 0)) {
					inside = key;
				}
			}
		}
		String before = LAST_TOWN.get(player.getStringUUID());
		if (inside != null && !inside.equals(before)) {
			Town town = BY_KEY.get(inside);
			if (town.isAngryAt(player.getUUID())) {
				player.sendSystemMessage(Component.literal("Doors slam and shutters close as you walk into " + town.name() + ". They remember you.")
						.withStyle(ChatFormatting.RED), true);
			}
		}
		if (inside == null) {
			LAST_TOWN.remove(player.getStringUUID());
		} else {
			LAST_TOWN.put(player.getStringUUID(), inside);
		}
	}

	/** Adds one townsperson if the town has fewer than it should. */
	private static void populate(Town town) {
		ServerLevel level = town.level;
		if (!town.entitiesLoaded()) {
			return; // Part of the town is out of range: its people there wouldn't be counted.
		}
		List<TownsfolkEntity> residents = residents(town);
		int living = 0;
		Map<String, Integer> jobs = new HashMap<>();
		Set<BlockPos> homes = new HashSet<>();
		for (TownsfolkEntity resident : residents) {
			if (!resident.isVisitor()) {
				living++;
				jobs.merge(resident.jobId(), 1, Integer::sum);
				homes.add(resident.home());
			}
		}
		if (living >= town.def.population) {
			return;
		}
		BlockPos spot = town.pickSpawn(level.getRandom());
		if (spot == null || !level.hasChunkAt(spot)) {
			return;
		}
		String job = TownData.pickJob(town.def, jobs, level.getRandom());
		spawn(town, job, spot, jobs.getOrDefault(job, 0), homes);
	}

	public static TownsfolkEntity spawn(Town town, String job, BlockPos spot, int index, Set<BlockPos> takenHomes) {
		ServerLevel level = town.level;
		TownsfolkEntity person = TownFeature.TOWNSFOLK.create(level, EntitySpawnReason.EVENT);
		if (person == null) {
			return null;
		}
		person.snapTo(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5, level.getRandom().nextFloat() * 360f, 0);
		BlockPos home = town.pickHome(takenHomes, level.getRandom());
		person.settle(town, job, index, home, level.getRandom());
		level.addFreshEntity(person);
		return person;
	}

	public static List<TownsfolkEntity> residents(Town town) {
		AABB area = AABB.of(town.box).inflate(32);
		return town.level.getEntitiesOfClass(TownsfolkEntity.class, area, t -> t.isAlive() && t.townKey().equals(town.key));
	}

	// ---------- When players hurt townsfolk ----------

	/** Someone hurt a townsperson outside of a bar fight. The town won't forget it in a hurry. */
	static void onCivilianHurt(TownsfolkEntity victim, ServerPlayer player, ServerLevel level) {
		Town town = victim.town();
		victim.panic(200);
		if (town == null) {
			return;
		}
		boolean wasAngry = town.isAngryAt(player.getUUID());
		TownGrudges.makeAngry(town, player.getUUID(), level.getGameTime() + 24000L);
		for (TownsfolkEntity other : level.getEntitiesOfClass(TownsfolkEntity.class, victim.getBoundingBox().inflate(24),
				t -> t != victim && t.townKey().equals(town.key))) {
			other.panic(160);
		}
		if (!wasAngry) {
			victim.shout(level.getRandom().nextBoolean() ? "HELP! A pirate is attacking us!" : "Somebody call the Marines!", 32);
			player.sendSystemMessage(Component.literal(town.name() + " won't trade with you until tomorrow.").withStyle(ChatFormatting.RED));
			// Sometimes the Marines are close enough to hear.
			if (level.getRandom().nextFloat() < 0.4f) {
				callMarines(town, player, level);
			}
		}
	}

	static void onCivilianKilled(TownsfolkEntity victim, ServerPlayer player, ServerLevel level) {
		Town town = victim.town();
		boolean news = true;
		if (town != null) {
			TownGrudges.makeAngry(town, player.getUUID(), level.getGameTime() + 24000L * 3);
			callMarines(town, player, level);
			// The town keeps bringing in new people, so only the first few attacks a day make the papers.
			news = TownGrudges.countKill(town, player.getUUID());
		}
		if (news) {
			Bounty.raise(player, 2_000_000L, "The papers say you attacked innocent townsfolk.", false);
		}
	}

	private static void callMarines(Town town, ServerPlayer player, ServerLevel level) {
		BlockPos from = town.randomOpenNear(town.plaza, 20, level.getRandom());
		int count = 2 + level.getRandom().nextInt(2);
		for (int i = 0; i < count; i++) {
			HumanNpc marine = NpcFeature.spawn(level, i == 0 ? "marine_officer" : "marine", from.offset(i, 0, 0), 0f);
			if (marine != null) {
				marine.setTarget(player);
			}
		}
		player.sendSystemMessage(Component.literal("Marines come running from the town's garrison!").withStyle(ChatFormatting.BLUE));
	}

	/**
	 * Player-founded towns (settlement package) are added here too, so their townsfolk get the same routines,
	 * bars, markets and festivals. Replaces any town with the same key.
	 */
	public static void putTown(Town town) {
		BY_KEY.put(town.key, town);
	}

	public static void removeTown(String key) {
		BY_KEY.remove(key);
	}

	/** For /town and other features: the town a player is standing in, if any. */
	public static Town townOf(Player player) {
		String key = LAST_TOWN.get(player.getStringUUID());
		return key == null ? null : BY_KEY.get(key);
	}

	static void clear() {
		BY_KEY.clear();
		LAST_TOWN.clear();
	}
}
