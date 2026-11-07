package com.onepiecemod.endgame;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

/**
 * The endgame chat commands:
 *   /endgame                    your New Game+ cycle, the Final War, and every raid (open, won, treasure ready)
 *   /endgame history            the pages of the true history you have read, and hints for the rest
 *   /newgameplus [confirm]      what New Game+ does, then start it (after the post-game)
 * Operators only, for testing:
 *   /endgame raid <id>          start any raid here, unlocked or not
 *   /endgame stop               end the raid you're in
 *   /endgame finale             play the Laugh Tale finale again
 *   /endgame dawn               play the Dawn (the true ending) now
 *   /endgame history all        learn every page of the true history
 *   /endgame finalwar           bring the Final War now
 *   /endgame cycle <n>          set your New Game+ cycle
 */
public class EndgameCommands {
	public static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
			dispatcher.register(Commands.literal("endgame")
					.executes(context -> {
						ServerPlayer player = context.getSource().getPlayerOrException();
						status(player);
						return 1;
					})
					.then(Commands.literal("raid")
							.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
							.then(Commands.argument("id", StringArgumentType.word())
									.suggests((context, builder) -> SharedSuggestionProvider.suggest(RaidDef.all().keySet(), builder))
									.executes(context -> {
										ServerPlayer player = context.getSource().getPlayerOrException();
										RaidDef raid = RaidDef.get(StringArgumentType.getString(context, "id"));
										if (raid == null) {
											context.getSource().sendFailure(Component.literal("Unknown raid. Raids: " + String.join(", ", RaidDef.all().keySet())));
											return 0;
										}
										String problem = Raids.start(player, raid);
										if (problem != null) {
											context.getSource().sendFailure(Component.literal(problem));
											return 0;
										}
										return 1;
									})))
					.then(Commands.literal("history")
							.executes(context -> {
								VoidCentury.showHistory(context.getSource().getPlayerOrException());
								return 1;
							})
							.then(Commands.literal("all")
									.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
									.executes(context -> {
										ServerPlayer player = context.getSource().getPlayerOrException();
										VoidCentury.PAGES.forEach(page -> VoidCentury.learn(player, page));
										return 1;
									})))
					.then(Commands.literal("dawn")
							.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
							.executes(context -> {
								VoidCentury.startDawn(context.getSource().getPlayerOrException());
								return 1;
							}))
					.then(Commands.literal("stop")
							.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
							.executes(context -> {
								boolean stopped = Raids.stop(context.getSource().getPlayerOrException());
								context.getSource().sendSystemMessage(Component.literal(stopped ? "Raid called off." : "You're not in a raid."));
								return stopped ? 1 : 0;
							}))
					.then(Commands.literal("finale")
							.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
							.executes(context -> {
								ServerPlayer player = context.getSource().getPlayerOrException();
								Finale.startScene(player);
								return 1;
							}))
					.then(Commands.literal("finalwar")
							.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
							.executes(context -> {
								ServerPlayer player = context.getSource().getPlayerOrException();
								String problem = Raids.start(player, RaidDef.get("final_war"));
								if (problem != null) {
									context.getSource().sendFailure(Component.literal(problem));
									return 0;
								}
								EndgameData.set(player, EndgameData.of(player).withFlag("finale").withFlag("final_war"));
								return 1;
							}))
					.then(Commands.literal("cycle")
							.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
							.then(Commands.argument("n", IntegerArgumentType.integer(0, NewGamePlus.MAX_CYCLE))
									.executes(context -> {
										ServerPlayer player = context.getSource().getPlayerOrException();
										int cycle = IntegerArgumentType.getInteger(context, "n");
										EndgameData.set(player, EndgameData.of(player).withCycle(cycle));
										context.getSource().sendSystemMessage(Component.literal("New Game+ cycle set to " + cycle + "."));
										return 1;
									}))));

			dispatcher.register(Commands.literal("newgameplus")
					.executes(context -> {
						ServerPlayer player = context.getSource().getPlayerOrException();
						String problem = NewGamePlus.problem(player);
						if (problem != null) {
							context.getSource().sendFailure(Component.literal(problem));
							return 0;
						}
						NewGamePlus.describe(player);
						player.sendSystemMessage(Component.literal("Type /newgameplus confirm to begin. This can't be undone.").withStyle(ChatFormatting.YELLOW));
						return 1;
					})
					.then(Commands.literal("confirm")
							.executes(context -> {
								ServerPlayer player = context.getSource().getPlayerOrException();
								String problem = NewGamePlus.problem(player);
								if (problem != null) {
									context.getSource().sendFailure(Component.literal(problem));
									return 0;
								}
								NewGamePlus.start(player);
								return 1;
							})));
		});
	}

	static void status(ServerPlayer player) {
		EndgameData data = EndgameData.of(player);
		player.sendSystemMessage(Component.literal("=== Endgame ===").withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal(data.cycle() == 0 ? "First voyage (New Game+ opens after the post-game)."
				: "New Game+ " + data.cycle() + " of " + NewGamePlus.MAX_CYCLE + ". Bosses beaten this cycle: " + data.cycleBosses().size() + ".")
				.withStyle(ChatFormatting.DARK_RED));
		if (data.hasFlag("finale") && !data.hasFlag("final_war")) {
			long left = Math.max(0, data.timer("final_war") - player.level().getServer().overworld().getGameTime());
			player.sendSystemMessage(Component.literal(left > 0 ? "The Final War comes in about " + Math.max(1, left / 1200) + " minutes."
					: "The Final War comes as soon as you stand on dry land in the Overworld.").withStyle(ChatFormatting.AQUA));
		}
		player.sendSystemMessage(Component.literal("True history: " + VoidCentury.pagesRead(player) + "/" + VoidCentury.PAGES.size()
				+ " pages (/endgame history).").withStyle(ChatFormatting.YELLOW));
		listRaids(player);
		if (NewGamePlus.problem(player) == null) {
			player.sendSystemMessage(Component.literal("New Game+ is ready: type /newgameplus").withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD));
		}
	}

	static void listRaids(ServerPlayer player) {
		EndgameData data = EndgameData.of(player);
		long now = player.level().getServer().overworld().getGameTime();
		player.sendSystemMessage(Component.literal("Raids:").withStyle(ChatFormatting.GOLD));
		for (RaidDef raid : RaidDef.all().values()) {
			String state;
			ChatFormatting color;
			if (!raid.unlocked().test(player)) {
				state = "locked: " + raid.unlockText();
				color = ChatFormatting.DARK_GRAY;
			} else {
				long wait = data.timer("raid:" + raid.id()) - now;
				String treasure = wait <= 0 ? "treasure ready" : "treasure in " + Math.max(1, (wait + 23999) / 24000) + " days";
				state = (data.cleared().contains(raid.id()) ? "won, " : "open, ") + treasure;
				color = raid.color();
			}
			player.sendSystemMessage(Component.literal(" " + raid.name() + " (" + raid.crew() + "): " + state).withStyle(color));
		}
	}
}
