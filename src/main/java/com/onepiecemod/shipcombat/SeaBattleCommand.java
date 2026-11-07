package com.onepiecemod.shipcombat;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.context.CommandContext;

import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

import com.onepiecemod.ship.ShipEntity;

/**
 * /seabattle marine|pirate|battle [tier]  (operators only): calls an enemy ship (or a Marine-vs-pirate fight)
 * about 50 blocks from you, so you can try out ship combat without waiting for one to turn up.
 * /seabattle fleet marine|pirate [tier]: calls a whole fleet at you (a naval battle, see NavalBattles).
 * Tier 0-5: higher is tougher (Marine Battleship at 3+, pirate Galleon at 2+).
 */
public class SeaBattleCommand {
	static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("seabattle")
						.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
						.then(kind("marine"))
						.then(kind("pirate"))
						.then(kind("battle"))
						.then(Commands.literal("fleet")
								.then(fleet("marine"))
								.then(fleet("pirate")))));
	}

	private static com.mojang.brigadier.builder.LiteralArgumentBuilder<CommandSourceStack> kind(String kind) {
		return Commands.literal(kind)
				.executes(context -> run(context, kind, 1))
				.then(Commands.argument("tier", IntegerArgumentType.integer(0, 5))
						.executes(context -> run(context, kind, IntegerArgumentType.getInteger(context, "tier"))));
	}

	private static com.mojang.brigadier.builder.LiteralArgumentBuilder<CommandSourceStack> fleet(String kind) {
		return Commands.literal(kind)
				.executes(context -> runFleet(context, kind, 1))
				.then(Commands.argument("tier", IntegerArgumentType.integer(0, 4))
						.executes(context -> runFleet(context, kind, IntegerArgumentType.getInteger(context, "tier"))));
	}

	private static int runFleet(CommandContext<CommandSourceStack> context, String kind, int tier) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
		CommandSourceStack source = context.getSource();
		ShipEntity flagship = NavalBattles.start(source.getLevel(), source.getPlayerOrException(), source.getPosition(), source.getRotation().y, 60,
				kind.equals("pirate") ? ShipBrain.Faction.PIRATE : ShipBrain.Faction.MARINE, tier);
		if (flagship == null) {
			source.sendFailure(Component.literal("No open sea (5+ blocks deep) about 60 blocks from here. Try further out at sea."));
			return 0;
		}
		source.sendSuccess(() -> Component.literal("Called a " + kind + " fleet led by the " + flagship.getName().getString() + "."), true);
		return 1;
	}

	private static int run(CommandContext<CommandSourceStack> context, String kind, int tier) {
		CommandSourceStack source = context.getSource();
		ServerLevel level = source.getLevel();
		Vec3 at = source.getPosition();
		float heading = source.getRotation().y;
		ShipEntity first = SeaEncounters.spawnAt(level, at, heading, 50, kind.equals("pirate") ? ShipBrain.Faction.PIRATE : ShipBrain.Faction.MARINE, tier, null);
		if (first == null) {
			source.sendFailure(Component.literal("No open sea (5+ blocks deep) about 50 blocks from here. Try further out at sea."));
			return 0;
		}
		if (kind.equals("battle")) {
			SeaEncounters.spawnAt(level, at, heading, 50, ShipBrain.Faction.PIRATE, tier, first.position());
		}
		source.sendSuccess(() -> Component.literal("Called the " + first.getName().getString()
				+ (kind.equals("battle") ? " and a pirate ship" : "") + " at "
				+ first.blockPosition().toShortString() + "."), true);
		return 1;
	}
}
