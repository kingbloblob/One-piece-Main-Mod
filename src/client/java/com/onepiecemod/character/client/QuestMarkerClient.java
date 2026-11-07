package com.onepiecemod.character.client;

import java.util.HashMap;
import java.util.Map;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.character.QuestJourneys;

/**
 * Remembers the "!" and "?" the server sends for nearby quest givers (see QuestJourneys).
 * CharacterRenderer shows them above the character's name.
 */
public class QuestMarkerClient {
	private static Map<Integer, Integer> markers = Map.of();

	public static void initialize() {
		ClientPlayNetworking.registerGlobalReceiver(QuestJourneys.Markers.TYPE, (payload, context) -> {
			Map<Integer, Integer> next = new HashMap<>();
			for (int i = 0; i < payload.ids().size() && i < payload.kinds().size(); i++) {
				next.put(payload.ids().get(i), payload.kinds().get(i));
			}
			markers = next;
		});
	}

	/** The marker to show over this entity, or null for none. */
	public static Component markerFor(int entityId) {
		Integer kind = markers.get(entityId);
		if (kind == null || !com.onepiecemod.questlog.client.ClientConfig.questMarkers()) { // Screen setting: quest_markers.
			return null;
		}
		return switch (kind) {
			case QuestJourneys.MARKER_NEW -> Component.literal("!").withStyle(ChatFormatting.YELLOW, ChatFormatting.BOLD);
			case QuestJourneys.MARKER_READY -> Component.literal("?").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD);
			case QuestJourneys.MARKER_WAITING -> Component.literal("?").withStyle(ChatFormatting.GRAY, ChatFormatting.BOLD);
			default -> null;
		};
	}
}
