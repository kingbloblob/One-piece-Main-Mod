package com.onepiecemod.shipcombat.client;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.lwjgl.sdl.SDLScancode;

import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.entity.EntityRenderers;
import net.minecraft.client.renderer.entity.ThrownItemRenderer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.npc.client.NpcRenderer;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.shipcombat.CannonReloadPayload;
import com.onepiecemod.shipcombat.Cannons;
import com.onepiecemod.shipcombat.FireCannonsPayload;
import com.onepiecemod.shipcombat.ShipCombatFeature;
import com.onepiecemod.shipcombat.ShipSpecialPayload;

/**
 * Client-only setup for ship combat: the fire-cannons key (C), Coup de Burst (X) and Gaon Cannon (N),
 * the aim marker that shows where a broadside will land, the cannons-ready line under the crosshair,
 * and how cannonballs and enemy pirates are drawn. OnePieceModClient calls initialize().
 */
public class ShipCombatClient {
	private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(OnePieceMod.id("ships"));

	static final KeyMapping FIRE_CANNONS = KeyMappingHelper.registerKeyMapping(new KeyMapping(
			"key.onepiece.fire_cannons",
			SDLScancode.SDL_SCANCODE_M,
			CATEGORY
	));
	private static final KeyMapping COUP_DE_BURST = KeyMappingHelper.registerKeyMapping(new KeyMapping(
			"key.onepiece.coup_de_burst",
			SDLScancode.SDL_SCANCODE_I,
			CATEGORY
	));
	private static final KeyMapping GAON_CANNON = KeyMappingHelper.registerKeyMapping(new KeyMapping(
			"key.onepiece.gaon_cannon",
			SDLScancode.SDL_SCANCODE_N,
			CATEGORY
	));

	/** Red dots where the broadside will land, and faint ones along the way. */
	private static final DustParticleOptions LANDING = new DustParticleOptions(0xFF3A2A, 1.6f);
	private static final DustParticleOptions ARC = new DustParticleOptions(0xFFE9B8, 0.6f);

	/** When each ship's cannons are ready again, in this world's game time (from CannonReloadPayload). */
	private static final Map<Integer, Long> READY_AT = new HashMap<>();

	public static void initialize() {
		// Drawn like a big thrown snowball, using the ammo item's picture.
		EntityRenderers.register(ShipCombatFeature.CANNONBALL_ENTITY, context -> new ThrownItemRenderer<>(context, 1.6f, false));
		EntityRenderers.register(ShipCombatFeature.SEA_PIRATE, NpcRenderer::new); // Shared pirate/Marine renderer (npc package).

		ClientPlayNetworking.registerGlobalReceiver(CannonReloadPayload.TYPE, (payload, context) -> {
			if (context.client().level != null) {
				READY_AT.put(payload.shipId(), context.client().level.getGameTime() + payload.ticks());
			}
		});
		ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> READY_AT.clear());
		HudElementRegistry.attachElementAfter(VanillaHudElements.CROSSHAIR, OnePieceMod.id("ship_guns"), new ShipCombatHud());

		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			// Only while aboard a ship, so these keys stay free for other things on land. The server checks the rest.
			ShipEntity ship = client.player == null ? null : ShipEntity.aboard(client.player);
			while (FIRE_CANNONS.consumeClick()) {
				if (ship != null) {
					ClientPlayNetworking.send(new FireCannonsPayload());
				}
			}
			while (COUP_DE_BURST.consumeClick()) {
				if (ship != null) {
					ClientPlayNetworking.send(new ShipSpecialPayload(false));
				}
			}
			while (GAON_CANNON.consumeClick()) {
				if (ship != null) {
					ClientPlayNetworking.send(new ShipSpecialPayload(true));
				}
			}
			if (ship != null && client.gui.screen() == null && client.player.tickCount % 2 == 0) {
				showAim(client, ship);
			}
		});
	}

	/** Ticks until this ship's cannons are ready (0 = ready now). */
	static long reloadLeft(Minecraft client, ShipEntity ship) {
		Long ready = READY_AT.get(ship.getId());
		return ready == null || client.level == null ? 0 : Math.max(0, ready - client.level.getGameTime());
	}

	/**
	 * Flies an imaginary cannonball from the guns facing where you look, with the same speed, gravity and drag as a real
	 * one, and marks where it comes down: on the sea, on land, or on another ship.
	 */
	private static void showAim(Minecraft client, ShipEntity ship) {
		Vec3 look = client.player.getViewVector(1.0f);
		List<Cannons.Gun> guns = Cannons.gunsFacing(ship, look);
		if (guns.isEmpty()) {
			return;
		}
		Vec3 start = Vec3.ZERO;
		for (Cannons.Gun gun : guns) {
			start = start.add(gun.muzzle());
		}
		Vec3 pos = start.scale(1.0 / guns.size());
		Vec3 velocity = Cannons.aimFromLook(look).scale(Cannons.MUZZLE_SPEED);
		double sea = ship.getY() + ship.getLayout().waterline;
		List<ShipEntity> ships = client.level.getEntitiesOfClass(ShipEntity.class, ship.getBoundingBox().inflate(160, 32, 160), other -> other != ship);
		for (int tick = 0; tick < 200; tick++) {
			Vec3 next = pos.add(velocity);
			velocity = velocity.scale(Cannons.DRAG).subtract(0, Cannons.GRAVITY, 0);
			if (tick % 3 == 2) {
				client.level.addParticle(ARC, next.x, next.y, next.z, 0, 0, 0);
			}
			if (landed(client, ships, next, sea)) {
				for (int i = 0; i < 10; i++) {
					double angle = Math.PI * 2 * i / 10;
					client.level.addParticle(LANDING, next.x + Math.cos(angle) * 1.4, Math.max(next.y, sea) + 0.2, next.z + Math.sin(angle) * 1.4, 0, 0, 0);
				}
				return;
			}
			pos = next;
		}
	}

	private static boolean landed(Minecraft client, List<ShipEntity> ships, Vec3 at, double sea) {
		if (at.y <= sea) {
			return true;
		}
		BlockPos cell = BlockPos.containing(at);
		BlockState state = client.level.getBlockState(cell);
		if (!state.canBeReplaced() && !state.getCollisionShape(client.level, cell).isEmpty()) {
			return true;
		}
		for (ShipEntity other : ships) {
			if (other.blockAt(at)) {
				return true;
			}
		}
		return false;
	}
}
