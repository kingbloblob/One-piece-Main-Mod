package com.onepiecemod.weather;

import com.onepiecemod.util.Motion;
import java.util.List;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.ItemTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LightningBolt;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.zombie.Drowned;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.power.ModAttachments;
import com.onepiecemod.resource.Resources;
import com.onepiecemod.sea.SeaEntities;
import com.onepiecemod.sea.SeaKingEntity;
import com.onepiecemod.sea.SeaKingSpawner;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.weapon.ClimaTactItem;

/**
 * What each event does to players, mobs and the sea while it runs: the particles, sounds, lightning,
 * pulling, freezing and treasure. Ships are pushed in SeaForces instead.
 */
public class SeaEventEffects {
	private static final String LOST_SOUL_TAG = "onepiece_lost_soul";

	// ---- Called by SeaEvents ----

	static void begin(ServerLevel level, SeaEvent event) {
		if (event.type == SeaEventType.CALM_BELT_AMBUSH) {
			surfaceSeaKings(level, event);
		}
	}

	static void warningTick(ServerLevel level, SeaEvent event, long time) {
		// Whirlpools and Aqua Laguna's wave are drawn on each player's own game (WeatherVisuals), so they can show lots of particles.
	}

	static void tick(ServerLevel level, SeaEvent event, long time) {
		List<ServerPlayer> inside = level.players().stream()
				.filter(player -> !player.isSpectator() && event.isInside(player.getX(), player.getZ())).toList();
		switch (event.type) {
			case STORM -> storm(level, event, time, inside);
			case WHIRLPOOL -> whirlpool(level, event, time);
			case AQUA_LAGUNA -> aquaLaguna(level, event, time);
			case CALM_BELT_AMBUSH -> ambush(level, event, time);
			case BLIZZARD -> blizzard(level, time, inside);
			case HEAT_WAVE -> heatWave(level, time, inside);
			case FLORIAN_MIST -> florianMist(level, event, time, inside);
			case WATERSPOUT -> waterspout(level, event, time);
			case ROGUE_WAVE -> rogueWave(level, event, time);
			case HAILSTORM -> hailstorm(level, time, inside);
		}
	}

	static void finish(ServerLevel level, SeaEvent event) {
		switch (event.type) {
			case WHIRLPOOL -> {
				// The whirlpool spits out things it swallowed long ago.
				int count = 3 + level.getRandom().nextInt(4);
				for (int i = 0; i < count; i++) {
					dropTreasure(level, new Vec3(event.x, level.getSeaLevel() + 0.5, event.z), 0.4);
				}
				level.sendParticles(ParticleTypes.SPLASH, event.x, level.getSeaLevel() + 0.5, event.z, 80, 2, 0.5, 2, 0.3);
			}
			case AQUA_LAGUNA -> {
				// Treasure washed up on the beach.
				RandomSource random = level.getRandom();
				int count = 5 + random.nextInt(5);
				for (int i = 0; i < count; i++) {
					int x = Mth.floor(event.x + (random.nextDouble() - 0.5) * 30);
					int z = Mth.floor(event.z + (random.nextDouble() - 0.5) * 30);
					int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING, x, z);
					if (y >= level.getSeaLevel()) {
						dropTreasure(level, new Vec3(x + 0.5, y + 0.5, z + 0.5), 0.1);
					}
				}
			}
			case FLORIAN_MIST -> {
				// The lost souls fade away with the mist.
				AABB area = new AABB(event.x - event.radius - 40, level.getMinY(), event.z - event.radius - 40,
						event.x + event.radius + 40, level.getMaxY(), event.z + event.radius + 40);
				for (Drowned soul : level.getEntitiesOfClass(Drowned.class, area, drowned -> drowned.entityTags().contains(LOST_SOUL_TAG))) {
					level.sendParticles(ParticleTypes.SOUL, soul.getX(), soul.getY() + 1, soul.getZ(), 15, 0.3, 0.6, 0.3, 0.02);
					soul.discard();
				}
			}
			default -> {
			}
		}
	}

	// ---- Grand Line Storm ----

	private static void storm(ServerLevel level, SeaEvent event, long time, List<ServerPlayer> inside) {
		RandomSource random = level.getRandom();
		Vec3 wind = event.direction();
		double gust = event.gust(time);

		for (ServerPlayer player : inside) {
			// Rough seas: spray flying past in the wind.
			if (time % 4 == 0) {
				level.sendParticles(ParticleTypes.SPLASH, player.getX() - wind.x * 6, level.getSeaLevel() + 1, player.getZ() - wind.z * 6,
						25, 8, 0.5, 8, 0.4);
			}
			// Swimmers are tossed by the wind and dragged under by the waves.
			if (time % 5 == 0 && player.isInWater() && !player.isPassenger()) {
				shove(player, wind.scale(0.18 * gust).add(0, -0.06, 0));
			}
		}

		// Lightning, about every 3 seconds, near a player.
		if (!inside.isEmpty() && time % 60 == 0) {
			ServerPlayer near = inside.get(random.nextInt(inside.size()));
			Vec3 strike;
			if (near.getVehicle() instanceof ShipEntity ship && random.nextFloat() < 0.3f) {
				// Ships are the tallest thing at sea, so lightning loves them.
				List<Entity> crew = ship.getPassengers();
				strike = crew.get(random.nextInt(crew.size())).position();
			} else {
				double angle = random.nextDouble() * Mth.TWO_PI;
				double distance = 6 + random.nextDouble() * 24;
				strike = new Vec3(near.getX() + Math.cos(angle) * distance, 0, near.getZ() + Math.sin(angle) * distance);
				strike = new Vec3(strike.x, level.getHeight(Heightmap.Types.MOTION_BLOCKING, Mth.floor(strike.x), Mth.floor(strike.z)), strike.z);
			}
			ServerPlayer target = nearestPlayer(inside, strike, 4);
			if (target != null && target.getMainHandItem().getItem() instanceof ClimaTactItem) {
				// Nami's trick: a Clima-Tact draws the lightning away from you.
				target.sendOverlayMessage(Component.literal("Your Clima-Tact pulls the lightning away!").withStyle(ChatFormatting.YELLOW));
				strike = strike.add(8, 0, 8);
			}
			LightningBolt bolt = new LightningBolt(EntityTypes.LIGHTNING_BOLT, level);
			bolt.setPos(strike);
			level.addFreshEntity(bolt);
		}
	}

	// ---- Whirlpool ----

	private static void whirlpool(ServerLevel level, SeaEvent event, long time) {
		double surface = level.getSeaLevel();

		if (time % 100 == 0) {
			level.playSound(null, event.x, surface, event.z, com.onepiecemod.sound.WorldSounds.WHIRLPOOL, SoundSource.AMBIENT, 4.0f, 1.0f);
		}

		// Pull in everything floating or swimming: players, mobs, boats, dropped items.
		if (time % 2 == 0) {
			AABB area = new AABB(event.x - event.radius, surface - 12, event.z - event.radius,
					event.x + event.radius, surface + 3, event.z + event.radius);
			for (Entity entity : level.getEntitiesOfClass(Entity.class, area,
					e -> e.isInWater() && !(e instanceof ShipEntity) && !e.isPassenger() && !e.isSpectator())) {
				Vec3 pull = SeaForces.push(event, entity.getX(), entity.getZ(), time).scale(1.5);
				if (event.distance(entity.getX(), entity.getZ()) < 5) {
					pull = pull.add(0, -0.1, 0); // The eye of the whirlpool drags you down.
				}
				shove(entity, pull);
			}
		}

		// The crew of a ship caught in the eye gets dizzy.
		if (time % 40 == 0) {
			for (ShipEntity ship : level.getEntitiesOfClass(ShipEntity.class, new AABB(event.x - 6, surface - 10, event.z - 6, event.x + 6, surface + 10, event.z + 6))) {
				for (Entity rider : ship.getPassengers()) {
					if (rider instanceof ServerPlayer player) {
						player.addEffect(new MobEffectInstance(MobEffects.NAUSEA, 100, 0));
						if (ship.getControllingPassenger() == player) {
							player.sendOverlayMessage(Component.literal("We're in the eye! Hold W to sail out!").withStyle(ChatFormatting.DARK_AQUA));
						}
					}
				}
			}
		}
	}

	// ---- Aqua Laguna ----

	private static void aquaLaguna(ServerLevel level, SeaEvent event, long time) {
		Vec3 dir = event.direction();
		Vec3 side = new Vec3(-dir.z, 0, dir.x);
		double front = event.waveFront(time);
		double sea = level.getSeaLevel();
		Vec3 middle = new Vec3(event.x, sea, event.z).add(dir.scale(front));

		if (time % 60 == 0) {
			level.playSound(null, middle.x, middle.y + 4, middle.z, com.onepiecemod.sound.WorldSounds.WAVE_CRASH, SoundSource.WEATHER, 6.0f, 0.9f);
		}

		// Anything low down that the wave reaches gets slammed, once. High ground or a roof keeps you safe.
		AABB reach = new AABB(event.x - event.radius * 2, sea - 4, event.z - event.radius * 2,
				event.x + event.radius * 2, sea + 9, event.z + event.radius * 2);
		for (LivingEntity entity : level.getEntitiesOfClass(LivingEntity.class, reach, e -> !e.isSpectator() && !(e instanceof SeaKingEntity))) {
			double along = (entity.getX() - event.x) * dir.x + (entity.getZ() - event.z) * dir.z;
			double across = Math.abs((entity.getX() - event.x) * side.x + (entity.getZ() - event.z) * side.z);
			if (across > event.radius || along > front || along < front - 3) {
				continue;
			}
			if (!level.canSeeSky(entity.blockPosition().above()) || entity instanceof Player p && p.isCreative()) {
				continue;
			}
			if (event.hitByWave.add(entity.getUUID())) {
				entity.hurtServer(level, level.damageSources().drown(), 5.0f);
				shove(entity, dir.scale(1.6).add(0, 0.6, 0));
				if (entity instanceof ServerPlayer player) {
					player.sendSystemMessage(Component.literal("The great wave slams into you!").withStyle(ChatFormatting.BLUE));
				}
			}
		}
	}

	// ---- Waterspout ----

	/** A ship's hull can't be pushed below this share of its maximum by the weather alone: storms batter, they don't sink. */
	private static final float WEATHER_HULL_FLOOR = 0.25f;

	private static void waterspout(ServerLevel level, SeaEvent event, long time) {
		Vec3 spout = event.spout(time);
		double sea = level.getSeaLevel();
		RandomSource random = level.getRandom();

		if (time % 5 == 0) {
			level.sendParticles(ParticleTypes.SPLASH, spout.x, sea + 1, spout.z, 40, 3, 0.6, 3, 0.4);
		}
		if (time % 80 == 0) {
			level.playSound(null, spout.x, sea + 4, spout.z, com.onepiecemod.sound.WorldSounds.WHIRLPOOL, SoundSource.WEATHER, 5.0f, 1.4f);
		}

		// Anything loose in or on the water near the funnel is sucked up and flung.
		double r = SeaEvent.SPOUT_RADIUS;
		AABB area = new AABB(spout.x - r, sea - 3, spout.z - r, spout.x + r, sea + 30, spout.z + r);
		if (time % 3 == 0) {
			for (Entity entity : level.getEntitiesOfClass(Entity.class, area,
					e -> !(e instanceof ShipEntity) && !e.isPassenger() && !e.isSpectator() && !(e instanceof SeaKingEntity)
							&& !(e instanceof Player p && (p.isCreative() || p.getAbilities().flying)))) {
				double dx = spout.x - entity.getX();
				double dz = spout.z - entity.getZ();
				double distance = Math.sqrt(dx * dx + dz * dz);
				if (distance > r) {
					continue;
				}
				Vec3 inward = distance < 0.1 ? Vec3.ZERO : new Vec3(dx / distance, 0, dz / distance);
				Vec3 around = new Vec3(-inward.z, 0, inward.x);
				double lift = entity.getY() < sea + 18 ? 0.32 : 0.05;
				shove(entity, inward.scale(0.08).add(around.scale(0.35)).add(0, lift, 0));
				entity.fallDistance = 0;
				if (entity instanceof ServerPlayer player && time % 60 == 0) {
					player.sendOverlayMessage(Component.literal("You're caught in the waterspout!").withStyle(ChatFormatting.DARK_AQUA));
				}
			}
		}

		// Ships in the funnel are battered, and anyone standing on deck can be swept overboard.
		if (time % 20 == 0) {
			for (ShipEntity ship : level.getEntitiesOfClass(ShipEntity.class, area.inflate(10, 0, 10))) {
				double reach = r + ship.getBbWidth() * 0.3;
				if (Math.hypot(ship.getX() - spout.x, ship.getZ() - spout.z) > reach || ship.sinking) {
					continue;
				}
				strainHull(level, ship, 0.05f, new Vec3(spout.x, ship.getY() + 2, spout.z));
				for (Entity onDeck : com.onepiecemod.ship.ShipDecks.onDeck(ship)) {
					if (onDeck instanceof ServerPlayer player && !player.isCreative() && random.nextFloat() < 0.25f) {
						shove(player, new Vec3(random.nextDouble() - 0.5, 1.1, random.nextDouble() - 0.5));
						player.sendSystemMessage(Component.literal("The waterspout tears you off the deck!").withStyle(ChatFormatting.DARK_AQUA));
					}
				}
				for (Entity rider : ship.getPassengers()) {
					if (rider instanceof ServerPlayer player) {
						player.sendOverlayMessage(Component.literal("The waterspout is tearing at the hull! Sail out of it!").withStyle(ChatFormatting.RED));
					}
				}
			}
		}

		// The Grand Line's famous weirdness: it rains fish.
		if (time % 30 == 0) {
			for (ServerPlayer player : level.players()) {
				if (event.isInside(player.getX(), player.getZ()) && random.nextFloat() < 0.5f) {
					Item fish = random.nextInt(4) == 0 ? Items.SALMON : random.nextInt(8) == 0 ? Items.PUFFERFISH : Items.COD;
					ItemEntity drop = new ItemEntity(level, player.getX() + (random.nextDouble() - 0.5) * 12, player.getY() + 14,
							player.getZ() + (random.nextDouble() - 0.5) * 12, new ItemStack(fish));
					level.addFreshEntity(drop);
				}
			}
		}
	}

	/**
	 * Weather damage to a ship's hull: the hull points drop (so enemy cannons finish the job faster), but no blocks
	 * break off and the weather alone never sinks a ship. Docking repairs it, as always.
	 */
	public static void strainHull(ServerLevel level, ShipEntity ship, float share, Vec3 at) {
		float max = com.onepiecemod.shipcombat.ShipHull.max(ship);
		float hull = com.onepiecemod.shipcombat.ShipHull.get(ship);
		float floor = max * WEATHER_HULL_FLOOR;
		if (hull <= floor) {
			return;
		}
		ship.setAttached(com.onepiecemod.shipcombat.ShipHull.HULL, Math.max(floor, hull - max * share));
		level.playSound(null, BlockPos.containing(at), com.onepiecemod.sound.WorldSounds.SHIP_HULL_HIT, SoundSource.NEUTRAL, 2.0f, 0.8f);
		level.sendParticles(ParticleTypes.SPLASH, at.x, at.y, at.z, 30, 1.5, 1, 1.5, 0.3);
	}

	// ---- Rogue wave ----

	private static void rogueWave(ServerLevel level, SeaEvent event, long time) {
		Vec3 dir = event.direction();
		Vec3 side = new Vec3(-dir.z, 0, dir.x);
		double front = event.waveFront(time);
		double sea = level.getSeaLevel();
		Vec3 middle = new Vec3(event.x, sea, event.z).add(dir.scale(front));
		if (time % 50 == 0) {
			level.playSound(null, middle.x, middle.y + 4, middle.z, com.onepiecemod.sound.WorldSounds.WAVE_CRASH, SoundSource.WEATHER, 5.0f, 1.0f);
		}

		// Ships: bow into the wave and she rides over it. Side-on, the wave smashes into the hull and the deck tips.
		for (ShipEntity ship : level.getEntitiesOfClass(ShipEntity.class, new AABB(event.x - event.radius * 2, sea - 12, event.z - event.radius * 2,
				event.x + event.radius * 2, sea + 12, event.z + event.radius * 2))) {
			double along = (ship.getX() - event.x) * dir.x + (ship.getZ() - event.z) * dir.z;
			double across = Math.abs((ship.getX() - event.x) * side.x + (ship.getZ() - event.z) * side.z);
			if (ship.sinking || across > event.radius || along > front || along < front - 4 || !event.hitByWave.add(ship.getUUID())) {
				continue;
			}
			float yaw = ship.getYRot() * Mth.DEG_TO_RAD;
			Vec3 heading = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
			// 1 = the wave hits square on the side, 0 = straight on the bow or the stern.
			double broadside = Math.abs(heading.x * side.x + heading.z * side.z);
			broadside = Math.sqrt(Math.max(0, 1 - broadside * broadside));
			ServerPlayer captain = ship.getControllingPassenger() instanceof ServerPlayer p ? p : null;
			if (broadside > 0.6) {
				strainHull(level, ship, 0.22f, ship.position().add(0, 2, 0));
				for (Entity onDeck : com.onepiecemod.ship.ShipDecks.onDeck(ship)) {
					if (onDeck instanceof LivingEntity living && !(onDeck instanceof Player p && p.isCreative())) {
						shove(living, dir.scale(1.2).add(0, 0.7, 0));
					}
				}
				if (captain != null) {
					captain.sendSystemMessage(Component.literal("The rogue wave slams into your side! Next time, turn into it!")
							.withStyle(ChatFormatting.RED));
				}
			} else if (captain != null) {
				captain.sendSystemMessage(Component.literal("You took the rogue wave on the bow and rode right over it. Nice sailing!")
						.withStyle(ChatFormatting.AQUA));
				com.onepiecemod.advancement.AdvancementFeature.grant(captain, "journey/ride_the_wave");
			}
		}

		// Swimmers are thrown along with it.
		AABB reach = new AABB(event.x - event.radius * 2, sea - 4, event.z - event.radius * 2,
				event.x + event.radius * 2, sea + 4, event.z + event.radius * 2);
		for (LivingEntity entity : level.getEntitiesOfClass(LivingEntity.class, reach,
				e -> e.isInWater() && !e.isPassenger() && !e.isSpectator() && !(e instanceof SeaKingEntity))) {
			double along = (entity.getX() - event.x) * dir.x + (entity.getZ() - event.z) * dir.z;
			double across = Math.abs((entity.getX() - event.x) * side.x + (entity.getZ() - event.z) * side.z);
			if (across <= event.radius && along <= front && along >= front - 3 && event.hitByWave.add(entity.getUUID())) {
				entity.hurtServer(level, level.damageSources().drown(), 3.0f);
				shove(entity, dir.scale(1.4).add(0, 0.5, 0));
			}
		}
	}

	// ---- Hailstorm ----

	private static void hailstorm(ServerLevel level, long time, List<ServerPlayer> inside) {
		RandomSource random = level.getRandom();
		for (ServerPlayer player : inside) {
			if (time % 3 == 0) {
				level.sendParticles(new net.minecraft.core.particles.ItemParticleOption(ParticleTypes.ITEM, Items.SNOWBALL), player.getX(), player.getY() + 8, player.getZ(), 30, 9, 2, 9, 0.0);
			}
			if (time % 40 != 0 || player.isCreative() || !level.canSeeSky(player.blockPosition().above())) {
				continue;
			}
			if (hasFruit(player, "hie_hie_no_mi", "yuki_yuki_no_mi", "mera_mera_no_mi", "magu_magu_no_mi")) {
				continue; // Ice users don't mind, fire users melt it before it lands.
			}
			ItemStack helmet = player.getItemBySlot(EquipmentSlot.HEAD);
			if (!helmet.isEmpty()) {
				if (random.nextInt(3) == 0) {
					helmet.hurtAndBreak(1, player, EquipmentSlot.HEAD);
					level.playSound(null, player.blockPosition(), SoundEvents.GLASS_HIT, SoundSource.WEATHER, 0.8f, 1.6f);
				}
				continue;
			}
			player.hurtServer(level, level.damageSources().generic(), 1.5f);
			player.sendOverlayMessage(Component.literal("Ouch! Hail! Get under a roof or wear a helmet!").withStyle(ChatFormatting.WHITE));
		}
	}

	// ---- Calm Belt Sea King ambush ----

	private static void surfaceSeaKings(ServerLevel level, SeaEvent event) {
		if (level.getDifficulty() == Difficulty.PEACEFUL) {
			return;
		}
		RandomSource random = level.getRandom();
		int wanted = 2 + random.nextInt(2);
		int spawned = 0;
		for (int attempt = 0; attempt < 16 && spawned < wanted; attempt++) {
			double angle = random.nextDouble() * Mth.TWO_PI;
			double distance = 10 + random.nextDouble() * 10;
			BlockPos spot = BlockPos.containing(event.x + Math.cos(angle) * distance, level.getSeaLevel() - 5, event.z + Math.sin(angle) * distance);
			if (!SeaKingSpawner.isDeepWater(level, spot)) {
				continue;
			}
			SeaKingEntity seaKing = SeaEntities.SEA_KING.create(level, EntitySpawnReason.EVENT);
			if (seaKing != null) {
				seaKing.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
				seaKing.setYRot(random.nextFloat() * 360);
				level.addFreshEntity(seaKing);
				geyser(level, spot.getX() + 0.5, spot.getZ() + 0.5);
				spawned++;
			}
		}
		level.playSound(null, event.x, level.getSeaLevel(), event.z, com.onepiecemod.sound.WorldSounds.SEA_KING_AMBIENT, SoundSource.HOSTILE, 4.0f, 0.8f);
	}

	private static void ambush(ServerLevel level, SeaEvent event, long time) {
		// Water bursting up as the Sea Kings circle.
		if (time % 25 == 0) {
			RandomSource random = level.getRandom();
			double angle = random.nextDouble() * Mth.TWO_PI;
			double distance = 6 + random.nextDouble() * 14;
			geyser(level, event.x + Math.cos(angle) * distance, event.z + Math.sin(angle) * distance);
		}
	}

	private static void geyser(ServerLevel level, double x, double z) {
		double y = level.getSeaLevel();
		level.sendParticles(ParticleTypes.SPLASH, x, y + 1, z, 60, 1.2, 2.5, 1.2, 0.3);
		level.sendParticles(ParticleTypes.BUBBLE_COLUMN_UP, x, y - 2, z, 20, 1, 1, 1, 0.1);
		level.playSound(null, x, y, z, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 3.0f, 0.6f);
	}

	// ---- Sudden Blizzard ----

	private static void blizzard(ServerLevel level, long time, List<ServerPlayer> inside) {
		for (ServerPlayer player : inside) {
			if (time % 4 == 0) {
				level.sendParticles(ParticleTypes.SNOWFLAKE, player.getX(), player.getY() + 6, player.getZ(), 40, 10, 3, 10, 0.05);
			}
			if (time % 10 != 0) {
				continue;
			}
			if (player.isCreative() || hasFruit(player, "hie_hie_no_mi", "mera_mera_no_mi", "magu_magu_no_mi") || isWarm(level, player)) {
				continue;
			}
			int frozen = player.getTicksFrozen();
			if (frozen == 0) {
				player.sendOverlayMessage(Component.literal("You're freezing! Find a fire or put on leather armor!").withStyle(ChatFormatting.AQUA));
			}
			// Like standing in powder snow. Once you're fully frozen, it starts to hurt.
			player.setTicksFrozen(Math.min(player.getTicksRequiredToFreeze() + 20, frozen + 25));
		}
	}

	/** Leather armor, or a fire, campfire, lava or magma block close by, keeps you warm. */
	public static boolean isWarm(ServerLevel level, ServerPlayer player) {
		for (EquipmentSlot slot : new EquipmentSlot[] {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET}) {
			if (player.getItemBySlot(slot).is(ItemTags.FREEZE_IMMUNE_WEARABLES)) {
				return true;
			}
		}
		BlockPos center = player.blockPosition();
		for (BlockPos pos : BlockPos.betweenClosed(center.offset(-4, -2, -4), center.offset(4, 2, 4))) {
			BlockState state = level.getBlockState(pos);
			if (state.is(Blocks.CAMPFIRE) || state.is(Blocks.SOUL_CAMPFIRE) || state.is(Blocks.FIRE) || state.is(Blocks.SOUL_FIRE)
					|| state.is(Blocks.LAVA) || state.is(Blocks.MAGMA_BLOCK)) {
				return true;
			}
		}
		return false;
	}

	// ---- Scorching Heat Wave ----

	private static void heatWave(ServerLevel level, long time, List<ServerPlayer> inside) {
		for (ServerPlayer player : inside) {
			if (time % 6 == 0) {
				level.sendParticles(ParticleTypes.WHITE_ASH, player.getX(), player.getY() + 1, player.getZ(), 15, 6, 2, 6, 0.01);
			}
			if (time % 10 != 0 || player.isCreative() || player.isInWater() || !level.canSeeSky(player.blockPosition().above())) {
				continue;
			}
			if (hasFruit(player, "mera_mera_no_mi", "magu_magu_no_mi")) {
				continue; // Fire users love this weather.
			}
			// About one hunger point every 17 seconds out in the sun. Ice users melt twice as fast.
			player.causeFoodExhaustion(hasFruit(player, "hie_hie_no_mi") ? 0.24f : 0.12f);
		}
	}

	// ---- Florian Triangle Mist ----

	private static void florianMist(ServerLevel level, SeaEvent event, long time, List<ServerPlayer> inside) {
		RandomSource random = level.getRandom();
		for (ServerPlayer player : inside) {
			if (time % 3 == 0) {
				level.sendParticles(ParticleTypes.CLOUD, player.getX(), player.getY() + 1, player.getZ(), 12, 9, 2, 9, 0.005);
			}
			if (time % 200 == 0 && random.nextFloat() < 0.5f) {
				String[] whispers = {
						"You hear a violin playing somewhere in the mist... Yohohoho!",
						"A huge, rotting ship drifts past in the mist, then it's gone.",
						"Something cold brushes past your shoulder.",
						"Laughter echoes across the water. There's nobody there."};
				player.sendSystemMessage(Component.literal(whispers[random.nextInt(whispers.length)]).withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC));
				level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.AMBIENT_CAVE.value(), SoundSource.AMBIENT, 1.0f, 0.8f);
			}
		}

		// Lost souls rise out of the water. They carry a little treasure.
		if (time % 100 == 0 && !inside.isEmpty() && level.getDifficulty() != Difficulty.PEACEFUL) {
			AABB area = new AABB(event.x - event.radius, level.getMinY(), event.z - event.radius, event.x + event.radius, level.getMaxY(), event.z + event.radius);
			int souls = level.getEntitiesOfClass(Drowned.class, area, drowned -> drowned.entityTags().contains(LOST_SOUL_TAG)).size();
			if (souls < 5) {
				ServerPlayer near = inside.get(random.nextInt(inside.size()));
				BlockPos spot = SeaKingSpawner.findDeepWater(level, near, random);
				if (spot != null) {
					Drowned soul = EntityTypes.DROWNED.create(level, EntitySpawnReason.EVENT);
					if (soul != null) {
						soul.setPos(spot.getX() + 0.5, level.getSeaLevel() - 1, spot.getZ() + 0.5);
						soul.setCustomName(Component.literal("Lost Soul").withStyle(ChatFormatting.GRAY));
						soul.addTag(LOST_SOUL_TAG);
						soul.setItemSlot(EquipmentSlot.OFFHAND, new ItemStack(random.nextFloat() < 0.3f ? Items.GOLD_INGOT : Items.GOLD_NUGGET, 1 + random.nextInt(3)));
						soul.setDropChance(EquipmentSlot.OFFHAND, 1.0f);
						level.addFreshEntity(soul);
						level.sendParticles(ParticleTypes.SOUL, soul.getX(), soul.getY() + 1, soul.getZ(), 15, 0.3, 0.6, 0.3, 0.02);
					}
				}
			}
		}
	}

	// ---- Helpers ----

	/** Gives something a push (Motion.sync makes sure a player's own game sees it). */
	private static void shove(Entity entity, Vec3 push) {
		entity.setDeltaMovement(entity.getDeltaMovement().add(push));
		Motion.sync(entity);
	}

	public static boolean hasFruit(Player player, String... fruits) {
		String eaten = player.getAttachedOrElse(ModAttachments.DEVIL_FRUIT, "");
		for (String fruit : fruits) {
			if (fruit.equals(eaten)) {
				return true;
			}
		}
		return false;
	}

	private static ServerPlayer nearestPlayer(List<ServerPlayer> players, Vec3 at, double within) {
		ServerPlayer best = null;
		double bestDistance = within * within;
		for (ServerPlayer player : players) {
			double distance = player.position().distanceToSqr(at.x, player.getY(), at.z);
			if (distance <= bestDistance) {
				best = player;
				bestDistance = distance;
			}
		}
		return best;
	}

	/** Sea treasure: mostly small things, sometimes something great. */
	private static void dropTreasure(ServerLevel level, Vec3 at, double toss) {
		RandomSource random = level.getRandom();
		int roll = random.nextInt(100);
		Item item;
		int count;
		if (roll < 18) { item = Items.KELP; count = 3 + random.nextInt(5); }
		else if (roll < 30) { item = Items.BONE; count = 1 + random.nextInt(3); }
		else if (roll < 48) { item = Items.GOLD_NUGGET; count = 3 + random.nextInt(7); }
		else if (roll < 60) { item = Items.IRON_INGOT; count = 1 + random.nextInt(3); }
		else if (roll < 70) { item = Items.PRISMARINE_SHARD; count = 2 + random.nextInt(4); }
		else if (roll < 78) { item = Items.NAUTILUS_SHELL; count = 1; }
		else if (roll < 87) { item = Resources.SEA_PEARL; count = 1 + random.nextInt(2); }
		else if (roll < 94) { item = Items.EMERALD; count = 1 + random.nextInt(2); }
		else if (roll < 99) { item = Items.DIAMOND; count = 1; }
		else { item = Items.HEART_OF_THE_SEA; count = 1; }
		ItemEntity drop = new ItemEntity(level, at.x, at.y, at.z, new ItemStack(item, count));
		drop.setDeltaMovement((random.nextDouble() - 0.5) * toss, 0.3 + random.nextDouble() * toss, (random.nextDouble() - 0.5) * toss);
		level.addFreshEntity(drop);
	}
}
