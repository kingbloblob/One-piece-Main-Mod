package com.onepiecemod.hideout;

import java.util.EnumSet;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.state.BlockState;

import com.onepiecemod.crew.CrewMode;
import com.onepiecemod.crew.CrewmateEntity;

/**
 * Life at the hideout for crewmates who live there (set to Work inside the claim):
 * at dusk they gather round a campfire, at night they go to bed (a free bed in the claim), and in the
 * morning they get up and go back to their jobs. Never during a Navy attack, and never while fighting.
 */
public class HideoutLifeGoal extends Goal {
	private static final long DUSK = 11500;
	private static final long NIGHT = 12800;
	private static final long MORNING = 23300;

	/** Which bed each crewmate is heading for, so two don't pick the same one. Server thread only. */
	private static final java.util.Map<java.util.UUID, BlockPos> HEADING = new java.util.HashMap<>();

	private final CrewmateEntity crewmate;
	private BlockPos bed;
	private BlockPos campfire;
	private int repath;
	private int cooldown;

	public HideoutLifeGoal(CrewmateEntity crewmate) {
		this.crewmate = crewmate;
		this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
	}

	private long time() {
		return Math.floorMod(crewmate.level().getOverworldClockTime(), 24000L);
	}

	private boolean night() {
		long time = time();
		return time >= NIGHT && time < MORNING;
	}

	private boolean dusk() {
		long time = time();
		return time >= DUSK && time < NIGHT;
	}

	private HideoutFlagBlockEntity home() {
		if (crewmate.getMode() != CrewMode.WORK || crewmate.getCaptainId() == null || crewmate.isKnockedOut()
				|| !(crewmate.level() instanceof ServerLevel level) || HideoutSiege.isUnderAttack(crewmate.getCaptainId())
				|| !Hideouts.inOwnClaim(crewmate, crewmate.getCaptainId())) {
			return null;
		}
		return Hideouts.flag(level.getServer(), crewmate.getCaptainId());
	}

	@Override
	public boolean canUse() {
		if (--cooldown > 0 || crewmate.getTarget() != null) {
			return false;
		}
		cooldown = 40;
		if (!night() && !dusk()) {
			return false;
		}
		HideoutFlagBlockEntity flag = home();
		if (flag == null || flag.level() < 1) {
			return false;
		}
		bed = null;
		campfire = null;
		if (night()) {
			bed = freeBed(flag.survey().beds);
		}
		if (bed == null) {
			campfire = nearest(flag.survey().campfires);
		}
		return bed != null || campfire != null;
	}

	@Override
	public boolean canContinueToUse() {
		if (crewmate.getTarget() != null || crewmate.isKnockedOut() || crewmate.getMode() != CrewMode.WORK
				|| HideoutSiege.isUnderAttack(crewmate.getCaptainId())) {
			return false;
		}
		if (bed != null) {
			return night() && crewmate.level().getBlockState(bed).getBlock() instanceof BedBlock;
		}
		return dusk() || (night() && campfire != null);
	}

	@Override
	public void start() {
		repath = 0;
		if (bed != null) {
			HEADING.put(crewmate.getUUID(), bed);
		}
	}

	@Override
	public void stop() {
		if (crewmate.isSleeping()) {
			crewmate.stopSleeping();
		}
		crewmate.getNavigation().stop();
		HEADING.remove(crewmate.getUUID());
		bed = null;
		campfire = null;
		cooldown = 40;
	}

	@Override
	public boolean requiresUpdateEveryTick() {
		return true;
	}

	@Override
	public void tick() {
		if (crewmate.isSleeping()) {
			return;
		}
		BlockPos goal = bed != null ? bed : campfire;
		if (goal == null) {
			return;
		}
		double distance = crewmate.distanceToSqr(goal.getX() + 0.5, goal.getY(), goal.getZ() + 0.5);
		if (bed != null && distance < 2.5 * 2.5) {
			BlockState state = crewmate.level().getBlockState(bed);
			if (state.getBlock() instanceof BedBlock && !state.getValue(BedBlock.OCCUPIED)) {
				crewmate.getNavigation().stop();
				crewmate.startSleeping(bed);
			} else {
				bed = null; // Someone got there first: sit by the fire instead.
				HEADING.remove(crewmate.getUUID());
				campfire = nearestCampfire();
			}
			return;
		}
		if (bed == null && distance < 3.5 * 3.5) {
			crewmate.getNavigation().stop();
			crewmate.getLookControl().setLookAt(goal.getX() + 0.5, goal.getY() + 0.5, goal.getZ() + 0.5);
			return;
		}
		if (--repath <= 0) {
			// Repath now and then, not every tick (see the towns lag fix).
			repath = 40 + crewmate.getId() % 20;
			crewmate.getNavigation().moveTo(goal.getX() + 0.5, goal.getY(), goal.getZ() + 0.5, 0.9);
		}
	}

	private BlockPos nearestCampfire() {
		HideoutFlagBlockEntity flag = home();
		return flag == null ? null : nearest(flag.survey().campfires);
	}

	private BlockPos freeBed(List<BlockPos> beds) {
		BlockPos best = null;
		double bestDistance = Double.MAX_VALUE;
		for (BlockPos pos : beds) {
			BlockState state = crewmate.level().getBlockState(pos);
			if (!(state.getBlock() instanceof BedBlock) || state.getValue(BedBlock.OCCUPIED) || takenByCrewmate(pos)) {
				continue;
			}
			double distance = crewmate.distanceToSqr(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5);
			if (distance < bestDistance) {
				best = pos;
				bestDistance = distance;
			}
		}
		return best;
	}

	/** Another crewmate is already heading for (or sleeping in) this bed. */
	private boolean takenByCrewmate(BlockPos pos) {
		for (java.util.Map.Entry<java.util.UUID, BlockPos> entry : HEADING.entrySet()) {
			if (!entry.getKey().equals(crewmate.getUUID()) && entry.getValue().equals(pos)) {
				return true;
			}
		}
		return false;
	}

	private BlockPos nearest(List<BlockPos> list) {
		BlockPos best = null;
		double bestDistance = Double.MAX_VALUE;
		for (BlockPos pos : list) {
			double distance = crewmate.distanceToSqr(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5);
			if (distance < bestDistance) {
				best = pos;
				bestDistance = distance;
			}
		}
		return best;
	}
}
