package com.onepiecemod.menus.client;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

import net.minecraft.network.chat.Component;

import net.fabricmc.fabric.api.resource.v1.ResourceLoader;
import net.fabricmc.fabric.api.resource.v1.pack.PackActivationType;
import net.fabricmc.loader.api.FabricLoader;

import com.onepiecemod.OnePieceMod;

/**
 * The anime look for vanilla Minecraft: brighter, warmer colours, flatter cel-style shading and inked item edges,
 * so vanilla blocks, items and mobs sit next to the mod's own art.
 *
 * It is a built-in resource pack inside the mod (src/main/resources/resourcepacks/anime_look), made by
 * tools/anime/gen_anime_look.py from the game's own textures. It leaves the menus to the pirate_menus pack and
 * never touches the mod's onepiece textures.
 *
 * It is off by default. Two ways to turn it on:
 * - in game: Options > Resource Packs, move "One Piece Anime Look" to the right side;
 * - for modpacks: set look=on in config/onepiece-anime.txt (the pack is then on by default).
 */
public class AnimeLook {
	private static final Path CONFIG = FabricLoader.getInstance().getConfigDir().resolve("onepiece-anime.txt");

	public static void initialize() {
		boolean on = lookOn();
		FabricLoader.getInstance().getModContainer(OnePieceMod.MOD_ID).ifPresent(mod -> ResourceLoader.registerBuiltinPack(
				OnePieceMod.id("anime_look"), mod, Component.literal("One Piece Anime Look"),
				on ? PackActivationType.DEFAULT_ENABLED : PackActivationType.NORMAL));
	}

	private static boolean lookOn() {
		try {
			if (!Files.exists(CONFIG)) {
				Files.writeString(CONFIG, """
						# One Piece Mod: anime colours and shading for vanilla blocks, items and mobs.
						# on  = turned on by default (you can still switch it off in Options > Resource Packs)
						# off = turned off by default (you can still switch it on in Options > Resource Packs)
						look=off
						""");
				return false;
			}
			for (String line : Files.readAllLines(CONFIG)) {
				String l = line.trim().toLowerCase(Locale.ROOT).replace(" ", "");
				if (l.startsWith("look=")) {
					return l.substring(5).matches("on|true|yes|1");
				}
			}
		} catch (IOException e) {
			OnePieceMod.LOGGER.warn("Could not read {}", CONFIG, e);
		}
		return false;
	}
}
