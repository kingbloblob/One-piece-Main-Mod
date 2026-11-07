package com.onepiecemod.style;

import com.onepiecemod.progression.CombatPaths;

import com.onepiecemod.util.Motion;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.core.registries.Registries;
import net.minecraft.tags.ItemTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.haki.HakiPowers;
import com.onepiecemod.multiplayer.PlayerCrews;

/**
 * What every technique does when you press Z, plus Shift+Z (pick the next move) and air jumps.
 * Each move is one "case" below. The numbers are damage in half-hearts (2 = one heart).
 */
public class StyleMoves {
	/** Air jumps per style before you have to land. Geppo (Rokushiki) can kick the air more than Sky Walk. */
	/**
	 * Gloves other mods add to #onepiece:fist_weapons, like One Piece Arsenal's Fishman Gloves. Fist styles (Fish-Man
	 * Karate, Ryusoken, Fist of Love) work with them as if the hand were empty. Black Leg still needs an empty hand.
	 */
	public static final TagKey<Item> FIST_WEAPONS = TagKey.create(Registries.ITEM, OnePieceMod.id("fist_weapons"));

	public static final int GEPPO_JUMPS = 5;
	public static final int SKY_WALK_JUMPS = 3;

	// ---- The keys ----

	public static void handle(ServerPlayer player, int action) {
		switch (action) {
			case StylePayload.USE -> use(player);
			case StylePayload.NEXT -> next(player);
			case StylePayload.AIR_JUMP -> airJump(player);
			default -> { }
		}
	}

	private static void next(ServerPlayer player) {
		FightingStyle style = StyleAttachments.active(player);
		if (style == null) {
			actionBar(player, Component.literal("You don't know a fighting style yet. Type /style to see how to learn one.").withStyle(ChatFormatting.RED));
			return;
		}
		List<Technique> moves = style.unlockedTechniques(player);
		int index = (player.getAttachedOrElse(StyleAttachments.SELECTED_TECHNIQUE, 0) + 1) % moves.size();
		player.setAttached(StyleAttachments.SELECTED_TECHNIQUE, index);
		actionBar(player, Component.literal(style.title() + ": " + moves.get(index).title()).withStyle(ChatFormatting.GOLD));
	}

	/** The move Z will use right now. */
	public static Technique selected(Player player) {
		FightingStyle style = StyleAttachments.active(player);
		if (style == null) {
			return null;
		}
		List<Technique> moves = style.unlockedTechniques(player);
		int index = player.getAttachedOrElse(StyleAttachments.SELECTED_TECHNIQUE, 0);
		return moves.get(Math.floorMod(index, moves.size()));
	}

	private static void use(ServerPlayer player) {
		Technique technique = selected(player);
		if (technique == null) {
			actionBar(player, Component.literal("You don't know a fighting style yet. Type /style to see how to learn one.").withStyle(ChatFormatting.RED));
			return;
		}
		if (player.isSpectator() || !player.isAlive()) {
			return;
		}

		String problem = whyNot(player, technique.style());
		if (problem != null) {
			actionBar(player, Component.literal(problem).withStyle(ChatFormatting.RED));
			return;
		}

		ServerLevel level = (ServerLevel) player.level();
		long now = level.getGameTime();
		StyleState state = StyleState.of(player);
		int wait = state.secondsLeft(technique, now);
		if (wait > 0) {
			actionBar(player, Component.literal(technique.title() + " is ready in " + wait + "s").withStyle(ChatFormatting.GRAY));
			return;
		}
		if (!player.isCreative() && player.getFoodData().getFoodLevel() <= 2) {
			actionBar(player, Component.literal("You're too hungry to fight like that. Eat something!").withStyle(ChatFormatting.RED));
			return;
		}

		state.startCooldown(player, technique, now + StyleMastery.cooldownTicks(player, technique));
		player.causeFoodExhaustion(technique.hunger() * 4.0f); // 4 exhaustion = 1 hunger point.
		actionBar(player, Component.literal(technique.title() + "!").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
		hitSomething = false;
		perform(technique, player, level, state, now);
		afterTechnique(player, technique, state, now);
		StyleMastery.add(player, technique.style(), hitSomething ? 2 : 1);
	}

	/** Style paths that trigger after a technique: Momentum (tier 2 B) and Iron Will (tier 3 A). */
	private static void afterTechnique(ServerPlayer player, Technique technique, StyleState state, long now) {
		FightingStyle style = technique.style();
		if (hitSomething && CombatPaths.has(player, style, 2, "b")) {
			state.startCooldown(player, technique, now + StyleMastery.cooldownTicks(player, technique) * 2L / 3);
		}
		if (CombatPaths.has(player, style, 3, "a")) {
			player.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.RESISTANCE, 80, 0, false, true));
		}
	}

	/** Set by hit() while a technique runs, so landing a move gives more mastery than missing. */
	private static boolean hitSomething;

	/** True if this main hand item is free for a fist style: empty, or gloves in #onepiece:fist_weapons. */
	public static boolean fistsFree(ItemStack hand) {
		return hand.isEmpty() || hand.is(FIST_WEAPONS);
	}

	/** What the player must be holding to use their style, or null if they're fine. */
	public static String whyNot(Player player, FightingStyle style) {
		return switch (style) {
			case SANTORYU -> !player.getMainHandItem().is(ItemTags.SWORDS) ? "Hold a sword to use Three Sword Style."
					: StyleMasters.countSwords(player.getInventory()) < 3 ? "Three Sword Style needs three swords (hotbar or off hand)."
					: null;
			case NITORYU -> !player.getMainHandItem().is(ItemTags.SWORDS) || !player.getOffhandItem().is(ItemTags.SWORDS)
					? "Two Sword Style needs a sword in your main hand and one in your off hand." : null;
			case KITSUNEBI, SOUL_FENCING -> !player.getMainHandItem().is(ItemTags.SWORDS) ? "Hold a sword to use " + style.title() + "." : null;
			case BLACK_LEG -> !player.getMainHandItem().isEmpty() ? "Empty your main hand to use " + style.title() + "." : null;
			case FISHMAN_KARATE, RYUSOKEN, FIST_OF_LOVE -> !fistsFree(player.getMainHandItem())
					? "Empty your main hand (or wear fighting gloves) to use " + style.title() + "." : null;
			case SOGEKING -> !player.getMainHandItem().is(Items.BOW) && !player.getMainHandItem().is(Items.CROSSBOW)
					? "Hold a bow or crossbow to use Sogeking Sniping." : null;
			case ROKUSHIKI -> null;
		};
	}

	// ---- The techniques ----

	private static void perform(Technique technique, ServerPlayer player, ServerLevel level, StyleState state, long now) {
		com.onepiecemod.anim.CombatAnims.technique(player, technique);
		com.onepiecemod.sound.StyleSounds.play(technique, player, level); // The technique's own sound (sound/StyleSounds).
		Vec3 look = player.getLookAngle();
		Vec3 flatLook = new Vec3(look.x, 0, look.z).normalize();

		switch (technique) {
			// Santoryu
			case ONI_GIRI -> { // Dash 7 blocks and cut everyone in the way.
				for (LivingEntity target : inLine(player, level, 7.0, 1.2, 10)) {
					hit(player, level, target, 9.0f);
				}
				launch(player, flatLook.scale(2.2), 0.1);
				effect(level, player, ParticleTypes.SWEEP_ATTACK, 6, null);
			}
			case TATSUMAKI -> { // A tornado: everyone within 5 blocks is cut and thrown up.
				for (LivingEntity target : around(player, level, 5.0)) {
					hit(player, level, target, 8.0f);
					target.setDeltaMovement(target.getDeltaMovement().x * 0.3, 1.3, target.getDeltaMovement().z * 0.3);
					Motion.sync(target);
				}
				effect(level, player, ParticleTypes.SWEEP_ATTACK, 24, null);
				effect(level, player, ParticleTypes.CLOUD, 40, null);
			}
			case POUND_HO -> { // 108 Pound Cannon: a flying slash in a line.
				for (LivingEntity target : inLine(player, level, 20.0, 1.0, 10)) {
					hit(player, level, target, 10.0f);
				}
				trail(player, level, 20.0, ParticleTypes.SWEEP_ATTACK);
				sound(level, player, null);
			}
			case ASURA -> { // Nine swords: Strength II, extra cuts on every hit (see StylePassives).
				state.activeUntil.put(technique, now + 300);
				player.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 300, 1));
				effect(level, player, ParticleTypes.SMOKE, 60, null);
			}

			// Black Leg
			case CONCASSE -> { // Leap up; the landing kick happens in StylePassives when you hit the ground.
				state.concasseStart = now;
				launch(player, flatLook.scale(0.6), 1.1);
				sound(level, player, null);
			}
			case PARTY_TABLE -> { // Spinning handstand kick: everyone close gets kicked away.
				for (LivingEntity target : around(player, level, 3.5)) {
					hit(player, level, target, 7.0f);
					pushAway(target, player, 2.0, 0.5);
				}
				effect(level, player, ParticleTypes.CRIT, 30, null);
			}
			case DIABLE_JAMBE, IFRIT_JAMBE -> { // A burning leg for 15 seconds (the bonus damage is in StylePassives).
				state.activeUntil.put(technique, now + 300);
				player.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 300, 0));
				if (technique == Technique.IFRIT_JAMBE) {
					player.addEffect(new MobEffectInstance(MobEffects.SPEED, 300, 1));
				}
				effect(level, player, technique == Technique.IFRIT_JAMBE ? ParticleTypes.SOUL_FIRE_FLAME : ParticleTypes.FLAME, 40,
						null);
			}

			// Fish-Man Karate
			case THOUSAND_BRICK -> { // The shock goes through armor, so we use magic damage, which armor doesn't block.
				for (LivingEntity target : inLine(player, level, 4.0, 0.6, 1)) {
					target.hurtServer(level, player.damageSources().indirectMagic(player, player), armament(player, 14.0f));
					pushAway(target, player, 2.5, 0.4);
					effect(level, target, ParticleTypes.SPLASH, 40, null);
				}
			}
			case UCHIMIZU -> { // Water drops like bullets, at up to 5 enemies in front of you.
				boolean wet = player.isInWater() || level.isRainingAt(player.blockPosition());
				for (LivingEntity target : inCone(player, level, 12.0, 0.85, 5)) {
					hit(player, level, target, wet ? 10.0f : 5.0f);
					level.sendParticles(ParticleTypes.SPLASH, target.getX(), target.getY() + 1, target.getZ(), 20, 0.3, 0.3, 0.3, 0.1);
				}
				trail(player, level, 12.0, ParticleTypes.FALLING_WATER);
				sound(level, player, null);
			}
			case SAMEHADA -> { // 8 seconds of Resistance; hitting you back hurts (see StylePassives).
				state.activeUntil.put(technique, now + 160);
				player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 160, 1));
				effect(level, player, ParticleTypes.BUBBLE_POP, 40, null);
			}
			case BURAIKAN -> { // A huge wave: everyone in front is smashed and thrown.
				for (LivingEntity target : inCone(player, level, 8.0, 0.6, 20)) {
					hit(player, level, target, 16.0f);
					pushAway(target, player, 3.0, 0.7);
					level.sendParticles(ParticleTypes.SPLASH, target.getX(), target.getY() + 1, target.getZ(), 40, 0.5, 0.5, 0.5, 0.2);
				}
				trail(player, level, 8.0, ParticleTypes.BUBBLE);
				effect(level, player, ParticleTypes.SPLASH, 80, null);
			}

			// Rokushiki
			case SORU -> { // A burst of speed. Falling afterwards doesn't hurt.
				effect(level, player, ParticleTypes.CLOUD, 15, null);
				launch(player, flatLook.scale(2.6), 0.15);
				player.resetFallDistance();
			}
			case SHIGAN -> { // A finger like a bullet.
				for (LivingEntity target : inLine(player, level, 4.0, 0.6, 1)) {
					hit(player, level, target, 12.0f);
					effect(level, target, ParticleTypes.DAMAGE_INDICATOR, 10, null);
				}
			}
			case RANKYAKU -> { // A blade of air kicked in a line.
				for (LivingEntity target : inLine(player, level, 20.0, 1.0, 10)) {
					hit(player, level, target, 10.0f);
				}
				trail(player, level, 20.0, ParticleTypes.SWEEP_ATTACK);
				sound(level, player, null);
			}
			case TEKKAI -> { // Iron body: almost no damage, almost no movement.
				state.activeUntil.put(technique, now + 100);
				player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 100, 3));
				player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 100, 5));
				effect(level, player, ParticleTypes.WAX_ON, 30, null);
			}
			case ROKUOGAN -> { // A shock wave from both fists.
				for (LivingEntity target : inCone(player, level, 6.0, 0.6, 20)) {
					hit(player, level, target, 22.0f);
					pushAway(target, player, 2.5, 0.5);
				}
				Vec3 front = player.getEyePosition().add(look.scale(2));
				level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, front.x, front.y, front.z, 1, 0, 0, 0, 0);
				sound(level, player, null);
			}

			// Ryusoken
			case RYU_NO_KAGIZUME -> { // Grab and crush: the target can hardly move afterwards.
				for (LivingEntity target : inLine(player, level, 4.0, 0.6, 1)) {
					hit(player, level, target, 11.0f);
					target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 4));
					effect(level, target, ParticleTypes.CRIT, 20, null);
				}
			}
			case RYU_NO_IBUKI -> { // Crush the ground around you.
				for (LivingEntity target : around(player, level, 4.5)) {
					hit(player, level, target, 9.0f);
					target.setDeltaMovement(target.getDeltaMovement().x, 0.7, target.getDeltaMovement().z);
					Motion.sync(target);
				}
				effect(level, player, ParticleTypes.EXPLOSION, 6, null);
			}
			case HIKEN -> { // Fire Fist: a line of fire.
				for (LivingEntity target : inLine(player, level, 20.0, 1.2, 10)) {
					hit(player, level, target, 14.0f);
					target.igniteForSeconds(8);
				}
				trail(player, level, 20.0, ParticleTypes.FLAME);
				sound(level, player, null);
			}

			// Oden Nitoryu
			case PARADISE_TOTSUKA -> { // A wide cross slash.
				for (LivingEntity target : inCone(player, level, 5.0, 0.5, 10)) {
					hit(player, level, target, 10.0f);
				}
				effect(level, player, ParticleTypes.SWEEP_ATTACK, 12, null);
			}
			case TOGEN_TOTSUKA -> { // One huge strike.
				for (LivingEntity target : inLine(player, level, 5.0, 0.8, 1)) {
					hit(player, level, target, 18.0f);
					pushAway(target, player, 1.5, 0.3);
					effect(level, target, ParticleTypes.CRIT, 30, null);
				}
			}
			case BOILING_WILL -> {
				player.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 200, 1));
				player.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 200, 1));
				player.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 200, 0));
				effect(level, player, ParticleTypes.BUBBLE_POP, 40, null);
			}
			case ODENS_SCAR -> {
				for (LivingEntity target : inLine(player, level, 6.0, 0.8, 1)) {
					hit(player, level, target, 30.0f);
					target.addEffect(new MobEffectInstance(MobEffects.WITHER, 100, 1));
					pushAway(target, player, 2.0, 0.4);
				}
				trail(player, level, 6.0, ParticleTypes.SWEEP_ATTACK);
				sound(level, player, null);
			}

			// Kitsunebi-ryu
			case HOMURA_GIRI -> { // A flaming slash.
				for (LivingEntity target : inLine(player, level, 10.0, 1.0, 10)) {
					hit(player, level, target, 9.0f);
					target.igniteForSeconds(5);
				}
				trail(player, level, 10.0, ParticleTypes.FLAME);
				sound(level, player, null);
			}
			case CUT_THE_FLAMES -> { // Cut every fire nearby, including the one on you.
				player.clearFire();
				BlockPos center = player.blockPosition();
				for (BlockPos pos : BlockPos.betweenClosed(center.offset(-5, -2, -5), center.offset(5, 3, 5))) {
					if (level.getBlockState(pos).is(BlockTags.FIRE)) {
						level.removeBlock(pos, false);
						level.sendParticles(ParticleTypes.SMOKE, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 4, 0.2, 0.2, 0.2, 0.01);
					}
				}
				player.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 200, 0));
				effect(level, player, ParticleTypes.SWEEP_ATTACK, 8, null);
			}
			case KITSUNEBI_BLADE -> { // A burning blade (the fire and bonus damage are in StylePassives).
				state.activeUntil.put(technique, now + 300);
				effect(level, player, ParticleTypes.FLAME, 30, null);
			}

			// Soul King Fencing
			case YAHAZU_GIRI -> { // Walk past them... and they're cut a moment later (see StylePassives).
				for (LivingEntity target : inLine(player, level, 6.0, 1.2, 10)) {
					state.delayedCuts.add(new StyleState.DelayedCut(target, now + 40, 12.0f));
				}
				launch(player, flatLook.scale(1.8), 0.1);
				effect(level, player, ParticleTypes.NOTE, 6, null);
			}
			case GAVOTTE -> { // A long lunge.
				for (LivingEntity target : inLine(player, level, 8.0, 0.6, 1)) {
					hit(player, level, target, 9.0f);
					effect(level, target, ParticleTypes.CRIT, 15, null);
				}
				launch(player, flatLook.scale(1.0), 0.05);
			}
			case SOUL_SOLID -> { // A frozen blade for 10 seconds (see StylePassives).
				state.activeUntil.put(technique, now + 200);
				effect(level, player, ParticleTypes.SNOWFLAKE, 40, null);
			}
			case LULLABY -> { // A song so sad the enemies can't fight.
				for (LivingEntity target : around(player, level, 8.0)) {
					target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 120, 5));
					target.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 120, 0));
					target.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 120, 0));
					target.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 120, 1));
				}
				effect(level, player, ParticleTypes.NOTE, 30, null);
			}

			// Fist of Love
			case FIST_OF_LOVE_PUNCH -> {
				for (LivingEntity target : inLine(player, level, 4.0, 0.7, 1)) {
					hit(player, level, target, 14.0f);
					pushAway(target, player, 3.5, 0.8);
					effect(level, target, ParticleTypes.HEART, 5, null);
				}
			}
			case CANNONBALL -> { // Cannonballs thrown by hand at up to 5 enemies.
				for (LivingEntity target : inCone(player, level, 16.0, 0.5, 5)) {
					hit(player, level, target, 8.0f);
					level.sendParticles(ParticleTypes.EXPLOSION, target.getX(), target.getY() + 1, target.getZ(), 1, 0, 0, 0, 0);
					sound(level, target, com.onepiecemod.sound.BossSounds.STRIKE_LAND);
				}
			}
			case GALAXY_IMPACT -> { // A blast around you. It doesn't break blocks.
				for (LivingEntity target : around(player, level, 8.0)) {
					hit(player, level, target, 25.0f);
					pushAway(target, player, 3.0, 1.0);
				}
				level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, player.getX(), player.getY() + 1, player.getZ(), 3, 2, 1, 2, 0);
				sound(level, player, null);
			}

			// Sogeking Sniping
			case LEAD_STAR -> {
				for (LivingEntity target : inLine(player, level, 40.0, 0.5, 1)) {
					hit(player, level, target, 8.0f);
				}
				trail(player, level, 40.0, ParticleTypes.CRIT);
				sound(level, player, null);
			}
			case KAEN_BOSHI -> {
				for (LivingEntity target : inLine(player, level, 30.0, 0.5, 1)) {
					hit(player, level, target, 8.0f);
					target.igniteForSeconds(6);
				}
				trail(player, level, 30.0, ParticleTypes.FLAME);
				sound(level, player, null);
			}
			case POP_GREEN -> { // The seed bursts where it lands: on the first enemy or block you're aiming at.
				Vec3 landing = aimPoint(player, level, 24.0);
				for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, new AABB(landing, landing).inflate(4.0),
						entity -> isEnemy(player, entity))) {
					target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 100, 3));
					target.addEffect(new MobEffectInstance(MobEffects.POISON, 100, 0));
				}
				level.sendParticles(ParticleTypes.HAPPY_VILLAGER, landing.x, landing.y, landing.z, 60, 2.0, 0.8, 2.0, 0.1);
				level.playSound(null, landing.x, landing.y, landing.z, com.onepiecemod.sound.ModSounds.MOVE_PLANT, SoundSource.PLAYERS, 1.0f, 1.0f);
			}
			case FIREBIRD_STAR -> {
				for (LivingEntity target : inLine(player, level, 30.0, 1.5, 10)) {
					hit(player, level, target, 16.0f);
					target.igniteForSeconds(10);
				}
				trail(player, level, 30.0, ParticleTypes.FLAME);
				trail(player, level, 30.0, ParticleTypes.LAVA);
				sound(level, player, null);
			}
		}
	}

	/** Where your aim lands: the first enemy or solid block you're looking at, or the point at the end of the range. */
	private static Vec3 aimPoint(Player player, ServerLevel level, double range) {
		Vec3 step = player.getLookAngle().scale(0.5);
		Vec3 point = player.getEyePosition();
		for (double travelled = 0; travelled < range; travelled += 0.5) {
			Vec3 next = point.add(step);
			BlockPos pos = BlockPos.containing(next);
			if (!level.getBlockState(pos).getCollisionShape(level, pos).isEmpty()
					|| !level.getEntitiesOfClass(LivingEntity.class, new AABB(next, next).inflate(0.5), entity -> isEnemy(player, entity)).isEmpty()) {
				return point;
			}
			point = next;
		}
		return point;
	}

	// ---- Geppo and Sky Walk: jumping off the air ----

	private static void airJump(ServerPlayer player) {
		FightingStyle style = StyleAttachments.active(player);
		int maxJumps = style == FightingStyle.ROKUSHIKI ? GEPPO_JUMPS : style == FightingStyle.BLACK_LEG ? SKY_WALK_JUMPS : 0;
		StyleState state = StyleState.of(player);
		if (maxJumps == 0 || player.onGround() || player.isInWater() || player.isPassenger()
				|| player.getAbilities().flying || state.airJumps >= maxJumps) {
			return;
		}
		if (style == FightingStyle.BLACK_LEG && !player.getMainHandItem().isEmpty()) {
			return;
		}
		state.airJumps++;
		Vec3 motion = player.getDeltaMovement();
		player.setDeltaMovement(motion.x, 0.65, motion.z);
		Motion.sync(player);
		player.resetFallDistance();
		player.causeFoodExhaustion(0.4f);
		ServerLevel level = (ServerLevel) player.level();
		level.sendParticles(ParticleTypes.CLOUD, player.getX(), player.getY(), player.getZ(), 6, 0.2, 0.05, 0.2, 0.02);
		level.playSound(null, player.getX(), player.getY(), player.getZ(), com.onepiecemod.sound.StyleSounds.GEPPO, SoundSource.PLAYERS, 0.8f, 1.0f);
	}

	// ---- Helpers ----

	/** Should this technique hurt that entity? Monsters, bosses and anything fighting you: yes. Crewmates, friendly characters and animals: no. */
	public static boolean isEnemy(Player player, LivingEntity entity) {
		if (entity == player || !entity.isAlive() || CrewmateEntity.sameCrew(player, entity)) {
			return false;
		}
		// Your player crew, allied crews and kingdom guards are safe too (same rule as Devil Fruit moves).
		if (player.level().getServer() != null && PlayerCrews.friendly(player.level().getServer(), player, entity)) {
			return false;
		}
		if (entity instanceof TamableAnimal pet && pet.isOwnedBy(player)) {
			return false;
		}
		if (entity instanceof CharacterEntity character) {
			return character.isBoss();
		}
		if (entity instanceof Player other) {
			return !other.isCreative() && !other.isSpectator();
		}
		return entity instanceof Enemy
				|| (entity instanceof Mob mob && mob.getTarget() == player)
				|| entity == player.getLastHurtMob();
	}

	/** Damage from a technique. Armament Haki makes it 25% stronger, and style mastery up to 50% stronger. */
	public static void hit(ServerPlayer player, ServerLevel level, LivingEntity target, float damage) {
		DamageSource source = player.damageSources().playerAttack(player);
		FightingStyle style = StyleAttachments.active(player);
		float mastery = style == null ? 1.0f : StyleMastery.damageMultiplier(player, style);
		// Style paths: Power (+15%), and Finisher (+35% on enemies below 40% health).
		if (CombatPaths.has(player, style, 1, "a")) {
			mastery *= 1.15f;
		}
		if (CombatPaths.has(player, style, 2, "a") && target.getHealth() < target.getMaxHealth() * 0.4f) {
			mastery *= 1.35f;
		}
		float before = target.getHealth();
		target.hurtServer(level, source, armament(player, damage) * mastery);
		hitSomething = true;
		// Fighting Spirit (tier 3 B): heal 15% of the damage that actually landed, at most 2 hearts a hit.
		if (CombatPaths.has(player, style, 3, "b")) {
			float dealt = Math.max(0, before - target.getHealth());
			if (dealt > 0) {
				player.heal(Math.min(4.0f, dealt * 0.15f));
			}
		}
	}

	private static float armament(Player player, float damage) {
		return HakiPowers.hasArmamentActive(player) ? damage * 1.25f : damage;
	}

	public static List<LivingEntity> around(Player player, ServerLevel level, double radius) {
		return level.getEntitiesOfClass(LivingEntity.class, player.getBoundingBox().inflate(radius),
				entity -> isEnemy(player, entity) && entity.distanceTo(player) <= radius + 1);
	}

	/** Enemies along the line you're looking at, stopping at the first solid block. */
	public static List<LivingEntity> inLine(Player player, ServerLevel level, double range, double width, int max) {
		Set<LivingEntity> found = new LinkedHashSet<>();
		Vec3 start = player.getEyePosition();
		Vec3 step = player.getLookAngle().scale(0.5);
		Vec3 point = start;
		for (double travelled = 0; travelled < range && found.size() < max; travelled += 0.5) {
			point = point.add(step);
			BlockPos pos = BlockPos.containing(point);
			if (!level.getBlockState(pos).getCollisionShape(level, pos).isEmpty()) {
				break;
			}
			for (LivingEntity entity : level.getEntitiesOfClass(LivingEntity.class, new AABB(point, point).inflate(width),
					entity -> isEnemy(player, entity))) {
				if (found.size() < max) {
					found.add(entity);
				}
			}
		}
		return new ArrayList<>(found);
	}

	/** Enemies in front of you that you can see. minDot 1.0 is a thin line, 0.5 is a wide fan. */
	public static List<LivingEntity> inCone(Player player, ServerLevel level, double range, double minDot, int max) {
		Vec3 look = player.getLookAngle();
		List<LivingEntity> found = new ArrayList<>();
		for (LivingEntity entity : level.getEntitiesOfClass(LivingEntity.class, player.getBoundingBox().inflate(range),
				entity -> isEnemy(player, entity) && player.hasLineOfSight(entity))) {
			Vec3 toTarget = entity.getBoundingBox().getCenter().subtract(player.getEyePosition());
			if (toTarget.length() <= range && toTarget.normalize().dot(look) >= minDot && found.size() < max) {
				found.add(entity);
			}
		}
		return found;
	}

	public static void pushAway(LivingEntity target, Player from, double strength, double up) {
		Vec3 away = target.position().subtract(from.position());
		away = new Vec3(away.x, 0, away.z).normalize().scale(strength);
		target.setDeltaMovement(away.x, up, away.z);
		Motion.sync(target);
	}

	private static void launch(ServerPlayer player, Vec3 horizontal, double up) {
		player.setDeltaMovement(horizontal.x, up, horizontal.z);
		Motion.sync(player);
	}

	private static void trail(Player player, ServerLevel level, double range, ParticleOptions particle) {
		Vec3 look = player.getLookAngle();
		Vec3 eye = player.getEyePosition();
		for (double d = 1; d < range; d += 1.5) {
			Vec3 point = eye.add(look.scale(d));
			level.sendParticles(particle, point.x, point.y - 0.3, point.z, 1, 0, 0, 0, 0);
		}
	}

	public static void effect(ServerLevel level, LivingEntity at, ParticleOptions particle, int count, SoundEvent sound) {
		level.sendParticles(particle, at.getX(), at.getY() + at.getBbHeight() / 2, at.getZ(), count, 0.8, 0.6, 0.8, 0.05);
		sound(level, at, sound);
	}

	private static void sound(ServerLevel level, LivingEntity at, SoundEvent sound) {
		if (sound == null) {
			return; // null: the technique's StyleSounds sound already played.
		}
		level.playSound(null, at.getX(), at.getY(), at.getZ(), sound, SoundSource.PLAYERS, 1.0f, 1.0f);
	}

	public static void actionBar(ServerPlayer player, Component message) {
		player.connection.send(new ClientboundSetActionBarTextPacket(message));
	}
}
