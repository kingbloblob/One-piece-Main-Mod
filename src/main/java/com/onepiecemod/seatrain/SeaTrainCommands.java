package com.onepiecemod.seatrain;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

import com.onepiecemod.building.BuildingRegistry;
import com.onepiecemod.building.Parts;
import com.onepiecemod.character.CharacterFeature;

/**
 * /seatrain           the timetable for the stop you're standing at (also what the [Timetable] links run)
 * /seatrain go <id>   ride to a stop (what the [Ride] links run)
 * /seatrain name <..> rename your own Sea Train Station
 * /seatrain list      every stop you know, from anywhere
 */
public class SeaTrainCommands {
	static void register() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("seatrain")
						.executes(SeaTrainCommands::showTimetable)
						.then(Commands.literal("go")
								.then(Commands.argument("station", StringArgumentType.word()).executes(SeaTrainCommands::go)))
						.then(Commands.literal("name")
								.then(Commands.argument("name", StringArgumentType.greedyString()).executes(SeaTrainCommands::rename)))
						.then(Commands.literal("list").executes(SeaTrainCommands::list))
						.then(Commands.literal("preview").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.executes(SeaTrainCommands::preview))));
	}

	private static int showTimetable(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		Stations.Station here = Stations.here(player);
		if (here == null) {
			player.sendSystemMessage(Component.literal("You need to be at a Sea Train stop: Water 7's Blue Station, Enies Lobby, "
					+ "a Sea Train Station, or a station you built.").withStyle(ChatFormatting.RED));
			return 0;
		}
		Stations.learn(player, here.id());
		timetable(player, here);
		return 1;
	}

	/** Lists every stop the player can ride to from here, each with a [Ride] link. */
	static void timetable(ServerPlayer player, Stations.Station here) {
		ServerLevel level = (ServerLevel) player.level();
		boolean open = here.puffingTom() ? Trips.puffingTomOpen(player) : Trips.ownLinesOpen(player);
		player.sendSystemMessage(Component.literal("=== " + (here.puffingTom() ? "Puffing Tom" : "Sea Train") + " timetable: " + here.name() + " ===")
				.withStyle(ChatFormatting.AQUA));
		if (!open) {
			player.sendSystemMessage(Component.literal(here.puffingTom()
					? "\"This line only opens for you once your story reaches Water 7.\""
					: "Nobody here can drive a Sea Train yet. Finish the Water 7 chapter first.").withStyle(ChatFormatting.GRAY));
			return;
		}
		List<Stations.Station> stops = new ArrayList<>();
		for (String id : Stations.known(player)) {
			Stations.Station stop = Stations.get(level, id);
			if (stop != null && !stop.id().equals(here.id()) && stop.dim().equals(here.dim()) && stillThere(level, stop)) {
				stops.add(stop);
			}
		}
		if (stops.isEmpty()) {
			player.sendSystemMessage(Component.literal("You don't know any other stops yet. Sail to Enies Lobby, find a Sea Train Station "
					+ "on another island, or build your own: you can ride to any stop you've stood at.").withStyle(ChatFormatting.GRAY));
			return;
		}
		stops.sort(Comparator.comparingDouble(stop -> stop.pos().distSqr(here.pos())));
		String wallet = here.puffingTom()
				? Parts.count(player, CharacterFeature.BERRY) + " Berries"
				: (Parts.count(player, net.minecraft.world.item.Items.COAL) + Parts.count(player, net.minecraft.world.item.Items.CHARCOAL)) + " Coal";
		player.sendSystemMessage(Component.literal("Where to? (you have " + wallet + ")").withStyle(ChatFormatting.GOLD));
		for (Stations.Station stop : stops) {
			int distance = (int) Math.sqrt(stop.pos().distSqr(here.pos()));
			String fare = player.isCreative() ? "free" : here.puffingTom() ? Trips.berryFare(distance) + " Berries" : Trips.coalFare(distance) + " Coal";
			MutableComponent line = Component.literal("  [Ride] ").withStyle(style -> style.withColor(ChatFormatting.GREEN)
					.withClickEvent(new ClickEvent.RunCommand("/seatrain go " + stop.id()))
					.withHoverEvent(new HoverEvent.ShowText(Component.literal("Ride to " + stop.name() + " for " + fare))));
			line.append(Component.literal(stop.name()).withStyle(stop.puffingTom() ? ChatFormatting.YELLOW : ChatFormatting.WHITE));
			line.append(Component.literal(", " + distance + " blocks " + direction(here.pos(), stop.pos()) + ", " + fare)
					.withStyle(ChatFormatting.GRAY));
			player.sendSystemMessage(line);
		}
	}

	/** Drops player stations whose Ticket Booth is gone (far away, unloaded ones are trusted until someone gets there). */
	private static boolean stillThere(ServerLevel level, Stations.Station stop) {
		if (stop.puffingTom()) {
			return true;
		}
		ServerLevel stopLevel = level.getServer().getLevel(net.minecraft.resources.ResourceKey.create(
				net.minecraft.core.registries.Registries.DIMENSION, net.minecraft.resources.Identifier.parse(stop.dim())));
		if (stopLevel == null) {
			return false;
		}
		if (stopLevel.isLoaded(stop.pos()) && !stopLevel.getBlockState(stop.pos()).is(com.onepiecemod.building.Buildings.get(Stations.BOOTH).core())) {
			Stations.remove(level, stop.id()); // The Ticket Booth was broken.
			return false;
		}
		return true;
	}

	private static int go(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		ServerLevel level = (ServerLevel) player.level();
		Stations.Station here = Stations.here(player);
		if (here == null) {
			player.sendSystemMessage(Component.literal("You need to be at a Sea Train stop to board.").withStyle(ChatFormatting.RED));
			return 0;
		}
		Stations.Station there = Stations.get(level, StringArgumentType.getString(context, "station"));
		if (there == null || !Stations.knows(player, there.id()) || !stillThere(level, there)) {
			player.sendSystemMessage(Component.literal("The train doesn't know that stop. You can only ride to stops you've stood at.")
					.withStyle(ChatFormatting.RED));
			return 0;
		}
		return Trips.book(player, here, there) ? 1 : 0;
	}

	private static int rename(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		ServerLevel level = (ServerLevel) player.level();
		Stations.Station here = Stations.here(player);
		BuildingRegistry.Entry booth = here == null || here.puffingTom() ? null : BuildingRegistry.at(level, here.pos());
		if (booth == null || !booth.owner().equals(player.getUUID())) {
			player.sendSystemMessage(Component.literal("Stand at a Sea Train Station you built to name it.").withStyle(ChatFormatting.RED));
			return 0;
		}
		String name = StringArgumentType.getString(context, "name").trim();
		if (name.isEmpty() || name.length() > 32) {
			player.sendSystemMessage(Component.literal("Pick a name of 1 to 32 letters.").withStyle(ChatFormatting.RED));
			return 0;
		}
		Stations.put(level, here.withName(name));
		player.sendSystemMessage(Component.literal("Your station is now called " + name + ".").withStyle(ChatFormatting.GREEN));
		return 1;
	}

	/** Operators: park a Puffing Tom in front of you for 30 seconds, to look at it. */
	private static int preview(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		Trips.preview(player);
		return 1;
	}

	private static int list(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		ServerLevel level = (ServerLevel) player.level();
		List<String> known = Stations.known(player);
		player.sendSystemMessage(Component.literal("Sea Train stops you know: " + known.size()).withStyle(ChatFormatting.AQUA));
		for (String id : known) {
			Stations.Station stop = Stations.get(level, id);
			if (stop != null) {
				player.sendSystemMessage(Component.literal("  " + stop.name() + " at " + stop.pos().getX() + ", " + stop.pos().getZ()
						+ (stop.puffingTom() ? " (Puffing Tom)" : " (your line)")).withStyle(ChatFormatting.GRAY));
			}
		}
		if (!Trips.puffingTomOpen(player)) {
			player.sendSystemMessage(Component.literal("The Puffing Tom takes you once your story reaches Water 7.").withStyle(ChatFormatting.GRAY));
		}
		return 1;
	}

	/** "to the north-east" and so on. */
	static String direction(BlockPos from, BlockPos to) {
		int dx = to.getX() - from.getX();
		int dz = to.getZ() - from.getZ();
		String ns = Math.abs(dz) * 2 > Math.abs(dx) ? (dz < 0 ? "north" : "south") : "";
		String ew = Math.abs(dx) * 2 > Math.abs(dz) ? (dx < 0 ? "west" : "east") : "";
		return "to the " + (ns.isEmpty() || ew.isEmpty() ? ns + ew : ns + "-" + ew);
	}
}
