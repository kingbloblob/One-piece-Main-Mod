package com.onepiecemod.race;

import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.TextColor;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;

/**
 * Makes each race's perks and drawbacks actually happen in the game.
 *
 * Stat changes are attribute modifiers that are not saved with the player,
 * so we put them back every second (cheap, and it also covers respawning and logging in).
 */
public class RacePerks {
	/** The always-on stats from Race.stats. */
	private static final Identifier RACE_STATS = OnePieceMod.id("race_stats");
	/** Stats that switch on and off, like a Lunarian's armor while their flame burns. */
	private static final Identifier RACE_SITUATION = OnePieceMod.id("race_situation");

	/** Every attribute any race touches, so switching race clears the old ones. */
	private static final Set<Holder<Attribute>> ALL_ATTRIBUTES = new LinkedHashSet<>();

	/** Chance that a Mink's punch is charged with Electro. */
	private static final float ELECTRO_CHANCE = 0.25f;
	/** In Sulong form most punches carry Electro, and it hits twice as hard. */
	private static final float SULONG_ELECTRO_CHANCE = 0.6f;
	/** Biomes at least this hot count as hot for Minks: desert, savanna, badlands and the Nether. */
	private static final float HOT_TEMPERATURE = 1.5f;

	public static void initialize() {
		for (Race race : Race.values()) {
			for (Race.Stat stat : race.stats) {
				ALL_ATTRIBUTES.add(stat.attribute());
			}
		}
		ALL_ATTRIBUTES.add(Attributes.MOVEMENT_SPEED);
		ALL_ATTRIBUTES.add(Attributes.ARMOR);
		ALL_ATTRIBUTES.add(Attributes.ARMOR_TOUGHNESS);

		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 20 != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				everySecond(player);
			}
		});

		// Put the stats back straight away after respawning, and start with full hearts (Giants have more).
		ServerPlayerEvents.AFTER_RESPAWN.register((oldPlayer, newPlayer, alive) -> {
			everySecond(newPlayer);
			if (!alive) {
				newPlayer.setHealth(newPlayer.getMaxHealth());
			}
		});

		// Lunarians don't burn while their flame is lit.
		ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) -> {
			if (entity instanceof ServerPlayer player && source.is(DamageTypeTags.IS_FIRE)
					&& RaceAttachments.is(player, Race.LUNARIAN) && !player.isInWaterOrRain()) {
				return false; // false means "cancel this damage"
			}
			return true;
		});

		// Mink Electro: some punches give the target a shock.
		ServerLivingEntityEvents.AFTER_DAMAGE.register((entity, source, baseDamageTaken, damageTaken, blocked) -> {
			if (blocked || !(source.getEntity() instanceof ServerPlayer player) || source.getDirectEntity() != player
					|| entity == player || !RaceAttachments.is(player, Race.MINK)
					|| player.getRandom().nextFloat() >= (Sulong.isActive(player) ? SULONG_ELECTRO_CHANCE : ELECTRO_CHANCE)) {
				return;
			}
			electro(player, entity);
		});
	}

	/** Makes the player this race for good, and tells them. */
	public static void become(ServerPlayer player, Race race) {
		RaceAttachments.set(player, race);
		everySecond(player);
		player.setHealth(player.getMaxHealth());
		player.sendSystemMessage(Component.literal("You are now " + race.withArticle() + "! ")
				.withStyle(style -> style.withColor(TextColor.fromRgb(race.color)))
				.append(Component.literal("Type /race to see your perks.").withStyle(ChatFormatting.GRAY)));
		player.level().playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 1.0f, 1.0f);
	}

	/** Removes every race stat, e.g. when an operator resets someone's race. */
	public static void clear(ServerPlayer player) {
		for (Holder<Attribute> attribute : ALL_ATTRIBUTES) {
			AttributeInstance instance = player.getAttribute(attribute);
			if (instance != null) {
				instance.removeModifier(RACE_STATS);
				instance.removeModifier(RACE_SITUATION);
			}
		}
		if (player.getHealth() > player.getMaxHealth()) {
			player.setHealth(player.getMaxHealth());
		}
	}

	private static void everySecond(ServerPlayer player) {
		Race race = RaceAttachments.get(player);
		Map<Holder<Attribute>, AttributeModifier> stats = new HashMap<>();
		Map<Holder<Attribute>, AttributeModifier> situation = new HashMap<>();
		if (race != null && !player.isSpectator()) {
			for (Race.Stat stat : race.stats) {
				stats.put(stat.attribute(), new AttributeModifier(RACE_STATS, stat.amount(), stat.operation()));
			}
			situational(player, race, situation);
		}
		// Only touch modifiers that changed. Taking max health away and giving it back
		// every second would cut a Giant's health down each time.
		for (Holder<Attribute> attribute : ALL_ATTRIBUTES) {
			AttributeInstance instance = player.getAttribute(attribute);
			if (instance != null) {
				sync(instance, RACE_STATS, stats.get(attribute));
				sync(instance, RACE_SITUATION, situation.get(attribute));
			}
		}
	}

	/** The perks and drawbacks that depend on where the player is right now. */
	private static void situational(ServerPlayer player, Race race, Map<Holder<Attribute>, AttributeModifier> situation) {
		switch (race) {
			case FISHMAN -> {
				effect(player, MobEffects.WATER_BREATHING, 0);
				if (!player.isInWater()) {
					situation.put(Attributes.MOVEMENT_SPEED, new AttributeModifier(RACE_SITUATION, -0.1, AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
				}
			}
			case MINK -> {
				effect(player, MobEffects.NIGHT_VISION, 0);
				if (isHot(player)) {
					player.causeFoodExhaustion(0.15f);
				}
			}
			case GIANT -> player.causeFoodExhaustion(0.08f);
			case ONI -> player.causeFoodExhaustion(0.04f);
			case LUNARIAN -> {
				if (player.isInWaterOrRain()) {
					effect(player, MobEffects.WEAKNESS, 0);
					effect(player, MobEffects.SLOWNESS, 0);
				} else {
					situation.put(Attributes.ARMOR, new AttributeModifier(RACE_SITUATION, 4, AttributeModifier.Operation.ADD_VALUE));
					situation.put(Attributes.ARMOR_TOUGHNESS, new AttributeModifier(RACE_SITUATION, 2, AttributeModifier.Operation.ADD_VALUE));
					if (player.getRandom().nextInt(3) == 0) {
						// A little flame on their back, so others can tell.
						((ServerLevel) player.level()).sendParticles(ParticleTypes.SMALL_FLAME,
								player.getX(), player.getY() + player.getBbHeight() * 0.75, player.getZ(), 3, 0.15, 0.1, 0.15, 0.01);
					}
				}
			}
			default -> {
			}
		}
	}

	/** Makes the attribute have exactly this modifier under this id, or none if wanted is null. */
	private static void sync(AttributeInstance instance, Identifier id, AttributeModifier wanted) {
		AttributeModifier current = instance.getModifier(id);
		if (wanted == null) {
			if (current != null) {
				instance.removeModifier(id);
			}
		} else if (current == null || current.amount() != wanted.amount() || current.operation() != wanted.operation()) {
			instance.addOrUpdateTransientModifier(wanted);
		}
	}

	/**
	 * How much Haki training a player really gets, after their race's bonus.
	 * Humans train every kind 50% faster, Skypieans train Observation (Mantra) twice as fast.
	 * Called from HakiPowers when Haki training points are added.
	 */
	public static int hakiXp(ServerPlayer player, int amount, boolean observation) {
		Race race = RaceAttachments.get(player);
		double multiplier = 1.0;
		if (race == Race.HUMAN) {
			multiplier = 1.5;
		} else if (race == Race.SKYPIEAN && observation) {
			multiplier = 2.0;
		}
		double scaled = amount * multiplier;
		int whole = (int) Math.floor(scaled);
		// Leftover halves become a coin flip, so +1 point turns into 1 or 2 points for Humans.
		if (player.getRandom().nextDouble() < scaled - whole) {
			whole++;
		}
		return whole;
	}

	private static void electro(ServerPlayer player, LivingEntity target) {
		ServerLevel level = (ServerLevel) player.level();
		target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1), player);
		// The punch that triggered this just made the target briefly invulnerable, so let the shock through.
		target.damageCooldownTime = 0; // (setInvulnerableTime does not reset hit immunity in 26.3)
		target.hurtServer(level, player.damageSources().lightningBolt(), Sulong.isActive(player) ? 6.0f : 3.0f);
		level.sendParticles(ParticleTypes.ELECTRIC_SPARK, target.getX(), target.getY() + target.getBbHeight() / 2, target.getZ(),
				12, 0.3, 0.4, 0.3, 0.2);
		level.playSound(null, target.blockPosition(), SoundEvents.LIGHTNING_BOLT_IMPACT, SoundSource.PLAYERS, 0.4f, 1.8f);
		player.sendOverlayMessage(Component.literal("Electro!").withStyle(ChatFormatting.YELLOW));
	}

	private static boolean isHot(ServerPlayer player) {
		return player.level().getBiome(player.blockPosition()).value().getBaseTemperature() >= HOT_TEMPERATURE;
	}

	/** A short, quiet effect that we keep topping up, so it lasts while the condition holds. */
	private static void effect(ServerPlayer player, Holder<MobEffect> effect, int amplifier) {
		// Night vision flickers when it is about to run out, so give it longer.
		int duration = effect == MobEffects.NIGHT_VISION ? 300 : 60;
		MobEffectInstance current = player.getEffect(effect);
		if (current == null || current.getDuration() < duration - 40) {
			player.addEffect(new MobEffectInstance(effect, duration, amplifier, true, false, true));
		}
	}
}
