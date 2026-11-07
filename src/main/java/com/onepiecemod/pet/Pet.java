package com.onepiecemod.pet;

import java.util.UUID;

/**
 * Anything a player can tame: the One Piece creatures and Sea Kings.
 * Shared pet behaviour (following, defending, the Pet Whistle, healing, bond levels, abilities, towing) works through this.
 */
public interface Pet {
	/** The player who tamed it, or null while it's wild. */
	UUID getOwnerId();

	default boolean isTamed() {
		return getOwnerId() != null;
	}

	/** Told to wait where it is (sneak + right-click, or the Pet Whistle while sneaking). */
	boolean isStaying();

	void setStaying(boolean staying);

	/** Lives only in water: it can only be called to water, and swims under its rider. */
	boolean petSwims();

	/** Bond points: earned by fighting together, riding and feeding. See PetBond for the levels. */
	int getBond();

	void setBond(int bond);

	/** The ship this pet is harnessed to and pulls along (PetTowing), or null. */
	UUID getTowShip();

	void setTowShip(UUID ship);

	/** The key PetAbilities looks its ability up by: the creature's id, or "sea_king". */
	String petKind();
}
