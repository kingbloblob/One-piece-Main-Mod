package com.onepiecemod.ship.client;

import com.onepiecemod.client.RenderGuard;

import java.util.Map;
import java.util.WeakHashMap;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;

import net.minecraft.world.phys.AABB;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.block.BlockModelRenderState;
import net.minecraft.client.renderer.block.BlockModelResolver;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.core.BlockPos;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.material.FluidState;

import com.onepiecemod.ship.FlagBlock;
import com.onepiecemod.ship.FlagDesign;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipFeature;
import com.onepiecemod.ship.ShipHold;
import com.onepiecemod.ship.ShipLayout;

/**
 * Draws a sailing ship: every one of its blocks, turned to match the ship's heading, plus its painted flags.
 */
public class ShipRenderer extends EntityRenderer<ShipEntity, ShipRenderer.State> {
	/** Each ship's blocks, merged into a few big meshes, worked out once per ship (see ShipMesh). */
	private final Map<ShipLayout, ShipMesh> meshes = new WeakHashMap<>();
	private final BlockModelResolver blockModelResolver;

	public static class State extends EntityRenderState {
		public ShipLayout layout = ShipLayout.EMPTY;
		public ShipMesh mesh;
		public float rotation;
		public float time;
		/** Where the sea's surface is, in the ship's own height, and the hold cells it would show in (x, z pairs). */
		public float seaSurface;
		public int[] dryCells = new int[0];
		/** A coated ship's bubble (deepsea.ShipDive): centre and radii in the ship's own grid, or 0 radius for none. */
		public float bubbleX, bubbleY, bubbleZ, bubbleRX, bubbleRY, bubbleRZ;
	}

	/** The coated ship's bubble: a soft see-through blue skin. */
	private static final net.minecraft.resources.Identifier BUBBLE_TEXTURE = com.onepiecemod.OnePieceMod.id("textures/entity/ship_bubble.png");
	private static final int BUBBLE_COLOR = 0x50BEEBFF;
	private static final int BUBBLE_RINGS = 16, BUBBLE_SEGMENTS = 32;

	public ShipRenderer(EntityRendererProvider.Context context) {
		super(context);
		this.blockModelResolver = context.getBlockModelResolver();
		this.shadowRadius = 0; // A shadow the size of a ship looks odd on water.
	}

	@Override
	protected AABB getBoundingBoxForCulling(ShipEntity ship, float partialTick) {
		// A turned ship pokes out past its hit box at the corners, so draw it a bit earlier.
		return super.getBoundingBoxForCulling(ship, partialTick).inflate(ship.getBbWidth() * 0.25, 0, ship.getBbWidth() * 0.25);
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(ShipEntity ship, State state, float partialTick) {
		super.extractRenderState(ship, state, partialTick);
		RenderGuard.run("ship state", () -> {
			state.layout = ship.getLayout();
			state.mesh = meshes.computeIfAbsent(state.layout, layout -> ShipMesh.build(layout, blockModelResolver));
			state.rotation = ship.rotationSinceBuilt(partialTick);
			state.time = ship.tickCount + partialTick;
			extractDryHold(ship, state);
			extractBubble(ship, state);
		});
	}

	private static void maskQuad(PoseStack.Pose pose, VertexConsumer out, float x0, float y, float z0, boolean flip) {
		float[][] corners = {{x0, z0}, {x0, z0 + 1}, {x0 + 1, z0 + 1}, {x0 + 1, z0}};
		for (int i = 0; i < 4; i++) {
			float[] corner = corners[flip ? 3 - i : i];
			out.addVertex(pose, corner[0], y, corner[1]).setColor(-1).setUv(0, 0).setOverlay(OverlayTexture.NO_OVERLAY).setLight(0xF000F0).setNormal(pose, 0, flip ? -1 : 1, 0);
		}
	}

	private static void extractBubble(ShipEntity ship, State state) {
		state.bubbleRX = 0;
		ShipLayout layout = state.layout;
		if (layout.size() == 0 || !com.onepiecemod.deepsea.ShipDive.isCoated(ship)) {
			return;
		}
		state.bubbleX = (layout.min.getX() + layout.max.getX()) / 2.0f;
		state.bubbleY = (layout.min.getY() + layout.max.getY() + 1) / 2.0f;
		state.bubbleZ = (layout.min.getZ() + layout.max.getZ()) / 2.0f;
		state.bubbleRX = (float) com.onepiecemod.deepsea.ShipDive.bubbleRadius(layout.max.getX() - layout.min.getX());
		state.bubbleRY = (float) com.onepiecemod.deepsea.ShipDive.bubbleRadius(layout.max.getY() - layout.min.getY());
		state.bubbleRZ = (float) com.onepiecemod.deepsea.ShipDive.bubbleRadius(layout.max.getZ() - layout.min.getZ());
	}

	/** One vertex of the bubble, at ring (0 = top) and segment, pointing outwards. */
	private static void bubbleVertex(PoseStack.Pose pose, VertexConsumer out, State state, int ring, int segment, int light) {
		float theta = (float) Math.PI * ring / BUBBLE_RINGS;
		float phi = (float) Math.PI * 2 * segment / BUBBLE_SEGMENTS;
		float nx = Mth.sin(theta) * Mth.cos(phi), ny = Mth.cos(theta), nz = Mth.sin(theta) * Mth.sin(phi);
		// The block grid is drawn half a block off (blocks sit at pos - 0.5), so the bubble is too.
		out.addVertex(pose, state.bubbleX - 0.5f + nx * state.bubbleRX, state.bubbleY + ny * state.bubbleRY, state.bubbleZ - 0.5f + nz * state.bubbleRZ)
				.setColor(BUBBLE_COLOR).setUv(segment / (float) BUBBLE_SEGMENTS * 4, ring / (float) BUBBLE_RINGS * 2)
				.setOverlay(OverlayTexture.NO_OVERLAY).setLight(light).setNormal(pose, nx, ny, nz);
	}

	/** Finds the hold cells the sea's surface cuts through, so submit can hide the water there (see ShipHold). */
	private static void extractDryHold(ShipEntity ship, State state) {
		state.dryCells = new int[0];
		ShipLayout layout = state.layout;
		if (layout.size() == 0) {
			return;
		}
		// The sea's surface at the ship: the top water block near her waterline.
		Level level = ship.level();
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		int top = Mth.floor(state.y + layout.waterline) + 2;
		float surface = Float.NaN;
		for (int y = top; y > top - 6; y--) {
			FluidState fluid = level.getFluidState(pos.set(Mth.floor(state.x), y, Mth.floor(state.z)));
			if (fluid.is(FluidTags.WATER)) {
				if (level.getFluidState(pos.above()).is(FluidTags.WATER)) {
					return; // Water above too: she's dived under the surface (deepsea.ShipDive), nothing to hide.
				}
				surface = y + fluid.getHeight(level, pos);
				break;
			}
		}
		if (Float.isNaN(surface)) {
			return;
		}
		state.seaSurface = (float) (surface - state.y);
		int layer = Mth.floor(state.seaSurface);
		ShipHold.Interior hold = ShipHold.interior(layout);
		int[] cells = new int[hold.sizeX() * hold.sizeZ() * 2];
		int n = 0;
		for (int x = hold.min().getX(); x < hold.min().getX() + hold.sizeX(); x++) {
			for (int z = hold.min().getZ(); z < hold.min().getZ() + hold.sizeZ(); z++) {
				if (hold.isDry(x, layer, z)) {
					cells[n++] = x;
					cells[n++] = z;
				}
			}
		}
		state.dryCells = java.util.Arrays.copyOf(cells, n);
	}

	@Override
	public void submit(State state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
		RenderGuard.run("ship", poseStack, () -> {
			ShipLayout layout = state.layout;
			Map<BlockPos, FlagDesign> flags = layout.flagMap();

			poseStack.pushPose();
			poseStack.rotate(Axis.YP.rotationDegrees(-state.rotation));
			// Most of the ship: a few big merged meshes (one per kind of material), already placed block by block.
			state.mesh.submitMerged(poseStack, collector, state.lightCoords);
			// Blocks that draw themselves (chests, signs...) and painted flags, one by one.
			for (int i : state.mesh.loose()) {
				ShipLayout.ShipBlock block = layout.blocks.get(i);
				BlockPos pos = block.pos();
				poseStack.pushPose();
				// The ship turns around the middle of its centre block.
				poseStack.translate(pos.getX() - 0.5, pos.getY(), pos.getZ() - 0.5);
				if (block.state().is(ShipFeature.JOLLY_ROGER)) {
					FlagDesign design = flags.get(pos);
					if (design != null) {
						FlagDrawing.submit(poseStack, collector, design, block.state().getValue(FlagBlock.FACING), state.lightCoords, state.time + pos.getX() * 7);
					}
				} else {
					BlockModelRenderState model = state.mesh.looseModel(i);
					if (model != null) {
						model.submit(poseStack, collector, state.lightCoords, OverlayTexture.NO_OVERLAY, 0);
					}
				}
				poseStack.popPose();
			}
			// Hide the sea's surface inside the hold, like a boat does (an invisible sheet that blocks the water behind it).
			if (state.dryCells.length > 0) {
				int[] cells = state.dryCells;
				float surface = state.seaSurface;
				collector.submitCustomGeometry(poseStack, RenderTypes.waterMask(), (pose, out) -> {
					for (int c = 0; c < cells.length; c += 2) {
						float x0 = cells[c] - 0.5f, z0 = cells[c + 1] - 0.5f;
						// Just above and just below the surface, both ways up, so it hides from the deck and from the hold.
						for (float y : new float[] {surface + 0.02f, surface - 0.02f}) {
							maskQuad(pose, out, x0, y, z0, false);
							maskQuad(pose, out, x0, y, z0, true);
						}
					}
				});
			}
			// A coated ship's bubble, drawn last so the ship shows through it.
			if (state.bubbleRX > 0) {
				int light = state.lightCoords;
				collector.submitCustomGeometry(poseStack, RenderTypes.entityTranslucent(BUBBLE_TEXTURE), (pose, out) -> {
					for (int ring = 0; ring < BUBBLE_RINGS; ring++) {
						for (int segment = 0; segment < BUBBLE_SEGMENTS; segment++) {
							bubbleVertex(pose, out, state, ring, segment, light);
							bubbleVertex(pose, out, state, ring + 1, segment, light);
							bubbleVertex(pose, out, state, ring + 1, segment + 1, light);
							bubbleVertex(pose, out, state, ring, segment + 1, light);
						}
					}
				});
			}
			poseStack.popPose();

			super.submit(state, poseStack, collector, camera);
		});
	}
}
