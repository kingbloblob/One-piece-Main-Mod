package com.onepiecemod.cuisine;

/**
 * Fishing, cooking and the All Blue.
 *
 *  - Fish: 18 kinds, by sea (East Blue, Calm Belt, Grand Line, New World), by island, and two only the All Blue has.
 *    Caught with a normal fishing rod, see Fishing. Grill any raw fish into Grilled Fish.
 *  - Sanji's dishes: 17 meals made at the Ship's Galley whose buffs last 8 to 20 minutes, see CuisineItems and DishItem.
 *  - The All Blue: one per world in the New World, see AllBlue. The All Blue Compass points to it.
 *
 * Recipes: onepiece/station_recipes.json (Galley dishes, the compass) and data/onepiece/recipe (grilling).
 */
public class CuisineFeature {
	public static void initialize() {
		CuisineEffects.initialize();
		CuisineItems.initialize();
		Fishing.initialize();
		AllBlue.initialize();
	}
}
