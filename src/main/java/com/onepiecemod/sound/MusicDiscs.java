package com.onepiecemod.sound;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.JukeboxSong;
import net.minecraft.world.item.Rarity;

/**
 * Music discs with the mod's own songs. Play them in any jukebox.
 * The songs themselves are data files in data/onepiece_sounds/jukebox_song/.
 * Bosses sometimes drop them (see SoundFeature).
 */
public class MusicDiscs {
	public static final List<Item> ALL = new ArrayList<>();

	public static final Item TOWARD_THE_GRAND_LINE = disc("toward_the_grand_line");
	public static final Item FAIR_WINDS = disc("fair_winds");
	public static final Item CLASH_ON_THE_GRAND_LINE = disc("boss_battle");
	public static final Item CLASH_OF_EMPERORS = disc("emperor_battle");
	public static final Item JUSTICE_MARCHES = disc("justice_marches");
	public static final Item DRINK_TO_THE_HORIZON = disc("drink_to_the_horizon");
	public static final Item HAUL_THE_ANCHOR = disc("haul_the_anchor");
	public static final Item LANTERN_ON_THE_WAVES = disc("lantern_on_the_waves");
	public static final Item ABSOLUTE_JUSTICE = disc("admiral_battle");
	public static final Item WARLORD_OF_THE_SEA = disc("warlord_battle");
	public static final Item DAWN_OF_THE_VOID_CENTURY = disc("final_battle");
	public static final Item STORM_ON_THE_GRAND_LINE = disc("storm_at_sea");
	public static final Item TEN_THOUSAND_METERS_DOWN = disc("deep_sea");
	/** Sea Kings sometimes drop this one (see SoundFeature). */
	public static final Item SOMETHING_BENEATH_THE_WAVES = disc("sea_king");
	// Personal boss themes (2026-11-05): dropped by the bosses that fight to them (see BossMusic).
	public static final Item FATHER_OF_THE_SEAS = disc("whitebeard_battle");
	public static final Item SWEET_TYRANT = disc("big_mom_battle");
	public static final Item THE_STRONGEST_CREATURE = disc("kaido_battle");
	public static final Item DARKNESS_RISING = disc("blackbeard_battle");
	public static final Item FIVE_ELDERS = disc("elder_star_battle");
	public static final Item WORST_GENERATION = disc("supernova_battle");

	private static Item disc(String song) {
		Identifier id = Identifier.fromNamespaceAndPath(ModSounds.NAMESPACE, "music_disc_" + song);
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, id);
		ResourceKey<JukeboxSong> songKey = ResourceKey.create(Registries.JUKEBOX_SONG,
				Identifier.fromNamespaceAndPath(ModSounds.NAMESPACE, song));
		Item item = new Item(new Item.Properties().setId(key).stacksTo(1).rarity(Rarity.RARE).jukeboxPlayable(songKey));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		ALL.add(item);
		return item;
	}

	static void initialize() {
	}
}
