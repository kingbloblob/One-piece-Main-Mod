package com.onepiecemod.style;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;

import com.onepiecemod.character.CharacterAttachments;

/**
 * The fighting styles a player can learn. Each one is taught by a master character
 * (find them with their Vivre Card, then sneak and right-click them) or by reading a Dojo Scroll.
 *
 * To change what a master asks for, edit the numbers and items here.
 */
public enum FightingStyle {
	SANTORYU("santoryu", "Santoryu (Three Sword Style)", "zoro",
			50, Items.AIR, 0, 0, 3,
			"Fight with three swords: one in your hand, one in your off hand and one more in your hotbar."),
	BLACK_LEG("black_leg", "Black Leg Style", "sanji",
			50, Items.COOKED_SALMON, 16, 0, 0,
			"Kick instead of punch. Keep your main hand empty: a cook's hands are for cooking."),
	FISHMAN_KARATE("fishman_karate", "Fish-Man Karate", "jinbe",
			50, Items.PRISMARINE_SHARD, 16, 0, 0,
			"Bare-handed strikes that send shock waves through the water inside your enemy. Keep your main hand empty."),
	ROKUSHIKI("rokushiki", "Rokushiki (Six Powers)", "koby",
			100, Items.AIR, 0, 3, 0,
			"The Marines' and CP9's six superhuman techniques. Works with anything in your hands."),
	RYUSOKEN("ryusoken", "Ryusoken (Dragon Claw Fist)", "sabo",
			80, Items.IRON_INGOT, 16, 2, 0,
			"Fingers like dragon claws that crush whatever they grab. Keep your main hand empty."),
	NITORYU("nitoryu", "Oden Nitoryu (Two Sword Style)", "oden",
			100, Items.AIR, 0, 2, 2,
			"Oden's wild Two Sword Style. Hold a sword in your main hand and another in your off hand."),
	KITSUNEBI("kitsunebi", "Kitsunebi-ryu (Fox Fire Style)", "kinemon",
			60, Items.BLAZE_POWDER, 8, 0, 0,
			"A samurai style that cuts fire itself. Hold a sword, and fire can't burn you."),
	SOUL_FENCING("soul_fencing", "Soul King Fencing", "brook",
			60, Items.BONE, 16, 0, 0,
			"Brook's fast fencing with a sword chilled by the underworld. Hold a sword."),
	FIST_OF_LOVE("fist_of_love", "Fist of Love (Garp's Brawling)", "garp",
			120, Items.BREAD, 16, 3, 0,
			"The Hero of the Marines just punches very, very hard. Keep your main hand empty."),
	SOGEKING("sogeking", "Sogeking Sniping", "usopp",
			40, Items.WHEAT_SEEDS, 16, 0, 0,
			"Long-range trick shots and Pop Green seeds. Hold a bow or crossbow.");

	private final String id;
	private final String title;
	private final String master;
	private final int berryCost;
	private final Item trialItem;
	private final int trialCount;
	private final int bossesNeeded;
	private final int swordsNeeded;
	private final String howToFight;

	FightingStyle(String id, String title, String master, int berryCost, Item trialItem, int trialCount, int bossesNeeded, int swordsNeeded, String howToFight) {
		this.id = id;
		this.title = title;
		this.master = master;
		this.berryCost = berryCost;
		this.trialItem = trialItem;
		this.trialCount = trialCount;
		this.bossesNeeded = bossesNeeded;
		this.swordsNeeded = swordsNeeded;
		this.howToFight = howToFight;
	}

	public String id() {
		return id;
	}

	public String title() {
		return title;
	}

	/** The character id (from characters.json) who teaches this style. */
	public String master() {
		return master;
	}

	public int berryCost() {
		return berryCost;
	}

	/** Item the master asks you to bring, or AIR for none. */
	public Item trialItem() {
		return trialItem;
	}

	public int trialCount() {
		return trialCount;
	}

	/** How many different bosses you must have beaten before the master will teach you. */
	public int bossesNeeded() {
		return bossesNeeded;
	}

	/** Swords you must carry (hotbar or off hand) to learn and use this style, or 0. */
	public int swordsNeeded() {
		return swordsNeeded;
	}

	public String howToFight() {
		return howToFight;
	}

	/** Every technique in this style, in order, including ones the player hasn't unlocked yet. */
	public List<Technique> techniques() {
		List<Technique> list = new ArrayList<>();
		for (Technique technique : Technique.values()) {
			if (technique.style() == this) {
				list.add(technique);
			}
		}
		return list;
	}

	/** The techniques this player can use right now (the final one needs its boss beaten first). */
	public List<Technique> unlockedTechniques(Player player) {
		List<Technique> list = new ArrayList<>();
		for (Technique technique : techniques()) {
			if (technique.unlockBoss() == null
					|| CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, technique.unlockBoss())) {
				list.add(technique);
			}
		}
		return list;
	}

	public static FightingStyle byId(String id) {
		for (FightingStyle style : values()) {
			if (style.id.equals(id)) {
				return style;
			}
		}
		return null;
	}

	public static FightingStyle byMaster(String characterId) {
		for (FightingStyle style : values()) {
			if (style.master.equals(characterId)) {
				return style;
			}
		}
		return null;
	}
}
