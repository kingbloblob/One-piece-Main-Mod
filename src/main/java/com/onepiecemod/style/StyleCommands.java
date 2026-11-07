package com.onepiecemod.style;

import java.util.Arrays;
import java.util.List;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.suggestion.SuggestionProvider;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

/**
 * The /style chat commands:
 *   /style               show your styles, your moves and how to learn the others
 *   /style use <style>   switch to a style you know (santoryu, black_leg, ryusoken, sogeking...)
 *   /style learn <style> learn a style instantly (Creative mode only, for testing)
 */
public class StyleCommands {
	private static final SuggestionProvider<CommandSourceStack> STYLES = (context, builder) ->
			SharedSuggestionProvider.suggest(Arrays.stream(FightingStyle.values()).map(FightingStyle::id), builder);

	public static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("style")
						.executes(StyleCommands::info)
						.then(Commands.literal("use")
								.then(Commands.argument("style", StringArgumentType.word()).suggests(STYLES).executes(StyleCommands::use)))
						.then(Commands.literal("learn")
								.then(Commands.argument("style", StringArgumentType.word()).suggests(STYLES).executes(StyleCommands::learn)))
		));
	}

	private static int info(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		FightingStyle active = StyleAttachments.active(player);
		Technique selected = StyleMoves.selected(player);
		player.sendSystemMessage(Component.literal("=== Fighting Styles ===").withStyle(ChatFormatting.GOLD));

		for (FightingStyle style : FightingStyle.values()) {
			if (!StyleAttachments.knows(player, style)) {
				String needs = style.berryCost() + " Berries";
				if (style.trialCount() > 0) {
					needs += ", " + style.trialCount() + " " + style.trialItem().getName(new ItemStack(style.trialItem())).getString();
				}
				if (style.swordsNeeded() > 0) {
					needs += ", " + style.swordsNeeded() + " swords";
				}
				if (style.bossesNeeded() > 0) {
					needs += ", " + style.bossesNeeded() + " bosses beaten";
				}
				player.sendSystemMessage(Component.literal(style.title() + ": not learned. Sneak + right-click "
						+ capitalize(style.master()) + " (their Vivre Card points the way) with " + needs + ".").withStyle(ChatFormatting.GRAY));
				continue;
			}

			boolean using = style == active;
			player.sendSystemMessage(Component.literal(style.title() + (using ? " (using)" : " (/style use " + style.id() + ")"))
					.withStyle(using ? ChatFormatting.GREEN : ChatFormatting.WHITE));
			int mastery = StyleMastery.level(player, style);
			player.sendSystemMessage(Component.literal("  Mastery " + mastery + "/" + StyleMastery.MAX_LEVEL
					+ (mastery >= StyleMastery.MAX_LEVEL ? " (mastered)" : " (" + StyleMastery.pointsToNext(player, style) + " more points to level up)")
					+ ": +" + (5 * mastery) + "% damage, -" + (4 * mastery) + "% cooldowns").withStyle(ChatFormatting.AQUA));
			List<Technique> unlocked = style.unlockedTechniques(player);
			for (Technique technique : style.techniques()) {
				String marker = technique == selected ? "> " : "  ";
				if (unlocked.contains(technique)) {
					player.sendSystemMessage(Component.literal(marker + technique.title() + ": " + technique.description()
							+ " (" + StyleMastery.cooldownTicks(player, technique) / 20 + "s)").withStyle(technique == selected ? ChatFormatting.YELLOW : ChatFormatting.GRAY));
				} else {
					player.sendSystemMessage(Component.literal("  " + technique.title() + ": locked. Beat " + capitalize(technique.unlockBoss())
							+ "'s boss to unlock it.").withStyle(ChatFormatting.DARK_GRAY));
				}
			}
			player.sendSystemMessage(Component.literal("  Always on: " + alwaysOn(style)).withStyle(ChatFormatting.GRAY));
			player.sendSystemMessage(Component.literal("  [Paths] ").withStyle(s -> s.withColor(ChatFormatting.GOLD).withBold(true)
							.withClickEvent(new net.minecraft.network.chat.ClickEvent.RunCommand("/style paths " + style.id())))
					.append(Component.literal("upgrades from mastery 3, trained by " + capitalize(style.master()) + ".").withStyle(ChatFormatting.GRAY)));
		}
		player.sendSystemMessage(Component.literal("Z uses the selected move (>), Shift+Z picks the next one.").withStyle(ChatFormatting.YELLOW));
		return 1;
	}

	private static String alwaysOn(FightingStyle style) {
		return switch (style) {
			case SANTORYU -> "+1.5 damage for each extra sword you carry (up to 3 swords).";
			case BLACK_LEG -> "kicks hit like an iron sword, Sky Walk (jump up to " + StyleMoves.SKY_WALK_JUMPS + " times in mid-air).";
			case FISHMAN_KARATE -> "stronger punches (double in water), fast swimming and water breathing.";
			case ROKUSHIKI -> "Geppo (jump up to " + StyleMoves.GEPPO_JUMPS + " times in mid-air) and Kami-e (1 in 4 melee hits miss you).";
			case RYUSOKEN -> "+4 punch damage, and anything you punch is weakened for 3 seconds.";
			case NITORYU -> "+3 damage while you hold a sword in each hand.";
			case KITSUNEBI -> "fire and lava can't hurt you while you hold a sword.";
			case SOUL_FENCING -> "+2 sword damage.";
			case FIST_OF_LOVE -> "+6 punch damage and every punch knocks enemies far away.";
			case SOGEKING -> "none. Sogeking relies on tricks, so every move is a shot.";
		};
	}

	private static int use(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		FightingStyle style = FightingStyle.byId(StringArgumentType.getString(context, "style"));
		if (style == null || !StyleAttachments.knows(player, style)) {
			fail(player, Component.literal("You don't know that style. Type /style to see what you know."));
			return 0;
		}
		StyleAttachments.setActive(player, style);
		player.sendSystemMessage(Component.literal("You're now fighting with " + style.title() + ".").withStyle(ChatFormatting.GOLD));
		return 1;
	}

	private static int learn(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		FightingStyle style = FightingStyle.byId(StringArgumentType.getString(context, "style"));
		if (!player.isCreative()) {
			fail(player, Component.literal("/style learn only works in Creative mode. In Survival, find the style's master."));
			return 0;
		}
		if (style == null) {
			fail(player, Component.literal("That's not a style. Type /style to see them all."));
			return 0;
		}
		StyleMasters.teach(player, style);
		return 1;
	}

	// Replies go straight to the player's chat (like /haki), so they show even if the
	// sendCommandFeedback game rule is off or the command was run silently.
	private static void fail(ServerPlayer player, Component message) {
		player.sendSystemMessage(message.copy().withStyle(ChatFormatting.RED));
	}

	private static String capitalize(String id) {
		String spaced = id.replace('_', ' ');
		return Character.toUpperCase(spaced.charAt(0)) + spaced.substring(1);
	}
}
