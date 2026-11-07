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
 * The pirate look for Minecraft's own menus (title screen, pause, options, world select, loading and death screens).
 *
 * It is all a built-in resource pack inside the mod (src/main/resources/resourcepacks/pirate_menus), so no menu code
 * is changed and other mods like JEI keep working. It swaps in our own panorama, logo, wooden buttons, deck-plank
 * backgrounds, rope separators, splash texts, button wording and title-screen music.
 *
 * Two ways to turn it off:
 * - in game: Options > Resource Packs, move "One Piece Pirate Menus" to the left side;
 * - for modpacks: set theme=off in config/onepiece-menus.txt (the pack is then still listed, just off by default).
 */
public class PirateMenus {
	private static final Path CONFIG = FabricLoader.getInstance().getConfigDir().resolve("onepiece-menus.txt");

	public static void initialize() {
		boolean on = themeOn();
		FabricLoader.getInstance().getModContainer(OnePieceMod.MOD_ID).ifPresent(mod -> ResourceLoader.registerBuiltinPack(
				OnePieceMod.id("pirate_menus"), mod, Component.literal("One Piece Pirate Menus"),
				on ? PackActivationType.DEFAULT_ENABLED : PackActivationType.NORMAL));
	}

	private static boolean themeOn() {
		try {
			if (!Files.exists(CONFIG)) {
				Files.writeString(CONFIG, """
						# One Piece Mod: pirate look for the title screen and other Minecraft menus.
						# on  = turned on by default (you can still switch it off in Options > Resource Packs)
						# off = turned off by default (you can still switch it on in Options > Resource Packs)
						theme=on
						""");
				return true;
			}
			for (String line : Files.readAllLines(CONFIG)) {
				String l = line.trim().toLowerCase(Locale.ROOT).replace(" ", "");
				if (l.startsWith("theme=")) {
					return !l.substring(6).matches("off|false|no|0");
				}
			}
		} catch (IOException e) {
			OnePieceMod.LOGGER.warn("Could not read {}", CONFIG, e);
		}
		return true;
	}
}
