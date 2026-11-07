package com.onepiecemod.pet;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.event.player.UseEntityCallback;

import com.onepiecemod.ship.ShipEntity;

/**
 * Sea Kings (and Momoo) pulling your ship, like the two Sea Kings that pull Boa Hancock's ship across the Calm Belt.
 * Right-click your tamed Sea King with a Towing Harness while your ship is within 32 blocks: it swims ahead of the
 * ship and pulls. Do it again to unhitch. Up to two can pull one ship.
 * A towed ship is faster, and in the Calm Belt (no wind at all) it still crosses at a good speed.
 */
public final class PetTowing {
	private static final double HITCH_RANGE = 32.0;
	private static final int MAX_HAULERS = 2;

	/** Which ships were pulled this second, and by how many pets: ship UUID -> {haulers, game time}. */
	private static final Map<UUID, long[]> HAULERS = new HashMap<>();

	private PetTowing() {
	}

	public static boolean canTow(Pet pet) {
		return pet.petKind().equals("sea_king") || pet.petKind().equals("momoo");
	}

	/** Called from Pets.initialize(). */
	public static void initialize() {
		UseEntityCallback.EVENT.register((player, level, hand, entity, hitResult) -> {
			if (!player.getItemInHand(hand).is(Pets.TOWING_HARNESS) || !(entity instanceof Mob mob) || !(entity instanceof Pet pet)) {
				return InteractionResult.PASS;
			}
			if (level.isClientSide()) {
				return InteractionResult.SUCCESS;
			}
			if (!Pets.isOwner(pet, player)) {
				Pets.tell(player, Component.literal("Tame it first. Only its owner can harness it."), ChatFormatting.GRAY);
			} else if (!canTow(pet)) {
				Pets.tell(player, Component.empty().append(mob.getName()).append(" isn't strong enough to pull a ship. Try a Sea King or Momoo."),
						ChatFormatting.GRAY);
			} else if (pet.getTowShip() != null) {
				pet.setTowShip(null);
				Pets.tell(player, Component.empty().append(mob.getName()).append(" is unhitched and follows you again."), ChatFormatting.GREEN);
			} else {
				hitch(mob, pet, (ServerPlayer) player);
			}
			return InteractionResult.SUCCESS;
		});
		// Towed ships go faster (shipcombat.ShipCrewHelp multiplies this into the ship's speed).
		com.onepiecemod.shipcombat.ShipCrewHelp.towBonus = PetTowing::speedBonus;
	}

	private static void hitch(Mob mob, Pet pet, ServerPlayer player) {
		ShipEntity ship = ShipEntity.aboard(player);
		if (ship == null) {
			ShipEntity nearest = null;
			for (ShipEntity candidate : player.level().getEntitiesOfClass(ShipEntity.class, player.getBoundingBox().inflate(HITCH_RANGE))) {
				if (nearest == null || candidate.distanceToSqr(player) < nearest.distanceToSqr(player)) {
					nearest = candidate;
				}
			}
			ship = nearest;
		}
		if (ship == null || ship.sinking) {
			Pets.tell(player, Component.literal("No ship within 32 blocks to pull. Stand on your ship (or next to it) and try again."),
					ChatFormatting.GRAY);
			return;
		}
		int already = 0;
		for (Mob other : Pets.petsOf(player, 96)) {
			if (other != mob && ship.getUUID().equals(((Pet) other).getTowShip())) {
				already++;
			}
		}
		if (already >= MAX_HAULERS) {
			Pets.tell(player, Component.literal("Two are already pulling that ship. That's as many as fit in the harness."), ChatFormatting.GRAY);
			return;
		}
		pet.setTowShip(ship.getUUID());
		pet.setStaying(false);
		Pets.tell(player, Component.empty().append(mob.getName())
				.append(" is harnessed to your ship! Take the helm: it pulls you along, even through the Calm Belt."), ChatFormatting.GOLD);
		com.onepiecemod.advancement.AdvancementFeature.grant(player, "wonders/sea_king_tow");
	}

	/** Every tick on the server for a harnessed pet: swim to the spot ahead of the ship's bow. */
	public static void tick(Mob mob, ServerLevel level) {
		Pet pet = (Pet) mob;
		UUID shipId = pet.getTowShip();
		if (shipId == null || mob.isVehicle()) {
			return;
		}
		Entity entity = level.getEntity(shipId);
		if (entity == null) {
			return; // the ship is in an unloaded chunk; wait for it
		}
		if (!(entity instanceof ShipEntity ship) || ship.isRemoved() || ship.sinking) {
			pet.setTowShip(null);
			return;
		}
		float yaw = ship.getYRot() * Mth.DEG_TO_RAD;
		Vec3 heading = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
		Vec3 side = new Vec3(heading.z, 0, -heading.x);
		// Two haulers swim side by side, like Yuda and Kyuda.
		int slot = slotOf(mob, pet, level, shipId);
		double ahead = ship.getBbWidth() * 0.5 + 3.0 + mob.getBbWidth();
		double sideways = slot == 0 ? 0.0 : slot == 1 ? -mob.getBbWidth() * 0.8 : mob.getBbWidth() * 0.8;
		if (count(shipId, level) > 1) {
			sideways = slot == 0 ? -mob.getBbWidth() * 0.8 : mob.getBbWidth() * 0.8;
		}
		double waterY = ship.getY() + ship.getLayout().waterline - mob.getBbHeight() * 0.5;
		Vec3 target = ship.position().add(heading.scale(ahead)).add(side.scale(sideways));
		target = new Vec3(target.x, waterY, target.z);

		mob.getNavigation().stop();
		Vec3 offset = target.subtract(mob.position());
		if (offset.lengthSqr() > 40 * 40) {
			if (level.getFluidState(net.minecraft.core.BlockPos.containing(target)).is(FluidTags.WATER)) {
				mob.teleportTo(target.x, target.y, target.z);
			}
		} else {
			Vec3 pull = offset.scale(0.25);
			if (pull.length() > 1.2) {
				pull = pull.normalize().scale(1.2);
			}
			mob.setDeltaMovement(pull);
		}
		mob.setYRot(ship.getYRot());
		mob.setYBodyRot(ship.getYRot());
		mob.setYHeadRot(ship.getYRot());
		long[] entry = HAULERS.computeIfAbsent(shipId, id -> new long[] {0, 0, 0});
		if (entry[1] != level.getGameTime()) {
			entry[2] = level.getGameTime() - entry[1] == 1 ? entry[0] : 0; // last tick's full count
			entry[0] = 0;
			entry[1] = level.getGameTime();
		}
		entry[0]++;
		if (mob.tickCount % 600 == 0 && ship.getDeltaMovement().horizontalDistance() > 0.1) {
			PetBond.add(mob, 1); // pulling the ship together counts as time spent together
		}
	}

	private static int slotOf(Mob mob, Pet pet, ServerLevel level, UUID shipId) {
		int slot = 0;
		for (Mob other : level.getEntitiesOfClass(Mob.class, mob.getBoundingBox().inflate(48),
				m -> m instanceof Pet p && shipId.equals(p.getTowShip()))) {
			if (other != mob && other.getId() < mob.getId()) {
				slot++;
			}
		}
		return slot;
	}

	private static int count(UUID shipId, ServerLevel level) {
		long[] entry = HAULERS.get(shipId);
		return entry == null || level.getGameTime() - entry[1] > 2 ? 0 : (int) Math.max(entry[0], entry[2]);
	}

	/** How much faster a harnessed ship goes (1 = no harness). Much more in still air, where sails do nothing. */
	public static float speedBonus(ShipEntity ship) {
		if (!(ship.level() instanceof ServerLevel level)) {
			return 1f;
		}
		long[] entry = HAULERS.get(ship.getUUID());
		if (entry == null || level.getGameTime() - entry[1] > 40) {
			return 1f;
		}
		int haulers = (int) Math.min(MAX_HAULERS, Math.max(1, Math.max(entry[0], entry[2])));
		double wind = ShipEntity.windAt.apply(level, ship.blockPosition());
		// Calm: sails give only the base crawl, so the Sea Kings do the work (about 2.2x / 3.4x).
		// Normal wind: a smaller boost on top of the sails (+15% each).
		double calm = 1.0 - Math.min(1.0, Math.max(0.0, wind));
		return (float) (1.0 + haulers * (0.15 + 1.05 * calm));
	}

	/** Forget ships nobody has pulled for a while (called once a minute). */
	static void cleanUp(long now) {
		HAULERS.values().removeIf(entry -> now - entry[1] > 1200);
	}
}
