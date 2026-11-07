package com.onepiecemod.ship.client;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

import org.joml.Matrix4fc;
import org.joml.Vector3f;

import com.mojang.blaze3d.vertex.PoseStack;

import net.fabricmc.fabric.api.client.renderer.v1.Renderer;
import net.fabricmc.fabric.api.client.renderer.v1.mesh.Mesh;
import net.fabricmc.fabric.api.client.renderer.v1.mesh.MeshView;
import net.fabricmc.fabric.api.client.renderer.v1.mesh.MutableMesh;
import net.fabricmc.fabric.api.client.renderer.v1.mesh.QuadEmitter;

import it.unimi.dsi.fastutil.ints.IntList;

import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.block.BlockModelRenderState;
import net.minecraft.client.renderer.block.BlockModelResolver;
import net.minecraft.client.renderer.block.dispatch.BlockStateModelPart;
import net.minecraft.client.renderer.block.model.BlockDisplayContext;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.resources.model.geometry.BakedQuad;
import net.minecraft.client.resources.model.sprite.Material;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.LightCoordsUtil;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.ship.ShipFeature;
import com.onepiecemod.ship.ShipLayout;

/**
 * A ship's blocks, ready to draw fast.
 *
 * Drawing thousands of blocks one at a time is slow, and most of their faces press against other blocks where nobody
 * can see them. So, once per ship, every block's model is copied into a few big merged meshes (one per kind of
 * material: solid/cut-out, see-through, tinted...), already moved to its spot on the ship, with the hidden faces
 * between solid blocks left out. A whole ship then takes a handful of draw calls instead of thousands.
 *
 * With Fabric's renderer installed (always, with Fabric API) block models hand over their quads as a Fabric mesh instead
 * of vanilla model parts, so those are merged into one Fabric mesh per batch the same way.
 *
 * Blocks that draw themselves (chests, banners, painted flags) are left "loose" and drawn one by one as before.
 * If the game's block model internals ever change and the copy can't be made, every block falls back to loose.
 */
final class ShipMesh {
	private static final BlockDisplayContext BLOCK_DISPLAY_CONTEXT = BlockDisplayContext.create();

	/** One draw call: vanilla model parts, or (with Fabric's renderer) a merged Fabric mesh. */
	private record Batch(RenderType renderType, int[] tints, int blockLight, List<BlockStateModelPart> parts, Mesh mesh) {
	}

	private final List<Batch> batches;
	private final int[] loose;
	private final Map<Integer, BlockModelRenderState> looseModels;

	private ShipMesh(List<Batch> batches, int[] loose, Map<Integer, BlockModelRenderState> looseModels) {
		this.batches = batches;
		this.loose = loose;
		this.looseModels = looseModels;
	}

	/** Indexes (into ShipLayout.blocks) of blocks drawn one by one. */
	int[] loose() {
		return loose;
	}

	BlockModelRenderState looseModel(int index) {
		return looseModels.get(index);
	}

	void submitMerged(PoseStack poseStack, SubmitNodeCollector collector, int lightCoords) {
		for (Batch batch : batches) {
			int light = LightCoordsUtil.max(lightCoords, batch.blockLight());
			if (batch.mesh() != null) {
				RenderType renderType = batch.renderType();
				collector.submitBlockModel(poseStack, layer -> renderType, renderType.hasBlending(), List.of(), batch.mesh(), batch.tints(),
						light, OverlayTexture.NO_OVERLAY, 0);
			} else {
				collector.submitBlockModel(poseStack, batch.renderType(), batch.parts(), batch.tints(), light, OverlayTexture.NO_OVERLAY, 0);
			}
		}
	}

	// ---- Building ----

	private static Field partsField;
	private static Field renderTypeField;
	private static Field tintsField;
	private static Field transformField;
	private static Field specialField;
	/** Added by Fabric's renderer: where a block's quads go when the model is drawn through Fabric (null without it). */
	private static Field meshField;
	private static boolean reflectionTried;
	private static boolean reflectionWorks;

	private static synchronized boolean reflection() {
		if (!reflectionTried) {
			reflectionTried = true;
			try {
				partsField = field("modelParts");
				renderTypeField = field("renderType");
				tintsField = field("tintLayers");
				transformField = field("transformation");
				specialField = field("specialRenderer");
				try {
					meshField = field("mesh");
				} catch (NoSuchFieldException e) {
					meshField = null;
				}
				reflectionWorks = true;
			} catch (ReflectiveOperationException | RuntimeException e) {
				OnePieceMod.LOGGER.warn("Ship meshes can't be merged on this game version; drawing ships block by block. ({})", e.toString());
			}
		}
		return reflectionWorks;
	}

	private static Field field(String name) throws NoSuchFieldException {
		Field field = BlockModelRenderState.class.getDeclaredField(name);
		field.setAccessible(true);
		return field;
	}

	static ShipMesh build(ShipLayout layout, BlockModelResolver resolver) {
		// Full, solid blocks (planks, wool...) hide the faces of their neighbours that touch them.
		Set<BlockPos> solid = new HashSet<>();
		for (ShipLayout.ShipBlock block : layout.blocks) {
			if (block.state().isSolidRender()) {
				solid.add(block.pos());
			}
		}
		boolean merge = reflection();
		Map<String, Batch> batches = new LinkedHashMap<>();
		Map<String, List<BakedQuad>> quads = new HashMap<>();
		Map<String, Integer> flags = new HashMap<>();
		Map<String, Material.Baked> particles = new HashMap<>();
		Map<String, MutableMesh> meshes = new HashMap<>();
		List<Integer> loose = new ArrayList<>();
		Map<Integer, BlockModelRenderState> looseModels = new HashMap<>();

		for (int i = 0; i < layout.blocks.size(); i++) {
			ShipLayout.ShipBlock block = layout.blocks.get(i);
			BlockPos pos = block.pos();
			if (block.state().is(ShipFeature.JOLLY_ROGER)) {
				loose.add(i); // Painted flags are drawn by FlagDrawing.
				continue;
			}
			if (solid.contains(pos) && allSidesSolid(solid, pos)) {
				continue; // Buried inside a thick hull: never seen.
			}
			BlockModelRenderState model = new BlockModelRenderState();
			resolver.update(model, block.state(), BLOCK_DISPLAY_CONTEXT);
			if (model.isEmpty()) {
				continue;
			}
			if (!merge || !mergeInto(model, pos, solid, batches, quads, flags, particles, meshes)) {
				loose.add(i);
				looseModels.put(i, model);
			}
		}

		List<Batch> result = new ArrayList<>();
		for (Map.Entry<String, Batch> entry : batches.entrySet()) {
			Batch batch = entry.getValue();
			MutableMesh mesh = meshes.get(entry.getKey());
			if (mesh != null) {
				if (mesh.size() > 0) {
					result.add(new Batch(batch.renderType(), batch.tints(), batch.blockLight(), List.of(), mesh.immutableCopy()));
				}
				continue;
			}
			BlockStateModelPart part = new MergedPart(quads.get(entry.getKey()), flags.get(entry.getKey()), particles.get(entry.getKey()));
			result.add(new Batch(batch.renderType(), batch.tints(), batch.blockLight(), List.of(part), null));
		}
		return new ShipMesh(result, loose.stream().mapToInt(Integer::intValue).toArray(), looseModels);
	}

	/** Copies one block's quads into the right batch. False if the block must be drawn on its own. */
	@SuppressWarnings("unchecked")
	private static boolean mergeInto(BlockModelRenderState model, BlockPos pos, Set<BlockPos> solid, Map<String, Batch> batches,
			Map<String, List<BakedQuad>> quads, Map<String, Integer> flags, Map<String, Material.Baked> particles,
			Map<String, MutableMesh> meshes) {
		try {
			if (specialField.get(model) != null) {
				return false; // Chests, banners and the like draw themselves.
			}
			List<BlockStateModelPart> parts = (List<BlockStateModelPart>) partsField.get(model);
			RenderType renderType = (RenderType) renderTypeField.get(model);
			IntList tintList = (IntList) tintsField.get(model);
			Matrix4fc transform = (Matrix4fc) transformField.get(model);
			MeshView fabricMesh = meshField == null ? null : (MeshView) meshField.get(model);
			boolean useMesh = (parts == null || parts.isEmpty()) && fabricMesh != null && fabricMesh.size() > 0;
			if ((parts == null && !useMesh) || renderType == null) {
				return false;
			}
			int[] tints = tintList == null || tintList.isEmpty() ? BlockModelRenderState.EMPTY_TINTS : tintList.toIntArray();
			String key = (useMesh ? "mesh|" : "") + renderType + "|" + Arrays.toString(tints) + "|" + model.blockLightCoords;
			batches.computeIfAbsent(key, k -> new Batch(renderType, tints, model.blockLightCoords, List.of(), null));
			if (useMesh) {
				mergeMesh(fabricMesh, meshes.computeIfAbsent(key, k -> Renderer.get().mutableMesh()), transform, pos, solid);
				return true;
			}
			List<BakedQuad> into = quads.computeIfAbsent(key, k -> new ArrayList<>());
			// The ship turns around the middle of its centre block (see ShipRenderer).
			float dx = pos.getX() - 0.5f, dy = pos.getY(), dz = pos.getZ() - 0.5f;
			for (BlockStateModelPart part : parts) {
				flags.merge(key, part.materialFlags(), (a, b) -> a | b);
				particles.putIfAbsent(key, part.particleMaterial());
				for (BakedQuad quad : part.getQuads(null)) {
					into.add(moved(quad, transform, dx, dy, dz));
				}
				for (Direction direction : Direction.values()) {
					if (solid.contains(pos.relative(direction))) {
						continue; // This face presses against a solid block: hidden.
					}
					for (BakedQuad quad : part.getQuads(direction)) {
						into.add(moved(quad, transform, dx, dy, dz));
					}
				}
			}
			return true;
		} catch (ReflectiveOperationException | ClassCastException e) {
			return false;
		}
	}

	/** Copies a block's Fabric quads into a ship batch, moved to the block's spot, leaving out faces hidden by solid neighbours. */
	private static void mergeMesh(MeshView from, MutableMesh into, Matrix4fc transform, BlockPos pos, Set<BlockPos> solid) {
		float dx = pos.getX() - 0.5f, dy = pos.getY(), dz = pos.getZ() - 0.5f;
		QuadEmitter emitter = into.emitter();
		Vector3f corner = new Vector3f();
		from.forEach(quad -> {
			Direction cull = quad.cullFace();
			if (cull != null && solid.contains(pos.relative(cull))) {
				return; // This face presses against a solid block: hidden.
			}
			emitter.copyFrom(quad);
			for (int i = 0; i < 4; i++) {
				quad.copyPos(i, corner);
				if (transform != null) {
					transform.transformPosition(corner);
				}
				emitter.pos(i, corner.x + dx, corner.y + dy, corner.z + dz);
			}
			emitter.cullFace(null);
			emitter.emit();
		});
	}

	private static BakedQuad moved(BakedQuad quad, Matrix4fc transform, float dx, float dy, float dz) {
		return new BakedQuad(move(quad.position0(), transform, dx, dy, dz), move(quad.position1(), transform, dx, dy, dz),
				move(quad.position2(), transform, dx, dy, dz), move(quad.position3(), transform, dx, dy, dz),
				quad.packedUV0(), quad.packedUV1(), quad.packedUV2(), quad.packedUV3(), quad.direction(), quad.materialInfo());
	}

	private static Vector3f move(org.joml.Vector3fc position, Matrix4fc transform, float dx, float dy, float dz) {
		Vector3f moved = new Vector3f(position);
		if (transform != null) {
			transform.transformPosition(moved);
		}
		return moved.add(dx, dy, dz);
	}

	private static boolean allSidesSolid(Set<BlockPos> solid, BlockPos pos) {
		for (Direction direction : Direction.values()) {
			if (!solid.contains(pos.relative(direction))) {
				return false;
			}
		}
		return true;
	}

	/** All the quads of one batch, as a single model part. */
	private record MergedPart(List<BakedQuad> quads, int flags, Material.Baked particle) implements BlockStateModelPart {
		@Override
		public List<BakedQuad> getQuads(Direction direction) {
			return direction == null ? quads : List.of();
		}

		@Override
		public boolean useAmbientOcclusion() {
			return false;
		}

		@Override
		public Material.Baked particleMaterial() {
			return particle;
		}

		@Override
		public int materialFlags() {
			return flags;
		}

		@Override
		public boolean equals(Object other) {
			return this == other;
		}

		@Override
		public int hashCode() {
			return Objects.hashCode(System.identityHashCode(this));
		}
	}
}
