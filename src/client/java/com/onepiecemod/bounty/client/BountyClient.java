package com.onepiecemod.bounty.client;

import net.minecraft.client.renderer.entity.EntityRenderers;

import com.onepiecemod.bounty.BountyFeature;
import com.onepiecemod.npc.client.NpcRenderer;

/**
 * Client-only setup for bounties. OnePieceModClient calls initialize().
 */
public class BountyClient {
	public static void initialize() {
		EntityRenderers.register(BountyFeature.MARINE, NpcRenderer::new); // Shared pirate/Marine renderer (npc package).
		EntityRenderers.register(BountyFeature.BOUNTY_HUNTER, BountyHunterRenderer::new);
		BountyBadge.initialize(); // The wanted poster in the inventory (ryan asked 2026-10-29).
	}
}
