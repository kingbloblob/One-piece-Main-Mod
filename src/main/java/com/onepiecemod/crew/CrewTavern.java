package com.onepiecemod.crew;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

/**
 * The Pirate Tavern: the building you need before anyone will join your crew
 * (like Partys Bar, where Luffy met Shanks). Everything is measured from the Recruitment Board,
 * which stands on the floor in the middle of the room:
 *
 *   Floor:     5x5 of any planks, under the board.
 *   Posts:     a log post in each corner, 3 blocks tall.
 *   Roof:      5x5 of planks, wooden slabs or wooden stairs, on top of the posts.
 *   Inside:    2 Barrels (the bar), 1 Lantern, 1 Bed (for new recruits).
 *
 * Walls and doors are up to you.
 */
public class CrewTavern {
	public static final int SIZE = 5;
	private static final int HALF = SIZE / 2;
	private static final int HEIGHT = 3; // Room height between floor and roof.

	/** What's still missing: block positions to outline, and furniture to add. */
	public record Check(List<BlockPos> missingBlocks, List<String> missingThings) {
		public boolean complete() {
			return missingBlocks.isEmpty() && missingThings.isEmpty();
		}
	}

	/** Checks the tavern whose Recruitment Board is (or will be) at boardPos. */
	public static Check check(ServerLevel level, BlockPos boardPos) {
		List<BlockPos> missing = new ArrayList<>();
		List<String> things = new ArrayList<>();
		int floorMissing = 0;
		int postsMissing = 0;
		int roofMissing = 0;

		for (int dx = -HALF; dx <= HALF; dx++) {
			for (int dz = -HALF; dz <= HALF; dz++) {
				BlockPos floor = boardPos.offset(dx, -1, dz);
				if (!level.getBlockState(floor).is(BlockTags.PLANKS)) {
					missing.add(floor);
					floorMissing++;
				}
				BlockPos roof = boardPos.offset(dx, HEIGHT, dz);
				BlockState roofState = level.getBlockState(roof);
				if (!roofState.is(BlockTags.PLANKS) && !roofState.is(BlockTags.WOODEN_SLABS) && !roofState.is(BlockTags.WOODEN_STAIRS)) {
					missing.add(roof);
					roofMissing++;
				}
				if (Math.abs(dx) == HALF && Math.abs(dz) == HALF) {
					for (int dy = 0; dy < HEIGHT; dy++) {
						BlockPos post = boardPos.offset(dx, dy, dz);
						if (!level.getBlockState(post).is(BlockTags.LOGS)) {
							missing.add(post);
							postsMissing++;
						}
					}
				}
			}
		}

		// Count the furniture inside the room.
		int barrels = 0;
		int lanterns = 0;
		int beds = 0;
		for (BlockPos pos : BlockPos.betweenClosed(boardPos.offset(-HALF, 0, -HALF), boardPos.offset(HALF, HEIGHT - 1, HALF))) {
			BlockState state = level.getBlockState(pos);
			if (state.is(Blocks.BARREL)) {
				barrels++;
			} else if (state.is(Blocks.LANTERN) || state.is(Blocks.SOUL_LANTERN)) {
				lanterns++;
			} else if (state.is(BlockTags.BEDS)) {
				beds++;
			}
		}

		if (!level.getBlockState(boardPos).is(CrewBlocks.RECRUITMENT_BOARD)) {
			things.add("a Recruitment Board in the middle of the floor");
		}
		if (floorMissing > 0) {
			things.add(floorMissing + " more planks in the 5x5 floor");
		}
		if (postsMissing > 0) {
			things.add(postsMissing + " more logs for the corner posts (3 tall)");
		}
		if (roofMissing > 0) {
			things.add(roofMissing + " more planks, wooden slabs or stairs for the 5x5 roof");
		}
		if (barrels < 2) {
			things.add((2 - barrels) + " more Barrel" + (barrels == 0 ? "s" : "") + " for the bar");
		}
		if (lanterns < 1) {
			things.add("a Lantern");
		}
		if (beds < 1) {
			things.add("a Bed for new recruits");
		}
		return new Check(missing, things);
	}

	/** True if the player stands within 8 blocks of a Recruitment Board in a finished tavern. */
	public static boolean playerIsAtTavern(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		BlockPos center = player.blockPosition();
		for (BlockPos pos : BlockPos.betweenClosed(center.offset(-8, -4, -8), center.offset(8, 4, 8))) {
			if (level.getBlockState(pos).is(CrewBlocks.RECRUITMENT_BOARD) && check(level, pos.immutable()).complete()) {
				return true;
			}
		}
		return false;
	}

	/** Lists what's missing in chat and shows the outline for 30 seconds. */
	public static void explain(ServerPlayer player, BlockPos boardPos) {
		Check result = check((ServerLevel) player.level(), boardPos);
		if (result.complete()) {
			player.sendSystemMessage(Component.literal("This Pirate Tavern is finished! Recruits are waiting inside.")
					.withStyle(ChatFormatting.GREEN));
			return;
		}
		player.sendSystemMessage(Component.literal("To finish the Pirate Tavern you still need:").withStyle(ChatFormatting.GOLD));
		for (String thing : result.missingThings()) {
			player.sendSystemMessage(Component.literal("  - " + thing).withStyle(ChatFormatting.YELLOW));
		}
		player.sendSystemMessage(Component.literal(com.onepiecemod.building.BuildingOutlines.GHOST_HINT).withStyle(ChatFormatting.GRAY));
		// See-through ghost blocks of everything that's missing (drawn by the building code, shared with the other buildings).
		com.onepiecemod.building.BuildingOutlines.show(player, com.onepiecemod.building.TavernPlan.INSTANCE, boardPos.immutable());
	}

	/** Prints the building plan, layer by layer. */
	public static void printPlan(ServerPlayer player) {
		player.sendSystemMessage(Component.literal("=== Pirate Tavern blueprint ===").withStyle(ChatFormatting.GOLD));
		String[] lines = {
				"1. Floor: a 5x5 square of any planks.",
				"2. Posts: a log in each corner of the floor, stacked 3 high.",
				"3. Roof: a 5x5 layer of planks, wooden slabs or wooden stairs on top of the posts.",
				"4. Inside: 2 Barrels, 1 Lantern and 1 Bed.",
				"5. The Recruitment Board goes on the floor in the very middle.",
				"Walls and a door are up to you. Click the ground with this blueprint to see where everything goes."
		};
		for (String line : lines) {
			player.sendSystemMessage(Component.literal(line).withStyle(ChatFormatting.YELLOW));
		}
	}

	// ---------- The outline shown with particles ----------

	private record Outline(ServerLevel level, BlockPos boardPos, int ticksLeft) {}

	private static final Map<UUID, Outline> OUTLINES = new HashMap<>();

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (OUTLINES.isEmpty() || server.getTickCount() % 10 != 0) {
				return;
			}
			for (UUID id : new ArrayList<>(OUTLINES.keySet())) {
				Outline outline = OUTLINES.get(id);
				if (outline.ticksLeft() <= 0 || server.getPlayerList().getPlayer(id) == null) {
					OUTLINES.remove(id);
					continue;
				}
				OUTLINES.put(id, new Outline(outline.level(), outline.boardPos(), outline.ticksLeft() - 10));
				Check result = check(outline.level(), outline.boardPos());
				if (result.complete()) {
					OUTLINES.remove(id);
					ServerPlayer player = server.getPlayerList().getPlayer(id);
					player.sendSystemMessage(Component.literal("The Pirate Tavern is finished! Right-click the Recruitment Board to meet the recruits.")
							.withStyle(ChatFormatting.GREEN));
					continue;
				}
				for (BlockPos pos : result.missingBlocks()) {
					outline.level().sendParticles(ParticleTypes.FLAME, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 1, 0.15, 0.15, 0.15, 0.0);
				}
				BlockPos board = outline.boardPos();
				if (!outline.level().getBlockState(board).is(CrewBlocks.RECRUITMENT_BOARD)) {
					outline.level().sendParticles(ParticleTypes.HAPPY_VILLAGER, board.getX() + 0.5, board.getY() + 0.5, board.getZ() + 0.5, 3, 0.2, 0.2, 0.2, 0.0);
				}
			}
		});
	}
}
