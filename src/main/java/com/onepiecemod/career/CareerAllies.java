package com.onepiecemod.career;

import java.util.List;

import com.onepiecemod.sound.ModSounds;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

/**
 * "Requesting backup!": calls a few Marine or Revolutionary soldiers to fight beside you for 3 minutes.
 * More soldiers at higher ranks (see Career.Rank.backup), and a shorter wait before the next call.
 */
final class CareerAllies {
	private CareerAllies() {
	}

	/** Ticks before backup can be called again: 8 minutes, 30 seconds less per rank, never under 3 minutes. */
	static long cooldown(int rank) {
		return Math.max(20L * 180, 20L * (480 - 30L * rank));
	}

	static void call(ServerPlayer player) {
		CareerData data = Careers.get(player);
		Career career = data.path();
		if (career == Career.PIRATE) {
			player.sendSystemMessage(Component.literal("Nobody answers. Only Marines and Revolutionaries can call for backup.").withStyle(ChatFormatting.GRAY));
			return;
		}
		ServerLevel level = (ServerLevel) player.level();
		long now = level.getGameTime();
		if (now < data.backupReadyAt()) {
			player.sendSystemMessage(Component.literal("Backup isn't ready yet: " + (data.backupReadyAt() - now) / 20 + " seconds.").withStyle(ChatFormatting.GRAY));
			return;
		}
		List<CareerAllyEntity> here = level.getEntitiesOfClass(CareerAllyEntity.class, player.getBoundingBox().inflate(64.0),
				ally -> player.getUUID().equals(ally.getOwnerId()));
		if (!here.isEmpty()) {
			player.sendSystemMessage(Component.literal("Your backup is still with you.").withStyle(ChatFormatting.GRAY));
			return;
		}

		Career.Rank rank = data.currentRank();
		int spawned = 0;
		for (String kit : CareerSquads.backup(career, data.rank(), rank.backup())) {
			CareerAllyEntity ally = CareerSquads.ally(level, player, career, kit, data.rank());
			if (ally == null) {
				continue;
			}
			BlockPos pos = CareerSquads.spotNear(level, player.blockPosition(), 2, 5);
			if (pos == null) {
				pos = player.blockPosition();
			}
			ally.snapTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, player.getYRot(), 0f);
			level.addFreshEntity(ally);
			spawned++;
		}
		if (spawned == 0) {
			return;
		}
		Careers.set(player, data.withBackupReadyAt(now + cooldown(data.rank())));
		ModSounds.play(player, ModSounds.DEN_DEN_MUSHI_CALL);
		player.sendSystemMessage(Component.literal(career == Career.MARINE
				? "Purupuru... \"" + rank.name() + ", backup is here! " + spawned + (spawned == 1 ? " Marine" : " Marines") + " at your side.\""
				: "Purupuru... \"Comrade, we're with you!\" " + spawned + (spawned == 1 ? " Revolutionary joins" : " Revolutionaries join") + " the fight.")
				.withStyle(career.color));
		player.sendSystemMessage(Component.literal("They fight beside you for 3 minutes.").withStyle(ChatFormatting.GRAY));
	}
}
