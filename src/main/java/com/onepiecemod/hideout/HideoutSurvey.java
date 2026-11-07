package com.onepiecemod.hideout;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.block.BarrelBlock;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.CampfireBlock;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BedPart;

import com.onepiecemod.building.BuildingRegistry;
import com.onepiecemod.building.Buildings;
import com.onepiecemod.building.Multiblock;
import com.onepiecemod.ship.ShipFeature;

/**
 * What the crew has built inside the claim: beds, campfires, cannons, storage, a kitchen, and finished
 * buildings (Watchtower, Dojo, Shipyard...). The flag walks the claim one slice per tick, so a full
 * look-over costs almost nothing and takes about 3 seconds.
 */
public class HideoutSurvey {
	/** Blocks above and below the flag that count as part of the hideout. */
	static final int BELOW = 12;
	static final int ABOVE = 20;

	public final List<BlockPos> beds = new ArrayList<>();
	public final List<BlockPos> campfires = new ArrayList<>();
	public final List<BlockPos> cannons = new ArrayList<>();
	public int storage;
	public boolean craftingTable;
	public boolean kitchen;
	public int lights;
	/** Ids of finished buildings in the claim, like "alarm_bell" (Watchtower) or "treasure_vault". */
	public final Set<String> buildings = new HashSet<>();

	/** Looks at one column slab (all z and y for this x offset). */
	void scanSlice(ServerLevel level, BlockPos flag, int dx) {
		int r = Hideouts.RADIUS;
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		for (int dz = -r; dz <= r; dz++) {
			if (dx * dx + dz * dz > r * r) {
				continue;
			}
			int x = flag.getX() + dx;
			int z = flag.getZ() + dz;
			if (!level.hasChunkAt(pos.set(x, flag.getY(), z))) {
				continue;
			}
			for (int y = flag.getY() - BELOW; y <= flag.getY() + ABOVE; y++) {
				pos.set(x, y, z);
				BlockState state = level.getBlockState(pos);
				if (state.isAir()) {
					continue;
				}
				look(state, pos);
			}
		}
	}

	private void look(BlockState state, BlockPos pos) {
		if (state.getBlock() instanceof BedBlock) {
			if (state.getValue(BedBlock.PART) == BedPart.HEAD) {
				beds.add(pos.immutable());
			}
		} else if (state.getBlock() instanceof CampfireBlock) {
			campfires.add(pos.immutable());
		} else if (state.is(ShipFeature.CANNON)) {
			cannons.add(pos.immutable());
		} else if (state.getBlock() instanceof ChestBlock || state.getBlock() instanceof BarrelBlock) {
			storage++;
		} else if (state.is(Blocks.CRAFTING_TABLE) || state.is(Blocks.CRAFTER)) {
			craftingTable = true;
		} else if (state.is(Blocks.FURNACE) || state.is(Blocks.SMOKER) || state.is(Blocks.BLAST_FURNACE)) {
			kitchen = true;
		} else if (state.getLightEmission() >= 10 || state.is(BlockTags.CANDLES)) {
			lights++;
		} else {
			// Mod stoves and galley blocks count as a kitchen too.
			String name = BuiltInRegistries.BLOCK.getKey(state.getBlock()).getPath();
			if (name.contains("stove") || name.contains("galley") || name.contains("oven")) {
				kitchen = true;
			}
		}
	}

	/** After the last slice: which buildings in the claim are finished. */
	void checkBuildings(ServerLevel level, BlockPos flag) {
		for (BuildingRegistry.Entry entry : BuildingRegistry.all(level)) {
			BlockPos pos = entry.pos();
			double dx = pos.getX() - flag.getX();
			double dz = pos.getZ() - flag.getZ();
			if (dx * dx + dz * dz > Hideouts.RADIUS * Hideouts.RADIUS || !level.isLoaded(pos)) {
				continue;
			}
			Multiblock building = Buildings.get(entry.type());
			if (building != null && level.getBlockState(pos).is(building.core()) && building.check(level, pos).complete()) {
				buildings.add(entry.type());
			}
		}
	}

	/** Finished buildings other than the Watchtower (which has its own step). */
	public int otherBuildings() {
		int count = 0;
		for (String id : buildings) {
			if (!id.equals("alarm_bell")) {
				count++;
			}
		}
		return count;
	}
}
