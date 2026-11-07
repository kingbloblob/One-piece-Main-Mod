package com.onepiecemod.multiplayer;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import com.mojang.brigadier.suggestion.SuggestionProvider;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Prediction;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

/**
 * Co-op commands, merged into /crew:
 *   /crew role <player> <role|none>       captain: give a crewmate a job (First Mate, Swordsman, Doctor, ...)
 *   /crew roles                           every job and what it does for the crew
 *   /crew poster                          the crew's Wanted Poster (costs 1 paper)
 *   /crew challenge <captain> [berries]   captain or First Mate: challenge another crew to a sea battle
 *   /crew challenge accept <captain>      accept a challenge
 *   /crew surrender                       give up the sea battle
 *   /crew battle                          how the sea battle is going
 */
public class CoopCommands {
	private static final SuggestionProvider<CommandSourceStack> MEMBERS = (context, builder) -> {
		MinecraftServer server = context.getSource().getServer();
		ServerPlayer player = context.getSource().getPlayer();
		PirateCrew crew = player == null ? null : PlayerCrews.get(server, PlayerCrews.captainOf(server, player.getUUID()));
		List<String> names = new ArrayList<>();
		if (crew != null) {
			crew.members.forEach(id -> names.add(crew.nameOf(id)));
		}
		return SharedSuggestionProvider.suggest(names, builder);
	};

	private static final SuggestionProvider<CommandSourceStack> ROLES = (context, builder) -> {
		List<String> ids = new ArrayList<>(PlayerRoles.ids());
		ids.add("none");
		return SharedSuggestionProvider.suggest(ids, builder);
	};

	private static final SuggestionProvider<CommandSourceStack> CHALLENGERS = (context, builder) -> {
		MinecraftServer server = context.getSource().getServer();
		ServerPlayer player = context.getSource().getPlayer();
		UUID captain = player == null ? null : PlayerRoles.officerOf(server, player);
		if (captain == null && player != null) {
			captain = player.getUUID();
		}
		return SharedSuggestionProvider.suggest(captain == null ? List.of() : SeaWars.challengers(server, captain), builder);
	};

	public static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("crew")
						.then(Commands.literal("role")
								.then(Commands.argument("player", StringArgumentType.word()).suggests(MEMBERS)
										.then(Commands.argument("role", StringArgumentType.word()).suggests(ROLES).executes(CoopCommands::role))))
						.then(Commands.literal("roles").executes(CoopCommands::roles))
						.then(Commands.literal("poster").executes(CoopCommands::poster))
						.then(Commands.literal("challenge")
								.then(Commands.literal("accept")
										.then(Commands.argument("captain", StringArgumentType.word()).suggests(CHALLENGERS).executes(CoopCommands::accept)))
								.then(Commands.argument("captain", EntityArgument.player())
										.executes(context -> challenge(context, 0))
										.then(Commands.argument("berries", IntegerArgumentType.integer(0, 100_000))
												.executes(context -> challenge(context, IntegerArgumentType.getInteger(context, "berries"))))))
						.then(Commands.literal("surrender").executes(CoopCommands::surrender))
						.then(Commands.literal("battle").executes(CoopCommands::battle))
		));
	}

	// ---- Roles ----

	private static int role(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer captain = context.getSource().getPlayerOrException();
		MinecraftServer server = context.getSource().getServer();
		PirateCrew crew = PlayerCrews.get(server, captain.getUUID());
		if (crew == null) {
			return fail(context, "Only a captain with players in their crew can hand out jobs. Invite someone with /crew invite <player>.");
		}
		String name = StringArgumentType.getString(context, "player");
		UUID member = null;
		for (UUID id : crew.members) {
			if (crew.nameOf(id).equalsIgnoreCase(name)) {
				member = id;
			}
		}
		if (member == null) {
			return fail(context, "Nobody by that name is in your crew. See /crew members.");
		}
		String role = StringArgumentType.getString(context, "role").toLowerCase(java.util.Locale.ROOT);
		String memberName = crew.nameOf(member);
		if (role.equals("none")) {
			crew.roles.remove(member);
			PlayerCrews.save(server);
			PlayerCrews.tell(server, captain.getUUID(), Component.literal(memberName + " is a deckhand again.").withStyle(ChatFormatting.YELLOW));
			return 1;
		}
		if (!PlayerRoles.isRole(role)) {
			return fail(context, "No such job. Try one of: " + String.join(", ", PlayerRoles.ids()) + " (or none).");
		}
		UUID holder = PlayerRoles.holder(crew, role);
		if (holder != null && !holder.equals(member)) {
			crew.roles.remove(holder);
			PlayerCrews.tell(server, captain.getUUID(), Component.literal(crew.nameOf(holder) + " hands the " + PlayerRoles.title(role)
					+ " job over.").withStyle(ChatFormatting.GRAY));
		}
		crew.roles.put(member, role);
		PlayerCrews.save(server);
		PlayerCrews.tell(server, captain.getUUID(), Component.literal(memberName + " is now the crew's " + PlayerRoles.title(role) + "! "
				+ PlayerRoles.perk(role) + ".").withStyle(ChatFormatting.GOLD));
		return 1;
	}

	private static int roles(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		MinecraftServer server = context.getSource().getServer();
		PirateCrew crew = PlayerCrews.get(server, PlayerCrews.captainOf(server, player.getUUID()));
		player.sendSystemMessage(Component.literal("=== Crew jobs (the captain sets them with /crew role <player> <job>) ===").withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal("Each job helps every crewmate within 48 blocks of the player doing it.").withStyle(ChatFormatting.GRAY));
		for (String id : PlayerRoles.ids()) {
			UUID holder = crew == null ? null : PlayerRoles.holder(crew, id);
			player.sendSystemMessage(Component.literal(PlayerRoles.title(id) + " (" + id + ")").withStyle(ChatFormatting.YELLOW)
					.append(Component.literal(": " + PlayerRoles.perk(id)).withStyle(ChatFormatting.WHITE))
					.append(Component.literal(holder != null ? "  - " + crew.nameOf(holder) : "").withStyle(ChatFormatting.AQUA)));
		}
		return 1;
	}

	// ---- Shared bounty ----

	private static int poster(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		MinecraftServer server = context.getSource().getServer();
		UUID captain = PlayerCrews.captainOf(server, player.getUUID());
		if (captain == null) {
			return fail(context, "You're not in a player crew. Your own poster is /bounty poster.");
		}
		if (!player.isCreative()) {
			int slot = player.getInventory().findSlotMatchingItem(new ItemStack(Items.PAPER));
			if (slot < 0) {
				return fail(context, "You need a sheet of paper to print the crew's poster.");
			}
			player.getInventory().removeItem(slot, 1);
		}
		ItemStack poster = CrewBounties.poster(server, captain);
		if (!player.getInventory().add(poster)) {
			player.drop(poster, false, Prediction.SERVER_ONLY);
		}
		player.sendSystemMessage(Component.literal("You printed the " + PlayerCrews.crewName(server, captain)
				+ "'s Wanted Poster. Right-click it to read it.").withStyle(ChatFormatting.GOLD));
		return 1;
	}

	// ---- Sea battles ----

	private static int challenge(CommandContext<CommandSourceStack> context, int wager) throws CommandSyntaxException {
		ServerPlayer sender = context.getSource().getPlayerOrException();
		ServerPlayer target = EntityArgument.getPlayer(context, "captain");
		MinecraftServer server = context.getSource().getServer();
		UUID ours = officerCrew(server, sender);
		if (ours == null) {
			return fail(context, "Only a captain (or their First Mate) can challenge another crew. Start one with /crew create <name>.");
		}
		UUID theirs = officerCrew(server, target);
		if (theirs == null) {
			UUID theirCaptain = PlayerCrews.captainOf(server, target.getUUID());
			return fail(context, theirCaptain != null
					? target.getName().getString() + " isn't their crew's captain or First Mate. Challenge " + SeaWars.nameOf(server, theirCaptain) + "."
					: target.getName().getString() + " doesn't captain a crew.");
		}
		String problem = SeaWars.challenge(server, sender, ours, theirs, wager);
		return problem == null ? 1 : fail(context, problem);
	}

	private static int accept(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer sender = context.getSource().getPlayerOrException();
		MinecraftServer server = context.getSource().getServer();
		UUID ours = officerCrew(server, sender);
		if (ours == null) {
			return fail(context, "Only your captain (or First Mate) can accept a challenge.");
		}
		String problem = SeaWars.accept(server, sender, ours, StringArgumentType.getString(context, "captain"));
		return problem == null ? 1 : fail(context, problem);
	}

	private static int surrender(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer sender = context.getSource().getPlayerOrException();
		MinecraftServer server = context.getSource().getServer();
		UUID ours = officerCrew(server, sender);
		if (ours == null) {
			return fail(context, "Only your captain (or First Mate) can surrender.");
		}
		String problem = SeaWars.surrender(server, ours);
		return problem == null ? 1 : fail(context, problem);
	}

	private static int battle(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		MinecraftServer server = context.getSource().getServer();
		SeaWars.status(server, player, PlayerCrews.crewKey(server, player));
		return 1;
	}

	/** The captain id of the crew this player may speak for (captain or First Mate), making the captain's player crew if needed. */
	private static UUID officerCrew(MinecraftServer server, ServerPlayer player) {
		PlayerCrews.ensure(player);
		return PlayerRoles.officerOf(server, player);
	}

	private static int fail(CommandContext<CommandSourceStack> context, String message) {
		context.getSource().sendFailure(Component.literal(message));
		return 0;
	}
}
