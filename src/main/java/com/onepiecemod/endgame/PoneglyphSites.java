package com.onepiecemod.endgame;

import java.util.ArrayList;
import java.util.List;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.resource.Resources;

/**
 * Makes sure every structure the story needs a Poneglyph in really has one. Some rebuilt landmarks lost theirs
 * (Hachinosu's Road Poneglyph is needed for Laugh Tale). The first time a player walks into one of these
 * structures, a Poneglyph is looked for nearby; if there is none, one rises out of the ground a few blocks away.
 * Each structure gets this once (remembered on the Overworld), so it never doubles up.
 */
public class PoneglyphSites {
	/** Structures that must have a Poneglyph. */
	private static final List<String> NEEDED = List.of("hachinosu", "shandora", "ohara_library", "mokomo_dukedom",
			"whole_cake_chateau", "onigashima", "alubarna_palace", "ryugu_palace", "void_century_ruins", "laugh_tale",
			"elbaph_tree");
	private static final int CHECK_EVERY = 100;
	private static final int LOOK = 24;

	/** "structure@chunkX,chunkZ" for each structure already checked. */
	private static final AttachmentType<List<String>> CHECKED = AttachmentRegistry.create(
			OnePieceMod.id("poneglyph_sites"),
			builder -> builder.persistent(Codec.STRING.listOf())
	);

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % CHECK_EVERY != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				if (!player.isSpectator()) {
					check(server, player);
				}
			}
		});
	}

	private static void check(MinecraftServer server, ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		BlockPos pos = player.blockPosition();
		for (String id : NEEDED) {
			ResourceKey<Structure> key = ResourceKey.create(Registries.STRUCTURE, OnePieceMod.id(id));
			StructureStart start = level.structureManager().getStructureWithPieceAt(pos, holder -> holder.is(key));
			if (!start.isValid()) {
				continue;
			}
			String site = id + "@" + start.getChunkPos().x() + "," + start.getChunkPos().z();
			List<String> checked = server.overworld().getAttachedOrElse(CHECKED, List.of());
			if (checked.contains(site)) {
				return;
			}
			List<String> list = new ArrayList<>(checked);
			list.add(site);
			server.overworld().setAttached(CHECKED, list);
			if (!hasPoneglyph(level, start) && raise(level, player)) {
				player.sendSystemMessage(Component.literal("The ground rumbles. A great black stone cube pushes up out of the earth nearby: a Poneglyph!")
						.withStyle(ChatFormatting.GOLD));
			}
			return;
		}
	}

	/** Looks inside the structure's bounding box, in the middle, for a Poneglyph. */
	private static boolean hasPoneglyph(ServerLevel level, StructureStart start) {
		var box = start.getBoundingBox();
		BlockPos center = box.getCenter();
		int halfX = Math.min(box.getXSpan() / 2, 64);
		int halfZ = Math.min(box.getZSpan() / 2, 64);
		for (BlockPos at : BlockPos.betweenClosed(center.getX() - halfX, box.minY(), center.getZ() - halfZ,
				center.getX() + halfX, box.maxY(), center.getZ() + halfZ)) {
			if (level.isLoaded(at) && level.getBlockState(at).is(Resources.PONEGLYPH)) {
				return true;
			}
		}
		return false;
	}

	/** Puts a two-block Poneglyph on open ground a few blocks from the player. */
	private static boolean raise(ServerLevel level, ServerPlayer player) {
		BlockPos base = player.blockPosition();
		for (int distance = 3; distance <= 6; distance++) {
			for (Direction direction : Direction.Plane.HORIZONTAL) {
				for (int dy = -2; dy <= 2; dy++) {
					BlockPos spot = base.relative(direction, distance).above(dy);
					if (fits(level, spot)) {
						level.setBlockAndUpdate(spot, Resources.PONEGLYPH.defaultBlockState());
						level.setBlockAndUpdate(spot.above(), Resources.PONEGLYPH.defaultBlockState());
						return true;
					}
				}
			}
		}
		return false;
	}

	private static boolean fits(ServerLevel level, BlockPos spot) {
		return level.getBlockState(spot).canBeReplaced() && level.getFluidState(spot).isEmpty()
				&& level.getBlockState(spot.above()).canBeReplaced() && level.getFluidState(spot.above()).isEmpty()
				&& level.getBlockState(spot.above(2)).isAir()
				&& level.getBlockState(spot.below()).isFaceSturdy(level, spot.below(), Direction.UP);
	}
}
