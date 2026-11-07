package com.onepiecemod.weather;

import java.util.function.BiFunction;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

import com.onepiecemod.ship.ShipEntity;

/**
 * Grand Line weather and sea events: storms, whirlpools, Aqua Laguna, Sea King ambushes in the Calm Belt,
 * blizzards, heat waves and the Florian Triangle's mist. OnePieceMod calls initialize() once, after SeaFeature.
 *
 * Cheat commands for testing (need cheats / operator):
 *   /seaevent start <type>   start one next to you, skipping most of the warning
 *   /seaevent stop           end every event
 *   /seaevent list           what's happening right now
 */
public class WeatherFeature {
	public static void initialize() {
		SeaEventSync.initialize();
		SeaEvents.initialize();
		com.onepiecemod.island.IslandFeature.initialize(); // Island titles and climates.

		// Ships feel the events. The Calm Belt's rule stays: we multiply on top of whatever was there before.
		BiFunction<Level, BlockPos, Double> before = ShipEntity.windAt;
		ShipEntity.windAt = (level, pos) -> before.apply(level, pos) * SeaForces.windAt(level, pos);
		ShipEntity.seaPush = SeaForces::push;

		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("seaevent")
						.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
						.then(Commands.literal("start")
								.then(Commands.argument("type", StringArgumentType.word())
										.suggests((context, builder) -> {
											for (SeaEventType type : SeaEventType.values()) {
												builder.suggest(type.id);
											}
											return builder.buildFuture();
										})
										.executes(WeatherFeature::startCommand)))
						.then(Commands.literal("stop").executes(context -> {
							int count = SeaEvents.stopAll(context.getSource().getServer().overworld());
							context.getSource().sendSuccess(() -> Component.literal("Ended " + count + " sea event(s)."), true);
							return count;
						}))
						.then(Commands.literal("list").executes(WeatherFeature::listCommand))));
	}

	private static int startCommand(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		SeaEventType type = SeaEventType.byId(StringArgumentType.getString(context, "type"));
		if (type == null) {
			context.getSource().sendFailure(Component.literal("Unknown event. Try: storm, whirlpool, aqua_laguna, calm_belt_ambush, blizzard, heat_wave, florian_mist"));
			return 0;
		}
		String problem = SeaEvents.start((ServerLevel) player.level(), type, player);
		if (problem != null) {
			context.getSource().sendFailure(Component.literal(problem));
			return 0;
		}
		context.getSource().sendSuccess(() -> Component.literal("Started: " + type.title).withStyle(type.color), true);
		return 1;
	}

	private static int listCommand(CommandContext<CommandSourceStack> context) {
		long time = context.getSource().getServer().overworld().getGameTime();
		if (SeaEvents.ACTIVE.isEmpty()) {
			context.getSource().sendSuccess(() -> Component.literal("The seas are quiet right now."), false);
		}
		for (SeaEvent event : SeaEvents.ACTIVE) {
			String when = event.isActive(time)
					? (event.endTime - time) / 20 + "s left"
					: "starts in " + (event.startTime - time) / 20 + "s";
			context.getSource().sendSuccess(() -> Component.literal(event.type.title + " at "
					+ (int) event.x + ", " + (int) event.z + " (" + when + ")").withStyle(event.type.color), false);
		}
		return SeaEvents.ACTIVE.size();
	}
}
