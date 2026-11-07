package com.onepiecemod.bounty;

import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;

/**
 * The kinds of Marine that hunt pirates. Change the numbers here to make them tougher or weaker.
 * Each rank has its own skin: assets/onepiece/textures/entity/marine/<id>.png
 */
public enum MarineRank {
	//          id           name                  health damage weapon            shoots  bounty for beating  berries dropped
	RECRUIT("recruit", "Marine Recruit", 20, 4, Items.IRON_SWORD, false, 200_000L, 1),
	RIFLEMAN("rifleman", "Marine Rifleman", 20, 2, Items.BOW, true, 200_000L, 1),
	LIEUTENANT("lieutenant", "Marine Lieutenant", 40, 7, Items.IRON_SWORD, false, 1_000_000L, 3),
	CAPTAIN("captain", "Marine Captain", 80, 10, Items.DIAMOND_SWORD, false, 3_000_000L, 8);

	private final String id;
	public final String displayName;
	public final double health;
	public final double damage;
	public final Item weapon;
	public final boolean ranged;
	/** How much the pirate's bounty rises for beating this Marine. */
	public final long bountyReward;
	public final int berries;

	MarineRank(String id, String displayName, double health, double damage, Item weapon, boolean ranged, long bountyReward, int berries) {
		this.id = id;
		this.displayName = displayName;
		this.health = health;
		this.damage = damage;
		this.weapon = weapon;
		this.ranged = ranged;
		this.bountyReward = bountyReward;
		this.berries = berries;
	}

	public String id() {
		return id;
	}

	public static MarineRank byId(String id) {
		for (MarineRank rank : values()) {
			if (rank.id.equals(id)) {
				return rank;
			}
		}
		return RECRUIT;
	}
}
