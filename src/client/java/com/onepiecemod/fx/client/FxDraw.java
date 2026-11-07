package com.onepiecemod.fx.client;

import org.joml.Vector3f;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;

import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.util.Mth;

/**
 * Small drawing tools for move effects: tubes, boxes, spheres and bands, built from flat four-cornered
 * pieces. All positions are measured from the effect entity, in blocks.
 */
public class FxDraw {
	/** Light level for things that glow: as bright as daylight, even in a cave at night. */
	public static final int GLOW = 0xF000F0;

	private final PoseStack.Pose pose;
	private final VertexConsumer out;
	private final int light;

	public FxDraw(PoseStack.Pose pose, VertexConsumer out, int light) {
		this.pose = pose;
		this.out = out;
		this.light = light;
	}

	/** A color with its see-through-ness replaced: alpha 0 is invisible, 1 is solid. */
	public static int alpha(int argb, float alpha) {
		int a = Mth.clamp((int) (alpha * 255), 0, 255);
		return (a << 24) | (argb & 0xFFFFFF);
	}

	/** Mixes two colors: t = 0 gives a, t = 1 gives b. */
	public static int mix(int a, int b, float t) {
		int ar = (a >> 16) & 0xFF, ag = (a >> 8) & 0xFF, ab = a & 0xFF;
		int br = (b >> 16) & 0xFF, bg = (b >> 8) & 0xFF, bb = b & 0xFF;
		return (a & 0xFF000000) | ((int) Mth.lerp(t, ar, br) << 16) | ((int) Mth.lerp(t, ag, bg) << 8) | (int) Mth.lerp(t, ab, bb);
	}

	/** A repeatable random number from 0 to 1 for a seed and an index. */
	public static float rnd(int seed, int index) {
		int h = seed * 0x9E3779B1 + index * 0x85EBCA6B;
		h ^= h >>> 15;
		h *= 0x2C1B3C6D;
		h ^= h >>> 12;
		h *= 0x297A2D39;
		h ^= h >>> 15;
		return (h & 0xFFFFFF) / (float) 0x1000000;
	}

	public void quad(Vector3f a, Vector3f b, Vector3f c, Vector3f d, int argb, Vector3f normal) {
		vertex(a, 0, 0, argb, normal);
		vertex(b, 0, 1, argb, normal);
		vertex(c, 1, 1, argb, normal);
		vertex(d, 1, 0, argb, normal);
	}

	private void vertex(Vector3f p, float u, float v, int argb, Vector3f n) {
		out.addVertex(pose, p.x, p.y, p.z)
				.setColor(argb)
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(light)
				.setNormal(pose, n.x, n.y, n.z);
	}

	/**
	 * A tube from a to b, ra thick at a and rb thick at b (radius, in blocks). A radius of 0 makes a point,
	 * so this also draws cones and spikes. sides = 4 gives a square tube, 8 or more looks round.
	 */
	public void tube(Vector3f a, Vector3f b, float ra, float rb, int sides, float twist, int argb, boolean caps) {
		Vector3f d = new Vector3f(b).sub(a);
		if (d.lengthSquared() < 1.0e-6f) {
			return;
		}
		d.normalize();
		Vector3f u = Math.abs(d.y) < 0.99f ? new Vector3f(d).cross(0, 1, 0) : new Vector3f(d).cross(1, 0, 0);
		u.normalize();
		Vector3f v = new Vector3f(d).cross(u).normalize();

		Vector3f[] ringA = new Vector3f[sides];
		Vector3f[] ringB = new Vector3f[sides];
		for (int i = 0; i < sides; i++) {
			float angle = twist + i * Mth.TWO_PI / sides;
			float cos = Mth.cos(angle), sin = Mth.sin(angle);
			ringA[i] = new Vector3f(a).add(u.x * cos * ra + v.x * sin * ra, u.y * cos * ra + v.y * sin * ra, u.z * cos * ra + v.z * sin * ra);
			ringB[i] = new Vector3f(b).add(u.x * cos * rb + v.x * sin * rb, u.y * cos * rb + v.y * sin * rb, u.z * cos * rb + v.z * sin * rb);
		}
		for (int i = 0; i < sides; i++) {
			int j = (i + 1) % sides;
			float mid = twist + (i + 0.5f) * Mth.TWO_PI / sides;
			Vector3f n = new Vector3f(u).mul(Mth.cos(mid)).add(new Vector3f(v).mul(Mth.sin(mid)));
			quad(ringA[i], ringB[i], ringB[j], ringA[j], argb, n);
		}
		if (caps) {
			Vector3f back = new Vector3f(d).negate();
			if (ra > 0) {
				for (int i = 0; i < sides; i++) {
					int j = (i + 1) % sides;
					quad(a, ringA[j], ringA[i], ringA[i], argb, back);
				}
			}
			if (rb > 0) {
				for (int i = 0; i < sides; i++) {
					int j = (i + 1) % sides;
					quad(b, ringB[i], ringB[j], ringB[j], argb, d);
				}
			}
		}
	}

	/** A ball, made of rings like a globe. squash below 1 flattens it. */
	public void sphere(Vector3f center, float radius, float squash, int argb) {
		int rings = 8, segments = 14;
		for (int r = 0; r < rings; r++) {
			float t0 = Mth.PI * r / rings - Mth.HALF_PI;
			float t1 = Mth.PI * (r + 1) / rings - Mth.HALF_PI;
			for (int s = 0; s < segments; s++) {
				float p0 = Mth.TWO_PI * s / segments;
				float p1 = Mth.TWO_PI * (s + 1) / segments;
				Vector3f a = globe(center, radius, squash, t0, p0);
				Vector3f b = globe(center, radius, squash, t1, p0);
				Vector3f c = globe(center, radius, squash, t1, p1);
				Vector3f d = globe(center, radius, squash, t0, p1);
				Vector3f n = globe(new Vector3f(), 1, 1, (t0 + t1) / 2, (p0 + p1) / 2);
				quad(a, b, c, d, argb, n);
			}
		}
	}

	private static Vector3f globe(Vector3f center, float radius, float squash, float lat, float lon) {
		float c = Mth.cos(lat);
		return new Vector3f(center.x + c * Mth.cos(lon) * radius, center.y + Mth.sin(lat) * radius * squash, center.z + c * Mth.sin(lon) * radius);
	}

	/** An upright band around a center, like the side of a can with no lid: from y0 to y1 at a radius. */
	public void band(Vector3f center, float radius, float y0, float y1, int segments, int argb) {
		for (int s = 0; s < segments; s++) {
			float p0 = Mth.TWO_PI * s / segments;
			float p1 = Mth.TWO_PI * (s + 1) / segments;
			Vector3f a = new Vector3f(center.x + Mth.cos(p0) * radius, center.y + y0, center.z + Mth.sin(p0) * radius);
			Vector3f b = new Vector3f(center.x + Mth.cos(p0) * radius, center.y + y1, center.z + Mth.sin(p0) * radius);
			Vector3f c = new Vector3f(center.x + Mth.cos(p1) * radius, center.y + y1, center.z + Mth.sin(p1) * radius);
			Vector3f d = new Vector3f(center.x + Mth.cos(p1) * radius, center.y + y0, center.z + Mth.sin(p1) * radius);
			quad(a, b, c, d, argb, new Vector3f(Mth.cos((p0 + p1) / 2), 0, Mth.sin((p0 + p1) / 2)));
		}
	}

	/** A flat ring lying on the ground, from an inner to an outer radius. */
	public void disc(Vector3f center, float inner, float outer, int segments, int argb) {
		Vector3f up = new Vector3f(0, 1, 0);
		for (int s = 0; s < segments; s++) {
			float p0 = Mth.TWO_PI * s / segments;
			float p1 = Mth.TWO_PI * (s + 1) / segments;
			Vector3f a = new Vector3f(center.x + Mth.cos(p0) * inner, center.y, center.z + Mth.sin(p0) * inner);
			Vector3f b = new Vector3f(center.x + Mth.cos(p0) * outer, center.y, center.z + Mth.sin(p0) * outer);
			Vector3f c = new Vector3f(center.x + Mth.cos(p1) * outer, center.y, center.z + Mth.sin(p1) * outer);
			Vector3f d = new Vector3f(center.x + Mth.cos(p1) * inner, center.y, center.z + Mth.sin(p1) * inner);
			quad(a, b, c, d, argb, up);
		}
	}

	/**
	 * A box in a turned frame: x goes along "right", y along "up" and z along "forward", measured from origin.
	 * Used for the fist shapes.
	 */
	public void box(Vector3f origin, Vector3f right, Vector3f up, Vector3f forward,
			float x0, float y0, float z0, float x1, float y1, float z1, int argb) {
		Vector3f[] c = new Vector3f[8];
		for (int i = 0; i < 8; i++) {
			float x = (i & 1) == 0 ? x0 : x1;
			float y = (i & 2) == 0 ? y0 : y1;
			float z = (i & 4) == 0 ? z0 : z1;
			c[i] = new Vector3f(origin).add(new Vector3f(right).mul(x)).add(new Vector3f(up).mul(y)).add(new Vector3f(forward).mul(z));
		}
		Vector3f nr = new Vector3f(right), nl = new Vector3f(right).negate();
		Vector3f nu = new Vector3f(up), nd = new Vector3f(up).negate();
		Vector3f nf = new Vector3f(forward), nb = new Vector3f(forward).negate();
		quad(c[0], c[2], c[6], c[4], argb, nl); // left (x0)
		quad(c[1], c[5], c[7], c[3], argb, nr); // right (x1)
		quad(c[0], c[4], c[5], c[1], argb, nd); // bottom (y0)
		quad(c[2], c[3], c[7], c[6], argb, nu); // top (y1)
		quad(c[0], c[1], c[3], c[2], argb, nb); // back (z0)
		quad(c[4], c[6], c[7], c[5], argb, nf); // front (z1)
	}

	/** Right, up and forward directions for something pointing along "forward", turned by roll radians. */
	public static Vector3f[] frame(Vector3f forward, float roll) {
		Vector3f f = new Vector3f(forward);
		if (f.lengthSquared() < 1.0e-6f) {
			f.set(0, 0, 1);
		}
		f.normalize();
		Vector3f right = Math.abs(f.y) < 0.99f ? new Vector3f(f).cross(0, 1, 0) : new Vector3f(f).cross(1, 0, 0);
		right.normalize();
		Vector3f up = new Vector3f(right).cross(f).normalize();
		if (roll != 0) {
			float c = Mth.cos(roll), s = Mth.sin(roll);
			Vector3f r2 = new Vector3f(right).mul(c).add(new Vector3f(up).mul(s));
			Vector3f u2 = new Vector3f(up).mul(c).sub(new Vector3f(right).mul(s));
			right = r2;
			up = u2;
		}
		return new Vector3f[]{right, up, f};
	}
}
