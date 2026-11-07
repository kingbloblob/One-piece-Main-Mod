package com.onepiecemod.endgame;

import java.util.List;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.story.StoryProgress;
import com.onepiecemod.story.StoryTracker;

/**
 * New Game+: once the whole story is done (Imu beaten), start it again from Foosha Village and keep everything else:
 * your Devil Fruit, Haki, stats, fighting styles, crew, titles, kingdoms and items.
 *
 * Each cycle (up to NG+5) makes every boss you meet tougher and pays more Berries for them.
 * The first time you beat a boss in a cycle, it drops its Devil Fruit again. Story boss goals ask for a fresh win.
 */
public class NewGamePlus {
	public static final int MAX_CYCLE = 5;
	/** Bosses that already got their New Game+ boost (or are raid bosses, which get it from the raid). */
	public static final String CHECKED_TAG = "onepiece_ng_checked";
	/** Bosses boosted for New Game+ carry "onepiece_ng_<cycle>". */
	private static final String CYCLE_TAG = "onepiece_ng_";
	private static final Identifier NG_DAMAGE = OnePieceMod.id("new_game_plus_damage");
	private static final double NEARBY = 96;
	/** Every 2 seconds, bosses this close to a New Game+ player that loaded before the player came near get their boost. */
	private static final double SCAN = 64;

	public static void initialize() {
		// Bosses near a New Game+ player get stronger as they appear (summoned, spawned at a lair, or loaded from disk the first time).
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity instanceof CharacterEntity boss && boss.isBoss() && !boss.entityTags().contains(CHECKED_TAG)) {
				int cycle = nearbyCycle(level, boss);
				if (cycle > 0) {
					boost(boss, cycle);
				}
			}
		});
		// Lair bosses usually load while the player is still far off (the world loads ~10 chunks out), so check again as they get close.
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 40 != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				int cycle = EndgameData.of(player).cycle();
				if (cycle <= 0 || player.isSpectator()) {
					continue;
				}
				for (CharacterEntity boss : player.level().getEntitiesOfClass(CharacterEntity.class, player.getBoundingBox().inflate(SCAN),
						boss -> boss.isBoss() && !boss.entityTags().contains(CHECKED_TAG))) {
					boost(boss, Math.max(cycle, nearbyCycle((ServerLevel) player.level(), boss)));
				}
			}
		});
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (entity instanceof CharacterEntity boss && boss.isBoss() && entity.level() instanceof ServerLevel level) {
				onBossDefeated(level, boss);
			}
		});
	}

	// ---- How much tougher ----

	public static double damageBonus(int cycle) {
		return 0.2 * cycle;
	}

	public static double healthBonus(int cycle) {
		return 0.25 * cycle;
	}

	/** Raid enemies grow less per cycle (raids already scale with Resistance and party size). */
	public static double raidHealthBonus(int cycle) {
		return 0.15 * cycle;
	}

	/**
	 * The least health a boss has in this cycle. Without it, early bosses stayed trivial in New Game+ (Buggy had 125 health
	 * at NG+1, a few seconds for a player who has finished the story). NG+1 1300, NG+3 1900, NG+5 2500.
	 */
	public static float healthFloor(int cycle) {
		return cycle <= 0 ? 0 : 1000 + 300 * cycle;
	}

	/** The least attack damage a boss has in this cycle: NG+1 16, NG+3 20, NG+5 24. */
	public static double damageFloor(int cycle) {
		return cycle <= 0 ? 0 : 14 + 2 * cycle;
	}

	/** Extra Resistance levels (each = 20% less damage taken) for bosses that are already at the health cap. */
	public static int resistanceBonus(int cycle) {
		return cycle >= 5 ? 2 : cycle >= 3 ? 1 : 0;
	}

	private static int nearbyCycle(ServerLevel level, CharacterEntity boss) {
		int cycle = 0;
		for (ServerPlayer player : level.players()) {
			if (player.distanceToSqr(boss) < NEARBY * NEARBY) {
				cycle = Math.max(cycle, EndgameData.of(player).cycle());
			}
		}
		return cycle;
	}

	private static void boost(CharacterEntity boss, int cycle) {
		boss.addTag(CHECKED_TAG);
		boss.addTag(CYCLE_TAG + cycle);
		AttributeInstance damage = boss.getAttribute(Attributes.ATTACK_DAMAGE);
		if (damage != null) {
			// +20% per cycle, and never less than the cycle's floor, so early bosses still hurt.
			double base = Math.max(1, damage.getBaseValue());
			double bonus = Math.max(damageBonus(cycle), damageFloor(cycle) / base - 1);
			damage.addOrReplacePermanentModifier(new AttributeModifier(NG_DAMAGE, bonus, AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
		}
		// Most bosses are past Minecraft's 1024 health cap, so the extra health turns into smaller hits (see CharacterEntity).
		float health = boss.effectiveMaxHealth();
		float wanted = Math.max(health * (float) (1 + healthBonus(cycle)), healthFloor(cycle));
		boss.setHealthScale(boss.getHealthScale() * wanted / Math.max(1, health));
		int resistance = resistanceBonus(cycle);
		if (resistance > 0) {
			boss.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, MobEffectInstance.INFINITE_DURATION, resistance - 1, false, false));
		}
		if (boss.getCustomName() != null) {
			boss.setCustomName(Component.literal(boss.getCustomName().getString() + " [NG+" + cycle + "]"));
		}
	}

	private static int cycleOf(CharacterEntity boss) {
		for (int cycle = MAX_CYCLE; cycle > 0; cycle--) {
			if (boss.entityTags().contains(CYCLE_TAG + cycle)) {
				return cycle;
			}
		}
		return 0;
	}

	// ---- Rewards ----

	/** New Game+ players nearby: count the win for this cycle, and the first win per cycle drops the fruit again. */
	private static void onBossDefeated(ServerLevel level, CharacterEntity boss) {
		String id = boss.getCharacterId();
		CharacterData data = boss.getData();
		boolean fruitDropped = false;
		int bonusCycle = Math.max(cycleOf(boss), 0);
		for (ServerPlayer player : level.players()) {
			EndgameData endgame = EndgameData.of(player);
			if (endgame.cycle() <= 0 || player.distanceToSqr(boss) > 48 * 48) {
				continue;
			}
			boolean firstThisCycle = !endgame.cycleBosses().contains(id);
			EndgameData.set(player, endgame.withCycleBoss(id));
			if (!firstThisCycle || boss.entityTags().contains(Raids.TAG)) {
				continue;
			}
			// The normal drop skipped the fruit (the boss was beaten in an earlier cycle), so drop it once per cycle here.
			if (!boss.isFirstWin() && !fruitDropped) {
				ItemStack fruit = CharacterData.stack(data.fruitItem, 1);
				if (!fruit.isEmpty()) {
					boss.spawnAtLocation(level, fruit);
					fruitDropped = true;
				}
			}
			int berries = (int) Math.round(data.bounty * 0.5 * Math.max(bonusCycle, endgame.cycle()));
			Raids.give(player, new ItemStack(CharacterFeature.BERRY), berries);
			player.sendSystemMessage(Component.literal("New Game+ " + endgame.cycle() + " bonus: " + berries + " Berries.")
					.withStyle(ChatFormatting.DARK_RED));
		}
	}

	/** Story "beat this boss" goals: on the first playthrough any win counts; in New Game+ it must be this cycle. */
	public static boolean bossGoalDone(ServerPlayer player, String boss) {
		EndgameData data = EndgameData.of(player);
		if (data.cycle() <= 0) {
			return CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, boss);
		}
		return data.cycleBosses().contains(boss);
	}

	// ---- Starting a new cycle ----

	/** Why this player can't start New Game+ yet, or null if they can. */
	public static String problem(ServerPlayer player) {
		EndgameData data = EndgameData.of(player);
		if (data.cycle() >= MAX_CYCLE) {
			return "You already reached New Game+ " + MAX_CYCLE + ", the last cycle. You are a legend.";
		}
		StoryProgress progress = StoryProgress.of(player);
		if (progress == null || !progress.allDone()) {
			return "Finish every chapter first, the post-game too (beat Imu, then hear the Dawn at Laugh Tale).";
		}
		return null;
	}

	public static void describe(ServerPlayer player) {
		int next = EndgameData.of(player).cycle() + 1;
		player.sendSystemMessage(Component.literal("=== New Game+ " + next + " ===").withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD));
		for (String line : List.of(
				"The story starts again at chapter 1. Your quests and story events start over too.",
				"You keep your Devil Fruit, awakening, Haki, stats, fighting styles, crew, ship, titles, kingdoms, bounty and items.",
				"Bosses near you get " + Math.round(healthBonus(next) * 100) + "% more health and " + Math.round(damageBonus(next) * 100)
						+ "% more damage" + (resistanceBonus(next) > 0 ? ", plus Resistance " + resistanceBonus(next) : "") + ".",
				"Even the early bosses are no pushovers: every boss has at least " + Math.round(healthFloor(next)) + " health.",
				"Each boss pays " + Math.round(50 * next) + "% of its bounty in extra Berries and drops its Devil Fruit again, once per cycle.",
				"Raid treasure grows by " + (50 * next) + "%.")) {
			player.sendSystemMessage(Component.literal(" - " + line).withStyle(ChatFormatting.GRAY));
		}
	}

	public static void start(ServerPlayer player) {
		EndgameData data = EndgameData.of(player).nextCycle();
		EndgameData.set(player, data);
		player.setAttached(CharacterAttachments.QUESTS_STARTED, List.of());
		player.setAttached(CharacterAttachments.QUESTS_DONE, List.of());
		player.setAttached(CharacterAttachments.MET, List.of());
		StoryProgress.set(player, StoryProgress.START);
		player.sendSystemMessage(Component.literal("New Game+ " + data.cycle() + " begins. The sea remembers your name, but the world has grown stronger.")
				.withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD));
		StoryTracker.startChapter(player, 0);
		com.onepiecemod.worldevent.WorldNews.report(player.level().getServer(),
				player.getName().getString() + " has set sail again from Foosha Village. A new age begins! (New Game+ " + data.cycle() + ")",
				ChatFormatting.DARK_RED);
	}
}
