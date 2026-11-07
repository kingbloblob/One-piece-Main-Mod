package com.onepiecemod.weapon;

import java.util.function.Supplier;

import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/**
 * Every kind of ammo, and which family of weapon fires it.
 * What each one does when it hits is in Shot.java.
 */
public enum Ammo {
	/** Plain lead bullets for pistols and rifles. */
	BULLET(Kind.BULLET, () -> WeaponItems.BULLET),
	/** Marine bullets with a Seastone core: they weaken Devil Fruit users. */
	SEASTONE_BULLET(Kind.BULLET, () -> WeaponItems.SEASTONE_BULLET),
	/** For the Hand Cannon. Explodes, but never breaks blocks. */
	CANNONBALL(Kind.CANNONBALL, () -> WeaponItems.CANNONBALL),
	/** Usopp's basic slingshot ammo. */
	LEAD_STAR(Kind.STAR, () -> WeaponItems.LEAD_STAR),
	/** A small blast where it lands. */
	EXPLODING_STAR(Kind.STAR, () -> WeaponItems.EXPLODING_STAR),
	/** Hot sauce in the eyes: blinds and dizzies. */
	TABASCO_STAR(Kind.STAR, () -> WeaponItems.TABASCO_STAR),
	/** A seed that sprouts a thorny trap where it lands. */
	POP_GREEN(Kind.STAR, () -> WeaponItems.POP_GREEN);

	/** Which weapons can fire it. */
	public enum Kind { BULLET, CANNONBALL, STAR }

	private final Kind kind;
	private final Supplier<Item> item;

	Ammo(Kind kind, Supplier<Item> item) {
		this.kind = kind;
		this.item = item;
	}

	public Kind kind() {
		return kind;
	}

	public Item item() {
		return item.get();
	}

	/** The ammo this stack is, or null if it isn't ammo. */
	public static Ammo of(ItemStack stack) {
		for (Ammo ammo : values()) {
			if (!stack.isEmpty() && stack.is(ammo.item())) {
				return ammo;
			}
		}
		return null;
	}
}
