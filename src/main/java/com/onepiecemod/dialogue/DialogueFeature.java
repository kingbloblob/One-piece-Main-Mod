package com.onepiecemod.dialogue;

import java.util.List;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;

/**
 * The two messages behind the talk screen:
 * the server sends a Page (who's talking, what they say, the choices), and the player's game
 * sends back a Choose when a choice is clicked. The rules are in Dialogue, the screen in dialogue/client.
 * OnePieceMod calls initialize() once while the game loads.
 */
public class DialogueFeature {
	/**
	 * Server -> player: "show this on the talk screen".
	 *
	 * @param entityId  the character's entity, so the screen can draw them and send choices back
	 * @param speaker   their name
	 * @param text      what they say
	 * @param hint      a small grey note under it (rewards, progress), or ""
	 * @param choiceIds    what each choice is ("job", "trade", ... see Dialogue)
	 * @param choiceLabels the words on each choice's button
	 */
	public record Page(int entityId, String speaker, String text, String hint,
			List<String> choiceIds, List<String> choiceLabels) implements CustomPacketPayload {
		public static final Type<Page> TYPE = new Type<>(OnePieceMod.id("dialogue_page"));
		public static final StreamCodec<ByteBuf, Page> CODEC = StreamCodec.composite(
				ByteBufCodecs.VAR_INT, Page::entityId,
				ByteBufCodecs.STRING_UTF8, Page::speaker,
				ByteBufCodecs.STRING_UTF8, Page::text,
				ByteBufCodecs.STRING_UTF8, Page::hint,
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), Page::choiceIds,
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), Page::choiceLabels,
				Page::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Player -> server: "I clicked this choice while talking to this character". */
	public record Choose(int entityId, String choice) implements CustomPacketPayload {
		public static final Type<Choose> TYPE = new Type<>(OnePieceMod.id("dialogue_choose"));
		public static final StreamCodec<ByteBuf, Choose> CODEC = StreamCodec.composite(
				ByteBufCodecs.VAR_INT, Choose::entityId,
				ByteBufCodecs.STRING_UTF8, Choose::choice,
				Choose::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	public static void initialize() {
		PayloadTypeRegistry.clientboundPlay().register(Page.TYPE, Page.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(Choose.TYPE, Choose.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(Choose.TYPE,
				(payload, context) -> Dialogue.choose(context.player(), payload.entityId(), payload.choice()));
		DialogueData.get(); // Read the lines now, so a broken dialogue.json shows up at startup, not mid-game.
	}
}
