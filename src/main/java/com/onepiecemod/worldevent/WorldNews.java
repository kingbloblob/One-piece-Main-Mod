package com.onepiecemod.worldevent;

import java.util.ArrayList;
import java.util.List;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.sound.ModSounds;

/**
 * Headlines from world events (Buster Calls, fleets, the Reverie, Emperors...). Each one is told to every player
 * by News Coo and kept in a short list on the Overworld, newest last, so a newspaper can print them later.
 */
public class WorldNews {
	private static final int KEEP = 40;

	/** Saved on the Overworld: "day|headline", oldest first. */
	public static final AttachmentType<List<String>> HEADLINES = AttachmentRegistry.create(
			OnePieceMod.id("world_news"),
			builder -> builder.persistent(Codec.STRING.listOf())
	);

	/** Tells everyone and remembers the headline. */
	public static void report(MinecraftServer server, String headline, ChatFormatting color) {
		Component message = Component.literal("[News Coo] " + headline).withStyle(color);
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			player.sendSystemMessage(message);
			ModSounds.play(player, ModSounds.NEWS_COO, 0.6f);
		}
		remember(server, headline);
	}

	/** Remembers a headline without announcing it. */
	public static void remember(MinecraftServer server, String headline) {
		List<String> list = new ArrayList<>(server.overworld().getAttachedOrElse(HEADLINES, List.of()));
		long day = server.overworld().getGameTime() / 24000L + 1;
		list.add(day + "|" + headline);
		while (list.size() > KEEP) {
			list.remove(0);
		}
		server.overworld().setAttached(HEADLINES, list);
	}

	/** The latest headlines, newest first, without the day. */
	public static List<String> recent(MinecraftServer server, int count) {
		List<String> list = server.overworld().getAttachedOrElse(HEADLINES, List.of());
		List<String> out = new ArrayList<>();
		for (int i = list.size() - 1; i >= 0 && out.size() < count; i--) {
			String entry = list.get(i);
			int bar = entry.indexOf('|');
			out.add(bar >= 0 ? entry.substring(bar + 1) : entry);
		}
		return out;
	}

	/** A Den Den Mushi call to one player: a ring, then the line in chat. */
	public static void call(ServerPlayer player, String caller, String line, ChatFormatting color) {
		ModSounds.play(player, ModSounds.DEN_DEN_MUSHI_CALL, 0.8f);
		player.sendSystemMessage(Component.literal("[Den Den Mushi] " + caller + ": ").withStyle(ChatFormatting.DARK_AQUA)
				.append(Component.literal(line).withStyle(color)));
	}
}
