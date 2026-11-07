package com.onepiecemod.body;

import io.netty.buffer.ByteBuf;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.race.RaceAttachments;

/**
 * Body customization: sliders for height, weight, chest, arms, legs and head.
 *
 * New players see the body screen straight after the race picker. Players who already
 * had a race before this was added see it the next time they join.
 * Type /body to change your look again at any time.
 *
 * Only height changes gameplay: it scales the player (and their hitbox) by up to 10%,
 * stacked on top of the Giant or Tontatta size. Everything else is just looks.
 */
public class BodyFeature {
	/** The size change from the height slider. Not saved: we put it back every second instead. */
	private static final Identifier HEIGHT = OnePieceMod.id("body_height");

	/** Server -> player: "show the body screen". firstTime means it can't be skipped with Escape. */
	public record OpenEditor(boolean firstTime) implements CustomPacketPayload {
		public static final Type<OpenEditor> TYPE = new Type<>(OnePieceMod.id("open_body_editor"));
		public static final StreamCodec<ByteBuf, OpenEditor> CODEC = StreamCodec.composite(
				ByteBufCodecs.BOOL, OpenEditor::firstTime,
				OpenEditor::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Player -> server: "this is my new body". */
	public record Choose(Body body) implements CustomPacketPayload {
		public static final Type<Choose> TYPE = new Type<>(OnePieceMod.id("choose_body"));
		public static final StreamCodec<ByteBuf, Choose> CODEC = Body.STREAM_CODEC.map(Choose::new, Choose::body);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Player -> server: "these are my new looks" (hair, scar, outfit). */
	public record ChooseLook(Look look) implements CustomPacketPayload {
		public static final Type<ChooseLook> TYPE = new Type<>(OnePieceMod.id("choose_look"));
		public static final StreamCodec<ByteBuf, ChooseLook> CODEC = Look.STREAM_CODEC.map(ChooseLook::new, ChooseLook::look);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	public static void initialize() {
		BodyAttachments.initialize();

		PayloadTypeRegistry.clientboundPlay().register(OpenEditor.TYPE, OpenEditor.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(Choose.TYPE, Choose.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(ChooseLook.TYPE, ChooseLook.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(ChooseLook.TYPE,
				(payload, context) -> context.player().setAttached(BodyAttachments.LOOK, payload.look().clamped()));

		ServerPlayNetworking.registerGlobalReceiver(Choose.TYPE, (payload, context) -> {
			ServerPlayer player = context.player();
			BodyAttachments.set(player, payload.body().clamped());
			applyHeight(player);
		});

		// Players who picked a race before body customization existed get the screen once, on join.
		// (New players get it from the race picker, which opens the body screen when they pick.)
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
			ServerPlayer player = handler.player;
			applyHeight(player);
			if (BodyAttachments.get(player) == null && RaceAttachments.get(player) != null
					&& ServerPlayNetworking.canSend(player, OpenEditor.TYPE)) {
				ServerPlayNetworking.send(player, new OpenEditor(true));
			}
		});

		// Size modifiers are lost when you respawn, so put them back then, and check every second too.
		ServerPlayerEvents.AFTER_RESPAWN.register((oldPlayer, newPlayer, alive) -> applyHeight(newPlayer));
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 20 == 0) {
				for (ServerPlayer player : server.getPlayerList().getPlayers()) {
					applyHeight(player);
				}
			}
		});

		// /body opens the body screen again, so you can change your look.
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("body").executes(context -> {
					ServerPlayer player = context.getSource().getPlayerOrException();
					if (!ServerPlayNetworking.canSend(player, OpenEditor.TYPE)) {
						player.sendSystemMessage(Component.literal("You need the One Piece mod installed to change your body.")
								.withStyle(ChatFormatting.RED));
						return 0;
					}
					ServerPlayNetworking.send(player, new OpenEditor(false));
					return 1;
				})
		));
	}

	/** Makes the player's size match their height slider. Only touches the attribute when it changed. */
	public static void applyHeight(ServerPlayer player) {
		AttributeInstance scale = player.getAttribute(Attributes.SCALE);
		if (scale == null) {
			return;
		}
		Body body = BodyAttachments.get(player);
		double amount = body == null ? 0 : body.heightScale() - 1;
		AttributeModifier current = scale.getModifier(HEIGHT);
		if (amount == 0) {
			if (current != null) {
				scale.removeModifier(HEIGHT);
			}
		} else if (current == null || current.amount() != amount) {
			// "Multiplied total" so it stacks with the race size: a tall Giant is 10% bigger than a normal Giant.
			scale.addOrUpdateTransientModifier(new AttributeModifier(HEIGHT, amount, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
		}
	}
}
