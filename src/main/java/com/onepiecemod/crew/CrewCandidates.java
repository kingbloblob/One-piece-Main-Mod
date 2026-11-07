package com.onepiecemod.crew;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Random;

import net.minecraft.server.level.ServerPlayer;

/**
 * The recruits waiting at the tavern. For every role there are 3 candidates: one of each kind
 * (see CrewVariant), each with a random name and personality.
 *
 * Candidates are worked out from the captain, the role, the day and how many people the captain
 * has hired, so the same 3 people wait all day and a fresh set shows up every Minecraft day
 * (and after every hire). Nothing needs to be saved.
 */
public class CrewCandidates {
	private static final String[] FIRST_NAMES = {
			"Kenji", "Mira", "Bastian", "Coral", "Rook", "Nell", "Haru", "Ines", "Dorian", "Saki",
			"Tobias", "Lark", "Oren", "Pip", "Wren", "Gale", "Jory", "Kai", "Marlo", "Tess",
			"Bram", "Yuki", "Fen", "Rosa", "Ike", "Sela", "Dax", "Momo", "Garo", "Lio"
	};

	/** One recruit you could hire. */
	public record Candidate(CrewRole role, int variantIndex, CrewVariant variant, CrewPersonality personality,
			String name, int price, int health, int damage) {
		public String fullName() {
			return role.title() + " " + name;
		}
	}

	/**
	 * A code for "today's recruits for this captain". It changes every Minecraft day and after every hire,
	 * exactly when the candidates change. Hire buttons carry it, so an old list can't hire a new person.
	 */
	public static int listCode(ServerPlayer captain, Crew crew) {
		return Math.floorMod(Objects.hash(captain.level().getGameTime() / 24000L, crew.hires()), 1_000_000);
	}

	public static List<Candidate> forRole(ServerPlayer captain, Crew crew, CrewRole role) {
		long day = captain.level().getGameTime() / 24000L; // A Minecraft day is 24,000 ticks.
		int basePrice = CrewHiring.cost(crew.hires());
		List<Candidate> candidates = new ArrayList<>();
		for (int i = 0; i < CrewVariant.COUNT; i++) {
			Random random = new Random(Objects.hash(captain.getUUID(), role.ordinal(), i, day, crew.hires()));
			CrewVariant variant = CrewVariant.of(role, i);
			CrewPersonality personality = CrewPersonality.values()[random.nextInt(CrewPersonality.values().length)];
			String name = FIRST_NAMES[random.nextInt(FIRST_NAMES.length)];
			int price = (int) Math.round(basePrice * variant.costMultiplier() * personality.costMultiplier());
			int health = (int) Math.round(role.health() * variant.healthMultiplier() * personality.healthMultiplier());
			int damage = (int) Math.round(role.damage() * variant.damageMultiplier() * personality.damageMultiplier());
			candidates.add(new Candidate(role, i, variant, personality, name, Math.max(1, price), health, Math.max(1, damage)));
		}
		return candidates;
	}
}
