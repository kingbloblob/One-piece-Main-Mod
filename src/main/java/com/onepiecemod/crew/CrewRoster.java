package com.onepiecemod.crew;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.UUIDUtil;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.entity.event.v1.ServerEntityLevelChangeEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.ship.ShipEntity;

/**
 * Keeps the crew together:
 * - Crewmates on Follow catch up with their captain when they fall far behind, go through
 *   Nether/End portals with them, and come along after the captain respawns.
 * - When the captain sails a ship, Follow crewmates take the free seats, and hop off when the captain does.
 * - A crewmate who dies while their captain is offline is written down here, and the captain is told
 *   (and the role is freed) when they log back in.
 */
public class CrewRoster {
	/** Follow crewmates further away than this get brought to the captain. */
	private static final double CATCH_UP_DISTANCE = 40.0;
	/** Crewmates this close to a ship the captain is sailing climb aboard. */
	private static final double BOARD_DISTANCE = 64.0;

	/** A crewmate who died while their captain was offline. */
	public record Fallen(UUID id, String name) {
		public static final Codec<Fallen> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				UUIDUtil.CODEC.fieldOf("id").forGetter(Fallen::id),
				Codec.STRING.fieldOf("name").forGetter(Fallen::name)
		).apply(instance, Fallen::new));
	}

	/** Saved on the Overworld: captain -> crewmates who fell while they were away. */
	public static final AttachmentType<Map<UUID, List<Fallen>>> FALLEN = AttachmentRegistry.create(
			OnePieceMod.id("fallen_crewmates"),
			builder -> builder.persistent(Codec.unboundedMap(UUIDUtil.STRING_CODEC, Fallen.CODEC.listOf())));

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 10 != 0) {
				return;
			}
			for (ServerPlayer captain : server.getPlayerList().getPlayers()) {
				keepTogether(captain);
			}
		});
		// Through a portal: bring the Follow crew along right away.
		ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL.register((player, origin, destination) -> keepTogether(player));
		ServerPlayerEvents.AFTER_RESPAWN.register((oldPlayer, newPlayer, alive) -> keepTogether(newPlayer));
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> reportFallen(handler.player));
	}

	/** The crewmate with this id, if it's loaded in any world. */
	public static CrewmateEntity find(MinecraftServer server, UUID id) {
		for (ServerLevel level : server.getAllLevels()) {
			Entity entity = level.getEntity(id);
			if (entity instanceof CrewmateEntity crewmate) {
				return crewmate;
			}
		}
		return null;
	}

	private static void keepTogether(ServerPlayer captain) {
		Crew crew = captain.getAttached(CrewAttachments.CREW);
		if (crew == null || crew.members().isEmpty() || !captain.isAlive() || captain.isSpectator()) {
			return;
		}
		ShipEntity ship = captain.getVehicle() instanceof ShipEntity s ? s : null;
		for (UUID id : crew.members().values()) {
			CrewmateEntity crewmate = find(captain.level().getServer(), id);
			if (crewmate == null || !crewmate.isAlive() || crewmate.isKnockedOut()) {
				continue; // A knocked-out crewmate catches up once they're back on their feet.
			}
			// Nobody stays seated on a ship the captain isn't sailing: the first seat is the helm.
			if (crewmate.getVehicle() instanceof ShipEntity seat && seat != ship) {
				crewmate.stopRiding();
			}
			if (crewmate.getMode() != CrewMode.FOLLOW) {
				continue;
			}
			if (ship != null) {
				boardShip(crewmate, ship);
				continue;
			}
			boolean otherWorld = crewmate.level() != captain.level();
			if ((otherWorld || crewmate.distanceToSqr(captain) > CATCH_UP_DISTANCE * CATCH_UP_DISTANCE) && captain.onGround()) {
				bringTo(crewmate, captain);
			}
		}
	}

	private static void boardShip(CrewmateEntity crewmate, ShipEntity ship) {
		if (crewmate.getVehicle() == ship || crewmate.level() != ship.level()
				|| crewmate.distanceToSqr(ship) > BOARD_DISTANCE * BOARD_DISTANCE || !ship.canAddPassenger(crewmate)) {
			return;
		}
		crewmate.stopRiding();
		crewmate.getNavigation().stop();
		crewmate.startRiding(ship);
	}

	/** Moves a crewmate to a safe spot next to the captain, even from another world. */
	public static void bringTo(CrewmateEntity crewmate, ServerPlayer captain) {
		ServerLevel level = (ServerLevel) captain.level();
		Vec3 spot = safeSpotNear(level, crewmate, captain.blockPosition());
		crewmate.stopRiding();
		crewmate.getNavigation().stop();
		crewmate.teleportTo(level, spot.x, spot.y, spot.z, Set.of(), crewmate.getYRot(), crewmate.getXRot(), true);
	}

	private static Vec3 safeSpotNear(ServerLevel level, CrewmateEntity crewmate, BlockPos center) {
		for (int tries = 0; tries < 20; tries++) {
			int dx = crewmate.getRandom().nextInt(5) - 2;
			int dz = crewmate.getRandom().nextInt(5) - 2;
			if (dx == 0 && dz == 0) {
				continue;
			}
			for (int dy = -1; dy <= 1; dy++) {
				BlockPos pos = center.offset(dx, dy, dz);
				Vec3 feet = Vec3.atBottomCenterOf(pos);
				if (level.getBlockState(pos.below()).isFaceSturdy(level, pos.below(), Direction.UP)
						&& level.noCollision(crewmate, crewmate.getDimensions(crewmate.getPose()).makeBoundingBox(feet))) {
					return feet;
				}
			}
		}
		return Vec3.atBottomCenterOf(center); // Where the captain stands.
	}

	// ---------- Crewmates who fell while the captain was away ----------

	public static void rememberFallen(MinecraftServer server, UUID captainId, UUID crewmateId, String name) {
		ServerLevel overworld = server.overworld();
		Map<UUID, List<Fallen>> all = new HashMap<>(overworld.getAttachedOrElse(FALLEN, Map.of()));
		List<Fallen> list = new ArrayList<>(all.getOrDefault(captainId, List.of()));
		list.add(new Fallen(crewmateId, name));
		all.put(captainId, list);
		overworld.setAttached(FALLEN, all);
	}

	private static void reportFallen(ServerPlayer captain) {
		ServerLevel overworld = captain.level().getServer().overworld();
		Map<UUID, List<Fallen>> all = overworld.getAttachedOrElse(FALLEN, Map.of());
		List<Fallen> fallen = all.get(captain.getUUID());
		if (fallen == null) {
			return;
		}
		Map<UUID, List<Fallen>> rest = new HashMap<>(all);
		rest.remove(captain.getUUID());
		overworld.setAttached(FALLEN, rest);

		Crew crew = captain.getAttached(CrewAttachments.CREW);
		for (Fallen lost : fallen) {
			if (crew == null) {
				break;
			}
			for (CrewRole role : CrewRole.values()) {
				if (lost.id().equals(crew.member(role))) {
					crew = crew.withoutMember(role);
					captain.sendSystemMessage(Component.literal("While you were away, " + lost.name() + " fell in battle. The "
							+ role.title() + " spot on your crew is open again.").withStyle(ChatFormatting.RED));
				}
			}
		}
		if (crew != null) {
			captain.setAttached(CrewAttachments.CREW, crew);
		}
	}
}
