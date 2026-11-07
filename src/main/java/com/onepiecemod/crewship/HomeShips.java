package com.onepiecemod.crewship;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.core.BlockPos;
import net.minecraft.core.UUIDUtil;
import net.minecraft.server.MinecraftServer;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * Every crew's home ship, saved on the Overworld: one per captain.
 * The ship itself carries a Ship's Log block whose saved data holds the same homeId, so we can tell
 * "this is the home ship" whether she is docked (real blocks) or sailing (a ship entity).
 */
public final class HomeShips {
	/**
	 * One home ship.
	 * @param homeId      matches the homeId saved in the Ship's Log on board
	 * @param crewName    shown in reports while the captain is offline
	 * @param level       0..5, see {@link CrewShipLevels}; the highest level reached so far is in best
	 * @param dimension   where the log was last seen docked ("" while unknown)
	 * @param dockPos     where the log was last seen docked
	 * @param lastHaulDay the in-game day of the last daily haul
	 */
	public record HomeShip(UUID homeId, String crewName, int level, int best, String dimension, Optional<BlockPos> dockPos, long lastHaulDay) {
		public static final Codec<HomeShip> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				UUIDUtil.CODEC.fieldOf("home_id").forGetter(HomeShip::homeId),
				Codec.STRING.optionalFieldOf("crew", "").forGetter(HomeShip::crewName),
				Codec.INT.optionalFieldOf("level", 0).forGetter(HomeShip::level),
				Codec.INT.optionalFieldOf("best", 0).forGetter(HomeShip::best),
				Codec.STRING.optionalFieldOf("dimension", "").forGetter(HomeShip::dimension),
				BlockPos.CODEC.optionalFieldOf("dock_pos").forGetter(HomeShip::dockPos),
				Codec.LONG.optionalFieldOf("last_haul_day", -1L).forGetter(HomeShip::lastHaulDay)
		).apply(instance, HomeShip::new));

		public HomeShip withLevel(int newLevel) {
			return new HomeShip(homeId, crewName, newLevel, Math.max(best, newLevel), dimension, dockPos, lastHaulDay);
		}

		public HomeShip dockedAt(String newDimension, BlockPos pos) {
			return new HomeShip(homeId, crewName, level, best, newDimension, Optional.of(pos.immutable()), lastHaulDay);
		}

		public HomeShip hauled(long day) {
			return new HomeShip(homeId, crewName, level, best, dimension, dockPos, day);
		}
	}

	public static final AttachmentType<Map<String, HomeShip>> HOME_SHIPS = AttachmentRegistry.create(
			OnePieceMod.id("home_ships"),
			builder -> builder.persistent(Codec.unboundedMap(Codec.STRING, HomeShip.CODEC)));

	private HomeShips() {
	}

	public static Map<String, HomeShip> all(MinecraftServer server) {
		return server.overworld().getAttachedOrElse(HOME_SHIPS, Map.of());
	}

	/** The captain's home ship, or null. */
	public static HomeShip of(MinecraftServer server, UUID captain) {
		return captain == null ? null : all(server).get(captain.toString());
	}

	public static void put(MinecraftServer server, UUID captain, HomeShip home) {
		Map<String, HomeShip> map = new HashMap<>(all(server));
		map.put(captain.toString(), home);
		server.overworld().setAttached(HOME_SHIPS, map);
	}

	public static void remove(MinecraftServer server, UUID captain) {
		Map<String, HomeShip> map = new HashMap<>(all(server));
		if (map.remove(captain.toString()) != null) {
			server.overworld().setAttached(HOME_SHIPS, map);
		}
	}

	/** True if this homeId is still the captain's home ship (an old log left behind after a move is not). */
	public static boolean isCurrent(MinecraftServer server, UUID captain, UUID homeId) {
		HomeShip home = of(server, captain);
		return home != null && homeId != null && home.homeId().equals(homeId);
	}
}
