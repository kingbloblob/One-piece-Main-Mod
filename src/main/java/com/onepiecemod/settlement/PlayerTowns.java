package com.onepiecemod.settlement;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * Every player-founded town, saved on the Overworld: owner uuid -> town. One town per player.
 */
public final class PlayerTowns {
	/** How far from the town bell plots may go (flat distance). */
	public static final int RADIUS = 48;
	/** Town bells must be at least this far apart. */
	public static final int SPACING = 128;

	/** A marked-out plot: a box from min to max (inclusive), floor at min.y. */
	public record Plot(String kind, BlockPos min, BlockPos max) {
		public static final Codec<Plot> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				Codec.STRING.fieldOf("kind").forGetter(Plot::kind),
				BlockPos.CODEC.fieldOf("min").forGetter(Plot::min),
				BlockPos.CODEC.fieldOf("max").forGetter(Plot::max)
		).apply(instance, Plot::new));

		public PlotKind type() {
			return PlotKind.byName(kind);
		}

		public boolean contains(BlockPos pos) {
			return pos.getX() >= min.getX() && pos.getX() <= max.getX() && pos.getZ() >= min.getZ() && pos.getZ() <= max.getZ()
					&& pos.getY() >= min.getY() - 2 && pos.getY() <= max.getY();
		}

		public boolean overlaps(Plot other) {
			return min.getX() <= other.max.getX() && max.getX() >= other.min.getX()
					&& min.getZ() <= other.max.getZ() && max.getZ() >= other.min.getZ();
		}
	}

	/**
	 * One town.
	 * @param treasury   Berries from rent, waiting to be collected (or spent on upgrades)
	 * @param lastRentDay the last day rent was paid
	 * @param upgrades   town upgrades bought (see {@link Settlements.TownUpgrade})
	 */
	public record PlayerTown(String ownerName, String name, String culture, BlockPos bell, List<Plot> plots, long treasury,
			long lastRentDay, List<String> upgrades) {
		public static final Codec<PlayerTown> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				Codec.STRING.optionalFieldOf("owner_name", "").forGetter(PlayerTown::ownerName),
				Codec.STRING.optionalFieldOf("name", "New Town").forGetter(PlayerTown::name),
				Codec.STRING.optionalFieldOf("culture", "east_blue").forGetter(PlayerTown::culture),
				BlockPos.CODEC.fieldOf("bell").forGetter(PlayerTown::bell),
				Plot.CODEC.listOf().optionalFieldOf("plots", List.of()).forGetter(PlayerTown::plots),
				Codec.LONG.optionalFieldOf("treasury", 0L).forGetter(PlayerTown::treasury),
				Codec.LONG.optionalFieldOf("last_rent_day", -1L).forGetter(PlayerTown::lastRentDay),
				Codec.STRING.listOf().optionalFieldOf("upgrades", List.of()).forGetter(PlayerTown::upgrades)
		).apply(instance, PlayerTown::new));

		public PlayerTown withPlots(List<Plot> list) {
			return new PlayerTown(ownerName, name, culture, bell, List.copyOf(list), treasury, lastRentDay, upgrades);
		}

		public PlayerTown withName(String newName) {
			return new PlayerTown(ownerName, newName, culture, bell, plots, treasury, lastRentDay, upgrades);
		}

		public PlayerTown withCulture(String newCulture) {
			return new PlayerTown(ownerName, name, newCulture, bell, plots, treasury, lastRentDay, upgrades);
		}

		public PlayerTown withTreasury(long amount, long day) {
			return new PlayerTown(ownerName, name, culture, bell, plots, amount, day, upgrades);
		}

		public PlayerTown withUpgrade(String id) {
			List<String> list = new ArrayList<>(upgrades);
			list.add(id);
			return new PlayerTown(ownerName, name, culture, bell, plots, treasury, lastRentDay, List.copyOf(list));
		}

		public boolean inRange(BlockPos pos) {
			double dx = pos.getX() - bell.getX();
			double dz = pos.getZ() - bell.getZ();
			return dx * dx + dz * dz <= RADIUS * RADIUS && Math.abs(pos.getY() - bell.getY()) <= 32;
		}

		public Plot plotAt(BlockPos pos) {
			for (Plot plot : plots) {
				if (plot.contains(pos)) {
					return plot;
				}
			}
			return null;
		}
	}

	public static final AttachmentType<Map<String, PlayerTown>> TOWNS = AttachmentRegistry.create(
			OnePieceMod.id("player_towns"),
			builder -> builder.persistent(Codec.unboundedMap(Codec.STRING, PlayerTown.CODEC)));

	private PlayerTowns() {
	}

	public static Map<String, PlayerTown> all(MinecraftServer server) {
		return server.overworld().getAttachedOrElse(TOWNS, Map.of());
	}

	public static PlayerTown of(MinecraftServer server, UUID owner) {
		return owner == null ? null : all(server).get(owner.toString());
	}

	public static void put(MinecraftServer server, UUID owner, PlayerTown town) {
		Map<String, PlayerTown> map = new HashMap<>(all(server));
		map.put(owner.toString(), town);
		server.overworld().setAttached(TOWNS, map);
	}

	public static void remove(MinecraftServer server, UUID owner) {
		Map<String, PlayerTown> map = new HashMap<>(all(server));
		if (map.remove(owner.toString()) != null) {
			server.overworld().setAttached(TOWNS, map);
		}
	}

	/** Whose town has its bell at this spot, or null. */
	public static UUID ownerOfBell(MinecraftServer server, BlockPos pos) {
		for (Map.Entry<String, PlayerTown> entry : all(server).entrySet()) {
			if (entry.getValue().bell().equals(pos)) {
				return UUID.fromString(entry.getKey());
			}
		}
		return null;
	}

	/** The town (owner uuid) whose plotting range this spot is in, or null. */
	public static UUID townAt(MinecraftServer server, BlockPos pos) {
		for (Map.Entry<String, PlayerTown> entry : all(server).entrySet()) {
			if (entry.getValue().inRange(pos)) {
				return UUID.fromString(entry.getKey());
			}
		}
		return null;
	}
}
