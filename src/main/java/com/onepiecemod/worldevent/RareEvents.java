package com.onepiecemod.worldevent;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import org.jetbrains.annotations.Nullable;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetActionBarTextPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.resource.Resources;
import com.onepiecemod.sea.CalmBelt;
import com.onepiecemod.season.Season;
import com.onepiecemod.season.Seasons;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.shipcombat.NavalBattles;
import com.onepiecemod.shipcombat.ShipBrain;
import com.onepiecemod.weather.SeaEventType;
import com.onepiecemod.weather.SeaEvents;

/**
 * Rare world events: once in a while (about one every three or four in-game days) something big happens near one of
 * the players, and News Coo tells the whole world about it.
 *
 *  - Buster Call raid: the World Government makes an example of a wanted pirate (bounty 30,000,000+) and orders a
 *    Buster Call on the island they're standing on, whether they caused trouble there or not (see IslandBusterCall).
 *  - Meteor shower: Admiral Fujitora "prays" at the sky. Burning stones fall around you for half a minute, blow
 *    craters (rebuilt 10 minutes later, like a Buster Call's) and leave meteorite ore to dig out of the wreck.
 *  - Treasure convoy: a World Government fleet escorts a Royal Galleon full of tribute past your ship (see MarineFleets).
 *  - Pirate armada: a big pirate fleet comes for your ship (see NavalBattles).
 *  - Great Cyclone: a giant drifting storm crosses your course (see weather.SeaEvents). Three times as likely in autumn.
 *
 * Operators: /worldevent rare [id], /worldevent rare status.
 */
public class RareEvents {
	// ---- Tune these ----
	/** Chance each in-game morning that a rare event happens somewhere. */
	private static final float DAILY_CHANCE = 0.3f;
	/** At least this many days between rare events, and none in a new world's first days. */
	private static final int MIN_DAYS_BETWEEN = 2;
	private static final int FIRST_DAY = 2;
	private static final long BUSTER_CALL_BOUNTY = 30_000_000L;

	public enum Kind {
		BUSTER_CALL("buster_call", 2), METEOR_SHOWER("meteor_shower", 3), TREASURE_CONVOY("treasure_convoy", 3),
		PIRATE_ARMADA("pirate_armada", 2), GREAT_CYCLONE("great_cyclone", 2);

		public final String id;
		final int weight;

		Kind(String id, int weight) {
			this.id = id;
			this.weight = weight;
		}

		@Nullable
		static Kind byId(String id) {
			for (Kind kind : values()) {
				if (kind.id.equals(id)) {
					return kind;
				}
			}
			return null;
		}
	}

	private static long lastCheckedDay = -1;
	private static long lastEventDay = -100;
	private static String lastEvent = "none yet";
	private static final List<MeteorShower> SHOWERS = new ArrayList<>();

	static void tick(MinecraftServer server) {
		ServerLevel level = server.overworld();
		for (Iterator<MeteorShower> it = SHOWERS.iterator(); it.hasNext(); ) {
			if (!it.next().tick()) {
				it.remove();
			}
		}
		if (server.getTickCount() % 100 != 0) {
			return;
		}
		long day = level.getOverworldClockTime() / 24000L;
		if (lastCheckedDay < 0) {
			lastCheckedDay = day; // Just started: wait for the next morning, so restarting never triggers one.
			return;
		}
		if (day == lastCheckedDay) {
			return;
		}
		lastCheckedDay = day;
		if (day < FIRST_DAY || day - lastEventDay < MIN_DAYS_BETWEEN || level.getRandom().nextFloat() >= DAILY_CHANCE) {
			return;
		}
		List<ServerPlayer> players = new ArrayList<>(level.players().stream().filter(p -> !p.isSpectator() && !p.isCreative()).toList());
		Collections.shuffle(players, new java.util.Random(level.getRandom().nextLong()));
		for (ServerPlayer player : players) {
			if (startRandom(player) == null) {
				return;
			}
		}
	}

	static void stopAll() {
		for (MeteorShower shower : SHOWERS) {
			shower.ruins.ifPresent(live -> Ruins.close(live, shower.level.getGameTime()));
		}
		SHOWERS.clear();
		lastCheckedDay = -1;
	}

	/** Tries the events in a weighted random order until one fits this player. Null if one started, or why none could. */
	@Nullable
	static String startRandom(ServerPlayer player) {
		RandomSource random = player.getRandom();
		Season season = Seasons.seasonAt(player.level(), player.blockPosition());
		List<Kind> bag = new ArrayList<>();
		for (Kind kind : Kind.values()) {
			int weight = kind.weight * (kind == Kind.GREAT_CYCLONE && season == Season.AUTUMN ? 3 : 1);
			for (int i = 0; i < weight; i++) {
				bag.add(kind);
			}
		}
		Collections.shuffle(bag, new java.util.Random(random.nextLong()));
		Set<Kind> tried = new HashSet<>();
		String why = "Nothing fits here.";
		for (Kind kind : bag) {
			if (tried.add(kind)) {
				String problem = start(player, kind);
				if (problem == null) {
					return null;
				}
				why = problem;
			}
		}
		return why;
	}

	/** Starts one event near this player. Null if it worked, otherwise why it can't happen here. */
	@Nullable
	static String start(ServerPlayer player, Kind kind) {
		if (!(player.level() instanceof ServerLevel level) || level.dimension() != Level.OVERWORLD) {
			return "Rare events only happen in the Overworld.";
		}
		MinecraftServer server = level.getServer();
		ShipEntity ship = ShipEntity.aboard(player) instanceof ShipEntity s ? s : null;
		CalmBelt.Sea sea = CalmBelt.seaAt(level, player.blockPosition());
		String name = player.getName().getString();
		String problem;
		switch (kind) {
			case BUSTER_CALL -> {
				if (Bounty.get(player) < BUSTER_CALL_BOUNTY) {
					return "A surprise Buster Call needs a bounty of 30,000,000 or more.";
				}
				IslandTrouble.Spot spot = IslandTrouble.islandAt(level, player.blockPosition(), true);
				if (spot == null || spot.center == null) {
					return "A Buster Call needs you to be on an island.";
				}
				if (IslandBusterCall.isRunning(spot.key)) {
					return "A Buster Call is already under way here.";
				}
				WorldNews.report(server, "The Five Elders have had enough of " + name + ". Marine HQ is sending a fleet to make an example of them!",
						ChatFormatting.DARK_RED);
				IslandBusterCall.start(level, spot, player);
				problem = null;
			}
			case METEOR_SHOWER -> {
				if (!level.canSeeSky(player.blockPosition())) {
					return "A meteor shower needs open sky.";
				}
				SHOWERS.add(new MeteorShower(level, player));
				WorldNews.report(server, "Admiral Fujitora was seen near " + name + ", praying at the sky... Witnesses say the stars began to fall!",
						ChatFormatting.LIGHT_PURPLE);
				player.sendSystemMessage(Component.literal("The sky is glowing red. Falling stars are coming! Get under cover, or watch where they land: "
						+ "meteorites hold rare ore.").withStyle(ChatFormatting.RED, ChatFormatting.BOLD));
				problem = null;
			}
			case TREASURE_CONVOY -> {
				if (ship == null || sea == null) {
					return "A treasure convoy only sails past ships at sea.";
				}
				problem = MarineFleets.send(level, player, true);
				if (problem == null) {
					WorldNews.report(server, "A World Government treasure convoy is carrying the kingdoms' tribute to Mary Geoise, through the waters near "
							+ name + ". Any pirate who touches it will pay dearly!", ChatFormatting.LIGHT_PURPLE);
				}
			}
			case PIRATE_ARMADA -> {
				if (ship == null || sea == null || !sea.grandLine()) {
					return "A pirate armada only hunts ships on the Grand Line.";
				}
				if (NavalBattles.inBattle(player)) {
					return "You're already in a sea battle.";
				}
				int tier = sea == CalmBelt.Sea.NEW_WORLD ? 4 : 3;
				ShipEntity flagship = NavalBattles.start(level, player, player.position(), ship.getYRot(), 90, ShipBrain.Faction.PIRATE, tier);
				if (flagship == null) {
					return "No open sea for an armada around here.";
				}
				WorldNews.report(server, "A great pirate armada led by the " + flagship.getName().getString() + " is raiding ships on the Grand Line. "
						+ "Its latest target: " + name + "!", ChatFormatting.RED);
				problem = null;
			}
			case GREAT_CYCLONE -> {
				if (ship == null || sea == null) {
					return "A Great Cyclone only comes for ships out at sea.";
				}
				problem = SeaEvents.start(level, SeaEventType.CYCLONE, player);
				if (problem == null) {
					WorldNews.report(server, "Weather birds warn sailors: a GREAT CYCLONE is crossing the sea near " + name + ". All ships, find harbour!",
							ChatFormatting.DARK_PURPLE);
				}
			}
			default -> problem = "Unknown event.";
		}
		if (problem == null) {
			lastEventDay = level.getOverworldClockTime() / 24000L;
			lastEvent = kind.id + " near " + name + " on day " + (lastEventDay + 1);
		}
		return problem;
	}

	// ---- Commands (added under /worldevent by WorldEvents) ----

	static LiteralArgumentBuilder<CommandSourceStack> command() {
		return Commands.literal("rare")
				.executes(context -> reply(context.getSource(), startRandom(context.getSource().getPlayerOrException()), "A rare event begins."))
				.then(Commands.literal("status").executes(context -> {
					long day = context.getSource().getServer().overworld().getOverworldClockTime() / 24000L;
					long wait = Math.max(0, lastEventDay + MIN_DAYS_BETWEEN - day);
					context.getSource().sendSuccess(() -> Component.literal("Last rare event: " + lastEvent + ". "
							+ (wait > 0 ? "None for another " + wait + " day(s)." : "Each morning there's a " + Math.round(DAILY_CHANCE * 100) + "% chance."))
							.withStyle(ChatFormatting.GOLD), false);
					return 1;
				}))
				.then(Commands.argument("id", StringArgumentType.word())
						.suggests((context, builder) -> SharedSuggestionProvider.suggest(
								java.util.Arrays.stream(Kind.values()).map(k -> k.id), builder))
						.executes(context -> {
							Kind kind = Kind.byId(StringArgumentType.getString(context, "id"));
							if (kind == null) {
								return reply(context.getSource(), "Events: buster_call, meteor_shower, treasure_convoy, pirate_armada, great_cyclone", "");
							}
							return reply(context.getSource(), start(context.getSource().getPlayerOrException(), kind), "Started: " + kind.id);
						}));
	}

	private static int reply(CommandSourceStack source, @Nullable String error, String ok) {
		if (error != null) {
			source.sendFailure(Component.literal(error));
			return 0;
		}
		source.sendSuccess(() -> Component.literal(ok).withStyle(ChatFormatting.GOLD), true);
		return 1;
	}

	// ------------------------------------------------------------------------------------------

	/** Fujitora's meteor shower: a warning, then a burning stone every few seconds around where it began. */
	private static class MeteorShower {
		private static final int WARNING = 20 * 15;
		private static final int EVERY = 20 * 5;
		private static final int FALL_TICKS = 40;
		private static final int COUNT = 6;

		final ServerLevel level;
		final Vec3 center;
		final UUID target;
		final long startTime;
		final List<Meteor> falling = new ArrayList<>();
		final Set<UUID> witnesses = new HashSet<>();
		java.util.Optional<Ruins.Live> ruins = java.util.Optional.empty();
		int launched;

		MeteorShower(ServerLevel level, ServerPlayer player) {
			this.level = level;
			this.center = player.position();
			this.target = player.getUUID();
			this.startTime = level.getGameTime();
		}

		/** False when it's over. */
		boolean tick() {
			long age = level.getGameTime() - startTime;
			RandomSource random = level.getRandom();
			if (age < WARNING) {
				// A red glow and sparks high up.
				if (age % 10 == 0) {
					level.sendParticles(ParticleTypes.LAVA, center.x, center.y + 50, center.z, 6, 30, 4, 30, 0);
				}
				return true;
			}
			if (launched < COUNT && (age - WARNING) % EVERY == 0) {
				launched++;
				launch(random);
			}
			for (Iterator<Meteor> it = falling.iterator(); it.hasNext(); ) {
				Meteor meteor = it.next();
				if (!meteor.tick()) {
					impact(meteor, random);
					it.remove();
				}
			}
			if (launched >= COUNT && falling.isEmpty()) {
				finish();
				return false;
			}
			return true;
		}

		private void launch(RandomSource random) {
			// Aim at the player's area: 8 to 48 blocks from them, never right on top of them.
			ServerPlayer player = level.getServer().getPlayerList().getPlayer(target);
			Vec3 around = player != null && player.level() == level && player.position().distanceTo(center) < 150 ? player.position() : center;
			// Stars like to fall on land (where you can dig the ore out): try a few spots, take the sea only if there's no land.
			Vec3 land = null;
			for (int attempt = 0; attempt < 12; attempt++) {
				double angle = random.nextDouble() * Mth.TWO_PI;
				double distance = 8 + random.nextDouble() * 40;
				int x = Mth.floor(around.x + Math.cos(angle) * distance);
				int z = Mth.floor(around.z + Math.sin(angle) * distance);
				if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
					continue;
				}
				int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
				land = new Vec3(x + 0.5, y, z + 0.5);
				if (level.getFluidState(new BlockPos(x, y - 1, z)).isEmpty()) {
					break;
				}
			}
			if (land == null) {
				return;
			}
			double from = random.nextDouble() * Mth.TWO_PI;
			Vec3 sky = land.add(Math.cos(from) * 35, 80, Math.sin(from) * 35);
			falling.add(new Meteor(sky, land));
			level.playSound(null, sky.x, land.y + 20, sky.z, SoundEvents.FIRECHARGE_USE, SoundSource.WEATHER, 6.0f, 0.4f);
		}

		private void impact(Meteor meteor, RandomSource random) {
			Vec3 at = meteor.land;
			BlockPos pos = BlockPos.containing(at);
			level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, at.x, at.y + 1, at.z, 1, 0, 0, 0, 0);
			level.sendParticles(ParticleTypes.LAVA, at.x, at.y + 1, at.z, 40, 2, 1, 2, 0.5);
			level.sendParticles(ParticleTypes.LARGE_SMOKE, at.x, at.y + 2, at.z, 60, 3, 2, 3, 0.05);
			level.playSound(null, pos, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.WEATHER, 8.0f, 0.6f);

			// Hurts anything close, and sets it on fire.
			for (LivingEntity living : level.getEntitiesOfClass(LivingEntity.class, new AABB(pos).inflate(6))) {
				double d = living.position().distanceTo(at);
				if (d < 6) {
					living.hurtServer(level, level.damageSources().inFire(), (float) (12 * (1 - d / 6)));
					living.igniteForSeconds(4);
				}
			}
			for (ServerPlayer player : level.players()) {
				if (player.position().distanceTo(at) < 48) {
					witnesses.add(player.getUUID());
				}
			}

			// A crater on land (written down, rebuilt later). In the sea it's just a huge splash.
			if (level.getFluidState(pos.below()).isEmpty()) {
				if (ruins.isEmpty()) {
					IslandTrouble.Spot spot = IslandTrouble.islandAt(level, pos, true);
					ruins = java.util.Optional.of(Ruins.open(spot != null ? spot.key : level.getBiome(pos).unwrapKey()
							.map(k -> k.identifier().toString()).orElse("minecraft:plains") + "@" + pos.getX() + "," + pos.getZ()));
					ruins.get().cause = "meteor shower";
				}
				Ruins.crater(level, ruins.get(), pos.below(), 3 + random.nextInt(2), random);
				dropMeteorite(at.add(0, -1, 0), random);
			} else {
				level.sendParticles(ParticleTypes.SPLASH, at.x, at.y + 1, at.z, 120, 3, 1, 3, 0.6);
			}
		}

		private void dropMeteorite(Vec3 at, RandomSource random) {
			List<ItemStack> loot = new ArrayList<>();
			loot.add(new ItemStack(Items.RAW_IRON, 2 + random.nextInt(4)));
			loot.add(new ItemStack(Items.GOLD_NUGGET, 4 + random.nextInt(8)));
			if (random.nextFloat() < 0.5f) {
				loot.add(new ItemStack(Resources.RAW_KOKUTO, 1 + random.nextInt(2)));
			}
			if (random.nextFloat() < 0.3f) {
				loot.add(new ItemStack(Items.AMETHYST_SHARD, 2 + random.nextInt(4)));
			}
			if (random.nextFloat() < 0.2f) {
				loot.add(new ItemStack(Items.DIAMOND));
			}
			if (random.nextFloat() < 0.06f) {
				loot.add(new ItemStack(Items.NETHERITE_SCRAP));
			}
			for (ItemStack stack : loot) {
				ItemEntity drop = new ItemEntity(level, at.x, at.y, at.z, stack);
				drop.setDeltaMovement((random.nextDouble() - 0.5) * 0.3, 0.3, (random.nextDouble() - 0.5) * 0.3);
				level.addFreshEntity(drop);
			}
		}

		private void finish() {
			ruins.ifPresent(live -> Ruins.close(live, level.getGameTime()));
			for (UUID id : witnesses) {
				ServerPlayer player = level.getServer().getPlayerList().getPlayer(id);
				if (player != null) {
					com.onepiecemod.advancement.AdvancementFeature.grant(player, "journey/falling_star");
					player.connection.send(new ClientboundSetActionBarTextPacket(Component.literal("The stars stop falling. The craters will mend in 10 minutes.")
							.withStyle(ChatFormatting.LIGHT_PURPLE)));
				}
			}
		}

		/** One falling stone: a streak of fire from the sky to the ground. */
		private class Meteor {
			final Vec3 sky;
			final Vec3 land;
			int age;

			Meteor(Vec3 sky, Vec3 land) {
				this.sky = sky;
				this.land = land;
			}

			/** False when it hits. */
			boolean tick() {
				age++;
				double t = Math.min(1, age / (double) FALL_TICKS);
				Vec3 now = sky.lerp(land, t * t); // Speeding up as it falls.
				level.sendParticles(ParticleTypes.FLAME, now.x, now.y, now.z, 12, 0.6, 0.6, 0.6, 0.02);
				level.sendParticles(ParticleTypes.LARGE_SMOKE, now.x, now.y, now.z, 6, 0.8, 0.8, 0.8, 0.01);
				level.sendParticles(ParticleTypes.LAVA, now.x, now.y, now.z, 2, 0.4, 0.4, 0.4, 0);
				return age < FALL_TICKS;
			}
		}
	}
}
