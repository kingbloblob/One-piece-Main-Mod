package com.onepiecemod.weapon;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.level.Level;

import com.onepiecemod.OnePieceMod;

/**
 * The One Piece enchantments. Their table data (cost, max level, which items) is in
 * data/onepiece/enchantment/*.json; what they do is code, in MeleeEffects and GunItem/Shot:
 *  - Seastone Edge (I-III): +2 damage per level to Devil Fruit users, 10% per level to weaken them.
 *  - Haki Coating (I-III): +1.5 damage per level while your Armament Haki is on.
 *  - Flying Slash (I-II, swords): fully charged swings send a cutting wave ahead.
 *  - Quick Draw (I-III, guns): 15% faster reload per level.
 *  - Sniper's Eye (I-III, guns): +25% range per level and steadier aim.
 */
public class WeaponEnchantments {
	public static final ResourceKey<Enchantment> SEASTONE_EDGE = key("seastone_edge");
	public static final ResourceKey<Enchantment> HAKI_COATING = key("haki_coating");
	public static final ResourceKey<Enchantment> FLYING_SLASH = key("flying_slash");
	public static final ResourceKey<Enchantment> QUICK_DRAW = key("quick_draw");
	public static final ResourceKey<Enchantment> SNIPERS_EYE = key("snipers_eye");

	private static ResourceKey<Enchantment> key(String name) {
		return ResourceKey.create(Registries.ENCHANTMENT, OnePieceMod.id(name));
	}

	/** The level of this enchantment on the item (0 if it doesn't have it). */
	public static int level(Level level, ItemStack stack, ResourceKey<Enchantment> enchantment) {
		return level(stack, enchantment);
	}

	/** Same, without needing the world: reads the enchantments stored on the item (so tooltips can use it too). */
	public static int level(ItemStack stack, ResourceKey<Enchantment> enchantment) {
		if (stack.isEmpty()) {
			return 0;
		}
		for (var entry : stack.getEnchantments().entrySet()) {
			if (entry.getKey().is(enchantment)) {
				return entry.getIntValue();
			}
		}
		return 0;
	}
}
