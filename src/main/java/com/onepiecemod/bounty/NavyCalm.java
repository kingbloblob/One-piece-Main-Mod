package com.onepiecemod.bounty;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Predicate;

import net.minecraft.server.level.ServerPlayer;

import com.onepiecemod.character.CharacterEntity;

/**
 * When the Navy leaves a pirate alone. Marine hunts, Navy raids and bounty hunters only start when
 * {@link #canStart} says yes:
 * - Not while something big is already going on: a story event, an endgame raid, a boss fight
 *   (other parts of the mod add their own events with {@link #register}).
 * - Not while lying low at home: within {@link #HOME_RADIUS} blocks of the bed or Respawn Anchor you sleep at.
 */
public final class NavyCalm {
	/** How close to your bed counts as "at home". */
	public static final double HOME_RADIUS = 48.0;
	/** A boss this close that is fighting you means you're in a boss fight. */
	private static final double BOSS_FIGHT_RANGE = 40.0;

	private static final List<Predicate<ServerPlayer>> BUSY = new CopyOnWriteArrayList<>();

	private NavyCalm() {
	}

	/**
	 * Adds a "this player is in the middle of something big" check, like a raid or a war.
	 * While any check says yes, no new Marine hunt, Navy raid or bounty hunter starts for that player.
	 */
	public static void register(Predicate<ServerPlayer> busy) {
		BUSY.add(busy);
	}

	/** True if a new hunt, raid or bounty hunter may start for this player right now. */
	public static boolean canStart(ServerPlayer player) {
		// Nothing new starts while the player is on the death screen: it would land where they died, not where they respawn.
		return player.isAlive() && !isBusy(player) && !isHome(player);
	}

	/** In a story event, an endgame raid, a boss fight, or anything else registered. */
	public static boolean isBusy(ServerPlayer player) {
		if (NavyRaids.isRaiding(player)
				|| com.onepiecemod.endgame.Raids.raidOf(player) != null
				|| inBossFight(player)) {
			return true;
		}
		for (Predicate<ServerPlayer> check : BUSY) {
			if (check.test(player)) {
				return true;
			}
		}
		return false;
	}

	/** Lying low: near the bed or Respawn Anchor you set, in the same world. */
	public static boolean isHome(ServerPlayer player) {
		ServerPlayer.RespawnConfig respawn = player.getRespawnConfig();
		if (respawn == null || respawn.respawnData() == null) {
			return false;
		}
		return respawn.respawnData().dimension() == player.level().dimension()
				&& respawn.respawnData().pos().distSqr(player.blockPosition()) < HOME_RADIUS * HOME_RADIUS;
	}

	private static boolean inBossFight(ServerPlayer player) {
		return !player.level().getEntitiesOfClass(CharacterEntity.class, player.getBoundingBox().inflate(BOSS_FIGHT_RANGE),
				boss -> boss.isBoss() && boss.isAlive() && boss.getTarget() == player).isEmpty();
	}
}
