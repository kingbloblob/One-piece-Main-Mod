package com.onepiecemod.vegapunk;

import java.util.List;

/**
 * Franky-style body upgrades. Each has three tiers; every tier is one module installed by right-clicking it.
 * Tier II also uses up a Vegapunk Chip, tier III two chips and a Seraphim Feather (see Cyborg.installCost).
 */
public enum CyborgUpgrade {
	IRON_FRAME("iron_frame", "iron_frame_plating", "Iron Frame", false,
			List.of("+2 armour, +1 toughness", "+4 armour, +2 toughness", "+6 armour, +3 toughness, hard to knock back")),
	STRONG_RIGHT("strong_right", "strong_right_arm", "Strong Right Arm", false,
			List.of("+1 attack, +1.5 more bare-handed", "+2 attack, +3 more bare-handed", "+3 attack, +4.5 more bare-handed")),
	COLA_ENGINE("cola_engine", "cola_engine_core", "Cola Engine", false,
			List.of("Holds 3 Colas of fuel, faster sprint", "Holds 6 Colas, faster sprint", "Holds 9 Colas, fastest sprint")),
	RADICAL_BEAM("radical_beam", "radical_beam_emitter", "Radical Beam", false,
			List.of("C: laser beam (1 Cola)", "Stronger, longer beam", "Strongest beam, quicker to recharge")),
	COUP_DE_VENT("coup_de_vent", "coup_de_vent_cannon", "Coup de Vent", false,
			List.of("Sneak + C: air cannon blast (half a Cola)", "Harder blast; look down to boost up", "Hardest blast, biggest boost")),
	LUNARIAN_PLATING("lunarian_plating", "lunarian_plating", "Lunarian Plating", true,
			List.of("Shrugs off a third of fire", "Shrugs off two thirds of fire; flame armour when hurt",
					"Fire and lava can't hurt you; glide while sneaking in the air"));

	public static final int MAX_TIER = 3;

	public final String id;
	public final String itemId;
	public final String title;
	/** Made from Seraphim Feathers, so only after the first Seraphim hunt. */
	public final boolean needsFeather;
	/** What each tier gives, for tooltips and /cyborg. */
	public final List<String> tiers;

	CyborgUpgrade(String id, String itemId, String title, boolean needsFeather, List<String> tiers) {
		this.id = id;
		this.itemId = itemId;
		this.title = title;
		this.needsFeather = needsFeather;
		this.tiers = tiers;
	}

	public static CyborgUpgrade byId(String id) {
		for (CyborgUpgrade upgrade : values()) {
			if (upgrade.id.equals(id)) {
				return upgrade;
			}
		}
		return null;
	}
}
