package com.onepiecemod.weather;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;

/**
 * Sends the list of sea events to each player's game, so their ship feels the storm or whirlpool
 * at the same time the server does. The game keeps its copy in CLIENT_EVENTS.
 */
public class SeaEventSync {
	/** The events this player's game knows about. Empty on a server. Filled by WeatherClient. */
	public static volatile List<SeaEvent> CLIENT_EVENTS = List.of();

	public record SeaEventsPayload(List<SeaEvent> events) implements CustomPacketPayload {
		public static final Type<SeaEventsPayload> TYPE = new Type<>(OnePieceMod.id("sea_events"));
		public static final StreamCodec<FriendlyByteBuf, SeaEventsPayload> CODEC = StreamCodec.of(
				(buf, payload) -> {
					buf.writeVarInt(payload.events.size());
					for (SeaEvent event : payload.events) {
						event.write(buf);
					}
				},
				buf -> {
					int count = buf.readVarInt();
					List<SeaEvent> events = new ArrayList<>(count);
					for (int i = 0; i < count; i++) {
						events.add(SeaEvent.read(buf));
					}
					return new SeaEventsPayload(events);
				});

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	public static void initialize() {
		PayloadTypeRegistry.clientboundPlay().register(SeaEventsPayload.TYPE, SeaEventsPayload.CODEC);
	}

	public static void send(ServerPlayer player, List<SeaEvent> events) {
		if (ServerPlayNetworking.canSend(player, SeaEventsPayload.TYPE)) {
			ServerPlayNetworking.send(player, new SeaEventsPayload(List.copyOf(events)));
		}
	}
}
