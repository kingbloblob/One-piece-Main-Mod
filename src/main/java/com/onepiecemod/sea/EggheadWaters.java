package com.onepiecemod.sea;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.character.Locations;
import com.onepiecemod.story.StoryData;
import com.onepiecemod.story.StoryEvents;
import com.onepiecemod.story.StoryProgress;

/**
 * The sea around Egghead is guarded, like in the show: as the Sunny reaches Egghead, Vegapunk's Mecha-Shark attacks it,
 * and Lilith's Sea Beast Weapons patrol the water.
 * In the story chapter "egghead" you have to beat both, in that order, before you can reach Labophase: when you sail
 * within 400 blocks of Egghead, the next one comes for you. Beating one sets the story flag event:egghead_<boss id>.
 */
public final class EggheadWaters {
	private static final String CHAPTER = "egghead";
	private static final String PLACE = "egghead_lab";
	private static final String[] ORDER = {"mecha_shark", "sea_beast_weapon"};
	private static final int RANGE = 400;

	/** Where each player's nearest Egghead is (found in the background), and when to look again. */
	private static final Map<UUID, BlockPos> EGGHEAD = new HashMap<>();
	private static final Map<UUID, Long> NEXT_SEARCH = new HashMap<>();
	/** No new guard before this game time (after one appears, or right after you beat the first). */
	private static final Map<UUID, Long> NEXT_SPAWN = new HashMap<>();

	private EggheadWaters() {
	}

	public static String flag(String bossId) {
		return "event:egghead_" + bossId;
	}

	static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 100 != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				tick(player);
			}
		});
	}

	/** The Egghead guard this player has to beat next for the story, or null. */
	static SeaBosses.Boss next(ServerPlayer player) {
		StoryProgress progress = StoryProgress.of(player);
		StoryData.Chapter chapter = progress == null ? null : StoryData.chapter(progress.chapter());
		if (chapter == null || !CHAPTER.equals(chapter.id)) {
			return null;
		}
		for (String id : ORDER) {
			if (!progress.hasFlag(flag(id))) {
				return SeaBosses.get(id);
			}
		}
		return null;
	}

	private static void tick(ServerPlayer player) {
		if (!player.isAlive() || player.isCreative() || player.isSpectator() || player.level().dimension() != Level.OVERWORLD) {
			return;
		}
		SeaBosses.Boss boss = next(player);
		if (boss == null) {
			return;
		}
		ServerLevel level = (ServerLevel) player.level();
		long now = level.getGameTime();
		UUID id = player.getUUID();
		BlockPos egghead = EGGHEAD.get(id);
		if ((egghead == null || distance(player, egghead) > RANGE * 2) && now >= NEXT_SEARCH.getOrDefault(id, 0L)) {
			NEXT_SEARCH.put(id, now + 1200);
			Locations.findLater(player, PLACE, RANGE + 200, (found, result) -> result.ifPresent(f -> EGGHEAD.put(found.getUUID(), f.pos())));
		}
		if (egghead == null || distance(player, egghead) > RANGE || !atSea(player, level) || now < NEXT_SPAWN.getOrDefault(id, 0L)) {
			return;
		}
		if (!level.getEntitiesOfClass(SeaKingEntity.class, player.getBoundingBox().inflate(160), SeaKingEntity::isSeaBoss).isEmpty()) {
			return;
		}
		// It surfaces about 28 blocks away, in front of you if the water there is deep enough.
		for (int i = 0; i < 8; i++) {
			Vec3 dir = Vec3.directionFromRotation(0.0f, player.getYRot() + i * 45.0f);
			BlockPos spot = BlockPos.containing(player.getX() + dir.x * 28, level.getSeaLevel() - 5, player.getZ() + dir.z * 28);
			if (SeaKingSpawner.isDeepWater(level, spot)) {
				if (SeaBosses.spawn(level, boss, Vec3.atBottomCenterOf(spot), player) != null) {
					NEXT_SPAWN.put(id, now + 1200);
					if (boss.id().equals(ORDER[0])) {
						player.sendSystemMessage(Component.literal("Egghead's winter cloud is just ahead... and something made of steel is hunting your ship.")
								.withStyle(ChatFormatting.AQUA, ChatFormatting.ITALIC));
					}
				}
				return;
			}
		}
	}

	/** Called by SeaBosses for everyone who helped beat a sea boss. */
	static void onBeaten(ServerPlayer player, SeaBosses.Boss boss) {
		if (boss.sea() != null) {
			return;
		}
		StoryProgress progress = StoryProgress.of(player);
		if (progress == null || progress.hasFlag(flag(boss.id()))) {
			return;
		}
		boolean storyNow = next(player) != null;
		StoryEvents.setFlag(player, flag(boss.id()));
		if (!storyNow) {
			return;
		}
		if (next(player) != null) {
			NEXT_SPAWN.put(player.getUUID(), player.level().getGameTime() + 400);
			player.sendSystemMessage(Component.literal("The Mecha-Shark sinks in pieces... but something much bigger is moving under the waves.")
					.withStyle(ChatFormatting.AQUA, ChatFormatting.ITALIC));
		} else {
			player.sendSystemMessage(Component.literal("Egghead's guards are beaten. The way to Labophase is open.")
					.withStyle(ChatFormatting.AQUA, ChatFormatting.ITALIC));
		}
	}

	private static double distance(ServerPlayer player, BlockPos pos) {
		double dx = player.getX() - pos.getX();
		double dz = player.getZ() - pos.getZ();
		return Math.sqrt(dx * dx + dz * dz);
	}

	/** On the water: swimming, on a ship or boat, or standing just above the sea. */
	private static boolean atSea(ServerPlayer player, ServerLevel level) {
		if (player.isInWater() || player.isPassenger() || com.onepiecemod.ship.ShipEntity.aboard(player) != null) {
			return true;
		}
		BlockPos pos = player.blockPosition();
		for (int down = 0; down <= 4; down++) {
			if (level.getFluidState(pos.below(down)).is(FluidTags.WATER)) {
				return true;
			}
		}
		return false;
	}
}
