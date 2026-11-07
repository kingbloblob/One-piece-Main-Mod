package com.onepiecemod.news;

import java.util.List;

import com.mojang.brigadier.context.CommandContext;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

/**
 * The /news chat commands:
 *   /news             the latest headlines in chat
 *   /news off | on    stop or restart the morning paper
 *   /news paper       (ops, for testing) get today's paper right now
 *   /news posters     (ops, for testing) pin Wanted Posters in the town you're standing in, even if it has some
 */
public class NewsCommands {
	public static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("news")
						.executes(NewsCommands::headlines)
						.then(Commands.literal("off").executes(context -> setOff(context, true)))
						.then(Commands.literal("on").executes(context -> setOff(context, false)))
						.then(Commands.literal("paper")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.executes(NewsCommands::paper))
						.then(Commands.literal("posters")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.executes(NewsCommands::posters))));
	}

	private static int headlines(CommandContext<CommandSourceStack> context) {
		CommandSourceStack source = context.getSource();
		List<NewsLog.Headline> news = NewsLog.recent(source.getServer(), 30);
		source.sendSystemMessage(Component.literal("--- World Economy News: latest headlines ---").withStyle(ChatFormatting.GOLD));
		if (news.isEmpty()) {
			source.sendSystemMessage(Component.literal("No pirate news yet. Go make some!").withStyle(ChatFormatting.GRAY));
		}
		for (int i = 0; i < Math.min(5, news.size()); i++) {
			NewsLog.Headline h = news.get(i);
			source.sendSystemMessage(Component.literal("Day " + h.day() + ": ").withStyle(ChatFormatting.GRAY)
					.append(Component.literal(h.headline()).withStyle(ChatFormatting.YELLOW)));
		}
		return news.size();
	}

	private static int setOff(CommandContext<CommandSourceStack> context, boolean off) {
		ServerPlayer player = context.getSource().getPlayer();
		if (player == null) {
			return 0;
		}
		player.setAttached(NewsCoo.PAPER_OFF, off);
		player.sendSystemMessage(Component.literal(off
				? "The News Coo won't bring you the paper any more. /news on to start again."
				: "The News Coo will bring you the paper every morning.").withStyle(ChatFormatting.GOLD));
		return 1;
	}

	private static int paper(CommandContext<CommandSourceStack> context) {
		ServerPlayer player = context.getSource().getPlayer();
		if (player == null) {
			return 0;
		}
		player.setAttached(NewsCoo.LAST_PAPER, NewsLog.day(player.level().getServer()) - 2);
		NewsCoo.deliver(player);
		return 1;
	}

	private static int posters(CommandContext<CommandSourceStack> context) {
		ServerPlayer player = context.getSource().getPlayer();
		if (player == null) {
			return 0;
		}
		ServerLevel level = (ServerLevel) player.level();
		var start = PosterPlacer.townAt(level, player.blockPosition());
		if (start != null) {
			List<Long> done = new java.util.ArrayList<>(level.getAttachedOrElse(PosterPlacer.DONE, List.of()));
			done.remove(Long.valueOf(start.getChunkPos().pack()));
			level.setAttached(PosterPlacer.DONE, done);
		}
		int placed = PosterPlacer.check(level, player.blockPosition());
		player.sendSystemMessage(Component.literal(placed < 0 ? "You're not in a town or Marine base."
				: "Pinned " + placed + " Wanted Posters here.").withStyle(ChatFormatting.GOLD));
		return Math.max(0, placed);
	}
}
