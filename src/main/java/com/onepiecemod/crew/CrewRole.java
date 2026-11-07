package com.onepiecemod.crew;

import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/**
 * The nine jobs on a pirate ship, just like the Straw Hat crew.
 * A captain can hire one crewmate for each role.
 *
 * Each role has:
 * - minCrew: how many crewmates you need before this role will join you (late joiners in the story need more).
 * - a trial item: what the recruit asks for to prove you're worth following.
 * - health and damage for the crewmate, and the weapon they carry.
 * - a job they do in Work mode (see the job package).
 * - a perk the captain gets while that crewmate is nearby.
 */
public enum CrewRole {
	SWORDSMAN("swordsman", "Swordsman", "Like Zoro", 0, Items.IRON_SWORD, 3, 34, 3, Items.IRON_SWORD, "guarding this spot",
			"Strength I"),
	NAVIGATOR("navigator", "Navigator", "Like Nami", 0, Items.MAP, 1, 24, 3, Items.BLAZE_ROD, "watching the weather and making maps",
			"Speed I"),
	SNIPER("sniper", "Sniper", "Like Usopp", 0, Items.ARROW, 32, 24, 2, Items.BOW, "keeping lookout from this spot",
			"Nearby monsters glow so you can see them"),
	COOK("cook", "Cook", "Like Sanji", 0, Items.CAKE, 1, 30, 6, Items.AIR, "farming and cooking",
			"Slowly refills your hunger"),
	DOCTOR("doctor", "Doctor", "Like Chopper", 0, Items.GOLDEN_APPLE, 2, 26, 3, Items.AIR, "running an infirmary here",
			"Regeneration when you are below half health; heals the crew"),
	SHIPWRIGHT("shipwright", "Shipwright", "Like Franky", 3, Items.IRON_BLOCK, 4, 36, 2, Items.IRON_AXE, "repairing gear and fixing the place up",
			"Haste I"),
	ARCHAEOLOGIST("archaeologist", "Archaeologist", "Like Robin", 4, Items.BOOK, 8, 26, 4, Items.AIR, "digging and studying here",
			"Luck I (better loot)"),
	MUSICIAN("musician", "Musician", "Like Brook", 5, Items.JUKEBOX, 1, 28, 3, Items.IRON_SWORD, "playing music for the crops",
			"Resistance I for you and the crew"),
	HELMSMAN("helmsman", "Helmsman", "Like Jinbe", 6, Items.HEART_OF_THE_SEA, 1, 40, 7, Items.AIR, "fishing and watching the water",
			"Water Breathing and Dolphin's Grace");

	private final String id;
	private final String title;
	private final String inspiredBy;
	private final int minCrew;
	private final Item trialItem;
	private final int trialCount;
	private final double health;
	private final double damage;
	private final Item weapon;
	private final String job;
	private final String perk;

	CrewRole(String id, String title, String inspiredBy, int minCrew, Item trialItem, int trialCount,
			double health, double damage, Item weapon, String job, String perk) {
		this.id = id;
		this.title = title;
		this.inspiredBy = inspiredBy;
		this.minCrew = minCrew;
		this.trialItem = trialItem;
		this.trialCount = trialCount;
		this.health = health;
		this.damage = damage;
		this.weapon = weapon;
		this.job = job;
		this.perk = perk;
	}

	public String id() { return id; }
	public String title() { return title; }
	public String inspiredBy() { return inspiredBy; }
	public int minCrew() { return minCrew; }
	public Item trialItem() { return trialItem; }
	public int trialCount() { return trialCount; }
	public double health() { return health; }
	public double damage() { return damage; }
	public ItemStack weapon() { return new ItemStack(weapon); }
	/** What this role does in Work mode, like "farming and cooking". */
	public String job() { return job; }
	public String perk() { return perk; }

	/** Finds a role from its id, like "cook". Returns null if there is no such role. */
	public static CrewRole byId(String id) {
		for (CrewRole role : values()) {
			if (role.id.equals(id)) {
				return role;
			}
		}
		return null;
	}
}
