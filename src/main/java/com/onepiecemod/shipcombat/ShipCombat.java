package com.onepiecemod.shipcombat;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.WeakHashMap;

import org.jetbrains.annotations.Nullable;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.BossEvent;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.ship.ShipEntity;

/**
 * Runs ship combat every tick: enemy ship captains (ShipBrain), sinking ships, hull bars at the top of the screen,
 * boarding fights, and new encounters at sea. Also handles right-clicking ships (boarding and repairs) and rewards.
 */
public class ShipCombat {
	/** How close you must be to an enemy ship to see its hull bar. */
	private static final double BAR_RANGE = 80;
	private static final double FLEET_BAR_RANGE = 45;
	/** Enemy ships this far from every player sail off (are removed). */
	private static final double DESPAWN_RANGE = 200;

	private static final Set<ShipEntity> LOADED = Collections.newSetFromMap(new WeakHashMap<>());
	private static final Map<ShipEntity, ServerBossEvent> BARS = new WeakHashMap<>();
	private static final Map<ShipEntity, UUID> LAST_ATTACKER = new WeakHashMap<>();
	private static final Map<ShipEntity, Long> LAST_HIT = new WeakHashMap<>();
	/** No dropping anchor this long after your ship was hit (dropping anchor and setting sail again mends the hull). */
	private static final int BATTLE_TICKS = 20 * 30;
	/** ...or while an enemy ship hunting you is this close. */
	private static final double BATTLE_RANGE = 80;

	static void initialize() {
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity instanceof ShipEntity ship) {
				LOADED.add(ship);
				ShipHull.resumeIfBroken(ship);
			}
		});
		ServerEntityEvents.ENTITY_UNLOAD.register((entity, level) -> {
			if (entity instanceof ShipEntity ship) {
				LOADED.remove(ship);
				removeBar(ship);
			}
		});
		ServerTickEvents.END_SERVER_TICK.register(ShipCombat::tick);
	}

	public static List<ShipEntity> loadedShips() {
		return new ArrayList<>(LOADED);
	}

	private static void tick(MinecraftServer server) {
		int time = server.getTickCount();
		for (ShipEntity ship : loadedShips()) {
			if (ship.isRemoved() || !(ship.level() instanceof ServerLevel level)) {
				LOADED.remove(ship);
				removeBar(ship);
				continue;
			}
			if (ship.sinking) {
				ShipHull.tickSinking(ship, level);
			} else {
				Ramming.tick(ship, level);
				ShipBrain brain = ShipBrain.of(ship);
				if (brain != null) {
					brain.tick(level);
					if (time % 100 == 0 && brain.awayFromPlayers(level, DESPAWN_RANGE)) {
						ship.discard(); // Nobody around for 30 seconds: sailed over the horizon.
					}
				}
			}
		}
		if (time % 10 == 0) {
			updateBars();
		}
		if (time % 20 == 0) {
			Boarding.tick(server);
			ShipCrewHelp.tick(server);
			EnemyBoarders.tick(server);
			GunCrews.tick(server);
			NavalBattles.tick(server);
		}
		SeaEncounters.tick(server);
		ShipSpecials.tick(server);
	}

	// ---- Right-clicking a ship ----

	static InteractionResult onRightClickShip(ShipEntity ship, ServerPlayer player) {
		if (ShipBrain.isAi(ship)) {
			return Boarding.board(player, ship);
		}
		ItemStack held = player.getItemInHand(InteractionHand.MAIN_HAND);
		if (player.getVehicle() == ship && ShipHull.tryRepair(ship, player, held)) {
			return InteractionResult.SUCCESS;
		}
		return InteractionResult.PASS;
	}

	// ---- Hits and rewards ----

	/**
	 * Why this ship can't drop anchor right now, or null if it can. Docking and setting sail again gives a fresh hull,
	 * so in the middle of a sea battle that would be a free full repair.
	 */
	@Nullable
	public static String dockBlockedReason(ShipEntity ship) {
		if (!(ship.level() instanceof ServerLevel level)) {
			return null;
		}
		String war = com.onepiecemod.multiplayer.SeaWars.dockBlockedReason(ship);
		if (war != null) {
			return war;
		}
		Long hit = LAST_HIT.get(ship);
		if (hit != null && level.getGameTime() - hit < BATTLE_TICKS) {
			long seconds = (BATTLE_TICKS - (level.getGameTime() - hit)) / 20 + 1;
			return "You're under fire! You can drop anchor " + seconds + " seconds after the last hit.";
		}
		for (ShipEntity other : loadedShips()) {
			ShipBrain brain = ShipBrain.of(other);
			if (brain != null && other.level() == level && !other.sinking && other.distanceToSqr(ship) < BATTLE_RANGE * BATTLE_RANGE
					&& brain.isTargeting(ship)) {
				return "An enemy ship is closing in! Sink her, or sail away, before you drop anchor.";
			}
		}
		return null;
	}

	/** True if this ship was hit within the last `ticks` ticks. */
	public static boolean recentlyHit(ShipEntity ship, int ticks) {
		Long hit = LAST_HIT.get(ship);
		return hit != null && ship.level().getGameTime() - hit < ticks;
	}

	@Nullable
	static ServerPlayer lastAttacker(ShipEntity ship, ServerLevel level) {
		UUID last = LAST_ATTACKER.get(ship);
		return last == null ? null : level.getServer().getPlayerList().getPlayer(last);
	}

	static void noteHit(ShipEntity ship, @Nullable ServerPlayer attacker, @Nullable ShipEntity fromShip) {
		LAST_HIT.put(ship, ship.level().getGameTime());
		if (attacker != null) {
			LAST_ATTACKER.put(ship, attacker.getUUID());
		}
		ShipBrain brain = ShipBrain.of(ship);
		if (brain != null) {
			brain.hitBy(fromShip, attacker);
		}
	}

	/** Sinking an enemy ship pays: berries and salvage float up, and sinking Marines raises your bounty. */
	static void rewardSinking(ShipEntity ship, ServerLevel level, @Nullable ServerPlayer attacker) {
		ShipBrain.Faction faction = ShipBrain.factionOf(ship);
		if (faction == null) {
			return; // A player's ship: whatever was in its chests already spilled.
		}
		if (attacker == null) {
			UUID last = LAST_ATTACKER.get(ship);
			attacker = last == null ? null : level.getServer().getPlayerList().getPlayer(last);
		}
		int tier = ShipBrain.tierOf(ship);
		Vec3 at = ship.position().add(0, ship.getLayout().waterline + 1, 0);
		var random = level.getRandom();
		ShipHull.drop(level, at, new ItemStack(CharacterFeature.BERRY, 10 + tier * 6 + random.nextInt(10)));
		ShipHull.drop(level, at, new ItemStack(ShipCombatFeature.CANNONBALL, 3 + random.nextInt(6)));
		ShipHull.drop(level, at, new ItemStack(Items.GUNPOWDER, 2 + random.nextInt(4)));
		ShipHull.drop(level, at, new ItemStack(Items.IRON_INGOT, 1 + random.nextInt(3)));
		if (random.nextInt(3) == 0) {
			ShipHull.drop(level, at, new ItemStack(Items.GOLD_INGOT, 1 + random.nextInt(2 + tier)));
		}
		if (tier >= 3 && random.nextInt(4) == 0) {
			ShipHull.drop(level, at, new ItemStack(Items.DIAMOND));
		}

		if (attacker != null && attacker.distanceToSqr(ship) < 160 * 160) {
			com.onepiecemod.advancement.AdvancementFeature.grant(attacker, "journey/sink_ship");
			if (faction == ShipBrain.Faction.MARINE) {
				Bounty.raise(attacker, 8_000_000L * (tier + 1), "You sank a Marine warship!", false);
			} else {
				attacker.sendSystemMessage(Component.literal("You sank a pirate ship! Grab the salvage before it drifts off.")
						.withStyle(ChatFormatting.GOLD));
			}
		}
	}

	// ---- Hull bars ----

	private static void updateBars() {
		Set<ShipEntity> enemiesInView = new HashSet<>();
		for (ShipEntity ship : loadedShips()) {
			if (!ship.isRemoved() && !ship.sinking && ShipBrain.isAi(ship)) {
				enemiesInView.add(ship);
			}
		}
		for (ShipEntity ship : loadedShips()) {
			if (ship.isRemoved() || !(ship.level() instanceof ServerLevel level)) {
				continue;
			}
			float max = ShipHull.max(ship);
			float hull = Math.max(0, ShipHull.get(ship));
			boolean enemy = ShipBrain.isAi(ship);

			Set<ServerPlayer> viewers = new HashSet<>();
			if (enemy) {
				// Fleets have their own bar (NavalBattles), so each fleet ship's hull only shows up close.
				double range = NavalBattles.isFleetShip(ship) ? FLEET_BAR_RANGE : BAR_RANGE;
				for (ServerPlayer player : level.players()) {
					if (player.distanceToSqr(ship) < range * range) {
						viewers.add(player);
					}
				}
			} else {
				// Your own hull: shown once it's damaged, or when an enemy ship is near.
				boolean danger = hull < max || enemiesInView.stream().anyMatch(e -> e.level() == level && e.distanceToSqr(ship) < BAR_RANGE * BAR_RANGE);
				if (danger) {
					for (Entity passenger : ship.getPassengers()) {
						if (passenger instanceof ServerPlayer player) {
							viewers.add(player);
						}
					}
				}
			}

			if (viewers.isEmpty()) {
				removeBar(ship);
				continue;
			}
			ServerBossEvent bar = BARS.computeIfAbsent(ship, s -> new ServerBossEvent(UUID.randomUUID(), Component.empty(),
					enemy ? BossEvent.BossBarColor.RED : BossEvent.BossBarColor.GREEN, BossEvent.BossBarOverlay.NOTCHED_10));
			String title = enemy ? ship.getName().getString() : "Your ship's hull";
			bar.setName(Component.literal(title + "  " + Math.round(hull) + " / " + Math.round(max)));
			bar.setProgress(max <= 0 ? 0 : Math.min(1f, hull / max));
			for (ServerPlayer player : new ArrayList<>(bar.getPlayers())) {
				if (!viewers.contains(player)) {
					bar.removePlayer(player);
				}
			}
			for (ServerPlayer player : viewers) {
				if (!bar.getPlayers().contains(player)) {
					bar.addPlayer(player);
				}
			}
		}
	}

	private static void removeBar(ShipEntity ship) {
		ServerBossEvent bar = BARS.remove(ship);
		if (bar != null) {
			bar.removeAllPlayers();
		}
	}
}
