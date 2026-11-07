package com.onepiecemod.stats;

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
 * The /stats chat commands (the K key opens the same thing as a screen):
 *   /stats                          show your Pirate Level and stat tree
 *   /stats spend <stat>             spend a point, e.g. /stats spend strength
 *   /stats addxp <player> <amount>  operators: give training XP (handy for testing)
 *   /stats reset <player>           operators: hand back all of someone's points so they can spend them again
 */
public class StatsCommands {
	public static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("stats")
						.executes(StatsCommands::info)
						.then(Commands.literal("spend")
								.then(Commands.argument("stat", StringArgumentType.word())
										.suggests((context, builder) -> SharedSuggestionProvider.suggest(
												Arrays.stream(PlayerStat.values()).map(stat -> stat.id), builder))
										.executes(StatsCommands::spend)))
						.then(Commands.literal("respec").executes(context -> {
							StatRespec.respec(context.getSource().getPlayerOrException());
							return 1;
						}))
						.then(Commands.literal("addxp")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.argument("player", EntityArgument.player())
										.then(Commands.argument("amount", IntegerArgumentType.integer(1))
												.executes(StatsCommands::addXp))))
						.then(Commands.literal("reset")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.argument("player", EntityArgument.player()).executes(StatsCommands::reset)))
		));
	}

	private static int info(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		StatsData data = StatsAttachments.get(player);
		int level = data.level();
		String progress = level >= StatsData.MAX_LEVEL ? "max level"
				: data.xpIntoLevel() + "/" + StatsData.xpForNextLevel(level) + " XP to the next level";
		player.sendSystemMessage(Component.literal("=== Pirate Level " + level + " (" + progress + ") ===")
				.withStyle(ChatFormatting.GOLD));
		for (PlayerStat stat : PlayerStat.values()) {
			player.sendSystemMessage(Component.literal(stat.displayName + ": " + data.rank(stat) + "/" + PlayerStat.MAX_RANK)
					.withStyle(style -> style.withColor(TextColor.fromRgb(stat.color)))
					.append(Component.literal("  " + stat.perRank).withStyle(ChatFormatting.GRAY)));
		}
		player.sendSystemMessage(Component.literal(data.freePoints() + " stat points to spend. Press K or use /stats spend <stat>.")
				.withStyle(ChatFormatting.YELLOW));
		player.sendSystemMessage(Component.literal("Earn XP by beating mobs and bosses, taking hits, and sprinting or swimming.")
				.withStyle(ChatFormatting.GRAY));
		return 1;
	}

	private static int spend(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		PlayerStat stat = PlayerStat.byId(StringArgumentType.getString(context, "stat"));
		if (stat == null) {
			context.getSource().sendFailure(Component.literal("Unknown stat. Try strength, toughness, speed, stamina or swordsmanship."));
			return 0;
		}
		return StatTraining.spend(player, stat) ? 1 : 0;
	}

	private static int addXp(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer target = EntityArgument.getPlayer(context, "player");
		int amount = IntegerArgumentType.getInteger(context, "amount");
		StatTraining.addXp(target, amount, true);
		context.getSource().sendSuccess(() -> Component.literal("Gave " + target.getName().getString() + " " + amount
				+ " Pirate XP (now level " + StatsAttachments.get(target).level() + ")."), true);
		return 1;
	}

	private static int reset(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer target = EntityArgument.getPlayer(context, "player");
		StatsAttachments.set(target, StatsAttachments.get(target).withoutRanks());
		StatBonuses.apply(target);
		StatsPayloads.sync(target);
		target.sendSystemMessage(Component.literal("Your stat points were handed back. Press K to spend them again.")
				.withStyle(ChatFormatting.YELLOW));
		context.getSource().sendSuccess(() -> Component.literal("Reset " + target.getName().getString() + "'s stat tree."), true);
		return 1;
	}
}
