package com.onepiecemod.shipcombat;

import java.util.Optional;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.multiplayer.SharedShips;
import com.onepiecemod.ship.ShipEntity;

/**
 * A grappling hook on a rope. Aim at a ship up to 24 blocks away and right-click to swing across:
 * onto an enemy ship to board it, or onto your own crew's ship to climb aboard.
 */
public class BoardingHookItem extends Item {
	private static final double RANGE = 24;
	/** How many ticks behind the server a player's screen may show a moving ship. */
	private static final double LAG_TICKS = 6;

	public BoardingHookItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (!(level instanceof ServerLevel serverLevel) || !(player instanceof ServerPlayer serverPlayer)) {
			return InteractionResult.SUCCESS;
		}
		ShipEntity target = shipInSight(serverLevel, player);
		if (target == null) {
			player.sendOverlayMessage(Component.literal("Aim the hook at a ship within " + (int) RANGE + " blocks.").withStyle(ChatFormatting.GRAY));
			return InteractionResult.FAIL;
		}

		// Draw the rope flying out.
		Vec3 eye = player.getEyePosition();
		Vec3 to = target.position().add(0, target.getLayout().waterline + 1.5, 0);
		for (double t = 0; t <= 1; t += 0.05) {
			Vec3 p = eye.lerp(to, t);
			serverLevel.sendParticles(ParticleTypes.CRIT, p.x, p.y, p.z, 1, 0, 0, 0, 0);
		}
		serverLevel.playSound(null, player.blockPosition(), com.onepiecemod.sound.WorldSounds.GRAPPLE, SoundSource.PLAYERS, 1.0f, 1.0f);

		InteractionResult result;
		if (ShipBrain.isAi(target)) {
			result = Boarding.board(serverPlayer, target);
		} else {
			UUID owner = target.getAttached(SharedShips.OWNER);
			if (owner != null && !SharedShips.isCrew(serverLevel.getServer(), owner, serverPlayer)) {
				// In a sea battle with her crew the hook works like boarding by hand: below half hull, you swing across.
				if (com.onepiecemod.multiplayer.SeaWars.tryBoard(target, serverPlayer, owner, RANGE)) {
					boolean boarded = ShipEntity.aboard(player) == target;
					if (boarded) {
						ItemStack stack = player.getItemInHand(hand);
						stack.hurtAndBreak(1, player, hand);
						player.getCooldowns().addCooldown(stack, 40);
					}
					return boarded ? InteractionResult.SUCCESS : InteractionResult.FAIL;
				}
				player.sendOverlayMessage(Component.literal("That ship belongs to another crew.").withStyle(ChatFormatting.RED));
				return InteractionResult.FAIL;
			}
			target.boardOnDeck(player);
			player.sendOverlayMessage(Component.literal("Welcome aboard!"));
			result = InteractionResult.SUCCESS;
		}

		if (result == InteractionResult.SUCCESS) {
			ItemStack stack = player.getItemInHand(hand);
			stack.hurtAndBreak(1, player, hand);
			player.getCooldowns().addCooldown(stack, 40);
		}
		return result;
	}

	/** The nearest ship the player is looking at, within range (not the one they are standing on). */
	private static ShipEntity shipInSight(ServerLevel level, Player player) {
		Vec3 eye = player.getEyePosition();
		Vec3 end = eye.add(player.getViewVector(1.0f).scale(RANGE));
		ShipEntity best = null;
		double bestDistance = Double.MAX_VALUE;
		for (ShipEntity ship : level.getEntitiesOfClass(ShipEntity.class, player.getBoundingBox().inflate(RANGE + 16))) {
			if (ship == ShipEntity.aboard(player) || ship.sinking) {
				continue;
			}
			// A sailing ship is drawn a few ticks behind where the server has it (the network takes time),
			// so also count a hit on where it was a moment ago: you aim at what you see.
			Vec3 moved = ship.position().subtract(ship.xo, ship.yo, ship.zo).scale(LAG_TICKS);
			AABB box = ship.getBoundingBox().inflate(1.0);
			box = box.minmax(box.move(moved.reverse()));
			Optional<Vec3> hit = box.contains(eye) ? Optional.of(eye) : box.clip(eye, end);
			if (hit.isPresent() && hit.get().distanceToSqr(eye) < bestDistance) {
				bestDistance = hit.get().distanceToSqr(eye);
				best = ship;
			}
		}
		return best;
	}
}
