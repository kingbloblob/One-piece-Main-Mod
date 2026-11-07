package com.onepiecemod.ship;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.networking.v1.EntityTrackingEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;

/**
 * Messages sent between the server and players' games for ships and flags.
 */
public class ShipPayloads {
	/** Server -> player: "this ship entity is made of these blocks". Sent when a player first sees a ship. */
	public record ShipBlocks(int entityId, ShipLayout layout) implements CustomPacketPayload {
		public static final Type<ShipBlocks> TYPE = new Type<>(OnePieceMod.id("ship_blocks"));
		public static final StreamCodec<ByteBuf, ShipBlocks> CODEC = StreamCodec.composite(
				ByteBufCodecs.VAR_INT, ShipBlocks::entityId,
				ShipLayout.STREAM_CODEC, ShipBlocks::layout,
				ShipBlocks::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Player -> server: "save this painting onto the Jolly Roger in my hand". */
	public record SaveDesign(boolean offhand, FlagDesign design) implements CustomPacketPayload {
		public static final Type<SaveDesign> TYPE = new Type<>(OnePieceMod.id("save_design"));
		public static final StreamCodec<ByteBuf, SaveDesign> CODEC = StreamCodec.composite(
				ByteBufCodecs.BOOL, SaveDesign::offhand,
				FlagDesign.STREAM_CODEC, SaveDesign::design,
				SaveDesign::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	public static void initialize() {
		PayloadTypeRegistry.clientboundPlay().register(ShipBlocks.TYPE, ShipBlocks.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(SaveDesign.TYPE, SaveDesign.CODEC);

		ServerPlayNetworking.registerGlobalReceiver(SaveDesign.TYPE, (payload, context) -> {
			InteractionHand hand = payload.offhand() ? InteractionHand.OFF_HAND : InteractionHand.MAIN_HAND;
			ItemStack stack = context.player().getItemInHand(hand);
			// Only paint the item if they really are still holding a Jolly Roger.
			if (stack.is(ShipFeature.JOLLY_ROGER_ITEM)) {
				stack.set(ShipFeature.FLAG_DESIGN, payload.design());
			}
		});

		// When a player comes close enough to see a ship, tell their game what the ship looks like.
		EntityTrackingEvents.START_TRACKING.register((entity, player) -> {
			if (entity instanceof ShipEntity ship) {
				ServerPlayNetworking.send(player, new ShipBlocks(ship.getId(), ship.getLayout()));
			}
		});
	}
}
