package com.onepiecemod.mesh.client;

import java.io.DataInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.BufferedInputStream;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

import org.joml.Matrix4f;
import org.joml.Vector3f;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;

import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.server.packs.resources.Resource;
import net.minecraft.util.Mth;

import com.onepiecemod.OnePieceMod;

/**
 * Smooth, curved models (no cubes) for the big transformations: Imu's forms, Loki and his Nidhogg form,
 * Luffy's Wild Nika. They are made by tools/meshes/gen_meshes.py and saved as
 * assets/onepiece/meshes/<name>.bin: a set of bones, each with its own patch of small coloured faces and
 * its own wobble/swing animations. The colours sit on the corners of the faces, so one plain white
 * texture is used and Minecraft's normal lighting shades the curves.
 *
 * BossForms, ZoanClient and CharacterRenderer ask has(name) first and fall back to their cube models.
 */
public final class MeshForms {
	private static final Identifier WHITE = OnePieceMod.id("textures/entity/fx/white.png");
	private static final int MAGIC = 0x4F504D31;
	/** Corners whose colour has this alpha glow (eyes, flames). */
	private static final int GLOW_ALPHA = 0xFE;

	private static final Map<String, Optional<Mesh>> CACHE = new ConcurrentHashMap<>();

	private MeshForms() {
	}

	/** What the model is doing this frame. */
	public static final class Input {
		public float ageInTicks;
		public float walkPos;
		public float walkSpeed;
		/** Head turn and tilt relative to the body, in degrees. */
		public float headYaw;
		public float headPitch;
		public boolean flying;
		/** Ticks since the transformation started (the roar plays for the first 30), or -1. */
		public float formAge = -1;
		/** 0 to 1 while an attack plays, otherwise -1. */
		public float attack = -1;
	}

	private record Anim(int state, int axis, float amp, float period, float phase) {
	}

	private static final class Bone {
		int parent;
		float px, py, pz;
		Anim[] anims;
		float[] pos;
		float[] nrm;
		int[] col;
	}

	public static final class Mesh {
		/** For a character's own look: the size the character was modelled at (drawn at its real size / this). */
		final float scale;
		final Bone[] bones;

		Mesh(float scale, Bone[] bones) {
			this.scale = scale;
			this.bones = bones;
		}

		public float scale() {
			return scale;
		}
	}

	/** The mesh with this name, or null when there's none (or it failed to load). */
	public static Mesh get(String name) {
		return CACHE.computeIfAbsent(name, MeshForms::load).orElse(null);
	}

	public static boolean has(String name) {
		return get(name) != null;
	}

	/** Forgets loaded meshes (after a resource reload). */
	public static void clear() {
		CACHE.clear();
	}

	private static Optional<Mesh> load(String name) {
		Optional<Resource> resource = Minecraft.getInstance().getResourceManager().getResource(OnePieceMod.id("meshes/" + name + ".bin"));
		if (resource.isEmpty()) {
			return Optional.empty();
		}
		try (InputStream raw = resource.get().open(); DataInputStream in = new DataInputStream(new BufferedInputStream(raw))) {
			if (in.readInt() != MAGIC) {
				throw new IOException("not a mesh file");
			}
			float scale = in.readFloat();
			Bone[] bones = new Bone[in.readInt()];
			for (int b = 0; b < bones.length; b++) {
				Bone bone = new Bone();
				in.readUTF();
				bone.parent = in.readInt();
				bone.px = in.readFloat();
				bone.py = in.readFloat();
				bone.pz = in.readFloat();
				bone.anims = new Anim[in.readInt()];
				for (int a = 0; a < bone.anims.length; a++) {
					bone.anims[a] = new Anim(in.readByte(), in.readByte(), in.readFloat(), in.readFloat(), in.readFloat());
				}
				int corners = in.readInt() * 4;
				bone.pos = new float[corners * 3];
				bone.nrm = new float[corners * 3];
				bone.col = new int[corners];
				for (int v = 0; v < corners; v++) {
					bone.pos[v * 3] = in.readFloat();
					bone.pos[v * 3 + 1] = in.readFloat();
					bone.pos[v * 3 + 2] = in.readFloat();
					bone.nrm[v * 3] = in.readByte() / 127.0f;
					bone.nrm[v * 3 + 1] = in.readByte() / 127.0f;
					bone.nrm[v * 3 + 2] = in.readByte() / 127.0f;
					bone.col[v] = in.readInt();
				}
				bones[b] = bone;
			}
			return Optional.of(new Mesh(scale, bones));
		} catch (IOException | RuntimeException e) {
			OnePieceMod.LOGGER.warn("Couldn't load mesh {}: {}", name, e.toString());
			return Optional.empty();
		}
	}

	private static float value(Anim a, Input in) {
		float t = in.ageInTicks / 20.0f;
		return switch (a.state) {
			case 0 -> a.amp * Mth.sin(Mth.TWO_PI * t / a.period + a.phase);
			case 1 -> a.amp * Mth.sin(in.walkPos * 0.6662f * a.period + a.phase) * Math.min(1.0f, in.walkSpeed);
			case 2 -> in.attack >= 0 ? a.amp * Mth.sin(Mth.PI * in.attack) : 0;
			case 3 -> in.formAge >= 0 && in.formAge < 30 ? a.amp * Mth.sin(Mth.PI * in.formAge / 30.0f) : 0;
			case 4 -> in.flying ? a.amp * Mth.sin(Mth.TWO_PI * t / a.period + a.phase) : 0;
			case 5 -> in.flying ? 0 : a.amp;
			case 6 -> a.amp * (a.axis == 1 ? -in.headYaw : -in.headPitch);
			case 7 -> in.attack >= 0 ? a.amp * slash(in.attack) : 0;
			default -> 0;
		};
	}

	/**
	 * A heavy weapon swing over 0..1: a slow wind-up the other way, a fast strike through, a short hold,
	 * then an eased return. Peaks at 1, dips to -0.4 during the wind-up.
	 */
	static float slash(float t) {
		if (t < 0.35f) {
			return -0.4f * smooth(t / 0.35f);
		}
		if (t < 0.55f) {
			float u = 1.0f - (t - 0.35f) / 0.2f;
			return -0.4f + 1.4f * (1.0f - u * u * u);
		}
		return 1.0f - smooth(Math.min(1.0f, (t - 0.55f) / 0.45f));
	}

	private static float smooth(float x) {
		return x * x * (3.0f - 2.0f * x);
	}

	/**
	 * Draws the mesh standing at the pose stack's origin, facing the way the entity faces.
	 * size multiplies the whole model; deathTime > 0 makes it topple over.
	 */
	public static void submit(Mesh mesh, Input in, PoseStack poseStack, SubmitNodeCollector collector, float bodyRot, float size,
			float deathTime, int light, int overlay) {
		Matrix4f[] mats = new Matrix4f[mesh.bones.length];
		for (int b = 0; b < mesh.bones.length; b++) {
			Bone bone = mesh.bones[b];
			float rx = 0, ry = 0, rz = 0, up = 0;
			for (Anim a : bone.anims) {
				float v = value(a, in);
				switch (a.axis) {
					case 0 -> rx += v;
					case 1 -> ry += v;
					case 2 -> rz += v;
					default -> up += v;
				}
			}
			Matrix4f m = bone.parent >= 0 ? new Matrix4f(mats[bone.parent]) : new Matrix4f();
			if (rx != 0 || ry != 0 || rz != 0 || up != 0) {
				m.translate(bone.px, bone.py + up, bone.pz)
						.rotateZYX(rz * Mth.DEG_TO_RAD, ry * Mth.DEG_TO_RAD, rx * Mth.DEG_TO_RAD)
						.translate(-bone.px, -bone.py, -bone.pz);
			}
			mats[b] = m;
		}

		poseStack.pushPose();
		if (deathTime > 0) {
			float fall = Math.min(1.0f, (deathTime - 1.0f) / 20.0f * 1.6f);
			poseStack.rotate(Axis.ZP.rotationDegrees((float) Math.sqrt(Math.max(0.0f, fall)) * 90.0f));
		}
		poseStack.rotate(Axis.YP.rotationDegrees(180.0f - bodyRot));
		poseStack.scale(size, size, size);
		collector.submitCustomGeometry(poseStack, RenderTypes.entityCutout(WHITE), (pose, out) -> {
			Vector3f p = new Vector3f();
			Vector3f n = new Vector3f();
			for (int b = 0; b < mesh.bones.length; b++) {
				Bone bone = mesh.bones[b];
				Matrix4f m = mats[b];
				int corners = bone.col.length;
				for (int v = 0; v < corners; v++) {
					m.transformPosition(bone.pos[v * 3], bone.pos[v * 3 + 1], bone.pos[v * 3 + 2], p);
					m.transformDirection(bone.nrm[v * 3], bone.nrm[v * 3 + 1], bone.nrm[v * 3 + 2], n);
					int argb = bone.col[v];
					boolean glow = (argb >>> 24) == GLOW_ALPHA;
					out.addVertex(pose, p.x, p.y, p.z)
							.setColor(argb | 0xFF000000)
							.setUv(0.5f, 0.5f)
							.setOverlay(overlay)
							.setLight(glow ? 0xF000F0 : light)
							.setNormal(pose, n.x, n.y, n.z);
				}
			}
		});
		poseStack.popPose();
	}
}
