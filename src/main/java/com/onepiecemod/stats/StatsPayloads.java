package com.onepiecemod.stats;

import java.util.ArrayList;
import java.util.List;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;

/**
 * Messages between the server and players' games for the stat tree.
 */
public class StatsPayloads {
	/** Server -> player: "here are your XP and ranks" (ranks in PlayerStat order). Sent whenever they change. */
	public record Sync(int xp, List<Integer> ranks, int respecCost) implements CustomPacketPayload {
		public static final Type<Sync> TYPE = new Type<>(OnePieceMod.id("player_stats_sync"));
		public static final StreamCodec<ByteBuf, Sync> CODEC = StreamCodec.composite(
				ByteBufCodecs.VAR_INT, Sync::xp,
				ByteBufCodecs.VAR_INT.apply(ByteBufCodecs.list()), Sync::ranks,
				ByteBufCodecs.VAR_INT, Sync::respecCost,
				Sync::new
		);

		public static Sync of(StatsData data, int respecCost) {
			List<Integer> ranks = new ArrayList<>();
			for (PlayerStat stat : PlayerStat.values()) {
				ranks.add(data.rank(stat));
			}
			return new Sync(data.xp(), ranks, respecCost);
		}

		/** Turns the message back into StatsData on the player's game. */
		public StatsData toData() {
			StatsData data = StatsData.EMPTY.withXp(xp);
			PlayerStat[] stats = PlayerStat.values();
			for (int i = 0; i < stats.length && i < ranks.size(); i++) {
				data = data.withRank(stats[i], ranks.get(i));
			}
			return data;
		}

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Player -> server: "spend one point on this stat". */
	public record Spend(String statId) implements CustomPacketPayload {
		public static final Type<Spend> TYPE = new Type<>(OnePieceMod.id("spend_stat_point"));
		public static final StreamCodec<ByteBuf, Spend> CODEC = StreamCodec.composite(
				ByteBufCodecs.STRING_UTF8, Spend::statId,
				Spend::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Player -> server: "give me my points back" (the Reset button). */
	public record Respec(boolean confirmed) implements CustomPacketPayload {
		public static final Type<Respec> TYPE = new Type<>(OnePieceMod.id("respec_stats"));
		public static final StreamCodec<ByteBuf, Respec> CODEC = ByteBufCodecs.BOOL.map(Respec::new, Respec::confirmed);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	public static void initialize() {
		PayloadTypeRegistry.clientboundPlay().register(Sync.TYPE, Sync.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(Spend.TYPE, Spend.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(Respec.TYPE, Respec.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(Respec.TYPE, (payload, context) -> StatRespec.respec(context.player()));

		ServerPlayNetworking.registerGlobalReceiver(Spend.TYPE, (payload, context) -> {
			PlayerStat stat = PlayerStat.byId(payload.statId());
			if (stat != null) {
				StatTraining.spend(context.player(), stat);
			}
		});

		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> sync(handler.player));
	}

	/** Tells the player's game their current stats, so the stat tree screen is up to date. */
	public static void sync(ServerPlayer player) {
		// Players without the mod installed can't read it, so don't send it to them.
		if (ServerPlayNetworking.canSend(player, Sync.TYPE)) {
			StatsData data = StatsAttachments.get(player);
			ServerPlayNetworking.send(player, Sync.of(data, StatRespec.cost(StatRespec.respecs(player), data)));
		}
	}
}
