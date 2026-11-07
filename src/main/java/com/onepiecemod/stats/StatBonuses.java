package com.onepiecemod.stats;

import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.food.FoodData;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;

import com.onepiecemod.OnePieceMod;

/**
 * Turns stat tree ranks into real bonuses.
 *
 * Most bonuses are attribute modifiers with their own ids (onepiece:stat_strength and so on),
 * so they simply add on top of race stats (onepiece:race_stats), Armament Haki and gear without clashing.
 * They are saved with the player, so extra hearts from Toughness are still there when you log back in.
 *
 * Stamina's healing, slower hunger and Second Wind are handled here by hand.
 */
public class StatBonuses {
	/** Every attribute the stat tree touches, so taking points back clears the old bonuses. */
	private static final Set<Holder<Attribute>> ALL_ATTRIBUTES = new LinkedHashSet<>();
	private static final Map<PlayerStat, Identifier> IDS = new HashMap<>();

	/** Stamina heals this much health per rank, every 4 seconds, while you have food (max 1 heart per 4 s at rank 20). */
	private static final float HEAL_PER_RANK = 0.05f;
	private static final int HEAL_INTERVAL_TICKS = 80;
	/** Iron Stomach: chance that a drop in hunger is put back. */
	private static final float IRON_STOMACH_SAVE_CHANCE = 0.25f;
	/** Second Wind kicks in at or below 3 hearts, at most once every 5 minutes. */
	private static final float SECOND_WIND_HEALTH = 6.0f;
	private static final int SECOND_WIND_COOLDOWN_TICKS = 20 * 60 * 5;

	/** Not saved: a restart just resets these. */
	/** Food level and saturation last tick, for Iron Stomach. */
	private static final Map<UUID, float[]> LAST_FOOD = new HashMap<>();

	public static void initialize() {
		for (PlayerStat stat : PlayerStat.values()) {
			IDS.put(stat, OnePieceMod.id("stat_" + stat.id));
		}
		ALL_ATTRIBUTES.add(Attributes.ATTACK_DAMAGE);
		ALL_ATTRIBUTES.add(Attributes.ATTACK_KNOCKBACK);
		ALL_ATTRIBUTES.add(Attributes.BLOCK_BREAK_SPEED);
		ALL_ATTRIBUTES.add(Attributes.MAX_HEALTH);
		ALL_ATTRIBUTES.add(Attributes.ARMOR);
		ALL_ATTRIBUTES.add(Attributes.KNOCKBACK_RESISTANCE);
		ALL_ATTRIBUTES.add(Attributes.ARMOR_TOUGHNESS);
		ALL_ATTRIBUTES.add(Attributes.MOVEMENT_SPEED);
		ALL_ATTRIBUTES.add(Attributes.WATER_MOVEMENT_EFFICIENCY);
		ALL_ATTRIBUTES.add(Attributes.STEP_HEIGHT);
		ALL_ATTRIBUTES.add(Attributes.JUMP_STRENGTH);
		ALL_ATTRIBUTES.add(Attributes.SAFE_FALL_DISTANCE);
		ALL_ATTRIBUTES.add(Attributes.OXYGEN_BONUS);
		ALL_ATTRIBUTES.add(Attributes.ATTACK_SPEED);
		ALL_ATTRIBUTES.add(Attributes.SWEEPING_DAMAGE_RATIO);
		ALL_ATTRIBUTES.add(Attributes.ENTITY_INTERACTION_RANGE);

		ServerTickEvents.END_SERVER_TICK.register(server -> {
			int tick = server.getTickCount();
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				StatsData data = StatsAttachments.get(player);
				// Swordsmanship switches on and off as you swap items, so check often (but only change what changed).
				if (tick % 5 == 0) {
					apply(player, data);
				}
				if (data.rank(PlayerStat.STAMINA) >= PlayerStat.FIRST_MILESTONE) {
					ironStomach(player);
				}
				if (tick % HEAL_INTERVAL_TICKS == 0) {
					staminaHeal(player, data.rank(PlayerStat.STAMINA));
				}
			}
		});

		// The new body after respawning has no bonuses yet: put them back and fill up the extra hearts.
		ServerPlayerEvents.AFTER_RESPAWN.register((oldPlayer, newPlayer, alive) -> {
			apply(newPlayer);
			if (!alive) {
				newPlayer.setHealth(newPlayer.getMaxHealth());
			}
			LAST_FOOD.remove(newPlayer.getUUID());
		});

		// Second Wind (Stamina rank 20).
		ServerLivingEntityEvents.AFTER_DAMAGE.register((entity, source, baseDamageTaken, damageTaken, blocked) -> {
			if (entity instanceof ServerPlayer player && player.isAlive() && player.getHealth() <= SECOND_WIND_HEALTH
					&& StatsAttachments.rank(player, PlayerStat.STAMINA) >= PlayerStat.SECOND_MILESTONE) {
				secondWind(player);
			}
		});

		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
			LAST_FOOD.remove(handler.player.getUUID());
		});
	}

	/** Puts the player's stat bonuses on them right now (for example after spending a point). */
	public static void apply(ServerPlayer player) {
		apply(player, StatsAttachments.get(player));
	}

	private static void apply(ServerPlayer player, StatsData data) {
		Map<Holder<Attribute>, Map<Identifier, AttributeModifier>> wanted = new HashMap<>();
		if (!player.isSpectator()) {
			int strength = data.rank(PlayerStat.STRENGTH);
			add(wanted, PlayerStat.STRENGTH, Attributes.ATTACK_DAMAGE, 0.25 * strength, Operation.ADD_VALUE);
			if (strength >= PlayerStat.FIRST_MILESTONE) {
				add(wanted, PlayerStat.STRENGTH, Attributes.ATTACK_KNOCKBACK, 0.5, Operation.ADD_VALUE);
			}
			if (strength >= PlayerStat.SECOND_MILESTONE) {
				add(wanted, PlayerStat.STRENGTH, Attributes.BLOCK_BREAK_SPEED, 0.25, Operation.ADD_MULTIPLIED_BASE);
			}

			int toughness = data.rank(PlayerStat.TOUGHNESS);
			add(wanted, PlayerStat.TOUGHNESS, Attributes.MAX_HEALTH, 0.5 * toughness, Operation.ADD_VALUE);
			add(wanted, PlayerStat.TOUGHNESS, Attributes.ARMOR, 0.1 * toughness, Operation.ADD_VALUE);
			if (toughness >= PlayerStat.FIRST_MILESTONE) {
				add(wanted, PlayerStat.TOUGHNESS, Attributes.KNOCKBACK_RESISTANCE, 0.25, Operation.ADD_VALUE);
			}
			if (toughness >= PlayerStat.SECOND_MILESTONE) {
				add(wanted, PlayerStat.TOUGHNESS, Attributes.ARMOR_TOUGHNESS, 3, Operation.ADD_VALUE);
			}

			int speed = data.rank(PlayerStat.SPEED);
			add(wanted, PlayerStat.SPEED, Attributes.MOVEMENT_SPEED, 0.0075 * speed, Operation.ADD_MULTIPLIED_BASE);
			add(wanted, PlayerStat.SPEED, Attributes.WATER_MOVEMENT_EFFICIENCY, 0.015 * speed, Operation.ADD_VALUE);
			if (speed >= PlayerStat.FIRST_MILESTONE) {
				add(wanted, PlayerStat.SPEED, Attributes.STEP_HEIGHT, 0.4, Operation.ADD_VALUE);
			}
			if (speed >= PlayerStat.SECOND_MILESTONE) {
				add(wanted, PlayerStat.SPEED, Attributes.JUMP_STRENGTH, 0.06, Operation.ADD_VALUE);
				add(wanted, PlayerStat.SPEED, Attributes.SAFE_FALL_DISTANCE, 3, Operation.ADD_VALUE);
			}

			int stamina = data.rank(PlayerStat.STAMINA);
			add(wanted, PlayerStat.STAMINA, Attributes.OXYGEN_BONUS, 0.1 * stamina, Operation.ADD_VALUE);

			// Swordsmanship only counts while a sword is in your main hand.
			int swords = data.rank(PlayerStat.SWORDSMANSHIP);
			if (player.getMainHandItem().is(ItemTags.SWORDS)) {
				add(wanted, PlayerStat.SWORDSMANSHIP, Attributes.ATTACK_DAMAGE, 0.3 * swords, Operation.ADD_VALUE);
				add(wanted, PlayerStat.SWORDSMANSHIP, Attributes.ATTACK_SPEED, 0.015 * swords, Operation.ADD_MULTIPLIED_BASE);
				if (swords >= PlayerStat.FIRST_MILESTONE) {
					add(wanted, PlayerStat.SWORDSMANSHIP, Attributes.SWEEPING_DAMAGE_RATIO, 0.3, Operation.ADD_VALUE);
				}
				if (swords >= PlayerStat.SECOND_MILESTONE) {
					add(wanted, PlayerStat.SWORDSMANSHIP, Attributes.ENTITY_INTERACTION_RANGE, 1, Operation.ADD_VALUE);
				}
			}
		}

		for (Holder<Attribute> attribute : ALL_ATTRIBUTES) {
			AttributeInstance instance = player.getAttribute(attribute);
			if (instance == null) {
				continue;
			}
			Map<Identifier, AttributeModifier> forAttribute = wanted.getOrDefault(attribute, Map.of());
			for (Identifier id : IDS.values()) {
				sync(instance, id, forAttribute.get(id));
			}
		}
		if (player.getHealth() > player.getMaxHealth()) {
			player.setHealth(player.getMaxHealth());
		}
	}

	private static void add(Map<Holder<Attribute>, Map<Identifier, AttributeModifier>> wanted, PlayerStat stat,
			Holder<Attribute> attribute, double amount, Operation operation) {
		if (amount == 0) {
			return;
		}
		Identifier id = IDS.get(stat);
		wanted.computeIfAbsent(attribute, key -> new HashMap<>()).put(id, new AttributeModifier(id, amount, operation));
	}

	/** Makes the attribute have exactly this modifier under this id, or none if wanted is null. Only touches it if it changed. */
	private static void sync(AttributeInstance instance, Identifier id, AttributeModifier wanted) {
		AttributeModifier current = instance.getModifier(id);
		if (wanted == null) {
			if (current != null) {
				instance.removeModifier(id);
			}
		} else if (current == null || current.amount() != wanted.amount() || current.operation() != wanted.operation()) {
			if (current != null) {
				instance.removeModifier(id);
			}
			// Permanent means saved with the player, so max health is right the moment they log in.
			instance.addPermanentModifier(wanted);
		}
	}

	/** Stamina: slowly heal while you have enough food. */
	private static void staminaHeal(ServerPlayer player, int rank) {
		if (rank > 0 && player.isAlive() && player.getHealth() < player.getMaxHealth()
				&& player.getFoodData().getFoodLevel() > 6) {
			player.heal(rank * HEAL_PER_RANK);
		}
	}

	/**
	 * Iron Stomach (Stamina rank 10): each time your hunger or saturation goes down,
	 * there is a 1 in 4 chance it is put back, so you get hungry about 25% slower.
	 */
	private static void ironStomach(ServerPlayer player) {
		FoodData food = player.getFoodData();
		float[] before = LAST_FOOD.get(player.getUUID());
		if (before != null && (food.getFoodLevel() < before[0] || food.getSaturationLevel() < before[1])
				&& player.getRandom().nextFloat() < IRON_STOMACH_SAVE_CHANCE) {
			food.setFoodLevel((int) before[0]);
			food.setSaturation(before[1]);
		}
		LAST_FOOD.put(player.getUUID(), new float[] {food.getFoodLevel(), food.getSaturationLevel()});
	}

	private static void secondWind(ServerPlayer player) {
		long now = player.level().getGameTime();
		if (now < player.getAttachedOrElse(StatsAttachments.SECOND_WIND_READY_AT, 0L)) {
			return;
		}
		player.setAttached(StatsAttachments.SECOND_WIND_READY_AT, now + SECOND_WIND_COOLDOWN_TICKS);
		player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 100, 1), player);
		player.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, 200, 0), player);
		player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 60, 0), player);
		ServerLevel level = (ServerLevel) player.level();
		level.sendParticles(ParticleTypes.HAPPY_VILLAGER, player.getX(), player.getY() + 1, player.getZ(), 15, 0.4, 0.6, 0.4, 0.05);
		level.playSound(null, player.blockPosition(), SoundEvents.TOTEM_USE, SoundSource.PLAYERS, 0.4f, 1.4f);
		player.sendOverlayMessage(Component.literal("Second Wind! You won't go down that easily.").withStyle(ChatFormatting.GREEN));
	}
}
