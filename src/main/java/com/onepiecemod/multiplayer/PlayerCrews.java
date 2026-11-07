package com.onepiecemod.multiplayer;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.core.UUIDUtil;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.ServerScoreboard;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.scores.PlayerTeam;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.empire.PirateGuardEntity;

/**
 * Every player crew on the server, saved on the Overworld: captain id -> crew.
 * Also answers "which crew is this entity in?" and "are these two friends?" for the rest of the feature.
 */
public class PlayerCrews {
	public static final int MAX_MEMBERS = 11; // Plus the captain: 12 players, like a big Straw Hat Grand Fleet ship.
	public static final int MAX_ALLIES = 6;

	public static final AttachmentType<Map<UUID, PirateCrew>> CREWS = AttachmentRegistry.create(
			OnePieceMod.id("player_crews"),
			builder -> builder.persistent(Codec.unboundedMap(UUIDUtil.STRING_CODEC, PirateCrew.CODEC))
	);

	private static final String TEAM_PREFIX = "op_crew_";

	public static void initialize() {
		// Loading this class registers the attachment.
	}

	/** All crews. Change one, then call save(). */
	public static Map<UUID, PirateCrew> all(MinecraftServer server) {
		return server.overworld().getAttachedOrElse(CREWS, Map.of());
	}

	public static void save(MinecraftServer server, Map<UUID, PirateCrew> crews) {
		server.overworld().setAttached(CREWS, new HashMap<>(crews));
	}

	/** Saves after changing one crew in place. */
	public static void save(MinecraftServer server) {
		save(server, all(server));
	}

	public static PirateCrew get(MinecraftServer server, UUID captain) {
		return captain == null ? null : all(server).get(captain);
	}

	/**
	 * The captain's player crew, created the first time it's needed.
	 * Returns null if this player isn't a captain (they never ran /crew create).
	 */
	public static PirateCrew ensure(ServerPlayer captain) {
		Crew crew = captain.getAttached(CrewAttachments.CREW);
		if (crew == null) {
			return null;
		}
		MinecraftServer server = captain.level().getServer();
		Map<UUID, PirateCrew> crews = new HashMap<>(all(server));
		PirateCrew pirates = crews.get(captain.getUUID());
		if (pirates == null) {
			pirates = PirateCrew.create(crew.name());
			pirates.names.put(captain.getUUID(), captain.getName().getString());
			crews.put(captain.getUUID(), pirates);
			save(server, crews);
		}
		return pirates;
	}

	/** The captain of the player crew this player sailed with: themselves if they lead one. Null if in no player crew. */
	public static UUID captainOf(MinecraftServer server, UUID player) {
		Map<UUID, PirateCrew> crews = all(server);
		if (crews.containsKey(player)) {
			return player;
		}
		for (Map.Entry<UUID, PirateCrew> entry : crews.entrySet()) {
			if (entry.getValue().members.contains(player)) {
				return entry.getKey();
			}
		}
		return null;
	}

	/**
	 * Which crew an entity fights for, as its captain's id.
	 * Players: their crew's captain, or themselves. Hired crewmates: their captain. Kingdom guards: their ruler's crew.
	 */
	public static UUID crewKey(MinecraftServer server, Entity entity) {
		UUID player = null;
		if (entity instanceof Player p) {
			player = p.getUUID();
		} else if (entity instanceof CrewmateEntity crewmate) {
			player = crewmate.getCaptainId();
		} else if (entity instanceof PirateGuardEntity guard) {
			player = guard.getRuler();
		}
		if (player == null) {
			return null;
		}
		UUID captain = captainOf(server, player);
		return captain != null ? captain : player;
	}

	public static boolean allied(MinecraftServer server, UUID crewA, UUID crewB) {
		PirateCrew a = get(server, crewA);
		return a != null && a.allies.contains(crewB);
	}

	/** Same crew or allied crews. */
	public static boolean friendly(MinecraftServer server, Entity a, Entity b) {
		UUID keyA = crewKey(server, a);
		UUID keyB = crewKey(server, b);
		if (keyA == null || keyB == null) {
			return false;
		}
		return keyA.equals(keyB) || allied(server, keyA, keyB);
	}

	/** A crew's name for messages, even if it has no player crew yet. */
	public static String crewName(MinecraftServer server, UUID captain) {
		PirateCrew crew = get(server, captain);
		if (crew != null) {
			return crew.name;
		}
		ServerPlayer player = server.getPlayerList().getPlayer(captain);
		if (player != null) {
			Crew npcCrew = player.getAttached(CrewAttachments.CREW);
			// Messages say "the <name>", so "Luffy Pirates" reads right where "Luffy's crew" gave "the Luffy's crew".
			return npcCrew != null ? npcCrew.name() : player.getName().getString() + " Pirates";
		}
		return "Unknown Pirates";
	}

	/** Sends a message to every online player in the crew, captain included. */
	public static void tell(MinecraftServer server, UUID captain, Component message) {
		PirateCrew crew = get(server, captain);
		ServerPlayer leader = server.getPlayerList().getPlayer(captain);
		if (leader != null) {
			leader.sendSystemMessage(message);
		}
		if (crew != null) {
			for (UUID member : crew.members) {
				ServerPlayer player = server.getPlayerList().getPlayer(member);
				if (player != null) {
					player.sendSystemMessage(message);
				}
			}
		}
	}

	// ---- Name tags: everyone in a player crew shows "[Crew Name]" over their head and in the tab list ----

	/** Puts the player on their crew's scoreboard team, or takes them off if they left. */
	public static void syncTeam(ServerPlayer player) {
		MinecraftServer server = player.level().getServer();
		ServerScoreboard scoreboard = server.getScoreboard();
		String scoreName = player.getScoreboardName();
		PlayerTeam current = scoreboard.getPlayersTeam(scoreName);

		UUID captain = captainOf(server, player.getUUID());
		PirateCrew crew = get(server, captain);
		if (crew == null || crew.members.isEmpty()) {
			// A crew of one doesn't need a name tag. Only remove our own teams, never a map maker's.
			if (current != null && current.getName().startsWith(TEAM_PREFIX)) {
				scoreboard.removePlayerFromTeam(scoreName, current);
			}
			return;
		}

		String teamName = TEAM_PREFIX + captain.toString().substring(0, 8);
		PlayerTeam team = scoreboard.getPlayerTeam(teamName);
		if (team == null) {
			team = scoreboard.addPlayerTeam(teamName);
		}
		Component prefix = Component.literal("[" + crew.name + "] ").withStyle(ChatFormatting.GOLD);
		if (!prefix.equals(team.getPlayerPrefix())) {
			team.setPlayerPrefix(prefix);
		}
		if (current == null || (current != team && current.getName().startsWith(TEAM_PREFIX))) {
			scoreboard.addPlayerToTeam(scoreName, team);
		}
	}

	/** Removes a crew's name tag team, for when the crew breaks up. */
	public static void removeTeam(MinecraftServer server, UUID captain) {
		PlayerTeam team = server.getScoreboard().getPlayerTeam(TEAM_PREFIX + captain.toString().substring(0, 8));
		if (team != null) {
			server.getScoreboard().removePlayerTeam(team);
		}
	}
}
