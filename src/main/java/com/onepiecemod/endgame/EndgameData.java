package com.onepiecemod.endgame;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * Everything the endgame remembers about a player. Saved on the player and kept when they die.
 *
 * @param cycle       0 for the first playthrough, 1 for New Game+ 1, and so on.
 * @param flags       one-time things in this cycle: "finale" (Laugh Tale finale played), "final_war" (Final War started).
 * @param timers      game times: "raid:<id>" = when that raid gives full loot again, "final_war" = when the Final War comes.
 * @param cleared     raids won at least once, in any cycle.
 * @param cycleBosses bosses beaten in this New Game+ cycle (story boss goals and fruit drops in NG+ use it).
 * @param selected    the raid the Raid Den Den Mushi is tuned to.
 */
public record EndgameData(int cycle, List<String> flags, Map<String, Long> timers, List<String> cleared,
		List<String> cycleBosses, String selected) {
	public static final EndgameData EMPTY = new EndgameData(0, List.of(), Map.of(), List.of(), List.of(), "");

	public static final Codec<EndgameData> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.INT.optionalFieldOf("cycle", 0).forGetter(EndgameData::cycle),
			Codec.STRING.listOf().optionalFieldOf("flags", List.of()).forGetter(EndgameData::flags),
			Codec.unboundedMap(Codec.STRING, Codec.LONG).optionalFieldOf("timers", Map.of()).forGetter(EndgameData::timers),
			Codec.STRING.listOf().optionalFieldOf("cleared", List.of()).forGetter(EndgameData::cleared),
			Codec.STRING.listOf().optionalFieldOf("cycle_bosses", List.of()).forGetter(EndgameData::cycleBosses),
			Codec.STRING.optionalFieldOf("selected", "").forGetter(EndgameData::selected)
	).apply(instance, EndgameData::new));

	public static final AttachmentType<EndgameData> DATA = AttachmentRegistry.create(
			OnePieceMod.id("endgame"),
			builder -> builder.persistent(CODEC).copyOnDeath()
	);

	public static EndgameData of(Player player) {
		return player.getAttachedOrElse(DATA, EMPTY);
	}

	public static void set(Player player, EndgameData data) {
		player.setAttached(DATA, data);
	}

	public boolean hasFlag(String flag) {
		return flags.contains(flag);
	}

	public EndgameData withFlag(String flag) {
		if (flags.contains(flag)) {
			return this;
		}
		List<String> list = new ArrayList<>(flags);
		list.add(flag);
		return new EndgameData(cycle, list, timers, cleared, cycleBosses, selected);
	}

	public long timer(String key) {
		return timers.getOrDefault(key, 0L);
	}

	public EndgameData withTimer(String key, long time) {
		Map<String, Long> map = new HashMap<>(timers);
		map.put(key, time);
		return new EndgameData(cycle, flags, map, cleared, cycleBosses, selected);
	}

	public EndgameData withCleared(String raid) {
		if (cleared.contains(raid)) {
			return this;
		}
		List<String> list = new ArrayList<>(cleared);
		list.add(raid);
		return new EndgameData(cycle, flags, timers, list, cycleBosses, selected);
	}

	public EndgameData withCycleBoss(String boss) {
		if (cycleBosses.contains(boss)) {
			return this;
		}
		List<String> list = new ArrayList<>(cycleBosses);
		list.add(boss);
		return new EndgameData(cycle, flags, timers, cleared, list, selected);
	}

	public EndgameData withSelected(String raid) {
		return new EndgameData(cycle, flags, timers, cleared, cycleBosses, raid);
	}

	/** The start of a new cycle: one higher, and this cycle's flags, Final War timer and bosses forgotten. */
	public EndgameData nextCycle() {
		Map<String, Long> map = new HashMap<>(timers);
		map.remove("final_war");
		return new EndgameData(cycle + 1, List.of(), map, cleared, List.of(), selected);
	}

	public EndgameData withCycle(int newCycle) {
		return new EndgameData(newCycle, flags, timers, cleared, cycleBosses, selected);
	}
}
