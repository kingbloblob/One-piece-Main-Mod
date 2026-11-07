package com.onepiecemod.fx;

import org.joml.Vector3f;
import org.joml.Vector3fc;

import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * A short-lived, harmless entity that only exists to be drawn: the stretchy arm, fire fist, ice spear
 * and so on of a Devil Fruit move. The damage itself is still done by FruitAbilities; this is just the look.
 *
 * The server spawns it (see MoveFx), every nearby player's game draws it with MoveRenderer, and it
 * removes itself after its lifetime. It is never saved with the world.
 */
public class MoveEffectEntity extends Entity {
	private static final EntityDataAccessor<Integer> STYLE = SynchedEntityData.defineId(MoveEffectEntity.class, EntityDataSerializers.INT);
	private static final EntityDataAccessor<Integer> COLOR = SynchedEntityData.defineId(MoveEffectEntity.class, EntityDataSerializers.INT);
	private static final EntityDataAccessor<Integer> COLOR2 = SynchedEntityData.defineId(MoveEffectEntity.class, EntityDataSerializers.INT);
	/** Where the move goes, measured from this entity: direction times length. */
	private static final EntityDataAccessor<Vector3fc> REACH = SynchedEntityData.defineId(MoveEffectEntity.class, EntityDataSerializers.VECTOR3);
	private static final EntityDataAccessor<Float> SIZE = SynchedEntityData.defineId(MoveEffectEntity.class, EntityDataSerializers.FLOAT);
	private static final EntityDataAccessor<Integer> LIFE = SynchedEntityData.defineId(MoveEffectEntity.class, EntityDataSerializers.INT);
	/** Ticks to wait before the shape shows up (an explosion waits for the ball that causes it). */
	private static final EntityDataAccessor<Integer> DELAY = SynchedEntityData.defineId(MoveEffectEntity.class, EntityDataSerializers.INT);
	/** The entity id of whoever used the move, so arms and auras can follow them. -1 for none. */
	private static final EntityDataAccessor<Integer> OWNER = SynchedEntityData.defineId(MoveEffectEntity.class, EntityDataSerializers.INT);
	private static final EntityDataAccessor<Boolean> HAS_TRAIL = SynchedEntityData.defineId(MoveEffectEntity.class, EntityDataSerializers.BOOLEAN);
	private static final EntityDataAccessor<ParticleOptions> TRAIL = SynchedEntityData.defineId(MoveEffectEntity.class, EntityDataSerializers.PARTICLE);

	public MoveEffectEntity(EntityType<? extends MoveEffectEntity> type, Level level) {
		super(type, level);
		this.noPhysics = true;
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		builder.define(STYLE, 0);
		builder.define(COLOR, 0xFFFFFFFF);
		builder.define(COLOR2, 0xFFFFFFFF);
		builder.define(REACH, new Vector3f(0, 0, 1));
		builder.define(SIZE, 1.0f);
		builder.define(LIFE, 10);
		builder.define(DELAY, 0);
		builder.define(OWNER, -1);
		builder.define(HAS_TRAIL, false);
		builder.define(TRAIL, ParticleTypes.CRIT);
	}

	// ---- Set up by MoveFx on the server ----

	public void setup(MoveStyle style, int color, int color2, Vec3 reach, float size, int life, Entity owner) {
		entityData.set(STYLE, style.ordinal());
		entityData.set(COLOR, color);
		entityData.set(COLOR2, color2);
		entityData.set(REACH, new Vector3f((float) reach.x, (float) reach.y, (float) reach.z));
		entityData.set(SIZE, size);
		entityData.set(LIFE, Math.max(1, life));
		entityData.set(OWNER, owner != null ? owner.getId() : -1);
	}

	/** Waits this many ticks before showing up. */
	public void delay(int ticks) {
		entityData.set(DELAY, Math.max(0, ticks));
	}

	public int delayTicks() {
		return entityData.get(DELAY);
	}

	public void setTrail(ParticleOptions particle) {
		entityData.set(TRAIL, particle);
		entityData.set(HAS_TRAIL, true);
	}

	// ---- Read by the renderer ----

	public MoveStyle style() {
		return MoveStyle.byId(entityData.get(STYLE));
	}

	public int color() {
		return entityData.get(COLOR);
	}

	public int color2() {
		return entityData.get(COLOR2);
	}

	public Vector3fc reach() {
		return entityData.get(REACH);
	}

	public float size() {
		return entityData.get(SIZE);
	}

	public int life() {
		return entityData.get(LIFE);
	}

	public Entity owner() {
		int id = entityData.get(OWNER);
		return id >= 0 ? level().getEntity(id) : null;
	}

	/**
	 * How far along its path a flying shape (fist, orb, spear) is, from 0 at the start to 1 when it arrives.
	 * Shapes that don't fly return 1.
	 */
	public static float travel(MoveStyle style, float age, int life) {
		float flight = switch (style) {
			case FIST, ORB -> 0.45f;
			case SPEAR -> 0.3f;
			case ARM -> 0.3f;
			default -> 0f;
		};
		if (flight <= 0) {
			return 1;
		}
		float t = Mth.clamp(age / (life * flight), 0, 1);
		return style == MoveStyle.ARM ? t : 1 - (1 - t) * (1 - t); // Arms shoot out evenly, the rest slow down a little at the end.
	}

	// ---- Life ----

	@Override
	public void tick() {
		super.tick();
		if (level() instanceof ServerLevel) {
			if (tickCount >= life() + delayTicks() + 2) {
				discard();
			}
			return;
		}
		// On the client: leave a trail of particles behind flying shapes.
		if (entityData.get(HAS_TRAIL) && tickCount <= life()) {
			MoveStyle style = style();
			float t = travel(style, tickCount, life());
			Vector3fc r = reach();
			Vec3 head = position().add(r.x() * t, r.y() * t, r.z() * t);
			int count = style == MoveStyle.PILLAR || style == MoveStyle.TORNADO || style == MoveStyle.RING ? 4 : 2;
			for (int i = 0; i < count; i++) {
				double spread = size() * 0.4;
				level().addParticle(entityData.get(TRAIL),
						head.x + (random.nextDouble() - 0.5) * spread,
						head.y + (random.nextDouble() - 0.5) * spread,
						head.z + (random.nextDouble() - 0.5) * spread,
						0, 0.02, 0);
			}
		}
	}

	// Seen from as far away as a big mob, even though the entity itself is tiny.
	@Override
	public boolean shouldRenderAtSqrDistance(double distance) {
		return distance < 96 * 96;
	}

	@Override
	public boolean shouldBeSaved() {
		return false;
	}

	@Override
	public boolean isPickable() {
		return false;
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		return false;
	}

	@Override
	public boolean isIgnoringBlockTriggers() {
		return true;
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
	}
}
