package com.onepiecemod.weather.client;

import org.joml.Vector3f;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.weather.SeaEvent;
import com.onepiecemod.weather.SeaEventSync;
import com.onepiecemod.weather.SeaEventType;

/**
 * Draws the Great Cyclone as a real shape, not just particles: a twisting, swaying tornado funnel from the sea up into
 * a huge dark cloud ceiling, with a skirt of spray at its foot. The funnel is three see-through layers (pale outside,
 * black core) that turn at different speeds, with spiral bands of light and dark running up them, so it looks like it's
 * spinning. WeatherVisuals adds the particles on top (spray, wreckage, rain bands).
 *
 * During the warning the funnel reaches down out of the clouds; it touches the sea when the storm starts, and pulls
 * back up into the clouds at the end.
 */
public class CycloneRenderer {
	private static final Identifier TEXTURE = OnePieceMod.id("textures/environment/cyclone_cloud.png");
	/** Daylight, no lamp light: the cyclone gets darker at night like everything else outdoors. */
	private static final int LIGHT = 0xF00000;
	private static final double MAX_DISTANCE = 420;

	static final double HEIGHT = 80;
	private static final int HEIGHT_STEPS = 30;
	private static final int SIDES = 32;
	private static final double CEILING_RADIUS = 170;

	/** The funnel's layers: how wide (times the funnel), color, how see-through and how fast it turns. */
	private static final double[] LAYER_WIDTH = {1.25, 0.95, 0.6};
	private static final int[] LAYER_COLOR = {0x7E858D, 0x464C54, 0x23272C};
	private static final float[] LAYER_ALPHA = {0.45f, 0.8f, 1.0f};
	private static final double[] LAYER_SPIN = {0.05, 0.08, 0.12};

	public static void initialize() {
		LevelRenderEvents.COLLECT_SUBMITS.register(CycloneRenderer::render);
	}

	/** The funnel's radius at a height (0 = the sea, 1 = the cloud ceiling): thin at the bottom, flaring at the top. */
	static double radius(double u) {
		return 4.5 + 26 * Math.pow(u, 2.0);
	}

	private static void render(LevelRenderContext context) {
		Minecraft minecraft = Minecraft.getInstance();
		if (minecraft.level == null || SeaEventSync.CLIENT_EVENTS.isEmpty()) {
			return;
		}
		Vec3 camera = context.levelState().cameraRenderState.pos;
		float time = context.levelState().gameTime + context.levelState().worldPartialTicks;
		double sea = minecraft.level.getSeaLevel();
		for (SeaEvent event : SeaEventSync.CLIENT_EVENTS) {
			if (event.type != SeaEventType.CYCLONE || time > event.endTime) {
				continue;
			}
			if (Math.sqrt(Mth.square(camera.x - event.x) + Mth.square(camera.z - event.z)) > MAX_DISTANCE + event.radius) {
				continue;
			}
			draw(context, event, camera, time, sea);
		}
	}

	private static void draw(LevelRenderContext context, SeaEvent event, Vec3 camera, float time, double sea) {
		// How far down the funnel reaches: half way during the warning, dropping to the sea over the last 10 seconds
		// before the storm starts, and rising back into the clouds over its last 8 seconds.
		double reach;
		if (time < event.startTime) {
			reach = 0.45 + 0.55 * (1 - Mth.clamp((event.startTime - time) / 200.0, 0, 1));
		} else {
			reach = Mth.clamp((event.endTime - time) / 160.0, 0, 1);
		}
		double bottomU = 1 - reach;
		// The ceiling gathers during the warning and fades at the very end.
		float ceilingAlpha = (float) Mth.clamp(time < event.startTime ? 0.55 + 0.45 * reach : Math.min(1, (event.endTime - time) / 100.0), 0, 1);
		Vec3 drift = event.direction();

		PoseStack poseStack = context.poseStack();
		SubmitNodeCollector collector = context.submitNodeCollector();
		RenderType type = RenderTypes.entityTranslucent(TEXTURE);
		poseStack.pushPose();
		// Fog hides anything past the render distance, but a cyclone should be seen coming from far off. So a far one
		// is drawn smaller and nearer, in line with where it really is: it looks the same size, just less fogged.
		double dx = event.x - camera.x;
		double dy = sea - camera.y;
		double dz = event.z - camera.z;
		double far = Math.sqrt(dx * dx + dz * dz);
		double clear = Minecraft.getInstance().options.getEffectiveRenderDistance() * 16 * 0.55;
		float scale = far > clear ? (float) (clear / far) : 1;
		poseStack.translate(dx * scale, dy * scale, dz * scale);
		poseStack.scale(scale, scale, scale);
		collector.submitCustomGeometry(poseStack, type, (pose, out) -> {
			Mesh mesh = new Mesh(pose, out);
			ceiling(mesh, event, time, ceilingAlpha);
			if (reach > 0.01) {
				for (int layer = 0; layer < LAYER_WIDTH.length; layer++) {
					funnel(mesh, event, time, drift, bottomU, layer);
				}
				if (bottomU < 0.02 && time >= event.startTime) {
					foot(mesh, event, time, drift);
				}
			}
		});
		poseStack.popPose();
	}

	/** One layer of the funnel: rings up the height, each centered where the funnel snakes to at that height. */
	private static void funnel(Mesh mesh, SeaEvent event, float time, Vec3 drift, double bottomU, int layer) {
		Vector3f[] below = null;
		float[] belowU = null;
		for (int k = 0; k <= HEIGHT_STEPS; k++) {
			double u = bottomU + (1 - bottomU) * k / HEIGHT_STEPS;
			Vec3 c = WeatherVisuals.funnelCenter(event, (long) time, u, drift).subtract(event.x, 0, event.z);
			double r = radius(u) * LAYER_WIDTH[layer];
			// Lower layers turn faster, like a real tornado.
			double turn = time * LAYER_SPIN[layer] * (1.6 - u);
			Vector3f[] ring = new Vector3f[SIDES + 1];
			float[] ringU = new float[SIDES + 1];
			for (int i = 0; i <= SIDES; i++) {
				double a = turn + i * Mth.TWO_PI / SIDES;
				// A slightly ragged edge, so it doesn't look like a perfect cone.
				double ragged = 1 + 0.08 * Math.sin(a * 5 + u * 17 + time * 0.05) + 0.05 * Math.sin(a * 11 - u * 23);
				ring[i] = new Vector3f((float) (c.x + Math.cos(a) * r * ragged), (float) (u * HEIGHT), (float) (c.z + Math.sin(a) * r * ragged));
				ringU[i] = i / (float) SIDES;
			}
			if (below != null) {
				double uPrev = bottomU + (1 - bottomU) * (k - 1) / HEIGHT_STEPS;
				for (int i = 0; i < SIDES; i++) {
					float v0 = (float) (k - 1) / HEIGHT_STEPS;
					float v1 = (float) k / HEIGHT_STEPS;
					mesh.quad(below[i], ring[i], ring[i + 1], below[i + 1], belowU[i], v0, ringU[i], v1, ringU[i + 1], v1, belowU[i + 1], v0,
							funnelColor(layer, i, uPrev, time), funnelColor(layer, i, u, time),
							funnelColor(layer, i + 1, u, time), funnelColor(layer, i + 1, uPrev, time));
				}
			}
			below = ring;
			belowU = ringU;
		}
	}

	/** A funnel corner's color: spiral bands of lighter and darker cloud climbing the funnel, blended smoothly. */
	private static int funnelColor(int layer, int side, double u, float time) {
		double a = side * Mth.TWO_PI / SIDES;
		double band = Math.sin(a * 3 + u * 11 - time * 0.15) * 0.6 + Math.sin(a * 7 - u * 29 + time * 0.23) * 0.4;
		float shade = (float) (0.78 + 0.22 * band);
		float alpha = LAYER_ALPHA[layer] * (float) (0.78 + 0.22 * Math.sin(a * 4 - u * 16 + time * 0.2 + layer));
		// Fade the very top into the ceiling, and the outer layer near the sea (it's spray there).
		alpha *= (float) (1 - smooth((u - 0.9) / 0.1));
		if (layer == 0) {
			alpha *= (float) Mth.clamp(u / 0.2, 0.2, 1);
		}
		return tint(LAYER_COLOR[layer], shade, alpha);
	}

	/** The cloud ceiling: a huge dark disc turning slowly, with spiral arms and a lower "wall cloud" around the funnel. */
	private static void ceiling(Mesh mesh, SeaEvent event, float time, float fade) {
		int rings = 22;
		int segments = 96;
		double turn = -time * 0.006;
		for (int ringIndex = 0; ringIndex < rings; ringIndex++) {
			double r0 = CEILING_RADIUS * Math.pow(ringIndex / (double) rings, 1.3);
			double r1 = CEILING_RADIUS * Math.pow((ringIndex + 1) / (double) rings, 1.3);
			for (int s = 0; s < segments; s++) {
				double a0 = turn + s * Mth.TWO_PI / segments;
				double a1 = turn + (s + 1) * Mth.TWO_PI / segments;
				Vector3f p00 = ceilingPoint(r0, a0, time);
				Vector3f p10 = ceilingPoint(r1, a0, time);
				Vector3f p11 = ceilingPoint(r1, a1, time);
				Vector3f p01 = ceilingPoint(r0, a1, time);
				float u0 = s / (float) segments;
				float u1 = (s + 1) / (float) segments;
				float v0 = ringIndex / (float) rings;
				float v1 = (ringIndex + 1) / (float) rings;
				mesh.quad(p00, p10, p11, p01, u0, v0, u0, v1, u1, v1, u1, v0,
						ceilingColor(r0, a0 - turn, time, fade), ceilingColor(r1, a0 - turn, time, fade),
						ceilingColor(r1, a1 - turn, time, fade), ceilingColor(r0, a1 - turn, time, fade));
			}
		}
	}

	/** A ceiling corner's color: dark, with spiral arms, and a ragged soft edge instead of a neat circle. */
	private static int ceilingColor(double r, double a, float time, float fade) {
		double arms = Math.sin(a * 2 - r * 0.06 + time * 0.01);
		float shade = (float) (0.8 + 0.2 * arms + 0.08 * Math.sin(a * 9 + r * 0.2));
		double edge = CEILING_RADIUS * (0.3 + 0.06 * Math.sin(a * 3 + time * 0.004) + 0.03 * Math.sin(a * 5 - r * 0.02) + 0.03 * arms);
		float alpha = (float) (0.95 * (1 - smooth((r - edge) / (CEILING_RADIUS - edge)))) * fade;
		return tint(0x30353C, shade, alpha);
	}

	private static Vector3f ceilingPoint(double r, double a, float time) {
		// Lowest in the middle (the wall cloud the funnel hangs from), rising toward the edges, with lumps.
		double y = HEIGHT + 3 - 15 * Math.exp(-Mth.square(r / 50)) + r * 0.03 + 0.6 * Math.sin(a * 3 + r * 0.05 + time * 0.01);
		return new Vector3f((float) (Math.cos(a) * r), (float) y, (float) (Math.sin(a) * r));
	}

	/** A pale skirt of spray where the funnel churns up the sea. */
	private static void foot(Mesh mesh, SeaEvent event, float time, Vec3 drift) {
		Vec3 c = WeatherVisuals.funnelCenter(event, (long) time, 0, drift).subtract(event.x, 0, event.z);
		int steps = 4;
		double turn = time * 0.2;
		Vector3f[] below = null;
		for (int k = 0; k <= steps; k++) {
			double h = k * 3.0;
			double r = 7 + k * 3.2;
			Vector3f[] ring = new Vector3f[SIDES + 1];
			for (int i = 0; i <= SIDES; i++) {
				double a = turn + i * Mth.TWO_PI / SIDES;
				ring[i] = new Vector3f((float) (c.x + Math.cos(a) * r), (float) h, (float) (c.z + Math.sin(a) * r));
			}
			if (below != null) {
				for (int i = 0; i < SIDES; i++) {
					double a = (i + 0.5) * Mth.TWO_PI / SIDES;
					float lower = (float) (0.5 * (1 - (k - 1) / (double) steps) * (0.6 + 0.4 * Math.sin(a * 5 + time * 0.3)));
					float upper = (float) (0.5 * (1 - k / (double) steps) * (0.6 + 0.4 * Math.sin(a * 5 + time * 0.3)));
					int bottom = tint(0xC9D3DB, 1, lower);
					int top = tint(0xC9D3DB, 1, upper);
					mesh.quad(below[i], ring[i], ring[i + 1], below[i + 1], i / (float) SIDES, 0.8f, i / (float) SIDES, 1,
							(i + 1) / (float) SIDES, 1, (i + 1) / (float) SIDES, 0.8f, bottom, top, top, bottom);
				}
			}
			below = ring;
		}
	}

	private static double smooth(double t) {
		t = Mth.clamp(t, 0, 1);
		return t * t * (3 - 2 * t);
	}

	private static int tint(int rgb, float shade, float alpha) {
		int r = Mth.clamp((int) (((rgb >> 16) & 0xFF) * shade), 0, 255);
		int g = Mth.clamp((int) (((rgb >> 8) & 0xFF) * shade), 0, 255);
		int b = Mth.clamp((int) ((rgb & 0xFF) * shade), 0, 255);
		int a = Mth.clamp((int) (alpha * 255), 0, 255);
		return a << 24 | r << 16 | g << 8 | b;
	}

	/** Writes quads with their own texture coordinates (this render type shows both sides, so once is enough). */
	private static final Vector3f SIDE_NORMAL = new Vector3f(0.6f, 0.2f, 0.77f).normalize();

	private record Mesh(PoseStack.Pose pose, VertexConsumer out) {
		void quad(Vector3f a, Vector3f b, Vector3f c, Vector3f d,
				float ua, float va, float ub, float vb, float uc, float vc, float ud, float vd, int ca, int cb, int cc, int cd) {
			if (Math.max(Math.max(ca >>> 24, cb >>> 24), Math.max(cc >>> 24, cd >>> 24)) < 3) {
				return;
			}
			// The same sideways normal everywhere: the shading comes from the colors, so the game's sunlight doesn't
			// paint flat parts (the funnel's flared top) bright white.
			Vector3f n = new Vector3f(SIDE_NORMAL);
			vertex(a, ua, va, ca, n);
			vertex(b, ub, vb, cb, n);
			vertex(c, uc, vc, cc, n);
			vertex(d, ud, vd, cd, n);
		}

		private void vertex(Vector3f p, float u, float v, int color, Vector3f n) {
			out.addVertex(pose, p.x, p.y, p.z)
					.setColor(color)
					.setUv(u, v)
					.setOverlay(OverlayTexture.NO_OVERLAY)
					.setLight(LIGHT)
					.setNormal(pose, n.x, n.y, n.z);
		}
	}
}
