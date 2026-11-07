package com.onepiecemod.multiplayer;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.jetbrains.annotations.Nullable;

import net.minecraft.core.Holder;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;

import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.shipcombat.ShipCombat;
import com.onepiecemod.shipcombat.ShipHull;

/**
 * Jobs for real players in a player crew, set by the captain with /crew role <player> <role>.
 * The nine Straw Hat jobs work like a hired crewmate's perk, but for the whole crew around that player
 * (the player gets it too), plus First Mate, who can do the captain's paperwork.
 *
 * Extras on top of the aura:
 *  - Doctor: also patches up crewmates below 3/4 health.
 *  - Sniper: monsters and rival-crew players nearby glow.
 *  - Shipwright: slowly mends the hull of the crew ship they stand on, between hits.
 */
public class PlayerRoles {
	public static final String FIRST_MATE = "first_mate";
	private static final double AURA_RANGE = 48.0;
	private static final double SNIPER_RANGE = 32.0;
	private static final float SHIPWRIGHT_MEND = 2f; // hull points every 2 seconds

	/** Every role a player can be given, as ids: first_mate plus the nine crew roles. */
	public static List<String> ids() {
		List<String> ids = new ArrayList<>();
		ids.add(FIRST_MATE);
		for (CrewRole role : CrewRole.values()) {
			ids.add(role.id());
		}
		return ids;
	}

	public static boolean isRole(String id) {
		return FIRST_MATE.equals(id) || CrewRole.byId(id) != null;
	}

	public static String title(String id) {
		if (FIRST_MATE.equals(id)) {
			return "First Mate";
		}
		CrewRole role = id == null ? null : CrewRole.byId(id);
		return role != null ? role.title() : "Deckhand";
	}

	public static String perk(String id) {
		if (FIRST_MATE.equals(id)) {
			return "Can invite and kick crewmates, and start, accept or surrender sea battles";
		}
		CrewRole role = CrewRole.byId(id);
		if (role == null) {
			return "";
		}
		return switch (role) {
			case DOCTOR -> "Regeneration for crewmates below 3/4 health";
			case SNIPER -> "Monsters and rival players nearby glow";
			case SHIPWRIGHT -> "Haste I; mends the crew ship's hull between hits";
			default -> role.perk();
		};
	}

	@Nullable
	public static String roleOf(MinecraftServer server, UUID player) {
		UUID captain = PlayerCrews.captainOf(server, player);
		PirateCrew crew = PlayerCrews.get(server, captain);
		return crew == null ? null : crew.roles.get(player);
	}

	/** The captain, or their First Mate: who may invite, kick and run sea battles. Returns the crew's captain id, or null. */
	@Nullable
	public static UUID officerOf(MinecraftServer server, ServerPlayer player) {
		UUID captain = PlayerCrews.captainOf(server, player.getUUID());
		if (captain == null) {
			return null;
		}
		if (captain.equals(player.getUUID())) {
			return captain;
		}
		PirateCrew crew = PlayerCrews.get(server, captain);
		return crew != null && FIRST_MATE.equals(crew.roles.get(player.getUUID())) ? captain : null;
	}

	/** Every 2 seconds: each player with a role helps the crew players around them. */
	static void tick(MinecraftServer server) {
		for (ServerPlayer worker : server.getPlayerList().getPlayers()) {
			UUID captain = PlayerCrews.captainOf(server, worker.getUUID());
			PirateCrew crew = PlayerCrews.get(server, captain);
			if (crew == null || !worker.isAlive() || worker.isSpectator()) {
				continue;
			}
			String id = crew.roles.get(worker.getUUID());
			CrewRole role = id == null ? null : CrewRole.byId(id);
			if (role == null) {
				continue;
			}
			for (ServerPlayer mate : crewNear(server, worker, captain, crew)) {
				help(role, mate);
			}
			if (role == CrewRole.SNIPER) {
				spot(server, worker);
			} else if (role == CrewRole.SHIPWRIGHT) {
				mendShip(worker, captain);
			}
		}
	}

	/** Online players of this crew (captain included) within the aura range of the worker, the worker too. */
	private static List<ServerPlayer> crewNear(MinecraftServer server, ServerPlayer worker, UUID captain, PirateCrew crew) {
		List<ServerPlayer> near = new ArrayList<>();
		List<UUID> everyone = new ArrayList<>(crew.members);
		everyone.add(captain);
		for (UUID id : everyone) {
			ServerPlayer mate = server.getPlayerList().getPlayer(id);
			if (mate != null && mate.isAlive() && mate.level() == worker.level() && mate.distanceToSqr(worker) < AURA_RANGE * AURA_RANGE) {
				near.add(mate);
			}
		}
		return near;
	}

	private static void help(CrewRole role, ServerPlayer mate) {
		switch (role) {
			case SWORDSMAN -> effect(mate, MobEffects.STRENGTH);
			case NAVIGATOR -> effect(mate, MobEffects.SPEED);
			case SNIPER -> effect(mate, MobEffects.NIGHT_VISION);
			case COOK -> {
				if (mate.getFoodData().needsFood()) {
					mate.getFoodData().eat(1, 0.3f);
				}
			}
			case DOCTOR -> {
				if (mate.getHealth() < mate.getMaxHealth() * 0.75f) {
					effect(mate, MobEffects.REGENERATION);
				}
			}
			case SHIPWRIGHT -> effect(mate, MobEffects.HASTE);
			case ARCHAEOLOGIST -> effect(mate, MobEffects.LUCK);
			case MUSICIAN -> effect(mate, MobEffects.RESISTANCE);
			case HELMSMAN -> {
				effect(mate, MobEffects.WATER_BREATHING);
				effect(mate, MobEffects.DOLPHINS_GRACE);
			}
		}
	}

	/** Sniper's eye: monsters, and players of crews at war with ours, glow for a few seconds. */
	private static void spot(MinecraftServer server, ServerPlayer sniper) {
		for (LivingEntity target : sniper.level().getEntitiesOfClass(LivingEntity.class, sniper.getBoundingBox().inflate(SNIPER_RANGE),
				target -> target.isAlive() && target != sniper
						&& (target instanceof Enemy || target instanceof ServerPlayer other && SeaWars.atWar(server, sniper, other)))) {
			target.addEffect(new MobEffectInstance(MobEffects.GLOWING, 60, 0, true, false, false));
		}
	}

	/** Shipwright aboard a crew ship that hasn't been hit for 5 seconds: the hull slowly comes back. */
	private static void mendShip(ServerPlayer shipwright, UUID captain) {
		ShipEntity ship = ShipEntity.aboard(shipwright);
		if (ship == null || ship.sinking || ShipCombat.recentlyHit(ship, 100)) {
			return;
		}
		UUID owner = ship.getAttached(SharedShips.OWNER);
		if (owner == null || !owner.equals(captain)) {
			return;
		}
		float max = ShipHull.max(ship);
		float hull = ShipHull.get(ship);
		if (hull < max) {
			ship.setAttached(ShipHull.HULL, Math.min(max, hull + SHIPWRIGHT_MEND));
		}
	}

	private static void effect(ServerPlayer player, Holder<MobEffect> effect) {
		player.addEffect(new MobEffectInstance(effect, 100, 0, true, false, true));
	}

	/** Clears a player's role when they leave a crew. */
	static void forget(PirateCrew crew, UUID player) {
		crew.roles.remove(player);
	}

	/** Who holds a role in this crew, if anyone. */
	@Nullable
	static UUID holder(PirateCrew crew, String role) {
		for (Map.Entry<UUID, String> entry : crew.roles.entrySet()) {
			if (entry.getValue().equals(role)) {
				return entry.getKey();
			}
		}
		return null;
	}
}
