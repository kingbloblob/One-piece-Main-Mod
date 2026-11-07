package com.onepiecemod.sea;

import java.util.Optional;

import com.mojang.datafixers.util.Pair;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Prediction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Container;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CampfireBlock;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.SlabType;
import net.minecraft.world.level.gamerules.GameRules;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.storage.LevelData;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.world.PalmTreeFeature;
import com.onepiecemod.world.RingBiomeSource;

/**
 * Every new Grand Line world starts the same way: you wash up on a tiny East Blue island in open sea,
 * with a dinghy, a Log Pose and a few supplies. Foosha Village is a short row away, and the Log Pose
 * points there once you've stayed on the island a while.
 *
 * Happens once, the first time a brand-new Grand Line world starts. Older worlds and other world types are left alone.
 */
public class StartingIsland {
	/** Where the starting island is (empty if this world has none) and the island the first Log Pose reading points to. */
	public record Site(Optional<BlockPos> center, Optional<BlockPos> firstIsland) {
		public static final Codec<Site> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				BlockPos.CODEC.optionalFieldOf("center").forGetter(Site::center),
				BlockPos.CODEC.optionalFieldOf("first_island").forGetter(Site::firstIsland)
		).apply(instance, Site::new));

		static final Site NONE = new Site(Optional.empty(), Optional.empty());
	}

	/** Saved on the Overworld, so the island is only made once. */
	public static final AttachmentType<Site> SITE = AttachmentRegistry.create(
			OnePieceMod.id("starting_island"), builder -> builder.persistent(Site.CODEC));

	/** Saved on each player: they already got their castaway kit (dinghy + Log Pose). */
	public static final AttachmentType<Boolean> KIT_GIVEN = AttachmentRegistry.create(
			OnePieceMod.id("castaway_kit"), builder -> builder.persistent(Codec.BOOL).copyOnDeath());

	/** Rough size of the island: about 25 blocks across. */
	private static final int RADIUS = 12;
	/** How far the island sits from Foosha Village: far enough to count as another island for the Log Pose (over ISLAND_SPACING), close enough for a short row. */
	private static final int MIN_FROM_FOOSHA = 300;
	private static final int MAX_FROM_FOOSHA = 560;
	/** Stay inside the East Blue ring. */
	private static final int MAX_FROM_CENTER = 1200;

	public static void initialize() {
		ServerLifecycleEvents.SERVER_STARTED.register(server -> {
			try {
				setUp(server);
			} catch (RuntimeException e) {
				OnePieceMod.LOGGER.error("Couldn't make the starting island; players will spawn normally", e);
			}
		});
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> giveKit(handler.getPlayer()));
	}

	public static Site site(ServerLevel overworld) {
		Site site = overworld.getAttached(SITE);
		return site != null ? site : Site.NONE;
	}

	/** The starting island, if the player is standing on it. */
	public static boolean isOnStartingIsland(ServerLevel level, BlockPos pos) {
		return level.dimension() == Level.OVERWORLD && site(level).center()
				.map(center -> IslandFinder.horizontalDistance(center, pos) < IslandFinder.ISLAND_SPACING)
				.orElse(false);
	}

	private static void setUp(MinecraftServer server) {
		ServerLevel level = server.overworld();
		if (level.hasAttached(SITE)) {
			return;
		}
		// Only brand-new Grand Line worlds. An old save keeps its spawn.
		if (!(level.getChunkSource().getGenerator().getBiomeSource() instanceof RingBiomeSource) || level.getGameTime() > 200) {
			level.setAttached(SITE, Site.NONE);
			return;
		}
		long start = System.currentTimeMillis();
		Optional<BlockPos> foosha = findFoosha(level);
		BlockPos anchor = foosha.filter(pos -> horizontal(pos) < MAX_FROM_CENTER).orElse(BlockPos.ZERO);
		Optional<BlockPos> spot = findOpenSea(level, anchor, MIN_FROM_FOOSHA, MAX_FROM_FOOSHA);
		if (spot.isEmpty()) {
			spot = findOpenSea(level, BlockPos.ZERO, 0, 900);
		}
		if (spot.isEmpty()) {
			OnePieceMod.LOGGER.warn("No open sea for a starting island near spawn; players will spawn normally");
			level.setAttached(SITE, Site.NONE);
			return;
		}
		BlockPos spawn = build(level, spot.get());
		level.setRespawnData(LevelData.RespawnData.of(Level.OVERWORLD, spawn, 0.0f, 0.0f));
		// The island is small, so don't scatter new players into the water around it.
		level.getGameRules().set(GameRules.RESPAWN_RADIUS, 2, server);
		level.setAttached(SITE, new Site(Optional.of(spawn), foosha));
		OnePieceMod.LOGGER.info("Made the starting island at {} (Foosha Village at {}) in {} ms",
				spawn.toShortString(), foosha.map(BlockPos::toShortString).orElse("none"), System.currentTimeMillis() - start);
	}

	private static Optional<BlockPos> findFoosha(ServerLevel level) {
		ResourceKey<Structure> key = ResourceKey.create(Registries.STRUCTURE, OnePieceMod.id("foosha_village"));
		Optional<Holder.Reference<Structure>> holder = level.registryAccess().lookupOrThrow(Registries.STRUCTURE).get(key);
		if (holder.isEmpty()) {
			return Optional.empty();
		}
		Pair<BlockPos, Holder<Structure>> found = level.getChunkSource().getGenerator()
				.findNearestMapStructure(level, HolderSet.direct(holder.get()), BlockPos.ZERO, 100, false);
		return found == null ? Optional.empty() : Optional.of(found.getFirst());
	}

	/**
	 * A spot of open water at least 30 blocks from any land and not too deep, between minDistance and maxDistance
	 * from {@code around}, nearest first. Uses the world generator's height, so nothing has to be generated yet.
	 */
	private static Optional<BlockPos> findOpenSea(ServerLevel level, BlockPos around, int minDistance, int maxDistance) {
		for (int distance = Math.max(minDistance, 0); distance <= maxDistance; distance += 24) {
			int points = distance == 0 ? 1 : Math.max(8, (int) (2 * Math.PI * distance / 48));
			for (int i = 0; i < points; i++) {
				double angle = 2 * Math.PI * i / points;
				BlockPos spot = around.offset((int) Math.round(Math.cos(angle) * distance), 0, (int) Math.round(Math.sin(angle) * distance));
				if (horizontal(spot) < MAX_FROM_CENTER && isOpenSea(level, spot)) {
					return Optional.of(spot);
				}
			}
		}
		return Optional.empty();
	}

	private static boolean isOpenSea(ServerLevel level, BlockPos center) {
		int sea = level.getSeaLevel();
		int floor = floorHeight(level, center.getX(), center.getZ());
		if (floor > sea - 4 || floor < sea - 30) {
			return false; // Too shallow (land close by) or so deep the island would be a tall pillar.
		}
		for (int radius : new int[] {16, 32, 48}) {
			for (int i = 0; i < 12; i++) {
				double angle = 2 * Math.PI * i / 12;
				int x = center.getX() + (int) Math.round(Math.cos(angle) * radius);
				int z = center.getZ() + (int) Math.round(Math.sin(angle) * radius);
				if (floorHeight(level, x, z) > sea - 3) {
					return false;
				}
			}
		}
		return true;
	}

	/** The top of the sea floor or land at x, z, as the generator will make it. */
	private static int floorHeight(ServerLevel level, int x, int z) {
		return level.getChunkSource().getGenerator().getBaseHeight(x, z, Heightmap.Types.OCEAN_FLOOR_WG, level,
				level.getChunkSource().randomState());
	}

	// ---------- Building it ----------

	/** Raises a small sandy island with grass in the middle, palms, a campfire, a wrecked raft and a supply chest. Returns the spawn spot. */
	private static BlockPos build(ServerLevel level, BlockPos center) {
		RandomSource random = RandomSource.create(level.getSeed() ^ 0x0E57B1E5L);
		int sea = level.getSeaLevel();
		int reach = RADIUS * 2;
		// Generate the chunks first, so the island isn't overwritten when they generate later.
		for (int cx = (center.getX() - reach) >> 4; cx <= (center.getX() + reach) >> 4; cx++) {
			for (int cz = (center.getZ() - reach) >> 4; cz <= (center.getZ() + reach) >> 4; cz++) {
				level.getChunk(cx, cz);
			}
		}

		double phase = random.nextDouble() * Math.PI * 2;
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		for (int dx = -reach; dx <= reach; dx++) {
			for (int dz = -reach; dz <= reach; dz++) {
				double angle = Math.atan2(dz, dx);
				double edge = RADIUS + 2.0 * Math.sin(angle * 3 + phase) + 1.2 * Math.sin(angle * 5 - phase);
				double t = Math.sqrt(dx * dx + dz * dz) / edge;
				int top;
				if (t <= 1.0) {
					top = sea + 1 + (int) Math.round(4.0 * (1.0 - t * t)); // A gentle hill: sea + 5 in the middle.
				} else if (t <= 1.7) {
					top = sea - 1 - (int) Math.round((t - 1.0) * 14.0); // A sandy shelf sloping down under the water.
				} else {
					continue;
				}
				int x = center.getX() + dx;
				int z = center.getZ() + dz;
				int floor = level.getHeight(Heightmap.Types.OCEAN_FLOOR, x, z) - 1;
				boolean grassy = top >= sea + 3;
				for (int y = floor + 1; y <= top; y++) {
					BlockState block;
					if (y == top) {
						block = grassy ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.SAND.defaultBlockState();
					} else if (y >= top - 3) {
						block = grassy ? Blocks.DIRT.defaultBlockState() : Blocks.SAND.defaultBlockState();
					} else {
						block = Blocks.SANDSTONE.defaultBlockState();
					}
					level.setBlock(pos.set(x, y, z), block, 2);
				}
				if (top >= sea) {
					// Clear seagrass or kelp that was standing on the old sea floor above the new ground.
					for (int y = top + 1; y <= sea + 1; y++) {
						level.setBlock(pos.set(x, y, z), Blocks.AIR.defaultBlockState(), 2);
					}
					if (grassy && random.nextInt(5) == 0) {
						level.setBlock(pos.set(x, top + 1, z), Blocks.SHORT_GRASS.defaultBlockState(), 2);
					}
				}
			}
		}

		BlockPos spawn = surface(level, center);
		// Palms around the hill.
		int palms = 3;
		for (int i = 0; i < palms; i++) {
			double angle = phase + i * (Math.PI * 2 / palms) + random.nextDouble() * 0.6;
			BlockPos ground = surface(level, center.offset((int) Math.round(Math.cos(angle) * 6), 0, (int) Math.round(Math.sin(angle) * 6)));
			PalmTreeFeature.INSTANCE.place(level, level.getChunkSource().getGenerator(), random, ground);
		}

		// A campfire with a signal plume, so the island is easy to find again from the sea.
		BlockPos fire = surface(level, center.offset(2, 0, 2));
		level.setBlock(fire, Blocks.CAMPFIRE.defaultBlockState().setValue(CampfireBlock.SIGNAL_FIRE, true), 3);
		level.setBlock(fire.below(), Blocks.HAY_BLOCK.defaultBlockState(), 3);

		// The supply chest that washed up with you.
		BlockPos chestPos = surface(level, center.offset(-2, 0, 1));
		level.setBlock(chestPos, Blocks.CHEST.defaultBlockState().setValue(ChestBlock.FACING, Direction.EAST), 3);
		if (level.getBlockEntity(chestPos) instanceof Container chest) {
			ItemStack[] supplies = {
					new ItemStack(Items.BREAD, 6), new ItemStack(Items.COOKED_COD, 4), new ItemStack(Items.FISHING_ROD),
					new ItemStack(Items.OAK_LOG, 8), new ItemStack(Items.TORCH, 8), new ItemStack(Items.STRING, 4),
					new ItemStack(Items.OAK_PLANKS, 8), new ItemStack(Items.BARREL)
			};
			for (int slot = 0; slot < supplies.length; slot++) {
				chest.setItem(slot * 3 % 27, supplies[slot]);
			}
		}

		// What's left of the raft you came on: some broken planks on the beach.
		double raftAngle = phase + Math.PI;
		BlockPos raft = center.offset((int) Math.round(Math.cos(raftAngle) * (RADIUS - 4)), 0, (int) Math.round(Math.sin(raftAngle) * (RADIUS - 4)));
		BlockState plank = Blocks.OAK_SLAB.defaultBlockState().setValue(SlabBlock.TYPE, SlabType.BOTTOM);
		for (int[] offset : new int[][] {{0, 0}, {1, 0}, {0, 1}, {1, 1}, {2, 1}, {-1, 0}}) {
			if (random.nextInt(4) != 0) {
				BlockPos at = surface(level, raft.offset(offset[0], 0, offset[1]));
				if (level.getBlockState(at).isAir()) {
					level.setBlock(at, plank, 3);
				}
			}
		}
		BlockPos barrel = surface(level, raft.offset(-1, 0, 2));
		level.setBlock(barrel, Blocks.BARREL.defaultBlockState(), 3);
		return spawn;
	}

	/** The first air block above the ground at x, z. */
	private static BlockPos surface(ServerLevel level, BlockPos pos) {
		return new BlockPos(pos.getX(), level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, pos.getX(), pos.getZ()), pos.getZ());
	}

	private static double horizontal(BlockPos pos) {
		return Math.sqrt((double) pos.getX() * pos.getX() + (double) pos.getZ() * pos.getZ());
	}

	// ---------- The castaway kit ----------

	private static void giveKit(ServerPlayer player) {
		ServerLevel overworld = player.level().getServer().overworld();
		if (site(overworld).center().isEmpty() || Boolean.TRUE.equals(player.getAttached(KIT_GIVEN))) {
			return;
		}
		player.setAttached(KIT_GIVEN, true);
		player.getInventory().placeItemBackInInventory(new ItemStack(Items.OAK_BOAT), Prediction.SERVER_ONLY);
		player.getInventory().placeItemBackInInventory(new ItemStack(SeaItems.LOG_POSE), Prediction.SERVER_ONLY);
		player.sendSystemMessage(Component.literal("You wash up on a tiny island in the East Blue with a dinghy and a Log Pose. "
				+ "Stay on the island a while and the Log Pose will point the way to the next one.").withStyle(ChatFormatting.AQUA));
	}
}
