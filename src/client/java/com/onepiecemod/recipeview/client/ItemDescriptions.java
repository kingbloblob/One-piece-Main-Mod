package com.onepiecemod.recipeview.client;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.lang.reflect.Type;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;

import net.minecraft.ChatFormatting;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;

import net.fabricmc.fabric.api.client.item.v1.ItemTooltipCallback;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterData;

/**
 * The short grey line under the name of every One Piece item ("A coil of rigging rope...").
 * The text is in src/main/resources/onepiece/item_descriptions.json, written by
 * tools/descriptions/gen_descriptions.py. Wanted Posters and Vivre Cards are described here from characters.json.
 */
public class ItemDescriptions {
	private static final int WRAP = 40;
	private static Map<String, String> texts;

	public static void initialize() {
		ItemTooltipCallback.EVENT.register((stack, context, flag, lines) -> {
			Identifier id = BuiltInRegistries.ITEM.getKey(stack.getItem());
			if (!id.getNamespace().startsWith(OnePieceMod.MOD_ID)) {
				return;
			}
			String text = describe(id);
			if (text == null || lines.isEmpty()) {
				return;
			}
			int at = 1;
			for (String line : wrap(text)) {
				lines.add(Math.min(at++, lines.size()), Component.literal(line).withStyle(ChatFormatting.GRAY));
			}
		});
	}

	public static String describe(Identifier id) {
		String path = id.getPath();
		if (path.startsWith("wanted_poster_")) {
			CharacterData who = CharacterData.get(path.substring("wanted_poster_".length()));
			return who == null ? null : "Use it on a block to fight " + who.name + " as a boss. Win to unlock Hard, then Expert. Sneak for a Normal fight.";
		}
		if (path.startsWith("vivre_card_")) {
			CharacterData who = CharacterData.get(path.substring("vivre_card_".length()));
			return who == null ? null : "Right-click to see which way " + who.name + "'s home is. Right-click again when you get there and they'll be waiting.";
		}
		return texts().get(id.toString());
	}

	private static Map<String, String> texts() {
		if (texts == null) {
			texts = new HashMap<>();
			try (InputStream in = ItemDescriptions.class.getResourceAsStream("/onepiece/item_descriptions.json")) {
				if (in != null) {
					Type type = new TypeToken<Map<String, String>>() {}.getType();
					texts = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), type);
				}
			} catch (Exception e) {
				OnePieceMod.LOGGER.warn("Could not read onepiece/item_descriptions.json", e);
			}
		}
		return texts;
	}

	/** Splits text into lines of about WRAP characters, at spaces. */
	private static List<String> wrap(String text) {
		List<String> lines = new ArrayList<>();
		StringBuilder line = new StringBuilder();
		for (String word : text.split(" ")) {
			if (!line.isEmpty() && line.length() + word.length() + 1 > WRAP) {
				lines.add(line.toString());
				line.setLength(0);
			}
			if (!line.isEmpty()) {
				line.append(' ');
			}
			line.append(word);
		}
		if (!line.isEmpty()) {
			lines.add(line.toString());
		}
		return lines;
	}
}
