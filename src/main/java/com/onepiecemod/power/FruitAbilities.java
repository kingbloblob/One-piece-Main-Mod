package com.onepiecemod.power;

import com.onepiecemod.util.Motion;
import net.minecraft.world.level.block.BonemealSource;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.BonemealableBlock;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.fx.MoveFx;
import com.onepiecemod.multiplayer.PlayerCrews;
import com.onepiecemod.fx.MoveStyle;
import com.onepiecemod.sound.FruitSounds;

/**
 * The moves of every Devil Fruit.
 * Press R for the first move, or sneak and press R for the second one.
 *
 * Damage is in half-hearts: 10 damage = 5 hearts.
 * Effect times are in ticks: 20 ticks = 1 second.
 */
public class FruitAbilities {
	// Set when a move hurts something, so the move counts toward Devil Fruit mastery.
	private static boolean hitSomething;
	/** True while a move runs: the move's own sound (FruitSounds) replaces the vanilla sounds it plays at you. */
	private static boolean quietVanilla;

	// The fruit whose move is being used right now, and how the next beam should look (null = pick one).
	// See com.onepiecemod.fx.MoveFx for the shapes.
	private static DevilFruit current;
	static MoveFx.Look look;

	public static void use(ServerPlayer player, DevilFruit fruit, boolean secondary) {
		ServerLevel level = (ServerLevel) player.level();
		long now = level.getGameTime();
		int slot = secondary ? 1 : 0;
		long readyAt = readyAt(player, slot);

		if (now < readyAt) {
			long seconds = (readyAt - now + 19) / 20;
			player.sendOverlayMessage(Component.translatable("message.onepiece.power_cooldown", seconds).withStyle(ChatFormatting.GRAY));
			return;
		}

		hitSomething = false;
		current = fruit;
		look = null;
		quietVanilla = true;
		int cooldownSeconds;
		try {
			cooldownSeconds = secondary ? secondary(player, level, fruit.id()) : primary(player, level, fruit.id());
		} finally {
			quietVanilla = false;
		}
		setReadyAt(player, slot, now + (long) (cooldownSeconds * 20L * Awakening.cooldownMultiplier(player, fruit)
				* com.onepiecemod.config.ModConfig.powerCooldowns()));
		if (cooldownSeconds > 0) {
			FruitSounds.playMove(player, fruit, secondary);
		}

		// Only moves that actually hit an enemy train your fruit.
		if (hitSomething) {
			Awakening.addMastery(player, fruit);
		}

		String move = secondary ? fruit.secondary() : fruit.primary();
		ZoanForms.Active form = ZoanForms.get(player);
		if (secondary && form != null) {
			move = ZoanForms.signatureName(form.form());
		}
		player.sendOverlayMessage(Component.literal(move + "!").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
	}

	/** The R move. Returns the cooldown in seconds. */
	private static int primary(ServerPlayer player, ServerLevel level, String fruit) {
		switch (fruit) {
			case "gomu_gomu_no_mi" -> { // A stretchy punch from far away.
				look = MoveFx.GOMU_ARM;
				LivingEntity target = beam(player, level, 14, ParticleTypes.CRIT);
				if (target != null) {
					hit(player, target, level, 8);
					push(target, player, 2.5, 0.5);
				}
				sound(level, player, SoundEvents.PLAYER_ATTACK_KNOCKBACK);
				return 2;
			}
			case "ope_ope_no_mi" -> { // Swap places with what you look at, or blink forward.
				look = MoveFx.ROOM_LINE;
				MoveFx.room(player, level, 10);
				LivingEntity target = beam(player, level, 24, ParticleTypes.END_ROD);
				if (target != null) {
					Vec3 mine = player.position();
					player.teleportTo(target.getX(), target.getY(), target.getZ());
					target.teleportTo(mine.x, mine.y, mine.z);
					hit(player, target, level, 9); // ...and a scalpel cut on the way.
				} else {
					blink(player, level, 10);
				}
				sound(level, player, SoundEvents.ENDERMAN_TELEPORT);
				return 3;
			}
			case "bara_bara_no_mi" -> { // Fire your fist off your arm.
				look = MoveFx.FLYING_FIST;
				LivingEntity target = beam(player, level, 12, ParticleTypes.CRIT);
				if (target != null) {
					hit(player, target, level, 7);
				}
				sound(level, player, SoundEvents.PLAYER_ATTACK_SWEEP);
				return 2;
			}
			case "gura_gura_no_mi" -> { // Shatter the air in front of you.
				look = MoveFx.QUAKE_CRACK;
				LivingEntity target = beam(player, level, 10, ParticleTypes.EXPLOSION);
				if (target != null) {
					hit(player, target, level, 14);
					push(target, player, 4.0, 0.8);
				}
				sound(level, player, SoundEvents.GENERIC_EXPLODE.value());
				return 5;
			}
			case "soru_soru_no_mi" -> { // Take some of their life for yourself.
				LivingEntity target = beam(player, level, 12, ParticleTypes.WITCH);
				if (target != null) {
					hit(player, target, level, 6);
					FruitControl.apply(target, new MobEffectInstance(MobEffects.WEAKNESS, 200, 1));
					FruitControl.apply(target, new MobEffectInstance(MobEffects.SLOWNESS, 200, 1));
					player.heal(6);
				}
				sound(level, player, SoundEvents.WITCH_CELEBRATE);
				return 8;
			}
			case "jiki_jiki_no_mi" -> { // Throw everything nearby away from you.
				for (LivingEntity target : nearby(player, level, 8)) {
					hit(player, target, level, 8);
					push(target, player, 2.5, 0.4);
				}
				particles(level, player, ParticleTypes.ELECTRIC_SPARK, 40);
				sound(level, player, SoundEvents.ANVIL_LAND);
				return 5;
			}
			case "wara_wara_no_mi" -> { // Curse a target through your straw dolls.
				LivingEntity target = beam(player, level, 14, ParticleTypes.WITCH);
				if (target != null) {
					FruitControl.apply(target, new MobEffectInstance(MobEffects.WITHER, 100, 1));
					FruitControl.apply(target, new MobEffectInstance(MobEffects.WEAKNESS, 100, 1));
					hit(player, target, level, 5);
				}
				sound(level, player, SoundEvents.WITCH_CELEBRATE);
				return 6;
			}
			case "toshi_toshi_no_mi" -> { // Turn a mob into a baby, or weaken a player.
				LivingEntity target = beam(player, level, 12, ParticleTypes.HEART);
				if (target instanceof Mob mob && !mob.isBaby() && !FruitControl.isTough(target)) {
					mob.setBaby(true);
				} else if (target != null) {
					FruitControl.apply(target, new MobEffectInstance(MobEffects.WEAKNESS, 300, 2));
					FruitControl.apply(target, new MobEffectInstance(MobEffects.SLOWNESS, 300, 1));
				}
				sound(level, player, SoundEvents.WITCH_CELEBRATE);
				return 10;
			}
			case "ito_ito_no_mi" -> { // Puppet strings: hold a target in the air.
				look = MoveFx.STRING;
				LivingEntity target = beam(player, level, 16, ParticleTypes.CRIT);
				if (target != null) {
					FruitControl.apply(target, new MobEffectInstance(MobEffects.LEVITATION, 30, 1));
					FruitControl.apply(target, new MobEffectInstance(MobEffects.SLOWNESS, 100, 3));
					hit(player, target, level, 8);
				}
				sound(level, player, SoundEvents.TRIPWIRE_ATTACH);
				return 5;
			}
			case "mero_mero_no_mi" -> { // A love beam that turns a target to stone.
				look = MoveFx.HEART_ORB;
				LivingEntity target = beam(player, level, 16, ParticleTypes.HEART);
				if (target != null) {
					petrify(target, 80);
					hit(player, target, level, 8);
				}
				sound(level, player, SoundEvents.STONE_PLACE);
				return 6;
			}
			case "nikyu_nikyu_no_mi" -> { // Paw blast that sends a target flying far away.
				look = MoveFx.PAW_ORB;
				LivingEntity target = beam(player, level, 16, ParticleTypes.CLOUD);
				if (target != null) {
					hit(player, target, level, 8);
					push(target, player, 5.0, 1.5);
				}
				sound(level, player, SoundEvents.WIND_CHARGE_BURST.value());
				return 4;
			}
			case "kage_kage_no_mi" -> { // Steal a shadow and get stronger.
				LivingEntity target = beam(player, level, 12, ParticleTypes.SQUID_INK);
				if (target != null) {
					FruitControl.apply(target, new MobEffectInstance(MobEffects.BLINDNESS, 100, 0));
					FruitControl.apply(target, new MobEffectInstance(MobEffects.WEAKNESS, 200, 1));
					player.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 100, 0));
					hit(player, target, level, 4);
				}
				sound(level, player, SoundEvents.WARDEN_SONIC_CHARGE);
				return 8;
			}
			case "zushi_zushi_no_mi" -> { // Crush a target into the ground.
				look = MoveFx.GRAVITY_BLADE;
				LivingEntity target = beam(player, level, 16, ParticleTypes.CLOUD);
				if (target != null) {
					hit(player, target, level, 8);
					target.setDeltaMovement(target.getDeltaMovement().x, -2.0, target.getDeltaMovement().z);
					Motion.sync(target);
					FruitControl.apply(target, new MobEffectInstance(MobEffects.SLOWNESS, 80, 4));
				}
				sound(level, player, SoundEvents.ANVIL_LAND);
				return 4;
			}
			case "mochi_mochi_no_mi" -> { // Sticky mochi glues a target in place.
				LivingEntity target = beam(player, level, 14, ParticleTypes.WHITE_ASH);
				if (target != null) {
					petrify(target, 80);
					hit(player, target, level, 6);
				}
				sound(level, player, SoundEvents.SLIME_SQUISH);
				return 5;
			}
			case "fuku_fuku_no_mi" -> { // Kin'emon's flaming sword slash.
				LivingEntity target = beam(player, level, 7, ParticleTypes.FLAME);
				if (target != null) {
					hit(player, target, level, 9);
					target.igniteForSeconds(6);
				}
				sound(level, player, SoundEvents.PLAYER_ATTACK_SWEEP);
				return 3;
			}
			case "nomi_nomi_no_mi" -> { // Spot every creature around you through walls.
				for (LivingEntity target : nearby(player, level, 32)) {
					FruitControl.apply(target, new MobEffectInstance(MobEffects.GLOWING, 200, 0));
				}
				player.addEffect(fx(MobEffects.STRENGTH, 10, 0)); // You know exactly where their weak spots are.
				sound(level, player, SoundEvents.BEACON_ACTIVATE);
				return 15;
			}
			case "hana_hana_no_mi" -> { // Sprout arms on a target and squeeze.
				LivingEntity target = beam(player, level, 16, ParticleTypes.CRIT);
				if (target != null) {
					petrify(target, 40);
					hit(player, target, level, 9);
				}
				sound(level, player, SoundEvents.PLAYER_ATTACK_KNOCKBACK);
				return 4;
			}
			case "yomi_yomi_no_mi" -> { // The chill of the underworld freezes a target.
				LivingEntity target = beam(player, level, 12, ParticleTypes.SNOWFLAKE);
				if (target != null) {
					freeze(target);
					hit(player, target, level, 6);
				}
				sound(level, player, SoundEvents.GLASS_BREAK);
				return 4;
			}
			case "mera_mera_no_mi" -> { // Hiken: a giant fist of fire.
				look = MoveFx.FIRE_FIST;
				LivingEntity target = beam(player, level, 22, ParticleTypes.FLAME);
				if (target != null) {
					hit(player, target, level, 10);
					target.igniteForSeconds(6);
					push(target, player, 1.5, 0.3);
				}
				sound(level, player, SoundEvents.BLAZE_SHOOT);
				return 4;
			}
			case "hie_hie_no_mi" -> { // A blade of ice that freezes what it hits.
				look = MoveFx.ICE_SPEAR;
				LivingEntity target = beam(player, level, 18, ParticleTypes.SNOWFLAKE);
				if (target != null) {
					freeze(target);
					hit(player, target, level, 7);
				}
				sound(level, player, SoundEvents.GLASS_BREAK);
				return 3;
			}
			case "yami_yami_no_mi" -> { // Kurouzu: drag a target straight to you.
				look = MoveFx.DARK_PULL;
				LivingEntity target = beam(player, level, 20, ParticleTypes.SQUID_INK);
				if (target != null) {
					push(target, player, -2.5, 0.3);
					FruitControl.apply(target, new MobEffectInstance(MobEffects.DARKNESS, 100, 0));
					hit(player, target, level, 6);
				}
				sound(level, player, SoundEvents.WARDEN_SONIC_CHARGE);
				return 4;
			}
			case "suna_suna_no_mi" -> { // A blade of sand that dries out the target.
				look = MoveFx.SAND_BLADE;
				LivingEntity target = beam(player, level, 16, ParticleTypes.WHITE_ASH);
				if (target != null) {
					hit(player, target, level, 6);
					FruitControl.apply(target, new MobEffectInstance(MobEffects.WITHER, 80, 1));
					FruitControl.apply(target, new MobEffectInstance(MobEffects.HUNGER, 200, 2));
				}
				sound(level, player, SoundEvents.SAND_BREAK);
				return 4;
			}
			case "magu_magu_no_mi" -> { // A fist of magma.
				look = MoveFx.MAGMA_FIST;
				LivingEntity target = beam(player, level, 18, ParticleTypes.LAVA);
				if (target != null) {
					hit(player, target, level, 10);
					target.igniteForSeconds(10);
				}
				sound(level, player, SoundEvents.LAVA_POP);
				return 4;
			}
			case "pika_pika_no_mi" -> { // Move at the speed of light.
				particles(level, player, ParticleTypes.END_ROD, 20);
				blink(player, level, 24);
				particles(level, player, ParticleTypes.END_ROD, 20);
				sound(level, player, SoundEvents.ENDERMAN_TELEPORT);
				return 3;
			}
			case "mori_mori_no_mi" -> { // Roots drain a target and heal you.
				LivingEntity target = beam(player, level, 14, ParticleTypes.HAPPY_VILLAGER);
				if (target != null) {
					hit(player, target, level, 6);
					FruitControl.apply(target, new MobEffectInstance(MobEffects.SLOWNESS, 100, 3));
					player.heal(6);
				}
				sound(level, player, SoundEvents.GRASS_BREAK);
				return 5;
			}
			case "moku_moku_no_mi" -> { // A cloud of smoke that blinds and slows.
				look = MoveFx.SMOKE_FIST;
				LivingEntity target = beam(player, level, 16, ParticleTypes.LARGE_SMOKE);
				if (target != null) {
					hit(player, target, level, 5);
					FruitControl.apply(target, new MobEffectInstance(MobEffects.BLINDNESS, 100, 0));
					FruitControl.apply(target, new MobEffectInstance(MobEffects.SLOWNESS, 100, 2));
				}
				sound(level, player, SoundEvents.FIRE_EXTINGUISH);
				return 3;
			}
			case "goro_goro_no_mi" -> { // El Thor: lightning wherever you look.
				Vec3 end = beamEnd(player, level, 32);
				lightning(level, end);
				MoveFx.bolt(level, end, 2.2f);
				return 3;
			}
			case "hito_hito_no_mi" -> { // Rumble Ball: a stronger, tougher form.
				transform(player, level, MobEffects.STRENGTH, 0, MobEffects.SPEED, 0, MobEffects.RESISTANCE, 0);
				ZoanForms.start(player, current, 600); // Really become the animal for 30 seconds.
				return 60;
			}
			case "hito_hito_no_mi_daibutsu" -> { // A giant golden Buddha.
				transform(player, level, MobEffects.STRENGTH, 1, MobEffects.RESISTANCE, 1, MobEffects.SLOWNESS, 0);
				return 60;
			}
			case "uo_uo_no_mi_seiryu" -> { // Become a dragon that floats through the sky.
				transform(player, level, MobEffects.STRENGTH, 1, MobEffects.RESISTANCE, 0, MobEffects.SLOW_FALLING, 0);
				ZoanForms.start(player, current, 600); // Really become the animal for 30 seconds.
				player.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 600, 0));
				player.addEffect(new MobEffectInstance(MobEffects.JUMP_BOOST, 600, 2));
				return 60;
			}
			case "ryu_ryu_no_mi_nidhogg" -> { // Loki's hybrid: a winged dragon-giant crackling with thunder.
				transform(player, level, MobEffects.STRENGTH, 1, MobEffects.RESISTANCE, 1, MobEffects.SLOW_FALLING, 0);
				ZoanForms.start(player, current, 600); // Really become the dragon-man for 30 seconds.
				player.addEffect(new MobEffectInstance(MobEffects.JUMP_BOOST, 600, 1));
				lightning(level, player.position().add(player.getLookAngle().multiply(3, 0, 3)));
				return 60;
			}
			case "ryu_ryu_no_mi_allosaurus" -> {
				transform(player, level, MobEffects.STRENGTH, 1, MobEffects.SPEED, 0, MobEffects.RESISTANCE, 0);
				return 60;
			}
			case "ryu_ryu_no_mi_pteranodon" -> {
				transform(player, level, MobEffects.SPEED, 1, MobEffects.SLOW_FALLING, 0, MobEffects.JUMP_BOOST, 2);
				player.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 600, 0));
				return 60;
			}
			case "neko_neko_no_mi_leopard" -> {
				transform(player, level, MobEffects.SPEED, 1, MobEffects.STRENGTH, 1, MobEffects.JUMP_BOOST, 0);
				ZoanForms.start(player, current, 600); // Really become the animal for 30 seconds.
				return 60;
			}
			case "tori_tori_no_mi_phoenix" -> {
				transform(player, level, MobEffects.REGENERATION, 1, MobEffects.SLOW_FALLING, 0, MobEffects.SPEED, 0);
				ZoanForms.start(player, current, 600); // Really become the animal for 30 seconds.
				player.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 600, 0));
				particles(level, player, ParticleTypes.SOUL_FIRE_FLAME, 40);
				MoveFx.at(level, MoveStyle.PILLAR, player.position(), new Vec3(0, 5, 0), MoveFx.BLUE_FIRE, MoveFx.BLUE_FIRE_OUT, 2.4f, 26, null);
				return 60;
			}
			case "inu_inu_no_mi_okuchi_no_makami" -> {
				transform(player, level, MobEffects.SPEED, 1, MobEffects.STRENGTH, 0, MobEffects.RESISTANCE, 0);
				particles(level, player, ParticleTypes.SNOWFLAKE, 40);
				return 60;
			}
			case "numa_numa_no_mi" -> { return beamAttack(player, level, 16, ParticleTypes.SQUID_INK, 4, SoundEvents.SLIME_SQUISH, 4, target -> { push(target, player, -2.0, 0.2); FruitControl.apply(target, fx(MobEffects.SLOWNESS, 5, 3)); }); }
			case "gasu_gasu_no_mi" -> { return beamAttack(player, level, 16, ParticleTypes.WITCH, 4, SoundEvents.FIRE_EXTINGUISH, 4, target -> FruitControl.apply(target, fx(MobEffects.POISON, 6, 1))); }
			case "yuki_yuki_no_mi" -> { return beamAttack(player, level, 16, ParticleTypes.SNOWFLAKE, 6, SoundEvents.POWDER_SNOW_STEP, 3, FruitAbilities::freeze); }
			case "horo_horo_no_mi" -> { return beamAttack(player, level, 18, ParticleTypes.SOUL, 4, SoundEvents.WARDEN_SONIC_CHARGE, 6, target -> { FruitControl.apply(target, fx(MobEffects.WEAKNESS, 10, 2)); FruitControl.apply(target, fx(MobEffects.SLOWNESS, 10, 1)); FruitControl.apply(target, fx(MobEffects.NAUSEA, 6, 0)); }); }
			case "bisu_bisu_no_mi" -> { return beamAttack(player, level, 6, ParticleTypes.CRIT, 9, SoundEvents.PLAYER_ATTACK_KNOCKBACK, 2, NONE); }
			case "pero_pero_no_mi" -> { return beamAttack(player, level, 16, ParticleTypes.CRIT, 6, SoundEvents.STONE_PLACE, 5, target -> petrify(target, 80)); }
			case "mira_mira_no_mi" -> { // Step out of a mirror and strike, or just slip through one.
				LivingEntity target = beam(player, level, 16, ParticleTypes.END_ROD);
				if (target != null) {
					hit(player, target, level, 8);
				} else {
					blink(player, level, 16);
				}
				sound(level, player, SoundEvents.GLASS_BREAK);
				return 4;
			}
			case "netsu_netsu_no_mi" -> { return beamAttack(player, level, 6, ParticleTypes.FLAME, 9, SoundEvents.BLAZE_SHOOT, 2, target -> target.igniteForSeconds(5)); }
			case "bari_bari_no_mi" -> { return beamAttack(player, level, 6, ParticleTypes.END_ROD, 8, SoundEvents.ANVIL_LAND, 3, target -> push(target, player, 3.0, 0.5)); }
			case "hobi_hobi_no_mi" -> { return beamAttack(player, level, 4, ParticleTypes.HAPPY_VILLAGER, 8, SoundEvents.WITCH_CELEBRATE, 10, target -> { petrify(target, 400); FruitControl.apply(target, fx(MobEffects.WEAKNESS, 20, 4)); FruitControl.apply(target, fx(MobEffects.GLOWING, 20, 0)); }); }
			case "doru_doru_no_mi" -> { return beamAttack(player, level, 14, ParticleTypes.WHITE_ASH, 6, SoundEvents.STONE_PLACE, 5, target -> petrify(target, 80)); }
			case "bomu_bomu_no_mi" -> { return beamAttack(player, level, 18, ParticleTypes.EXPLOSION, 9, SoundEvents.GENERIC_EXPLODE.value(), 3, target -> push(target, player, 1.5, 0.4)); }
			case "kilo_kilo_no_mi" -> { return areaAttack(player, level, 4, ParticleTypes.CLOUD, 11, SoundEvents.ANVIL_LAND, 6, target -> { target.setDeltaMovement(0, -1.5, 0); Motion.sync(target); }); }
			case "supa_supa_no_mi" -> { return beamAttack(player, level, 6, ParticleTypes.SWEEP_ATTACK, 8, SoundEvents.PLAYER_ATTACK_SWEEP, 2, NONE); }
			case "mane_mane_no_mi" -> { return beamAttack(player, level, 5, ParticleTypes.CRIT, 9, SoundEvents.PLAYER_ATTACK_KNOCKBACK, 2, target -> push(target, player, 2.0, 0.4)); }
			case "noro_noro_no_mi" -> { return beamAttack(player, level, 20, ParticleTypes.END_ROD, 6, SoundEvents.BEACON_ACTIVATE, 6, target -> { FruitControl.apply(target, fx(MobEffects.SLOWNESS, 30, 6)); FruitControl.apply(target, fx(MobEffects.MINING_FATIGUE, 30, 2)); }); }
			case "doa_doa_no_mi" -> { MoveFx.door(player, level, 0xFFFFF0D0, 0xFFB07A3A); throughWall(player, level, 8); MoveFx.door(player, level, 0xFFFFF0D0, 0xFFB07A3A); sound(level, player, SoundEvents.WOODEN_DOOR_OPEN); return 3; }
			case "awa_awa_no_mi" -> { return beamAttack(player, level, 14, ParticleTypes.CLOUD, 7, SoundEvents.BUBBLE_COLUMN_UPWARDS_AMBIENT, 4, target -> { FruitControl.apply(target, fx(MobEffects.WEAKNESS, 15, 3)); FruitControl.apply(target, fx(MobEffects.SLOWNESS, 15, 1)); }); }
			case "fuwa_fuwa_no_mi" -> { return beamAttack(player, level, 18, ParticleTypes.CLOUD, 8, SoundEvents.WIND_CHARGE_BURST.value(), 4, target -> FruitControl.apply(target, fx(MobEffects.LEVITATION, 4, 2))); }
			case "ishi_ishi_no_mi" -> { return beamAttack(player, level, 8, ParticleTypes.CLOUD, 10, SoundEvents.STONE_PLACE, 3, target -> push(target, player, 1.5, 0.4)); }
			case "hira_hira_no_mi" -> { return beamAttack(player, level, 8, ParticleTypes.SWEEP_ATTACK, 9, SoundEvents.PLAYER_ATTACK_SWEEP, 2, NONE); }
			case "nagi_nagi_no_mi" -> { return beamAttack(player, level, 6, ParticleTypes.CRIT, 7, SoundEvents.PLAYER_ATTACK_KNOCKBACK, 2, NONE); }
			case "horu_horu_no_mi" -> { return beamAttack(player, level, 16, ParticleTypes.CLOUD, 8, SoundEvents.WIND_CHARGE_BURST.value(), 4, target -> push(target, player, 3.0, 0.6)); }
			case "doku_doku_no_mi" -> { return beamAttack(player, level, 18, ParticleTypes.WITCH, 4, SoundEvents.BREWING_STAND_BREW, 4, target -> FruitControl.apply(target, fx(MobEffects.POISON, 8, 2))); }
			case "bane_bane_no_mi" -> { dash(player, 2.5, 1.0); sound(level, player, SoundEvents.SLIME_JUMP); return beamAttack(player, level, 5, ParticleTypes.CRIT, 8, SoundEvents.SLIME_JUMP, 3, NONE); }
			case "kira_kira_no_mi" -> { return beamAttack(player, level, 6, ParticleTypes.CRIT, 11, SoundEvents.ANVIL_LAND, 3, target -> push(target, player, 2.0, 0.5)); }
			case "woshu_woshu_no_mi" -> { return beamAttack(player, level, 14, ParticleTypes.CLOUD, 7, SoundEvents.BUBBLE_COLUMN_UPWARDS_AMBIENT, 4, target -> { FruitControl.apply(target, fx(MobEffects.WEAKNESS, 15, 3)); FruitControl.apply(target, fx(MobEffects.SLOWNESS, 15, 2)); }); }
			case "oto_oto_no_mi" -> { return beamAttack(player, level, 22, ParticleTypes.NOTE, 7, SoundEvents.NOTE_BLOCK_BASS.value(), 3, NONE); }
			case "shiro_shiro_no_mi" -> { return beamAttack(player, level, 22, ParticleTypes.EXPLOSION, 8, SoundEvents.GENERIC_EXPLODE.value(), 4, NONE); }
			case "baku_baku_no_mi" -> { return beamAttack(player, level, 4, ParticleTypes.CRIT, 8, SoundEvents.GENERIC_EAT.value(), 3, target -> player.heal(4)); }
			case "choki_choki_no_mi" -> { return beamAttack(player, level, 6, ParticleTypes.SWEEP_ATTACK, 10, SoundEvents.SHEEP_SHEAR, 2, NONE); }
			case "fude_fude_no_mi" -> { return beamAttack(player, level, 14, ParticleTypes.SQUID_INK, 6, SoundEvents.SQUID_SQUIRT, 3, target -> FruitControl.apply(target, fx(MobEffects.BLINDNESS, 5, 0))); }
			case "kibi_kibi_no_mi" -> { return beamAttack(player, level, 10, ParticleTypes.HEART, 0, SoundEvents.GENERIC_EAT.value(), 5, target -> befriend(player, target)); }
			case "toki_toki_no_mi" -> { blink(player, level, 20); player.addEffect(fx(MobEffects.INVISIBILITY, 3, 0)); sound(level, player, SoundEvents.ENDERMAN_TELEPORT); return 6; }
			case "memo_memo_no_mi" -> { return beamAttack(player, level, 10, ParticleTypes.ENCHANT, 7, SoundEvents.ILLUSIONER_CAST_SPELL, 5, target -> forgetYou(target)); }
			case "riki_riki_no_mi" -> { return beamAttack(player, level, 5, ParticleTypes.CRIT, 13, SoundEvents.PLAYER_ATTACK_KNOCKBACK, 4, target -> push(target, player, 3.0, 0.6)); }
			case "wapu_wapu_no_mi" -> { teleportToLook(player, level, 32); sound(level, player, SoundEvents.ENDERMAN_TELEPORT); return 4; }
			case "shiku_shiku_no_mi" -> { return beamAttack(player, level, 14, ParticleTypes.WITCH, 7, SoundEvents.WITCH_CELEBRATE, 5, target -> { FruitControl.apply(target, fx(MobEffects.POISON, 8, 0)); FruitControl.apply(target, fx(MobEffects.HUNGER, 15, 2)); FruitControl.apply(target, fx(MobEffects.WEAKNESS, 15, 1)); }); }
			case "beta_beta_no_mi" -> { return beamAttack(player, level, 14, ParticleTypes.ITEM_SLIME, 3, SoundEvents.SLIME_SQUISH, 4, target -> FruitControl.apply(target, fx(MobEffects.SLOWNESS, 8, 5))); }
			case "pamu_pamu_no_mi" -> { return beamAttack(player, level, 14, ParticleTypes.EXPLOSION, 10, SoundEvents.GENERIC_EXPLODE.value(), 4, target -> push(target, player, 2.0, 0.5)); }
			case "sui_sui_no_mi" -> { MoveFx.shockwave(level, player.position(), 2.5, 0xFFE0F4FF, 0xFF5AA0D0); throughWall(player, level, 10); MoveFx.shockwave(level, player.position(), 2.5, 0xFFE0F4FF, 0xFF5AA0D0); sound(level, player, SoundEvents.PLAYER_SPLASH); return 4; }
			case "buki_buki_no_mi" -> { return beamAttack(player, level, 22, ParticleTypes.CRIT, 7, SoundEvents.CROSSBOW_SHOOT, 2, NONE); }
			case "guru_guru_no_mi" -> { return areaAttack(player, level, 4, ParticleTypes.SWEEP_ATTACK, 7, SoundEvents.PLAYER_ATTACK_SWEEP, 4, target -> push(target, player, 2.5, 0.5)); }
			case "modo_modo_no_mi" -> { return beamAttack(player, level, 12, ParticleTypes.END_ROD, 7, SoundEvents.BEACON_ACTIVATE, 5, FruitAbilities::makeYounger); }
			case "sube_sube_no_mi" -> { return beamAttack(player, level, 6, ParticleTypes.CRIT, 7, SoundEvents.PLAYER_ATTACK_KNOCKBACK, 2, NONE); }
			case "ori_ori_no_mi" -> { return beamAttack(player, level, 16, ParticleTypes.CRIT, 7, SoundEvents.CHAIN_PLACE, 5, target -> petrify(target, 100)); }
			case "chiyu_chiyu_no_mi" -> { heal(player, level); return 10; }
			case "nui_nui_no_mi" -> { return beamAttack(player, level, 14, ParticleTypes.CRIT, 7, SoundEvents.TRIPWIRE_ATTACH, 5, target -> petrify(target, 80)); }
			case "ton_ton_no_mi" -> { return areaAttack(player, level, 4, ParticleTypes.CLOUD, 12, SoundEvents.ANVIL_LAND, 8, target -> { target.setDeltaMovement(0, -1.5, 0); Motion.sync(target); }); }
			case "ato_ato_no_mi" -> { return beamAttack(player, level, 14, ParticleTypes.WITCH, 7, SoundEvents.ILLUSIONER_CAST_SPELL, 6, target -> { FruitControl.apply(target, fx(MobEffects.SLOWNESS, 10, 3)); FruitControl.apply(target, fx(MobEffects.MINING_FATIGUE, 10, 2)); FruitControl.apply(target, fx(MobEffects.WEAKNESS, 10, 1)); }); }
			case "sabi_sabi_no_mi" -> { return beamAttack(player, level, 5, ParticleTypes.WHITE_ASH, 8, SoundEvents.GRINDSTONE_USE, 3, target -> FruitControl.apply(target, fx(MobEffects.WEAKNESS, 15, 2))); }
			case "mato_mato_no_mi" -> { homingHit(player, level, 30, 9); return 3; }
			case "mogu_mogu_no_mi" -> { return zoan(player, level, fx(MobEffects.STRENGTH, 30, 0), fx(MobEffects.HASTE, 30, 1), fx(MobEffects.NIGHT_VISION, 30, 0)); }
			case "uma_uma_no_mi" -> { return zoan(player, level, fx(MobEffects.SPEED, 30, 2), fx(MobEffects.JUMP_BOOST, 30, 1), fx(MobEffects.RESISTANCE, 30, 0)); }
			case "sara_sara_no_mi_axolotl" -> { return zoan(player, level, fx(MobEffects.REGENERATION, 30, 1), fx(MobEffects.RESISTANCE, 30, 0), fx(MobEffects.WATER_BREATHING, 30, 0)); }
			case "inu_inu_no_mi_wolf" -> { return zoan(player, level, fx(MobEffects.STRENGTH, 30, 0), fx(MobEffects.SPEED, 30, 1), fx(MobEffects.NIGHT_VISION, 30, 0)); }
			case "inu_inu_no_mi_jackal" -> { return zoan(player, level, fx(MobEffects.STRENGTH, 30, 0), fx(MobEffects.SPEED, 30, 1), fx(MobEffects.JUMP_BOOST, 30, 0)); }
			case "neko_neko_no_mi_saber_tiger" -> { return zoan(player, level, fx(MobEffects.STRENGTH, 30, 1), fx(MobEffects.SPEED, 30, 1), fx(MobEffects.JUMP_BOOST, 30, 0)); }
			case "ryu_ryu_no_mi_pachycephalosaurus" -> { return zoan(player, level, fx(MobEffects.STRENGTH, 30, 1), fx(MobEffects.RESISTANCE, 30, 1), fx(MobEffects.SPEED, 30, 0)); }
			case "ryu_ryu_no_mi_triceratops" -> { return zoan(player, level, fx(MobEffects.STRENGTH, 30, 1), fx(MobEffects.RESISTANCE, 30, 1), fx(MobEffects.SPEED, 30, 0)); }
			case "ryu_ryu_no_mi_spinosaurus" -> { return zoan(player, level, fx(MobEffects.STRENGTH, 30, 1), fx(MobEffects.SPEED, 30, 0), fx(MobEffects.DOLPHINS_GRACE, 30, 0)); }
			case "ryu_ryu_no_mi_brachiosaurus" -> { return zoan(player, level, fx(MobEffects.RESISTANCE, 30, 1), fx(MobEffects.STRENGTH, 30, 1), fx(MobEffects.HEALTH_BOOST, 30, 2)); }
			case "zou_zou_no_mi_mammoth" -> { return zoan(player, level, fx(MobEffects.STRENGTH, 30, 1), fx(MobEffects.RESISTANCE, 30, 1), fx(MobEffects.SLOWNESS, 30, 0)); }
			case "zou_zou_no_mi" -> { return zoan(player, level, fx(MobEffects.STRENGTH, 30, 0), fx(MobEffects.RESISTANCE, 30, 1), fx(MobEffects.HEALTH_BOOST, 30, 1)); }
			case "ushi_ushi_no_mi_giraffe" -> { return zoan(player, level, fx(MobEffects.STRENGTH, 30, 0), fx(MobEffects.SPEED, 30, 0), fx(MobEffects.JUMP_BOOST, 30, 1)); }
			case "ushi_ushi_no_mi_bison" -> { return zoan(player, level, fx(MobEffects.STRENGTH, 30, 1), fx(MobEffects.RESISTANCE, 30, 0), fx(MobEffects.SPEED, 30, 0)); }
			case "tori_tori_no_mi_falcon" -> { return zoan(player, level, fx(MobEffects.SPEED, 30, 1), fx(MobEffects.SLOW_FALLING, 30, 0), fx(MobEffects.JUMP_BOOST, 30, 2), fx(MobEffects.STRENGTH, 30, 0)); }
			case "hebi_hebi_no_mi_anaconda" -> { return zoan(player, level, fx(MobEffects.STRENGTH, 30, 0), fx(MobEffects.RESISTANCE, 30, 0), fx(MobEffects.SPEED, 30, 0)); }
			case "hebi_hebi_no_mi_king_cobra" -> { return zoan(player, level, fx(MobEffects.STRENGTH, 30, 0), fx(MobEffects.SPEED, 30, 1), fx(MobEffects.RESISTANCE, 30, 0)); }
			case "hebi_hebi_no_mi_yamata_no_orochi" -> { return zoan(player, level, fx(MobEffects.STRENGTH, 30, 1), fx(MobEffects.RESISTANCE, 30, 0), fx(MobEffects.HEALTH_BOOST, 30, 2)); }
			case "inu_inu_no_mi_kyubi_no_kitsune" -> { return zoan(player, level, fx(MobEffects.SPEED, 30, 1), fx(MobEffects.STRENGTH, 30, 0), fx(MobEffects.JUMP_BOOST, 30, 1)); }
			case "kumo_kumo_no_mi_rosamygale_grauvogeli" -> { return zoan(player, level, fx(MobEffects.STRENGTH, 30, 0), fx(MobEffects.RESISTANCE, 30, 0), fx(MobEffects.NIGHT_VISION, 30, 0)); }
			default -> {
				return 1;
			}
		}
	}

	/** The Sneak + R move. Returns the cooldown in seconds. */
	private static int secondary(ServerPlayer player, ServerLevel level, String fruit) {
		// In a full Zoan form (leopard, phoenix, dragon, Heavy Point), Sneak + R is the form's signature attack.
		int signature = ZoanForms.signature(player, level);
		if (signature >= 0) {
			return signature;
		}
		switch (fruit) {
			case "gomu_gomu_no_mi" -> { // Launch yourself like a slingshot.
				Vec3 grab = beamEnd(player, level, 10);
				MoveFx.arm(player, level, grab, false);
				MoveFx.arm(player, level, grab, true);
				dash(player, 2.5, 0.8);
				sound(level, player, SoundEvents.WIND_CHARGE_BURST.value());
				return 4;
			}
			case "ope_ope_no_mi" -> { // Operate on yourself: heal and remove all effects.
				MoveFx.room(player, level, 5);
				player.removeAllEffects();
				player.heal(16);
				particles(level, player, ParticleTypes.HAPPY_VILLAGER, 20);
				sound(level, player, SoundEvents.BEACON_ACTIVATE);
				return 45;
			}
			case "bara_bara_no_mi" -> { // Split into pieces and float away.
				player.addEffect(new MobEffectInstance(MobEffects.INVISIBILITY, 160, 0));
				player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 160, 0));
				player.addEffect(new MobEffectInstance(MobEffects.SPEED, 160, 1));
				particles(level, player, ParticleTypes.POOF, 30);
				return 20;
			}
			case "gura_gura_no_mi" -> { // A quake that throws everyone around you away.
				MoveFx.quake(player, level, 10);
				for (LivingEntity target : nearby(player, level, 10)) {
					hit(player, target, level, 10);
					push(target, player, 3.0, 0.8);
				}
				particles(level, player, ParticleTypes.EXPLOSION_EMITTER, 1);
				sound(level, player, SoundEvents.GENERIC_EXPLODE.value());
				return 12;
			}
			case "soru_soru_no_mi", "goro_goro_no_mi" -> { // Lightning on several enemies at once.
				int bolts = 0;
				for (LivingEntity target : nearby(player, level, 14)) {
					if (bolts++ >= 5) {
						break;
					}
					lightning(level, target.position());
				}
				return 15;
			}
			case "jiki_jiki_no_mi" -> { // Pull every dropped item around you to your feet.
				MoveFx.area(player, level, current, ParticleTypes.ELECTRIC_SPARK, 6);
				for (ItemEntity item : level.getEntitiesOfClass(ItemEntity.class, player.getBoundingBox().inflate(20))) {
					item.teleportTo(player.getX(), player.getY(), player.getZ());
				}
				particles(level, player, ParticleTypes.ELECTRIC_SPARK, 30);
				sound(level, player, SoundEvents.ANVIL_LAND);
				return 10;
			}
			case "wara_wara_no_mi" -> { // Straw dolls take your damage for a while.
				MoveFx.aura(player, level, current, ParticleTypes.WHITE_ASH);
				player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 200, 1));
				player.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, 200, 2));
				particles(level, player, ParticleTypes.WHITE_ASH, 30);
				return 30;
			}
			case "toshi_toshi_no_mi" -> { // Age yourself up into a powerful adult form.
				MoveFx.aura(player, level, current, ParticleTypes.HEART);
				player.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 400, 1));
				player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 400, 0));
				particles(level, player, ParticleTypes.HEART, 20);
				return 40;
			}
			case "ito_ito_no_mi" -> { // Ride strings through the air.
				dash(player, 2.0, 0.6);
				player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 160, 0));
				return 5;
			}
			case "mero_mero_no_mi" -> { // Everyone around you is turned to stone.
				MoveFx.area(player, level, current, ParticleTypes.HEART, 7);
				for (LivingEntity target : nearby(player, level, 7)) {
					petrify(target, 100);
				}
				particles(level, player, ParticleTypes.HEART, 40);
				sound(level, player, SoundEvents.STONE_PLACE);
				return 20;
			}
			case "nikyu_nikyu_no_mi" -> { // Send yourself flying across the land.
				dash(player, 4.0, 1.5);
				player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 300, 0));
				sound(level, player, SoundEvents.WIND_CHARGE_BURST.value());
				return 15;
			}
			case "kage_kage_no_mi" -> { // Absorb shadows for huge power.
				MoveFx.aura(player, level, current, ParticleTypes.SQUID_INK);
				player.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 300, 1));
				player.addEffect(new MobEffectInstance(MobEffects.ABSORPTION, 300, 2));
				particles(level, player, ParticleTypes.SQUID_INK, 40);
				return 45;
			}
			case "zushi_zushi_no_mi" -> { // Heavy gravity pins everything nearby.
				MoveFx.at(level, MoveStyle.SPHERE, player.position().add(0, 0.6, 0), Vec3.ZERO, 0xFFC8A0FF, 0xFF3A1470, -9f, 26, null);
				MoveFx.shockwave(level, player.position(), 9, 0xFFC8A0FF, 0xFF3A1470);
				for (LivingEntity target : nearby(player, level, 9)) {
					target.setDeltaMovement(0, -1.5, 0);
					Motion.sync(target);
					FruitControl.apply(target, new MobEffectInstance(MobEffects.SLOWNESS, 120, 4));
					hit(player, target, level, 4);
				}
				particles(level, player, ParticleTypes.CLOUD, 40);
				sound(level, player, SoundEvents.ANVIL_LAND);
				return 15;
			}
			case "mochi_mochi_no_mi", "fuku_fuku_no_mi" -> { // Thick armor (mochi or a fancy outfit).
				MoveFx.aura(player, level, current, ParticleTypes.WHITE_ASH);
				player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 160, 2));
				particles(level, player, ParticleTypes.WHITE_ASH, 30);
				return 25;
			}
			case "nomi_nomi_no_mi" -> { // A huge brain learns fast: 5 free levels.
				player.giveExperienceLevels(5);
				sound(level, player, SoundEvents.PLAYER_LEVELUP);
				return 600;
			}
			case "hana_hana_no_mi" -> { // A thousand arms hold everyone nearby.
				MoveFx.at(level, MoveStyle.SPIKES, player.position(), new Vec3(7, 0, 0), MoveFx.SKIN, 0xFFF0A0C0, 0.6f, 40, null);
				for (LivingEntity target : nearby(player, level, 7)) {
					petrify(target, 60);
					hit(player, target, level, 4);
				}
				particles(level, player, ParticleTypes.CRIT, 40);
				return 15;
			}
			case "yomi_yomi_no_mi" -> { // Leave your body as an invisible soul.
				player.addEffect(new MobEffectInstance(MobEffects.INVISIBILITY, 200, 0));
				player.addEffect(new MobEffectInstance(MobEffects.SPEED, 200, 1));
				return 30;
			}
			case "mera_mera_no_mi" -> { // A ring of fire around you.
				MoveFx.area(player, level, current, ParticleTypes.FLAME, 6);
				for (LivingEntity target : nearby(player, level, 6)) {
					target.igniteForSeconds(8);
					hit(player, target, level, 6);
				}
				particles(level, player, ParticleTypes.FLAME, 80);
				sound(level, player, SoundEvents.BLAZE_SHOOT);
				return 10;
			}
			case "hie_hie_no_mi" -> { // Ice Age: freeze everything nearby, even the sea.
				MoveFx.area(player, level, current, ParticleTypes.SNOWFLAKE, 8);
				for (LivingEntity target : nearby(player, level, 8)) {
					freeze(target);
				}
				freezeWater(level, player, player.blockPosition(), 8, false);
				particles(level, player, ParticleTypes.SNOWFLAKE, 80);
				sound(level, player, SoundEvents.GLASS_BREAK);
				return 15;
			}
			case "yami_yami_no_mi" -> { // Black Hole: pull everything around you in.
				MoveFx.blackHole(player, level, 12);
				for (LivingEntity target : nearby(player, level, 12)) {
					push(target, player, -2.0, 0.2);
					hit(player, target, level, 6);
					FruitControl.apply(target, new MobEffectInstance(MobEffects.DARKNESS, 100, 0));
					FruitControl.apply(target, new MobEffectInstance(MobEffects.WEAKNESS, 100, 1));
				}
				particles(level, player, ParticleTypes.SQUID_INK, 80);
				sound(level, player, SoundEvents.WARDEN_SONIC_CHARGE);
				return 15;
			}
			case "suna_suna_no_mi" -> { // A sandstorm lifts everyone off the ground.
				MoveFx.area(player, level, current, ParticleTypes.WHITE_ASH, 8);
				for (LivingEntity target : nearby(player, level, 8)) {
					FruitControl.apply(target, new MobEffectInstance(MobEffects.LEVITATION, 40, 1));
					FruitControl.apply(target, new MobEffectInstance(MobEffects.BLINDNESS, 80, 0));
					hit(player, target, level, 4);
				}
				particles(level, player, ParticleTypes.WHITE_ASH, 100);
				sound(level, player, SoundEvents.SAND_BREAK);
				return 15;
			}
			case "magu_magu_no_mi" -> { // Meteor Volcano: magma rains on everything nearby.
				MoveFx.meteors(level, player.position(), 10, 6, MoveFx.MAGMA_BALL);
				for (LivingEntity target : nearby(player, level, 10)) {
					MoveFx.meteor(level, target.position(), MoveFx.MAGMA_BALL);
					target.igniteForSeconds(8);
					hit(player, target, level, 6);
				}
				particles(level, player, ParticleTypes.LAVA, 60);
				sound(level, player, SoundEvents.LAVA_POP);
				return 18;
			}
			case "pika_pika_no_mi" -> { // A laser beam.
				look = MoveFx.LASER;
				LivingEntity target = beam(player, level, 32, ParticleTypes.END_ROD);
				if (target != null) {
					hit(player, target, level, 10);
					FruitControl.apply(target, new MobEffectInstance(MobEffects.GLOWING, 100, 0));
				}
				sound(level, player, SoundEvents.BEACON_ACTIVATE);
				return 5;
			}
			case "mori_mori_no_mi" -> { // Make plants and crops around you grow.
				MoveFx.area(player, level, current, ParticleTypes.HAPPY_VILLAGER, 6);
				growPlants(level, player, player.blockPosition(), 6);
				particles(level, player, ParticleTypes.HAPPY_VILLAGER, 60);
				sound(level, player, SoundEvents.BONE_MEAL_USE);
				return 20;
			}
			case "moku_moku_no_mi" -> { // Float up on a cloud of smoke.
				MoveFx.at(level, MoveStyle.TORNADO, player.position(), new Vec3(0, 3, 0), MoveFx.SMOKE, MoveFx.SMOKE_OUT, 1.6f, 40, player);
				player.addEffect(new MobEffectInstance(MobEffects.LEVITATION, 50, 1));
				player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 240, 0));
				particles(level, player, ParticleTypes.LARGE_SMOKE, 40);
				return 12;
			}
			case "hito_hito_no_mi", "tori_tori_no_mi_phoenix" -> { // Heal yourself and friends nearby.
				MoveFx.aura(player, level, current, fruit.equals("hito_hito_no_mi") ? ParticleTypes.HAPPY_VILLAGER : ParticleTypes.SOUL_FIRE_FLAME);
				player.heal(8);
				for (Player friend : level.getEntitiesOfClass(Player.class, player.getBoundingBox().inflate(8))) {
					friend.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 200, 1));
				}
				particles(level, player, fruit.equals("hito_hito_no_mi") ? ParticleTypes.HAPPY_VILLAGER : ParticleTypes.SOUL_FIRE_FLAME, 40);
				return 40;
			}
			case "hito_hito_no_mi_daibutsu" -> { // A shockwave from the Buddha's palm.
				MoveFx.shockwave(level, player.position(), 8, MoveFx.GOLD, MoveFx.GOLD_OUT);
				for (LivingEntity target : nearby(player, level, 8)) {
					hit(player, target, level, 8);
					push(target, player, 2.5, 0.6);
				}
				particles(level, player, ParticleTypes.EXPLOSION, 10);
				sound(level, player, SoundEvents.GENERIC_EXPLODE.value());
				return 12;
			}
			case "ryu_ryu_no_mi_nidhogg" -> { // Dragon Thunder: a crackling bolt that slows whatever it hits.
				look = MoveFx.THUNDER_BREATH;
				LivingEntity target = beam(player, level, 22, ParticleTypes.ELECTRIC_SPARK);
				if (target != null) {
					hit(player, target, level, 12);
					FruitControl.apply(target, fx(MobEffects.SLOWNESS, 2, 1));
					lightning(level, target.position());
				}
				sound(level, player, SoundEvents.TRIDENT_THUNDER.value());
				return 8;
			}
			case "uo_uo_no_mi_seiryu" -> { // Bolo Breath: a blast of dragon fire.
				look = MoveFx.DRAGON_BREATH;
				LivingEntity target = beam(player, level, 24, ParticleTypes.FLAME);
				if (target != null) {
					hit(player, target, level, 14);
					target.igniteForSeconds(8);
					push(target, player, 2.0, 0.5);
				}
				sound(level, player, SoundEvents.BLAZE_SHOOT);
				return 8;
			}
			case "ryu_ryu_no_mi_allosaurus", "neko_neko_no_mi_leopard" -> { // Pounce and bite.
				look = MoveFx.CLAWS;
				dash(player, 1.6, 0.4);
				LivingEntity target = beam(player, level, 5, ParticleTypes.CRIT);
				if (target != null) {
					hit(player, target, level, 10);
				}
				sound(level, player, SoundEvents.RAVAGER_ROAR);
				return 5;
			}
			case "ryu_ryu_no_mi_pteranodon" -> { // Shoot up into the sky and glide.
				dash(player, 1.5, 1.8);
				player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 300, 0));
				sound(level, player, SoundEvents.WIND_CHARGE_BURST.value());
				return 8;
			}
			case "inu_inu_no_mi_okuchi_no_makami" -> { // Freezing breath.
				look = MoveFx.FROST_BREATH;
				LivingEntity target = beam(player, level, 16, ParticleTypes.SNOWFLAKE);
				if (target != null) {
					freeze(target);
					hit(player, target, level, 8);
				}
				sound(level, player, SoundEvents.GLASS_BREAK);
				return 5;
			}
			case "numa_numa_no_mi" -> { return areaAttack(player, level, 7, ParticleTypes.SQUID_INK, 3, SoundEvents.SLIME_SQUISH, 15, target -> petrify(target, 80)); }
			case "gasu_gasu_no_mi" -> { return areaAttack(player, level, 8, ParticleTypes.WITCH, 2, SoundEvents.FIRE_EXTINGUISH, 18, target -> { FruitControl.apply(target, fx(MobEffects.POISON, 10, 1)); FruitControl.apply(target, fx(MobEffects.NAUSEA, 8, 0)); }); }
			case "yuki_yuki_no_mi" -> { return areaAttack(player, level, 8, ParticleTypes.SNOWFLAKE, 3, SoundEvents.POWDER_SNOW_STEP, 15, FruitAbilities::freeze); }
			case "horo_horo_no_mi" -> { return areaAttack(player, level, 6, ParticleTypes.EXPLOSION, 6, SoundEvents.GENERIC_EXPLODE.value(), 12, NONE); }
			case "bisu_bisu_no_mi" -> { return buff(player, level, ParticleTypes.WHITE_ASH, 25, fx(MobEffects.RESISTANCE, 15, 1), fx(MobEffects.ABSORPTION, 15, 1), fx(MobEffects.SATURATION, 1, 2)); }
			case "pero_pero_no_mi" -> { return buff(player, level, ParticleTypes.CRIT, 25, fx(MobEffects.RESISTANCE, 10, 1)); }
			case "mira_mira_no_mi" -> { return buff(player, level, ParticleTypes.END_ROD, 25, fx(MobEffects.INVISIBILITY, 10, 0)); }
			case "netsu_netsu_no_mi" -> { return areaAttack(player, level, 6, ParticleTypes.FLAME, 4, SoundEvents.BLAZE_SHOOT, 10, target -> target.igniteForSeconds(6)); }
			case "bari_bari_no_mi" -> { return buff(player, level, ParticleTypes.END_ROD, 20, fx(MobEffects.RESISTANCE, 5, 3)); }
			case "hobi_hobi_no_mi" -> { return buff(player, level, ParticleTypes.POOF, 30, fx(MobEffects.INVISIBILITY, 15, 0)); }
			case "doru_doru_no_mi" -> { return buff(player, level, ParticleTypes.WHITE_ASH, 25, fx(MobEffects.RESISTANCE, 15, 1), fx(MobEffects.ABSORPTION, 15, 1)); }
			case "bomu_bomu_no_mi" -> { return areaAttack(player, level, 4, ParticleTypes.EXPLOSION_EMITTER, 10, SoundEvents.GENERIC_EXPLODE.value(), 8, target -> push(target, player, 2.0, 0.6)); }
			case "kilo_kilo_no_mi" -> { return buff(player, level, ParticleTypes.CLOUD, 15, fx(MobEffects.SLOW_FALLING, 15, 0), fx(MobEffects.JUMP_BOOST, 15, 2)); }
			case "supa_supa_no_mi" -> { return buff(player, level, ParticleTypes.CRIT, 25, fx(MobEffects.RESISTANCE, 15, 1), fx(MobEffects.STRENGTH, 15, 0)); }
			case "mane_mane_no_mi" -> { return buff(player, level, ParticleTypes.POOF, 25, fx(MobEffects.INVISIBILITY, 15, 0)); }
			case "noro_noro_no_mi" -> { return areaAttack(player, level, 6, ParticleTypes.END_ROD, 0, SoundEvents.BEACON_ACTIVATE, 15, target -> FruitControl.apply(target, fx(MobEffects.SLOWNESS, 10, 4))); }
			case "doa_doa_no_mi" -> { return buff(player, level, ParticleTypes.POOF, 25, fx(MobEffects.INVISIBILITY, 6, 0), fx(MobEffects.RESISTANCE, 6, 3)); }
			case "awa_awa_no_mi" -> { return areaAttack(player, level, 6, ParticleTypes.CLOUD, 0, SoundEvents.BUBBLE_COLUMN_UPWARDS_AMBIENT, 15, target -> FruitControl.apply(target, fx(MobEffects.WEAKNESS, 15, 2))); }
			case "fuwa_fuwa_no_mi" -> { return buff(player, level, ParticleTypes.CLOUD, 15, fx(MobEffects.LEVITATION, 2, 1), fx(MobEffects.SLOW_FALLING, 20, 0)); }
			case "ishi_ishi_no_mi" -> { return buff(player, level, ParticleTypes.CLOUD, 25, fx(MobEffects.RESISTANCE, 10, 2), fx(MobEffects.SLOWNESS, 10, 0)); }
			case "hira_hira_no_mi" -> { return buff(player, level, ParticleTypes.CRIT, 20, fx(MobEffects.RESISTANCE, 10, 1)); }
			case "nagi_nagi_no_mi" -> { return buff(player, level, ParticleTypes.POOF, 30, fx(MobEffects.INVISIBILITY, 20, 0), fx(MobEffects.SPEED, 20, 0)); }
			case "horu_horu_no_mi" -> { player.heal(10); buff(player, level, ParticleTypes.HEART, 0, fx(MobEffects.REGENERATION, 10, 1), fx(MobEffects.STRENGTH, 10, 0)); return 40; }
			case "doku_doku_no_mi" -> { return areaAttack(player, level, 8, ParticleTypes.WITCH, 2, SoundEvents.BREWING_STAND_BREW, 18, target -> { FruitControl.apply(target, fx(MobEffects.POISON, 10, 1)); FruitControl.apply(target, fx(MobEffects.WITHER, 6, 0)); }); }
			case "bane_bane_no_mi" -> { return pounce(player, level, 10, 5); }
			case "kira_kira_no_mi" -> { return buff(player, level, ParticleTypes.END_ROD, 25, fx(MobEffects.RESISTANCE, 10, 2)); }
			case "woshu_woshu_no_mi" -> { return areaAttack(player, level, 6, ParticleTypes.CLOUD, 0, SoundEvents.BUBBLE_COLUMN_UPWARDS_AMBIENT, 15, target -> { FruitControl.apply(target, fx(MobEffects.LEVITATION, 2, 0)); FruitControl.apply(target, fx(MobEffects.WEAKNESS, 10, 1)); }); }
			case "oto_oto_no_mi" -> { return areaAttack(player, level, 8, ParticleTypes.NOTE, 5, SoundEvents.NOTE_BLOCK_BASS.value(), 12, target -> FruitControl.apply(target, fx(MobEffects.NAUSEA, 6, 0))); }
			case "shiro_shiro_no_mi" -> { return buff(player, level, ParticleTypes.EXPLOSION, 30, fx(MobEffects.RESISTANCE, 15, 1), fx(MobEffects.ABSORPTION, 15, 2)); }
			case "baku_baku_no_mi" -> { return buff(player, level, ParticleTypes.HAPPY_VILLAGER, 30, fx(MobEffects.SATURATION, 1, 9), fx(MobEffects.STRENGTH, 10, 0)); }
			case "choki_choki_no_mi" -> { return buff(player, level, ParticleTypes.CRIT, 20, fx(MobEffects.RESISTANCE, 8, 1)); }
			case "fude_fude_no_mi" -> { summonGolem(player, level); return 180; }
			case "kibi_kibi_no_mi" -> { return buff(player, level, ParticleTypes.HEART, 30, fx(MobEffects.SATURATION, 1, 6), fx(MobEffects.REGENERATION, 5, 1)); }
			case "toki_toki_no_mi" -> { return buff(player, level, ParticleTypes.END_ROD, 30, fx(MobEffects.SPEED, 15, 2), fx(MobEffects.HASTE, 15, 1), fx(MobEffects.STRENGTH, 15, 0)); }
			case "memo_memo_no_mi" -> { return buff(player, level, ParticleTypes.ENCHANT, 30, fx(MobEffects.INVISIBILITY, 10, 0)); }
			case "riki_riki_no_mi" -> { return buff(player, level, ParticleTypes.CRIT, 30, fx(MobEffects.STRENGTH, 15, 1)); }
			case "wapu_wapu_no_mi" -> { return beamAttack(player, level, 24, ParticleTypes.PORTAL, 4, SoundEvents.ENDERMAN_TELEPORT, 8, target -> target.teleportTo(target.getX(), target.getY() + 12, target.getZ())); }
			case "shiku_shiku_no_mi" -> { player.removeAllEffects(); player.heal(6); particles(level, player, ParticleTypes.HAPPY_VILLAGER, 20); MoveFx.heal(player, level, 0xFFE8D0FF, 0xFF6A9A40); return 30; }
			case "beta_beta_no_mi" -> { return areaAttack(player, level, 5, ParticleTypes.FLAME, 4, SoundEvents.BLAZE_SHOOT, 12, target -> { FruitControl.apply(target, fx(MobEffects.SLOWNESS, 6, 3)); target.igniteForSeconds(6); }); }
			case "pamu_pamu_no_mi" -> { return areaAttack(player, level, 5, ParticleTypes.EXPLOSION, 9, SoundEvents.GENERIC_EXPLODE.value(), 12, NONE); }
			case "sui_sui_no_mi" -> { player.addEffect(fx(MobEffects.INVISIBILITY, 3, 0)); return pounce(player, level, 9, 6); }
			case "buki_buki_no_mi" -> { return beamAttack(player, level, 26, ParticleTypes.EXPLOSION, 10, SoundEvents.GENERIC_EXPLODE.value(), 8, NONE); }
			case "guru_guru_no_mi" -> { return buff(player, level, ParticleTypes.CLOUD, 15, fx(MobEffects.LEVITATION, 3, 1), fx(MobEffects.SLOW_FALLING, 15, 0)); }
			case "modo_modo_no_mi" -> { player.heal(12); particles(level, player, ParticleTypes.END_ROD, 20); MoveFx.heal(player, level, 0xFFFFF6D0, 0xFFC8A040); return 40; }
			case "sube_sube_no_mi" -> { return buff(player, level, ParticleTypes.CLOUD, 20, fx(MobEffects.SPEED, 15, 1)); }
			case "ori_ori_no_mi" -> { return areaAttack(player, level, 6, ParticleTypes.CRIT, 0, SoundEvents.CHAIN_PLACE, 15, target -> petrify(target, 60)); }
			case "chiyu_chiyu_no_mi" -> { for (Player friend : level.getEntitiesOfClass(Player.class, player.getBoundingBox().inflate(10))) { friend.addEffect(fx(MobEffects.REGENERATION, 10, 2)); } particles(level, player, ParticleTypes.HAPPY_VILLAGER, 40); MoveFx.heal(player, level, 0xFFD8FFC0, 0xFF3CA040); MoveFx.pulse(player, level, ParticleTypes.HAPPY_VILLAGER, 10); return 45; }
			case "nui_nui_no_mi" -> { player.heal(8); particles(level, player, ParticleTypes.HAPPY_VILLAGER, 15); MoveFx.heal(player, level, 0xFFFFE0F0, 0xFFF080B0); return 25; }
			case "ton_ton_no_mi" -> { return buff(player, level, ParticleTypes.CLOUD, 20, fx(MobEffects.RESISTANCE, 10, 2), fx(MobEffects.SLOWNESS, 10, 1)); }
			case "ato_ato_no_mi" -> { return areaAttack(player, level, 6, ParticleTypes.WITCH, 0, SoundEvents.ILLUSIONER_CAST_SPELL, 15, target -> { FruitControl.apply(target, fx(MobEffects.NAUSEA, 8, 0)); FruitControl.apply(target, fx(MobEffects.SLOWNESS, 8, 2)); }); }
			case "sabi_sabi_no_mi" -> { return areaAttack(player, level, 6, ParticleTypes.WHITE_ASH, 0, SoundEvents.GRINDSTONE_USE, 15, target -> { FruitControl.apply(target, fx(MobEffects.WEAKNESS, 10, 1)); FruitControl.apply(target, fx(MobEffects.SLOWNESS, 10, 0)); }); }
			case "mato_mato_no_mi" -> { return areaAttack(player, level, 30, ParticleTypes.END_ROD, 0, SoundEvents.BEACON_ACTIVATE, 20, target -> FruitControl.apply(target, fx(MobEffects.GLOWING, 15, 0))); }
			case "mogu_mogu_no_mi" -> { dig(player, level, 6); sound(level, player, SoundEvents.GRAVEL_BREAK); return 3; }
			case "uma_uma_no_mi" -> { dash(player, 2.5, 0.3); return beamAttack(player, level, 5, ParticleTypes.CRIT, 8, SoundEvents.HORSE_GALLOP, 4, target -> push(target, player, 2.0, 0.4)); }
			case "sara_sara_no_mi_axolotl" -> { return areaAttack(player, level, 8, ParticleTypes.WITCH, 3, SoundEvents.FIRE_EXTINGUISH, 15, target -> FruitControl.apply(target, fx(MobEffects.POISON, 10, 1))); }
			case "inu_inu_no_mi_wolf" -> { return pounce(player, level, 9, 5); }
			case "inu_inu_no_mi_jackal" -> { return pounce(player, level, 9, 5); }
			case "neko_neko_no_mi_saber_tiger" -> { return pounce(player, level, 11, 5); }
			case "ryu_ryu_no_mi_pachycephalosaurus" -> { dash(player, 1.8, 0.2); return beamAttack(player, level, 5, ParticleTypes.EXPLOSION, 12, SoundEvents.ANVIL_LAND, 6, target -> push(target, player, 3.0, 0.6)); }
			case "ryu_ryu_no_mi_triceratops" -> { dash(player, 2.0, 0.2); return beamAttack(player, level, 5, ParticleTypes.CRIT, 11, SoundEvents.RAVAGER_ROAR, 6, target -> push(target, player, 3.0, 0.5)); }
			case "ryu_ryu_no_mi_spinosaurus" -> { return pounce(player, level, 11, 5); }
			case "ryu_ryu_no_mi_brachiosaurus" -> { return areaAttack(player, level, 7, ParticleTypes.EXPLOSION, 9, SoundEvents.ANVIL_LAND, 12, target -> push(target, player, 2.5, 0.6)); }
			case "zou_zou_no_mi_mammoth" -> { dash(player, 1.8, 0.2); return beamAttack(player, level, 5, ParticleTypes.CRIT, 12, SoundEvents.RAVAGER_ROAR, 6, target -> push(target, player, 3.5, 0.7)); }
			case "zou_zou_no_mi" -> { return beamAttack(player, level, 5, ParticleTypes.CRIT, 10, SoundEvents.RAVAGER_ROAR, 5, target -> push(target, player, 2.5, 0.6)); }
			case "ushi_ushi_no_mi_giraffe" -> { return beamAttack(player, level, 6, ParticleTypes.SWEEP_ATTACK, 11, SoundEvents.PLAYER_ATTACK_SWEEP, 5, target -> push(target, player, 2.0, 0.4)); }
			case "ushi_ushi_no_mi_bison" -> { dash(player, 2.0, 0.2); return beamAttack(player, level, 5, ParticleTypes.CRIT, 10, SoundEvents.RAVAGER_ROAR, 5, target -> push(target, player, 3.0, 0.5)); }
			case "tori_tori_no_mi_falcon" -> { dash(player, 1.5, 1.8); player.addEffect(fx(MobEffects.SLOW_FALLING, 15, 0)); sound(level, player, SoundEvents.WIND_CHARGE_BURST.value()); return 8; }
			case "hebi_hebi_no_mi_anaconda" -> { return beamAttack(player, level, 6, ParticleTypes.CRIT, 6, SoundEvents.PLAYER_ATTACK_KNOCKBACK, 6, target -> petrify(target, 60)); }
			case "hebi_hebi_no_mi_king_cobra" -> { return beamAttack(player, level, 6, ParticleTypes.WITCH, 6, SoundEvents.PLAYER_ATTACK_KNOCKBACK, 5, target -> FruitControl.apply(target, fx(MobEffects.POISON, 8, 1))); }
			case "hebi_hebi_no_mi_yamata_no_orochi" -> { return areaAttack(player, level, 6, ParticleTypes.WITCH, 8, SoundEvents.RAVAGER_ROAR, 12, target -> FruitControl.apply(target, fx(MobEffects.POISON, 6, 1))); }
			case "inu_inu_no_mi_kyubi_no_kitsune" -> { return buff(player, level, ParticleTypes.POOF, 30, fx(MobEffects.INVISIBILITY, 20, 0)); }
			case "kumo_kumo_no_mi_rosamygale_grauvogeli" -> { return beamAttack(player, level, 16, ParticleTypes.CRIT, 2, SoundEvents.SPIDER_AMBIENT, 5, target -> web(player, level, target)); }
			default -> {
				return 1;
			}
		}
	}

	// ---------- Shortcuts used by most fruits ----------

	private static final Consumer<LivingEntity> NONE = target -> { };

	/** An effect lasting some seconds. Level 0 is "I", 1 is "II", and so on. */
	static MobEffectInstance fx(Holder<MobEffect> effect, int seconds, int level) {
		return new MobEffectInstance(effect, seconds * 20, level);
	}

	/** Fire a beam, hurt the first creature it hits, then run "extra" on it. Returns the cooldown. */
	private static int beamAttack(ServerPlayer player, ServerLevel level, double range, ParticleOptions particle, float damage,
			SoundEvent sound, int cooldown, Consumer<LivingEntity> extra) {
		LivingEntity target = beam(player, level, range, particle);
		if (target != null) {
			if (damage > 0) {
				hit(player, target, level, damage);
			}
			extra.accept(target);
		}
		sound(level, player, sound);
		return cooldown;
	}

	/** Hurt every creature around you, then run "extra" on each. Returns the cooldown. */
	private static int areaAttack(ServerPlayer player, ServerLevel level, double radius, ParticleOptions particle, float damage,
			SoundEvent sound, int cooldown, Consumer<LivingEntity> extra) {
		for (LivingEntity target : nearby(player, level, radius)) {
			if (damage > 0) {
				hit(player, target, level, damage);
			}
			extra.accept(target);
		}
		particles(level, player, particle, 60);
		MoveFx.area(player, level, current, particle, radius);
		sound(level, player, sound);
		return cooldown;
	}

	/** Give yourself some effects. Returns the cooldown. */
	private static int buff(ServerPlayer player, ServerLevel level, ParticleOptions particle, int cooldown, MobEffectInstance... effects) {
		for (MobEffectInstance effect : effects) {
			player.addEffect(effect);
		}
		particles(level, player, particle, 30);
		MoveFx.aura(player, level, current, particle);
		return cooldown;
	}

	/** Zoan transformation: effects for 30 seconds, then a 60 second cooldown. */
	private static int zoan(ServerPlayer player, ServerLevel level, MobEffectInstance... effects) {
		for (MobEffectInstance effect : effects) {
			player.addEffect(zoanEffect(effect.getEffect(), effect.getDuration(), effect.getAmplifier()));
		}
		particles(level, player, ParticleTypes.EXPLOSION, 30);
		MoveFx.transform(player, level, current);
		sound(level, player, FruitSounds.ZOAN_SHIFT);
		return 60;
	}

	/** Leap forward and bite or claw whatever is in front of you. */
	private static int pounce(ServerPlayer player, ServerLevel level, float damage, int cooldown) {
		dash(player, 1.6, 0.4);
		return beamAttack(player, level, 5, ParticleTypes.CRIT, damage, SoundEvents.RAVAGER_ROAR, cooldown, NONE);
	}

	/** Walk through the first wall in front of you (Doa Doa, Sui Sui). */
	private static void throughWall(ServerPlayer player, ServerLevel level, double range) {
		Vec3 direction = player.getLookAngle().multiply(1, 0, 1).normalize();
		Vec3 lastFree = player.position();
		boolean passedWall = false;

		for (double distance = 0.5; distance <= range; distance += 0.5) {
			Vec3 offset = direction.scale(distance);
			boolean free = level.noCollision(player, player.getBoundingBox().move(offset));
			if (!free) {
				passedWall = true;
			} else if (passedWall) {
				lastFree = player.position().add(offset);
				break;
			} else {
				lastFree = player.position().add(offset);
			}
		}
		player.teleportTo(lastFree.x, lastFree.y, lastFree.z);
	}

	/** Teleport to the spot you are looking at. */
	private static void teleportToLook(ServerPlayer player, ServerLevel level, double range) {
		Vec3 end = beamEnd(player, level, range);
		// Land just short of what you looked at. Looking at the ground used to put your head there and your feet
		// inside it; now you stand on top of it instead, and if there's no room at all you stay put.
		Vec3 feet = end.subtract(player.getLookAngle().scale(0.5)).subtract(0, player.getEyeHeight(), 0);
		if (!level.noCollision(player, player.getBoundingBox().move(feet.subtract(player.position())))) {
			feet = new Vec3(feet.x, end.y, feet.z);
		}
		if (!level.noCollision(player, player.getBoundingBox().move(feet.subtract(player.position())))) {
			return;
		}
		MoveFx.trail(level, player.position(), feet, current);
		player.teleportTo(feet.x, feet.y, feet.z);
		player.fallDistance = 0;
	}

	/** Fude Fude: draw an iron golem that fights for you. */
	private static void summonGolem(ServerPlayer player, ServerLevel level) {
		Entity golem = EntityTypes.IRON_GOLEM.create(level, EntitySpawnReason.MOB_SUMMONED);
		if (golem != null) {
			golem.setPos(player.position().add(player.getLookAngle().multiply(2, 0, 2)));
			level.addFreshEntity(golem);
			particles(level, player, ParticleTypes.SQUID_INK, 40);
		}
	}

	/** Kibi Kibi: tame an animal, or make an angry mob forget about fighting. */
	private static void befriend(ServerPlayer player, LivingEntity target) {
		if (target instanceof TamableAnimal animal && !animal.isTame()) {
			animal.tame(player);
		} else {
			forgetYou(target);
		}
	}

	/** Memo Memo: a mob forgets it was fighting; a player gets confused. */
	private static void forgetYou(LivingEntity target) {
		if (target instanceof Mob mob) {
			mob.setTarget(null);
		}
		FruitControl.apply(target, new MobEffectInstance(MobEffects.NAUSEA, 160, 0));
		FruitControl.apply(target, new MobEffectInstance(MobEffects.SLOWNESS, 100, 1));
	}

	/** Modo Modo: make a mob a baby, or weaken a player. */
	private static void makeYounger(LivingEntity target) {
		if (target instanceof Mob mob && !mob.isBaby() && !FruitControl.isTough(target)) {
			mob.setBaby(true);
		} else {
			FruitControl.apply(target, new MobEffectInstance(MobEffects.WEAKNESS, 300, 2));
		}
	}

	/** Chiyu Chiyu: heal whoever you look at, or yourself. */
	private static void heal(ServerPlayer player, ServerLevel level) {
		LivingEntity target = beam(player, level, 12, ParticleTypes.HEART);
		boolean friend = target instanceof Player || target instanceof TamableAnimal pet && pet.isOwnedBy(player);
		LivingEntity patient = friend ? target : player;
		patient.heal(12);
		particles(level, patient, ParticleTypes.HAPPY_VILLAGER, 20);
		MoveFx.heal(patient, level, 0xFFD8FFC0, 0xFF3CA040);
	}

	/** Mato Mato: hit the closest enemy, even around corners. */
	private static void homingHit(ServerPlayer player, ServerLevel level, double range, float damage) {
		LivingEntity closest = null;
		for (LivingEntity target : nearby(player, level, range)) {
			if (closest == null || player.distanceToSqr(target) < player.distanceToSqr(closest)) {
				closest = target;
			}
		}
		if (closest != null) {
			hit(player, closest, level, damage);
			particles(level, closest, ParticleTypes.CRIT, 20);
			MoveFx.beam(player, level, current, ParticleTypes.CRIT, closest.getBoundingBox().getCenter(), true, null);
		}
		sound(level, player, SoundEvents.CROSSBOW_SHOOT);
	}

	/** Mogu Mogu: dig a 3 by 3 tunnel the way you are looking. Never breaks chests or bedrock. */
	private static void dig(ServerPlayer player, ServerLevel level, int length) {
		Vec3 eye = player.getEyePosition();
		Vec3 direction = player.getLookAngle();
		for (int distance = 1; distance <= length; distance++) {
			BlockPos center = BlockPos.containing(eye.add(direction.scale(distance)));
			for (BlockPos pos : BlockPos.betweenClosed(center.offset(-1, -1, -1), center.offset(1, 1, 1))) {
				BlockState state = level.getBlockState(pos);
				float hardness = state.getDestroySpeed(level, pos);
				if (!state.isAir() && hardness >= 0 && hardness < 50 && level.getBlockEntity(pos) == null && mayChange(player, level, pos)) {
					level.destroyBlock(pos, true, player);
				}
			}
		}
	}

	/** Kumo Kumo: trap a creature in a cobweb. */
	private static void web(ServerPlayer player, ServerLevel level, LivingEntity target) {
		BlockPos pos = target.blockPosition();
		if (level.getBlockState(pos).isAir() && mayChange(player, level, pos)) {
			level.setBlockAndUpdate(pos, Blocks.COBWEB.defaultBlockState());
		}
	}

	// ---------- Helpers used by the moves above ----------

	/**
	 * Sends a beam out from your eyes. Returns the first creature it hits, or null if it hits a wall
	 * or nothing.
	 */
	static LivingEntity beam(ServerPlayer player, ServerLevel level, double range, ParticleOptions particle) {
		Vec3 start = player.getEyePosition();
		Vec3 direction = player.getLookAngle();
		Vec3 end = start.add(direction.scale(range));
		LivingEntity found = null;

		for (double distance = 1.0; distance <= range; distance += 0.5) {
			Vec3 point = start.add(direction.scale(distance));
			level.sendParticles(particle, point.x, point.y, point.z, 1, 0.05, 0.05, 0.05, 0.0);

			if (isSolid(level, point)) {
				end = point;
				break;
			}

			List<LivingEntity> hits = level.getEntitiesOfClass(LivingEntity.class, new AABB(point, point).inflate(0.6),
					entity -> isValidTarget(player, entity));
			if (!hits.isEmpty()) {
				found = hits.get(0);
				end = found.getBoundingBox().getCenter();
				break;
			}
		}

		// Show the move itself: a stretchy arm, a fire fist, an ice spear... (see MoveFx).
		MoveFx.beam(player, level, current, particle, end, found != null, look);
		look = null;
		return found;
	}

	/** Where your line of sight first hits a block (or the end of the range). */
	private static Vec3 beamEnd(ServerPlayer player, ServerLevel level, double range) {
		Vec3 start = player.getEyePosition();
		Vec3 direction = player.getLookAngle();
		Vec3 last = start;

		for (double distance = 1.0; distance <= range; distance += 0.5) {
			Vec3 point = start.add(direction.scale(distance));
			if (isSolid(level, point)) {
				break;
			}
			last = point;
		}
		return last;
	}

	private static boolean isSolid(ServerLevel level, Vec3 point) {
		BlockPos pos = BlockPos.containing(point);
		return !level.getBlockState(pos).getCollisionShape(level, pos).isEmpty();
	}

	/** Creatures around you that your powers are allowed to hit. */
	static List<LivingEntity> nearby(ServerPlayer player, ServerLevel level, double radius) {
		return level.getEntitiesOfClass(LivingEntity.class, player.getBoundingBox().inflate(radius),
				entity -> isValidTarget(player, entity));
	}

	// Don't hit yourself, creative players, or your own pets and crewmates.
	static boolean isValidTarget(ServerPlayer player, LivingEntity entity) {
		if (entity == player || !entity.isAlive()) {
			return false;
		}
		if (entity instanceof Player other && (other.isCreative() || other.isSpectator())) {
			return false;
		}
		if (entity instanceof TamableAnimal pet && pet.isOwnedBy(player)) {
			return false;
		}
		// Your crew, allied crews, hired crewmates and kingdom guards: beams pass them by.
		return !PlayerCrews.friendly(player.level().getServer(), player, entity);
	}

	static void hit(ServerPlayer player, LivingEntity target, ServerLevel level, float damage) {
		if (!hitSomething && current != null) {
			FruitSounds.playHit(target, current); // Once per move, where it lands.
		}
		hitSomething = true;
		target.hurtServer(level, player.damageSources().playerAttack(player), damage * power(player));
	}

	/**
	 * How hard your fruit hits. It grows slowly as you train it, so fruits keep up with the
	 * tougher bosses later on: x1 at 0 mastery, x1.75 at full mastery, x2 once awakened.
	 */
	public static float power(Player player) {
		float trained = Math.min(Awakening.getMastery(player), Awakening.masteryNeeded()) / (float) Math.max(1, Awakening.masteryNeeded());
		return 1.0f + 0.75f * trained + (Awakening.isAwakenedNow(player) ? 0.25f : 0.0f);
	}

	/** Pushes the target away from you. A negative strength pulls it closer instead. */
	static void push(LivingEntity target, ServerPlayer player, double strength, double up) {
		Vec3 away = target.position().subtract(player.position()).normalize().scale(strength);
		target.setDeltaMovement(away.x, up, away.z);
		Motion.sync(target);
	}

	/** Launches you the way you are looking. */
	static void dash(ServerPlayer player, double strength, double up) {
		Vec3 look = player.getLookAngle().scale(strength);
		player.setDeltaMovement(look.x, Math.max(look.y, 0) + up, look.z);
		Motion.sync(player);
		player.fallDistance = 0;
		ServerLevel level = (ServerLevel) player.level();
		MoveFx.at(level, MoveStyle.RING, player.position().add(0, 0.1, 0), new Vec3(2.5, 0, 0), 0xFFFFFFFF, 0xFFD0E0F0, 0.5f, 10, null);
	}

	/** Teleports you forward until just before you would hit a wall. */
	private static void blink(ServerPlayer player, ServerLevel level, double range) {
		Vec3 direction = player.getLookAngle();
		Vec3 best = player.position();

		for (double distance = 0.5; distance <= range; distance += 0.5) {
			Vec3 offset = direction.scale(distance);
			if (!level.noCollision(player, player.getBoundingBox().move(offset))) {
				break;
			}
			best = player.position().add(offset);
		}
		MoveFx.trail(level, player.position(), best, current);
		player.teleportTo(best.x, best.y, best.z);
		player.fallDistance = 0;
	}

	static void freeze(LivingEntity target) {
		target.setTicksFrozen(target.getTicksRequiredToFreeze() + 100);
		FruitControl.apply(target, new MobEffectInstance(MobEffects.SLOWNESS, 100, 3));
	}

	/** Can't move or break blocks for a while. */
	static void petrify(LivingEntity target, int ticks) {
		FruitControl.apply(target, new MobEffectInstance(MobEffects.SLOWNESS, ticks, 9));
		FruitControl.apply(target, new MobEffectInstance(MobEffects.MINING_FATIGUE, ticks, 2));
	}

	/** Zoan transformation: three effects for 30 seconds. */
	private static void transform(ServerPlayer player, ServerLevel level,
			Holder<MobEffect> first, int firstLevel,
			Holder<MobEffect> second, int secondLevel,
			Holder<MobEffect> third, int thirdLevel) {
		player.addEffect(zoanEffect(first, 600, firstLevel));
		player.addEffect(zoanEffect(second, 600, secondLevel));
		player.addEffect(zoanEffect(third, 600, thirdLevel));
		particles(level, player, ParticleTypes.EXPLOSION, 3);
		MoveFx.transform(player, level, current);
		sound(level, player, FruitSounds.ZOAN_SHIFT);
	}

	/**
	 * Zoan forms give at most Strength I. With Strength II on top of your sword, Zoans did about twice
	 * the damage of every other fruit (measured with FruitBench).
	 */
	private static MobEffectInstance zoanEffect(Holder<MobEffect> effect, int ticks, int level) {
		return new MobEffectInstance(effect, ticks, effect.equals(MobEffects.STRENGTH) ? Math.min(level, 0) : level);
	}

	static void lightning(ServerLevel level, Vec3 at) {
		LightningBolt bolt = new LightningBolt(EntityTypes.LIGHTNING_BOLT, level);
		bolt.setPos(at);
		level.addFreshEntity(bolt);
		MoveFx.bolt(level, at, 1.0f);
	}

	/** Turns water around a spot into ice. Frosted ice melts again later, normal ice stays. */
	static void freezeWater(ServerLevel level, Entity user, BlockPos center, int radius, boolean melts) {
		BlockState ice = melts ? Blocks.FROSTED_ICE.defaultBlockState() : Blocks.ICE.defaultBlockState();
		for (BlockPos pos : BlockPos.betweenClosed(center.offset(-radius, -2, -radius), center.offset(radius, 0, radius))) {
			if (level.getBlockState(pos).is(Blocks.WATER) && level.getFluidState(pos).isSource()
					&& level.getBlockState(pos.above()).isAir() && mayChange(user, level, pos)) {
				level.setBlockAndUpdate(pos, ice);
			}
		}
	}

	/**
	 * Whether a power may change this block: not in spawn protection or adventure mode, the same rules
	 * as placing a block by hand. Null user = a harmless passive effect, always allowed.
	 */
	static boolean mayChange(Entity user, ServerLevel level, BlockPos pos) {
		return !(user instanceof Player player) || (player.mayBuild() && level.mayInteract(player, pos));
	}

	/** Like using bone meal on every plant nearby. */
	private static void growPlants(ServerLevel level, Entity user, BlockPos center, int radius) {
		for (BlockPos pos : BlockPos.betweenClosed(center.offset(-radius, -2, -radius), center.offset(radius, 2, radius))) {
			BlockState state = level.getBlockState(pos);
			if (state.getBlock() instanceof BonemealableBlock plant && plant.isValidBonemealTarget(level, pos, state, BonemealSource.INTERACTION)
					&& !state.is(Blocks.GRASS_BLOCK) && mayChange(user, level, pos)) {
				plant.performBonemeal(level, level.getRandom(), pos.immutable(), state, BonemealSource.INTERACTION);
			}
		}
	}

	static void particles(ServerLevel level, LivingEntity at, ParticleOptions particle, int count) {
		level.sendParticles(particle, at.getX(), at.getY() + at.getBbHeight() / 2, at.getZ(), count, 0.8, 0.8, 0.8, 0.05);
	}

	static void sound(ServerLevel level, LivingEntity at, SoundEvent sound) {
		if (quietVanilla && at instanceof ServerPlayer && sound.location().getNamespace().equals("minecraft")) {
			return;
		}
		level.playSound(null, at.getX(), at.getY(), at.getZ(), sound, SoundSource.PLAYERS, 1.0f, 1.0f);
	}

	/** Seconds until the R move (or the Sneak + R move) is ready again, 0 if ready. The HUD shows this. */
	public static int secondsLeft(ServerPlayer player, boolean secondary) {
		long ticks = readyAt(player, secondary ? 1 : 0) - player.level().getGameTime();
		return ticks <= 0 ? 0 : (int) ((ticks + 19) / 20);
	}

	/** Makes both moves ready right away (the FruitBench test uses this between fruits). */
	public static void resetCooldowns(Player player) {
		player.removeAttached(ModAttachments.FRUIT_COOLDOWNS);
	}

	// The game tick when a move is ready again: slot 0 = R, slot 1 = Sneak + R.
	private static long readyAt(Player player, int slot) {
		List<Long> readyAt = player.getAttachedOrElse(ModAttachments.FRUIT_COOLDOWNS, List.of());
		return slot < readyAt.size() ? readyAt.get(slot) : 0L;
	}

	private static void setReadyAt(Player player, int slot, long tick) {
		List<Long> readyAt = new ArrayList<>(player.getAttachedOrElse(ModAttachments.FRUIT_COOLDOWNS, List.of()));
		while (readyAt.size() < 2) {
			readyAt.add(0L);
		}
		readyAt.set(slot, tick);
		player.setAttached(ModAttachments.FRUIT_COOLDOWNS, List.copyOf(readyAt));
	}
}
