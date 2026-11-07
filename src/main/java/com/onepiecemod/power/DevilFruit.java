package com.onepiecemod.power;

/**
 * Everything the mod needs to know about one Devil Fruit.
 *
 * @param id        the item id, like "mera_mera_no_mi" (Zoan models go on the end: "tori_tori_no_mi_phoenix")
 * @param name      the name shown in game
 * @param type      Paramecia, Logia or Zoan
 * @param color     main color of the fruit, used for its texture
 * @param accent    swirl color of the fruit
 * @param primary   name of the move used with the power key (R)
 * @param secondary name of the move used with Sneak + power key
 */
public record DevilFruit(String id, String name, Type type, int color, int accent, String primary, String secondary) {
	public enum Type {
		/** Superhuman body powers, like rubber or strings. */
		PARAMECIA,
		/** Turn into an element, like fire or ice. Attacks often pass right through them. */
		LOGIA,
		/** Turn into an animal. */
		ZOAN
	}
}
