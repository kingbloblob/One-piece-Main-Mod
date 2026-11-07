package com.onepiecemod.arena;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.util.RandomSource;

import com.onepiecemod.crew.CrewPersonality;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewVariant;
import com.onepiecemod.npc.NpcNames;

/**
 * The pirate crew on the other side of a Davy Back Fight: a captain and a few members you can win.
 * Each member has a crew role, so a member you win joins your crew as a normal crewmate for that role.
 */
public class RivalCrew {
	/** One member you could win. `taken` points at one of your own crewmates they won earlier (null = their own). */
	public static class Member {
		final String name;
		final CrewRole role;
		final int variant;
		final CrewPersonality personality;
		final int level;
		final ArenaRecord.Taken taken;

		Member(String name, CrewRole role, int variant, CrewPersonality personality, int level, ArenaRecord.Taken taken) {
			this.name = name;
			this.role = role;
			this.variant = variant;
			this.personality = personality;
			this.level = level;
			this.taken = taken;
		}

		String fullName() {
			return taken != null ? taken.name() : role.title() + " " + name;
		}
	}

	private record Famous(String crew, String captain, String[] members) {}

	/** Rival crews that answer a Davy Back Flag. Foxy has his own (see foxy()). */
	private static final Famous[] FAMOUS = {
			new Famous("Bellamy Pirates", "Bellamy the Hyena", new String[] {"Sarquiss", "Muchi", "Lilly", "Eddy"}),
			new Famous("Bluejam Pirates", "Captain Bluejam", new String[] {"Porchemy", "Gal", "Rindo", "Mesa"}),
			new Famous("Krieg Pirates", "Don Krieg", new String[] {"Gin", "Pearl", "Kagi", "Patty"}),
			new Famous("Caribou Pirates", "Caribou the Wet-Haired", new String[] {"Coribou", "Duro", "Kepp", "Lorna"}),
			new Famous("Fallen Monk Pirates", "Urouge the Mad Monk", new String[] {"Taji", "Bonsai", "Hoji", "Rin"}),
			new Famous("Kuja Rivals", "Captain Sandersonia", new String[] {"Daisy", "Kikyo", "Ran", "Belladonna"}),
	};

	final String crewName;
	final String captainName;
	final boolean foxy;
	/** 0-4 from the player's threat level: tougher rivals for famous pirates. */
	final int tier;
	final List<Member> members = new ArrayList<>();

	private RivalCrew(String crewName, String captainName, boolean foxy, int tier) {
		this.crewName = crewName;
		this.captainName = captainName;
		this.foxy = foxy;
		this.tier = tier;
	}

	/** The Foxy Pirates of Long Ring Long Land, from the show. */
	public static RivalCrew foxy(int tier, List<ArenaRecord.Taken> yours, RandomSource random) {
		RivalCrew rival = new RivalCrew("Foxy Pirates", "Foxy the Silver Fox", true, Math.max(1, tier));
		rival.add("Porche", CrewRole.MUSICIAN, random);
		rival.add("Hamburg", CrewRole.SHIPWRIGHT, random);
		rival.add("Pickles", CrewRole.SWORDSMAN, random);
		rival.add("Big Pan", CrewRole.COOK, random);
		rival.add("Capote", CrewRole.SNIPER, random);
		rival.addYours(yours);
		return rival;
	}

	public static RivalCrew random(int tier, List<ArenaRecord.Taken> yours, RandomSource random) {
		Famous famous = FAMOUS[random.nextInt(FAMOUS.length)];
		boolean madeUp = random.nextInt(3) == 0;
		String crew = madeUp ? NpcNames.crew(random) : famous.crew();
		String captain = madeUp ? "Captain " + NpcNames.first(random) : famous.captain();
		RivalCrew rival = new RivalCrew(crew, captain, false, tier);
		List<CrewRole> roles = new ArrayList<>(List.of(CrewRole.values()));
		for (String name : famous.members()) {
			rival.add(name, roles.remove(random.nextInt(roles.size())), random);
		}
		rival.addYours(yours);
		return rival;
	}

	private void add(String name, CrewRole role, RandomSource random) {
		CrewPersonality[] all = CrewPersonality.values();
		int level = 1 + random.nextInt(2 + tier);
		members.add(new Member(name, role, random.nextInt(CrewVariant.COUNT), all[random.nextInt(all.length)], Math.min(10, level), null));
	}

	/** Crewmates other crews won from you turn up again, so you can win them back (at most two per fight). */
	private void addYours(List<ArenaRecord.Taken> yours) {
		int added = 0;
		for (ArenaRecord.Taken taken : yours) {
			CrewRole role = CrewRole.byId(taken.role());
			CrewPersonality personality = CrewPersonality.byName(taken.personality());
			if (role == null || added >= 2) {
				continue;
			}
			members.add(0, new Member(taken.name(), role, taken.variant(),
					personality != null ? personality : CrewPersonality.values()[0], taken.level(), taken));
			added++;
		}
	}

	/** Adds a crewmate this crew just won from the player, so the player can win them back in the same fight. */
	void addWon(ArenaRecord.Taken taken) {
		CrewRole role = CrewRole.byId(taken.role());
		CrewPersonality personality = CrewPersonality.byName(taken.personality());
		if (role != null) {
			members.add(0, new Member(taken.name(), role, taken.variant(),
					personality != null ? personality : CrewPersonality.values()[0], taken.level(), taken));
		}
	}

	/** How much tougher this crew's fighters are than the base NPC kits. */
	double strength() {
		return 1.0 + 0.45 * tier;
	}
}
