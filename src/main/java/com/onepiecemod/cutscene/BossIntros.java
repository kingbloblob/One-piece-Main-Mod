package com.onepiecemod.cutscene;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.WeakHashMap;

import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.CharacterEntity;

/**
 * The title card a boss gets the first time it starts a fight with you: cinema bars, the boss's name and title,
 * and a line from them, while your view turns to face them.
 *
 * While it plays the boss stands still and doesn't attack (CharacterEntity asks holding()), so the intro is never
 * a free hit. It ends after about 4 seconds, when every viewer pressed skip, or as soon as someone hits the boss.
 * Players who have already seen this boss's intro don't get it again, and if every nearby player has, the fight
 * starts straight away.
 */
public final class BossIntros {
	/** How long the intro plays (and the boss holds still) if nobody skips. */
	public static final int TICKS = 90;
	/** Players this close to the boss watch the intro. */
	private static final double RANGE = 40;

	private static final class Intro {
		final Set<UUID> viewers = new HashSet<>();
		final Set<UUID> skipped = new HashSet<>();
		long endsAt;
	}

	/** Bosses whose intro is playing right now. Weak, so a boss that unloads mid-intro doesn't leak. */
	private static final Map<CharacterEntity, Intro> RUNNING = new WeakHashMap<>();

	/**
	 * The boss just noticed a target and is about to start the fight (CharacterEntity calls this once).
	 * Sends the intro to every nearby player who hasn't seen this boss's intro yet.
	 *
	 * @return true if an intro started (the boss should wait; the fight starts when holding() turns false)
	 */
	public static boolean start(CharacterEntity boss, ServerLevel level) {
		if (RUNNING.containsKey(boss)) {
			return true;
		}
		CharacterData character = boss.getData();
		if (character == null) {
			return false;
		}
		String key = "boss:" + boss.getCharacterId();
		List<ServerPlayer> watchers = new ArrayList<>();
		for (ServerPlayer player : level.players()) {
			if (!player.isSpectator() && player.distanceToSqr(boss) < RANGE * RANGE
					&& CutsceneFeature.canSend(player) && !CutsceneFeature.seen(player, key)) {
				watchers.add(player);
			}
		}
		if (watchers.isEmpty()) {
			return false;
		}

		CutsceneFeature.Boss info = CutsceneFeature.data().bosses.get(boss.getCharacterId());
		String title = info != null ? info.title : "";
		String line = info != null && !info.line.isEmpty() ? info.line : character.greeting;
		int color = CutsceneFeature.color(info != null ? info.color : "", 0xF2C14E);
		CutsceneFeature.Play packet = new CutsceneFeature.Play(CutsceneFeature.BOSS_INTRO, character.name, title,
				line == null || line.isEmpty() ? List.of() : List.of(character.name + ": " + line), color, TICKS, boss.getId(), 0);

		Intro intro = new Intro();
		intro.endsAt = level.getGameTime() + TICKS;
		for (ServerPlayer player : watchers) {
			CutsceneFeature.markSeen(player, key);
			intro.viewers.add(player.getUUID());
			ServerPlayNetworking.send(player, packet);
		}
		RUNNING.put(boss, intro);
		return true;
	}

	/** Is this boss's intro still playing? While it is, the boss stands still and doesn't attack. */
	public static boolean holding(CharacterEntity boss) {
		if (RUNNING.isEmpty()) {
			return false;
		}
		Intro intro = RUNNING.get(boss);
		if (intro == null) {
			return false;
		}
		if (finished(intro, boss.level().getServer(), boss.level().getGameTime())) {
			RUNNING.remove(boss);
			return false;
		}
		return true;
	}

	/** Somebody hit the boss: the intro is over, the fight is on. */
	public static void interrupt(CharacterEntity boss) {
		if (!RUNNING.isEmpty()) {
			RUNNING.remove(boss);
		}
	}

	/** A player pressed the skip key (or has cutscenes turned off). */
	static void skipped(ServerPlayer player) {
		for (Intro intro : RUNNING.values()) {
			if (intro.viewers.contains(player.getUUID())) {
				intro.skipped.add(player.getUUID());
			}
		}
	}

	private static boolean finished(Intro intro, MinecraftServer server, long now) {
		if (now >= intro.endsAt) {
			return true;
		}
		for (UUID viewer : intro.viewers) {
			if (!intro.skipped.contains(viewer) && server != null && server.getPlayerList().getPlayer(viewer) != null) {
				return false; // Someone is still watching.
			}
		}
		return true;
	}

	/** Drops intros of bosses that died or stopped ticking. Cheap: the map is almost always empty. */
	static void cleanUp(MinecraftServer server) {
		if (RUNNING.isEmpty() || server.getTickCount() % 20 != 0) {
			return;
		}
		Iterator<Map.Entry<CharacterEntity, Intro>> it = RUNNING.entrySet().iterator();
		while (it.hasNext()) {
			Map.Entry<CharacterEntity, Intro> entry = it.next();
			if (entry.getKey().isRemoved() || !entry.getKey().isAlive() || entry.getKey().level().getGameTime() > entry.getValue().endsAt + 40) {
				it.remove();
			}
		}
	}

	private BossIntros() {
	}
}
