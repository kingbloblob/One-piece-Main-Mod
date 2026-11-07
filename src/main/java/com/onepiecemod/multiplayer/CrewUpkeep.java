package com.onepiecemod.multiplayer;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Holder;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.crew.CrewmateEntity;

/**
 * Keeps player crews tidy, every 10 seconds:
 *  - copies the captain's crew name, everyone's name and bounty (so /crew bounty works for offline players),
 *  - pays the captain 10% of every bounty raise their crewmates get (the captain answers for the whole crew),
 *  - breaks up a crew whose captain ran /crew disband,
 *  - name tags over everyone's head.
 * And every 2 seconds, players get the perks of their captain's hired crewmates standing near them.
 */
public class CrewUpkeep {
	public static final double CAPTAIN_SHARE = 0.10;
	private static final double PERK_RANGE = 48.0;

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 200 == 0) {
				upkeep(server);
			}
			if (server.getTickCount() % 40 == 0) {
				sharePerks(server);
				PlayerRoles.tick(server);
			}
		});
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> server.execute(() -> {
			PlayerCrews.syncTeam(handler.getPlayer());
			UUID captain = PlayerCrews.captainOf(server, handler.getPlayer().getUUID());
			PirateCrew crew = PlayerCrews.get(server, captain);
			if (crew != null && !captain.equals(handler.getPlayer().getUUID())) {
				handler.getPlayer().sendSystemMessage(Component.literal("You sail with the " + crew.name
						+ ". Type /crew members to see who's aboard.").withStyle(ChatFormatting.GOLD));
			}
		}));
	}

	private static void upkeep(MinecraftServer server) {
		boolean changed = false;
		Map<ServerPlayer, Long> raises = new HashMap<>();
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			changed |= checkPlayer(server, player, raises);
			PlayerCrews.syncTeam(player);
		}
		// Crew fame: crewmates nearby share in each new bounty. Record the shares at once so they don't count as raises next time.
		for (ServerPlayer player : CrewBounties.shareFame(server, raises)) {
			PirateCrew crew = PlayerCrews.get(server, PlayerCrews.captainOf(server, player.getUUID()));
			if (crew != null) {
				crew.bounties.put(player.getUUID(), Bounty.get(player));
				changed = true;
			}
		}
		if (changed) {
			PlayerCrews.save(server);
		}
	}

	// Returns true if a crew changed and needs saving.
	private static boolean checkPlayer(MinecraftServer server, ServerPlayer player, Map<ServerPlayer, Long> raises) {
		UUID id = player.getUUID();
		Crew npcCrew = player.getAttached(CrewAttachments.CREW);
		Map<UUID, PirateCrew> crews = PlayerCrews.all(server);
		boolean changed = false;

		// Captain who disbanded with /crew disband: the player crew goes too.
		PirateCrew own = crews.get(id);
		if (own != null && npcCrew == null) {
			dissolve(server, id);
			return false; // dissolve() already saved.
		}

		// A crewmate who started their own crew with /crew create has left their old one.
		if (npcCrew != null) {
			for (Map.Entry<UUID, PirateCrew> entry : crews.entrySet()) {
				if (entry.getValue().members.remove(id)) {
					entry.getValue().bounties.remove(id);
					PlayerRoles.forget(entry.getValue(), id);
					PlayerCrews.tell(server, entry.getKey(), Component.literal(player.getName().getString()
							+ " left the " + entry.getValue().name + " to captain the " + npcCrew.name() + ".").withStyle(ChatFormatting.YELLOW));
					player.sendSystemMessage(Component.literal("You left the " + entry.getValue().name
							+ " to captain your own crew.").withStyle(ChatFormatting.YELLOW));
					changed = true;
				}
			}
		}
		if (own != null && !own.name.equals(npcCrew.name())) {
			own.name = npcCrew.name();
			changed = true;
		}

		UUID captain = PlayerCrews.captainOf(server, id);
		PirateCrew crew = PlayerCrews.get(server, captain);
		if (crew == null) {
			return changed;
		}

		String name = player.getName().getString();
		if (!name.equals(crew.names.get(id))) {
			crew.names.put(id, name);
			changed = true;
		}

		long bounty = Bounty.get(player);
		Long last = crew.bounties.put(id, bounty);
		if (last == null || last != bounty) {
			changed = true;
		}
		if (last != null && bounty > last) {
			raises.put(player, bounty - last);
		}
		// The captain's share of a crewmate's new fame.
		if (last != null && bounty > last && !captain.equals(id)) {
			crew.owed += (long) ((bounty - last) * CAPTAIN_SHARE);
		}
		if (captain.equals(id) && crew.owed > 0) {
			long share = crew.owed;
			crew.owed = 0;
			Bounty.raise(player, share, "Your crew's deeds are on your head too.", false);
			crew.bounties.put(id, Bounty.get(player));
		}
		return changed;
	}

	/** Breaks up a captain's player crew: members go free, allies forget it. */
	public static void dissolve(MinecraftServer server, UUID captain) {
		if (PlayerCrews.get(server, captain) != null) {
			SeaWars.crewGone(server, captain);
		}
		Map<UUID, PirateCrew> crews = new HashMap<>(PlayerCrews.all(server));
		PirateCrew crew = crews.remove(captain);
		if (crew == null) {
			return;
		}
		Component news = Component.literal("The " + crew.name + " has broken up. You're a free pirate again.").withStyle(ChatFormatting.YELLOW);
		for (UUID member : crew.members) {
			ServerPlayer player = server.getPlayerList().getPlayer(member);
			if (player != null) {
				player.sendSystemMessage(news);
			}
		}
		for (UUID ally : crew.allies) {
			PirateCrew other = crews.get(ally);
			if (other != null) {
				other.allies.remove(captain);
			}
		}
		PlayerCrews.save(server, crews);
		PlayerCrews.removeTeam(server, captain);
		for (UUID member : crew.members) {
			ServerPlayer player = server.getPlayerList().getPlayer(member);
			if (player != null) {
				PlayerCrews.syncTeam(player);
			}
		}
	}

	// ---- Crewmates help everyone in the crew, not just the captain ----

	private static void sharePerks(MinecraftServer server) {
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			UUID captain = PlayerCrews.captainOf(server, player.getUUID());
			if (captain == null || captain.equals(player.getUUID())) {
				continue; // Captains already get perks from the crew feature.
			}
			for (CrewmateEntity crewmate : player.level().getEntitiesOfClass(CrewmateEntity.class,
					player.getBoundingBox().inflate(PERK_RANGE),
					crewmate -> crewmate.isAlive() && captain.equals(crewmate.getCaptainId()))) {
				switch (crewmate.getRole()) {
					case SWORDSMAN -> effect(player, MobEffects.STRENGTH);
					case NAVIGATOR -> effect(player, MobEffects.SPEED);
					case SNIPER -> effect(player, MobEffects.NIGHT_VISION);
					case COOK -> {
						if (player.getFoodData().needsFood()) {
							player.getFoodData().eat(1, 0.3f);
						}
					}
					case DOCTOR -> {
						if (player.getHealth() < player.getMaxHealth() / 2) {
							effect(player, MobEffects.REGENERATION);
						}
					}
					case SHIPWRIGHT -> effect(player, MobEffects.HASTE);
					case ARCHAEOLOGIST -> effect(player, MobEffects.LUCK);
					case MUSICIAN -> effect(player, MobEffects.RESISTANCE);
					case HELMSMAN -> {
						effect(player, MobEffects.WATER_BREATHING);
						effect(player, MobEffects.DOLPHINS_GRACE);
					}
				}
			}
		}
	}

	private static void effect(ServerPlayer player, Holder<MobEffect> effect) {
		player.addEffect(new MobEffectInstance(effect, 100, 0, true, false, true));
	}
}
