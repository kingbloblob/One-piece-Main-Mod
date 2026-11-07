package com.onepiecemod.vegapunk;

import java.util.Map;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;

/** Messages between the server and players' games for cyborg upgrades. */
public class VegapunkPayloads {
	/** Server -> player: your upgrade tiers and fuel. */
	public record Sync(Map<String, Integer> tiers, int fuel, int tank) implements CustomPacketPayload {
		public static final Type<Sync> TYPE = new Type<>(OnePieceMod.id("cyborg_sync"));
		public static final StreamCodec<ByteBuf, Sync> CODEC = StreamCodec.composite(
				ByteBufCodecs.map(java.util.HashMap::new, ByteBufCodecs.STRING_UTF8, ByteBufCodecs.VAR_INT), Sync::tiers,
				ByteBufCodecs.VAR_INT, Sync::fuel,
				ByteBufCodecs.VAR_INT, Sync::tank,
				Sync::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Player -> server: the C key (sneaking = Coup de Vent, else Radical Beam). */
	public record Use(boolean sneaking) implements CustomPacketPayload {
		public static final Type<Use> TYPE = new Type<>(OnePieceMod.id("cyborg_use"));
		public static final StreamCodec<ByteBuf, Use> CODEC = ByteBufCodecs.BOOL.map(Use::new, Use::sneaking);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	static void initialize() {
		PayloadTypeRegistry.clientboundPlay().register(Sync.TYPE, Sync.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(Use.TYPE, Use.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(Use.TYPE, (payload, context) -> Cyborg.use(context.player(), payload.sneaking()));
	}
}
