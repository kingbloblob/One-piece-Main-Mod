package com.onepiecemod.haki;

import java.util.List;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

import com.onepiecemod.OnePieceMod;

/**
 * Server -> one player: "these creatures are glowing for you" (Observation Haki sensing).
 * Only the player who senses them sees the outline; everyone else sees nothing.
 */
public record HakiSensePayload(List<Integer> entityIds) implements CustomPacketPayload {
	public static final Type<HakiSensePayload> TYPE = new Type<>(OnePieceMod.id("haki_sense"));
	public static final StreamCodec<ByteBuf, HakiSensePayload> CODEC = ByteBufCodecs.VAR_INT.apply(ByteBufCodecs.list(256))
			.map(HakiSensePayload::new, HakiSensePayload::entityIds);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
