package com.onepiecemod.hud;

import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

import com.onepiecemod.OnePieceMod;

/**
 * Server -> player: everything the on-screen HUD shows, sent twice a second.
 * Cooldowns are in whole seconds (0 means ready). Empty strings mean "nothing to show".
 */
public record HudPayload(
		int observationLevel, int armamentLevel, int conquerorLevel,
		boolean observationOn, boolean armamentOn, int conquerorCooldown,
		String fruitId, String fruitName, String primaryMove, String secondaryMove,
		int primaryCooldown, int secondaryCooldown, int mastery, boolean awakened, boolean formActive,
		long bounty, int pirateLevel, int levelXp, int levelXpNeeded,
		String styleName, String techniqueName, int techniqueCooldown,
		String chapterTitle, String goalText) implements CustomPacketPayload {

	public static final Type<HudPayload> TYPE = new Type<>(OnePieceMod.id("hud_sync"));
	public static final StreamCodec<FriendlyByteBuf, HudPayload> CODEC = CustomPacketPayload.codec(HudPayload::write, HudPayload::read);

	private void write(FriendlyByteBuf buf) {
		buf.writeVarInt(observationLevel);
		buf.writeVarInt(armamentLevel);
		buf.writeVarInt(conquerorLevel);
		buf.writeBoolean(observationOn);
		buf.writeBoolean(armamentOn);
		buf.writeVarInt(conquerorCooldown);
		buf.writeUtf(fruitId);
		buf.writeUtf(fruitName);
		buf.writeUtf(primaryMove);
		buf.writeUtf(secondaryMove);
		buf.writeVarInt(primaryCooldown);
		buf.writeVarInt(secondaryCooldown);
		buf.writeVarInt(mastery);
		buf.writeBoolean(awakened);
		buf.writeBoolean(formActive);
		buf.writeVarLong(bounty);
		buf.writeVarInt(pirateLevel);
		buf.writeVarInt(levelXp);
		buf.writeVarInt(levelXpNeeded);
		buf.writeUtf(styleName);
		buf.writeUtf(techniqueName);
		buf.writeVarInt(techniqueCooldown);
		buf.writeUtf(chapterTitle);
		buf.writeUtf(goalText);
	}

	private static HudPayload read(FriendlyByteBuf buf) {
		return new HudPayload(
				buf.readVarInt(), buf.readVarInt(), buf.readVarInt(),
				buf.readBoolean(), buf.readBoolean(), buf.readVarInt(),
				buf.readUtf(), buf.readUtf(), buf.readUtf(), buf.readUtf(),
				buf.readVarInt(), buf.readVarInt(), buf.readVarInt(), buf.readBoolean(), buf.readBoolean(),
				buf.readVarLong(), buf.readVarInt(), buf.readVarInt(), buf.readVarInt(),
				buf.readUtf(), buf.readUtf(), buf.readVarInt(),
				buf.readUtf(), buf.readUtf());
	}

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
