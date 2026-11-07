package com.onepiecemod.lifeskill;

import java.util.Arrays;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.TextColor;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

/**
 * /skills                                   your four life skills, with progress bars and the next perk
 * /skills info <skill>                      every perk of one skill, and which you have
 * /skills set <player> <skill> <level>      operators: set a level (testing)
 * /skills addxp <player> <skill> <amount>   operators: give XP
 */
final class LifeSkillCommands {
	private LifeSkillCommands() {
	}

	static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("skills")
						.executes(LifeSkillCommands::overview)
						.then(Commands.literal("info")
								.then(skillArgument().executes(LifeSkillCommands::info)))
						.then(Commands.literal("set")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.argument("player", EntityArgument.player())
										.then(skillArgument()
												.then(Commands.argument("level", IntegerArgumentType.integer(1, LifeSkill.MAX_LEVEL))
														.executes(LifeSkillCommands::set)))))
						.then(Commands.literal("addxp")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.argument("player", EntityArgument.player())
										.then(skillArgument()
												.then(Commands.argument("amount", IntegerArgumentType.integer(1))
														.executes(LifeSkillCommands::addXp)))))
		));
	}

	private static com.mojang.brigadier.builder.RequiredArgumentBuilder<CommandSourceStack, String> skillArgument() {
		return Commands.argument("skill", StringArgumentType.word())
				.suggests((context, builder) -> SharedSuggestionProvider.suggest(Arrays.stream(LifeSkill.values()).map(skill -> skill.id), builder));
	}

	private static LifeSkill skill(CommandContext<CommandSourceStack> context) {
		LifeSkill skill = LifeSkill.byId(StringArgumentType.getString(context, "skill"));
		if (skill == null) {
			context.getSource().sendFailure(Component.literal("Unknown skill. Try farming, mining, cooking or smithing."));
		}
		return skill;
	}

	private static String bar(int into, int needed) {
		int filled = needed <= 0 ? 10 : Math.min(10, into * 10 / needed);
		return "[" + "|".repeat(filled) + ".".repeat(10 - filled) + "]";
	}

	private static int overview(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		LifeSkillData data = LifeSkills.data(player);
		player.sendSystemMessage(Component.literal("=== Life Skills ===").withStyle(ChatFormatting.GOLD));
		for (LifeSkill skill : LifeSkill.values()) {
			int level = data.level(skill);
			String progress = level >= LifeSkill.MAX_LEVEL ? "MAX"
					: bar(data.xpIntoLevel(skill), LifeSkillData.xpForNextLevel(level)) + " "
					+ data.xpIntoLevel(skill) + "/" + LifeSkillData.xpForNextLevel(level);
			LifeSkill.Milestone next = null;
			for (LifeSkill.Milestone milestone : skill.milestones) {
				if (milestone.level() > level) {
					next = milestone;
					break;
				}
			}
			String nextText = next == null ? "  all perks unlocked" : "  next: " + next.name() + " at " + next.level();
			player.sendSystemMessage(Component.literal(skill.displayName + " " + level + " ")
					.withStyle(style -> style.withColor(TextColor.fromRgb(skill.color)))
					.append(Component.literal(progress).withStyle(ChatFormatting.WHITE))
					.append(Component.literal(nextText).withStyle(ChatFormatting.GRAY)));
		}
		player.sendSystemMessage(Component.literal("Farm grown crops, mine ores, cook food and craft gear to level up. /skills info <skill> for perks.")
				.withStyle(ChatFormatting.GRAY));
		return 1;
	}

	private static int info(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		LifeSkill skill = skill(context);
		if (skill == null) {
			return 0;
		}
		int level = LifeSkills.level(player, skill);
		player.sendSystemMessage(Component.literal("=== " + skill.displayName + " " + level + "/" + LifeSkill.MAX_LEVEL + " ===")
				.withStyle(style -> style.withColor(TextColor.fromRgb(skill.color))));
		player.sendSystemMessage(Component.literal(skill.levelBonus).withStyle(ChatFormatting.WHITE));
		for (LifeSkill.Milestone milestone : skill.milestones) {
			boolean have = level >= milestone.level();
			player.sendSystemMessage(Component.literal((have ? "[x] " : "[ ] ") + milestone.level() + " " + milestone.name() + ": ")
					.withStyle(have ? ChatFormatting.GREEN : ChatFormatting.DARK_GRAY)
					.append(Component.literal(milestone.description()).withStyle(ChatFormatting.GRAY)));
		}
		return 1;
	}

	private static int set(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer target = EntityArgument.getPlayer(context, "player");
		LifeSkill skill = skill(context);
		if (skill == null) {
			return 0;
		}
		int level = IntegerArgumentType.getInteger(context, "level");
		LifeSkills.setLevel(target, skill, level);
		context.getSource().sendSuccess(() -> Component.literal("Set " + target.getName().getString() + "'s "
				+ skill.displayName + " to " + level + "."), true);
		return 1;
	}

	private static int addXp(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer target = EntityArgument.getPlayer(context, "player");
		LifeSkill skill = skill(context);
		if (skill == null) {
			return 0;
		}
		int amount = IntegerArgumentType.getInteger(context, "amount");
		LifeSkills.addXpForced(target, skill, amount);
		context.getSource().sendSuccess(() -> Component.literal("Gave " + target.getName().getString() + " " + amount + " "
				+ skill.displayName + " XP (now " + LifeSkills.level(target, skill) + ")."), true);
		return 1;
	}
}
