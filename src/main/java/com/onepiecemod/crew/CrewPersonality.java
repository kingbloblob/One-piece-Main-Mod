package com.onepiecemod.crew;

/**
 * Every recruit has a personality. It changes their price, their stats, how fast they work,
 * and what they say to their captain.
 *
 * The numbers are multipliers: 1.0 = normal, 1.2 = 20% more, 0.5 = half.
 * workTime is how long a job takes: 0.5 = twice as fast, 2.0 = twice as slow.
 */
public enum CrewPersonality {
	STEADY("Steady", "Does the job, no fuss.", 1.0, 1.0, 1.0, 1.0,
			"Ready when you are, Captain.",
			"Another fine day at sea.",
			"I'll handle it."),
	BRAVE("Brave", "Hits 20% harder. Never backs down.", 1.1, 1.0, 1.2, 1.0,
			"Nobody lays a finger on my captain!",
			"Bring on the next fight!",
			"Fear? Never heard of it."),
	LOYAL("Loyal", "25% more health. Would follow you anywhere.", 1.0, 1.25, 1.0, 1.0,
			"Wherever you sail, I sail.",
			"I'll protect this crew with my life.",
			"You can count on me, Captain."),
	LAZY("Lazy", "Cheap (30% off), but works twice as slowly.", 0.7, 1.0, 1.0, 2.0,
			"Can we take a nap first?",
			"*yawn* ...is it lunch yet?",
			"Five more minutes..."),
	HARDWORKING("Hardworking", "Works twice as fast. Costs 20% more.", 1.2, 1.0, 1.0, 0.5,
			"Already done! What's next?",
			"Idle hands sink ships.",
			"I'll work through the night if I have to."),
	GREEDY("Greedy", "Costs 50% more, but 15% tougher and stronger.", 1.5, 1.15, 1.15, 1.0,
			"Is there treasure in it for me?",
			"I'm worth every Berry, you know.",
			"Gold, gold, gold..."),
	CHEERFUL("Cheerful", "10% off and 10% more health. Always smiling.", 0.9, 1.1, 1.0, 1.0,
			"What a wonderful day to be a pirate!",
			"Shishishi! This crew is the best!",
			"Let's throw a party tonight!"),
	GRUMPY("Grumpy", "20% off and hits 10% harder, but complains a lot.", 0.8, 1.0, 1.1, 1.0,
			"Hmph. Fine.",
			"This ship creaks too much.",
			"Why do I always get the worst jobs?");

	private final String title;
	private final String description;
	private final double costMultiplier;
	private final double healthMultiplier;
	private final double damageMultiplier;
	private final double workTime;
	private final String[] lines;

	CrewPersonality(String title, String description, double costMultiplier, double healthMultiplier,
			double damageMultiplier, double workTime, String... lines) {
		this.title = title;
		this.description = description;
		this.costMultiplier = costMultiplier;
		this.healthMultiplier = healthMultiplier;
		this.damageMultiplier = damageMultiplier;
		this.workTime = workTime;
		this.lines = lines;
	}

	public String title() { return title; }
	public String description() { return description; }
	public double costMultiplier() { return costMultiplier; }
	public double healthMultiplier() { return healthMultiplier; }
	public double damageMultiplier() { return damageMultiplier; }
	public double workTime() { return workTime; }
	/** Things this crewmate says now and then. */
	public String[] lines() { return lines; }

	public static CrewPersonality byName(String name) {
		for (CrewPersonality personality : values()) {
			if (personality.name().equals(name)) {
				return personality;
			}
		}
		return STEADY;
	}
}
