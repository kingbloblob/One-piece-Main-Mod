package com.onepiecemod.race;

import java.util.List;

import net.minecraft.core.Holder;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation;
import net.minecraft.world.entity.ai.attributes.Attributes;

/**
 * The races a player can be. Each one picks a few always-on stat changes (attributes),
 * and RacePerks adds the special rules (breathing underwater, fire immunity, and so on).
 *
 * The perks and drawbacks text is what the race picker screen and /race show,
 * so keep it in step with the stats below and the rules in RacePerks.
 */
public enum Race {
	HUMAN("human", "Human", 0xE0C090,
			"The most common people of the seas. Nothing special, so they make up for it with willpower.",
			List.of("Haki trains 50% faster", "No drawbacks"),
			List.of("No special body powers"),
			List.of()),

	FISHMAN("fishman", "Fish-Man", 0x3FA7D6,
			"Born under the sea, with ten times the strength of a human.",
			List.of("Breathe underwater forever", "Swim fast and mine at full speed underwater", "+2 attack damage"),
			List.of("10% slower on land", "Burn for longer when set on fire"),
			List.of(
					stat(Attributes.ATTACK_DAMAGE, 2, Operation.ADD_VALUE),
					stat(Attributes.WATER_MOVEMENT_EFFICIENCY, 0.6, Operation.ADD_VALUE),
					stat(Attributes.SUBMERGED_MINING_SPEED, 0.8, Operation.ADD_VALUE),
					stat(Attributes.BURNING_TIME, 0.5, Operation.ADD_MULTIPLIED_BASE))),

	MINK("mink", "Mink", 0xF2B134,
			"Furry warriors from Zou who fight with Electro.",
			List.of("15% faster and jump higher", "Electro: 1 in 4 punches shocks the target", "See in the dark",
					"Sulong under the full moon: much stronger and faster (master it to use at will)"),
			List.of("Get hungry fast in hot places (desert, savanna, Nether)", "Burn for longer when set on fire"),
			List.of(
					stat(Attributes.MOVEMENT_SPEED, 0.15, Operation.ADD_MULTIPLIED_BASE),
					stat(Attributes.JUMP_STRENGTH, 0.08, Operation.ADD_VALUE),
					stat(Attributes.BURNING_TIME, 0.5, Operation.ADD_MULTIPLIED_BASE))),

	GIANT("giant", "Giant", 0xB5651D,
			"Warriors of Elbaph, one and a half times your size.",
			List.of("+5 hearts", "+2 attack damage, long reach", "Hard to knock back, step up full blocks"),
			List.of("Too tall for normal doors and tunnels", "Swing 20% slower", "Get hungry 50% faster"),
			List.of(
					stat(Attributes.SCALE, 0.5, Operation.ADD_VALUE),
					stat(Attributes.MAX_HEALTH, 10, Operation.ADD_VALUE),
					stat(Attributes.ATTACK_DAMAGE, 2, Operation.ADD_VALUE),
					stat(Attributes.ENTITY_INTERACTION_RANGE, 1.5, Operation.ADD_VALUE),
					stat(Attributes.BLOCK_INTERACTION_RANGE, 1.5, Operation.ADD_VALUE),
					stat(Attributes.KNOCKBACK_RESISTANCE, 0.5, Operation.ADD_VALUE),
					stat(Attributes.STEP_HEIGHT, 0.5, Operation.ADD_VALUE),
					stat(Attributes.ATTACK_SPEED, -0.2, Operation.ADD_MULTIPLIED_BASE))),

	SKYPIEAN("skypiean", "Skypiean", 0xAFE3FF,
			"People of the sky islands, with little wings and a natural gift for Mantra.",
			List.of("Observation Haki (Mantra) trains 2x faster", "Fall from 8 blocks safely, half fall damage", "Jump higher"),
			List.of("-2 hearts", "-1 attack damage"),
			List.of(
					stat(Attributes.SAFE_FALL_DISTANCE, 5, Operation.ADD_VALUE),
					stat(Attributes.FALL_DAMAGE_MULTIPLIER, -0.5, Operation.ADD_MULTIPLIED_BASE),
					stat(Attributes.JUMP_STRENGTH, 0.06, Operation.ADD_VALUE),
					stat(Attributes.MAX_HEALTH, -4, Operation.ADD_VALUE),
					stat(Attributes.ATTACK_DAMAGE, -1, Operation.ADD_VALUE))),

	LUNARIAN("lunarian", "Lunarian", 0xFF5A1F,
			"A nearly extinct race with a flame on their back. Almost unbeatable while it burns.",
			List.of("While dry: immune to fire and lava", "While dry: +4 armor, +2 armor toughness"),
			List.of("In water or rain your flame goes out:", "you lose your perks and get Weakness and Slowness"),
			List.of()),

	LONG_ARM("long_arm", "Long-Arm Tribe", 0x9C6ADE,
			"Their arms have two elbows, so they reach much further.",
			List.of("+2 blocks reach for hitting and building"),
			List.of("Swing 15% slower"),
			List.of(
					stat(Attributes.ENTITY_INTERACTION_RANGE, 2, Operation.ADD_VALUE),
					stat(Attributes.BLOCK_INTERACTION_RANGE, 2, Operation.ADD_VALUE),
					stat(Attributes.ATTACK_SPEED, -0.15, Operation.ADD_MULTIPLIED_BASE))),

	LONG_LEG("long_leg", "Long-Leg Tribe", 0x5BC0A0,
			"Their legs are as long as a whole person.",
			List.of("15% faster", "Jump higher and step up full blocks"),
			List.of("-1 heart", "Slow when sneaking"),
			List.of(
					stat(Attributes.MOVEMENT_SPEED, 0.15, Operation.ADD_MULTIPLIED_BASE),
					stat(Attributes.JUMP_STRENGTH, 0.1, Operation.ADD_VALUE),
					stat(Attributes.STEP_HEIGHT, 0.5, Operation.ADD_VALUE),
					stat(Attributes.MAX_HEALTH, -2, Operation.ADD_VALUE),
					stat(Attributes.SNEAKING_SPEED, -0.4, Operation.ADD_MULTIPLIED_BASE))),

	TONTATTA("tontatta", "Tontatta Dwarf", 0xE86A92,
			"Tiny, lightning fast and stronger than they look. Great diggers.",
			List.of("Half size: fit through 1-block gaps", "25% faster, +2 attack damage", "Break blocks 30% faster"),
			List.of("-3 hearts", "-1 block reach"),
			List.of(
					stat(Attributes.SCALE, -0.5, Operation.ADD_VALUE),
					stat(Attributes.MOVEMENT_SPEED, 0.25, Operation.ADD_MULTIPLIED_BASE),
					stat(Attributes.ATTACK_DAMAGE, 2, Operation.ADD_VALUE),
					stat(Attributes.BLOCK_BREAK_SPEED, 0.3, Operation.ADD_MULTIPLIED_BASE),
					stat(Attributes.MAX_HEALTH, -6, Operation.ADD_VALUE),
					stat(Attributes.ENTITY_INTERACTION_RANGE, -1, Operation.ADD_VALUE),
					stat(Attributes.BLOCK_INTERACTION_RANGE, -1, Operation.ADD_VALUE))),

	ONI("oni", "Oni", 0xC0392B,
			"Horned warriors of Wano legend, as tough as they are strong.",
			List.of("+3 armor, +2 attack damage", "Your hits knock enemies further", "Hard to knock back"),
			List.of("10% slower", "Get hungry faster"),
			List.of(
					stat(Attributes.ARMOR, 3, Operation.ADD_VALUE),
					stat(Attributes.ATTACK_DAMAGE, 2, Operation.ADD_VALUE),
					stat(Attributes.ATTACK_KNOCKBACK, 0.5, Operation.ADD_VALUE),
					stat(Attributes.KNOCKBACK_RESISTANCE, 0.3, Operation.ADD_VALUE),
					stat(Attributes.MOVEMENT_SPEED, -0.1, Operation.ADD_MULTIPLIED_BASE)));

	/** One always-on stat change, like "+2 attack damage". */
	public record Stat(Holder<Attribute> attribute, double amount, Operation operation) {
	}

	private static Stat stat(Holder<Attribute> attribute, double amount, Operation operation) {
		return new Stat(attribute, amount, operation);
	}

	public final String id;
	public final String displayName;
	public final int color;
	public final String description;
	public final List<String> perks;
	public final List<String> drawbacks;
	public final List<Stat> stats;

	Race(String id, String displayName, int color, String description, List<String> perks, List<String> drawbacks, List<Stat> stats) {
		this.id = id;
		this.displayName = displayName;
		this.color = color;
		this.description = description;
		this.perks = perks;
		this.drawbacks = drawbacks;
		this.stats = stats;
	}

	/** "a Giant" or "an Oni", for messages. */
	public String withArticle() {
		return ("AEIOU".indexOf(displayName.charAt(0)) >= 0 ? "an " : "a ") + displayName;
	}

	/** Finds a race by its saved id, such as "fishman". Returns null for unknown ids. */
	public static Race byId(String id) {
		for (Race race : values()) {
			if (race.id.equals(id)) {
				return race;
			}
		}
		return null;
	}
}
