package com.onepiecemod.style;

import com.onepiecemod.util.Motion;
import java.util.List;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterEntity;

/**
 * Everything a style does on its own, without pressing a key:
 * extra punch/kick/sword damage, Kami-e dodging, Samehada's spiky skin, Concasse's landing,
 * the named swords' special effects, and the bosses that drop swords and scrolls.
 */
public class StylePassives {
	private static final Identifier BONUS_ID = OnePieceMod.id("style_bonus");
	/** Chance that Kami-e dodges a melee hit (0.25 = 1 in 4). */
	private static final float KAMI_E_CHANCE = 0.25f;

	public static void initialize() {
		ServerTickEvents.END_LEVEL_TICK.register(level -> {
			for (ServerPlayer player : level.getPlayers(p -> true)) {
				tick(player, level);
			}
		});

		AttackEntityCallback.EVENT.register((player, level, hand, target, hitResult) -> {
			if (player instanceof ServerPlayer serverPlayer && target instanceof LivingEntity living && !player.isSpectator()) {
				onAttack(serverPlayer, (ServerLevel) level, living);
			}
			return InteractionResult.PASS; // PASS lets the normal attack still happen.
		});

		ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) -> {
			if (!(entity instanceof ServerPlayer player)) {
				return true;
			}
			StyleState state = StyleState.of(player);
			// Kitsunebi-ryu: a samurai holding a sword cuts the flames before they touch him.
			if (StyleAttachments.isUsing(player, FightingStyle.KITSUNEBI) && player.getMainHandItem().is(ItemTags.SWORDS)
					&& source.is(DamageTypeTags.IS_FIRE)) {
				player.clearFire();
				return false;
			}
			// Concasse: landing your own heel kick never hurts you.
			if (state.concasseStart > 0 && source.is(DamageTypeTags.IS_FALL)) {
				return false;
			}
			// Kami-e: your body goes limp like paper and the blow slides past.
			long now = player.level().getGameTime();
			if (StyleAttachments.isUsing(player, FightingStyle.ROKUSHIKI) && !state.isActive(Technique.TEKKAI, now)
					&& source.getEntity() instanceof LivingEntity && source.getDirectEntity() == source.getEntity()
					&& player.getRandom().nextFloat() < KAMI_E_CHANCE) {
				ServerLevel level = (ServerLevel) player.level();
				level.sendParticles(ParticleTypes.CLOUD, player.getX(), player.getY() + 1, player.getZ(), 8, 0.3, 0.5, 0.3, 0.02);
				StyleMoves.actionBar(player, Component.literal("Kami-e!").withStyle(ChatFormatting.AQUA));
				return false; // false means "cancel this damage"
			}
			return true;
		});

		// Samehada Shotei: whoever punches shark skin gets hurt.
		ServerLivingEntityEvents.AFTER_DAMAGE.register((entity, source, baseDamageTaken, damageTaken, blocked) -> {
			if (entity instanceof ServerPlayer player && !source.is(DamageTypes.THORNS)
					&& source.getEntity() instanceof LivingEntity attacker && source.getDirectEntity() == attacker && attacker != player
					&& StyleState.of(player).isActive(Technique.SAMEHADA, player.level().getGameTime())) {
				attacker.hurtServer((ServerLevel) player.level(), player.damageSources().thorns(player), 4.0f);
				StyleMoves.pushAway(attacker, player, 1.5, 0.3);
			}
		});

		// Bosses who carry famous swords or know Rokushiki drop them.
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (entity instanceof CharacterEntity boss && boss.isBoss() && boss.isFirstWin() && boss.level() instanceof ServerLevel level) {
				ItemStack drop = switch (boss.getCharacterId()) {
					case "mihawk" -> new ItemStack(StyleItems.YORU);
					case "kaido" -> new ItemStack(StyleItems.ENMA);
					case "moria" -> new ItemStack(StyleItems.SHUSUI); // Ryuma, Shusui's owner, was one of Moria's zombies.
					case "lucci" -> new ItemStack(StyleItems.SCROLLS.get(FightingStyle.ROKUSHIKI));
					default -> ItemStack.EMPTY;
				};
				if (!drop.isEmpty()) {
					boss.spawnAtLocation(level, drop);
				}
			}
		});
	}

	private static void tick(ServerPlayer player, ServerLevel level) {
		FightingStyle style = StyleAttachments.active(player);
		StyleState state = StyleState.of(player);
		long now = level.getGameTime();

		if (player.onGround()) {
			state.airJumps = 0;
		}

		// Concasse: the heel kick lands when you touch the ground again.
		if (state.concasseStart > 0 && now - state.concasseStart > 5) {
			if (player.onGround() || player.isInWater()) {
				for (LivingEntity target : StyleMoves.around(player, level, 3.5)) {
					StyleMoves.hit(player, level, target, 11.0f);
					target.setDeltaMovement(target.getDeltaMovement().x, 0.8, target.getDeltaMovement().z);
					Motion.sync(target);
				}
				StyleMoves.effect(level, player, ParticleTypes.EXPLOSION, 3, SoundEvents.PLAYER_ATTACK_KNOCKBACK);
				state.concasseStart = 0;
			} else if (now - state.concasseStart > 100) {
				state.concasseStart = 0; // Never landed (fell into the void or got stuck). Give up.
			}
		}

		// Yahazu Giri: the cuts land a moment after Brook walks past.
		state.delayedCuts.removeIf(cut -> {
			if (cut.at() > now) {
				return false;
			}
			if (cut.target().isAlive() && cut.target().level() == level) {
				StyleMoves.hit(player, level, cut.target(), cut.damage());
				level.sendParticles(ParticleTypes.SWEEP_ATTACK, cut.target().getX(), cut.target().getY() + 1, cut.target().getZ(), 2, 0.3, 0.3, 0.3, 0);
			}
			return true;
		});

		updateBonusDamage(player, style, state, now);

		// Fish-Men are at home in the sea.
		if (style == FightingStyle.FISHMAN_KARATE && player.isInWater() && now % 20 == 0) {
			player.addEffect(new MobEffectInstance(MobEffects.DOLPHINS_GRACE, 60, 0, false, false, true));
			player.addEffect(new MobEffectInstance(MobEffects.WATER_BREATHING, 60, 0, false, false, true));
		}

		// A little flame or shadow while a timed move is running, so you can see it.
		if (now % 4 == 0) {
			if (state.isActive(Technique.IFRIT_JAMBE, now)) {
				level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, player.getX(), player.getY() + 0.3, player.getZ(), 2, 0.2, 0.2, 0.2, 0.01);
			} else if (state.isActive(Technique.DIABLE_JAMBE, now)) {
				level.sendParticles(ParticleTypes.FLAME, player.getX(), player.getY() + 0.3, player.getZ(), 2, 0.2, 0.2, 0.2, 0.01);
			}
			if (state.isActive(Technique.KITSUNEBI_BLADE, now)) {
				level.sendParticles(ParticleTypes.FLAME, player.getX(), player.getY() + 1, player.getZ(), 2, 0.3, 0.3, 0.3, 0.01);
			}
			if (state.isActive(Technique.SOUL_SOLID, now)) {
				level.sendParticles(ParticleTypes.SNOWFLAKE, player.getX(), player.getY() + 1, player.getZ(), 2, 0.3, 0.3, 0.3, 0.01);
			}
			if (state.isActive(Technique.ASURA, now)) {
				level.sendParticles(ParticleTypes.SMOKE, player.getX(), player.getY() + 1, player.getZ(), 4, 0.6, 0.6, 0.6, 0.01);
			}
		}
	}

	/** Extra attack damage from your style, added as an attribute bonus (like a Strength effect). */
	private static void updateBonusDamage(ServerPlayer player, FightingStyle style, StyleState state, long now) {
		double bonus = 0;
		ItemStack hand = player.getMainHandItem();
		if (style == FightingStyle.SANTORYU && hand.is(ItemTags.SWORDS)) {
			// +1.5 for each extra sword: three swords give +3.
			bonus = (Math.min(3, StyleMasters.countSwords(player.getInventory())) - 1) * 1.5;
		} else if (style == FightingStyle.BLACK_LEG && hand.isEmpty()) {
			bonus = 5; // A kick hits as hard as an iron sword.
			if (state.isActive(Technique.IFRIT_JAMBE, now)) {
				bonus += 9;
			} else if (state.isActive(Technique.DIABLE_JAMBE, now)) {
				bonus += 4;
			}
		} else if (style == FightingStyle.FISHMAN_KARATE && StyleMoves.fistsFree(hand)) {
			bonus = player.isInWater() ? 6 : 3;
		} else if (style == FightingStyle.RYUSOKEN && StyleMoves.fistsFree(hand)) {
			bonus = 4;
		} else if (style == FightingStyle.FIST_OF_LOVE && StyleMoves.fistsFree(hand)) {
			bonus = 6; // Garp's bare fist is worth more than most swords.
		} else if (style == FightingStyle.NITORYU && hand.is(ItemTags.SWORDS) && player.getOffhandItem().is(ItemTags.SWORDS)) {
			bonus = 3;
		} else if (style == FightingStyle.KITSUNEBI && hand.is(ItemTags.SWORDS)) {
			bonus = state.isActive(Technique.KITSUNEBI_BLADE, now) ? 5 : 1;
		} else if (style == FightingStyle.SOUL_FENCING && hand.is(ItemTags.SWORDS)) {
			bonus = 2;
		}

		AttributeInstance attackDamage = player.getAttribute(Attributes.ATTACK_DAMAGE);
		if (attackDamage == null) {
			return;
		}
		AttributeModifier current = attackDamage.getModifier(BONUS_ID);
		if (bonus <= 0) {
			if (current != null) {
				attackDamage.removeModifier(BONUS_ID);
			}
		} else if (current == null || current.amount() != bonus) {
			// Only change it when the number changes, so we don't resend it to the player every tick.
			attackDamage.addOrUpdateTransientModifier(new AttributeModifier(BONUS_ID, bonus, AttributeModifier.Operation.ADD_VALUE));
		}
	}

	/** Runs just before a normal melee hit lands. */
	private static void onAttack(ServerPlayer player, ServerLevel level, LivingEntity target) {
		FightingStyle style = StyleAttachments.active(player);
		StyleState state = StyleState.of(player);
		long now = level.getGameTime();
		ItemStack hand = player.getMainHandItem();

		// Diable Jambe and Ifrit Jambe: burning kicks.
		if (style == FightingStyle.BLACK_LEG && hand.isEmpty()) {
			if (state.isActive(Technique.IFRIT_JAMBE, now)) {
				target.igniteForSeconds(8);
			} else if (state.isActive(Technique.DIABLE_JAMBE, now)) {
				target.igniteForSeconds(4);
			}
		}

		// Asura: every swing also cuts two more enemies near your target.
		if (style == FightingStyle.SANTORYU && hand.is(ItemTags.SWORDS) && state.isActive(Technique.ASURA, now)) {
			cutNearby(player, level, target, 2, (float) player.getAttributeValue(Attributes.ATTACK_DAMAGE) * 0.75f);
		}

		// Ryusoken: a dragon claw crushes, so the enemy hits weaker for a bit.
		if (style == FightingStyle.RYUSOKEN && StyleMoves.fistsFree(hand)) {
			target.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 60, 0));
		}

		// Fist of Love: every punch sends them flying.
		if (style == FightingStyle.FIST_OF_LOVE && StyleMoves.fistsFree(hand)) {
			double yawRadians = Math.toRadians(player.getYRot());
			target.knockback(1.5, Math.sin(yawRadians), -Math.cos(yawRadians), target.damageSources().generic(), 0.0f);
		}

		// Fox Fire Blade burns, Soul Solid freezes.
		if (hand.is(ItemTags.SWORDS)) {
			if (style == FightingStyle.KITSUNEBI && state.isActive(Technique.KITSUNEBI_BLADE, now)) {
				target.igniteForSeconds(6);
			} else if (style == FightingStyle.SOUL_FENCING && state.isActive(Technique.SOUL_SOLID, now)) {
				target.setTicksFrozen(target.getTicksRequiredToFreeze() + 60);
				target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 2));
				level.sendParticles(ParticleTypes.SNOWFLAKE, target.getX(), target.getY() + 1, target.getZ(), 10, 0.3, 0.5, 0.3, 0.02);
			}
		}

		// The named swords.
		if (hand.is(StyleItems.SANDAI_KITETSU) && player.getRandom().nextFloat() < 0.1f) {
			// Cursed: sometimes it cuts its owner.
			player.hurtServer(level, player.damageSources().magic(), 2.0f);
			player.sendSystemMessage(Component.literal("Sandai Kitetsu bites its owner...").withStyle(ChatFormatting.DARK_RED));
		} else if (hand.is(StyleItems.SHUSUI)) {
			// The black blade leaves wounds that won't heal right away.
			target.addEffect(new MobEffectInstance(MobEffects.WITHER, 60, 1));
		} else if (hand.is(StyleItems.ENMA)) {
			// Enma pulls the strength out of whoever swings it.
			player.causeFoodExhaustion(2.0f);
		} else if (hand.is(StyleItems.YORU)) {
			// The world's strongest slash reaches past your target.
			cutNearby(player, level, target, 3, 5.0f);
		} else if (hand.is(StyleItems.SHODAI_KITETSU)) {
			// The first Kitetsu: its hunger hurts the target badly, and its curse bites back harder.
			target.addEffect(new MobEffectInstance(MobEffects.WITHER, 60, 0));
			if (player.getRandom().nextFloat() < 0.2f) {
				StyleMoves.hit(player, level, target, 5.0f);
				level.sendParticles(ParticleTypes.DAMAGE_INDICATOR, target.getX(), target.getY() + 1, target.getZ(), 6, 0.3, 0.4, 0.3, 0.1);
			}
			if (player.getRandom().nextFloat() < 0.08f) {
				player.hurtServer(level, player.damageSources().magic(), 3.0f);
				player.sendSystemMessage(Component.literal("Shodai Kitetsu hungers for its owner's blood...").withStyle(ChatFormatting.DARK_RED));
			}
		} else if (hand.is(StyleItems.AME_NO_HABAKIRI)) {
			// Oden's pair: with Enma in the other hand, every cut is a Togen Totsuka that hits everyone near.
			if (player.getOffhandItem().is(StyleItems.ENMA)) {
				cutNearby(player, level, target, 4, 4.0f);
			} else {
				target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 0));
			}
		} else if (hand.is(StyleItems.ACE)) {
			// Roger's blade carries Conqueror's Haki: a wide cleave, and Armament makes it hit even harder.
			cutNearby(player, level, target, 4, 4.0f);
			if (com.onepiecemod.haki.HakiPowers.hasArmamentActive(player)) {
				StyleMoves.hit(player, level, target, 3.0f);
				level.sendParticles(ParticleTypes.ELECTRIC_SPARK, target.getX(), target.getY() + 1, target.getZ(), 10, 0.4, 0.5, 0.4, 0.1);
			}
		}
	}

	private static void cutNearby(ServerPlayer player, ServerLevel level, LivingEntity target, int max, float damage) {
		List<LivingEntity> nearby = level.getEntitiesOfClass(LivingEntity.class, target.getBoundingBox().inflate(3.0),
				entity -> entity != target && StyleMoves.isEnemy(player, entity));
		for (int i = 0; i < Math.min(max, nearby.size()); i++) {
			StyleMoves.hit(player, level, nearby.get(i), damage);
			level.sendParticles(ParticleTypes.SWEEP_ATTACK, nearby.get(i).getX(), nearby.get(i).getY() + 1, nearby.get(i).getZ(), 1, 0, 0, 0, 0);
		}
	}
}
