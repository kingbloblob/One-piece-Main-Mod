package com.onepiecemod.style;

/**
 * Every special move. Press Z to use the selected one, Shift+Z to pick the next one.
 * Cooldowns are in ticks (20 ticks = 1 second). Hunger is how much the move tires you out.
 * The last move of most styles is locked until you beat the boss named in unlockBoss.
 * What each move actually does is in StyleMoves.java.
 */
public enum Technique {
	// Santoryu: Zoro's Three Sword Style
	ONI_GIRI(FightingStyle.SANTORYU, "Oni Giri", 100, 2.0f, null,
			"Dash forward and cut every enemy you pass."),
	TATSUMAKI(FightingStyle.SANTORYU, "Tatsumaki", 160, 3.0f, null,
			"Spin like a tornado: cuts everyone around you and throws them into the air."),
	POUND_HO(FightingStyle.SANTORYU, "108 Pound Cannon", 120, 3.0f, null,
			"A flying slash that hits every enemy in a line up to 20 blocks away."),
	ASURA(FightingStyle.SANTORYU, "Kyutoryu Asura", 900, 8.0f, "mihawk",
			"Nine swords for 15 seconds: Strength II, and every swing also cuts 2 more enemies nearby."),

	// Black Leg: Sanji's kicks
	CONCASSE(FightingStyle.BLACK_LEG, "Concasse", 120, 2.0f, null,
			"Leap high, then drop a heel kick on everyone where you land."),
	PARTY_TABLE(FightingStyle.BLACK_LEG, "Party Table Kick Course", 120, 2.0f, null,
			"A spinning handstand kick that knocks everyone around you away."),
	DIABLE_JAMBE(FightingStyle.BLACK_LEG, "Diable Jambe", 600, 4.0f, null,
			"Your leg burns red-hot for 15 seconds: kicks hit harder and set enemies on fire."),
	IFRIT_JAMBE(FightingStyle.BLACK_LEG, "Ifrit Jambe", 900, 8.0f, "king",
			"Blue flames for 15 seconds: kicks hit far harder, burn longer, and you run faster."),

	// Fish-Man Karate: Jinbe's style
	THOUSAND_BRICK(FightingStyle.FISHMAN_KARATE, "Thousand-Brick Fist", 100, 2.0f, null,
			"A punch whose shock goes straight through armor. Hits the enemy right in front of you."),
	UCHIMIZU(FightingStyle.FISHMAN_KARATE, "Uchimizu", 80, 2.0f, null,
			"Flick drops of water like bullets at up to 5 enemies in front. Twice as strong in water or rain."),
	SAMEHADA(FightingStyle.FISHMAN_KARATE, "Samehada Shotei", 400, 3.0f, null,
			"Shark-skin palms for 8 seconds: you take less damage and anyone who hits you gets hurt."),
	BURAIKAN(FightingStyle.FISHMAN_KARATE, "Buraikan", 900, 8.0f, "big_mom",
			"Hurl a huge wave of water that smashes and throws every enemy in front of you."),

	// Rokushiki: the Six Powers (Geppo and Kami-e work on their own, no key needed)
	SORU(FightingStyle.ROKUSHIKI, "Soru", 40, 1.0f, null,
			"Move so fast you vanish: a quick dash where you're looking."),
	SHIGAN(FightingStyle.ROKUSHIKI, "Shigan", 60, 1.5f, null,
			"A finger strike like a bullet on the enemy you're looking at, up to 4 blocks away."),
	RANKYAKU(FightingStyle.ROKUSHIKI, "Rankyaku", 120, 3.0f, null,
			"Kick a blade of air that cuts every enemy in a line up to 20 blocks away."),
	TEKKAI(FightingStyle.ROKUSHIKI, "Tekkai", 300, 2.0f, null,
			"Turn your body to iron for 5 seconds: Resistance IV, but you can barely move."),
	ROKUOGAN(FightingStyle.ROKUSHIKI, "Rokuogan", 900, 8.0f, "lucci",
			"The secret seventh power: a huge shock wave that blasts everyone in front of you."),

	// Ryusoken: Sabo's Dragon Claw Fist
	RYU_NO_KAGIZUME(FightingStyle.RYUSOKEN, "Ryu no Kagizume", 80, 2.0f, null,
			"Grab the enemy in front of you with a dragon claw: big damage and they can barely move for 3 seconds."),
	RYU_NO_IBUKI(FightingStyle.RYUSOKEN, "Ryu no Ibuki", 160, 3.0f, null,
			"Crush the ground: everyone around you is hurt and thrown off their feet."),
	HIKEN(FightingStyle.RYUSOKEN, "Hiken", 600, 6.0f, "fujitora",
			"Ace's Fire Fist, passed on to Sabo: a pillar of fire that burns every enemy in a line up to 20 blocks."),

	// Oden Nitoryu: Oden's Two Sword Style
	PARADISE_TOTSUKA(FightingStyle.NITORYU, "Paradise Totsuka", 120, 2.0f, null,
			"A wide cross slash with both swords that cuts every enemy in front of you."),
	TOGEN_TOTSUKA(FightingStyle.NITORYU, "Togen Totsuka", 160, 3.0f, null,
			"One huge two-sword strike on the enemy right in front of you."),
	BOILING_WILL(FightingStyle.NITORYU, "Boiling Will", 900, 4.0f, null,
			"Like Oden in the boiling pot: 10 seconds of Resistance II, Regeneration II and Fire Resistance."),
	ODENS_SCAR(FightingStyle.NITORYU, "The Scar That Kaido Kept", 900, 8.0f, "kaido",
			"The only cut that ever scarred Kaido: a massive strike that also withers the target."),

	// Kitsunebi-ryu: Kin'emon's Fox Fire Style
	HOMURA_GIRI(FightingStyle.KITSUNEBI, "Homura-giri", 100, 2.0f, null,
			"A flaming slash that cuts and burns every enemy in a line up to 10 blocks."),
	CUT_THE_FLAMES(FightingStyle.KITSUNEBI, "Cut the Flames", 300, 2.0f, null,
			"Cut every fire around you (within 5 blocks) and take its strength: Strength I for 10 seconds."),
	KITSUNEBI_BLADE(FightingStyle.KITSUNEBI, "Fox Fire Blade", 900, 6.0f, "king",
			"Your blade burns for 15 seconds: every hit does +4 damage and sets the enemy on fire."),

	// Soul King Fencing: Brook's style
	YAHAZU_GIRI(FightingStyle.SOUL_FENCING, "Hanauta Sancho: Yahazu Giri", 120, 2.0f, null,
			"Walk straight past enemies humming a tune. Two seconds later, everyone you passed is cut."),
	GAVOTTE(FightingStyle.SOUL_FENCING, "Gavotte Bond en Avant", 60, 1.5f, null,
			"A lightning-fast lunge that stabs the first enemy up to 8 blocks away."),
	SOUL_SOLID(FightingStyle.SOUL_FENCING, "Soul Solid", 400, 3.0f, null,
			"Chill your blade with the cold of the underworld for 10 seconds: every hit freezes and slows."),
	LULLABY(FightingStyle.SOUL_FENCING, "Soul King's Lullaby", 900, 6.0f, "moria",
			"Play a song so sad that every enemy within 8 blocks is blinded, dizzy and almost frozen for 6 seconds."),

	// Fist of Love: Garp's brawling
	FIST_OF_LOVE_PUNCH(FightingStyle.FIST_OF_LOVE, "Fist of Love", 80, 2.0f, null,
			"A loving punch to the enemy in front of you that sends them flying."),
	CANNONBALL(FightingStyle.FIST_OF_LOVE, "Cannonball Barrage", 200, 4.0f, null,
			"Throw cannonballs by hand at up to 5 enemies you can see within 16 blocks."),
	GALAXY_IMPACT(FightingStyle.FIST_OF_LOVE, "Galaxy Impact", 1200, 10.0f, "aokiji",
			"Garp's ultimate punch: a huge blast that hits every enemy within 8 blocks."),

	// Sogeking Sniping: Usopp's style
	LEAD_STAR(FightingStyle.SOGEKING, "Lead Star", 40, 1.0f, null,
			"A sniper shot at the first enemy you're aiming at, up to 40 blocks away."),
	KAEN_BOSHI(FightingStyle.SOGEKING, "Kaen Boshi", 100, 1.5f, null,
			"A Flame Star: hits the first enemy up to 30 blocks away and sets it on fire."),
	POP_GREEN(FightingStyle.SOGEKING, "Pop Green: Devil", 200, 2.0f, null,
			"Shoot a seed where you aim: it bursts into thorny vines that poison and trap every enemy within 4 blocks."),
	FIREBIRD_STAR(FightingStyle.SOGEKING, "Firebird Star", 900, 6.0f, "doflamingo",
			"A blazing bird of fire that flies 30 blocks and burns every enemy in its path.");

	private final FightingStyle style;
	private final String title;
	private final int cooldownTicks;
	private final float hunger;
	private final String unlockBoss;
	private final String description;

	Technique(FightingStyle style, String title, int cooldownTicks, float hunger, String unlockBoss, String description) {
		this.style = style;
		this.title = title;
		this.cooldownTicks = cooldownTicks;
		this.hunger = hunger;
		this.unlockBoss = unlockBoss;
		this.description = description;
	}

	public FightingStyle style() {
		return style;
	}

	public String title() {
		return title;
	}

	public int cooldownTicks() {
		return cooldownTicks;
	}

	public float hunger() {
		return hunger;
	}

	/** Boss id you must beat to unlock this move, or null if it's available from the start. */
	public String unlockBoss() {
		return unlockBoss;
	}

	public String description() {
		return description;
	}

	/** Finds a move by its enum name (like "ONI_GIRI"), or null if there is none. */
	public static Technique byName(String name) {
		for (Technique technique : values()) {
			if (technique.name().equals(name)) {
				return technique;
			}
		}
		return null;
	}
}
