package com.onepiecemod.town;

import java.util.EnumSet;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.util.LandRandomPos;
import net.minecraft.world.level.pathfinder.Path;
import net.minecraft.world.entity.player.Player;

/**
 * A townsperson's day. Every second they check the clock and decide where they should be:
 *
 *   6-7 am   at home, getting up          noon   lunch on the plaza
 *   7 am-5 pm at work (merchants at their market stall, fishers on the docks, cooks at the stove)
 *   5-7 pm   evening: the bar for sailors and bartenders, the plaza for everybody else, kids play tag
 *   7 pm     home and to bed (bar regulars stay out until midnight)
 *
 * Rain sends people indoors, festivals pull everyone to the plaza to dance, and Aqua Laguna sends them hiding.
 * They open doors and gates on the way (TownNavigation, TownDoorGoal). Someone who can't get through steps aside and
 * tries again, picks another spot if any spot will do, and gives up on a home or workplace nobody can reach (the town
 * remembers it for a day). If they're still stuck while nobody is watching, they just turn up where they were going.
 * Once there they don't stand like statues: workers shuffle about their workplace and people stroll around town.
 */
public class TownRoutineGoal extends Goal {
	public enum Activity { HOME, SLEEP, WORK, MARKET, SOCIAL, PLAY, BAR, FESTIVAL, SHELTER }

	private final TownsfolkEntity mob;
	private Activity activity = Activity.HOME;
	private BlockPos target;
	private int recheck;
	private int stuckTicks;
	private double lastDistance = Double.MAX_VALUE;
	private int idleTicks;
	/** Ticks until we may plan a new path. A failed search (target out of reach) waits longer, so it isn't redone every tick. */
	private int pathCooldown;
	/** Times in a row the way to the current target was blocked, and when that started. */
	private int failures;
	private int blockedSince;
	/** Where we stood at the last movement check, and how many checks in a row we barely moved. */
	private net.minecraft.world.phys.Vec3 lastPos;
	private int stillChecks;
	/** A short step aside (to get unstuck, or a stroll around the workplace) that the routine leaves alone. */
	private int sideTrip;
	/** Already climbed out once while stuck this time (once is enough: hopping about again and again looks silly). */
	private boolean climbed;

	public TownRoutineGoal(TownsfolkEntity mob) {
		this.mob = mob;
		this.setFlags(EnumSet.of(Flag.MOVE, Flag.JUMP));
	}

	@Override
	public boolean canUse() {
		return !mob.isTrading() && mob.brawlId() == 0 && !mob.isKnockedOut() && !mob.isPassenger() && !mob.isPanicking();
	}

	@Override
	public boolean canContinueToUse() {
		return canUse();
	}

	@Override
	public void start() {
		recheck = 0;
	}

	@Override
	public void stop() {
		mob.getNavigation().stop();
	}

	@Override
	public boolean requiresUpdateEveryTick() {
		return true;
	}

	public static Activity activityFor(TownsfolkEntity mob) {
		long time = mob.level().getOverworldClockTime() % 24000L;
		TownData.Job job = mob.job();
		Town town = mob.town();
		TownData.Festival festival = town == null ? null : Festivals.active(town);
		if (festival != null && festival.hazard) {
			return Activity.SHELTER;
		}
		boolean hasBar = town == null || town.def.bar;
		if (festival != null) {
			// Bartenders keep pouring and market sellers keep selling; everyone else parties.
			if ("bartender".equals(mob.jobId()) && hasBar) {
				return Activity.BAR;
			}
			return job.marketer ? Activity.MARKET : Activity.FESTIVAL;
		}
		boolean raining = mob.level().isRaining();
		Activity planned;
		if (time >= 23500 || time < 1000) {
			planned = Activity.HOME;
		} else if (time < 6000 || (time >= 7000 && time < 11000)) {
			planned = job.child ? Activity.PLAY : job.marketer ? Activity.MARKET : Activity.WORK;
		} else if (time < 7000) {
			planned = job.marketer || "cook".equals(mob.jobId()) || "bartender".equals(mob.jobId()) ? (job.marketer ? Activity.MARKET : Activity.WORK)
					: Activity.SOCIAL;
		} else if (time < 13000) {
			planned = job.child ? Activity.PLAY : (job.brawler || job.nightOwl) && hasBar ? Activity.BAR : Activity.SOCIAL;
		} else if (time < 18000) {
			planned = job.nightOwl && hasBar ? Activity.BAR : time < 13600 ? Activity.HOME : Activity.SLEEP;
		} else {
			planned = Activity.SLEEP;
		}
		if ("bartender".equals(mob.jobId()) && hasBar && planned == Activity.WORK) {
			planned = Activity.BAR;
		}
		if (mob.isVisitor()) {
			planned = Activity.MARKET;
		}
		// Rain: outdoor folk head for the bar or home.
		if (raining && (planned == Activity.SOCIAL || planned == Activity.PLAY
				|| (planned == Activity.WORK && ("farmer".equals(mob.jobId()) || "fisher".equals(mob.jobId()))))) {
			planned = hasBar && !job.child ? Activity.BAR : Activity.HOME;
		}
		return planned;
	}

	private BlockPos targetFor(Activity activity) {
		Town town = mob.town();
		var random = mob.getRandom();
		return switch (activity) {
			case HOME, SLEEP, SHELTER -> mob.home();
			case WORK, MARKET -> mob.work();
			case BAR -> town != null && town.scanned ? near(town, mob.bar(), 5) : mob.bar();
			// Mostly around the plaza, but now and then a stroll somewhere else in town.
			case SOCIAL -> town != null && town.scanned
					? random.nextInt(3) == 0 ? town.randomOpenNear(mob.blockPosition(), 40, random) : town.randomOpenNear(mob.plaza(), 12, random)
					: mob.plaza();
			case FESTIVAL -> town != null && town.scanned ? town.randomOpenNear(mob.plaza(), 10, random) : mob.plaza();
			case PLAY -> town != null && town.scanned ? town.randomOpenNear(mob.plaza(), 16, random) : mob.plaza();
		};
	}

	private BlockPos near(Town town, BlockPos center, int radius) {
		BlockPos best = center;
		for (int i = 0; i < 6; i++) {
			BlockPos spot = town.indoor.isEmpty() ? center : town.indoor.get(mob.getRandom().nextInt(town.indoor.size()));
			if (spot.closerThan(center, radius) && town.reachable(spot)) {
				return spot;
			}
		}
		return best;
	}

	@Override
	public void tick() {
		if (--recheck <= 0) {
			recheck = 20;
			Activity now = activityFor(mob);
			if (now != activity || target == null) {
				if (activity == Activity.SLEEP && mob.isSleeping()) {
					mob.stopSleeping();
				}
				if (activity == Activity.MARKET && now != Activity.MARKET) {
					mob.holdWorkItem();
				}
				activity = now;
				target = targetFor(now);
				resetProgress();
				if (now == Activity.MARKET && mob.job().marketer) {
					mob.holdWares();
				}
			}
		}
		if (mob.isSleeping()) {
			return;
		}
		double distance = Math.sqrt(mob.distanceToSqr(target.getX() + 0.5, target.getY(), target.getZ() + 0.5));
		double arrive = activity == Activity.SLEEP || activity == Activity.HOME ? 1.8 : activity == Activity.WORK || activity == Activity.MARKET ? 2.5 : 3.5;
		if (sideTrip > 0) {
			sideTrip--;
			if (!mob.getNavigation().isDone()) {
				return;
			}
			sideTrip = 0;
			pathCooldown = 0;
		}
		if (distance > arrive) {
			walkTo(distance);
			return;
		}
		stuckTicks = 0;
		failures = 0;
		stillChecks = 0;
		climbed = false;
		atTarget();
	}

	private void resetProgress() {
		pathCooldown = 0;
		stuckTicks = 0;
		failures = 0;
		stillChecks = 0;
		sideTrip = 0;
		climbed = false;
		lastPos = null;
		lastDistance = Double.MAX_VALUE;
	}

	private void walkTo(double distance) {
		double speed = activity == Activity.PLAY ? 1.15 : activity == Activity.SHELTER ? 1.25 : 0.9;
		// Path searches are the most expensive thing a townsperson does, so plan only when the old path ran out (or every
		// few seconds to catch moved doors), never twice within half a second, and spread over ticks by entity id.
		if (pathCooldown > 0) {
			pathCooldown--;
		}
		boolean idle = mob.getNavigation().isDone();
		if (pathCooldown <= 0 && (idle || (mob.tickCount + mob.getId()) % 60 == 0)) {
			boolean found = mob.getNavigation().moveTo(target.getX() + 0.5, target.getY(), target.getZ() + 0.5, speed);
			Path path = mob.getNavigation().getPath();
			// A path that stops short is fine if it gets us a good bit closer (the target is just far away); one that
			// ends about where we already are means a wall, a locked door or a cliff is in the way.
			boolean useful = found && path != null && (path.canReach() || path.getDistToTarget() < distance - 3);
			pathCooldown = useful ? 10 : 40 + mob.getRandom().nextInt(20);
			if (!useful) {
				blocked();
				return;
			}
			// The first step of a route is the block we're standing in. Don't insist on reaching its exact middle:
			// a candle or a flower pot there (on a table, say) would stop us for good.
			if (path.getNextNodeIndex() == 0 && path.getNodeCount() > 1 && path.getNodePos(0).equals(mob.blockPosition())) {
				path.advance();
			}
		}
		// Walking into something (a crowd, a fence corner, a table)? Notice when we've hardly moved for 3 seconds.
		if ((mob.tickCount + mob.getId()) % 20 == 0) {
			net.minecraft.world.phys.Vec3 here = mob.position();
			if (lastPos != null && here.distanceToSqr(lastPos) < 0.25) {
				if (++stillChecks >= 3) {
					stillChecks = 0;
					blocked();
				}
			} else {
				stillChecks = 0;
			}
			lastPos = here;
		}
		// Getting nowhere? After half a minute out of everyone's sight, just be there.
		if (distance < lastDistance - 0.5) {
			lastDistance = distance;
			stuckTicks = 0;
		} else if (++stuckTicks > 600 && !watched()) {
			arrive();
		}
	}

	/** The way to the target is blocked. Try something else, depending on how often it has happened. */
	private void blocked() {
		Town town = mob.town();
		if (failures++ == 0) {
			blockedSince = mob.tickCount;
		}
		// Nobody looking and stuck for 10 seconds: just be there. Still stuck after half a minute of trying: be there
		// anyway, even if someone sees it (better than standing in a sealed loft all game).
		if (failures >= 3 && mob.tickCount - blockedSince > 200 && (!watched() || mob.tickCount - blockedSince > 600)) {
			arrive();
			return;
		}
		// No route at all, not even a step: the trouble is where we stand (in a cauldron, on a cluttered table, in a
		// ditch), not where we're going.
		Path path = mob.getNavigation().getPath();
		boolean noRoute = path == null || (path.getNodeCount() <= 1 && !path.canReach());
		// Swimming and can't find a way out of the water, hanging on a ladder that leads nowhere, wedged against a
		// ceiling, or nowhere to step at all: climb out to the nearest dry spot to stand.
		if (!climbed && failures >= 2 && (mob.isInWater() || mob.onClimbable() || !mob.level().noCollision(mob, mob.getBoundingBox().deflate(0.05))
				|| failures >= 3 && noRoute) && climbOut()) {
			return;
		}
		boolean anySpot = activity == Activity.SOCIAL || activity == Activity.PLAY || activity == Activity.FESTIVAL || activity == Activity.BAR;
		if (anySpot && !noRoute && town != null && town.scanned) {
			// Any spot will do: forget this one and pick another.
			town.markUnreachable(target);
			target = targetFor(activity);
			pathCooldown = 0;
			lastDistance = Double.MAX_VALUE;
			return;
		}
		if (failures >= 4 && !noRoute && town != null && town.scanned) {
			// Home or work can't be reached from here (a sealed room, a wall where the door used to be): move.
			town.markUnreachable(target);
			if (activity == Activity.HOME || activity == Activity.SLEEP || activity == Activity.SHELTER) {
				mob.moveHome(town);
			} else if (activity == Activity.WORK || activity == Activity.MARKET) {
				mob.moveWork(town);
			}
			BlockPos old = target;
			target = targetFor(activity);
			if (!target.equals(old)) {
				failures = 0;
			}
			pathCooldown = 0;
			lastDistance = Double.MAX_VALUE;
			return;
		}
		stepAside(4, 0.7);
	}

	/** Walk a few blocks somewhere else nearby: to get around whatever is in the way, or just to potter about. */
	private void stepAside(int radius, double speed) {
		net.minecraft.world.phys.Vec3 spot = LandRandomPos.getPos(mob, radius, 2);
		if (spot != null && mob.getNavigation().moveTo(spot.x, spot.y, spot.z, speed)) {
			sideTrip = 80;
		}
	}

	/** Hop to the nearest spot within 4 blocks with solid ground and room to stand, out of the water. */
	private boolean climbOut() {
		BlockPos here = mob.blockPosition();
		BlockPos best = null;
		double bestDistance = Double.MAX_VALUE;
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		for (int dx = -4; dx <= 4; dx++) {
			for (int dz = -4; dz <= 4; dz++) {
				for (int dy = -2; dy <= 3; dy++) {
					pos.set(here.getX() + dx, here.getY() + dy, here.getZ() + dz);
					double distance = pos.distSqr(here);
					if (distance < bestDistance && (dx != 0 || dz != 0 || dy != 0) && standable(pos)) {
						bestDistance = distance;
						best = pos.immutable();
					}
				}
			}
		}
		if (best == null) {
			return false;
		}
		mob.getNavigation().stop();
		mob.snapTo(best.getX() + 0.5, best.getY(), best.getZ() + 0.5, mob.getYRot(), 0);
		pathCooldown = 0;
		climbed = true;
		return true;
	}

	private boolean standable(BlockPos feet) {
		var level = mob.level();
		BlockPos below = feet.below();
		var ground = level.getBlockState(below).getCollisionShape(level, below);
		return !ground.isEmpty() && ground.max(net.minecraft.core.Direction.Axis.Y) >= 0.5 && level.getFluidState(below).isEmpty()
				&& !level.getBlockState(feet).is(net.minecraft.tags.BlockTags.CLIMBABLE) && level.getBlockState(feet).getCollisionShape(level, feet).isEmpty() && level.getFluidState(feet).isEmpty()
				&& level.getBlockState(feet.above()).getCollisionShape(level, feet.above()).isEmpty() && level.getFluidState(feet.above()).isEmpty();
	}

	private void arrive() {
		mob.getNavigation().stop();
		mob.snapTo(target.getX() + 0.5, target.getY(), target.getZ() + 0.5, mob.getYRot(), 0);
		resetProgress();
	}

	private boolean watched() {
		Player player = mob.level().getNearestPlayer(mob, 24.0);
		return player != null && player.hasLineOfSight(mob);
	}

	private void atTarget() {
		var random = mob.getRandom();
		switch (activity) {
			case SLEEP -> mob.tryToSleep();
			case FESTIVAL -> {
				// Dance! Hop and spin to the music.
				if (mob.onGround() && random.nextInt(25) == 0) {
					mob.getJumpControl().jump();
				}
				mob.setYRot(mob.getYRot() + 9f);
				mob.setYBodyRot(mob.getYRot());
				if (mob.tickCount % 30 == 0 && mob.level() instanceof ServerLevel level) {
					level.sendParticles(ParticleTypes.NOTE, mob.getX(), mob.getY() + mob.getBbHeight() + 0.4, mob.getZ(), 1, 0.2, 0.1, 0.2, 1.0);
				}
				wander(random.nextInt(120) == 0);
			}
			case PLAY -> {
				if (mob.onGround() && random.nextInt(40) == 0) {
					mob.getJumpControl().jump();
				}
				wander(random.nextInt(50) == 0); // Tag! Run to another spot.
			}
			case WORK, MARKET -> {
				if (++idleTicks % 80 == 0) {
					mob.swing(net.minecraft.world.InteractionHand.MAIN_HAND, net.minecraft.world.item.component.SwingAnimation.DEFAULT);
					BlockPos work = mob.work();
					mob.getLookControl().setLookAt(work.getX() + 0.5, work.getY() + 0.5, work.getZ() + 0.5);
				}
				// Potter about the workplace now and then (stall keepers stay close to their stall).
				if (random.nextInt(activity == Activity.MARKET ? 700 : 300) == 0) {
					stepAside(activity == Activity.MARKET ? 2 : 5, 0.6);
				}
				wander(activity == Activity.WORK && random.nextInt(900) == 0);
			}
			case SOCIAL -> wander(random.nextInt(300) == 0);
			case BAR -> {
				if (random.nextInt(400) == 0) {
					stepAside(3, 0.6);
				}
				wander(random.nextInt(500) == 0);
			}
			case HOME -> {
				if (random.nextInt(500) == 0) {
					stepAside(3, 0.5);
				}
			}
			default -> { }
		}
	}

	/** Pick a new spot nearby for the same activity. */
	private void wander(boolean move) {
		if (move) {
			target = targetFor(activity);
			pathCooldown = 0;
			failures = 0;
			lastDistance = Double.MAX_VALUE;
		}
	}
}
