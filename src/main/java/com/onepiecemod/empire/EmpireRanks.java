package com.onepiecemod.empire;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.haki.HakiAttachments;
import com.onepiecemod.haki.HakiData;
import com.onepiecemod.story.StoryGates;
import com.onepiecemod.story.StoryProgress;

/**
 * Earning titles. Every 10 seconds each player is checked against the next title's requirements:
 *
 *  Emperor of the Sea: 1 billion bounty, beat Kaido, Big Mom, Shanks or Blackbeard on Hard,
 *                      6 crewmates, a Kingdom Flag planted, and the story past Wano. Only 4 at a time.
 *  Pirate King:        an Emperor who finished the story at Laugh Tale. Only 1 at a time.
 *  King of the World:  the Pirate King with 3 billion bounty, all four Admirals beaten,
 *                      and Conqueror's Haki at its top level. Only 1 at a time.
 *
 * In multiplayer, a title holder killed by another player drops one title, which opens a seat.
 */
public class EmpireRanks {
	private static final int CHECK_EVERY_TICKS = 20 * 10;
	private static final String[] EMPERORS = {"kaido", "big_mom", "shanks", "blackbeard"};
	private static final String[] ADMIRALS = {"akainu", "kizaru", "fujitora", "ryokugyu"};

	/** One line of the requirement list shown by /empire. */
	public record Requirement(String text, boolean done) {
	}

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % CHECK_EVERY_TICKS != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				check(player);
			}
		});

		// Lose a fight to another player and you lose a title.
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (entity instanceof ServerPlayer victim && source.getEntity() instanceof ServerPlayer killer && killer != victim) {
				Title title = EmpireData.title(victim);
				if (title != Title.NONE) {
					Title lower = Title.byLevel(title.ordinal() - 1);
					EmpireData.setTitle(victim, lower);
					broadcast(victim.level().getServer(), Component.literal(killer.getName().getString() + " has defeated "
							+ title.displayName + " " + victim.getName().getString() + "! The seat of " + title.displayName + " is open.")
							.withStyle(title.color));
				}
			}
		});
	}

	public static Title titleOf(Player player) {
		return EmpireData.title(player);
	}

	/** Gives the player their next title if they now qualify. */
	public static void check(ServerPlayer player) {
		Title next = EmpireData.title(player).next();
		if (next == null || !allDone(requirements(player, next))) {
			return;
		}
		EmpireData.setTitle(player, next);
		MinecraftServer server = player.level().getServer();
		String announcement = switch (next) {
			case EMPEROR -> player.getName().getString() + " is now one of the Four Emperors of the Sea!";
			case PIRATE_KING -> player.getName().getString() + " found the One Piece and is the new Pirate King!";
			case KING_OF_THE_WORLD -> player.getName().getString() + " has become the King of the World!";
			default -> "";
		};
		broadcast(server, Component.literal(announcement).withStyle(next.color, ChatFormatting.BOLD));
		player.sendSystemMessage(Component.literal("Your loot grows by " + (int) (next.lootBonus * 100) + "%, your kingdoms pay "
				+ next.taxPerDay + " Berries a day, and you may rule " + next.maxKingdoms + " kingdoms.").withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal("But the World Government will not allow it. Expect the Navy far more often, and Buster Calls.")
				.withStyle(ChatFormatting.DARK_AQUA));
		((ServerLevel) player.level()).playSound(null, player.blockPosition(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE,
				SoundSource.PLAYERS, 1.0f, 0.8f);
	}

	private static boolean allDone(List<Requirement> list) {
		for (Requirement requirement : list) {
			if (!requirement.done()) {
				return false;
			}
		}
		return true;
	}

	/** What it takes to earn this title, and what the player already has. */
	public static List<Requirement> requirements(ServerPlayer player, Title title) {
		List<Requirement> list = new ArrayList<>();
		MinecraftServer server = player.level().getServer();
		long bounty = Bounty.get(player);
		switch (title) {
			case EMPEROR -> {
				list.add(new Requirement("A bounty of 1,000,000,000 Berries (" + Bounty.format(bounty) + ")", bounty >= 1_000_000_000L));
				list.add(new Requirement("Beat Kaido, Big Mom, Shanks or Blackbeard on Hard", beatAny(player, EMPERORS, ":hard")));
				Crew crew = player.getAttached(CrewAttachments.CREW);
				int size = crew != null ? crew.size() : 0;
				list.add(new Requirement("A crew of 6 or more (" + size + ")", size >= 6));
				forgetMissingFlags(player);
				list.add(new Requirement("Plant a Kingdom Flag", !EmpireData.kingdoms(player).isEmpty()));
				list.add(new Requirement("Finish the Wano chapter of the story",
						!StoryGates.gatesOn(player) || StoryProgress.orStart(player).completed(StoryGates.AFTER_WANO)));
			}
			case PIRATE_KING -> {
				list.add(new Requirement("Be an Emperor", EmpireData.title(player).atLeast(Title.EMPEROR)));
				list.add(new Requirement("Reach Laugh Tale and finish the story", StoryProgress.orStart(player).finished()));
			}
			case KING_OF_THE_WORLD -> {
				list.add(new Requirement("Be the Pirate King", EmpireData.title(player).atLeast(Title.PIRATE_KING)));
				list.add(new Requirement("A bounty of 3,000,000,000 Berries (" + Bounty.format(bounty) + ")", bounty >= 3_000_000_000L));
				list.add(new Requirement("Beat all four Admirals (Akainu, Kizaru, Fujitora, Ryokugyu)", beatAll(player, ADMIRALS)));
				HakiData haki = HakiAttachments.get(player);
				list.add(new Requirement("Master Conqueror's Haki (level " + haki.conquerorLevel() + " of " + HakiData.MAX_LEVEL + ")",
						haki.conquerorLevel() >= HakiData.MAX_LEVEL));
			}
			default -> {
			}
		}
		if (title.maxHolders > 0) {
			int taken = EmpireData.otherHolders(server, player.getUUID(), title);
			list.add(new Requirement("A free seat (" + taken + " of " + title.maxHolders + " taken; defeat a holder to free one)",
					taken < title.maxHolders));
		}
		return list;
	}

	private static boolean beatAny(Player player, String[] ids, String suffix) {
		for (String id : ids) {
			if (CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, id + suffix)) {
				return true;
			}
		}
		return false;
	}

	private static boolean beatAll(Player player, String[] ids) {
		for (String id : ids) {
			if (!CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, id)) {
				return false;
			}
		}
		return true;
	}

	/** Drops kingdoms whose flag has been broken (only checks flags in loaded chunks). */
	public static void forgetMissingFlags(ServerPlayer player) {
		ServerLevel overworld = player.level().getServer().overworld();
		for (BlockPos pos : EmpireData.kingdoms(player)) {
			if (overworld.isLoaded(pos) && !overworld.getBlockState(pos).is(EmpireFeature.KINGDOM_FLAG)) {
				EmpireData.removeKingdom(player, pos);
			}
		}
	}

	static void broadcast(MinecraftServer server, Component message) {
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			player.sendSystemMessage(message);
		}
	}

	// ---- Navy pressure, used by the bounty package's hunts and raids ----

	/** Multiplies the chance of a Navy hunt or raid. 1 for pirates without a title. */
	public static float navyChance(ServerPlayer player) {
		return EmpireData.title(player).navyChance;
	}

	/** Shortens the break between Navy hunts or raids for title holders. */
	public static int navyBreak(ServerPlayer player, int breakTicks) {
		return Math.round(breakTicks * EmpireData.title(player).navyBreak);
	}
}
