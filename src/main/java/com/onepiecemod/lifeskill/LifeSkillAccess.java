package com.onepiecemod.lifeskill;

/** Small doorway for the mixins (they live in another package). */
public final class LifeSkillAccess {
	private LifeSkillAccess() {
	}

	public static void setTakingFromFurnace(boolean value) {
		LifeSkillHooks.takingFromFurnace = value;
	}
}
