package com.onepiecemod.town;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.trading.Merchant;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.npc.HumanNpc;

/**
 * A townsperson: farmers, fishers, merchants, bartenders, cooks, shipwrights, kids and old folk.
 *
 * Each one belongs to a town (see Towns), has a home (usually a bed), a workplace and a job, and follows a daily
 * routine (TownRoutineGoal): up at dawn, work all day, lunch on the plaza, the bar or the square in the evening,
 * bed at night. Merchants and cooks trade like villagers (sneak and talk to haggle), sailors start bar brawls,
 * and everybody turns out for festivals. Hurt one and the whole town turns against you.
 */
public class TownsfolkEntity extends PathfinderMob implements Merchant {
	private static final EntityDataAccessor<String> DATA_SKIN = SynchedEntityData.defineId(TownsfolkEntity.class, EntityDataSerializers.STRING);
	/** Every townsperson carries this entity tag (IslandTrouble looks for it). */
	public static final String TAG = "onepiece_townsfolk";
	/** Brawl knock-out: "seeing stars" for this many ticks. */
	private static final int KO_TICKS = 160;

	private String townKey = "";
	private String townId = "";
	private String jobId = "elder";
	private int jobIndex;
	private BlockPos home;
	private BlockPos work;
	private BlockPos plaza;
	private BlockPos bar;
	private boolean visitor; // Foreign traders sail away when the market closes.

	// Not saved: brawls, haggling and trading only matter while you're there.
	private int brawlId;
	private LivingEntity brawlTarget;
	private int koTicks;
	private int panicTicks;
	private Player tradingPlayer;
	private MerchantOffers offers;
	private long offersDay = -1;
	private String offersFestival = "";
	private final Map<UUID, Integer> haggled = new HashMap<>(); // player -> price change % (for today)
	private long haggleDay = -1;
	private int talkCooldown;

	public TownsfolkEntity(EntityType<? extends TownsfolkEntity> type, Level level) {
		super(type, level);
		this.setPersistenceRequired();
		// Townsfolk walk round water, never through it: a route that swims ends in a ditch or a harbour they can't climb out of.
		this.setPathfindingMalus(net.minecraft.world.level.pathfinder.PathType.WATER, -1.0f);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return PathfinderMob.createMobAttributes()
				.add(Attributes.MAX_HEALTH, 20.0)
				.add(Attributes.MOVEMENT_SPEED, 0.5)
				.add(Attributes.ATTACK_DAMAGE, 2.0)
				.add(Attributes.FOLLOW_RANGE, 48.0);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(DATA_SKIN, "villager_0");
	}

	@Override
	protected void registerGoals() {
		this.goalSelector.addGoal(0, new FloatGoal(this));
		this.goalSelector.addGoal(1, new PanicGoal(this, 0.85) {
			@Override
			public boolean canUse() {
				return brawlId == 0 && super.canUse();
			}
		});
		this.goalSelector.addGoal(2, new TownBrawlGoal(this));
		// Run from players the town is angry with, and from pirates who are out for blood.
		this.goalSelector.addGoal(3, new AvoidEntityGoal<>(this, Player.class, 10.0f, 0.6, 0.8, this::fearsPlayer));
		this.goalSelector.addGoal(3, new AvoidEntityGoal<>(this, HumanNpc.class, 10.0f, 0.6, 0.8,
				npc -> !((HumanNpc) npc).isMarineSide() && ((HumanNpc) npc).getTarget() != null));
		this.goalSelector.addGoal(4, new TownDoorGoal(this));
		this.goalSelector.addGoal(5, new TownRoutineGoal(this));
		this.goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 8.0f));
		this.goalSelector.addGoal(9, new RandomLookAroundGoal(this));
	}

	// ---------- Setup ----------

	/** Makes this a resident of a town with a job. Call once when spawning. */
	public void settle(Town town, String job, int index, BlockPos home, RandomSource random) {
		this.townKey = town.key;
		this.townId = town.structureId;
		this.addTag(TAG); // The world events thread's island Trouble meter counts harm done to anyone with this tag.
		this.jobId = job;
		this.jobIndex = index;
		this.home = home;
		this.plaza = town.plaza;
		this.bar = town.bar;
		TownData.Job data = TownData.job(job);
		this.work = town.pickWork(data, index, random);
		String group = TownData.skinGroup(town.def.culture, job);
		Integer count = TownSkins.COUNT.get(group);
		this.entityData.set(DATA_SKIN, group + "_" + random.nextInt(count == null ? 1 : Math.max(1, count)));
		this.setCustomName(Component.literal(TownNames.pick(town.def.culture, random) + " the " + data.title));
		this.setCustomNameVisible(false);
		if (data.child) {
			setBase(Attributes.SCALE, 0.6);
			setBase(Attributes.MOVEMENT_SPEED, 0.6);
			setBase(Attributes.MAX_HEALTH, 12);
			this.setHealth(12);
		}
		holdWorkItem();
	}

	public void makeVisitor() {
		this.visitor = true;
	}

	private void setBase(net.minecraft.core.Holder<net.minecraft.world.entity.ai.attributes.Attribute> attribute, double value) {
		AttributeInstance instance = this.getAttribute(attribute);
		if (instance != null) {
			instance.setBaseValue(value);
		}
	}

	public void holdWorkItem() {
		TownData.Job data = job();
		this.setItemSlot(EquipmentSlot.MAINHAND, data.hold == null ? ItemStack.EMPTY : CharacterData.stack(data.hold, 1));
		this.setDropChance(EquipmentSlot.MAINHAND, 0.0f);
	}

	/** Market sellers show off one of their wares. */
	public void holdWares() {
		MerchantOffers list = getOffers();
		for (MerchantOffer offer : list) {
			if (!offer.getResult().is(com.onepiecemod.character.CharacterFeature.BERRY)) {
				this.setItemSlot(EquipmentSlot.MAINHAND, offer.getResult().copyWithCount(1));
				this.setDropChance(EquipmentSlot.MAINHAND, 0.0f);
				return;
			}
		}
	}

	// ---------- Getters ----------

	public String getSkin() {
		return this.entityData.get(DATA_SKIN);
	}

	public TownData.Job job() {
		return TownData.job(jobId);
	}

	public String jobId() {
		return jobId;
	}

	public String townKey() {
		return townKey;
	}

	public Town town() {
		return Towns.byKey(townKey);
	}

	@Override
	protected net.minecraft.world.entity.ai.navigation.PathNavigation createNavigation(Level level) {
		return new TownNavigation(this, level);
	}

	/** The old home turned out to be unreachable: find another one in town. */
	public void moveHome(Town town) {
		java.util.Set<BlockPos> taken = new java.util.HashSet<>();
		for (TownsfolkEntity other : Towns.residents(town)) {
			if (other != this) {
				taken.add(other.home());
			}
		}
		this.home = town.pickHome(taken, getRandom());
	}

	/** The old workplace turned out to be unreachable: pick another. */
	public void moveWork(Town town) {
		this.work = town.pickWork(job(), jobIndex, getRandom());
	}

	public BlockPos home() {
		return home != null ? home : blockPosition();
	}

	public BlockPos work() {
		return work != null ? work : home();
	}

	public BlockPos plaza() {
		Town town = town();
		return town != null && town.scanned ? town.plaza : plaza != null ? plaza : home();
	}

	public BlockPos bar() {
		Town town = town();
		return town != null && town.scanned ? town.bar : bar != null ? bar : plaza();
	}

	public boolean isChild() {
		return job().child;
	}

	public boolean isVisitor() {
		return visitor;
	}

	public String shortName() {
		return hasCustomName() ? getCustomName().getString() : "A townsperson";
	}

	// ---------- Brawls ----------

	public int brawlId() {
		return brawlId;
	}

	public void joinBrawl(int id) {
		this.brawlId = id;
		if (isSleeping()) {
			stopSleeping();
		}
	}

	public void leaveBrawl() {
		this.brawlId = 0;
		this.brawlTarget = null;
		this.koTicks = 0;
	}

	public LivingEntity brawlTarget() {
		return brawlTarget;
	}

	public void setBrawlTarget(LivingEntity target) {
		this.brawlTarget = target;
	}

	public boolean isKnockedOut() {
		return koTicks > 0;
	}

	public void panic(int ticks) {
		this.panicTicks = Math.max(panicTicks, ticks);
	}

	public boolean isPanicking() {
		return panicTicks > 0;
	}

	private boolean fearsPlayer(LivingEntity entity) {
		if (!(entity instanceof Player player) || player.isCreative() || player.isSpectator() || brawlId != 0) {
			return false;
		}
		Town town = town();
		if (town != null && town.isAngryAt(player.getUUID())) {
			return true;
		}
		// The most wanted pirates in the world make ordinary folk nervous.
		return !job().marketer && !"bartender".equals(jobId) && Bounty.threatLevel(player) >= 4;
	}

	// ---------- Ticking ----------

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (panicTicks > 0) {
			panicTicks--;
		}
		if (talkCooldown > 0) {
			talkCooldown--;
		}
		if (koTicks > 0) {
			koTicks--;
			this.getNavigation().stop();
			if (koTicks % 10 == 0) {
				level.sendParticles(ParticleTypes.CRIT, getX(), getY() + getBbHeight() + 0.3, getZ(), 3, 0.25, 0.05, 0.25, 0.0);
			}
		}
		// Heal slowly, so brawlers are fresh again by the next evening.
		if (this.tickCount % 40 == 0 && brawlId == 0 && getHealth() < getMaxHealth()) {
			heal(1.0f);
		}
		if (tradingPlayer != null && !stillValid(tradingPlayer)) {
			setTradingPlayer(null);
		}
	}

	@Override
	public boolean removeWhenFarAway(double distance) {
		return false;
	}

	// ---------- Getting hurt ----------

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		if (source.getEntity() instanceof Player player && !player.isCreative() && BarBrawls.onPlayerHit(this, player, level)) {
			// A bar fight: fists only, and nobody dies.
			if (!player.getMainHandItem().isEmpty()) {
				amount = Math.min(amount, 4.0f);
			}
			return brawlHit(level, source, amount, player);
		}
		if (brawlId != 0 && source.getEntity() instanceof TownsfolkEntity) {
			return brawlHit(level, source, amount, source.getEntity());
		}
		boolean hurt = super.hurtServer(level, source, amount);
		if (hurt && source.getEntity() instanceof ServerPlayer player && !player.isCreative()) {
			Towns.onCivilianHurt(this, player, level);
		}
		return hurt;
	}

	private boolean brawlHit(ServerLevel level, DamageSource source, float amount, net.minecraft.world.entity.Entity attacker) {
		if (koTicks > 0) {
			return false;
		}
		// Eight hearts' worth of punches (four for kids) and you're seeing stars.
		float koAt = Math.max(2.0f, getMaxHealth() - 8.0f);
		if (getHealth() - amount > koAt) {
			return super.hurtServer(level, source, amount);
		}
		super.hurtServer(level, source, Math.max(0.0f, getHealth() - koAt));
		setHealth(Math.max(koAt, getHealth()));
		koTicks = KO_TICKS;
		brawlTarget = null;
		BarBrawls.onKnockout(this, attacker, level);
		return true;
	}

	@Override
	public void die(DamageSource source) {
		super.die(source);
		if (this.level() instanceof ServerLevel level && source.getEntity() instanceof ServerPlayer player && !player.isCreative()) {
			Towns.onCivilianKilled(this, player, level);
		}
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return isSleeping() ? null : SoundEvents.VILLAGER_AMBIENT;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.VILLAGER_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.VILLAGER_DEATH;
	}

	@Override
	public float getVoicePitch() {
		return isChild() ? 1.5f : super.getVoicePitch();
	}

	// ---------- Talking ----------

	@Override
	protected InteractionResult mobInteract(Player player, InteractionHand hand) {
		if (hand != InteractionHand.MAIN_HAND) {
			return super.mobInteract(player, hand);
		}
		if (this.level().isClientSide()) {
			return InteractionResult.SUCCESS;
		}
		ServerPlayer serverPlayer = (ServerPlayer) player;
		Town town = town();
		if (isSleeping()) {
			say(serverPlayer, "Zzz... five more minutes... zzz...");
			return InteractionResult.SUCCESS;
		}
		if (brawlId != 0 || koTicks > 0) {
			say(serverPlayer, koTicks > 0 ? "Ugh... is the room spinning, or is it me?" : "Not now, I'm busy!");
			return InteractionResult.SUCCESS;
		}
		if (town != null && town.isAngryAt(player.getUUID())) {
			say(serverPlayer, "Stay away from me! I'll call the Marines!");
			panic(60);
			return InteractionResult.SUCCESS;
		}
		if (com.onepiecemod.sidejob.SideJobs.onTalk(serverPlayer, this)) {
			return InteractionResult.SUCCESS; // A town request or Wanted contract (sidejob package).
		}
		boolean shop = !getOffers().isEmpty();
		if (shop && player.isShiftKeyDown()) {
			haggle(serverPlayer);
			return InteractionResult.SUCCESS;
		}
		if (shop) {
			if (tradingPlayer == null) {
				say(serverPlayer, greeting(serverPlayer));
				applyHaggle(serverPlayer);
				setTradingPlayer(player);
				openTradingScreen(player, getDisplayName(), 1);
			}
			return InteractionResult.SUCCESS;
		}
		say(serverPlayer, chatter(serverPlayer));
		return InteractionResult.SUCCESS;
	}

	public void say(ServerPlayer player, String text) {
		player.sendSystemMessage(Component.literal(shortName() + ": ").withStyle(ChatFormatting.YELLOW)
				.append(Component.literal(text).withStyle(ChatFormatting.WHITE)));
		this.lookAt(player, 30f, 30f);
		this.playSound(isChild() ? SoundEvents.VILLAGER_YES : SoundEvents.VILLAGER_AMBIENT, 0.8f, getVoicePitch());
	}

	/** Out loud to everyone near: market calls, brawl shouts, festival cheers. */
	public void shout(String text, double range) {
		if (!(this.level() instanceof ServerLevel level)) {
			return;
		}
		Component line = Component.literal(shortName() + ": ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(text).withStyle(ChatFormatting.WHITE));
		for (ServerPlayer player : level.players()) {
			if (player.distanceToSqr(this) < range * range) {
				player.sendSystemMessage(line);
			}
		}
	}

	public boolean readyToTalk() {
		return talkCooldown <= 0;
	}

	public void didTalk(int ticks) {
		talkCooldown = ticks;
	}

	private String greeting(ServerPlayer player) {
		TownData.Festival festival = town() == null ? null : Festivals.active(town());
		if (festival != null && !festival.hazard) {
			return "Welcome, welcome! It's the " + festival.name + ", everything's festive today!";
		}
		int threat = Bounty.threatLevel(player);
		if (threat >= 3) {
			return "Y-yes, of course! Anything you want, sir! No charge for... no, there is a charge. Sorry.";
		}
		List<String> calls = job().calls;
		if (!calls.isEmpty() && this.getRandom().nextBoolean()) {
			return calls.get(this.getRandom().nextInt(calls.size()));
		}
		return "Have a look. Sneak and talk to me if you want to haggle.";
	}

	private String chatter(ServerPlayer player) {
		RandomSource random = this.getRandom();
		Town town = town();
		TownData.Festival festival = town == null ? null : Festivals.active(town);
		if (festival != null && random.nextFloat() < 0.6f) {
			if (festival.hazard) {
				return "The tide is coming! Get inside, quick!";
			}
			return random.nextBoolean() ? "Isn't the " + festival.name + " wonderful? Stay till the end!"
					: "Have you tried the festival food yet? The stalls are on the square!";
		}
		long bounty = Bounty.get(player);
		int threat = Bounty.threatLevel(player);
		if (threat > 0 && random.nextFloat() < 0.4f) {
			String amount = Bounty.format(bounty);
			return switch (threat) {
				case 1 -> "Hey, aren't you on a wanted poster? " + amount + "... that's not much, ha!";
				case 2 -> "You're " + player.getName().getString() + "! I saw your poster. " + amount + " Berries!";
				case 3 -> "A " + amount + " bounty... p-please don't wreck our town.";
				default -> "You're the one the papers call a monster! " + amount + "! Mommy...";
			};
		}
		if (isChild() && threat > 0 && random.nextBoolean()) {
			return "Whoa, a real pirate! Can I join your crew?!";
		}
		long time = this.level().getOverworldClockTime() % 24000L;
		float roll = random.nextFloat();
		if (roll < 0.2f && !TownData.rumors().isEmpty()) {
			return TownData.rumors().get(random.nextInt(TownData.rumors().size()));
		}
		if (roll < 0.35f) {
			if (time < 1000 || time > 23000) {
				return "Up with the sun! A good day's work ahead.";
			} else if (time > 11000) {
				return "Long day. I'm off for a drink and then to bed.";
			}
		}
		List<String> lines = job().lines;
		if (!lines.isEmpty()) {
			return lines.get(random.nextInt(lines.size()));
		}
		return "Nice weather today, isn't it?";
	}

	// ---------- Haggling ----------

	private void haggle(ServerPlayer player) {
		long day = this.level().getOverworldClockTime() / 24000L;
		if (haggleDay != day) {
			haggled.clear();
			haggleDay = day;
		}
		if (haggled.containsKey(player.getUUID())) {
			int change = haggled.get(player.getUUID());
			say(player, change < 0 ? "We already made a deal today. Don't push your luck!"
					: "I said what I said. Come back tomorrow if you don't like it.");
			return;
		}
		// Your reputation helps a bit: a bigger bounty scares a better price out of them.
		float chance = 0.5f + 0.05f * Math.min(4, Bounty.threatLevel(player));
		if (this.getRandom().nextFloat() < chance) {
			haggled.put(player.getUUID(), -25);
			say(player, "Ugh, fine! A quarter off, just for you. Don't tell anyone.");
			this.playSound(SoundEvents.VILLAGER_YES, 1.0f, 1.0f);
			if (this.level() instanceof ServerLevel level) {
				level.sendParticles(ParticleTypes.HAPPY_VILLAGER, getX(), getY() + getBbHeight(), getZ(), 8, 0.4, 0.3, 0.4, 0.0);
			}
		} else {
			haggled.put(player.getUUID(), 20);
			say(player, "Haggling with me? Now the price went UP!");
			this.playSound(SoundEvents.VILLAGER_NO, 1.0f, 1.0f);
		}
	}

	private void applyHaggle(ServerPlayer player) {
		long day = this.level().getOverworldClockTime() / 24000L;
		int change = haggleDay == day ? haggled.getOrDefault(player.getUUID(), 0) : 0;
		for (MerchantOffer offer : getOffers()) {
			offer.resetSpecialPriceDiff();
			if (change != 0) {
				int base = offer.getBaseCostA().getCount();
				int diff = Math.round(base * change / 100.0f);
				if (diff == 0) {
					diff = change < 0 ? -1 : 1;
				}
				offer.setSpecialPriceDiff(Mth.clamp(diff, 1 - base, 64 - base));
			}
		}
	}

	// ---------- Trading (Merchant) ----------

	@Override
	public void setTradingPlayer(Player player) {
		this.tradingPlayer = player;
		if (player == null && offers != null) {
			for (MerchantOffer offer : offers) {
				offer.resetSpecialPriceDiff();
			}
		}
		if (player != null) {
			this.getNavigation().stop();
		}
	}

	@Override
	public Player getTradingPlayer() {
		return tradingPlayer;
	}

	public boolean isTrading() {
		return tradingPlayer != null;
	}

	@Override
	public MerchantOffers getOffers() {
		long day = this.level().getOverworldClockTime() / 24000L;
		Town town = town();
		TownData.Festival festival = town == null ? null : Festivals.active(town);
		String festivalId = festival == null ? "" : festival.name;
		if (offers != null && offersDay == day && offersFestival.equals(festivalId)) {
			return offers;
		}
		offers = new MerchantOffers();
		offersDay = day;
		offersFestival = festivalId;
		TownData.Job data = job();
		if (visitor) {
			// Foreign traders: a handful of rare goods from far-off seas, different every visit.
			RandomSource random = RandomSource.create(day * 31L + getUUID().getLeastSignificantBits());
			addSome(TownData.imports(), 5, random);
			return offers;
		}
		for (TownData.Trade trade : data.trades) {
			add(trade);
		}
		if (data.marketer && !townId.isEmpty() && town != null) {
			// Local goods change from day to day: whatever the ships brought in.
			RandomSource random = RandomSource.create(day * 17L + getUUID().getMostSignificantBits());
			addSome(TownData.culture(town.def.culture).goods, 3, random);
		}
		if (festival != null && (data.marketer || "cook".equals(jobId) || "bartender".equals(jobId))) {
			for (TownData.Trade trade : festival.goods) {
				add(trade);
			}
		}
		return offers;
	}

	private void add(TownData.Trade trade) {
		MerchantOffer offer = trade.toOffer();
		if (offer != null) {
			offers.add(offer);
		}
	}

	private void addSome(List<TownData.Trade> pool, int count, RandomSource random) {
		if (pool == null || pool.isEmpty()) {
			return;
		}
		java.util.List<TownData.Trade> copy = new java.util.ArrayList<>(pool);
		for (int i = 0; i < count && !copy.isEmpty(); i++) {
			add(copy.remove(random.nextInt(copy.size())));
		}
	}

	@Override
	public void overrideOffers(MerchantOffers offers) {
		// Only used on the player's side of the trade screen.
	}

	@Override
	public void notifyTrade(MerchantOffer offer) {
		offer.increaseUses();
		this.playSound(SoundEvents.VILLAGER_YES, 1.0f, getVoicePitch());
		if (this.level() instanceof ServerLevel level) {
			level.sendParticles(ParticleTypes.HAPPY_VILLAGER, getX(), getY() + getBbHeight(), getZ(), 3, 0.3, 0.2, 0.3, 0.0);
		}
	}

	@Override
	public void notifyTradeUpdated(ItemStack stack) {
	}

	@Override
	public int getVillagerXp() {
		return 0;
	}

	@Override
	public void overrideXp(int xp) {
	}

	@Override
	public boolean showProgressBar() {
		return false;
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
		return this.level().isClientSide();
	}

	// ---------- Sleeping ----------

	/** Lie down in the home bed if it's free. */
	public void tryToSleep() {
		if (isSleeping() || home == null) {
			return;
		}
		BlockState state = this.level().getBlockState(home);
		if (state.getBlock() instanceof BedBlock && !state.getValue(BedBlock.OCCUPIED)) {
			startSleeping(home);
		}
	}

	// ---------- Saving ----------

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putString("TownKey", townKey);
		output.putString("Town", townId);
		output.putString("Job", jobId);
		output.putInt("JobIndex", jobIndex);
		output.putString("Skin", getSkin());
		output.putBoolean("Visitor", visitor);
		putPos(output, "Home", home);
		putPos(output, "Work", work);
		putPos(output, "Plaza", plaza);
		putPos(output, "Bar", bar);
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		this.townKey = input.getStringOr("TownKey", "");
		this.townId = input.getStringOr("Town", "");
		this.jobId = input.getStringOr("Job", "elder");
		this.jobIndex = input.getIntOr("JobIndex", 0);
		this.entityData.set(DATA_SKIN, input.getStringOr("Skin", getSkin()));
		this.visitor = input.getBooleanOr("Visitor", false);
		this.home = getPos(input, "Home");
		this.work = getPos(input, "Work");
		this.plaza = getPos(input, "Plaza");
		this.bar = getPos(input, "Bar");
	}

	private static void putPos(ValueOutput output, String key, BlockPos pos) {
		if (pos != null) {
			output.putLong(key, pos.asLong());
		}
	}

	private static BlockPos getPos(ValueInput input, String key) {
		long value = input.getLongOr(key, Long.MIN_VALUE);
		return value == Long.MIN_VALUE ? null : BlockPos.of(value);
	}

	/** Helper for the renderer: is this skin texture name one that exists? */
	public static boolean validSkin(String skin) {
		int cut = skin.lastIndexOf('_');
		if (cut < 0) {
			return false;
		}
		Integer count = TownSkins.COUNT.get(skin.substring(0, cut));
		try {
			int index = Integer.parseInt(skin.substring(cut + 1));
			return count != null && index >= 0 && index < count;
		} catch (NumberFormatException e) {
			return false;
		}
	}
}
