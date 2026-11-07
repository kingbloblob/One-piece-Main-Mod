package com.onepiecemod.crew.job;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.phys.AABB;

import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewmateEntity;

/**
 * Guard duty for the swordsman (like Zoro) and the sniper (like Usopp).
 * They stand at their post and attack any monster that comes close.
 * The swordsman charges in; the sniper shoots from further away and shouts a warning to the captain.
 */
public class GuardWorkGoal extends WorkGoal {
	private final int guardRange;
	private int warningCooldown;

	public GuardWorkGoal(CrewmateEntity guard, CrewRole role) {
		super(guard, role);
		this.guardRange = role == CrewRole.SNIPER ? 24 : 16;
	}

	@Override
	protected void workTick(ServerLevel level, BlockPos post) {
		if (warningCooldown > 0) {
			warningCooldown--;
		}
		List<Monster> monsters = level.getEntitiesOfClass(Monster.class, new AABB(post).inflate(guardRange), Monster::isAlive);
		Monster closest = null;
		for (Monster monster : monsters) {
			if (closest == null || monster.distanceToSqr(worker) < closest.distanceToSqr(worker)) {
				closest = monster;
			}
		}
		if (closest != null) {
			worker.setTarget(closest); // The fighting goal takes over from here.
			if (worker.getRole() == CrewRole.SNIPER && warningCooldown == 0) {
				worker.tellCaptain("Enemy spotted! A " + closest.getName().getString() + " is coming!");
				warningCooldown = 30; // Don't shout more than every 30 seconds.
			}
		}
	}

	// After a fight, walk back to the post.
	@Override
	protected BlockPos findTarget(ServerLevel level, BlockPos post) {
		return awayFromPost(post) ? post : null;
	}

	@Override
	protected void act(ServerLevel level, BlockPos pos) {
		// Back at the post. Nothing else to do but keep watch.
	}
}
