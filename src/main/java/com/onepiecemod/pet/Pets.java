package com.onepiecemod.pet;

import java.util.List;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.OnePieceMod;

/**
 * Shared pet code: finding a pet's owner, calling it over, healing it, keeping its rider breathing,
 * and steering creatures that swim. Also registers the Pet Whistle.
 */
public final class Pets {
	/** Blow it to call every pet you have nearby. Sneak while blowing to make them all wait. */
	public static Item PET_WHISTLE;
	/** Right-click your tamed Sea King (or Momoo) with it to harness it to your ship. See PetTowing. */
	public static Item TOWING_HARNESS;

	private Pets() {
	}

	/** Called from Creatures.initialize(). */
	public static void initialize() {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id("pet_whistle"));
		PET_WHISTLE = Registry.register(BuiltInRegistries.ITEM, key,
				new PetWhistleItem(new Item.Properties().setId(key).stacksTo(1).rarity(Rarity.UNCOMMON)));
		ResourceKey<Item> harnessKey = ResourceKey.create(Registries.ITEM, OnePieceMod.id("towing_harness"));
		TOWING_HARNESS = Registry.register(BuiltInRegistries.ITEM, harnessKey,
				new Item(new Item.Properties().setId(harnessKey).stacksTo(1).rarity(Rarity.UNCOMMON)) {
					@Override
					public void appendHoverText(net.minecraft.world.item.ItemStack stack, Item.TooltipContext context,
							net.minecraft.world.item.component.TooltipDisplay display, java.util.function.Consumer<Component> tooltip,
							net.minecraft.world.item.TooltipFlag flag) {
						tooltip.accept(Component.literal("Use on your tamed Sea King or Momoo near your ship:").withStyle(ChatFormatting.GRAY));
						tooltip.accept(Component.literal("it pulls the ship, even through the Calm Belt").withStyle(ChatFormatting.GRAY));
						tooltip.accept(Component.literal("Use again to unhitch").withStyle(ChatFormatting.GRAY));
					}
				});
		PetAbilities.initialize();
		PetTowing.initialize();
		PetsCommand.initialize();
	}

	public static LivingEntity ownerOf(Pet pet, Level level) {
		UUID id = pet.getOwnerId();
		return id == null ? null : level.getPlayerByUUID(id);
	}

	public static boolean isOwner(Pet pet, Entity entity) {
		return entity instanceof Player player && player.getUUID().equals(pet.getOwnerId());
	}

	/** Every living pet of this player within range (only loaded ones can hear the whistle). */
	public static List<Mob> petsOf(Player player, double range) {
		return new java.util.ArrayList<>(player.level().getEntitiesOfClass(Mob.class, player.getBoundingBox().inflate(range, 64.0, range),
				mob -> mob.isAlive() && mob instanceof Pet pet && player.getUUID().equals(pet.getOwnerId())));
	}

	/**
	 * Hops a pet over to its owner, like tamed wolves do. Swimmers only go to water deep enough for them.
	 * Returns false when there is nowhere safe to put it.
	 */
	public static boolean bringTo(Mob mob, LivingEntity owner) {
		Vec3 spot = ((Pet) mob).petSwims() ? waterNear(owner.level(), owner.blockPosition(), mob.getBbHeight())
				: owner.position();
		if (spot == null) {
			return false;
		}
		mob.teleportTo(spot.x, spot.y, spot.z);
		mob.getNavigation().stop();
		return true;
	}

	/** The nearest spot of water around pos that is at least two blocks deep, or null. */
	public static Vec3 waterNear(Level level, BlockPos pos, float height) {
		int depth = Math.max(2, Math.min(4, (int) Math.ceil(height))); // a Sea King's head sticks out of 4 deep water, that's fine
		for (int r = 0; r <= 6; r += 2) {
			for (int dx = -r; dx <= r; dx += 2) {
				for (int dz = -r; dz <= r; dz += 2) {
					if (Math.max(Math.abs(dx), Math.abs(dz)) != r) {
						continue; // only the ring at this distance
					}
					for (int dy = 1; dy >= -12; dy--) {
						BlockPos top = pos.offset(dx, dy, dz);
						if (deepWater(level, top, depth)) {
							return new Vec3(top.getX() + 0.5, top.getY() - depth + 1, top.getZ() + 0.5);
						}
					}
				}
			}
		}
		return null;
	}

	private static boolean deepWater(Level level, BlockPos top, int depth) {
		for (int i = 0; i < depth; i++) {
			if (!level.getFluidState(top.below(i)).is(FluidTags.WATER)) {
				return false;
			}
		}
		return true;
	}

	/**
	 * Every tick on the server, also while a player rides it (a ridden mob's own AI, and so tick() below, is
	 * switched off while its rider's game steers it). Called from the pet's tick().
	 */
	public static void serverTick(Mob mob, ServerLevel level) {
		Pet pet = (Pet) mob;
		if (pet.petSwims()) {
			// The creature keeps its rider supplied with air, so you can ride it under the sea.
			for (Entity rider : mob.getPassengers()) {
				if (rider.isUnderWater()) {
					rider.setAirSupply(rider.getMaxAirSupply());
				}
			}
		}
		if (pet.isTamed()) {
			PetAbilities.tick(mob, level);
			PetAbilities.tickRam(mob, level);
			PetTowing.tick(mob, level);
			if (mob.getControllingPassenger() instanceof Player && mob.tickCount % 600 == 0) {
				PetBond.add(mob, 1); // riding together
			}
			if (mob.tickCount % 1200 == 0) {
				PetTowing.cleanUp(level.getGameTime());
			}
		}
	}

	/** From the pet's AI step on the server: tamed pets slowly heal when nothing has hurt them for a while. */
	public static void tick(Mob mob, ServerLevel level) {
		Pet pet = (Pet) mob;
		if (!pet.isTamed() || mob.tickCount % 40 != 0) {
			return;
		}
		if (mob.getHealth() < mob.getMaxHealth() && mob.getTarget() == null
				&& mob.tickCount - mob.getLastHurtByMobTimestamp() > 200) {
			// A Pet Bed or a full Pet Bowl close by: it heals three times as fast.
			float rate = nearPetComfort(mob, level) ? 3.0f : 1.0f;
			mob.heal(Math.max(1.0f, mob.getMaxHealth() / 60.0f) * rate);
		}
	}

	/** True if a Pet Bed or Pet Bowl (furniture) is within 4 blocks of the pet. */
	public static boolean nearPetComfort(Mob mob, ServerLevel level) {
		net.minecraft.core.BlockPos at = mob.blockPosition();
		for (net.minecraft.core.BlockPos pos : net.minecraft.core.BlockPos.betweenClosed(at.offset(-4, -2, -4), at.offset(4, 2, 4))) {
			net.minecraft.world.level.block.state.BlockState state = level.getBlockState(pos);
			if (state.is(com.onepiecemod.furniture.FurnitureBlocks.PET_BED) || state.is(com.onepiecemod.furniture.FurnitureBlocks.PET_BOWL)) {
				return true;
			}
		}
		return false;
	}

	/**
	 * Steering a ridden swimmer up and down. Look down while moving forward to dive, look up to come back up.
	 * Otherwise it swims along the surface with its back out of the water, so the rider stays dry.
	 */
	public static void steerSwimming(Mob mob, Player rider) {
		if (!mob.isInWater()) {
			return;
		}
		Vec3 motion = mob.getDeltaMovement();
		double depth = mob.getFluidHeight(FluidTags.WATER);
		float pitch = rider.getXRot();
		boolean forward = rider.zza > 0.0f;
		double up;
		if (forward && pitch > 35.0f) {
			up = -0.12; // dive
		} else if (forward && pitch < -30.0f && depth > mob.getBbHeight() * 0.6) {
			up = 0.12; // climb back up
		} else if (depth > mob.getBbHeight() * 0.6) {
			up = 0.06; // drift back up to the surface
		} else if (depth < mob.getBbHeight() * 0.35) {
			up = -0.03; // settle into the water
		} else {
			up = 0.0;
		}
		mob.setDeltaMovement(motion.x, up, motion.z);
	}

	/** How fast a ridden swimmer moves: a tenth of its speed stat, like its own swimming AI uses. */
	public static float swimRiddenSpeed(double speedStat) {
		return (float) (speedStat * 0.09);
	}

	public static void tell(Player player, Component text, ChatFormatting color) {
		if (player instanceof ServerPlayer serverPlayer) {
			serverPlayer.sendSystemMessage(text.copy().withStyle(color));
		}
	}

	/** A tamed pet killed something: bond points (more for big prey). */
	public static void onKill(Mob mob, LivingEntity killed) {
		if (((Pet) mob).isTamed()) {
			PetBond.add(mob, killed.getMaxHealth() >= 100 ? 10 : 3);
		}
	}

	private static final java.util.Map<UUID, Long> LAST_FED = new java.util.HashMap<>();

	/** The owner fed a tamed pet its favourite food: one bond point, once a minute. */
	public static void onFed(Mob mob) {
		if (!((Pet) mob).isTamed()) {
			return;
		}
		long now = mob.level().getGameTime();
		Long last = LAST_FED.get(mob.getUUID());
		if (last == null || now - last >= 1200) {
			LAST_FED.put(mob.getUUID(), now);
			PetBond.add(mob, 1);
		}
	}

	/** Lets the owner know when a pet dies, and where. */
	public static void diedNotice(Mob mob) {
		LivingEntity owner = ownerOf((Pet) mob, mob.level());
		if (owner instanceof ServerPlayer player) {
			BlockPos pos = mob.blockPosition();
			player.sendSystemMessage(Component.empty().append(mob.getName())
					.append(" died at " + pos.getX() + ", " + pos.getY() + ", " + pos.getZ() + ".")
					.withStyle(ChatFormatting.RED));
		}
	}
}
