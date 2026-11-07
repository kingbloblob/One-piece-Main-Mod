package com.onepiecemod.multiplayer;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Set;
import java.util.UUID;
import java.util.WeakHashMap;

import net.minecraft.ChatFormatting;
import net.minecraft.core.UUIDUtil;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.Event;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.ship.ShipEntity;

/**
 * Crew ships. A ship belongs to the crew of whoever sails it first.
 *  - Your crew: board, steer and use the chests, like your own ship.
 *  - Allied crews: hop aboard as passengers once one of your crew is at the helm. No chests, no steering.
 *  - Everyone else: can't board.
 * Docking turns a ship back into blocks, and the next crew to set sail with it claims it again.
 */
public class SharedShips {
	/** The captain id of the crew that owns this ship, saved on the ship entity. */
	public static final AttachmentType<UUID> OWNER = AttachmentRegistry.create(
			OnePieceMod.id("ship_owner"),
			builder -> builder.persistent(UUIDUtil.CODEC)
	);

	/** Runs before the ship's own right-click handler, so we can say no first. */
	private static final Identifier EARLY = OnePieceMod.id("shared_ships");

	/** Loaded ships, checked once a second for a new captain to claim them. */
	private static final Set<ShipEntity> LOADED = Collections.newSetFromMap(new WeakHashMap<>());

	public static void initialize() {
		UseEntityCallback.EVENT.addPhaseOrdering(EARLY, Event.DEFAULT_PHASE);
		UseEntityCallback.EVENT.register(EARLY, (player, level, hand, entity, hitResult) ->
				entity instanceof ShipEntity ship && player instanceof ServerPlayer serverPlayer && hand == InteractionHand.MAIN_HAND
						? checkUse(ship, serverPlayer) : InteractionResult.PASS);

		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity instanceof ShipEntity ship) {
				LOADED.add(ship);
			}
		});

		// Setting sail from the Ship's Wheel puts you straight aboard, without a right-click. Claim those ships here.
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 20 != 0) {
				return;
			}
			for (ShipEntity ship : new ArrayList<>(LOADED)) {
				if (ship.isRemoved()) {
					LOADED.remove(ship);
				} else if (!ship.hasAttached(OWNER) && ship.getControllingPassenger() instanceof ServerPlayer captain) {
					claim(ship, captain);
				}
			}
		});
	}

	static InteractionResult checkUse(ShipEntity ship, ServerPlayer player) {
		MinecraftServer server = player.level().getServer();
		UUID owner = ship.getAttached(OWNER);
		if (owner == null) {
			// Stepping aboard a passing merchant or a derelict doesn't make her yours; taking her wheel does (tick below).
			if (!ship.entityTags().contains(com.onepiecemod.voyage.WanderingShips.TAG)) {
				claim(ship, player);
			}
			return InteractionResult.PASS;
		}
		if (isCrew(server, owner, player)) {
			return InteractionResult.PASS;
		}

		String crewName = PlayerCrews.crewName(server, owner);
		if (PlayerCrews.allied(server, owner, PlayerCrews.crewKey(server, player))) {
			// Aboard = at a seat OR walking her deck. Deck walkers aren't riding the ship, so getVehicle() let an ally
			// standing on deck open the crew's chests and take the helm.
			if (ShipEntity.aboard(player) == ship || player.getVehicle() == ship) {
				player.sendOverlayMessage(Component.literal("Only the " + crewName + " can use their ship's storage and helm.").withStyle(ChatFormatting.YELLOW));
				return InteractionResult.FAIL;
			}
			boolean crewAtHelm = ship.getControllingPassenger() instanceof ServerPlayer captain && isCrew(server, owner, captain);
			if (!crewAtHelm) {
				player.sendOverlayMessage(Component.literal("Wait for the " + crewName + " to take the helm, then hop aboard.").withStyle(ChatFormatting.YELLOW));
				return InteractionResult.FAIL;
			}
			return InteractionResult.PASS;
		}

		// In a sea battle with her crew: board her once she's battered below half hull (SeaWars).
		if (SeaWars.tryBoard(ship, player, owner)) {
			return InteractionResult.FAIL;
		}
		player.sendOverlayMessage(Component.literal("This ship belongs to the " + crewName + ". Join or ally with them to board.").withStyle(ChatFormatting.RED));
		return InteractionResult.FAIL;
	}

	/** True if the player sails in the crew that owns the ship (or claimed it themselves before joining a crew). */
	public static boolean isCrew(MinecraftServer server, UUID owner, ServerPlayer player) {
		return owner.equals(player.getUUID()) || owner.equals(PlayerCrews.crewKey(server, player));
	}

	private static void claim(ShipEntity ship, ServerPlayer player) {
		MinecraftServer server = player.level().getServer();
		UUID crew = PlayerCrews.crewKey(server, player);
		ship.setAttached(OWNER, crew);
		player.sendSystemMessage(Component.literal("This ship now sails under the flag of the "
				+ PlayerCrews.crewName(server, crew) + ". Only your crew can steer it or open its chests.").withStyle(ChatFormatting.AQUA));
	}
}
