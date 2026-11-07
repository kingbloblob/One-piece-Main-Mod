package com.onepiecemod.seatrain;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.advancement.AdvancementFeature;
import com.onepiecemod.building.Parts;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.crew.CrewMode;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.story.StoryGates;
import com.onepiecemod.story.StoryProgress;

/**
 * Riding the Sea Train, from paying the fare to stepping off at the far end.
 *
 * A trip is a short scene, about ten seconds:
 * 1. The Puffing Tom appears at the platform with you in the cab, blows its horn and pulls away.
 * 2. The screen goes dark ("Next stop: Enies Lobby") while you cross the sea.
 * 3. You pull into the far station, the train stops, you step off and it steams away.
 * Your crewmates and pets who are following you come along. Sneak to skip the ride.
 */
public class Trips {
	/** The Water 7 chapter: the Puffing Tom takes you once your story reaches it. */
	static final String WATER_7 = "enies_lobby";

	private static final int DEPART_TICKS = 100;
	private static final int DARK_AT = 70;
	private static final int WAIT_TICKS = 20;
	private static final int ARRIVE_TICKS = 70;
	private static final double ARRIVE_DISTANCE = 30.0;

	private static final Map<UUID, Trip> TRIPS = new HashMap<>();

	private static final class Trip {
		final UUID player;
		final Station from;
		final Station to;
		SeaTrainEntity train;
		int ticks;
		boolean arriving;
		Vec3 landing;
		/** Where the arriving train stops (the cab beside the landing spot, or on the booth's track). */
		Vec3 stopAt;
		float arriveYaw;
		final List<UUID> companions = new ArrayList<>();

		Trip(UUID player, Station from, Station to) {
			this.player = player;
			this.from = from;
			this.to = to;
		}
	}

	/** Shorthand so this class reads like the rest of the package. */
	private record Station(String id, String name, boolean puffingTom, BlockPos pos, String dim) {
		static Station of(Stations.Station s) {
			return new Station(s.id(), s.name(), s.puffingTom(), s.pos(), s.dim());
		}
	}

	// ---------- Rules ----------

	/** True once the player's story has reached Water 7 (or in Creative, or with story gates off). */
	public static boolean puffingTomOpen(ServerPlayer player) {
		return !StoryGates.gatesOn(player) || StoryProgress.orStart(player).reached(WATER_7);
	}

	/** True once the player has finished the Water 7 chapter: Iceburg's crews will run a line for them. */
	public static boolean ownLinesOpen(ServerPlayer player) {
		return !StoryGates.gatesOn(player) || StoryProgress.orStart(player).completed(WATER_7);
	}

	/** Puffing Tom fare in Berries. */
	static int berryFare(int distance) {
		return 15 + distance / 100;
	}

	/** Fare on your own line, paid in coal for the boiler. */
	static int coalFare(int distance) {
		return Math.max(1, distance / 300);
	}

	static boolean onTrip(ServerPlayer player) {
		return TRIPS.containsKey(player.getUUID());
	}

	// ---------- Booking ----------

	/** Checks everything, takes the fare and starts the trip. Messages the player if it can't. */
	static boolean book(ServerPlayer player, Stations.Station fromStation, Stations.Station toStation) {
		if (onTrip(player)) {
			return false;
		}
		if (fromStation.id().equals(toStation.id())) {
			player.sendSystemMessage(Component.literal("You're already here.").withStyle(ChatFormatting.RED));
			return false;
		}
		if (!fromStation.dim().equals(toStation.dim())) {
			player.sendSystemMessage(Component.literal("No Sea Train runs between worlds.").withStyle(ChatFormatting.RED));
			return false;
		}
		if (!player.isCreative() && player.tickCount - player.getLastHurtByMobTimestamp() < 200
				&& player.getLastHurtByMob() != null && player.getLastHurtByMob().isAlive()) {
			player.sendSystemMessage(Component.literal("The conductor won't let you aboard in the middle of a fight.").withStyle(ChatFormatting.RED));
			return false;
		}
		if (player.isPassenger()) {
			player.sendSystemMessage(Component.literal("Get off first.").withStyle(ChatFormatting.RED));
			return false;
		}
		if (fromStation.puffingTom() && !puffingTomOpen(player)) {
			player.sendSystemMessage(Component.literal("\"Sorry, this line opens for you once your story reaches Water 7.\"").withStyle(ChatFormatting.RED));
			return false;
		}
		if (!fromStation.puffingTom() && !ownLinesOpen(player)) {
			player.sendSystemMessage(Component.literal("Nobody here can drive a Sea Train yet. Finish the Water 7 chapter first.").withStyle(ChatFormatting.RED));
			return false;
		}
		int distance = (int) Math.sqrt(fromStation.pos().distSqr(toStation.pos()));
		if (!canPay(player, fromStation.puffingTom(), distance)) {
			return false;
		}
		Trip trip = new Trip(player.getUUID(), Station.of(fromStation), Station.of(toStation));
		ServerLevel level = (ServerLevel) player.level();
		for (Entity companion : companions(player)) {
			trip.companions.add(companion.getUUID());
		}
		float wanted = toward(player.position(), Vec3.atCenterOf(toStation.pos()));
		Track track = fromStation.puffingTom() ? null : track(level, fromStation.pos());
		Vec3 board = track != null ? track.seat() : player.position();
		float yaw = track != null ? track.pick(wanted) : clearestYaw(level, player.blockPosition(), wanted, +1);
		Vec3 seat = SeaTrainEntity.SEAT.yRot(-yaw * ((float) Math.PI / 180f));
		trip.train = spawnTrain(level, board.subtract(seat), yaw);
		if (trip.train == null) {
			return false;
		}
		if (!player.startRiding(trip.train, true, true)) {
			trip.train.scrap();
			player.sendSystemMessage(Component.literal("You couldn't get aboard.").withStyle(ChatFormatting.RED));
			return false;
		}
		pay(player, fromStation.puffingTom(), distance);
		level.playSound(null, player.blockPosition(), SoundEvents.GOAT_HORN_SOUND_VARIANTS.get(7).value(), SoundSource.NEUTRAL, 3.0f, 0.8f);
		player.sendSystemMessage(Component.literal("All aboard! Next stop: " + toStation.name() + ". (Sneak to skip the ride.)")
				.withStyle(ChatFormatting.AQUA));
		TRIPS.put(player.getUUID(), trip);
		AdvancementFeature.grant(player, "journey/sea_train");
		return true;
	}

	private static boolean canPay(ServerPlayer player, boolean puffingTom, int distance) {
		if (player.isCreative()) {
			return true;
		}
		if (puffingTom) {
			int fare = berryFare(distance);
			if (Parts.count(player, CharacterFeature.BERRY) < fare) {
				player.sendSystemMessage(Component.literal("The ticket costs " + fare + " Berries.").withStyle(ChatFormatting.RED));
				return false;
			}
		} else {
			int fare = coalFare(distance);
			if (Parts.count(player, Items.COAL) + Parts.count(player, Items.CHARCOAL) < fare) {
				player.sendSystemMessage(Component.literal("The boiler needs " + fare + " Coal or Charcoal for that trip.").withStyle(ChatFormatting.RED));
				return false;
			}
		}
		return true;
	}

	private static void pay(ServerPlayer player, boolean puffingTom, int distance) {
		if (player.isCreative()) {
			return;
		}
		if (puffingTom) {
			Parts.take(player, CharacterFeature.BERRY, berryFare(distance));
		} else {
			takeCoal(player, coalFare(distance));
		}
	}

	private static boolean takeCoal(ServerPlayer player, int amount) {
		int coal = Parts.count(player, Items.COAL);
		int charcoal = Parts.count(player, Items.CHARCOAL);
		if (coal + charcoal < amount) {
			return false;
		}
		int fromCoal = Math.min(coal, amount);
		take(player, Items.COAL, fromCoal);
		take(player, Items.CHARCOAL, amount - fromCoal);
		return true;
	}

	private static void take(ServerPlayer player, Item item, int amount) {
		if (amount > 0) {
			Parts.take(player, item, amount);
		}
	}

	/** Crewmates who are following you and pets who aren't told to sit, close by. */
	private static List<Entity> companions(ServerPlayer player) {
		List<Entity> list = new ArrayList<>();
		AABB box = player.getBoundingBox().inflate(24.0);
		for (TamableAnimal pet : player.level().getEntitiesOfClass(TamableAnimal.class, box, pet -> pet.isOwnedBy(player))) {
			if (pet instanceof CrewmateEntity crewmate ? crewmate.getMode() == CrewMode.FOLLOW : !pet.isOrderedToSit()) {
				if (!pet.isPassenger() && !pet.isLeashed()) {
					list.add(pet);
				}
			}
		}
		return list;
	}

	// ---------- Running trips ----------

	static void tick(MinecraftServer server) {
		Iterator<Trip> iterator = TRIPS.values().iterator();
		while (iterator.hasNext()) {
			Trip trip = iterator.next();
			ServerPlayer player = server.getPlayerList().getPlayer(trip.player);
			if (player == null || !player.isAlive()) {
				if (trip.train != null) {
					trip.train.scrap();
				}
				iterator.remove();
				continue;
			}
			if (!step(trip, player)) {
				iterator.remove();
			}
		}
	}

	/** Moves one trip on by a tick. Returns false when it's over. */
	private static boolean step(Trip trip, ServerPlayer player) {
		trip.ticks++;
		ServerLevel level = (ServerLevel) player.level();
		boolean aboard = trip.train != null && player.getVehicle() == trip.train;

		if (!trip.arriving) {
			if (!aboard) {
				return skip(trip, player); // Sneaked off: straight to the far station.
			}
			SeaTrainEntity train = trip.train;
			if (trip.ticks == 20) {
				train.setSpeed(0.02, 0.025); // Pull away, faster and faster.
				level.playSound(null, train.blockPosition(), SoundEvents.PISTON_EXTEND, SoundSource.NEUTRAL, 1.5f, 0.5f);
			}
			if (trip.ticks > 20 && trip.ticks % 8 == 0) {
				level.playSound(null, train.blockPosition(), SoundEvents.BLAZE_SHOOT, SoundSource.NEUTRAL, 0.5f, 0.5f); // chug
			}
			if (trip.ticks == DARK_AT) {
				fadeOut(player, trip.to.name());
			}
			if (trip.ticks >= DEPART_TICKS) {
				train.leave(20);
				player.stopRiding();
				trip.train = null;
				crossTheSea(trip, player);
			}
			return true;
		}

		// Arriving.
		if (trip.train == null) {
			if (trip.ticks < DEPART_TICKS + WAIT_TICKS || !level.isLoaded(BlockPos.containing(trip.landing))) {
				return true; // Let the far station's chunks load while the screen is dark.
			}
			Vec3 back = Vec3.directionFromRotation(0f, trip.arriveYaw).scale(-ARRIVE_DISTANCE);
			Vec3 seat = SeaTrainEntity.SEAT.yRot(-trip.arriveYaw * ((float) Math.PI / 180f));
			trip.train = spawnTrain(level, trip.stopAt.add(back).subtract(seat), trip.arriveYaw);
			if (trip.train == null) {
				return finish(trip, player);
			}
			// Slow down evenly so she stops right at the platform: v = 2d/t to start, then brake.
			double start = 2 * ARRIVE_DISTANCE / ARRIVE_TICKS;
			trip.train.setSpeed(start, -start / ARRIVE_TICKS);
			player.startRiding(trip.train, true, true);
			return true;
		}
		if (!aboard) {
			return finish(trip, player);
		}
		if (trip.ticks % 8 == 0 && trip.train.speed() > 0.05) {
			level.playSound(null, trip.train.blockPosition(), SoundEvents.BLAZE_SHOOT, SoundSource.NEUTRAL, 0.5f, 0.5f);
		}
		if (trip.train.speed() <= 0.0) {
			level.playSound(null, trip.train.blockPosition(), SoundEvents.GOAT_HORN_SOUND_VARIANTS.get(7).value(), SoundSource.NEUTRAL, 3.0f, 0.8f);
			return finish(trip, player);
		}
		return true;
	}

	private static void fadeOut(ServerPlayer player, String destination) {
		player.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 80, 0, false, false, false));
		player.connection.send(new ClientboundSetTitlesAnimationPacket(10, 40, 15));
		player.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal("Next stop: " + destination).withStyle(ChatFormatting.WHITE)));
		player.connection.send(new ClientboundSetTitleTextPacket(Component.literal("Puffing Tom").withStyle(ChatFormatting.AQUA)));
	}

	/** Moves the player (in the dark) to the far end, then the arriving train comes for them. */
	private static void crossTheSea(Trip trip, ServerPlayer player) {
		ServerLevel level = levelOf(player.level().getServer(), trip.to.dim());
		if (level == null) {
			trip.arriving = true;
			return;
		}
		BlockPos landing = trip.to.puffingTom() ? trip.to.pos() : boothLanding(level, trip.to.pos());
		trip.landing = Vec3.atBottomCenterOf(landing);
		Vec3 from = Vec3.atCenterOf(trip.from.pos());
		Track track = trip.to.puffingTom() ? null : track(level, trip.to.pos());
		trip.stopAt = track != null ? track.seat() : trip.landing;
		trip.arriveYaw = track != null ? track.pick(toward(from, trip.landing))
				: clearestYaw(level, landing, toward(from, trip.landing), -1);
		trip.arriving = true;
		trip.ticks = Math.max(trip.ticks, DEPART_TICKS);
		if (!player.hasEffect(MobEffects.BLINDNESS)) {
			fadeOut(player, trip.to.name());
		}
		player.teleportTo(level, trip.landing.x, trip.landing.y, trip.landing.z, java.util.Set.of(), player.getYRot(), player.getXRot(), false);
		bringCompanions(trip, player, level);
	}

	/** Sneaked off the departing train: no ride, just go. */
	private static boolean skip(Trip trip, ServerPlayer player) {
		if (trip.train != null) {
			trip.train.leave(40);
			trip.train = null;
		}
		crossTheSea(trip, player);
		trip.ticks = DEPART_TICKS + WAIT_TICKS + ARRIVE_TICKS;
		return finish(trip, player);
	}

	/** Steps off onto the platform; the train steams away. */
	private static boolean finish(Trip trip, ServerPlayer player) {
		if (trip.train != null) {
			if (player.getVehicle() == trip.train) {
				player.stopRiding();
			}
			trip.train.leave(60);
		}
		if (trip.landing != null) {
			player.teleportTo(trip.landing.x, trip.landing.y, trip.landing.z);
			player.removeEffect(MobEffects.BLINDNESS);
			player.sendSystemMessage(Component.literal("Arrived at " + trip.to.name() + ".").withStyle(ChatFormatting.GREEN));
		}
		return false;
	}

	private static void bringCompanions(Trip trip, ServerPlayer player, ServerLevel level) {
		ServerLevel fromLevel = levelOf(player.level().getServer(), trip.from.dim());
		if (fromLevel == null) {
			return;
		}
		for (UUID id : trip.companions) {
			Entity companion = fromLevel.getEntity(id);
			if (companion != null && companion.isAlive() && !companion.isPassenger()) {
				companion.teleportTo(level, trip.landing.x, trip.landing.y, trip.landing.z, java.util.Set.of(),
						companion.getYRot(), companion.getXRot(), false);
			}
		}
	}

	/** A parked train 4 blocks to the player's right, facing where they face; it leaves after 30 seconds. */
	static void preview(ServerPlayer player) {
		float yaw = Math.round(player.getYRot() / 45f) * 45f;
		Vec3 right = Vec3.directionFromRotation(0f, yaw + 90f).scale(4);
		SeaTrainEntity train = spawnTrain((ServerLevel) player.level(), player.position().add(right), yaw);
		if (train != null) {
			train.onTrip = false;
			train.leave(600);
			train.setSpeed(0, 0);
		}
	}

	// ---------- Helpers ----------

	private static SeaTrainEntity spawnTrain(ServerLevel level, Vec3 pos, float yaw) {
		SeaTrainEntity train = SeaTrainFeature.SEA_TRAIN.create(level, EntitySpawnReason.TRIGGERED);
		if (train == null) {
			return null;
		}
		train.setPos(pos.x, pos.y, pos.z);
		train.setYRot(yaw);
		train.yRotO = yaw;
		train.onTrip = true;
		level.addFreshEntity(train);
		PuffingTom.assemble(level, train);
		return train;
	}

	/** The yaw that faces from one point to another. */
	private static float toward(Vec3 from, Vec3 to) {
		Vec3 d = to.subtract(from);
		return (float) (Math.atan2(-d.x, d.z) * 180.0 / Math.PI);
	}

	/**
	 * Of the eight compass headings near the wanted one, the one with the fewest blocks in the way
	 * of the train (ahead when leaving, behind when arriving), so it doesn't plough through houses.
	 */
	private static float clearestYaw(ServerLevel level, BlockPos origin, float wanted, int sign) {
		float best = wanted;
		int bestScore = Integer.MAX_VALUE;
		for (int i = 0; i < 8; i++) {
			float yaw = Math.round(wanted / 45f) * 45f + i * 45f;
			float off = Math.abs(((yaw - wanted) % 360 + 540) % 360 - 180);
			Vec3 dir = Vec3.directionFromRotation(0f, yaw).scale(sign);
			int blocked = 0;
			for (int step = 2; step <= 30; step += 2) {
				for (int side = -1; side <= 1; side++) {
					Vec3 at = Vec3.atBottomCenterOf(origin).add(dir.scale(step)).add(new Vec3(-dir.z, 0, dir.x).scale(side * 1.5));
					for (int dy = 1; dy <= 3; dy++) {
						if (!level.getBlockState(BlockPos.containing(at.x, origin.getY() + dy, at.z)).getCollisionShape(level, origin).isEmpty()) {
							blocked++;
						}
					}
				}
			}
			int score = blocked * 10 + (int) off; // A clear track wins; ties go to the straightest one.
			if (score < bestScore) {
				bestScore = score;
				best = yaw;
			}
		}
		return best;
	}

	/**
	 * A player station's track: the platform edge with the most rails. The train's cab stops at its middle,
	 * running along it one way or the other.
	 */
	private record Track(Vec3 seat, float yaw) {
		/** Of the two ways along the track, the one closer to the wanted heading. */
		float pick(float wanted) {
			float off = Math.abs(((yaw - wanted) % 360 + 540) % 360 - 180);
			return off <= 90 ? yaw : yaw + 180;
		}
	}

	private static Track track(ServerLevel level, BlockPos booth) {
		Track best = null;
		int bestRails = 0;
		for (Direction side : Direction.Plane.HORIZONTAL) {
			int rails = 0;
			for (int i = -2; i <= 2; i++) {
				if (level.getBlockState(booth.relative(side, 2).relative(side.getClockWise(), i)).is(BlockTags.RAILS)) {
					rails++;
				}
			}
			if (rails > bestRails) {
				bestRails = rails;
				best = new Track(Vec3.atBottomCenterOf(booth.relative(side, 2)), side.getClockWise().toYRot());
			}
		}
		return best;
	}

	/** A free spot beside a booth, on its platform. */
	private static BlockPos boothLanding(ServerLevel level, BlockPos booth) {
		for (Direction direction : Direction.Plane.HORIZONTAL) {
			BlockPos spot = booth.relative(direction);
			if (level.getBlockState(spot).getCollisionShape(level, spot).isEmpty()
					&& level.getBlockState(spot.above()).getCollisionShape(level, spot).isEmpty()) {
				return spot;
			}
		}
		return booth.above();
	}

	private static ServerLevel levelOf(MinecraftServer server, String dim) {
		return server.getLevel(ResourceKey.create(Registries.DIMENSION, Identifier.parse(dim)));
	}

	static boolean isOverworld(Level level) {
		return level.dimension() == Level.OVERWORLD;
	}
}
