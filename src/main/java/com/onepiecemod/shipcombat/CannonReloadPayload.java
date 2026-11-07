package com.onepiecemod.shipcombat;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

import com.onepiecemod.OnePieceMod;

/** Server -> crew: "this ship's cannons just fired and need this many ticks to reload". Drives the cannons-ready light. */
public record CannonReloadPayload(int shipId, int ticks) implements CustomPacketPayload {
	public static final Type<CannonReloadPayload> TYPE = new Type<>(OnePieceMod.id("cannon_reload"));
	public static final StreamCodec<ByteBuf, CannonReloadPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, CannonReloadPayload::shipId,
			ByteBufCodecs.VAR_INT, CannonReloadPayload::ticks,
			CannonReloadPayload::new
	);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
