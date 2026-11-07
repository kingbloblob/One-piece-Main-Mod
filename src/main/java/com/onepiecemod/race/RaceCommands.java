package com.onepiecemod.race;

import java.util.Arrays;

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
 * The /race chat commands:
 *   /race                        show your race, its perks and drawbacks
 *   /race list                   show every race
 *   /race pick                   open the race picker again (only if you haven't picked yet)
 *   /race set <player> <race>    operators: change someone's race
 *   /race reset <player>         operators: forget someone's race, so the picker shows again
 */
public class RaceCommands {
	public static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("race")
						.executes(RaceCommands::info)
						.then(Commands.literal("list").executes(RaceCommands::list))
						.then(Commands.literal("pick").executes(RaceCommands::pick))
						.then(Commands.literal("set")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.argument("player", EntityArgument.player())
										.then(Commands.argument("race", StringArgumentType.word())
												.suggests((context, builder) -> SharedSuggestionProvider.suggest(
														Arrays.stream(Race.values()).map(race -> race.id), builder))
												.executes(RaceCommands::set))))
						.then(Commands.literal("reset")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.argument("player", EntityArgument.player()).executes(RaceCommands::reset)))
		));
	}

	private static int info(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		Race race = RaceAttachments.get(player);
		if (race == null) {
			player.sendSystemMessage(Component.literal("You haven't picked a race yet. Type /race pick.").withStyle(ChatFormatting.YELLOW));
			return 1;
		}
		player.sendSystemMessage(Component.literal("=== You are " + race.withArticle() + " ===")
				.withStyle(style -> style.withColor(TextColor.fromRgb(race.color))));
		player.sendSystemMessage(Component.literal(race.description).withStyle(ChatFormatting.GRAY));
		for (String perk : race.perks) {
			player.sendSystemMessage(Component.literal(" + " + perk).withStyle(ChatFormatting.GREEN));
		}
		for (String drawback : race.drawbacks) {
			player.sendSystemMessage(Component.literal(" - " + drawback).withStyle(ChatFormatting.RED));
		}
		if (race == Race.MINK) {
			player.sendSystemMessage(Sulong.describe(player));
		}
		return 1;
	}

	private static int list(CommandContext<CommandSourceStack> context) {
		for (Race race : Race.values()) {
			context.getSource().sendSystemMessage(Component.literal(race.displayName)
					.withStyle(style -> style.withColor(TextColor.fromRgb(race.color)))
					.append(Component.literal(": " + String.join(", ", race.perks)).withStyle(ChatFormatting.GRAY)));
		}
		return Race.values().length;
	}

	private static int pick(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		if (RaceAttachments.get(player) != null) {
			player.sendSystemMessage(Component.literal("You already picked your race. Only an operator can change it with /race reset.")
					.withStyle(ChatFormatting.RED));
			return 0;
		}
		RacePayloads.openPickerIfNeeded(player);
		return 1;
	}

	private static int set(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer target = EntityArgument.getPlayer(context, "player");
		Race race = Race.byId(StringArgumentType.getString(context, "race"));
		if (race == null) {
			context.getSource().sendFailure(Component.literal("Unknown race. Try one of: "
					+ String.join(", ", Arrays.stream(Race.values()).map(r -> r.id).toList())));
			return 0;
		}
		RacePerks.become(target, race);
		context.getSource().sendSuccess(() -> Component.literal(target.getName().getString() + " is now " + race.withArticle() + "."), true);
		return 1;
	}

	private static int reset(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer target = EntityArgument.getPlayer(context, "player");
		RaceAttachments.set(target, null);
		RacePerks.clear(target);
		RacePayloads.openPickerIfNeeded(target);
		context.getSource().sendSuccess(() -> Component.literal(target.getName().getString() + " can pick a new race."), true);
		return 1;
	}
}
