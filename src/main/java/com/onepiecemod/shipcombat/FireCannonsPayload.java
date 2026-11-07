package com.onepiecemod.shipcombat;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

import com.onepiecemod.OnePieceMod;

/** Player -> server: "I pressed the fire-cannons key". The server checks the ship, the aim and the ammo. */
public record FireCannonsPayload() implements CustomPacketPayload {
	public static final Type<FireCannonsPayload> TYPE = new Type<>(OnePieceMod.id("fire_cannons"));
	public static final StreamCodec<ByteBuf, FireCannonsPayload> CODEC = StreamCodec.unit(new FireCannonsPayload());

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
