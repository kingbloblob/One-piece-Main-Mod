package com.onepiecemod.questlog;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import io.netty.buffer.ByteBuf;

import com.mojang.serialization.Codec;

import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.QuartPos;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.QuestHandler;
import com.onepiecemod.sea.CalmBelt;
import com.onepiecemod.sea.LogPoseTracker;
import com.onepiecemod.sea.SeaItems;
import com.onepiecemod.sea.StartingIsland;
import com.onepiecemod.story.StoryProgress;

/**
 * The quest journal (O key or /questlog) and the navigation bar at the top of the screen.
 *
 * Journal: the player's game asks, the server answers with which quest steps are active, ready to hand in
 * and finished, plus the islands their Log Pose recorded. The game reads characters.json itself for the text.
 *
 * Navigation bar: once a second the server tells each player which sea they're in, where their Log Pose
 * points, and how their tracked quest is going (see journal/client/NavigationOverlay).
 *
 * "Tracking" a quest pins it under the compass. It is saved on the player, so it stays after a restart.
 * OnePieceMod calls initialize() once while the game loads.
 */
public class QuestLogFeature {
	/** The tracked quest: a step key like "luffy:0", "story" for the main story, or "" for none. */
	public static final AttachmentType<String> TRACKED = AttachmentRegistry.create(
			OnePieceMod.id("tracked_quest"),
			builder -> builder.persistent(Codec.STRING).copyOnDeath());

	public static final String STORY = "story";

	/** Player -> server: "send me my journal". */
	public record Request() implements CustomPacketPayload {
		public static final Request INSTANCE = new Request();
		public static final Type<Request> TYPE = new Type<>(OnePieceMod.id("quest_journal_request"));
		public static final StreamCodec<ByteBuf, Request> CODEC = StreamCodec.unit(INSTANCE);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Player -> server: "track this quest" ("" stops tracking). */
	public record Track(String key) implements CustomPacketPayload {
		public static final Type<Track> TYPE = new Type<>(OnePieceMod.id("quest_journal_track"));
		public static final StreamCodec<ByteBuf, Track> CODEC = StreamCodec.composite(
				ByteBufCodecs.STRING_UTF8, Track::key, Track::new);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/**
	 * Server -> player: "open the journal with this".
	 *
	 * @param active   quest steps given but not finished, like "luffy:0"
	 * @param ready    the active steps that are done and only need handing in
	 * @param done     finished quest steps, oldest first
	 * @param chapter  the story chapter the player is on (counting from 0)
	 * @param islands  islands the Log Pose recorded, oldest first, as "x,z,biome id"
	 * @param target   where the Log Pose points now, "x,z,biome id", or ""
	 * @param tracked  the tracked quest key
	 */
	public record Open(List<String> active, List<String> ready, List<String> done, int chapter,
			List<String> islands, String target, String tracked) implements CustomPacketPayload {
		public static final Type<Open> TYPE = new Type<>(OnePieceMod.id("quest_journal_open"));
		public static final StreamCodec<ByteBuf, Open> CODEC = StreamCodec.composite(
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), Open::active,
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), Open::ready,
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), Open::done,
				ByteBufCodecs.VAR_INT, Open::chapter,
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), Open::islands,
				ByteBufCodecs.STRING_UTF8, Open::target,
				ByteBufCodecs.STRING_UTF8, Open::tracked,
				Open::new);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/**
	 * Server -> player, once a second: what the navigation bar shows.
	 *
	 * @param sea          CalmBelt.Sea name (BLUE, CALM_BELT...) by distance from spawn, or "" outside the Overworld
	 * @param logPose      true when a Log Pose is in the inventory
	 * @param hasTarget    true when the Log Pose needle points somewhere
	 * @param targetBiome  the biome id of the island it points to, or "foosha" for the first reading
	 * @param recording    seconds spent recording the island you're on (0 when not recording)
	 * @param recordNeeded seconds needed to record an island
	 * @param islands      islands recorded so far
	 * @param tracked      the tracked quest key ("" for none)
	 * @param trackedReady true when the tracked quest step is done and only needs handing in
	 */
	public record Nav(String sea, boolean logPose, boolean hasTarget, int targetX, int targetZ, String targetBiome,
			int recording, int recordNeeded, int islands, String tracked, boolean trackedReady) implements CustomPacketPayload {
		public static final Type<Nav> TYPE = new Type<>(OnePieceMod.id("navigation_sync"));
		public static final StreamCodec<ByteBuf, Nav> CODEC = CustomPacketPayload.codec(Nav::write, Nav::read);

		private void write(ByteBuf buf) {
			ByteBufCodecs.STRING_UTF8.encode(buf, sea);
			buf.writeBoolean(logPose);
			buf.writeBoolean(hasTarget);
			ByteBufCodecs.VAR_INT.encode(buf, targetX);
			ByteBufCodecs.VAR_INT.encode(buf, targetZ);
			ByteBufCodecs.STRING_UTF8.encode(buf, targetBiome);
			ByteBufCodecs.VAR_INT.encode(buf, recording);
			ByteBufCodecs.VAR_INT.encode(buf, recordNeeded);
			ByteBufCodecs.VAR_INT.encode(buf, islands);
			ByteBufCodecs.STRING_UTF8.encode(buf, tracked);
			buf.writeBoolean(trackedReady);
		}

		private static Nav read(ByteBuf buf) {
			return new Nav(ByteBufCodecs.STRING_UTF8.decode(buf), buf.readBoolean(), buf.readBoolean(),
					ByteBufCodecs.VAR_INT.decode(buf), ByteBufCodecs.VAR_INT.decode(buf), ByteBufCodecs.STRING_UTF8.decode(buf),
					ByteBufCodecs.VAR_INT.decode(buf), ByteBufCodecs.VAR_INT.decode(buf), ByteBufCodecs.VAR_INT.decode(buf),
					ByteBufCodecs.STRING_UTF8.decode(buf), buf.readBoolean());
		}

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** The biome of each player's Log Pose target, worked out once per target instead of every second. */
	private record TargetName(BlockPos pos, String biome) {
	}

	private static final Map<UUID, TargetName> TARGET_NAMES = new HashMap<>();

	public static void initialize() {
		PayloadTypeRegistry.serverboundPlay().register(Request.TYPE, Request.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(Track.TYPE, Track.CODEC);
		PayloadTypeRegistry.clientboundPlay().register(Open.TYPE, Open.CODEC);
		PayloadTypeRegistry.clientboundPlay().register(Nav.TYPE, Nav.CODEC);

		ServerPlayNetworking.registerGlobalReceiver(Request.TYPE, (payload, context) -> open(context.player()));
		ServerPlayNetworking.registerGlobalReceiver(Track.TYPE, (payload, context) -> track(context.player(), payload.key()));

		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("questlog").executes(context -> {
					open(context.getSource().getPlayerOrException());
					return 1;
				})));

		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 20 != 5) { // Off by a few ticks from the HUD, so they don't both send on the same tick.
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				if (ServerPlayNetworking.canSend(player, Nav.TYPE)) {
					ServerPlayNetworking.send(player, nav(player));
				}
			}
		});
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> TARGET_NAMES.remove(handler.getPlayer().getUUID()));
	}

	/** Packs up the player's quests and voyage and tells their game to open the journal. */
	public static void open(ServerPlayer player) {
		List<String> active = new ArrayList<>();
		List<String> ready = new ArrayList<>();
		for (String key : player.getAttachedOrElse(CharacterAttachments.QUESTS_STARTED, List.<String>of())) {
			if (isDone(player, key)) {
				continue;
			}
			CharacterData.Quest quest = quest(key);
			if (quest == null) {
				continue;
			}
			active.add(key);
			if (QuestHandler.isComplete(player, quest)) {
				ready.add(key);
			}
		}

		ServerLevel level = (ServerLevel) player.level();
		LogPoseTracker.Journey journey = LogPoseTracker.journey(player);
		List<String> islands = new ArrayList<>();
		for (BlockPos pos : journey.visited()) {
			// The starting island sits in an ocean biome, so it gets its own name instead of "Deep Cold Ocean".
			String name = StartingIsland.isOnStartingIsland(level, pos) ? "start" : biomeName(level, pos);
			islands.add(pos.getX() + "," + pos.getZ() + "," + name);
		}
		String target = journey.target().map(pos -> pos.getX() + "," + pos.getZ() + "," + targetBiome(level, pos)).orElse("");

		ServerPlayNetworking.send(player, new Open(active, ready,
				player.getAttachedOrElse(CharacterAttachments.QUESTS_DONE, List.<String>of()),
				StoryProgress.orStart(player).chapter(), islands, target, tracked(player)));
	}

	/** Sets the tracked quest, if it's one the player really has (or the story, or none). */
	private static void track(ServerPlayer player, String key) {
		boolean valid = key.isEmpty() || key.equals(STORY)
				|| (CharacterAttachments.has(player, CharacterAttachments.QUESTS_STARTED, key) && !isDone(player, key));
		if (valid) {
			player.setAttached(TRACKED, key);
		}
	}

	/** The tracked quest. A finished one stops being tracked by itself. */
	public static String tracked(ServerPlayer player) {
		String key = player.getAttachedOrElse(TRACKED, "");
		if (!key.isEmpty() && !key.equals(STORY) && (isDone(player, key) || quest(key) == null)) {
			player.removeAttached(TRACKED);
			return "";
		}
		return key;
	}

	private static Nav nav(ServerPlayer player) {
		boolean overworld = player.level().dimension() == Level.OVERWORLD;
		String sea = overworld ? CalmBelt.seaByDistance(player.blockPosition()).name() : "";
		boolean logPose = player.getInventory().countItem(SeaItems.LOG_POSE) > 0;

		LogPoseTracker.Journey journey = LogPoseTracker.journey(player);
		Optional<BlockPos> target = journey.target();
		String biome = "";
		if (logPose && target.isPresent() && overworld) {
			TargetName cached = TARGET_NAMES.get(player.getUUID());
			if (cached == null || !cached.pos().equals(target.get())) {
				cached = new TargetName(target.get(), targetBiome((ServerLevel) player.level(), target.get()));
				TARGET_NAMES.put(player.getUUID(), cached);
			}
			biome = cached.biome();
		}
		boolean pointing = logPose && overworld && target.isPresent();

		String tracked = tracked(player);
		boolean ready = false;
		if (!tracked.isEmpty() && !tracked.equals(STORY)) {
			CharacterData.Quest quest = quest(tracked);
			ready = quest != null && QuestHandler.isComplete(player, quest);
		}

		return new Nav(sea, logPose, pointing,
				pointing ? target.get().getX() : 0, pointing ? target.get().getZ() : 0, biome,
				logPose ? LogPoseTracker.secondsRecorded(player) : 0, LogPoseTracker.recordSeconds(),
				journey.visited().size(), tracked, ready);
	}

	private static boolean isDone(ServerPlayer player, String key) {
		return CharacterAttachments.has(player, CharacterAttachments.QUESTS_DONE, key);
	}

	/** The quest step for a key like "luffy:2", or null if it doesn't exist (anymore). */
	public static CharacterData.Quest quest(String key) {
		int colon = key.lastIndexOf(':');
		if (colon < 0) {
			return null;
		}
		CharacterData character = CharacterData.get(key.substring(0, colon));
		try {
			int step = Integer.parseInt(key.substring(colon + 1));
			return character != null && step >= 0 && step < character.quests.size() ? character.quests.get(step) : null;
		} catch (NumberFormatException e) {
			return null;
		}
	}

	private static String targetBiome(ServerLevel level, BlockPos pos) {
		if (StartingIsland.site(level).firstIsland().filter(pos::equals).isPresent()) {
			return "foosha";
		}
		return biomeName(level, pos);
	}

	/** The biome there, like "onepiece:alabasta", read from the world generator so far-away chunks needn't load. */
	private static String biomeName(ServerLevel level, BlockPos pos) {
		return level.getChunkSource().getGenerator().getBiomeSource()
				.createUncachedResolver(level.getChunkSource().randomState())
				.getNoiseBiome(QuartPos.fromBlock(pos.getX()), QuartPos.fromBlock(64), QuartPos.fromBlock(pos.getZ()))
				.getRegisteredName();
	}
}
