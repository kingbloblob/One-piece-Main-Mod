package com.onepiecemod.voyage;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import org.jetbrains.annotations.Nullable;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.monster.skeleton.Skeleton;
import net.minecraft.world.entity.npc.wanderingtrader.WanderingTrader;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.sea.CalmBelt;
import com.onepiecemod.ship.ShipDecks;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipFeature;
import com.onepiecemod.ship.ShipLayout;
import com.onepiecemod.shipcombat.ShipHull;
import com.onepiecemod.town.TownData;
import com.onepiecemod.weather.SeaEvent;
import com.onepiecemod.weather.SeaEventType;
import com.onepiecemod.weather.SeaEvents;

/**
 * Ships that are just passing by, neither Marine nor pirate. They hold a course across the sea and vanish over the
 * horizon once nobody is near.
 * - Merchant ship: sail alongside and step aboard to trade with the Sea Merchant. Sink her and the cargo is yours,
 *   but that's piracy: your bounty goes up.
 * - Derelict: a battered sloop with nobody aboard, drifting. Loot the chest, and take the wheel to make her yours.
 * - Ghost ship (at night, or in the Florian Triangle's mist): a grey galleon. Step aboard and its skeleton crew
 *   rises from the deck. Its chests are worth it, and it can be claimed like a derelict.
 */
public final class WanderingShips {
	public enum Kind { MERCHANT, DERELICT, GHOST }

	public static final String TAG = "onepiece_wanderer";
	private static final String KIND_TAG = "onepiece_wanderer_";
	private static final String CREW_TAG = "onepiece_ghost_crew";

	// ---- Tune these ----
	private static final int CHECK_EVERY = 20 * 60;
	private static final float CHANCE = 0.12f;
	private static final int COOLDOWN = 20 * 60 * 6;
	/** Nobody within this many blocks for a while: the ship sails over the horizon. */
	private static final double DESPAWN_RANGE = 220;
	private static final long PIRACY_BOUNTY = 6_000_000L;

	private static final Map<UUID, Long> NEXT = new HashMap<>();
	/** Ghost ships whose crew already rose, and merchant ships whose sinking was already dealt with. */
	private static final Set<UUID> HANDLED = new HashSet<>();
	private static final Map<UUID, Float> COURSE = new HashMap<>();
	private static final Map<UUID, Integer> AWAY = new HashMap<>();
	private static final Map<UUID, Integer> AVOID = new HashMap<>();
	/** Where each ship was a second ago, to notice it has run aground; and how long it's backing off. */
	private static final Map<UUID, Vec3> LAST_POS = new HashMap<>();
	private static final Map<UUID, Integer> REVERSE = new HashMap<>();

	private WanderingShips() {
	}

	static void clear() {
		NEXT.clear();
		HANDLED.clear();
		COURSE.clear();
		AWAY.clear();
		AVOID.clear();
		LAST_POS.clear();
		REVERSE.clear();
	}

	@Nullable
	public static Kind kindOf(ShipEntity ship) {
		for (Kind kind : Kind.values()) {
			if (ship.entityTags().contains(KIND_TAG + kind.name().toLowerCase())) {
				return kind;
			}
		}
		return null;
	}

	static void tick(MinecraftServer server) {
		ServerLevel level = server.overworld();
		for (ShipEntity ship : com.onepiecemod.shipcombat.ShipCombat.loadedShips()) {
			if (ship.level() == level && ship.entityTags().contains(TAG)) {
				steer(level, ship, server.getTickCount());
			}
		}
		if (server.getTickCount() % CHECK_EVERY != 29) {
			return;
		}
		long now = level.getGameTime();
		for (ServerPlayer player : level.players()) {
			ShipEntity ship = SeaSpots.sailing(player);
			if (ship == null || now < NEXT.getOrDefault(player.getUUID(), 0L) || player.getRandom().nextFloat() >= CHANCE
					|| wanderersNear(level, ship.position(), 300) > 0) {
				continue;
			}
			CalmBelt.Sea sea = SeaSpots.sea(level, ship.blockPosition());
			if (sea == null || sea == CalmBelt.Sea.CALM_BELT) {
				continue;
			}
			if (start(level, player, ship, pick(level, player, sea)) == null) {
				NEXT.put(player.getUUID(), now + COOLDOWN);
			}
		}
	}

	private static Kind pick(ServerLevel level, ServerPlayer player, CalmBelt.Sea sea) {
		RandomSource random = level.getRandom();
		SeaEvent mist = SeaEvents.eventNear(player.getX(), player.getZ(), 30);
		boolean spooky = mist != null && mist.type == SeaEventType.FLORIAN_MIST;
		if (spooky || !level.isBrightOutside() && sea.grandLine() && random.nextFloat() < 0.45f) {
			return Kind.GHOST;
		}
		return random.nextFloat() < 0.6f ? Kind.MERCHANT : Kind.DERELICT;
	}

	/** True if any ship at all is this close (so a new one doesn't appear inside it). */
	private static boolean shipNear(ServerLevel level, Vec3 at, double within) {
		for (ShipEntity other : com.onepiecemod.shipcombat.ShipCombat.loadedShips()) {
			if (other.level() == level && !other.isRemoved() && other.position().distanceToSqr(at.x, other.getY(), at.z) < within * within) {
				return true;
			}
		}
		return false;
	}

	private static int wanderersNear(ServerLevel level, Vec3 at, double within) {
		int count = 0;
		for (ShipEntity other : com.onepiecemod.shipcombat.ShipCombat.loadedShips()) {
			if (other.level() == level && other.entityTags().contains(TAG) && other.position().distanceToSqr(at) < within * within) {
				count++;
			}
		}
		return count;
	}

	/** Sends a wandering ship across this player's bow. Returns null if it worked, or why not. /voyage ship uses it too. */
	@Nullable
	public static String start(ServerLevel level, ServerPlayer player, ShipEntity near, Kind kind) {
		ShipLayout layout = switch (kind) {
			case MERCHANT -> WanderingDesigns.merchant(level);
			case DERELICT -> WanderingDesigns.derelict(level);
			case GHOST -> WanderingDesigns.ghost(level);
		};
		int reach = Math.max(9, Math.max(layout.max.getX() - layout.min.getX(), layout.max.getZ() - layout.min.getZ()) / 2 + 1);
		BlockPos spot = null;
		for (int attempt = 0; attempt < 4 && spot == null; attempt++) {
			BlockPos found = SeaSpots.openWaterNear(level, near, 70, 30, 120, reach, 5);
			if (found != null && !shipNear(level, Vec3.atCenterOf(found), reach * 2 + 12)) {
				spot = found;
			}
		}
		if (spot == null) {
			return "There's no open sea around for another ship.";
		}
		ShipEntity ship = ShipFeature.SHIP.create(level, EntitySpawnReason.EVENT);
		if (ship == null) {
			return "The ship failed to spawn.";
		}
		ship.setLayout(layout);
		// Crossing the player's path: aimed a little to one side of them, not straight at them.
		float toward = (float) (Mth.atan2(near.getX() - spot.getX(), -(near.getZ() - spot.getZ())) * Mth.RAD_TO_DEG);
		float course = toward + (level.getRandom().nextBoolean() ? 35 : -35);
		ship.snapTo(spot.getX() + 0.5, spot.getY() - layout.waterline, spot.getZ() + 0.5, course, 0);
		RandomSource random = level.getRandom();
		String name = switch (kind) {
			case MERCHANT -> MERCHANT_NAMES[random.nextInt(MERCHANT_NAMES.length)];
			case DERELICT -> "Derelict " + DERELICT_NAMES[random.nextInt(DERELICT_NAMES.length)];
			case GHOST -> GHOST_NAMES[random.nextInt(GHOST_NAMES.length)];
		};
		ship.setCustomName(Component.literal(name));
		ship.addTag(TAG);
		ship.addTag(KIND_TAG + kind.name().toLowerCase());
		ShipHull.setMax(ship, ShipHull.sizeToHull(layout.size()) * (kind == Kind.DERELICT ? 0.6f : 1f));
		level.addFreshEntity(ship);
		COURSE.put(ship.getUUID(), course);

		switch (kind) {
			case MERCHANT -> {
				boardMerchant(level, ship);
				player.sendSystemMessage(Component.literal("A merchant ship, the " + name + ", is crossing your course. Pull alongside and step aboard to trade!")
						.withStyle(ChatFormatting.GREEN));
			}
			case DERELICT -> player.sendSystemMessage(Component.literal("A ship is drifting out there with torn sails and nobody at the wheel... a derelict!")
					.withStyle(ChatFormatting.YELLOW));
			case GHOST -> {
				player.sendSystemMessage(Component.literal("A grey ship glides out of the dark, with no lights and no crew you can see. A ghost ship...")
						.withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
				level.playSound(null, ship.getX(), ship.getY() + 4, ship.getZ(), SoundEvents.AMBIENT_CAVE.value(), SoundSource.AMBIENT, 6.0f, 0.6f);
			}
		}
		return null;
	}

	// ---- Sailing ----

	private static void steer(ServerLevel level, ShipEntity ship, int tick) {
		Kind kind = kindOf(ship);
		UUID id = ship.getUUID();
		if (ship.sinking) {
			if (kind == Kind.MERCHANT && HANDLED.add(id)) {
				merchantSunk(level, ship);
			}
			return;
		}
		// Someone took the wheel: she's theirs now.
		if (ship.getControllingPassenger() instanceof ServerPlayer captain) {
			claim(level, ship, captain, kind);
			return;
		}
		float course = COURSE.computeIfAbsent(id, key -> ship.getYRot());
		float yaw = ship.getYRot();
		int avoid = AVOID.getOrDefault(id, 0);
		int reverse = REVERSE.getOrDefault(id, 0);
		if (tick % 20 == 0 && reverse == 0) {
			// Hardly moved in a second: run aground or bumping another ship. Back off and head for the most open water.
			Vec3 last = LAST_POS.put(id, ship.position());
			if (last != null && last.distanceToSqr(ship.position()) < 0.25) {
				course = openestCourse(level, ship, course);
				COURSE.put(id, course);
				REVERSE.put(id, reverse = 50);
				AVOID.put(id, avoid = 100);
			}
		}
		if (reverse > 0) {
			REVERSE.put(id, reverse - 1);
			float turnBack = Mth.wrapDegrees(course - yaw);
			ship.aiTurn = Mth.clamp(-turnBack / 15f, -1f, 1f); // Back off while swinging toward open water.
			ship.aiForward = -1;
			ship.setHandling(1f, 1f);
			return;
		}
		if (avoid > 0) {
			AVOID.put(id, avoid - 1);
		} else if (!openWater(level, ship, yaw, 14) || !openWater(level, ship, yaw, 22)) {
			// Land ahead: swing round to whichever side is clear, and keep that as the new course.
			course = openWater(level, ship, yaw + 90, 18) ? yaw + 90 : yaw - 90;
			COURSE.put(id, course);
			AVOID.put(id, 60);
		}
		float turn = Mth.wrapDegrees(course - yaw);
		ship.aiTurn = Mth.clamp(-turn / 15f, -1f, 1f);
		ship.aiForward = 1;
		// Merchants plod, derelicts and ghost ships only drift. (Set every tick, after the crew-help pass.)
		float speed = kind == Kind.MERCHANT ? 0.5f : kind == Kind.GHOST ? 0.25f : 0.18f;
		ship.setHandling(speed, 0.6f);

		if (tick % 20 == 0) {
			if (kind == Kind.GHOST) {
				haunt(level, ship);
			}
			if (!SeaSpots.anyPlayerNear(level, ship.position(), DESPAWN_RANGE)) {
				int away = AWAY.merge(id, 1, Integer::sum);
				if (away >= 30) {
					forget(level, ship);
				}
			} else {
				AWAY.remove(id);
			}
		}
	}

	/** Of eight headings, the one with open water furthest out, preferring headings close to `wanted`. */
	private static float openestCourse(ServerLevel level, ShipEntity ship, float wanted) {
		float best = wanted + 180;
		double bestScore = -1;
		for (int i = 0; i < 8; i++) {
			float yaw = wanted + i * 45;
			int clear = 0;
			for (int d = 8; d <= 40 && openWater(level, ship, yaw, d); d += 8) {
				clear++;
			}
			double score = clear * 10 - Math.abs(Mth.wrapDegrees(yaw - wanted)) / 45.0;
			if (score > bestScore) {
				bestScore = score;
				best = yaw;
			}
		}
		return best;
	}

	private static boolean openWater(ServerLevel level, ShipEntity ship, float yaw, double ahead) {
		float radians = yaw * Mth.DEG_TO_RAD;
		double x = ship.getX() - Mth.sin(radians) * ahead;
		double z = ship.getZ() + Mth.cos(radians) * ahead;
		BlockPos surface = BlockPos.containing(x, ship.getY() + ship.getLayout().waterline - 0.5, z);
		if (!level.hasChunkAt(surface)) {
			return false;
		}
		return level.getFluidState(surface).is(FluidTags.WATER) && level.getFluidState(surface.below()).is(FluidTags.WATER)
				&& level.getBlockState(surface.above()).canBeReplaced();
	}

	/** Sails over the horizon: the ship and anyone left of its crew disappear. */
	private static void forget(ServerLevel level, ShipEntity ship) {
		for (Entity onDeck : ShipDecks.onDeck(ship)) {
			if (onDeck.entityTags().contains(TAG) || onDeck.entityTags().contains(CREW_TAG)) {
				onDeck.discard();
			}
		}
		UUID id = ship.getUUID();
		COURSE.remove(id);
		AWAY.remove(id);
		AVOID.remove(id);
		HANDLED.remove(id);
		LAST_POS.remove(id);
		REVERSE.remove(id);
		ship.discard();
	}

	private static void claim(ServerLevel level, ShipEntity ship, ServerPlayer captain, @Nullable Kind kind) {
		ship.removeTag(TAG);
		if (kind != null) {
			ship.removeTag(KIND_TAG + kind.name().toLowerCase());
		}
		ship.aiForward = 0;
		ship.aiTurn = 0;
		UUID id = ship.getUUID();
		COURSE.remove(id);
		AWAY.remove(id);
		AVOID.remove(id);
		if (kind == Kind.MERCHANT) {
			captain.sendSystemMessage(Component.literal("You took the merchant's wheel. That's piracy, and the Marines will hear of it!")
					.withStyle(ChatFormatting.RED));
			Bounty.raise(captain, PIRACY_BOUNTY, "You stole a merchant ship!", false);
			for (Entity onDeck : ShipDecks.onDeck(ship)) {
				if (onDeck instanceof WanderingTrader trader && trader.entityTags().contains(TAG)) {
					level.sendParticles(ParticleTypes.SPLASH, trader.getX(), trader.getY(), trader.getZ(), 20, 0.3, 0.3, 0.3, 0.2);
					trader.discard(); // Jumps overboard and swims for it.
				}
			}
		} else {
			captain.sendSystemMessage(Component.literal((kind == Kind.GHOST ? "The ghost ship" : "The derelict")
					+ " answers to your wheel. She's yours now! Drop anchor (right-click the deck twice) to keep her.")
					.withStyle(ChatFormatting.GOLD));
			com.onepiecemod.advancement.AdvancementFeature.grant(captain, "journey/claim_derelict");
		}
	}

	// ---- Merchant ships ----

	private static final String[] MERCHANT_NAMES = {
			"Golden Gull", "Sea Lily", "Fat Purse", "Spice Wind", "Lucky Tuna", "Blue Barrel", "Cloud Trader", "Honest Kelp"};
	private static final String[] DERELICT_NAMES = {"Sloop", "Sea Dog", "Rusty Hook", "Lost Lamb", "Broken Mast"};
	private static final String[] GHOST_NAMES = {"Silent Bride", "Grey Lantern", "Rumbar's Shadow", "Drowned Hope", "The Weeping Gull"};

	/** The Sea Merchant stands at the bow, selling goods from far-off seas for Berries. */
	private static void boardMerchant(ServerLevel level, ShipEntity ship) {
		WanderingTrader trader = EntityTypes.WANDERING_TRADER.create(level, EntitySpawnReason.EVENT);
		if (trader == null) {
			return;
		}
		List<Vec3> deck = ship.seatPositions();
		Vec3 spot = deck.size() > 3 ? deck.get(deck.size() - 1) : ship.position().add(0, ship.getLayout().waterline + 1, 0);
		trader.snapTo(spot.x, spot.y, spot.z, ship.getYRot(), 0);
		trader.setNoAi(true); // Stays put on the deck (the deck carries it along).
		trader.setDespawnDelay(Integer.MAX_VALUE / 2);
		trader.setPersistenceRequired();
		trader.setCustomName(Component.literal("Sea Merchant"));
		trader.addTag(TAG);
		MerchantOffers offers = trader.getOffers();
		offers.clear();
		List<TownData.Trade> imports = new java.util.ArrayList<>(TownData.imports());
		RandomSource random = level.getRandom();
		for (int i = 0; i < 6 && !imports.isEmpty(); i++) {
			MerchantOffer offer = imports.remove(random.nextInt(imports.size())).toOffer();
			if (offer != null) {
				offers.add(offer);
			}
		}
		level.addFreshEntity(trader);
	}

	/** Someone sank a merchant ship: the cargo floats up, and the nearest ship's crew gets a bounty for piracy. */
	private static void merchantSunk(ServerLevel level, ShipEntity ship) {
		RandomSource random = level.getRandom();
		Vec3 at = ship.position().add(0, ship.getLayout().waterline + 1, 0);
		SeaMonsters.drop(level, at, new ItemStack(CharacterFeature.BERRY, 30 + random.nextInt(40)));
		SeaMonsters.drop(level, at, new ItemStack(Items.EMERALD, 2 + random.nextInt(4)));
		SeaMonsters.drop(level, at, new ItemStack(Items.GOLD_INGOT, 2 + random.nextInt(4)));
		SeaMonsters.drop(level, at, new ItemStack(Items.SUGAR, 4 + random.nextInt(8)));
		for (Entity onDeck : ShipDecks.onDeck(ship)) {
			if (onDeck instanceof WanderingTrader trader && trader.entityTags().contains(TAG)) {
				trader.discard();
			}
		}
		ServerPlayer pirate = null;
		double best = 120 * 120;
		for (ServerPlayer player : level.players()) {
			double d = player.distanceToSqr(ship);
			if (!player.isSpectator() && d < best && ShipEntity.aboard(player) != ship) {
				best = d;
				pirate = player;
			}
		}
		if (pirate != null) {
			Bounty.raise(pirate, PIRACY_BOUNTY, "You sank a merchant ship!", false);
		}
	}

	// ---- Ghost ships ----

	private static void haunt(ServerLevel level, ShipEntity ship) {
		RandomSource random = level.getRandom();
		double w = ship.getBbWidth() * 0.35;
		level.sendParticles(ParticleTypes.SOUL, ship.getX(), ship.getY() + ship.getLayout().waterline + 2, ship.getZ(), 6, w, 1.5, w, 0.01);
		level.sendParticles(ParticleTypes.SOUL_FIRE_FLAME, ship.getX(), ship.getY() + ship.getLayout().waterline + 1, ship.getZ(), 3, w, 0.5, w, 0.0);
		UUID id = ship.getUUID();
		if (HANDLED.contains(id)) {
			return;
		}
		List<ServerPlayer> aboard = new java.util.ArrayList<>(ShipEntity.playersAboard(ship));
		aboard.removeIf(p -> p.isCreative() || p.isSpectator());
		if (aboard.isEmpty()) {
			return;
		}
		HANDLED.add(id);
		// The dead crew climbs up out of the deck.
		List<Vec3> deck = ship.seatPositions();
		int count = level.getDifficulty() == net.minecraft.world.Difficulty.PEACEFUL ? 0 : 3 + random.nextInt(3);
		for (int i = 0; i < count && deck.size() > 1; i++) {
			Vec3 spot = deck.get(1 + random.nextInt(deck.size() - 1));
			Skeleton skeleton = EntityTypes.SKELETON.create(level, EntitySpawnReason.EVENT);
			if (skeleton == null) {
				continue;
			}
			skeleton.snapTo(spot.x, spot.y, spot.z, random.nextFloat() * 360, 0);
			skeleton.setItemSlot(EquipmentSlot.MAINHAND, new ItemStack(random.nextBoolean() ? Items.IRON_SWORD : Items.BOW));
			skeleton.setItemSlot(EquipmentSlot.HEAD, new ItemStack(Items.LEATHER_HELMET)); // A sailor's cap (and shade from the sun).
			skeleton.setDropChance(EquipmentSlot.HEAD, 0f);
			skeleton.addTag(CREW_TAG);
			level.addFreshEntity(skeleton);
			level.sendParticles(ParticleTypes.SOUL, spot.x, spot.y + 1, spot.z, 15, 0.3, 0.6, 0.3, 0.02);
		}
		for (ServerPlayer player : aboard) {
			player.sendSystemMessage(Component.literal(count > 0 ? "The deck creaks... and the ship's dead crew rises to defend her!"
					: "The deck creaks. Something is watching you... but nothing comes.").withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
			com.onepiecemod.advancement.AdvancementFeature.grant(player, "journey/ghost_ship");
		}
		level.playSound(null, ship.getX(), ship.getY() + 3, ship.getZ(), SoundEvents.SKELETON_AMBIENT, SoundSource.HOSTILE, 3.0f, 0.5f);
	}
}
