package com.onepiecemod.weapon;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.EquipmentSlotGroup;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ItemAttributeModifiers;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.haki.HakiPowers;

/**
 * Black Blades (kokuto). In the story, a sword turns black for good when a master swordsman fights
 * with it coated in Armament Haki for a very long time (Ryuma's Shusui, Mihawk's Yoru).
 *
 * In the mod: fight with a Great Grade or better sword while Armament Haki is on. Every hit that
 * lands tempers the blade a little. After 1,500 such hits it becomes a Black Blade for good:
 * +2 attack damage on top of its grade, and the item keeps it when traded or stored.
 * The tooltip shows how far along the tempering is. Shusui, Yoru and the Kokuto Blade are black already.
 */
public class BlackBlades {
	public static final int HITS_NEEDED = 1500;
	private static final double BONUS = 2.0;
	private static final Identifier MODIFIER = OnePieceMod.id("black_blade");
	/** Blades the story already made black. */
	private static final Set<String> CANON_BLACK = Set.of("shusui", "yoru", "kokuto_blade");

	/** Armament-coated hits landed with this sword so far. */
	public static final DataComponentType<Integer> TEMPER = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE, OnePieceMod.id("haki_temper"),
			DataComponentType.<Integer>builder().persistent(Codec.INT).networkSynchronized(ByteBufCodecs.VAR_INT).ignoreSwapAnimation().build());
	/** Present (true) once the sword has turned black. */
	public static final DataComponentType<Boolean> BLACK = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE, OnePieceMod.id("black_blade"),
			DataComponentType.<Boolean>builder().persistent(Codec.BOOL).networkSynchronized(ByteBufCodecs.BOOL).build());

	static void initialize() {
		ServerLivingEntityEvents.AFTER_DAMAGE.register((entity, source, baseDamageTaken, damageTaken, blocked) -> {
			if (blocked || damageTaken <= 0 || !(source.getEntity() instanceof ServerPlayer player)
					|| source.getDirectEntity() != player || entity == player) {
				return;
			}
			ItemStack sword = player.getMainHandItem();
			if (!WeaponUpgrades.isSword(sword) || isBlack(sword) || WeaponUpgrades.grade(sword) < 2
					|| !HakiPowers.hasArmamentActive(player)) {
				return;
			}
			temper(player, sword);
		});
	}

	public static boolean isBlack(ItemStack stack) {
		if (Boolean.TRUE.equals(stack.get(BLACK))) {
			return true;
		}
		Identifier id = BuiltInRegistries.ITEM.getKey(stack.getItem());
		return id.getNamespace().equals(OnePieceMod.MOD_ID) && CANON_BLACK.contains(id.getPath());
	}

	private static void temper(ServerPlayer player, ItemStack sword) {
		int hits = sword.getOrDefault(TEMPER, 0) + 1;
		if (hits < HITS_NEEDED) {
			sword.set(TEMPER, hits);
			if (hits % (HITS_NEEDED / 4) == 0) {
				player.sendSystemMessage(Component.literal("Your Haki is soaking into the blade... " + hits * 100 / HITS_NEEDED + "% tempered.")
						.withStyle(ChatFormatting.DARK_GRAY));
			}
			return;
		}
		sword.remove(TEMPER);
		sword.set(BLACK, true);
		ItemAttributeModifiers modifiers = sword.getOrDefault(DataComponents.ATTRIBUTE_MODIFIERS, ItemAttributeModifiers.EMPTY)
				.withModifierAdded(Attributes.ATTACK_DAMAGE, new AttributeModifier(MODIFIER, BONUS, AttributeModifier.Operation.ADD_VALUE),
						EquipmentSlotGroup.MAINHAND);
		sword.set(DataComponents.ATTRIBUTE_MODIFIERS, modifiers);
		ServerLevel level = (ServerLevel) player.level();
		level.sendParticles(ParticleTypes.SQUID_INK, player.getX(), player.getY() + 1.2, player.getZ(), 40, 0.5, 0.6, 0.5, 0.05);
		level.playSound(null, player.blockPosition(), SoundEvents.ANVIL_USE, SoundSource.PLAYERS, 1.0f, 0.6f);
		player.sendSystemMessage(Component.literal("Your sword has turned black! It is a Black Blade now (+" + (int) BONUS + " attack damage).")
				.withStyle(ChatFormatting.DARK_PURPLE, ChatFormatting.BOLD));
		com.onepiecemod.advancement.AdvancementFeature.grant(player, "powers/black_blade");
	}

	/** Tooltip lines: "Black Blade", or the tempering progress on a Great Grade+ sword. */
	static List<Component> describe(ItemStack stack) {
		List<Component> lines = new ArrayList<>();
		if (!WeaponUpgrades.isSword(stack)) {
			return lines;
		}
		if (isBlack(stack)) {
			lines.add(Component.literal("Black Blade (Kokuto)").withStyle(ChatFormatting.DARK_PURPLE));
		} else if (stack.has(TEMPER)) {
			lines.add(Component.literal("Haki tempering: " + stack.getOrDefault(TEMPER, 0) + "/" + HITS_NEEDED).withStyle(ChatFormatting.DARK_GRAY));
		} else if (WeaponUpgrades.grade(stack) >= 2) {
			lines.add(Component.literal("Fight with Armament Haki on to temper it into a Black Blade").withStyle(ChatFormatting.DARK_GRAY));
		}
		return lines;
	}
}
