package com.onepiecemod.style;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

import com.onepiecemod.OnePieceMod;

/**
 * The tiny message the player's game sends to the server when they press a fighting style key.
 * Keys only exist on the player's computer, so the server has to be told about them.
 */
public record StylePayload(int action) implements CustomPacketPayload {
	/** Z: use the selected technique. */
	public static final int USE = 0;
	/** Shift+Z: select the next technique. */
	public static final int NEXT = 1;
	/** Jump pressed while in the air (Geppo and Sky Walk). */
	public static final int AIR_JUMP = 2;

	public static final CustomPacketPayload.Type<StylePayload> TYPE = new CustomPacketPayload.Type<>(OnePieceMod.id("fighting_style"));
	public static final StreamCodec<ByteBuf, StylePayload> CODEC = ByteBufCodecs.VAR_INT.map(StylePayload::new, StylePayload::action);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
