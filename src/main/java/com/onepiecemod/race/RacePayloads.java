package com.onepiecemod.race;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;

/**
 * Messages between the server and players' games for picking a race.
 */
public class RacePayloads {
	/** Server -> player: "you have no race yet, show the race picker". */
	public record OpenPicker() implements CustomPacketPayload {
		public static final OpenPicker INSTANCE = new OpenPicker();
		public static final Type<OpenPicker> TYPE = new Type<>(OnePieceMod.id("open_race_picker"));
		public static final StreamCodec<ByteBuf, OpenPicker> CODEC = StreamCodec.unit(INSTANCE);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Player -> server: "I pick this race". */
	public record Choose(String raceId) implements CustomPacketPayload {
		public static final Type<Choose> TYPE = new Type<>(OnePieceMod.id("choose_race"));
		public static final StreamCodec<ByteBuf, Choose> CODEC = StreamCodec.composite(
				ByteBufCodecs.STRING_UTF8, Choose::raceId,
				Choose::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	public static void initialize() {
		PayloadTypeRegistry.clientboundPlay().register(OpenPicker.TYPE, OpenPicker.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(Choose.TYPE, Choose.CODEC);

		ServerPlayNetworking.registerGlobalReceiver(Choose.TYPE, (payload, context) -> {
			Race race = Race.byId(payload.raceId());
			// You only get to pick once. Operators can reset it with /race reset.
			if (race != null && RaceAttachments.get(context.player()) == null) {
				RacePerks.become(context.player(), race);
			}
		});

		// Show the picker the first time someone joins (and every join until they pick).
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> openPickerIfNeeded(handler.player));
	}

	/** Asks the player's game to show the race picker, if they have no race yet. */
	public static void openPickerIfNeeded(ServerPlayer player) {
		// Players without the mod installed can't show the screen, so don't send it to them.
		if (RaceAttachments.get(player) == null && ServerPlayNetworking.canSend(player, OpenPicker.TYPE)) {
			ServerPlayNetworking.send(player, OpenPicker.INSTANCE);
		}
	}
}
