package com.onepiecemod.worldevent;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.jetbrains.annotations.Nullable;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BiomeTags;
import net.minecraft.util.Mth;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.animal.golem.IronGolem;
import net.minecraft.world.entity.npc.villager.AbstractVillager;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.bounty.MarineEntity;
import com.onepiecemod.bounty.NavyCalm;
import com.onepiecemod.bounty.NavyRaids;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.empire.BusterCall;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.npc.NpcFeature;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.shipcombat.ShipBrain;
import com.onepiecemod.shipcombat.ShipCombat;
import com.onepiecemod.sound.ModSounds;

/**
 * Trouble on an island: how angry the World Government is about what you did there.
 *
 * Every island you make trouble on gets a Trouble meter (0-100), saved with the world. It rises when you
 *  - beat Marines (+4, officers +8, Vice Admirals +15) or sink a Marine ship near the island (+12),
 *  - hurt townsfolk (villagers +10, iron golems +5),
 *  - beat a boss there (+10, a World Government boss like Smoker, Lucci or an Admiral +25),
 *  - wreck a town or other structure (+0.15 per block broken).
 * Wanted pirates make more trouble (+15% per threat level), and more again during the Reverie.
 * It cools down by 2 a minute.
 *
 *  35: Marine HQ sends reinforcements.  70: a Vice Admiral asks for a Buster Call (a warning).
 * 100: a BUSTER CALL on the island, if a pirate with at least 50,000,000 Berries is there. Smaller fry
 *      get a Navy raid instead.
 *
 * An "island" is the spot where the trouble started; anything within 128 blocks of it counts as the same island.
 */
public class IslandTrouble {
	public static final double ISLAND_RADIUS = 128;
	public static final float REINFORCE_AT = 35;
	public static final float WARN_AT = 70;
	public static final float BUSTER_CALL_AT = 100;
	/** The bounty a pirate needs before the Navy will Buster Call an island over them. */
	public static final long BUSTER_CALL_BOUNTY = 50_000_000L;
	/** After a Buster Call, the same island can't get another for one in-game day. */
	private static final long CALL_COOLDOWN = 24000L;
	private static final float COOL_PER_MINUTE = 2f;

	/** One troubled island. key = "biome id@x,z". */
	public record Island(String key, float trouble, int stage, long lastCall) {
		static final Codec<Island> CODEC = RecordCodecBuilder.create(i -> i.group(
				Codec.STRING.fieldOf("key").forGetter(Island::key),
				Codec.FLOAT.fieldOf("trouble").forGetter(Island::trouble),
				Codec.INT.fieldOf("stage").forGetter(Island::stage),
				Codec.LONG.fieldOf("last_call").forGetter(Island::lastCall)
		).apply(i, Island::new));
	}

	public static final AttachmentType<List<Island>> SAVED = AttachmentRegistry.create(
			OnePieceMod.id("island_trouble"),
			builder -> builder.persistent(Island.CODEC.listOf())
	);

	/** Working copy (the saved list is rewritten every 30 s and on stop). */
	static class Spot {
		final String key;
		final BlockPos center;
		float trouble;
		int stage; // 0 calm, 1 reinforcements sent, 2 warned
		long lastCall;

		Spot(String key, float trouble, int stage, long lastCall) {
			this.key = key;
			this.center = centerOf(key);
			this.trouble = trouble;
			this.stage = stage;
			this.lastCall = lastCall;
		}
	}

	private static final Map<String, Spot> SPOTS = new HashMap<>();
	private static boolean loaded = false;

	static void initialize() {
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (!(source.getEntity() instanceof ServerPlayer player) || entity == player || !(entity.level() instanceof ServerLevel level)) {
				return;
			}
			float amount = troubleForKill(entity);
			if (amount > 0) {
				add(level, entity.blockPosition(), player, amount);
			}
		});
		PlayerBlockBreakEvents.AFTER.register((level, player, pos, state, blockEntity) -> {
			if (level instanceof ServerLevel server && player instanceof ServerPlayer sp && !sp.isCreative() && insideStructure(server, pos)) {
				add(server, pos, sp, 0.15f);
			}
		});
	}

	private static float troubleForKill(LivingEntity entity) {
		if (entity instanceof MarineEntity marine) {
			if ("vice_admiral".equals(marine.getKitId())) {
				return 15;
			}
			return marine.getBountyReward() >= 1_000_000L ? 8 : 4;
		}
		if (entity instanceof CharacterEntity character && character.isBoss()) {
			return switch (character.getCharacterId()) {
				case "smoker", "tashigi", "koby", "lucci", "magellan", "akainu", "kizaru", "fujitora", "ryokugyu", "aokiji",
						"garp", "sengoku", "kuma", "imu", "vegapunk" -> 25;
				default -> 10;
			};
		}
		if (entity instanceof AbstractVillager || entity.entityTags().contains("onepiece_townsfolk")) {
			return 10;
		}
		if (entity instanceof IronGolem) {
			return 5;
		}
		return 0;
	}

	/** True if the spot is inside a generated structure (a town, a fort, a lair...). */
	private static boolean insideStructure(ServerLevel level, BlockPos pos) {
		for (Structure structure : level.structureManager().getAllStructuresAt(pos).keySet()) {
			StructureStart start = level.structureManager().getStructureAt(pos, structure);
			if (start.isValid()) {
				return true;
			}
		}
		return false;
	}

	// ---- Islands ----

	public static Component islandName(String key) {
		int at = key.indexOf('@');
		String biome = at >= 0 ? key.substring(0, at) : key;
		int colon = biome.indexOf(':');
		if (colon < 0) {
			return Component.literal("the island");
		}
		return Component.translatable("biome." + biome.substring(0, colon) + "." + biome.substring(colon + 1));
	}

	@Nullable
	public static BlockPos centerOf(String key) {
		int at = key.indexOf('@');
		if (at < 0) {
			return null;
		}
		String[] xz = key.substring(at + 1).split(",");
		try {
			return new BlockPos(Integer.parseInt(xz[0]), 64, Integer.parseInt(xz[1]));
		} catch (RuntimeException e) {
			return null;
		}
	}

	@Nullable
	static Spot nearest(BlockPos pos) {
		Spot best = null;
		double bestDistance = ISLAND_RADIUS * ISLAND_RADIUS;
		for (Spot spot : SPOTS.values()) {
			if (spot.center == null) {
				continue;
			}
			double dx = spot.center.getX() - pos.getX();
			double dz = spot.center.getZ() - pos.getZ();
			double d = dx * dx + dz * dz;
			if (d < bestDistance) {
				bestDistance = d;
				best = spot;
			}
		}
		return best;
	}

	/** The island at this spot: an existing one, or a new one if this is land. Null out at sea or off the Overworld. */
	@Nullable
	static Spot islandAt(ServerLevel level, BlockPos pos, boolean create) {
		if (level.dimension() != Level.OVERWORLD) {
			return null;
		}
		Spot spot = nearest(pos);
		if (spot != null || !create) {
			return spot;
		}
		Holder<Biome> biome = level.getBiome(pos);
		if (biome.is(BiomeTags.IS_OCEAN) || biome.is(BiomeTags.IS_DEEP_OCEAN) || biome.is(BiomeTags.IS_RIVER)) {
			return null;
		}
		String id = biome.unwrapKey().map(ResourceKey::identifier).map(Object::toString).orElse("minecraft:plains");
		String key = id + "@" + pos.getX() + "," + pos.getZ();
		spot = new Spot(key, 0, 0, -CALL_COOLDOWN);
		SPOTS.put(key, spot);
		return spot;
	}

	public static float troubleAt(ServerLevel level, BlockPos pos) {
		Spot spot = islandAt(level, pos, false);
		return spot == null ? 0 : spot.trouble;
	}

	/** Adds trouble on the island at pos, caused by this player. */
	public static void add(ServerLevel level, BlockPos pos, ServerPlayer player, float amount) {
		// Fighting off a hideout siege, a Navy raid or a story battle is already a big Navy event:
		// those kills shouldn't also call in reinforcements or a Buster Call on top.
		if (level.getDifficulty() == Difficulty.PEACEFUL || NavyCalm.isBusy(player)) {
			return;
		}
		Spot spot = islandAt(level, pos, true);
		if (spot == null || IslandBusterCall.isRunning(spot.key)) {
			return;
		}
		float multiplier = (1 + 0.15f * Bounty.threatLevel(player)) * Reverie.troubleMultiplier(level.getServer());
		spot.trouble = Mth.clamp(spot.trouble + amount * multiplier, 0, BUSTER_CALL_AT);
		react(level, spot, player);
	}

	/** Sets trouble directly (for /worldevent trouble). */
	static void set(ServerLevel level, ServerPlayer player, float value) {
		Spot spot = islandAt(level, player.blockPosition(), true);
		if (spot != null) {
			spot.trouble = Mth.clamp(value, 0, BUSTER_CALL_AT);
			spot.stage = 0;
			react(level, spot, player);
		}
	}

	private static void react(ServerLevel level, Spot spot, ServerPlayer player) {
		Component name = islandName(spot.key);
		if (spot.trouble >= BUSTER_CALL_AT) {
			long now = level.getGameTime();
			boolean bigFish = Bounty.get(player) >= BUSTER_CALL_BOUNTY;
			if (bigFish && now - spot.lastCall >= CALL_COOLDOWN && !BusterCall.isActive(player)) {
				spot.lastCall = now;
				spot.stage = 0;
				IslandBusterCall.start(level, spot, player);
			} else if (!NavyRaids.isRaiding(player) && Bounty.get(player) > 0 && !IslandBusterCall.isRunning(spot.key)) {
				WorldNews.call(player, "Marine HQ", "All units to " + name.getString() + "! Arrest the pirate " + player.getName().getString() + "!",
						ChatFormatting.RED);
				NavyRaids.start(player);
				spot.trouble = 60;
				spot.stage = 1;
			} else {
				spot.trouble = 60;
			}
			return;
		}
		if (spot.trouble >= WARN_AT && spot.stage < 2) {
			spot.stage = 2;
			for (ServerPlayer near : playersOn(level, spot)) {
				WorldNews.call(near, "Vice Admiral", "This is a Vice Admiral of Marine HQ. Requesting permission for a Buster Call on "
						+ name.getString() + ". Pirates on that island: surrender or leave.", ChatFormatting.RED);
				ModSounds.play(near, ModSounds.NAVY_BUGLE);
			}
		} else if (spot.trouble >= REINFORCE_AT && spot.stage < 1) {
			spot.stage = 1;
			WorldNews.call(player, "Marine HQ", "Trouble reported on " + name.getString() + ". Reinforcements are on the way.", ChatFormatting.GOLD);
			sendReinforcements(level, player);
		}
	}

	/** A Marine squad lands near the player: an officer and 3-4 men. */
	private static void sendReinforcements(ServerLevel level, ServerPlayer player) {
		BlockPos spot = WorldEvents.landingSpot(level, player.blockPosition(), 20, 32, player.getRandom());
		if (spot == null) {
			return;
		}
		int size = 3 + player.getRandom().nextInt(2);
		for (int i = 0; i <= size; i++) {
			String kit = i == 0 ? "marine_officer" : i % 2 == 0 ? "marine_rifle" : "marine";
			HumanNpc npc = NpcFeature.spawn(level, kit, spot.offset(player.getRandom().nextInt(5) - 2, 0, player.getRandom().nextInt(5) - 2), 0);
			if (npc != null && Bounty.get(player) > 0) {
				npc.setTarget(player);
			}
		}
	}

	static List<ServerPlayer> playersOn(ServerLevel level, Spot spot) {
		List<ServerPlayer> list = new ArrayList<>();
		if (spot.center == null) {
			return list;
		}
		for (ServerPlayer player : level.players()) {
			double dx = player.getX() - spot.center.getX();
			double dz = player.getZ() - spot.center.getZ();
			if (dx * dx + dz * dz < (ISLAND_RADIUS + 32) * (ISLAND_RADIUS + 32)) {
				list.add(player);
			}
		}
		return list;
	}

	// ---- Every tick ----

	private static final java.util.Set<ShipEntity> SEEN_SINKING = java.util.Collections.newSetFromMap(new java.util.WeakHashMap<>());

	static void tick(MinecraftServer server) {
		if (!loaded) {
			load(server);
		}
		int time = server.getTickCount();
		if (time % 20 == 0) {
			watchSinkingMarines(server.overworld());
		}
		if (time % (20 * 30) == 0) {
			// Cool down. Islands with no trouble left are forgotten.
			SPOTS.values().removeIf(spot -> {
				spot.trouble = Math.max(0, spot.trouble - COOL_PER_MINUTE / 2);
				if (spot.trouble < REINFORCE_AT - 10) {
					spot.stage = 0;
				} else if (spot.trouble < WARN_AT - 10) {
					spot.stage = Math.min(spot.stage, 1);
				}
				return spot.trouble <= 0 && server.overworld().getGameTime() - spot.lastCall >= CALL_COOLDOWN
						&& !IslandBusterCall.isRunning(spot.key);
			});
			save(server);
		}
	}

	/** A Marine ship going down near an island is trouble for whoever was closest. */
	private static void watchSinkingMarines(ServerLevel level) {
		for (ShipEntity ship : ShipCombat.loadedShips()) {
			if (ship.sinking && ship.level() == level && ShipBrain.factionOf(ship) == ShipBrain.Faction.MARINE && SEEN_SINKING.add(ship)) {
				ServerPlayer nearest = null;
				double best = 100 * 100;
				for (ServerPlayer player : level.players()) {
					double d = player.distanceToSqr(ship);
					if (d < best && !player.isSpectator()) {
						best = d;
						nearest = player;
					}
				}
				if (nearest != null) {
					Spot spot = nearest(ship.blockPosition());
					if (spot != null) {
						add(level, spot.center, nearest, 12);
					}
				}
			}
		}
	}

	static void load(MinecraftServer server) {
		SPOTS.clear();
		for (Island island : server.overworld().getAttachedOrElse(SAVED, List.of())) {
			SPOTS.put(island.key(), new Spot(island.key(), island.trouble(), island.stage(), island.lastCall()));
		}
		loaded = true;
	}

	static void unload() {
		SPOTS.clear();
		loaded = false;
	}

	static void save(MinecraftServer server) {
		if (!loaded) {
			return;
		}
		List<Island> list = new ArrayList<>();
		for (Spot spot : SPOTS.values()) {
			list.add(new Island(spot.key, spot.trouble, spot.stage, spot.lastCall));
		}
		server.overworld().setAttached(SAVED, list);
	}

	/** One line for /island. */
	static Component describe(ServerLevel level, ServerPlayer player) {
		Spot spot = islandAt(level, player.blockPosition(), false);
		if (spot == null) {
			return Component.literal("No trouble here. The Marines aren't watching this place.").withStyle(ChatFormatting.GRAY);
		}
		int value = Math.round(spot.trouble);
		ChatFormatting color = value >= WARN_AT ? ChatFormatting.RED : value >= REINFORCE_AT ? ChatFormatting.GOLD : ChatFormatting.YELLOW;
		String note = IslandBusterCall.isRunning(spot.key) ? " A BUSTER CALL is under way!"
				: value >= WARN_AT ? " A Vice Admiral wants a Buster Call. Lie low or leave."
				: value >= REINFORCE_AT ? " The Marines sent reinforcements." : "";
		return Component.literal("Trouble on ").withStyle(color).append(islandName(spot.key).copy().withStyle(color))
				.append(Component.literal(": " + value + " / 100." + note).withStyle(color));
	}

	@Nullable
	static Spot spotByKey(String key) {
		return SPOTS.get(key);
	}

	static void clearTrouble(Spot spot) {
		spot.trouble = 0;
		spot.stage = 0;
	}
}
