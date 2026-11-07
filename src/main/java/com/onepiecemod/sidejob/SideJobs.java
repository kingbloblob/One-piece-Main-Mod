package com.onepiecemod.sidejob;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.function.Predicate;

import org.jetbrains.annotations.Nullable;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.chat.Style;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Prediction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BarrelBlockEntity;
import net.minecraft.world.level.levelgen.Heightmap;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.bounty.BountyFeature;
import com.onepiecemod.bounty.BountyHunterEntity;
import com.onepiecemod.bounty.HunterFruit;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.creature.Creatures;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.npc.NpcFeature;
import com.onepiecemod.sound.ModSounds;
import com.onepiecemod.stats.StatTraining;
import com.onepiecemod.town.Town;
import com.onepiecemod.town.TownsfolkEntity;

/**
 * Side jobs for the long middle of the game: things to do between one story island and the next.
 *
 *  - Town requests. Each day about 1 in 4 townsfolk needs help. Walk past them and they call out; talk to them
 *    to hear what they need: bring them goods (a fisher wants cod, a smith wants iron...), chase off pirates or
 *    monsters, or find something they lost (it's in a barrel 50-130 blocks away). Go back to them to get paid.
 *  - Wanted contracts. Bartenders, sailors and foreign traders know who has a price on their head. A contract
 *    points 200-450 blocks away; when you get close, the target shows up: a pirate captain and their crew,
 *    a Devil Fruit user, a man-eating beast, or (after Impel Down) an escaped convict. Beat the target to get paid,
 *    and 5% of the target's bounty is added to yours (Marines get Merit instead).
 *
 * Both get bigger as the story goes on (East Blue, Paradise, Summit War, New World). One job at a time; /jobs
 * shows it. Jobs are saved on the player; enemies are not (they come back if you leave and return).
 */
public final class SideJobs {
	public static final String TAG = "onepiece_side_job";
	private static final String BOSS_TAG = "onepiece_side_job_boss";
	private static final int SPAWN_DISTANCE = 56;
	private static final int LOST_DISTANCE = 40;
	private static final int FORGET_DISTANCE = 160;
	/** Out of 100: how many townsfolk need help on a given day. */
	private static final int NEEDY_PERCENT = 25;

	/** The player's current job, if any. */
	public static final AttachmentType<SideJob> JOB = AttachmentRegistry.create(
			OnePieceMod.id("side_job"), builder -> builder.persistent(SideJob.CODEC).copyOnDeath());

	/** How many jobs the player finished: "requests" and "contracts". */
	public static final AttachmentType<Map<String, Integer>> DONE = AttachmentRegistry.create(
			OnePieceMod.id("side_jobs_done"), builder -> builder.persistent(Codec.unboundedMap(Codec.STRING, Codec.INT)).copyOnDeath());

	private record Offer(SideJob job, UUID from, long until) {
	}

	/** Contract enemies alive right now, by player. Never saved. */
	private record Live(String jobId, List<Mob> mobs) {
	}

	private static final Map<UUID, Offer> OFFERS = new HashMap<>();
	private static final Map<UUID, Live> LIVE = new HashMap<>();
	/** "player townsfolk day": who already called out to whom today. */
	private static final Set<String> CALLED = new HashSet<>();
	private static final Map<UUID, Long> NEXT_CALL = new HashMap<>();

	private SideJobs() {
	}

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(SideJobs::tick);
		ServerLivingEntityEvents.AFTER_DEATH.register(SideJobs::onDeath);
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			// A contract enemy that isn't part of a running job (the server restarted, or the job is over).
			if (entity.entityTags().contains(TAG) && LIVE.values().stream().noneMatch(live -> live.mobs.contains(entity))) {
				entity.discard();
			}
		});
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> {
			LIVE.clear();
			OFFERS.clear();
			CALLED.clear();
			NEXT_CALL.clear();
		});
		registerCommands();
	}

	@Nullable
	public static SideJob job(ServerPlayer player) {
		return player.getAttached(JOB);
	}

	public static int done(ServerPlayer player, String key) {
		return player.getAttachedOrElse(DONE, Map.of()).getOrDefault(key, 0);
	}

	// ---- Talking to townsfolk (called by TownsfolkEntity) ----

	/** Called when a player talks to a townsperson. Returns true if a side job handled the talk. */
	public static boolean onTalk(ServerPlayer player, TownsfolkEntity person) {
		SideJob job = job(player);
		boolean shop = !person.getOffers().isEmpty();
		if (job != null && !job.isContract() && isGiver(job, person)) {
			if (ready(player, job)) {
				handIn(player, person, job);
				return true;
			}
			person.say(player, "Any luck with that? " + progressText(player, job) + ".");
			return !shop;
		}
		if (job == null && !player.isShiftKeyDown() && needy(person)) {
			Offer pending = OFFERS.get(player.getUUID());
			if (pending != null && pending.from.equals(person.getUUID()) && pending.until > player.level().getGameTime()) {
				return false; // Already heard this one: talking again opens the shop (or chats) as usual.
			}
			offer(player, person);
			return true;
		}
		return false;
	}

	/** About 1 in 4 townsfolk need help each day (the same ones all day). */
	private static boolean needy(TownsfolkEntity person) {
		long day = person.level().getOverworldClockTime() / 24000L;
		long hash = person.getUUID().getLeastSignificantBits() ^ (day * 0x9E3779B97F4A7C15L);
		hash ^= hash >>> 29;
		hash *= 0xBF58476D1CE4E5B9L;
		hash ^= hash >>> 32;
		return Math.floorMod(hash, 100) < NEEDY_PERCENT;
	}

	private static boolean isGiver(SideJob job, TownsfolkEntity person) {
		if (person.getUUID().toString().equals(job.giver())) {
			return true;
		}
		// The giver is gone (killed, or moved away): anyone from the same spot can take it and pass it on.
		ServerLevel level = (ServerLevel) person.level();
		Entity giver = level.getEntity(UUID.fromString(job.giver()));
		return (giver == null || !giver.isAlive()) && person.blockPosition().distSqr(job.origin()) < 48 * 48;
	}

	private static String townName(TownsfolkEntity person) {
		Town town = person.town();
		return town == null ? "town" : town.name();
	}

	private static void offer(ServerPlayer player, TownsfolkEntity person) {
		RandomSource random = player.getRandom();
		boolean peaceful = player.level().getDifficulty() == Difficulty.PEACEFUL;
		SideJob job = null;
		if (!peaceful && JobBoard.postsContracts(person.jobId())) {
			job = JobBoard.contract(player, person, townName(person), random);
		} else {
			for (int i = 0; i < 6 && (job == null || peaceful && job.kind().startsWith("CULL")); i++) {
				job = JobBoard.request(player, person, townName(person), random);
			}
		}
		OFFERS.put(player.getUUID(), new Offer(job, person.getUUID(), player.level().getGameTime() + 20 * 120));
		if (job.isContract()) {
			person.say(player, "Psst. You look like you can handle yourself. There's a fresh Wanted poster on the wall...");
		} else {
			person.say(player, job.name());
		}
		player.sendSystemMessage(Component.literal(job.isContract() ? "[Wanted] " : "[Request] ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(job.title()).withStyle(ChatFormatting.YELLOW))
				.append(Component.literal(job.isContract() ? " - " + job.name() : "").withStyle(ChatFormatting.GRAY)));
		MutableComponent line = Component.literal("Reward: " + job.berries() + " Berries").withStyle(ChatFormatting.GOLD);
		if (job.bounty() > 0) {
			line.append(Component.literal(" (bounty " + Bounty.format(job.bounty()) + ")").withStyle(ChatFormatting.GRAY));
		}
		line.append(Component.literal("  "))
				.append(Component.literal("[Accept]").withStyle(Style.EMPTY.withColor(ChatFormatting.GREEN).withBold(true)
						.withClickEvent(new ClickEvent.RunCommand("/jobs accept"))))
				.append(Component.literal(" "))
				.append(Component.literal("[No thanks]").withStyle(Style.EMPTY.withColor(ChatFormatting.RED)
						.withClickEvent(new ClickEvent.RunCommand("/jobs decline"))));
		player.sendSystemMessage(line);
	}

	private static String accept(ServerPlayer player) {
		if (job(player) != null) {
			return "You already have a job. Finish it, or give up with /jobs abandon.";
		}
		Offer offer = OFFERS.remove(player.getUUID());
		if (offer == null || offer.until < player.level().getGameTime()) {
			return "Nobody is asking you for anything right now. Talk to townsfolk who call out to you.";
		}
		SideJob job = offer.job;
		player.setAttached(JOB, job);
		player.sendSystemMessage(Component.literal("Job taken: ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(job.title()).withStyle(ChatFormatting.YELLOW)));
		player.sendSystemMessage(Component.literal(howTo(player, job)).withStyle(ChatFormatting.GRAY));
		ModSounds.play(player, ModSounds.NEWS_COO, 0.5f);
		return null;
	}

	/** What to do next, in one line. */
	private static String howTo(ServerPlayer player, SideJob job) {
		String where = job.hasPlace()
				? " Head about " + distance(player.blockPosition(), job.target()) + " blocks " + JobBoard.direction(player.blockPosition(), job.target())
						+ ", to around " + job.target().getX() + ", " + job.target().getZ() + "."
				: "";
		return switch (job.kind()) {
			case "FETCH" -> "Bring them to " + job.giverName() + " in " + job.town() + ".";
			case "CULL_PIRATES", "CULL_MONSTERS" -> "Anywhere counts. Then go back to " + job.giverName() + " in " + job.town() + ".";
			case "LOST" -> "It was lost somewhere out there." + where + " Bring it back to " + job.giverName() + ".";
			default -> "The target is hiding out." + where + " They'll show up when you get close.";
		};
	}

	// ---- Progress and handing in ----

	private static boolean ready(ServerPlayer player, SideJob job) {
		return switch (job.kind()) {
			case "FETCH" -> player.getInventory().countItem(CharacterData.item(job.item())) >= job.count();
			case "CULL_PIRATES", "CULL_MONSTERS" -> job.progress() >= job.count();
			case "LOST" -> count(player, stack -> isKeepsake(stack, job)) > 0;
			default -> false;
		};
	}

	private static String progressText(ServerPlayer player, SideJob job) {
		return switch (job.kind()) {
			case "FETCH" -> "You have " + Math.min(job.count(), player.getInventory().countItem(CharacterData.item(job.item()))) + "/" + job.count();
			case "CULL_PIRATES", "CULL_MONSTERS" -> Math.min(job.progress(), job.count()) + "/" + job.count() + " beaten";
			case "LOST" -> job.progress() == 0 ? "Not found yet" : "It's lying out there in a barrel";
			default -> "Still at large";
		};
	}

	private static void handIn(ServerPlayer player, TownsfolkEntity person, SideJob job) {
		if ("FETCH".equals(job.kind())) {
			remove(player, stack -> stack.is(CharacterData.item(job.item())), job.count());
		} else if ("LOST".equals(job.kind())) {
			remove(player, stack -> isKeepsake(stack, job), 1);
		}
		person.say(player, switch (job.kind()) {
			case "FETCH" -> "That's exactly what I needed! Thank you!";
			case "LOST" -> "You found it! I thought it was gone forever...";
			default -> "They won't bother us again. You're a hero!";
		});
		player.removeAttached(JOB);
		pay(player, job, "requests");
	}

	private static void pay(ServerPlayer player, SideJob job, String key) {
		ItemStack berries = new ItemStack(CharacterFeature.BERRY, job.berries());
		if (!player.getInventory().add(berries)) {
			player.drop(berries, false, Prediction.SERVER_ONLY);
		}
		player.sendSystemMessage(Component.literal("+" + job.berries() + " Berries").withStyle(ChatFormatting.GOLD));
		StatTraining.addXp(player, job.berries(), true);
		ModSounds.play(player, ModSounds.QUEST_COMPLETE, 0.8f);

		Map<String, Integer> done = new HashMap<>(player.getAttachedOrElse(DONE, Map.of()));
		int total = done.getOrDefault(key, 0) + 1;
		done.put(key, total);
		player.setAttached(DONE, done);
		if ("contracts".equals(key)) {
			com.onepiecemod.advancement.AdvancementFeature.grant(player, "pirate/wanted_contract");
			int bonus = switch (total) {
				case 5 -> 40;
				case 15 -> 100;
				case 30 -> 200;
				default -> 0;
			};
			if (total == 15) {
				com.onepiecemod.advancement.AdvancementFeature.grant(player, "pirate/pirate_hunter");
			}
			if (bonus > 0) {
				player.sendSystemMessage(Component.literal("Contracts done: " + total + ". People now call you a " + hunterRank(total)
						+ "! The bars chip in " + bonus + " Berries.").withStyle(ChatFormatting.LIGHT_PURPLE));
				player.getInventory().add(new ItemStack(CharacterFeature.BERRY, bonus));
			}
		} else {
			com.onepiecemod.advancement.AdvancementFeature.grant(player, "pirate/town_helper");
			if (total == 20) {
				com.onepiecemod.advancement.AdvancementFeature.grant(player, "pirate/friend_of_the_towns");
			}
		}
	}

	static String hunterRank(int contracts) {
		if (contracts >= 30) {
			return "Pirate Hunter";
		}
		if (contracts >= 15) {
			return "Famous Bounty Hunter";
		}
		if (contracts >= 5) {
			return "Bounty Hunter";
		}
		return contracts >= 1 ? "Rookie Bounty Hunter" : "nobody (yet)";
	}

	private static boolean isKeepsake(ItemStack stack, SideJob job) {
		CustomData data = stack.get(DataComponents.CUSTOM_DATA);
		return data != null && job.id().equals(data.copyTag().getStringOr("onepiece_job", ""));
	}

	private static int count(ServerPlayer player, Predicate<ItemStack> test) {
		int total = 0;
		for (int i = 0; i < player.getInventory().getContainerSize(); i++) {
			ItemStack stack = player.getInventory().getItem(i);
			if (!stack.isEmpty() && test.test(stack)) {
				total += stack.getCount();
			}
		}
		return total;
	}

	private static void remove(ServerPlayer player, Predicate<ItemStack> test, int amount) {
		for (int i = 0; i < player.getInventory().getContainerSize() && amount > 0; i++) {
			ItemStack stack = player.getInventory().getItem(i);
			if (!stack.isEmpty() && test.test(stack)) {
				int take = Math.min(amount, stack.getCount());
				stack.shrink(take);
				amount -= take;
			}
		}
		player.getInventory().setChanged();
	}

	// ---- Kills ----

	private static void onDeath(LivingEntity entity, DamageSource source) {
		if (!(entity.level() instanceof ServerLevel level)) {
			return;
		}
		if (entity.entityTags().contains(BOSS_TAG)) {
			for (ServerPlayer player : level.getServer().getPlayerList().getPlayers()) {
				SideJob job = job(player);
				if (job != null && entity.entityTags().contains(TAG + "_" + job.id())) {
					contractDone(player, job);
				}
			}
			return;
		}
		if (!(source.getEntity() instanceof ServerPlayer player)) {
			return;
		}
		SideJob job = job(player);
		if (job == null || job.progress() >= job.count()) {
			return;
		}
		boolean counts = switch (job.kind()) {
			case "CULL_PIRATES" -> entity instanceof HumanNpc npc && !npc.isMarineSide() || entity instanceof BountyHunterEntity;
			case "CULL_MONSTERS" -> entity instanceof Enemy && !(entity instanceof HumanNpc);
			default -> false;
		};
		if (!counts) {
			return;
		}
		SideJob next = job.withProgress(job.progress() + 1);
		player.setAttached(JOB, next);
		if (next.progress() >= next.count()) {
			player.sendSystemMessage(Component.literal("[Request] Done! Go back to " + job.giverName() + " in " + job.town() + " to get paid.")
					.withStyle(ChatFormatting.GREEN));
		} else {
			player.sendOverlayMessage(Component.literal(job.title() + ": " + next.progress() + "/" + next.count()).withStyle(ChatFormatting.GOLD));
		}
	}

	private static void contractDone(ServerPlayer player, SideJob job) {
		String target = job.title().replace("Wanted: ", "");
		player.removeAttached(JOB);
		LIVE.remove(player.getUUID());
		player.sendSystemMessage(Component.literal("[Wanted] ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(target + " is down! The contract is yours.").withStyle(ChatFormatting.GREEN)));
		if (job.bounty() > 0) {
			Bounty.raise(player, job.bounty() / 20, "Took down " + target, false);
		}
		pay(player, job, "contracts");
	}

	// ---- Every second ----

	private static void tick(MinecraftServer server) {
		if (server.getTickCount() % 20 != 0) {
			return;
		}
		long now = server.overworld().getGameTime();
		OFFERS.values().removeIf(offer -> offer.until < now);
		if (CALLED.size() > 4000) {
			CALLED.clear();
		}
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			if (player.isSpectator() || player.level().dimension() != Level.OVERWORLD) {
				continue;
			}
			SideJob job = job(player);
			if (job == null) {
				callOut(player, now);
				continue;
			}
			if (job.isContract()) {
				tickContract(player, job, server.getTickCount());
			} else if ("LOST".equals(job.kind()) && job.progress() == 0) {
				tickLost(player, job, server.getTickCount());
			}
		}
	}

	/** A townsperson who needs help calls out to a player walking past (at most once a minute). */
	private static void callOut(ServerPlayer player, long now) {
		if (now < NEXT_CALL.getOrDefault(player.getUUID(), 0L) || OFFERS.containsKey(player.getUUID())) {
			return;
		}
		ServerLevel level = (ServerLevel) player.level();
		long day = level.getOverworldClockTime() / 24000L;
		for (TownsfolkEntity person : level.getEntitiesOfClass(TownsfolkEntity.class, player.getBoundingBox().inflate(7.0),
				person -> person.isAlive() && !person.isSleeping())) {
			String key = player.getUUID() + " " + person.getUUID() + " " + day;
			if (!needy(person) || CALLED.contains(key)) {
				continue;
			}
			CALLED.add(key);
			NEXT_CALL.put(player.getUUID(), now + 20 * 60);
			person.say(player, JobBoard.postsContracts(person.jobId())
					? "Hey, you! Looking for work? I hear things... come talk to me."
					: "Excuse me! Could you help me with something? Come talk to me!");
			return;
		}
	}

	private static void tickLost(ServerPlayer player, SideJob job, int tick) {
		ServerLevel level = (ServerLevel) player.level();
		int distance = distance(player.blockPosition(), job.target());
		if (distance > LOST_DISTANCE) {
			hint(player, job, distance, tick);
			return;
		}
		BlockPos spot = groundNear(level, job.target(), 10, player.getRandom());
		if (spot == null) {
			spot = groundNear(level, player.blockPosition(), 8, player.getRandom());
		}
		if (spot == null) {
			return;
		}
		level.setBlockAndUpdate(spot, Blocks.BARREL.defaultBlockState());
		if (level.getBlockEntity(spot) instanceof BarrelBlockEntity barrel) {
			ItemStack keepsake = new ItemStack(CharacterData.item(job.item()));
			keepsake.set(DataComponents.CUSTOM_NAME, Component.literal(job.title().replace("Find ", "")).withStyle(ChatFormatting.GOLD));
			CompoundTag tag = new CompoundTag();
			tag.putString("onepiece_job", job.id());
			keepsake.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
			barrel.setItem(13, keepsake);
		}
		player.setAttached(JOB, job.withProgress(1).withTarget(spot));
		player.sendSystemMessage(Component.literal("[Request] There! An overturned barrel at " + spot.getX() + ", " + spot.getY() + ", " + spot.getZ()
				+ ". It must be in there.").withStyle(ChatFormatting.YELLOW));
	}

	private static void tickContract(ServerPlayer player, SideJob job, int tick) {
		ServerLevel level = (ServerLevel) player.level();
		Live live = LIVE.get(player.getUUID());
		if (live != null && !live.jobId.equals(job.id())) {
			discard(live);
			LIVE.remove(player.getUUID());
			live = null;
		}
		int distance = distance(player.blockPosition(), job.target());
		if (live != null) {
			Mob boss = live.mobs.get(0);
			boolean far = player.blockPosition().distSqr(boss.blockPosition()) > FORGET_DISTANCE * FORGET_DISTANCE;
			if (far || (boss.isRemoved() && !boss.isDeadOrDying()) || boss.level() != level) {
				// You left (or the target vanished): they'll be waiting when you come back.
				discard(live);
				LIVE.remove(player.getUUID());
			}
			return;
		}
		if (distance > SPAWN_DISTANCE) {
			hint(player, job, distance, tick);
			return;
		}
		if (level.getDifficulty() == Difficulty.PEACEFUL) {
			if (tick % 200 == 0) {
				player.sendOverlayMessage(Component.literal("Nobody's here on Peaceful. Wanted targets only show up on Easy or harder.")
						.withStyle(ChatFormatting.GRAY));
			}
			return;
		}
		if (!level.hasChunkAt(job.target())) {
			return; // Wait until the hideout's own chunk is loaded before deciding it's all sea.
		}
		BlockPos spot = groundNear(level, job.target(), 24, player.getRandom());
		boolean cameOut = false;
		if (spot == null) {
			spot = groundNear(level, player.blockPosition(), 20, player.getRandom());
			cameOut = true;
		}
		if (spot == null) {
			return; // Out at sea with no land around: try again in a second.
		}
		List<Mob> mobs = spawnTargets(level, player, job, spot);
		if (mobs.isEmpty()) {
			return;
		}
		LIVE.put(player.getUUID(), new Live(job.id(), mobs));
		player.setAttached(JOB, job.withTarget(spot));
		ModSounds.play(player, ModSounds.NEWS_COO, 0.8f);
		String target = job.title().replace("Wanted: ", "");
		player.sendSystemMessage(Component.literal("[Wanted] ").withStyle(ChatFormatting.GOLD).append(Component.literal(
				(cameOut ? target + " spotted you and came out to fight!" : "Found the hideout! " + target + " is here.")
						+ (mobs.size() > 1 ? " Beat the leader to claim the bounty." : "")).withStyle(ChatFormatting.RED)));
	}

	/** Shows where to go, every 10 seconds, above the hotbar. */
	private static void hint(ServerPlayer player, SideJob job, int distance, int tick) {
		if (tick % 200 != 0) {
			return;
		}
		player.sendOverlayMessage(Component.literal(job.title() + ": " + distance + " blocks " + JobBoard.direction(player.blockPosition(), job.target())
				+ " (" + job.target().getX() + ", " + job.target().getZ() + ")").withStyle(ChatFormatting.GOLD));
	}

	private static List<Mob> spawnTargets(ServerLevel level, ServerPlayer player, SideJob job, BlockPos spot) {
		RandomSource random = player.getRandom();
		int tier = JobBoard.tier(player);
		String target = job.title().replace("Wanted: ", "");
		List<Mob> mobs = new ArrayList<>();
		Mob boss = null;
		switch (job.kind()) {
			case "FRUIT" -> {
				BountyHunterEntity hunter = BountyFeature.BOUNTY_HUNTER.create(level, EntitySpawnReason.EVENT);
				if (hunter != null) {
					hunter.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
					hunter.setup(HunterFruit.random(random, tier + 2), 2 + tier);
					hunter.setCustomName(Component.literal(target + " (" + hunter.getFruit().name() + ")"));
					level.addFreshEntity(hunter);
					boss = hunter;
				}
			}
			case "BEAST" -> {
				var type = Creatures.TYPES.get(job.item());
				Mob beast = type == null ? null : type.create(level, EntitySpawnReason.EVENT);
				if (beast != null) {
					beast.snapTo(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5, random.nextFloat() * 360f, 0);
					scale(beast, 2.5, 1.3);
					beast.setCustomName(Component.literal(target));
					level.addFreshEntity(beast);
					boss = beast;
				}
			}
			default -> {
				HumanNpc captain = NpcFeature.spawn(level, "pirate_captain", spot, random.nextFloat() * 360f);
				if (captain != null) {
					boolean convict = "CONVICT".equals(job.kind());
					scale(captain, (convict ? 4 : 2) + tier, 1.0 + 0.3 * tier);
					captain.setCustomName(Component.literal(target + " (" + Bounty.format(job.bounty()) + ")"));
					boss = captain;
				}
			}
		}
		if (boss == null) {
			return mobs;
		}
		boss.addTag(BOSS_TAG);
		boss.setCustomNameVisible(true);
		mobs.add(boss);
		int crew = switch (job.kind()) {
			case "CREW" -> job.count();
			case "FRUIT" -> tier >= 2 ? 2 : 1;
			default -> 0;
		};
		String[] kits = switch (tier) {
			case 0 -> new String[] {"rookie_pirate"};
			case 1 -> new String[] {"pirate", "pirate_gunner"};
			case 2 -> new String[] {"pirate", "pirate_gunner", "bounty_hunter"};
			default -> new String[] {"headliner", "gifter", "donquixote", "blackbeard_pirate"};
		};
		for (int i = 0; i < crew; i++) {
			BlockPos pos = groundNear(level, spot, 5, random);
			HumanNpc goon = NpcFeature.spawn(level, kits[random.nextInt(kits.length)], pos != null ? pos : spot, random.nextFloat() * 360f);
			if (goon != null) {
				mobs.add(goon);
			}
		}
		for (Mob mob : mobs) {
			mob.addTag(TAG);
			mob.addTag(TAG + "_" + job.id());
			mob.setPersistenceRequired();
			mob.setTarget(player);
		}
		return mobs;
	}

	private static void scale(Mob mob, double health, double damage) {
		var maxHealth = mob.getAttribute(Attributes.MAX_HEALTH);
		if (maxHealth != null) {
			maxHealth.setBaseValue(maxHealth.getBaseValue() * health);
		}
		var attack = mob.getAttribute(Attributes.ATTACK_DAMAGE);
		if (attack != null) {
			attack.setBaseValue(attack.getBaseValue() * damage);
		}
		mob.setHealth(mob.getMaxHealth());
	}

	private static void discard(Live live) {
		for (Mob mob : live.mobs) {
			if (mob.isAlive()) {
				mob.discard();
			}
		}
	}

	/** Dry, solid ground within radius of a spot (any height). Null if there's none in loaded chunks. */
	@Nullable
	private static BlockPos groundNear(ServerLevel level, BlockPos around, int radius, RandomSource random) {
		for (int attempt = 0; attempt < 30; attempt++) {
			int x = around.getX() + (attempt == 0 ? 0 : random.nextInt(radius * 2 + 1) - radius);
			int z = around.getZ() + (attempt == 0 ? 0 : random.nextInt(radius * 2 + 1) - radius);
			if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
				continue;
			}
			BlockPos pos = new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z);
			if (level.getBlockState(pos.below()).isSolid() && level.getFluidState(pos).isEmpty()
					&& level.getFluidState(pos.below()).isEmpty() && level.getBlockState(pos.above()).isAir()) {
				return pos;
			}
		}
		return null;
	}

	private static int distance(BlockPos a, BlockPos b) {
		double dx = a.getX() - b.getX();
		double dz = a.getZ() - b.getZ();
		return (int) Math.round(Math.sqrt(dx * dx + dz * dz));
	}

	// ---- /jobs ----

	private static void registerCommands() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("jobs")
						.executes(context -> {
							show(context.getSource().getPlayerOrException());
							return 1;
						})
						.then(Commands.literal("accept").executes(context -> {
							ServerPlayer player = context.getSource().getPlayerOrException();
							String error = accept(player);
							if (error != null) {
								player.sendSystemMessage(Component.literal(error).withStyle(ChatFormatting.GRAY));
							}
							return error == null ? 1 : 0;
						}))
						.then(Commands.literal("decline").executes(context -> {
							ServerPlayer player = context.getSource().getPlayerOrException();
							OFFERS.remove(player.getUUID());
							player.sendSystemMessage(Component.literal("Maybe another time.").withStyle(ChatFormatting.GRAY));
							return 1;
						}))
						.then(Commands.literal("abandon").executes(context -> {
							ServerPlayer player = context.getSource().getPlayerOrException();
							SideJob job = job(player);
							if (job == null) {
								player.sendSystemMessage(Component.literal("You don't have a job.").withStyle(ChatFormatting.GRAY));
								return 0;
							}
							player.removeAttached(JOB);
							Live live = LIVE.remove(player.getUUID());
							if (live != null) {
								discard(live);
							}
							player.sendSystemMessage(Component.literal("You gave up on: " + job.title()).withStyle(ChatFormatting.GRAY));
							return 1;
						}))
						// For testing: talk to the nearest townsperson as if right-clicking them (operators only).
						.then(Commands.literal("talk").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS)).executes(context -> {
							ServerPlayer player = context.getSource().getPlayerOrException();
							List<TownsfolkEntity> near = player.level().getEntitiesOfClass(TownsfolkEntity.class,
									player.getBoundingBox().inflate(16.0), e -> e.isAlive());
							if (near.isEmpty()) {
								return 0;
							}
							near.sort(java.util.Comparator.comparingDouble(player::distanceToSqr));
							return onTalk(player, near.get(0)) ? 1 : 0;
						}))
						// For testing: an offer from the nearest townsperson (operators only).
						.then(Commands.literal("offer").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.literal("request").executes(context -> testOffer(context.getSource().getPlayerOrException(), false)))
								.then(Commands.literal("contract").executes(context -> testOffer(context.getSource().getPlayerOrException(), true))))));
	}

	private static int testOffer(ServerPlayer player, boolean contract) {
		List<TownsfolkEntity> near = player.level().getEntitiesOfClass(TownsfolkEntity.class, player.getBoundingBox().inflate(16.0), e -> e.isAlive());
		if (near.isEmpty()) {
			player.sendSystemMessage(Component.literal("Stand near a townsperson (/town spawn <job>).").withStyle(ChatFormatting.RED));
			return 0;
		}
		TownsfolkEntity person = near.get(0);
		SideJob job = contract ? JobBoard.contract(player, person, townName(person), player.getRandom())
				: JobBoard.request(player, person, townName(person), player.getRandom());
		OFFERS.put(player.getUUID(), new Offer(job, person.getUUID(), player.level().getGameTime() + 20 * 120));
		player.sendSystemMessage(Component.literal("Test offer: " + job.title() + " (" + job.kind() + "). /jobs accept to take it.")
				.withStyle(ChatFormatting.AQUA));
		return 1;
	}

	private static void show(ServerPlayer player) {
		SideJob job = job(player);
		player.sendSystemMessage(Component.literal("=== Side jobs (" + JobBoard.tierName(JobBoard.tier(player)) + " jobs) ===").withStyle(ChatFormatting.GOLD));
		if (job == null) {
			player.sendSystemMessage(Component.literal("No job right now. Townsfolk who need help call out to you as you walk by. "
					+ "Bartenders, sailors and foreign traders know about Wanted pirates.").withStyle(ChatFormatting.GRAY));
		} else {
			player.sendSystemMessage(Component.literal(job.title()).withStyle(ChatFormatting.YELLOW)
					.append(Component.literal(" (from " + job.giverName() + ", " + job.town() + ")").withStyle(ChatFormatting.GRAY)));
			player.sendSystemMessage(Component.literal(progressText(player, job) + ". " + howTo(player, job)).withStyle(ChatFormatting.WHITE));
			player.sendSystemMessage(Component.literal("Reward: " + job.berries() + " Berries. ").withStyle(ChatFormatting.GOLD)
					.append(Component.literal("[Give up]").withStyle(Style.EMPTY.withColor(ChatFormatting.RED)
							.withClickEvent(new ClickEvent.RunCommand("/jobs abandon")))));
		}
		int contracts = done(player, "contracts");
		player.sendSystemMessage(Component.literal("Town requests done: " + done(player, "requests") + ". Contracts done: " + contracts
				+ " (" + hunterRank(contracts) + ").").withStyle(ChatFormatting.GRAY));
	}
}
