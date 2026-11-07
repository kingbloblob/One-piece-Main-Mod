package com.onepiecemod.pet;

import java.util.EnumSet;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.player.Player;

/** The goals every pet shares: follow its owner, defend its owner, and join its owner's fights. */
public final class PetGoals {
	private PetGoals() {
	}

	/** A tamed pet follows its owner around, and hops over if left more than 24 blocks behind. */
	public static class FollowOwner<T extends PathfinderMob & Pet> extends Goal {
		private final T mob;
		private LivingEntity owner;

		public FollowOwner(T mob) {
			this.mob = mob;
			this.setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK));
		}

		@Override
		public boolean canUse() {
			owner = Pets.ownerOf(mob, mob.level());
			return owner != null && !mob.isStaying() && !mob.isVehicle() && mob.getTowShip() == null && !owner.isSpectator()
					&& mob.distanceToSqr(owner) > 64.0;
		}

		@Override
		public boolean canContinueToUse() {
			return owner != null && owner.isAlive() && !mob.isStaying() && !mob.isVehicle() && mob.getTowShip() == null
					&& mob.distanceToSqr(owner) > 9.0;
		}

		@Override
		public void tick() {
			mob.getLookControl().setLookAt(owner, 10.0f, mob.getMaxHeadXRot());
			if (mob.tickCount % 10 != 0) {
				return;
			}
			if (mob.distanceToSqr(owner) > 576.0 && (mob.petSwims() || owner.onGround()) && Pets.bringTo(mob, owner)) {
				return;
			}
			mob.getNavigation().moveTo(owner, 1.2);
		}

		@Override
		public void stop() {
			owner = null;
			mob.getNavigation().stop();
		}
	}

	/** A tamed fighter joins in on whatever mob its owner hits (never other players). */
	public static class OwnerAttacks<T extends PathfinderMob & Pet> extends Goal {
		private final T mob;
		private int seenTimestamp;

		public OwnerAttacks(T mob) {
			this.mob = mob;
			this.setFlags(EnumSet.of(Goal.Flag.TARGET));
		}

		@Override
		public boolean canUse() {
			LivingEntity owner = Pets.ownerOf(mob, mob.level());
			if (owner == null || mob.isStaying()) {
				return false;
			}
			LivingEntity victim = owner.getLastHurtMob();
			return victim != null && owner.getLastHurtMobTimestamp() != seenTimestamp && victim != mob
					&& victim.isAlive() && !(victim instanceof Player) && mob.canAttack(victim);
		}

		@Override
		public void start() {
			LivingEntity owner = Pets.ownerOf(mob, mob.level());
			seenTimestamp = owner.getLastHurtMobTimestamp();
			mob.setTarget(owner.getLastHurtMob());
		}
	}

	/** A tamed fighter attacks whoever hurts its owner. */
	public static class DefendOwner<T extends PathfinderMob & Pet> extends Goal {
		private final T mob;
		private LivingEntity attacker;

		public DefendOwner(T mob) {
			this.mob = mob;
			this.setFlags(EnumSet.of(Goal.Flag.TARGET));
		}

		@Override
		public boolean canUse() {
			LivingEntity owner = Pets.ownerOf(mob, mob.level());
			if (owner == null) {
				return false;
			}
			attacker = owner.getLastHurtByMob();
			return attacker != null && attacker != mob && attacker.isAlive() && mob.canAttack(attacker);
		}

		@Override
		public void start() {
			mob.setTarget(attacker);
		}
	}
}
