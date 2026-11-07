package com.onepiecemod.ship;

import net.minecraft.world.level.block.state.BlockState;

/**
 * Upgrades fitted to a ship at a Galley-La Shipyard, stored on its Ship's Wheel (HelmBlock HULL, SAILS, GUNS, 0 to 5).
 * Levels 4 and 5 are legendary (Adam Wood, Kokuto steel, a Nether Star for level 5). Hull V also mends itself in battle.
 *  - Hull: iron plating. More hull points, and every hit does a little less.
 *  - Sails: reinforced sailcloth. Faster top speed.
 *  - Guns: heavy gun carriages. Cannonballs hit harder and the crew reloads faster.
 * The numbers for each level are here, so they are easy to change.
 */
public final class ShipUpgrades {
	public static final int MAX_LEVEL = 5;
	/** Galley-La fits levels 1 to 3. Levels 4 and 5 are legendary work (see ShipyardUpgrades). */
	public static final int GALLEY_LA_MAX = 3;

	// One number per level, 0 to 5. Levels 4 and 5 still help, a bit less each.
	private static final float[] HULL = {1f, 1.3f, 1.6f, 1.9f, 2.3f, 2.7f};
	private static final float[] DAMAGE_TAKEN = {1f, 0.92f, 0.84f, 0.76f, 0.70f, 0.64f};
	private static final float[] SPEED = {1f, 1.1f, 1.2f, 1.3f, 1.38f, 1.45f};
	private static final float[] GUN_DAMAGE = {1f, 1.2f, 1.4f, 1.6f, 1.8f, 2.0f};
	private static final float[] RELOAD = {1f, 0.88f, 0.76f, 0.64f, 0.58f, 0.52f};

	private ShipUpgrades() {
	}

	private static float at(float[] table, int level) {
		return table[Math.max(0, Math.min(level, table.length - 1))];
	}

	/** Hull points multiplier (level 3 = +90%, level 5 = +170%). */
	public static float hullBonus(int level) {
		return at(HULL, level);
	}

	/** How much of every hit the hull takes (level 3 = 76%, level 5 = 64%). */
	public static float damageTaken(int level) {
		return at(DAMAGE_TAKEN, level);
	}

	/** Top speed multiplier. */
	public static float speedBonus(int level) {
		return at(SPEED, level);
	}

	/** Cannon damage multiplier. */
	public static float gunDamage(int level) {
		return at(GUN_DAMAGE, level);
	}

	/** Reload time multiplier. */
	public static float reloadTime(int level) {
		return at(RELOAD, level);
	}

	public static int hull(ShipLayout layout) {
		return level(layout, HelmBlock.HULL);
	}

	public static int sails(ShipLayout layout) {
		return level(layout, HelmBlock.SAILS);
	}

	public static int guns(ShipLayout layout) {
		return level(layout, HelmBlock.GUNS);
	}

	private static int level(ShipLayout layout, net.minecraft.world.level.block.state.properties.IntegerProperty property) {
		int index = layout.indexAt(layout.helm);
		if (index < 0) {
			return 0;
		}
		BlockState wheel = layout.blocks.get(index).state();
		return wheel.hasProperty(property) ? wheel.getValue(property) : 0;
	}

	/** "Hull II, Sails I" for a wheel's fitted upgrades, or "" if none. */
	public static String describe(BlockState wheel) {
		if (!wheel.hasProperty(HelmBlock.HULL)) {
			return "";
		}
		StringBuilder text = new StringBuilder();
		append(text, "Hull", wheel.getValue(HelmBlock.HULL));
		append(text, "Sails", wheel.getValue(HelmBlock.SAILS));
		append(text, "Guns", wheel.getValue(HelmBlock.GUNS));
		return text.toString();
	}

	private static final String[] ROMAN = {"", "I", "II", "III", "IV", "V"};

	private static void append(StringBuilder text, String name, int level) {
		if (level > 0) {
			if (!text.isEmpty()) {
				text.append(", ");
			}
			text.append(name).append(' ').append(ROMAN[Math.min(level, ROMAN.length - 1)]);
		}
	}
}
