package com.onepiecemod.worldevent;

import java.util.UUID;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.BossEvent;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.bounty.Bounty;

/**
 * The Reverie: every 4 in-game days (80 minutes of play) the kings of the world meet at Mary Geoise for 10 minutes.
 *  - While it runs, Marine fleets sail three times as often, many escorting a Royal Galleon full of treasure.
 *    Attacking one is a crime the whole world hears about (and a big bounty).
 *  - The Navy is on edge: trouble on islands counts 50% more.
 *  - At the end the kings decide something, and the papers report it. Some decisions change the world for an hour:
 *    more Marine fleets, quicker Buster Calls, or higher bounties for the worst pirates.
 * The schedule is saved with the world.
 */
public class Reverie {
	private static final long FIRST_AT = 24000L * 3;
	private static final long EVERY = 24000L * 4;
	private static final long LASTS = 20L * 60 * 10;
	private static final long EFFECT_LASTS = 20L * 60 * 60;

	public enum Outcome { NONE, NAVY_REINFORCED, BUSTER_CALLS_EASIER, BOUNTIES_RAISED, WARLORDS_ABOLISHED, KING_MISSING }

	/** next = game time of the next Reverie, until = end of the current one (0 = none), effect + effectUntil = its aftermath. */
	public record State(long next, long until, int effect, long effectUntil) {
		static final Codec<State> CODEC = RecordCodecBuilder.create(i -> i.group(
				Codec.LONG.fieldOf("next").forGetter(State::next),
				Codec.LONG.fieldOf("until").forGetter(State::until),
				Codec.INT.fieldOf("effect").forGetter(State::effect),
				Codec.LONG.fieldOf("effect_until").forGetter(State::effectUntil)
		).apply(i, State::new));
	}

	public static final AttachmentType<State> SAVED = AttachmentRegistry.create(
			OnePieceMod.id("reverie"),
			builder -> builder.persistent(State.CODEC)
	);

	private static ServerBossEvent bar;

	private static State state(MinecraftServer server) {
		return server.overworld().getAttachedOrElse(SAVED, new State(FIRST_AT, 0, 0, 0));
	}

	private static void save(MinecraftServer server, State state) {
		server.overworld().setAttached(SAVED, state);
	}

	public static boolean isActive(MinecraftServer server) {
		return state(server).until() > server.overworld().getGameTime();
	}

	private static Outcome effect(MinecraftServer server) {
		State state = state(server);
		if (state.effectUntil() <= server.overworld().getGameTime()) {
			return Outcome.NONE;
		}
		Outcome[] all = Outcome.values();
		return all[Math.max(0, Math.min(all.length - 1, state.effect()))];
	}

	/** How much more often Marine fleets sail. */
	public static float fleetMultiplier(MinecraftServer server) {
		return (isActive(server) ? 3f : 1f) * (effect(server) == Outcome.NAVY_REINFORCED ? 2f : 1f);
	}

	/** How much more trouble everything makes. */
	public static float troubleMultiplier(MinecraftServer server) {
		return (isActive(server) ? 1.5f : 1f) * (effect(server) == Outcome.BUSTER_CALLS_EASIER ? 1.25f : 1f);
	}

	static void tick(MinecraftServer server) {
		if (server.getTickCount() % 20 != 0) {
			return;
		}
		long now = server.overworld().getGameTime();
		State state = state(server);
		if (state.until() > 0 && now >= state.until()) {
			finish(server, state);
		} else if (state.until() == 0 && now >= state.next() && !server.getPlayerList().getPlayers().isEmpty()) {
			start(server);
		}
		updateBar(server);
	}

	static void start(MinecraftServer server) {
		long now = server.overworld().getGameTime();
		State state = state(server);
		save(server, new State(now + EVERY, now + LASTS, state.effect(), state.effectUntil()));
		WorldNews.report(server, "THE REVERIE BEGINS! Kings from fifty nations sail to Mary Geoise under Marine escort.", ChatFormatting.LIGHT_PURPLE);
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			player.sendSystemMessage(Component.literal("For 10 minutes, Marine fleets escort Royal Galleons across the sea, and the Navy is on edge.")
					.withStyle(ChatFormatting.LIGHT_PURPLE));
		}
	}

	static void stop(MinecraftServer server) {
		State state = state(server);
		if (state.until() > 0) {
			finish(server, state);
		}
	}

	private static void finish(MinecraftServer server, State state) {
		long now = server.overworld().getGameTime();
		RandomSource random = server.overworld().getRandom();
		Outcome[] picks = {Outcome.NAVY_REINFORCED, Outcome.BUSTER_CALLS_EASIER, Outcome.BOUNTIES_RAISED, Outcome.WARLORDS_ABOLISHED, Outcome.KING_MISSING};
		Outcome outcome = picks[random.nextInt(picks.length)];
		save(server, new State(Math.max(state.next(), now + 24000L), 0, outcome.ordinal(), now + EFFECT_LASTS));
		String headline = switch (outcome) {
			case NAVY_REINFORCED -> "REVERIE ENDS: the kings fund a bigger Navy. Expect twice as many Marine fleets at sea for a while.";
			case BUSTER_CALLS_EASIER -> "REVERIE ENDS: the World Government vows to crush piracy. Islands that harbour pirates will be Buster Called sooner.";
			case BOUNTIES_RAISED -> "REVERIE ENDS: the kings demand action against the worst pirates. Big bounties raised by 10%!";
			case WARLORDS_ABOLISHED -> "REVERIE ENDS: the Seven Warlords of the Sea system is abolished! Former Warlords are now hunted like any pirate.";
			default -> "REVERIE ENDS: a king has gone missing from Mary Geoise. Nobody will say where.";
		};
		WorldNews.report(server, headline, ChatFormatting.LIGHT_PURPLE);
		if (outcome == Outcome.BOUNTIES_RAISED) {
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				long bounty = Bounty.get(player);
				if (bounty >= 100_000_000L) {
					Bounty.raise(player, bounty / 10, "The kings at the Reverie named you a menace.", false);
				}
			}
		}
		if (bar != null) {
			bar.removeAllPlayers();
		}
	}

	private static void updateBar(MinecraftServer server) {
		State state = state(server);
		long now = server.overworld().getGameTime();
		if (state.until() <= now) {
			if (bar != null) {
				bar.removeAllPlayers();
			}
			return;
		}
		if (bar == null) {
			bar = new ServerBossEvent(UUID.randomUUID(), Component.literal("The Reverie at Mary Geoise"), BossEvent.BossBarColor.PINK,
					BossEvent.BossBarOverlay.PROGRESS);
		}
		bar.setProgress(Math.max(0, Math.min(1, (state.until() - now) / (float) LASTS)));
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			bar.addPlayer(player);
		}
	}

	static void unload() {
		if (bar != null) {
			bar.removeAllPlayers();
			bar = null;
		}
	}

	static String status(MinecraftServer server) {
		long now = server.overworld().getGameTime();
		State state = state(server);
		if (state.until() > now) {
			return "The Reverie is on now (" + (state.until() - now) / 1200 + " min left).";
		}
		long wait = Math.max(0, state.next() - now);
		Outcome effect = effect(server);
		return "Next Reverie in about " + wait / 1200 + " minutes." + (effect != Outcome.NONE ? " Last Reverie's decision still in force: "
				+ effect.name().toLowerCase().replace('_', ' ') + "." : "");
	}
}
