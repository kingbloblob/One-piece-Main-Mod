package com.onepiecemod.haki;

import java.util.function.Consumer;

import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

/**
 * The /haki chat commands (the V, B and G keys just run these for you):
 *   /haki               show your Haki levels and how to train them
 *   /haki observation   switch Observation Haki on or off (V)
 *   /haki armament      switch Armament Haki on or off (B)
 *   /haki conqueror     release Conqueror's Haki (G)
 */
public class HakiCommands {
	public static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("haki")
						.executes(HakiCommands::info)
						.then(Commands.literal("observation").executes(context -> run(context, HakiPowers::toggleObservation)))
						.then(Commands.literal("armament").executes(context -> run(context, HakiPowers::toggleArmament)))
						.then(Commands.literal("conqueror").executes(context -> run(context, HakiPowers::releaseConqueror)))
		));
	}

	private static int run(CommandContext<CommandSourceStack> context, Consumer<ServerPlayer> action)
			throws CommandSyntaxException {
		action.accept(context.getSource().getPlayerOrException());
		return 1;
	}

	private static int info(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		HakiData haki = HakiAttachments.get(player);
		player.sendSystemMessage(Component.literal("=== Your Haki ===").withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(line("Observation (V)", haki.observationXp(), haki.observationOn(),
				"take hits from mobs, 5x faster while blind"));
		player.sendSystemMessage(line("Armament (B)", haki.armamentXp(), haki.armamentOn(),
				"punch mobs with bare hands"));
		if (haki.conqueror()) {
			player.sendSystemMessage(Component.literal("Conqueror's (G): level " + haki.conquerorLevel()
					+ ". Grows when you beat bosses and use it.").withStyle(ChatFormatting.DARK_PURPLE));
		} else {
			player.sendSystemMessage(Component.literal("Conqueror's: not awakened. Rare: beating bosses might awaken it.")
					.withStyle(ChatFormatting.GRAY));
		}
		player.sendSystemMessage(Component.literal("Tip: sneak + right-click Rayleigh for a lesson (20 Berries).")
				.withStyle(ChatFormatting.YELLOW));
		player.sendSystemMessage(Component.literal("[Haki Paths] ").withStyle(style -> style.withColor(ChatFormatting.GOLD).withBold(true)
						.withClickEvent(new net.minecraft.network.chat.ClickEvent.RunCommand("/haki paths")))
				.append(Component.literal("From level 2, pick upgrades at Rayleigh, Shanks or Boa Hancock (/haki paths).")
						.withStyle(ChatFormatting.GRAY)));
		return 1;
	}

	private static Component line(String name, int xp, boolean on, String howToTrain) {
		int level = HakiData.level(xp);
		String text;
		if (level == 0) {
			text = name + ": not awakened. " + HakiData.xpToNext(xp) + " training to go (" + howToTrain + ").";
		} else if (level >= HakiData.MAX_LEVEL) {
			text = name + ": MASTERED, " + (on ? "on" : "off") + ".";
		} else {
			text = name + ": level " + level + "/" + HakiData.MAX_LEVEL + ", " + (on ? "on" : "off") + ". "
					+ HakiData.xpToNext(xp) + " training to next level.";
		}
		return Component.literal(text).withStyle(level == 0 ? ChatFormatting.GRAY : ChatFormatting.WHITE);
	}
}
