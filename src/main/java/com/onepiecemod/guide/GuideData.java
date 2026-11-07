package com.onepiecemod.guide;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import com.google.gson.Gson;

import com.onepiecemod.OnePieceMod;

/**
 * The chapters of the Pirate's Handbook, read from src/main/resources/onepiece/guide.json.
 * Edit that file to change what the book says. No code changes needed.
 */
public class GuideData {
	public static class Chapter {
		public String id;
		public String title;
		/** Item id shown next to the chapter title, like "onepiece:log_pose". */
		public String icon = "minecraft:book";
		/** Hex colour for the title and headings, like "FFD75E". */
		public String color = "FFD75E";
		/** One entry per line. "# " = heading, "- " = bullet, "> " = tip, "" = empty line. */
		public List<String> text = new ArrayList<>();

		public int colorArgb() {
			try {
				return 0xFF000000 | Integer.parseInt(color, 16);
			} catch (NumberFormatException e) {
				return 0xFFFFD75E;
			}
		}
	}

	private static class File {
		List<Chapter> chapters = new ArrayList<>();
	}

	private static List<Chapter> chapters;

	public static List<Chapter> chapters() {
		if (chapters == null) {
			try (InputStream in = GuideData.class.getResourceAsStream("/onepiece/guide.json")) {
				chapters = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), File.class).chapters;
			} catch (Exception e) {
				OnePieceMod.LOGGER.error("Could not read onepiece/guide.json", e);
				chapters = new ArrayList<>();
			}
		}
		return chapters;
	}
}
