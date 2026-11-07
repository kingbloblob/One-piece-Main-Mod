package com.onepiecemod.worldevent;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * Buster Call craters that heal. Every block a shell blows away is written down first, and some time after the
 * Buster Call ends the islanders rebuild: the blocks come back, bottom up, exactly as they were.
 * Generated structures (and player builds) are never lost for good.
 *
 * Never touched: blocks with a block entity (chests, signs, beds, banners, the Kingdom Flag...), unbreakable blocks
 * and liquids. If a player has put something in a crater by the time it's rebuilt, the player's block stays.
 * The list is saved on the Overworld, so a restart in the middle doesn't lose anything.
 */
public class Ruins {
	/** Ticks between the end of a Buster Call and the start of rebuilding (10 minutes). */
	public static final long REBUILD_DELAY = 20L * 60 * 10;
	/** Blocks put back per tick. */
	private static final int REBUILD_PER_TICK = 48;

	/** One Buster Call's craters. restoreAt = game time to start rebuilding (Long.MAX_VALUE while it's still going). */
	public record Batch(String island, long restoreAt, List<BlockState> palette, List<Long> positions, List<Integer> states) {
		static final Codec<Batch> CODEC = RecordCodecBuilder.create(i -> i.group(
				Codec.STRING.fieldOf("island").forGetter(Batch::island),
				Codec.LONG.fieldOf("restore_at").forGetter(Batch::restoreAt),
				BlockState.CODEC.listOf().fieldOf("palette").forGetter(Batch::palette),
				Codec.LONG.listOf().fieldOf("positions").forGetter(Batch::positions),
				Codec.INT.listOf().fieldOf("states").forGetter(Batch::states)
		).apply(i, Batch::new));
	}

	public static final AttachmentType<List<Batch>> SAVED = AttachmentRegistry.create(
			OnePieceMod.id("buster_call_ruins"),
			builder -> builder.persistent(Batch.CODEC.listOf())
	);

	/** A batch being filled or rebuilt (in memory). */
	static class Live {
		final String island;
		long restoreAt;
		final List<BlockState> palette = new ArrayList<>();
		final Map<BlockState, Integer> paletteIndex = new HashMap<>();
		final ArrayDeque<long[]> scars = new ArrayDeque<>(); // {pos, state index}
		final Set<Long> taken = new HashSet<>();
		boolean announced = false;

		Live(String island, long restoreAt) {
			this.island = island;
			this.restoreAt = restoreAt;
		}

		void record(BlockPos pos, BlockState state) {
			long packed = pos.asLong();
			if (taken.add(packed)) {
				int index = paletteIndex.computeIfAbsent(state, s -> {
					palette.add(s);
					return palette.size() - 1;
				});
				scars.add(new long[] {packed, index});
			}
		}

		/** Bottom-up order, so blocks are rebuilt on top of something. */
		void sortForRebuild() {
			List<long[]> list = new ArrayList<>(scars);
			list.sort(Comparator.comparingInt(s -> BlockPos.getY(s[0])));
			scars.clear();
			scars.addAll(list);
		}

		Batch toBatch() {
			List<Long> positions = new ArrayList<>(scars.size());
			List<Integer> states = new ArrayList<>(scars.size());
			for (long[] scar : scars) {
				positions.add(scar[0]);
				states.add((int) scar[1]);
			}
			return new Batch(island, restoreAt, List.copyOf(palette), positions, states);
		}

		static Live of(Batch batch, long now) {
			// A Buster Call that was running when the server stopped is over now.
			Live live = new Live(batch.island(), batch.restoreAt() == Long.MAX_VALUE ? now + REBUILD_DELAY : batch.restoreAt());
			for (BlockState state : batch.palette()) {
				live.paletteIndex.put(state, live.palette.size());
				live.palette.add(state);
			}
			int n = Math.min(batch.positions().size(), batch.states().size());
			for (int i = 0; i < n; i++) {
				live.taken.add(batch.positions().get(i));
				live.scars.add(new long[] {batch.positions().get(i), batch.states().get(i)});
			}
			live.sortForRebuild();
			return live;
		}
	}

	private static final List<Live> LIVE = new ArrayList<>();
	private static boolean loaded = false;
	private static boolean dirty = false;

	static void load(MinecraftServer server) {
		LIVE.clear();
		long now = server.overworld().getGameTime();
		for (Batch batch : server.overworld().getAttachedOrElse(SAVED, List.of())) {
			LIVE.add(Live.of(batch, now));
		}
		loaded = true;
		dirty = true;
	}

	static void unload() {
		LIVE.clear();
		loaded = false;
	}

	static void save(MinecraftServer server) {
		if (!loaded || !dirty) {
			return;
		}
		List<Batch> batches = new ArrayList<>();
		for (Live live : LIVE) {
			if (!live.scars.isEmpty()) {
				batches.add(live.toBatch());
			}
		}
		server.overworld().setAttached(SAVED, batches);
		dirty = false;
	}

	/** Starts a new batch for a Buster Call. */
	static Live open(String island) {
		Live live = new Live(island, Long.MAX_VALUE);
		LIVE.add(live);
		dirty = true;
		return live;
	}

	/** The Buster Call is over: rebuild after the delay. */
	static void close(Live live, long now) {
		live.restoreAt = now + REBUILD_DELAY;
		live.sortForRebuild();
		dirty = true;
	}

	/** Rebuild everything right away (for /worldevent restore). */
	static int rebuildNow(long now) {
		int count = 0;
		for (Live live : LIVE) {
			live.restoreAt = Math.min(live.restoreAt, now);
			live.sortForRebuild();
			count += live.scars.size();
		}
		dirty = true;
		return count;
	}

	static int pending() {
		int count = 0;
		for (Live live : LIVE) {
			count += live.scars.size();
		}
		return count;
	}

	/** Blows a crater: removes blocks in a ball, scorches the ground around it, and writes all of it down. */
	static void crater(ServerLevel level, Live live, BlockPos center, int radius, RandomSource random) {
		double r2 = (radius + 0.5) * (radius + 0.5);
		for (int dx = -radius - 1; dx <= radius + 1; dx++) {
			for (int dy = -radius; dy <= radius; dy++) {
				for (int dz = -radius - 1; dz <= radius + 1; dz++) {
					BlockPos pos = center.offset(dx, dy, dz);
					if (!level.hasChunkAt(pos)) {
						continue;
					}
					BlockState state = level.getBlockState(pos);
					if (state.isAir() || !breakable(level, pos, state)) {
						continue;
					}
					double d2 = dx * dx + dy * dy * 1.6 + dz * dz; // A bit flatter than a ball.
					if (d2 <= r2 - random.nextFloat() * radius) {
						live.record(pos, state);
						level.setBlock(pos, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE | Block.UPDATE_SUPPRESS_DROPS);
					} else if (d2 <= r2 + radius * 2.5 && state.is(BlockTags.DIRT) && level.getBlockState(pos.above()).isAir()) {
						// Scorched earth around the crater.
						live.record(pos, state);
						level.setBlock(pos, Blocks.COARSE_DIRT.defaultBlockState(), Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE | Block.UPDATE_SUPPRESS_DROPS);
					}
				}
			}
		}
		dirty = true;
	}

	private static boolean breakable(ServerLevel level, BlockPos pos, BlockState state) {
		return !state.hasBlockEntity() && state.getFluidState().isEmpty() && state.getDestroySpeed(level, pos) >= 0
				&& !state.is(Blocks.BEDROCK) && !state.is(BlockTags.WITHER_IMMUNE);
	}

	/** True if the block there now is one the crater left (air, water that ran in, scorched dirt, fire). */
	private static boolean stillScarred(BlockState now) {
		return now.isAir() || !now.getFluidState().isEmpty() || now.is(Blocks.COARSE_DIRT) || now.is(BlockTags.FIRE)
				|| now.canBeReplaced();
	}

	static void tick(MinecraftServer server) {
		if (!loaded) {
			load(server);
		}
		ServerLevel level = server.overworld();
		long now = level.getGameTime();
		int budget = REBUILD_PER_TICK;
		for (Live live : List.copyOf(LIVE)) {
			if (live.restoreAt > now) {
				continue;
			}
			if (!live.announced) {
				live.announced = true;
				tellNearby(level, live, Component.literal("The people of ").withStyle(ChatFormatting.GREEN)
						.append(IslandTrouble.islandName(live.island).copy().withStyle(ChatFormatting.GREEN))
						.append(Component.literal(" are rebuilding after the Buster Call.").withStyle(ChatFormatting.GREEN)));
			}
			int checks = budget * 4;
			while (budget > 0 && checks-- > 0 && !live.scars.isEmpty()) {
				long[] scar = live.scars.poll();
				BlockPos pos = BlockPos.of(scar[0]);
				if (!level.isLoaded(pos)) {
					live.scars.add(scar); // Try again when someone is near.
					continue;
				}
				live.taken.remove(scar[0]);
				BlockState now0 = level.getBlockState(pos);
				BlockState original = live.palette.get((int) scar[1]);
				if (stillScarred(now0) && !now0.equals(original)) {
					level.setBlock(pos, original, Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE | Block.UPDATE_SUPPRESS_DROPS);
					if (level.getRandom().nextInt(12) == 0) {
						level.sendParticles(ParticleTypes.HAPPY_VILLAGER, pos.getX() + 0.5, pos.getY() + 1.0, pos.getZ() + 0.5, 1, 0.3, 0.2, 0.3, 0);
					}
				}
				budget--;
				dirty = true;
			}
			if (live.scars.isEmpty()) {
				LIVE.remove(live);
				dirty = true;
			}
			if (budget <= 0) {
				break;
			}
		}
		if (now % 600 == 0) {
			save(server);
		}
	}

	private static void tellNearby(ServerLevel level, Live live, Component message) {
		BlockPos center = IslandTrouble.centerOf(live.island);
		for (ServerPlayer player : level.players()) {
			if (center == null || player.blockPosition().closerThan(center, 250)) {
				player.sendSystemMessage(message);
			}
		}
	}
}
