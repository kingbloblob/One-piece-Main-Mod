package com.onepiecemod.cuisine;

import java.util.HashMap;
import java.util.Map;
import java.util.Random;
import java.util.UUID;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.animal.fish.TropicalFish;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.sea.CalmBelt;

/**
 * The All Blue: Sanji's dream, the one sea where the fish of all four Blues meet.
 *
 * There is one per world, somewhere out in the New World. Its spot comes from the world seed, so it never moves.
 * Inside it every catch is a fish (no junk), fish from every sea bite, two fish exist nowhere else, and you
 * sometimes reel in two at once. Its waters shimmer and are full of tropical fish.
 *
 * The All Blue Compass (Navigator's Desk) points to it.
 */
public class AllBlue {
	/** How far from spawn its centre lies, in blocks (the New World starts at 3500). */
	public static final int DISTANCE = 4400;
	/** How wide it is: everything within this many blocks of the centre. */
	public static final int RADIUS = 160;
	/** Don't show the arrival title again for this long. */
	private static final long TITLE_REPEAT_TICKS = 6000;

	public static final AttachmentType<Boolean> FOUND = AttachmentRegistry.create(
			OnePieceMod.id("all_blue_found"), builder -> builder.persistent(Codec.BOOL).copyOnDeath());

	private static final Map<UUID, Long> lastTitle = new HashMap<>();
	private static long cachedSeed;
	private static BlockPos cachedCenter;

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(AllBlue::tick);
	}

	/** The centre of the All Blue in this world (sea level). */
	public static BlockPos center(MinecraftServer server) {
		ServerLevel overworld = server.overworld();
		long seed = overworld.getSeed();
		if (cachedCenter == null || seed != cachedSeed) {
			Random random = new Random(seed * 31 + 0xA11B1EL);
			double angle = random.nextDouble() * Math.PI * 2;
			cachedCenter = new BlockPos((int) (Math.cos(angle) * DISTANCE), overworld.getSeaLevel(), (int) (Math.sin(angle) * DISTANCE));
			cachedSeed = seed;
		}
		return cachedCenter;
	}

	/** Is this spot in the All Blue? */
	public static boolean contains(ServerLevel level, double x, double z) {
		if (level.dimension() != Level.OVERWORLD) {
			return false;
		}
		BlockPos center = center(level.getServer());
		double dx = x - center.getX();
		double dz = z - center.getZ();
		return dx * dx + dz * dz <= (double) RADIUS * RADIUS;
	}

	private static void tick(MinecraftServer server) {
		if (server.getTickCount() % 10 != 0) {
			return;
		}
		ServerLevel overworld = server.overworld();
		for (ServerPlayer player : overworld.players()) {
			if (!contains(overworld, player.getX(), player.getZ())) {
				continue;
			}
			shimmer(overworld, player);
			if (server.getTickCount() % 40 == 0) {
				arrive(server, player);
			}
			if (server.getTickCount() % 200 == 0) {
				stockFish(overworld, player);
			}
		}
	}

	private static void arrive(MinecraftServer server, ServerPlayer player) {
		long now = server.getTickCount();
		Long last = lastTitle.get(player.getUUID());
		if (last != null && now - last < TITLE_REPEAT_TICKS) {
			lastTitle.put(player.getUUID(), now);
			return;
		}
		lastTitle.put(player.getUUID(), now);
		player.connection.send(new ClientboundSetTitleTextPacket(Component.literal("The All Blue").withStyle(ChatFormatting.AQUA)));
		player.connection.send(new ClientboundSetSubtitleTextPacket(
				Component.literal("Where the fish of every sea meet").withStyle(ChatFormatting.WHITE)));
		if (!Boolean.TRUE.equals(player.getAttached(FOUND))) {
			player.setAttached(FOUND, true);
			player.sendSystemMessage(Component.literal("You found the All Blue! Sanji's dream is real. Every catch here is a fish, "
					+ "fish from all the seas bite, and two kinds live nowhere else: the All Blue Kingfish and the Rainbow Sunfish.")
					.withStyle(ChatFormatting.AQUA));
			player.level().playSound(null, player.blockPosition(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 0.8f, 1.0f);
		}
	}

	/** Glitter on the water around the player, so the All Blue looks different from any other sea. */
	private static void shimmer(ServerLevel level, ServerPlayer player) {
		RandomSource random = player.getRandom();
		double y = level.getSeaLevel() - 0.1;
		for (int i = 0; i < 16; i++) {
			double x = player.getX() + random.nextGaussian() * 9;
			double z = player.getZ() + random.nextGaussian() * 9;
			level.sendParticles(player, i % 4 == 0 ? ParticleTypes.END_ROD : ParticleTypes.GLOW, false, false, x, y, z, 1, 0.3, 0.02, 0.3, 0.01);
		}
		level.sendParticles(player, ParticleTypes.BUBBLE_COLUMN_UP, false, false,
				player.getX() + random.nextGaussian() * 6, y - 1.5, player.getZ() + random.nextGaussian() * 6, 6, 0.5, 0.5, 0.5, 0.05);
	}

	/** Keeps a few tropical fish swimming around, so the water looks alive. */
	private static void stockFish(ServerLevel level, ServerPlayer player) {
		AABB around = player.getBoundingBox().inflate(24);
		if (level.getEntitiesOfClass(TropicalFish.class, around).size() >= 8) {
			return;
		}
		RandomSource random = player.getRandom();
		for (int i = 0; i < 3; i++) {
			BlockPos pos = BlockPos.containing(player.getX() + random.nextInt(25) - 12, level.getSeaLevel() - 2 - random.nextInt(4),
					player.getZ() + random.nextInt(25) - 12);
			if (level.getFluidState(pos).isSource() && CalmBelt.seaAt(level, pos) != null) {
				EntityTypes.TROPICAL_FISH.spawn(level, pos, EntitySpawnReason.NATURAL);
			}
		}
	}
}
