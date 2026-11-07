package com.onepiecemod.npc;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BiomeTags;
import net.minecraft.tags.TagKey;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.Heightmap;

import com.onepiecemod.OnePieceMod;

/**
 * Pirate gangs and Marine patrols that walk around islands and beaches, day and night.
 * Which groups show up depends on the biome: Buggy's clowns in the East Blue, Baroque Works in Alabasta,
 * Beasts Pirates in Wano, Fish-Men around Fish-Man Island... (the "patrols" part of npc_kits.json).
 *
 * Marines only attack players who have a bounty, but pirates attack everyone, and the two sides fight each other.
 */
public class NpcPatrols {
	private static final TagKey<Biome> ISLANDS = TagKey.create(Registries.BIOME, OnePieceMod.id("one_piece_islands"));
	public static final String PATROL_TAG = "onepiece_patrol";

	private static final int CHECK_EVERY = 20 * 30; // ticks
	private static final float CHANCE = 0.12f;      // per player per check
	private static final int MAX_NEARBY = 6;        // patrol NPCs around one player

	static void initialize() {
	}

	static void tick(MinecraftServer server) {
		if (server.getTickCount() % CHECK_EVERY != 0) {
			return;
		}
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			if (player.level().dimension() == Level.OVERWORLD && !player.isCreative() && !player.isSpectator()
					&& player.level().getDifficulty() != Difficulty.PEACEFUL && player.getRandom().nextFloat() < CHANCE) {
				sendPatrol(player, false);
			}
		}
	}

	/** Tries to bring one group in 28-44 blocks from the player. forced = ignore the crowd limit (for /npc patrol). */
	public static boolean sendPatrol(ServerPlayer player, boolean forced) {
		ServerLevel level = (ServerLevel) player.level();
		Holder<Biome> biome = level.getBiome(player.blockPosition());
		String biomeId = biome.unwrapKey().map(ResourceKey::identifier).map(Object::toString).orElse("");
		List<NpcKit.Patrol> groups = NpcKit.patrolsFor(biomeId);
		// Grand Line islands and any beach get patrols; other vanilla biomes (deep forests, mountains...) stay quiet.
		if (groups.isEmpty() || !(NpcKit.listsBiome(biomeId) || biome.is(ISLANDS) || biome.is(BiomeTags.IS_BEACH))) {
			return false;
		}
		if (!forced) {
			int nearby = level.getEntitiesOfClass(HumanNpc.class, player.getBoundingBox().inflate(64.0),
					npc -> npc.entityTags().contains(PATROL_TAG)).size();
			if (nearby >= MAX_NEARBY) {
				return false;
			}
		}

		RandomSource random = player.getRandom();
		NpcKit.Patrol group = pickGroup(groups, random);
		BlockPos spot = findSpot(level, player, random);
		if (spot == null) {
			return false;
		}
		int size = group.min + random.nextInt(Math.max(1, group.max - group.min + 1));
		int spawned = 0;
		for (int i = 0; i < size; i++) {
			String kitId = i == 0 && group.leader != null ? group.leader : NpcKit.pick(group.kits, random);
			BlockPos pos = surface(level, spot.getX() + random.nextInt(5) - 2, spot.getZ() + random.nextInt(5) - 2);
			if (!safeStand(level, pos)) {
				pos = spot; // That spot was water or cramped: stand at the group's checked spot instead.
			}
			HumanNpc npc = NpcFeature.spawn(level, kitId, pos, random.nextFloat() * 360f);
			if (npc != null) {
				npc.addTag(PATROL_TAG);
				spawned++;
			}
		}
		return spawned > 0;
	}

	private static NpcKit.Patrol pickGroup(List<NpcKit.Patrol> groups, RandomSource random) {
		int total = 0;
		for (NpcKit.Patrol group : groups) {
			total += Math.max(1, group.weight);
		}
		int roll = random.nextInt(total);
		for (NpcKit.Patrol group : groups) {
			roll -= Math.max(1, group.weight);
			if (roll < 0) {
				return group;
			}
		}
		return groups.get(0);
	}

	private static BlockPos findSpot(ServerLevel level, ServerPlayer player, RandomSource random) {
		for (int attempt = 0; attempt < 12; attempt++) {
			double angle = random.nextDouble() * Math.PI * 2;
			int distance = 28 + random.nextInt(17);
			int x = (int) Math.floor(player.getX() + Math.cos(angle) * distance);
			int z = (int) Math.floor(player.getZ() + Math.sin(angle) * distance);
			if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
				continue;
			}
			BlockPos pos = surface(level, x, z);
			if (safeStand(level, pos) && Math.abs(pos.getY() - player.getY()) < 16) {
				return pos;
			}
		}
		return null;
	}

	/** Solid dry ground underfoot and two blocks of open air (no water, no blocks) to stand in. */
	static boolean safeStand(ServerLevel level, BlockPos pos) {
		return level.getBlockState(pos.below()).isSolid() && level.getFluidState(pos.below()).isEmpty()
				&& level.getBlockState(pos).getCollisionShape(level, pos).isEmpty() && level.getFluidState(pos).isEmpty()
				&& level.getBlockState(pos.above()).getCollisionShape(level, pos.above()).isEmpty()
				&& level.getFluidState(pos.above()).isEmpty();
	}

	private static BlockPos surface(ServerLevel level, int x, int z) {
		return new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z);
	}
}
