package com.onepiecemod.shipcombat;

import java.util.List;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

import com.onepiecemod.bounty.MarineEntity;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.npc.NpcKit;

/**
 * A pirate (or outlaw) from an enemy crew: aboard pirate ships, guarding pirate hideouts, roaming islands.
 * They attack players and Marines on sight.
 *
 * Their looks, crews, names, weapons and fighting styles come from the shared NPC code (com.onepiecemod.npc, npc_kits.json).
 */
public class SeaPirateEntity extends HumanNpc {
	/** The kits a pirate ship's deckhands are picked from. */
	private static final List<String> DECKHANDS = List.of("pirate", "pirate", "pirate_gunner", "rookie_pirate");

	public SeaPirateEntity(EntityType<? extends SeaPirateEntity> type, Level level) {
		super(type, level);
	}

	public static AttributeSupplier.Builder createAttributes() {
		return HumanNpc.createNpcAttributes()
				.add(Attributes.MAX_HEALTH, 22.0)
				.add(Attributes.FOLLOW_RANGE, 32.0);
	}

	@Override
	public boolean isMarineSide() {
		return false;
	}

	@Override
	protected void addTargetGoals() {
		this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
		this.targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, MarineEntity.class, true));
	}

	public boolean isCaptain() {
		return "pirate_captain".equals(getKitId());
	}

	/** Call once when spawning a ship's crew. tier (0-5) makes the whole crew tougher in more dangerous seas. */
	public void setup(boolean captain, int tier, RandomSource random) {
		applyKit(captain ? "pirate_captain" : NpcKit.pick(DECKHANDS, random), random);
		double scale = 1 + tier * 0.25;
		this.getAttribute(Attributes.MAX_HEALTH).setBaseValue(this.getMaxHealth() * scale);
		this.getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(this.getAttributeBaseValue(Attributes.ATTACK_DAMAGE) + tier);
		this.setHealth(this.getMaxHealth());
	}

	@Override
	protected void dropCustomDeathLoot(ServerLevel level, DamageSource source, boolean recentlyHit) {
		super.dropCustomDeathLoot(level, source, recentlyHit);
		if (getRandom().nextInt(3) == 0) {
			spawnAtLocation(level, new ItemStack(ShipCombatFeature.CANNONBALL, 1 + getRandom().nextInt(3)));
		}
	}
}
