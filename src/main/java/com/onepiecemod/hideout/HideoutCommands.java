package com.onepiecemod.hideout;

import java.util.ArrayList;
import java.util.List;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

/**
 * The /hideout chat commands:
 *   /hideout              where your hideout is, its level and what the next level needs
 *   /hideout attack       cheat: the Navy attacks your hideout now (needs cheats / operator)
 *   /hideout attack stop  cheat: call it off
 *   /hideout away         cheat: an attack while you're away, settled by the defence rating
 *   /hideout haul [days]  cheat: the crew brings in the daily haul now
 */
final class HideoutCommands {
	private HideoutCommands() {
	}

	static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("hideout")
						.executes(context -> info(context.getSource().getPlayerOrException()))
						.then(Commands.literal("attack")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.executes(context -> {
									String problem = HideoutSiege.start(context.getSource().getPlayerOrException());
									if (problem != null) {
										context.getSource().sendFailure(Component.literal(problem));
									}
									return problem == null ? 1 : 0;
								})
								.then(Commands.literal("stop").executes(context -> {
									boolean stopped = HideoutSiege.stop(context.getSource().getPlayerOrException());
									context.getSource().sendSuccess(() -> Component.literal(stopped ? "Attack called off." : "No attack running."), false);
									return stopped ? 1 : 0;
								})))
						.then(Commands.literal("away")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.executes(HideoutCommands::away))
						.then(Commands.literal("haul")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.executes(context -> haul(context, 1))
								.then(Commands.argument("days", IntegerArgumentType.integer(1, 3))
										.executes(context -> haul(context, IntegerArgumentType.getInteger(context, "days")))))
		));
	}

	static int info(ServerPlayer player) {
		Hideouts.Hideout hideout = Hideouts.of(player.level().getServer(), player.getUUID());
		if (hideout == null) {
			player.sendSystemMessage(Component.literal("You have no hideout yet. Craft a Hideout Flag (a Jolly Roger on two sticks, "
					+ "with planks) and plant it on an island to claim the land around it.").withStyle(ChatFormatting.YELLOW));
			return 0;
		}
		player.sendSystemMessage(Component.literal("=== " + hideout.crewName() + " hideout: " + HideoutLevels.NAMES[hideout.level()]
				+ " ===").withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal("Flag at " + hideout.pos().getX() + " " + hideout.pos().getY() + " " + hideout.pos().getZ()
				+ ". " + HideoutLevels.perk(hideout.level())));
		HideoutFlagBlockEntity flag = Hideouts.flag(player.level().getServer(), player.getUUID());
		if (flag == null) {
			player.sendSystemMessage(Component.literal("Defence " + hideout.defence() + ". Attacks held off: " + hideout.held()
					+ ", lost: " + hideout.lost() + ". Go there for more.").withStyle(ChatFormatting.GRAY));
			return 1;
		}
		ServerLevel level = (ServerLevel) flag.getLevel();
		for (String line : stats(level, flag)) {
			player.sendSystemMessage(Component.literal(line).withStyle(ChatFormatting.GRAY));
		}
		if (flag.level() < HideoutLevels.MAX && flag.surveyed()) {
			player.sendSystemMessage(Component.literal("Next: " + HideoutLevels.NAMES[flag.level() + 1]).withStyle(ChatFormatting.YELLOW));
			for (HideoutLevels.Need need : HideoutLevels.needs(flag.level() + 1, flag.survey(), flag.residents(level).size())) {
				player.sendSystemMessage(Component.literal((need.done() ? "  [x] " : "  [ ] ") + need.text() + " "
						+ Math.min(need.have(), need.need()) + "/" + need.need()).withStyle(need.done() ? ChatFormatting.GREEN : ChatFormatting.WHITE));
			}
		}
		return 1;
	}

	/** Lines about defence and the Navy, for chat and the screen. */
	static List<String> stats(ServerLevel level, HideoutFlagBlockEntity flag) {
		List<String> lines = new ArrayList<>();
		Hideouts.Hideout saved = Hideouts.of(level.getServer(), flag.owner());
		int cannons = flag.survey().cannons.size();
		lines.add("Defence rating: " + flag.defence(level));
		lines.add("Cannons: " + cannons + (cannons > 0 ? ", cannonballs in stash: " + flag.cannonballs() : ""));
		lines.add("Beds: " + flag.survey().beds.size() + ", campfires: " + flag.survey().campfires.size()
				+ ", buildings: " + flag.survey().buildings.size());
		int threat = flag.threat(level);
		String navy = threat == 0 ? "None (no bounty)" : threat <= 1 ? "Low" : threat <= 3 ? "Watching you" : "High";
		if (HideoutSiege.isUnderAttack(flag.owner())) {
			navy = "UNDER ATTACK!";
		} else if (flag.level() < 1) {
			navy += " (they ignore a hideout below Pirate Camp)";
		}
		lines.add("Navy interest: " + navy);
		if (saved != null) {
			lines.add("Attacks held off: " + saved.held() + ", lost: " + saved.lost());
		}
		return lines;
	}

	private static int away(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		Hideouts.Hideout hideout = Hideouts.of(player.level().getServer(), player.getUUID());
		if (hideout == null) {
			context.getSource().sendFailure(Component.literal("You have no hideout."));
			return 0;
		}
		HideoutSiege.awayAttack(player.level().getServer(), player.getUUID(), hideout.withThreat(Math.max(1, hideout.threat())));
		return 1;
	}

	private static int haul(CommandContext<CommandSourceStack> context, int days) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		HideoutFlagBlockEntity flag = Hideouts.flag(player.level().getServer(), player.getUUID());
		if (flag == null) {
			context.getSource().sendFailure(Component.literal("You have no hideout, or its flag isn't loaded."));
			return 0;
		}
		flag.runHaul((ServerLevel) flag.getLevel(), days, true);
		return 1;
	}
}
