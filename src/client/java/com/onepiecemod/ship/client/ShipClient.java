package com.onepiecemod.ship.client;

import java.util.HashMap;
import java.util.Map;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderers;
import net.minecraft.client.renderer.entity.EntityRenderers;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientEntityEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.ship.FlagDesign;
import com.onepiecemod.ship.JollyRogerItem;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipFeature;
import com.onepiecemod.ship.ShipLayout;
import com.onepiecemod.ship.ShipPayloads;

/**
 * Client-only setup for ships and Jolly Rogers. OnePieceModClient calls initialize().
 */
public class ShipClient {
	// Ship blocks that arrived a moment before the ship itself did. Used up as soon as the ship appears.
	private static final Map<Integer, ShipLayout> WAITING = new HashMap<>();

	public static void initialize() {
		EntityRenderers.register(ShipFeature.SHIP, ShipRenderer::new);
		BlockEntityRenderers.register(ShipFeature.FLAG_BLOCK_ENTITY, FlagRenderer::new);

		ClientPlayNetworking.registerGlobalReceiver(ShipPayloads.ShipBlocks.TYPE, (payload, context) -> {
			Entity entity = context.client().level == null ? null : context.client().level.getEntity(payload.entityId());
			if (entity instanceof ShipEntity ship) {
				ship.setLayout(payload.layout());
			} else {
				WAITING.put(payload.entityId(), payload.layout());
			}
		});
		ClientEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			ShipLayout layout = WAITING.remove(entity.getId());
			if (layout != null && entity instanceof ShipEntity ship) {
				ship.setLayout(layout);
			}
		});

		// Walking on deck: the ship carries you along (ShipDecks). Players' own games move them, so this runs here.
		net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents.END_CLIENT_TICK.register(client -> {
			if (client.player != null && client.level != null && !client.isPaused()) {
				com.onepiecemod.ship.ShipDecks.carryOnClient(client.player);
			}
		});

		JollyRogerItem.openDesigner = hand -> {
			Minecraft minecraft = Minecraft.getInstance();
			ItemStack stack = minecraft.player.getItemInHand(hand);
			FlagDesign design = stack.getOrDefault(ShipFeature.FLAG_DESIGN, FlagDesign.blank());
			minecraft.gui.setScreen(new JollyRogerScreen(hand, design));
		};
	}
}
