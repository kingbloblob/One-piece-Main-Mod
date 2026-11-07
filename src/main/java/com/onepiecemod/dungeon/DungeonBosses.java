package com.onepiecemod.dungeon;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.BossEvent;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.advancement.AdvancementFeature;
import com.onepiecemod.anim.Anim;
import com.onepiecemod.anim.CombatAnims;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.character.BossStrikes;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.config.ModConfig;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.npc.NpcFeature;
import com.onepiecemod.sound.BossSounds;
import com.onepiecemod.util.Motion;

/**
 * Dungeon mini-bosses: the strongest guard at the bottom of each dungeon (tools/dungeons). The structure places a
 * normal pirate NPC with the tag onepiece_miniboss_&lt;dungeon id&gt;; when NpcFeature dresses it, setUp() turns it
 * into the boss from onepiece/dungeon_bosses.json:
 *  - its own name, health, damage, armor and size, and a boss bar for everyone within 36 blocks,
 *  - telegraphed moves every few seconds (a warning circle or line first, then the hit; step out of it):
 *    slam, slash, dash, fire_ring, sandstorm, curse,
 *  - a wave of minions at 66% and 33% health, and an enraged last third (faster, stronger, quicker moves),
 *  - on death: its drops, the bounty, and a chance at the dungeon's legendary blade. Missing the blade raises the
 *    killer's pity count for that dungeon, and after `pity` misses the next kill always drops it.
 * Phase flags are entity tags, so they survive a save and reload; the moves' timers are only in memory.
 */
public final class DungeonBosses {
	private DungeonBosses() {}

	public static final String TAG_PREFIX = "onepiece_miniboss_";
	private static final String READY = "onepiece_miniboss_ready";
	private static final String ENGAGED = "onepiece_mb_engaged";
	private static final String PHASE2 = "onepiece_mb_phase2";
	private static final String PHASE3 = "onepiece_mb_phase3";
	private static final double BAR_RANGE = 36;

	/** Per player: kills of each dungeon's boss since its legendary last dropped for them. */
	public static final AttachmentType<Map<String, Integer>> PITY = AttachmentRegistry.create(OnePieceMod.id("dungeon_pity"),
			builder -> builder.persistent(Codec.unboundedMap(Codec.STRING, Codec.INT)).copyOnDeath());
	/** Per player: dungeons whose boss they have beaten. */
	public static final AttachmentType<List<String>> CLEARED = AttachmentRegistry.create(OnePieceMod.id("dungeons_cleared"),
			builder -> builder.persistent(Codec.STRING.listOf()).copyOnDeath());

	private static final class State {
		final HumanNpc boss;
		final DungeonBossDef def;
		final ServerBossEvent bar;
		int cooldown = 60;
		int windup;
		int dash;
		String move = "";
		Vec3 aim = Vec3.ZERO;

		State(HumanNpc boss, DungeonBossDef def) {
			this.boss = boss;
			this.def = def;
			this.bar = new ServerBossEvent(UUID.randomUUID(), Component.literal(def.name).withStyle(ChatFormatting.BOLD), color(def.color),
					BossEvent.BossBarOverlay.NOTCHED_6);
		}
	}

	private static final Map<UUID, State> ACTIVE = new HashMap<>();

	public static void initialize() {
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity instanceof HumanNpc npc && npc.entityTags().contains(READY)) {
				track(npc);
			}
		});
		ServerEntityEvents.ENTITY_UNLOAD.register((entity, level) -> {
			State st = ACTIVE.remove(entity.getUUID());
			if (st != null) {
				st.bar.removeAllPlayers();
			}
		});
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			State st = ACTIVE.remove(entity.getUUID());
			if (st != null) {
				st.bar.removeAllPlayers();
				Entity killer = source.getEntity();
				defeated(st, killer instanceof ServerPlayer p ? p : null);
			}
		});
		ServerTickEvents.END_SERVER_TICK.register(DungeonBosses::tick);
		registerCommands();
		OnePieceMod.LOGGER.info("Dungeon mini-bosses: {}", DungeonBossDef.all().size());
	}

	/** The dungeon id in a mob's onepiece_miniboss_&lt;id&gt; tag, or null. */
	public static String bossId(Entity entity) {
		for (String tag : entity.entityTags()) {
			if (tag.startsWith(TAG_PREFIX) && !tag.equals(READY)) {
				return tag.substring(TAG_PREFIX.length());
			}
		}
		return null;
	}

	/** Called by NpcFeature right after a structure guard got its kit. Turns a tagged guard into its dungeon's boss. */
	public static void afterGuardDressed(HumanNpc npc) {
		if (npc.entityTags().contains(READY)) {
			return;
		}
		DungeonBossDef def = DungeonBossDef.get(bossId(npc));
		if (def == null) {
			return;
		}
		setUp(npc, def);
	}

	private static void setUp(HumanNpc npc, DungeonBossDef def) {
		base(npc, Attributes.MAX_HEALTH, def.health * ModConfig.npcHealth());
		base(npc, Attributes.ATTACK_DAMAGE, Math.max(1.0, def.damage * ModConfig.npcDamage() - CharacterData.weaponBonus(npc.getMainHandItem())));
		base(npc, Attributes.ARMOR, def.armor);
		base(npc, Attributes.KNOCKBACK_RESISTANCE, 0.8);
		base(npc, Attributes.FOLLOW_RANGE, 32);
		if (def.scale > 0) {
			base(npc, Attributes.SCALE, def.scale);
		}
		npc.setHealth(npc.getMaxHealth());
		npc.setCustomName(Component.literal(def.name).withStyle(textColor(def.color)));
		npc.setCustomNameVisible(true);
		npc.makeGuard();
		npc.setHomeTo(npc.blockPosition(), 12);
		npc.addTag(READY);
		track(npc);
	}

	private static void base(LivingEntity e, net.minecraft.core.Holder<net.minecraft.world.entity.ai.attributes.Attribute> attribute, double value) {
		AttributeInstance a = e.getAttribute(attribute);
		if (a != null) {
			a.setBaseValue(value);
		}
	}

	private static void track(HumanNpc npc) {
		DungeonBossDef def = DungeonBossDef.get(bossId(npc));
		if (def != null && npc.isAlive() && !ACTIVE.containsKey(npc.getUUID())) {
			ACTIVE.put(npc.getUUID(), new State(npc, def));
		}
	}

	// ---------- every tick ----------

	private static void tick(MinecraftServer server) {
		if (ACTIVE.isEmpty()) {
			return;
		}
		for (State st : new ArrayList<>(ACTIVE.values())) {
			if (!st.boss.isAlive() || st.boss.isRemoved()) {
				st.bar.removeAllPlayers();
				ACTIVE.remove(st.boss.getUUID());
				continue;
			}
			tickBoss(st, (ServerLevel) st.boss.level());
		}
	}

	private static void tickBoss(State st, ServerLevel level) {
		HumanNpc boss = st.boss;
		float frac = boss.getHealth() / boss.getMaxHealth();
		st.bar.setProgress(Mth.clamp(frac, 0f, 1f));
		if (boss.tickCount % 10 == 0) {
			updateBar(st, level);
		}
		LivingEntity target = boss.getTarget();
		boolean fighting = target != null && target.isAlive() && boss.distanceToSqr(target) < 30 * 30;
		if (!fighting) {
			st.windup = 0;
			st.dash = 0;
			return;
		}
		if (!boss.entityTags().contains(ENGAGED)) {
			boss.addTag(ENGAGED);
			shout(st, st.def.line(0), ChatFormatting.GOLD);
			level.playSound(null, boss.blockPosition(), BossSounds.INTRO, SoundSource.HOSTILE, 1.6f, 1.0f);
		}
		if (frac <= 0.66f && !boss.entityTags().contains(PHASE2)) {
			boss.addTag(PHASE2);
			callMinions(st, level, target);
			shout(st, st.def.line(1), ChatFormatting.GOLD);
			level.playSound(null, boss.blockPosition(), BossSounds.PHASE, SoundSource.HOSTILE, 1.6f, 1.0f);
		}
		if (frac <= 0.33f && !boss.entityTags().contains(PHASE3)) {
			boss.addTag(PHASE3);
			callMinions(st, level, target);
			enrage(st, level);
		}
		boolean enraged = boss.entityTags().contains(PHASE3);

		if (st.dash > 0) {
			st.dash--;
			if (st.dash == 0 || boss.position().distanceToSqr(st.aim) < 2.5 * 2.5) {
				st.dash = 0;
				for (LivingEntity v : victims(boss, level, boss.position(), 3.0)) {
					hit(st, level, v, 1.1f);
				}
				level.sendParticles(ParticleTypes.CRIT, boss.getX(), boss.getY() + 1, boss.getZ(), 30, 1.2, 0.6, 1.2, 0.3);
			}
			return;
		}
		if (st.windup > 0) {
			st.windup--;
			boss.getNavigation().stop();
			boss.getLookControl().setLookAt(st.aim.x, st.aim.y + 1, st.aim.z);
			if (st.windup % 4 == 0) {
				telegraph(st, level, st.windup <= 8 ? 0xFFE040 : 0xFF2020);
			}
			if (st.windup == 0) {
				perform(st, level, target);
			}
			return;
		}
		if (--st.cooldown <= 0 && boss.distanceToSqr(target) < 14 * 14) {
			List<String> moves = st.def.moves;
			st.move = moves.get(boss.getRandom().nextInt(moves.size()));
			st.aim = target.position();
			st.windup = windup(st.move);
			if (enraged) {
				st.windup = st.windup * 2 / 3;
			}
			st.cooldown = (enraged ? 70 : 100) + boss.getRandom().nextInt(40);
			level.playSound(null, boss.blockPosition(), BossSounds.WINDUP, SoundSource.HOSTILE, 1.2f, 1.0f);
			CombatAnims.play(boss, st.move.equals("slash") ? Anim.CROSS_SLASH : st.move.equals("dash") ? Anim.POUNCE : Anim.POWER_UP);
		}
	}

	private static int windup(String move) {
		return switch (move) {
			case "dash" -> 14;
			case "slash" -> 18;
			default -> 26;
		};
	}

	/** The warning shape for the move being wound up: where it will hit. */
	private static void telegraph(State st, ServerLevel level, int color) {
		Vec3 at = st.boss.position();
		switch (st.move) {
			case "slash" -> {
				Vec3 dir = flat(st.aim.subtract(at));
				DustParticleOptions dust = new DustParticleOptions(color, 1.4f);
				for (double d = 1; d <= 12; d += 0.5) {
					Vec3 p = at.add(dir.scale(d));
					level.sendParticles(dust, p.x, at.y + 0.15, p.z, 1, 0.1, 0, 0.1, 0);
				}
			}
			case "dash" -> BossStrikes.ring(level, st.aim, 2.5, color);
			case "slam" -> BossStrikes.ring(level, at, 5.0, color);
			case "fire_ring", "curse" -> BossStrikes.ring(level, at, 6.0, color);
			case "sandstorm" -> BossStrikes.ring(level, at, 7.0, color);
			default -> BossStrikes.ring(level, at, 4.0, color);
		}
	}

	private static void perform(State st, ServerLevel level, LivingEntity target) {
		HumanNpc boss = st.boss;
		Vec3 at = boss.position();
		switch (st.move) {
			case "slam" -> {
				CombatAnims.play(boss, Anim.GROUND_SLAM);
				for (LivingEntity v : victims(boss, level, at, 5.0)) {
					hit(st, level, v, 1.3f);
					Vec3 away = flat(v.position().subtract(at));
					v.push(away.x * 1.2, 0.6, away.z * 1.2);
					Motion.sync(v);
				}
				level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y + 0.3, at.z, 10, 2.5, 0.2, 2.5, 0);
				level.playSound(null, boss.blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.HOSTILE, 1.4f, 0.7f);
			}
			case "slash" -> {
				CombatAnims.play(boss, Anim.SPIN_SLASH);
				Vec3 dir = flat(st.aim.subtract(at));
				for (double d = 1; d <= 12; d += 1.0) {
					Vec3 p = at.add(dir.scale(d));
					level.sendParticles(ParticleTypes.SWEEP_ATTACK, p.x, at.y + 1, p.z, 1, 0, 0, 0, 0);
				}
				for (LivingEntity v : victims(boss, level, at.add(dir.scale(6)), 7.0)) {
					if (distanceToLine(v.position(), at, dir, 12) < 1.7) {
						hit(st, level, v, 1.2f);
					}
				}
				level.playSound(null, boss.blockPosition(), BossSounds.SLASH_LINE, SoundSource.HOSTILE, 1.4f, 1.0f);
			}
			case "dash" -> {
				CombatAnims.play(boss, Anim.DASH);
				Vec3 dir = flat(st.aim.subtract(at));
				double dist = Math.min(14, Math.sqrt(flatDist(st.aim, at)));
				boss.setDeltaMovement(dir.x * (0.5 + dist * 0.12), 0.4, dir.z * (0.5 + dist * 0.12));
				Motion.sync(boss);
				st.dash = 12;
				level.playSound(null, boss.blockPosition(), BossSounds.LEAP, SoundSource.HOSTILE, 1.4f, 1.0f);
			}
			case "fire_ring" -> {
				CombatAnims.play(boss, Anim.ROAR);
				for (LivingEntity v : victims(boss, level, at, 6.0)) {
					hit(st, level, v, 0.8f);
					v.igniteForSeconds(5);
				}
				for (int i = 0; i < 48; i++) {
					double a = i * Math.PI * 2 / 48;
					level.sendParticles(ParticleTypes.FLAME, at.x + Math.cos(a) * 6, at.y + 0.3, at.z + Math.sin(a) * 6, 3, 0.2, 0.4, 0.2, 0.02);
				}
				level.playSound(null, boss.blockPosition(), BossSounds.SIGNATURE, SoundSource.HOSTILE, 1.4f, 1.0f);
			}
			case "sandstorm" -> {
				CombatAnims.play(boss, Anim.CAST);
				for (LivingEntity v : victims(boss, level, at, 7.0)) {
					hit(st, level, v, 0.5f);
					v.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 60, 0));
					v.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 80, 1));
				}
				level.sendParticles(new DustParticleOptions(0xD8C08A, 2.2f), at.x, at.y + 1.2, at.z, 160, 4.0, 1.2, 4.0, 0);
				level.playSound(null, boss.blockPosition(), BossSounds.GROUND_WAVE, SoundSource.HOSTILE, 1.4f, 1.2f);
			}
			case "curse" -> {
				CombatAnims.play(boss, Anim.SUMMON);
				for (LivingEntity v : victims(boss, level, at, 6.0)) {
					hit(st, level, v, 0.6f);
					v.addEffect(new MobEffectInstance(MobEffects.WITHER, 100, 0));
					v.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 100, 0));
				}
				level.sendParticles(ParticleTypes.SOUL, at.x, at.y + 0.5, at.z, 60, 3.5, 0.6, 3.5, 0.03);
				level.playSound(null, boss.blockPosition(), BossSounds.BLACK_HOLE, SoundSource.HOSTILE, 1.2f, 1.3f);
			}
			default -> {
			}
		}
	}

	private static void hit(State st, ServerLevel level, LivingEntity victim, float mult) {
		float damage = (float) (st.def.damage * ModConfig.npcDamage() * mult);
		victim.hurtServer(level, st.boss.damageSources().mobAttack(st.boss), damage);
	}

	private static void callMinions(State st, ServerLevel level, LivingEntity target) {
		DungeonBossDef.Minions m = st.def.minions;
		if (m == null || m.kit == null || m.count <= 0) {
			return;
		}
		HumanNpc boss = st.boss;
		CombatAnims.play(boss, Anim.SUMMON);
		for (int i = 0; i < m.count; i++) {
			BlockPos spot = boss.blockPosition();
			for (int tries = 0; tries < 8; tries++) {
				BlockPos p = boss.blockPosition().offset(boss.getRandom().nextInt(9) - 4, 0, boss.getRandom().nextInt(9) - 4);
				if (level.getBlockState(p).getCollisionShape(level, p).isEmpty()
						&& level.getBlockState(p.above()).getCollisionShape(level, p.above()).isEmpty()
						&& !level.getBlockState(p.below()).getCollisionShape(level, p.below()).isEmpty()) {
					spot = p;
					break;
				}
			}
			HumanNpc minion = NpcFeature.spawn(level, m.kit, spot, boss.getRandom().nextFloat() * 360f);
			if (minion != null) {
				minion.makeGuard();
				minion.addTag(BossStrikes.MINION_TAG);
				minion.setTarget(target);
				level.sendParticles(ParticleTypes.POOF, spot.getX() + 0.5, spot.getY() + 1, spot.getZ() + 0.5, 12, 0.3, 0.5, 0.3, 0.02);
			}
		}
	}

	private static void enrage(State st, ServerLevel level) {
		HumanNpc boss = st.boss;
		boss.addEffect(new MobEffectInstance(MobEffects.SPEED, 20 * 600, 0));
		boss.addEffect(new MobEffectInstance(MobEffects.STRENGTH, 20 * 600, 0));
		boss.setCustomName(Component.literal(st.def.name).withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD));
		st.bar.setColor(BossEvent.BossBarColor.RED);
		st.bar.setName(Component.literal(st.def.name + " (enraged)").withStyle(ChatFormatting.BOLD));
		CombatAnims.play(boss, Anim.ROAR);
		level.sendParticles(ParticleTypes.ANGRY_VILLAGER, boss.getX(), boss.getY() + 2, boss.getZ(), 10, 0.6, 0.6, 0.6, 0);
		level.playSound(null, boss.blockPosition(), BossSounds.ENRAGE, SoundSource.HOSTILE, 1.8f, 1.0f);
		shout(st, st.def.line(2), ChatFormatting.RED);
	}

	// ---------- defeat ----------

	private static void defeated(State st, ServerPlayer killer) {
		HumanNpc boss = st.boss;
		ServerLevel level = (ServerLevel) boss.level();
		DungeonBossDef def = st.def;
		List<ServerPlayer> nearby = level.getEntitiesOfClass(ServerPlayer.class, boss.getBoundingBox().inflate(BAR_RANGE), Player::isAlive);
		if (killer == null && !nearby.isEmpty()) {
			killer = nearby.get(0);
		}
		for (DungeonBossDef.Drop drop : def.drops) {
			if (boss.getRandom().nextFloat() <= drop.chance) {
				int n = drop.min + (drop.max > drop.min ? boss.getRandom().nextInt(drop.max - drop.min + 1) : 0);
				ItemStack stack = CharacterData.stack(drop.item, n);
				if (!stack.isEmpty()) {
					boss.spawnAtLocation(level, stack);
				}
			}
		}
		boolean blade = false;
		if (def.legendary != null && killer != null) {
			Map<String, Integer> pity = new HashMap<>(killer.getAttachedOrElse(PITY, Map.of()));
			int misses = pity.getOrDefault(def.id, 0);
			blade = boss.getRandom().nextFloat() < def.legendary.chance || (def.legendary.pity > 0 && misses + 1 >= def.legendary.pity);
			pity.put(def.id, blade ? 0 : misses + 1);
			killer.setAttached(PITY, pity);
			if (blade) {
				ItemStack sword = CharacterData.stack(def.legendary.item, 1);
				if (!sword.isEmpty()) {
					boss.spawnAtLocation(level, sword);
					Component msg = Component.literal(def.name + " dropped " + sword.getHoverName().getString() + "!")
							.withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD);
					for (ServerPlayer p : nearby) {
						p.sendSystemMessage(msg);
					}
					level.playSound(null, boss.blockPosition(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 1.0f, 1.0f);
				}
			} else {
				int left = Math.max(1, def.legendary.pity - misses - 1);
				ItemStack sword = CharacterData.stack(def.legendary.item, 1);
				killer.sendSystemMessage(Component.literal("No " + sword.getHoverName().getString() + " this time. The blade is close: it will be yours within "
						+ left + (left == 1 ? " more victory." : " more victories.")).withStyle(ChatFormatting.GRAY));
			}
		}
		if (killer != null && def.bounty > 0) {
			Bounty.add(killer, def.bounty);
			killer.sendSystemMessage(Component.literal("Your bounty rose by " + Bounty.format(def.bounty) + " Berries!").withStyle(ChatFormatting.YELLOW), true);
		}
		for (ServerPlayer p : nearby) {
			List<String> cleared = new ArrayList<>(p.getAttachedOrElse(CLEARED, List.of()));
			if (!cleared.contains(def.id)) {
				cleared.add(def.id);
				p.setAttached(CLEARED, cleared);
			}
			AdvancementFeature.grant(p, "pirate/dungeon_delver");
			AdvancementFeature.grant(p, "pirate/dungeon_master", def.id);
			p.sendSystemMessage(Component.literal(def.title + " has fallen! The sanctum behind the throne is open.")
					.withStyle(ChatFormatting.GREEN));
		}
		level.sendParticles(ParticleTypes.TOTEM_OF_UNDYING, boss.getX(), boss.getY() + 1, boss.getZ(), 60, 0.8, 1.2, 0.8, 0.3);
	}

	// ---------- helpers ----------

	private static void updateBar(State st, ServerLevel level) {
		AABB box = st.boss.getBoundingBox().inflate(BAR_RANGE);
		List<ServerPlayer> near = level.getEntitiesOfClass(ServerPlayer.class, box, p -> p.isAlive() && !p.isSpectator());
		for (ServerPlayer p : near) {
			if (!st.bar.getPlayers().contains(p)) {
				st.bar.addPlayer(p);
			}
		}
		for (ServerPlayer p : new ArrayList<>(st.bar.getPlayers())) {
			if (!near.contains(p)) {
				st.bar.removePlayer(p);
			}
		}
	}

	private static void shout(State st, String line, ChatFormatting color) {
		if (line == null || line.isEmpty()) {
			return;
		}
		Component msg = Component.literal(st.def.name + ": ").withStyle(color, ChatFormatting.BOLD)
				.append(Component.literal(line).withStyle(ChatFormatting.WHITE));
		for (ServerPlayer p : st.bar.getPlayers()) {
			p.sendSystemMessage(msg);
		}
	}

	/** Who a move hurts: players (not in creative or spectator), crewmates and tamed creatures. */
	private static List<LivingEntity> victims(HumanNpc boss, ServerLevel level, Vec3 at, double radius) {
		return level.getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(radius, 3, radius), e -> e != boss && e.isAlive()
				&& !e.entityTags().contains(BossStrikes.MINION_TAG)
				&& !(e instanceof Player p && (p.isCreative() || p.isSpectator()))
				&& (e instanceof Player || e instanceof com.onepiecemod.crew.CrewmateEntity
						|| (e instanceof com.onepiecemod.creature.CreatureEntity pet && pet.isTamed()))
				&& flatDist(e.position(), at) <= radius * radius);
	}

	private static Vec3 flat(Vec3 v) {
		Vec3 f = new Vec3(v.x, 0, v.z);
		return f.lengthSqr() < 1.0E-4 ? new Vec3(1, 0, 0) : f.normalize();
	}

	private static double flatDist(Vec3 a, Vec3 b) {
		double dx = a.x - b.x;
		double dz = a.z - b.z;
		return dx * dx + dz * dz;
	}

	private static double distanceToLine(Vec3 p, Vec3 start, Vec3 dir, double length) {
		Vec3 rel = new Vec3(p.x - start.x, 0, p.z - start.z);
		double t = Mth.clamp(rel.dot(dir), 0, length);
		Vec3 closest = dir.scale(t);
		return Math.sqrt(flatDist(rel, closest));
	}

	private static BossEvent.BossBarColor color(String name) {
		return switch (name == null ? "" : name) {
			case "yellow" -> BossEvent.BossBarColor.YELLOW;
			case "purple" -> BossEvent.BossBarColor.PURPLE;
			case "pink" -> BossEvent.BossBarColor.PINK;
			case "blue" -> BossEvent.BossBarColor.BLUE;
			case "green" -> BossEvent.BossBarColor.GREEN;
			case "white" -> BossEvent.BossBarColor.WHITE;
			default -> BossEvent.BossBarColor.RED;
		};
	}

	private static ChatFormatting textColor(String name) {
		return switch (name == null ? "" : name) {
			case "yellow" -> ChatFormatting.GOLD;
			case "purple" -> ChatFormatting.DARK_PURPLE;
			case "pink" -> ChatFormatting.LIGHT_PURPLE;
			case "blue" -> ChatFormatting.BLUE;
			case "green" -> ChatFormatting.GREEN;
			default -> ChatFormatting.RED;
		};
	}

	// ---------- /dungeon ----------

	private static void registerCommands() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("dungeon")
						.then(Commands.literal("list").executes(context -> {
							ServerPlayer player = context.getSource().getPlayerOrException();
							List<String> cleared = player.getAttachedOrElse(CLEARED, List.of());
							Map<String, Integer> pity = player.getAttachedOrElse(PITY, Map.of());
							player.sendSystemMessage(Component.literal("Dungeons of the Grand Line:").withStyle(ChatFormatting.GOLD));
							for (DungeonBossDef def : DungeonBossDef.all().values()) {
								String blade = def.legendary == null ? "" : CharacterData.stack(def.legendary.item, 1).getHoverName().getString();
								player.sendSystemMessage(Component.literal((cleared.contains(def.id) ? " [x] " : " [ ] ") + def.title + " - " + def.name
										+ (blade.isEmpty() ? "" : " (guards " + blade + ", tries " + pity.getOrDefault(def.id, 0) + ")"))
										.withStyle(cleared.contains(def.id) ? ChatFormatting.GREEN : ChatFormatting.GRAY));
							}
							player.sendSystemMessage(Component.literal("Dungeon chests hold maps to the next dungeon.").withStyle(ChatFormatting.DARK_GRAY));
							return 1;
						}))
						.then(Commands.literal("spawn")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.argument("id", StringArgumentType.word())
										.suggests((context, builder) -> SharedSuggestionProvider.suggest(DungeonBossDef.all().keySet(), builder))
										.executes(context -> {
											DungeonBossDef def = DungeonBossDef.get(StringArgumentType.getString(context, "id"));
											if (def == null) {
												context.getSource().sendFailure(Component.literal("No such dungeon boss."));
												return 0;
											}
											ServerLevel level = context.getSource().getLevel();
											HumanNpc npc = NpcFeature.spawn(level, def.kit, BlockPos.containing(context.getSource().getPosition()), 0f);
											if (npc == null) {
												context.getSource().sendFailure(Component.literal("Kit " + def.kit + " is missing."));
												return 0;
											}
											npc.addTag(TAG_PREFIX + def.id);
											setUp(npc, def);
											context.getSource().sendSuccess(() -> Component.literal("Spawned " + def.name), true);
											return 1;
										})))));
	}
}
