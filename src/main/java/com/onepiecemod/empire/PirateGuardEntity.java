package com.onepiecemod.empire;

import java.util.EnumSet;
import java.util.UUID;

import net.minecraft.core.BlockPos;
import net.minecraft.core.UUIDUtil;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.MoveTowardsRestrictionGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.goal.target.TargetGoal;
import net.minecraft.world.entity.monster.Creeper;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

import com.onepiecemod.crew.CrewmateEntity;

/**
 * A pirate who lives in your kingdom and guards it, like an iron golem guards a village.
 * They patrol near the Kingdom Flag and fight monsters, Marines, and anyone who hurts their ruler.
 * Better titles give them better swords and armor. If the flag is broken, they leave.
 */
public class PirateGuardEntity extends PathfinderMob {
	private BlockPos home;
	private UUID ruler;
	private Title gear = Title.NONE;

	public PirateGuardEntity(EntityType<? extends PirateGuardEntity> type, Level level) {
		super(type, level);
		setPersistenceRequired(); // Guards never despawn on their own.
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Mob.createMobAttributes()
				.add(Attributes.MAX_HEALTH, 30.0)
				.add(Attributes.MOVEMENT_SPEED, 0.3)
				.add(Attributes.ATTACK_DAMAGE, 4.0)
				.add(Attributes.KNOCKBACK_RESISTANCE, 0.4)
				.add(Attributes.FOLLOW_RANGE, 32.0);
	}

	public BlockPos home() {
		return home;
	}

	public UUID getRuler() { return ruler; } // Used by multiplayer alliances.

	/** Called by the Kingdom Flag when it recruits this guard. */
	void setHome(BlockPos flag, UUID ruler, Title title) {
		this.home = flag;
		this.ruler = ruler;
		setHomeTo(flag, (int) KingdomFlagBlockEntity.RADIUS);
		equip(title);
	}

	/** Health, damage and gear for the ruler's title. */
	void equip(Title title) {
		this.gear = title;
		Item sword;
		Item chest;
		Item helmet;
		switch (title) {
			case EMPEROR -> {
				sword = Items.IRON_SWORD;
				chest = Items.IRON_CHESTPLATE;
				helmet = Items.CHAINMAIL_HELMET;
			}
			case PIRATE_KING -> {
				sword = Items.DIAMOND_SWORD;
				chest = Items.IRON_CHESTPLATE;
				helmet = Items.IRON_HELMET;
			}
			case KING_OF_THE_WORLD -> {
				sword = Items.NETHERITE_SWORD;
				chest = Items.DIAMOND_CHESTPLATE;
				helmet = Items.DIAMOND_HELMET;
			}
			default -> {
				sword = Items.STONE_SWORD;
				chest = Items.LEATHER_CHESTPLATE;
				helmet = Items.LEATHER_HELMET;
			}
		}
		setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(sword));
		setItemSlot(EquipmentSlot.CHEST, new ItemStack(chest));
		setItemSlot(EquipmentSlot.HEAD, new ItemStack(helmet));
		for (EquipmentSlot slot : new EquipmentSlot[] {EquipmentSlot.MAINHAND, EquipmentSlot.CHEST, EquipmentSlot.HEAD}) {
			setDropChance(slot, 0.0f); // No free armor from your own guards.
		}
		getAttribute(Attributes.MAX_HEALTH).setBaseValue(30.0 + 10.0 * title.ordinal());
		getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(4.0 + 1.5 * title.ordinal());
		setHealth(getMaxHealth());
		setCustomName(Component.literal(title == Title.NONE ? "Pirate Guard" : title.displayName + "'s Guard"));
	}

	// The "brain": lower numbers are more important.
	@Override
	protected void registerGoals() {
		this.goalSelector.addGoal(1, new FloatGoal(this));
		this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.1, true));
		this.goalSelector.addGoal(3, new MoveTowardsRestrictionGoal(this, 1.0)); // Walk back if they wander off.
		this.goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.6));
		this.goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 8.0f));
		this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));

		this.targetSelector.addGoal(1, new DefendRulerGoal(this));
		this.targetSelector.addGoal(2, new HurtByTargetGoal(this, PirateGuardEntity.class).setAlertOthers());
		// Like iron golems: attack monsters (Marines count), but leave creepers alone.
		this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, Mob.class, 5, true, false,
				(target, level) -> target instanceof Enemy && !(target instanceof Creeper)));
	}

	/** Guards never fight their ruler or the ruler's crew. */
	@Override
	public boolean canAttack(LivingEntity target) {
		if (ruler != null && (ruler.equals(target.getUUID()) || ruler.equals(CrewmateEntity.captainOf(target)))) {
			return false;
		}
		if (target instanceof PirateGuardEntity other && other.ruler != null && other.ruler.equals(ruler)) {
			return false;
		}
		return super.canAttack(target);
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (tickCount % 100 != 0) {
			return;
		}
		// No flag, no kingdom: the guard goes home.
		if (home == null || (level.isLoaded(home) && !level.getBlockState(home).is(EmpireFeature.KINGDOM_FLAG))) {
			discard();
			return;
		}
		// The ruler earned a new title: hand out the new gear.
		Title current = Title.byLevel(EmpireData.holders(level.getServer()).getOrDefault(String.valueOf(ruler), 0));
		if (current != gear) {
			equip(current);
		}
		if (getHealth() < getMaxHealth()) {
			heal(1.0f); // Slowly patch themselves up.
		}
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		if (home != null) {
			output.putLong("Home", home.asLong());
		}
		if (ruler != null) {
			output.store("Ruler", UUIDUtil.CODEC, ruler);
		}
		output.putInt("Gear", gear.ordinal());
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		long packed = input.getLongOr("Home", Long.MIN_VALUE);
		home = packed == Long.MIN_VALUE ? null : BlockPos.of(packed);
		ruler = input.read("Ruler", UUIDUtil.CODEC).orElse(null);
		gear = Title.byLevel(input.getIntOr("Gear", 0));
		if (home != null) {
			setHomeTo(home, (int) KingdomFlagBlockEntity.RADIUS);
		}
	}

	/** Attack whoever is hurting the ruler, if the ruler is in the kingdom. */
	private static class DefendRulerGoal extends TargetGoal {
		private final PirateGuardEntity guard;
		private LivingEntity attacker;

		DefendRulerGoal(PirateGuardEntity guard) {
			super(guard, false);
			this.guard = guard;
			setFlags(EnumSet.of(Flag.TARGET));
		}

		@Override
		public boolean canUse() {
			if (guard.ruler == null || guard.home == null || !(guard.level() instanceof ServerLevel level)) {
				return false;
			}
			ServerPlayer player = level.getServer().getPlayerList().getPlayer(guard.ruler);
			if (player == null || player.level() != level || !player.blockPosition().closerThan(guard.home, KingdomFlagBlockEntity.RADIUS)) {
				return false;
			}
			attacker = player.getLastHurtByMob();
			return attacker != null && attacker.isAlive() && player.tickCount - player.getLastHurtByMobTimestamp() < 100
					&& guard.canAttack(attacker);
		}

		@Override
		public void start() {
			guard.setTarget(attacker);
			super.start();
		}
	}
}
