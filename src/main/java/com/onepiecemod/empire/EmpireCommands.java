package com.onepiecemod.empire;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

/**
 * The /empire chat commands:
 *   /empire                    your title, your kingdoms, and what you need for the next title
 *   /empire set <title>        (ops, for testing) none, emperor, pirate_king or king_of_the_world
 *   /empire bustercall [stop]  (ops, for testing) call a Buster Call on yourself right now
 */
public class EmpireCommands {
	public static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("empire")
						.executes(EmpireCommands::info)
						.then(Commands.literal("set")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.argument("title", StringArgumentType.word())
										.suggests((context, builder) -> {
											for (Title title : Title.values()) {
												builder.suggest(title.name().toLowerCase());
											}
											return builder.buildFuture();
										})
										.executes(EmpireCommands::set)))
						.then(Commands.literal("bustercall")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.executes(context -> {
									String problem = BusterCall.start(context.getSource().getPlayerOrException());
									if (problem != null) {
										context.getSource().sendFailure(Component.literal(problem));
									}
									return 1;
								})
								.then(Commands.literal("stop").executes(context -> {
									boolean stopped = BusterCall.stop(context.getSource().getPlayerOrException());
									context.getSource().sendSystemMessage(Component.literal(stopped ? "Buster Call called off." : "No Buster Call running."));
									return 1;
								})))
		));
	}

	private static int info(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		Title title = EmpireData.title(player);
		EmpireRanks.forgetMissingFlags(player);
		player.sendSystemMessage(Component.literal("=== Your empire ===").withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal("Title: " + title.displayName).withStyle(title.color));
		player.sendSystemMessage(Component.literal("Kingdoms: " + EmpireData.kingdoms(player).size() + " of " + title.maxKingdoms
				+ ". Loot bonus: +" + (int) (title.lootBonus * 100) + "%. Taxes: " + title.taxPerDay + " Berries a day per kingdom."));
		if (title != Title.NONE) {
			player.sendSystemMessage(Component.literal("The Navy comes " + title.navyChance + "x as often, and Buster Calls can strike.")
					.withStyle(ChatFormatting.DARK_AQUA));
		}
		Title next = title.next();
		if (next == null) {
			player.sendSystemMessage(Component.literal("You rule the world. There is nothing left to conquer.").withStyle(ChatFormatting.DARK_PURPLE));
			return 1;
		}
		player.sendSystemMessage(Component.literal("To become " + next.displayName + ":").withStyle(next.color));
		for (EmpireRanks.Requirement requirement : EmpireRanks.requirements(player, next)) {
			player.sendSystemMessage(Component.literal((requirement.done() ? " [x] " : " [ ] ") + requirement.text())
					.withStyle(requirement.done() ? ChatFormatting.GREEN : ChatFormatting.GRAY));
		}
		return 1;
	}

	private static int set(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		String name = StringArgumentType.getString(context, "title");
		for (Title title : Title.values()) {
			if (title.name().equalsIgnoreCase(name)) {
				EmpireData.setTitle(player, title);
				context.getSource().sendSystemMessage(Component.literal("Your title is now " + title.displayName + "."));
				return 1;
			}
		}
		context.getSource().sendFailure(Component.literal("Unknown title. Use none, emperor, pirate_king or king_of_the_world."));
		return 0;
	}
}
