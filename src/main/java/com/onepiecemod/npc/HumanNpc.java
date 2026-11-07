package com.onepiecemod.npc;

import com.onepiecemod.util.Motion;
import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.MoveTowardsRestrictionGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.OpenDoorGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.util.DefaultRandomPos;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.RangedAttackMob;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.CharacterFeature;

/**
 * The shared brain and body of every pirate and Marine NPC (MarineEntity and SeaPirateEntity extend it).
 *
 * An NPC is dressed from a kit in npc_kits.json: it rolls a skin, crew, rank, name, weapon and combat style.
 * The skin and style are sent to players' games so the renderer can draw the right outfit and arm pose.
 */
public abstract class HumanNpc extends Monster implements RangedAttackMob {
	private static final EntityDataAccessor<String> DATA_SKIN = SynchedEntityData.defineId(HumanNpc.class, EntityDataSerializers.STRING);
	private static final EntityDataAccessor<String> DATA_STYLE = SynchedEntityData.defineId(HumanNpc.class, EntityDataSerializers.STRING);

	private String kitId = "";
	private int rankIndex = 0;
	private String rank = "";
	private String crew = "";
	private boolean guard = false;
	private int berries = 1;
	private long bountyReward = 0;

	private Goal combatGoal;
	private boolean retreating = false;
	private int retreatCooldown = 0;
	private int specialCooldown = 40;
	private int hits = 0;
	private final List<Bomb> bombs = new ArrayList<>();

	private record Bomb(Vec3 pos, int fuse) {}

	protected HumanNpc(EntityType<? extends HumanNpc> type, Level level) {
		super(type, level);
		this.getNavigation().setCanOpenDoors(true); // Guards in buildings walk through doors instead of getting stuck.
		updateCombatGoal();
	}

	public static AttributeSupplier.Builder createNpcAttributes() {
		return Monster.createMonsterAttributes()
				.add(Attributes.MAX_HEALTH, 20.0)
				.add(Attributes.ATTACK_DAMAGE, 4.0)
				.add(Attributes.MOVEMENT_SPEED, 0.3)
				.add(Attributes.FOLLOW_RANGE, 40.0);
	}

	/** Marines and the World Government are one side, pirates and outlaws the other. */
	public abstract boolean isMarineSide();

	/** Who this NPC goes after on its own (players, the other side...). Priority 1 is "whoever hit me". */
	protected abstract void addTargetGoals();

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(DATA_SKIN, "deckhand_0");
		builder.define(DATA_STYLE, CombatStyle.SWORD.id);
	}

	// The "brain": lower numbers are more important.
	@Override
	protected void registerGoals() {
		this.goalSelector.addGoal(0, new FloatGoal(this));
		this.goalSelector.addGoal(1, new RetreatGoal());
		this.goalSelector.addGoal(3, new OpenDoorGoal(this, true)); // Opens doors on its path and closes them behind it.
		// Priority 2 is the fighting goal, added in updateCombatGoal() because it depends on the combat style.
		this.goalSelector.addGoal(4, new MoveTowardsRestrictionGoal(this, 1.0)); // Guards walk back to their post.
		this.goalSelector.addGoal(6, new WaterAvoidingRandomStrollGoal(this, 0.8));
		this.goalSelector.addGoal(7, new LookAtPlayerGoal(this, Player.class, 12.0f));
		this.goalSelector.addGoal(8, new RandomLookAroundGoal(this));

		// Hit one and the whole group turns on you.
		this.targetSelector.addGoal(1, new HurtByTargetGoal(this).setAlertOthers());
		addTargetGoals();
	}

	private void updateCombatGoal() {
		if (combatGoal != null) {
			this.goalSelector.removeGoal(combatGoal);
		}
		CombatStyle style = getStyle();
		combatGoal = style.ranged
				? new SkirmishGoal<>(this, style.chaseSpeed, style.minInterval, style.maxInterval, style.range)
				: new MeleeAttackGoal(this, style.chaseSpeed, true);
		this.goalSelector.addGoal(2, combatGoal);
	}

	// ---------- Kits ----------

	/** Dresses this NPC from a kit: rolls its look, crew, rank, name and loadout. Call once when spawning. */
	public void applyKit(NpcKit kit, RandomSource random) {
		if (kit == null) {
			return;
		}
		this.kitId = kit.id;
		this.rankIndex = random.nextInt(Math.max(1, kit.ranks.size()));
		this.rank = kit.ranks.isEmpty() ? "" : kit.ranks.get(rankIndex);
		String crewPick = kit.crews == null || kit.crews.isEmpty() ? "" : NpcKit.pick(kit.crews, random);
		this.crew = "*".equals(crewPick) ? NpcNames.crew(random) : crewPick;
		this.berries = Math.max(0, kit.berries + rankIndex);
		this.bountyReward = kit.bounty + kit.bounty * rankIndex / 2;
		this.entityData.set(DATA_SKIN, kit.pickSkin(random));

		NpcKit.Loadout loadout = kit.pickLoadout(random);
		CombatStyle style = CombatStyle.byId(loadout.style);
		this.entityData.set(DATA_STYLE, style.id);
		String weapon = loadout.weapons == null || loadout.weapons.isEmpty() ? "" : NpcKit.pick(loadout.weapons, random);
		equip(EquipmentSlot.MAINHAND, weapon);
		equip(EquipmentSlot.OFFHAND, loadout.offhand);

		// Higher ranks in the same kit are a little tougher.
		double toughness = (1.0 + 0.15 * rankIndex) * com.onepiecemod.config.ModConfig.npcHealth();
		setBase(Attributes.MAX_HEALTH, (kit.health > 0 ? kit.health : 20) * toughness);
		double damage = (kit.damage > 0 ? kit.damage : 4) * (1.0 + 0.1 * rankIndex) * com.onepiecemod.config.ModConfig.npcDamage();
		// The kit's damage is the whole hit, so take back what the held weapon adds.
		setBase(Attributes.ATTACK_DAMAGE, (style == CombatStyle.HAKI ? damage * 1.3 : damage)
				- com.onepiecemod.character.CharacterData.weaponBonus(this.getMainHandItem()));
		setBase(Attributes.ARMOR, kit.armor);
		setBase(Attributes.KNOCKBACK_RESISTANCE, kit.knockbackResistance);
		if (kit.speed > 0) {
			setBase(Attributes.MOVEMENT_SPEED, kit.speed);
		}
		if (kit.scale > 0) {
			setBase(Attributes.SCALE, fitScale(kit.scale));
		}
		this.setHealth(this.getMaxHealth());
		this.setCustomName(Component.literal(NpcNames.fill(kit.name, rank, crew, random)));
		updateCombatGoal();
	}

	/**
	 * Very tall kits (Pacifista are Kuma-sized, 6.9 m) shrink to fit the room where they appear, so a guard placed
	 * indoors or a patrol under a roof doesn't spawn with its head in the ceiling. Outdoors they keep full size.
	 */
	private float fitScale(float scale) {
		if (scale <= 1.5F) {
			return scale;
		}
		BlockPos feet = this.blockPosition();
		int need = Mth.ceil(1.95F * scale);
		int clear = 0;
		while (clear < need && this.level().getBlockState(feet.above(clear)).getCollisionShape(this.level(), feet.above(clear)).isEmpty()) {
			clear++;
		}
		return clear >= need ? scale : Math.max(1.0F, Math.min(scale, (clear - 0.2F) / 1.95F));
	}

	public void applyKit(String kitId, RandomSource random) {
		applyKit(NpcKit.get(kitId), random);
	}

	/** Structure guards stay put, never despawn, and attack trespassers. */
	public void makeGuard() {
		this.guard = true;
		this.setPersistenceRequired();
		this.setHomeTo(this.blockPosition(), 16);
	}

	private void equip(EquipmentSlot slot, String itemId) {
		if (itemId == null || itemId.isEmpty()) {
			this.setItemSlot(slot, ItemStack.EMPTY);
			return;
		}
		ItemStack stack = CharacterData.stack(itemId, 1);
		this.setItemSlot(slot, stack);
		// The mod's guns and blades drop now and then; plain vanilla gear never does.
		boolean modItem = !stack.isEmpty() && !"minecraft".equals(BuiltInRegistries.ITEM.getKey(stack.getItem()).getNamespace());
		this.setDropChance(slot, modItem ? 0.04f : 0.0f);
	}

	private void setBase(net.minecraft.core.Holder<net.minecraft.world.entity.ai.attributes.Attribute> attribute, double value) {
		AttributeInstance instance = this.getAttribute(attribute);
		if (instance != null) {
			instance.setBaseValue(value);
		}
	}

	/** Fish-Men breathe underwater, so a fight by the sea never drowns them. */
	@Override
	public boolean canBreatheUnderwater() {
		return "fishman".equals(kitId) || super.canBreatheUnderwater();
	}

	public CombatStyle getStyle() {
		return CombatStyle.byId(this.entityData.get(DATA_STYLE));
	}

	/** Changes the look after the kit was applied (Vegapunk's named Seraphim). Must be a skin from NpcSkins. */
	public void setSkin(String skin) {
		if (validSkin(skin)) {
			this.entityData.set(DATA_SKIN, skin);
		}
	}

	/** Changes how this NPC fights after the kit was applied (Vegapunk's hunt units). */
	public void setStyle(CombatStyle style) {
		this.entityData.set(DATA_STYLE, style.id);
		updateCombatGoal();
	}

	/** Texture name in textures/entity/npc/, like "marine_grunt_7". */
	public String getSkin() {
		return this.entityData.get(DATA_SKIN);
	}

	public String getKitId() {
		return kitId;
	}

	public String getRankTitle() {
		return rank;
	}

	public String getCrew() {
		return crew;
	}

	public boolean isGuard() {
		return guard;
	}

	/** How much a pirate player's bounty rises for beating this NPC (0 = use the default). */
	public long getBountyReward() {
		return bountyReward;
	}

	/** Friends never hurt each other: Marines with Marines, pirates with pirates. */
	@Override
	public boolean considersEntityAsAlly(Entity other) {
		if (other instanceof HumanNpc npc && npc.isMarineSide() == this.isMarineSide()) {
			return true;
		}
		return super.considersEntityAsAlly(other);
	}

	private boolean isEnemy(LivingEntity entity) {
		if (entity == this || !entity.isAlive() || this.isAlliedTo(entity)) {
			return false;
		}
		if (entity instanceof Player player && (player.isCreative() || player.isSpectator())) {
			return false;
		}
		// Marines only hurt players they are already fighting; pirates hit anyone in the way.
		return entity == getTarget() || (entity instanceof Player && !isMarineSide()) || entity instanceof HumanNpc;
	}

	// ---------- Retreat ----------

	/** Low-rank grunts. Officers, captains, agents and anything big never run. */
	private boolean isGrunt() {
		NpcKit kit = NpcKit.get(kitId);
		return kit != null && kit.health > 0 && kit.health <= 30 && rankIndex <= 1;
	}

	/**
	 * A nearly beaten grunt runs back to its friends, calls them over, then turns to fight again.
	 * Without friends nearby it just runs away from the attacker for a few seconds.
	 */
	private class RetreatGoal extends Goal {
		private int timer;

		RetreatGoal() {
			this.setFlags(java.util.EnumSet.of(Goal.Flag.MOVE));
		}

		@Override
		public boolean canUse() {
			LivingEntity target = getTarget();
			return retreatCooldown <= 0 && target != null && target.isAlive()
					&& getHealth() < getMaxHealth() * 0.25f && isGrunt();
		}

		@Override
		public void start() {
			retreating = true;
			timer = 80 + getRandom().nextInt(40);
			LivingEntity attacker = getTarget();
			HumanNpc friend = null;
			double best = Double.MAX_VALUE;
			for (HumanNpc other : level().getEntitiesOfClass(HumanNpc.class, getBoundingBox().inflate(24.0, 8.0, 24.0),
					npc -> npc != HumanNpc.this && npc.isAlive() && npc.isMarineSide() == isMarineSide() && !npc.retreating)) {
				double d = other.distanceToSqr(HumanNpc.this);
				if (d > 36.0 && d < best && other.distanceToSqr(attacker) > distanceToSqr(attacker) * 0.5) {
					best = d;
					friend = other;
				}
			}
			if (friend != null) {
				getNavigation().moveTo(friend, 1.3);
			} else {
				Vec3 away = DefaultRandomPos.getPosAway(HumanNpc.this, 16, 7, attacker.position());
				if (away != null) {
					getNavigation().moveTo(away.x, away.y, away.z, 1.3);
				}
			}
		}

		@Override
		public boolean canContinueToUse() {
			return timer > 0 && !getNavigation().isDone();
		}

		@Override
		public void tick() {
			timer--;
		}

		@Override
		public void stop() {
			retreating = false;
			retreatCooldown = 400; // 20 seconds before it runs again.
			getNavigation().stop();
			// Back with the group: everyone nearby without a fight joins in.
			LivingEntity attacker = getTarget();
			if (attacker != null && attacker.isAlive()) {
				for (HumanNpc other : level().getEntitiesOfClass(HumanNpc.class, getBoundingBox().inflate(12.0, 6.0, 12.0),
						npc -> npc != HumanNpc.this && npc.isMarineSide() == isMarineSide() && npc.getTarget() == null)) {
					other.setTarget(attacker);
				}
			}
		}
	}

	// ---------- Special moves ----------

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		tickBombs(level);
		if (retreatCooldown > 0) {
			retreatCooldown--;
		}
		if (specialCooldown > 0) {
			specialCooldown--;
		}
		LivingEntity target = getTarget();
		this.setAggressive(target != null);
		if (target == null || !target.isAlive() || retreating || specialCooldown > 0 || !this.getSensing().hasLineOfSight(target)) {
			return;
		}
		double distance = this.distanceTo(target);
		switch (getStyle()) {
			case SWORD -> {
				if (rankIndex >= 1 && distance > 6 && distance < 16) {
					flyingSlash(level, target);
				} else if (distance > 3 && distance < 8) {
					lunge(target, 1.0);
					specialCooldown = 70;
				}
			}
			case BRAWLER, HAKI -> {
				if (distance > 3 && distance < 7) {
					lunge(target, 0.9);
					specialCooldown = 90;
				}
			}
			case HEAVY -> {
				if (distance < 3.5) {
					groundSlam(level);
				}
			}
			case ROKUSHIKI -> {
				if (target.getY() > this.getY() + 2.5 && distance < 8 && this.onGround()) {
					geppo(level);
				} else if (distance > 4 && distance < 24) {
					soru(level, target);
				}
			}
			case FISHMAN -> {
				if (distance > 4 && distance < 14) {
					waterShot(level, target);
				}
			}
			default -> { }
		}
	}

	private void lunge(LivingEntity target, double power) {
		com.onepiecemod.anim.CombatAnims.play(this, getStyle() == CombatStyle.SWORD ? com.onepiecemod.anim.Anim.THRUST : com.onepiecemod.anim.Anim.PUNCH);
		Vec3 direction = target.position().subtract(this.position()).normalize();
		this.setDeltaMovement(direction.x * power, 0.3, direction.z * power);
		Motion.sync(this);
		this.playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 0.8f, 1.2f);
	}

	/** Swordsman officers: a slash that flies through the air. */
	private void flyingSlash(ServerLevel level, LivingEntity target) {
		this.swing(net.minecraft.world.InteractionHand.MAIN_HAND, net.minecraft.world.item.component.SwingAnimation.DEFAULT);
		com.onepiecemod.anim.CombatAnims.play(this, com.onepiecemod.anim.Anim.SLASH);
		this.playSound(SoundEvents.PLAYER_ATTACK_SWEEP, 1.2f, 0.7f);
		Hit hit = trace(level, target, 18, 0.03f, ParticleTypes.SWEEP_ATTACK, 2);
		if (hit.target() != null) {
			hit.target().hurtServer(level, this.damageSources().mobAttack(this), attackDamage() * 0.8f);
		}
		specialCooldown = 100;
	}

	/** Heavy hitters: smash the ground and knock back everyone close by. */
	private void groundSlam(ServerLevel level) {
		this.swing(net.minecraft.world.InteractionHand.MAIN_HAND, net.minecraft.world.item.component.SwingAnimation.DEFAULT);
		com.onepiecemod.anim.CombatAnims.play(this, com.onepiecemod.anim.Anim.GROUND_SLAM);
		level.sendParticles(ParticleTypes.EXPLOSION, this.getX(), this.getY() + 0.2, this.getZ(), 1, 0, 0, 0, 0);
		level.sendParticles(ParticleTypes.CLOUD, this.getX(), this.getY() + 0.1, this.getZ(), 20, 1.5, 0.1, 1.5, 0.05);
		level.playSound(null, this.blockPosition(), SoundEvents.ANVIL_LAND, SoundSource.HOSTILE, 0.8f, 0.6f);
		for (LivingEntity victim : level.getEntitiesOfClass(LivingEntity.class, this.getBoundingBox().inflate(3.0), this::isEnemy)) {
			victim.hurtServer(level, this.damageSources().mobAttack(this), attackDamage() * 0.7f);
			Vec3 push = victim.position().subtract(this.position()).normalize();
			victim.knockback(0.9, -push.x, -push.z, victim.damageSources().generic(), 0.0f);
		}
		specialCooldown = 120;
	}

	/** Rokushiki Soru: move so fast it looks like a blink, and appear right next to the target. */
	private void soru(ServerLevel level, LivingEntity target) {
		Vec3 back = this.position().subtract(target.position()).normalize().scale(1.5);
		Vec3 spot = target.position().add(back);
		AABB box = this.getBoundingBox().move(spot.subtract(this.position()));
		if (!level.noCollision(this, box)) {
			specialCooldown = 20;
			return;
		}
		level.sendParticles(ParticleTypes.POOF, this.getX(), this.getY() + 1, this.getZ(), 8, 0.3, 0.5, 0.3, 0.02);
		this.teleportTo(spot.x, spot.y, spot.z);
		com.onepiecemod.anim.CombatAnims.play(this, com.onepiecemod.anim.Anim.DASH);
		level.sendParticles(ParticleTypes.POOF, spot.x, spot.y + 1, spot.z, 8, 0.3, 0.5, 0.3, 0.02);
		level.playSound(null, this.blockPosition(), SoundEvents.ENDER_DRAGON_FLAP, SoundSource.HOSTILE, 0.8f, 1.6f);
		specialCooldown = 60 + this.getRandom().nextInt(40);
	}

	/** Rokushiki Geppo: kick off the air to jump up to the target. */
	private void geppo(ServerLevel level) {
		com.onepiecemod.anim.CombatAnims.play(this, com.onepiecemod.anim.Anim.KICK);
		this.setDeltaMovement(this.getDeltaMovement().x, 0.9, this.getDeltaMovement().z);
		Motion.sync(this);
		level.sendParticles(ParticleTypes.CLOUD, this.getX(), this.getY(), this.getZ(), 6, 0.3, 0.05, 0.3, 0.02);
		specialCooldown = 50;
	}

	/** Fish-Man Karate: flick a drop of water hard enough to hit like a bullet. */
	private void waterShot(ServerLevel level, LivingEntity target) {
		this.swing(net.minecraft.world.InteractionHand.MAIN_HAND, net.minecraft.world.item.component.SwingAnimation.DEFAULT);
		com.onepiecemod.anim.CombatAnims.play(this, com.onepiecemod.anim.Anim.FLICK);
		this.playSound(SoundEvents.PLAYER_SPLASH_HIGH_SPEED, 0.8f, 1.4f);
		Hit hit = trace(level, target, 16, 0.04f, ParticleTypes.SPLASH, 1);
		if (hit.target() != null) {
			hit.target().hurtServer(level, this.damageSources().mobAttack(this), attackDamage() * 0.9f);
			Vec3 push = hit.target().position().subtract(this.position()).normalize();
			hit.target().knockback(0.6, -push.x, -push.z, hit.target().damageSources().generic(), 0.0f);
		}
		specialCooldown = 70;
	}

	private float attackDamage() {
		return (float) this.getAttributeValue(Attributes.ATTACK_DAMAGE);
	}

	// ---------- Melee ----------

	@Override
	public boolean doHurtTarget(ServerLevel level, Entity target) {
		boolean hit = super.doHurtTarget(level, target);
		if (!hit || !(target instanceof LivingEntity victim)) {
			return hit;
		}
		hits++;
		Vec3 push = victim.position().subtract(this.position()).normalize();
		switch (getStyle()) {
			case BRAWLER -> {
				if (hits % 3 == 0) { // Haymaker!
					com.onepiecemod.anim.CombatAnims.play(this, com.onepiecemod.anim.Anim.UPPERCUT);
					victim.knockback(1.2, -push.x, -push.z, victim.damageSources().generic(), 0.0f);
					victim.setDeltaMovement(victim.getDeltaMovement().add(0, 0.35, 0));
					level.sendParticles(ParticleTypes.CRIT, victim.getX(), victim.getY() + 1, victim.getZ(), 12, 0.3, 0.3, 0.3, 0.2);
					this.playSound(SoundEvents.PLAYER_ATTACK_KNOCKBACK, 1.0f, 0.8f);
				}
			}
			case HEAVY -> {
				victim.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 0), this);
				victim.knockback(0.6, -push.x, -push.z, victim.damageSources().generic(), 0.0f);
			}
			case HAKI -> level.sendParticles(ParticleTypes.SQUID_INK, victim.getX(), victim.getY() + 1, victim.getZ(), 6, 0.2, 0.3, 0.2, 0.02);
			case ROKUSHIKI -> {
				if (this.getRandom().nextInt(4) == 0) { // Shigan: a finger strike like a bullet.
					com.onepiecemod.anim.CombatAnims.play(this, com.onepiecemod.anim.Anim.THRUST);
					victim.damageCooldownTime = 0; // 26.3: this is the hit-immunity timer (setInvulnerableTime no longer resets it).
					victim.hurtServer(level, this.damageSources().mobAttack(this), attackDamage() * 0.5f);
					level.sendParticles(ParticleTypes.CRIT, victim.getX(), victim.getY() + 1, victim.getZ(), 8, 0.2, 0.2, 0.2, 0.3);
				}
			}
			case FISHMAN -> victim.knockback(0.8, -push.x, -push.z, victim.damageSources().generic(), 0.0f);
			default -> { }
		}
		Motion.sync(victim);
		return true;
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		CombatStyle style = getStyle();
		if (source.getEntity() != null && !source.is(net.minecraft.tags.DamageTypeTags.BYPASSES_INVULNERABILITY)) {
			// Observation Haki: sometimes they see the hit coming and step aside.
			if (style == CombatStyle.HAKI && this.getRandom().nextFloat() < 0.2f) {
				Vec3 away = this.position().subtract(source.getEntity().position()).normalize();
				this.setDeltaMovement(away.z * 0.5, 0.15, -away.x * 0.5);
				Motion.sync(this);
				level.sendParticles(ParticleTypes.ENCHANTED_HIT, this.getX(), this.getY() + 1, this.getZ(), 6, 0.3, 0.4, 0.3, 0.1);
				return false;
			}
			// Tekkai: harden the body like iron.
			if (style == CombatStyle.ROKUSHIKI && this.getRandom().nextFloat() < 0.25f) {
				amount *= 0.4f;
				com.onepiecemod.anim.CombatAnims.play(this, com.onepiecemod.anim.Anim.GUARD);
				level.playSound(null, this.blockPosition(), SoundEvents.ANVIL_PLACE, SoundSource.HOSTILE, 0.4f, 1.8f);
			}
		}
		return super.hurtServer(level, source, amount);
	}

	// ---------- Ranged ----------

	@Override
	public void performRangedAttack(LivingEntity target, float power) {
		if (!(this.level() instanceof ServerLevel level)) {
			return;
		}
		switch (getStyle()) {
			case SNIPER -> shoot(level, target, 32, 0.01f, 1.6f);
			case BOMBER -> throwBomb(level, target);
			case BEAM -> beam(level, target);
			default -> shoot(level, target, 20, getMainHandItem().isEmpty() ? 0.08f : 0.05f, 1.0f);
		}
	}

	private void shoot(ServerLevel level, LivingEntity target, double range, float spread, float damageScale) {
		if (getMainHandItem().getItem() instanceof com.onepiecemod.weapon.GunItem) {
			com.onepiecemod.anim.CombatAnims.play(this, com.onepiecemod.anim.Anim.SHOOT);
		}
		level.playSound(null, this.getX(), this.getY(), this.getZ(), SoundEvents.FIREWORK_ROCKET_BLAST, SoundSource.HOSTILE,
				1.0f, 0.9f + this.getRandom().nextFloat() * 0.2f);
		Hit hit = trace(level, target, range, spread, ParticleTypes.SMOKE, 3);
		if (hit.target() != null) {
			hit.target().hurtServer(level, this.damageSources().mobAttack(this), attackDamage() * damageScale);
			level.sendParticles(ParticleTypes.CRIT, hit.point().x, hit.point().y, hit.point().z, 6, 0.2, 0.2, 0.2, 0.1);
		}
	}

	/** Lobs a bomb at where the target is standing. It goes off a second later, so you can run. */
	private void throwBomb(ServerLevel level, LivingEntity target) {
		this.swing(net.minecraft.world.InteractionHand.MAIN_HAND, net.minecraft.world.item.component.SwingAnimation.DEFAULT);
		com.onepiecemod.anim.CombatAnims.play(this, com.onepiecemod.anim.Anim.THROW);
		Vec3 from = this.getEyePosition();
		Vec3 to = target.position().add((this.getRandom().nextDouble() - 0.5) * 2, 0.1, (this.getRandom().nextDouble() - 0.5) * 2);
		for (int i = 1; i < 12; i++) {
			double t = i / 12.0;
			Vec3 p = from.lerp(to, t).add(0, Math.sin(t * Math.PI) * 2.5, 0);
			level.sendParticles(ParticleTypes.SMOKE, p.x, p.y, p.z, 1, 0, 0, 0, 0);
		}
		level.playSound(null, to.x, to.y, to.z, SoundEvents.TNT_PRIMED, SoundSource.HOSTILE, 0.8f, 1.3f);
		bombs.add(new Bomb(to, 20));
	}

	private void tickBombs(ServerLevel level) {
		if (bombs.isEmpty()) {
			return;
		}
		List<Bomb> burning = new ArrayList<>(bombs);
		bombs.clear();
		for (Bomb bomb : burning) {
			if (bomb.fuse() <= 0) {
				blast(level, bomb.pos(), 2.5, attackDamage() * 1.2f);
				continue;
			}
			if (bomb.fuse() % 4 == 0) {
				level.sendParticles(ParticleTypes.SMALL_FLAME, bomb.pos().x, bomb.pos().y + 0.3, bomb.pos().z, 2, 0.05, 0.05, 0.05, 0.01);
			}
			bombs.add(new Bomb(bomb.pos(), bomb.fuse() - 1));
		}
	}

	/** Pacifista and Seraphim: a laser beam that bursts where it lands. */
	private void beam(ServerLevel level, LivingEntity target) {
		com.onepiecemod.anim.CombatAnims.play(this, com.onepiecemod.anim.Anim.POINT);
		level.playSound(null, this.getX(), this.getY(), this.getZ(), SoundEvents.BEACON_ACTIVATE, SoundSource.HOSTILE, 1.0f, 2.0f);
		Hit hit = trace(level, target, 24, 0.02f, ParticleTypes.END_ROD, 1);
		if (hit.target() != null) {
			hit.target().hurtServer(level, this.damageSources().mobAttack(this), attackDamage() * 0.9f);
		}
		blast(level, hit.point(), 2.0, attackDamage() * 0.5f);
	}

	/** A bang that hurts and knocks back enemies nearby, but never friends and never blocks. */
	private void blast(ServerLevel level, Vec3 at, double radius, float damage) {
		level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y + 0.3, at.z, 1, 0, 0, 0, 0);
		level.sendParticles(ParticleTypes.SMOKE, at.x, at.y + 0.3, at.z, 12, 0.6, 0.4, 0.6, 0.02);
		level.playSound(null, at.x, at.y, at.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.0f, 1.2f);
		for (LivingEntity victim : level.getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(radius), this::isEnemy)) {
			double distance = Math.sqrt(victim.distanceToSqr(at));
			float scaled = (float) (damage * (1.0 - distance / (radius + 1.0)));
			if (scaled > 0.5f) {
				victim.hurtServer(level, this.damageSources().mobAttack(this), scaled);
				Vec3 push = victim.position().subtract(at).normalize();
				victim.knockback(0.5, -push.x, -push.z, victim.damageSources().generic(), 0.0f);
			}
		}
	}

	private record Hit(LivingEntity target, Vec3 point) {}

	/** A straight shot from the eyes toward the target that stops at the first wall or enemy. Never hits friends. */
	private Hit trace(ServerLevel level, LivingEntity target, double range, float spread, ParticleOptions particle, int particleEvery) {
		RandomSource random = this.getRandom();
		Vec3 start = this.getEyePosition();
		Vec3 aim = new Vec3(target.getX(), target.getY(0.6), target.getZ());
		Vec3 direction = aim.subtract(start).normalize().add(
				(random.nextFloat() - 0.5) * spread, (random.nextFloat() - 0.5) * spread, (random.nextFloat() - 0.5) * spread).normalize();
		Vec3 last = start;
		int step = 0;
		for (double distance = 0.5; distance <= range; distance += 0.5) {
			Vec3 point = start.add(direction.scale(distance));
			if (distance > 1.0 && step++ % particleEvery == 0) {
				level.sendParticles(particle, point.x, point.y, point.z, 1, 0.0, 0.0, 0.0, 0.0);
			}
			BlockPos pos = BlockPos.containing(point);
			if (!level.getBlockState(pos).getCollisionShape(level, pos).isEmpty()) {
				return new Hit(null, last);
			}
			List<LivingEntity> hits = level.getEntitiesOfClass(LivingEntity.class, new AABB(point, point).inflate(0.35), this::isEnemy);
			if (!hits.isEmpty()) {
				return new Hit(hits.get(0), point);
			}
			last = point;
		}
		return new Hit(null, last);
	}

	// ---------- Loot, saving ----------

	@Override
	protected void dropCustomDeathLoot(ServerLevel level, DamageSource source, boolean recentlyHit) {
		super.dropCustomDeathLoot(level, source, recentlyHit);
		if (berries > 0) {
			spawnAtLocation(level, new ItemStack(CharacterFeature.BERRY, berries));
		}
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putString("NpcKit", kitId);
		output.putString("NpcSkin", getSkin());
		output.putString("NpcStyle", getStyle().id);
		output.putString("NpcRank", rank);
		output.putInt("NpcRankIndex", rankIndex);
		output.putString("NpcCrew", crew);
		output.putBoolean("NpcGuard", guard);
		output.putInt("NpcBerries", berries);
		output.putLong("NpcBounty", bountyReward);
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		this.kitId = input.getStringOr("NpcKit", "");
		this.entityData.set(DATA_SKIN, input.getStringOr("NpcSkin", getSkin()));
		this.entityData.set(DATA_STYLE, input.getStringOr("NpcStyle", getStyle().id));
		this.rank = input.getStringOr("NpcRank", "");
		this.rankIndex = input.getIntOr("NpcRankIndex", 0);
		this.crew = input.getStringOr("NpcCrew", "");
		this.guard = input.getBooleanOr("NpcGuard", false);
		this.berries = input.getIntOr("NpcBerries", berries);
		this.bountyReward = input.getLongOr("NpcBounty", 0L);
		if ("pacifista".equals(kitId) && getMainHandItem().is(Items.NETHERITE_AXE)) {
			// Older saves: Pacifistas used to roll an axe. They fight with lasers and their fists now.
			setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
			if (getStyle() == CombatStyle.HEAVY) {
				this.entityData.set(DATA_STYLE, CombatStyle.BRAWLER.id);
			}
		}
		updateCombatGoal();
	}

	/** Guards are placed by structures and must stay; everyone else may despawn like normal monsters. */
	@Override
	public boolean removeWhenFarAway(double distance) {
		return !guard && super.removeWhenFarAway(distance);
	}

	/** Helper for the renderer and commands: is this skin texture name sensible? */
	public static boolean validSkin(String skin) {
		int cut = skin.lastIndexOf('_');
		if (cut < 0) {
			return false;
		}
		Integer count = NpcSkins.COUNT.get(skin.substring(0, cut));
		int index = Mth.clamp(parse(skin.substring(cut + 1)), -1, 9999);
		return count != null && index >= 0 && index < count;
	}

	private static int parse(String s) {
		try {
			return Integer.parseInt(s);
		} catch (NumberFormatException e) {
			return -1;
		}
	}
}
