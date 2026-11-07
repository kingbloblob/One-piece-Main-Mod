package com.onepiecemod.hideout;

import java.util.ArrayList;
import java.util.List;

import io.netty.buffer.ByteBuf;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.crew.CrewmateEntity;

/**
 * Messages for the hideout screen: the server sends what the flag knows, the screen's buttons send back
 * "stash" (open the stash), "station" (set the crew in the claim to live here) or "refresh".
 */
public final class HideoutPayloads {
	private HideoutPayloads() {
	}

	/**
	 * Server -> player: the hideout screen's contents.
	 * @param needs   what the next level needs: "1" (done) or "0" followed by the text, like "1Beds 3/3"
	 * @param crew    one line per crewmate living here
	 * @param stats   defence, cannons, Navy interest...
	 * @param report  the last daily report
	 */
	public record Sync(BlockPos pos, String crewName, int level, String perk, List<String> needs, List<String> crew,
			List<String> stats, List<String> report, boolean open) implements CustomPacketPayload {
		public static final Type<Sync> TYPE = new Type<>(OnePieceMod.id("hideout_sync"));
		public static final StreamCodec<ByteBuf, Sync> CODEC = StreamCodec.of((buf, sync) -> {
			FriendlyByteBuf out = new FriendlyByteBuf(buf);
			out.writeBlockPos(sync.pos);
			out.writeUtf(sync.crewName);
			out.writeVarInt(sync.level);
			out.writeUtf(sync.perk);
			writeList(out, sync.needs);
			writeList(out, sync.crew);
			writeList(out, sync.stats);
			writeList(out, sync.report);
			out.writeBoolean(sync.open);
		}, buf -> {
			FriendlyByteBuf in = new FriendlyByteBuf(buf);
			return new Sync(in.readBlockPos(), in.readUtf(), in.readVarInt(), in.readUtf(), readList(in), readList(in),
					readList(in), readList(in), in.readBoolean());
		});

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Player -> server: a button on the hideout screen. */
	public record Action(BlockPos pos, String action) implements CustomPacketPayload {
		public static final Type<Action> TYPE = new Type<>(OnePieceMod.id("hideout_action"));
		public static final StreamCodec<ByteBuf, Action> CODEC = StreamCodec.of((buf, action) -> {
			FriendlyByteBuf out = new FriendlyByteBuf(buf);
			out.writeBlockPos(action.pos);
			out.writeUtf(action.action);
		}, buf -> {
			FriendlyByteBuf in = new FriendlyByteBuf(buf);
			return new Action(in.readBlockPos(), in.readUtf());
		});

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	private static void writeList(FriendlyByteBuf out, List<String> list) {
		out.writeVarInt(list.size());
		for (String line : list) {
			out.writeUtf(line);
		}
	}

	private static List<String> readList(FriendlyByteBuf in) {
		int size = in.readVarInt();
		List<String> list = new ArrayList<>(size);
		for (int i = 0; i < size; i++) {
			list.add(in.readUtf());
		}
		return list;
	}

	static void initialize() {
		PayloadTypeRegistry.clientboundPlay().register(Sync.TYPE, Sync.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(Action.TYPE, Action.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(Action.TYPE, (payload, context) -> {
			ServerPlayer player = context.player();
			ServerLevel level = (ServerLevel) player.level();
			if (player.distanceToSqr(Vec3.atCenterOf(payload.pos())) > 10 * 10 || !level.isLoaded(payload.pos())
					|| !(level.getBlockEntity(payload.pos()) instanceof HideoutFlagBlockEntity flag) || !flag.isCrew(player)) {
				return;
			}
			switch (payload.action()) {
				case "stash" -> flag.openStash(player);
				case "station" -> {
					if (!player.getUUID().equals(flag.owner())) {
						player.sendSystemMessage(Component.literal("Only the captain can tell the crew where to live.").withStyle(ChatFormatting.YELLOW));
					} else {
						int count = flag.stationCrew(player);
						player.sendSystemMessage(Component.literal(count == 0
								? "No crewmates to move in. Bring them inside the claim first (or they already live here)."
								: count + (count == 1 ? " crewmate moves" : " crewmates move") + " into the hideout and get to work.")
								.withStyle(ChatFormatting.GOLD));
						send(player, flag, false);
					}
				}
				default -> send(player, flag, false);
			}
		});
	}

	static void open(ServerPlayer player, HideoutFlagBlockEntity flag) {
		if (!ServerPlayNetworking.canSend(player, Sync.TYPE)) {
			HideoutCommands.info(player); // A player without the mod on their game: chat instead.
			return;
		}
		send(player, flag, true);
	}

	static void send(ServerPlayer player, HideoutFlagBlockEntity flag, boolean open) {
		ServerLevel level = (ServerLevel) player.level();
		int lvl = flag.level();
		List<String> needs = new ArrayList<>();
		List<CrewmateEntity> residents = flag.residents(level);
		if (!flag.surveyed()) {
			needs.add("0The crew is still looking the place over...");
		} else if (lvl < HideoutLevels.MAX) {
			for (HideoutLevels.Need need : HideoutLevels.needs(lvl + 1, flag.survey(), residents.size())) {
				needs.add((need.done() ? "1" : "0") + need.text() + " " + Math.min(need.have(), need.need()) + "/" + need.need());
			}
		}
		List<String> crew = new ArrayList<>();
		for (CrewmateEntity crewmate : residents) {
			String doing = crewmate.isKnockedOut() ? "knocked out" : crewmate.isSleeping() ? "asleep" : "working";
			crew.add(crewmate.getDisplayName().getString() + " Lv " + crewmate.getCrewLevel() + " (" + doing + ")");
		}
		List<String> stats = HideoutCommands.stats(level, flag);
		send(player, new Sync(flag.getBlockPos(), flag.crewName(level), lvl, HideoutLevels.perk(lvl), needs, crew, stats,
				List.copyOf(flag.report()), open));
	}

	private static void send(ServerPlayer player, Sync sync) {
		ServerPlayNetworking.send(player, sync);
	}
}
