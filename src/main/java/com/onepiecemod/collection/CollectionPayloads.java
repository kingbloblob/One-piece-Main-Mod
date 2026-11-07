package com.onepiecemod.collection;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;

import com.onepiecemod.OnePieceMod;

/** Server -> player: "open the Collector's Log", with everything the player has collected. */
public class CollectionPayloads {
	/**
	 * lists: the saved lists (see CollectionProgress) plus "fish", "food" (item ids) and "goals" (finished island goals as
	 * "place:index"). counters: the saved counters.
	 */
	public record Open(Map<String, List<String>> lists, Map<String, Integer> counters) implements CustomPacketPayload {
		public static final Type<Open> TYPE = new Type<>(OnePieceMod.id("open_collections"));
		public static final StreamCodec<ByteBuf, Open> CODEC = StreamCodec.composite(
				ByteBufCodecs.map(HashMap::new, ByteBufCodecs.STRING_UTF8, ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list())), Open::lists,
				ByteBufCodecs.map(HashMap::new, ByteBufCodecs.STRING_UTF8, ByteBufCodecs.VAR_INT), Open::counters,
				Open::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	static void initialize() {
		PayloadTypeRegistry.clientboundPlay().register(Open.TYPE, Open.CODEC);
	}
}
