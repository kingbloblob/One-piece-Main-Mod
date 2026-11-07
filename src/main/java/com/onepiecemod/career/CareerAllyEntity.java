package com.onepiecemod.career;

import java.util.EnumSet;
import java.util.UUID;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.level.Level;

import com.onepiecemod.bounty.MarineEntity;
import com.onepiecemod.empire.PirateGuardEntity;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.shipcombat.SeaPirateEntity;

/**
 * A Marine or Revolutionary soldier who answered your Den Den Mushi call. It follows you, fights whoever
 * you fight (and pirates or Marines on its own), can't be hurt by you, and leaves after a few minutes.
 * Never saved: if it unloads, it's gone.
 */
public class CareerAllyEntity extends HumanNpc {
	/** Revolutionary skins live in textures/entity/career/; Marines use the normal NPC skins (empty here). */
	private static final EntityDataAccessor<String> DATA_CAREER_SKIN = SynchedEntityData.defineId(CareerAllyEntity.class, EntityDataSerializers.STRING);
	/** How long backup stays: 3 minutes. */
	public static final int LIFETIME = 20 * 180;

	private UUID ownerId;
	private boolean marineSide = true;
	private int ticksLeft = LIFETIME;

	public CareerAllyEntity(EntityType<? extends CareerAllyEntity> type, Level level) {
		super(type, level);
		this.xpReward = 0;
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(DATA_CAREER_SKIN, "");
	}

	public void setup(ServerPlayer owner, boolean marine) {
		this.ownerId = owner.getUUID();
		this.marineSide = marine;
	}

	public void setCareerSkin(String skin) {
		this.entityData.set(DATA_CAREER_SKIN, skin);
	}

	public String getCareerSkin() {
		return this.entityData.get(DATA_CAREER_SKIN);
	}

	public UUID getOwnerId() {
		return ownerId;
	}

	public ServerPlayer getOwner() {
		if (ownerId == null || !(this.level() instanceof ServerLevel level)) {
			return null;
		}
		ServerPlayer owner = level.getServer().getPlayerList().getPlayer(ownerId);
		return owner != null && owner.level() == level && owner.isAlive() ? owner : null;
	}

	@Override
	public boolean isMarineSide() {
		return marineSide;
	}

	@Override
	protected void registerGoals() {
		super.registerGoals();
		this.goalSelector.addGoal(5, new FollowOwnerGoal());
	}

	@Override
	protected void addTargetGoals() {
		this.targetSelector.addGoal(2, new DefendOwnerGoal());
		// The other side, and monsters, on sight.
		this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, LivingEntity.class, 10, true, false,
				(target, level) -> isFoe(target)));
	}

	private boolean isFoe(LivingEntity target) {
		if (target instanceof CareerAllyEntity) {
			return false;
		}
		if (marineSide) {
			return target instanceof SeaPirateEntity || target instanceof PirateGuardEntity
					|| (target instanceof Enemy && !(target instanceof HumanNpc));
		}
		return target instanceof MarineEntity || (target instanceof Enemy && !(target instanceof HumanNpc));
	}

	/** Never turns on its owner or the rest of the backup. Revolutionaries side with nobody else. */
	@Override
	public boolean considersEntityAsAlly(Entity other) {
		if (ownerId != null && ownerId.equals(other.getUUID())) {
			return true;
		}
		if (other instanceof CareerAllyEntity ally) {
			return ownerId != null && ownerId.equals(ally.ownerId);
		}
		if (!marineSide && other instanceof HumanNpc) {
			return false;
		}
		return super.considersEntityAsAlly(other);
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		Entity attacker = source.getEntity();
		if (attacker != null && (attacker.getUUID().equals(ownerId) || attacker instanceof CareerAllyEntity)) {
			return false; // Friendly fire does nothing.
		}
		return super.hurtServer(level, source, amount);
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (--ticksLeft <= 0 || (this.tickCount % 20 == 0 && getOwner() == null)) {
			leave(level);
		}
	}

	/** Back to base, in a puff of smoke. */
	public void leave(ServerLevel level) {
		level.sendParticles(ParticleTypes.POOF, getX(), getY() + 1, getZ(), 12, 0.3, 0.6, 0.3, 0.02);
		discard();
	}

	/** Backup drops nothing: no Berries to farm from your own soldiers. */
	@Override
	protected void dropCustomDeathLoot(ServerLevel level, DamageSource source, boolean recentlyHit) {
	}

	@Override
	public boolean removeWhenFarAway(double distance) {
		return false;
	}

	/** Walks after the owner, and catches up instantly if left far behind. */
	private class FollowOwnerGoal extends Goal {
		FollowOwnerGoal() {
			this.setFlags(EnumSet.of(Goal.Flag.MOVE));
		}

		@Override
		public boolean canUse() {
			ServerPlayer owner = getOwner();
			return owner != null && getTarget() == null && distanceToSqr(owner) > 6 * 6;
		}

		@Override
		public boolean canContinueToUse() {
			ServerPlayer owner = getOwner();
			return owner != null && getTarget() == null && distanceToSqr(owner) > 3 * 3;
		}

		@Override
		public void tick() {
			ServerPlayer owner = getOwner();
			if (owner == null) {
				return;
			}
			if (distanceToSqr(owner) > 24 * 24 && owner.onGround()) {
				snapTo(owner.getX() + getRandom().nextInt(3) - 1, owner.getY(), owner.getZ() + getRandom().nextInt(3) - 1);
				getNavigation().stop();
			} else if (getNavigation().isDone() || tickCount % 10 == 0) {
				getNavigation().moveTo(owner, 1.15);
			}
		}

		@Override
		public void stop() {
			getNavigation().stop();
		}
	}

	/** Attacks whatever hurt the owner, or whatever the owner is hitting. */
	private class DefendOwnerGoal extends Goal {
		private LivingEntity picked;

		DefendOwnerGoal() {
			this.setFlags(EnumSet.of(Goal.Flag.TARGET));
		}

		@Override
		public boolean canUse() {
			ServerPlayer owner = getOwner();
			if (owner == null || tickCount % 5 != 0) {
				return false;
			}
			LivingEntity attacker = owner.getLastHurtByMob();
			if (valid(attacker) && owner.tickCount - owner.getLastHurtByMobTimestamp() < 100) {
				picked = attacker;
				return true;
			}
			LivingEntity victim = owner.getLastHurtMob();
			if (valid(victim) && owner.tickCount - owner.getLastHurtMobTimestamp() < 100) {
				picked = victim;
				return true;
			}
			return false;
		}

		private boolean valid(LivingEntity entity) {
			return entity != null && entity.isAlive() && entity != getTarget() && !isAlliedTo(entity)
					&& entity.level() == level() && distanceToSqr(entity) < 32 * 32;
		}

		@Override
		public void start() {
			setTarget(picked);
		}

		@Override
		public boolean canContinueToUse() {
			return false;
		}
	}
}
