package com.onepiecemod.world;

import com.onepiecemod.world.mixin.JigsawStructureAccessor;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.VerticalAnchor;
import net.minecraft.world.level.levelgen.heightproviders.ConstantHeight;
import net.minecraft.world.level.levelgen.heightproviders.HeightProvider;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.level.levelgen.structure.TerrainAdjustment;
import net.minecraft.world.level.levelgen.structure.structures.JigsawStructure;

/**
 * Clears the hill above our land and coast builds before they are placed, and slopes it back round their edge.
 * <p>
 * StructureSiteRules sets coast builds down to sea level (up to 24 blocks) and settles land builds into slopes. The
 * vanilla beard_thin terrain adaptation only carves about a dozen blocks above the bottom of the template (which for
 * our builds is a few blocks under their ground), so on a high shore the build ended up in a dug-out pit with the
 * grass cap of the hill hanging over it like a cave roof (ryan 2026-11-02, Gray Terminal under the hill of a castle).
 * <p>
 * Here, inside the footprint every natural block above the build's ground row is removed (the build places its own
 * ground, hills and houses right after), and within {@link #MARGIN} blocks round it the terrain is cut down to a
 * slope rising 3 blocks per 2 out from the build, its top dressed with the hill's own surface block. Nothing hangs
 * over the build any more. The margin is the 12 blocks a beard-adapted structure already owns round its pieces,
 * so every chunk touched here is one the game hands this structure to place in.
 */
public final class TerrainCut {
	private TerrainCut() {}

	private static final int MARGIN = 12;
	/** -Donepiece.terrainCut=false turns it off, for comparing worlds. */
	private static final boolean ENABLED = !"false".equals(System.getProperty("onepiece.terrainCut"));

	public static void before(StructureStart start, WorldGenLevel level, BoundingBox chunkBox) {
		if (!ENABLED) return;
		Structure structure = start.getStructure();
		TerrainAdjustment adj = structure.terrainAdaptation();
		// beard builds, and builds with no terrain adaptation at all (Tower of Justice): those have no 12-block margin of
		// their own, so only the margin inside chunks the build already touches gets sloped, but nothing hangs over it
		if (adj != TerrainAdjustment.BEARD_THIN && adj != TerrainAdjustment.BEARD_BOX && adj != TerrainAdjustment.NONE) return;
		if (!(structure instanceof JigsawStructure jigsaw)) return;
		JigsawStructureAccessor acc = (JigsawStructureAccessor) (Object) jigsaw;
		if (acc.onepiece$projectStartToHeightmap().isEmpty()) return; // fixed-height builds (caves) stay as they are
		Identifier id = level.registryAccess().lookupOrThrow(Registries.STRUCTURE).getKey(structure);
		StructureSiteRules.Site site = StructureSiteRules.siteOf(id);
		if (site != StructureSiteRules.Site.LAND && site != StructureSiteRules.Site.COAST) return;
		List<StructurePiece> pieces = start.getPieces();
		if (pieces.isEmpty()) return;
		HeightProvider hp = acc.onepiece$startHeight();
		if (!(hp instanceof ConstantHeight c) || !(c.getValue() instanceof VerticalAnchor.Absolute a)) return;
		// the tiler writes start_height = -(canvas ground row above the template bottom), see tools/landmarks/tiler.py
		int ground = pieces.get(0).getBoundingBox().minY() - a.y();

		List<BoundingBox> boxes = new ArrayList<>();
		for (StructurePiece p : pieces) {
			BoundingBox b = p.getBoundingBox();
			if (b.maxX() + MARGIN >= chunkBox.minX() && b.minX() - MARGIN <= chunkBox.maxX()
					&& b.maxZ() + MARGIN >= chunkBox.minZ() && b.minZ() - MARGIN <= chunkBox.maxZ()) boxes.add(b);
		}
		if (boxes.isEmpty()) return;

		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		BlockState air = Blocks.AIR.defaultBlockState();
		for (int x = chunkBox.minX(); x <= chunkBox.maxX(); x++) {
			for (int z = chunkBox.minZ(); z <= chunkBox.maxZ(); z++) {
				double d = Double.MAX_VALUE;
				for (BoundingBox b : boxes) {
					int dx = Math.max(0, Math.max(b.minX() - x, x - b.maxX()));
					int dz = Math.max(0, Math.max(b.minZ() - z, z - b.maxZ()));
					d = Math.min(d, Math.sqrt(dx * dx + dz * dz));
					if (d == 0) break;
				}
				if (d > MARGIN) continue;
				int allowed = ground + (int) Math.ceil(d * 1.5);
				int top = level.getHeight(Heightmap.Types.WORLD_SURFACE_WG, x, z) - 1;
				if (top <= allowed) continue;
				BlockState surface = level.getBlockState(pos.set(x, top, z));
				for (int y = top; y > allowed; y--) {
					pos.setY(y);
					if (!level.getBlockState(pos).isAir()) level.setBlock(pos, air, 2);
				}
				if (d == 0) continue; // the build lays its own ground here
				// the cut slope gets the hill's surface (grass on dirt or rock), not a raw face of dirt and stone
				pos.setY(allowed);
				BlockState now = level.getBlockState(pos);
				if (surface.is(Blocks.GRASS_BLOCK) || surface.is(Blocks.PODZOL) || surface.is(Blocks.MYCELIUM)) {
					if (now.is(BlockTags.DIRT) || now.is(BlockTags.BASE_STONE_OVERWORLD) || now.is(Blocks.GRAVEL)) level.setBlock(pos, surface, 2);
				} else if (surface.is(Blocks.SAND) || surface.is(Blocks.RED_SAND)) {
					if ((now.is(BlockTags.DIRT) || now.is(BlockTags.BASE_STONE_OVERWORLD))
							&& !level.getBlockState(pos.below()).isAir()) level.setBlock(pos, surface, 2);
				}
			}
		}
	}
}
