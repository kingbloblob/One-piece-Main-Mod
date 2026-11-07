package com.onepiecemod.dialogue;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;

/**
 * What each character says on the talk screen, read from src/main/resources/onepiece/dialogue.json.
 * To change a line, edit that JSON file, not this class. Any line left out falls back to "default".
 * The quest steps themselves (what to do, what they say when you're done) stay in characters.json.
 */
public class DialogueData {
	public Lines defaults = new Lines();
	public Map<String, Lines> characters = Map.of();

	/** One character's lines. Every field is optional. */
	public static class Lines {
		/** Said when you start talking. One is picked at random. */
		public List<String> hello;
		/** "What's this place like?" */
		public String island;
		/** "Tell me about yourself." */
		public String self;
		/** "Join my crew!" */
		public String recruit;
		/** "Any advice for the voyage?" when no line for your story chapter is in "chapters". */
		public String advice;
		/** Advice for one story chapter, by chapter id from story.json, like "koby" or "wano". */
		public Map<String, String> chapters;
		/** After you take one of their jobs. */
		public String accept;
		/** After "Not right now." */
		public String decline;
		/** Said before the reminder when a job isn't finished yet. */
		public String waiting;
		/** Said as the shop opens (traders). */
		public String trade;
		/** "Teach me to fight." (Haki and fighting-style masters.) */
		public String train;
		/** "Goodbye." */
		public String bye;
	}

	// ---- Loading ----

	private static DialogueData data;

	public static DialogueData get() {
		if (data == null) {
			try (InputStream in = DialogueData.class.getResourceAsStream("/onepiece/dialogue.json")) {
				data = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), DialogueData.class);
			} catch (Exception e) {
				throw new RuntimeException("Could not read onepiece/dialogue.json", e);
			}
			if (data.characters == null) {
				data.characters = new LinkedHashMap<>();
			}
		}
		return data;
	}

	/** This character's lines, or the default lines if they have none. */
	public static Lines of(String characterId) {
		Lines lines = get().characters.get(characterId);
		return lines != null ? lines : get().defaults;
	}

	/** Picks the character's line, or the default one if theirs is missing. */
	public static String pick(String own, String fallback) {
		return own != null && !own.isEmpty() ? own : fallback;
	}
}
