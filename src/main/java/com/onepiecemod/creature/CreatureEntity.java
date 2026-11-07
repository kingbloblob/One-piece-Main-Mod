package com.onepiecemod.creature;

import com.onepiecemod.util.Motion;
import java.util.EnumSet;
import java.util.List;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.world.Difficulty;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.SmoothSwimmingLookControl;
import net.minecraft.world.entity.ai.control.SmoothSwimmingMoveControl;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LeapAtTargetGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RandomSwimmingGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.ai.navigation.WaterBoundPathNavigation;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;

/**
 * One class for all the One Piece creatures. Which creature it is comes from its entity type,
 * and the matching CreatureSpecies says how it behaves (see CreatureSpecies.ALL).
 *
 * Things you can do with them:
 * - Hold their favorite food: they follow you. Feed a hurt one to heal it.
 * - Feed a tameable one until it trusts you: it follows you, fights for you (if it can fight) and never despawns.
 * - Sneak + right-click your tamed creature to make it stay or follow again.
 * - Wild beasts that hunt you (Bananawani, Lapahn) can only be tamed once you beat them below 30% health.
 * - Right-click a tamed rideable creature with an empty hand to ride it. Steer like a horse, jump with Space.
 *   Swimmers stay at the surface; look down while moving to dive, and they give you air under water.
 * - The Pet Whistle (com.onepiecemod.pet) calls every pet you own, or tells them all to wait.
 * - Shear a Cotton Candy Lamb for sugar every few minutes.
 * Herd animals stay together, and some animals settle down to sleep at night.
 */
public class CreatureEntity extends PathfinderMob implements com.onepiecemod.pet.Pet, net.minecraft.world.entity.PlayerRideableJumping {
	private static final int HARVEST_COOLDOWN = 6000; // 5 minutes

	private UUID ownerId;
	private boolean staying;
	private int harvestCooldown;
	private float pendingJump; // 0..1, set by the rider's jump bar
	private int bond; // pet.PetBond
	private UUID towShip; // pet.PetTowing

	public CreatureEntity(EntityType<? extends CreatureEntity> type, Level level) {
		super(type, level);
		if (species().swims()) {
			// Swims like a dolphin: turns smoothly and moves in 3D through the water.
			this.moveControl = new SmoothSwimmingMoveControl(this, 85, 10, 0.02f, 0.1f, true);
			this.lookControl = new SmoothSwimmingLookControl(this, 10);
		}
		this.xpReward = species().xp();
	}

	/** The settings for this creature. Works even while the entity is still being built. */
	public CreatureSpecies species() {
		return Creatures.speciesOf(this.getType());
	}

	public static AttributeSupplier.Builder createAttributes(CreatureSpecies species) {
		return Monster.createMonsterAttributes()
				.add(Attributes.MAX_HEALTH, species.health() * com.onepiecemod.config.ModConfig.creatureHealth())
				.add(Attributes.ATTACK_DAMAGE, Math.max(1.0, species.damage() * com.onepiecemod.config.ModConfig.creatureDamage()))
				.add(Attributes.MOVEMENT_SPEED, species.speed())
				.add(Attributes.ARMOR, species.armor())
				.add(Attributes.ATTACK_KNOCKBACK, species.knockback())
				.add(Attributes.FOLLOW_RANGE, 24.0)
				.add(Attributes.TEMPT_RANGE, 10.0); // TemptGoal crashes without it
	}

	// ---------- Brains ----------

	@Override
	protected void registerGoals() {
		CreatureSpecies species = species();
		Item food = foodItem();
		if (species.swims()) {
			if (species.fights()) {
				this.goalSelector.addGoal(1, new MeleeAttackGoal(this, 1.3, true));
			}
			this.goalSelector.addGoal(2, new com.onepiecemod.pet.PetGoals.FollowOwner<>(this));
			if (food != null) {
				this.goalSelector.addGoal(3, new TemptGoal(this, 1.2, stack -> stack.is(food), false));
			}
			this.goalSelector.addGoal(4, new HerdGoal());
			this.goalSelector.addGoal(5, new RandomSwimmingGoal(this, 1.0, 40) {
				@Override
				public boolean canUse() {
					return !staying && super.canUse();
				}
			});
			this.goalSelector.addGoal(6, new RandomLookAroundGoal(this));
		} else {
			this.goalSelector.addGoal(0, new FloatGoal(this));
			if (species.fights()) {
				if (species.leaps()) {
					this.goalSelector.addGoal(1, new LeapAtTargetGoal(this, 0.4f));
				}
				this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.2, false));
			} else {
				this.goalSelector.addGoal(1, new PanicGoal(this, 1.5));
			}
			this.goalSelector.addGoal(3, new com.onepiecemod.pet.PetGoals.FollowOwner<>(this));
			if (food != null) {
				this.goalSelector.addGoal(4, new TemptGoal(this, 1.1, stack -> stack.is(food), false));
			}
			this.goalSelector.addGoal(5, new HerdGoal());
			this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 1.0) {
				@Override
				public boolean canUse() {
					return !staying && !isSleepy() && super.canUse();
				}
			});
			// The South Bird ignores everyone: it only cares about pointing south.
			if (!species.id().equals("south_bird")) {
				this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8.0f));
				this.goalSelector.addGoal(8, new RandomLookAroundGoal(this) {
					@Override
					public boolean canUse() {
						return !isSleepy() && super.canUse();
					}
				});
			}
		}

		if (species.fights()) {
			this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
			this.targetSelector.addGoal(2, new com.onepiecemod.pet.PetGoals.DefendOwner<>(this));
			this.targetSelector.addGoal(3, new com.onepiecemod.pet.PetGoals.OwnerAttacks<>(this));
		}
		if (species.behavior() == CreatureSpecies.Behavior.HOSTILE) {
			// Wild ones hunt players. Once tamed they leave players alone unless told to (or hurt).
			this.targetSelector.addGoal(4, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false,
					(target, level) -> !isTamed()));
		}
	}

	private Item foodItem() {
		String food = species().food();
		return food.isEmpty() ? null : BuiltInRegistries.ITEM.getValue(Identifier.parse(food));
	}

	/** Night time for animals that sleep: they lie still instead of wandering around. */
	public boolean isSleepy() {
		if (!species().sleepsAtNight() || this.getTarget() != null || this.isVehicle()) {
			return false;
		}
		long time = this.level().getDefaultClockTime() % 24000L;
		return time >= 13000L && time < 23000L;
	}

	// ---------- Taming, feeding, riding, harvesting ----------

	@Override
	public boolean isTamed() {
		return ownerId != null;
	}

	@Override
	public UUID getOwnerId() {
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
		return species().swims();
	}

	@Override
	public int getBond() {
		return bond;
	}

	@Override
	public void setBond(int bond) {
		this.bond = bond;
	}

	@Override
	public UUID getTowShip() {
		return towShip;
	}

	@Override
	public void setTowShip(UUID ship) {
		this.towShip = ship;
	}

	@Override
	public String petKind() {
		return species().id();
	}

	/** Beasts that hunt you only give in once they're beaten: below 30% health. Everything else just needs food. */
	private boolean beatenEnoughToTame() {
		return species().behavior() != CreatureSpecies.Behavior.HOSTILE || this.getHealth() <= this.getMaxHealth() * 0.3f;
	}

	public LivingEntity getOwner() {
		return ownerId == null ? null : this.level().getPlayerByUUID(ownerId);
	}

	private boolean isOwner(Player player) {
		return ownerId != null && ownerId.equals(player.getUUID());
	}

	@Override
	protected InteractionResult mobInteract(Player player, InteractionHand hand) {
		CreatureSpecies species = species();
		ItemStack stack = player.getItemInHand(hand);
		Item food = foodItem();
		boolean server = this.level() instanceof ServerLevel;

		// Shearing (Cotton Candy Lamb).
		if (!species.harvestTool().isEmpty()
				&& stack.is(BuiltInRegistries.ITEM.getValue(Identifier.parse(species.harvestTool())))) {
			if (server && harvestCooldown <= 0) {
				Item drop = BuiltInRegistries.ITEM.getValue(Identifier.parse(species.harvestDrop()));
				this.spawnAtLocation((ServerLevel) this.level(), new ItemStack(drop, species.harvestCount()));
				playSound("entity.sheep.shear");
				harvestCooldown = HARVEST_COOLDOWN;
			}
			return InteractionResult.SUCCESS;
		}

		// Feeding: heals, and slowly wins the creature's trust.
		if (food != null && stack.is(food)) {
			if (species.tameable() && !isTamed() && !beatenEnoughToTame()) {
				// Too wild: it won't eat from your hand while it still has fight left in it.
				if (server) {
					tell(player, " is too wild to tame. Beat it down below 30% health, then feed it.");
				}
				return InteractionResult.CONSUME;
			}
			boolean wantsFood = this.getHealth() < this.getMaxHealth() || (species.tameable() && !isTamed());
			if (!wantsFood) {
				return InteractionResult.PASS;
			}
			if (server) {
				if (!player.isCreative()) {
					stack.shrink(1);
				}
				if (isTamed() || species.behavior() != CreatureSpecies.Behavior.HOSTILE) {
					this.heal(4.0f); // a beaten wild beast doesn't get its strength back from one bite
				}
				if (isTamed() && isOwner(player)) {
					com.onepiecemod.pet.Pets.onFed(this);
				}
				if (species.tameable() && !isTamed()) {
					if (this.random.nextInt(3) == 0) {
						tame(player);
					} else {
						particles(ParticleTypes.SMOKE);
					}
				}
			}
			return InteractionResult.SUCCESS;
		}

		if (isTamed() && isOwner(player) && stack.isEmpty()) {
			if (player.isShiftKeyDown()) {
				// Sneak + right-click: stay here / follow me again.
				if (server) {
					staying = !staying;
					this.getNavigation().stop();
					tell(player, staying ? " will stay here." : " will follow you.");
				}
				return InteractionResult.SUCCESS;
			}
			if (species.rideable() && !this.isVehicle()) {
				if (server) {
					player.startRiding(this);
				}
				return InteractionResult.SUCCESS;
			}
		}
		return super.mobInteract(player, hand);
	}

	private void tame(Player player) {
		ownerId = player.getUUID();
		staying = false;
		this.setTarget(null);
		this.setLastHurtByMob(null); // forgive the beating it took
		this.setAggressive(false);
		this.setPersistenceRequired();
		particles(ParticleTypes.HEART);
		tell(player, species().flies()
				? " trusts you now! Right-click it with an empty hand to ride it. Hold Space to take off, look where you want to fly."
				: species().rideable()
				? " trusts you now! Right-click it with an empty hand to ride it."
				: " trusts you now and will follow you.");
		tell(player, " has an ability: " + com.onepiecemod.pet.PetAbilities.name(this) + ". Type /pets to see it.");
	}

	private void tell(Player player, String text) {
		if (player instanceof ServerPlayer serverPlayer) {
			serverPlayer.sendSystemMessage(Component.empty().append(this.getName()).append(text).withStyle(ChatFormatting.GREEN));
		}
	}

	private void particles(net.minecraft.core.particles.SimpleParticleType type) {
		if (this.level() instanceof ServerLevel level) {
			level.sendParticles(type, this.getX(), this.getY() + this.getBbHeight() * 0.8, this.getZ(),
					7, this.getBbWidth() * 0.4, 0.3, this.getBbWidth() * 0.4, 0.02);
		}
	}

	private void playSound(String id) {
		SoundEvent sound = sound(id);
		if (sound != null) {
			this.playSound(sound, 1.0f, 1.0f);
		}
	}

	// A tamed creature never turns on its owner, the owner's crewmates or the owner's other pets.
	@Override
	public boolean canAttack(LivingEntity target) {
		if (target instanceof Player player && isOwner(player)) {
			return false;
		}
		if (target == this.getFirstPassenger()) {
			return false; // never bite its own rider
		}
		if (isTamed() && com.onepiecemod.crew.CrewmateEntity.sameCrew(this, target)) {
			return false;
		}
		return super.canAttack(target);
	}

	// Riding: the player steers, just like a horse.
	@Override
	public LivingEntity getControllingPassenger() {
		if (species().rideable() && this.getFirstPassenger() instanceof Player player) {
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
		if (species().swims()) {
			com.onepiecemod.pet.Pets.steerSwimming(this, player);
		} else if (this.isInWater() && this.getFluidHeight(net.minecraft.tags.FluidTags.WATER) > this.getBbHeight() * 0.4) {
			// Land mounts paddle along the surface instead of sinking with you on their back.
			Vec3 motion = this.getDeltaMovement();
			this.setDeltaMovement(motion.x, Math.max(motion.y, 0.08), motion.z);
		} else if (pendingJump > 0.0f && this.onGround()) {
			// Jump! Big beasts jump a bit lower, Lapahn jump like the giant rabbits they are.
			double strength = (species().id().equals("lapahn") ? 1.0 : species().renderScale() > 1.3f ? 0.6 : 0.75) * pendingJump;
			Vec3 motion = this.getDeltaMovement();
			Vec3 ahead = Vec3.directionFromRotation(0.0f, this.getYRot()).scale(0.3 * pendingJump * Math.max(0.0f, player.zza));
			this.setDeltaMovement(motion.x + ahead.x, strength, motion.z + ahead.z);
			Motion.sync(this);
			pendingJump = 0.0f;
		}
	}

	// ---------- Jumping while ridden (land mounts): hold Space to charge, like a horse ----------

	@Override
	public boolean canJump() {
		// Fliers use Space to climb instead of the jump bar.
		return species().rideable() && !species().swims() && !species().flies();
	}

	@Override
	public void onPlayerJump(int power) {
		if (!canJump() || power <= 0) {
			return;
		}
		pendingJump = power >= 90 ? 1.0f : 0.4f + 0.6f * power / 90.0f;
	}

	@Override
	public void handleStartJump(int power) {
	}

	@Override
	public void handleStopJump() {
	}

	@Override
	protected Vec3 getRiddenInput(Player player, Vec3 travelVector) {
		if (flyingRidden(player)) {
			// Fly where you look: forward follows the camera up and down, Space climbs, and with no keys it glides down slowly.
			float forward = player.zza < 0.0f ? player.zza * 0.4f : player.zza;
			float pitch = player.getXRot() * net.minecraft.util.Mth.DEG_TO_RAD;
			double up = -net.minecraft.util.Mth.sin(pitch) * forward + (player.isJumping() ? 0.7 : 0.0);
			if (forward == 0.0f && !player.isJumping()) {
				up = -0.15;
			}
			return new Vec3(player.xxa * 0.5f, up, net.minecraft.util.Mth.cos(pitch) * forward);
		}
		float forward = player.zza;
		if (forward <= 0.0f) {
			forward *= 0.25f; // Backing up is slow.
		}
		return new Vec3(player.xxa * 0.5f, 0.0, forward);
	}

	@Override
	protected float getRiddenSpeed(Player player) {
		double speed = this.getAttributeValue(Attributes.MOVEMENT_SPEED);
		float bonus = com.onepiecemod.pet.PetAbilities.riddenSpeedFactor(this);
		if (flyingRidden(player)) {
			return species().flySpeed() * bonus;
		}
		// Swimmers' speed stat is ten times their real swim speed (their AI scales it down too).
		return (species().swims() ? com.onepiecemod.pet.Pets.swimRiddenSpeed(speed) : (float) speed * 1.1f) * bonus;
	}

	// ---------- Flying mounts (Fuzza, Punk Hazard Dragon) ----------

	/** In the air with a rider, or taking off (Space held, also from water). Runs on the rider's game, which steers. */
	private boolean flyingRidden(Player player) {
		return species().flies() && (player.isJumping() || (!this.onGround() && !this.isInWater()));
	}

	@Override
	public void travel(Vec3 input) {
		if (species().flies() && this.getControllingPassenger() instanceof Player player && flyingRidden(player)) {
			this.travelFlying(input, this.getSpeed()); // no gravity while it flaps its wings
			return;
		}
		super.travel(input);
	}

	// Tells the server a flying mount may stay in the air (no "flying is not enabled" kick).
	@Override
	public boolean isFlyingVehicle() {
		return species().flies() && this.isVehicle();
	}

	// Fliers land softly, and so does their rider.
	@Override
	public boolean causeFallDamage(double fallDistance, float multiplier, DamageSource source) {
		if (species().flies()) {
			return false;
		}
		return super.causeFallDamage(fallDistance, multiplier, source);
	}

	// Jumping off in mid-air: you float down instead of dropping like a stone.
	@Override
	protected void removePassenger(Entity passenger) {
		super.removePassenger(passenger);
		if (species().flies() && !this.onGround() && !this.level().isClientSide() && passenger instanceof LivingEntity living) {
			living.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 160, 0));
		}
	}

	// ---------- Movement and fighting ----------

	// Swimmers find their way through water only.
	@Override
	protected PathNavigation createNavigation(Level level) {
		return species().swims() ? new WaterBoundPathNavigation(this, level) : super.createNavigation(level);
	}

	// Swimmers move freely in water instead of sinking to the bottom.
	@Override
	public void travelInWater(Vec3 input, double baseGravity, boolean isFalling, double oldY) {
		if (!species().swims()) {
			super.travelInWater(input, baseGravity, isFalling, oldY);
			return;
		}
		this.moveRelative(this.getSpeed(), input);
		this.move(MoverType.SELF, this.getDeltaMovement());
		this.setDeltaMovement(this.getDeltaMovement().scale(0.9));
	}

	@Override
	public boolean doHurtTarget(ServerLevel level, Entity target) {
		boolean hit = super.doHurtTarget(level, target);
		CreatureSpecies species = species();
		if (hit) {
			com.onepiecemod.pet.PetAbilities.onHit(this, target);
		}
		if (hit && target instanceof LivingEntity living) {
			if (species.poisonSeconds() > 0) {
				living.addEffect(new MobEffectInstance(MobEffects.POISON, species.poisonSeconds() * 20, 0), this);
			}
			if (species.fireSeconds() > 0) {
				living.igniteForSeconds(species.fireSeconds());
			}
		}
		return hit;
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		CreatureSpecies species = species();

		// Hostile creatures vanish on Peaceful, like zombies do.
		if (species.behavior() == CreatureSpecies.Behavior.HOSTILE && !isTamed() && level.getDifficulty() == Difficulty.PEACEFUL) {
			this.discard();
			return;
		}
		if (harvestCooldown > 0) {
			harvestCooldown--;
		}
		com.onepiecemod.pet.Pets.tick(this, level);
		// Fish out of water slowly dry out.
		if (species.swims() && !this.isInWater() && this.onGround() && this.tickCount % 20 == 0) {
			this.hurtServer(level, this.damageSources().dryOut(), 1.0f);
		}
		// Sleeping animals stop where they are.
		if (isSleepy() && this.tickCount % 20 == 0) {
			this.getNavigation().stop();
		}
		// The South Bird always faces south while it stands still.
		if (species.id().equals("south_bird") && this.getNavigation().isDone()) {
			this.setYRot(0.0f);
			this.setYBodyRot(0.0f);
			this.setYHeadRot(0.0f);
		}
	}

	@Override
	public void tick() {
		super.tick();
		if (this.level() instanceof ServerLevel level) {
			com.onepiecemod.pet.Pets.serverTick(this, level);
			// High in the sky on a flying mount: an achievement.
			if (species().flies() && this.tickCount % 20 == 0 && this.getControllingPassenger() instanceof ServerPlayer rider
					&& this.getY() - level.getHeight(net.minecraft.world.level.levelgen.Heightmap.Types.MOTION_BLOCKING,
							this.getBlockX(), this.getBlockZ()) > 12) {
				com.onepiecemod.advancement.AdvancementFeature.grant(rider, "wonders/sky_rider");
			}
		}
	}

	// Tamed beasts never vanish, not even hostile ones on Peaceful.
	@Override
	public void checkDespawn() {
		if (!isTamed()) {
			super.checkDespawn();
		}
	}

	// The owner can't hurt their own pet by accident (sweeping blows, hitting things while riding it).
	// Sneak while attacking if you really mean it.
	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		if (isTamed() && com.onepiecemod.pet.Pets.isOwner(this, source.getEntity()) && !source.getEntity().isShiftKeyDown()) {
			return false;
		}
		boolean hurt = super.hurtServer(level, source, amount);
		if (hurt) {
			com.onepiecemod.pet.PetAbilities.onHurt(this, source);
		}
		return hurt;
	}

	@Override
	public boolean killedEntity(ServerLevel level, LivingEntity killed, DamageSource source) {
		boolean result = super.killedEntity(level, killed, source);
		com.onepiecemod.pet.Pets.onKill(this, killed);
		return result;
	}

	@Override
	public void die(DamageSource damageSource) {
		if (isTamed() && !this.isRemoved()) {
			com.onepiecemod.pet.Pets.diedNotice(this);
		}
		super.die(damageSource);
	}

	// ---------- Saving ----------

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putString("Owner", ownerId == null ? "" : ownerId.toString());
		output.putBoolean("Staying", staying);
		output.putInt("HarvestCooldown", harvestCooldown);
		output.putInt("Bond", bond);
		output.putString("TowShip", towShip == null ? "" : towShip.toString());
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		String owner = input.getStringOr("Owner", "");
		ownerId = owner.isEmpty() ? null : UUID.fromString(owner);
		staying = input.getBooleanOr("Staying", false);
		harvestCooldown = input.getIntOr("HarvestCooldown", 0);
		bond = input.getIntOr("Bond", 0);
		String tow = input.getStringOr("TowShip", "");
		towShip = tow.isEmpty() ? null : UUID.fromString(tow);
	}

	// ---------- Sounds: borrowed from vanilla animals ----------

	private static SoundEvent sound(String id) {
		return id.isEmpty() ? null : BuiltInRegistries.SOUND_EVENT.getValue(Identifier.parse(id));
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return isSleepy() ? null : sound(species().ambientSound());
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource damageSource) {
		return sound(species().hurtSound());
	}

	@Override
	protected SoundEvent getDeathSound() {
		return sound(species().deathSound());
	}

	@Override
	public float getVoicePitch() {
		// Big creatures sound deeper, small ones higher.
		return super.getVoicePitch() * (species().renderScale() > 1.2f ? 0.8f : species().height() < 1.0f ? 1.3f : 1.0f);
	}

	// ---------- Goals ----------

	/** Herd animals drift back toward the others of their kind when they wander too far off. */
	private class HerdGoal extends Goal {
		private CreatureEntity buddy;

		HerdGoal() {
			this.setFlags(EnumSet.of(Goal.Flag.MOVE));
		}

		@Override
		public boolean canUse() {
			if (!species().herd() || isTamed() || staying || isSleepy() || getRandom().nextInt(40) != 0) {
				return false;
			}
			List<CreatureEntity> near = level().getEntitiesOfClass(CreatureEntity.class, getBoundingBox().inflate(16.0, 6.0, 16.0),
					other -> other != CreatureEntity.this && other.getType() == getType());
			if (near.isEmpty()) {
				return false;
			}
			buddy = near.get(getRandom().nextInt(near.size()));
			return distanceToSqr(buddy) > 36.0;
		}

		@Override
		public boolean canContinueToUse() {
			return buddy != null && buddy.isAlive() && distanceToSqr(buddy) > 16.0 && !getNavigation().isDone();
		}

		@Override
		public void start() {
			getNavigation().moveTo(buddy, 1.0);
		}

		@Override
		public void stop() {
			buddy = null;
		}
	}
}
