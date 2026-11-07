package com.onepiecemod.building;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.core.BlockPos;
import net.minecraft.core.UUIDUtil;
import net.minecraft.server.level.ServerLevel;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * Remembers where every building core was placed, saved with each world (dimension).
 * That way buildings keep working after a restart, and the Den Den Mushi Relay can find
 * your other relays. If a core gets broken, its entry is dropped the next time it's looked at.
 */
public class BuildingRegistry {
	/**
	 * One placed building.
	 *
	 * @param type    the building's id, like "den_den_relay"
	 * @param owner   the player who placed the core
	 * @param lastDay the last in-game day the building paid out (shipyard stock, feast...)
	 */
	public record Entry(String type, BlockPos pos, UUID owner, long lastDay) {
		public static final Codec<Entry> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				Codec.STRING.fieldOf("type").forGetter(Entry::type),
				BlockPos.CODEC.fieldOf("pos").forGetter(Entry::pos),
				UUIDUtil.CODEC.fieldOf("owner").forGetter(Entry::owner),
				Codec.LONG.optionalFieldOf("last_day", -1L).forGetter(Entry::lastDay)
		).apply(instance, Entry::new));

		public Entry withLastDay(long day) {
			return new Entry(type, pos, owner, day);
		}
	}

	public static final AttachmentType<List<Entry>> BUILDINGS = AttachmentRegistry.create(
			OnePieceMod.id("buildings"),
			builder -> builder.persistent(Entry.CODEC.listOf())
	);

	public static List<Entry> all(ServerLevel level) {
		return level.getAttachedOrElse(BUILDINGS, List.of());
	}

	public static Entry at(ServerLevel level, BlockPos pos) {
		for (Entry entry : all(level)) {
			if (entry.pos().equals(pos)) {
				return entry;
			}
		}
		return null;
	}

	/** Adds (or replaces) the building at this spot. */
	public static void put(ServerLevel level, Entry entry) {
		List<Entry> list = new ArrayList<>(all(level));
		list.removeIf(old -> old.pos().equals(entry.pos()));
		list.add(entry);
		level.setAttached(BUILDINGS, list);
	}

	public static void remove(ServerLevel level, BlockPos pos) {
		List<Entry> list = new ArrayList<>(all(level));
		if (list.removeIf(old -> old.pos().equals(pos))) {
			level.setAttached(BUILDINGS, list);
		}
	}

	/** The in-game day number, counting from the start of the world. */
	public static long day(ServerLevel level) {
		return level.getGameTime() / 24000L;
	}
}
