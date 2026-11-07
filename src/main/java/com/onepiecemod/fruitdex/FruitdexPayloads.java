package com.onepiecemod.fruitdex;

import java.util.List;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;

import com.onepiecemod.OnePieceMod;

/**
 * Messages from the server to a player's game for the encyclopedia and the first-bite cutscene.
 */
public class FruitdexPayloads {
	/** Server -> player: "open the encyclopedia". Carries what the player has found and eaten. */
	public record Open(List<String> discovered, List<String> sighted, String eaten, boolean awakened, int mastery) implements CustomPacketPayload {
		public static final Type<Open> TYPE = new Type<>(OnePieceMod.id("open_fruitdex"));
		public static final StreamCodec<ByteBuf, Open> CODEC = StreamCodec.composite(
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), Open::discovered,
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), Open::sighted,
				ByteBufCodecs.STRING_UTF8, Open::eaten,
				ByteBufCodecs.BOOL, Open::awakened,
				ByteBufCodecs.VAR_INT, Open::mastery,
				Open::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Server -> player: "you just ate this fruit, play the cutscene". */
	public record FirstBite(String fruitId) implements CustomPacketPayload {
		public static final Type<FirstBite> TYPE = new Type<>(OnePieceMod.id("first_bite"));
		public static final StreamCodec<ByteBuf, FirstBite> CODEC = StreamCodec.composite(
				ByteBufCodecs.STRING_UTF8, FirstBite::fruitId,
				FirstBite::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	static void initialize() {
		PayloadTypeRegistry.clientboundPlay().register(Open.TYPE, Open.CODEC);
		PayloadTypeRegistry.clientboundPlay().register(FirstBite.TYPE, FirstBite.CODEC);
	}
}
