package com.onepiecemod.crew;

import java.util.Arrays;
import java.util.UUID;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.suggestion.SuggestionProvider;

import net.minecraft.util.Prediction;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

/**
 * The /crew chat commands:
 *   /crew create <name>    start a crew, you are the captain
 *   /crew                  show your crew and what each open role costs
 *   /crew recruits         at a Pirate Tavern: see which jobs have recruits waiting
 *   /crew hire <role>      see the 3 candidates for a job (swordsman, navigator, sniper, cook, ...)
 *   /crew hire <role> <n>  hire candidate 1, 2 or 3 (clicking [Hire] in chat does this for you)
 *   /crew blueprint        read how to build a Pirate Tavern
 *   /crew dismiss <role>   send a crewmate away
 *   /crew disband          end your crew
 *   /crew call             everyone nearby enough to hear comes to you and follows
 *   /crew all <mode>       every crewmate within 32 blocks follows, waits or works
 * Press U for the crew window, which does most of this with buttons.
 */
public class CrewCommands {
	private static final SuggestionProvider<CommandSourceStack> ROLES = (context, builder) ->
			SharedSuggestionProvider.suggest(Arrays.stream(CrewRole.values()).map(CrewRole::id), builder);

	public static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("crew")
						.executes(CrewCommands::info)
						.then(Commands.literal("info").executes(CrewCommands::info))
						.then(Commands.literal("create")
								.then(Commands.argument("name", StringArgumentType.greedyString()).executes(CrewCommands::create)))
						.then(Commands.literal("recruits").executes(context -> {
							showRecruitBoard(context.getSource().getPlayerOrException());
							return 1;
						}))
						.then(Commands.literal("blueprint").executes(context -> {
							CrewTavern.printPlan(context.getSource().getPlayerOrException());
							return 1;
						}))
						.then(Commands.literal("hire")
								.then(Commands.argument("role", StringArgumentType.word()).suggests(ROLES).executes(CrewCommands::candidates)
										.then(Commands.argument("choice", IntegerArgumentType.integer(1, CrewVariant.COUNT)).executes(context -> hire(context, null))
												.then(Commands.argument("list", IntegerArgumentType.integer(0))
														.executes(context -> hire(context, IntegerArgumentType.getInteger(context, "list")))))))
						.then(Commands.literal("dismiss")
								.then(Commands.argument("role", StringArgumentType.word()).suggests(ROLES).executes(CrewCommands::dismiss)))
						.then(Commands.literal("disband").executes(CrewCommands::disband))
						.then(Commands.literal("call").executes(context -> {
							callCrew(context.getSource().getPlayerOrException());
							return 1;
						}))
						.then(Commands.literal("all")
								.then(Commands.literal("follow").executes(context -> orderAll(context, CrewMode.FOLLOW)))
								.then(Commands.literal("wait").executes(context -> orderAll(context, CrewMode.WAIT)))
								.then(Commands.literal("work").executes(context -> orderAll(context, CrewMode.WORK))))
		));
	}

	private static int create(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		String name = StringArgumentType.getString(context, "name").trim();
		if (player.getAttached(CrewAttachments.CREW) != null) {
			context.getSource().sendFailure(Component.literal("You already lead a crew. Use /crew disband first."));
			return 0;
		}
		if (name.isEmpty() || name.length() > 32) {
			context.getSource().sendFailure(Component.literal("Pick a crew name between 1 and 32 letters."));
			return 0;
		}
		createCrew(player, name);
		return 1;
	}

	/** Starts a crew with this player as captain and hands them a Tavern Blueprint. */
	public static void createCrew(ServerPlayer player, String name) {
		player.setAttached(CrewAttachments.CREW, Crew.create(name));
		player.getInventory().placeItemBackInInventory(new ItemStack(CrewBlocks.TAVERN_BLUEPRINT), Prediction.SERVER_ONLY);
		player.sendSystemMessage(Component.literal("The " + name + " set sail! Captain " + player.getName().getString()
				+ ", recruits wait at a Pirate Tavern. Here's a Tavern Blueprint: use it to see how to build one.")
				.withStyle(ChatFormatting.GOLD));
		CrewPayloads.refresh(player);
	}

	private static int info(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		Crew crew = player.getAttached(CrewAttachments.CREW);
		if (crew == null) {
			context.getSource().sendFailure(Component.literal("You don't have a crew yet. Use /crew create <name>."));
			return 0;
		}

		int price = CrewHiring.cost(crew.hires());
		player.sendSystemMessage(Component.literal("=== " + crew.name() + " (Captain " + player.getName().getString() + ") ===")
				.withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal(crew.size() + "/9 crewmates. Next hire costs " + price + " Berries. Press U for the crew window.")
				.withStyle(ChatFormatting.YELLOW));

		for (CrewRole role : CrewRole.values()) {
			MutableComponent line = Component.literal(role.title() + ": ").withStyle(ChatFormatting.WHITE);
			UUID memberId = crew.member(role);
			if (memberId != null) {
				Entity member = findLoaded(context.getSource().getServer(), memberId);
				String name = member instanceof CrewmateEntity crewmate
						? crewmate.getName().getString() + " (level " + crewmate.getCrewLevel() + " " + crewmate.getPersonality().title() + " "
								+ crewmate.getVariant().title() + ")"
						: "hired (not nearby)";
				line.append(Component.literal(name).withStyle(ChatFormatting.GREEN));
			} else {
				String needs = role.trialCount() + " " + CrewHiring.itemName(role.trialItem());
				if (role.minCrew() > 0) {
					needs += ", needs " + role.minCrew() + " crewmates";
				}
				line.append(Component.literal("open - " + needs + " (" + role.inspiredBy() + ")").withStyle(ChatFormatting.GRAY));
			}
			player.sendSystemMessage(line);
		}
		return 1;
	}

	// The crewmate's entity, if it's in a loaded part of any world. Otherwise null.
	private static Entity findLoaded(MinecraftServer server, UUID id) {
		for (ServerLevel level : server.getAllLevels()) {
			Entity entity = level.getEntity(id);
			if (entity != null) {
				return entity;
			}
		}
		return null;
	}

	private static CrewRole roleArgument(CommandContext<CommandSourceStack> context) {
		CrewRole role = CrewRole.byId(StringArgumentType.getString(context, "role"));
		if (role == null) {
			context.getSource().sendFailure(Component.literal("That's not a crew role. Try swordsman, navigator, sniper, cook, doctor, shipwright, archaeologist, musician or helmsman."));
		}
		return role;
	}

	// listCode: which day's list the [Hire] button came from (null when typed by hand).
	private static int hire(CommandContext<CommandSourceStack> context, Integer listCode) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		CrewRole role = roleArgument(context);
		if (role == null) {
			return 0;
		}
		boolean hired = CrewHiring.hire(player, role, IntegerArgumentType.getInteger(context, "choice") - 1, listCode);
		CrewPayloads.refresh(player);
		return hired ? 1 : 0;
	}

	// Lists the 3 candidates for a job, each with a clickable [Hire] button.
	private static int candidates(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		CrewRole role = roleArgument(context);
		if (role == null) {
			return 0;
		}
		Crew crew = CrewHiring.checkCanHire(player, role);
		if (crew == null) {
			return 0;
		}
		player.sendSystemMessage(Component.literal("=== " + role.title() + " recruits (" + role.inspiredBy() + ") ===").withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal("Each also asks for " + role.trialCount() + " " + CrewHiring.itemName(role.trialItem())
				+ ". Job: " + role.job() + ". Perk: " + role.perk() + ".").withStyle(ChatFormatting.GRAY));
		int number = 1;
		int listCode = CrewCandidates.listCode(player, crew);
		for (CrewCandidates.Candidate candidate : CrewCandidates.forRole(player, crew, role)) {
			String command = "/crew hire " + role.id() + " " + number + " " + listCode;
			MutableComponent line = Component.literal(number + ". " + candidate.name() + ", ").withStyle(ChatFormatting.WHITE)
					.append(Component.literal(candidate.personality().title() + " " + candidate.variant().title()).withStyle(style -> style
							.withColor(ChatFormatting.AQUA)
							.withHoverEvent(new HoverEvent.ShowText(Component.literal(candidate.personality().description())))))
					.append(Component.literal(" - " + candidate.health() + " health, " + candidate.damage() + " strength, "
							+ candidate.variant().speedWord() + " - " + candidate.price() + " Berries ").withStyle(ChatFormatting.GRAY))
					.append(Component.literal("[Hire]").withStyle(style -> style
							.withColor(ChatFormatting.GREEN)
							.withBold(true)
							.withClickEvent(new ClickEvent.RunCommand(command))
							.withHoverEvent(new HoverEvent.ShowText(Component.literal("Hire " + candidate.fullName())))));
			player.sendSystemMessage(line);
			number++;
		}
		player.sendSystemMessage(Component.literal("New recruits arrive every day.").withStyle(ChatFormatting.DARK_GRAY));
		return 1;
	}

	/** What the Recruitment Board shows: every job, and a button to see its recruits. */
	public static void showRecruitBoard(ServerPlayer player) {
		Crew crew = player.getAttached(CrewAttachments.CREW);
		if (crew == null) {
			player.sendSystemMessage(Component.literal("Recruits only sign up with a real captain. Start a crew with /crew create <name>.")
					.withStyle(ChatFormatting.YELLOW));
			return;
		}
		player.sendSystemMessage(Component.literal("=== Recruitment Board: " + crew.name() + " ===").withStyle(ChatFormatting.GOLD));
		for (CrewRole role : CrewRole.values()) {
			MutableComponent line = Component.literal(role.title() + ": ").withStyle(ChatFormatting.WHITE);
			if (crew.member(role) != null) {
				line.append(Component.literal("hired").withStyle(ChatFormatting.GREEN));
			} else if (crew.size() < role.minCrew()) {
				line.append(Component.literal("joins once you have " + role.minCrew() + " crewmates").withStyle(ChatFormatting.DARK_GRAY));
			} else {
				String command = "/crew hire " + role.id();
				line.append(Component.literal("[See recruits]").withStyle(style -> style
						.withColor(ChatFormatting.AQUA)
						.withClickEvent(new ClickEvent.RunCommand(command))
						.withHoverEvent(new HoverEvent.ShowText(Component.literal("Meet the " + role.title() + " candidates")))));
			}
			player.sendSystemMessage(line);
		}
	}

	/** Everyone who can hear the call (anywhere in a loaded part of any world) comes to the captain and follows. */
	public static void callCrew(ServerPlayer player) {
		Crew crew = player.getAttached(CrewAttachments.CREW);
		if (crew == null || crew.members().isEmpty()) {
			player.sendSystemMessage(Component.literal("You don't have any crewmates to call.").withStyle(ChatFormatting.RED));
			return;
		}
		int came = 0;
		int down = 0;
		for (UUID id : crew.members().values()) {
			CrewmateEntity crewmate = CrewRoster.find(player.level().getServer(), id);
			if (crewmate == null) {
				continue;
			}
			if (crewmate.isKnockedOut()) {
				down++;
				continue;
			}
			crewmate.setMode(CrewMode.FOLLOW);
			if (crewmate.level() != player.level() || crewmate.distanceToSqr(player) > 16) {
				CrewRoster.bringTo(crewmate, player);
			}
			came++;
		}
		int away = crew.size() - came - down;
		String message = came + " crewmate" + (came == 1 ? "" : "s") + " answered your call.";
		if (down > 0) {
			message += " " + down + " knocked out.";
		}
		if (away > 0) {
			message += " " + away + " too far away to hear (go to them, then call again).";
		}
		player.sendSystemMessage(Component.literal(message).withStyle(ChatFormatting.GOLD));
		CrewPayloads.refresh(player);
	}

	// Sets the mode of every crewmate within 32 blocks.
	private static int orderAll(CommandContext<CommandSourceStack> context, CrewMode newMode) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		Crew crew = player.getAttached(CrewAttachments.CREW);
		int count = 0;
		if (crew != null) {
			for (UUID id : crew.members().values()) {
				CrewmateEntity crewmate = CrewRoster.find(player.level().getServer(), id);
				if (crewmate != null && crewmate.level() == player.level() && crewmate.distanceToSqr(player) < 32 * 32
						&& !crewmate.isKnockedOut()) {
					crewmate.setMode(newMode);
					count++;
				}
			}
		}
		int total = count;
		String doing = switch (newMode) {
			case FOLLOW -> "following you";
			case WAIT -> "waiting";
			case WORK -> "working where they stand";
		};
		context.getSource().sendSuccess(() -> Component.literal(total + " crewmate" + (total == 1 ? " is " : "s are ") + doing + ".")
				.withStyle(ChatFormatting.AQUA), false);
		CrewPayloads.refresh(player);
		return total;
	}

	private static int dismiss(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		Crew crew = player.getAttached(CrewAttachments.CREW);
		CrewRole role = CrewRole.byId(StringArgumentType.getString(context, "role"));
		if (crew == null || role == null || crew.member(role) == null) {
			context.getSource().sendFailure(Component.literal("There's nobody in that role to dismiss."));
			return 0;
		}
		CrewHiring.dismiss(context.getSource().getServer(), crew.member(role));
		player.setAttached(CrewAttachments.CREW, crew.withoutMember(role));
		context.getSource().sendSuccess(() -> Component.literal("Your " + role.title() + " left the crew."), false);
		CrewPayloads.refresh(player);
		return 1;
	}

	private static int disband(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		Crew crew = player.getAttached(CrewAttachments.CREW);
		if (crew == null) {
			context.getSource().sendFailure(Component.literal("You don't have a crew."));
			return 0;
		}
		for (UUID memberId : crew.members().values()) {
			CrewHiring.dismiss(context.getSource().getServer(), memberId);
		}
		player.removeAttached(CrewAttachments.CREW);
		context.getSource().sendSuccess(() -> Component.literal("The " + crew.name() + " has disbanded."), false);
		CrewPayloads.refresh(player);
		return 1;
	}
}
