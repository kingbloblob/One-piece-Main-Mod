package com.onepiecemod.multiplayer;

import net.minecraft.resources.Identifier;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.Event;

import com.onepiecemod.OnePieceMod;

/**
 * Crews of real players: invite friends into your crew, share ships, add up bounties, and make alliances.
 * Builds on the crew feature (/crew create makes you a captain). OnePieceMod calls initialize() once while the game loads.
 */
public class MultiplayerFeature {
	/**
	 * The friendly-fire check runs before every other ALLOW_DAMAGE listener. Otherwise a crewmate's punch was blocked only
	 * after Haki dodges (free Observation XP), Logia dodges, Kami-e or a Reject Dial had already reacted to it.
	 */
	private static final Identifier FRIENDLY_FIRE = OnePieceMod.id("friendly_fire");

	public static void initialize() {
		PlayerCrews.initialize();
		PlayerCrewCommands.initialize();
		CrewUpkeep.initialize();
		SharedShips.initialize();
		CoopCommands.initialize();
		SeaWars.initialize();
		CrewBounties.initialize();

		// No friendly fire between players in the same crew or allied crews, their hired crewmates and kingdom guards.
		ServerLivingEntityEvents.ALLOW_DAMAGE.addPhaseOrdering(FRIENDLY_FIRE, Event.DEFAULT_PHASE);
		ServerLivingEntityEvents.ALLOW_DAMAGE.register(FRIENDLY_FIRE, (entity, source, amount) -> {
			if (source.getEntity() == null || source.getEntity() == entity || entity.level().getServer() == null) {
				return true;
			}
			return !com.onepiecemod.crew.CrewmateEntity.sameCrew(entity, source.getEntity())
					&& !PlayerCrews.friendly(entity.level().getServer(), entity, source.getEntity());
		});
	}
}
