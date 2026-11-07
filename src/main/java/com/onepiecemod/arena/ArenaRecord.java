package com.onepiecemod.arena;

import java.util.ArrayList;
import java.util.List;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

/**
 * A player's arena history, saved on the player.
 *
 * @param corridaBest highest Corrida cup won (-1 = none yet, 0 Rookie, 1 Veteran, 2 Champion)
 * @param corridaWins how many Corrida tournaments the player has won in total
 * @param dbfWins     Davy Back Fights won (2 of the 3 games)
 * @param dbfLosses   Davy Back Fights lost
 * @param taken       crewmates that rival crews won from this player, waiting to be won back
 * @param foxyDay     the last Minecraft day the Foxy Pirates challenged this player at Long Ring Long Land
 * @param foxyBeaten  true once the player has won a Davy Back Fight against Foxy
 */
public record ArenaRecord(int corridaBest, int corridaWins, int dbfWins, int dbfLosses, List<Taken> taken, long foxyDay,
		boolean foxyBeaten) {

	/** A crewmate a rival crew took in a Davy Back Fight. Everything needed to bring them back as they were. */
	public record Taken(String role, int variant, String personality, String name, int level, String heldBy) {
		public static final Codec<Taken> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				Codec.STRING.fieldOf("role").forGetter(Taken::role),
				Codec.INT.fieldOf("variant").forGetter(Taken::variant),
				Codec.STRING.fieldOf("personality").forGetter(Taken::personality),
				Codec.STRING.fieldOf("name").forGetter(Taken::name),
				Codec.INT.fieldOf("level").forGetter(Taken::level),
				Codec.STRING.fieldOf("heldBy").forGetter(Taken::heldBy)
		).apply(instance, Taken::new));
	}

	public static final Codec<ArenaRecord> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.INT.optionalFieldOf("corridaBest", -1).forGetter(ArenaRecord::corridaBest),
			Codec.INT.optionalFieldOf("corridaWins", 0).forGetter(ArenaRecord::corridaWins),
			Codec.INT.optionalFieldOf("dbfWins", 0).forGetter(ArenaRecord::dbfWins),
			Codec.INT.optionalFieldOf("dbfLosses", 0).forGetter(ArenaRecord::dbfLosses),
			Taken.CODEC.listOf().optionalFieldOf("taken", List.of()).forGetter(ArenaRecord::taken),
			Codec.LONG.optionalFieldOf("foxyDay", -1L).forGetter(ArenaRecord::foxyDay),
			Codec.BOOL.optionalFieldOf("foxyBeaten", false).forGetter(ArenaRecord::foxyBeaten)
	).apply(instance, ArenaRecord::new));

	public static final ArenaRecord EMPTY = new ArenaRecord(-1, 0, 0, 0, List.of(), -1L, false);

	public ArenaRecord withCorridaWin(int tier) {
		return new ArenaRecord(Math.max(corridaBest, tier), corridaWins + 1, dbfWins, dbfLosses, taken, foxyDay, foxyBeaten);
	}

	public ArenaRecord withFight(boolean won, boolean beatFoxy) {
		return new ArenaRecord(corridaBest, corridaWins, dbfWins + (won ? 1 : 0), dbfLosses + (won ? 0 : 1), taken, foxyDay,
				foxyBeaten || beatFoxy);
	}

	public ArenaRecord withTaken(Taken crewmate) {
		List<Taken> list = new ArrayList<>(taken);
		list.add(crewmate);
		return new ArenaRecord(corridaBest, corridaWins, dbfWins, dbfLosses, list, foxyDay, foxyBeaten);
	}

	public ArenaRecord withoutTaken(Taken crewmate) {
		List<Taken> list = new ArrayList<>(taken);
		list.remove(crewmate);
		return new ArenaRecord(corridaBest, corridaWins, dbfWins, dbfLosses, list, foxyDay, foxyBeaten);
	}

	public ArenaRecord withFoxyDay(long day) {
		return new ArenaRecord(corridaBest, corridaWins, dbfWins, dbfLosses, taken, day, foxyBeaten);
	}
}
