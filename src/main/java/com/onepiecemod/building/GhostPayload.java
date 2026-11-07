package com.onepiecemod.building;

import java.util.ArrayList;
import java.util.List;

import io.netty.buffer.ByteBuf;

import net.minecraft.core.BlockPos;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;

import com.onepiecemod.OnePieceMod;

/**
 * Server -> player: "draw these see-through ghost blocks" (an empty list means "hide them").
 * Blocks are sent by their state number, so the player's game knows the exact block and shape.
 */
public record GhostPayload(List<BlockPos> positions, List<Integer> states) implements CustomPacketPayload {
	public static final Type<GhostPayload> TYPE = new Type<>(OnePieceMod.id("blueprint_ghosts"));
	public static final StreamCodec<ByteBuf, GhostPayload> CODEC = StreamCodec.composite(
			BlockPos.STREAM_CODEC.apply(ByteBufCodecs.list()), GhostPayload::positions,
			ByteBufCodecs.VAR_INT.apply(ByteBufCodecs.list()), GhostPayload::states,
			GhostPayload::new
	);

	public static GhostPayload of(List<GhostPlan.Ghost> ghosts) {
		List<BlockPos> positions = new ArrayList<>();
		List<Integer> states = new ArrayList<>();
		for (GhostPlan.Ghost ghost : ghosts) {
			positions.add(ghost.pos());
			states.add(Block.getId(ghost.state()));
		}
		return new GhostPayload(positions, states);
	}

	public static GhostPayload hide() {
		return new GhostPayload(List.of(), List.of());
	}

	public BlockState state(int index) {
		return Block.stateById(states.get(index));
	}

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}

	public static void register() {
		PayloadTypeRegistry.clientboundPlay().register(TYPE, CODEC);
	}
}
