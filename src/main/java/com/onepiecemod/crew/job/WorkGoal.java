package com.onepiecemod.crew.job;

import net.minecraft.world.item.component.SwingAnimation;
import java.util.EnumSet;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.anim.Anim;
import com.onepiecemod.anim.CombatAnims;
import com.onepiecemod.crew.CrewMode;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewmateEntity;

/**
 * The shared part of every crew job. Each role's job extends this class.
 *
 * About once a second, while the crewmate is in Work mode:
 * 1. workTick() runs, for things done on the spot (healing, playing music, crafting from the bag...).
 * 2. findTarget() picks a block to walk to. If there is none and the bag has finished goods,
 *    the crewmate heads to the nearest chest or barrel to drop them off.
 * 3. When they reach the block, act() does the work there.
 *
 * Everything happens within RANGE blocks of the spot where the captain set them to work.
 */
public abstract class WorkGoal extends Goal {
	public static final int RANGE = 10;

	protected final CrewmateEntity worker;
	private final CrewRole role;
	private BlockPos target;
	private boolean goingToStore;
	private int cooldown;
	private int ticksTrying;

	protected WorkGoal(CrewmateEntity worker, CrewRole role) {
		this.worker = worker;
		this.role = role;
		this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
	}

	/** Work done on the spot, about once a second. */
	protected void workTick(ServerLevel level, BlockPos post) {}

	/** A block to walk to and work on, or null if there's nothing to do. */
	protected abstract BlockPos findTarget(ServerLevel level, BlockPos post);

	/** The work done once the crewmate reaches the block from findTarget(). */
	protected abstract void act(ServerLevel level, BlockPos pos);

	/** The body animation for doing this job (see the anim package), or null for a plain arm swing. */
	protected Anim workAnim() {
		return null;
	}

	/** True for things this job makes or finds that belong in the chest. */
	protected boolean shouldStore(ItemStack stack) {
		return false;
	}

	protected boolean isWorking() {
		if (worker.getTarget() != null && !worker.getTarget().isAlive()) {
			worker.setTarget(null); // The fight is over, back to work.
		}
		return worker.getMode() == CrewMode.WORK
				&& worker.getRole() == role
				&& worker.getWorkPos() != null
				&& worker.getTarget() == null // Fighting comes first.
				&& worker.level() instanceof ServerLevel;
	}

	@Override
	public boolean canUse() {
		if (!isWorking()) {
			return false;
		}
		if (cooldown > 0) {
			cooldown--;
			return false;
		}
		cooldown = (int) Math.round(20 * worker.workTime()); // Lazy crewmates take longer, hard workers and high levels less.
		ServerLevel level = (ServerLevel) worker.level();
		BlockPos post = worker.getWorkPos();
		workTick(level, post);

		goingToStore = false;
		target = findTarget(level, post);
		if (target == null && JobHelpers.hasAny(worker.getInventory(), this::shouldStore)) {
			target = JobHelpers.nearestChest(level, post, RANGE);
			goingToStore = target != null;
		}
		return target != null;
	}

	@Override
	public boolean canContinueToUse() {
		return target != null && ticksTrying < 400 && isWorking(); // Give up after 20 seconds if they can't get there.
	}

	@Override
	public boolean requiresUpdateEveryTick() {
		return true;
	}

	@Override
	public void start() {
		ticksTrying = 0;
		walkToTarget();
	}

	@Override
	public void tick() {
		if (target == null) {
			return; // Finished last tick; the goal stops on the next check.
		}
		ticksTrying++;
		worker.getLookControl().setLookAt(Vec3.atCenterOf(target));
		if (target.closerToCenterThan(worker.position(), 2.5)) {
			ServerLevel level = (ServerLevel) worker.level();
			Anim anim = goingToStore ? null : workAnim();
			if (anim != null) {
				CombatAnims.play(worker, anim);
			} else {
				worker.swing(InteractionHand.MAIN_HAND, SwingAnimation.DEFAULT);
			}
			if (goingToStore) {
				store(level, target);
			} else {
				act(level, target);
				worker.addXp(1); // A little XP for every job done.
			}
			target = null; // Done. canContinueToUse() is now false and the goal stops.
		} else if (ticksTrying % 20 == 0) {
			walkToTarget(); // Re-plan the path every second in case something moved.
		}
	}

	@Override
	public void stop() {
		target = null;
		worker.getNavigation().stop();
	}

	private void walkToTarget() {
		worker.getNavigation().moveTo(target.getX() + 0.5, target.getY(), target.getZ() + 0.5, 0.9);
	}

	private void store(ServerLevel level, BlockPos pos) {
		BlockEntity blockEntity = level.getBlockEntity(pos);
		if (blockEntity instanceof Container chest) {
			JobHelpers.deposit(worker.getInventory(), chest, this::shouldStore);
			blockEntity.setChanged();
		}
	}

	/** True when the crewmate stands more than a few blocks from their post. */
	protected boolean awayFromPost(BlockPos post) {
		return !post.closerToCenterThan(worker.position(), 3.0);
	}
}
