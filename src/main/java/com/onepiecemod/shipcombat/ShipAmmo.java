package com.onepiecemod.shipcombat;

import org.jetbrains.annotations.Nullable;

import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/**
 * What a cannon can fire. Plain cannonballs do full hull damage; the others trade some of it for an extra effect
 * (see CannonballEntity.onHitEntity). Hold special ammo in your hand when you fire to load it.
 */
public enum ShipAmmo {
	CANNONBALL("Cannonballs", 1.0f),
	/** Tangles the enemy's rigging: she sails at half speed and turns slowly for a while. */
	CHAIN_SHOT("Chain Shot", 0.5f),
	/** Sets the enemy ship burning: hull damage over time, and her crew catches fire. */
	FIRE_SHOT("Fire Shot", 0.6f),
	/** Shreds people on deck (and boarding crews) but barely scratches the hull. */
	GRAPESHOT("Grapeshot", 0.35f);

	public final String title;
	/** Share of a normal cannonball's hull damage. */
	public final float hullDamage;

	ShipAmmo(String title, float hullDamage) {
		this.title = title;
		this.hullDamage = hullDamage;
	}

	public Item item() {
		return switch (this) {
			case CANNONBALL -> ShipCombatFeature.CANNONBALL;
			case CHAIN_SHOT -> ShipCombatFeature.CHAIN_SHOT;
			case FIRE_SHOT -> ShipCombatFeature.FIRE_SHOT;
			case GRAPESHOT -> ShipCombatFeature.GRAPESHOT;
		};
	}

	/** The ammo this item is, or null if it isn't cannon ammo. */
	@Nullable
	public static ShipAmmo of(ItemStack stack) {
		for (ShipAmmo ammo : values()) {
			if (!stack.isEmpty() && stack.is(ammo.item())) {
				return ammo;
			}
		}
		return null;
	}

	/** Special ammo in either hand, or plain cannonballs. */
	public static ShipAmmo held(ItemStack mainHand, ItemStack offHand) {
		ShipAmmo main = of(mainHand);
		if (main != null) {
			return main;
		}
		ShipAmmo off = of(offHand);
		return off != null ? off : CANNONBALL;
	}
}
