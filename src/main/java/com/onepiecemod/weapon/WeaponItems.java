package com.onepiecemod.weapon;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.ToolMaterial;

import com.onepiecemod.OnePieceMod;

/**
 * Every gun, ammo and melee weapon from the series.
 * Names are in assets/onepiece_weapons/lang/en_us.json, recipes in onepiece/station_recipes.json,
 * special effects in MeleeEffects.java, boss drops in WeaponFeature.java.
 *
 * Melee damage = 1 (your fist) + the material's bonus (iron 2, diamond 3, netherite 4) + the number below.
 * Speed is attacks per second minus 4, so -2.4 is a normal sword and -3.3 is very slow.
 *
 * Gun stats are explained in GunItem.Stats (the last three: magazine size, reload ticks, kick in degrees).
 */
public class WeaponItems {
	/** Everything, in the order shown in the creative tab. */
	static final List<Item> ALL = new ArrayList<>();

	// ---- Guns (right-click to shoot) ----

	/** The everyday pirate pistol. */
	public static final Item FLINTLOCK_PISTOL = gun("flintlock_pistol", GunItem.Hold.PISTOL, new GunItem.Stats(8.0f, 20, 40, 0.04f, 1, Ammo.Kind.BULLET, 6, 40, 3.0f), 300, Rarity.COMMON);
	/** Standard Marine issue: slower, but hits hard and far. */
	public static final Item MARINE_RIFLE = gun("marine_rifle", GunItem.Hold.RIFLE, new GunItem.Stats(11.0f, 34, 72, 0.01f, 1, Ammo.Kind.BULLET, 5, 50, 4.0f), 400, Rarity.UNCOMMON);
	/** Capone "Gang" Bege's mafia gun: three quick rounds per pull. */
	public static final Item TOMMY_GUN = gun("tommy_gun", GunItem.Hold.RIFLE, new GunItem.Stats(5.0f, 24, 40, 0.08f, 3, Ammo.Kind.BULLET, 30, 60, 1.3f), 500, Rarity.RARE);
	/** A Marine shoulder cannon. The blast never breaks blocks. */
	public static final Item HAND_CANNON = gun("hand_cannon", GunItem.Hold.RIFLE, new GunItem.Stats(12.0f, 60, 48, 0.03f, 1, Ammo.Kind.CANNONBALL, 0, 0, 8.0f), 200, Rarity.UNCOMMON);
	/** Van Augur's sniper rifle. Only Blackbeard drops it. */
	public static final Item SENRIKU = gun("senriku", GunItem.Hold.RIFLE, new GunItem.Stats(20.0f, 60, 160, 0.0f, 1, Ammo.Kind.BULLET, 4, 70, 6.0f), 800, Rarity.EPIC);
	/** Usopp's first big slingshot. Fires stars and Pop Greens. */
	public static final Item KABUTO = gun("kabuto", GunItem.Hold.SLINGSHOT, new GunItem.Stats(6.0f, 15, 40, 0.03f, 1, Ammo.Kind.STAR, 0, 0, 0.8f), 400, Rarity.UNCOMMON);
	/** Usopp's black slingshot from after the time skip. */
	public static final Item KURO_KABUTO = gun("kuro_kabuto", GunItem.Hold.SLINGSHOT, new GunItem.Stats(9.0f, 10, 64, 0.015f, 1, Ammo.Kind.STAR, 0, 0, 0.8f), 800, Rarity.RARE);

	// ---- Ammo ----

	public static final Item BULLET = simple("bullet", 64, Rarity.COMMON);
	public static final Item SEASTONE_BULLET = simple("seastone_bullet", 64, Rarity.UNCOMMON);
	public static final Item CANNONBALL = simple("cannonball", 16, Rarity.COMMON);
	public static final Item LEAD_STAR = simple("lead_star", 64, Rarity.COMMON);
	public static final Item EXPLODING_STAR = simple("exploding_star", 64, Rarity.COMMON);
	public static final Item TABASCO_STAR = simple("tabasco_star", 64, Rarity.COMMON);
	public static final Item POP_GREEN = simple("pop_green", 64, Rarity.UNCOMMON);

	// ---- Melee ----

	/** Kaido's spiked iron club. Slow, crushing, and full-power hits send a shockwave. Kaido drops it. */
	public static final Item HASSAIKAI = melee("hassaikai", ToolMaterial.NETHERITE, 9.0f, -3.3f, Rarity.EPIC);
	/** Whitebeard's bisento. Full-power hits shake the ground around you. Whitebeard drops it. */
	public static final Item MURAKUMOGIRI = melee("murakumogiri", ToolMaterial.NETHERITE, 8.0f, -3.1f, Rarity.EPIC);
	/** Crocodile's poisoned golden hook. Crocodile drops it. */
	public static final Item GOLDEN_HOOK = melee("golden_hook", ToolMaterial.DIAMOND, 4.0f, -2.4f, Rarity.RARE);
	/** Killer's spinning wrist scythes: fast, and they cut everyone around you. Killer drops them. */
	public static final Item PUNISHER = melee("punisher", ToolMaterial.DIAMOND, 3.0f, -1.8f, Rarity.RARE);
	/** Katakuri's mochi-coated trident: sticky hits slow and pull. Katakuri drops it. */
	public static final Item MOGURA = melee("mogura", ToolMaterial.NETHERITE, 5.0f, -2.8f, Rarity.EPIC);
	/** Enel's golden staff: sometimes calls down lightning. Enel drops it. */
	public static final Item NONOSAMA_BO = melee("nonosama_bo", ToolMaterial.DIAMOND, 4.0f, -2.6f, Rarity.RARE);
	/** Big Mom's little yellow umbrella homie. Big Mom drops it. */
	public static final Item HOMIE_UMBRELLA = melee("homie_umbrella", ToolMaterial.DIAMOND, 4.0f, -2.4f, Rarity.EPIC);
	/** Arlong's saw-toothed sword: its teeth leave wounds that keep hurting. */
	public static final Item KIRIBACHI = melee("kiribachi", ToolMaterial.IRON, 5.0f, -2.8f, Rarity.UNCOMMON);
	/** Kuro's cat claws: weak but very fast, and hits make you quicker (Nukiashi). */
	public static final Item NEKO_NO_TE = melee("neko_no_te", ToolMaterial.IRON, 2.0f, -1.6f, Rarity.UNCOMMON);
	/** Tashigi's sword. */
	public static final Item SHIGURE = melee("shigure", ToolMaterial.DIAMOND, 3.0f, -2.2f, Rarity.RARE);
	/** Brook's cane sword: freezes what it cuts with the chill of the underworld. */
	public static final Item SOUL_SOLID = melee("soul_solid", ToolMaterial.DIAMOND, 3.0f, -2.0f, Rarity.RARE);
	/** Law's long nodachi. */
	public static final Item KIKOKU = melee("kikoku", ToolMaterial.NETHERITE, 5.0f, -2.8f, Rarity.EPIC);
	/** Shanks's saber. With Armament Haki on, hits clash with extra force. */
	public static final Item GRYPHON = melee("gryphon", ToolMaterial.NETHERITE, 7.0f, -2.4f, Rarity.EPIC);
	/** Nami's weather staff. See ClimaTactItem. */
	public static final Item SORCERY_CLIMA_TACT = register("sorcery_clima_tact", ClimaTactItem::new,
			new Item.Properties().sword(ToolMaterial.IRON, 1.0f, -2.0f).rarity(Rarity.RARE));
	/** Buggy's throwing knives. See ThrowingKnifeItem. Buggy drops a handful. */
	public static final Item BUGGY_KNIFE = register("buggy_knife", ThrowingKnifeItem::new,
			new Item.Properties().stacksTo(16));

	private static Item gun(String name, GunItem.Hold hold, GunItem.Stats stats, int durability, Rarity rarity) {
		return register(name, properties -> new GunItem(stats, hold, properties),
				new Item.Properties().durability(durability).enchantable(10).rarity(rarity));
	}

	private static Item melee(String name, ToolMaterial material, float damage, float speed, Rarity rarity) {
		Item.Properties properties = new Item.Properties().sword(material, damage, speed).rarity(rarity);
		if (material == ToolMaterial.NETHERITE) {
			properties.fireResistant();
		}
		return register(name, Item::new, properties);
	}

	private static Item simple(String name, int stackSize, Rarity rarity) {
		return register(name, Item::new, new Item.Properties().stacksTo(stackSize).rarity(rarity));
	}

	private static Item register(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		ALL.add(item);
		return item;
	}

	// ---- Upgrades (see UpgradeItem and WeaponUpgrades) ----

	public static final Item SKILLFUL_WHETSTONE = upgrade("skillful_whetstone", UpgradeItem.Kind.SKILLFUL_WHETSTONE, Rarity.UNCOMMON);
	public static final Item GREAT_WHETSTONE = upgrade("great_whetstone", UpgradeItem.Kind.GREAT_WHETSTONE, Rarity.RARE);
	public static final Item SUPREME_WHETSTONE = upgrade("supreme_whetstone", UpgradeItem.Kind.SUPREME_WHETSTONE, Rarity.EPIC);
	public static final Item SCOPE = upgrade("scope", UpgradeItem.Kind.SCOPE, Rarity.UNCOMMON);
	public static final Item LONG_BARREL = upgrade("long_barrel", UpgradeItem.Kind.LONG_BARREL, Rarity.UNCOMMON);
	public static final Item HAIR_TRIGGER = upgrade("hair_trigger", UpgradeItem.Kind.HAIR_TRIGGER, Rarity.UNCOMMON);
	public static final Item FLAME_DIAL = upgrade("flame_dial", UpgradeItem.Kind.FLAME_DIAL, Rarity.RARE);
	public static final Item IMPACT_DIAL = upgrade("impact_dial", UpgradeItem.Kind.IMPACT_DIAL, Rarity.RARE);

	private static Item upgrade(String name, UpgradeItem.Kind kind, Rarity rarity) {
		return register(name, properties -> new UpgradeItem(kind, properties), new Item.Properties().stacksTo(16).rarity(rarity));
	}

	/** Loads this class, which registers everything above. */
	static void initialize() {
	}
}
