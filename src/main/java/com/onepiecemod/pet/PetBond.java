package com.onepiecemod.pet;

import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;

import com.onepiecemod.OnePieceMod;

/**
 * Bond levels: a tamed pet grows closer to you the more you do together.
 * - Fighting: +3 for each kill it makes (+10 for a big one, 100+ health).
 * - Riding: +1 for every 30 seconds you ride it.
 * - Feeding it its favourite food: +1 (at most once a minute).
 * Each level past 1 gives it +6% health and +5% attack. At level 5 its ability gets stronger,
 * at level 10 it's a Legendary partner.
 */
public final class PetBond {
	public static final int MAX_LEVEL = 10;
	/** Level at which a pet's ability gets its stronger form. */
	public static final int EMPOWERED_LEVEL = 5;

	private static final Identifier HEALTH_BONUS = OnePieceMod.id("pet_bond_health");
	private static final Identifier ATTACK_BONUS = OnePieceMod.id("pet_bond_attack");

	private PetBond() {
	}

	/** Total bond points needed to reach a level: 0, 20, 60, 120, ... 900 for level 10. */
	public static int pointsFor(int level) {
		return 10 * level * (level - 1);
	}

	public static int level(Pet pet) {
		int bond = pet.getBond();
		int level = 1;
		while (level < MAX_LEVEL && bond >= pointsFor(level + 1)) {
			level++;
		}
		return level;
	}

	public static boolean empowered(Pet pet) {
		return level(pet) >= EMPOWERED_LEVEL;
	}

	/** "Bond 3 (45/60)" or "Bond 10 Legendary". */
	public static String describe(Pet pet) {
		int level = level(pet);
		return level >= MAX_LEVEL ? "Bond 10 Legendary" : "Bond " + level + " (" + pet.getBond() + "/" + pointsFor(level + 1) + ")";
	}

	/** Adds bond points; tells the owner and makes the pet stronger when it reaches a new level. */
	public static void add(Mob mob, int points) {
		Pet pet = (Pet) mob;
		if (!pet.isTamed() || points <= 0 || !(mob.level() instanceof ServerLevel level)) {
			return;
		}
		int before = level(pet);
		pet.setBond(Math.min(pointsFor(MAX_LEVEL) + 100, pet.getBond() + points));
		int after = level(pet);
		if (after <= before) {
			return;
		}
		applyBonuses(mob);
		mob.heal(mob.getMaxHealth());
		level.sendParticles(ParticleTypes.HEART, mob.getX(), mob.getY() + mob.getBbHeight(), mob.getZ(), 10,
				mob.getBbWidth() * 0.5, 0.4, mob.getBbWidth() * 0.5, 0.02);
		LivingEntity owner = Pets.ownerOf(pet, level);
		if (owner instanceof ServerPlayer player) {
			String text = " and you grew closer! Bond level " + after + ".";
			if (after == EMPOWERED_LEVEL) {
				text += " Its ability " + PetAbilities.name(mob) + " is stronger now.";
			} else if (after == MAX_LEVEL) {
				text += " A Legendary partner!";
			}
			player.sendSystemMessage(Component.empty().append(mob.getName()).append(text).withStyle(ChatFormatting.LIGHT_PURPLE));
			if (after == MAX_LEVEL) {
				com.onepiecemod.advancement.AdvancementFeature.grant(player, "wonders/legendary_partner");
			}
		}
	}

	/** Sets the health and attack bonus for the pet's bond level (saved with the entity, so this only runs on level up). */
	public static void applyBonuses(Mob mob) {
		int bonusLevels = level((Pet) mob) - 1;
		AttributeInstance health = mob.getAttribute(Attributes.MAX_HEALTH);
		if (health != null) {
			health.addOrReplacePermanentModifier(new AttributeModifier(HEALTH_BONUS, 0.06 * bonusLevels,
					AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
		}
		AttributeInstance attack = mob.getAttribute(Attributes.ATTACK_DAMAGE);
		if (attack != null) {
			attack.addOrReplacePermanentModifier(new AttributeModifier(ATTACK_BONUS, 0.05 * bonusLevels,
					AttributeModifier.Operation.ADD_MULTIPLIED_BASE));
		}
	}
}
