package com.onepiecemod.career;

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
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

/**
 * The /career chat commands:
 *   /career                         your career, rank, points and what the next promotion needs
 *   /career orders                  get orders (or see the ones you have)
 *   /career abandon                 call off your orders
 *   /career backup                  call for backup
 *   /career leave confirm           leave the Marines or the Revolutionary Army
 *   /career set <player> <career> [rank]   cheat: set a career (needs cheats / operator)
 *   /career points <player> <n>     cheat: add Merit or Liberation
 *   /career ambush                  cheat: send a pirate ambush (Marines) or CP agents (Revolutionaries) now
 */
final class CareerCommands {
	private CareerCommands() {
	}

	static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("career")
						.executes(CareerCommands::info)
						.then(Commands.literal("orders").executes(context -> run(context, "orders")))
						.then(Commands.literal("abandon").executes(context -> run(context, "abandon")))
						.then(Commands.literal("backup").executes(context -> run(context, "backup")))
						.then(Commands.literal("leave")
								.executes(context -> {
									context.getSource().getPlayerOrException().sendSystemMessage(Component.literal(
											"Type /career leave confirm to leave. Marines lose their rank and Merit; Revolutionaries keep their bounty.")
											.withStyle(ChatFormatting.YELLOW));
									return 1;
								})
								.then(Commands.literal("confirm").executes(context -> run(context, "leave"))))
						.then(Commands.literal("set")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.argument("player", EntityArgument.player())
										.then(Commands.argument("career", StringArgumentType.word())
												.suggests((context, builder) -> SharedSuggestionProvider.suggest(new String[]{"pirate", "marine", "revolutionary"}, builder))
												.executes(context -> set(context, 0))
												.then(Commands.argument("rank", IntegerArgumentType.integer(0, 10))
														.executes(context -> set(context, IntegerArgumentType.getInteger(context, "rank")))))))
						.then(Commands.literal("points")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.argument("player", EntityArgument.player())
										.then(Commands.argument("amount", IntegerArgumentType.integer(1))
												.executes(CareerCommands::points))))
						.then(Commands.literal("ambush")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.executes(context -> {
									boolean sent = CareerAmbush.ambush(context.getSource().getPlayerOrException());
									if (!sent) {
										context.getSource().sendFailure(Component.literal("No ambush: you're a pirate, one is already here, or there's no dry ground nearby."));
									}
									return sent ? 1 : 0;
								}))
		));
	}

	private static int run(CommandContext<CommandSourceStack> context, String action) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		switch (action) {
			case "orders" -> CareerMissions.request(player);
			case "abandon" -> CareerMissions.abandon(player);
			case "backup" -> CareerAllies.call(player);
			case "leave" -> Careers.leave(player);
			default -> {
			}
		}
		return 1;
	}

	private static int info(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		CareerData data = Careers.get(player);
		Career career = data.path();
		if (career == Career.PIRATE) {
			player.sendSystemMessage(Component.literal("You're a free pirate.").withStyle(ChatFormatting.GOLD));
			player.sendSystemMessage(Component.literal("To join the Marines, talk to Koby at Shells Town (or Garp, Sengoku, Tashigi) while your bounty is "
					+ "10,000,000 or less. To join the Revolutionary Army, talk to Dragon, Sabo or Ivankov, or wait for their letter.")
					.withStyle(ChatFormatting.GRAY));
			return 1;
		}
		player.sendSystemMessage(Component.literal(career.displayName + " " + data.currentRank().name() + ": " + data.points() + " " + career.points
				+ ", " + data.missionsDone() + " orders carried out").withStyle(career.color));
		Career.Rank next = data.nextRank();
		if (next == null) {
			player.sendSystemMessage(Component.literal("You've reached the top rank.").withStyle(ChatFormatting.GRAY));
		} else {
			player.sendSystemMessage(Component.literal("Next: " + next.name() + " at " + next.need() + " " + career.points
					+ (next.trialCount() > 0 ? ". " + Careers.trialText(career, next) + " (" + Careers.trialProgress(player, next) + "/" + next.trialCount() + ")" : ""))
					.withStyle(ChatFormatting.GRAY));
		}
		player.sendSystemMessage(Component.literal("Salary " + data.currentRank().salary() + " Berries a day. Backup: " + data.currentRank().backup()
				+ ". " + (career == Career.MARINE ? "Strikes: " + data.strikes() + "/" + Careers.MAX_STRIKES : "Bounty: " + com.onepiecemod.bounty.Bounty.format(com.onepiecemod.bounty.Bounty.get(player))))
				.withStyle(ChatFormatting.GRAY));
		data.mission().ifPresent(mission -> CareerMissions.describe(player, mission));
		return 1;
	}

	private static int set(CommandContext<CommandSourceStack> context, int rank) throws CommandSyntaxException {
		ServerPlayer target = EntityArgument.getPlayer(context, "player");
		Career career = Career.byId(StringArgumentType.getString(context, "career"));
		CareerData data = Careers.get(target).joined(career, Careers.today(target.level().getServer()));
		int top = Math.max(0, career.ranks.size() - 1);
		int index = Math.min(rank, top);
		data = data.withRank(index).withPoints(career.ranks.isEmpty() ? 0 : career.rank(index).need());
		Careers.set(target, data);
		CareerMissions.clear(target);
		if (career == Career.MARINE) {
			com.onepiecemod.bounty.Bounty.set(target, 0L);
		}
		context.getSource().sendSuccess(() -> Component.literal(target.getName().getString() + " is now: " + career.displayName
				+ (career.ranks.isEmpty() ? "" : " " + career.rank(index).name())), true);
		return 1;
	}

	private static int points(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer target = EntityArgument.getPlayer(context, "player");
		Careers.addPoints(target, IntegerArgumentType.getInteger(context, "amount"), "cheat", true);
		return 1;
	}
}
