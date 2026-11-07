package com.onepiecemod.endgame;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.ExperienceOrb;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.boss.wither.WitherBoss;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.config.ModConfig;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.sea.CalmBelt;

/**
 * The New World difficulty tier. Past the New World line (3500 blocks from spawn) hostile mobs, pirates and Marines
 * are tougher, and the deep New World (6000+, where the last Emperors and Laugh Tale wait) and the End are tougher still:
 *
 * <pre>
 *   tier            health   damage   armor   extra drops
 *   New World        +50%     +30%      -     more XP, 8% chance of Berries
 *   Deep New World  +100%     +60%     +4     twice the XP, 15% chance of Berries
 * </pre>
 *
 * The "new_world_strength" setting scales all of it (0 = off). Bosses and quest characters have their own numbers and
 * are left alone, and so are raid enemies. Each mob is checked once, where it first appears.
 */
public class NewWorldTier {
	public static final int DEEP_RADIUS = 6000;
	private static final String CHECKED_TAG = "onepiece_tier_checked";
	private static final String TIER_TAG = "onepiece_tier_";
	private static final Identifier HEALTH = OnePieceMod.id("new_world_health");
	private static final Identifier DAMAGE = OnePieceMod.id("new_world_damage");
	private static final Identifier ARMOR = OnePieceMod.id("new_world_armor");

	private static final double[] HEALTH_BONUS = {0, 0.5, 1.0};
	private static final double[] DAMAGE_BONUS = {0, 0.3, 0.6};
	private static final double[] ARMOR_BONUS = {0, 0, 4};
	private static final float[] BERRY_CHANCE = {0, 0.08f, 0.15f};
	private static final int[] BONUS_XP = {0, 3, 6};
	private static final java.util.List<Entity> PENDING = new java.util.ArrayList<>();

	public static void initialize() {
		// Checked at the end of the tick, so whatever spawned the mob has finished setting it up (raids tag theirs right after spawning).
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (!entity.entityTags().contains(CHECKED_TAG) && affected(entity)) {
				PENDING.add(entity);
			}
		});
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			for (Entity entity : PENDING) {
				if (entity.isAlive() && affected(entity) && entity.level() instanceof ServerLevel level && !entity.entityTags().contains(CHECKED_TAG)) {
					entity.addTag(CHECKED_TAG);
					int tier = tierAt(level, entity);
					if (tier > 0 && ModConfig.newWorldStrength() > 0) {
						boost((LivingEntity) entity, tier);
					}
				}
			}
			PENDING.clear();
		});
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			int tier = tierOf(entity);
			if (tier > 0 && source.getEntity() instanceof ServerPlayer && entity.level() instanceof ServerLevel level) {
				ExperienceOrb.award(level, entity.position(), BONUS_XP[tier]);
				if (level.getRandom().nextFloat() < BERRY_CHANCE[tier]) {
					entity.spawnAtLocation(level, new ItemStack(CharacterFeature.BERRY, 1 + level.getRandom().nextInt(tier + 1)));
				}
			}
		});
		// A one-time warning the first time a player crosses into each tier.
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 40 != 0 || ModConfig.newWorldStrength() <= 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				int tier = tierAt((ServerLevel) player.level(), player);
				if (tier > 0 && !player.entityTags().contains(TIER_TAG + "warned_" + tier)) {
					player.addTag(TIER_TAG + "warned_" + tier);
					warn(player, tier);
				}
			}
		});
	}

	/** Hostile mobs, and pirates and Marines who aren't town guards. Not bosses, characters, the Wither or raid enemies. */
	private static boolean affected(Entity entity) {
		if (entity instanceof CharacterEntity || entity instanceof WitherBoss || entity.entityTags().contains(Raids.TAG)) {
			return false;
		}
		if (entity instanceof HumanNpc npc) {
			return !npc.isGuard() && !(npc instanceof com.onepiecemod.career.CareerAllyEntity);
		}
		return entity instanceof Monster;
	}

	/** 0 = normal, 1 = New World, 2 = deep New World (or the End). */
	public static int tierAt(ServerLevel level, Entity entity) {
		if (level.dimension() == Level.END) {
			return 2;
		}
		if (level.dimension() != Level.OVERWORLD) {
			return 0;
		}
		double x = entity.getX();
		double z = entity.getZ();
		double distance = Math.sqrt(x * x + z * z);
		return distance >= DEEP_RADIUS ? 2 : distance >= CalmBelt.NEW_WORLD_RADIUS ? 1 : 0;
	}

	/** The tier a mob was boosted to, or 0. */
	public static int tierOf(Entity entity) {
		for (int tier = 2; tier > 0; tier--) {
			if (entity.entityTags().contains(TIER_TAG + tier)) {
				return tier;
			}
		}
		return 0;
	}

	private static void boost(LivingEntity mob, int tier) {
		double strength = ModConfig.newWorldStrength();
		mob.addTag(TIER_TAG + tier);
		add(mob.getAttribute(Attributes.MAX_HEALTH), HEALTH, HEALTH_BONUS[tier] * strength, AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
		add(mob.getAttribute(Attributes.ATTACK_DAMAGE), DAMAGE, DAMAGE_BONUS[tier] * strength, AttributeModifier.Operation.ADD_MULTIPLIED_BASE);
		if (ARMOR_BONUS[tier] > 0) {
			add(mob.getAttribute(Attributes.ARMOR), ARMOR, ARMOR_BONUS[tier] * strength, AttributeModifier.Operation.ADD_VALUE);
		}
		mob.setHealth(mob.getMaxHealth());
	}

	private static void add(AttributeInstance attribute, Identifier id, double amount, AttributeModifier.Operation operation) {
		if (attribute != null && amount > 0) {
			attribute.addOrReplacePermanentModifier(new AttributeModifier(id, amount, operation));
		}
	}

	private static void warn(ServerPlayer player, int tier) {
		double strength = ModConfig.newWorldStrength();
		String health = Math.round(HEALTH_BONUS[tier] * strength * 100) + "%";
		String damage = Math.round(DAMAGE_BONUS[tier] * strength * 100) + "%";
		String where = player.level().dimension() == Level.END ? "the heights of the Red Line" : tier == 2 ? "the deep New World" : "the New World";
		player.sendSystemMessage(Component.literal("You have entered " + where + ".").withStyle(ChatFormatting.RED, ChatFormatting.BOLD));
		player.sendSystemMessage(Component.literal("Enemies here have " + health + " more health and hit " + damage + " harder"
				+ (tier == 2 ? ", and wear armor" : "") + ". They also drop more XP, and sometimes Berries.").withStyle(ChatFormatting.GRAY));
	}
}
