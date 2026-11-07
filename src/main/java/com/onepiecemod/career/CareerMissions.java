package com.onepiecemod.career;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import com.onepiecemod.sound.ModSounds;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.character.Locations;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.stats.StatTraining;

/**
 * Orders from headquarters. A Marine is sent after a pirate crew; a Revolutionary is sent to drive a Navy
 * garrison out of a place. The enemies only appear when you get close (48 blocks), and come back if you
 * leave and return. Beat them all for Merit or Liberation, Berries and Pirate XP.
 *
 * Orders point at the nearest pirate camp (Marines) or Marine outpost (Revolutionaries) within 1200 blocks,
 * else at a spot 150 to 350 blocks away; the enemies stand on the nearest dry land there.
 * The enemies get tougher (and more) with your rank.
 */
final class CareerMissions {
	static final String TAG = "onepiece_career_mission";

	private static final List<String> PIRATE_HIDEOUTS = List.of("a pirate hideout", "a smugglers' cove", "a pirate camp", "a raided village");
	private static final List<String> NAVY_OUTPOSTS = List.of("a Navy outpost", "a Marine checkpoint", "a slave market", "a World Government post");

	/** Enemies alive right now, by mission owner. Not saved: they're never saved either. */
	private static final Map<UUID, Set<UUID>> LIVE = new HashMap<>();
	private static final Map<UUID, UUID> OWNER_OF = new HashMap<>();
	/** Players whose orders are being looked up, with when it started (a player who logs off never gets an answer). */
	private static final Map<UUID, Long> PENDING = new HashMap<>();
	/** A real camp or outpost further than this is too far for one job: a random spot is used instead. */
	private static final int MAX_DISTANCE = 1200;

	private CareerMissions() {
	}

	// ---- Getting orders ----

	static void request(ServerPlayer player) {
		CareerData data = Careers.get(player);
		Career career = data.path();
		if (career == Career.PIRATE) {
			player.sendSystemMessage(Component.literal("Pirates don't take orders.").withStyle(ChatFormatting.GRAY));
			return;
		}
		if (data.mission().isPresent()) {
			describe(player, data.mission().get());
			return;
		}
		ServerLevel level = (ServerLevel) player.level();
		if (level.dimension() != Level.OVERWORLD) {
			player.sendSystemMessage(Component.literal("No signal down here. Ask for orders at sea.").withStyle(ChatFormatting.GRAY));
			return;
		}

		long now = level.getGameTime();
		Long asked = PENDING.get(player.getUUID());
		if (asked != null && now - asked < 1200) {
			player.sendSystemMessage(Component.literal("HQ is still checking the charts...").withStyle(ChatFormatting.GRAY));
			return;
		}
		PENDING.put(player.getUUID(), now);
		// Point at a real pirate camp or Navy outpost when one is near. The search runs in the background
		// (on the server thread it can freeze the game for close to a minute); a random spot is the fallback.
		String target = career == Career.MARINE ? "pirate_camp" : "marine_base";
		player.sendSystemMessage(Component.literal("Purupuru... \"HQ here. Checking the charts, stand by...\"").withStyle(ChatFormatting.GRAY));
		if (!Locations.findLater(player, target, MAX_DISTANCE, (who, found) -> {
			PENDING.remove(who.getUUID());
			give(who, career, found.filter(f -> Locations.distance(who.blockPosition(), f.pos()) <= MAX_DISTANCE).orElse(null));
		})) {
			PENDING.remove(player.getUUID());
			give(player, career, null);
		}
	}

	/** Hands out the orders, at `found` or (when null) a random spot a few hundred blocks away. */
	private static void give(ServerPlayer player, Career career, Locations.Found found) {
		CareerData data = Careers.get(player);
		ServerLevel level = (ServerLevel) player.level();
		if (data.path() != career || data.mission().isPresent() || level.dimension() != Level.OVERWORLD) {
			return;
		}
		int tier = data.rank();
		BlockPos at;
		String placeName;
		if (found != null) {
			at = found.pos();
			placeName = "the " + Locations.name(found.id());
		} else {
			double angle = level.getRandom().nextDouble() * Math.PI * 2;
			int distance = 150 + level.getRandom().nextInt(200);
			at = new BlockPos((int) (player.getX() + Math.cos(angle) * distance), 64, (int) (player.getZ() + Math.sin(angle) * distance));
			List<String> names = career == Career.MARINE ? PIRATE_HIDEOUTS : NAVY_OUTPOSTS;
			placeName = names.get(level.getRandom().nextInt(names.size()));
		}

		int size = Math.min(8, 3 + tier / 2);
		int reward = 40 + 30 * tier;
		CareerData.Mission mission = new CareerData.Mission(career == Career.MARINE ? "hunt" : "liberate", placeName,
				at.getX(), at.getY(), at.getZ(), size, size, tier, reward);
		Careers.set(player, data.withMission(mission));
		ModSounds.play(player, ModSounds.DEN_DEN_MUSHI_CALL);
		player.sendSystemMessage(Component.literal(career == Career.MARINE
				? "Purupuru... \"HQ here. A pirate crew was spotted near " + placeName + ". Bring them in!\""
				: "Purupuru... \"Comrade. The Navy is holding " + placeName + ". Drive them out and free the people!\"")
				.withStyle(career.color));
		describe(player, mission);
	}

	static void describe(ServerPlayer player, CareerData.Mission mission) {
		player.sendSystemMessage(Component.literal(text(player, mission) + ", around " + mission.x() + ", " + mission.z()
				+ ". Reward: " + mission.reward() + " " + Careers.career(player).points + ".").withStyle(ChatFormatting.GRAY));
	}

	/** "Pirate crew at Arlong Park: 340 blocks north-east (5 left)". */
	static String text(ServerPlayer player, CareerData.Mission mission) {
		String what = "hunt".equals(mission.kind()) ? "Pirates at " : "Navy garrison at ";
		BlockPos pos = mission.pos();
		BlockPos flat = new BlockPos(player.getBlockX(), pos.getY(), player.getBlockZ());
		int distance = Locations.distance(flat, pos);
		String where = distance < 24 ? "right here" : distance + " blocks " + Locations.direction(flat, pos);
		return what + mission.place() + ": " + where + " (" + mission.remaining() + " left)";
	}

	static void abandon(ServerPlayer player) {
		CareerData data = Careers.get(player);
		if (data.mission().isEmpty()) {
			return;
		}
		clear(player);
		player.sendSystemMessage(Component.literal("Orders called off.").withStyle(ChatFormatting.GRAY));
	}

	/** Drops the orders and sends away any enemies that came for them. */
	static void clear(ServerPlayer player) {
		despawn(player.level().getServer(), player.getUUID());
		CareerData data = Careers.get(player);
		if (data.mission().isPresent()) {
			Careers.set(player, data.withMission(null));
		}
	}

	// ---- Every second ----

	static void tick(MinecraftServer server) {
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			CareerData data = Careers.get(player);
			if (data.mission().isEmpty() || data.path() == Career.PIRATE) {
				continue;
			}
			CareerData.Mission mission = data.mission().get();
			ServerLevel level = (ServerLevel) player.level();
			Set<UUID> live = LIVE.get(player.getUUID());
			double dx = player.getX() - mission.x();
			double dz = player.getZ() - mission.z();
			double distance = Math.sqrt(dx * dx + dz * dz);

			if (live != null && !live.isEmpty()) {
				// Left the area (or the enemies unloaded): send them away; they'll be back when you return.
				boolean anyLoaded = false;
				for (UUID id : live) {
					if (level.getEntity(id) != null) {
						anyLoaded = true;
						break;
					}
				}
				if (!anyLoaded || distance > 160 || level.dimension() != Level.OVERWORLD) {
					despawn(server, player.getUUID());
				}
			} else if (level.dimension() == Level.OVERWORLD && distance < 48 && mission.remaining() > 0) {
				spawn(level, player, data.path(), mission);
			}

			if (player.tickCount % 40 < 20 && holdingDenDen(player)) {
				player.sendOverlayMessage(Component.literal("Orders: " + text(player, mission)).withStyle(data.path().color));
			}
		}
	}

	private static boolean holdingDenDen(ServerPlayer player) {
		return isDenDen(player.getMainHandItem()) || isDenDen(player.getOffhandItem());
	}

	private static boolean isDenDen(ItemStack stack) {
		return stack.is(CareerFeature.NAVY_DEN_DEN_MUSHI) || stack.is(CareerFeature.REVOLUTIONARY_DEN_DEN_MUSHI);
	}

	private static void spawn(ServerLevel level, ServerPlayer player, Career career, CareerData.Mission mission) {
		// Stand them on dry ground near the mark.
		BlockPos center = null;
		for (int r = 0; r <= 64 && center == null; r += 4) {
			for (int i = 0; i < 12 && center == null; i++) {
				double angle = i * Math.PI / 6;
				center = CareerSquads.dryGround(level, mission.x() + (int) (Math.cos(angle) * r), mission.z() + (int) (Math.sin(angle) * r));
			}
		}
		if (center == null) {
			center = CareerSquads.surface(level, mission.x(), mission.z());
		}
		if (!level.isPositionEntityTicking(center)) {
			// Not fully loaded yet (just arrived): enemies put there can't be seen, so they'd be sent again. Next second.
			return;
		}
		List<String> kits = career == Career.MARINE
				? CareerSquads.pirateCrew(mission.tier(), mission.total())
				: CareerSquads.navyGarrison(mission.tier(), mission.total());
		// Those already beaten stay beaten: only the rest come back.
		kits = kits.subList(mission.total() - mission.remaining(), kits.size());
		Set<UUID> live = LIVE.computeIfAbsent(player.getUUID(), id -> new HashSet<>());
		double toughness = 1.0 + 0.12 * mission.tier();
		for (String kit : kits) {
			HumanNpc npc = CareerSquads.enemy(level, kit, toughness);
			if (npc == null) {
				continue;
			}
			BlockPos pos = CareerSquads.dryGround(level, center.getX() + level.getRandom().nextInt(7) - 3, center.getZ() + level.getRandom().nextInt(7) - 3);
			CareerSquads.place(level, npc, pos != null ? pos : center, player, TAG);
			live.add(npc.getUUID());
			OWNER_OF.put(npc.getUUID(), player.getUUID());
		}
		Careers.set(player, Careers.get(player).withMission(mission.at(center)));
		player.sendSystemMessage(Component.literal(career == Career.MARINE
				? "There they are! " + kits.size() + " pirates. Bring them in!"
				: "The garrison! " + kits.size() + " of the Navy's men. Drive them out!").withStyle(ChatFormatting.YELLOW));
	}

	private static void despawn(MinecraftServer server, UUID owner) {
		Set<UUID> live = LIVE.remove(owner);
		if (live == null) {
			return;
		}
		for (UUID id : live) {
			OWNER_OF.remove(id);
			for (ServerLevel level : server.getAllLevels()) {
				Entity entity = level.getEntity(id);
				if (entity != null) {
					entity.discard();
				}
			}
		}
	}

	/** An enemy from someone's orders was beaten (by anyone). */
	static void onDeath(Entity entity) {
		UUID owner = OWNER_OF.remove(entity.getUUID());
		if (owner == null) {
			return;
		}
		Set<UUID> live = LIVE.get(owner);
		if (live != null) {
			live.remove(entity.getUUID());
		}
		ServerPlayer player = entity.level().getServer().getPlayerList().getPlayer(owner);
		if (player == null) {
			return;
		}
		CareerData data = Careers.get(player);
		if (data.mission().isEmpty()) {
			return;
		}
		CareerData.Mission mission = data.mission().get();
		int left = mission.remaining() - 1;
		if (left > 0) {
			Careers.set(player, data.withMission(mission.withRemaining(left)));
			player.sendOverlayMessage(Component.literal(left + " left!").withStyle(ChatFormatting.YELLOW));
			return;
		}
		// Orders carried out.
		LIVE.remove(owner);
		Careers.set(player, data.missionDone());
		int berries = 3 + 2 * mission.tier();
		player.sendSystemMessage(Component.literal(data.path() == Career.MARINE
				? "Orders carried out! The pirates are in chains."
				: "The garrison is driven out! The people cheer for the Revolutionary Army.").withStyle(data.path().color, ChatFormatting.BOLD));
		Careers.give(player, new ItemStack(CharacterFeature.BERRY, berries));
		player.sendSystemMessage(Component.literal("+" + berries + " Berries").withStyle(ChatFormatting.GOLD));
		ModSounds.play(player, ModSounds.QUEST_COMPLETE);
		StatTraining.addXp(player, 20 + 10 * mission.tier(), true);
		Careers.addPoints(player, mission.reward(), "orders carried out", true);
	}
}
