package com.onepiecemod.sea;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.LodestoneTracker;
import net.minecraft.world.level.Level;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;

import com.onepiecemod.OnePieceMod;

/**
 * How the Log Pose works, like in the Grand Line:
 * stay on an island for 45 seconds with a Log Pose in your inventory and it records that island.
 * Then its needle points to the next island. Sail there, stay a while again, and it points to the one after.
 *
 * The islands you've recorded are saved on the player, so the needle never leads you back.
 */
public class LogPoseTracker {
	/** Seconds on an island before the Log Pose records it. Settings file: log_pose_record_seconds (45). */
	public static int recordSeconds() {
		return com.onepiecemod.config.ModConfig.logPoseRecordSeconds();
	}

	/** Only the most recent islands are remembered, so in a long journey old ones can come round again. */
	private static final int REMEMBERED_ISLANDS = 16;

	/** A player's journey: islands already recorded (oldest first) and where the needle points now. */
	public record Journey(List<BlockPos> visited, Optional<BlockPos> target) {
		public static final Codec<Journey> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				BlockPos.CODEC.listOf().fieldOf("visited").forGetter(Journey::visited),
				BlockPos.CODEC.optionalFieldOf("target").forGetter(Journey::target)
		).apply(instance, Journey::new));

		public static final Journey EMPTY = new Journey(List.of(), Optional.empty());

		public Optional<BlockPos> currentIsland() {
			return visited.isEmpty() ? Optional.empty() : Optional.of(visited.get(visited.size() - 1));
		}
	}

	public static final AttachmentType<Journey> JOURNEY = AttachmentRegistry.create(
			OnePieceMod.id("log_pose_journey"),
			builder -> builder
					.persistent(Journey.CODEC) // Save it to disk.
					.copyOnDeath() // Dying doesn't erase where you've been.
	);

	/** Where each player started standing still on land, and for how many seconds. Not saved. */
	private record Recording(BlockPos start, int seconds) {
	}

	private static final Map<UUID, Recording> RECORDING = new HashMap<>();

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 20 != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				tick(player);
			}
		});
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> RECORDING.remove(handler.getPlayer().getUUID()));
	}

	public static Journey journey(ServerPlayer player) {
		Journey journey = player.getAttached(JOURNEY);
		return journey != null ? journey : Journey.EMPTY;
	}

	/** How many seconds the player has been recording the island they're on, or 0. */
	public static int secondsRecorded(ServerPlayer player) {
		Recording recording = RECORDING.get(player.getUUID());
		return recording != null ? recording.seconds() : 0;
	}

	/** Runs once a second for each player. */
	private static void tick(ServerPlayer player) {
		if (player.level().dimension() != Level.OVERWORLD || !hasLogPose(player.getInventory())) {
			RECORDING.remove(player.getUUID());
			return;
		}
		Journey journey = journey(player);
		pointLogPoses(player.getInventory(), journey.target());

		if (!standingOnIsland(player)) {
			RECORDING.remove(player.getUUID());
			return;
		}
		BlockPos here = player.blockPosition();
		Optional<BlockPos> current = journey.currentIsland();
		if (current.isPresent() && IslandFinder.horizontalDistance(current.get(), here) < IslandFinder.ISLAND_SPACING) {
			return; // This island is already recorded.
		}

		// Count up while the player stays on the same island. Walking around it is fine; wander far off and it starts again.
		Recording recording = RECORDING.get(player.getUUID());
		if (recording == null || IslandFinder.horizontalDistance(recording.start(), here) > 96) {
			recording = new Recording(here, 0);
		}
		recording = new Recording(recording.start(), recording.seconds() + 1);
		RECORDING.put(player.getUUID(), recording);

		if (recording.seconds() < recordSeconds()) {
			return; // Records quietly; one chat line when it's done. Right-click the Log Pose to check progress.
		}
		RECORDING.remove(player.getUUID());
		recordIsland(player, journey, here);
	}

	private static void recordIsland(ServerPlayer player, Journey journey, BlockPos here) {
		ServerLevel level = (ServerLevel) player.level();
		if (journey.target().isPresent()
				&& IslandFinder.horizontalDistance(journey.target().get(), here) < IslandFinder.ISLAND_SPACING) {
			player.sendSystemMessage(Component.literal("You made it to the island your Log Pose pointed to!")
					.withStyle(ChatFormatting.GOLD));
		}

		List<BlockPos> visited = new ArrayList<>(journey.visited());
		visited.add(here);
		while (visited.size() > REMEMBERED_ISLANDS) {
			visited.remove(0);
		}
		Optional<BlockPos> next = journey.visited().isEmpty() && StartingIsland.isOnStartingIsland(level, here)
				? StartingIsland.site(level).firstIsland() // Your first reading points to Foosha Village, where the story starts.
				: Optional.empty();
		if (next.isEmpty()) {
			next = IslandFinder.findNext(level, here, visited);
		}
		player.setAttached(JOURNEY, new Journey(visited, next));
		pointLogPoses(player.getInventory(), next);

		level.playSound(null, player.blockPosition(), SoundEvents.LODESTONE_COMPASS_LOCK, SoundSource.PLAYERS, 1.0f, 1.0f);
		if (next.isPresent()) {
			int distance = (int) IslandFinder.horizontalDistance(here, next.get());
			player.sendSystemMessage(Component.literal("Your Log Pose recorded this island. The needle now points to the next island: ")
					.append(targetName(level, next.get()))
					.append(", about " + distance + " blocks away.")
					.withStyle(ChatFormatting.AQUA));
		} else {
			player.sendSystemMessage(Component.literal("Your Log Pose recorded this island, but there's no other island within "
					+ "2000 blocks. The needle spins.").withStyle(ChatFormatting.GRAY));
		}
	}

	/** On solid ground, not swimming, not riding a boat or ship, and not in an ocean or river biome (except the starting island). */
	private static boolean standingOnIsland(ServerPlayer player) {
		return player.onGround() && !player.isInWater() && !player.isPassenger()
				&& (IslandFinder.isLand(player.level().getBiome(player.blockPosition()))
						|| StartingIsland.isOnStartingIsland(player.level(), player.blockPosition())); // It's built out in an ocean biome.
	}

	private static boolean hasLogPose(Inventory inventory) {
		for (int slot = 0; slot < inventory.getContainerSize(); slot++) {
			if (inventory.getItem(slot).is(SeaItems.LOG_POSE)) {
				return true;
			}
		}
		return false;
	}

	/**
	 * Makes every Log Pose in the inventory point at the target. The needle uses the same
	 * "lodestone" data a compass uses, so Minecraft turns it toward the target by itself.
	 */
	private static void pointLogPoses(Inventory inventory, Optional<BlockPos> target) {
		LodestoneTracker wanted = target
				.map(pos -> new LodestoneTracker(Optional.of(GlobalPos.of(Level.OVERWORLD, pos)), false))
				.orElse(null);
		for (int slot = 0; slot < inventory.getContainerSize(); slot++) {
			ItemStack stack = inventory.getItem(slot);
			if (stack.is(SeaItems.LOG_POSE) && !Objects.equals(stack.get(DataComponents.LODESTONE_TRACKER), wanted)) {
				if (wanted != null) {
					stack.set(DataComponents.LODESTONE_TRACKER, wanted);
				} else {
					stack.remove(DataComponents.LODESTONE_TRACKER);
				}
			}
		}
	}

	/** What to call the island the needle points to: Foosha Village for the very first reading, otherwise the island's biome. */
	public static Component targetName(ServerLevel level, BlockPos target) {
		if (StartingIsland.site(level).firstIsland().filter(target::equals).isPresent()) {
			return Component.literal("Foosha Village on Dawn Island");
		}
		return IslandFinder.islandName(level, target);
	}

}
