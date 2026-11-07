package com.onepiecemod.treasure;

/**
 * The three kinds of treasure map.
 * - BURIED: a chest a few blocks under a red X on some island. From newspapers, pirate captains and wrecks.
 * - WRECK: a sunken ship on the sea floor with its treasure still aboard. From newspapers and wrecks.
 * - HOARD: a pirate captain's hoard, buried deep and guarded by their old crew. Dropped by bosses.
 * - CASTAWAY: a castaway's cache on a tiny sandbar in shallow sea. From messages in bottles (voyage package).
 */
public enum TreasureKind {
	BURIED("buried", "Torn Treasure Map", "Treasure Map", 250, 700, true),
	WRECK("wreck", "Soggy Wreck Chart", "Wreck Chart", 250, 800, false),
	HOARD("hoard", "Captain's Hoard Map", "Hoard Map", 500, 1400, true),
	/** A castaway's cache: a tiny sandbar island with a palm tree, out in shallow sea, the chest buried under it. */
	CASTAWAY("castaway", "Castaway's Chart", "Castaway Chart", 200, 650, false);

	public final String id;
	/** The name before it is unfolded. */
	public final String closedName;
	/** The name of the vanilla map it turns into. */
	public final String openName;
	/** How far away the treasure is, in blocks. */
	public final int minDistance;
	public final int maxDistance;
	/** True = on land, false = on the sea floor. */
	public final boolean land;

	TreasureKind(String id, String closedName, String openName, int minDistance, int maxDistance, boolean land) {
		this.id = id;
		this.closedName = closedName;
		this.openName = openName;
		this.minDistance = minDistance;
		this.maxDistance = maxDistance;
		this.land = land;
	}

	public static TreasureKind byId(String id) {
		for (TreasureKind kind : values()) {
			if (kind.id.equals(id)) {
				return kind;
			}
		}
		return BURIED;
	}
}
