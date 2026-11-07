package com.onepiecemod.shipcombat;

import java.util.HashMap;
import java.util.Map;

import org.jetbrains.annotations.Nullable;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipLayout;

/**
 * Lets add-on mods (like One Piece Arsenal) bring their own cannons and cannon ammo.
 *
 *  - Cannons: put the block in the onepiece:cannons block tag and give it a horizontal FACING property, and it fires
 *    like the plain Cannon, on ships (the M key) and on land (right-click it with ammo). registerCannon() says how
 *    that block shoots. Its block entity, if it has one, is passed in: ships keep it while they sail.
 *  - Ammo: registerShell() makes an item cannon ammo. Hold it when you fire. The cannonball carries the whole
 *    stack (so data on it, like a material, comes along), is drawn as it, and the shell decides its hull damage
 *    and what else happens when it hits.
 */
public final class CannonAddons {
	/** Blocks Cannons fires. The plain Cannon is in it. */
	public static final TagKey<Block> CANNONS = TagKey.create(Registries.BLOCK, OnePieceMod.id("cannons"));

	/**
	 * How one cannon shoots, as multipliers of the plain Cannon (1 = the same).
	 * damage: cannonball damage. speed: muzzle speed, so range. reload: reload time (lower is faster). spread: aim wobble.
	 */
	public record Profile(float damage, float speed, float reload, float spread) {
		public static final Profile PLAIN = new Profile(1f, 1f, 1f, 1f);
	}

	/** Works out a cannon block's Profile. blockEntity is null for blocks without one. Only called on the server. */
	@FunctionalInterface
	public interface CannonType {
		Profile profile(ServerLevel level, BlockState state, @Nullable BlockEntity blockEntity);
	}

	/** Cannon ammo from an add-on. Everything happens on the server. */
	public interface Shell {
		/** Share of a normal cannonball's hull damage (1 = the same). */
		float hullDamage(ItemStack shell);

		/** After it hit a ship and did its hull damage. at is where it struck her planks. */
		default void onHitShip(ServerLevel level, CannonballEntity ball, ShipEntity ship, Vec3 at) {
		}

		/** After it hit something that isn't a ship (and hurt it). */
		default void onHitEntity(ServerLevel level, CannonballEntity ball, Entity target) {
		}

		/** When it bursts, wherever that is (not when it splashes into the sea). */
		default void onBurst(ServerLevel level, CannonballEntity ball, Vec3 at) {
		}
	}

	private static final Map<Block, CannonType> CANNON_TYPES = new HashMap<>();
	private static final Map<Item, Shell> SHELLS = new HashMap<>();

	private CannonAddons() {
	}

	/** Call once while the game loads, on both sides. The block must also be in the onepiece:cannons tag. */
	public static void registerCannon(Block block, CannonType type) {
		CANNON_TYPES.put(block, type);
	}

	/** Call once while the game loads, on both sides (the ship HUD shows held shells too). */
	public static void registerShell(Item item, Shell shell) {
		SHELLS.put(item, shell);
	}

	/** A block Cannons can fire. */
	public static boolean isCannon(BlockState state) {
		return state.is(CANNONS) && state.hasProperty(HorizontalDirectionalBlock.FACING);
	}

	@Nullable
	public static Shell shell(ItemStack stack) {
		return stack.isEmpty() ? null : SHELLS.get(stack.getItem());
	}

	/** Anything a cannon can fire: cannonballs, the special shot in ShipAmmo, or an add-on's shell. */
	public static boolean isAmmo(ItemStack stack) {
		return ShipAmmo.of(stack) != null || shell(stack) != null;
	}

	/** How a cannon placed in the world shoots. */
	public static Profile profile(ServerLevel level, BlockState state, BlockPos pos) {
		CannonType type = CANNON_TYPES.get(state.getBlock());
		return type == null ? Profile.PLAIN : type.profile(level, state, level.getBlockEntity(pos));
	}

	/** How a cannon aboard a ship shoots. Its block entity is rebuilt from what the ship saved. */
	public static Profile profile(ServerLevel level, ShipLayout.ShipBlock block) {
		CannonType type = CANNON_TYPES.get(block.state().getBlock());
		if (type == null) {
			return Profile.PLAIN;
		}
		BlockEntity saved = block.nbt().map(nbt -> BlockEntity.loadStatic(BlockPos.ZERO, block.state(), nbt, level.registryAccess())).orElse(null);
		return type.profile(level, block.state(), saved);
	}
}
