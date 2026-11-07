package com.onepiecemod.questtree;

import java.util.ArrayList;
import java.util.List;

import io.netty.buffer.ByteBuf;

import net.minecraft.commands.Commands;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.story.StoryData;
import com.onepiecemod.story.StoryGoals;
import com.onepiecemod.story.StoryProgress;

/**
 * The quest tree: one screen that shows the whole story and every character's quest line,
 * with what's done, what you're on now and what's still locked.
 *
 * Only the server knows a player's progress, so opening it goes like this:
 * the J key (or /quests) asks the server, the server packs up the player's progress and sends it,
 * and the player's game opens the screen (see questtree/client/QuestTreeScreen).
 * OnePieceMod calls initialize() once while the game loads.
 */
public class QuestTreeFeature {
	/** Player -> server: "send me my quest tree". */
	public record Request() implements CustomPacketPayload {
		public static final Request INSTANCE = new Request();
		public static final Type<Request> TYPE = new Type<>(OnePieceMod.id("quest_tree_request"));
		public static final StreamCodec<ByteBuf, Request> CODEC = StreamCodec.unit(INSTANCE);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/**
	 * Server -> player: "open the quest tree with this progress".
	 *
	 * @param chapter        the story chapter the player is on (counting from 0)
	 * @param goalsDone      goals done in that chapter, by position ("0", "2"...)
	 * @param goalProgress   one entry per goal of that chapter: "3/16" style progress, or "" if the goal doesn't count anything
	 * @param questsStarted  character quest steps given to the player, like "luffy:0"
	 * @param questsDone     character quest steps finished, like "luffy:0"
	 * @param questsReady    quest givers whose current step is done and only needs handing in, like "luffy"
	 */
	public record Open(int chapter, List<String> goalsDone, List<String> goalProgress,
			List<String> questsStarted, List<String> questsDone, List<String> questsReady) implements CustomPacketPayload {
		public static final Type<Open> TYPE = new Type<>(OnePieceMod.id("open_quest_tree"));
		public static final StreamCodec<ByteBuf, Open> CODEC = StreamCodec.composite(
				ByteBufCodecs.VAR_INT, Open::chapter,
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), Open::goalsDone,
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), Open::goalProgress,
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), Open::questsStarted,
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), Open::questsDone,
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), Open::questsReady,
				Open::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	public static void initialize() {
		PayloadTypeRegistry.serverboundPlay().register(Request.TYPE, Request.CODEC);
		PayloadTypeRegistry.clientboundPlay().register(Open.TYPE, Open.CODEC);

		ServerPlayNetworking.registerGlobalReceiver(Request.TYPE, (payload, context) -> open(context.player()));

		// /quests opens the same screen, for anyone who'd rather type than press J.
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("quests").executes(context -> {
					open(context.getSource().getPlayerOrException());
					return 1;
				})
		));
	}

	/** Packs up the player's progress and tells their game to open the quest tree. */
	public static void open(ServerPlayer player) {
		StoryProgress progress = StoryProgress.orStart(player);
		List<String> goalProgress = new ArrayList<>();
		StoryData.Chapter chapter = StoryData.chapter(progress.chapter());
		if (chapter != null) {
			for (StoryData.Goal goal : chapter.goals) {
				String text = StoryGoals.progressText(player, progress, goal);
				goalProgress.add(text == null ? "" : text);
			}
		}

		List<String> ready = new ArrayList<>();
		for (CharacterData character : CharacterData.all().values()) {
			int step = currentStep(player, character);
			if (step < character.quests.size()
					&& CharacterAttachments.has(player, CharacterAttachments.QUESTS_STARTED, character.id + ":" + step)
					&& stepComplete(player, character.quests.get(step))) {
				ready.add(character.id);
			}
		}

		ServerPlayNetworking.send(player, new Open(progress.chapter(), progress.goals(), goalProgress,
				player.getAttachedOrElse(CharacterAttachments.QUESTS_STARTED, List.of()),
				player.getAttachedOrElse(CharacterAttachments.QUESTS_DONE, List.of()),
				ready));
	}

	/** Same rule as QuestHandler: the first step that isn't done yet. */
	private static int currentStep(ServerPlayer player, CharacterData character) {
		int step = 0;
		while (step < character.quests.size()
				&& CharacterAttachments.has(player, CharacterAttachments.QUESTS_DONE, character.id + ":" + step)) {
			step++;
		}
		return step;
	}

	/** Same checks as QuestHandler uses when you talk to the quest giver. */
	private static boolean stepComplete(ServerPlayer player, CharacterData.Quest quest) {
		return com.onepiecemod.character.QuestHandler.isComplete(player, quest);
	}
}
