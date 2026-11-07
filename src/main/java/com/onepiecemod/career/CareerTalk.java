package com.onepiecemod.career;

import net.minecraft.server.level.ServerPlayer;

/**
 * The career part of the talk screen (dialogue package). Marine recruiters (Koby, Garp, Sengoku, Tashigi)
 * and Revolutionaries (Dragon, Sabo, Ivankov) offer to sign you up, and later give you orders.
 */
public final class CareerTalk {
	/** What a choice leads to: the character's line, the grey hint, and whether "Sign me up" should follow. */
	public record Answer(String text, String hint, boolean offerJoin) {
	}

	private CareerTalk() {
	}

	/** Which career this character recruits for, or null. */
	private static Career recruitsFor(String characterId) {
		if (Career.MARINE_RECRUITERS.contains(characterId)) {
			return Career.MARINE;
		}
		if (Career.REVOLUTIONARY_RECRUITERS.contains(characterId)) {
			return Career.REVOLUTIONARY;
		}
		return null;
	}

	/** The button text for this character, or null if they have nothing to say about careers. */
	public static String choiceLabel(ServerPlayer player, String characterId) {
		Career path = recruitsFor(characterId);
		if (path == null) {
			return null;
		}
		Career mine = Careers.career(player);
		if (mine == path) {
			return path == Career.MARINE ? "Reporting for duty!" : "Any word from HQ?";
		}
		return path == Career.MARINE ? "I want to join the Marines." : "I want to join the Revolution.";
	}

	/** The first click: they explain, or (for members) hand out orders. */
	public static Answer talk(ServerPlayer player, String characterId) {
		Career path = recruitsFor(characterId);
		if (path == null) {
			return new Answer("...", null, false);
		}
		CareerData data = Careers.get(player);
		if (data.path() == path) {
			CareerMissions.request(player);
			Career.Rank next = data.nextRank();
			String hint = next == null ? "You're at the top: " + data.currentRank().name() + "."
					: data.points() + "/" + next.need() + " " + path.points + " for " + next.name()
					+ (next.trialCount() > 0 ? ". " + Careers.trialText(path, next) + " (" + Careers.trialProgress(player, next) + "/" + next.trialCount() + ")" : "") + ".";
			return new Answer(path == Career.MARINE
					? "At ease, " + data.currentRank().name() + ". Your orders are on your Den Den Mushi."
					: "Good to see you, comrade. Headquarters sent word to your Den Den Mushi.", hint, false);
		}
		String why = Careers.whyNot(player, path);
		if (why != null) {
			return new Answer(path == Career.MARINE ? "Hmm. I'm sorry, but I can't sign you up." : "Not yet. The Revolution needs you free and clear.", why, false);
		}
		if (path == Career.MARINE) {
			return new Answer("You want to protect people? Then join us! You'll start as a Seaman Recruit. "
					+ "Hunt pirates, follow orders, and one day you could be an Admiral.",
					"Your bounty is pardoned. Marines stop hunting you, pirates start. You can't get a bounty while you serve.", true);
		}
		return new Answer("The World Government chains this world. We mean to break those chains. Will you fight with us?",
				"You keep your bounty and the Navy keeps hunting you. Earn Liberation by fighting the Navy and the World Government.", true);
	}

	/** "Sign me up!" */
	public static Answer join(ServerPlayer player, String characterId) {
		Career path = recruitsFor(characterId);
		if (path == null) {
			return new Answer("...", null, false);
		}
		String why = Careers.whyNot(player, path);
		if (why != null) {
			return new Answer("I'm afraid not.", why, false);
		}
		Careers.join(player, path);
		return new Answer(path == Career.MARINE ? "Welcome to the Navy, Recruit {player}! Justice will prevail!"
				: "Welcome, comrade {player}. Dawn is coming.",
				"Right-click your Den Den Mushi for your rank and orders; sneak + right-click calls backup.", false);
	}
}
