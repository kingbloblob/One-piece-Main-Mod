package com.onepiecemod.weapon;

import java.util.HashMap;
import java.util.Map;

import org.jetbrains.annotations.Nullable;

import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/**
 * Lets add-on mods (like One Piece Arsenal) bring their own gun and slingshot ammo.
 *
 * registerRound() makes an item ammo for one family of weapon (bullets, cannonballs or stars). It fires like
 * its base ammo (sound, muzzle flash, and for a cannonball the blast), and the Round decides what else happens:
 * extra damage, a different trail, and effects when it hits. The fired stack (one round, with all its data,
 * like a material) is passed in, so one item can be many kinds of ammo.
 */
public final class GunAddons {
	/** Ammo from an add-on. Everything happens on the server. */
	public interface Round {
		/** Extra damage on top of the gun's, before the headshot bonus. */
		default float bonusDamage(ServerPlayer shooter, ServerLevel level, LivingEntity target, ItemStack round) {
			return 0.0f;
		}

		/** After it hurt the creature it hit. */
		default void onHit(ServerPlayer shooter, ServerLevel level, LivingEntity target, ItemStack round, ItemStack gun) {
		}

		/** Where the shot stopped, whether it hit a creature (target) or not (null). Called after onHit. */
		default void onLand(ServerPlayer shooter, ServerLevel level, Vec3 at, @Nullable LivingEntity target, ItemStack round) {
		}

		/** The particles along the shot's path, or null for its base ammo's. */
		default @Nullable ParticleOptions trail(ItemStack round) {
			return null;
		}
	}

	private record Entry(Ammo base, Round round) {}

	private static final Map<Item, Entry> ROUNDS = new HashMap<>();

	private GunAddons() {
	}

	/**
	 * Call once while the game loads, on both sides. base is the main mod ammo it fires like, and decides which
	 * weapons take it (Ammo.BULLET: pistols and rifles; Ammo.CANNONBALL: the Hand Cannon; Ammo.LEAD_STAR: slingshots).
	 */
	public static void registerRound(Item item, Ammo base, Round round) {
		ROUNDS.put(item, new Entry(base, round));
	}

	/** The main mod ammo an add-on round fires like, or null if it isn't one. */
	public static @Nullable Ammo base(ItemStack stack) {
		Entry entry = stack.isEmpty() ? null : ROUNDS.get(stack.getItem());
		return entry == null ? null : entry.base();
	}

	/** The add-on round for this stack, or null if it isn't one. */
	public static @Nullable Round round(ItemStack stack) {
		Entry entry = stack.isEmpty() ? null : ROUNDS.get(stack.getItem());
		return entry == null ? null : entry.round();
	}

	/** The ammo this stack fires as: the main mod's own, or an add-on round's base. Null if it isn't ammo. */
	public static @Nullable Ammo firesAs(ItemStack stack) {
		Ammo ammo = Ammo.of(stack);
		return ammo != null ? ammo : base(stack);
	}
}
