package com.onepiecemod.shipcombat;

import java.util.Map;
import java.util.WeakHashMap;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.ship.ShipEntity;

/**
 * Ramming: sail into another ship fast enough and both hulls take damage. The one being rammed takes the most,
 * and a bigger, faster ship hits harder. Ships can't sail through each other (ShipEntity.sail), so the hit lands
 * the moment the bows meet.
 */
public class Ramming {
	/** Slower than this (blocks per tick) is just bumping alongside. Full sail is about 0.3 to 0.55. */
	private static final double MIN_SPEED = 0.18;
	/** Damage to the rammed ship at full speed (0.55 blocks a tick) from a 500-block ship. */
	private static final float FULL_DAMAGE = 60f;
	/** The rammer takes this share of the damage. */
	private static final float RECOIL = 0.3f;
	private static final int COOLDOWN_TICKS = 40;

	private static final Map<ShipEntity, Long> NEXT_RAM = new WeakHashMap<>();
	/** Where each ship was last tick. (xo/zo don't work here: a player-steered ship is moved by packets, not its tick.) */
	private static final Map<ShipEntity, Vec3> LAST_POS = new WeakHashMap<>();

	static void tick(ShipEntity ship, ServerLevel level) {
		Vec3 last = LAST_POS.put(ship, ship.position());
		if (last == null) {
			return;
		}
		Vec3 moved = ship.position().subtract(last).multiply(1, 0, 1);
		double speed = moved.length();
		long now = level.getGameTime();
		if (speed < MIN_SPEED || now < NEXT_RAM.getOrDefault(ship, 0L)) {
			return;
		}
		// Look a couple of ticks ahead: the ship stops right before the other hull, so it never actually overlaps.
		ShipEntity target = ship.shipTouching(moved.normalize().scale(Math.max(1.0, speed * 3)));
		if (target == null || ShipBrain.sameSide(ship, target)) {
			return;
		}
		NEXT_RAM.put(ship, now + COOLDOWN_TICKS);
		NEXT_RAM.put(target, now + COOLDOWN_TICKS / 2);

		float weight = (float) Math.sqrt(Math.max(50, ship.getLayout().size()) / 500.0);
		float damage = FULL_DAMAGE * (float) Math.min(1.0, speed / 0.55) * Math.min(2.0f, weight);
		ServerPlayer captain = ship.getControllingPassenger() instanceof ServerPlayer player ? player : null;
		Vec3 contact = ship.position().add(target.position()).scale(0.5).add(0, ship.getLayout().waterline, 0);

		ShipHull.damage(target, damage, captain, contact, ship);
		ShipHull.damage(ship, damage * RECOIL, null, contact, target);
		level.sendParticles(ParticleTypes.EXPLOSION, contact.x, contact.y + 1, contact.z, 3, 1.0, 0.5, 1.0, 0);
		level.playSound(null, BlockPos.containing(contact), SoundEvents.ZOMBIE_ATTACK_WOODEN_DOOR, SoundSource.NEUTRAL, 3.0f, 0.6f);
		if (captain != null) {
			captain.sendOverlayMessage(Component.literal("RAMMED the " + target.getName().getString() + "! (" + Math.round(damage) + " hull damage)")
					.withStyle(ChatFormatting.GOLD));
		}
	}
}
