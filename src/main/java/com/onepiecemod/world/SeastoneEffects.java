package com.onepiecemod.world;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.entity.EntityTypeTest;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;

import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.power.DevilFruitPowers;
import com.onepiecemod.power.SeaWeakness;

/**
 * Seastone is "solid sea", so it weakens Devil Fruit users just like water does:
 * holding it, standing on or leaning against Seastone blocks, being hit by a Seastone Jitte or wearing Seastone Cuffs.
 * Whether a fruit user is drained right now (powers off) is decided in power.SeaWeakness.
 */
public class SeastoneEffects {
	/** True for players who ate a fruit, and for story characters who have one (Crocodile, Enel...). */
	public static boolean isFruitUser(LivingEntity entity) {
		if (entity instanceof Player player) {
			return DevilFruitPowers.hasAnyFruit(player);
		}
		if (entity instanceof CharacterEntity character) {
			String fruit = character.getData().fruitItem;
			return fruit != null && !fruit.isEmpty();
		}
		return false;
	}

	/** Makes a fruit user weak and slow, and seals their power, for a while. 20 ticks = 1 second. */
	public static void drain(LivingEntity entity, int ticks) {
		entity.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, ticks, 2));
		entity.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, ticks, 3));
		entity.addEffect(new MobEffectInstance(MobEffects.MINING_FATIGUE, ticks, 1));
		SeaWeakness.seal(entity, ticks);
	}

	public static void initialize() {
		// A hit from the Seastone Jitte drains a fruit user's power for 5 seconds.
		AttackEntityCallback.EVENT.register((player, level, hand, target, hitResult) -> {
			if (!level.isClientSide() && player.getMainHandItem().is(WorldBlocks.SEASTONE_JITTE)
					&& target instanceof LivingEntity livingTarget && isFruitUser(livingTarget)) {
				drain(livingTarget, 100);
			}
			return InteractionResult.PASS; // Let the normal sword hit happen too.
		});

		// Marines and jailers swing Seastone Jitte too: their hits drain a fruit user for 3 seconds.
		ServerLivingEntityEvents.AFTER_DAMAGE.register((entity, source, baseDamage, damage, blocked) -> {
			if (!blocked && source.getDirectEntity() instanceof LivingEntity attacker && !(attacker instanceof Player)
					&& attacker.getMainHandItem().is(WorldBlocks.SEASTONE_JITTE) && isFruitUser(entity)) {
				drain(entity, 60);
			}
		});

		// Once a second: fruit users touching seastone (or sealed by it) feel weak. Fruit-user characters
		// (bosses like Crocodile) also lose their strength in the sea.
		ServerTickEvents.END_LEVEL_TICK.register(level -> {
			if (level.getGameTime() % 20 != 0) {
				return;
			}
			for (ServerPlayer player : level.getPlayers(p -> true)) {
				if (isFruitUser(player) && (SeaWeakness.touchesSeastone(player) || SeaWeakness.isSealed(player))) {
					weaken(player);
				}
			}
			for (CharacterEntity character : level.getEntities(EntityTypeTest.forClass(CharacterEntity.class),
					character -> isFruitUser(character) && SeaWeakness.isDrained(character))) {
				weaken(character);
			}
		});
	}

	private static void weaken(LivingEntity entity) {
		entity.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 40, 1, false, false, true));
		entity.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 0, false, false, true));
	}
}
