package com.onepiecemod.town;

import com.onepiecemod.util.Motion;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import it.unimi.dsi.fastutil.ints.IntArrayList;
import it.unimi.dsi.fastutil.ints.IntList;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.FireworkRocketEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.FireworkExplosion;
import net.minecraft.world.item.component.Fireworks;
import net.minecraft.world.phys.Vec3;

/**
 * Town festivals from towns.json: Wano's Fire Festival, Drum's cherry blossoms, the Harvest Festival in the East Blue,
 * Alabasta's Rain Festival, Totto Land's Tea Party, Whisky Peak's (suspicious) welcome parties, and Water 7's
 * Aqua Laguna, which is not a party at all: the townsfolk hide and big waves sweep the docks.
 *
 * Each festival runs every few in-game days at set hours. While it's on, townsfolk gather and dance on the plaza,
 * there are lights, fireworks and music, the stalls sell festival food, and players who join in get a small gift.
 * Beating a boss for the first time earns you a Victory Banquet in the next town you visit in the evening.
 */
public class Festivals {
	private static final String BANQUET_TAG = "onepiece_banquet_pending";
	private static final String BANQUET = "victory_banquet";
	/** How long a player must stay at a festival before the townsfolk hand them a gift. */
	private static final int GIFT_AFTER = 20 * 45;

	private static final Map<UUID, Long> ARRIVED = new HashMap<>();

	/** The festival going on in this town right now, or null. */
	public static TownData.Festival active(Town town) {
		long gameTime = town.level.getGameTime();
		if (town.forcedFestival != null && gameTime < town.forcedUntil) {
			return TownData.festival(town.forcedFestival);
		}
		if (town.banquetFor != null && gameTime < town.banquetUntil) {
			return TownData.festival(BANQUET);
		}
		TownData.Festival festival = TownData.festival(town.def.festival);
		if (festival == null || festival.every <= 0) {
			return null;
		}
		long dayTime = town.level.getOverworldClockTime();
		long day = dayTime / 24000L;
		long time = dayTime % 24000L;
		boolean today = Math.floorMod(day, festival.every) == Math.floorMod(festival.offset, festival.every);
		return today && time >= festival.start && time < festival.end ? festival : null;
	}

	/** Which festival is next, and in how many days (for /town info). */
	public static String nextFestival(Town town) {
		TownData.Festival festival = TownData.festival(town.def.festival);
		if (festival == null || festival.every <= 0) {
			return "none";
		}
		long day = town.level.getOverworldClockTime() / 24000L;
		long time = town.level.getOverworldClockTime() % 24000L;
		for (int i = 0; i <= festival.every; i++) {
			long d = day + i;
			if (Math.floorMod(d, festival.every) == Math.floorMod(festival.offset, festival.every) && (i > 0 || time < festival.end)) {
				return festival.name + (i == 0 ? " (today)" : " in " + i + " day" + (i == 1 ? "" : "s"));
			}
		}
		return festival.name;
	}

	public static void force(Town town, String festivalId, int ticks) {
		town.forcedFestival = festivalId;
		town.forcedUntil = town.level.getGameTime() + ticks;
	}

	// ---------- Ticking ----------

	static void tick(Town town, ServerLevel level, long gameTime) {
		TownData.Festival festival = active(town);
		String id = festival == null ? null : festival.name + "@" + (level.getOverworldClockTime() / 24000L);
		if (id == null) {
			if (town.lastFestivalId != null) {
				town.lastFestivalId = null;
				town.giftsGiven.clear();
				town.announcedTo.clear();
			}
			if (gameTime % 40 == 0) {
				maybeStartBanquet(town, level);
			}
			return;
		}
		if (!id.equals(town.lastFestivalId)) {
			town.lastFestivalId = id;
			town.giftsGiven.clear();
			town.announcedTo.clear();
		}
		BlockPos plaza = town.plaza;
		boolean playerNear = level.getNearestPlayer(plaza.getX(), plaza.getY(), plaza.getZ(), 128, false) != null;
		if (!playerNear) {
			return;
		}
		if (gameTime % 20 == 0) {
			welcomePlayers(town, festival, level, gameTime);
		}
		RandomSource random = level.getRandom();
		if (gameTime % 4 == 0) {
			effects(town, festival, level, random);
		}
		music(town, festival, level, gameTime);
		if (!festival.fireworks.isEmpty() && gameTime % 50 == 0 && random.nextInt(3) > 0) {
			launchFirework(town, festival, level, random);
		}
		if (festival.hazard && gameTime % 40 == 0) {
			waves(town, level, random);
		}
	}

	private static void welcomePlayers(Town town, TownData.Festival festival, ServerLevel level, long gameTime) {
		for (ServerPlayer player : level.players()) {
			boolean inside = town.contains(player.blockPosition(), 8);
			if (player.blockPosition().closerThan(town.plaza, 160) && town.announcedTo.add(player.getUUID())) {
				String text = String.format(festival.announce, town.name());
				player.sendSystemMessage(Component.literal("[" + festival.name + "] ").withStyle(festival.hazard ? ChatFormatting.DARK_RED : ChatFormatting.LIGHT_PURPLE)
						.append(Component.literal(text).withStyle(festival.hazard ? ChatFormatting.RED : ChatFormatting.GOLD)));
				if (festival.hazard) {
					level.playSound(null, player.blockPosition(), SoundEvents.BELL_BLOCK, SoundSource.AMBIENT, 1.0f, 0.8f);
				}
			}
			if (!inside || festival.hazard) {
				ARRIVED.remove(player.getUUID());
				continue;
			}
			long arrived = ARRIVED.computeIfAbsent(player.getUUID(), k -> gameTime);
			if (gameTime - arrived >= GIFT_AFTER && town.giftsGiven.add(player.getUUID())) {
				giveGifts(player, festival, level);
			}
		}
	}

	private static void giveGifts(ServerPlayer player, TownData.Festival festival, ServerLevel level) {
		for (String spec : festival.gifts) {
			ItemStack stack = TownData.gift(spec);
			if (!stack.isEmpty() && !player.getInventory().add(stack)) {
				player.drop(stack, false, net.minecraft.util.Prediction.SERVER_ONLY);
			}
		}
		if (festival.effect != null && !festival.effect.isEmpty()) {
			BuiltInRegistries.MOB_EFFECT.get(Identifier.parse(festival.effect)).ifPresent(effect -> {
				Holder<MobEffect> holder = effect;
				int seconds = holder.is(net.minecraft.world.effect.MobEffects.NAUSEA) ? 8 : 180;
				player.addEffect(new MobEffectInstance(holder, seconds * 20, 0));
			});
		}
		player.sendSystemMessage(Component.literal("The townsfolk pull you into the " + festival.name + " and press treats into your hands!")
				.withStyle(ChatFormatting.GOLD));
		level.playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.6f, 1.4f);
	}

	private static void effects(Town town, TownData.Festival festival, ServerLevel level, RandomSource random) {
		BlockPos plaza = town.plaza;
		for (String kind : festival.particles) {
			double x = plaza.getX() + 0.5 + (random.nextDouble() - 0.5) * 28;
			double z = plaza.getZ() + 0.5 + (random.nextDouble() - 0.5) * 28;
			double y = plaza.getY() + 1;
			switch (kind) {
				case "flame" -> level.sendParticles(ParticleTypes.FLAME, x, y + 3 + random.nextDouble() * 3, z, 2, 0.1, 0.1, 0.1, 0.01);
				case "lantern" -> level.sendParticles(ParticleTypes.END_ROD, x, y + 2 + random.nextDouble() * 4, z, 1, 0.0, 0.05, 0.0, 0.01);
				case "spark" -> level.sendParticles(ParticleTypes.LAVA, x, y + 1, z, 1, 0.2, 0.0, 0.2, 0.0);
				case "cherry" -> level.sendParticles(ParticleTypes.CHERRY_LEAVES, x, y + 10 + random.nextDouble() * 6, z, 4, 6, 1, 6, 0.0);
				case "snow" -> level.sendParticles(ParticleTypes.SNOWFLAKE, x, y + 8, z, 3, 5, 1, 5, 0.0);
				case "bonfire" -> {
					level.sendParticles(ParticleTypes.FLAME, plaza.getX() + 0.5, y + 0.2, plaza.getZ() + 0.5, 4, 0.3, 0.3, 0.3, 0.02);
					level.sendParticles(ParticleTypes.CAMPFIRE_COSY_SMOKE, plaza.getX() + 0.5, y + 1, plaza.getZ() + 0.5, 1, 0.2, 0.2, 0.2, 0.01);
				}
				case "notes" -> level.sendParticles(ParticleTypes.NOTE, x, y + 1.5, z, 1, 0.3, 0.2, 0.3, 1.0);
				case "confetti" -> level.sendParticles(ParticleTypes.HAPPY_VILLAGER, x, y + 3, z, 4, 1.5, 1.0, 1.5, 0.0);
				case "rain" -> level.sendParticles(ParticleTypes.SPLASH, x, y + 0.2, z, 6, 2, 0.1, 2, 0.0);
				case "wave" -> {
					if (!town.water.isEmpty()) {
						BlockPos water = town.water.get(random.nextInt(town.water.size()));
						level.sendParticles(ParticleTypes.SPLASH, water.getX() + 0.5, water.getY() + 0.5, water.getZ() + 0.5, 20, 1.5, 0.5, 1.5, 0.2);
						level.sendParticles(ParticleTypes.BUBBLE_POP, water.getX() + 0.5, water.getY() + 1, water.getZ() + 0.5, 8, 1.5, 0.5, 1.5, 0.1);
					}
				}
				default -> { }
			}
		}
	}

	/** A little band plays on the plaza: taiko drums for Wano, a fiddle for harbour towns, chimes for blossoms and tea. */
	private static void music(Town town, TownData.Festival festival, ServerLevel level, long gameTime) {
		BlockPos at = town.plaza.above();
		int beat = (int) (gameTime % 64);
		switch (festival.music) {
			case "taiko" -> {
				if (beat % 8 == 0) {
					play(level, at, SoundEvents.NOTE_BLOCK_BASEDRUM.value(), 1.6f, 0.6f);
				} else if (beat % 8 == 4 && beat % 32 != 28) {
					play(level, at, SoundEvents.NOTE_BLOCK_SNARE.value(), 1.0f, 0.8f);
				}
				if (beat == 60) {
					play(level, at, SoundEvents.NOTE_BLOCK_FLUTE.value(), 1.0f, 1.2f);
				}
			}
			case "fiddle" -> {
				int[] tune = {0, 4, 7, 4, 9, 7, 4, 2};
				if (beat % 8 == 0) {
					play(level, at, SoundEvents.NOTE_BLOCK_BANJO.value(), 1.0f, pitch(tune[(beat / 8) % tune.length]));
				}
				if (beat % 16 == 0) {
					play(level, at, SoundEvents.NOTE_BLOCK_BASS.value(), 1.0f, pitch(tune[(beat / 16) % 4]));
				}
			}
			case "chime" -> {
				int[] tune = {7, 9, 12, 9, 7, 4, 2, 4};
				if (beat % 8 == 0) {
					play(level, at, SoundEvents.NOTE_BLOCK_CHIME.value(), 1.0f, pitch(tune[(beat / 8) % tune.length]));
				}
			}
			case "alarm" -> {
				if (beat % 32 == 0) {
					play(level, at, SoundEvents.BELL_BLOCK, 2.0f, 0.9f);
				}
			}
			default -> { }
		}
	}

	private static float pitch(int semitones) {
		return (float) Math.pow(2.0, (semitones - 12) / 12.0);
	}

	private static void play(ServerLevel level, BlockPos at, SoundEvent sound, float volume, float pitch) {
		level.playSound(null, at, sound, SoundSource.RECORDS, volume, pitch);
	}

	private static void launchFirework(Town town, TownData.Festival festival, ServerLevel level, RandomSource random) {
		BlockPos from = town.open.isEmpty() ? town.plaza : town.randomOpenNear(town.plaza, 14, random);
		IntList colors = new IntArrayList();
		colors.add((int) festival.fireworks.get(random.nextInt(festival.fireworks.size())));
		colors.add((int) festival.fireworks.get(random.nextInt(festival.fireworks.size())));
		FireworkExplosion.Shape[] shapes = FireworkExplosion.Shape.values();
		FireworkExplosion explosion = new FireworkExplosion(shapes[random.nextInt(shapes.length)], colors, new IntArrayList(), random.nextBoolean(), true);
		ItemStack rocket = new ItemStack(Items.FIREWORK_ROCKET);
		rocket.set(DataComponents.FIREWORKS, new Fireworks(1 + random.nextInt(2), List.of(explosion)));
		FireworkRocketEntity entity = new FireworkRocketEntity(level, from.getX() + 0.5, from.getY() + 0.5, from.getZ() + 0.5, rocket);
		level.addFreshEntity(entity);
	}

	/** Aqua Laguna: waves crash over the docks and push anyone standing near the water inland. */
	private static void waves(Town town, ServerLevel level, RandomSource random) {
		if (town.water.isEmpty()) {
			return;
		}
		level.playSound(null, town.water.get(random.nextInt(town.water.size())), SoundEvents.GENERIC_SPLASH, SoundSource.AMBIENT, 2.0f, 0.5f);
		for (ServerPlayer player : level.players()) {
			if (!town.contains(player.blockPosition(), 4) || player.isCreative() || player.isSpectator()) {
				continue;
			}
			for (BlockPos water : town.water) {
				if (water.closerThan(player.blockPosition(), 4) && player.getY() <= water.getY() + 2) {
					Vec3 push = Vec3.atCenterOf(town.plaza).subtract(player.position()).normalize().scale(1.2);
					player.push(push.x, 0.4, push.z);
					Motion.sync(player);
					level.sendParticles(ParticleTypes.SPLASH, player.getX(), player.getY() + 1, player.getZ(), 30, 0.6, 0.6, 0.6, 0.3);
					player.sendSystemMessage(Component.literal("A huge wave crashes over the dock!").withStyle(ChatFormatting.AQUA), true);
					break;
				}
			}
		}
	}

	// ---------- Victory banquets ----------

	/** A player beat a boss for the first time: the next town they visit in the evening throws them a banquet. */
	public static void bossBeaten(ServerPlayer player, String bossName) {
		player.addTag(BANQUET_TAG);
		player.sendSystemMessage(Component.literal("Word of your victory over " + bossName
				+ " will spread. Visit a town in the evening: they'll want to celebrate!").withStyle(ChatFormatting.GOLD));
	}

	private static void maybeStartBanquet(Town town, ServerLevel level) {
		long time = level.getOverworldClockTime() % 24000L;
		if (time < 11500 || time > 20000 || !town.scanned) {
			return;
		}
		for (ServerPlayer player : level.players()) {
			if (player.entityTags().contains(BANQUET_TAG) && town.contains(player.blockPosition(), 0)) {
				player.removeTag(BANQUET_TAG);
				town.banquetFor = player.getName().getString();
				town.banquetUntil = level.getGameTime() + 5000;
				town.announcedTo.clear();
				town.giftsGiven.clear();
				Component news = Component.literal("[" + town.name() + "] ").withStyle(ChatFormatting.LIGHT_PURPLE)
						.append(Component.literal("The whole town comes out to throw a banquet in honour of " + town.banquetFor + "!")
								.withStyle(ChatFormatting.GOLD));
				for (ServerPlayer other : level.players()) {
					if (other.blockPosition().closerThan(town.plaza, 160)) {
						other.sendSystemMessage(news);
						town.announcedTo.add(other.getUUID());
					}
				}
				return;
			}
		}
	}

	static void forget(Player player) {
		ARRIVED.remove(player.getUUID());
	}

	static void clear() {
		ARRIVED.clear();
	}
}
