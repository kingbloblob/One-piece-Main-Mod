package com.onepiecemod.crew;

/**
 * What a crewmate is doing right now. The captain right-clicks a crewmate to switch.
 */
public enum CrewMode {
	/** Walk with the captain and fight beside them. */
	FOLLOW("is following you"),
	/** Stay in place. */
	WAIT("will wait here"),
	/** Do their job around the spot where they were told to work. */
	WORK("is getting to work here");

	private final String message;

	CrewMode(String message) {
		this.message = message;
	}

	public String message() {
		return message;
	}

	/** The next mode when the captain right-clicks: Follow, Wait, Work, then back to Follow. */
	public CrewMode next() {
		return switch (this) {
			case FOLLOW -> WAIT;
			case WAIT -> WORK;
			case WORK -> FOLLOW;
		};
	}

	public static CrewMode byName(String name) {
		for (CrewMode mode : values()) {
			if (mode.name().equals(name)) {
				return mode;
			}
		}
		return FOLLOW;
	}
}
