package com.onepiecemod.haki;

import com.onepiecemod.util.Motion;
import com.onepiecemod.sound.ModSounds;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.BiPredicate;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.progression.CombatPaths;
import com.onepiecemod.progression.CombatPaths.Haki;
import com.onepiecemod.race.RacePerks;
import com.onepiecemod.story.StoryGates;

/**
 * What the three kinds of Haki do, and how you train them.
 *
 * - Observation: switched on by default once awakened. Gives a chance to dodge attacks,
 *   and while you sneak, every creature nearby glows so you can "sense" it through walls.
 *   Train it by getting hit by mobs (3x faster while you have Blindness: blindfold training!).
 * - Armament: switch it on with the B key or /haki armament. Harder punches, tougher skin,
 *   and it lets you hit Logia users. Costs hunger while on. Train it with fully charged hits on mobs, bare-handed or with Armament on.
 * - Conqueror's: very rare. 1 in 100 players are born with it, or it can awaken when you beat a boss.
 *   Press G (or /haki conqueror) to release it: weak hostile mobs nearby faint, strong ones freeze.
 */
public class HakiPowers {
	/** Characters who teach Haki when you sneak and right-click them (friendly version only). */
	private static final Set<String> TEACHERS = Set.of("rayleigh");
	private static final int LESSON_PRICE = 20; // Berries
	private static final int LESSON_XP = 60;

	private static final Identifier ARMAMENT_DAMAGE = OnePieceMod.id("armament_haki");
	private static final Identifier ARMAMENT_ARMOR = OnePieceMod.id("armament_haki_armor");

	public static void initialize() {
		PayloadTypeRegistry.clientboundPlay().register(HakiSensePayload.TYPE, HakiSensePayload.CODEC);

		// Observation Haki: see the attack coming and step aside.
		ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) -> {
			if (!(entity instanceof ServerPlayer player)) {
				return true;
			}
			Entity attacker = source.getEntity();
			if (attacker == null || attacker == player || source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
				return true;
			}

			HakiData haki = HakiAttachments.get(player);
			int level = haki.observationLevel();
			if (haki.observationOn() && level >= HakiData.MAX_LEVEL && futureSightReady(player)) {
				// Future Sight: you saw this one coming seconds ago. Dodge it for sure and strike back faster.
				int cooldown = CombatPaths.has(player, Haki.OBSERVATION, 3, "a") ? FUTURE_SIGHT_COOLDOWN_CLEAR : FUTURE_SIGHT_COOLDOWN;
				player.setAttached(HakiAttachments.FUTURE_SIGHT_READY_AT, player.level().getGameTime() + cooldown);
				dodge(player, attacker);
				afterDodge(player);
				if (CombatPaths.has(player, Haki.OBSERVATION, 3, "b")) {
					foresightStrike(player, attacker);
				}
				player.addEffect(new MobEffectInstance(MobEffects.SPEED, 40, 1, false, false));
				player.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 40, 0, false, false));
				player.sendSystemMessage(Component.literal("Future Sight!").withStyle(ChatFormatting.LIGHT_PURPLE, ChatFormatting.BOLD), true);
				return false;
			}
			float chance = dodgeChance(level) + (CombatPaths.has(player, Haki.OBSERVATION, 1, "b") ? 0.06f : 0);
			if (haki.observationOn() && level >= 1 && player.getRandom().nextFloat() < chance) {
				dodge(player, attacker);
				afterDodge(player);
				addObservationXp(player, 2);
				return false; // false means "cancel this damage"
			}

			// Getting hit is how you learn to see it coming. Training blind (Blindness effect) is 5x faster.
			addObservationXp(player, player.hasEffect(MobEffects.BLINDNESS) ? 3 : 1);
			return true;
		});

		// Armament Haki: punching trains it, and with it on your hits land with a black flash.
		AttackEntityCallback.EVENT.register((player, level, hand, target, hitResult) -> {
			if (level.isClientSide() || !(player instanceof ServerPlayer serverPlayer) || !(target instanceof LivingEntity)) {
				return InteractionResult.PASS;
			}
			boolean bareHanded = player.getMainHandItem().isEmpty();
			boolean active = hasArmamentActive(player);
			// Only full-strength hits on real fighters count, so spam-clicking or punching armor stands doesn't train it.
			boolean realHit = player.getAttackStrengthScale(0.5f) >= 0.9f && (target instanceof Mob || target instanceof Player);
			if ((bareHanded || active) && realHit) {
				addArmamentXp(serverPlayer, 1);
			}
			if (active) {
				ServerLevel serverLevel = (ServerLevel) level;
				serverLevel.sendParticles(ParticleTypes.SQUID_INK, target.getX(), target.getY() + target.getBbHeight() / 2,
						target.getZ(), 6, 0.2, 0.2, 0.2, 0.02);
				serverLevel.playSound(null, target.getX(), target.getY(), target.getZ(), ModSounds.ARMAMENT_HIT,
						SoundSource.PLAYERS, 0.3f, 1.6f);
			}
			return InteractionResult.PASS; // PASS lets the normal attack still happen.
		});

		// Mastered Armament (Ryou) and Conqueror's coating: an extra blow that goes through armor.
		ServerLivingEntityEvents.AFTER_DAMAGE.register((entity, source, baseDamage, damageTaken, blocked) -> {
			if (damageTaken > 0 && entity.isAlive() && source.getDirectEntity() instanceof ServerPlayer player
					&& source.getEntity() == player && source.is(DamageTypes.PLAYER_ATTACK)) {
				advancedHit(player, entity, damageTaken);
			}
		});

		// Beating a boss can awaken Conqueror's Haki (the stronger the boss, the better the odds).
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (entity instanceof CharacterEntity character && character.isBoss()
					&& source.getEntity() instanceof ServerPlayer player) {
				onBossDefeated(player, character.getData().tier, character.getCharacterId());
			}
		});

		// Rayleigh's lessons: sneak + right-click him to pay for a training session.
		UseEntityCallback.EVENT.register((player, level, hand, entity, hitResult) -> {
			if (hand != InteractionHand.MAIN_HAND || !player.isShiftKeyDown()
					|| !(entity instanceof CharacterEntity teacher) || teacher.isBoss()
					|| !TEACHERS.contains(teacher.getCharacterId())) {
				return InteractionResult.PASS;
			}
			if (player instanceof ServerPlayer serverPlayer) {
				teach(serverPlayer, teacher);
				com.onepiecemod.progression.PathTraining.showHaki(serverPlayer); // Branching upgrades he can train.
			}
			return InteractionResult.SUCCESS;
		});

		// Things that happen over time: Armament's hunger cost, Observation's sensing, the birth roll.
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			int tick = server.getTickCount();
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				HakiData haki = HakiAttachments.get(player);
				if (!haki.bornRolled()) {
					rollBirth(player, haki);
				}
				if (tick % 20 == 0) {
					updateArmament(player);
				}
				if (tick % 10 == 0) {
					sense(player);
				}
			}
		});
	}

	// ---- For other parts of the mod ----

	/**
	 * True if this attacker's hits are coated in Armament Haki: a player with it switched on, or a strong story
	 * character (Haki users and tier 4-5 bosses). Devil Fruit code should let these hits land on Logia users.
	 */
	public static boolean hasArmamentActive(Entity attacker) {
		if (attacker instanceof Player player) {
			HakiData haki = HakiAttachments.get(player);
			return haki.armamentOn() && haki.armamentLevel() >= 1;
		}
		if (attacker instanceof CharacterEntity character) {
			return "haki".equals(character.getData().power) || character.getData().tier >= 4;
		}
		return false;
	}

	/** Other mods' ways a single hit can carry Armament Haki, like a weapon coated in it (see registerCoatedHit). */
	private static final List<BiPredicate<Entity, DamageSource>> COATED_HITS = new CopyOnWriteArrayList<>();

	/**
	 * Lets another mod say a hit is coated in Armament Haki even when the attacker's body isn't, like One Piece
	 * Arsenal's Haki-imbued weapons and Black Blades. The check gets the attacker and the hit.
	 */
	public static void registerCoatedHit(BiPredicate<Entity, DamageSource> check) {
		COATED_HITS.add(check);
	}

	/** True if this hit carries Armament Haki: the attacker has it on, or another mod says the hit is coated. */
	public static boolean isCoatedHit(Entity attacker, DamageSource source) {
		if (hasArmamentActive(attacker)) {
			return true;
		}
		for (BiPredicate<Entity, DamageSource> check : COATED_HITS) {
			if (check.test(attacker, source)) {
				return true;
			}
		}
		return false;
	}

	// ---- Switching Haki on and off (used by /haki and the V, B and G keys) ----

	public static void toggleObservation(ServerPlayer player) {
		HakiData haki = HakiAttachments.get(player);
		if (haki.observationLevel() < 1) {
			tell(player, "You haven't awakened Observation Haki yet. " + HakiData.xpToNext(haki.observationXp())
					+ " more training needed: take hits from mobs, ideally while blind.", ChatFormatting.GRAY);
			return;
		}
		boolean on = !haki.observationOn();
		HakiAttachments.set(player, haki.withObservationOn(on));
		if (on) ModSounds.play(player, ModSounds.OBSERVATION_ON, 0.7f);
		tell(player, on ? "Observation Haki: ON. Sneak to sense what's around you." : "Observation Haki: OFF.",
				ChatFormatting.AQUA);
	}

	public static void toggleArmament(ServerPlayer player) {
		HakiData haki = HakiAttachments.get(player);
		if (haki.armamentLevel() < 1) {
			tell(player, "You haven't awakened Armament Haki yet. " + HakiData.xpToNext(haki.armamentXp())
					+ " more training needed: punch mobs with your bare hands.", ChatFormatting.GRAY);
			return;
		}
		boolean on = !haki.armamentOn();
		if (on && tooHungryForArmament(player)) {
			tell(player, "You're too hungry to use Armament Haki. Eat something first.", ChatFormatting.RED);
			return;
		}
		HakiAttachments.set(player, haki.withArmamentOn(on));
		updateArmament(player);
		if (on) {
			com.onepiecemod.anim.CombatAnims.play(player, com.onepiecemod.anim.Anim.POWER_UP);
		}
		tell(player, on ? "Armament Haki: ON. Your arms harden black." : "Armament Haki: OFF.", ChatFormatting.DARK_GRAY);
		if (on) {
			player.level().playSound(null, player.getX(), player.getY(), player.getZ(), ModSounds.ARMAMENT_ON,
					SoundSource.PLAYERS, 0.5f, 1.4f);
		}
	}

	/** Seconds until Conqueror's Haki can be used again, 0 if ready. The HUD shows this. */
	public static int conquerorSecondsLeft(ServerPlayer player) {
		long ticks = player.getAttachedOrElse(HakiAttachments.CONQUEROR_READY_AT, 0L) - player.level().getGameTime();
		return ticks <= 0 ? 0 : (int) ((ticks + 19) / 20);
	}

	/** Releases a wave of Conqueror's Haki. Weak hostile mobs faint, strong ones freeze up. */
	public static void releaseConqueror(ServerPlayer player) {
		HakiData haki = HakiAttachments.get(player);
		if (!haki.conqueror()) {
			tell(player, "You don't have the will of a king... yet. Beating strong bosses might awaken it.", ChatFormatting.GRAY);
			return;
		}
		long now = player.level().getGameTime();
		long readyAt = player.getAttachedOrElse(HakiAttachments.CONQUEROR_READY_AT, 0L);
		if (now < readyAt) {
			tell(player, "Your will needs to recover: " + ((readyAt - now) / 20 + 1) + "s.", ChatFormatting.GRAY);
			return;
		}
		if (tooHungry(player)) {
			tell(player, "You're too hungry to use Conqueror's Haki. Eat something first.", ChatFormatting.RED);
			return;
		}

		int level = haki.conquerorLevel();
		ServerLevel serverLevel = (ServerLevel) player.level();
		boolean overwhelming = CombatPaths.has(player, Haki.CONQUEROR, 1, "a");
		boolean crown = CombatPaths.has(player, Haki.CONQUEROR, 2, "a");
		double radius = 6 + 2 * level + (overwhelming ? 4 : 0);
		float faintBelow = 10 + 15 * level + (overwhelming ? 15 : 0); // Mobs with less max health than this faint. Zombies have 20.
		int fainted = 0;

		for (LivingEntity target : serverLevel.getEntitiesOfClass(LivingEntity.class, player.getBoundingBox().inflate(radius),
				e -> e != player && e.isAlive())) {
			if (target instanceof Player other) {
				other.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 100, 0));
				other.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 2));
			} else if (target instanceof CharacterEntity character && character.isBoss()) {
				// Bosses have Haki of their own: they only flinch. Crown of Will makes them buckle.
				target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, crown ? 80 : 40, 3));
				if (crown) {
					target.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 80, 1));
				}
			} else if (target instanceof Enemy || (target instanceof Mob mob && mob.getTarget() == player)) {
				if (target.getMaxHealth() <= faintBelow) {
					// They pass out cold. Huge damage so armor can't save them; counts as your kill for drops.
					target.hurtServer(serverLevel, player.damageSources().playerAttack(player), target.getMaxHealth() * 100);
					serverLevel.sendParticles(ParticleTypes.BUBBLE_POP, target.getX(), target.getEyeY(), target.getZ(),
							8, 0.2, 0.1, 0.2, 0.02);
					fainted++;
				} else {
					target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 3));
					target.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 80, 1));
				}
			}
			// Animals and friendly characters are left alone: a king's will only crushes those who oppose them.
		}

		com.onepiecemod.anim.CombatAnims.play(player, com.onepiecemod.anim.Anim.ROAR);
		serverLevel.sendParticles(ParticleTypes.ELECTRIC_SPARK, player.getX(), player.getY() + 1, player.getZ(),
				80, radius / 2, 1.0, radius / 2, 0.2);
		com.onepiecemod.fx.ElementFx.conqueror(player, serverLevel, radius); // The red-black shockwave.
		serverLevel.playSound(null, player.getX(), player.getY(), player.getZ(), ModSounds.CONQUEROR_BURST,
				SoundSource.PLAYERS, 2.0f, 1.0f);
		if (!player.getAbilities().instabuild) {
			player.causeFoodExhaustion(12.0f); // About 3 hunger points.
		}
		long cooldown = Math.max(20, 60 - 8 * level) * 20L;
		if (CombatPaths.has(player, Haki.CONQUEROR, 1, "b")) {
			cooldown = cooldown * 3 / 4; // Kingly Presence.
		}
		player.setAttached(HakiAttachments.CONQUEROR_READY_AT, now + cooldown);
		if (CombatPaths.has(player, Haki.CONQUEROR, 2, "b")) {
			rally(player, serverLevel, radius);
		}
		addConquerorXp(player, 2 + 3 * fainted);
		tell(player, fainted > 0 ? fainted + " enemies fainted from your Conqueror's Haki!" : "Your Conqueror's Haki shakes the air.",
				ChatFormatting.DARK_PURPLE);
	}

	// ---- How each power works ----

	/** Level 1: 8%, level 4: 20%, level 5 (Future Sight): 35%. */
	private static float dodgeChance(int level) {
		return level >= HakiData.MAX_LEVEL ? 0.35f : 0.04f + 0.04f * level;
	}

	private static void dodge(ServerPlayer player, Entity attacker) {
		// Hop a little to the side of the attack.
		double dx = player.getX() - attacker.getX();
		double dz = player.getZ() - attacker.getZ();
		double length = Math.max(0.01, Math.sqrt(dx * dx + dz * dz));
		player.setDeltaMovement(player.getDeltaMovement().add(-dz / length * 0.4, 0.1, dx / length * 0.4));
		Motion.sync(player);

		ServerLevel level = (ServerLevel) player.level();
		level.sendParticles(ParticleTypes.CLOUD, player.getX(), player.getY() + 1, player.getZ(), 5, 0.3, 0.3, 0.3, 0.01);
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.PLAYER_ATTACK_NODAMAGE,
				SoundSource.PLAYERS, 0.8f, 1.5f);
		player.sendSystemMessage(Component.literal("Dodged!").withStyle(ChatFormatting.AQUA), true);
	}

	/** Future Sight (Observation level 5) can save you from one hit every few seconds. */
	private static final int FUTURE_SIGHT_COOLDOWN = 20 * 8;
	private static final int FUTURE_SIGHT_COOLDOWN_CLEAR = 20 * 5;

	/** Observation tier 2 paths: Counter (Strength II) or Swift Reflexes (Speed II and a little healing) after a dodge. */
	private static void afterDodge(ServerPlayer player) {
		if (CombatPaths.has(player, Haki.OBSERVATION, 2, "a")) {
			player.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 60, 1, false, true));
		} else if (CombatPaths.has(player, Haki.OBSERVATION, 2, "b")) {
			player.addEffect(new MobEffectInstance(MobEffects.SPEED, 60, 1, false, true));
			player.heal(1.0f);
		}
	}

	/** Observation tier 3 B: Future Sight dodges and strikes back in the same breath. */
	private static void foresightStrike(ServerPlayer player, Entity attacker) {
		if (!(attacker instanceof LivingEntity target) || !target.isAlive() || player.distanceToSqr(target) > 36) {
			return;
		}
		ServerLevel level = (ServerLevel) player.level();
		target.damageCooldownTime = 0;
		target.hurtServer(level, player.damageSources().playerAttack(player), 8.0f);
		level.sendParticles(ParticleTypes.CRIT, target.getX(), target.getY() + target.getBbHeight() / 2, target.getZ(),
				12, 0.3, 0.3, 0.3, 0.2);
	}

	/** Conqueror's tier 2 B: your crew, allies and pets nearby fight harder. */
	private static void rally(ServerPlayer player, ServerLevel level, double radius) {
		for (LivingEntity ally : level.getEntitiesOfClass(LivingEntity.class, player.getBoundingBox().inflate(radius),
				e -> e.isAlive() && (e == player
						|| (e instanceof net.minecraft.world.entity.TamableAnimal pet && pet.isOwnedBy(player))
						|| (e instanceof Player other && com.onepiecemod.multiplayer.PlayerCrews.friendly(level.getServer(), player, other))))) {
			ally.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 200, 0));
			ally.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 200, 0));
		}
		tell(player, "Your will rallies your crew!", ChatFormatting.GOLD);
	}

	private static boolean futureSightReady(ServerPlayer player) {
		return player.level().getGameTime() >= player.getAttachedOrElse(HakiAttachments.FUTURE_SIGHT_READY_AT, 0L);
	}

	/**
	 * Level 5 Armament (Advanced Armament, "Ryou"): your Haki flows inside the target, so a quarter of every melee hit
	 * lands again as damage armor can't stop, and they're pushed back. Mastered Conqueror's on top of that
	 * ("coating" your hits with the will of a king) adds another 15%, black lightning and Weakness.
	 */
	private static void advancedHit(ServerPlayer player, LivingEntity target, float damage) {
		HakiData haki = HakiAttachments.get(player);
		boolean ryou = haki.armamentOn() && haki.armamentLevel() >= HakiData.MAX_LEVEL;
		boolean coated = haki.armamentOn() && haki.armamentLevel() >= 1 && haki.conqueror()
				&& haki.conquerorLevel() >= HakiData.MAX_LEVEL;
		if (!ryou && !coated) {
			return;
		}
		ServerLevel level = (ServerLevel) player.level();
		float ryouShare = CombatPaths.has(player, Haki.ARMAMENT, 3, "a") ? 0.40f : 0.25f; // Ryou Burst.
		float extra = (ryou ? ryouShare : 0) * damage + (coated ? 0.15f : 0) * damage;
		target.damageCooldownTime = 0; // The extra blow is part of the same punch, so let it through.
		target.hurtServer(level, player.damageSources().indirectMagic(player, player), extra);
		if (ryou) {
			Vec3 push = target.position().subtract(player.position()).multiply(1, 0, 1).normalize().scale(0.5);
			target.push(push.x, 0.15, push.z);
			level.sendParticles(ParticleTypes.SONIC_BOOM, target.getX(), target.getY() + target.getBbHeight() / 2, target.getZ(),
					1, 0, 0, 0, 0);
			if (CombatPaths.has(player, Haki.ARMAMENT, 3, "b")) {
				emission(player, level, target, damage * 0.4f);
			}
		}
		if (coated) {
			target.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 60, 0), player);
			level.sendParticles(ParticleTypes.ELECTRIC_SPARK, target.getX(), target.getY() + target.getBbHeight() / 2,
					target.getZ(), 14, 0.4, 0.5, 0.4, 0.3);
			level.sendParticles(ParticleTypes.SQUID_INK, target.getX(), target.getY() + target.getBbHeight() / 2,
					target.getZ(), 8, 0.3, 0.4, 0.3, 0.05);
		}
	}

	/** Armament tier 3 B (Emission): the blow bursts out of the target and hits up to 2 enemies behind it. */
	private static void emission(ServerPlayer player, ServerLevel level, LivingEntity target, float damage) {
		Vec3 dir = target.position().subtract(player.position()).multiply(1, 0, 1);
		if (dir.lengthSqr() < 1.0e-4) {
			return;
		}
		dir = dir.normalize();
		Vec3 from = target.position();
		int hits = 0;
		for (LivingEntity other : level.getEntitiesOfClass(LivingEntity.class, target.getBoundingBox().inflate(4),
				e -> e != target && e != player && e.isAlive() && com.onepiecemod.style.StyleMoves.isEnemy(player, e))) {
			Vec3 to = other.position().subtract(from).multiply(1, 0, 1);
			if (to.lengthSqr() > 16 || to.normalize().dot(dir) < 0.5) {
				continue;
			}
			other.hurtServer(level, player.damageSources().indirectMagic(player, player), damage);
			level.sendParticles(ParticleTypes.SQUID_INK, other.getX(), other.getY() + other.getBbHeight() / 2, other.getZ(),
					6, 0.2, 0.3, 0.2, 0.05);
			if (++hits >= 2) {
				break;
			}
		}
	}

	/**
	 * While sneaking with Observation on, nearby creatures glow (you can see them through walls).
	 * The glow is sent only to you, so other players don't see your targets light up.
	 */
	private static void sense(ServerPlayer player) {
		HakiData haki = HakiAttachments.get(player);
		int level = haki.observationLevel();
		if (!haki.observationOn() || level < 1 || !player.isShiftKeyDown()
				|| !ServerPlayNetworking.canSend(player, HakiSensePayload.TYPE)) {
			return;
		}
		double radius = (8 + 6 * level) * (CombatPaths.has(player, Haki.OBSERVATION, 1, "a") ? 1.5 : 1.0); // Wide Sense.
		List<Integer> ids = new ArrayList<>();
		for (LivingEntity target : player.level().getEntitiesOfClass(LivingEntity.class, player.getBoundingBox().inflate(radius),
				e -> e != player && e.isAlive())) {
			if (ids.size() < 256) {
				ids.add(target.getId());
			}
		}
		ServerPlayNetworking.send(player, new HakiSensePayload(ids));
		if (!player.getAbilities().instabuild) {
			player.causeFoodExhaustion(0.05f);
		}
	}

	/** Adds or removes Armament's damage and armor bonus, and charges its hunger cost. Runs once a second. */
	private static void updateArmament(ServerPlayer player) {
		HakiData haki = HakiAttachments.get(player);
		int level = haki.armamentLevel();
		boolean on = haki.armamentOn() && level >= 1;

		if (on && tooHungryForArmament(player)) {
			HakiAttachments.set(player, haki.withArmamentOn(false));
			tell(player, "You're too hungry to keep up Armament Haki. It fades.", ChatFormatting.RED);
			on = false;
		}

		AttributeInstance damage = player.getAttribute(Attributes.ATTACK_DAMAGE);
		AttributeInstance armor = player.getAttribute(Attributes.ARMOR);
		damage.removeModifier(ARMAMENT_DAMAGE);
		armor.removeModifier(ARMAMENT_ARMOR);
		if (!on) {
			return;
		}
		// Level 1: +2 damage. Level 5: +6 damage and +8 armor. Paths add more (Iron Body, Hardened Fists, Blade Coating).
		ItemStack hand = player.getMainHandItem();
		double bonusDamage = 1 + level;
		if (CombatPaths.has(player, Haki.ARMAMENT, 1, "b") && com.onepiecemod.style.StyleMoves.fistsFree(hand)) {
			bonusDamage += 2;
		}
		if (CombatPaths.has(player, Haki.ARMAMENT, 2, "a") && hand.is(net.minecraft.tags.ItemTags.SWORDS)) {
			bonusDamage += 2;
		}
		damage.addTransientModifier(new AttributeModifier(ARMAMENT_DAMAGE, bonusDamage, AttributeModifier.Operation.ADD_VALUE));
		double bonusArmor = (level >= 2 ? 2 * (level - 1) : 0) + (CombatPaths.has(player, Haki.ARMAMENT, 1, "a") ? 3 : 0);
		if (bonusArmor > 0) {
			armor.addTransientModifier(new AttributeModifier(ARMAMENT_ARMOR, bonusArmor, AttributeModifier.Operation.ADD_VALUE));
		}
		if (!player.getAbilities().instabuild) {
			// About 1 hunger point every 20 seconds, half that with Efficient Will.
			player.causeFoodExhaustion(CombatPaths.has(player, Haki.ARMAMENT, 2, "b") ? 0.1f : 0.2f);
		}
	}

	private static void onBossDefeated(ServerPlayer player, int tier, String bossId) {
		HakiData haki = HakiAttachments.get(player);
		if (haki.conqueror()) {
			addConquerorXp(player, 40 * tier);
			return;
		}
		if (!StoryGates.conquerorRollAllowed(player, bossId)) {
			return; // With story gates on, only the first win against each boss rolls.
		}
		// Tier 1 boss: 2%. Tier 5 (Emperors and Admirals): 10%.
		if (player.getRandom().nextFloat() < 0.02f * tier) {
			HakiAttachments.set(player, haki.withConqueror(true));
			announceConqueror(player, "In the heat of battle, the will of a king awakens in you!");
		}
	}

	/** The first time we see a player, roll the 1 in 100 chance that they were born with Conqueror's Haki. */
	private static void rollBirth(ServerPlayer player, HakiData haki) {
		if (player.getRandom().nextInt(100) == 0) {
			HakiAttachments.set(player, haki.withConqueror(true));
			announceConqueror(player, "You were born with the Conqueror's Haki. Only one in a million has it!");
		} else {
			HakiAttachments.set(player, haki.withBornRolled());
		}
	}

	private static void announceConqueror(ServerPlayer player, String message) {
		tell(player, message, ChatFormatting.DARK_PURPLE);
		tell(player, "Press G (or type /haki conqueror) to release it.", ChatFormatting.LIGHT_PURPLE);
		player.level().playSound(null, player.getX(), player.getY(), player.getZ(), ModSounds.CONQUEROR_AWAKEN,
				SoundSource.PLAYERS, 1.0f, 1.0f);
	}

	private static void teach(ServerPlayer player, CharacterEntity teacher) {
		String name = teacher.getData().name;
		boolean free = player.getAbilities().instabuild; // Creative mode lessons are free, handy for testing.
		if (!free && count(player.getInventory(), CharacterFeature.BERRY) < LESSON_PRICE) {
			tell(player, name + ": Lessons cost " + LESSON_PRICE + " Berries. Even I need to pay my bar tab.", ChatFormatting.YELLOW);
			return;
		}
		if (!free) {
			take(player.getInventory(), CharacterFeature.BERRY, LESSON_PRICE);
		}
		tell(player, name + ": Feel the presence around you... and harden your will!", ChatFormatting.YELLOW);
		addObservationXp(player, LESSON_XP);
		addArmamentXp(player, LESSON_XP);
	}

	/** Armament fades at 3 food (6 normally) with the Efficient Will path. */
	private static boolean tooHungryForArmament(ServerPlayer player) {
		int limit = CombatPaths.has(player, Haki.ARMAMENT, 2, "b") ? 3 : 6;
		return !player.getAbilities().instabuild && player.getFoodData().getFoodLevel() <= limit;
	}

	// ---- Training ----

	public static void addObservationXp(ServerPlayer player, int amount) {
		amount = RacePerks.hakiXp(player, com.onepiecemod.config.ModConfig.scale(amount, com.onepiecemod.config.ModConfig.hakiXp()), true); // Humans and Skypieans learn faster.
		HakiData haki = HakiAttachments.get(player);
		int before = haki.observationLevel();
		haki = haki.withObservationXp(haki.observationXp() + amount);
		HakiAttachments.set(player, haki);
		levelUp(player, "Observation Haki", before, haki.observationLevel(),
				before == 0 ? "You can sense the presence of others! Sneak to see them. Press V to switch it off." : null);
	}

	public static void addArmamentXp(ServerPlayer player, int amount) {
		amount = RacePerks.hakiXp(player, com.onepiecemod.config.ModConfig.scale(amount, com.onepiecemod.config.ModConfig.hakiXp()), false); // Humans learn faster.
		HakiData haki = HakiAttachments.get(player);
		int before = haki.armamentLevel();
		haki = haki.withArmamentXp(haki.armamentXp() + amount);
		HakiAttachments.set(player, haki);
		levelUp(player, "Armament Haki", before, haki.armamentLevel(),
				before == 0 ? "Your fists can harden with will! Press B to switch it on." : null);
	}

	public static void addConquerorXp(ServerPlayer player, int amount) {
		amount = com.onepiecemod.config.ModConfig.scale(amount, com.onepiecemod.config.ModConfig.hakiXp());
		HakiData haki = HakiAttachments.get(player);
		int before = haki.conquerorLevel();
		haki = haki.withConquerorXp(haki.conquerorXp() + amount);
		HakiAttachments.set(player, haki);
		levelUp(player, "Conqueror's Haki", before, haki.conquerorLevel(), null);
	}

	private static void levelUp(ServerPlayer player, String name, int before, int after, String firstTimeTip) {
		if (after <= before) {
			return;
		}
		String title = after >= HakiData.MAX_LEVEL ? name + " mastered!" : before == 0 ? name + " awakened!" : name + " level " + after + "!";
		tell(player, title, ChatFormatting.GOLD);
		if (firstTimeTip != null) {
			tell(player, firstTimeTip, ChatFormatting.YELLOW);
		}
		if (after >= HakiData.MAX_LEVEL) {
			String masteryTip = switch (name) {
				case "Observation Haki" -> "Future Sight: every 8 seconds you see the next attack coming and dodge it for sure.";
				case "Armament Haki" -> "Advanced Armament: your punches and sword hits now strike inside the enemy, through their armor.";
				default -> "Conqueror's coating: with Armament on, your hits carry the will of a king.";
			};
			tell(player, masteryTip, ChatFormatting.LIGHT_PURPLE);
		}
		player.level().playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.PLAYER_LEVELUP,
				SoundSource.PLAYERS, 0.8f, 1.2f);
	}

	// ---- Small helpers ----

	private static boolean tooHungry(ServerPlayer player) {
		return !player.getAbilities().instabuild && player.getFoodData().getFoodLevel() <= 6;
	}

	private static void tell(ServerPlayer player, String message, ChatFormatting color) {
		player.sendSystemMessage(Component.literal(message).withStyle(color));
	}

	private static int count(Inventory inventory, Item item) {
		int total = 0;
		for (int i = 0; i < inventory.getContainerSize(); i++) {
			ItemStack stack = inventory.getItem(i);
			if (stack.is(item)) {
				total += stack.getCount();
			}
		}
		return total;
	}

	private static void take(Inventory inventory, Item item, int amount) {
		for (int i = 0; i < inventory.getContainerSize() && amount > 0; i++) {
			ItemStack stack = inventory.getItem(i);
			if (stack.is(item)) {
				int used = Math.min(amount, stack.getCount());
				stack.shrink(used);
				amount -= used;
			}
		}
	}
}
