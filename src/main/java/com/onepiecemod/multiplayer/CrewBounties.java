package com.onepiecemod.multiplayer;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.ItemLore;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.bounty.BountyFeature;
import com.onepiecemod.config.ModConfig;

/**
 * Bounties shared by a crew of players:
 *  - Crew fame: when a player's bounty rises, crewmates within 64 blocks get a share too (ModConfig crew_fame_share).
 *  - Defeating a rival player adds a share of their bounty to yours (ModConfig player_kill_bounty), double in a sea battle,
 *    at most once per rival every 30 minutes so friends can't farm each other.
 *  - The crew's Wanted Poster (/crew poster): every crewmate's bounty and the crew total.
 */
public class CrewBounties {
	private static final double FAME_RANGE = 64;
	private static final long KILL_COOLDOWN_TICKS = 20L * 60 * 30;

	/** "killer|victim" -> game tick the next reward is allowed. Not saved. */
	private static final Map<String, Long> KILL_COOLDOWN = new HashMap<>();

	public static void initialize() {
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (entity instanceof ServerPlayer victim && source.getEntity() instanceof ServerPlayer killer && killer != victim) {
				defeated(killer, victim);
			}
		});
	}

	/** The total bounty of a crew of players, or of a lone captain. */
	public static long crewBounty(MinecraftServer server, UUID captain) {
		PirateCrew crew = PlayerCrews.get(server, captain);
		long total = crew != null ? crew.totalBounty() : 0;
		ServerPlayer leader = server.getPlayerList().getPlayer(captain);
		if (leader != null && (crew == null || !crew.bounties.containsKey(captain))) {
			total += Bounty.get(leader);
		}
		return total;
	}

	private static void defeated(ServerPlayer killer, ServerPlayer victim) {
		MinecraftServer server = killer.level().getServer();
		if (PlayerCrews.friendly(server, killer, victim)) {
			return;
		}
		long bounty = Bounty.get(victim);
		double share = ModConfig.playerKillBounty() * (SeaWars.atWar(server, killer, victim) ? 2 : 1);
		long reward = (long) (bounty * share);
		if (reward <= 0) {
			return;
		}
		String key = killer.getUUID() + "|" + victim.getUUID();
		long now = server.overworld().getGameTime();
		if (KILL_COOLDOWN.getOrDefault(key, 0L) > now) {
			return;
		}
		KILL_COOLDOWN.put(key, now + KILL_COOLDOWN_TICKS);
		KILL_COOLDOWN.values().removeIf(until -> until < now);
		Bounty.raise(killer, reward, "You defeated " + victim.getName().getString() + "!", false);
		killer.sendSystemMessage(Component.literal("You defeated " + victim.getName().getString() + ", wanted for " + Bounty.format(bounty)
				+ "! The Marines take note.").withStyle(ChatFormatting.GOLD));
	}

	/**
	 * Called by CrewUpkeep every 10 seconds with how much each player's bounty rose since last time.
	 * Every other crew player near them gets crew_fame_share of it. Returns the players whose bounty changed here.
	 */
	static List<ServerPlayer> shareFame(MinecraftServer server, Map<ServerPlayer, Long> raises) {
		double share = ModConfig.crewFameShare();
		List<ServerPlayer> changed = new ArrayList<>();
		if (share <= 0 || raises.isEmpty()) {
			return changed;
		}
		Map<ServerPlayer, Long> gains = new HashMap<>();
		for (Map.Entry<ServerPlayer, Long> entry : raises.entrySet()) {
			ServerPlayer hero = entry.getKey();
			UUID captain = PlayerCrews.captainOf(server, hero.getUUID());
			if (captain == null) {
				continue;
			}
			long gain = (long) (entry.getValue() * share);
			if (gain <= 0) {
				continue;
			}
			for (ServerPlayer mate : SeaWars.online(server, captain)) {
				if (mate != hero && mate.level() == hero.level() && mate.distanceToSqr(hero) < FAME_RANGE * FAME_RANGE) {
					gains.merge(mate, gain, Long::sum);
				}
			}
		}
		for (Map.Entry<ServerPlayer, Long> entry : gains.entrySet()) {
			Bounty.raise(entry.getKey(), entry.getValue(), "Your crew's deeds are on your head too.", false);
			changed.add(entry.getKey());
		}
		return changed;
	}

	/** A Wanted Poster of the whole crew. */
	static ItemStack poster(MinecraftServer server, UUID captain) {
		PirateCrew crew = PlayerCrews.get(server, captain);
		String name = PlayerCrews.crewName(server, captain);
		List<Component> lore = new ArrayList<>();
		lore.add(Component.literal("DEAD OR ALIVE").withStyle(ChatFormatting.DARK_RED));
		lore.add(Component.literal("The " + name).withStyle(ChatFormatting.GOLD));
		long total = crewBounty(server, captain);
		lore.add(Component.literal("Crew bounty " + Bounty.format(total)).withStyle(ChatFormatting.YELLOW));
		if (crew != null) {
			List<UUID> everyone = new ArrayList<>();
			everyone.add(captain);
			everyone.addAll(crew.members);
			for (UUID id : everyone) {
				String role = id.equals(captain) ? "Captain" : PlayerRoles.title(crew.roles.get(id));
				lore.add(Component.literal(role + " " + crew.nameOf(id) + "  " + Bounty.format(crew.bounties.getOrDefault(id, 0L)))
						.withStyle(ChatFormatting.WHITE));
			}
		}
		lore.add(Component.literal(Bounty.levelName(Bounty.threatLevel(total))).withStyle(ChatFormatting.GRAY));
		lore.add(Component.literal("MARINE").withStyle(ChatFormatting.BLUE));
		ItemStack poster = new ItemStack(BountyFeature.BOUNTY_POSTER);
		poster.set(DataComponents.ITEM_NAME, Component.literal("Wanted: the " + name));
		poster.set(DataComponents.LORE, new ItemLore(lore));
		return poster;
	}
}
