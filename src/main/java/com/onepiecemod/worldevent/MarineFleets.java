package com.onepiecemod.worldevent;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import org.jetbrains.annotations.Nullable;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.npc.NpcNames;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipFeature;
import com.onepiecemod.ship.ShipLayout;
import com.onepiecemod.shipcombat.ShipBrain;
import com.onepiecemod.shipcombat.ShipDesigns;
import com.onepiecemod.shipcombat.ShipHull;
import com.onepiecemod.sound.ModSounds;

/**
 * Marine fleets crossing the sea. Now and then a sailing player sees a column of 3-5 Marine ships (a Vice Admiral's
 * flagship in front) pass across the horizon on their way somewhere. They keep their course and leave you alone,
 * unless you are a wanted pirate who comes within 60 blocks, or you fire on them: then the whole fleet turns to fight.
 * Further out on the Grand Line the fleets are bigger and their ships tougher.
 *
 * During the Reverie, fleets escort a Royal Galleon carrying a king and his treasure to Mary Geoise.
 * Sinking or capturing it is a crime the whole world hears about.
 */
public class MarineFleets {
	public static final String TAG = "onepiece_marine_fleet";
	public static final String ROYAL_TAG = "onepiece_royal_ship";

	// ---- How often. ----
	private static final int CHECK_EVERY = 20 * 60;          // ticks between rolls
	private static final float CHANCE = 0.08f;               // per sailing player per roll
	private static final int COOLDOWN = 20 * 60 * 15;        // ticks before the same player sees another fleet
	private static final double NOTICE_RANGE = 60;           // wanted pirates closer than this get attacked
	private static final double SPAWN_DISTANCE = 140;
	private static final double SPACING = 26;

	private static final Map<UUID, Long> NEXT_FLEET = new HashMap<>();
	private static final List<Fleet> FLEETS = new ArrayList<>();

	static void tick(MinecraftServer server) {
		ServerLevel level = server.overworld();
		Iterator<Fleet> it = FLEETS.iterator();
		while (it.hasNext()) {
			if (!it.next().tick(level)) {
				it.remove();
			}
		}
		if (server.getTickCount() % CHECK_EVERY != 0 || level.getDifficulty() == Difficulty.PEACEFUL) {
			return;
		}
		float chance = CHANCE * Reverie.fleetMultiplier(server);
		long now = level.getGameTime();
		for (ServerPlayer player : level.players()) {
			if (!(ShipEntity.aboard(player) instanceof ShipEntity ship) || ShipBrain.isAi(ship) || player.isSpectator()
					|| now < NEXT_FLEET.getOrDefault(player.getUUID(), 0L) || fleetNear(player)) {
				continue;
			}
			if (player.getRandom().nextFloat() < chance && send(level, player, Reverie.isActive(server)) != null) {
				NEXT_FLEET.put(player.getUUID(), now + COOLDOWN);
			}
		}
	}

	private static boolean fleetNear(Player player) {
		for (Fleet fleet : FLEETS) {
			Vec3 lead = fleet.lastPos;
			if (lead != null && lead.distanceToSqr(player.position()) < 400 * 400) {
				return true;
			}
		}
		return false;
	}

	/** Sends a fleet past this player. Returns an error, or null if it's on its way. */
	@Nullable
	static String send(ServerLevel level, ServerPlayer player, boolean royal) {
		RandomSource random = level.getRandom();
		double ring = Math.sqrt(player.getX() * player.getX() + player.getZ() * player.getZ());
		int tier = ring < 1500 ? 1 : ring < 3500 ? 2 : ring < 6000 ? 3 : 4;
		int size = 3 + random.nextInt(2) + (tier >= 3 ? 1 : 0);

		for (int attempt = 0; attempt < 12; attempt++) {
			// Start off to one side, aim at a spot 40-70 blocks from the player, and carry on past.
			double side = random.nextDouble() * Math.PI * 2;
			Vec3 start = player.position().add(Math.cos(side) * SPAWN_DISTANCE, 0, Math.sin(side) * SPAWN_DISTANCE);
			double miss = (40 + random.nextInt(31)) * (random.nextBoolean() ? 1 : -1);
			Vec3 passBy = player.position().add(-Math.sin(side) * miss, 0, Math.cos(side) * miss);
			float heading = WorldEvents.yawTowards(passBy.x - start.x, passBy.z - start.z);
			Vec3 back = new Vec3(Mth.sin(heading * Mth.DEG_TO_RAD), 0, -Mth.cos(heading * Mth.DEG_TO_RAD)); // Behind the leader.

			List<Vec3> spots = new ArrayList<>();
			for (int i = 0; i < size; i++) {
				Vec3 spot = start.add(back.scale(i * SPACING));
				if (WorldEvents.deepWaterSurface(level, Mth.floor(spot.x), Mth.floor(spot.z)) == null
						|| WorldEvents.deepWaterSurface(level, Mth.floor(spot.x) + 9, Mth.floor(spot.z)) == null
						|| WorldEvents.deepWaterSurface(level, Mth.floor(spot.x) - 9, Mth.floor(spot.z)) == null) {
					break;
				}
				spots.add(spot);
			}
			if (spots.size() < Math.min(3, size)) {
				continue;
			}

			String admiral = NpcNames.surname(random);
			Fleet fleet = new Fleet(heading, royal, admiral);
			for (int i = 0; i < spots.size(); i++) {
				boolean flagship = i == 0;
				boolean royalShip = royal && i == 1;
				ShipEntity ship = spawnShip(level, spots.get(i), heading, tier, flagship, royalShip, admiral);
				if (ship != null) {
					fleet.ships.add(ship.getUUID());
					if (royalShip) {
						fleet.royalShip = ship.getUUID();
					}
				}
			}
			if (fleet.ships.isEmpty()) {
				return "Couldn't place the ships.";
			}
			fleet.lastPos = spots.get(0);
			FLEETS.add(fleet);
			String what = royal ? "A Marine fleet is escorting a Royal Galleon to the Reverie" : "A Marine fleet under Vice Admiral " + admiral + " is crossing the sea";
			player.sendSystemMessage(Component.literal(what + ". " + (Bounty.get(player) > 0
					? "Keep your distance, pirate: they'll attack within 60 blocks." : "They won't bother you if you don't bother them."))
					.withStyle(royal ? ChatFormatting.LIGHT_PURPLE : ChatFormatting.AQUA));
			ModSounds.play(player, ModSounds.NAVY_BUGLE, 0.5f);
			return null;
		}
		return "No open sea for a fleet around here.";
	}

	@Nullable
	private static ShipEntity spawnShip(ServerLevel level, Vec3 spot, float heading, int tier, boolean flagship, boolean royal, String admiral) {
		Integer surface = WorldEvents.deepWaterSurface(level, Mth.floor(spot.x), Mth.floor(spot.z));
		if (surface == null) {
			return null;
		}
		ShipEntity ship = ShipFeature.SHIP.create(level, EntitySpawnReason.EVENT);
		if (ship == null) {
			return null;
		}
		ShipLayout layout = royal ? royalGalleon() : ShipDesigns.marine(level, flagship || tier >= 3).layout();
		ship.setLayout(layout);
		ship.snapTo(Mth.floor(spot.x) + 0.5, surface - layout.waterline, Mth.floor(spot.z) + 0.5, heading, 0);
		ship.setCustomName(Component.literal(royal ? "Royal Galleon" : flagship ? "Vice Admiral " + admiral + "'s Flagship"
				: tier >= 3 ? "Marine Battleship" : "Marine Warship"));
		ShipBrain.mark(ship, ShipBrain.Faction.MARINE, royal ? 0 : tier + (flagship ? 1 : 0));
		ship.addTag(TAG);
		if (royal) {
			ship.addTag(ROYAL_TAG);
		}
		ShipHull.setMax(ship, ShipHull.sizeToHull(layout.size()) * (1 + tier * 0.25f) * (flagship ? 1.4f : 1f));
		level.addFreshEntity(ship);
		return ship;
	}

	/** A Marine galleon painted for royalty: white and gold, purple sails, and treasure in the hold. */
	private static ShipLayout royalGalleon() {
		ShipLayout base = ShipDesigns.pirateGalleon();
		List<ShipLayout.ShipBlock> blocks = new ArrayList<>();
		for (ShipLayout.ShipBlock block : base.blocks) {
			BlockState state = block.state();
			BlockState swapped = state.is(Blocks.WOOL.red()) ? (block.pos().getY() <= 3 ? Blocks.GOLD_BLOCK : Blocks.WOOL.purple()).defaultBlockState()
					: state.is(Blocks.WOOL.black()) ? Blocks.WOOL.yellow().defaultBlockState()
					: state.is(Blocks.STRIPPED_DARK_OAK_LOG) ? Blocks.CONCRETE.white().defaultBlockState()
					: state;
			Optional<net.minecraft.nbt.CompoundTag> nbt = block.nbt();
			if (nbt.isPresent() && nbt.get().getStringOr("LootTable", "").equals("onepiece:chests/pirate")) {
				net.minecraft.nbt.CompoundTag copy = nbt.get().copy();
				copy.putString("LootTable", "onepiece:chests/treasure");
				nbt = Optional.of(copy);
			}
			blocks.add(new ShipLayout.ShipBlock(block.pos(), swapped, nbt));
		}
		return new ShipLayout(blocks, base.flags, base.helm, base.bow, base.waterline);
	}

	/** Royal ship sunk or taken: a world-shaking crime. */
	private static void royalShipLost(ServerLevel level, ShipEntity ship) {
		ServerPlayer culprit = null;
		double best = 120 * 120;
		for (ServerPlayer player : level.players()) {
			double d = player.distanceToSqr(ship);
			if (d < best && !player.isSpectator()) {
				best = d;
				culprit = player;
			}
		}
		if (culprit == null) {
			return;
		}
		WorldNews.report(level.getServer(), "Pirate " + culprit.getName().getString() + " attacked a Royal Galleon on its way to the Reverie!",
				ChatFormatting.LIGHT_PURPLE);
		Bounty.raise(culprit, 40_000_000L * (Bounty.threatLevel(culprit) + 1), "You attacked royalty!", true);
	}

	// ------------------------------------------------------------------------------------------

	private static class Fleet {
		final float heading;
		final boolean royal;
		final String admiral;
		final List<UUID> ships = new ArrayList<>();
		UUID royalShip;
		boolean royalLost = false;
		boolean engaged = false;
		Vec3 lastPos;
		final Map<UUID, Integer> avoid = new HashMap<>();
		final Map<UUID, Float> avoidYaw = new HashMap<>();

		Fleet(float heading, boolean royal, String admiral) {
			this.heading = heading;
			this.royal = royal;
			this.admiral = admiral;
		}

		/** False once every ship is gone. */
		boolean tick(ServerLevel level) {
			List<ShipEntity> alive = new ArrayList<>();
			for (UUID id : ships) {
				Entity entity = level.getEntity(id);
				if (entity instanceof ShipEntity ship && ship.isAlive()) {
					alive.add(ship);
				}
			}
			if (royalShip != null && !royalLost) {
				Entity royalEntity = level.getEntity(royalShip);
				if (royalEntity instanceof ShipEntity ship && (ship.sinking || !ship.getPassengers().isEmpty())) {
					royalLost = true;
					royalShipLost(level, ship);
				}
			}
			if (alive.isEmpty()) {
				return false;
			}
			lastPos = alive.get(0).position();

			if (!engaged && level.getGameTime() % 10 == 0 && provoked(level, alive)) {
				engaged = true;
				for (ShipEntity ship : alive) {
					for (Entity passenger : level.players()) {
						if (passenger.distanceToSqr(ship) < 120 * 120 && passenger instanceof ServerPlayer player) {
							player.sendSystemMessage(Component.literal("Vice Admiral " + admiral + "'s fleet is coming about to attack!")
									.withStyle(ChatFormatting.RED));
							ModSounds.play(player, ModSounds.NAVY_BUGLE);
						}
					}
					break;
				}
			}
			if (engaged) {
				return true; // ShipBrain is in charge now: they fight, and leave when nobody's around.
			}
			// Cruising: everyone holds the fleet's heading and steers round land. ShipBrain has already steered
			// this tick (ship combat runs first), so this replaces its choice.
			for (ShipEntity ship : alive) {
				if (ship.sinking || !ship.getPassengers().isEmpty()) {
					continue;
				}
				float yaw = ship.getYRot();
				float desired = heading;
				int left = avoid.getOrDefault(ship.getUUID(), 0);
				if (left > 0) {
					avoid.put(ship.getUUID(), left - 1);
					desired = avoidYaw.get(ship.getUUID());
				} else if (!openWater(level, ship, yaw, 14) || !openWater(level, ship, yaw, 24)) {
					float turn = openWater(level, ship, yaw + 60, 20) ? yaw + 60 : yaw - 60;
					avoid.put(ship.getUUID(), 60);
					avoidYaw.put(ship.getUUID(), turn);
					desired = turn;
				}
				float turnNeeded = Mth.wrapDegrees(desired - yaw);
				ship.aiTurn = Mth.clamp(-turnNeeded / 15f, -1f, 1f);
				ship.aiForward = 0.8f;
			}
			return true;
		}

		/** Somebody fired on the fleet, or a wanted pirate sailed too close. */
		boolean provoked(ServerLevel level, List<ShipEntity> alive) {
			for (ShipEntity ship : alive) {
				if (ShipHull.get(ship) < ShipHull.max(ship) - 0.5f) {
					return true;
				}
				for (ServerPlayer player : level.players()) {
					if (!player.isCreative() && !player.isSpectator() && Bounty.get(player) > 0
							&& player.distanceToSqr(ship) < NOTICE_RANGE * NOTICE_RANGE) {
						return true;
					}
				}
			}
			return false;
		}

		static boolean openWater(ServerLevel level, ShipEntity ship, float yaw, double ahead) {
			float radians = yaw * Mth.DEG_TO_RAD;
			double x = ship.getX() - Mth.sin(radians) * ahead;
			double z = ship.getZ() + Mth.cos(radians) * ahead;
			BlockPos surface = BlockPos.containing(x, ship.getY() + ship.getLayout().waterline - 0.5, z);
			if (!level.hasChunkAt(surface)) {
				return true; // Unknown sea ahead: keep going (unloaded ships don't tick anyway).
			}
			return level.getFluidState(surface).is(FluidTags.WATER) && level.getFluidState(surface.below()).is(FluidTags.WATER)
					&& level.getBlockState(surface.above()).canBeReplaced();
		}
	}

	static int count() {
		return FLEETS.size();
	}

	static void clear() {
		FLEETS.clear();
	}
}
