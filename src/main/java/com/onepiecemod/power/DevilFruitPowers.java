package com.onepiecemod.power;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.haki.HakiPowers;

/**
 * What Devil Fruits do all the time (passive powers), plus the link between the power key and
 * the moves in FruitAbilities. We "listen" for things happening in the game, like taking damage
 * or punching, and change the result for fruit users.
 */
public class DevilFruitPowers {
	// How long Yomi Yomi waits between revives. The time it is ready again is saved on the player.
	private static final long YOMI_REVIVE_COOLDOWN = 20 * 60 * 10; // 10 minutes

	/** The fruit this player has eaten, or null if none. */
	public static DevilFruit getFruit(Player player) {
		return DevilFruits.get(player.getAttached(ModAttachments.DEVIL_FRUIT));
	}

	public static boolean hasFruit(Player player, String fruitId) {
		return fruitId.equals(player.getAttached(ModAttachments.DEVIL_FRUIT));
	}

	public static boolean hasAnyFruit(Player player) {
		return getFruit(player) != null;
	}

	public static boolean isLogia(Player player) {
		DevilFruit fruit = getFruit(player);
		return fruit != null && fruit.type() == DevilFruit.Type.LOGIA;
	}

	public static void initialize() {
		FruitBench.initialize(); // Only runs with -Donepiece.fruitbench=true.
		Awakening.initialize(); // First, so awakening at death happens before Yomi Yomi's revive.
		ZoanForms.initialize();
		com.onepiecemod.fx.ElementFx.initialize();
		registerPowerKey();
		registerDamagePowers();
		registerTickPowers();

		// Rubber punch: Gomu Gomu users knock enemies much further than normal.
		AttackEntityCallback.EVENT.register((player, level, hand, target, hitResult) -> {
			if (!level.isClientSide() && hasFruit(player, "gomu_gomu_no_mi") && target instanceof LivingEntity livingTarget) {
				double yawRadians = Math.toRadians(player.getYRot());
				livingTarget.knockback(2.0, Math.sin(yawRadians), -Math.cos(yawRadians), livingTarget.damageSources().generic(), 0.0f);
			}
			return InteractionResult.PASS; // PASS lets the normal attack still happen.
		});
	}

	// The player's game sends UseFruitPowerPayload when they press R. Here the server runs the move.
	private static void registerPowerKey() {
		PayloadTypeRegistry.serverboundPlay().register(UseFruitPowerPayload.TYPE, UseFruitPowerPayload.CODEC);

		ServerPlayNetworking.registerGlobalReceiver(UseFruitPowerPayload.TYPE, (payload, context) -> {
			ServerPlayer player = context.player();
			DevilFruit fruit = getFruit(player);

			boolean mink = com.onepiecemod.race.RaceAttachments.is(player, com.onepiecemod.race.Race.MINK);
			if (mink && payload.move() == UseFruitPowerPayload.AWAKENED && (fruit == null || player.isShiftKeyDown())) {
				// Minks use the Awaken key for Sulong (sneak + Y if they also ate a Devil Fruit).
				com.onepiecemod.race.Sulong.useAtWill(player);
			} else if (fruit == null) {
				player.sendOverlayMessage(Component.translatable("message.onepiece.no_fruit").withStyle(ChatFormatting.GRAY));
			} else if (SeaWeakness.isDrained(player)) {
				// The sea (and Seastone, the sea turned to stone) cancels Devil Fruit powers.
				player.sendOverlayMessage(Component.literal(SeaWeakness.reason(player)).withStyle(ChatFormatting.AQUA));
			} else if (player.isAlive() && !player.isSpectator()) {
				if (payload.move() == UseFruitPowerPayload.AWAKENED) {
					Awakening.useAwakening(player, fruit);
				} else {
					FruitAbilities.use(player, fruit, payload.move() == UseFruitPowerPayload.SECONDARY);
				}
			}
		});
	}

	private static void registerDamagePowers() {
		ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) -> {
			if (!(entity instanceof ServerPlayer player)) {
				return true;
			}
			DevilFruit fruit = getFruit(player);
			if (fruit == null || SeaWeakness.isDrained(player)) {
				return true; // In the sea or touching Seastone, the body is just a body: no immunities, no dodging.
			}

			// false means "cancel this damage".
			return switch (fruit.id()) {
				// Rubber bounces off the ground and doesn't conduct electricity.
				case "gomu_gomu_no_mi" -> !source.is(DamageTypeTags.IS_FALL) && !source.is(DamageTypes.LIGHTNING_BOLT);
				// You can't burn fire or magma.
				case "mera_mera_no_mi", "magu_magu_no_mi" -> !source.is(DamageTypeTags.IS_FIRE) && dodge(player, source, 0.5f);
				case "netsu_netsu_no_mi" -> !source.is(DamageTypeTags.IS_FIRE);
				// You can't freeze ice.
				case "hie_hie_no_mi", "yuki_yuki_no_mi" -> !source.is(DamageTypeTags.IS_FREEZING) && dodge(player, source, 0.5f);
				case "inu_inu_no_mi_okuchi_no_makami" -> !source.is(DamageTypeTags.IS_FREEZING);
				// Lightning can't hurt the god of thunder.
				case "goro_goro_no_mi" -> !source.is(DamageTypes.LIGHTNING_BOLT) && dodge(player, source, 0.5f);
				// The Phoenix's flames don't burn it.
				case "tori_tori_no_mi_phoenix" -> !source.is(DamageTypeTags.IS_FIRE);
				// A body in pieces, or made of mochi, lets some hits pass through.
				case "bara_bara_no_mi", "mochi_mochi_no_mi" -> dodge(player, source, 0.35f);
				// Slippery skin makes attacks slide off.
				case "sube_sube_no_mi" -> dodge(player, source, 0.4f);
				// A bomb human can't be hurt by explosions.
				case "bomu_bomu_no_mi" -> !source.is(DamageTypeTags.IS_EXPLOSION);
				// Every other Logia: attacks often pass right through your body.
				default -> fruit.type() != DevilFruit.Type.LOGIA || dodge(player, source, 0.5f);
			};
		});

		// Yomi Yomi and Orochi's eight heads: come back to life once every 10 minutes.
		// Like a Totem of Undying, it can't save you from /kill, the void, or eating a second Devil Fruit.
		ServerLivingEntityEvents.ALLOW_DEATH.register((entity, source, amount) -> {
			if (entity instanceof ServerPlayer player && !source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)
					&& (hasFruit(player, "yomi_yomi_no_mi") || hasFruit(player, "hebi_hebi_no_mi_yamata_no_orochi"))) {
				ServerLevel level = (ServerLevel) player.level();
				long now = level.getGameTime();
				if (now >= player.getAttachedOrElse(ModAttachments.REVIVE_READY, 0L)) {
					player.setAttached(ModAttachments.REVIVE_READY, now + YOMI_REVIVE_COOLDOWN);
					player.setHealth(player.getMaxHealth() / 2);
					player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 200, 1));
					player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 100, 2));
					level.sendParticles(ParticleTypes.SOUL, player.getX(), player.getY() + 1, player.getZ(), 40, 0.6, 0.8, 0.6, 0.05);
					player.sendSystemMessage(Component.translatable("message.onepiece.yomi_revive").withStyle(ChatFormatting.LIGHT_PURPLE));
					return false; // false means "don't die".
				}
			}
			return true;
		});
	}

	/**
	 * Returns false (cancel the damage) when an attack passes through the player's body.
	 * Only works on attacks from a creature, and never in water, which shuts off Devil Fruit powers.
	 */
	private static boolean dodge(ServerPlayer player, DamageSource source, float chance) {
		Entity attacker = source.getEntity();
		if (attacker == null || SeaWeakness.isDrained(player) || attackerHasArmamentHaki(attacker, source)) {
			return true;
		}
		if (player.getRandom().nextFloat() < Awakening.adjustDodgeChance(player, getFruit(player), chance)) {
			((ServerLevel) player.level()).sendParticles(ParticleTypes.POOF, player.getX(), player.getY() + 1, player.getZ(), 10, 0.3, 0.5, 0.3, 0.02);
			com.onepiecemod.fx.ElementFx.logiaDodge(player, getFruit(player)); // The body turns into its element for a moment.
			return false;
		}
		return true;
	}

	// Armament Haki lets you hit Logia users for real.
	// Other mods can coat a single hit too, like One Piece Arsenal's Haki-imbued weapons (HakiPowers.registerCoatedHit).
	private static boolean attackerHasArmamentHaki(Entity attacker, DamageSource source) {
		return HakiPowers.isCoatedHit(attacker, source);
	}

	private static void registerTickPowers() {
		ServerTickEvents.END_LEVEL_TICK.register(level -> {
			boolean everySecond = level.getGameTime() % 20 == 0;

			for (ServerPlayer player : level.getPlayers(p -> true)) {
				DevilFruit fruit = getFruit(player);
				if (fruit == null) {
					continue;
				}

				// The sea hates Devil Fruit users: waist deep in it they go limp and sink like a hammer.
				// Shallows, rain and the deck (or flooded cabins) of a sailing ship don't count, see SeaWeakness.isInSea.
				if (SeaWeakness.isInSea(player)) {
					player.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 40, 2, false, false, true));
					player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 1, false, false, true));

					// A ladder or vine is the one way out: you can still pull yourself up it, slowly.
					if (!player.onClimbable()) {
						Vec3 motion = player.getDeltaMovement();
						player.setDeltaMovement(motion.x * 0.5, Math.min(motion.y, 0) - 0.04, motion.z * 0.5);
						player.needsSync = true; // Not Motion.sync: this runs every tick, a packet each tick would fight the player's own movement.
					}
					if (everySecond && player.isUnderWater()) {
						level.sendParticles(ParticleTypes.BUBBLE, player.getX(), player.getY() + 1, player.getZ(), 6, 0.3, 0.4, 0.3, 0.02);
					}
					continue;
				}
				// Seastone switches the passive powers off too (its weakness comes from SeastoneEffects).
				if (SeaWeakness.isDrained(player)) {
					continue;
				}

				// Hie Hie: water freezes under your feet, so you can walk across the sea.
				if (fruit.id().equals("hie_hie_no_mi") && level.getGameTime() % 4 == 0) {
					FruitAbilities.freezeWater(level, null, player.blockPosition(), 2, true); // Melting ice to walk on, like Frost Walker.
				}

				// Doku Doku: poison can't hurt you.
				if (fruit.id().equals("doku_doku_no_mi") && everySecond) {
					player.removeEffect(MobEffects.POISON);
				}

				// Phoenix: your flames slowly heal you.
				if (fruit.id().equals("tori_tori_no_mi_phoenix") && everySecond) {
					player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 60, 0, true, false, true));
				}
			}
		});
	}
}
