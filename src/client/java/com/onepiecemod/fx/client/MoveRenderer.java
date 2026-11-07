package com.onepiecemod.fx.client;

import com.onepiecemod.client.RenderGuard;

import org.joml.Vector3f;
import org.joml.Vector3fc;

import com.mojang.blaze3d.vertex.PoseStack;

import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.fx.MoveEffectEntity;
import com.onepiecemod.fx.MoveFx;
import com.onepiecemod.fx.MoveStyle;

/**
 * Draws the shapes of Devil Fruit moves (see MoveStyle). Everything is built from simple tubes, boxes and
 * balls, tinted with the move's colors, so no special textures are needed.
 *
 * Glowing shapes (fire, light, ice...) ignore darkness. The rubber arm is solid and lit like the player.
 */
public class MoveRenderer extends EntityRenderer<MoveEffectEntity, MoveRenderer.State> {
	private static final Identifier WHITE = OnePieceMod.id("textures/entity/fx/white.png");
	private static final Vector3f UP = new Vector3f(0, 1, 0);

	public static class State extends EntityRenderState {
		public MoveStyle style = MoveStyle.ORB;
		public int color, color2;
		public final Vector3f reach = new Vector3f();
		public float size;
		public int life;
		public float age;
		public int seed;
		/** Where the shape starts, measured from the entity: moves with the owner for arms and auras. */
		public final Vector3f anchor = new Vector3f();

		/** A copy to draw from later in the frame, so reusing this state can't change the picture. */
		State copy() {
			State c = new State();
			c.style = style;
			c.color = color;
			c.color2 = color2;
			c.reach.set(reach);
			c.size = size;
			c.life = life;
			c.age = age;
			c.seed = seed;
			c.anchor.set(anchor);
			c.lightCoords = lightCoords;
			return c;
		}
	}

	public MoveRenderer(EntityRendererProvider.Context context) {
		super(context);
		this.shadowRadius = 0;
	}

	@Override
	protected boolean affectedByCulling(MoveEffectEntity entity) {
		return false; // A long beam can be on screen while this tiny entity isn't.
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(MoveEffectEntity entity, State state, float partialTick) {
		super.extractRenderState(entity, state, partialTick);
		RenderGuard.run("move effect state", () -> {
			state.style = entity.style();
			state.color = entity.color();
			state.color2 = entity.color2();
			Vector3fc reach = entity.reach();
			state.reach.set(reach);
			state.size = entity.size();
			state.life = entity.life();
			state.age = entity.tickCount + partialTick - entity.delayTicks();
			state.seed = entity.getId() * 31 + 7;
			state.anchor.set(0, 0, 0);

			Entity owner = entity.owner();
			if (owner == null) {
				return;
			}
			Vec3 here = entity.getPosition(partialTick);
			Vec3 at = owner.getPosition(partialTick);
			switch (state.style) {
				case ARM -> {
					// Start at the owner's shoulder, even while they move. The fist stays where it was aimed.
					float yaw = owner.getViewYRot(partialTick) * Mth.DEG_TO_RAD;
					float side = state.size < 0 ? -1 : 1;
					Vec3 right = new Vec3(-Mth.cos(yaw), 0, -Mth.sin(yaw)).scale(0.37 * side);
					Vec3 shoulder = at.add(0, owner.getBbHeight() * 0.78, 0).add(right);
					Vec3 anchor = shoulder.subtract(here);
					state.anchor.set((float) anchor.x, (float) anchor.y, (float) anchor.z);
					state.reach.sub(state.anchor); // From the shoulder to the aimed point.
				}
				case SPHERE, TORNADO, HELIX -> {
					Vec3 offset = at.subtract(here);
					float lift = state.style == MoveStyle.SPHERE ? owner.getBbHeight() / 2 : 0;
					state.anchor.set((float) offset.x, (float) offset.y + lift, (float) offset.z);
				}
				default -> {
				}
			}
		});
	}

	@Override
	public void submit(State state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
		RenderGuard.run("move effect", poseStack, () -> {
			if (state.age > state.life + 1 || state.age < 0) {
				return;
			}
			State s = state.copy();
			float p = Mth.clamp(s.age / s.life, 0, 1);
			if (s.style == MoveStyle.ARM) {
				// Solid and lit by the world, like the rest of the player.
				int light = s.lightCoords;
				collector.submitCustomGeometry(poseStack, RenderTypes.entityCutout(WHITE), (pose, out) -> arm(new FxDraw(pose, out, light), s, p));
				if (s.color == MoveFx.HAKI) {
					// Armament Haki: a dark shine around the black arm.
					collector.submitCustomGeometry(poseStack, glow(), (pose, out) -> armSheen(new FxDraw(pose, out, FxDraw.GLOW), s, p));
				}
				return;
			}
			collector.submitCustomGeometry(poseStack, glow(), (pose, out) -> {
				FxDraw d = new FxDraw(pose, out, FxDraw.GLOW);
				switch (s.style) {
					case FIST -> fist(d, s, p);
					case BEAM -> beam(d, s, p);
					case SPEAR -> spear(d, s, p);
					case ORB -> orb(d, s, p);
					case BOLT -> bolt(d, s, p);
					case SPHERE -> sphere(d, s, p);
					case RING -> ring(d, s, p);
					case SLASH -> slash(d, s, p, 0, 1.0f);
					case CLAW -> claw(d, s, p);
					case PILLAR -> pillar(d, s, p);
					case SPIKES -> spikes(d, s, p);
					case TORNADO -> tornado(d, s, p);
					case CRACK -> crack(d, s, p);
					case BURST -> burst(d, s, p);
					case GATE -> gate(d, s, p);
					case WAVES -> waves(d, s, p);
					case SHIELD -> shield(d, s, p);
					case HELIX -> helix(d, s, p);
					case WEB -> web(d, s, p);
					default -> {
					}
				}
			});
		});
	}

	private static RenderType glow() {
		return RenderTypes.entityTranslucentEmissive(WHITE);
	}

	/** Fades out over the last part of the effect's life: 1 until "from", then down to 0. */
	private static float fadeAfter(float p, float from) {
		return p < from ? 1 : 1 - (p - from) / (1 - from);
	}

	private static Vector3f along(Vector3f dir, float distance) {
		return new Vector3f(dir).mul(distance);
	}

	// ---- The shapes ----

	/** A rubber arm: shoots out, holds for a moment, then snaps back. */
	private static void arm(FxDraw d, State s, float p) {
		float out = p < 0.3f ? p / 0.3f : p < 0.55f ? 1 : 1 - (p - 0.55f) / 0.45f;
		out = Mth.clamp(out, 0, 1);
		float length = s.reach.length() * out;
		if (length < 0.05f) {
			return;
		}
		Vector3f dir = new Vector3f(s.reach).normalize();
		Vector3f start = new Vector3f(s.anchor);
		Vector3f fistBack = new Vector3f(start).add(along(dir, Math.max(0, length - 0.3f)));
		Vector3f fistFront = new Vector3f(start).add(along(dir, length + 0.1f));

		// The arm gets a little thinner in the middle as it stretches.
		float thin = 0.13f - 0.04f * Math.min(1, length / 12);
		Vector3f middle = new Vector3f(start).lerp(fistBack, 0.5f);
		d.tube(start, middle, 0.14f, thin, 6, 0, s.color, true);
		d.tube(middle, fistBack, thin, 0.15f, 6, 0, s.color, true);
		// A wrist band, then the fist with its knuckles.
		Vector3f wrist = new Vector3f(start).add(along(dir, Math.max(0, length - 0.42f)));
		d.tube(wrist, fistBack, 0.17f, 0.17f, 6, 0, s.color2, true);
		Vector3f[] f = FxDraw.frame(dir, 0);
		d.box(fistBack, f[0], f[1], f[2], -0.22f, -0.2f, 0, 0.22f, 0.2f, 0.36f, s.color);
		d.box(fistBack, f[0], f[1], f[2], -0.2f, 0.02f, 0.3f, 0.2f, 0.18f, 0.42f, s.color2);
		d.box(fistBack, f[0], f[1], f[2], 0.18f, -0.14f, 0.04f, 0.3f, 0.06f, 0.28f, s.color); // thumb
		// Speed lines along the arm while it shoots out.
		if (p < 0.3f) {
			Vector3f[] g = FxDraw.frame(dir, 0);
			for (int i = 0; i < 3; i++) {
				float angle = i * Mth.TWO_PI / 3 + FxDraw.rnd(s.seed, i);
				Vector3f off = new Vector3f(g[0]).mul(Mth.cos(angle) * 0.32f).add(new Vector3f(g[1]).mul(Mth.sin(angle) * 0.32f));
				Vector3f a = new Vector3f(start).add(along(dir, length * 0.35f)).add(off);
				d.tube(a, new Vector3f(fistFront).add(off).sub(along(dir, 0.4f)), 0.01f, 0.02f, 3, 0, 0xFFFFFFFF, false);
			}
		}
	}

	/** The purple-black shine of Armament Haki around a stretched arm. */
	private static void armSheen(FxDraw d, State s, float p) {
		float out = p < 0.3f ? p / 0.3f : p < 0.55f ? 1 : 1 - (p - 0.55f) / 0.45f;
		float length = s.reach.length() * Mth.clamp(out, 0, 1);
		if (length < 0.05f) {
			return;
		}
		Vector3f dir = new Vector3f(s.reach).normalize();
		Vector3f start = new Vector3f(s.anchor);
		Vector3f end = new Vector3f(start).add(along(dir, length + 0.15f));
		Vector3f mid = new Vector3f(start).add(along(dir, length * 0.4f));
		d.tube(mid, end, 0.05f, 0.34f, 8, s.age * 0.3f, FxDraw.alpha(0xFF8A50FF, 0.22f), true);
	}

	/** A giant fist of fire (or magma, or smoke) that flies forward with a trail, then bursts. */
	private static void fist(FxDraw d, State s, float p) {
		float t = MoveEffectEntity.travel(MoveStyle.FIST, s.age, s.life);
		float length = s.reach.length();
		Vector3f dir = new Vector3f(s.reach).normalize();
		float fade = fadeAfter(p, 0.55f);
		float flicker = 1 + 0.07f * Mth.sin(s.age * 2.3f + s.seed);
		float size = s.size * (0.55f + 0.45f * Math.min(1, p * 3)) * flicker * (1 + Math.max(0, p - 0.5f) * 1.2f);
		Vector3f head = along(dir, length * t);

		// The trail: a cone from behind the fist back toward your hand, twisting like flames.
		float tail = Math.min(length * t, 3.5f + size * 2);
		Vector3f tailStart = new Vector3f(head).sub(along(dir, tail));
		d.tube(tailStart, head, 0.05f, 0.32f * size, 8, s.age * 0.25f, FxDraw.alpha(s.color, 0.7f * fade), false);
		d.tube(tailStart, head, 0.12f, 0.55f * size, 8, -s.age * 0.2f, FxDraw.alpha(s.color2, 0.42f * fade), false);

		// The fist: a big block for the hand, four knuckles in front and a thumb on the side.
		Vector3f[] f = FxDraw.frame(dir, FxDraw.rnd(s.seed, 1) * 0.6f - 0.3f);
		fistShape(d, head, f, size * 0.62f, FxDraw.alpha(s.color, 0.97f * fade));
		fistShape(d, head, f, size * 0.8f, FxDraw.alpha(s.color2, 0.62f * fade));
	}

	private static void fistShape(FxDraw d, Vector3f at, Vector3f[] f, float k, int color) {
		d.box(at, f[0], f[1], f[2], -0.5f * k, -0.45f * k, -0.55f * k, 0.5f * k, 0.45f * k, 0.3f * k, color);
		for (int i = 0; i < 4; i++) {
			float y = (-0.44f + i * 0.23f) * k;
			d.box(at, f[0], f[1], f[2], -0.46f * k, y, 0.28f * k, 0.38f * k, y + 0.2f * k, 0.56f * k, color);
		}
		d.box(at, f[0], f[1], f[2], 0.48f * k, -0.22f * k, -0.25f * k, 0.7f * k, 0.18f * k, 0.25f * k, color);
	}

	/** A straight beam that grows quickly to full width, then thins out. */
	private static void beam(FxDraw d, State s, float p) {
		float width = s.size * (p < 0.1f ? p / 0.1f : (float) Math.pow(1 - (p - 0.1f) / 0.9f, 0.4));
		if (width <= 0.001f) {
			return;
		}
		Vector3f end = new Vector3f(s.reach);
		Vector3f start = new Vector3f();
		d.tube(start, end, width * 0.25f, width * 0.2f, 8, s.age * 0.5f, FxDraw.alpha(s.color, 1.0f), true);
		d.tube(start, end, width * 0.5f, width * 0.42f, 8, -s.age * 0.3f, FxDraw.alpha(s.color2, 0.75f), true);
		// A flash at the hand and a splash where it lands.
		d.sphere(start, width * 0.4f, 1, FxDraw.alpha(s.color2, 0.4f));
		d.sphere(end, width * 0.9f, 1, FxDraw.alpha(s.color, 0.5f));
	}

	/** A crystal spear that flies, sticks where it lands, then shatters into shards. */
	private static void spear(FxDraw d, State s, float p) {
		float t = MoveEffectEntity.travel(MoveStyle.SPEAR, s.age, s.life);
		Vector3f dir = new Vector3f(s.reach).normalize();
		Vector3f tip = along(dir, s.reach.length() * t);
		float k = s.size;
		float fade = fadeAfter(p, 0.5f);
		float twist = FxDraw.rnd(s.seed, 2) * Mth.PI;
		Vector3f mid = new Vector3f(tip).sub(along(dir, 0.45f * k));
		Vector3f back = new Vector3f(tip).sub(along(dir, 1.9f * k));
		d.tube(back, mid, 0.05f * k, 0.13f * k, 4, twist, FxDraw.alpha(s.color, 0.95f * fade), true);
		d.tube(mid, tip, 0.13f * k, 0, 4, twist, FxDraw.alpha(s.color, 0.95f * fade), false);
		d.tube(back, mid, 0.09f * k, 0.24f * k, 4, twist, FxDraw.alpha(s.color2, 0.6f * fade), true);
		d.tube(mid, tip, 0.24f * k, 0, 4, twist, FxDraw.alpha(s.color2, 0.6f * fade), false);
		// Frost trail.
		if (t < 1) {
			d.tube(new Vector3f(back).sub(along(dir, 2.5f)), back, 0, 0.12f * k, 4, twist, FxDraw.alpha(s.color, 0.3f), false);
		}
		// Shards burst out once it lands.
		if (t >= 1 && p > 0.32f) {
			float burst = (p - 0.32f) * 4;
			for (int i = 0; i < 7; i++) {
				Vector3f out = new Vector3f(FxDraw.rnd(s.seed, 10 + i) - 0.5f, FxDraw.rnd(s.seed, 20 + i) * 0.8f, FxDraw.rnd(s.seed, 30 + i) - 0.5f).normalize();
				Vector3f a = new Vector3f(tip).add(new Vector3f(out).mul(burst));
				Vector3f b = new Vector3f(a).add(new Vector3f(out).mul(0.35f * k));
				d.tube(a, b, 0.08f * k, 0, 4, i, FxDraw.alpha(s.color2, 0.8f * fade), true);
			}
		}
	}

	/** A glowing ball that flies, then pops. */
	private static void orb(FxDraw d, State s, float p) {
		float t = MoveEffectEntity.travel(MoveStyle.ORB, s.age, s.life);
		Vector3f dir = new Vector3f(s.reach).normalize();
		Vector3f head = along(dir, s.reach.length() * t);
		float fade = t < 1 ? 1 : fadeAfter(p, 0.45f);
		float r = 0.45f * s.size * (1 + 0.08f * Mth.sin(s.age * 1.7f)) * (t < 1 ? 1 : 1 + (p - 0.45f) * 1.5f);
		d.sphere(head, r * 0.55f, 1, FxDraw.alpha(s.color, 0.95f * fade));
		d.sphere(head, r, 1, FxDraw.alpha(s.color2, 0.5f * fade));
		if (t < 1) {
			float tail = Math.min(s.reach.length() * t, 3f);
			d.tube(new Vector3f(head).sub(along(dir, tail)), head, 0, r * 0.75f, 8, s.age * 0.3f, FxDraw.alpha(s.color2, 0.3f), false);
		}
	}

	/** A jagged lightning bolt that flickers and changes shape every couple of ticks. */
	private static void bolt(FxDraw d, State s, float p) {
		if (((int) s.age) % 4 == 3 && p > 0.2f) {
			return; // A flicker: lightning blinks.
		}
		int shape = s.seed + (int) (s.age / 2) * 101;
		float length = s.reach.length();
		int pieces = Math.max(5, (int) (length / 1.4f));
		Vector3f dir = new Vector3f(s.reach).normalize();
		Vector3f[] f = FxDraw.frame(dir, 0);
		float jag = 0.45f * Math.max(0.6f, s.size) * Math.min(1, length / 6);
		float fade = fadeAfter(p, 0.4f);

		Vector3f last = new Vector3f();
		for (int i = 1; i <= pieces; i++) {
			float along = length * i / pieces;
			Vector3f next = along(dir, along);
			if (i < pieces) {
				next.add(new Vector3f(f[0]).mul((FxDraw.rnd(shape, i) - 0.5f) * 2 * jag)).add(new Vector3f(f[1]).mul((FxDraw.rnd(shape, i + 50) - 0.5f) * 2 * jag));
			}
			zap(d, last, next, s, fade);
			// Now and then a small branch splits off.
			if (i < pieces - 1 && FxDraw.rnd(shape, i + 100) < 0.3f) {
				Vector3f b = new Vector3f(next).add(new Vector3f(f[0]).mul((FxDraw.rnd(shape, i + 150) - 0.5f) * 3 * jag))
						.add(new Vector3f(f[1]).mul((FxDraw.rnd(shape, i + 200) - 0.5f) * 3 * jag)).add(along(dir, length / pieces * 0.8f));
				zap(d, next, b, s, fade * 0.7f);
			}
			last = next;
		}
	}

	private static void zap(FxDraw d, Vector3f a, Vector3f b, State s, float fade) {
		float k = Math.max(0.5f, s.size);
		d.tube(a, b, 0.05f * k, 0.05f * k, 4, 0, FxDraw.alpha(s.color, fade), true);
		d.tube(a, b, 0.16f * k, 0.16f * k, 4, 0.8f, FxDraw.alpha(s.color2, 0.4f * fade), true);
	}

	/** A bubble that grows and fades, or with a negative size, a dark sphere that sucks inward. */
	private static void sphere(FxDraw d, State s, float p) {
		Vector3f c = new Vector3f(s.anchor);
		if (s.size >= 0) {
			float r = s.size * (0.3f + 0.7f * (1 - (1 - p) * (1 - p) * (1 - p)));
			float a = 0.55f * (1 - p);
			d.sphere(c, r * 0.8f, 1, FxDraw.alpha(s.color, a * 0.6f));
			d.sphere(c, r, 1, FxDraw.alpha(s.color2, a));
		} else {
			float r = -s.size * (float) Math.pow(1 - p, 0.7) + 0.25f;
			float a = 0.7f * Math.min(1, p * 5) * fadeAfter(p, 0.85f);
			d.sphere(c, r, 1, FxDraw.alpha(s.color2, a));
			d.sphere(c, r * 0.6f, 1, FxDraw.alpha(s.color, a));
			// A flat swirl around it, like water going down a drain.
			d.disc(new Vector3f(c).add(0, -0.2f, 0), r * 1.1f, r * 1.9f, 24, FxDraw.alpha(s.color, 0.35f * a));
		}
	}

	/** A shockwave ring that rushes outward along the ground. */
	private static void ring(FxDraw d, State s, float p) {
		float max = s.reach.length();
		float r = max * (1 - (1 - p) * (1 - p));
		float a = 1 - p;
		float height = (0.8f * s.size) * (1 - p) + 0.15f;
		Vector3f c = new Vector3f();
		d.band(c, r * 0.94f, 0, height * 0.6f, 40, FxDraw.alpha(s.color, 0.6f * a));
		d.band(c, r, 0, height, 40, FxDraw.alpha(s.color2, 0.85f * a));
		d.disc(new Vector3f(0, 0.04f, 0), r * 0.75f, r, 40, FxDraw.alpha(s.color2, 0.3f * a));
	}

	/**
	 * A crescent cut that sweeps across in front of you. offset shifts it sideways (for claws),
	 * scale makes it smaller.
	 */
	private static void slash(FxDraw d, State s, float p, float offset, float scale) {
		float radius = s.reach.length() * scale;
		boolean claw = s.style == MoveStyle.CLAW;
		float roll = claw ? 1.25f + FxDraw.rnd(s.seed, 3) * 0.3f : (FxDraw.rnd(s.seed, 3) - 0.5f) * 1.2f;
		Vector3f[] f = FxDraw.frame(s.reach, roll);
		Vector3f center = new Vector3f(f[0]).mul(offset);
		float spread = claw ? 0.9f : 1.3f; // How far around it cuts, in radians to each side.
		float sweep = Math.min(1, p / 0.35f);
		float from = -spread, to = -spread + 2 * spread * sweep;
		float fade = fadeAfter(p, 0.35f);
		int steps = 18;
		float thick = 0.32f * Math.max(0.5f, s.size) * scale;
		for (int i = 0; i < steps; i++) {
			float a0 = Mth.lerp(i / (float) steps, from, to);
			float a1 = Mth.lerp((i + 1) / (float) steps, from, to);
			// Thick in the middle, thin at both tips.
			float w0 = thick * Mth.sin((a0 + spread) / (2 * spread) * Mth.PI);
			float w1 = thick * Mth.sin((a1 + spread) / (2 * spread) * Mth.PI);
			Vector3f o0 = arc(center, f, a0, radius), o1 = arc(center, f, a1, radius);
			Vector3f m0 = arc(center, f, a0, radius - w0 * 0.4f), m1 = arc(center, f, a1, radius - w1 * 0.4f);
			Vector3f i0 = arc(center, f, a0, radius - w0), i1 = arc(center, f, a1, radius - w1);
			// Lit as if facing up, so the blade looks equally bright from both sides.
			d.quad(m0, o0, o1, m1, FxDraw.alpha(s.color, 0.95f * fade), UP);
			d.quad(i0, m0, m1, i1, FxDraw.alpha(s.color2, 0.55f * fade), UP);
		}
	}

	private static Vector3f arc(Vector3f center, Vector3f[] f, float angle, float radius) {
		return new Vector3f(center).add(new Vector3f(f[2]).mul(Mth.cos(angle) * radius)).add(new Vector3f(f[0]).mul(Mth.sin(angle) * radius));
	}

	/** Three claw marks side by side. */
	private static void claw(FxDraw d, State s, float p) {
		for (int i = -1; i <= 1; i++) {
			slash(d, s, Math.min(1, p * (1.1f + i * 0.1f)), i * 0.35f, 0.75f);
		}
	}

	/** A column that bursts up from the ground, wobbles, then fades. */
	private static void pillar(FxDraw d, State s, float p) {
		float height = s.reach.length() * Math.min(1, p / 0.25f);
		float fade = fadeAfter(p, 0.65f);
		float r = 0.6f * s.size * (1 + 0.12f * Mth.sin(s.age * 1.5f + s.seed));
		Vector3f base = new Vector3f(0, -0.2f, 0);
		Vector3f top = new Vector3f(0, height, 0);
		d.tube(base, top, r * 0.5f, r * 0.25f, 8, s.age * 0.3f, FxDraw.alpha(s.color, 0.85f * fade), true);
		d.tube(base, top, r, r * 0.55f, 8, -s.age * 0.2f, FxDraw.alpha(s.color2, 0.5f * fade), true);
		d.disc(new Vector3f(0, 0.05f, 0), 0, r * 1.6f, 16, FxDraw.alpha(s.color2, 0.4f * fade));
	}

	/** Crystals (or roots, or arms) bursting out of the ground in a circle, then sinking back. */
	private static void spikes(FxDraw d, State s, float p) {
		float radius = s.reach.length();
		float rise = p < 0.12f ? p / 0.12f : p > 0.8f ? 1 - (p - 0.8f) / 0.2f : 1;
		int count = Mth.clamp((int) (radius * 3), 8, 30);
		for (int i = 0; i < count; i++) {
			float angle = i * Mth.TWO_PI / count + FxDraw.rnd(s.seed, i) * 0.3f;
			float dist = radius * (0.35f + 0.65f * FxDraw.rnd(s.seed, i + 40));
			float height = (0.8f + 1.8f * FxDraw.rnd(s.seed, i + 80)) * s.size * rise;
			float tilt = 0.25f + 0.25f * FxDraw.rnd(s.seed, i + 120);
			Vector3f base = new Vector3f(Mth.cos(angle) * dist, -0.3f, Mth.sin(angle) * dist);
			Vector3f tip = new Vector3f(base).add(Mth.cos(angle) * height * tilt, height, Mth.sin(angle) * height * tilt);
			float r = 0.28f * s.size;
			float twist = FxDraw.rnd(s.seed, i + 160) * Mth.PI;
			d.tube(base, tip, r * 0.55f, 0, 4, twist, FxDraw.alpha(s.color, 0.9f), true);
			d.tube(base, tip, r, 0, 4, twist, FxDraw.alpha(s.color2, 0.75f), true);
		}
	}

	/** A spinning funnel: stacked rings that get wider toward the top. */
	private static void tornado(FxDraw d, State s, float p) {
		float height = s.reach.length();
		float grow = Math.min(1, p / 0.2f);
		float fade = fadeAfter(p, 0.7f);
		int rings = 10;
		for (int i = 0; i < rings; i++) {
			float h = height * i / rings * grow;
			float r = Mth.lerp(i / (float) (rings - 1), 0.35f, Math.max(0.6f, s.size));
			float spin = s.age * 0.45f + i * 0.7f;
			Vector3f c = new Vector3f(s.anchor).add(Mth.cos(spin) * 0.15f * i / rings * s.size, h, Mth.sin(spin) * 0.15f * i / rings * s.size);
			d.band(c, r, 0, height / rings * 0.7f, 16, FxDraw.alpha(i % 2 == 0 ? s.color : s.color2, 0.62f * fade));
		}
	}

	/** Cracks spreading through the air from one point, like a shattered window. */
	private static void crack(FxDraw d, State s, float p) {
		float length = s.reach.length();
		Vector3f[] f = FxDraw.frame(s.reach, 0);
		float grow = Math.min(1, p / 0.15f);
		float fade = fadeAfter(p, 0.5f);
		int rays = 9;
		for (int r = 0; r < rays; r++) {
			float angle = r * Mth.TWO_PI / rays + FxDraw.rnd(s.seed, r) * 0.5f;
			float rayLength = length * (0.6f + 0.4f * FxDraw.rnd(s.seed, r + 20)) * grow;
			Vector3f last = new Vector3f();
			int pieces = 5;
			for (int i = 1; i <= pieces; i++) {
				float bend = angle + (FxDraw.rnd(s.seed, r * 10 + i + 40) - 0.5f) * 0.6f;
				float dist = rayLength * i / pieces;
				Vector3f next = new Vector3f(f[0]).mul(Mth.cos(bend) * dist).add(new Vector3f(f[1]).mul(Mth.sin(bend) * dist));
				float w = 0.06f * s.size * (1 - i / (float) (pieces + 1));
				d.tube(last, next, w, w * 0.8f, 4, 0, FxDraw.alpha(s.color, fade), true);
				d.tube(last, next, w * 2.5f, w * 2f, 4, 0.8f, FxDraw.alpha(s.color2, 0.35f * fade), true);
				last = next;
			}
		}
	}

	// ---- Shapes added in the polish pass ----

	/** An explosion: a white-hot core that swells and fades, rays shooting out, and a smoke ring on the ground. */
	private static void burst(FxDraw d, State s, float p) {
		float radius = Math.max(0.8f, s.reach.length());
		float grow = 1 - (1 - Math.min(1, p / 0.35f)) * (1 - Math.min(1, p / 0.35f));
		float fade = fadeAfter(p, 0.3f);
		Vector3f c = new Vector3f();
		// The flash: brightest at the start.
		d.sphere(c, radius * (0.25f + 0.35f * grow), 1, FxDraw.alpha(0xFFFFFFFF, 0.9f * fadeAfter(p, 0.12f)));
		d.sphere(c, radius * (0.3f + 0.35f * grow), 1, FxDraw.alpha(s.color, 0.6f * fade));
		d.sphere(c, radius * (0.4f + 0.45f * grow), 1, FxDraw.alpha(s.color2, 0.25f * fade));
		// Rays of fire and debris.
		int rays = 12;
		for (int i = 0; i < rays; i++) {
			Vector3f dir = new Vector3f(FxDraw.rnd(s.seed, i) - 0.5f, FxDraw.rnd(s.seed, i + 30) * 0.9f - 0.2f, FxDraw.rnd(s.seed, i + 60) - 0.5f);
			if (dir.lengthSquared() < 1.0e-4f) {
				dir.set(0, 1, 0);
			}
			dir.normalize();
			float len = radius * (0.8f + 0.7f * FxDraw.rnd(s.seed, i + 90)) * grow;
			Vector3f a = new Vector3f(dir).mul(len * 0.35f);
			Vector3f b = new Vector3f(dir).mul(len * 1.15f);
			d.tube(a, b, 0.14f * s.size, 0, 4, i, FxDraw.alpha(s.color, 0.9f * fade), false);
		}
		// Smoke ring rolling out along the ground.
		float ring = radius * (0.6f + 1.0f * grow);
		Vector3f ground = new Vector3f(0, -radius * 0.35f, 0);
		d.disc(ground, ring * 0.7f, ring, 28, FxDraw.alpha(s.color2, 0.45f * fadeAfter(p, 0.45f)));
		d.band(ground, ring, 0, 0.5f * s.size * (1 - p) + 0.1f, 28, FxDraw.alpha(s.color2, 0.4f * fadeAfter(p, 0.45f)));
	}

	/** A glowing doorway standing in the air: a ring that opens, a swirl inside it, then it closes. */
	private static void gate(FxDraw d, State s, float p) {
		float radius = Math.max(0.4f, s.reach.length());
		float open = p < 0.2f ? p / 0.2f : p > 0.75f ? 1 - (p - 0.75f) / 0.25f : 1;
		open = Mth.clamp(open, 0, 1);
		if (open < 0.02f) {
			return;
		}
		Vector3f[] f = FxDraw.frame(s.reach, 0);
		float r = radius * open;
		int seg = 20;
		Vector3f c = new Vector3f();
		// The frame: a thick bright ring, with a softer halo around it.
		for (int i = 0; i < seg; i++) {
			float a0 = i * Mth.TWO_PI / seg, a1 = (i + 1) * Mth.TWO_PI / seg;
			Vector3f p0 = ellipse(c, f, a0, r * 0.75f, r);
			Vector3f p1 = ellipse(c, f, a1, r * 0.75f, r);
			d.tube(p0, p1, 0.07f * s.size, 0.07f * s.size, 4, 0, FxDraw.alpha(s.color, 0.95f), false);
			d.tube(p0, p1, 0.2f * s.size, 0.2f * s.size, 4, 0.8f, FxDraw.alpha(s.color2, 0.35f), false);
			// The see-through middle.
			d.quad(c, p0, p1, c, FxDraw.alpha(s.color2, 0.22f * open), new Vector3f(f[2]));
		}
		// A swirl turning inside it.
		for (int k = 0; k < 3; k++) {
			Vector3f last = new Vector3f(c);
			for (int i = 1; i <= 8; i++) {
				float t = i / 8f;
				float a = s.age * 0.35f + k * Mth.TWO_PI / 3 + t * 2.4f;
				Vector3f next = ellipse(c, f, a, r * 0.7f * t, r * 0.9f * t);
				d.tube(last, next, 0.03f * s.size, 0.03f * s.size, 3, 0, FxDraw.alpha(s.color, 0.7f * open), false);
				last = next;
			}
		}
	}

	/** A point on an upright oval facing along f[2]: width along f[0], height along f[1]. */
	private static Vector3f ellipse(Vector3f c, Vector3f[] f, float angle, float width, float height) {
		return new Vector3f(c).add(new Vector3f(f[0]).mul(Mth.cos(angle) * width)).add(new Vector3f(f[1]).mul(Mth.sin(angle) * height));
	}

	/** Sound waves: four rings rolling forward along the reach, growing as they go, one after the other. */
	private static void waves(FxDraw d, State s, float p) {
		float length = s.reach.length();
		Vector3f dir = new Vector3f(s.reach).normalize();
		Vector3f[] f = FxDraw.frame(dir, 0);
		int count = 4;
		for (int k = 0; k < count; k++) {
			float t = (p * 1.6f) - k * 0.18f;
			if (t <= 0 || t >= 1) {
				continue;
			}
			Vector3f c = new Vector3f(dir).mul(length * t);
			float r = (0.35f + 1.6f * t) * s.size;
			float a = (1 - t) * 0.9f;
			int seg = 18;
			for (int i = 0; i < seg; i++) {
				float a0 = i * Mth.TWO_PI / seg, a1 = (i + 1) * Mth.TWO_PI / seg;
				Vector3f p0 = ellipse(c, f, a0, r, r);
				Vector3f p1 = ellipse(c, f, a1, r, r);
				d.tube(p0, p1, 0.05f * s.size, 0.05f * s.size, 4, 0, FxDraw.alpha(k % 2 == 0 ? s.color : s.color2, a), false);
			}
			// Little musical notes riding on the wave.
			Vector3f note = ellipse(c, f, FxDraw.rnd(s.seed, k) * Mth.TWO_PI, r, r);
			d.sphere(note, 0.09f * s.size, 1, FxDraw.alpha(s.color, a));
			d.tube(note, new Vector3f(note).add(new Vector3f(f[1]).mul(0.3f * s.size)), 0.02f * s.size, 0.02f * s.size, 3, 0, FxDraw.alpha(s.color, a), false);
		}
	}

	/** A glassy panel of hexagons facing along the reach: pops up, shimmers, then cracks away. */
	private static void shield(FxDraw d, State s, float p) {
		float half = Math.max(0.5f, s.size);
		float pop = Math.min(1, p / 0.15f);
		float fade = fadeAfter(p, 0.7f);
		if (pop * fade < 0.02f) {
			return;
		}
		Vector3f[] f = FxDraw.frame(s.reach, 0);
		Vector3f normal = new Vector3f(f[2]);
		float hex = 0.32f * half;
		float shimmer = 0.5f + 0.5f * Mth.sin(s.age * 0.6f + s.seed);
		int rows = Math.max(2, Math.round(half / (hex * 1.5f)));
		for (int row = -rows; row <= rows; row++) {
			for (int col = -rows; col <= rows; col++) {
				float x = (col + (row & 1) * 0.5f) * hex * 1.75f;
				float y = row * hex * 1.5f;
				if (x * x + y * y > half * half) {
					continue;
				}
				Vector3f center = new Vector3f(f[0]).mul(x * pop).add(new Vector3f(f[1]).mul(y * pop));
				// Each cell drifts away a little as the shield breaks.
				if (p > 0.7f) {
					center.add(new Vector3f(normal).mul((p - 0.7f) * 2 * FxDraw.rnd(s.seed, row * 31 + col)));
				}
				float k = hex * 0.92f * pop;
				Vector3f last = null;
				for (int i = 0; i <= 6; i++) {
					float a = i * Mth.TWO_PI / 6 + Mth.PI / 6;
					Vector3f corner = ellipse(center, f, a, k, k);
					if (last != null) {
						d.tube(last, corner, 0.025f * half, 0.025f * half, 3, 0, FxDraw.alpha(s.color, 0.9f * fade), false);
						d.quad(center, last, corner, center, FxDraw.alpha(s.color2, (0.18f + 0.12f * shimmer) * fade), normal);
					}
					last = corner;
				}
			}
		}
	}

	/** Two ribbons spiraling up around you, sparkling at their tips. */
	private static void helix(FxDraw d, State s, float p) {
		float height = Math.max(1, s.reach.length());
		float radius = Math.max(0.4f, s.size);
		float fade = fadeAfter(p, 0.6f);
		float rise = Math.min(1, p / 0.5f);
		Vector3f base = new Vector3f(s.anchor);
		int steps = 16;
		for (int k = 0; k < 2; k++) {
			Vector3f last = null;
			for (int i = 0; i <= steps; i++) {
				float t = i / (float) steps * rise;
				float a = s.age * 0.3f + k * Mth.PI + t * Mth.TWO_PI * 1.5f;
				float r = radius * (1 - 0.35f * t);
				Vector3f next = new Vector3f(base).add(Mth.cos(a) * r, t * height, Mth.sin(a) * r);
				if (last != null) {
					float w = 0.06f * (0.4f + 0.6f * i / steps);
					d.tube(last, next, w, w, 4, 0, FxDraw.alpha(k == 0 ? s.color : s.color2, 0.85f * fade * (0.3f + 0.7f * i / steps)), false);
				}
				last = next;
			}
			d.sphere(last, 0.13f, 1, FxDraw.alpha(0xFFFFFFFF, 0.9f * fade));
			d.sphere(last, 0.26f, 1, FxDraw.alpha(k == 0 ? s.color : s.color2, 0.4f * fade));
		}
	}

	/** A web spreading out flat: spokes from the middle, joined by rings of thread. */
	private static void web(FxDraw d, State s, float p) {
		float radius = Math.max(0.5f, s.reach.length());
		float grow = Math.min(1, p / 0.25f);
		float fade = fadeAfter(p, 0.65f);
		Vector3f[] f = FxDraw.frame(s.reach, FxDraw.rnd(s.seed, 1));
		int spokes = 8;
		float w = 0.025f * Math.max(0.6f, s.size);
		Vector3f c = new Vector3f();
		Vector3f[] tips = new Vector3f[spokes];
		for (int i = 0; i < spokes; i++) {
			float a = i * Mth.TWO_PI / spokes + (FxDraw.rnd(s.seed, i) - 0.5f) * 0.3f;
			tips[i] = ellipse(c, f, a, radius * grow, radius * grow);
			d.tube(c, tips[i], w, w, 3, 0, FxDraw.alpha(s.color, 0.95f * fade), false);
		}
		for (int ring = 1; ring <= 4; ring++) {
			float t = ring / 4f;
			for (int i = 0; i < spokes; i++) {
				Vector3f a = new Vector3f(tips[i]).mul(t);
				Vector3f b = new Vector3f(tips[(i + 1) % spokes]).mul(t);
				// The thread sags a little toward the middle, like a real web.
				Vector3f mid = new Vector3f(a).add(b).mul(0.5f * 0.92f);
				d.tube(a, mid, w * 0.8f, w * 0.8f, 3, 0, FxDraw.alpha(s.color, 0.85f * fade), false);
				d.tube(mid, b, w * 0.8f, w * 0.8f, 3, 0, FxDraw.alpha(s.color, 0.85f * fade), false);
			}
		}
		d.sphere(c, radius * 0.08f + 0.05f, 1, FxDraw.alpha(s.color2, 0.6f * fade));
	}
}
