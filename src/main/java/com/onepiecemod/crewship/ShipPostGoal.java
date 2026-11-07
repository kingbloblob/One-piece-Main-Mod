package com.onepiecemod.crewship;

import java.util.EnumSet;
import java.util.UUID;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.component.SwingAnimation;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.crew.CrewMode;
import com.onepiecemod.crew.CrewmateEntity;

/**
 * A crewmate stationed aboard the home ship keeps to their post: by day they work in their room (or help out on
 * deck), by night they sleep in their bunk. Works while docked (walking like normal) and while sailing (the ship's
 * blocks aren't real then, so they walk straight to the spot, and hop there if something's in the way).
 * Fighting comes first: any target and this goal steps aside.
 */
public class ShipPostGoal extends Goal {
	private static final long NIGHT = 12800;
	private static final long MORNING = 23300;

	private final CrewmateEntity crewmate;
	private int repath;
	private int stuck;
	private double lastDistance = Double.MAX_VALUE;
	private int workTimer;
	private boolean lying;

	public ShipPostGoal(CrewmateEntity crewmate) {
		this.crewmate = crewmate;
		this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
	}

	private boolean stationed() {
		if (!(crewmate.level() instanceof ServerLevel level)) {
			return false;
		}
		UUID station = crewmate.getAttached(CrewShipFeature.STATIONED);
		if (station == null) {
			return false;
		}
		if (crewmate.getMode() != CrewMode.WORK || !HomeShips.isCurrent(level.getServer(), crewmate.getCaptainId(), station)) {
			crewmate.removeAttached(CrewShipFeature.STATIONED);
			return false;
		}
		return !crewmate.isKnockedOut() && crewmate.getTarget() == null;
	}

	@Override
	public boolean canUse() {
		return stationed();
	}

	@Override
	public boolean canContinueToUse() {
		return stationed();
	}

	@Override
	public boolean requiresUpdateEveryTick() {
		return true;
	}

	@Override
	public void start() {
		repath = 0;
		stuck = 0;
		lastDistance = Double.MAX_VALUE;
	}

	@Override
	public void stop() {
		wakeUp();
		crewmate.getNavigation().stop();
	}

	private void wakeUp() {
		if (lying) {
			lying = false;
			crewmate.setPose(Pose.STANDING);
		}
	}

	private boolean night() {
		long time = Math.floorMod(crewmate.level().getOverworldClockTime(), 24000L);
		return time >= NIGHT && time < MORNING;
	}

	@Override
	public void tick() {
		CrewShipLife.Assignment job = CrewShipLife.assignment(crewmate);
		if (job == null) {
			// The ship isn't loaded around them (or was just docked): wait where they are.
			crewmate.getNavigation().stop();
			return;
		}
		CrewShipSurvey.Frame frame = job.home().frame;
		if (crewmate.getVehicle() != null) {
			crewmate.stopRiding();
		}
		boolean sleep = night() && job.bunk() != null;
		Vec3 target = sleep ? frame.feet(job.bunk().pos(), job.bunk().top()) : frame.feet(job.post(), 0.02);
		double distance = crewmate.position().distanceTo(target);

		if (sleep && distance < 0.9) {
			crewmate.getNavigation().stop();
			crewmate.setPos(target.x, target.y, target.z);
			crewmate.setDeltaMovement(Vec3.ZERO);
			if (!lying) {
				lying = true;
				crewmate.setPose(Pose.SLEEPING);
			}
			return;
		}
		wakeUp();

		if (distance < (frame.sailing() ? 0.6 : 1.2)) {
			crewmate.getNavigation().stop();
			stuck = 0;
			lastDistance = Double.MAX_VALUE;
			if (job.lookAt() != null) {
				Vec3 look = frame.center(job.lookAt());
				crewmate.getLookControl().setLookAt(look.x, look.y, look.z);
			}
			if (job.room() != null && --workTimer <= 0) {
				workTimer = 60 + crewmate.getRandom().nextInt(60);
				crewmate.swing(InteractionHand.MAIN_HAND, SwingAnimation.DEFAULT);
				CrewShipLife.workFlourish(crewmate, job.room());
			}
			return;
		}

		// Not getting any closer? Hop over.
		if (distance < lastDistance - 0.05) {
			lastDistance = distance;
			stuck = 0;
		} else {
			stuck++;
		}
		int patience = frame.sailing() ? 60 : 160;
		if (distance > (frame.sailing() ? 12 : 32) || stuck > patience) {
			crewmate.getNavigation().stop();
			crewmate.teleportTo(target.x, target.y + 0.05, target.z);
			crewmate.resetFallDistance();
			stuck = 0;
			lastDistance = Double.MAX_VALUE;
			return;
		}
		if (frame.sailing()) {
			crewmate.getMoveControl().setWantedPosition(target.x, target.y, target.z, 0.8);
		} else if (--repath <= 0) {
			repath = 40 + crewmate.getId() % 20;
			crewmate.getNavigation().moveTo(target.x, target.y, target.z, 0.9);
		}
	}
}
