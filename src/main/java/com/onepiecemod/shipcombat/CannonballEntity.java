package com.onepiecemod.shipcombat;

import org.jetbrains.annotations.Nullable;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.throwableitemprojectile.ThrowableItemProjectile;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.ship.ShipEntity;

/**
 * A flying cannonball. It falls in an arc like a snowball, trails smoke, and explodes when it hits something.
 * Ships it hits lose hull points (see ShipHull). The blast hurts people but never breaks blocks.
 * Landing in the sea just makes a big splash.
 * It can also carry an add-on's shell instead (see CannonAddons), which decides its hull damage and extra effects.
 */
public class CannonballEntity extends ThrowableItemProjectile {
	private static final int MAX_AGE = 200;
	private static final float BLAST_SIZE = 1.8f;
	private static final int CHAINED_TICKS = 20 * 10;
	private static final int BURN_TICKS = 20 * 8;
	private static final float GRAPESHOT_CREW_DAMAGE = 8f;
	private static final double GRAPESHOT_RADIUS = 5;

	private int fromShipId = -1;
	private float damage = ShipHull.CANNONBALL_DAMAGE;
	/** Where the ball really struck a ship's planks (its box can be far bigger than the hull). */
	@Nullable
	private Vec3 shipHitAt;

	public CannonballEntity(EntityType<? extends CannonballEntity> type, Level level) {
		super(type, level);
	}

	@Override
	protected Item getDefaultItem() {
		return ShipCombatFeature.CANNONBALL;
	}

	/** The ship that fired this ball, so it never hits its own ship or crew. */
	public void setFromShip(@Nullable ShipEntity ship) {
		this.fromShipId = ship == null ? -1 : ship.getId();
	}

	public void setDamage(float damage) {
		this.damage = damage;
	}

	/** Loads special ammo. The ball is drawn as that item, and the game saves it with the ball. */
	public void setAmmo(ShipAmmo ammo) {
		setItem(new ItemStack(ammo.item()));
	}

	/** Loads an add-on's shell (see CannonAddons). The ball is drawn as it and keeps its data. */
	public void setShell(ItemStack shell) {
		setItem(shell.copyWithCount(1));
	}

	/** The add-on shell this ball carries, or null for cannonballs and ShipAmmo. */
	@Nullable
	public CannonAddons.Shell shell() {
		return CannonAddons.shell(getItem());
	}

	/** The player who fired this ball, or null (a Marine or pirate ship, or nobody). */
	@Nullable
	public ServerPlayer shooter() {
		return getOwner() instanceof ServerPlayer player ? player : null;
	}

	public ShipAmmo ammo() {
		ShipAmmo ammo = ShipAmmo.of(getItem());
		return ammo == null ? ShipAmmo.CANNONBALL : ammo;
	}

	@Nullable
	private ShipEntity fromShip() {
		return fromShipId >= 0 && level().getEntity(fromShipId) instanceof ShipEntity ship ? ship : null;
	}

	/** Aboard the ship that fired this ball: the captain at the wheel, or anyone walking her deck. */
	public boolean onFiringShip(Entity entity) {
		ShipEntity ship = ShipEntity.aboard(entity);
		return ship != null && ship.getId() == fromShipId;
	}

	@Override
	protected boolean canHitEntity(Entity entity) {
		if (entity instanceof CannonballEntity || entity instanceof ShipEntity ship && ship.sinking) {
			return false;
		}
		if (fromShipId >= 0 && (entity.getId() == fromShipId || onFiringShip(entity))) {
			return false;
		}
		if (entity instanceof ShipEntity ship && shipHitDistance(ship) < 0) {
			return false; // Only inside the ship's square box, not on a real block of it: the ball flies on past.
		}
		return super.canHitEntity(entity);
	}

	/**
	 * How far along this tick's flight the ball first touches one of the ship's real blocks, or -1 if it doesn't.
	 * A ship's box is a big square that also covers the open water beside a long, thin hull.
	 */
	private double shipHitDistance(ShipEntity ship) {
		Vec3 motion = getDeltaMovement();
		double length = motion.length();
		if (length < 1.0e-4) {
			return ship.blockHitDistance(position(), new Vec3(0, -1, 0), 0.5, 1.0f);
		}
		return ship.blockHitDistance(position(), motion.scale(1 / length), length + 0.3, 1.0f);
	}

	@Override
	public void tick() {
		if (!level().isClientSide() && !isRemoved()) {
			hitShipFromInsideItsBox();
			if (isRemoved()) {
				return;
			}
		}
		super.tick();
		if (level().isClientSide()) {
			level().addParticle(ParticleTypes.SMOKE, getX(), getY() + 0.25, getZ(), 0, 0.02, 0);
			return;
		}
		if (isInWater()) {
			// Splash! A miss.
			if (level() instanceof ServerLevel level) {
				level.sendParticles(ParticleTypes.SPLASH, getX(), getY() + 0.5, getZ(), 40, 0.6, 0.3, 0.6, 0.3);
				level.sendParticles(ParticleTypes.BUBBLE_COLUMN_UP, getX(), getY(), getZ(), 12, 0.4, 0.4, 0.4, 0.1);
				level.playSound(null, blockPosition(), com.onepiecemod.sound.WorldSounds.CANNONBALL_SPLASH, SoundSource.NEUTRAL, 2.5f, 0.9f + level.getRandom().nextFloat() * 0.2f);
			}
			discard();
		} else if (tickCount > MAX_AGE) {
			discard();
		}
	}

	/**
	 * The game only notices a projectile entering a box from outside. A ship's box is a big square around the whole
	 * ship, so a ball fired at close range already starts inside an enemy's box and would sail through her planks.
	 */
	private void hitShipFromInsideItsBox() {
		for (ShipEntity ship : level().getEntitiesOfClass(ShipEntity.class, getBoundingBox(), ship -> ship.getBoundingBox().contains(position()))) {
			if (canHitEntity(ship)) {
				onHit(new EntityHitResult(ship));
				return;
			}
		}
	}

	@Override
	protected void onHitEntity(EntityHitResult result) {
		super.onHitEntity(result);
		if (!(level() instanceof ServerLevel level)) {
			return;
		}
		Entity target = result.getEntity();
		ServerPlayer shooter = getOwner() instanceof ServerPlayer player ? player : null;
		if (target instanceof ShipEntity ship) {
			double distance = Math.max(0, shipHitDistance(ship));
			Vec3 motion = getDeltaMovement();
			Vec3 at = motion.lengthSqr() < 1.0e-8 ? position() : position().add(motion.normalize().scale(distance));
			shipHitAt = at;
			ShipAmmo ammo = ammo();
			CannonAddons.Shell shell = shell();
			ShipHull.damage(ship, damage * (shell != null ? shell.hullDamage(getItem()) : ammo.hullDamage), shooter, at, fromShip());
			if (shell != null) {
				shell.onHitShip(level, this, ship, at);
				return;
			}
			switch (ammo) {
				case CHAIN_SHOT -> {
					ShipHull.chain(ship, CHAINED_TICKS);
					level.playSound(null, BlockPos.containing(at), SoundEvents.CHAIN_BREAK, SoundSource.NEUTRAL, 2.0f, 0.7f);
					if (shooter != null) {
						shooter.sendOverlayMessage(Component.literal("Chain shot! Her rigging is tangled.").withStyle(ChatFormatting.AQUA));
					}
				}
				case FIRE_SHOT -> {
					ShipHull.ignite(ship, BURN_TICKS);
					level.playSound(null, BlockPos.containing(at), SoundEvents.FIRECHARGE_USE, SoundSource.NEUTRAL, 2.0f, 0.8f);
				}
				case GRAPESHOT -> {
					for (Entity passenger : ship.getPassengers()) {
						passenger.hurtServer(level, damageSources().thrown(this, getOwner()), GRAPESHOT_CREW_DAMAGE);
					}
				}
				default -> {
				}
			}
		} else {
			target.hurtServer(level, damageSources().thrown(this, getOwner()), damage * 0.5f);
			if (ammo() == ShipAmmo.FIRE_SHOT) {
				target.igniteForSeconds(5);
			}
			CannonAddons.Shell shell = shell();
			if (shell != null) {
				shell.onHitEntity(level, this, target);
			}
		}
	}

	@Override
	protected void onHit(HitResult result) {
		super.onHit(result);
		if (level() instanceof ServerLevel level && !isRemoved()) {
			Vec3 at = shipHitAt != null ? shipHitAt : result.getLocation();
			// Our own blast: ShipHull ignores it on ships (the hit above already counted), but it hurts people nearby.
			level.explode(this, at.x, at.y, at.z, BLAST_SIZE, Level.ExplosionInteraction.NONE);
			if (ammo() == ShipAmmo.GRAPESHOT) {
				// A cloud of iron balls: hurts everyone around where it bursts (not the shooter's own ship's crew).
				for (LivingEntity victim : level.getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(GRAPESHOT_RADIUS),
						victim -> victim != getOwner() && (fromShipId < 0 || !onFiringShip(victim)))) {
					victim.hurtServer(level, damageSources().thrown(this, getOwner()), GRAPESHOT_CREW_DAMAGE);
				}
				level.sendParticles(ParticleTypes.CRIT, at.x, at.y, at.z, 40, 1.5, 1.0, 1.5, 0.5);
			}
			CannonAddons.Shell shell = shell();
			if (shell != null) {
				shell.onBurst(level, this, at);
			}
			level.sendParticles(ParticleTypes.LARGE_SMOKE, at.x, at.y, at.z, 16, 0.5, 0.5, 0.5, 0.05);
			discard();
		}
	}

	/** Cannonballs can be seen from far away, like arrows. */
	@Override
	public boolean shouldRenderAtSqrDistance(double distance) {
		return distance < 160 * 160;
	}
}
