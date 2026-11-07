package com.onepiecemod.treasure;

import java.util.List;
import java.util.Optional;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.RandomizableContainer;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.RandomizableContainerBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.templatesystem.BlockIgnoreProcessor;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.level.storage.loot.LootTable;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.npc.NpcFeature;

/**
 * Puts a treasure into the world the first time a player comes near its X. Runs only on chunks that are already
 * loaded, so it never makes the server generate terrain.
 * - Buried treasure: a chest 2 blocks under a Dig Spot (a patch of freshly turned earth with a red X).
 * - Captain's hoard: the same but 4 blocks down with gold around it, and 3 of the captain's old crew on guard.
 * - Sunken wreck: one of the vanilla shipwrecks laid on the sea floor, its chests filled with our loot.
 */
public final class TreasureBuilder {
	public static final ResourceKey<LootTable> BURIED_LOOT = loot("treasure/buried");
	public static final ResourceKey<LootTable> HOARD_LOOT = loot("treasure/hoard");
	public static final ResourceKey<LootTable> WRECK_LOOT = loot("treasure/wreck");
	public static final ResourceKey<LootTable> WRECK_MAP_LOOT = loot("treasure/wreck_map");
	public static final ResourceKey<LootTable> CASTAWAY_LOOT = loot("treasure/castaway");
	private static final ResourceKey<LootTable> WRECK_SUPPLY_LOOT = ResourceKey.create(Registries.LOOT_TABLE,
			Identifier.withDefaultNamespace("chests/shipwreck_supply"));

	/** Whole wrecks only (the half wrecks lack the captain's cabin with the treasure chest). */
	private static final List<String> WRECKS = List.of(
			"shipwreck/rightsideup_full", "shipwreck/rightsideup_full_degraded", "shipwreck/with_mast",
			"shipwreck/with_mast_degraded", "shipwreck/sideways_full", "shipwreck/sideways_full_degraded",
			"shipwreck/upsidedown_full", "shipwreck/upsidedown_full_degraded");

	private static final String[] HOARD_GUARDS = {"pirate_captain", "pirate", "pirate_gunner"};

	private TreasureBuilder() {
	}

	private static ResourceKey<LootTable> loot(String path) {
		return ResourceKey.create(Registries.LOOT_TABLE, OnePieceMod.id(path));
	}

	/** Builds the site. Returns the treasure chest, or null if the chunks aren't loaded yet (try again later). */
	public static BlockPos build(ServerLevel level, TreasureSites.Site site, ServerPlayer near) {
		TreasureKind kind = TreasureKind.byId(site.kind());
		BlockPos chest = kind == TreasureKind.CASTAWAY ? raiseIslet(level, site.pos())
				: kind.land ? buryChest(level, site.pos(), kind) : sinkWreck(level, site.pos());
		if (chest != null) {
			near.sendOverlayMessage(Component.literal(kind == TreasureKind.CASTAWAY ? "A lonely palm tree sticks out of the sea ahead..."
					: kind.land ? "The X on your map is close by..." : "The wreck from your chart lies somewhere below..."));
		}
		return chest;
	}

	/** True once the treasure chest has been opened (its loot rolled) or broken. */
	public static boolean isLooted(ServerLevel level, BlockPos chest) {
		if (!loaded(level, chest.getX() - 1, chest.getZ() - 1, chest.getX() + 1, chest.getZ() + 1)) {
			return false;
		}
		BlockEntity be = level.getBlockEntity(chest);
		return !(be instanceof RandomizableContainerBlockEntity container) || container.getLootTable() == null;
	}

	private static boolean loaded(ServerLevel level, int minX, int minZ, int maxX, int maxZ) {
		for (int cx = minX >> 4; cx <= maxX >> 4; cx++) {
			for (int cz = minZ >> 4; cz <= maxZ >> 4; cz++) {
				if (!level.getChunkSource().hasChunk(cx, cz)) {
					return false;
				}
			}
		}
		return true;
	}

	private static boolean insideStructure(ServerLevel level, BlockPos pos) {
		return level.structureManager().getStructureWithPieceAt(pos, holder -> true).isValid();
	}

	// ---------- Buried treasure and hoards ----------

	private static BlockPos buryChest(ServerLevel level, BlockPos mark, TreasureKind kind) {
		if (!loaded(level, mark.getX() - 16, mark.getZ() - 16, mark.getX() + 16, mark.getZ() + 16)) {
			return null;
		}
		RandomSource random = level.getRandom();
		BlockPos top = findGround(level, mark);
		if (top == null) {
			// The map was drawn from the rough shape of the land; nothing dry here after all. Put it on whatever is there.
			top = level.getHeightmapPos(Heightmap.Types.OCEAN_FLOOR, mark).below();
		}
		BlockState ground = level.getBlockState(top);
		BlockState filler = ground.is(BlockTags.SAND) ? Blocks.SAND.defaultBlockState() : Blocks.DIRT.defaultBlockState();
		int depth = kind == TreasureKind.HOARD ? 4 : 2;
		BlockPos chest = top.below(depth);

		// Solid earth between the X and the chest (caves or water pockets would give it away).
		for (int dy = 1; dy < depth; dy++) {
			BlockPos p = top.below(dy);
			if (!level.getBlockState(p).isSolidRender()) {
				level.setBlock(p, filler, Block.UPDATE_CLIENTS);
			}
		}
		Direction facing = Direction.Plane.HORIZONTAL.getRandomDirection(random);
		level.setBlock(chest, Blocks.CHEST.defaultBlockState().setValue(ChestBlock.FACING, facing), Block.UPDATE_CLIENTS);
		RandomizableContainer.setBlockEntityLootTable(level, random, chest, kind == TreasureKind.HOARD ? HOARD_LOOT : BURIED_LOOT);

		if (kind == TreasureKind.HOARD) {
			// A pile of the captain's gold around the chest, and the bones of whoever tried before you.
			Direction side = facing.getClockWise();
			level.setBlock(chest.relative(side), Blocks.GOLD_BLOCK.defaultBlockState(), Block.UPDATE_CLIENTS);
			level.setBlock(chest.relative(side.getOpposite()), Blocks.RAW_GOLD_BLOCK.defaultBlockState(), Block.UPDATE_CLIENTS);
			level.setBlock(chest.relative(facing.getOpposite()), Blocks.BONE_BLOCK.defaultBlockState(), Block.UPDATE_CLIENTS);
			level.setBlock(chest.below(), Blocks.GOLD_BLOCK.defaultBlockState(), Block.UPDATE_CLIENTS);
		}

		// The X itself, and no flower or grass hiding it.
		BlockPos above = top.above();
		if (!level.getBlockState(above).isAir() && level.getBlockState(above).canBeReplaced()) {
			level.setBlock(above, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS);
		}
		level.setBlock(top, TreasureFeature.DIG_SPOT.defaultBlockState(), Block.UPDATE_CLIENTS);

		if (kind == TreasureKind.HOARD) {
			spawnGuards(level, top, random);
		}
		return chest;
	}

	/** Open, dry, natural ground within 10 blocks of the mark (not inside a town or other build). */
	private static BlockPos findGround(ServerLevel level, BlockPos mark) {
		for (int r = 0; r <= 10; r += 2) {
			for (int dx = -r; dx <= r; dx += 2) {
				for (int dz = -r; dz <= r; dz += 2) {
					if (Math.max(Math.abs(dx), Math.abs(dz)) != r) {
						continue; // Only the ring at this radius.
					}
					BlockPos top = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, mark.offset(dx, 0, dz)).below();
					BlockState state = level.getBlockState(top);
					if (state.getFluidState().isEmpty() && state.isSolidRender() && !state.is(BlockTags.LOGS)
							&& !state.is(BlockTags.LEAVES) && !state.hasBlockEntity()
							&& top.getY() > level.getSeaLevel() && !insideStructure(level, top)) {
						return top;
					}
				}
			}
		}
		return null;
	}

	private static void spawnGuards(ServerLevel level, BlockPos top, RandomSource random) {
		for (int i = 0; i < HOARD_GUARDS.length; i++) {
			double angle = (Math.PI * 2 / HOARD_GUARDS.length) * i + random.nextDouble();
			BlockPos at = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES,
					top.offset((int) Math.round(Math.cos(angle) * 4), 0, (int) Math.round(Math.sin(angle) * 4)));
			HumanNpc guard = NpcFeature.spawn(level, HOARD_GUARDS[i], at, random.nextFloat() * 360);
			if (guard != null) {
				guard.addTag("onepiece_treasure_guard");
				guard.makeGuard(); // Stays within 16 blocks of where it stood, never despawns.
			}
		}
	}

	// ---------- Castaway's cache ----------

	/**
	 * A tiny sandbar island rising out of shallow sea: one palm tree, the castaway's cold campfire and a smashed rowboat,
	 * and the cache buried under a Dig Spot. Returns the chest, or null if the chunks aren't loaded yet.
	 */
	private static BlockPos raiseIslet(ServerLevel level, BlockPos mark) {
		int radius = 6;
		if (!loaded(level, mark.getX() - radius - 2, mark.getZ() - radius - 2, mark.getX() + radius + 2, mark.getZ() + radius + 2)) {
			return null;
		}
		RandomSource random = level.getRandom();
		int water = level.getSeaLevel() - 1; // The top water block.
		BlockState sand = Blocks.SAND.defaultBlockState();
		for (int dx = -radius - 1; dx <= radius + 1; dx++) {
			for (int dz = -radius - 1; dz <= radius + 1; dz++) {
				// A slightly lumpy circle, highest in the middle.
				double d = Math.sqrt(dx * dx + dz * dz) + (random.nextDouble() - 0.5) * 0.8;
				int top = d < 2.5 ? water + 2 : d < 4.5 ? water + 1 : d < radius ? water : d < radius + 1.2 ? water - 1 : Integer.MIN_VALUE;
				if (top == Integer.MIN_VALUE) {
					continue;
				}
				int x = mark.getX() + dx;
				int z = mark.getZ() + dz;
				int floor = level.getHeight(Heightmap.Types.OCEAN_FLOOR, x, z);
				for (int y = Math.min(floor, top) - 1; y <= top; y++) {
					BlockPos p = new BlockPos(x, y, z);
					BlockState here = level.getBlockState(p);
					if (y < floor && here.isSolidRender()) {
						continue; // Real sea floor: leave it.
					}
					level.setBlock(p, y < top - 3 ? Blocks.SANDSTONE.defaultBlockState() : sand, Block.UPDATE_CLIENTS);
				}
			}
		}

		// The palm tree, leaning a little toward the sea.
		BlockPos trunk = mark.offset(1, water + 3 - mark.getY(), 1);
		BlockState log = Blocks.JUNGLE_LOG.defaultBlockState();
		BlockState leaves = Blocks.JUNGLE_LEAVES.defaultBlockState().setValue(net.minecraft.world.level.block.LeavesBlock.PERSISTENT, true);
		BlockPos top = trunk;
		for (int i = 0; i < 6; i++) {
			top = trunk.offset(i >= 4 ? 1 : 0, i, 0);
			level.setBlock(top, log, Block.UPDATE_CLIENTS);
		}
		BlockPos crown = top.above();
		level.setBlock(crown, leaves, Block.UPDATE_CLIENTS);
		for (Direction dir : Direction.Plane.HORIZONTAL) {
			for (int i = 1; i <= 3; i++) {
				BlockPos frond = crown.relative(dir, i).below(i == 3 ? 1 : 0);
				if (level.getBlockState(frond).isAir()) {
					level.setBlock(frond, leaves, Block.UPDATE_CLIENTS);
				}
			}
		}
		// Coconuts (cocoa pods hang from jungle logs).
		Direction podSide = Direction.Plane.HORIZONTAL.getRandomDirection(random);
		BlockPos pod = top.relative(podSide);
		if (level.getBlockState(pod).isAir()) {
			level.setBlock(pod, Blocks.COCOA.defaultBlockState().setValue(net.minecraft.world.level.block.CocoaBlock.FACING, podSide.getOpposite())
					.setValue(net.minecraft.world.level.block.CocoaBlock.AGE, 2), Block.UPDATE_CLIENTS);
		}

		// The castaway's camp: a cold campfire and a barrel, and the wreck of the rowboat that brought them.
		level.setBlock(surface(level, mark, -2, 2), Blocks.CAMPFIRE.defaultBlockState()
				.setValue(net.minecraft.world.level.block.CampfireBlock.LIT, false), Block.UPDATE_CLIENTS);
		level.setBlock(surface(level, mark, -3, -1), Blocks.BARREL.defaultBlockState(), Block.UPDATE_CLIENTS);
		for (int i = 0; i < 3; i++) {
			BlockPos plank = surface(level, mark, 4 + i, -3 + (i == 2 ? 1 : 0));
			if (plank.getY() <= water + 2 && level.getBlockState(plank).canBeReplaced()) {
				level.setBlock(plank, Blocks.SPRUCE_SLAB.defaultBlockState(), Block.UPDATE_CLIENTS);
			}
		}

		// The cache: 2 under a Dig Spot at the high middle of the sandbar.
		BlockPos digTop = surface(level, mark, -1, -1).below();
		BlockPos chest = digTop.below(2);
		level.setBlock(digTop.below(), sand, Block.UPDATE_CLIENTS);
		level.setBlock(chest, Blocks.CHEST.defaultBlockState().setValue(ChestBlock.FACING, Direction.Plane.HORIZONTAL.getRandomDirection(random)),
				Block.UPDATE_CLIENTS);
		RandomizableContainer.setBlockEntityLootTable(level, random, chest, CASTAWAY_LOOT);
		level.setBlock(digTop, TreasureFeature.DIG_SPOT.defaultBlockState(), Block.UPDATE_CLIENTS);
		return chest;
	}

	/** The first open block above the sand at this offset from the mark. */
	private static BlockPos surface(ServerLevel level, BlockPos mark, int dx, int dz) {
		return level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, mark.offset(dx, 0, dz));
	}

	// ---------- Sunken wrecks ----------

	private static BlockPos sinkWreck(ServerLevel level, BlockPos mark) {
		RandomSource random = level.getRandom();
		Identifier id = Identifier.withDefaultNamespace(WRECKS.get(random.nextInt(WRECKS.size())));
		Optional<StructureTemplate> found = level.getStructureTemplateManager().get(id);
		if (found.isEmpty()) {
			OnePieceMod.LOGGER.warn("Treasure wreck template {} is missing", id);
			return loaded(level, mark.getX(), mark.getZ(), mark.getX(), mark.getZ()) ? seaFloorChest(level, mark, random) : null;
		}
		StructureTemplate template = found.get();
		Rotation rotation = Rotation.getRandom(random);
		StructurePlaceSettings settings = new StructurePlaceSettings().setRotation(rotation)
				.addProcessor(BlockIgnoreProcessor.STRUCTURE_AND_AIR);

		// Centre the wreck on the X.
		BoundingBox box = template.getBoundingBox(settings, BlockPos.ZERO);
		BlockPos origin = mark.offset(-(box.minX() + box.maxX()) / 2, 0, -(box.minZ() + box.maxZ()) / 2);
		box = template.getBoundingBox(settings, origin);
		if (!loaded(level, box.minX() - 1, box.minZ() - 1, box.maxX() + 1, box.maxZ() + 1)) {
			return null;
		}

		// Settle it on the lowest part of the sea floor under it, a little sunk into the sand.
		int floor = Integer.MAX_VALUE;
		for (int i = 0; i <= 2; i++) {
			for (int j = 0; j <= 2; j++) {
				int x = box.minX() + (box.maxX() - box.minX()) * i / 2;
				int z = box.minZ() + (box.maxZ() - box.minZ()) * j / 2;
				floor = Math.min(floor, level.getHeight(Heightmap.Types.OCEAN_FLOOR, x, z));
			}
		}
		origin = new BlockPos(origin.getX(), floor - 2, origin.getZ());
		template.placeInWorld(level, origin, origin, settings, random, Block.UPDATE_CLIENTS);

		// The wreck's chests are marked with data structure blocks; the chest sits under each mark.
		BlockPos treasure = null;
		BlockPos any = null;
		for (StructureTemplate.StructureBlockInfo info : template.filterBlocks(origin, settings, Blocks.STRUCTURE_BLOCK)) {
			if (info.nbt() == null) {
				continue;
			}
			String marker = info.nbt().getStringOr("metadata", "");
			BlockPos chest = info.pos().below();
			ResourceKey<LootTable> table = switch (marker) {
				case "treasure_chest" -> WRECK_LOOT;
				case "map_chest" -> WRECK_MAP_LOOT;
				case "supply_chest" -> WRECK_SUPPLY_LOOT;
				default -> null;
			};
			if (table == null || !(level.getBlockEntity(chest) instanceof RandomizableContainerBlockEntity)) {
				continue;
			}
			RandomizableContainer.setBlockEntityLootTable(level, random, chest, table);
			any = chest;
			if (table == WRECK_LOOT) {
				treasure = chest;
			}
		}
		if (treasure == null) {
			treasure = any;
		}
		// No chest survived in this wreck: leave one on the sea floor in the middle of it.
		return treasure != null ? treasure : seaFloorChest(level, mark, random);
	}

	private static BlockPos seaFloorChest(ServerLevel level, BlockPos mark, RandomSource random) {
		BlockPos chest = level.getHeightmapPos(Heightmap.Types.OCEAN_FLOOR, mark);
		level.setBlock(chest, Blocks.CHEST.defaultBlockState().setValue(ChestBlock.WATERLOGGED,
				level.getFluidState(chest).isSource()), Block.UPDATE_CLIENTS);
		RandomizableContainer.setBlockEntityLootTable(level, random, chest, WRECK_LOOT);
		return chest;
	}
}
