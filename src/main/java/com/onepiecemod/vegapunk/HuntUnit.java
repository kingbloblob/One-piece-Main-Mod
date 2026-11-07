package com.onepiecemod.vegapunk;

import net.minecraft.world.BossEvent;

import com.onepiecemod.npc.CombatStyle;

/**
 * The roaming mini-bosses Vegapunk built for the World Government.
 *
 * Pacifista are the "Kuma copies" first seen at Sabaody: walking laser cannons. The Mark III is the giant model from
 * Egghead. The Seraphim are Lunarian children grown from the lineage factor of famous fighters, so each one fights like
 * its original: S-Bear (Kuma), S-Hawk (Mihawk), S-Snake (Hancock) and S-Shark (Jinbe).
 *
 * Every unit is a normal Marine NPC (onepiece:marine) dressed from its kit, then made tougher and given signature moves
 * by VegapunkHunts.
 */
public enum HuntUnit {
	PACIFISTA("pacifista", "Pacifista PX-%d", "pacifista", null, false, 1,
			260, 14, 14, 3.83f, CombatStyle.BEAM, BossEvent.BossBarColor.YELLOW, 8,
			"A heavy clank of metal footsteps...", "Target confirmed. Eliminating."),
	MARK_III("mark_iii", "Pacifista Mark III", "pacifista", null, false, 3,
			420, 18, 16, 4.5f, CombatStyle.HEAVY, BossEvent.BossBarColor.YELLOW, 3,
			"The ground shakes. Something huge is walking this way.", "TARGET. LOCKED."),
	S_BEAR("s_bear", "Seraphim S-Bear", "seraphim", "seraphim_s_2", true, 4,
			520, 18, 14, 1.65f, CombatStyle.BRAWLER, BossEvent.BossBarColor.PURPLE, 3,
			"Black wings flash overhead. A Seraphim has found you.", "Where would you like to go on a trip?"),
	S_HAWK("s_hawk", "Seraphim S-Hawk", "seraphim", "seraphim_s_0", true, 4,
			480, 19, 12, 1.6f, CombatStyle.SWORD, BossEvent.BossBarColor.PURPLE, 3,
			"Black wings flash overhead. A Seraphim has found you.", "Your blade is dull. Mine is not."),
	S_SNAKE("s_snake", "Seraphim S-Snake", "seraphim", "seraphim_s_1", true, 4,
			460, 17, 12, 1.6f, CombatStyle.BRAWLER, BossEvent.BossBarColor.PURPLE, 3,
			"Black wings flash overhead. A Seraphim has found you.", "Kneel. You are not worthy to look at me."),
	S_SHARK("s_shark", "Seraphim S-Shark", "seraphim", "seraphim_s_3", true, 4,
			500, 18, 13, 1.65f, CombatStyle.FISHMAN, BossEvent.BossBarColor.PURPLE, 3,
			"Black wings flash overhead. A Seraphim has found you.", "Fish-Man Karate. Prepare yourself.");

	public final String id;
	/** Display name; %d is filled with a serial number for Pacifista. */
	public final String name;
	/** NPC kit (npc_kits.json) the unit is dressed from. */
	public final String kit;
	/** A fixed skin (textures/entity/npc/...), or null to keep the kit's random one. */
	public final String skin;
	public final boolean seraphim;
	/** 1 = Paradise (from Sabaody on), 3 = New World, 4 = New World after Wano (Egghead era). */
	public final int tier;
	public final double health;
	public final double damage;
	public final double armor;
	public final float scale;
	public final CombatStyle style;
	public final BossEvent.BossBarColor barColor;
	/** How often this unit is picked compared to the others that may appear. */
	public final int weight;
	/** What the hunted player reads when it arrives, and what it says when it sees them. */
	public final String arrival;
	public final String line;

	HuntUnit(String id, String name, String kit, String skin, boolean seraphim, int tier, double health, double damage, double armor,
			float scale, CombatStyle style, BossEvent.BossBarColor barColor, int weight, String arrival, String line) {
		this.id = id;
		this.name = name;
		this.kit = kit;
		this.skin = skin;
		this.seraphim = seraphim;
		this.tier = tier;
		this.health = health;
		this.damage = damage;
		this.armor = armor;
		this.scale = scale;
		this.style = style;
		this.barColor = barColor;
		this.weight = weight;
		this.arrival = arrival;
		this.line = line;
	}

	public static HuntUnit byId(String id) {
		for (HuntUnit unit : values()) {
			if (unit.id.equals(id)) {
				return unit;
			}
		}
		return null;
	}
}
