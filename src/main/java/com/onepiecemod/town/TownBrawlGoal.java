package com.onepiecemod.town;

import java.util.EnumSet;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/** Fists up! A townsperson in a bar brawl goes after whoever BarBrawls pointed them at. Nobody gets killed. */
public class TownBrawlGoal extends Goal {
	private final TownsfolkEntity mob;
	private int cooldown;

	public TownBrawlGoal(TownsfolkEntity mob) {
		this.mob = mob;
		this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
	}

	@Override
	public boolean canUse() {
		LivingEntity target = mob.brawlTarget();
		return mob.brawlId() != 0 && !mob.isKnockedOut() && target != null && target.isAlive();
	}

	@Override
	public void stop() {
		mob.getNavigation().stop();
	}

	@Override
	public boolean requiresUpdateEveryTick() {
		return true;
	}

	@Override
	public void tick() {
		LivingEntity target = mob.brawlTarget();
		if (target == null) {
			return;
		}
		mob.getLookControl().setLookAt(target, 30f, 30f);
		double distance = mob.distanceToSqr(target);
		if (distance > 3.2) {
			if (mob.tickCount % 10 == 0) {
				mob.getNavigation().moveTo(target, 1.15);
			}
		} else {
			mob.getNavigation().stop();
		}
		if (cooldown > 0) {
			cooldown--;
			return;
		}
		if (distance <= 4.0 && mob.level() instanceof ServerLevel level) {
			cooldown = 18 + mob.getRandom().nextInt(14);
			mob.swing(net.minecraft.world.InteractionHand.MAIN_HAND, net.minecraft.world.item.component.SwingAnimation.DEFAULT);
			if (!(target instanceof Player) && mob.getRandom().nextFloat() < 0.35f) {
				mob.playSound(SoundEvents.PLAYER_ATTACK_NODAMAGE, 0.8f, 1.0f); // Swing and a miss!
				return;
			}
			float damage = 1.0f + mob.getRandom().nextFloat();
			if (target instanceof Player player && player.getHealth() - damage <= 6.0f) {
				// They won't beat you senseless: once you're done for, they gloat instead.
				BarBrawls.onPlayerBeaten(mob, player, level);
				return;
			}
			if (target.hurtServer(level, mob.damageSources().mobAttack(mob), damage)) {
				Vec3 push = target.position().subtract(mob.position()).normalize();
				target.knockback(0.45, -push.x, -push.z, mob.damageSources().generic(), 0.0f);
				level.sendParticles(ParticleTypes.CRIT, target.getX(), target.getY() + 1.2, target.getZ(), 5, 0.2, 0.2, 0.2, 0.1);
				mob.playSound(SoundEvents.PLAYER_ATTACK_KNOCKBACK, 0.8f, 1.1f);
			}
		}
	}
}
