package com.onepiecemod.seatrain;

import java.util.ArrayList;
import java.util.List;

import org.joml.Quaternionf;
import org.joml.Vector3f;

import com.mojang.math.Transformation;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.Identifier;
import net.minecraft.nbt.NbtOps;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.ProblemReporter;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.TagValueInput;
import net.minecraft.world.phys.Vec3;

/**
 * What the Puffing Tom looks like: a steam engine with big red paddle wheels and a tall chimney,
 * pulling two blue carriages. Built from block displays (stretched blocks) riding the train,
 * so it needs no model files and looks the same for every player.
 *
 * Measured from the train's root, in blocks: +Z is forward, +X is the right-hand side.
 */
public class PuffingTom {
	/** The top of the chimney, where the steam comes out. */
	static final Vec3 CHIMNEY = new Vec3(0, 5.0, 6.1);

	/** Every train part carries this tag, so stray parts (from a restart mid-trip) can be cleared away. */
	static final String PART_TAG = "onepiece_sea_train_part";

	/** One stretched block: its lower corner, its size, and what it's made of (a vanilla block id, looked up when built). */
	private record Part(float x, float y, float z, float sx, float sy, float sz, String block, boolean glow) {}

	private static final List<Part> PARTS = new ArrayList<>();

	private static void box(float x, float y, float z, float sx, float sy, float sz, String block) {
		PARTS.add(new Part(x, y, z, sx, sy, sz, block, false));
	}

	private static void lamp(float x, float y, float z, float sx, float sy, float sz, String block) {
		PARTS.add(new Part(x, y, z, sx, sy, sz, block, true));
	}

	static {
		// ---- The engine (z 0 to 8.4) ----
		box(-1.5f, 0.15f, 0f, 3f, 0.45f, 8f, "black_concrete"); // chassis
		box(-1.2f, -0.2f, 0.6f, 2.4f, 0.4f, 1.4f, "gray_concrete"); // wheel trucks under the deck
		box(-1.2f, -0.2f, 5.8f, 2.4f, 0.4f, 1.4f, "gray_concrete");
		box(-1.1f, 0.6f, 2.5f, 2.2f, 1.7f, 5.0f, "black_concrete"); // the boiler
		box(-1.15f, 0.55f, 3.6f, 2.3f, 1.8f, 0.2f, "gold_block"); // brass bands round the boiler
		box(-1.15f, 0.55f, 5.4f, 2.3f, 1.8f, 0.2f, "gold_block");
		box(-1.2f, 0.55f, 7.4f, 2.4f, 1.9f, 0.35f, "cyan_terracotta"); // the front plate
		lamp(-0.4f, 1.5f, 7.65f, 0.8f, 0.8f, 0.25f, "sea_lantern"); // headlamp
		box(-1.45f, -0.15f, 7.8f, 2.9f, 0.45f, 0.6f, "iron_block"); // cow-catcher
		box(-0.45f, 2.3f, 5.65f, 0.9f, 2.1f, 0.9f, "black_concrete"); // chimney
		box(-0.65f, 4.4f, 5.45f, 1.3f, 0.35f, 1.3f, "gold_block"); // chimney crown
		box(-0.35f, 2.3f, 3.9f, 0.7f, 0.5f, 0.7f, "copper_block"); // steam dome
		// Paddle wheels: a red drum on each side with a dark hub.
		box(-1.95f, -0.3f, 2.6f, 0.45f, 2.7f, 2.7f, "red_concrete");
		box(1.5f, -0.3f, 2.6f, 0.45f, 2.7f, 2.7f, "red_concrete");
		box(-2.05f, 0.65f, 3.55f, 0.15f, 0.8f, 0.8f, "black_concrete");
		box(1.9f, 0.65f, 3.55f, 0.15f, 0.8f, 0.8f, "black_concrete");
		// The cab: open at the sides, with a roof. The passenger sits here.
		box(-1.5f, 0.6f, 2.25f, 3f, 1.4f, 0.25f, "dark_oak_planks"); // front wall under the windows
		box(-1.45f, 0.6f, -0.1f, 0.2f, 2.3f, 0.2f, "dark_oak_log"); // corner posts
		box(1.25f, 0.6f, -0.1f, 0.2f, 2.3f, 0.2f, "dark_oak_log");
		box(-1.45f, 0.6f, 2.25f, 0.2f, 2.3f, 0.2f, "dark_oak_log");
		box(1.25f, 0.6f, 2.25f, 0.2f, 2.3f, 0.2f, "dark_oak_log");
		box(-1.7f, 2.9f, -0.3f, 3.4f, 0.25f, 2.95f, "red_terracotta"); // cab roof
		box(-0.25f, 0.2f, -1.0f, 0.5f, 0.3f, 1.0f, "iron_block"); // coupling

		// ---- Two carriages behind ----
		carriage(-8.0f);
		carriage(-16.0f);
	}

	private static void carriage(float z) {
		box(-1.45f, -0.2f, z + 0.7f, 2.9f, 0.4f, 1.2f, "gray_concrete"); // wheel trucks
		box(-1.45f, -0.2f, z + 5.1f, 2.9f, 0.4f, 1.2f, "gray_concrete");
		box(-1.5f, 0.2f, z, 3f, 0.4f, 7f, "dark_oak_planks"); // floor
		box(-1.5f, 0.6f, z, 3f, 1.0f, 7f, "blue_concrete"); // lower walls
		box(-1.45f, 1.6f, z + 0.2f, 2.9f, 0.85f, 6.6f, "light_blue_stained_glass"); // windows
		for (float post : new float[] {0f, 1.7f, 3.4f, 5.1f, 6.75f}) {
			box(-1.5f, 1.6f, z + post, 3f, 0.85f, 0.25f, "blue_concrete"); // posts between the windows
		}
		box(-1.5f, 2.45f, z, 3f, 0.2f, 7f, "white_concrete"); // trim under the roof
		box(-1.65f, 2.65f, z - 0.1f, 3.3f, 0.25f, 7.2f, "red_terracotta"); // roof
		box(-1.0f, 2.9f, z + 0.3f, 2.0f, 0.2f, 6.4f, "red_terracotta"); // raised middle of the roof
		box(-0.25f, 0.25f, z + 7f, 0.5f, 0.3f, 1.0f, "iron_block"); // coupling to the car in front
	}

	/** Builds the engine and carriages around a train and puts them aboard it. */
	static void assemble(ServerLevel level, SeaTrainEntity train) {
		for (Part part : PARTS) {
			Entity display = display(level, part, train.getYRot());
			if (display != null) {
				display.setPos(train.getX(), train.getY(), train.getZ());
				level.addFreshEntity(display);
				display.startRiding(train, true, false);
			}
		}
	}

	private static Entity display(ServerLevel level, Part part, float yaw) {
		CompoundTag tag = new CompoundTag();
		tag.put("block_state", BlockState.CODEC.encodeStart(NbtOps.INSTANCE,
				BuiltInRegistries.BLOCK.getValue(Identifier.withDefaultNamespace(part.block())).defaultBlockState()).getOrThrow());
		Transformation transformation = new Transformation(new Vector3f(part.x(), part.y(), part.z()), new Quaternionf(),
				new Vector3f(part.sx(), part.sy(), part.sz()), new Quaternionf());
		tag.put("transformation", Transformation.EXTENDED_CODEC.encodeStart(NbtOps.INSTANCE, transformation).getOrThrow());
		tag.putFloat("view_range", 3.0f); // Seen from as far as a big ship.
		// The parts all sit at the train's root, which is often inside the platform floor (light 0).
		// Full sky light still follows day and night; the headlamp glows on its own.
		CompoundTag brightness = new CompoundTag();
		brightness.putInt("block", part.glow() ? 15 : 0);
		brightness.putInt("sky", 15);
		tag.put("brightness", brightness);
		Entity entity = EntityType.loadEntityRecursive(EntityTypes.BLOCK_DISPLAY,
				TagValueInput.create(ProblemReporter.DISCARDING, level.registryAccess(), tag), level,
				EntitySpawnReason.TRIGGERED, e -> e);
		if (entity != null) {
			entity.addTag(PART_TAG);
			entity.setYRot(yaw);
			entity.setYHeadRot(yaw);
		}
		return entity;
	}
}
