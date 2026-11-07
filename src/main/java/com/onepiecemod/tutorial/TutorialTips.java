package com.onepiecemod.tutorial;

import java.util.function.Predicate;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.haki.HakiAttachments;
import com.onepiecemod.power.ModAttachments;
import com.onepiecemod.power.SeaWeakness;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.style.StyleAttachments;

/**
 * One-time tips: the first time something happens (a Devil Fruit in your bag, the first Haki level,
 * the first time at a ship's wheel...), one chat line explains it and names the keys to press.
 * They teach the keys when they become useful, instead of all at once on the first day.
 *
 * Each tip shows once per player (saved as "tip:<id>" in the guide's seen list), even after the guide
 * is finished, and none show while the guide is off (/tutorial off).
 * The Voyage Log book (tutorial/client/TutorialBookScreen) lists the ones a player has seen, to read again.
 */
public enum TutorialTips {
	FRUIT_FOUND("fruit_found", "You found a Devil Fruit!",
			"Right-click to eat it and its power is yours forever. But a fruit user sinks like a stone in the sea, and eating a second fruit kills you. The Devil Fruit Encyclopedia tells you what each fruit does.",
			player -> TutorialFeature.carriesFruit(player) && !TutorialFeature.ateFruit(player)),
	FRUIT_EATEN("fruit_eaten", "Your power has awakened!",
			"{key.onepiece.use_fruit_power}: main move. Sneak + {key.onepiece.use_fruit_power}: second move. {key.onepiece.awaken_fruit}: awakening progress. Use your power a lot: mastery makes every move stronger.",
			TutorialFeature::ateFruit),
	SEA_WEAKNESS("sea_weakness", "The sea is draining you!",
			"Devil Fruit users lose their strength and sink in sea water, and their powers stop working. Climb out by a ladder or vines, or stay on deck.",
			player -> TutorialFeature.ateFruit(player) && SeaWeakness.isInSea(player)),
	OBSERVATION("observation", "Observation Haki awakened!",
			"Press {key.onepiece.observation_haki} to switch it on or off. It shows enemies through walls and helps you dodge. Taking hits trains it. /haki shows your levels.",
			player -> HakiAttachments.get(player).observationLevel() >= 1),
	ARMAMENT("armament", "Armament Haki awakened!",
			"Press {key.onepiece.armament_haki} to coat your body in Haki: harder hits, tougher skin, and you can hit Logia users. Punching with bare fists trains it.",
			player -> HakiAttachments.get(player).armamentLevel() >= 1),
	CONQUEROR("conqueror", "You have Conqueror's Haki!",
			"Only one in a million has it. Press {key.onepiece.conquerors_haki} to release it and knock out weaker foes around you. It needs time to recharge.",
			player -> HakiAttachments.get(player).conqueror()),
	STYLE("style", "You learned a fighting style!",
			"Press {key.onepiece_styles.technique} to use a technique, Shift + {key.onepiece_styles.technique} to pick the next one. /style lists your styles and switches between them.",
			player -> StyleAttachments.active(player) != null),
	HELM("helm", "You have the helm!",
			"W / S: sail and slow down. A / D: turn. Sneak: leave the wheel. Right-click the deck twice to drop anchor. With cannons aboard, {key.onepiece.fire_cannons} fires them.",
			player -> player.getVehicle() instanceof ShipEntity),
	CREW("crew", "Your crew is formed!",
			"Press {key.onepiece_crew.open} for the crew window: your crewmates, their jobs and orders. Crewmates follow you aboard and fight beside you.",
			player -> player.getAttached(CrewAttachments.CREW) != null),
	BOUNTY("bounty", "You have a bounty now!",
			"The Navy has noticed you. The higher it climbs, the stronger the Marines and bounty hunters that come after you. /bounty shows it.",
			player -> Bounty.get(player) > 0),
	EASY_PLAY("easy_play", "Want an easier (or harder) voyage?",
			"Press Esc > One Piece Settings > Easy Play. Simple mode gives new players a gentler start: the Navy waits until you beat your first boss, cooldowns are shorter and dying costs no mastery. Presets go from Story to Challenge.",
			player -> player.tickCount > 20 * 60 * 3 && player.level().getServer().isSingleplayer()
					&& !com.onepiecemod.config.ModConfig.simpleMode() && !com.onepiecemod.config.ModConfig.locked());

	public final String id;
	public final String title;
	public final String text;
	final Predicate<ServerPlayer> when;

	TutorialTips(String id, String title, String text, Predicate<ServerPlayer> when) {
		this.id = id;
		this.title = title;
		this.text = text;
		this.when = when;
	}

	String seenKey() {
		return "tip:" + id;
	}

	/** The tip with this id, or null. */
	public static TutorialTips byId(String id) {
		for (TutorialTips tip : values()) {
			if (tip.id.equals(id)) {
				return tip;
			}
		}
		return null;
	}

	/** Shows the first tip that has just become true (one at a time, so chat doesn't flood). */
	static TutorialFeature.Progress check(ServerPlayer player, TutorialFeature.Progress progress) {
		for (TutorialTips tip : values()) {
			if (progress.seen().contains(tip.seenKey())) {
				continue;
			}
			boolean now;
			try {
				now = tip.when.test(player);
			} catch (RuntimeException e) {
				now = false; // Another feature isn't ready for this player yet: try again later.
			}
			if (now) {
				player.sendSystemMessage(Component.literal("💡 " + tip.title + " ").withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD)
						.append(TutorialStep.withKeys(tip.text).withStyle(style -> style.withBold(false).withColor(ChatFormatting.GRAY))));
				player.level().playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 0.8f, 1.4f);
				return progress.withSeen(tip.seenKey());
			}
		}
		return progress;
	}

	/** Marks every tip that is already true as seen, without showing it (for veterans who start with the guide off). */
	static TutorialFeature.Progress markKnown(ServerPlayer player, TutorialFeature.Progress progress) {
		for (TutorialTips tip : values()) {
			try {
				if (tip.when.test(player)) {
					progress = progress.withSeen(tip.seenKey());
				}
			} catch (RuntimeException ignored) {
				// Checked again next time.
			}
		}
		return progress;
	}

}
