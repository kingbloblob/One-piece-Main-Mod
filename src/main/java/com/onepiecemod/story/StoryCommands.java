package com.onepiecemod.story;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;

import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

import com.onepiecemod.character.SeaChartItem;

/**
 * The /story chat commands:
 *   /story                         your chapter and goals (same as right-clicking the Captain's Log)
 *   /story chart                   a new Sea Chart for your chapter (costs 1 Paper in survival)
 *   /story log                     a new Captain's Log, if you lost yours
 *   /story chapters                every chapter, with the ones you've done ticked
 *   /story set <player> <chapter>  cheat: jump to a chapter (1 to 26), for testing
 *   /story gates on|off            operator: turn the story gates on or off for this world
 */
public class StoryCommands {
	public static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("story")
						.executes(StoryCommands::log)
						.then(Commands.literal("chart").executes(StoryCommands::chart))
						.then(Commands.literal("log").executes(StoryCommands::newLog))
						.then(Commands.literal("chapters").executes(StoryCommands::chapters))
						.then(Commands.literal("set")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.argument("player", EntityArgument.player())
										.then(Commands.argument("chapter", IntegerArgumentType.integer(1, StoryData.chapters().size() + 1))
												.executes(StoryCommands::set))))
						.then(Commands.literal("gates")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.literal("on").executes(context -> gates(context, true)))
								.then(Commands.literal("off").executes(context -> gates(context, false))))
		));
	}

	private static int log(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		StoryTracker.showLog(context.getSource().getPlayerOrException());
		return 1;
	}

	private static int chart(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		if (StoryTracker.currentCharts(player).isEmpty()) {
			context.getSource().sendFailure(Component.literal("This chapter has no Sea Chart. Check your Captain's Log for where to go."));
			return 0;
		}
		if (!player.isCreative()) {
			int slot = player.getInventory().findSlotMatchingItem(net.minecraft.world.item.Items.PAPER.getDefaultInstance());
			if (slot < 0) {
				context.getSource().sendFailure(Component.literal("You need 1 Paper to copy the chart."));
				return 0;
			}
			player.getInventory().removeItem(slot, 1);
		}
		for (String place : StoryTracker.currentCharts(player)) {
			StoryTracker.give(player, SeaChartItem.forTarget(place));
		}
		return 1;
	}

	private static int newLog(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		if (player.getInventory().countItem(StoryFeature.CAPTAINS_LOG) > 0) {
			context.getSource().sendFailure(Component.literal("You already have a Captain's Log."));
			return 0;
		}
		StoryTracker.give(player, new ItemStack(StoryFeature.CAPTAINS_LOG));
		return 1;
	}

	private static int chapters(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		int current = StoryProgress.orStart(player).chapter();
		StoryData.Saga saga = null;
		for (StoryData.Chapter chapter : StoryData.chapters()) {
			if (chapter.saga != saga) {
				saga = chapter.saga;
				player.sendSystemMessage(Component.literal(saga.title).withStyle(net.minecraft.ChatFormatting.GOLD));
			}
			String mark = chapter.index < current ? " ✔ " : chapter.index == current ? " ➤ " : " • ";
			player.sendSystemMessage(Component.literal(mark + (chapter.index + 1) + ". " + chapter.title)
					.withStyle(chapter.index == current ? net.minecraft.ChatFormatting.YELLOW : net.minecraft.ChatFormatting.GRAY));
		}
		return 1;
	}

	private static int set(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer target = EntityArgument.getPlayer(context, "player");
		int chapter = IntegerArgumentType.getInteger(context, "chapter");
		StoryTracker.startChapter(target, chapter - 1);
		context.getSource().sendSuccess(() -> Component.literal(target.getName().getString() + " is now on chapter " + chapter + "."), true);
		return 1;
	}

	private static int gates(CommandContext<CommandSourceStack> context, boolean on) {
		StoryGates.setGatesOff(context.getSource().getServer(), !on);
		context.getSource().sendSuccess(() -> Component.literal(on
				? "Story gates are on: posters, awakening, Haki lessons, leaf fruits and Laugh Tale follow the story."
				: "Story gates are off: everything is open, like before the story existed."), true);
		return 1;
	}
}
