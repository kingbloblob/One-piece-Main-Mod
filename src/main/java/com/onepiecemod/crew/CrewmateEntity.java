package com.onepiecemod.crew;

import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.UUIDUtil;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.core.component.DataComponents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.Containers;
import net.minecraft.world.entity.ContainerUser;
import net.minecraft.world.item.BowItem;
import net.minecraft.world.item.component.ItemAttributeModifiers;
import net.minecraft.world.item.equipment.Equippable;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.FollowOwnerGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.SitWhenOrderedToGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.OwnerHurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.OwnerHurtTargetGoal;
import net.minecraft.world.entity.monster.RangedAttackMob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.entity.projectile.arrow.Arrow;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

import com.onepiecemod.crew.job.ArchaeologistWorkGoal;
import com.onepiecemod.crew.job.CookWorkGoal;
import com.onepiecemod.crew.job.DoctorWorkGoal;
import com.onepiecemod.crew.job.GuardWorkGoal;
import com.onepiecemod.crew.job.HelmsmanWorkGoal;
import com.onepiecemod.crew.job.MusicianWorkGoal;
import com.onepiecemod.crew.job.NavigatorWorkGoal;
import com.onepiecemod.crew.job.ShipwrightWorkGoal;

/**
 * A hired pirate. They follow their captain, protect them, and (for some roles) do a job.
 *
 * We build on TamableAnimal, the same base class as wolves and cats. That gives us
 * "follow the owner", "teleport to the owner when far away" and "attack whatever hurts
 * the owner" for free.
 */
public class CrewmateEntity extends TamableAnimal implements RangedAttackMob {
	// The role and kind are sent to players' games so they can pick the right outfit.
	private static final EntityDataAccessor<String> DATA_ROLE = SynchedEntityData.defineId(CrewmateEntity.class, EntityDataSerializers.STRING);
	private static final EntityDataAccessor<Integer> DATA_VARIANT = SynchedEntityData.defineId(CrewmateEntity.class, EntityDataSerializers.INT);
	// Mode, level and "knocked out" are sent too, for the name tag and the lying-down pose.
	private static final EntityDataAccessor<Integer> DATA_MODE = SynchedEntityData.defineId(CrewmateEntity.class, EntityDataSerializers.INT);
	private static final EntityDataAccessor<Integer> DATA_LEVEL = SynchedEntityData.defineId(CrewmateEntity.class, EntityDataSerializers.INT);
	private static final EntityDataAccessor<Boolean> DATA_DOWNED = SynchedEntityData.defineId(CrewmateEntity.class, EntityDataSerializers.BOOLEAN);

	/** How long a knocked-out crewmate stays down: 60 seconds, or a third of that with the crew's doctor nearby. */
	public static final int KNOCKED_OUT_TICKS = 1200;
	private static final EquipmentSlot[] ARMOR_SLOTS = {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET};

	/**
	 * The bag, 18 slots. The captain opens it by sneaking and right-clicking.
	 * While it's open, the crewmate's armor and weapon sit in the bag too, so the captain can take them back.
	 * When it closes, the crewmate puts on the best armor and weapon in it.
	 */
	private final SimpleContainer inventory = new SimpleContainer(18) {
		@Override
		public void startOpen(ContainerUser user) {
			super.startOpen(user);
			unequipGear();
		}

		@Override
		public void stopOpen(ContainerUser user) {
			super.stopOpen(user);
			equipBestGear();
		}
	};

	private CrewMode mode = CrewMode.FOLLOW;
	private CrewPersonality personality = CrewPersonality.STEADY;
	private UUID captainId;
	private BlockPos workPos;
	private Goal combatGoal;
	private int crewLevel = 1;
	private int xp;
	private int downedTicks;
	/** True while the main hand holds the role's free weapon (it vanishes when swapped, so it can't be farmed). */
	private boolean issuedWeapon = true;

	public CrewmateEntity(EntityType<? extends CrewmateEntity> type, Level level) {
		super(type, level);
		updateCombatGoal();
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Mob.createMobAttributes()
				.add(Attributes.MAX_HEALTH, 30.0)
				.add(Attributes.MOVEMENT_SPEED, 0.3)
				.add(Attributes.ATTACK_DAMAGE, 3.0)
				.add(Attributes.FOLLOW_RANGE, 32.0);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(DATA_ROLE, CrewRole.SWORDSMAN.id());
		builder.define(DATA_VARIANT, 0);
		builder.define(DATA_MODE, CrewMode.FOLLOW.ordinal());
		builder.define(DATA_LEVEL, 1);
		builder.define(DATA_DOWNED, false);
	}

	// The "brain": lower numbers are more important.
	@Override
	protected void registerGoals() {
		this.goalSelector.addGoal(0, new KnockedOutGoal());
		this.goalSelector.addGoal(1, new FloatGoal(this));
		this.goalSelector.addGoal(2, new SitWhenOrderedToGoal(this)); // Wait mode.
		this.goalSelector.addGoal(3, new com.onepiecemod.crewship.ShipPostGoal(this)); // Stationed aboard the home ship: room by day, bunk by night.
		this.goalSelector.addGoal(3, new com.onepiecemod.hideout.HideoutLifeGoal(this)); // At a hideout: campfire at dusk, beds at night.
		this.goalSelector.addGoal(3, new com.onepiecemod.farm.FarmhandGoal(this)); // Set to Work by a Straw Hat Scarecrow: farm there first, any role.
		// Priority 3 is the fighting goal, added in updateCombatGoal() because it depends on the role.
		this.goalSelector.addGoal(3, new com.onepiecemod.mining.MinerWorkGoal(this)); // Any role posted beside a Mining Drill runs it.
		// Jobs for Work mode. Each one only runs for its own role.
		this.goalSelector.addGoal(4, new GuardWorkGoal(this, CrewRole.SWORDSMAN));
		this.goalSelector.addGoal(4, new GuardWorkGoal(this, CrewRole.SNIPER));
		this.goalSelector.addGoal(4, new NavigatorWorkGoal(this));
		this.goalSelector.addGoal(4, new CookWorkGoal(this));
		this.goalSelector.addGoal(4, new DoctorWorkGoal(this));
		this.goalSelector.addGoal(4, new ShipwrightWorkGoal(this));
		this.goalSelector.addGoal(4, new ArchaeologistWorkGoal(this));
		this.goalSelector.addGoal(4, new MusicianWorkGoal(this));
		this.goalSelector.addGoal(4, new HelmsmanWorkGoal(this));
		this.goalSelector.addGoal(5, new FollowOwnerGoal(this, 1.1, 8.0f, 3.0f) {
			@Override
			public boolean canUse() {
				return mode == CrewMode.FOLLOW && super.canUse();
			}

			@Override
			public boolean canContinueToUse() {
				return mode == CrewMode.FOLLOW && super.canContinueToUse();
			}
		});
		this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.8) {
			@Override
			public boolean canUse() {
				return mode == CrewMode.FOLLOW && super.canUse(); // Workers stay at their post.
			}
		});
		this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 8.0f));
		this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));

		this.targetSelector.addGoal(1, new OwnerHurtByTargetGoal(this)); // Fight whoever hurts the captain.
		this.targetSelector.addGoal(2, new OwnerHurtTargetGoal(this)); // Fight whoever the captain hits.
		this.targetSelector.addGoal(3, new HurtByTargetGoal(this)); // Fight back.
	}

	// Snipers shoot arrows from a distance, everyone else fights up close.
	private void updateCombatGoal() {
		if (combatGoal != null) {
			this.goalSelector.removeGoal(combatGoal);
		}
		combatGoal = getRole() == CrewRole.SNIPER
				? new com.onepiecemod.npc.SkirmishGoal<>(this, 1.0, 25, 35, 16.0f) // Keeps its distance and steps aside while shooting.
				: new MeleeAttackGoal(this, 1.2, true);
		this.goalSelector.addGoal(3, combatGoal);
	}

	// ---------- Role, captain, mode ----------

	public CrewRole getRole() {
		CrewRole role = CrewRole.byId(this.entityData.get(DATA_ROLE));
		return role != null ? role : CrewRole.SWORDSMAN;
	}

	/** Sets the role, keeping the current kind and personality. */
	public void setRole(CrewRole role) {
		setProfile(role, getVariantIndex(), personality);
	}

	/**
	 * Sets the role, kind (0-2, see CrewVariant) and personality, and gives the crewmate
	 * the matching health, damage, speed and weapon.
	 */
	public void setProfile(CrewRole role, int variantIndex, CrewPersonality newPersonality) {
		this.entityData.set(DATA_ROLE, role.id());
		this.entityData.set(DATA_VARIANT, Math.floorMod(variantIndex, CrewVariant.COUNT));
		this.personality = newPersonality;
		CrewVariant variant = getVariant();
		this.getAttribute(Attributes.MAX_HEALTH).setBaseValue(role.health() * variant.healthMultiplier() * personality.healthMultiplier()
				* CrewLevels.healthMultiplier(crewLevel));
		this.getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(role.damage() * variant.damageMultiplier() * personality.damageMultiplier()
				* CrewLevels.damageMultiplier(crewLevel));
		this.getAttribute(Attributes.MOVEMENT_SPEED).setBaseValue(0.3 * variant.speedMultiplier());
		if (issuedWeapon) {
			this.setItemSlot(EquipmentSlot.MAINHAND, role.weapon());
		}
		this.setDropChance(EquipmentSlot.MAINHAND, 0.0f); // No free swords from fallen crewmates (their own gear drops from dropInventory).
		this.entityData.set(DATA_LEVEL, crewLevel);
		updateCombatGoal();
	}

	/** Which of the role's three kinds this crewmate is (0, 1 or 2). */
	public int getVariantIndex() {
		return this.entityData.get(DATA_VARIANT);
	}

	public CrewVariant getVariant() {
		return CrewVariant.of(getRole(), getVariantIndex());
	}

	public CrewPersonality getPersonality() {
		return personality;
	}

	public int getCrewLevel() {
		return this.level().isClientSide() ? this.entityData.get(DATA_LEVEL) : crewLevel;
	}

	/** XP earned towards the next level. */
	public int getXp() {
		return xp;
	}

	/** How long a job takes: personality times level (higher levels work faster). 1.0 = one second. */
	public double workTime() {
		return personality.workTime() * CrewLevels.workTimeMultiplier(crewLevel);
	}

	/** Gives XP for fighting or working. Levels up (tougher, stronger, faster at work) when there's enough. */
	public void addXp(int amount) {
		if (amount <= 0 || crewLevel >= CrewLevels.MAX_LEVEL || !(this.level() instanceof ServerLevel serverLevel)) {
			return;
		}
		xp += amount;
		boolean levelled = false;
		while (crewLevel < CrewLevels.MAX_LEVEL && xp >= CrewLevels.xpToNext(crewLevel)) {
			xp -= CrewLevels.xpToNext(crewLevel);
			crewLevel++;
			levelled = true;
		}
		if (crewLevel >= CrewLevels.MAX_LEVEL) {
			xp = 0;
		}
		if (levelled) {
			setProfile(getRole(), getVariantIndex(), personality); // Applies the new level's health and strength.
			this.setHealth(this.getMaxHealth());
			serverLevel.sendParticles(net.minecraft.core.particles.ParticleTypes.HAPPY_VILLAGER,
					getX(), getY() + 1.2, getZ(), 15, 0.4, 0.6, 0.4, 0.0);
			this.playSound(SoundEvents.PLAYER_LEVELUP, 0.6f, 1.2f);
			tellCaptain(crewLevel >= CrewLevels.MAX_LEVEL
					? "I've reached level " + crewLevel + ", the best I can be! Thanks for believing in me, Captain."
					: "I reached level " + crewLevel + "! I'm tougher and stronger now.");
			CrewPayloads.refresh(getCaptain());
		}
	}

	/** Says one of their personality's lines to the captain. */
	public void chatter() {
		String[] lines = personality.lines();
		tellCaptain(lines[this.getRandom().nextInt(lines.length)]);
	}

	public UUID getCaptainId() {
		return captainId;
	}

	public void setCaptain(Player captain) {
		this.captainId = captain.getUUID();
		this.tame(captain); // Makes the "follow owner" and "protect owner" goals work.
	}

	/** The captain, if they're online. */
	public ServerPlayer getCaptain() {
		if (captainId == null || !(this.level() instanceof ServerLevel serverLevel)) {
			return null;
		}
		return serverLevel.getServer().getPlayerList().getPlayer(captainId);
	}

	/** Sends the captain a chat message from this crewmate, like "Sniper Kenji: Enemy spotted!". */
	public void tellCaptain(String message) {
		ServerPlayer captain = getCaptain();
		if (captain != null) {
			captain.sendSystemMessage(Component.empty()
					.append(this.getDisplayName())
					.append(": " + message)
					.withStyle(ChatFormatting.AQUA));
		}
	}

	public CrewMode getMode() {
		return this.level().isClientSide() ? CrewMode.values()[Math.floorMod(this.entityData.get(DATA_MODE), CrewMode.values().length)] : mode;
	}

	public void setMode(CrewMode newMode) {
		this.mode = newMode;
		this.entityData.set(DATA_MODE, newMode.ordinal());
		this.setOrderedToSit(newMode == CrewMode.WAIT);
		this.workPos = newMode == CrewMode.WORK ? this.blockPosition() : null;
		this.getNavigation().stop();
	}

	public BlockPos getWorkPos() {
		return workPos;
	}

	public SimpleContainer getInventory() {
		return inventory;
	}

	/** The unique id of whoever leads this entity's crew: a player is their own captain. */
	public static UUID captainOf(Entity entity) {
		if (entity instanceof Player player) {
			return player.getUUID();
		}
		if (entity instanceof CrewmateEntity crewmate) {
			return crewmate.getCaptainId();
		}
		if (entity instanceof com.onepiecemod.pet.Pet pet) {
			return pet.getOwnerId(); // The captain's tamed pets (creatures, Sea Kings) count as crew too.
		}
		return null;
	}

	public static boolean sameCrew(Entity a, Entity b) {
		UUID captainA = captainOf(a);
		return captainA != null && captainA.equals(captainOf(b));
	}

	// Never pick fights with your own crew (or the captain's pets), even after being hit by accident.
	@Override
	public boolean canAttack(LivingEntity target) {
		return !sameCrew(this, target) && super.canAttack(target);
	}

	@Override
	public boolean wantsToAttack(LivingEntity target, LivingEntity owner) {
		return !sameCrew(this, target) && super.wantsToAttack(target, owner);
	}

	// ---------- Staying in the crew ----------

	@Override
	public void tick() {
		super.tick();
		if (downedTicks > 0 && this.level() instanceof ServerLevel downedLevel) {
			tickKnockedOut(downedLevel);
		}
		// Every 5 seconds: if the captain is online and this crewmate is no longer on their crew list
		// (dismissed or disbanded while this crewmate was far away), they pack up and leave.
		if (this.level() instanceof ServerLevel serverLevel && (this.tickCount + this.getId()) % 100 == 0 && captainId != null) {
			ServerPlayer captain = serverLevel.getServer().getPlayerList().getPlayer(captainId);
			if (captain != null) {
				Crew crew = captain.getAttached(CrewAttachments.CREW);
				if (crew == null || !this.getUUID().equals(crew.member(getRole()))) {
					serverLevel.sendParticles(net.minecraft.core.particles.ParticleTypes.POOF,
							getX(), getY() + 0.8, getZ(), 12, 0.3, 0.5, 0.3, 0.02);
					dropInventory();
					discard();
				}
			}
		}
	}

	// ---------- Knocked out ----------

	/** True while knocked out: lying down, can't be hurt, and enemies ignore them. */
	public boolean isKnockedOut() {
		return this.entityData.get(DATA_DOWNED);
	}

	/**
	 * Called instead of dying. Returns true if the crewmate was knocked out (and so doesn't die).
	 * Falling into the void and /kill still kill for real.
	 */
	public boolean tryKnockOut(DamageSource source) {
		if (source.is(DamageTypeTags.BYPASSES_INVULNERABILITY) || isKnockedOut() || !(this.level() instanceof ServerLevel level)) {
			return false;
		}
		this.setHealth(1.0f);
		downedTicks = KNOCKED_OUT_TICKS;
		this.entityData.set(DATA_DOWNED, true);
		this.setTarget(null);
		this.getNavigation().stop();
		this.stopRiding();
		this.clearFire();
		level.sendParticles(net.minecraft.core.particles.ParticleTypes.CRIT, getX(), getY() + 1.0, getZ(), 20, 0.4, 0.4, 0.4, 0.1);
		tellCaptain("Ugh... I'm down! Give me a minute, Captain." + (hasDoctorNearby(level) ? "" : " (A doctor would help.)"));
		CrewPayloads.refresh(getCaptain());
		return true;
	}

	private void tickKnockedOut(ServerLevel level) {
		this.setTarget(null);
		this.setDeltaMovement(0, Math.min(0, this.getDeltaMovement().y), 0);
		// The crew's doctor patches them up three times as fast.
		downedTicks -= this.tickCount % 20 == 0 && hasDoctorNearby(level) ? 60 : 1;
		if (this.tickCount % 30 == 0) {
			level.sendParticles(net.minecraft.core.particles.ParticleTypes.CRIT, getX(), getY() + 0.6, getZ(), 3, 0.3, 0.1, 0.3, 0.0);
		}
		if (downedTicks <= 0) {
			downedTicks = 0;
			this.entityData.set(DATA_DOWNED, false);
			this.setHealth(this.getMaxHealth() * 0.25f);
			tellCaptain("I'm back on my feet!");
			CrewPayloads.refresh(getCaptain());
		}
	}

	private boolean hasDoctorNearby(ServerLevel level) {
		if (getRole() == CrewRole.DOCTOR) {
			return false; // Doctors can't treat themselves.
		}
		return !level.getEntitiesOfClass(CrewmateEntity.class, this.getBoundingBox().inflate(16.0),
				other -> other != this && other.getRole() == CrewRole.DOCTOR && !other.isKnockedOut() && sameCrew(this, other)).isEmpty();
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		if (isKnockedOut() && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
			return false; // Nobody kicks a crewmate while they're down.
		}
		return super.hurtServer(level, source, amount);
	}

	@Override
	public boolean canBeSeenAsEnemy() {
		return !isKnockedOut() && super.canBeSeenAsEnemy();
	}

	/** Keeps a knocked-out crewmate still: blocks every other goal that moves, looks or jumps. */
	private class KnockedOutGoal extends Goal {
		KnockedOutGoal() {
			this.setFlags(java.util.EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
		}

		@Override
		public boolean canUse() {
			return isKnockedOut();
		}

		@Override
		public void start() {
			getNavigation().stop();
		}
	}

	// ---------- Gear ----------

	/** Puts worn armor and a non-issued weapon into the bag (when the captain opens it). */
	private void unequipGear() {
		for (EquipmentSlot slot : ARMOR_SLOTS) {
			ItemStack worn = this.getItemBySlot(slot);
			if (!worn.isEmpty()) {
				this.setItemSlot(slot, inventory.addItem(worn)); // Stays worn if the bag is full.
			}
		}
		if (!issuedWeapon) {
			ItemStack leftover = inventory.addItem(this.getMainHandItem());
			if (leftover.isEmpty()) {
				issuedWeapon = true;
				this.setItemSlot(EquipmentSlot.MAINHAND, getRole().weapon());
			} else {
				this.setItemSlot(EquipmentSlot.MAINHAND, leftover);
			}
		}
	}

	/** Puts on the best armor in the bag and holds the best weapon (when the bag closes). */
	public void equipBestGear() {
		for (EquipmentSlot slot : ARMOR_SLOTS) {
			int best = -1;
			double bestValue = armorValue(this.getItemBySlot(slot), slot);
			for (int i = 0; i < inventory.getContainerSize(); i++) {
				ItemStack stack = inventory.getItem(i);
				Equippable equippable = stack.get(DataComponents.EQUIPPABLE);
				if (equippable != null && equippable.slot() == slot && armorValue(stack, slot) > bestValue) {
					best = i;
					bestValue = armorValue(stack, slot);
				}
			}
			if (best >= 0) {
				ItemStack worn = this.getItemBySlot(slot);
				this.setItemSlot(slot, inventory.getItem(best));
				inventory.setItem(best, worn);
				this.setDropChance(slot, 0.0f); // Dropped by dropInventory instead, so nothing drops twice.
			}
		}

		boolean sniper = getRole() == CrewRole.SNIPER;
		int best = -1;
		double bestValue = sniper ? (this.getMainHandItem().isEnchanted() ? 1 : 0) : attackValue(this.getMainHandItem());
		for (int i = 0; i < inventory.getContainerSize(); i++) {
			ItemStack stack = inventory.getItem(i);
			double value = sniper ? (stack.getItem() instanceof BowItem ? (stack.isEnchanted() ? 1 : 0.5) : -1) : attackValue(stack);
			if (value > bestValue) {
				best = i;
				bestValue = value;
			}
		}
		if (best >= 0) {
			ItemStack held = this.getMainHandItem();
			this.setItemSlot(EquipmentSlot.MAINHAND, inventory.getItem(best));
			inventory.setItem(best, issuedWeapon ? ItemStack.EMPTY : held); // The free role weapon just goes away.
			issuedWeapon = false;
		}
		inventory.setChanged();
	}

	private static double armorValue(ItemStack stack, EquipmentSlot slot) {
		if (stack.isEmpty()) {
			return 0;
		}
		ItemAttributeModifiers modifiers = stack.getOrDefault(DataComponents.ATTRIBUTE_MODIFIERS, ItemAttributeModifiers.EMPTY);
		return modifiers.compute(Attributes.ARMOR, 0, slot) + 0.5 * modifiers.compute(Attributes.ARMOR_TOUGHNESS, 0, slot);
	}

	private static double attackValue(ItemStack stack) {
		if (stack.isEmpty()) {
			return 0;
		}
		return stack.getOrDefault(DataComponents.ATTRIBUTE_MODIFIERS, ItemAttributeModifiers.EMPTY)
				.compute(Attributes.ATTACK_DAMAGE, 0, EquipmentSlot.MAINHAND);
	}

	// ---------- Name tag ----------

	/** On players' screens the name tag also shows the level and what they're doing, like "Swordsman Kenji Lv 3 - Waiting". */
	@Override
	public Component getDisplayName() {
		Component name = super.getDisplayName();
		if (!this.level().isClientSide()) {
			return name;
		}
		String doing = isKnockedOut() ? "Knocked out" : isSleeping() ? "Asleep" : switch (getMode()) {
			case FOLLOW -> "Following";
			case WAIT -> "Waiting";
			case WORK -> "Working";
		};
		return name.copy()
				.append(Component.literal(" Lv " + getCrewLevel()).withStyle(ChatFormatting.GOLD))
				.append(Component.literal(" - " + doing).withStyle(isKnockedOut() ? ChatFormatting.RED : ChatFormatting.GRAY));
	}

	// ---------- Talking to the captain ----------

	// Right-click: switch mode. Sneak + right-click: open the crewmate's bag.
	@Override
	public InteractionResult mobInteract(Player player, InteractionHand hand) {
		if (hand != InteractionHand.MAIN_HAND || !(player instanceof ServerPlayer serverPlayer)
				|| !player.getUUID().equals(captainId)) {
			return super.mobInteract(player, hand);
		}

		if (player.isShiftKeyDown()) {
			player.openMenu(new SimpleMenuProvider(
					(containerId, playerInventory, p) -> new ChestMenu(MenuType.GENERIC_9x2, containerId, playerInventory, inventory, 2),
					this.getDisplayName()));
		} else if (isKnockedOut()) {
			serverPlayer.sendSystemMessage(Component.empty().append(this.getDisplayName()).append(" is knocked out and can't take orders.")
					.withStyle(ChatFormatting.GRAY));
		} else {
			setMode(mode.next());
			String job = mode == CrewMode.WORK ? ": " + getRole().job() : "";
			serverPlayer.sendSystemMessage(Component.empty()
					.append(this.getDisplayName())
					.append(" " + mode.message() + job + ".")
					.withStyle(ChatFormatting.AQUA));
		}
		return InteractionResult.SUCCESS;
	}

	// ---------- Sniper shooting ----------

	@Override
	public void performRangedAttack(LivingEntity target, float power) {
		if (!(this.level() instanceof ServerLevel serverLevel)) {
			return;
		}
		Arrow arrow = new Arrow(serverLevel, this, new ItemStack(Items.ARROW), this.getMainHandItem());
		arrow.pickup = AbstractArrow.Pickup.DISALLOWED; // Can't farm free arrows from your sniper.

		double dx = target.getX() - this.getX();
		double dy = target.getY(0.3333) - arrow.getY();
		double dz = target.getZ() - this.getZ();
		double distance = Math.sqrt(dx * dx + dz * dz);
		arrow.shoot(dx, dy + distance * 0.2, dz, 1.6f, 4.0f); // Aim a little up so the arrow arcs onto the target.

		serverLevel.addFreshEntity(arrow);
		this.playSound(SoundEvents.ARROW_SHOOT, 1.0f, 1.0f);
	}

	// ---------- Death and leaving ----------

	@Override
	public void die(DamageSource damageSource) {
		if (this.level() instanceof ServerLevel serverLevel) {
			dropInventory();
			leaveCrew(serverLevel);
		}
		super.die(damageSource);
	}

	/** Drops the bag and any armor or weapon the captain gave them (not the free role weapon). */
	public void dropInventory() {
		Containers.dropContents(this.level(), this, inventory);
		for (EquipmentSlot slot : ARMOR_SLOTS) {
			Containers.dropItemStack(this.level(), getX(), getY(), getZ(), this.getItemBySlot(slot));
			this.setItemSlot(slot, ItemStack.EMPTY);
		}
		if (!issuedWeapon) {
			Containers.dropItemStack(this.level(), getX(), getY(), getZ(), this.getMainHandItem());
			this.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
		}
	}

	// Frees up this role in the captain's crew so they can hire someone new.
	private void leaveCrew(ServerLevel level) {
		if (captainId == null) {
			return;
		}
		ServerPlayer captain = level.getServer().getPlayerList().getPlayer(captainId);
		if (captain == null) {
			CrewRoster.rememberFallen(level.getServer(), captainId, this.getUUID(), this.getName().getString()); // Told when they log in.
			return;
		}
		Crew crew = captain.getAttached(CrewAttachments.CREW);
		CrewRole role = getRole();
		if (crew != null && this.getUUID().equals(crew.member(role))) {
			captain.setAttached(CrewAttachments.CREW, crew.withoutMember(role));
			captain.sendSystemMessage(Component.literal("The " + role.title() + " spot on your crew is open again.")
					.withStyle(ChatFormatting.GRAY));
			CrewPayloads.refresh(captain);
		}
	}

	// ---------- Saving and loading ----------

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putString("Role", getRole().id());
		output.putInt("Variant", getVariantIndex());
		output.putString("Personality", personality.name());
		output.putString("Mode", mode.name());
		output.putInt("Level", crewLevel);
		output.putInt("Xp", xp);
		output.putInt("Downed", downedTicks);
		output.putBoolean("IssuedWeapon", issuedWeapon);
		if (captainId != null) {
			output.store("Captain", UUIDUtil.CODEC, captainId);
		}
		if (workPos != null) {
			output.store("WorkPos", BlockPos.CODEC, workPos);
		}
		inventory.storeAsItemList(output.list("Inventory", ItemStack.CODEC));
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		crewLevel = Math.max(1, Math.min(CrewLevels.MAX_LEVEL, input.getIntOr("Level", 1)));
		xp = input.getIntOr("Xp", 0);
		downedTicks = input.getIntOr("Downed", 0);
		this.entityData.set(DATA_DOWNED, downedTicks > 0);
		issuedWeapon = input.getBooleanOr("IssuedWeapon", true);
		CrewRole role = CrewRole.byId(input.getStringOr("Role", CrewRole.SWORDSMAN.id()));
		setProfile(role != null ? role : CrewRole.SWORDSMAN, input.getIntOr("Variant", 0),
				CrewPersonality.byName(input.getStringOr("Personality", CrewPersonality.STEADY.name())));
		this.captainId = input.read("Captain", UUIDUtil.CODEC).orElse(null);
		this.mode = CrewMode.byName(input.getStringOr("Mode", CrewMode.FOLLOW.name()));
		this.entityData.set(DATA_MODE, mode.ordinal());
		this.workPos = input.read("WorkPos", BlockPos.CODEC).orElse(null);
		inventory.fromItemList(input.listOrEmpty("Inventory", ItemStack.CODEC));
	}

	// ---------- Things TamableAnimal needs that pirates don't use ----------

	@Override
	public boolean isFood(ItemStack stack) {
		return false; // Can't be bred.
	}

	@Override
	public AgeableMob getBreedOffspring(ServerLevel level, AgeableMob otherParent) {
		return null;
	}
}
