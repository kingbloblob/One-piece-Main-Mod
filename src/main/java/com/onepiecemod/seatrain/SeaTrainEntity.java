package com.onepiecemod.seatrain;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * The Puffing Tom itself: an invisible "root" that runs in a straight line.
 * The engine and the carriages are block displays riding it (see {@link PuffingTom}),
 * and the passenger sits in the driver's cab.
 *
 * It is never saved. A train with no trip behind it (after a restart, say) pulls away and vanishes.
 */
public class SeaTrainEntity extends Entity {
	/** Where the passenger sits, measured from the root: in the open cab behind the boiler. */
	static final Vec3 SEAT = new Vec3(0.0, 0.85, 1.15);

	private double speed;
	private double acceleration;
	private double maxSpeed = 1.1;
	private int lifeLeft = -1;
	/** Set by {@link Trips} while a trip is using this train. */
	boolean onTrip;

	public SeaTrainEntity(EntityType<? extends SeaTrainEntity> type, Level level) {
		super(type, level);
		this.noPhysics = true;
		this.setNoGravity(true);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		return false;
	}

	@Override
	public boolean shouldBeSaved() {
		return false; // A train only exists during a trip. (Not noSave() on the type: players can't ride those.)
	}

	@Override
	public boolean isPickable() {
		return false;
	}

	@Override
	protected boolean canAddPassenger(Entity passenger) {
		return true; // The whole train rides along, plus one passenger.
	}

	@Override
	protected void positionRider(Entity passenger, MoveFunction moveFunction) {
		if (passenger instanceof Display) {
			moveFunction.accept(passenger, getX(), getY(), getZ());
			return;
		}
		Vec3 seat = SEAT.yRot(-getYRot() * ((float) Math.PI / 180f));
		moveFunction.accept(passenger, getX() + seat.x, getY() + seat.y, getZ() + seat.z);
	}

	/** Which way the train faces and runs. */
	Vec3 heading() {
		return Vec3.directionFromRotation(0f, getYRot());
	}

	void setSpeed(double speed, double acceleration) {
		this.speed = speed;
		this.acceleration = acceleration;
	}

	double speed() {
		return speed;
	}

	/** Pull away and vanish after this many ticks, with nobody aboard but the train. */
	void leave(int ticks) {
		onTrip = false;
		lifeLeft = ticks;
		if (speed < 0.05) {
			setSpeed(0.05, 0.03);
		}
	}

	@Override
	public void tick() {
		super.tick();
		speed = Math.max(0, Math.min(maxSpeed, speed + acceleration));
		if (speed > 0) {
			Vec3 step = heading().scale(speed);
			setPos(getX() + step.x, getY(), getZ() + step.z);
		}
		if (!(level() instanceof ServerLevel level)) {
			return;
		}
		// Steam out of the chimney (at the front of the engine), more of it the faster she runs.
		if (tickCount % (speed > 0.3 ? 1 : 3) == 0) {
			Vec3 chimney = position().add(PuffingTom.CHIMNEY.yRot(-getYRot() * ((float) Math.PI / 180f)));
			level.sendParticles(speed > 0.3 ? ParticleTypes.LARGE_SMOKE : ParticleTypes.CAMPFIRE_COSY_SMOKE,
					chimney.x, chimney.y, chimney.z, 2, 0.15, 0.1, 0.15, 0.02);
		}
		if (!onTrip && lifeLeft < 0) {
			leave(40); // Left over from a trip that ended: off she goes.
		}
		if (lifeLeft > 0 && --lifeLeft == 0) {
			scrap();
		}
	}

	/** Removes the train and every carriage riding it. A player still aboard just steps off. */
	void scrap() {
		for (Entity passenger : getPassengers()) {
			if (passenger instanceof Display) {
				passenger.discard();
			} else {
				passenger.stopRiding();
			}
		}
		discard();
	}

	@Override
	public void remove(RemovalReason reason) {
		// Unloaded or killed: don't leave the carriages floating there.
		if (!level().isClientSide()) {
			for (Entity passenger : getPassengers()) {
				if (passenger instanceof Display) {
					passenger.discard();
				}
			}
		}
		super.remove(reason);
	}
}
