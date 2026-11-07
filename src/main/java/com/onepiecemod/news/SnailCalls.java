package com.onepiecemod.news;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.bounty.BountyHunterEntity;
import com.onepiecemod.bounty.MarineEntity;
import com.onepiecemod.bounty.NavyRaids;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.empire.BusterCall;
import com.onepiecemod.sea.SeaItems;
import com.onepiecemod.sound.ModSounds;

/**
 * Calls that come IN on your Den Den Mushi (calling your crew is in sea/DenDenMushiItem).
 * You need a Den Den Mushi somewhere in your bag to get them:
 *  - Villain taunts: a boss rings you when you come near their lair.
 *  - Marine alerts: you pick up Navy broadcasts when hunters, a raid or a Buster Call come for you.
 *  - Crew calls: a crewmate left behind rings you when they're attacked, and the line goes dead if they fall.
 */
public class SnailCalls {
	private static final double TAUNT_RANGE = 48.0;
	private static final long TAUNT_COOLDOWN = 20L * 60 * 20; // 20 minutes per boss.
	private static final double HUNTER_RANGE = 64.0;
	private static final long ALERT_COOLDOWN = 20L * 60 * 3;
	private static final double CREW_FAR = 24.0;
	private static final long CREW_COOLDOWN = 20L * 30;

	/** "player|boss" or "player|alert" to the game time it last rang. */
	private static final Map<String, Long> lastRang = new HashMap<>();
	private static final Map<UUID, Boolean> wasRaided = new HashMap<>();
	private static final Map<UUID, Boolean> wasBusterCalled = new HashMap<>();

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 40 != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				if (player.isAlive() && !player.isSpectator()) {
					check(server, player);
				}
			}
		});

		ServerLivingEntityEvents.AFTER_DAMAGE.register((entity, source, baseDamage, damage, blocked) -> {
			if (entity instanceof CrewmateEntity crewmate && damage > 0 && crewmate.isAlive()) {
				crewUnderAttack(crewmate, source.getEntity());
			}
		});
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (entity instanceof CrewmateEntity crewmate) {
				ServerPlayer captain = crewmate.getCaptain();
				if (captain != null && hasSnail(captain) && isFar(captain, crewmate)) {
					ring(captain);
					captain.sendSystemMessage(Component.literal("[Den Den Mushi] Puru puru... ").withStyle(ChatFormatting.GOLD)
							.append(crewmate.getDisplayName().copy().withStyle(ChatFormatting.AQUA))
							.append(Component.literal(": \"Captain... I'm sorry...\" The line goes dead.").withStyle(ChatFormatting.GRAY)));
				}
			}
		});
	}

	private static void check(MinecraftServer server, ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		long now = server.overworld().getGameTime();
		boolean snail = hasSnail(player);

		// Navy raids and Buster Calls starting.
		boolean raided = NavyRaids.isRaiding(player);
		if (raided && !wasRaided.getOrDefault(player.getUUID(), false) && snail) {
			marineBroadcast(player, "\"All ships, all ships! The pirate " + player.getName().getString()
					+ " has been found. Surround them and open fire!\"");
		}
		wasRaided.put(player.getUUID(), raided);
		boolean buster = BusterCall.isActive(player);
		if (buster && !wasBusterCalled.getOrDefault(player.getUUID(), false) && snail) {
			marineBroadcast(player, "\"This is a Buster Call. I repeat, this is a Buster Call. Ten warships, five Vice Admirals. "
					+ "Erase the island and everyone on it.\"");
		}
		wasBusterCalled.put(player.getUUID(), buster);

		if (!snail) {
			return;
		}

		// Marine hunters and bounty hunters closing in.
		if (!raided && !buster && now - lastRang.getOrDefault(player.getUUID() + "|hunters", -ALERT_COOLDOWN) >= ALERT_COOLDOWN) {
			List<MarineEntity> marines = level.getEntitiesOfClass(MarineEntity.class, player.getBoundingBox().inflate(HUNTER_RANGE),
					m -> m.isAlive() && MarineEntity.isHunting(m, player));
			List<BountyHunterEntity> hunters = level.getEntitiesOfClass(BountyHunterEntity.class,
					player.getBoundingBox().inflate(HUNTER_RANGE), LivingEntity::isAlive);
			Entity closest = !marines.isEmpty() ? marines.get(0) : !hunters.isEmpty() ? hunters.get(0) : null;
			if (closest != null) {
				lastRang.put(player.getUUID() + "|hunters", now);
				String where = direction(player, closest) + ", about " + (int) player.distanceTo(closest) + " blocks away";
				if (!marines.isEmpty()) {
					marineBroadcast(player, "\"Squad " + (1 + player.getRandom().nextInt(9)) + ", target spotted " + where
							+ ". Move in and take them alive!\"");
				} else {
					ring(player);
					player.sendSystemMessage(Component.literal("[Den Den Mushi] Puru puru... Gacha! ").withStyle(ChatFormatting.GOLD)
							.append(Component.literal("An informant whispers: \"Careful, a bounty hunter with Devil Fruit powers is after you, "
									+ where + ".\"").withStyle(ChatFormatting.YELLOW)));
				}
			}
		}

		// Villain taunts.
		for (CharacterEntity boss : level.getEntitiesOfClass(CharacterEntity.class, player.getBoundingBox().inflate(TAUNT_RANGE),
				b -> b.isAlive() && b.isBoss())) {
			String key = player.getUUID() + "|" + boss.getCharacterId();
			if (now - lastRang.getOrDefault(key, -TAUNT_COOLDOWN) < TAUNT_COOLDOWN) {
				continue;
			}
			lastRang.put(key, now);
			String line = NewsData.get().taunt(boss.getCharacterId(), boss.getData().tier, player.getRandom());
			ring(player);
			player.sendSystemMessage(Component.literal("[Den Den Mushi] Puru puru puru... Gacha! ").withStyle(ChatFormatting.GOLD)
					.append(Component.literal(boss.getData().name + ": ").withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD))
					.append(Component.literal("\"" + line + "\"").withStyle(ChatFormatting.RED)));
			break; // One call at a time.
		}
	}

	private static void crewUnderAttack(CrewmateEntity crewmate, Entity attacker) {
		ServerPlayer captain = crewmate.getCaptain();
		if (captain == null || !hasSnail(captain) || !isFar(captain, crewmate) || attacker == captain) {
			return;
		}
		long now = captain.level().getServer().overworld().getGameTime();
		String key = captain.getUUID() + "|crew|" + crewmate.getUUID();
		if (now - lastRang.getOrDefault(key, -CREW_COOLDOWN) < CREW_COOLDOWN) {
			return;
		}
		lastRang.put(key, now);
		String who = attacker != null ? attacker.getName().getString() : "something";
		String where = crewmate.level() != captain.level() ? "in another world"
				: "at " + crewmate.blockPosition().getX() + ", " + crewmate.blockPosition().getY() + ", " + crewmate.blockPosition().getZ()
						+ " (" + direction(captain, crewmate) + ")";
		ring(captain);
		captain.sendSystemMessage(Component.literal("[Den Den Mushi] Puru puru puru... Gacha! ").withStyle(ChatFormatting.GOLD)
				.append(crewmate.getDisplayName().copy().withStyle(ChatFormatting.AQUA))
				.append(Component.literal(": \"Captain! I'm under attack by " + who + " " + where + "! "
						+ (int) crewmate.getHealth() + " HP left!\"").withStyle(ChatFormatting.YELLOW)));
	}

	private static void marineBroadcast(ServerPlayer player, String message) {
		ring(player);
		player.sendSystemMessage(Component.literal("[Den Den Mushi] Bero bero... You pick up a Marine broadcast: ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(message).withStyle(ChatFormatting.BLUE)));
	}

	private static void ring(ServerPlayer player) {
		ModSounds.play(player, ModSounds.DEN_DEN_MUSHI_CALL);
	}

	public static boolean hasSnail(ServerPlayer player) {
		return player.getInventory().contains(stack -> stack.is(SeaItems.DEN_DEN_MUSHI));
	}

	private static boolean isFar(ServerPlayer captain, Entity crewmate) {
		return crewmate.level() != captain.level() || captain.distanceTo(crewmate) > CREW_FAR;
	}

	/** "north-east" etc.: where the other entity is, seen from the player. */
	private static String direction(Entity from, Entity to) {
		double dx = to.getX() - from.getX();
		double dz = to.getZ() - from.getZ();
		double angle = Math.toDegrees(Math.atan2(dx, -dz)); // 0 = north, 90 = east.
		String[] names = {"north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"};
		int index = (int) Math.round(((angle % 360) + 360) % 360 / 45.0) % 8;
		return "to the " + names[index];
	}
}
