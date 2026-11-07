package com.onepiecemod.bounty;

import java.util.UUID;

import net.minecraft.core.UUIDUtil;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.shipcombat.SeaPirateEntity;

/**
 * A Marine (or World Government agent). Marines go after players who have a bounty, and fight pirates on sight.
 * Hunters chase the pirate they were sent for; if they lose that pirate for a minute, they go home.
 * Structure guards (see HumanNpc.makeGuard) also attack anyone who walks right up to their post.
 *
 * Their looks, names, weapons and fighting styles come from the shared NPC code (com.onepiecemod.npc, npc_kits.json).
 */
public class MarineEntity extends HumanNpc {
	// The rank is sent to players' games (older versions picked the uniform from it).
	private static final EntityDataAccessor<String> DATA_RANK = SynchedEntityData.defineId(MarineEntity.class, EntityDataSerializers.STRING);

	private static final double HUNT_RANGE = 96.0;
	private static final int GIVE_UP_TICKS = 20 * 60;
	private static final double GUARD_RANGE = 10.0;

	private UUID huntedId; // The pirate this Marine was sent for.
	private int ticksWithoutPirate = 0;

	public MarineEntity(EntityType<? extends MarineEntity> type, Level level) {
		super(type, level);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return HumanNpc.createNpcAttributes()
				.add(Attributes.FOLLOW_RANGE, 48.0);
	}

	@Override
	public boolean isMarineSide() {
		return true;
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(DATA_RANK, MarineRank.RECRUIT.id());
	}

	@Override
	protected void addTargetGoals() {
		// Players who have a bounty.
		this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false,
				(target, level) -> target instanceof Player player && Bounty.get(player) > 0));
		// Guards: anyone who walks right up to their post.
		this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false,
				(target, level) -> isGuard() && !com.onepiecemod.career.Careers.isMarine(target) && target.distanceToSqr(this) < GUARD_RANGE * GUARD_RANGE));
		// Pirates, always.
		this.targetSelector.addGoal(4, new NearestAttackableTargetGoal<>(this, SeaPirateEntity.class, true));
	}

	// ---------- Rank and target ----------

	public MarineRank getRank() {
		return MarineRank.byId(this.entityData.get(DATA_RANK));
	}

	/**
	 * Sets the rank and dresses the Marine from that rank's kit: a random look, name, weapon and fighting style.
	 * Call once when spawning.
	 */
	public void setRank(MarineRank rank) {
		this.entityData.set(DATA_RANK, rank.id());
		applyKit(switch (rank) {
			case RECRUIT -> this.getRandom().nextInt(3) == 0 ? "marine_recruit" : "marine";
			case RIFLEMAN -> "marine_rifle";
			case LIEUTENANT -> "marine_officer";
			case CAPTAIN -> "elite_marine";
		}, this.getRandom());
		// Hunters and raiders are never weaker than their rank, so bounty balance stays the same.
		this.getAttribute(Attributes.MAX_HEALTH).setBaseValue(Math.max(rank.health, this.getMaxHealth()));
		this.getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(Math.max(rank.damage, this.getAttributeBaseValue(Attributes.ATTACK_DAMAGE)));
		this.setHealth(this.getMaxHealth());
	}

	/** How much a pirate's bounty rises for beating this Marine. */
	public long bountyReward() {
		return getBountyReward() > 0 ? getBountyReward() : getRank().bountyReward;
	}

	/** "Lieutenant Kato", "CP9 Agent Rocco"... for chat messages. */
	public String title() {
		return this.hasCustomName() ? this.getCustomName().getString() : getRank().displayName;
	}

	public void setHunted(Player pirate) {
		this.huntedId = pirate.getUUID();
		this.setTarget(pirate);
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (huntedId == null || this.tickCount % 20 != 0) {
			return;
		}

		ServerPlayer pirate = level.getServer().getPlayerList().getPlayer(huntedId);
		boolean pirateNearby = pirate != null && pirate.level() == level && pirate.isAlive()
				&& !pirate.isSpectator() && pirate.distanceToSqr(this) < HUNT_RANGE * HUNT_RANGE;

		if (pirateNearby) {
			ticksWithoutPirate = 0;
			// Keep chasing the pirate we were sent for, unless someone else is attacking us.
			if (getTarget() == null && !pirate.isCreative()) {
				setTarget(pirate);
			}
		} else {
			ticksWithoutPirate += 20;
			if (ticksWithoutPirate >= GIVE_UP_TICKS) {
				discard(); // The pirate got away. The squad goes back to base.
			}
		}
	}

	// ---------- Saving ----------

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putString("Rank", getRank().id());
		if (huntedId != null) {
			output.store("Hunted", UUIDUtil.CODEC, huntedId);
		}
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		this.entityData.set(DATA_RANK, input.getStringOr("Rank", MarineRank.RECRUIT.id()));
		this.huntedId = input.read("Hunted", UUIDUtil.CODEC).orElse(null);
	}

	/** Used by the spawner so it doesn't send more Marines than the cap. */
	public static boolean isHunting(Mob mob, Player pirate) {
		return mob instanceof MarineEntity marine && pirate.getUUID().equals(marine.huntedId);
	}
}
