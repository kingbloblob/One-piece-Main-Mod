package com.onepiecemod.ship;

import java.util.List;
import java.util.function.BiFunction;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.InterpolationHandler;
import net.minecraft.world.entity.LinearInterpolationHandler;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * A sailing ship. While it sails, all its blocks are stored inside this one entity (see ShipLayout)
 * and drawn by ShipRenderer. When you drop anchor, ShipAssembler puts the blocks back into the world.
 *
 * Steering works like a boat: the captain (the first person aboard) uses W/S for speed and A/D to turn.
 * Like boats and horses, the captain's own game moves the ship, so it feels smooth even on a laggy server.
 */
public class ShipEntity extends Entity {
	// ---- How ships handle. Change these to make ships faster or slower. ----
	private static final double BASE_SPEED = 0.12;       // blocks per tick with no sails at all (a rowing boat)
	private static final double SPEED_PER_SAIL = 0.035;  // extra top speed from sails (more sails, less extra each)
	private static final double MAX_SPEED = 0.55;        // the fastest any ship can go (about 11 blocks a second)
	private static final float TURN_SPEED = 2.5f;        // degrees per tick at full turn

	/**
	 * How much wind there is at a spot, from 0 (none) to 1 (normal). Only sails need wind; with no wind
	 * a ship can still crawl along at BASE_SPEED. Other parts of the mod (like the Calm Belt) replace this.
	 */
	public static BiFunction<Level, BlockPos, Double> windAt = (level, pos) -> 1.0;

	/**
	 * Extra movement each tick from the sea itself, like storm winds or a whirlpool's pull.
	 * Runs on whichever game is steering the ship. Sea events (com.onepiecemod.weather) replace this.
	 */
	public static java.util.function.Function<ShipEntity, Vec3> seaPush = ship -> Vec3.ZERO;

	// ---- Synced from the server: how this ship handles right now, and Coup de Burst. ----
	private static final EntityDataAccessor<Float> DATA_SPEED = SynchedEntityData.defineId(ShipEntity.class, EntityDataSerializers.FLOAT);
	private static final EntityDataAccessor<Float> DATA_TURN = SynchedEntityData.defineId(ShipEntity.class, EntityDataSerializers.FLOAT);
	private static final EntityDataAccessor<Integer> DATA_BURST = SynchedEntityData.defineId(ShipEntity.class, EntityDataSerializers.INT);
	/** Sabaody bubble coating: ticks of air left under the sea, 0 = not coated. See deepsea.ShipCoating. */
	private static final EntityDataAccessor<Integer> DATA_COATING = SynchedEntityData.defineId(ShipEntity.class, EntityDataSerializers.INT);

	/** Coup de Burst: how long the flight lasts, how fast, and the arc (blocks per tick up at the start, less each tick). */
	public static final int BURST_TICKS = 60;
	private static final double BURST_SPEED = 1.5;
	private static final double BURST_LIFT = 0.75;
	private static final double BURST_GRAVITY = 0.03;
	/** The game time the last Coup de Burst started (on whichever game steers the ship). */
	private long burstStart = -1000;

	private ShipLayout layout = ShipLayout.EMPTY;
	private double speed;
	private float turnLastTick;
	private long dockConfirmUntil;

	/** Steering for ships with no captain (Marine and pirate ships at sea). Set by shipcombat.ShipBrain. */
	public float aiForward;
	public float aiTurn;
	/** True once the hull is broken: the ship stops floating and goes down. See shipcombat.ShipHull. */
	public boolean sinking;

	public ShipEntity(EntityType<? extends ShipEntity> type, Level level) {
		super(type, level);
	}

	public ShipLayout getLayout() {
		return layout;
	}

	public void setLayout(ShipLayout layout) {
		this.layout = layout;
		refreshDimensions();
	}

	@Override
	public void defineSynchedData(SynchedEntityData.Builder builder) {
		// The blocks are sent with ShipPayloads.ShipBlocks instead, because there can be thousands.
		builder.define(DATA_SPEED, 1f);
		builder.define(DATA_TURN, 1f);
		builder.define(DATA_BURST, 0);
		builder.define(DATA_COATING, 0);
	}

	/** Ticks of bubble coating left under the sea (0 = none). Coated ships can dive, see deepsea.ShipDive. */
	public int coating() {
		return entityData.get(DATA_COATING);
	}

	/** Server: set the bubble coating (deepsea.ShipCoating). */
	public void setCoating(int ticks) {
		entityData.set(DATA_COATING, Math.max(0, ticks));
	}

	/** Top speed multiplier: sail upgrades, a Navigator in the crew, chain shot tangling the rigging... */
	public float speedFactor() {
		return entityData.get(DATA_SPEED);
	}

	/** Turning speed multiplier. */
	public float turnFactor() {
		return entityData.get(DATA_TURN);
	}

	/** Server: set how this ship handles. Sent to the captain's game, which does the steering. */
	public void setHandling(float speedFactor, float turnFactor) {
		if (speedFactor != speedFactor() || turnFactor != turnFactor()) {
			entityData.set(DATA_SPEED, speedFactor);
			entityData.set(DATA_TURN, turnFactor);
		}
	}

	/** Server: launch a Coup de Burst now. The game steering the ship flies it (see tick). */
	public void coupDeBurst() {
		entityData.set(DATA_BURST, entityData.get(DATA_BURST) + 1);
	}

	/** Ticks into the current Coup de Burst, or -1 if the ship isn't flying. */
	public int burstTick() {
		long ticks = level().getGameTime() - burstStart;
		return ticks >= 0 && ticks < BURST_TICKS ? (int) ticks : -1;
	}

	@Override
	public void onSyncedDataUpdated(EntityDataAccessor<?> accessor) {
		super.onSyncedDataUpdated(accessor);
		if (DATA_BURST.equals(accessor)) {
			// A new burst (not the count the server sends with the ship when a player first comes close).
			if (!level().isClientSide() || tickCount > 0) {
				burstStart = level().getGameTime();
			}
		}
	}

	/** How far the ship has turned since it was built, in degrees. Used to turn every block. */
	public float rotationSinceBuilt(float partialTick) {
		return getViewYRot(partialTick) - layout.bow.toYRot();
	}

	/** Turns a position on the ship by the ship's current heading. */
	public Vec3 rotate(Vec3 local, float partialTick) {
		float radians = rotationSinceBuilt(partialTick) * Mth.DEG_TO_RAD;
		float cos = Mth.cos(radians);
		float sin = Mth.sin(radians);
		return new Vec3(local.x * cos - local.z * sin, local.y, local.x * sin + local.z * cos);
	}

	/**
	 * How far along a line of sight (from eye, along the unit vector look) the first block of this ship is, or -1 if
	 * the line misses every block within reach. Used to pick big ships by their real shape, not their square box.
	 */
	public double blockHitDistance(Vec3 eye, Vec3 look, double reach, float partialTick) {
		float radians = -rotationSinceBuilt(partialTick) * Mth.DEG_TO_RAD;
		float cos = Mth.cos(radians), sin = Mth.sin(radians);
		Vec3 rel = eye.subtract(getPosition(partialTick));
		Vec3 start = new Vec3(rel.x * cos - rel.z * sin, rel.y, rel.x * sin + rel.z * cos);
		Vec3 direction = new Vec3(look.x * cos - look.z * sin, look.y, look.x * sin + look.z * cos);
		BlockPos last = null;
		for (double distance = 0; distance <= reach; distance += 0.05) {
			Vec3 point = start.add(direction.scale(distance));
			BlockPos cell = BlockPos.containing(point.x + 0.5, point.y, point.z + 0.5);
			if (cell.equals(last)) {
				continue;
			}
			last = cell;
			if (layout.indexAt(cell) >= 0) {
				return distance;
			}
		}
		return -1;
	}

	// ---- Size: the hit box covers the whole ship ----

	@Override
	public EntityDimensions getDimensions(Pose pose) {
		if (layout.size() == 0) {
			return super.getDimensions(pose);
		}
		int width = Math.max(layout.max.getX() - layout.min.getX(), layout.max.getZ() - layout.min.getZ()) + 1;
		// Two extra blocks on top so the crew's heads are inside the box: the game only lets you
		// right-click the ship you ride (chests, dropping anchor) while your eyes are inside its box.
		int height = layout.max.getY() - layout.min.getY() + 1 + 2;
		return EntityDimensions.fixed(width, height);
	}

	/**
	 * The game checks every block inside this box for water each tick. The ship floats itself (findWaterSurface), so a
	 * one-block column down its middle is enough to know it's in water; the whole hull made big sea battles slow.
	 */
	@Override
	public AABB getFluidInteractionBox() {
		return new AABB(getX() - 0.5, getY(), getZ() - 0.5, getX() + 0.5, getY() + layout.waterline + 1, getZ() + 0.5);
	}

	// ---- Sailing ----

	@Override
	public void tick() {
		super.tick();
		com.onepiecemod.sound.WorldSounds.tickShip(this); // Creaks, sails and wake (server only).
		ShipDecks.track(this);
		com.onepiecemod.deepsea.ShipDive.tick(this); // Coating wear and depth warnings (server only).
		turnLastTick = 0;

		if (!isLocalInstanceAuthoritative()) {
			// Someone else's game is steering this ship: just follow the positions it sends.
			return;
		}

		if (sinking) {
			// Going down: drift slowly to the sea floor (ShipHull removes the ship when it gets there).
			setDeltaMovement(0, -0.06, 0);
			sail(getYRot(), getDeltaMovement());
			return;
		}

		float forward = aiForward;
		float turn = aiTurn;
		boolean manned = aiForward != 0 || aiTurn != 0;
		if (getControllingPassenger() instanceof Player captain) {
			forward = captain.zza; // W = 1, S = -1
			turn = captain.xxa;    // A = 1, D = -1
			manned = true;
		}
		if (!manned) {
			// Nobody at the helm: the anchor holds the ship where it is.
			speed = 0;
		}

		// Sails make the ship faster, but a big heavy hull needs more of them.
		double wind = windAt.apply(level(), blockPosition());
		// Upgrades, crew and chain shot change this (see speedFactor, set by shipcombat.ShipCrewHelp).
		double sailSpeed = Math.min(MAX_SPEED, BASE_SPEED + SPEED_PER_SAIL * Math.sqrt(layout.sails) * wind);
		// Submarines run on an engine; under the sea sails catch only the currents (deepsea.ShipDive).
		double topSpeed = com.onepiecemod.deepsea.ShipDive.speedFactor(this, sailSpeed, BASE_SPEED) * speedFactor();
		double acceleration = 0.004 + 0.012 * Math.min(1.0, layout.sails * 6.0 / Math.max(1, layout.size()));
		double target = forward > 0 ? topSpeed : forward < 0 ? -topSpeed * 0.3 : 0;
		if (speed < target) {
			speed = Math.min(target, speed + acceleration);
		} else if (speed > target) {
			speed = Math.max(target, speed - acceleration * 1.5);
		}

		// Ships turn slower when they barely move, like a real ship.
		float turnAmount = turn * TURN_SPEED * turnFactor() * (float) Math.min(1.0, 0.35 + Math.abs(speed) / topSpeed);
		float newYaw = getYRot() - turnAmount;
		if (turnAmount != 0 && layout.size() > 0 && overlaps(position(), newYaw) > overlaps(position(), getYRot())) {
			turnAmount = 0; // Turning would swing the hull into a rock or a pier.
			newYaw = getYRot();
		}
		setYRot(newYaw);
		turnLastTick = -turnAmount;

		// Float: keep the waterline at the sea's surface. With no water underneath, fall (or sit on the beach).
		double ySpeed;
		Double surface = findWaterSurface();
		int burst = burstTick();
		if (burst >= 0) {
			// Coup de Burst: the whole ship leaps out of the sea and flies, then splashes down.
			speed = Math.max(speed, topSpeed);
			ySpeed = BURST_LIFT - BURST_GRAVITY * burst;
			setDeltaMovement(-Mth.sin(getYRot() * Mth.DEG_TO_RAD) * BURST_SPEED, ySpeed, Mth.cos(getYRot() * Mth.DEG_TO_RAD) * BURST_SPEED);
			if (ySpeed < 0 && surface != null && getY() + layout.waterline <= surface) {
				burstStart = -1000; // Splashdown.
			} else {
				sail(getYRot(), getDeltaMovement());
				return;
			}
		}
		Double dive = com.onepiecemod.deepsea.ShipDive.verticalSpeed(this); // Submarines and coated ships under the sea.
		if (dive != null) {
			ySpeed = dive;
		} else if (surface != null) {
			ySpeed = Mth.clamp((surface - layout.waterline - getY()) * 0.25, -0.2, 0.2);
		} else {
			ySpeed = getDeltaMovement().y - 0.04;
			speed *= 0.8; // Aground: you won't get far on sand.
		}

		float yaw = getYRot() * Mth.DEG_TO_RAD;
		Vec3 heading = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
		setDeltaMovement(heading.x * speed, ySpeed, heading.z * speed);
		if (manned) {
			setDeltaMovement(getDeltaMovement().add(seaPush.apply(this))); // Storms and whirlpools can't drag an anchored ship.
		}
		sail(getYRot(), getDeltaMovement());

		if (horizontalCollision) {
			speed *= 0.5; // Bump!
		}
	}

	// ---- Bumping into things ----
	// The game's own collision uses the entity's box, which for a ship is a big square (the longest side, both ways).
	// A long, thin ship would then hit piers and beaches far off to its side. So ships check their real hull instead.

	/** How far above the waterline hull blocks still count for bumping (piers and rocks stick up a little). */
	private static final double PROBE_ABOVE_WATER = 2.5;

	private ShipLayout probedLayout;
	private boolean probedDiving;
	private List<Vec3> probes = List.of();

	/** The hull blocks that can touch land or another ship: those near the waterline with an open side or nothing below. */
	private List<Vec3> probes() {
		// A ship that can dive bumps with her whole hull: under the sea the trench walls are all around her.
		boolean diving = com.onepiecemod.deepsea.ShipDive.canDive(this);
		if (probedLayout != layout || probedDiving != diving) {
			probedLayout = layout;
			probedDiving = diving;
			List<Vec3> result = new java.util.ArrayList<>();
			for (ShipLayout.ShipBlock block : layout.blocks) {
				BlockPos p = block.pos();
				if (!diving && p.getY() > layout.waterline + PROBE_ABOVE_WATER) {
					continue;
				}
				boolean outside = layout.indexAt(p.below()) < 0 || layout.indexAt(p.north()) < 0 || layout.indexAt(p.south()) < 0
						|| layout.indexAt(p.east()) < 0 || layout.indexAt(p.west()) < 0;
				if (outside) {
					result.add(new Vec3(p.getX(), p.getY() + 0.5, p.getZ()));
				}
			}
			probes = result;
		}
		return probes;
	}

	/** Where a hull probe would be in the world if the ship stood at `at`, heading `yaw`. */
	private Vec3 probeAt(Vec3 local, Vec3 at, float yaw) {
		float radians = (yaw - layout.bow.toYRot()) * Mth.DEG_TO_RAD;
		float cos = Mth.cos(radians), sin = Mth.sin(radians);
		return at.add(local.x * cos - local.z * sin, local.y, local.x * sin + local.z * cos);
	}

	/** How many hull blocks would be inside solid ground (or another ship) with the ship at `at`, heading `yaw`. */
	public int overlaps(Vec3 at, float yaw) {
		// Turning and sailing ask about the same spot several times a tick: answer those from memory.
		for (int i = 0; i < OVERLAP_MEMORY; i++) {
			if (overlapTick[i] == tickCount && overlapLayout[i] == layout && overlapYaw[i] == yaw
					&& overlapX[i] == at.x && overlapY[i] == at.y && overlapZ[i] == at.z) {
				return overlapCount[i];
			}
		}
		int count = countOverlaps(at, yaw);
		int slot = overlapNext;
		overlapNext = (overlapNext + 1) % OVERLAP_MEMORY;
		overlapTick[slot] = tickCount;
		overlapLayout[slot] = layout;
		overlapYaw[slot] = yaw;
		overlapX[slot] = at.x;
		overlapY[slot] = at.y;
		overlapZ[slot] = at.z;
		overlapCount[slot] = count;
		return count;
	}

	private static final int OVERLAP_MEMORY = 4;
	private final int[] overlapTick = { -1, -1, -1, -1 };
	private final ShipLayout[] overlapLayout = new ShipLayout[OVERLAP_MEMORY];
	private final float[] overlapYaw = new float[OVERLAP_MEMORY];
	private final double[] overlapX = new double[OVERLAP_MEMORY], overlapY = new double[OVERLAP_MEMORY], overlapZ = new double[OVERLAP_MEMORY];
	private final int[] overlapCount = new int[OVERLAP_MEMORY];
	private int overlapNext;

	/** A box around everywhere this ship's blocks can be, whichever way it faces (its hit box misses the corners when turned). */
	private AABB hullReach() {
		double dx = Math.max(Math.abs(layout.min.getX()), Math.abs(layout.max.getX())) + 1;
		double dz = Math.max(Math.abs(layout.min.getZ()), Math.abs(layout.max.getZ())) + 1;
		double r = Math.sqrt(dx * dx + dz * dz);
		return new AABB(getX() - r, getY() + layout.min.getY() - 1, getZ() - r, getX() + r, getY() + layout.max.getY() + 2, getZ() + r);
	}

	private int countOverlaps(Vec3 at, float yaw) {
		List<ShipEntity> others = level().getEntitiesOfClass(ShipEntity.class, getBoundingBox().move(at.subtract(position())).inflate(2),
				other -> other != this && !other.sinking && !other.isRemoved());
		// Each other ship's box (a probe outside it can't touch that ship) and its turn, worked out once instead of per probe.
		int n = others.size();
		AABB[] boxes = new AABB[n];
		float[] otherCos = new float[n], otherSin = new float[n];
		for (int k = 0; k < n; k++) {
			ShipEntity other = others.get(k);
			boxes[k] = other.hullReach();
			float radians = -other.rotationSinceBuilt(1.0f) * Mth.DEG_TO_RAD;
			otherCos[k] = Mth.cos(radians);
			otherSin[k] = Mth.sin(radians);
		}
		float radians = (yaw - layout.bow.toYRot()) * Mth.DEG_TO_RAD;
		float cos = Mth.cos(radians), sin = Mth.sin(radians);
		int count = 0;
		BlockPos.MutableBlockPos cell = new BlockPos.MutableBlockPos();
		for (Vec3 local : probes()) {
			double wx = at.x + local.x * cos - local.z * sin, wy = at.y + local.y, wz = at.z + local.x * sin + local.z * cos;
			cell.set(wx, wy, wz);
			net.minecraft.world.level.block.state.BlockState state = level().getBlockState(cell);
			if (!state.canBeReplaced() && !state.getCollisionShape(level(), cell).isEmpty()) {
				count++;
				continue;
			}
			for (int k = 0; k < n; k++) {
				if (!boxes[k].contains(wx, wy, wz)) {
					continue;
				}
				ShipEntity other = others.get(k);
				double rx = wx - other.getX(), ry = wy - other.getY(), rz = wz - other.getZ();
				if (other.layout.indexAt(BlockPos.containing(rx * otherCos[k] - rz * otherSin[k] + 0.5, ry, rx * otherSin[k] + rz * otherCos[k] + 0.5)) >= 0) {
					count++;
					break;
				}
			}
		}
		return count;
	}

	/** True if one of this ship's blocks is at that spot in the world right now. */
	public boolean blockAt(Vec3 world) {
		float radians = -rotationSinceBuilt(1.0f) * Mth.DEG_TO_RAD;
		float cos = Mth.cos(radians), sin = Mth.sin(radians);
		Vec3 rel = world.subtract(position());
		return layout.indexAt(BlockPos.containing(rel.x * cos - rel.z * sin + 0.5, rel.y, rel.x * sin + rel.z * cos + 0.5)) >= 0;
	}

	/** Another ship this one would be touching if it moved by `offset`, or null. Used for ramming (shipcombat). */
	public ShipEntity shipTouching(Vec3 offset) {
		Vec3 at = position().add(offset);
		List<ShipEntity> others = level().getEntitiesOfClass(ShipEntity.class, getBoundingBox().move(offset).inflate(2),
				other -> other != this && !other.sinking && !other.isRemoved());
		if (others.isEmpty()) {
			return null;
		}
		for (Vec3 local : probes()) {
			Vec3 world = probeAt(local, at, getYRot());
			for (ShipEntity other : others) {
				if (other.blockAt(world)) {
					return other;
				}
			}
		}
		return null;
	}

	/**
	 * Moves the ship by `motion`, stopping short of land, piers and other ships. Slides along the side of a pier
	 * when only one direction is blocked. Sets horizontalCollision and onGround like the game's own move would.
	 */
	private void sail(float yaw, Vec3 motion) {
		if (layout.size() == 0) {
			move(MoverType.SELF, motion);
			return;
		}
		Vec3 from = position();
		int stuck = overlaps(from, yaw); // Already touching something (built against the sea floor): don't get worse.
		double x = from.x + motion.x;
		double z = from.z + motion.z;
		boolean bumped = false;
		if ((motion.x != 0 || motion.z != 0) && overlaps(new Vec3(x, from.y, z), yaw) > stuck) {
			bumped = true;
			if (overlaps(new Vec3(x, from.y, from.z), yaw) <= stuck) {
				z = from.z;
			} else if (overlaps(new Vec3(from.x, from.y, z), yaw) <= stuck) {
				x = from.x;
			} else {
				x = from.x;
				z = from.z;
			}
		}
		double y = from.y + motion.y;
		boolean grounded = false;
		if (motion.y < 0 && overlaps(new Vec3(x, y, z), yaw) > overlaps(new Vec3(x, from.y, z), yaw)) {
			y = from.y;
			grounded = true;
		} else if (motion.y > 0 && probedDiving && overlaps(new Vec3(x, y, z), yaw) > overlaps(new Vec3(x, from.y, z), yaw)) {
			y = from.y; // Rising into a rock overhang under the sea.
		}
		setPos(x, y, z);
		if (grounded) {
			setDeltaMovement(getDeltaMovement().multiply(1, 0, 1));
		}
		horizontalCollision = bumped;
		setOnGround(grounded);
	}

	/** The height of the water's surface under the middle of the ship, or null if there is no water. */
	private Double findWaterSurface() {
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		int top = Mth.floor(getY() + layout.waterline) + 2;
		int bottom = Mth.floor(getY()) - 1;
		for (int y = top; y >= bottom; y--) {
			pos.set(getX(), y, getZ());
			FluidState fluid = level().getFluidState(pos);
			if (fluid.is(FluidTags.WATER)) {
				return y + (double) fluid.getHeight(level(), pos);
			}
		}
		return null;
	}

	// ---- People aboard ----

	@Override
	public LivingEntity getControllingPassenger() {
		return getFirstPassenger() instanceof Player captain ? captain : null;
	}

	@Override
	public boolean canAddPassenger(Entity passenger) {
		// Only the captain rides (at the wheel). Everyone else walks the deck (see ShipDecks).
		return getPassengers().isEmpty() && !layout.seats.isEmpty();
	}

	@Override
	public void positionRider(Entity passenger, MoveFunction moveFunction) {
		int seat = getPassengers().indexOf(passenger);
		if (seat < 0 || seat >= layout.seats.size()) {
			return;
		}
		Vec3 spot = rotate(layout.seats.get(seat), 1.0f);
		moveFunction.accept(passenger, getX() + spot.x, getY() + spot.y, getZ() + spot.z);
		// Turn the crew along with the ship.
		passenger.setYRot(passenger.getYRot() + turnLastTick);
		passenger.setYHeadRot(passenger.getYHeadRot() + turnLastTick);
	}

	@Override
	public Vec3 getDismountLocationForPassenger(LivingEntity passenger) {
		// Hop off where you stand. While sailing that means into the sea!
		return passenger.position();
	}

	/** Right-clicking the ship. ShipFeature hooks this up through Fabric's UseEntityCallback. */
	public InteractionResult onRightClick(Player player, InteractionHand hand) {
		if (hand != InteractionHand.MAIN_HAND) {
			return InteractionResult.PASS;
		}
		if (level().isClientSide()) {
			return InteractionResult.SUCCESS;
		}

		if (aboard(player) != this) {
			boardOnDeck(player);
			player.sendOverlayMessage(Component.literal(getControllingPassenger() == null
					? "Welcome aboard! Right-click the Ship's Wheel to take the helm." : "Welcome aboard!"));
			return InteractionResult.SUCCESS;
		}

		// On deck, looking at the wheel: take the helm (if nobody has it).
		if (player.getVehicle() != this && ShipInteractions.lookingAtHelm(this, player)) {
			if (getControllingPassenger() != null) {
				player.sendOverlayMessage(Component.literal(getControllingPassenger().getName().getString() + " has the helm."));
			} else if (player.startRiding(this)) {
				player.sendOverlayMessage(Component.literal("Captain! W/S to sail, A/D to turn. Sneak to leave the wheel. Right-click the deck twice to drop anchor."));
			}
			return InteractionResult.SUCCESS;
		}

		// Aboard: open the chest, crafting table or station you're looking at.
		if (player instanceof ServerPlayer serverPlayer && ShipInteractions.tryUse(this, serverPlayer)) {
			return InteractionResult.SUCCESS;
		}

		if (getControllingPassenger() != player) {
			return InteractionResult.PASS;
		}

		// The captain right-clicks twice to drop anchor, so it never happens by accident.
		String battle = com.onepiecemod.shipcombat.ShipCombat.dockBlockedReason(this);
		if (battle == null) {
			battle = com.onepiecemod.deepsea.ShipDive.dockBlockedReason(this);
		}
		if (battle != null) {
			player.sendOverlayMessage(Component.literal(battle).withStyle(ChatFormatting.RED));
		} else if (Math.abs(speed) > 0.05) {
			player.sendOverlayMessage(Component.literal("Slow down before dropping anchor (let go of W)."));
		} else if (level().getGameTime() > dockConfirmUntil) {
			dockConfirmUntil = level().getGameTime() + 60;
			player.sendOverlayMessage(Component.literal("Right-click again to drop anchor and turn the ship back into blocks."));
		} else if (level() instanceof ServerLevel serverLevel) {
			String problem = ShipAssembler.dock(serverLevel, this);
			if (problem != null) {
				player.sendOverlayMessage(Component.literal(problem).withStyle(ChatFormatting.RED));
			}
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public void remove(RemovalReason reason) {
		super.remove(reason);
		ShipDecks.untrack(this);
		if (!level().isClientSide()) {
			ShipInteractions.forget(this);
		}
	}

	// ---- Ships can't be broken by hitting them, only by cannonballs and explosions (see shipcombat.ShipHull) ----

	@Override
	public boolean isPickable() {
		return !isRemoved();
	}

	@Override
	public boolean isPushable() {
		return false;
	}

	/**
	 * On other players' games the ship glides between the positions the server sends, like a boat, instead of jumping.
	 * Packets often arrive in bunches, and a deck that jumps a few blocks at once drops the crew walking on it.
	 */
	@Override
	protected InterpolationHandler createInterpolationHandler() {
		return LinearInterpolationHandler.create(this, 3);
	}

	/**
	 * The server moves a captained ship to where the captain's game says it sailed (ServerGamePacketListenerImpl).
	 * The captain's game already bumped the real hull into the world (see sail), so don't redo it with the ship's box:
	 * that box is a big square and would catch on piers and beaches beside a long, thin hull, and the server would
	 * then pull the ship back every tick.
	 */
	@Override
	public void move(MoverType type, Vec3 movement) {
		if (type == MoverType.PLAYER && !level().isClientSide() && layout.size() > 0) {
			setPos(getX() + movement.x, getY() + movement.y, getZ() + movement.z);
			return;
		}
		super.move(type, movement);
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		return com.onepiecemod.shipcombat.ShipHull.hurt(this, level, source, amount);
	}

	// ---- Saving ----

	@Override
	public void addAdditionalSaveData(ValueOutput output) {
		output.store("Layout", ShipLayout.CODEC, layout);
		output.putDouble("Speed", speed);
		output.putInt("Coating", coating());
	}

	@Override
	public void readAdditionalSaveData(ValueInput input) {
		setLayout(input.read("Layout", ShipLayout.CODEC).orElse(ShipLayout.EMPTY));
		speed = input.getDoubleOr("Speed", 0);
		setCoating(input.getIntOr("Coating", 0));
	}

	/** Climb aboard: land on deck near the wheel, free to walk around while she sails. */
	public void boardOnDeck(Entity entity) {
		List<Vec3> spots = seatPositions();
		if (spots.isEmpty()) {
			return;
		}
		Vec3 spot = spots.get(spots.size() > 1 ? 1 + random.nextInt(Math.min(4, spots.size() - 1)) : 0);
		entity.stopRiding();
		entity.teleportTo(spot.x, spot.y + 0.05, spot.z);
		entity.resetFallDistance();
	}

	/** The ship a player (or anyone) is aboard right now, at the wheel or walking the deck, or null. */
	public static ShipEntity aboard(Entity entity) {
		return ShipDecks.shipOf(entity);
	}

	/** Every player aboard this ship: the captain at the wheel and everyone on deck. */
	public static List<ServerPlayer> playersAboard(ShipEntity ship) {
		List<ServerPlayer> players = new java.util.ArrayList<>();
		for (Entity passenger : ship.getPassengers()) {
			if (passenger instanceof ServerPlayer player) {
				players.add(player);
			}
		}
		for (Entity walker : ShipDecks.onDeck(ship)) {
			if (walker instanceof ServerPlayer player) {
				players.add(player);
			}
		}
		return players;
	}

	/** Seat positions in the world right now. Used when docking, to put everyone back on deck. */
	public List<Vec3> seatPositions() {
		return layout.seats.stream().map(seat -> rotate(seat, 1.0f).add(position())).toList();
	}
}
