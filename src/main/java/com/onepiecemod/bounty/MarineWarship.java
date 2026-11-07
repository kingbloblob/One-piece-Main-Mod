package com.onepiecemod.bounty;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;

import com.onepiecemod.ship.DecorBlock;
import com.onepiecemod.ship.HelmBlock;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipFeature;
import com.onepiecemod.ship.ShipLayout;

/**
 * The Marine warship that shows up offshore during a Navy raid. It is a normal ship from the ships feature,
 * built from blocks in code: a white and blue hull, two masts with white sails, and cannons on both sides.
 * Pirates can climb aboard and steal it. If nobody does, it sails away when the raid ends.
 */
public class MarineWarship {
	/** Put on the warship so a leftover one (for example after a server restart) can be cleaned up. */
	public static final String TAG = "onepiece_navy_warship";

	private static final float WATERLINE = 1.5f;

	/** The warship as it looks in the show (template marine_warship), or the block-code one below if that is missing. */
	public static ShipLayout layout(ServerLevel level) {
		ShipLayout fromTemplate = com.onepiecemod.ship.ShipTemplates.layout(level, "marine_warship");
		return fromTemplate != null ? fromTemplate : layout();
	}

	/** The ship's blocks, relative to its centre, with the bow pointing south (+Z). */
	public static ShipLayout layout() {
		List<ShipLayout.ShipBlock> blocks = new ArrayList<>();
		BlockState keel = Blocks.DARK_OAK_PLANKS.defaultBlockState();
		BlockState hull = Blocks.CONCRETE.white().defaultBlockState();
		BlockState stripe = Blocks.CONCRETE.blue().defaultBlockState();
		BlockState deck = Blocks.SPRUCE_PLANKS.defaultBlockState();
		BlockState mast = Blocks.OAK_LOG.defaultBlockState();
		BlockState sail = Blocks.WOOL.white().defaultBlockState();
		BlockState sailMark = Blocks.WOOL.blue().defaultBlockState();

		// Keel along the bottom.
		for (int z = -6; z <= 6; z++) {
			for (int x = -1; x <= 1; x++) {
				add(blocks, x, 0, z, keel);
			}
		}
		// Hull sides (white with a blue stripe) and the deck.
		for (int z = -7; z <= 7; z++) {
			int halfWidth = Math.abs(z) >= 6 ? 1 : 2; // Narrow at the bow and stern.
			for (int x = -halfWidth; x <= halfWidth; x++) {
				boolean edge = Math.abs(x) == halfWidth || Math.abs(z) == 7;
				add(blocks, x, 1, z, edge ? stripe : deck);
				if (edge) {
					add(blocks, x, 2, z, hull);
				}
			}
		}
		// Two masts with square sails. The blue blocks in the middle are the Marine mark.
		for (int y = 2; y <= 10; y++) {
			add(blocks, 0, y, -2, mast);
		}
		for (int y = 2; y <= 8; y++) {
			add(blocks, 0, y, 4, mast);
		}
		for (int x = -3; x <= 3; x++) {
			for (int y = 5; y <= 9; y++) {
				add(blocks, x, y, -1, (x == 0 && y == 7) || (Math.abs(x) == 1 && y == 7) ? sailMark : sail);
			}
		}
		for (int x = -2; x <= 2; x++) {
			for (int y = 5; y <= 7; y++) {
				add(blocks, x, y, 5, y == 6 && x == 0 ? sailMark : sail);
			}
		}
		// Cannons poking over both sides.
		for (int z : new int[] {-4, 1}) {
			add(blocks, 2, 3, z, ShipFeature.CANNON.defaultBlockState().setValue(DecorBlock.FACING, Direction.EAST));
			add(blocks, -2, 3, z, ShipFeature.CANNON.defaultBlockState().setValue(DecorBlock.FACING, Direction.WEST));
		}
		// The wheel near the stern, facing the bow.
		BlockPos helm = new BlockPos(0, 2, -5);
		add(blocks, helm.getX(), helm.getY(), helm.getZ(), ShipFeature.HELM.defaultBlockState().setValue(HelmBlock.FACING, Direction.SOUTH));

		return new ShipLayout(blocks, List.of(), helm, Direction.SOUTH, WATERLINE);
	}

	private static void add(List<ShipLayout.ShipBlock> blocks, int x, int y, int z, BlockState state) {
		BlockPos pos = new BlockPos(x, y, z);
		blocks.removeIf(block -> block.pos().equals(pos)); // Later blocks replace earlier ones.
		blocks.add(new ShipLayout.ShipBlock(pos, state, Optional.empty()));
	}

	/**
	 * Puts a warship on open water 28 to 56 blocks from the raid, side-on so its cannons face the shore.
	 * Returns null if there is no deep enough water nearby (an inland raid has no warship).
	 */
	public static ShipEntity spawn(ServerLevel level, BlockPos center, RandomSource random) {
		ShipLayout layout = layout(level);
		// The show-accurate warship is about 38 blocks long, so it needs more open water around it than the old one.
		int reach = Math.max(7, Math.max(layout.max.getX() - layout.min.getX(), layout.max.getZ() - layout.min.getZ()) / 2 + 1);
		for (int attempt = 0; attempt < 24; attempt++) {
			double angle = random.nextDouble() * Math.PI * 2;
			int distance = 28 + reach + random.nextInt(29);
			int x = Mth.floor(center.getX() + Math.cos(angle) * distance);
			int z = Mth.floor(center.getZ() + Math.sin(angle) * distance);
			Integer surface = deepWaterSurface(level, x, z);
			if (surface == null
					|| deepWaterSurface(level, x + reach, z) == null || deepWaterSurface(level, x - reach, z) == null
					|| deepWaterSurface(level, x, z + reach) == null || deepWaterSurface(level, x, z - reach) == null) {
				continue;
			}

			ShipEntity ship = ShipFeature.SHIP.create(level, EntitySpawnReason.EVENT);
			if (ship == null) {
				return null;
			}
			ship.setLayout(layout);
			// Turn the ship side-on to the raid, so the cannons point at it.
			float towardRaid = (float) Math.toDegrees(Math.atan2(-(center.getX() - x), center.getZ() - z));
			ship.snapTo(x + 0.5, surface - layout.waterline, z + 0.5, towardRaid + 90.0f, 0);
			level.addFreshEntity(ship);
			ship.addTag(TAG); // After adding, so the leftover-warship cleanup doesn't remove it as it arrives.
			return ship;
		}
		return null;
	}

	/** The Y of the water's surface if this column is open sea at least 4 blocks deep, otherwise null. */
	private static Integer deepWaterSurface(ServerLevel level, int x, int z) {
		if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
			return null;
		}
		int top = level.getHeight(Heightmap.Types.WORLD_SURFACE, x, z);
		int floor = level.getHeight(Heightmap.Types.OCEAN_FLOOR, x, z);
		BlockPos water = new BlockPos(x, top - 1, z);
		if (!level.getFluidState(water).is(FluidTags.WATER) || top - floor < 4) {
			return null;
		}
		return top;
	}
}
