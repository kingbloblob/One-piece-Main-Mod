package com.onepiecemod.shipcombat;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

import com.onepiecemod.OnePieceMod;

/** Player -> server: "Coup de Burst!" (gaon false) or "Gaon Cannon!" (gaon true). ShipSpecials checks the rest. */
public record ShipSpecialPayload(boolean gaon) implements CustomPacketPayload {
	public static final Type<ShipSpecialPayload> TYPE = new Type<>(OnePieceMod.id("ship_special"));
	public static final StreamCodec<ByteBuf, ShipSpecialPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.BOOL, ShipSpecialPayload::gaon,
			ShipSpecialPayload::new
	);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
