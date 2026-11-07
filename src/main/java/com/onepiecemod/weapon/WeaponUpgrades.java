package com.onepiecemod.weapon;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.resources.Identifier;
import net.minecraft.tags.ItemTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ItemAttributeModifiers;

import com.onepiecemod.OnePieceMod;

/**
 * Upgrades stored on a weapon: sword grades, gun parts and Skypiea Dials.
 * They are saved on the item itself (as "data components"), so an upgraded sword keeps its grade
 * when you drop it, trade it or put it in a chest. UpgradeItem.java applies them.
 */
public class WeaponUpgrades {
	/** 0 = ungraded, 1 = Skillful, 2 = Great, 3 = Supreme. */
	public static final DataComponentType<Integer> SWORD_GRADE = component("sword_grade");
	/** Which gun parts are fitted, as bits: 1 = Scope, 2 = Long Barrel, 4 = Hair Trigger. */
	public static final DataComponentType<Integer> GUN_PARTS = component("gun_parts");
	/** 0 = no Dial, 1 = Flame Dial, 2 = Impact Dial. */
	public static final DataComponentType<Integer> DIAL = component("dial");

	/** Rounds left in a gun's magazine. Missing = full. Changing it doesn't replay the "pull out" animation. */
	public static final DataComponentType<Integer> ROUNDS = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE, OnePieceMod.id("rounds"),
			DataComponentType.<Integer>builder().persistent(Codec.INT).networkSynchronized(ByteBufCodecs.VAR_INT).ignoreSwapAnimation().build());

	public static final int SCOPE = 1;
	public static final int LONG_BARREL = 2;
	public static final int HAIR_TRIGGER = 4;

	public static final int FLAME_DIAL = 1;
	public static final int IMPACT_DIAL = 2;

	public static final String[] GRADE_NAMES = {"Ungraded", "Skillful Grade (Ryo Wazamono)", "Great Grade (O Wazamono)", "Supreme Grade (Saijo O Wazamono)"};
	/** Extra attack damage each grade gives over an ungraded sword. */
	private static final double[] GRADE_BONUS = {0.0, 1.0, 2.5, 4.0};
	private static final Identifier GRADE_MODIFIER = OnePieceMod.id("sword_grade");

	/** The grade a famous blade already has in the story. Upgrading it only adds the difference. */
	private static final Map<String, Integer> CANON_GRADES = Map.ofEntries(
			Map.entry("sandai_kitetsu", 1), Map.entry("shigure", 1), Map.entry("soul_solid", 1),
			Map.entry("wado_ichimonji", 2), Map.entry("shusui", 2), Map.entry("enma", 2), Map.entry("kikoku", 2),
			Map.entry("ame_no_habakiri", 2),
			Map.entry("yoru", 3), Map.entry("shodai_kitetsu", 3),
			Map.entry("ace", 3)); // Ace's grade is never said in the story; as Roger's sword it is treated as Supreme.

	private static DataComponentType<Integer> component(String name) {
		return Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE, OnePieceMod.id(name),
				DataComponentType.<Integer>builder().persistent(Codec.INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());
	}

	/** Loads this class, which registers the components above. */
	static void initialize() {
	}

	// ---- Sword grades ----

	public static boolean isSword(ItemStack stack) {
		return stack.is(ItemTags.SWORDS);
	}

	public static int canonGrade(ItemStack stack) {
		Identifier id = BuiltInRegistries.ITEM.getKey(stack.getItem());
		return id.getNamespace().equals(OnePieceMod.MOD_ID) ? CANON_GRADES.getOrDefault(id.getPath(), 0) : 0;
	}

	public static int grade(ItemStack stack) {
		return Math.max(stack.getOrDefault(SWORD_GRADE, 0), canonGrade(stack));
	}

	/** Sets the grade and swaps the sword's bonus damage for the new grade's. */
	public static void setGrade(ItemStack stack, int grade) {
		stack.set(SWORD_GRADE, grade);
		double bonus = GRADE_BONUS[grade] - GRADE_BONUS[canonGrade(stack)];
		ItemAttributeModifiers old = stack.getOrDefault(DataComponents.ATTRIBUTE_MODIFIERS, ItemAttributeModifiers.EMPTY);
		List<ItemAttributeModifiers.Entry> entries = new ArrayList<>();
		for (ItemAttributeModifiers.Entry entry : old.modifiers()) {
			if (!entry.modifier().is(GRADE_MODIFIER)) {
				entries.add(entry);
			}
		}
		ItemAttributeModifiers updated = new ItemAttributeModifiers(entries);
		if (bonus > 0) {
			updated = updated.withModifierAdded(Attributes.ATTACK_DAMAGE,
					new AttributeModifier(GRADE_MODIFIER, bonus, AttributeModifier.Operation.ADD_VALUE), EquipmentSlotGroup.MAINHAND);
		}
		stack.set(DataComponents.ATTRIBUTE_MODIFIERS, updated);
	}

	// ---- Gun parts and Dials ----

	public static boolean hasPart(ItemStack stack, int part) {
		return (stack.getOrDefault(GUN_PARTS, 0) & part) != 0;
	}

	public static int dial(ItemStack stack) {
		return stack.getOrDefault(DIAL, 0);
	}

	/** Weapons other mods add to #onepiece:holds_dial, like One Piece Arsenal's jitte and spear. */
	public static final TagKey<Item> HOLDS_DIAL = TagKey.create(Registries.ITEM, OnePieceMod.id("holds_dial"));

	/** Swords, axes, the mod's melee weapons, guns and anything in #onepiece:holds_dial can hold a Dial. */
	public static boolean canHoldDial(ItemStack stack) {
		return stack.is(ItemTags.SWORDS) || stack.is(ItemTags.AXES) || stack.is(HOLDS_DIAL) || stack.getItem() instanceof GunItem
				|| (stack.getItem() != WeaponItems.BUGGY_KNIFE && WeaponItems.ALL.contains(stack.getItem())
						&& Ammo.of(stack) == null);
	}

	/** The lines shown on a weapon's tooltip. Empty if it has no upgrades. */
	public static List<Component> describe(ItemStack stack) {
		List<Component> lines = new ArrayList<>();
		if (isSword(stack) && grade(stack) > 0) {
			lines.add(Component.literal(GRADE_NAMES[grade(stack)]).withStyle(grade(stack) == 3 ? ChatFormatting.GOLD : ChatFormatting.AQUA));
		}
		lines.addAll(BlackBlades.describe(stack));
		if (hasPart(stack, SCOPE)) {
			lines.add(Component.literal("Scope: +50% range, steadier aim").withStyle(ChatFormatting.BLUE));
		}
		if (hasPart(stack, LONG_BARREL)) {
			lines.add(Component.literal("Long Barrel: +3 damage").withStyle(ChatFormatting.BLUE));
		}
		if (hasPart(stack, HAIR_TRIGGER)) {
			lines.add(Component.literal("Hair Trigger: 30% faster reload").withStyle(ChatFormatting.BLUE));
		}
		if (dial(stack) == FLAME_DIAL) {
			lines.add(Component.literal("Flame Dial: sets targets on fire").withStyle(ChatFormatting.RED));
		} else if (dial(stack) == IMPACT_DIAL) {
			lines.add(Component.literal("Impact Dial: huge knockback").withStyle(ChatFormatting.LIGHT_PURPLE));
		}
		return lines;
	}
}
