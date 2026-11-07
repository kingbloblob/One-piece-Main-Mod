package com.onepiecemod.building;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

/**
 * Shows players what a building still needs: a list in chat, and a see-through "ghost" of every
 * missing block, drawn right where it goes (like a schematic). As blocks get placed their ghosts
 * disappear. The ghosts stay for 10 minutes, until the building is finished, or until the player
 * sneaks and uses the blueprint in the air.
 */
public class BuildingOutlines {
	private static final int SHOW_TICKS = 12000; // 10 minutes.
	private static final int MAX_GHOSTS = 1024;

	private record Outline(ServerLevel level, GhostPlan plan, BlockPos corePos, int ticksLeft, List<GhostPlan.Ghost> sent) {}

	private static final Map<UUID, Outline> OUTLINES = new HashMap<>();

	/** Lists what's missing in chat and shows the ghost blocks. */
	public static void explain(ServerPlayer player, GhostPlan plan, BlockPos corePos) {
		GhostPlan.Check result = plan.check((ServerLevel) player.level(), corePos);
		if (result.complete()) {
			player.sendSystemMessage(Component.literal("This " + plan.name() + " is finished! " + plan.purpose())
					.withStyle(ChatFormatting.GREEN));
			return;
		}
		player.sendSystemMessage(Component.literal("To finish the " + plan.name() + " you still need:").withStyle(ChatFormatting.GOLD));
		for (String thing : result.missingThings()) {
			player.sendSystemMessage(Component.literal("  - " + thing).withStyle(ChatFormatting.YELLOW));
		}
		player.sendSystemMessage(Component.literal(GHOST_HINT).withStyle(ChatFormatting.GRAY));
		show(player, plan, corePos);
	}

	/** One line explaining the ghost blocks, for chat. */
	public static final String GHOST_HINT = "See-through ghost blocks show where each missing block goes. "
			+ "Furniture can go anywhere inside. Sneak and use the blueprint in the air to hide the ghosts.";

	/** Shows (or refreshes) the ghost blocks without printing anything. */
	public static void show(ServerPlayer player, GhostPlan plan, BlockPos corePos) {
		GhostPlan.Check result = plan.check((ServerLevel) player.level(), corePos);
		List<GhostPlan.Ghost> ghosts = limit(result.ghosts());
		ServerPlayNetworking.send(player, GhostPayload.of(ghosts));
		OUTLINES.put(player.getUUID(), new Outline((ServerLevel) player.level(), plan, corePos.immutable(), SHOW_TICKS, ghosts));
	}

	/** Hides this player's ghost blocks. */
	public static void hide(ServerPlayer player) {
		if (OUTLINES.remove(player.getUUID()) != null) {
			ServerPlayNetworking.send(player, GhostPayload.hide());
		}
	}

	/** Prints the building plan, step by step. */
	public static void printPlan(ServerPlayer player, Multiblock building) {
		player.sendSystemMessage(Component.literal("=== " + building.name() + " blueprint ===").withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal(building.purpose()).withStyle(ChatFormatting.AQUA));
		int step = 1;
		for (String line : building.plan()) {
			player.sendSystemMessage(Component.literal(step++ + ". " + line).withStyle(ChatFormatting.YELLOW));
		}
		player.sendSystemMessage(Component.literal("Click the ground with this blueprint to see ghost blocks where everything goes.")
				.withStyle(ChatFormatting.GRAY));
	}

	private static List<GhostPlan.Ghost> limit(List<GhostPlan.Ghost> ghosts) {
		return ghosts.size() <= MAX_GHOSTS ? ghosts : ghosts.subList(0, MAX_GHOSTS);
	}

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (OUTLINES.isEmpty() || server.getTickCount() % 10 != 0) {
				return;
			}
			for (UUID id : new ArrayList<>(OUTLINES.keySet())) {
				Outline outline = OUTLINES.get(id);
				ServerPlayer player = server.getPlayerList().getPlayer(id);
				if (player == null) {
					OUTLINES.remove(id);
					continue;
				}
				if (outline.ticksLeft() <= 0 || player.level() != outline.level()) {
					hide(player);
					continue;
				}
				GhostPlan.Check result = outline.plan().check(outline.level(), outline.corePos());
				if (result.complete()) {
					hide(player);
					player.sendSystemMessage(Component.literal("The " + outline.plan().name() + " is finished! " + outline.plan().purpose())
							.withStyle(ChatFormatting.GREEN));
					continue;
				}
				List<GhostPlan.Ghost> ghosts = limit(result.ghosts());
				if (!ghosts.equals(outline.sent())) {
					ServerPlayNetworking.send(player, GhostPayload.of(ghosts)); // Some blocks were placed (or broken).
				}
				OUTLINES.put(id, new Outline(outline.level(), outline.plan(), outline.corePos(), outline.ticksLeft() - 10, ghosts));
			}
		});
	}
}
