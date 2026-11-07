package com.onepiecemod.news;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.sound.ModSounds;

/**
 * The News Coo: a seagull in a hat that drops the newspaper every morning.
 * Out in the open the paper falls from the sky in front of you; indoors it goes straight into your bag.
 * /news off stops the deliveries, /news on starts them again.
 */
public class NewsCoo {
	/** The last day this player got a paper (-1 = never). */
	public static final AttachmentType<Long> LAST_PAPER = AttachmentRegistry.create(
			OnePieceMod.id("news_last_paper"),
			builder -> builder.persistent(Codec.LONG).copyOnDeath()
	);

	/** True if the player said /news off. */
	public static final AttachmentType<Boolean> PAPER_OFF = AttachmentRegistry.create(
			OnePieceMod.id("news_off"),
			builder -> builder.persistent(Codec.BOOL).copyOnDeath()
	);

	/** The paper comes after sunrise (time 0 is sunrise, 1000 is early morning). */
	private static final long MORNING = 1000L;

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 40 != 0) {
				return;
			}
			long time = server.overworld().getDefaultClockTime();
			if (time % 24000L < MORNING) {
				return;
			}
			long day = time / 24000L;
			for (ServerPlayer player : server.overworld().players()) {
				if (!player.isAlive() || player.isSpectator() || player.getAttachedOrElse(PAPER_OFF, false)) {
					continue;
				}
				if (player.getAttachedOrElse(LAST_PAPER, -1L) < day) {
					deliver(player);
				}
			}
		});
	}

	/** Brings the player today's paper, with the news since their last one. */
	public static void deliver(ServerPlayer player) {
		MinecraftServer server = player.level().getServer();
		long day = NewsLog.day(server);
		long last = player.getAttachedOrElse(LAST_PAPER, -1L);
		// Missed a few days? The paper only covers the last three.
		long since = Math.max(last + 1, day - 3);
		ItemStack paper = Newspaper.print(player, since);
		player.setAttached(LAST_PAPER, day);

		ServerLevel level = (ServerLevel) player.level();
		ModSounds.play(player, ModSounds.NEWS_COO);
		if (level.canSeeSky(player.blockPosition().above())) {
			// Drop it from the sky just in front of the player, with a puff of feathers.
			double x = player.getX() + player.getLookAngle().x * 1.5;
			double z = player.getZ() + player.getLookAngle().z * 1.5;
			double y = player.getY() + 6.0;
			ItemEntity drop = new ItemEntity(level, x, y, z, paper, 0.0, -0.1, 0.0);
			drop.setPickUpDelay(10);
			drop.setTarget(player.getUUID());
			level.addFreshEntity(drop);
			level.sendParticles(ParticleTypes.CLOUD, x, y + 0.5, z, 12, 0.4, 0.2, 0.4, 0.02);
			level.playSound(null, x, y, z, net.minecraft.sounds.SoundEvents.PARROT_FLY, SoundSource.NEUTRAL, 1.0f, 1.2f);
			player.sendSystemMessage(Component.literal("[News Coo] Kuu! A News Coo flies overhead and drops today's paper.")
					.withStyle(ChatFormatting.GOLD));
		} else {
			if (!player.getInventory().add(paper)) {
				player.drop(paper, false, net.minecraft.util.Prediction.SERVER_ONLY);
			}
			player.sendSystemMessage(Component.literal("[News Coo] Kuu! A News Coo pecks at the window and leaves today's paper with you.")
					.withStyle(ChatFormatting.GOLD));
		}
	}
}
