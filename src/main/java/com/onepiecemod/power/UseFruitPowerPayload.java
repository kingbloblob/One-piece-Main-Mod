package com.onepiecemod.power;

import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

import com.onepiecemod.OnePieceMod;

/**
 * The message the player's game sends to the server when they press the power key.
 * The server then decides what happens, so nobody can cheat by changing their own game.
 *
 * @param move which move: PRIMARY (R), SECONDARY (Sneak + R) or AWAKENED (Y)
 */
public record UseFruitPowerPayload(int move) implements CustomPacketPayload {
	public static final int PRIMARY = 0;
	public static final int SECONDARY = 1;
	public static final int AWAKENED = 2;

	public static final CustomPacketPayload.Type<UseFruitPowerPayload> TYPE = new CustomPacketPayload.Type<>(OnePieceMod.id("use_fruit_power"));
	public static final StreamCodec<RegistryFriendlyByteBuf, UseFruitPowerPayload> CODEC = StreamCodec.composite(ByteBufCodecs.VAR_INT, UseFruitPowerPayload::move, UseFruitPowerPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
