package com.onepiecemod.lifeskill;

import java.util.HashMap;
import java.util.Map;

import net.minecraft.ChatFormatting;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.TextColor;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;

/**
 * Life skills: Farming, Mining, Cooking and Smithing. This class is the public API other features use.
 *
 * Reading levels (to gate a recipe, an ore, a quest...):
 *   LifeSkills.level(player, LifeSkill.MINING)                       -> 1..50
 *   LifeSkills.has(player, LifeSkill.SMITHING, 25)                   -> true/false
 *   LifeSkills.require(player, LifeSkill.FARMING, 15, "plant Sea Cherries") -> false + a red message if too low
 *
 * Giving XP (quest rewards, custom machines):
 *   LifeSkills.addXp(player, LifeSkill.COOKING, 20)
 *
 * Making new content count, with no edit to this package:
 *   - Data only: add a block to data/onepiece/tags/block/life_skill/mining.json or farming.json,
 *     or an item to data/onepiece/tags/item/life_skill/cooking.json or smithing.json. It then gives the default XP.
 *     Items in data/onepiece/tags/item/life_skill/no_xp.json never give craft XP (stops craft/uncraft loops).
 *   - Java, with your own XP amount: LifeSkills.registerBlock(MY_ORE, LifeSkill.MINING, 9)
 *     or LifeSkills.registerCraft(MY_DISH, LifeSkill.COOKING, 12). Call it from your feature's initialize().
 *
 * Crops only count once fully grown (any block with an "age" property must be at its max age).
 * Ores mined with Silk Touch give no XP, so you can't place and re-mine one forever.
 */
public final class LifeSkills {
	public static final AttachmentType<LifeSkillData> DATA = AttachmentRegistry.create(
			OnePieceMod.id("life_skills"),
			builder -> builder
					.persistent(LifeSkillData.CODEC)
					.copyOnDeath()
	);

	public static final TagKey<Block> FARMING_BLOCKS = TagKey.create(Registries.BLOCK, OnePieceMod.id("life_skill/farming"));
	public static final TagKey<Block> MINING_BLOCKS = TagKey.create(Registries.BLOCK, OnePieceMod.id("life_skill/mining"));
	public static final TagKey<Item> COOKING_ITEMS = TagKey.create(Registries.ITEM, OnePieceMod.id("life_skill/cooking"));
	public static final TagKey<Item> SMITHING_ITEMS = TagKey.create(Registries.ITEM, OnePieceMod.id("life_skill/smithing"));
	public static final TagKey<Item> NO_XP_ITEMS = TagKey.create(Registries.ITEM, OnePieceMod.id("life_skill/no_xp"));

	/** Default XP for a tagged crop, ore, food or piece of gear that has no registered amount. */
	public static final int DEFAULT_CROP_XP = 3;
	public static final int DEFAULT_ORE_XP = 4;
	public static final int DEFAULT_FOOD_XP = 2;
	public static final int DEFAULT_GEAR_XP = 5;

	/** Pirate XP for each life skill level gained: 5 + the new level. All four skills to 50 = about 6,100 Pirate XP. */
	private static final int PIRATE_XP_BASE = 5;

	private static final Map<Block, Entry> BLOCK_XP = new HashMap<>();
	private static final Map<Item, Entry> CRAFT_XP = new HashMap<>();

	public record Entry(LifeSkill skill, int xp) {
	}

	private LifeSkills() {
	}

	// ---- Reading ----

	public static LifeSkillData data(Player player) {
		LifeSkillData data = player.getAttached(DATA);
		return data != null ? data : LifeSkillData.EMPTY;
	}

	public static int level(Player player, LifeSkill skill) {
		return data(player).level(skill);
	}

	public static boolean has(Player player, LifeSkill skill, int level) {
		return level(player, skill) >= level;
	}

	/** True if the player has the level. If not, tells them what they need (above the hotbar) and returns false. */
	public static boolean require(ServerPlayer player, LifeSkill skill, int level, String action) {
		if (has(player, skill, level)) {
			return true;
		}
		player.sendOverlayMessage(Component.literal("You need " + skill.displayName + " " + level + " to " + action
				+ " (you are " + level(player, skill) + ").").withStyle(ChatFormatting.RED));
		return false;
	}

	/** Chance (0..1) of the skill's per-level bonus: double harvest, double ore drops, or an extra portion. */
	public static double bonusChance(Player player, LifeSkill skill) {
		int level = level(player, skill);
		return switch (skill) {
			case FARMING, COOKING -> level * 0.005;
			case MINING -> level * 0.004;
			case SMITHING -> 0;
		};
	}

	// ---- Registering content ----

	/** Breaking this block (a grown crop, or an ore without Silk Touch) gives this XP. */
	public static void registerBlock(Block block, LifeSkill skill, int xp) {
		BLOCK_XP.put(block, new Entry(skill, xp));
	}

	/** Crafting, smelting or station-making this item gives this XP for each one made. */
	public static void registerCraft(Item item, LifeSkill skill, int xp) {
		CRAFT_XP.put(item, new Entry(skill, xp));
	}

	public static Entry blockEntry(Block block) {
		return BLOCK_XP.get(block);
	}

	public static Entry craftEntry(Item item) {
		return CRAFT_XP.get(item);
	}

	// ---- Giving XP ----

	/** Adds XP to a skill. Announces level-ups and milestones, and gives a little Pirate XP per level. */
	public static void addXp(ServerPlayer player, LifeSkill skill, int amount) {
		if (player.isCreative() || player.isSpectator()) {
			return; // Creative players can place and break anything, so they don't train.
		}
		addXpForced(player, skill, amount);
	}

	/** Like addXp, but also works in Creative (op commands, testing). */
	public static void addXpForced(ServerPlayer player, LifeSkill skill, int amount) {
		if (amount <= 0) {
			return;
		}
		LifeSkillData before = data(player);
		int oldLevel = before.level(skill);
		LifeSkillData after = before.withXp(skill, (int) Math.min(Integer.MAX_VALUE, (long) before.xp(skill) + amount));
		player.setAttached(DATA, after);
		int newLevel = after.level(skill);

		if (newLevel > oldLevel) {
			for (int level = oldLevel + 1; level <= newLevel; level++) {
				levelUp(player, skill, level);
			}
		} else {
			String progress = newLevel >= LifeSkill.MAX_LEVEL ? "max"
					: after.xpIntoLevel(skill) + "/" + LifeSkillData.xpForNextLevel(newLevel);
			player.sendOverlayMessage(Component.literal("+" + amount + " " + skill.displayName + " XP (" + progress + ")")
					.withStyle(style -> style.withColor(TextColor.fromRgb(skill.color))));
		}
	}

	private static void levelUp(ServerPlayer player, LifeSkill skill, int level) {
		player.sendSystemMessage(Component.literal(skill.displayName + " " + level + "!")
				.withStyle(style -> style.withColor(TextColor.fromRgb(skill.color)).withBold(true)));
		LifeSkill.Milestone milestone = skill.milestoneAt(level);
		if (milestone != null) {
			player.sendSystemMessage(Component.literal("Unlocked " + milestone.name() + ": ")
					.withStyle(style -> style.withColor(TextColor.fromRgb(0xFFD75E)))
					.append(Component.literal(milestone.description()).withStyle(ChatFormatting.GRAY)));
			player.level().playSound(null, player.blockPosition(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 0.6f, 1.0f);
		} else {
			player.level().playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.5f, 1.4f);
		}
		com.onepiecemod.stats.StatTraining.addXp(player, PIRATE_XP_BASE + level, false);
	}

	/** Op/testing: sets a skill straight to a level. */
	public static void setLevel(ServerPlayer player, LifeSkill skill, int level) {
		level = Math.max(1, Math.min(LifeSkill.MAX_LEVEL, level));
		player.setAttached(DATA, data(player).withXp(skill, LifeSkillData.totalXpForLevel(level)));
	}

	static Identifier id(Block block) {
		return BuiltInRegistries.BLOCK.getKey(block);
	}

	public static void initialize() {
		LifeSkillDefaults.register();
		LifeSkillHooks.initialize();
		LifeSkillCommands.initialize();
	}
}
