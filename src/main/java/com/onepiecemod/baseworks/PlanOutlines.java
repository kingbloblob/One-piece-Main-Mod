package com.onepiecemod.baseworks;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.building.GhostPayload;
import com.onepiecemod.building.GhostPlan;
import com.onepiecemod.building.Parts;
import com.onepiecemod.character.CharacterFeature;

/**
 * The ghost blocks of a plan book page: shown where the player clicked, updated as blocks go in, gone after
 * 10 minutes or when it's finished. The first time a player finishes each page they get a few Berries and some XP.
 * (Same see-through ghosts as the building blueprints, see the building package's BuildingOutlines.)
 */
public final class PlanOutlines {
	private static final int SHOW_TICKS = 20 * 60 * 10;
	private static final int MAX_GHOSTS = 1024;

	/** Plan pages each player has finished at least once (for the first-time reward). */
	public static final AttachmentType<List<String>> PLANS_BUILT = AttachmentRegistry.create(
			OnePieceMod.id("plans_built"),
			builder -> builder.persistent(Codec.STRING.listOf()).copyOnDeath());

	private record Outline(ServerLevel level, LayoutPlan.Placed placed, int ticksLeft, List<GhostPlan.Ghost> sent) {}

	private static final Map<UUID, Outline> OUTLINES = new HashMap<>();

	private PlanOutlines() {
	}

	static void show(ServerPlayer player, LayoutPlan.Placed placed) {
		ServerLevel level = (ServerLevel) player.level();
		GhostPlan.Check check = placed.check(level, placed.origin());
		if (check.complete()) {
			player.sendSystemMessage(Component.literal("This " + placed.name() + " is already built. " + placed.purpose())
					.withStyle(ChatFormatting.GREEN));
			finished(player, placed);
			return;
		}
		player.sendSystemMessage(Component.literal(placed.name() + " laid out. Still needed:").withStyle(ChatFormatting.GOLD));
		for (String line : check.missingThings()) {
			player.sendSystemMessage(Component.literal("  - " + line).withStyle(ChatFormatting.YELLOW));
		}
		player.sendSystemMessage(Component.literal("Ghost blocks show where each piece goes. Sneak and click a block with the book to put them away.")
				.withStyle(ChatFormatting.GRAY));
		List<GhostPlan.Ghost> ghosts = limit(check.ghosts());
		ServerPlayNetworking.send(player, GhostPayload.of(ghosts));
		OUTLINES.put(player.getUUID(), new Outline(level, placed, SHOW_TICKS, ghosts));
	}

	public static void hide(ServerPlayer player, boolean tell) {
		if (OUTLINES.remove(player.getUUID()) != null) {
			ServerPlayNetworking.send(player, GhostPayload.hide());
			if (tell) {
				player.sendSystemMessage(Component.literal("Plan ghosts put away.").withStyle(ChatFormatting.GRAY));
			}
		}
	}

	/** Sends this player's plan ghosts again (another tool drew its own ghosts over them for a while). */
	public static boolean resend(ServerPlayer player) {
		Outline outline = OUTLINES.get(player.getUUID());
		if (outline == null) {
			return false;
		}
		ServerPlayNetworking.send(player, GhostPayload.of(outline.sent()));
		return true;
	}

	private static List<GhostPlan.Ghost> limit(List<GhostPlan.Ghost> ghosts) {
		return ghosts.size() <= MAX_GHOSTS ? ghosts : ghosts.subList(0, MAX_GHOSTS);
	}

	static void tick(MinecraftServer server) {
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
				hide(player, false);
				continue;
			}
			GhostPlan.Check check = outline.placed().check(outline.level(), outline.placed().origin());
			if (check.complete()) {
				hide(player, false);
				player.sendSystemMessage(Component.literal("The " + outline.placed().name() + " is finished! " + outline.placed().purpose())
						.withStyle(ChatFormatting.GREEN));
				outline.level().playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.6f, 1.2f);
				finished(player, outline.placed());
				continue;
			}
			List<GhostPlan.Ghost> ghosts = limit(check.ghosts());
			if (!ghosts.equals(outline.sent()) && !com.onepiecemod.settlement.Settlements.drawingFor(player)) {
				ServerPlayNetworking.send(player, GhostPayload.of(ghosts));
			}
			OUTLINES.put(id, new Outline(outline.level(), outline.placed(), outline.ticksLeft() - 10, ghosts));
		}
	}

	/** First time this player finishes this page: a small reward. */
	private static void finished(ServerPlayer player, LayoutPlan.Placed placed) {
		List<String> built = player.getAttachedOrElse(PLANS_BUILT, List.of());
		if (built.contains(placed.plan().id)) {
			return;
		}
		List<String> list = new ArrayList<>(built);
		list.add(placed.plan().id);
		player.setAttached(PLANS_BUILT, list);
		int berries = 5 + Math.min(20, placed.plan().materials().values().stream().mapToInt(Integer::intValue).sum() / 8);
		Parts.give(player, new ItemStack(CharacterFeature.BERRY, berries));
		player.giveExperiencePoints(20);
		player.sendSystemMessage(Component.literal("First time building a " + placed.name() + ": +" + berries + " Berries. ("
				+ list.size() + " of " + (PlanBooks.DECK.size() + PlanBooks.BASE.size()) + " plans built)").withStyle(ChatFormatting.GOLD));
	}

	/** How many plan pages this player has built, for the Builder's Ledger. */
	public static int builtCount(ServerPlayer player) {
		return player.getAttachedOrElse(PLANS_BUILT, List.of()).size();
	}
}
