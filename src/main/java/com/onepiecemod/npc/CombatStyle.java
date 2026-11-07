package com.onepiecemod.npc;

/**
 * How a pirate or Marine NPC fights. Each NPC gets one from its kit's loadouts (npc_kits.json).
 * The special moves themselves are in HumanNpc.
 */
public enum CombatStyle {
	//         id           ranged  chase  shots: min max ticks, range
	SWORD("sword", false, 1.25, 0, 0, 0f),          // lunges at you, officers throw flying slashes
	BRAWLER("brawler", false, 1.3, 0, 0, 0f),       // bare fists, every third punch is a big knockback haymaker
	HEAVY("heavy", false, 1.0, 0, 0, 0f),           // axes, maces and jitte: hits slow you, ground slam up close
	HAKI("haki", false, 1.2, 0, 0, 0f),             // Armament Haki hits harder, Observation Haki dodges some hits
	ROKUSHIKI("rokushiki", false, 1.3, 0, 0, 0f),   // CP agents: Soru (blink next to you), Tekkai (block), Geppo (air jump)
	FISHMAN("fishman", false, 1.2, 0, 0, 0f),       // Fish-Man Karate: strong shoves and water shots from range
	GUNNER("gunner", true, 1.0, 25, 45, 16f),       // pistols and tommy guns
	SNIPER("sniper", true, 1.0, 60, 90, 30f),       // rifles from far away, hits hard
	BOMBER("bomber", true, 1.0, 50, 70, 12f),       // lobs bombs that explode after a second (no block damage)
	BEAM("beam", true, 0.9, 60, 80, 20f);           // Pacifista and Seraphim laser beams

	public final String id;
	public final boolean ranged;
	public final double chaseSpeed;
	public final int minInterval;
	public final int maxInterval;
	public final float range;

	CombatStyle(String id, boolean ranged, double chaseSpeed, int minInterval, int maxInterval, float range) {
		this.id = id;
		this.ranged = ranged;
		this.chaseSpeed = chaseSpeed;
		this.minInterval = minInterval;
		this.maxInterval = maxInterval;
		this.range = range;
	}

	public static CombatStyle byId(String id) {
		for (CombatStyle style : values()) {
			if (style.id.equals(id)) {
				return style;
			}
		}
		return SWORD;
	}
}
