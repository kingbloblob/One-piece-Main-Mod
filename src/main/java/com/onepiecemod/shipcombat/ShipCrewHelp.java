package com.onepiecemod.shipcombat;

import java.util.UUID;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.multiplayer.SharedShips;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipUpgrades;

/**
 * Your crew at sea. Once a second, for every ship a player's crew owns:
 *  - Navigator (like Nami): reads the wind, +15% top speed.
 *  - Helmsman (like Jinbe): steers through anything, turns 30% faster.
 *  - Shipwright (like Franky): patches the hull, 1 point a second once the ship hasn't been hit for 10 seconds.
 *  - Sniper (like Usopp): aims the cannons (see Cannons.fireFromKey).
 * Crewmates count once they've joined your crew, wherever they are (they mind the ship from below decks).
 * Also applies sail upgrades and chain shot to how the ship handles, and burns ships hit by fire shot.
 */
public class ShipCrewHelp {
	private static final float NAVIGATOR_SPEED = 1.15f;
	private static final float HELMSMAN_TURN = 1.3f;
	private static final float SHIPWRIGHT_MEND = 1f;
	private static final int SHIPWRIGHT_WAIT = 200;
	private static final float ADAM_HULL_MEND = 0.5f;
	private static final float CHAINED_SPEED = 0.5f;
	private static final float CHAINED_TURN = 0.6f;

	/** Extra {speed, turn} for a crew's home ship (set by the crewship package; 1 = none). */
	public static java.util.function.Function<ShipEntity, float[]> homeShipBonus = ship -> new float[] {1f, 1f};

	/** Extra speed from tamed Sea Kings pulling the ship in a Towing Harness (set by pet.PetTowing; 1 = none). */
	public static java.util.function.Function<ShipEntity, Float> towBonus = ship -> 1f;

	static void tick(MinecraftServer server) {
		for (ShipEntity ship : ShipCombat.loadedShips()) {
			if (ship.isRemoved() || ship.sinking || !(ship.level() instanceof ServerLevel level)) {
				continue;
			}
			boolean enemy = ShipBrain.factionOf(ship) != null;
			float speed = enemy ? 1f : ShipUpgrades.speedBonus(ShipUpgrades.sails(ship.getLayout()));
			float turn = 1f;
			if (!enemy) {
				Crew crew = crewOf(ship);
				if (has(crew, CrewRole.NAVIGATOR)) {
					speed *= NAVIGATOR_SPEED;
				}
				if (has(crew, CrewRole.HELMSMAN)) {
					turn *= HELMSMAN_TURN;
				}
				float[] home = homeShipBonus.apply(ship);
				speed *= home[0];
				turn *= home[1];
				speed *= towBonus.apply(ship);
				if (has(crew, CrewRole.SHIPWRIGHT) && !ShipCombat.recentlyHit(ship, SHIPWRIGHT_WAIT) && ShipHull.mend(ship, SHIPWRIGHT_MEND)
						&& server.getTickCount() % 100 == 0) {
					level.sendParticles(ParticleTypes.HAPPY_VILLAGER, ship.getX(), ship.getY() + ship.getLayout().waterline + 1.5, ship.getZ(),
							4, 1.5, 0.5, 1.5, 0);
				}
			}
			// Hull V: an Adam Wood hull that mends itself slowly, even in the middle of a battle.
			if (!enemy && ShipUpgrades.hull(ship.getLayout()) >= ShipUpgrades.MAX_LEVEL) {
				ShipHull.mend(ship, ADAM_HULL_MEND);
			}
			if (ShipHull.chained(ship)) {
				speed *= CHAINED_SPEED;
				turn *= CHAINED_TURN;
			}
			ship.setHandling(speed, turn);
			ShipHull.tickBurning(ship, level);
		}
	}

	/** True if the crew that owns this ship has someone in that role. */
	public static boolean has(ShipEntity ship, CrewRole role) {
		return has(crewOf(ship), role);
	}

	private static boolean has(Crew crew, CrewRole role) {
		return crew != null && crew.member(role) != null;
	}

	/** The crew that owns the ship (its captain must be online), or the captain at the wheel's own crew. */
	private static Crew crewOf(ShipEntity ship) {
		UUID owner = ship.getAttached(SharedShips.OWNER);
		ServerPlayer captain = owner == null || ship.level().getServer() == null ? null : ship.level().getServer().getPlayerList().getPlayer(owner);
		if (captain == null && ship.getControllingPassenger() instanceof ServerPlayer atTheWheel) {
			captain = atTheWheel;
		}
		return captain == null ? null : captain.getAttached(CrewAttachments.CREW);
	}
}
