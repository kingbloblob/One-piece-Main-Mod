package com.onepiecemod.race;

/**
 * Everything about races. OnePieceMod calls initialize() once, and this sets up the rest.
 */
public class RaceFeature {
	public static void initialize() {
		RaceAttachments.initialize();
		RacePayloads.initialize();
		RacePerks.initialize();
		Sulong.initialize();
		RaceCommands.initialize();
	}
}
