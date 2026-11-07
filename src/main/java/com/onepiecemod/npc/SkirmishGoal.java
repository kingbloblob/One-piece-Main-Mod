package com.onepiecemod.npc;

import java.util.EnumSet;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.monster.RangedAttackMob;

/**
 * How gunners, snipers, bombers and sniper crewmates fight: shoot from a distance, step side to side
 * while aiming, and back off when someone gets too close. Works like vanilla skeletons, but for any
 * ranged mob (vanilla's version only works while holding a bow).
 */
public class SkirmishGoal<T extends PathfinderMob & RangedAttackMob> extends Goal {
	private final T mob;
	private final double speed;
	private final int minInterval;
	private final int maxInterval;
	private final float range;
	/** Closer than this, the shooter walks backwards while it keeps shooting. */
	private final float keepAway;

	private int attackTime = -1;
	private int seeTime;
	private int strafeTime = -1;
	private boolean strafeClockwise;
	private boolean strafeBackwards;

	public SkirmishGoal(T mob, double speed, int minInterval, int maxInterval, float range) {
		this.mob = mob;
		this.speed = speed;
		this.minInterval = minInterval;
		this.maxInterval = maxInterval;
		this.range = range;
		this.keepAway = Math.max(4.0f, range * 0.35f);
		this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK));
	}

	@Override
	public boolean canUse() {
		LivingEntity target = mob.getTarget();
		return target != null && target.isAlive();
	}

	@Override
	public boolean canContinueToUse() {
		return canUse() || !mob.getNavigation().isDone();
	}

	@Override
	public void start() {
		mob.setAggressive(true);
	}

	@Override
	public void stop() {
		mob.setAggressive(false);
		seeTime = 0;
		attackTime = -1;
		strafeTime = -1;
		mob.getMoveControl().strafe(0.0f, 0.0f);
	}

	@Override
	public boolean requiresUpdateEveryTick() {
		return true;
	}

	@Override
	public void tick() {
		LivingEntity target = mob.getTarget();
		if (target == null) {
			return;
		}
		double distanceSqr = mob.distanceToSqr(target.getX(), target.getY(), target.getZ());
		boolean canSee = mob.getSensing().hasLineOfSight(target);
		if (canSee != seeTime > 0) {
			seeTime = 0;
		}
		seeTime = canSee ? seeTime + 1 : seeTime - 1;

		// Too far or can't see you: walk closer. In range: stop and start moving side to side.
		if (distanceSqr > range * range * 0.8 || seeTime < 20) {
			if (mob.tickCount % 10 == 0 || mob.getNavigation().isDone()) {
				mob.getNavigation().moveTo(target, speed);
			}
			strafeTime = -1;
		} else {
			mob.getNavigation().stop();
			strafeTime++;
		}

		if (strafeTime >= 20) {
			if (mob.getRandom().nextFloat() < 0.3f) {
				strafeClockwise = !strafeClockwise;
			}
			if (mob.getRandom().nextFloat() < 0.3f) {
				strafeBackwards = !strafeBackwards;
			}
			strafeTime = 0;
		}

		if (strafeTime > -1) {
			float forward;
			if (distanceSqr < keepAway * keepAway) {
				forward = -0.6f; // Someone is in my face: back off.
			} else if (distanceSqr > range * range * 0.6) {
				forward = 0.4f;
			} else {
				forward = strafeBackwards ? -0.2f : 0.2f;
			}
			mob.getMoveControl().strafe(forward, strafeClockwise ? 0.45f : -0.45f);
			mob.lookAt(target, 30.0f, 30.0f);
		}
		mob.getLookControl().setLookAt(target, 30.0f, 30.0f);

		// Shooting rhythm, the same as vanilla's ranged goal: closer targets get shot a bit more often.
		if (--attackTime == 0) {
			if (!canSee) {
				return;
			}
			float power = (float) Math.sqrt(distanceSqr) / range;
			mob.performRangedAttack(target, Math.max(0.1f, Math.min(1.0f, power)));
			attackTime = (int) Math.floor(power * (maxInterval - minInterval) + minInterval);
		} else if (attackTime < 0) {
			float power = (float) Math.sqrt(distanceSqr) / range;
			attackTime = (int) Math.floor(power * (maxInterval - minInterval) + minInterval);
		}
	}
}
