package com.onepiecemod.character;

import com.onepiecemod.util.Motion;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.ExperienceOrb;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.BossEvent;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
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
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.trading.ItemCost;
import net.minecraft.world.item.trading.Merchant;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.pathfinder.Path;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

import java.util.List;

/**
 * Every One Piece character in the world is one of these. It reads its stats from CharacterData.
 * - Boss version: hostile, has a boss health bar, uses a special attack, drops Berries and its Devil Fruit.
 * - Friendly version: stands still, and right-clicking it opens a shop (traders) or gives a quest.
 */
public class CharacterEntity extends PathfinderMob implements Merchant {
	// Synced data is sent to every player's game, so the renderer knows which skin to draw.
	private static final EntityDataAccessor<String> CHARACTER_ID = SynchedEntityData.defineId(CharacterEntity.class, EntityDataSerializers.STRING);
	private static final EntityDataAccessor<Boolean> IS_BOSS = SynchedEntityData.defineId(CharacterEntity.class, EntityDataSerializers.BOOLEAN);
	// Monster form (Kaido's dragon...) and the tick it began, so the renderer can draw it and play the roar.
	private static final EntityDataAccessor<String> FORM = SynchedEntityData.defineId(CharacterEntity.class, EntityDataSerializers.STRING);
	private static final EntityDataAccessor<Integer> FORM_SINCE = SynchedEntityData.defineId(CharacterEntity.class, EntityDataSerializers.INT);
	/** How big each monster form's body is, in blocks (width, height), whatever the character's own size. */
	private static final java.util.Map<String, float[]> FORM_SIZE = java.util.Map.of(
			"seiryu", new float[] {3.0f, 3.2f}, "pteranodon", new float[] {2.6f, 2.4f}, "venom_demon", new float[] {2.6f, 4.8f},
			"brachiosaurus", new float[] {3.2f, 6.5f}, "gyuki", new float[] {4.6f, 4.2f},
			"imu_demon", new float[] {2.4f, 5.2f}, "imu_beast", new float[] {9.0f, 34.0f}, "nidhogg", new float[] {10.0f, 36.0f});

	private ServerBossEvent bossBar;
	private boolean goalsAdded = false;
	private int abilityCooldown = 60;
	private Player tradingPlayer; // null when nobody is trading
	private MerchantOffers offers;
	private int offersCap = 5; // Highest shop level the current offers were built for (story gate, per player).

	// Trader levels work like villagers: 1 Novice, 2 Apprentice, 3 Journeyman, 4 Expert, 5 Master.
	// XP needed to reach the next level (same numbers as villagers, so the trade screen's XP bar matches).
	private static final int[] XP_FOR_NEXT_LEVEL = {0, 10, 70, 150, 250};
	private static final int RESTOCK_TICKS = 24000; // One Minecraft day.
	private int tradeLevel = 1;
	private int tradeXp = 0;
	private boolean levelUpPending = false;
	private int restockTimer = RESTOCK_TICKS;

	// Boss difficulty. Beat a boss and its Wanted Poster gives you the next one.
	public static final int NORMAL = 0;
	public static final int HARD = 1;
	public static final int EXPERT = 2;
	private static final String[] DIFFICULTY_NAMES = {"", "Hard", "Expert"};
	private static final float[] HEALTH_MULTIPLIER = {1.0f, 2.0f, 3.5f};
	private static final float[] DAMAGE_MULTIPLIER = {1.0f, 1.5f, 2.0f};
	private static final double[] BONUS_ARMOR = {0.0, 6.0, 12.0};
	private static final int[] BERRY_MULTIPLIER = {1, 2, 4};
	private static final int[] XP_REWARD = {20, 60, 150};
	/** Minecraft caps max health at 1024. Bosses meant to be tougher take less damage instead. */
	private static final float HEALTH_CAP = 1024.0f;
	/** Beating a boss again at a difficulty you've already won gives this share of the Berries, and no fruit or prizes. */
	private static final float REPEAT_BERRY_SHARE = 0.15f; // Default of the settings file's rematch_berry_share.
	private boolean firstWin = true;
	private int difficulty = NORMAL;
	/** Legend Ladder rung (1-5) for Emperor and Admiral rematches past Expert, 0 = not a ladder fight. See TitanLadder. */
	private int legendRung = 0;
	/** Raids and New Game+ make a boss tougher than its data file says (1 = as written). */
	private float healthScale = 1.0f;
	private int abilitiesUsed = 0;
	private boolean enraged = false;

	// Boss brain: bosses guard their spot, heal up when left alone, and come after you when you hide out of reach.
	/** How far a boss chases you from its spot. */
	private static final int BOSS_HOME_RADIUS = 32;
	/** Ticks without a target before a boss starts healing (30 seconds). */
	private static final int CALM_BEFORE_HEAL = 600;
	private int calmTicks = 0;
	private int stuckTicks = 0;
	private int reachTries = 0;

	// Boss fight: phases at 66% and 33% health, warnings before attacks, signature moves and a called crew.
	private int phase = 0; // 0 = not worked out yet (fresh spawn or just loaded)
	private final BossStrikes strikes = new BossStrikes();
	private String windupPower = null; // The attack the boss is winding up, or null.
	private int windupTicks = 0;
	private Vec3 windupMark = null; // Where an aimed attack will land (null for attacks around the boss).
	private boolean crewCalled = false;
	private final List<java.util.UUID> minions = new java.util.ArrayList<>();
	private static final String SIGNATURE = "signature";
	/** Emperors and Admirals: phase mechanics, phase 4 and the ultimate. */
	private final TitanFight titan = new TitanFight(strikes);

	public CharacterEntity(EntityType<? extends CharacterEntity> type, Level level) {
		super(type, level);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Mob.createMobAttributes()
				.add(Attributes.MAX_HEALTH, 40.0)
				.add(Attributes.ATTACK_DAMAGE, 4.0)
				.add(Attributes.MOVEMENT_SPEED, 0.3)
				.add(Attributes.FOLLOW_RANGE, 32.0)
				.add(Attributes.KNOCKBACK_RESISTANCE, 0.5);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(CHARACTER_ID, "luffy");
		builder.define(IS_BOSS, false);
		builder.define(FORM, "");
		builder.define(FORM_SINCE, 0);
	}

	/** The monster form this boss is in ("seiryu", "leopard"...), or "" when it looks like a person. */
	public String getForm() {
		return this.entityData.get(FORM);
	}

	/** Ticks since the monster form began (the renderer plays the roar during the first second or so). */
	public int getFormAge() {
		return this.tickCount - this.entityData.get(FORM_SINCE);
	}

	private void setForm(String form) {
		this.entityData.set(FORM, form);
		this.entityData.set(FORM_SINCE, this.tickCount);
		refreshDimensions();
	}

	@Override
	public void onSyncedDataUpdated(EntityDataAccessor<?> key) {
		super.onSyncedDataUpdated(key);
		if (FORM.equals(key)) {
			refreshDimensions(); // A dragon needs a much bigger body to hit than a person.
		}
	}

	@Override
	protected net.minecraft.world.entity.EntityDimensions getDefaultDimensions(net.minecraft.world.entity.Pose pose) {
		float[] size = FORM_SIZE.get(getForm());
		if (size == null) {
			return super.getDefaultDimensions(pose);
		}
		// The game multiplies this by the character's size, so divide it out: a form is the same size on everyone.
		float scale = Math.max(0.1f, getScale());
		return net.minecraft.world.entity.EntityDimensions.scalable(size[0] / scale, size[1] / scale);
	}

	public String getCharacterId() {
		return this.entityData.get(CHARACTER_ID);
	}

	/** False when everyone who beat this boss had already won at this difficulty (a rematch). Set as it dies. */
	public boolean isFirstWin() {
		return firstWin;
	}

	/**
	 * Makes this boss tougher than characters.json says (raids, New Game+). Health past the 1024 cap turns into
	 * smaller hits, like any big boss. Keeps the boss's current share of health.
	 */
	public void setHealthScale(float scale) {
		float share = getHealth() / getMaxHealth();
		this.healthScale = Math.max(0.1f, scale);
		getAttribute(Attributes.MAX_HEALTH).setBaseValue(Math.min(HEALTH_CAP, wantedHealth()));
		setHealth(getMaxHealth() * share);
	}

	public float getHealthScale() {
		return healthScale;
	}

	/** The health this boss really has to lose, counting the part above the 1024 cap. */
	public float effectiveMaxHealth() {
		return Math.max(getMaxHealth(), wantedHealth());
	}

	public boolean isBoss() {
		return this.entityData.get(IS_BOSS);
	}

	public int getDifficulty() {
		return difficulty;
	}

	public static String difficultyName(int difficulty) {
		return DIFFICULTY_NAMES[difficulty];
	}

	/** "Kaido", "Kaido (Hard)", "Kaido (Expert)" or "Kaido (Legend III)". */
	private Component displayName() {
		String name = getData().name;
		if (legendRung > 0) {
			return Component.literal(name + " (" + TitanLadder.rungName(legendRung) + ")");
		}
		return Component.literal(difficulty == NORMAL ? name : name + " (" + DIFFICULTY_NAMES[difficulty] + ")");
	}

	public int getLegendRung() {
		return legendRung;
	}

	/** A Legend Ladder fight: Expert, made tougher per rung. Call right after setCharacter. 0 = a plain Expert fight. */
	public void setLegendRung(int rung) {
		this.legendRung = Math.max(0, Math.min(TitanLadder.MAX_RUNG, rung));
		setDifficulty(EXPERT);
	}

	/** Makes a boss tougher. Call right after setCharacter. */
	public void setDifficulty(int difficulty) {
		this.difficulty = Math.max(NORMAL, Math.min(EXPERT, difficulty));
		CharacterData data = getData();
		getAttribute(Attributes.MAX_HEALTH).setBaseValue(Math.min(HEALTH_CAP, wantedHealth()));
		getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(data.damage * DAMAGE_MULTIPLIER[this.difficulty] * TitanLadder.damageFactor(legendRung) * com.onepiecemod.config.ModConfig.bossDamage()
				- CharacterData.weaponBonus(getMainHandItem()));
		getAttribute(Attributes.ARMOR).setBaseValue(BONUS_ARMOR[this.difficulty]);
		setHealth(getMaxHealth());
		setCustomName(displayName());
		updateBossBar();
	}

	private void updateBossBar() {
		if (bossBar == null) {
			return;
		}
		bossBar.setName(displayName());
		if (legendRung > 0) {
			bossBar.setColor(BossEvent.BossBarColor.PURPLE);
			bossBar.setOverlay(BossEvent.BossBarOverlay.NOTCHED_20);
		} else if (difficulty == EXPERT) {
			bossBar.setColor(BossEvent.BossBarColor.RED);
			bossBar.setOverlay(BossEvent.BossBarOverlay.NOTCHED_10);
		} else if (difficulty == HARD) {
			bossBar.setColor(BossEvent.BossBarColor.PINK);
			bossBar.setOverlay(BossEvent.BossBarOverlay.NOTCHED_6);
		}
	}

	public CharacterData getData() {
		CharacterData data = CharacterData.get(getCharacterId());
		return data != null ? data : CharacterData.get("luffy");
	}

	/** Turns this mob into a character. Called once when it is first spawned. */
	public void setCharacter(String id, boolean boss) {
		applyCharacter(id, boss);
		CharacterData data = getData();

		// Fresh spawn: set stats from the data file and fill up health.
		getAttribute(Attributes.MAX_HEALTH).setBaseValue(Math.min(HEALTH_CAP, wantedHealth()));
		getAttribute(Attributes.SCALE).setBaseValue(data.scale);
		setHealth(getMaxHealth());

		setItemSlot(EquipmentSlot.MAINHAND, CharacterData.stack(data.heldItem, 1));
		setItemSlot(EquipmentSlot.OFFHAND, CharacterData.stack(data.offhandItem, 1));
		// Their signature weapons (Yoru, Enma...) are for show: they only drop through the boss loot, never as gear.
		setDropChance(EquipmentSlot.MAINHAND, 0.0F);
		setDropChance(EquipmentSlot.OFFHAND, 0.0F);
		// data.damage is the whole hit, so take back what the held weapon adds.
		getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(data.damage * (isBoss() ? com.onepiecemod.config.ModConfig.bossDamage() : 1.0)
				- CharacterData.weaponBonus(getMainHandItem()));
		setCustomName(Component.literal(data.name));
		setCustomNameVisible(true);
		setPersistenceRequired(); // Never despawn.
	}

	/** The part of setCharacter that also has to happen when the world is loaded again. */
	private void applyCharacter(String id, boolean boss) {
		this.entityData.set(CHARACTER_ID, id);
		this.entityData.set(IS_BOSS, boss);

		if (!level().isClientSide()) {
			// Life-size height from characters.json, also for characters made with /summon or saved by an older version.
			getAttribute(Attributes.SCALE).setBaseValue(getData().scale);
		}
		if (level().isClientSide() || goalsAdded) {
			return;
		}
		goalsAdded = true;

		if (boss) {
			this.goalSelector.addGoal(0, new FloatGoal(this));
			this.goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.0, true));
			this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.7) {
				@Override
				public boolean canUse() {
					// Only strolls around its own spot; bossBrain walks it back when it ends up further away.
					return nearHome(10.0) && super.canUse();
				}
			});
			this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 12.0f));
			this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));
			this.targetSelector.addGoal(1, new HurtByTargetGoal(this));
			this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));

			CharacterData data = getData();
			BossEvent.BossBarColor color = switch (data.tier) {
				case 5 -> BossEvent.BossBarColor.RED;
				case 4 -> BossEvent.BossBarColor.PURPLE;
				case 3 -> BossEvent.BossBarColor.YELLOW;
				default -> BossEvent.BossBarColor.WHITE;
			};
			bossBar = new ServerBossEvent(java.util.UUID.randomUUID(), Component.literal(data.name), color, BossEvent.BossBarOverlay.PROGRESS);
		} else {
			// Shopkeepers and quest givers stay where you put them and look at nearby players.
			this.goalSelector.addGoal(0, new FloatGoal(this));
			this.goalSelector.addGoal(1, new LookAtPlayerGoal(this, Player.class, 8.0f));
			this.goalSelector.addGoal(2, new RandomLookAroundGoal(this));
		}
	}

	// ---- Saving and loading ----

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putString("Character", getCharacterId());
		output.putBoolean("Boss", isBoss());
		output.putInt("TradeLevel", tradeLevel);
		output.putInt("TradeXp", tradeXp);
		output.putInt("Difficulty", difficulty);
		output.putInt("LegendRung", legendRung);
		output.putFloat("HealthScale", healthScale);
		output.putString("BossForm", getForm());
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		applyCharacter(input.getStringOr("Character", "luffy"), input.getBooleanOr("Boss", false));
		tradeLevel = input.getIntOr("TradeLevel", 1);
		tradeXp = input.getIntOr("TradeXp", 0);
		difficulty = input.getIntOr("Difficulty", NORMAL);
		legendRung = input.getIntOr("LegendRung", 0);
		healthScale = input.getFloatOr("HealthScale", 1.0f);
		setForm(input.getStringOr("BossForm", ""));
		updateBossBar();
	}

	@Override
	public boolean removeWhenFarAway(double distance) {
		return false;
	}

	// ---- Fighting ----

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		// Friendly characters can't be hurt (except by /kill).
		if (!isBoss() && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
			return false;
		}
		// Bosses never choke inside walls: the giant ones (Loki, Imu) are taller than most places they stand.
		if (source.is(net.minecraft.world.damagesource.DamageTypes.IN_WALL)) {
			return false;
		}
		com.onepiecemod.cutscene.BossIntros.interrupt(this); // A hit ends the intro: the fight is on.
		// Above 1024 health, hits shrink instead, so a 3000-health boss still takes 3000 damage to beat.
		float wanted = wantedHealth();
		if (wanted > HEALTH_CAP) {
			amount *= HEALTH_CAP / wanted;
		}
		return super.hurtServer(level, source, amount);
	}

	/** The health this character should have at its difficulty, from the data file (may be above the 1024 cap). */
	private float wantedHealth() {
		return getData().health * (isBoss() ? HEALTH_MULTIPLIER[difficulty] * TitanLadder.healthFactor(legendRung) * (float) com.onepiecemod.config.ModConfig.bossHealth() * healthScale : 1.0f);
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (!isBoss()) {
			if (tradingPlayer != null) {
				getNavigation().stop();
			} else {
				traderTick(level);
			}
			return;
		}

		if (bossBar != null) {
			bossBar.setProgress(getHealth() / getMaxHealth());
			if (this.tickCount % 10 == 0) {
				updateBossBarPlayers(level);
			}
		}

		// Expert bosses fly into a rage at 30% health: stronger and faster until the end.
		if (difficulty == EXPERT && !enraged && getHealth() < getMaxHealth() * 0.3f) {
			enraged = true;
			addEffect(new MobEffectInstance(MobEffects.STRENGTH, Integer.MAX_VALUE, 1));
			addEffect(new MobEffectInstance(MobEffects.SPEED, Integer.MAX_VALUE, 1));
			level.sendParticles(ParticleTypes.ANGRY_VILLAGER, getX(), getY() + getBbHeight(), getZ(), 20, 0.8, 0.5, 0.8, 0.0);
			level.playSound(null, blockPosition(), com.onepiecemod.sound.BossSounds.ENRAGE, net.minecraft.sounds.SoundSource.HOSTILE, 2.5f, 1.0f);
			for (ServerPlayer player : bossBar.getPlayers()) {
				player.sendSystemMessage(Component.literal(getData().name + " is enraged!").withStyle(ChatFormatting.DARK_RED));
			}
		}

		if (com.onepiecemod.cutscene.BossIntros.holding(this)) { // Its intro is playing: stand and stare, no attacks yet.
			getNavigation().stop();
			if (getTarget() != null) {
				getLookControl().setLookAt(getTarget(), 30f, 30f);
			}
			return;
		}
		boolean outOfReach = bossBrain(level);
		strikes.tick(this, level);
		updatePhase(level);
		if (TitanFight.isTitan(getCharacterId())) {
			titan.tick(this, level, Math.max(1, phase), legendRung);
		}
		if (windupPower != null) {
			tickWindup(level);
			return;
		}

		// Every few seconds, use a special attack. Faster when below half health, and faster on Hard and Expert.
		// A boss that can't walk to you still uses its power from further away, so hiding on a pillar doesn't work.
		LivingEntity target = getTarget();
		double powerRange = outOfReach && getSensing().hasLineOfSight(target) ? 32 : 16;
		if (target != null && target.isAlive() && distanceTo(target) < powerRange) {
			abilityCooldown--;
			if (!crewCalled && com.onepiecemod.cutscene.BossIntros.start(this, level)) {
				return; // First time you meet this boss: its intro plays first (BossIntros), then the fight.
			}
			if (!crewCalled) {
				crewCalled = true;
				level.playSound(null, blockPosition(), com.onepiecemod.sound.BossSounds.INTRO, net.minecraft.sounds.SoundSource.HOSTILE, 3.0f, 1.0f); // The fight starts.
				callCrew(level, target);
			}
			if (abilityCooldown <= 0) {
				startWindup(target, level);
				boolean hurt = getHealth() < getMaxHealth() / 2;
				abilityCooldown = switch (difficulty) {
					case EXPERT -> hurt ? 35 : 50;
					case HARD -> hurt ? 45 : 70;
					default -> hurt ? 60 : 100;
				};
			}
		}
	}

	/** Is this boss within this many blocks of its spot (or has it no spot)? */
	private boolean nearHome(double range) {
		return !hasHome() || distanceToSqr(Vec3.atBottomCenterOf(getHomePosition())) < range * range;
	}

	/**
	 * The boss's thinking each tick, besides plain walking and hitting.
	 * Returns true while the target is out of reach (up a pillar, across water, too far from the boss's spot).
	 */
	private boolean bossBrain(ServerLevel level) {
		// Famous Marines and raid commanders sent after you roam; every other boss guards the spot it first stood on.
		boolean roams = entityTags().contains(com.onepiecemod.bounty.MarineHunters.HUNTER_TAG);
		if (!roams && !hasHome()) {
			setHomeTo(blockPosition(), BOSS_HOME_RADIUS);
		}
		LivingEntity target = getTarget();
		if (target == null || !target.isAlive()) {
			stuckTicks = 0;
			reachTries = 0;
			calmTicks++;
			if (!roams) {
				calmDown(level);
			}
			return false;
		}
		calmTicks = 0;

		// Ran far away from the boss's spot: it gives up and goes home.
		if (hasHome() && target.distanceToSqr(Vec3.atBottomCenterOf(getHomePosition())) > 48 * 48) {
			setTarget(null);
			return false;
		}
		double distance = distanceTo(target);
		Path path = getNavigation().getPath();
		boolean walkable = distance <= 4.0 || (path != null && path.canReach());
		boolean inHome = !hasHome() || isWithinHome(target.blockPosition());
		if (walkable && inHome) {
			stuckTicks = 0;
			reachTries = 0;
			return false;
		}
		stuckTicks++;
		// After 2 seconds of not getting closer, leap at the target, and if that didn't help, dash right next to it.
		if (stuckTicks >= 40 && inHome) {
			stuckTicks = 0;
			if (reachTries++ % 2 == 0 && distance < 12 && Math.abs(target.getY() - getY()) < 8) {
				leapAt(level, target);
			} else {
				dashTo(level, target);
			}
		}
		return stuckTicks > 20 || !inHome;
	}

	/** A big jump toward the target, high enough to land on a short pillar. */
	private void leapAt(ServerLevel level, LivingEntity target) {
		Vec3 flat = new Vec3(target.getX() - getX(), 0, target.getZ() - getZ());
		double height = target.getY() - getY();
		Vec3 push = flat.lengthSqr() < 0.01 ? Vec3.ZERO : flat.normalize().scale(Math.min(1.6, 0.25 + flat.length() * 0.12));
		setDeltaMovement(push.x, Math.max(0.5, Math.min(1.4, 0.55 + height * 0.14)), push.z);
		needsSync = true;
		com.onepiecemod.anim.CombatAnims.play(this, com.onepiecemod.anim.Anim.POUNCE);
		level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 0.1, getZ(), 12, 0.6, 0.1, 0.6, 0.05);
		playSound(com.onepiecemod.sound.BossSounds.LEAP, 1.2f, 1.0f);
	}

	/** Like Soru: the boss vanishes and appears right beside the target, if there's room for it there. */
	private void dashTo(ServerLevel level, LivingEntity target) {
		Vec3 toBoss = new Vec3(getX() - target.getX(), 0, getZ() - target.getZ());
		Vec3 side = toBoss.lengthSqr() < 0.01 ? new Vec3(1, 0, 0) : toBoss.normalize();
		for (Vec3 spot : List.of(target.position().add(side.scale(1.5)), target.position().subtract(side.scale(1.5)), target.position())) {
			if (level.noCollision(this, getBoundingBox().move(spot.subtract(position())))) {
				level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + 1, getZ(), 15, 0.4, 0.8, 0.4, 0.02);
				teleportTo(spot.x, spot.y, spot.z);
				getNavigation().stop();
				level.playSound(null, blockPosition(), com.onepiecemod.sound.StyleSounds.SORU, net.minecraft.sounds.SoundSource.HOSTILE, 1.0f, 1.0f);
				return;
			}
		}
	}

	/** Nobody to fight: walk back to the spot, and after 30 seconds heal back up and cool off. */
	private void calmDown(ServerLevel level) {
		if (calmTicks > 100 && hasHome() && !nearHome(12.0)) {
			Vec3 home = Vec3.atBottomCenterOf(getHomePosition());
			if (!nearHome(48.0)) {
				teleportTo(home.x, home.y, home.z);
			} else if (getNavigation().isDone()) {
				getNavigation().moveTo(home.x, home.y, home.z, 0.9);
			}
		}
		if (calmTicks == CALM_BEFORE_HEAL) {
			// The fight is over: the rage wears off and the attack pattern starts from the top.
			if (enraged) {
				enraged = false;
				removeEffect(MobEffects.STRENGTH);
				removeEffect(MobEffects.SPEED);
			}
			abilitiesUsed = 0;
			abilityCooldown = 60;
			// Back to the start of the fight: phase 1, no crew, nothing incoming.
			phase = 0;
			crewCalled = false;
			windupPower = null;
			strikes.clear();
			titan.clear();
			dismissCrew(level);
			if (!getForm().isEmpty()) {
				setForm(""); // Back to human shape.
				level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 1, getZ(), 30, 0.8, 1.0, 0.8, 0.02);
			}
		}
		if (calmTicks >= CALM_BEFORE_HEAL && calmTicks % 20 == 0 && getHealth() < getMaxHealth()) {
			heal(getMaxHealth() * 0.05f); // Full health again in about 20 seconds.
			level.sendParticles(ParticleTypes.HAPPY_VILLAGER, getX(), getY() + getBbHeight() * 0.6, getZ(), 3, 0.4, 0.4, 0.4, 0.0);
		}
	}

	// ---- Boss fight: phases, warnings, signature moves, crew ----

	/** Phase 1 above 66% health, phase 2 above 33%, then phase 3. Emperors and Admirals awaken into phase 4 below 12%. */
	private int phaseFor() {
		float share = getHealth() / getMaxHealth();
		if (share < 0.12f && TitanFight.isTitan(getCharacterId())) {
			return 4;
		}
		return share < 0.33f ? 3 : share < 0.66f ? 2 : 1;
	}

	private void updatePhase(ServerLevel level) {
		int now = phaseFor();
		if (phase == 0) {
			phase = now; // Just loaded: carry on quietly.
			return;
		}
		if (now <= phase) {
			return;
		}
		phase = now;
		BossFightData fight = BossFightData.get(getCharacterId());
		String line = now == 2 ? fight.phase2 : now == 3 ? fight.phase3 : fight.phase4;
		// The boss roars, throws everyone back a little, and says its line.
		com.onepiecemod.anim.CombatAnims.play(this, com.onepiecemod.anim.Anim.ROAR);
		com.onepiecemod.fx.MoveFx.shockwave(level, position(), 6, 0xFFFFFFFF, 0xFFE03030);
		level.playSound(null, blockPosition(), com.onepiecemod.sound.BossSounds.PHASE, net.minecraft.sounds.SoundSource.HOSTILE, 2.5f, 1.0f);
		for (Player player : level.getEntitiesOfClass(Player.class, getBoundingBox().inflate(6.0), p -> !p.isSpectator())) {
			Vec3 away = player.position().subtract(position()).multiply(1, 0, 1).normalize().scale(1.2);
			player.setDeltaMovement(away.x, 0.4, away.z);
			Motion.sync(player);
		}
		if (bossBar != null) {
			for (ServerPlayer player : bossBar.getPlayers()) {
				if (!line.isEmpty()) {
					player.sendSystemMessage(Component.literal(getData().name + ": ").withStyle(ChatFormatting.GOLD)
							.append(Component.literal(line).withStyle(ChatFormatting.RED)));
				}
				player.sendSystemMessage(Component.literal(now == 4 ? "Final phase: " + getData().name + " awakens!" : now == 3 ? "Phase 3: watch the ground!" : "Phase 2")
						.withStyle(now == 4 ? ChatFormatting.DARK_RED : ChatFormatting.GRAY), true);
			}
		}
		windupPower = null; // A phase change interrupts whatever it was winding up.
		abilityCooldown = 30;
		if (now == 2 && getTarget() != null) {
			callCrew(level, getTarget()); // Second wave of the crew.
			unleashCompanion(level, getTarget());
		}
		if (!fight.form.isEmpty() && getForm().isEmpty()) {
			transform(level, fight.form);
		}
		if (now >= 3 && !fight.form3.isEmpty() && !getForm().equals(fight.form3)) {
			transform(level, fight.form3); // Imu: the third form.
		}
		if (now == 4) {
			titan.ultimate(this, level);
		}
	}

	/** Kaido becomes the dragon, Lucci the leopard...: a burst of smoke, and the form's roar (see BossForms). */
	private void transform(ServerLevel level, String form) {
		setForm(form);
		level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 1, getZ(), 60, 1.2, 1.5, 1.2, 0.05);
		level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, getX(), getY() + 1, getZ(), 1, 0, 0, 0, 0);
		level.playSound(null, blockPosition(), SoundEvents.ENDER_DRAGON_GROWL, net.minecraft.sounds.SoundSource.HOSTILE, 2.0f, form.equals("leopard") ? 1.4f : 0.8f);
		if (bossBar != null) {
			for (ServerPlayer player : bossBar.getPlayers()) {
				player.sendSystemMessage(Component.literal(getData().name + " transforms!").withStyle(ChatFormatting.DARK_RED), true);
			}
		}
	}

	/** Starts the next attack: a short wind-up with a warning circle, then the attack (see tickWindup). */
	private void startWindup(LivingEntity target, ServerLevel level) {
		// A fruit-user boss in the sea, cuffed, or hit by Seastone can't call on its fruit: it just fights with its fists.
		if (com.onepiecemod.power.SeaWeakness.drainsFruitUser(this)) {
			level.sendParticles(ParticleTypes.BUBBLE_POP, getX(), getY() + getBbHeight() * 0.7, getZ(), 12, 0.4, 0.4, 0.4, 0.02);
			return;
		}
		String power = nextPower();
		if (power.equals(SIGNATURE)) {
			// Signature moves draw their own warning circles and land a moment later.
			BossFightData fight = BossFightData.get(getCharacterId());
			strikes.signature(fight.signature, this, target, level, (float) getAttributeValue(Attributes.ATTACK_DAMAGE), difficulty + (phase >= 3 ? 1 : 0));
			return;
		}
		windupPower = power;
		windupTicks = switch (difficulty) {
			case EXPERT -> 12;
			case HARD -> 16;
			default -> 22;
		} - (phase >= 3 ? 4 : 0);
		windupMark = BossAbility.areaRadius(power) > 0 || BossAbility.alwaysHits(power) ? null : target.position();
		com.onepiecemod.anim.CombatAnims.play(this, com.onepiecemod.anim.Anim.POWER_UP, windupTicks);
		level.sendParticles(ParticleTypes.ELECTRIC_SPARK, getX(), getY() + getBbHeight() * 0.7, getZ(), 12, 0.4, 0.4, 0.4, 0.05);
		playSound(com.onepiecemod.sound.BossSounds.WINDUP, 1.2f, Math.min(2.0f, 22.0f / windupTicks)); // Shorter wind-ups sound faster.
	}

	private void tickWindup(ServerLevel level) {
		LivingEntity target = getTarget();
		if (target == null || !target.isAlive()) {
			windupPower = null;
			return;
		}
		getNavigation().stop();
		getLookControl().setLookAt(target, 30.0f, 30.0f);
		windupTicks--;
		if (windupTicks % 3 == 0) {
			int color = windupTicks <= 6 ? 0xFFFFE040 : 0xFFE02020;
			double radius = BossAbility.areaRadius(windupPower);
			if (windupMark != null) {
				BossStrikes.ring(level, windupMark, 1.6, color);
			} else if (radius > 0) {
				BossStrikes.ring(level, position(), radius, color);
			}
		}
		if (windupTicks > 0) {
			return;
		}
		String power = windupPower;
		windupPower = null;
		if (windupMark != null && target.position().distanceToSqr(windupMark) > 2.5 * 2.5) {
			// Dodged: the attack lands on the empty circle.
			BossVisuals.show(power, this, windupMark, level);
			com.onepiecemod.anim.CombatAnims.bossPower(this, power);
			level.sendParticles(ParticleTypes.POOF, windupMark.x, windupMark.y + 0.3, windupMark.z, 10, 0.4, 0.2, 0.4, 0.02);
			return;
		}
		BossAbility.use(power, this, target, level);
	}

	/**
	 * Which attack comes next. Phase 1: the main power (Hard and Expert also mix in the second power).
	 * Phase 2: main and second power take turns. Phase 3: every third attack is the signature move.
	 * Expert bosses also unleash Conqueror's Haki every third attack before phase 3.
	 */
	private String nextPower() {
		CharacterData data = getData();
		abilitiesUsed++;
		if (phase >= 3 && abilitiesUsed % 3 == 0) {
			return SIGNATURE;
		}
		String power = data.power;
		boolean mixes = difficulty >= HARD || phase >= 2;
		if (mixes && abilitiesUsed % 2 == 0 && data.hardPower != null && !data.hardPower.isEmpty()) {
			power = data.hardPower;
		}
		if (difficulty == EXPERT && abilitiesUsed % 3 == 0) {
			power = "haki";
		}
		return BossAbility.resolve(power, getRandom());
	}

	/** The boss calls a few of its crew (Doflamingo's family, Akainu's Marines...). Bosses like Mihawk fight alone. */
	private void callCrew(ServerLevel level, LivingEntity target) {
		String kit = BossFightData.get(getCharacterId()).crew;
		if (kit == null || kit.isEmpty() || com.onepiecemod.npc.NpcKit.get(kit) == null) {
			return;
		}
		minions.removeIf(id -> level.getEntity(id) == null || !level.getEntity(id).isAlive());
		int count = Math.min(2 + difficulty, 5 - minions.size());
		int called = 0;
		for (int i = 0; i < count; i++) {
			net.minecraft.core.BlockPos spot = crewSpot(level);
			if (spot == null) {
				continue;
			}
			com.onepiecemod.npc.HumanNpc npc = com.onepiecemod.npc.NpcFeature.spawn(level, kit, spot, getRandom().nextFloat() * 360f);
			if (npc == null) {
				continue;
			}
			npc.addTag(BossStrikes.MINION_TAG);
			npc.setTarget(target);
			minions.add(npc.getUUID());
			level.sendParticles(ParticleTypes.POOF, npc.getX(), npc.getY() + 1, npc.getZ(), 12, 0.3, 0.6, 0.3, 0.02);
			called++;
		}
		if (called > 0 && bossBar != null) {
			for (ServerPlayer player : bossBar.getPlayers()) {
				player.sendSystemMessage(Component.literal(getData().name + " calls for backup!").withStyle(ChatFormatting.GOLD), true);
			}
		}
	}

	/** Shamrock lets Cerberus loose...: the boss's companion beast joins the fight (see BossFightData.companion). */
	private void unleashCompanion(ServerLevel level, LivingEntity target) {
		BossFightData fight = BossFightData.get(getCharacterId());
		net.minecraft.world.entity.EntityType<com.onepiecemod.creature.CreatureEntity> type =
				fight.companion.isEmpty() ? null : com.onepiecemod.creature.Creatures.TYPES.get(fight.companion);
		net.minecraft.core.BlockPos spot = type == null ? null : crewSpot(level);
		if (spot == null) {
			return;
		}
		com.onepiecemod.creature.CreatureEntity beast = type.create(level, net.minecraft.world.entity.EntitySpawnReason.EVENT);
		if (beast == null) {
			return;
		}
		beast.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
		setBase(beast, net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH, fight.companionHealth * (1 + difficulty * 0.5));
		setBase(beast, net.minecraft.world.entity.ai.attributes.Attributes.ATTACK_DAMAGE, fight.companionDamage * (1 + difficulty * 0.3));
		setBase(beast, net.minecraft.world.entity.ai.attributes.Attributes.SCALE, fight.companionScale);
		setBase(beast, net.minecraft.world.entity.ai.attributes.Attributes.KNOCKBACK_RESISTANCE, 0.8);
		beast.setHealth(beast.getMaxHealth());
		if (!fight.companionName.isEmpty()) {
			beast.setCustomName(Component.literal(fight.companionName).withStyle(ChatFormatting.RED));
			beast.setCustomNameVisible(true);
		}
		beast.addTag(BossStrikes.MINION_TAG);
		beast.setTarget(target);
		level.addFreshEntity(beast);
		minions.add(beast.getUUID());
		level.sendParticles(ParticleTypes.LARGE_SMOKE, beast.getX(), beast.getY() + 1, beast.getZ(), 40, 0.8, 1.0, 0.8, 0.05);
		level.playSound(null, beast.blockPosition(), SoundEvents.RAVAGER_ROAR, net.minecraft.sounds.SoundSource.HOSTILE, 2.5f, 0.5f);
		if (bossBar != null) {
			for (ServerPlayer player : bossBar.getPlayers()) {
				if (!fight.companionLine.isEmpty()) {
					player.sendSystemMessage(Component.literal(getData().name + ": ").withStyle(ChatFormatting.GOLD)
							.append(Component.literal(fight.companionLine).withStyle(ChatFormatting.RED)));
				}
				player.sendSystemMessage(Component.literal(getData().name + " unleashes " + (fight.companionName.isEmpty() ? "a beast" : fight.companionName) + "!")
						.withStyle(ChatFormatting.DARK_RED), true);
			}
		}
	}

	private static void setBase(LivingEntity entity, net.minecraft.core.Holder<net.minecraft.world.entity.ai.attributes.Attribute> attribute, double value) {
		net.minecraft.world.entity.ai.attributes.AttributeInstance instance = entity.getAttribute(attribute);
		if (instance != null) {
			instance.setBaseValue(value);
		}
	}

	/** A free spot with solid ground 3-7 blocks from the boss, at about its height (works inside lairs too). */
	private net.minecraft.core.BlockPos crewSpot(ServerLevel level) {
		for (int attempt = 0; attempt < 12; attempt++) {
			double angle = getRandom().nextDouble() * Math.PI * 2;
			double dist = 3 + getRandom().nextDouble() * 4;
			net.minecraft.core.BlockPos base = net.minecraft.core.BlockPos.containing(getX() + Math.cos(angle) * dist, getY(), getZ() + Math.sin(angle) * dist);
			for (int dy : new int[] {0, 1, -1, 2, -2}) {
				net.minecraft.core.BlockPos pos = base.offset(0, dy, 0);
				if (level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), net.minecraft.core.Direction.UP)
						&& level.getBlockState(pos).getCollisionShape(level, pos).isEmpty() && level.getFluidState(pos).isEmpty()
						&& level.getBlockState(pos.above()).getCollisionShape(level, pos.above()).isEmpty()) {
					return pos;
				}
			}
		}
		return null;
	}

	/** The crew leaves when the fight is over (boss beaten or calmed down). */
	private void dismissCrew(ServerLevel level) {
		for (java.util.UUID id : minions) {
			net.minecraft.world.entity.Entity npc = level.getEntity(id);
			if (npc != null && npc.isAlive()) {
				level.sendParticles(ParticleTypes.POOF, npc.getX(), npc.getY() + 1, npc.getZ(), 10, 0.3, 0.6, 0.3, 0.02);
				npc.discard();
			}
		}
		minions.clear();
	}

	/** How close you must be to see a boss's health bar (and to share the win). */
	private static final double BOSS_BAR_RANGE = 40.0;

	/**
	 * Shows the boss bar only to players close by, not to everyone who can see the boss.
	 * Without this, a boss living in a structure (like Kizaru at the Egghead Lab) showed its bar
	 * up to 160 blocks away, even at world spawn.
	 */
	private void updateBossBarPlayers(ServerLevel level) {
		for (ServerPlayer player : java.util.List.copyOf(bossBar.getPlayers())) {
			if (player.isRemoved() || player.level() != level || player.distanceToSqr(this) > BOSS_BAR_RANGE * BOSS_BAR_RANGE) {
				bossBar.removePlayer(player);
			}
		}
		for (ServerPlayer player : level.players()) {
			if (!player.isSpectator() && player.distanceToSqr(this) <= BOSS_BAR_RANGE * BOSS_BAR_RANGE) {
				bossBar.addPlayer(player);
			}
		}
	}

	@Override
	public void startSeenByPlayer(ServerPlayer player) {
		super.startSeenByPlayer(player);
		// The boss bar is added in updateBossBarPlayers, once the player comes within range.
	}

	@Override
	public void stopSeenByPlayer(ServerPlayer player) {
		super.stopSeenByPlayer(player);
		if (bossBar != null) {
			bossBar.removePlayer(player);
		}
	}

	@Override
	public void die(DamageSource source) {
		if (isBoss() && level() instanceof ServerLevel serverLevel) {
			dismissCrew(serverLevel);
		}
		if (isBoss() && level() instanceof ServerLevel && bossBar != null) {
			// Everyone who could see the boss bar gets credit, so friends can team up.
			// Full rewards only if someone here hasn't won at this difficulty yet. Rematches still pay a few Berries.
			String winKey = legendRung > 0 ? TitanLadder.key(getCharacterId(), legendRung)
					: getCharacterId() + (difficulty == EXPERT ? ":expert" : difficulty == HARD ? ":hard" : "");
			firstWin = bossBar.getPlayers().isEmpty();
			for (ServerPlayer player : bossBar.getPlayers()) {
				if (!CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, winKey)) {
					firstWin = true;
				}
			}
			for (ServerPlayer player : bossBar.getPlayers()) {
				// "kaido" counts for quests at any difficulty. "kaido:hard" and "kaido:expert" unlock the next fight.
				CharacterAttachments.add(player, CharacterAttachments.BOSSES_DEFEATED, getCharacterId());
				if (difficulty >= HARD) {
					CharacterAttachments.add(player, CharacterAttachments.BOSSES_DEFEATED, getCharacterId() + ":hard");
				}
				if (difficulty == EXPERT) {
					CharacterAttachments.add(player, CharacterAttachments.BOSSES_DEFEATED, getCharacterId() + ":expert");
				}
				boolean newRung = legendRung > 0 && !CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, winKey);
				if (legendRung > 0) {
					CharacterAttachments.add(player, CharacterAttachments.BOSSES_DEFEATED, winKey);
				}
				player.sendSystemMessage(Component.literal("You defeated ").append(displayName()).append("!").withStyle(ChatFormatting.GOLD));
				if (legendRung > 0) {
					TitanLadder.onWin(player, getCharacterId(), legendRung, newRung);
				} else if (difficulty == EXPERT && TitanLadder.isLadderBoss(getCharacterId())) {
					player.sendSystemMessage(Component.literal("The Legend Ladder is open: use their Wanted Poster again for a "
							+ TitanLadder.rungName(TitanLadder.nextRung(player, getCharacterId())) + " fight. See /ladder.").withStyle(ChatFormatting.LIGHT_PURPLE));
				} else if (difficulty < EXPERT) {
					player.sendSystemMessage(Component.literal("Use their Wanted Poster again for a " + DIFFICULTY_NAMES[difficulty + 1]
							+ " fight with better rewards.").withStyle(ChatFormatting.GRAY));
				}
			}
		}
		super.die(source);
	}

	@Override
	protected void dropCustomDeathLoot(ServerLevel level, DamageSource source, boolean recentlyHit) {
		super.dropCustomDeathLoot(level, source, recentlyHit);
		if (!isBoss()) {
			return;
		}
		CharacterData data = getData();
		// Berries come in stacks of up to 64.
		int berries = com.onepiecemod.config.ModConfig.scale(Math.round(data.bounty * BERRY_MULTIPLIER[difficulty] * (1 + legendRung * 0.5f)), com.onepiecemod.config.ModConfig.bossBerries());
		if (!firstWin) {
			berries = Math.round(berries * com.onepiecemod.config.ModConfig.rematchBerryShare()); // REPEAT_BERRY_SHARE unless the settings file changes it.
		}
		while (berries > 0) {
			int stack = Math.min(berries, 64);
			spawnAtLocation(level, new ItemStack(CharacterFeature.BERRY, stack));
			berries -= stack;
		}
		ExperienceOrb.award(level, position(), XP_REWARD[difficulty] * data.tier);
		if (!firstWin) {
			return; // Prizes and the Devil Fruit only drop the first time, so rematches can't farm them.
		}

		// Hard and Expert wins have a few extra prizes.
		for (String reward : difficulty == EXPERT ? data.expertRewards : difficulty == HARD ? data.hardRewards : List.<String>of()) {
			ItemStack prize = CharacterData.stack(reward, 1);
			if (!prize.isEmpty()) {
				spawnAtLocation(level, prize);
			}
		}
		// Legend Ladder rungs have their own prizes on top.
		for (String reward : TitanLadder.rewards(legendRung)) {
			String[] parts = reward.split("\\*");
			ItemStack prize = CharacterData.stack(parts[0], parts.length > 1 ? Integer.parseInt(parts[1]) : 1);
			if (!prize.isEmpty()) {
				spawnAtLocation(level, prize);
			}
		}
		if (legendRung > 0) {
			return; // The fruit and bonus drop came with the first win already.
		}

		// Beat a character's boss version and you get their Devil Fruit.
		// If that fruit isn't in the mod yet, nothing drops.
		ItemStack fruit = CharacterData.stack(data.fruitItem, 1);
		if (!fruit.isEmpty()) {
			spawnAtLocation(level, fruit);
		}
		ItemStack bonus = CharacterData.stack(data.bonusDrop, 1);
		if (!bonus.isEmpty()) {
			spawnAtLocation(level, bonus);
		}
	}

	// ---- Talking: shops and quests ----

	/** Level-ups and restocking happen when nobody is trading, just like villagers. */
	private void traderTick(ServerLevel level) {
		if (levelUpPending) {
			levelUpPending = false;
			tradeLevel++;
			offers = null; // Rebuild the shop next time, now with the new level's trades.
			level.sendParticles(ParticleTypes.HAPPY_VILLAGER, getX(), getY() + getBbHeight(), getZ(), 15, 0.5, 0.5, 0.5, 0.0);
			playSound(SoundEvents.PLAYER_LEVELUP, 1.0f, 1.0f);
		}

		restockTimer--;
		if (restockTimer <= 0) {
			restockTimer = RESTOCK_TICKS;
			if (offers != null) {
				for (MerchantOffer offer : offers) {
					offer.resetUses();
				}
			}
		}
	}

	private boolean canLevelUp() {
		return tradeLevel < 5 && tradeXp >= XP_FOR_NEXT_LEVEL[tradeLevel];
	}

	@Override
	protected InteractionResult mobInteract(Player player, InteractionHand hand) {
		if (isBoss() || hand != InteractionHand.MAIN_HAND) {
			return super.mobInteract(player, hand);
		}
		if (player instanceof ServerPlayer serverPlayer) {
			// Opens the talk screen; its choices lead to quests and the shop (see dialogue/Dialogue).
			QuestHandler.meet(player, getData());
			com.onepiecemod.dialogue.Dialogue.open(serverPlayer, this);
		}
		return InteractionResult.SUCCESS;
	}

	/** Opens this trader's shop for the player. Returns false if someone else is already trading. */
	public boolean openShop(Player player) {
		if (tradingPlayer != null && tradingPlayer != player) {
			return false;
		}
		setTradingPlayer(player);
		int cap = com.onepiecemod.story.StoryGates.shopLevelCap(player);
		if (cap != offersCap) {
			offersCap = cap;
			offers = null; // This player's story allows a different set of wares.
		}
		if (tradeLevel > cap && getData().levels != null && getData().levels.size() > cap && player instanceof ServerPlayer serverPlayer) {
			serverPlayer.sendSystemMessage(Component.literal(getData().name + ": " + com.onepiecemod.story.StoryGates.shopCapHint(cap))
					.withStyle(net.minecraft.ChatFormatting.GRAY));
		}
		openTradingScreen(player, Component.literal(getData().name), tradeLevel); // Their name, even if /summon gave them none.
		return true;
	}

	@Override
	public void setTradingPlayer(Player player) {
		this.tradingPlayer = player;
	}

	@Override
	public Player getTradingPlayer() {
		return tradingPlayer;
	}

	@Override
	public MerchantOffers getOffers() {
		if (offers != null) {
			return offers;
		}
		// Build the shop from the data file: every trade from Novice up to the trader's current level.
		offers = new MerchantOffers();
		List<List<CharacterData.Trade>> levels = getData().levels;
		for (int i = 0; i < tradeLevel && i < offersCap && i < levels.size(); i++) {
			for (CharacterData.Trade trade : levels.get(i)) {
				ItemStack result = trade.chart != null ? SeaChartItem.forTarget(trade.chart) : CharacterData.stack(trade.sell, trade.sellCount);
				if (result.isEmpty() || CharacterData.item(trade.buy) == Items.AIR) {
					continue; // Skip trades for items that don't exist.
				}
				offers.add(new MerchantOffer(
						new ItemCost(CharacterData.item(trade.buy), trade.buyCount),
						result,
						trade.maxUses,
						trade.xp,
						0.0f));
			}
		}
		return offers;
	}

	@Override
	public void overrideOffers(MerchantOffers offers) {
		// Only used on the player's side of the trade screen.
	}

	@Override
	public void notifyTrade(MerchantOffer offer) {
		offer.increaseUses();
		playSound(SoundEvents.VILLAGER_YES, 1.0f, 1.0f);
		tradeXp += offer.getXp();
		com.onepiecemod.keepsake.Keepsakes.onTrade(tradingPlayer, getCharacterId(), tradeLevel); // Master traders give their Vivre Card.
		if (canLevelUp()) {
			levelUpPending = true; // Happens once the player closes the trade screen.
		}
	}

	@Override
	public void notifyTradeUpdated(ItemStack stack) {
	}

	@Override
	public int getVillagerXp() {
		return tradeXp;
	}

	@Override
	public void overrideXp(int xp) {
	}

	@Override
	public boolean showProgressBar() {
		return true; // Show the villager-style XP bar on the trade screen.
	}

	@Override
	public boolean stillValid(Player player) {
		return tradingPlayer == player && isAlive() && player.distanceTo(this) < 8.0f;
	}

	@Override
	public SoundEvent getNotifyTradeSound() {
		return SoundEvents.VILLAGER_YES;
	}

	@Override
	public boolean isClientSide() {
		return level().isClientSide();
	}
}
