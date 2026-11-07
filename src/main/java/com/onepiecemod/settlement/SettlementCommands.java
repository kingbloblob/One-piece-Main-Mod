package com.onepiecemod.settlement;

import java.util.UUID;

import com.mojang.brigadier.arguments.StringArgumentType;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

/**
 * /mytown                    the town report
 * /mytown collect            take the rent out of the treasury (or use the planner on the bell)
 * /mytown name <name>        rename your town
 * /mytown culture <style>    how new townsfolk dress and what the market sells (east_blue, wano, alabasta...)
 * /mytown upgrade <id>       buy a town upgrade (the Builder's Ledger has buttons)
 * /mytown abandon confirm    give up your town (plots and treasury are lost; the blocks stay)
 * /mytown rent               cheat: pay a day's rent now
 */
final class SettlementCommands {
	private SettlementCommands() {
	}

	static void register() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("mytown")
						.executes(context -> {
							Settlements.report(context.getSource().getPlayerOrException());
							return 1;
						})
						.then(Commands.literal("collect").executes(context -> {
							ServerPlayer player = context.getSource().getPlayerOrException();
							if (Settlements.treasury(player) <= 0) {
								player.sendSystemMessage(Component.literal("The treasury is empty.").withStyle(ChatFormatting.GRAY));
								return 0;
							}
							Settlements.collect(player);
							return 1;
						}))
						.then(Commands.literal("name")
								.then(Commands.argument("name", StringArgumentType.greedyString()).executes(context -> {
									ServerPlayer player = context.getSource().getPlayerOrException();
									MinecraftServer server = player.level().getServer();
									PlayerTowns.PlayerTown town = PlayerTowns.of(server, player.getUUID());
									String name = StringArgumentType.getString(context, "name").trim();
									if (town == null || name.isEmpty() || name.length() > 32) {
										player.sendSystemMessage(Component.literal(town == null ? "You haven't founded a town."
												: "A town name needs 1 to 32 letters.").withStyle(ChatFormatting.RED));
										return 0;
									}
									PlayerTowns.put(server, player.getUUID(), town.withName(name));
									player.sendSystemMessage(Component.literal("Your town is now called " + name + ".").withStyle(ChatFormatting.GREEN));
									return 1;
								})))
						.then(Commands.literal("culture")
								.then(Commands.argument("style", StringArgumentType.word())
										.suggests((context, builder) -> {
											Settlements.CULTURES.forEach(builder::suggest);
											return builder.buildFuture();
										})
										.executes(context -> {
											ServerPlayer player = context.getSource().getPlayerOrException();
											MinecraftServer server = player.level().getServer();
											PlayerTowns.PlayerTown town = PlayerTowns.of(server, player.getUUID());
											String style = StringArgumentType.getString(context, "style");
											if (town == null || !Settlements.CULTURES.contains(style)) {
												player.sendSystemMessage(Component.literal(town == null ? "You haven't founded a town."
														: "Styles: " + String.join(", ", Settlements.CULTURES)).withStyle(ChatFormatting.RED));
												return 0;
											}
											PlayerTowns.put(server, player.getUUID(), town.withCulture(style));
											player.sendSystemMessage(Component.literal("Townsfolk who move in from now on come in the " + style
													+ " style, and the market sells " + style + " goods.").withStyle(ChatFormatting.GREEN));
											return 1;
										})))
						.then(Commands.literal("upgrade")
								.then(Commands.argument("upgrade", StringArgumentType.word())
										.suggests((context, builder) -> {
											for (Settlements.TownUpgrade upgrade : Settlements.TownUpgrade.values()) {
												builder.suggest(upgrade.id);
											}
											return builder.buildFuture();
										})
										.executes(context -> {
											ServerPlayer player = context.getSource().getPlayerOrException();
											String problem = Settlements.buyUpgrade(player, StringArgumentType.getString(context, "upgrade"));
											if (problem != null) {
												player.sendSystemMessage(Component.literal(problem).withStyle(ChatFormatting.RED));
												return 0;
											}
											return 1;
										})))
						.then(Commands.literal("abandon")
								.then(Commands.literal("confirm").executes(context -> {
									ServerPlayer player = context.getSource().getPlayerOrException();
									UUID id = player.getUUID();
									MinecraftServer server = player.level().getServer();
									if (PlayerTowns.of(server, id) == null) {
										return 0;
									}
									Settlements.abandon(server, id);
									player.sendSystemMessage(Component.literal("You gave up your town. Its people will drift away.").withStyle(ChatFormatting.YELLOW));
									return 1;
								})))
						.then(Commands.literal("rent")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.executes(context -> {
									ServerPlayer player = context.getSource().getPlayerOrException();
									int rent = Settlements.payOneDayNow(player);
									if (rent < 0) {
										return 0;
									}
									context.getSource().sendSuccess(() -> Component.literal("The townsfolk paid " + rent + " Berries rent."), false);
									return 1;
								}))
		));
	}
}
