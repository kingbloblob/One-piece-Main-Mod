package com.onepiecemod.town;

import java.util.List;
import java.util.Map;

import net.minecraft.util.RandomSource;

/** First names for townsfolk, a different flavour on each kind of island. */
public final class TownNames {
	private static final List<String> COMMON = List.of("Tom", "Anna", "Bill", "Mary", "Joe", "Rosa", "Sam", "Lily", "Hank", "Meg",
			"Otto", "Ella", "Gus", "Ida", "Ned", "Ruth", "Max", "Nell", "Abe", "Dora", "Pip", "Kaya", "Bob", "Jill", "Carl", "Tess",
			"Woop", "Genzo", "Boodle", "Merry", "Lucas");
	private static final Map<String, List<String>> BY_CULTURE = Map.of(
			"wano", List.of("Tama", "Hyogoro", "Okiku", "Tonoyasu", "Toko", "Hiyori", "Kawamatsu", "Shimotsuki", "Ushimaru", "Komachiyo",
					"Otsuru", "Hanzo", "Sukiyaki", "Yasuie", "Okobore", "Shinobu", "Kinji", "Ume", "Sakura", "Jirokichi"),
			"alabasta", List.of("Kohza", "Toto", "Pell", "Chaka", "Terracotta", "Karoo", "Igaram", "Amir", "Samira", "Hasan", "Layla",
					"Farid", "Nadia", "Tariq", "Zara", "Omar", "Yasmin", "Rashid", "Leila", "Karim"),
			"water7", List.of("Tilestone", "Peepley", "Lulu", "Kokoro", "Chimney", "Gonbe", "Zambai", "Mozu", "Kiwi", "Yokozuna",
					"Tom", "Hammer", "Rivet", "Plank", "Keel", "Sandy"),
			"totto", List.of("Praline", "Wafer", "Bonbon", "Truffle", "Sorbet", "Cocoa", "Mousse", "Biscotti", "Caramel", "Gelato",
					"Fudge", "Macaron", "Nougat", "Sprinkle"),
			"kuja", List.of("Marguerite", "Sweet Pea", "Aphelandra", "Daisy", "Rindo", "Ran", "Kikyo", "Belladonna", "Poppy", "Iris",
					"Azalea", "Camellia"),
			"sabaody", List.of("Pearl", "Sunny", "Pappag", "Shelly", "Nemo", "Bubbles", "Coral", "Marina", "Finn", "Skipper",
					"Bartolo", "Glimmer"),
			"grand_line", List.of("Lassoo", "Igor", "Hook", "Grog", "Rocky", "Mad Dog", "Scurvy Sam", "Patch", "Barnacle",
					"One-Eye Bob", "Rusty", "Gumbo"));

	private TownNames() {
	}

	public static String pick(String culture, RandomSource random) {
		List<String> list = BY_CULTURE.get(culture);
		if (list == null || random.nextFloat() < 0.25f) {
			list = COMMON;
		}
		return list.get(random.nextInt(list.size()));
	}
}
