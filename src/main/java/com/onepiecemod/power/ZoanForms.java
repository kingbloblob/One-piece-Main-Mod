package com.onepiecemod.power;

import java.util.Map;

import io.netty.buffer.ByteBuf;

import com.mojang.serialization.Codec;

import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentSyncPredicate;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.anim.Anim;
import com.onepiecemod.anim.CombatAnims;
import com.onepiecemod.fx.MoveFx;
import com.onepiecemod.fx.MoveStyle;

/**
 * Zoan fruits that really change your body: while the form lasts, everyone sees you as Lucci's leopard
 * form, Marco's blue phoenix, Kaido's dragon or Chopper's Heavy Point (drawn by zoan.client.ZoanRenderer),
 * and Sneak + R becomes the form's signature attack. The phoenix can fly.
 * The form ends when its time runs out, when you touch the sea, or when you die.
 */
public final class ZoanForms {
	/** Which fruit gives which form. The form id names the model and texture in zoan.client. */
	public static final Map<String, String> FORM_OF_FRUIT = Map.of(
			"neko_neko_no_mi_leopard", "leopard",
			"tori_tori_no_mi_phoenix", "phoenix",
			"uo_uo_no_mi_seiryu", "seiryu",
			"hito_hito_no_mi", "heavy_point",
			"ryu_ryu_no_mi_nidhogg", "nidhogg");

	/** A form someone is in: since/until are game ticks. */
	public record Active(String form, long since, long until) {
		public static final StreamCodec<ByteBuf, Active> STREAM_CODEC = StreamCodec.composite(
				ByteBufCodecs.STRING_UTF8, Active::form,
				ByteBufCodecs.VAR_LONG, Active::since,
				ByteBufCodecs.VAR_LONG, Active::until,
				Active::new);
	}

	/** The form a player is in right now. Sent to every player nearby so they can draw it; not saved. */
	public static final AttachmentType<Active> FORM = AttachmentRegistry.create(
			OnePieceMod.id("zoan_form"),
			builder -> builder.syncWith(Active.STREAM_CODEC, AttachmentSyncPredicate.all()));

	/** Saved: true while the phoenix form gave this player flight, so we can always take it back (even after a crash). */
	private static final AttachmentType<Boolean> GAVE_FLIGHT = AttachmentRegistry.create(
			OnePieceMod.id("zoan_gave_flight"),
			builder -> builder.persistent(Codec.BOOL));

	private ZoanForms() {
	}

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				Active active = player.getAttached(FORM);
				if (active != null) {
					long now = player.level().getGameTime();
					if (now >= active.until() || SeaWeakness.isDrained(player) || !player.isAlive() || player.isSpectator()) {
						end(player);
					} else if (active.form().equals("phoenix")) {
						giveFlight(player);
					}
				} else if (Boolean.TRUE.equals(player.getAttached(GAVE_FLIGHT))) {
					takeFlight(player); // Left the game mid-flight, or the form ended some other way.
				}
			}
		});
	}

	public static Active get(Entity entity) {
		return entity.getAttached(FORM);
	}

	/** Called by a Zoan fruit's R move. Returns true when this fruit has a full-body form. */
	static boolean start(ServerPlayer player, DevilFruit fruit, int ticks) {
		String form = FORM_OF_FRUIT.get(fruit.id());
		if (form == null) {
			return false;
		}
		long now = player.level().getGameTime();
		player.setAttached(FORM, new Active(form, now, now + ticks));
		CombatAnims.play(player, Anim.ROAR);
		return true;
	}

	/**
	 * Puts a player in a form that doesn't come from their fruit's R move (Luffy's Wild Nika, from Gear 5).
	 * Same rules as the others: drawn as the model, ends on timeout, the sea or death, Sneak + R is its signature.
	 */
	public static void startForm(ServerPlayer player, String form, int ticks) {
		long now = player.level().getGameTime();
		player.setAttached(FORM, new Active(form, now, now + ticks));
		CombatAnims.play(player, Anim.ROAR);
	}

	public static void end(ServerPlayer player) {
		Active active = player.getAttached(FORM);
		player.removeAttached(FORM);
		takeFlight(player);
		if (active != null && player.isAlive()) {
			ServerLevel level = (ServerLevel) player.level();
			level.sendParticles(ParticleTypes.POOF, player.getX(), player.getY() + 1, player.getZ(), 30, 0.6, 0.9, 0.6, 0.03);
			player.sendOverlayMessage(Component.translatable("message.onepiece.zoan_form_end"));
		}
	}

	private static void giveFlight(ServerPlayer player) {
		if (player.isCreative() || player.getAbilities().mayfly) {
			return;
		}
		player.getAbilities().mayfly = true;
		player.onUpdateAbilities();
		player.setAttached(GAVE_FLIGHT, true);
	}

	private static void takeFlight(ServerPlayer player) {
		if (!Boolean.TRUE.equals(player.getAttached(GAVE_FLIGHT))) {
			return;
		}
		player.removeAttached(GAVE_FLIGHT);
		if (player.isCreative() || player.isSpectator()) {
			return;
		}
		boolean wasFlying = player.getAbilities().flying;
		player.getAbilities().mayfly = false;
		player.getAbilities().flying = false;
		player.onUpdateAbilities();
		if (wasFlying) {
			// Drift down safely instead of dropping out of the sky.
			player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 200, 0));
		}
	}

	/**
	 * Sneak + R while in a form: the form's signature attack. Returns the cooldown in seconds,
	 * or -1 when you aren't in a form (then the fruit's normal Sneak + R move happens).
	 */
	static int signature(ServerPlayer player, ServerLevel level) {
		Active active = player.getAttached(FORM);
		if (active == null) {
			return -1;
		}
		return switch (active.form()) {
			case "leopard" -> rokuogan(player, level);
			case "phoenix" -> phoenixBrand(player, level);
			case "seiryu" -> boloBreath(player, level);
			case "heavy_point" -> kokuteiCross(player, level);
			case "nidhogg" -> nidhoggThunder(player, level);
			case "nika_wild" -> wildBite(player, level);
			default -> -1;
		};
	}

	/** The name shown when the signature attack is used. */
	static String signatureName(String form) {
		return switch (form) {
			case "leopard" -> "Rokuogan";
			case "phoenix" -> "Phoenix Brand";
			case "seiryu" -> "Bolo Breath";
			case "heavy_point" -> "Kokutei Cross";
			case "nidhogg" -> "Nidhogg Thunder";
			case "nika_wild" -> "Wild Bite";
			default -> "";
		};
	}

	/** Lucci: Rokuogan, a shockwave punched straight out of both fists. Hits everything in front of you. */
	private static int rokuogan(ServerPlayer player, ServerLevel level) {
		CombatAnims.play(player, Anim.PUNCH);
		Vec3 look = player.getLookAngle();
		Vec3 front = player.getEyePosition().add(look.scale(2.5));
		for (LivingEntity target : FruitAbilities.nearby(player, level, 7)) {
			Vec3 to = target.getBoundingBox().getCenter().subtract(player.getEyePosition()).normalize();
			if (to.dot(look) > 0.6) {
				FruitAbilities.hit(player, target, level, 16);
				FruitAbilities.push(target, player, 3.2, 0.5);
			}
		}
		MoveFx.at(level, MoveStyle.RING, front, look.scale(2.5), 0xFFFFFFFF, 0xFFE0B040, 1.6f, 14, null);
		MoveFx.at(level, MoveStyle.RING, front.add(look.scale(2.0)), look.scale(3.0), 0xFFFFFFFF, 0xFFE0B040, 2.4f, 16, null);
		level.sendParticles(ParticleTypes.SONIC_BOOM, front.x, front.y, front.z, 1, 0, 0, 0, 0);
		FruitAbilities.sound(level, player, com.onepiecemod.sound.StyleSounds.SHOCK_PUNCH);
		return 7;
	}

	/** Marco: Phoenix Brand, a flying kick in blue fire. Hits everything along the way and heals you a little. */
	private static int phoenixBrand(ServerPlayer player, ServerLevel level) {
		CombatAnims.play(player, Anim.KICK);
		Vec3 start = player.position();
		Vec3 look = player.getLookAngle();
		for (LivingEntity target : FruitAbilities.nearby(player, level, 10)) {
			Vec3 rel = target.position().subtract(start);
			double along = rel.dot(look);
			if (along > 0 && along < 10 && rel.subtract(look.scale(along)).length() < 2.0) {
				FruitAbilities.hit(player, target, level, 12);
				FruitAbilities.push(target, player, 2.0, 0.6);
			}
		}
		FruitAbilities.dash(player, 2.2, 0.15);
		player.heal(4);
		MoveFx.at(level, MoveStyle.BEAM, start.add(0, 1, 0), look.scale(10), MoveFx.BLUE_FIRE, MoveFx.BLUE_FIRE_OUT, 1.4f, 14, null);
		level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, player.getX(), player.getY() + 1, player.getZ(), 40, 1.0, 0.6, 1.0, 0.04);
		FruitAbilities.sound(level, player, com.onepiecemod.sound.StyleSounds.FIRE_KICK);
		return 6;
	}

	/** Kaido: Bolo Breath from the dragon's jaws. A long blast of fire that bursts where it lands. */
	private static int boloBreath(ServerPlayer player, ServerLevel level) {
		CombatAnims.play(player, Anim.ROAR);
		FruitAbilities.look = MoveFx.DRAGON_BREATH;
		LivingEntity first = FruitAbilities.beam(player, level, 32, ParticleTypes.FLAME);
		Vec3 burst = first != null ? first.position() : player.getEyePosition().add(player.getLookAngle().scale(16));
		for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, new AABB(burst, burst).inflate(4),
				target -> FruitAbilities.isValidTarget(player, target))) {
			FruitAbilities.hit(player, target, level, 18);
			target.igniteForSeconds(8);
		}
		MoveFx.shockwave(level, burst, 4, MoveFx.FIRE, MoveFx.FIRE_OUT);
		level.sendParticles(ParticleTypes.EXPLOSION, burst.x, burst.y + 1, burst.z, 4, 1.5, 0.5, 1.5, 0);
		FruitAbilities.sound(level, player, com.onepiecemod.sound.ModSounds.MOVE_DRAGON_ROAR);
		return 8;
	}

	/** Chopper: Kokutei Cross, two huge hooves crossing into an X. Big damage and big knockback on one target. */
	private static int kokuteiCross(ServerPlayer player, ServerLevel level) {
		CombatAnims.play(player, Anim.BARRAGE);
		FruitAbilities.look = MoveFx.CLAWS;
		LivingEntity target = FruitAbilities.beam(player, level, 5, ParticleTypes.CRIT);
		if (target != null) {
			FruitAbilities.hit(player, target, level, 15);
			FruitAbilities.push(target, player, 3.5, 0.7);
			Vec3 at = target.getBoundingBox().getCenter();
			level.sendParticles(ParticleTypes.CRIT, at.x, at.y, at.z, 40, 0.6, 0.6, 0.6, 0.3);
		}
		FruitAbilities.sound(level, player, com.onepiecemod.sound.StyleSounds.PUNCH);
		return 6;
	}

	/** Loki: the Nidhogg's thunder. A bolt-wreathed dragon breath that calls lightning down where it lands. */
	private static int nidhoggThunder(ServerPlayer player, ServerLevel level) {
		CombatAnims.play(player, Anim.ROAR);
		FruitAbilities.look = MoveFx.THUNDER_BREATH;
		LivingEntity first = FruitAbilities.beam(player, level, 28, ParticleTypes.ELECTRIC_SPARK);
		Vec3 burst = first != null ? first.position() : player.getEyePosition().add(player.getLookAngle().scale(14));
		for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, new AABB(burst, burst).inflate(4),
				target -> FruitAbilities.isValidTarget(player, target))) {
			FruitAbilities.hit(player, target, level, 16);
			FruitControl.apply(target, new MobEffectInstance(MobEffects.SLOWNESS, 40, 1));
		}
		FruitAbilities.lightning(level, burst);
		MoveFx.bolt(level, burst, 2.4f);
		level.sendParticles(ParticleTypes.ELECTRIC_SPARK, burst.x, burst.y + 1, burst.z, 60, 2.0, 1.0, 2.0, 0.2);
		FruitAbilities.sound(level, player, com.onepiecemod.sound.ModSounds.MOVE_DRAGON_ROAR);
		return 8;
	}

	/** Luffy, Wild Nika: a feral leap onto the nearest enemy and a rubbery bite that heals you. */
	private static int wildBite(ServerPlayer player, ServerLevel level) {
		CombatAnims.play(player, Anim.POUNCE);
		LivingEntity target = FruitAbilities.beam(player, level, 8, ParticleTypes.CLOUD);
		FruitAbilities.dash(player, 1.6, 0.5);
		if (target != null) {
			FruitAbilities.hit(player, target, level, 14);
			FruitAbilities.push(target, player, 1.2, 0.9);
			player.heal(5);
			Vec3 at = target.getBoundingBox().getCenter();
			level.sendParticles(ParticleTypes.CRIT, at.x, at.y, at.z, 30, 0.5, 0.5, 0.5, 0.3);
			level.sendParticles(ParticleTypes.CLOUD, at.x, at.y, at.z, 20, 0.6, 0.6, 0.6, 0.05);
		}
		FruitAbilities.sound(level, player, SoundEvents.RAVAGER_ATTACK);
		return 5;
	}
}
