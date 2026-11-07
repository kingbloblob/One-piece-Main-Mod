package com.onepiecemod.furniture;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.vehicle.DismountHelper;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * The invisible thing you ride when you sit on a chair, stool, bench or cushion.
 * It goes away when you stand up or the seat is broken, and is never saved.
 */
public class SeatEntity extends Entity {
	public SeatEntity(EntityType<?> type, Level level) {
		super(type, level);
		noPhysics = true;
		setNoGravity(true);
	}

	@Override
	public void tick() {
		super.tick();
		if (level().isClientSide()) {
			return;
		}
		BlockPos pos = BlockPos.containing(getX(), getY() + 0.01, getZ());
		boolean seat = level().getBlockState(pos).getBlock() instanceof FurnitureBlock block && block.isSeat();
		if (!isVehicle() || !seat) {
			ejectPassengers();
			discard();
		}
	}

	@Override
	public Vec3 getDismountLocationForPassenger(LivingEntity passenger) {
		// Stand up in front of the seat (where your legs are), else beside it or behind it, and only climb
		// on top of it when every side is blocked.
		BlockPos pos = BlockPos.containing(getX(), getY() + 0.01, getZ());
		BlockState state = level().getBlockState(pos);
		Direction front = state.hasProperty(FurnitureBlock.FACING) ? state.getValue(FurnitureBlock.FACING) : passenger.getDirection();
		for (Direction side : new Direction[] {front, front.getClockWise(), front.getCounterClockWise(), front.getOpposite()}) {
			Vec3 spot = DismountHelper.findSafeDismountLocation(passenger.getType(), level(), pos.relative(side), true);
			if (spot != null && spot.y <= pos.getY() + 1.0) {
				return spot;
			}
		}
		return new Vec3(getX(), pos.getY() + 1.0, getZ());
	}

	/** Never written to disk: when a chunk reloads, whoever was sitting is standing anyway. */
	@Override
	public boolean shouldBeSaved() {
		return false;
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		return false;
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
	}
}
