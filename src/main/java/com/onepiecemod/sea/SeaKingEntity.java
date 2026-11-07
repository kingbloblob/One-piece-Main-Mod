package com.onepiecemod.sea;

import com.onepiecemod.util.Motion;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.BossEvent;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.SmoothSwimmingLookControl;
import net.minecraft.world.entity.ai.control.SmoothSwimmingMoveControl;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RandomSwimmingGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.ai.navigation.WaterBoundPathNavigation;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * A Sea King: a giant sea serpent that lives in deep water and attacks anything that floats above it.
 * It knocks people off their boats and ships, can't leave the water, and drops Sea King Meat.
 * There are a few color variants so they don't all look the same.
 *
 * Taming: beat one down below 25% health, then right-click it with Sea King Bait (1 in 3 bites works).
 * A tamed Sea King follows you through the sea, fights for you, and you can ride it with an empty hand:
 * it swims along the surface, dives when you look down, and keeps you breathing under water.
 */
public class SeaKingEntity extends Monster implements com.onepiecemod.pet.Pet {
	public static final int VARIANTS = 3;
	private static final EntityDataAccessor<Integer> DATA_VARIANT = SynchedEntityData.defineId(SeaKingEntity.class, EntityDataSerializers.INT);
	/** Body styles from the show (see SeaKingModel.createBodyLayer): serpent, horned, whiskered, frilled, toad-headed, armoured. */
	public static final int STYLES = 6;
	public static final String[] STYLE_NAMES = {"Serpent", "Horned", "Whiskered", "Frilled", "Toad-Headed", "Armoured"};
	private static final EntityDataAccessor<Integer> DATA_STYLE = SynchedEntityData.defineId(SeaKingEntity.class, EntityDataSerializers.INT);

	private final ServerBossEvent bossBar = new ServerBossEvent(
			java.util.UUID.randomUUID(), Component.literal("Sea King"), BossEvent.BossBarColor.BLUE, BossEvent.BossBarOverlay.NOTCHED_10);

	private java.util.UUID ownerId;
	private boolean staying;
	/** Which Sea King boss this is (SeaBosses), or "" for an ordinary Sea King. */
	private String seaBoss = "";

	public SeaKingEntity(EntityType<? extends SeaKingEntity> type, Level level) {
		super(type, level);
		// Swims like a dolphin: turns smoothly and moves in 3D through the water.
		this.moveControl = new SmoothSwimmingMoveControl(this, 85, 10, 0.02f, 0.1f, true);
		this.lookControl = new SmoothSwimmingLookControl(this, 10);
		this.xpReward = 40;
		this.entityData.set(DATA_VARIANT, this.random.nextInt(VARIANTS));
		this.entityData.set(DATA_STYLE, this.random.nextInt(STYLES));
		// Sea Kings come in all sizes, like in the show: 80% to 125% of the usual (about 60 to 95 blocks long).
		// Saved with the entity; bosses and the Sea King Lord set their own size afterwards.
		if (!level.isClientSide() && this.getAttribute(Attributes.SCALE) != null) {
			this.getAttribute(Attributes.SCALE).setBaseValue(0.8 + this.random.nextDouble() * 0.45);
		}
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
				.add(Attributes.MAX_HEALTH, 200.0)
				.add(Attributes.ATTACK_DAMAGE, 14.0)
				.add(Attributes.ARMOR, 6.0)
				.add(Attributes.MOVEMENT_SPEED, 1.2)
				.add(Attributes.FOLLOW_RANGE, 48.0)
				.add(Attributes.KNOCKBACK_RESISTANCE, 1.0);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(DATA_VARIANT, 0);
		builder.define(DATA_STYLE, 0);
	}

	public int getVariant() {
		return this.entityData.get(DATA_VARIANT);
	}

	/** Which body style it has (0 to STYLES - 1). */
	public int getStyle() {
		return this.entityData.get(DATA_STYLE);
	}

	public void setStyle(int style) {
		this.entityData.set(DATA_STYLE, Math.floorMod(style, STYLES));
	}

	/** True for the four named sea bosses (SeaBosses). */
	public boolean isSeaBoss() {
		return !seaBoss.isEmpty();
	}

	public String getSeaBoss() {
		return seaBoss;
	}

	/** Makes this Sea King a boss: its id and which texture it wears. */
	public void setSeaBoss(String id, int variant) {
		this.seaBoss = id;
		this.entityData.set(DATA_VARIANT, variant);
		bossBar.setColor(BossEvent.BossBarColor.PURPLE);
	}

	@Override
	protected void registerGoals() {
		this.goalSelector.addGoal(1, new MeleeAttackGoal(this, 1.3, true));
		this.goalSelector.addGoal(2, new com.onepiecemod.pet.PetGoals.FollowOwner<>(this));
		this.goalSelector.addGoal(4, new RandomSwimmingGoal(this, 1.0, 40) {
			@Override
			public boolean canUse() {
				return !staying && super.canUse();
			}
		});
		this.goalSelector.addGoal(5, new RandomLookAroundGoal(this));
		this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
		this.targetSelector.addGoal(2, new com.onepiecemod.pet.PetGoals.DefendOwner<>(this));
		this.targetSelector.addGoal(3, new com.onepiecemod.pet.PetGoals.OwnerAttacks<>(this));
		// Anyone it can see. It can't leave the water, so people on land are safe. A tamed one leaves people alone.
		this.targetSelector.addGoal(4, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false,
				(target, level) -> !isTamed()));
	}

	// ---------- Taming and riding ----------

	@Override
	public java.util.UUID getOwnerId() {
		return ownerId;
	}

	@Override
	public boolean isStaying() {
		return staying;
	}

	@Override
	public void setStaying(boolean staying) {
		this.staying = staying;
	}

	@Override
	public boolean petSwims() {
		return true;
	}

	private int bond; // pet.PetBond
	private java.util.UUID towShip; // pet.PetTowing

	@Override
	public int getBond() {
		return bond;
	}

	@Override
	public void setBond(int bond) {
		this.bond = bond;
	}

	@Override
	public java.util.UUID getTowShip() {
		return towShip;
	}

	@Override
	public void setTowShip(java.util.UUID ship) {
		this.towShip = ship;
	}

	@Override
	public String petKind() {
		return "sea_king";
	}

	@Override
	protected net.minecraft.world.InteractionResult mobInteract(Player player, net.minecraft.world.InteractionHand hand) {
		net.minecraft.world.item.ItemStack stack = player.getItemInHand(hand);
		boolean server = this.level() instanceof ServerLevel;
		if (isSeaBoss() && stack.is(SeaItems.SEA_KING_BAIT)) {
			if (server) {
				com.onepiecemod.pet.Pets.tell(player, Component.literal("This one will never be tamed. It only knows hunger."), ChatFormatting.RED);
			}
			return net.minecraft.world.InteractionResult.CONSUME;
		}
		if (!isTamed() && stack.is(SeaItems.SEA_KING_BAIT)) {
			if (this.getHealth() > this.getMaxHealth() * 0.25f) {
				if (server) {
					com.onepiecemod.pet.Pets.tell(player, Component.literal("The Sea King snaps at the bait. Beat it down below 25% health first!"),
							ChatFormatting.GRAY);
				}
				return net.minecraft.world.InteractionResult.CONSUME;
			}
			if (server) {
				if (!player.isCreative()) {
					stack.shrink(1);
				}
				if (this.random.nextInt(3) == 0) {
					tame(player);
				} else {
					((ServerLevel) this.level()).sendParticles(net.minecraft.core.particles.ParticleTypes.SMOKE,
							getX(), getY() + getBbHeight(), getZ(), 10, 0.8, 0.4, 0.8, 0.02);
					com.onepiecemod.pet.Pets.tell(player, Component.literal("The Sea King gulps the bait but doesn't trust you yet..."),
							ChatFormatting.GRAY);
				}
			}
			return net.minecraft.world.InteractionResult.SUCCESS;
		}
		if (isTamed() && com.onepiecemod.pet.Pets.isOwner(this, player) && stack.isEmpty()) {
			if (player.isShiftKeyDown()) {
				if (server) {
					staying = !staying;
					this.getNavigation().stop();
					com.onepiecemod.pet.Pets.tell(player, Component.literal(staying ? "Your Sea King will stay here." : "Your Sea King will follow you."),
							ChatFormatting.GREEN);
				}
				return net.minecraft.world.InteractionResult.SUCCESS;
			}
			if (!this.isVehicle()) {
				if (server) {
					player.startRiding(this);
				}
				return net.minecraft.world.InteractionResult.SUCCESS;
			}
		}
		return super.mobInteract(player, hand);
	}

	private void tame(Player player) {
		ownerId = player.getUUID();
		staying = false;
		this.setTarget(null);
		this.setLastHurtByMob(null);
		this.setAggressive(false);
		this.setPersistenceRequired();
		bossBar.removeAllPlayers(); // it's on your side now, no more boss bar
		((ServerLevel) this.level()).sendParticles(net.minecraft.core.particles.ParticleTypes.HEART,
				getX(), getY() + getBbHeight(), getZ(), 12, 1.0, 0.5, 1.0, 0.02);
		com.onepiecemod.pet.Pets.tell(player, Component.literal(
				"The " + STYLE_NAMES[getStyle()] + " Sea King bows its head. It's yours! Right-click it with an empty hand to ride it through the sea."), ChatFormatting.GOLD);
		com.onepiecemod.pet.Pets.tell(player, Component.literal(
				"Its ability: King of the Deep. Wild Sea Kings leave you alone near it, and a Towing Harness lets it pull your ship."),
				ChatFormatting.GRAY);
	}

	// A tamed Sea King never turns on its owner, its rider, or its owner's crew and pets.
	@Override
	public boolean canAttack(net.minecraft.world.entity.LivingEntity target) {
		if (com.onepiecemod.pet.Pets.isOwner(this, target) || target == this.getFirstPassenger()) {
			return false;
		}
		if (isTamed() && com.onepiecemod.crew.CrewmateEntity.sameCrew(this, target)) {
			return false;
		}
		return super.canAttack(target);
	}

	@Override
	public net.minecraft.world.entity.LivingEntity getControllingPassenger() {
		// No owner check here: the owner isn't known on the rider's own game, which steers it. Only owners can climb on.
		if (this.getFirstPassenger() instanceof Player player) {
			return player;
		}
		return super.getControllingPassenger();
	}

	@Override
	protected void tickRidden(Player player, Vec3 travelVector) {
		super.tickRidden(player, travelVector);
		this.setRot(player.getYRot(), player.getXRot() * 0.5f);
		this.yRotO = this.getYRot();
		this.yBodyRot = this.getYRot();
		this.yHeadRot = this.getYRot();
		com.onepiecemod.pet.Pets.steerSwimming(this, player);
	}

	@Override
	protected Vec3 getRiddenInput(Player player, Vec3 travelVector) {
		float forward = player.zza;
		if (forward <= 0.0f) {
			forward *= 0.25f;
		}
		return new Vec3(player.xxa * 0.4f, 0.0, forward);
	}

	@Override
	protected float getRiddenSpeed(Player player) {
		return com.onepiecemod.pet.Pets.swimRiddenSpeed(this.getAttributeValue(Attributes.MOVEMENT_SPEED))
				* com.onepiecemod.pet.PetAbilities.riddenSpeedFactor(this);
	}

	@Override
	public void tick() {
		super.tick();
		if (this.level() instanceof ServerLevel level) {
			com.onepiecemod.pet.Pets.serverTick(this, level);
		}
	}

	// Tamed Sea Kings never vanish, not even on Peaceful.
	@Override
	public void checkDespawn() {
		if (!isTamed()) {
			super.checkDespawn();
		}
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		if (isTamed() && com.onepiecemod.pet.Pets.isOwner(this, source.getEntity()) && !source.getEntity().isShiftKeyDown()) {
			return false; // no hitting your own Sea King by accident (sneak to mean it)
		}
		boolean hurt = super.hurtServer(level, source, amount);
		if (hurt && isSeaBoss()) {
			SeaBosses.onHurt(this, source);
		}
		if (hurt) {
			com.onepiecemod.pet.PetAbilities.onHurt(this, source);
		}
		return hurt;
	}

	@Override
	public boolean killedEntity(ServerLevel level, net.minecraft.world.entity.LivingEntity killed, DamageSource source) {
		boolean result = super.killedEntity(level, killed, source);
		com.onepiecemod.pet.Pets.onKill(this, killed);
		return result;
	}

	// It finds its way through water only, never over land.
	@Override
	protected PathNavigation createNavigation(Level level) {
		return new WaterBoundPathNavigation(this, level);
	}

	// Moves freely in water instead of sinking or walking along the sea floor.
	@Override
	public void travelInWater(Vec3 input, double baseGravity, boolean isFalling, double oldY) {
		this.moveRelative(this.getSpeed(), input);
		this.move(MoverType.SELF, this.getDeltaMovement());
		this.setDeltaMovement(this.getDeltaMovement().scale(0.9));
	}

	@Override
	public boolean doHurtTarget(ServerLevel level, Entity target) {
		boolean hit = super.doHurtTarget(level, target);
		SeaBosses.Boss boss = SeaBosses.get(seaBoss);
		if (hit && boss != null) {
			SeaBosses.onBite(this, boss, target);
		}
		if (hit) {
			com.onepiecemod.pet.PetAbilities.onHit(this, target);
		}
		if (hit && target.isPassenger() && !(target.getVehicle() instanceof com.onepiecemod.pet.Pet)) {
			// Capsized! The rider gets thrown off their boat or ship and into the sea.
			target.stopRiding();
			target.setDeltaMovement(target.getDeltaMovement().add(0.0, 0.8, 0.0));
			Motion.sync(target);
			if (target instanceof ServerPlayer player) {
				player.sendSystemMessage(Component.literal("The Sea King knocked you into the sea!").withStyle(ChatFormatting.DARK_AQUA));
			}
		}
		return hit;
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		bossBar.setProgress(getHealth() / getMaxHealth());
		if (getCustomName() != null && !getCustomName().equals(bossBar.getName())) {
			bossBar.setName(getCustomName()); // A named Sea King, like the Sea King Lord (voyage.SeaMonsters).
			if (entityTags().contains("onepiece_sea_king_lord")) {
				bossBar.setColor(BossEvent.BossBarColor.RED);
			}
			if (isSeaBoss()) {
				bossBar.setColor(BossEvent.BossBarColor.PURPLE);
			}
		}
		SeaBosses.Boss boss = SeaBosses.get(seaBoss);
		if (boss != null && this.isAlive()) {
			SeaBosses.tick(this, level, boss);
		}
		com.onepiecemod.pet.Pets.tick(this, level);

		// Stranded on land or in a tiny puddle, it slowly dries out, like a beached whale.
		if (!this.isInWater() && this.onGround() && this.tickCount % 20 == 0) {
			this.hurtServer(level, this.damageSources().dryOut(), 2.0f);
		}
	}

	@Override
	public void startSeenByPlayer(ServerPlayer player) {
		super.startSeenByPlayer(player);
		if (!isTamed()) {
			bossBar.addPlayer(player);
		}
	}

	@Override
	public void stopSeenByPlayer(ServerPlayer player) {
		super.stopSeenByPlayer(player);
		bossBar.removePlayer(player);
	}

	@Override
	public void die(DamageSource damageSource) {
		if (isTamed() && !this.isRemoved()) {
			com.onepiecemod.pet.Pets.diedNotice(this);
		}
		super.die(damageSource);
		SeaBosses.Boss boss = SeaBosses.get(seaBoss);
		if (boss != null && this.level() instanceof ServerLevel level) {
			SeaBosses.onDeath(this, level, boss, damageSource);
			return;
		}
		if (damageSource.getEntity() instanceof ServerPlayer player) {
			player.sendSystemMessage(Component.literal("You defeated a Sea King! Cook the meat for a real pirate feast.")
					.withStyle(ChatFormatting.GOLD));
		}
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putInt("Variant", getVariant());
		output.putInt("Style", getStyle());
		output.putString("Owner", ownerId == null ? "" : ownerId.toString());
		output.putBoolean("Staying", staying);
		output.putString("SeaBoss", seaBoss);
		output.putInt("Bond", bond);
		output.putString("TowShip", towShip == null ? "" : towShip.toString());
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		this.entityData.set(DATA_VARIANT, input.getIntOr("Variant", 0));
		this.entityData.set(DATA_STYLE, Math.floorMod(input.getIntOr("Style", getStyle()), STYLES));
		String owner = input.getStringOr("Owner", "");
		ownerId = owner.isEmpty() ? null : java.util.UUID.fromString(owner);
		staying = input.getBooleanOr("Staying", false);
		seaBoss = input.getStringOr("SeaBoss", "");
		bond = input.getIntOr("Bond", 0);
		String tow = input.getStringOr("TowShip", "");
		towShip = tow.isEmpty() ? null : java.util.UUID.fromString(tow);
		if (isSeaBoss()) {
			bossBar.setColor(BossEvent.BossBarColor.PURPLE);
		}
	}

	// ---------- Sounds: a deep, loud roar ----------

	@Override
	protected SoundEvent getAmbientSound() {
		return com.onepiecemod.sound.WorldSounds.SEA_KING_AMBIENT;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource damageSource) {
		return com.onepiecemod.sound.WorldSounds.SEA_KING_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return com.onepiecemod.sound.WorldSounds.SEA_KING_DEATH;
	}

	@Override
	protected float getSoundVolume() {
		return 3.0f;
	}

	@Override
	public float getVoicePitch() {
		return 0.5f;
	}
}
