package com.onepiecemod.multiplayer;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

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

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.crew.CrewAttachments;

/**
 * Adds the multiplayer commands to /crew (the crew feature has create, hire, dismiss and disband):
 *   /crew invite <player>    captain: invite a player into your crew
 *   /crew join <captain>     accept an invite
 *   /crew leave              leave your crew
 *   /crew kick <player>      captain: remove a player
 *   /crew members            everyone in your crew, their bounties and where they are
 *   /crew bounty             your crew's total bounty
 *   /crew say <message>      talk to your crew only
 *   /crew ally <captain>     ask another crew for an alliance (or accept theirs)
 *   /crew unally <captain>   end an alliance (captain's name or the crew's name)
 *   /crew allies             list your allies
 *   /crew allysay <message>  talk to your crew and every allied crew
 */
public class PlayerCrewCommands {
	private static final long INVITE_TICKS = 20 * 60 * 5; // Invites last 5 minutes.

	/** invited player -> (captain -> game tick the invite runs out). Not saved: invites are quick. */
	private static final Map<UUID, Map<UUID, Long>> INVITES = new HashMap<>();
	/** captain asked -> (captain asking -> game tick the request runs out). */
	private static final Map<UUID, Map<UUID, Long>> ALLY_REQUESTS = new HashMap<>();

	private static final SuggestionProvider<CommandSourceStack> MY_INVITES = (context, builder) ->
			SharedSuggestionProvider.suggest(namesOf(context.getSource().getServer(), pending(INVITES, context.getSource())), builder);

	private static final SuggestionProvider<CommandSourceStack> MY_MEMBERS = (context, builder) -> {
		MinecraftServer server = context.getSource().getServer();
		PirateCrew crew = context.getSource().getPlayer() != null
				? PlayerCrews.get(server, PlayerCrews.captainOf(server, context.getSource().getPlayer().getUUID())) : null;
		List<String> names = new ArrayList<>();
		if (crew != null) {
			crew.members.forEach(id -> names.add(crew.nameOf(id)));
		}
		return SharedSuggestionProvider.suggest(names, builder);
	};

	private static final SuggestionProvider<CommandSourceStack> MY_ALLIES = (context, builder) -> {
		MinecraftServer server = context.getSource().getServer();
		PirateCrew crew = context.getSource().getPlayer() != null ? PlayerCrews.get(server, context.getSource().getPlayer().getUUID()) : null;
		List<String> names = new ArrayList<>();
		if (crew != null) {
			for (UUID ally : crew.allies) {
				PirateCrew other = PlayerCrews.get(server, ally);
				if (other != null) {
					names.add(other.nameOf(ally));
					names.add(other.name); // Crew names can have spaces: the argument takes the rest of the line.
				}
			}
		}
		return SharedSuggestionProvider.suggest(names, builder);
	};

	public static void initialize() {
		// Brigadier merges this with the crew feature's own /crew command.
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("crew")
						.then(Commands.literal("invite")
								.then(Commands.argument("player", EntityArgument.player()).executes(PlayerCrewCommands::invite)))
						.then(Commands.literal("join")
								.then(Commands.argument("captain", StringArgumentType.word()).suggests(MY_INVITES).executes(PlayerCrewCommands::join)))
						.then(Commands.literal("leave").executes(PlayerCrewCommands::leave))
						.then(Commands.literal("kick")
								.then(Commands.argument("player", StringArgumentType.word()).suggests(MY_MEMBERS).executes(PlayerCrewCommands::kick)))
						.then(Commands.literal("members").executes(PlayerCrewCommands::members))
						.then(Commands.literal("bounty").executes(PlayerCrewCommands::bounty))
						.then(Commands.literal("say")
								.then(Commands.argument("message", StringArgumentType.greedyString()).executes(context -> say(context, false))))
						.then(Commands.literal("allysay")
								.then(Commands.argument("message", StringArgumentType.greedyString()).executes(context -> say(context, true))))
						.then(Commands.literal("ally")
								.then(Commands.argument("captain", EntityArgument.player()).executes(PlayerCrewCommands::ally)))
						.then(Commands.literal("unally")
								.then(Commands.argument("captain", StringArgumentType.greedyString()).suggests(MY_ALLIES).executes(PlayerCrewCommands::unally)))
						.then(Commands.literal("allies").executes(PlayerCrewCommands::allies))
		));
	}

	// ---- Joining and leaving ----

	private static int invite(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer sender = context.getSource().getPlayerOrException();
		ServerPlayer target = EntityArgument.getPlayer(context, "player");
		MinecraftServer server = context.getSource().getServer();

		// The captain, or their First Mate, can invite.
		PirateCrew crew = PlayerCrews.ensure(sender);
		UUID captain = sender.getUUID();
		if (crew == null) {
			UUID officerOf = PlayerRoles.officerOf(server, sender);
			if (officerOf != null) {
				captain = officerOf;
				crew = PlayerCrews.get(server, captain);
			}
		}
		if (crew == null) {
			return fail(context, PlayerCrews.captainOf(server, sender.getUUID()) != null
					? "Only your captain (or the First Mate) can invite new crewmates."
					: "Start a crew first with /crew create <name>.");
		}
		if (target == sender || target.getUUID().equals(captain)) {
			return fail(context, "They're already aboard!");
		}
		if (crew.members.contains(target.getUUID())) {
			return fail(context, target.getName().getString() + " is already in your crew.");
		}
		if (crew.members.size() >= PlayerCrews.MAX_MEMBERS) {
			return fail(context, "Your crew is full (" + (PlayerCrews.MAX_MEMBERS + 1) + " players).");
		}
		if (target.getAttached(CrewAttachments.CREW) != null) {
			return fail(context, target.getName().getString() + " captains their own crew. Ask for an alliance instead: /crew ally "
					+ target.getName().getString());
		}

		String captainName = crew.nameOf(captain);
		INVITES.computeIfAbsent(target.getUUID(), id -> new HashMap<>()).put(captain, server.getTickCount() + INVITE_TICKS);
		sender.sendSystemMessage(Component.literal("You invited " + target.getName().getString() + " to join the " + crew.name + ".")
				.withStyle(ChatFormatting.AQUA));
		target.sendSystemMessage(Component.literal(sender.getName().getString() + " invites you to join the " + crew.name
				+ "! Type /crew join " + captainName + " within 5 minutes.").withStyle(ChatFormatting.GOLD));
		return 1;
	}

	private static int join(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		MinecraftServer server = context.getSource().getServer();
		UUID captain = findByName(server, pending(INVITES, context.getSource()), StringArgumentType.getString(context, "captain"));
		if (captain == null) {
			return fail(context, "That captain hasn't invited you, or the invite ran out. Ask them for a new one.");
		}
		if (player.getAttached(CrewAttachments.CREW) != null) {
			return fail(context, "You captain your own crew. Use /crew disband first, or ask for an alliance with /crew ally.");
		}
		PirateCrew crew = PlayerCrews.get(server, captain);
		if (crew == null) {
			return fail(context, "That crew has broken up.");
		}
		if (crew.members.size() >= PlayerCrews.MAX_MEMBERS) {
			return fail(context, "That crew is full.");
		}
		// No switching sides (or calling in reinforcements) in the middle of a sea battle.
		if (SeaWars.warOf(server, captain) != null) {
			return fail(context, "The " + crew.name + " are in a sea battle. Join them once it's over.");
		}

		// Leave your old crew first.
		UUID oldCaptain = PlayerCrews.captainOf(server, player.getUUID());
		if (oldCaptain != null) {
			removeMember(server, oldCaptain, player.getUUID(), player.getName().getString() + " left to join the " + crew.name + ".");
		}

		INVITES.get(player.getUUID()).remove(captain);
		crew.members.add(player.getUUID());
		crew.names.put(player.getUUID(), player.getName().getString());
		crew.bounties.put(player.getUUID(), Bounty.get(player));
		PlayerCrews.save(server);

		PlayerCrews.tell(server, captain, Component.literal(player.getName().getString() + " joined the " + crew.name + "! Welcome aboard, nakama!")
				.withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal("You can steer and use your crew's ships, can't hurt your crewmates, "
				+ "and get perks from your captain's hired crewmates. Try /crew members.").withStyle(ChatFormatting.YELLOW));
		syncCrewTeams(server, captain);
		return 1;
	}

	private static int leave(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		MinecraftServer server = context.getSource().getServer();
		UUID captain = PlayerCrews.captainOf(server, player.getUUID());
		if (captain == null || captain.equals(player.getUUID())) {
			return fail(context, captain == null ? "You're not in anyone's crew." : "Captains can't leave. Use /crew disband to break up the crew.");
		}
		String crewName = PlayerCrews.crewName(server, captain);
		removeMember(server, captain, player.getUUID(), player.getName().getString() + " left the crew.");
		player.sendSystemMessage(Component.literal("You left the " + crewName + ".").withStyle(ChatFormatting.YELLOW));
		PlayerCrews.syncTeam(player);
		return 1;
	}

	private static int kick(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer sender = context.getSource().getPlayerOrException();
		MinecraftServer server = context.getSource().getServer();
		UUID captain = PlayerRoles.officerOf(server, sender);
		PirateCrew crew = PlayerCrews.get(server, captain);
		if (crew == null) {
			return fail(context, "Only a captain (or the First Mate) can kick crewmates.");
		}
		UUID member = findByName(server, crew.members, StringArgumentType.getString(context, "player"));
		if (member == null) {
			return fail(context, "Nobody by that name is in your crew.");
		}
		if (member.equals(sender.getUUID())) {
			return fail(context, "Use /crew leave to leave the crew.");
		}
		String name = crew.nameOf(member);
		removeMember(server, captain, member, name + " was kicked off the crew.");
		ServerPlayer kicked = server.getPlayerList().getPlayer(member);
		if (kicked != null) {
			kicked.sendSystemMessage(Component.literal("You were kicked off the " + crew.name + ".").withStyle(ChatFormatting.RED));
			PlayerCrews.syncTeam(kicked);
		}
		return 1;
	}

	private static void removeMember(MinecraftServer server, UUID captain, UUID member, String news) {
		PirateCrew crew = PlayerCrews.get(server, captain);
		if (crew == null || !crew.members.remove(member)) {
			return;
		}
		crew.bounties.remove(member);
		PlayerRoles.forget(crew, member);
		PlayerCrews.save(server);
		PlayerCrews.tell(server, captain, Component.literal(news).withStyle(ChatFormatting.YELLOW));
		syncCrewTeams(server, captain);
	}

	// ---- Looking at your crew ----

	private static int members(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		MinecraftServer server = context.getSource().getServer();
		UUID captain = PlayerCrews.captainOf(server, player.getUUID());
		PirateCrew crew = PlayerCrews.get(server, captain);
		if (crew == null) {
			return fail(context, player.getAttached(CrewAttachments.CREW) != null
					? "No other players in your crew yet. Invite one with /crew invite <player>."
					: "You're not in a player crew. Start one with /crew create <name>, or ask a captain for an invite.");
		}

		player.sendSystemMessage(Component.literal("=== " + crew.name + " ===").withStyle(ChatFormatting.GOLD));
		List<UUID> everyone = new ArrayList<>();
		everyone.add(captain);
		everyone.addAll(crew.members);
		for (UUID id : everyone) {
			ServerPlayer online = server.getPlayerList().getPlayer(id);
			String role = id.equals(captain) ? "Captain " : crew.roles.containsKey(id) ? PlayerRoles.title(crew.roles.get(id)) + " " : "";
			String where = online == null ? "offline"
					: online.blockPosition().toShortString() + " in " + online.level().dimension().identifier().getPath();
			player.sendSystemMessage(Component.literal(role + crew.nameOf(id)).withStyle(id.equals(captain) ? ChatFormatting.YELLOW : ChatFormatting.WHITE)
					.append(Component.literal("  " + Bounty.format(crew.bounties.getOrDefault(id, 0L))).withStyle(ChatFormatting.RED))
					.append(Component.literal("  (" + where + ")").withStyle(online == null ? ChatFormatting.DARK_GRAY : ChatFormatting.GRAY)));
		}
		player.sendSystemMessage(Component.literal("Crew bounty: " + Bounty.format(crew.totalBounty())).withStyle(ChatFormatting.RED));
		return 1;
	}

	private static int bounty(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		MinecraftServer server = context.getSource().getServer();
		UUID captain = PlayerCrews.captainOf(server, player.getUUID());
		PirateCrew crew = PlayerCrews.get(server, captain);
		if (crew == null) {
			return fail(context, "You're not in a player crew. Your own bounty is in /bounty.");
		}
		long total = crew.totalBounty();
		player.sendSystemMessage(Component.literal("The " + crew.name + " are wanted for a total of " + Bounty.format(total) + ".")
				.withStyle(ChatFormatting.RED));
		player.sendSystemMessage(Component.literal("The Marines rank the crew as: " + Bounty.levelName(Bounty.threatLevel(total))
				+ ". The captain gets " + (int) (CrewUpkeep.CAPTAIN_SHARE * 100) + "% of every crewmate's new bounty on top.")
				.withStyle(ChatFormatting.YELLOW));
		return 1;
	}

	private static int say(CommandContext<CommandSourceStack> context, boolean allies) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		MinecraftServer server = context.getSource().getServer();
		UUID captain = PlayerCrews.captainOf(server, player.getUUID());
		PirateCrew crew = PlayerCrews.get(server, captain);
		if (crew == null) {
			return fail(context, "You're not in a player crew.");
		}
		String text = StringArgumentType.getString(context, "message");
		Component line = Component.literal("[" + (allies ? "Alliance" : crew.name) + "] ").withStyle(allies ? ChatFormatting.LIGHT_PURPLE : ChatFormatting.GOLD)
				.append(Component.literal(player.getName().getString() + ": ").withStyle(ChatFormatting.WHITE))
				.append(Component.literal(text).withStyle(ChatFormatting.GRAY));
		PlayerCrews.tell(server, captain, line);
		if (allies) {
			for (UUID ally : crew.allies) {
				PlayerCrews.tell(server, ally, line);
			}
		}
		return 1;
	}

	// ---- Alliances ----

	private static int ally(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer captain = context.getSource().getPlayerOrException();
		ServerPlayer other = EntityArgument.getPlayer(context, "captain");
		MinecraftServer server = context.getSource().getServer();

		PirateCrew crew = PlayerCrews.ensure(captain);
		if (crew == null) {
			return fail(context, "Only captains can make alliances. Start a crew with /crew create <name>.");
		}
		PirateCrew theirs = PlayerCrews.ensure(other);
		if (theirs == null) {
			UUID theirCaptain = PlayerCrews.captainOf(server, other.getUUID());
			return fail(context, theirCaptain != null && !theirCaptain.equals(captain.getUUID())
					? other.getName().getString() + " isn't a captain. Ask their captain, " + PlayerCrews.get(server, theirCaptain).nameOf(theirCaptain) + "."
					: other.getName().getString() + " doesn't captain a crew.");
		}
		if (other == captain) {
			return fail(context, "You can't ally with yourself.");
		}
		if (SeaWars.crewsAtWar(server, captain.getUUID(), other.getUUID())) {
			return fail(context, "You're in a sea battle with the " + theirs.name + ". Finish it (or /crew surrender) before making peace.");
		}
		if (crew.allies.contains(other.getUUID())) {
			return fail(context, "You're already allied with the " + theirs.name + ".");
		}
		if (crew.allies.size() >= PlayerCrews.MAX_ALLIES || theirs.allies.size() >= PlayerCrews.MAX_ALLIES) {
			return fail(context, "A crew can have at most " + PlayerCrews.MAX_ALLIES + " allies.");
		}

		// They asked us already: shake hands.
		Map<UUID, Long> asked = ALLY_REQUESTS.getOrDefault(captain.getUUID(), Map.of());
		Long until = asked.get(other.getUUID());
		if (until != null && until > server.getTickCount()) {
			ALLY_REQUESTS.get(captain.getUUID()).remove(other.getUUID());
			crew.allies.add(other.getUUID());
			theirs.allies.add(captain.getUUID());
			PlayerCrews.save(server);
			Component news = Component.literal("[News Coo] The " + crew.name + " and the " + theirs.name + " have formed an alliance!")
					.withStyle(ChatFormatting.LIGHT_PURPLE);
			server.getPlayerList().broadcastSystemMessage(news, false);
			Component rules = Component.literal("Allies can't hurt each other, can ride each other's ships, and talk with /crew allysay.")
					.withStyle(ChatFormatting.YELLOW);
			PlayerCrews.tell(server, captain.getUUID(), rules);
			PlayerCrews.tell(server, other.getUUID(), rules);
			return 1;
		}

		ALLY_REQUESTS.computeIfAbsent(other.getUUID(), id -> new HashMap<>()).put(captain.getUUID(), server.getTickCount() + INVITE_TICKS);
		captain.sendSystemMessage(Component.literal("You offered an alliance to the " + theirs.name + ".").withStyle(ChatFormatting.AQUA));
		other.sendSystemMessage(Component.literal("Captain " + captain.getName().getString() + " of the " + crew.name
				+ " offers an alliance! Type /crew ally " + captain.getName().getString() + " within 5 minutes to accept.")
				.withStyle(ChatFormatting.LIGHT_PURPLE));
		return 1;
	}

	private static int unally(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer captain = context.getSource().getPlayerOrException();
		MinecraftServer server = context.getSource().getServer();
		PirateCrew crew = PlayerCrews.get(server, captain.getUUID());
		if (crew == null) {
			return fail(context, "Only captains can end alliances.");
		}
		String wanted = StringArgumentType.getString(context, "captain");
		UUID ally = null;
		for (UUID id : crew.allies) {
			PirateCrew other = PlayerCrews.get(server, id);
			if (other != null && (other.nameOf(id).equalsIgnoreCase(wanted) || other.name.equalsIgnoreCase(wanted))) {
				ally = id;
			}
		}
		if (ally == null) {
			return fail(context, "You have no ally by that name. See /crew allies.");
		}
		PirateCrew theirs = PlayerCrews.get(server, ally);
		crew.allies.remove(ally);
		theirs.allies.remove(captain.getUUID());
		PlayerCrews.save(server);
		server.getPlayerList().broadcastSystemMessage(Component.literal("[News Coo] The alliance between the " + crew.name
				+ " and the " + theirs.name + " is over!").withStyle(ChatFormatting.LIGHT_PURPLE), false);
		return 1;
	}

	private static int allies(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		MinecraftServer server = context.getSource().getServer();
		PirateCrew crew = PlayerCrews.get(server, PlayerCrews.captainOf(server, player.getUUID()));
		if (crew == null || crew.allies.isEmpty()) {
			return fail(context, "Your crew has no allies yet. Captains can ask with /crew ally <captain>.");
		}
		player.sendSystemMessage(Component.literal("=== Allies of the " + crew.name + " ===").withStyle(ChatFormatting.LIGHT_PURPLE));
		for (UUID ally : crew.allies) {
			PirateCrew other = PlayerCrews.get(server, ally);
			if (other != null) {
				player.sendSystemMessage(Component.literal(other.name + " (Captain " + other.nameOf(ally) + ", "
						+ (other.members.size() + 1) + " players, " + Bounty.format(other.totalBounty()) + ")"));
			}
		}
		return 1;
	}

	// ---- Helpers ----

	private static int fail(CommandContext<CommandSourceStack> context, String message) {
		context.getSource().sendFailure(Component.literal(message));
		return 0;
	}

	/** Captains with an unexpired invite or request for the player running the command. */
	private static List<UUID> pending(Map<UUID, Map<UUID, Long>> requests, CommandSourceStack source) {
		List<UUID> result = new ArrayList<>();
		if (source.getPlayer() == null) {
			return result;
		}
		Map<UUID, Long> mine = requests.get(source.getPlayer().getUUID());
		if (mine != null) {
			mine.values().removeIf(until -> until < source.getServer().getTickCount());
			result.addAll(mine.keySet());
		}
		return result;
	}

	private static List<String> namesOf(MinecraftServer server, List<UUID> captains) {
		List<String> names = new ArrayList<>();
		for (UUID id : captains) {
			PirateCrew crew = PlayerCrews.get(server, id);
			if (crew != null) {
				names.add(crew.nameOf(id));
			}
		}
		return names;
	}

	private static UUID findByName(MinecraftServer server, List<UUID> ids, String name) {
		for (UUID id : ids) {
			ServerPlayer online = server.getPlayerList().getPlayer(id);
			if (online != null && online.getName().getString().equalsIgnoreCase(name)) {
				return id;
			}
			PirateCrew crew = PlayerCrews.get(server, PlayerCrews.captainOf(server, id));
			if (crew != null && crew.nameOf(id).equalsIgnoreCase(name)) {
				return id;
			}
		}
		return null;
	}

	private static void syncCrewTeams(MinecraftServer server, UUID captain) {
		PirateCrew crew = PlayerCrews.get(server, captain);
		List<UUID> everyone = new ArrayList<>();
		everyone.add(captain);
		if (crew != null) {
			everyone.addAll(crew.members);
		}
		for (UUID id : everyone) {
			ServerPlayer player = server.getPlayerList().getPlayer(id);
			if (player != null) {
				PlayerCrews.syncTeam(player);
			}
		}
	}
}
