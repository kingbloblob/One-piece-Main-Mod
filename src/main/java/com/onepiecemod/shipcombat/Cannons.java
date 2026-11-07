package com.onepiecemod.shipcombat;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.WeakHashMap;

import org.jetbrains.annotations.Nullable;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.multiplayer.SharedShips;
import com.onepiecemod.ship.DecorBlock;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipLayout;
import com.onepiecemod.ship.ShipUpgrades;
import com.onepiecemod.sound.ModSounds;

/**
 * Firing cannons.
 *  - Aboard a ship: press M (Options > Controls to change it). Every Cannon block on the side you are looking at fires
 *    where you look, one cannonball each from your inventory. Then the crew needs a moment to reload.
 *  - Hold special ammo (Chain Shot, Fire Shot, Grapeshot) when you press M to fire that instead (ShipAmmo).
 *  - On land: right-click a Cannon block holding a cannonball. It fires the way the cannon faces; look up to shoot further.
 *  - Other mods can add cannon blocks and ammo of their own (see CannonAddons): any block in the onepiece:cannons tag
 *    fires, each with its own damage, range, reload and aim, and their shells load like special ammo.
 *  - Marine and pirate ships fire theirs through ShipBrain, which aims for them.
 */
public class Cannons {
	/** How fast a cannonball leaves the barrel, in blocks per tick. */
	public static final double MUZZLE_SPEED = 2.0;
	/** The Cannon model's barrel reaches about 1.5 blocks out from the block's centre; shots start just past it. */
	public static final double MUZZLE_REACH = 1.6;
	/** Cannonballs fall like snowballs: this much speed lost to gravity per tick, and 1% to the air. */
	public static final double GRAVITY = 0.03;
	public static final double DRAG = 0.99;

	private static final int SHIP_RELOAD_TICKS = 50;
	private static final int LAND_RELOAD_TICKS = 30;
	/** How far off your view a cannon may point and still fire (in degrees, each way). */
	private static final double FIRING_ARC = 65;

	private static final Map<ShipEntity, Long> SHIP_READY = new WeakHashMap<>();
	private static final Map<BlockPos, Long> LAND_READY = new HashMap<>();

	/** A cannon on a ship right now: where its muzzle is and which way it points, in the world, and the block it is. */
	public record Gun(Vec3 muzzle, Vec3 facing, ShipLayout.ShipBlock block) {
		/** How this cannon shoots (see CannonAddons). Server only. */
		public CannonAddons.Profile profile(ServerLevel level) {
			return CannonAddons.profile(level, block);
		}
	}

	/**
	 * What a player's cannons will load: special ammo or an add-on shell in either hand (main hand first), else
	 * plain cannonballs. shell is the held shell stack, or empty. count is how many they carry.
	 */
	public record Loaded(ShipAmmo ammo, ItemStack shell, String title, int count) {
		public boolean matches(ItemStack stack) {
			return shell.isEmpty() ? stack.is(ammo.item()) : ItemStack.isSameItemSameComponents(stack, shell);
		}
	}

	public static Loaded loaded(Player player) {
		Inventory inventory = player.getInventory();
		for (ItemStack hand : List.of(player.getMainHandItem(), player.getOffhandItem())) {
			ShipAmmo special = ShipAmmo.of(hand);
			if (special != null) {
				return new Loaded(special, ItemStack.EMPTY, special.title, countAmmo(inventory, special.item()));
			}
			if (CannonAddons.shell(hand) != null) {
				ItemStack shell = hand.copyWithCount(1);
				int count = 0;
				for (int slot = 0; slot < inventory.getContainerSize(); slot++) {
					if (ItemStack.isSameItemSameComponents(inventory.getItem(slot), shell)) {
						count += inventory.getItem(slot).getCount();
					}
				}
				return new Loaded(ShipAmmo.CANNONBALL, shell, shell.getHoverName().getString(), count);
			}
		}
		return new Loaded(ShipAmmo.CANNONBALL, ItemStack.EMPTY, ShipAmmo.CANNONBALL.title, countAmmo(inventory, ShipAmmo.CANNONBALL.item()));
	}

	public static List<Gun> guns(ShipEntity ship) {
		List<Gun> guns = new ArrayList<>();
		for (ShipLayout.ShipBlock block : ship.getLayout().blocks) {
			BlockState state = block.state();
			if (!CannonAddons.isCannon(state)) {
				continue;
			}
			Direction face = state.getValue(DecorBlock.FACING);
			Vec3 facing = ship.rotate(new Vec3(face.getStepX(), 0, face.getStepZ()), 1.0f).normalize();
			Vec3 centre = ship.position().add(ship.rotate(new Vec3(block.pos().getX(), block.pos().getY() + 0.6, block.pos().getZ()), 1.0f));
			guns.add(new Gun(centre.add(facing.scale(MUZZLE_REACH)), facing, block)); // Just past the muzzle.
		}
		return guns;
	}

	/** The guns that point within FIRING_ARC of a direction (only the sideways part of it counts). */
	public static List<Gun> gunsFacing(ShipEntity ship, Vec3 direction) {
		Vec3 flat = new Vec3(direction.x, 0, direction.z);
		if (flat.lengthSqr() < 1.0e-4) {
			return List.of();
		}
		flat = flat.normalize();
		double minDot = Math.cos(Math.toRadians(FIRING_ARC));
		List<Gun> result = new ArrayList<>();
		for (Gun gun : guns(ship)) {
			if (gun.facing().dot(flat) >= minDot) {
				result.add(gun);
			}
		}
		return result;
	}

	// ---- Players ----

	/** The M key: fire a broadside from the ship you're aboard. */
	public static void fireFromKey(ServerPlayer player) {
		ShipEntity ship = ShipEntity.aboard(player);
		if (ship == null || ship.sinking) {
			player.sendOverlayMessage(Component.literal("Board a ship with Cannon blocks to fire them.").withStyle(ChatFormatting.GRAY));
			return;
		}
		UUID owner = ship.getAttached(SharedShips.OWNER);
		if (owner != null && !SharedShips.isCrew(player.level().getServer(), owner, player)) {
			player.sendOverlayMessage(Component.literal("Only the ship's own crew can fire her cannons.").withStyle(ChatFormatting.YELLOW));
			return;
		}
		ServerLevel level = (ServerLevel) player.level();
		long now = level.getGameTime();
		if (now < SHIP_READY.getOrDefault(ship, 0L)) {
			player.sendOverlayMessage(Component.literal("Reloading...").withStyle(ChatFormatting.GRAY));
			return;
		}

		Vec3 look = player.getViewVector(1.0f);
		List<Gun> guns = gunsFacing(ship, look);
		if (guns.isEmpty()) {
			player.sendOverlayMessage(Component.literal(guns(ship).isEmpty()
					? "This ship has no cannons. Place Cannon blocks facing out over the rail, then set sail."
					: "No cannons point that way. Look out over the side your cannons face.").withStyle(ChatFormatting.YELLOW));
			return;
		}

		Loaded loaded = loaded(player);
		int shots = player.isCreative() ? guns.size() : Math.min(guns.size(), loaded.count());
		if (shots == 0) {
			player.sendOverlayMessage(Component.literal(loaded.ammo() == ShipAmmo.CANNONBALL && loaded.shell().isEmpty()
					? "Out of cannonballs! Make them at a Shipwright's Bench from iron and gunpowder."
					: "Out of " + loaded.title() + "!").withStyle(ChatFormatting.RED));
			return;
		}
		if (!player.isCreative()) {
			takeAmmo(player.getInventory(), loaded, shots);
		}

		// Heavier guns hit harder; a Sniper in the crew (like Usopp) aims tighter and finds the weak spots.
		int gunLevel = ShipUpgrades.guns(ship.getLayout());
		boolean sniper = ShipCrewHelp.has(ship, CrewRole.SNIPER);
		float damage = ShipHull.CANNONBALL_DAMAGE * ShipUpgrades.gunDamage(gunLevel) * (sniper ? 1.15f : 1f);
		double wobble = sniper ? 0.4 : 1.0;
		Vec3 aim = aimFromLook(look);
		// Each gun shoots its own way (see CannonAddons); the crew needs as long to reload as those guns take on average.
		float reloadShare = 0;
		for (int i = 0; i < shots; i++) {
			Gun gun = guns.get(i);
			CannonAddons.Profile profile = gun.profile(level);
			double spread = wobble * profile.spread();
			Vec3 velocity = aim.scale(MUZZLE_SPEED * profile.speed()).add(level.getRandom().nextGaussian() * 0.03 * spread,
					level.getRandom().nextGaussian() * 0.02 * spread, level.getRandom().nextGaussian() * 0.03 * spread);
			fire(level, gun.muzzle(), velocity, player, ship, damage * profile.damage(), loaded.ammo(), loaded.shell());
			reloadShare += profile.reload() / shots;
		}
		int reload = Math.round(SHIP_RELOAD_TICKS * ShipUpgrades.reloadTime(gunLevel) * reloadShare);
		SHIP_READY.put(ship, now + reload);
		CannonReloadPayload status = new CannonReloadPayload(ship.getId(), reload);
		for (ServerPlayer crew : ShipEntity.playersAboard(ship)) {
			ServerPlayNetworking.send(crew, status);
		}
		if (shots < guns.size()) {
			player.sendOverlayMessage(Component.literal("Only " + shots + " " + loaded.title() + " left to fire!").withStyle(ChatFormatting.YELLOW));
		}
	}

	/** The direction cannons fire for a view direction: where the player looks, but never straight down or straight up. */
	public static Vec3 aimFromLook(Vec3 look) {
		return new Vec3(look.x, Math.max(-0.25, Math.min(0.7, look.y)), look.z).normalize();
	}

	/** Right-clicking a Cannon block on land with a cannonball (or special ammo, or an add-on's shell) in hand. */
	public static void fireLandCannon(ServerPlayer player, InteractionHand hand, BlockPos pos, BlockState state) {
		ServerLevel level = (ServerLevel) player.level();
		long now = level.getGameTime();
		if (now < LAND_READY.getOrDefault(pos, 0L)) {
			player.sendOverlayMessage(Component.literal("Reloading...").withStyle(ChatFormatting.GRAY));
			return;
		}
		if (LAND_READY.size() > 256) {
			LAND_READY.values().removeIf(time -> time < now); // Forget old cannons.
		}
		CannonAddons.Profile profile = CannonAddons.profile(level, state, pos);
		LAND_READY.put(pos.immutable(), now + Math.round(LAND_RELOAD_TICKS * profile.reload()));

		ItemStack held = player.getItemInHand(hand);
		ShipAmmo ammo = ShipAmmo.of(held);
		ItemStack shell = ammo == null && CannonAddons.shell(held) != null ? held.copyWithCount(1) : ItemStack.EMPTY;
		Direction face = state.hasProperty(DecorBlock.FACING) ? state.getValue(DecorBlock.FACING) : player.getDirection();
		double up = Math.max(-0.2, Math.min(0.8, player.getViewVector(1.0f).y + 0.1));
		Vec3 direction = new Vec3(face.getStepX(), up, face.getStepZ()).normalize();
		Vec3 muzzle = Vec3.atCenterOf(pos).add(face.getStepX() * MUZZLE_REACH, 0.1, face.getStepZ() * MUZZLE_REACH);
		fire(level, muzzle, direction.scale(MUZZLE_SPEED * profile.speed()), player, null, ShipHull.CANNONBALL_DAMAGE * profile.damage(),
				ammo == null ? ShipAmmo.CANNONBALL : ammo, shell);
		if (!player.isCreative()) {
			player.getItemInHand(hand).shrink(1);
		}
	}

	// ---- Shared by everyone ----

	/** Launches one cannonball with a bang and a puff of smoke. */
	public static void fire(ServerLevel level, Vec3 muzzle, Vec3 velocity, @Nullable Entity owner, @Nullable ShipEntity fromShip, float damage) {
		fire(level, muzzle, velocity, owner, fromShip, damage, ShipAmmo.CANNONBALL);
	}

	public static void fire(ServerLevel level, Vec3 muzzle, Vec3 velocity, @Nullable Entity owner, @Nullable ShipEntity fromShip, float damage, ShipAmmo ammo) {
		fire(level, muzzle, velocity, owner, fromShip, damage, ammo, ItemStack.EMPTY);
	}

	/** shell: an add-on's shell to load instead of ammo (see CannonAddons), or empty. */
	public static void fire(ServerLevel level, Vec3 muzzle, Vec3 velocity, @Nullable Entity owner, @Nullable ShipEntity fromShip, float damage,
			ShipAmmo ammo, ItemStack shell) {
		CannonballEntity ball = new CannonballEntity(ShipCombatFeature.CANNONBALL_ENTITY, level);
		if (shell.isEmpty()) {
			ball.setAmmo(ammo);
		} else {
			ball.setShell(shell);
		}
		ball.setPos(muzzle.x, muzzle.y, muzzle.z);
		ball.setDeltaMovement(velocity);
		ball.setOwner(owner);
		ball.setFromShip(fromShip);
		ball.setDamage(damage);
		level.addFreshEntity(ball);

		Vec3 smoke = velocity.normalize().scale(0.1);
		level.sendParticles(ParticleTypes.EXPLOSION, muzzle.x, muzzle.y, muzzle.z, 1, 0, 0, 0, 0);
		level.sendParticles(ParticleTypes.LARGE_SMOKE, muzzle.x, muzzle.y, muzzle.z, 10, 0.3 + smoke.x, 0.3, 0.3 + smoke.z, 0.04);
		level.playSound(null, BlockPos.containing(muzzle), ModSounds.CANNON, SoundSource.NEUTRAL, 4.0f, 0.9f + level.getRandom().nextFloat() * 0.2f);
	}

	/**
	 * Works out how to aim a cannon so the ball lands on a target: tries every angle from slightly down
	 * to 45 degrees up, flies an imaginary ball with the same gravity and air drag as a real one,
	 * and picks the angle that comes closest. Returns the launch velocity.
	 */
	public static Vec3 aim(Vec3 from, Vec3 to) {
		double dx = to.x - from.x;
		double dz = to.z - from.z;
		double distance = Math.sqrt(dx * dx + dz * dz);
		double rise = to.y - from.y;
		double bestAngle = 0;
		double bestError = Double.MAX_VALUE;
		for (int degrees = -10; degrees <= 45; degrees++) {
			double angle = Math.toRadians(degrees);
			double vx = Math.cos(angle) * MUZZLE_SPEED;
			double vy = Math.sin(angle) * MUZZLE_SPEED;
			double x = 0, y = 0;
			for (int tick = 0; tick < 200 && x < distance; tick++) {
				x += vx;
				y += vy;
				vx *= DRAG;
				vy = vy * DRAG - GRAVITY;
			}
			double error = x < distance ? Double.MAX_VALUE / 2 : Math.abs(y - rise);
			if (error < bestError) {
				bestError = error;
				bestAngle = angle;
			}
		}
		Vec3 flat = distance < 1.0e-3 ? new Vec3(1, 0, 0) : new Vec3(dx / distance, 0, dz / distance);
		return flat.scale(Math.cos(bestAngle) * MUZZLE_SPEED).add(0, Math.sin(bestAngle) * MUZZLE_SPEED, 0);
	}

	// ---- Ammo ----

	public static int countAmmo(Inventory inventory, Item ammo) {
		int count = 0;
		for (int slot = 0; slot < inventory.getContainerSize(); slot++) {
			ItemStack stack = inventory.getItem(slot);
			if (stack.is(ammo)) {
				count += stack.getCount();
			}
		}
		return count;
	}

	private static void takeAmmo(Inventory inventory, Loaded loaded, int amount) {
		for (int slot = 0; slot < inventory.getContainerSize() && amount > 0; slot++) {
			ItemStack stack = inventory.getItem(slot);
			if (loaded.matches(stack)) {
				int take = Math.min(amount, stack.getCount());
				stack.shrink(take);
				amount -= take;
			}
		}
	}
}
