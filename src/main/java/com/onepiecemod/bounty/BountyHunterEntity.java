package com.onepiecemod.bounty;

import java.util.UUID;

import net.minecraft.core.UUIDUtil;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

import com.onepiecemod.character.BossAbility;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.CharacterFeature;

/**
 * A bounty hunter: not a Marine, just someone who wants the Berries on your head.
 * Every hunter has a Devil Fruit and uses its moves every few seconds, like a boss does.
 * Like every Devil Fruit user, they get weak in water.
 */
public class BountyHunterEntity extends Monster {
	// Sent to players' games: which outfit to draw.
	private static final EntityDataAccessor<Integer> DATA_SKIN = SynchedEntityData.defineId(BountyHunterEntity.class, EntityDataSerializers.INT);
	public static final int SKINS = 3;

	private static final String[] NAMES = {
			"Iron Fang Rook", "Bloody Sasha", "Twin-Blade Kiro", "Mad Dog Barrow", "Silent Vel",
			"Hawk-Eye Duran", "Red Coat Moss", "Lucky Ines", "Grinning Holt", "Black Glove Tamsin"
	};

	private static final double HUNT_RANGE = 96.0;
	private static final int GIVE_UP_TICKS = 20 * 90;

	private String fruitItem = "onepiece:gomu_gomu_no_mi";
	private int strength = 3; // The threat level they were sent for, 3 to 5. Sets health, damage and rewards.
	private UUID huntedId;
	private int ticksWithoutPirate = 0;
	private int moveCooldown = 80;
	private int movesUsed = 0;

	public BountyHunterEntity(EntityType<? extends BountyHunterEntity> type, Level level) {
		super(type, level);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Monster.createMonsterAttributes()
				.add(Attributes.MAX_HEALTH, 60.0)
				.add(Attributes.ATTACK_DAMAGE, 6.0)
				.add(Attributes.MOVEMENT_SPEED, 0.32)
				.add(Attributes.FOLLOW_RANGE, 48.0)
				.add(Attributes.KNOCKBACK_RESISTANCE, 0.4);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(DATA_SKIN, 0);
	}

	@Override
	protected void registerGoals() {
		this.goalSelector.addGoal(1, new FloatGoal(this));
		this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.2, true));
		this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.8));
		this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 12.0f));
		this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));

		this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
		// Hunters only care about players with a price on their head.
		this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false,
				(target, level) -> target instanceof Player player && Bounty.get(player) > 0));
	}

	// ---------- Setting up ----------

	/** Gives the hunter a fruit, a name and stats for a threat level (3 to 5). Call once when spawning. */
	public void setup(HunterFruit fruit, int threat) {
		this.fruitItem = fruit.item();
		this.strength = Math.max(3, Math.min(5, threat));
		this.entityData.set(DATA_SKIN, getRandom().nextInt(SKINS));

		double health = switch (strength) { case 3 -> 60; case 4 -> 100; default -> 150; };
		double damage = switch (strength) { case 3 -> 6; case 4 -> 8; default -> 11; };
		getAttribute(Attributes.MAX_HEALTH).setBaseValue(health);
		getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(damage);
		setHealth(getMaxHealth());

		setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(strength >= 5 ? Items.NETHERITE_SWORD : strength == 4 ? Items.DIAMOND_SWORD : Items.IRON_SWORD));
		setDropChance(EquipmentSlot.MAINHAND, 0.0f);

		String name = NAMES[getRandom().nextInt(NAMES.length)];
		setCustomName(Component.literal(name + " (" + fruit.name() + ")"));
		setCustomNameVisible(true);
	}

	public void setHunted(Player pirate) {
		this.huntedId = pirate.getUUID();
		this.setTarget(pirate);
	}

	public int getSkin() {
		return this.entityData.get(DATA_SKIN);
	}

	public HunterFruit getFruit() {
		HunterFruit fruit = HunterFruit.byItem(fruitItem);
		return fruit != null ? fruit : HunterFruit.all().get(0);
	}

	public int getStrength() {
		return strength;
	}

	/** How much your bounty rises for beating this hunter. */
	public long bountyReward() {
		// Close to a Marine Captain (3M), so hunting hunters can't race your bounty ahead of the story.
		return switch (strength) { case 3 -> 3_000_000L; case 4 -> 6_000_000L; default -> 12_000_000L; };
	}

	// ---------- Fighting ----------

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);

		// The sea hates Devil Fruit users: in the sea or touching Seastone they lose their strength and their power.
		if (com.onepiecemod.power.SeaWeakness.isDrained(this)) {
			addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 40, 1));
			addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 2));
			return;
		}

		// Use a Devil Fruit move every few seconds, faster when hurt. Alternate between the two moves.
		LivingEntity target = getTarget();
		if (target != null && target.isAlive() && distanceTo(target) < 16) {
			if (--moveCooldown <= 0) {
				HunterFruit fruit = getFruit();
				movesUsed++;
				BossAbility.use(movesUsed % 2 == 0 ? fruit.power2() : fruit.power(), this, target, level);
				moveCooldown = getHealth() < getMaxHealth() / 2 ? 60 : 90;
			}
		}

		// Chase the pirate we came for. If they're gone for 90 seconds, give up and leave.
		if (huntedId == null || this.tickCount % 20 != 0) {
			return;
		}
		ServerPlayer pirate = level.getServer().getPlayerList().getPlayer(huntedId);
		boolean pirateNearby = pirate != null && pirate.level() == level && pirate.isAlive()
				&& !pirate.isSpectator() && pirate.distanceToSqr(this) < HUNT_RANGE * HUNT_RANGE;
		if (pirateNearby) {
			ticksWithoutPirate = 0;
			if (getTarget() == null && !pirate.isCreative()) {
				setTarget(pirate);
			}
		} else {
			ticksWithoutPirate += 20;
			if (ticksWithoutPirate >= GIVE_UP_TICKS) {
				level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 1, getZ(), 20, 0.4, 0.6, 0.4, 0.02);
				discard();
			}
		}
	}

	// ---------- Loot, saving ----------

	@Override
	protected void dropCustomDeathLoot(ServerLevel level, DamageSource source, boolean recentlyHit) {
		super.dropCustomDeathLoot(level, source, recentlyHit);
		spawnAtLocation(level, new ItemStack(CharacterFeature.BERRY, strength * 5));
		// Now and then the hunter's own Devil Fruit drops.
		if (getRandom().nextFloat() < 0.10f) {
			ItemStack fruit = CharacterData.stack(fruitItem, 1);
			if (!fruit.isEmpty()) {
				spawnAtLocation(level, fruit);
			}
		}
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putString("Fruit", fruitItem);
		output.putInt("Strength", strength);
		output.putInt("Skin", getSkin());
		if (huntedId != null) {
			output.store("Hunted", UUIDUtil.CODEC, huntedId);
		}
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		this.fruitItem = input.getStringOr("Fruit", fruitItem);
		this.strength = input.getIntOr("Strength", 3);
		this.entityData.set(DATA_SKIN, input.getIntOr("Skin", 0));
		this.huntedId = input.read("Hunted", UUIDUtil.CODEC).orElse(null);
	}
}
