package com.onepiecemod.haki;

/**
 * Everything about Haki. OnePieceMod calls initialize() once, and this sets up the rest.
 */
public class HakiFeature {
	public static void initialize() {
		HakiAttachments.initialize();
		HakiPowers.initialize();
		HakiCommands.initialize();
	}
}
