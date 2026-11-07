package com.onepiecemod.bounty;

import com.mojang.brigadier.arguments.LongArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.Items;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

/**
 * The /bounty chat commands:
 *   /bounty                     your bounty and how hard the Marines hunt you
 *   /bounty check <player>      someone else's bounty
 *   /bounty poster              print a Wanted Poster of yourself (costs 1 Paper in survival)
 *   /bounty set <player> <n>    cheat: set a bounty (needs cheats / operator)
 *   /bounty hunt                cheat: send a Marine squad at you right now (needs cheats / operator)
 *   /bounty hunters             cheat: send Devil Fruit bounty hunters at you right now (needs cheats / operator)
 *   /bounty raid                cheat: start a Navy raid where you stand (needs cheats / operator)
 *   /bounty raid stop           cheat: end your Navy raid
 */
public class BountyCommands {
	public static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("bounty")
						.executes(BountyCommands::info)
						.then(Commands.literal("check")
								.then(Commands.argument("player", EntityArgument.player()).executes(BountyCommands::check)))
						.then(Commands.literal("poster").executes(BountyCommands::poster))
						.then(Commands.literal("set")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.argument("player", EntityArgument.player())
										.then(Commands.argument("amount", LongArgumentType.longArg(0)).executes(BountyCommands::set))))
						.then(Commands.literal("hunt")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.executes(BountyCommands::hunt))
						.then(Commands.literal("hunters")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.executes(BountyCommands::hunters))
						.then(Commands.literal("raid")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.executes(BountyCommands::raid)
								.then(Commands.literal("stop").executes(BountyCommands::raidStop)))
		));
	}

	private static int info(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		long bounty = Bounty.get(player);
		int level = Bounty.threatLevel(bounty);
		player.sendSystemMessage(Component.literal("Your bounty: " + Bounty.format(bounty)).withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal("Threat level " + level + ": " + Bounty.levelName(level)).withStyle(ChatFormatting.YELLOW));
		player.sendSystemMessage(Component.literal(Bounty.levelDescription(level)).withStyle(ChatFormatting.GRAY));
		player.sendSystemMessage(Component.literal(NavyRaids.describe(level)).withStyle(ChatFormatting.GRAY));
		player.sendSystemMessage(Component.literal(BountyHunters.describe(level)).withStyle(ChatFormatting.GRAY));
		if (level > 0) {
			player.sendSystemMessage(Component.literal(NavyCalm.isHome(player)
					? "You're lying low at home: nobody comes for you within " + (int) NavyCalm.HOME_RADIUS + " blocks of your bed."
					: "Tip: nobody comes for you within " + (int) NavyCalm.HOME_RADIUS + " blocks of the bed you sleep in.")
					.withStyle(ChatFormatting.DARK_GREEN));
		}
		if (level == 0) {
			player.sendSystemMessage(Component.literal("Beat a boss to get your first bounty.").withStyle(ChatFormatting.GRAY));
		}
		return 1;
	}

	private static int check(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer target = EntityArgument.getPlayer(context, "player");
		long bounty = Bounty.get(target);
		context.getSource().sendSuccess(() -> Component.literal(target.getName().getString() + ": " + Bounty.format(bounty)
				+ " (" + Bounty.levelName(Bounty.threatLevel(bounty)) + ")").withStyle(ChatFormatting.GOLD), false);
		return 1;
	}

	private static int poster(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		if (Bounty.get(player) <= 0) {
			context.getSource().sendFailure(Component.literal("You don't have a bounty yet. Beat a boss first!"));
			return 0;
		}
		if (!player.isCreative()) {
			int slot = player.getInventory().findSlotMatchingItem(Items.PAPER.getDefaultInstance());
			if (slot < 0) {
				context.getSource().sendFailure(Component.literal("You need 1 Paper to print a poster."));
				return 0;
			}
			player.getInventory().removeItem(slot, 1);
		}
		BountyPosterItem.give(player);
		return 1;
	}

	private static int set(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer target = EntityArgument.getPlayer(context, "player");
		long amount = LongArgumentType.getLong(context, "amount");
		Bounty.set(target, amount);
		context.getSource().sendSuccess(() -> Component.literal(target.getName().getString() + "'s bounty is now "
				+ Bounty.format(amount) + " (" + Bounty.levelName(Bounty.threatLevel(amount)) + ")."), true);
		return 1;
	}

	private static int hunt(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		if (Bounty.get(player) <= 0) {
			context.getSource().sendFailure(Component.literal("You need a bounty first. Try /bounty set @s 100000000"));
			return 0;
		}
		if (!MarineHunters.forceHunt(player)) {
			context.getSource().sendFailure(Component.literal("No squad came. Either one is already chasing you, or there's no dry ground nearby."));
			return 0;
		}
		return 1;
	}

	private static int raid(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		String error = NavyRaids.start(player);
		if (error != null) {
			context.getSource().sendFailure(Component.literal(error));
			return 0;
		}
		return 1;
	}

	private static int raidStop(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		if (!NavyRaids.stop(player)) {
			context.getSource().sendFailure(Component.literal("No raid is running for you."));
			return 0;
		}
		context.getSource().sendSuccess(() -> Component.literal("The Navy raid is called off."), false);
		return 1;
	}

	private static int hunters(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		if (Bounty.get(player) <= 0) {
			context.getSource().sendFailure(Component.literal("You need a bounty first. Try /bounty set @s 500000000"));
			return 0;
		}
		if (BountyHunters.send(player) == 0) {
			context.getSource().sendFailure(Component.literal("No hunters came. Either some are already after you, or there's no dry ground nearby."));
			return 0;
		}
		return 1;
	}
}
