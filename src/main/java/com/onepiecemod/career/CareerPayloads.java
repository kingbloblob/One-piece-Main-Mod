package com.onepiecemod.career;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;

/**
 * Messages between the server and players' games for careers: the server sends the career for the HUD and
 * the career screen, and the screen's buttons send back what the player picked.
 */
public final class CareerPayloads {
	private CareerPayloads() {
	}

	/**
	 * Server -> player: the player's career.
	 * @param trialDone     how many of the next rank's trial bosses are beaten
	 * @param backupSeconds seconds until backup can be called again
	 * @param mission       the orders, as text ("" = none)
	 * @param open          open the career screen now
	 */
	public record Sync(String career, int rank, int points, int strikes, int missionsDone, int trialDone, int backupSeconds,
			String mission, int missionReward, boolean open) implements CustomPacketPayload {
		public static final Type<Sync> TYPE = new Type<>(OnePieceMod.id("career_sync"));
		public static final StreamCodec<ByteBuf, Sync> CODEC = StreamCodec.of((buf, sync) -> {
			FriendlyByteBuf out = new FriendlyByteBuf(buf);
			out.writeUtf(sync.career);
			out.writeVarInt(sync.rank);
			out.writeVarInt(sync.points);
			out.writeVarInt(sync.strikes);
			out.writeVarInt(sync.missionsDone);
			out.writeVarInt(sync.trialDone);
			out.writeVarInt(sync.backupSeconds);
			out.writeUtf(sync.mission);
			out.writeVarInt(sync.missionReward);
			out.writeBoolean(sync.open);
		}, buf -> {
			FriendlyByteBuf in = new FriendlyByteBuf(buf);
			return new Sync(in.readUtf(), in.readVarInt(), in.readVarInt(), in.readVarInt(), in.readVarInt(), in.readVarInt(),
					in.readVarInt(), in.readUtf(), in.readVarInt(), in.readBoolean());
		});

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Player -> server: a button on the career screen ("orders", "abandon", "backup", "leave"). */
	public record Action(String action) implements CustomPacketPayload {
		public static final Type<Action> TYPE = new Type<>(OnePieceMod.id("career_action"));
		public static final StreamCodec<ByteBuf, Action> CODEC = StreamCodec.of(
				(buf, action) -> new FriendlyByteBuf(buf).writeUtf(action.action),
				buf -> new Action(new FriendlyByteBuf(buf).readUtf()));

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	static void initialize() {
		PayloadTypeRegistry.clientboundPlay().register(Sync.TYPE, Sync.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(Action.TYPE, Action.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(Action.TYPE, (payload, context) -> {
			ServerPlayer player = context.player();
			switch (payload.action()) {
				case "orders" -> CareerMissions.request(player);
				case "abandon" -> CareerMissions.abandon(player);
				case "backup" -> CareerAllies.call(player);
				case "leave" -> Careers.leave(player);
				default -> {
				}
			}
			sync(player);
		});
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> sync(handler.player));
	}

	static void sync(ServerPlayer player) {
		send(player, false);
	}

	static void open(ServerPlayer player) {
		send(player, true);
	}

	private static void send(ServerPlayer player, boolean open) {
		if (!ServerPlayNetworking.canSend(player, Sync.TYPE)) {
			return;
		}
		CareerData data = Careers.get(player);
		Career.Rank next = data.nextRank();
		long backup = Math.max(0, data.backupReadyAt() - player.level().getGameTime()) / 20;
		ServerPlayNetworking.send(player, new Sync(data.career(), data.rank(), data.points(), data.strikes(), data.missionsDone(),
				next != null ? Careers.trialProgress(player, next) : 0, (int) backup,
				data.mission().map(mission -> CareerMissions.text(player, mission)).orElse(""),
				data.mission().map(CareerData.Mission::reward).orElse(0), open));
	}
}
