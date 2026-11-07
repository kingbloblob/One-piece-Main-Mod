package com.onepiecemod.cutscene;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.serialization.Codec;

import io.netty.buffer.ByteBuf;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;

/**
 * Cinematic moments: a title card when a big boss starts a fight with you for the first time (see BossIntros),
 * and story flashbacks when certain chapters start (Roger's execution, Ohara, Oden, God Valley...).
 *
 * The text lives in src/main/resources/onepiece/cutscenes.json. The server only sends a small packet;
 * the player's game draws black cinema bars and the text over the normal view, so nothing stops
 * and nothing heavy is rendered. Every cutscene can be skipped with the "Skip cutscene" key (Enter),
 * and turned off on the client under One Piece Settings > Screen.
 *
 * Each player sees each cutscene once. Seen flashbacks can be watched again with /flashback.
 * OnePieceMod calls initialize() once while the game loads.
 */
public final class CutsceneFeature {
	public static final int BOSS_INTRO = 0;
	public static final int FLASHBACK = 1;

	/** Cutscenes this player has already seen: "boss:kaido", "flash:ohara". */
	public static final AttachmentType<List<String>> SEEN = AttachmentRegistry.create(
			OnePieceMod.id("cutscenes_seen"),
			builder -> builder.persistent(Codec.STRING.listOf()).copyOnDeath());

	/**
	 * Server -> player: play a cutscene.
	 *
	 * @param kind     BOSS_INTRO or FLASHBACK
	 * @param title    the big text (boss name, flashback title)
	 * @param subtitle the small text (boss title, "where and when" of a flashback)
	 * @param lines    what is said, one entry per line, "Speaker: text" or plain narration
	 * @param color    accent colour, 0xRRGGBB
	 * @param ticks    how long it plays if nobody skips it
	 * @param entity   the boss's entity id (the camera turns to it), or -1
	 * @param delay    ticks to wait before it starts (so it doesn't cover the chapter title)
	 */
	public record Play(int kind, String title, String subtitle, List<String> lines, int color, int ticks, int entity, int delay)
			implements CustomPacketPayload {
		public static final Type<Play> TYPE = new Type<>(OnePieceMod.id("cutscene_play"));
		public static final StreamCodec<ByteBuf, Play> CODEC = CustomPacketPayload.codec(Play::write, Play::read);

		private void write(ByteBuf buf) {
			ByteBufCodecs.VAR_INT.encode(buf, kind);
			ByteBufCodecs.STRING_UTF8.encode(buf, title);
			ByteBufCodecs.STRING_UTF8.encode(buf, subtitle);
			ByteBufCodecs.VAR_INT.encode(buf, lines.size());
			for (String line : lines) {
				ByteBufCodecs.STRING_UTF8.encode(buf, line);
			}
			ByteBufCodecs.INT.encode(buf, color);
			ByteBufCodecs.VAR_INT.encode(buf, ticks);
			ByteBufCodecs.VAR_INT.encode(buf, entity + 1);
			ByteBufCodecs.VAR_INT.encode(buf, delay);
		}

		private static Play read(ByteBuf buf) {
			int kind = ByteBufCodecs.VAR_INT.decode(buf);
			String title = ByteBufCodecs.STRING_UTF8.decode(buf);
			String subtitle = ByteBufCodecs.STRING_UTF8.decode(buf);
			int count = Math.min(ByteBufCodecs.VAR_INT.decode(buf), 32);
			List<String> lines = new ArrayList<>();
			for (int i = 0; i < count; i++) {
				lines.add(ByteBufCodecs.STRING_UTF8.decode(buf));
			}
			int color = ByteBufCodecs.INT.decode(buf);
			int ticks = ByteBufCodecs.VAR_INT.decode(buf);
			int entity = ByteBufCodecs.VAR_INT.decode(buf) - 1;
			int delay = ByteBufCodecs.VAR_INT.decode(buf);
			return new Play(kind, title, subtitle, lines, color, ticks, entity, delay);
		}

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Player -> server: "I skipped the cutscene" (or "I have cutscenes turned off"). */
	public record Skip() implements CustomPacketPayload {
		public static final Skip INSTANCE = new Skip();
		public static final Type<Skip> TYPE = new Type<>(OnePieceMod.id("cutscene_skip"));
		public static final StreamCodec<ByteBuf, Skip> CODEC = StreamCodec.unit(INSTANCE);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	// ---- The data file ----

	public static class Data {
		public Map<String, Boss> bosses = Map.of();
		public Map<String, Flashback> flashbacks = Map.of();
	}

	public static class Boss {
		public String title = "";
		public String line = "";
		public String color = "";
	}

	public static class Flashback {
		public String chapter = "";
		public String title = "";
		public String when = "";
		public List<String> lines = List.of();
	}

	private static Data data = new Data();

	static Data data() {
		return data;
	}

	/** Flashback ids in file order. */
	static Map<String, Flashback> flashbacks() {
		return data.flashbacks;
	}

	private static void load() {
		try (InputStream in = CutsceneFeature.class.getResourceAsStream("/onepiece/cutscenes.json")) {
			if (in == null) {
				OnePieceMod.LOGGER.warn("Cutscene problem: onepiece/cutscenes.json is missing");
				return;
			}
			Data loaded = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), Data.class);
			if (loaded.bosses == null) {
				loaded.bosses = Map.of();
			}
			loaded.flashbacks = loaded.flashbacks == null ? Map.of() : new LinkedHashMap<>(loaded.flashbacks);
			data = loaded;
		} catch (Exception e) {
			OnePieceMod.LOGGER.warn("Cutscene problem: couldn't read onepiece/cutscenes.json", e);
		}
	}

	static int color(String hex, int fallback) {
		try {
			return hex == null || hex.isEmpty() ? fallback : Integer.parseInt(hex, 16) & 0xFFFFFF;
		} catch (NumberFormatException e) {
			return fallback;
		}
	}

	// ---- Seen ----

	static boolean seen(ServerPlayer player, String key) {
		return player.getAttachedOrElse(SEEN, List.<String>of()).contains(key);
	}

	static void markSeen(ServerPlayer player, String key) {
		List<String> seen = new ArrayList<>(player.getAttachedOrElse(SEEN, List.<String>of()));
		if (!seen.contains(key)) {
			seen.add(key);
			player.setAttached(SEEN, seen);
		}
	}

	static boolean canSend(ServerPlayer player) {
		return ServerPlayNetworking.canSend(player, Play.TYPE);
	}

	// ---- Flashbacks ----

	private static final int SEPIA = 0xD9A766;

	/** How long a flashback plays: a little for the title, then about 4 seconds per line (longer lines get more). */
	static int flashbackTicks(Flashback flashback) {
		int ticks = 50;
		for (String line : flashback.lines) {
			ticks += 50 + line.length();
		}
		return ticks;
	}

	private static Play flashbackPacket(Flashback flashback, int delay) {
		return new Play(FLASHBACK, flashback.title, flashback.when, flashback.lines, SEPIA, flashbackTicks(flashback), -1, delay);
	}

	/**
	 * A story chapter just started (StoryTracker.startChapter calls this).
	 * Plays its flashback the first time, a few seconds later so the chapter title shows first.
	 */
	public static void onChapterStart(ServerPlayer player, String chapterId) {
		if (!canSend(player)) {
			// The first chapter starts while the player is still joining: try again once their game is ready.
			PENDING.put(player.getUUID(), chapterId);
			return;
		}
		PENDING.remove(player.getUUID());
		for (Map.Entry<String, Flashback> entry : data.flashbacks.entrySet()) {
			String key = "flash:" + entry.getKey();
			if (entry.getValue().chapter.equals(chapterId) && !seen(player, key)) {
				markSeen(player, key);
				ServerPlayNetworking.send(player, flashbackPacket(entry.getValue(), 80));
				player.sendSystemMessage(Component.literal("A memory comes back... (watch it again any time with /flashback)")
						.withStyle(ChatFormatting.DARK_GRAY, ChatFormatting.ITALIC));
			}
		}
	}

	/** Chapter flashbacks waiting for a joining player's game to be ready (player -> chapter id). */
	private static final Map<java.util.UUID, String> PENDING = new java.util.HashMap<>();

	private static void retryPending(net.minecraft.server.MinecraftServer server) {
		if (PENDING.isEmpty() || server.getTickCount() % 20 != 0) {
			return;
		}
		for (Map.Entry<java.util.UUID, String> entry : new ArrayList<>(PENDING.entrySet())) {
			ServerPlayer player = server.getPlayerList().getPlayer(entry.getKey());
			if (player == null) {
				PENDING.remove(entry.getKey());
			} else if (canSend(player)) {
				onChapterStart(player, entry.getValue());
			}
		}
	}

	// ---- Setup ----

	public static void initialize() {
		load();
		PayloadTypeRegistry.clientboundPlay().register(Play.TYPE, Play.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(Skip.TYPE, Skip.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(Skip.TYPE, (payload, context) -> BossIntros.skipped(context.player()));
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			BossIntros.cleanUp(server);
			retryPending(server);
		});

		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("flashback")
						.executes(context -> {
							list(context.getSource().getPlayerOrException());
							return 1;
						})
						.then(Commands.literal("reset").executes(context -> {
							ServerPlayer player = context.getSource().getPlayerOrException();
							player.removeAttached(SEEN);
							player.sendSystemMessage(Component.literal("Boss intros and flashbacks will play again the next time they come up.")
									.withStyle(ChatFormatting.GRAY));
							return 1;
						}))
						.then(Commands.argument("id", StringArgumentType.word())
								.suggests((context, builder) -> {
									for (String id : data.flashbacks.keySet()) {
										builder.suggest(id);
									}
									return builder.buildFuture();
								})
								.executes(context -> {
									replay(context.getSource().getPlayerOrException(), StringArgumentType.getString(context, "id"),
											Commands.hasPermission(Commands.LEVEL_GAMEMASTERS).test(context.getSource()));
									return 1;
								}))));
	}

	/** /flashback: the memories this player has seen, click one to watch it again. */
	private static void list(ServerPlayer player) {
		player.sendSystemMessage(Component.literal("=== Memories ===").withStyle(ChatFormatting.GOLD));
		int count = 0;
		for (Map.Entry<String, Flashback> entry : data.flashbacks.entrySet()) {
			if (!seen(player, "flash:" + entry.getKey())) {
				continue;
			}
			count++;
			String command = "/flashback " + entry.getKey();
			player.sendSystemMessage(Component.literal(" ▶ " + entry.getValue().title).withStyle(style -> style
					.withColor(ChatFormatting.YELLOW)
					.withClickEvent(new ClickEvent.RunCommand(command))
					.withHoverEvent(new HoverEvent.ShowText(Component.literal(entry.getValue().when + "\nClick to watch")))));
		}
		int total = data.flashbacks.size();
		player.sendSystemMessage(Component.literal(count == 0
				? "No memories yet. They come back as the story goes on."
				: count + " of " + total + " memories found. Click one to watch it again.").withStyle(ChatFormatting.GRAY));
	}

	private static void replay(ServerPlayer player, String id, boolean op) {
		Flashback flashback = data.flashbacks.get(id);
		if (flashback == null) {
			player.sendSystemMessage(Component.literal("There's no memory called " + id + ". Type /flashback for the list.").withStyle(ChatFormatting.RED));
			return;
		}
		if (!op && !seen(player, "flash:" + id)) {
			player.sendSystemMessage(Component.literal("You haven't found that memory yet. Keep following the story.").withStyle(ChatFormatting.RED));
			return;
		}
		if (!canSend(player)) {
			return;
		}
		ServerPlayNetworking.send(player, flashbackPacket(flashback, 0));
	}

	private CutsceneFeature() {
	}
}
