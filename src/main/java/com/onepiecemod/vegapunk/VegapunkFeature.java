package com.onepiecemod.vegapunk;

import java.util.List;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

/**
 * Vegapunk's creations: Pacifista and Seraphim hunts (VegapunkHunts) and the cyborg upgrades built from their parts
 * (Cyborg, CyborgUpgrade, VegapunkItems). OnePieceMod calls initialize() once, after the NPCs.
 *
 * Commands: /cyborg (your upgrades and fuel). Operators: /vegapunk hunt <unit>, /vegapunk list, /vegapunk stop,
 * /cyborg set <player> <upgrade> <tier>, /cyborg fill <player>.
 */
public class VegapunkFeature {
	public static void initialize() {
		VegapunkItems.initialize();
		VegapunkPayloads.initialize();
		Cyborg.initialize();
		VegapunkHunts.initialize();
		registerCommands();
	}

	private static void registerCommands() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
			dispatcher.register(Commands.literal("vegapunk")
					.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
					.then(Commands.literal("hunt")
							.then(Commands.argument("unit", StringArgumentType.word())
									.suggests((context, builder) -> SharedSuggestionProvider.suggest(
											java.util.Arrays.stream(HuntUnit.values()).map(u -> u.id), builder))
									.executes(VegapunkFeature::huntCommand)))
					.then(Commands.literal("list").executes(context -> {
						List<String> lines = VegapunkHunts.describe();
						context.getSource().sendSuccess(() -> Component.literal(lines.isEmpty() ? "No hunts running."
								: "Hunts: " + String.join("; ", lines)).withStyle(ChatFormatting.GOLD), false);
						return lines.size();
					}))
					.then(Commands.literal("here").executes(context -> {
						ServerPlayer player = context.getSource().getPlayerOrException();
						List<HuntUnit> units = VegapunkHunts.eligible(player);
						context.getSource().sendSuccess(() -> Component.literal(units.isEmpty() ? "No hunts can find you here."
								: "Hunts that can find you here: " + String.join(", ", units.stream().map(u -> u.id).toList()))
								.withStyle(ChatFormatting.GOLD), false);
						return units.size();
					}))
					.then(Commands.literal("stop").executes(context -> {
						int n = VegapunkHunts.stopAll();
						context.getSource().sendSuccess(() -> Component.literal("Stopped " + n + " hunt(s).").withStyle(ChatFormatting.GOLD), true);
						return n;
					})));

			dispatcher.register(Commands.literal("cyborg")
					.executes(context -> status(context.getSource(), context.getSource().getPlayerOrException()))
					.then(Commands.literal("set")
							.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
							.then(Commands.argument("player", EntityArgument.player())
									.then(Commands.argument("upgrade", StringArgumentType.word())
											.suggests((context, builder) -> SharedSuggestionProvider.suggest(
													java.util.Arrays.stream(CyborgUpgrade.values()).map(u -> u.id), builder))
											.then(Commands.argument("tier", IntegerArgumentType.integer(0, CyborgUpgrade.MAX_TIER))
													.executes(VegapunkFeature::setCommand)))))
					.then(Commands.literal("fill")
							.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
							.then(Commands.argument("player", EntityArgument.player())
									.executes(context -> {
										ServerPlayer player = EntityArgument.getPlayer(context, "player");
										CyborgData data = Cyborg.get(player);
										Cyborg.set(player, data.withFuel(data.tank()));
										context.getSource().sendSuccess(() -> Component.literal("Filled the Cola tank.").withStyle(ChatFormatting.GOLD), true);
										return 1;
									}))));
		});
	}

	private static int huntCommand(CommandContext<CommandSourceStack> context) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		HuntUnit unit = HuntUnit.byId(StringArgumentType.getString(context, "unit"));
		if (unit == null) {
			context.getSource().sendFailure(Component.literal("Units: pacifista, mark_iii, s_bear, s_hawk, s_snake, s_shark"));
			return 0;
		}
		String name = VegapunkHunts.start(player, unit, true);
		if (name == null) {
			context.getSource().sendFailure(Component.literal("No dry ground close by for it to stand on."));
			return 0;
		}
		return 1;
	}

	private static int setCommand(CommandContext<CommandSourceStack> context) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
		ServerPlayer player = EntityArgument.getPlayer(context, "player");
		CyborgUpgrade upgrade = CyborgUpgrade.byId(StringArgumentType.getString(context, "upgrade"));
		if (upgrade == null) {
			context.getSource().sendFailure(Component.literal("Unknown upgrade."));
			return 0;
		}
		int tier = IntegerArgumentType.getInteger(context, "tier");
		Cyborg.set(player, Cyborg.get(player).withTier(upgrade, tier));
		context.getSource().sendSuccess(() -> Component.literal(upgrade.title + " set to tier " + tier + " for "
				+ player.getName().getString()).withStyle(ChatFormatting.GOLD), true);
		return 1;
	}

	private static int status(CommandSourceStack source, ServerPlayer player) {
		CyborgData data = Cyborg.get(player);
		if (!data.any()) {
			source.sendSuccess(() -> Component.literal("You're all flesh and blood. Beat Pacifista and Seraphim for parts, build cyborg "
					+ "modules at the Shipwright's Bench, then right-click a module to install it.").withStyle(ChatFormatting.GRAY), false);
			return 0;
		}
		source.sendSuccess(() -> Component.literal("Cyborg body").withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD), false);
		for (CyborgUpgrade upgrade : CyborgUpgrade.values()) {
			int tier = data.tier(upgrade);
			source.sendSuccess(() -> Component.literal(" " + upgrade.title + ": ").withStyle(ChatFormatting.WHITE)
					.append(Component.literal(tier == 0 ? "not installed" : "tier " + Cyborg.roman(tier) + " (" + upgrade.tiers.get(tier - 1) + ")")
							.withStyle(tier == 0 ? ChatFormatting.DARK_GRAY : ChatFormatting.GREEN)), false);
		}
		if (data.tank() > 0) {
			source.sendSuccess(() -> Component.literal(" Cola: " + Cyborg.fuelText(data) + " (refills from Colas and Cola Crates in your bag)")
					.withStyle(ChatFormatting.AQUA), false);
		}
		return 1;
	}
}
