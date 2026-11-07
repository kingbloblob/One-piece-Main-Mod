package com.onepiecemod.town;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;

import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.CharacterFeature;

/**
 * Bar brawls. In the evening, when the bar is busy and a player is around, a sailor may throw a mug at somebody
 * and the whole room joins in. Punch a brawler (or punch anyone in a bar) and you're in it too.
 *
 * Rules of a bar fight: fists (weapons hit no harder than a fist), nobody dies. Knock someone out and they sit there
 * seeing stars; take too much and they laugh at you and leave you be. Be the last one standing with at least one
 * knock-out and the bar pays you in Berries and a round of sake. Hitting townsfolk in a brawl never angers the town.
 */
public class BarBrawls {
	private static final int CHECK_EVERY = 20;
	private static final float BASE_CHANCE = 0.012f; // per second, per busy bar (times the town's brawlChance)
	private static final int MAX_TICKS = 20 * 90;
	private static final double BAR_RADIUS = 10.0;

	private static class Brawl {
		final int id;
		final Town town;
		final List<TownsfolkEntity> fighters = new ArrayList<>();
		final Set<UUID> players = new HashSet<>();
		final Set<UUID> beaten = new HashSet<>();
		final Map<UUID, Integer> knockouts = new HashMap<>();
		final long endsAt;

		Brawl(int id, Town town, long endsAt) {
			this.id = id;
			this.town = town;
			this.endsAt = endsAt;
		}
	}

	private static final Map<String, Brawl> BY_TOWN = new HashMap<>();
	private static final Map<Integer, Brawl> BY_ID = new HashMap<>();
	private static int nextId = 1;

	private static final List<String> OPENERS = List.of("%s knocks over %s's drink.", "%s says %s cheats at cards.",
			"%s throws a mug at %s.", "%s laughs at %s's dream of finding the One Piece.", "%s steals %s's meat!");
	private static final List<String> CHEERS = List.of("FIGHT! FIGHT! FIGHT!", "My money's on the big one!", "Somebody save the sake!",
			"Hit him again!", "Not the good chairs!");

	public static boolean active(Town town) {
		return BY_TOWN.containsKey(town.key);
	}

	/** Called by Towns for each visited town with a bar. */
	static void tick(Town town, ServerLevel level, long gameTime) {
		Brawl brawl = BY_TOWN.get(town.key);
		if (brawl != null) {
			tickBrawl(brawl, level, gameTime);
			return;
		}
		if (gameTime % CHECK_EVERY != 0 || !town.def.bar || !town.scanned) {
			return;
		}
		long time = level.getOverworldClockTime() % 24000L;
		if (time < 11000 || time > 19000 || Festivals.active(town) != null) {
			return;
		}
		if (level.getNearestPlayer(town.bar.getX() + 0.5, town.bar.getY(), town.bar.getZ() + 0.5, 24.0, false) == null) {
			return;
		}
		if (level.getRandom().nextFloat() < BASE_CHANCE * town.def.brawlChance) {
			start(town, level, null);
		}
	}

	/** Starts a brawl in the town's bar. firstPunch = the player who started it (or null). Returns false if nobody's there. */
	public static boolean start(Town town, ServerLevel level, ServerPlayer firstPunch) {
		if (BY_TOWN.containsKey(town.key)) {
			return false;
		}
		List<TownsfolkEntity> crowd = barCrowd(town, level);
		crowd.sort((a, b) -> Boolean.compare(b.job().brawler, a.job().brawler)); // Sailors first.
		int wanted = firstPunch != null ? Math.min(crowd.size(), 3) : Math.min(crowd.size(), 2 + level.getRandom().nextInt(3));
		if (wanted < (firstPunch != null ? 1 : 2)) {
			return false;
		}
		Brawl brawl = new Brawl(nextId++, town, level.getGameTime() + MAX_TICKS);
		for (int i = 0; i < wanted; i++) {
			TownsfolkEntity fighter = crowd.get(i);
			fighter.joinBrawl(brawl.id);
			brawl.fighters.add(fighter);
		}
		BY_TOWN.put(town.key, brawl);
		BY_ID.put(brawl.id, brawl);
		RandomSource random = level.getRandom();
		String opener;
		if (firstPunch != null) {
			brawl.players.add(firstPunch.getUUID());
			opener = firstPunch.getName().getString() + " throws the first punch!";
			for (TownsfolkEntity fighter : brawl.fighters) {
				fighter.setBrawlTarget(firstPunch);
			}
		} else {
			TownsfolkEntity a = brawl.fighters.get(0);
			TownsfolkEntity b = brawl.fighters.get(1);
			opener = String.format(OPENERS.get(random.nextInt(OPENERS.size())), a.shortName(), b.shortName());
			retarget(brawl, level);
		}
		Component message = Component.literal("[" + town.name() + "] " + opener + " BAR BRAWL!").withStyle(ChatFormatting.RED, ChatFormatting.BOLD);
		for (ServerPlayer player : level.players()) {
			if (player.blockPosition().closerThan(town.bar, 40)) {
				player.sendSystemMessage(message);
			}
		}
		level.playSound(null, town.bar, SoundEvents.GLASS_BREAK, SoundSource.NEUTRAL, 1.0f, 0.9f);
		return true;
	}

	private static List<TownsfolkEntity> barCrowd(Town town, ServerLevel level) {
		AABB area = new AABB(town.bar).inflate(BAR_RADIUS, 4, BAR_RADIUS);
		return new ArrayList<>(level.getEntitiesOfClass(TownsfolkEntity.class, area,
				t -> t.isAlive() && t.townKey().equals(town.key) && !t.isChild() && !t.isSleeping()
						&& !"bartender".equals(t.jobId()) && !t.isVisitor() && t.brawlId() == 0));
	}

	/** Everyone without a target picks someone to punch: another brawler, or a player who joined in. */
	private static void retarget(Brawl brawl, ServerLevel level) {
		List<LivingEntity> standing = new ArrayList<>();
		for (TownsfolkEntity fighter : brawl.fighters) {
			if (fighter.isAlive() && !fighter.isKnockedOut()) {
				standing.add(fighter);
			}
		}
		for (UUID id : brawl.players) {
			Player player = level.getPlayerByUUID(id);
			if (player != null && player.isAlive() && !brawl.beaten.contains(id) && player.blockPosition().closerThan(brawl.town.bar, 24)) {
				standing.add(player);
			}
		}
		for (TownsfolkEntity fighter : brawl.fighters) {
			LivingEntity target = fighter.brawlTarget();
			boolean bad = target == null || !target.isAlive() || (target instanceof TownsfolkEntity t && t.isKnockedOut())
					|| (target instanceof Player p && brawl.beaten.contains(p.getUUID()));
			if (!bad || fighter.isKnockedOut()) {
				continue;
			}
			List<LivingEntity> options = new ArrayList<>(standing);
			options.remove(fighter);
			fighter.setBrawlTarget(options.isEmpty() ? null : options.get(level.getRandom().nextInt(options.size())));
		}
	}

	private static void tickBrawl(Brawl brawl, ServerLevel level, long gameTime) {
		if (gameTime % 10 == 0) {
			retarget(brawl, level);
		}
		// The crowd cheers.
		if (gameTime % 20 == 0) {
			AABB area = new AABB(brawl.town.bar).inflate(12, 4, 12);
			for (TownsfolkEntity watcher : level.getEntitiesOfClass(TownsfolkEntity.class, area, t -> t.brawlId() == 0 && !t.isSleeping())) {
				if (!brawl.fighters.isEmpty()) {
					TownsfolkEntity fighter = brawl.fighters.get(level.getRandom().nextInt(brawl.fighters.size()));
					watcher.getLookControl().setLookAt(fighter);
				}
				if (watcher.onGround() && level.getRandom().nextInt(3) == 0) {
					watcher.getJumpControl().jump();
				}
				if (level.getRandom().nextInt(25) == 0 && watcher.readyToTalk()) {
					watcher.shout(CHEERS.get(level.getRandom().nextInt(CHEERS.size())), 20);
					watcher.didTalk(200);
				}
			}
		}
		int standing = 0;
		for (TownsfolkEntity fighter : brawl.fighters) {
			if (fighter.isAlive() && !fighter.isKnockedOut()) {
				standing++;
			}
		}
		int playersIn = 0;
		for (UUID id : brawl.players) {
			Player player = level.getPlayerByUUID(id);
			if (player != null && player.isAlive() && !brawl.beaten.contains(id) && player.blockPosition().closerThan(brawl.town.bar, 24)) {
				playersIn++;
			}
		}
		if (standing + playersIn <= 1 || (playersIn == 0 && standing == 0) || gameTime > brawl.endsAt) {
			finish(brawl, level);
		}
	}

	private static void finish(Brawl brawl, ServerLevel level) {
		BY_TOWN.remove(brawl.town.key);
		BY_ID.remove(brawl.id);
		for (TownsfolkEntity fighter : brawl.fighters) {
			fighter.leaveBrawl();
		}
		List<ServerPlayer> nearby = new ArrayList<>();
		for (ServerPlayer player : level.players()) {
			if (player.blockPosition().closerThan(brawl.town.bar, 40)) {
				nearby.add(player);
			}
		}
		boolean champion = false;
		for (UUID id : brawl.players) {
			ServerPlayer player = (ServerPlayer) level.getPlayerByUUID(id);
			int kos = brawl.knockouts.getOrDefault(id, 0);
			if (player == null || brawl.beaten.contains(id) || kos == 0) {
				continue;
			}
			champion = true;
			int berries = 3 + 2 * kos;
			give(player, new ItemStack(CharacterFeature.BERRY, berries));
			give(player, CharacterData.stack("onepiece:sake", 2));
			player.sendSystemMessage(Component.literal("You're the last one standing in " + brawl.town.name() + "'s bar! The regulars chip in "
					+ berries + " Berries and the bartender pours you a round.").withStyle(ChatFormatting.GOLD));
			level.sendParticles(ParticleTypes.HAPPY_VILLAGER, player.getX(), player.getY() + 2, player.getZ(), 15, 0.5, 0.4, 0.5, 0.0);
			level.playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.8f, 1.2f);
		}
		String closing = champion ? "Ha! Somebody finally showed them how it's done!" : "Alright, alright! Who's paying for the chairs?!";
		TownsfolkEntity barkeep = bartender(brawl.town, level);
		for (ServerPlayer player : nearby) {
			player.sendSystemMessage(Component.literal((barkeep != null ? barkeep.shortName() : "The bartender") + ": ").withStyle(ChatFormatting.YELLOW)
					.append(Component.literal(closing).withStyle(ChatFormatting.WHITE)));
		}
	}

	private static TownsfolkEntity bartender(Town town, ServerLevel level) {
		List<TownsfolkEntity> list = level.getEntitiesOfClass(TownsfolkEntity.class, new AABB(town.bar).inflate(16, 6, 16),
				t -> "bartender".equals(t.jobId()) && t.townKey().equals(town.key));
		return list.isEmpty() ? null : list.get(0);
	}

	private static void give(ServerPlayer player, ItemStack stack) {
		if (!stack.isEmpty() && !player.getInventory().add(stack)) {
			player.drop(stack, false, net.minecraft.util.Prediction.SERVER_ONLY);
		}
	}

	// ---------- Hooks from TownsfolkEntity / TownBrawlGoal ----------

	/**
	 * A player hit a townsperson. Returns true if this is part of a bar fight (it then stays non-lethal and the town
	 * doesn't mind); false if it's an attack on a civilian.
	 */
	static boolean onPlayerHit(TownsfolkEntity victim, Player player, ServerLevel level) {
		Brawl brawl = BY_ID.get(victim.brawlId());
		Town town = victim.town();
		if (brawl == null && town != null) {
			brawl = BY_TOWN.get(town.key);
			// Joining a brawl that's already going? Anyone near the bar is fair game.
			if (brawl != null && (victim.isChild() || !victim.blockPosition().closerThan(town.bar, BAR_RADIUS + 2))) {
				return false;
			}
		}
		if (brawl == null) {
			// Punching someone in a bar starts a bar fight (they'll punch back).
			if (town == null || !town.def.bar || !town.scanned || victim.isChild() || victim.isVisitor()
					|| !victim.blockPosition().closerThan(town.bar, BAR_RADIUS) || !(player instanceof ServerPlayer serverPlayer)) {
				return false;
			}
			if (!start(town, level, serverPlayer)) {
				return false;
			}
			brawl = BY_TOWN.get(town.key);
		}
		brawl.players.add(player.getUUID());
		brawl.beaten.remove(player.getUUID());
		if (victim.brawlId() != brawl.id) {
			victim.joinBrawl(brawl.id);
			brawl.fighters.add(victim);
		}
		victim.setBrawlTarget(player);
		return true;
	}

	static void onKnockout(TownsfolkEntity loser, Entity by, ServerLevel level) {
		Brawl brawl = BY_ID.get(loser.brawlId());
		if (brawl == null) {
			return;
		}
		if (by instanceof Player player) {
			brawl.knockouts.merge(player.getUUID(), 1, Integer::sum);
		}
		level.playSound(null, loser.blockPosition(), SoundEvents.ANVIL_LAND, SoundSource.NEUTRAL, 0.3f, 1.8f);
		loser.shout(level.getRandom().nextBoolean() ? "Ugh... I see stars..." : "Lucky... punch...", 16);
	}

	/** A brawler would have finished the player off: instead they laugh, and the player is out of the fight. */
	static void onPlayerBeaten(TownsfolkEntity winner, Player player, ServerLevel level) {
		Brawl brawl = BY_ID.get(winner.brawlId());
		if (brawl != null) {
			brawl.beaten.add(player.getUUID());
			for (TownsfolkEntity fighter : brawl.fighters) {
				if (fighter.brawlTarget() == player) {
					fighter.setBrawlTarget(null);
				}
			}
		} else {
			winner.setBrawlTarget(null);
		}
		if (winner.readyToTalk()) {
			winner.shout("Ha! Go sleep it off, " + (com.onepiecemod.bounty.Bounty.threatLevel(player) >= 2 ? "big shot" : "rookie") + "!", 20);
			winner.didTalk(100);
		}
	}

	/** For /town brawl. */
	public static boolean forceStart(Town town, ServerLevel level) {
		return start(town, level, null);
	}

	static BlockPos barOf(Town town) {
		return town.bar;
	}
}
