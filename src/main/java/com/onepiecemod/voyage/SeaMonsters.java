package com.onepiecemod.voyage;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
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
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.creature.CreatureEntity;
import com.onepiecemod.creature.Creatures;
import com.onepiecemod.resource.Resources;
import com.onepiecemod.sea.CalmBelt;
import com.onepiecemod.sea.SeaEntities;
import com.onepiecemod.sea.SeaKingEntity;
import com.onepiecemod.sea.SeaKingSpawner;
import com.onepiecemod.ship.ShipDecks;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.shipcombat.ShipHull;
import com.onepiecemod.treasure.TreasureFeature;
import com.onepiecemod.weather.SeaEventEffects;
import com.onepiecemod.weather.SeaEventType;
import com.onepiecemod.weather.SeaEvents;

/**
 * Sea monster encounters while you sail. Every 30 seconds each player at the helm (or on deck) of a ship out at sea has
 * a small chance to meet one. After a meeting that player gets a few quiet minutes.
 *  - Kraken: tentacles grab your hull, slowing the ship and squeezing it until you beat the Kraken off.
 *  - Sea King Lord: a Sea King three times the size of the others (New World, rarely the Grand Line).
 *  - Sea Monkeys: they laugh, splash, and whip up a rogue wave aimed at your ship.
 *  - Sea Cats: a hungry pack surfaces and goes for you.
 *  - Island Whale: a friendly giant swims beside you for a while, and leaves something behind when it dives.
 * The Calm Belt has its own Sea King ambushes (weather package), so nothing here happens there.
 */
public final class SeaMonsters {
	public enum Kind { KRAKEN, SEA_KING_LORD, SEA_MONKEYS, SEA_CATS, ISLAND_WHALE }

	// ---- Tune these to meet monsters more or less often ----
	private static final int CHECK_EVERY = 20 * 30;
	private static final float BLUE_CHANCE = 0.03f;
	private static final float GRAND_LINE_CHANCE = 0.05f;
	private static final float NEW_WORLD_CHANCE = 0.07f;
	/** After a meeting, how long until that player can meet another monster. */
	private static final int COOLDOWN = 20 * 60 * 7;

	public static final String TAG = "onepiece_sea_monster";
	public static final String LORD_TAG = "onepiece_sea_king_lord";
	public static final String KRAKEN_TAG = "onepiece_kraken_grab";

	private static final Map<UUID, Long> NEXT = new HashMap<>();
	private static final List<Encounter> ACTIVE = new ArrayList<>();

	private static final class Encounter {
		final Kind kind;
		final UUID player;
		final UUID ship;
		final List<UUID> mobs = new ArrayList<>();
		final long until;
		int seconds;

		Encounter(Kind kind, UUID player, UUID ship, long until) {
			this.kind = kind;
			this.player = player;
			this.ship = ship;
			this.until = until;
		}
	}

	private SeaMonsters() {
	}

	static void clear() {
		NEXT.clear();
		ACTIVE.clear();
	}

	static void tick(MinecraftServer server) {
		ServerLevel level = server.overworld();
		long now = level.getGameTime();
		if (server.getTickCount() % 20 == 3) {
			for (Encounter encounter : List.copyOf(ACTIVE)) {
				if (!tickEncounter(level, encounter, now)) {
					ACTIVE.remove(encounter);
				}
			}
		}
		if (server.getTickCount() % CHECK_EVERY != 7) {
			return;
		}
		for (ServerPlayer player : level.players()) {
			ShipEntity ship = SeaSpots.sailing(player);
			if (ship == null || now < NEXT.getOrDefault(player.getUUID(), 0L) || busy(player)
					|| SeaEvents.eventNear(player.getX(), player.getZ(), 20) != null) {
				continue;
			}
			CalmBelt.Sea sea = SeaSpots.sea(level, ship.blockPosition());
			if (sea == null || sea == CalmBelt.Sea.CALM_BELT) {
				continue;
			}
			float chance = sea == CalmBelt.Sea.NEW_WORLD ? NEW_WORLD_CHANCE : sea.grandLine() ? GRAND_LINE_CHANCE : BLUE_CHANCE;
			if (player.getRandom().nextFloat() >= chance) {
				continue;
			}
			if (start(level, player, ship, pick(level, sea)) == null) {
				NEXT.put(player.getUUID(), now + COOLDOWN);
			}
		}
	}

	private static boolean busy(ServerPlayer player) {
		for (Encounter encounter : ACTIVE) {
			if (encounter.player.equals(player.getUUID())) {
				return true;
			}
		}
		return false;
	}

	private static Kind pick(ServerLevel level, CalmBelt.Sea sea) {
		RandomSource random = level.getRandom();
		if (SeaSpots.peaceful(level)) {
			return Kind.ISLAND_WHALE;
		}
		int roll = random.nextInt(100);
		if (sea == CalmBelt.Sea.BLUE) {
			return roll < 45 ? Kind.SEA_CATS : roll < 75 ? Kind.ISLAND_WHALE : Kind.SEA_MONKEYS;
		}
		if (sea == CalmBelt.Sea.NEW_WORLD && roll < 25) {
			return Kind.SEA_KING_LORD;
		}
		roll = random.nextInt(100);
		return roll < 32 ? Kind.KRAKEN : roll < 52 ? Kind.SEA_MONKEYS : roll < 70 ? Kind.SEA_CATS : roll < 92 ? Kind.ISLAND_WHALE
				: Kind.SEA_KING_LORD;
	}

	/** Starts an encounter around this player's ship. Returns null if it worked, else why not. /voyage monster uses it too. */
	@Nullable
	public static String start(ServerLevel level, ServerPlayer player, ShipEntity ship, Kind kind) {
		if (kind != Kind.ISLAND_WHALE && SeaSpots.peaceful(level)) {
			return "Monsters don't come out on Peaceful.";
		}
		long now = level.getGameTime();
		RandomSource random = level.getRandom();
		Encounter encounter;
		switch (kind) {
			case KRAKEN -> {
				Vec3 at = deepSpotBeside(level, ship, ship.getBbWidth() * 0.5 + 3, 3);
				CreatureEntity kraken = at == null ? null : creature(level, "kraken", at);
				if (kraken == null) {
					return "No deep water right beside the ship for a Kraken.";
				}
				boost(kraken, 160, 0);
				kraken.addTag(KRAKEN_TAG);
				kraken.setCustomName(Component.literal("Kraken").withStyle(ChatFormatting.DARK_PURPLE));
				level.addFreshEntity(kraken);
				kraken.setTarget(player);
				geyser(level, at, 1.5f);
				encounter = new Encounter(kind, player.getUUID(), ship.getUUID(), now + 20 * 75);
				encounter.mobs.add(kraken.getUUID());
				tellNear(level, ship, Component.literal("Huge tentacles burst out of the sea and wrap around the hull! A KRAKEN! Beat it off before it crushes the ship!")
						.withStyle(ChatFormatting.DARK_PURPLE, ChatFormatting.BOLD));
			}
			case SEA_KING_LORD -> {
				Vec3 at = deepSpotBeside(level, ship, 22, 6);
				if (at == null) {
					return "No deep water near the ship for a Sea King Lord.";
				}
				SeaKingEntity lord = SeaEntities.SEA_KING.create(level, EntitySpawnReason.EVENT);
				if (lord == null) {
					return "The Sea King Lord failed to spawn.";
				}
				lord.snapTo(at.x, at.y, at.z, random.nextFloat() * 360, 0);
				boost(lord, 600, 24);
				if (lord.getAttribute(Attributes.SCALE) != null) {
					lord.getAttribute(Attributes.SCALE).setBaseValue(1.4); // about 105 blocks long
				}
				lord.addTag(TAG);
				lord.addTag(LORD_TAG);
				lord.setCustomName(Component.literal("Sea King Lord").withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD));
				lord.setPersistenceRequired();
				level.addFreshEntity(lord);
				lord.setTarget(player);
				geyser(level, at, 3f);
				level.playSound(null, at.x, at.y, at.z, com.onepiecemod.sound.WorldSounds.SEA_KING_AMBIENT, SoundSource.HOSTILE, 6.0f, 0.5f);
				encounter = new Encounter(kind, player.getUUID(), ship.getUUID(), now + 20 * 240);
				encounter.mobs.add(lord.getUUID());
				tellNear(level, ship, Component.literal("The sea swells like a hill... a SEA KING LORD rises, three times the size of any Sea King you've seen!")
						.withStyle(ChatFormatting.DARK_RED, ChatFormatting.BOLD));
			}
			case SEA_MONKEYS -> {
				Vec3 center = deepSpotBeside(level, ship, 22, 0.5);
				if (center == null) {
					return "No open sea near the ship for the Sea Monkeys.";
				}
				encounter = new Encounter(kind, player.getUUID(), ship.getUUID(), now + 20 * 40);
				for (int i = 0; i < 4; i++) {
					Vec3 at = center.add((random.nextDouble() - 0.5) * 8, 0, (random.nextDouble() - 0.5) * 8);
					CreatureEntity monkey = creature(level, "sea_monkey", at);
					if (monkey != null) {
						level.addFreshEntity(monkey);
						encounter.mobs.add(monkey.getUUID());
					}
				}
				geyser(level, center, 1f);
				level.playSound(null, center.x, center.y, center.z, SoundEvents.DOLPHIN_PLAY, SoundSource.HOSTILE, 3.0f, 1.4f);
				// The wave rolls from the monkeys toward the ship.
				float heading = (float) Math.atan2(ship.getZ() - center.z, ship.getX() - center.x);
				SeaEvents.start(level, SeaEventType.ROGUE_WAVE, player, heading);
				tellNear(level, ship, Component.literal("Sea Monkeys! They're laughing and slapping the water... they're whipping up a wave at you!")
						.withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD));
			}
			case SEA_CATS -> {
				encounter = new Encounter(kind, player.getUUID(), ship.getUUID(), now + 20 * 90);
				int count = 2 + random.nextInt(2);
				for (int i = 0; i < count; i++) {
					Vec3 at = deepSpotBeside(level, ship, 12 + random.nextInt(5), 2);
					CreatureEntity cat = at == null ? null : creature(level, "sea_cat", at);
					if (cat != null) {
						level.addFreshEntity(cat);
						cat.setTarget(player);
						encounter.mobs.add(cat.getUUID());
						geyser(level, at, 1f);
					}
				}
				if (encounter.mobs.isEmpty()) {
					return "No deep water near the ship for Sea Cats.";
				}
				tellNear(level, ship, Component.literal("A pack of Sea Cats surfaces around the ship, hissing. They look hungry!")
						.withStyle(ChatFormatting.RED));
			}
			case ISLAND_WHALE -> {
				Vec3 at = deepSpotBeside(level, ship, ship.getBbWidth() * 0.5 + 10, 2);
				CreatureEntity whale = at == null ? null : creature(level, "island_whale", at);
				if (whale == null) {
					return "No deep water beside the ship for an Island Whale.";
				}
				whale.setYRot(ship.getYRot());
				whale.setPersistenceRequired();
				level.addFreshEntity(whale);
				geyser(level, at, 2f);
				encounter = new Encounter(kind, player.getUUID(), ship.getUUID(), now + 20 * 50);
				encounter.mobs.add(whale.getUUID());
				tellNear(level, ship, Component.literal("An Island Whale surfaces beside your ship! Trees are growing on its back...")
						.withStyle(ChatFormatting.GREEN));
				for (ServerPlayer near : playersNear(level, ship, 64)) {
					com.onepiecemod.advancement.AdvancementFeature.grant(near, "journey/island_whale");
				}
			}
			default -> {
				return "Unknown monster.";
			}
		}
		ACTIVE.add(encounter);
		return null;
	}

	// ---- While it lasts ----

	/** Returns false when the encounter is over. */
	private static boolean tickEncounter(ServerLevel level, Encounter encounter, long now) {
		encounter.seconds++;
		List<Entity> mobs = new ArrayList<>();
		for (UUID id : encounter.mobs) {
			Entity mob = level.getEntity(id);
			if (mob != null && mob.isAlive()) {
				mobs.add(mob);
			}
		}
		ShipEntity ship = level.getEntity(encounter.ship) instanceof ShipEntity s && !s.isRemoved() ? s : null;
		ServerPlayer player = level.getServer().getPlayerList().getPlayer(encounter.player);
		boolean timeUp = now >= encounter.until;

		switch (encounter.kind) {
			case KRAKEN -> {
				Entity kraken = mobs.isEmpty() ? null : mobs.get(0);
				if (kraken == null) {
					return false; // Beaten: the reward drops in onDeath.
				}
				boolean holding = ship != null && kraken.distanceToSqr(ship) < Mth.square(ship.getBbWidth() * 0.5 + 12);
				if (timeUp || !holding) {
					level.sendParticles(ParticleTypes.SQUID_INK, kraken.getX(), kraken.getY() + 1, kraken.getZ(), 60, 2, 1, 2, 0.1);
					if (ship != null) {
						tellNear(level, ship, Component.literal("The Kraken lets go and sinks back into the deep.").withStyle(ChatFormatting.DARK_PURPLE));
					}
					kraken.discard();
					return false;
				}
				ShipHull.chain(ship, 30); // The tentacles drag on the ship like chain shot.
				if (kraken instanceof Mob mob && player != null && mob.getTarget() == null) {
					mob.setTarget(player);
				}
				if (encounter.seconds % 3 == 0) {
					SeaEventEffects.strainHull(level, ship, 0.03f, kraken.position());
				}
				level.sendParticles(ParticleTypes.SQUID_INK, ship.getX(), level.getSeaLevel() + 0.5, ship.getZ(), 12,
						ship.getBbWidth() * 0.3, 0.3, ship.getBbWidth() * 0.3, 0.02);
				// A tentacle sweeps the deck now and then.
				if (encounter.seconds % 4 == 0) {
					List<Entity> deck = ShipDecks.onDeck(ship);
					for (Entity rider : ship.getPassengers()) {
						deck.add(rider);
					}
					List<LivingEntity> targets = new ArrayList<>();
					for (Entity e : deck) {
						if (e instanceof Player p && !p.isCreative() && !p.isSpectator()) {
							targets.add(p);
						}
					}
					if (!targets.isEmpty()) {
						LivingEntity hit = targets.get(level.getRandom().nextInt(targets.size()));
						DamageSource source = kraken instanceof LivingEntity living ? level.damageSources().mobAttack(living) : level.damageSources().generic();
						hit.hurtServer(level, source, 4.0f);
						Vec3 away = hit.position().subtract(kraken.position()).multiply(1, 0, 1).normalize().scale(0.6);
						hit.setDeltaMovement(hit.getDeltaMovement().add(away.x, 0.4, away.z));
						com.onepiecemod.util.Motion.sync(hit);
						level.sendParticles(ParticleTypes.SPLASH, hit.getX(), hit.getY() + 1, hit.getZ(), 30, 0.6, 0.6, 0.6, 0.2);
						level.playSound(null, hit.blockPosition(), SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 1.5f, 0.6f);
					}
				}
				return true;
			}
			case SEA_MONKEYS -> {
				if (encounter.seconds % 4 == 0) {
					for (Entity monkey : mobs) {
						level.sendParticles(ParticleTypes.SPLASH, monkey.getX(), monkey.getY() + 1, monkey.getZ(), 12, 0.4, 0.4, 0.4, 0.2);
					}
					if (!mobs.isEmpty()) {
						Entity loud = mobs.get(0);
						level.playSound(null, loud.getX(), loud.getY(), loud.getZ(), SoundEvents.DOLPHIN_PLAY, SoundSource.HOSTILE, 2.0f, 1.6f);
					}
				}
				if (timeUp) {
					for (Entity monkey : mobs) {
						monkey.discard();
					}
					return false;
				}
				return !mobs.isEmpty();
			}
			case ISLAND_WHALE -> {
				Entity whale = mobs.isEmpty() ? null : mobs.get(0);
				if (whale == null) {
					return false;
				}
				if (encounter.seconds % 6 == 0) {
					spout(level, whale);
				}
				if (timeUp) {
					// It blows one last spout and dives, and something bobs up where it was.
					spout(level, whale);
					leaveGift(level, whale.position(), ship);
					whale.discard();
					return false;
				}
				return true;
			}
			default -> {
				// Sea Cats and the Sea King Lord fight on their own. Once nobody is around, they swim off.
				if (mobs.isEmpty()) {
					return false;
				}
				if (timeUp) {
					boolean watched = false;
					for (Entity mob : mobs) {
						watched |= level.getNearestPlayer(mob, 48) != null;
					}
					if (!watched) {
						mobs.forEach(Entity::discard);
						return false;
					}
				}
				return true;
			}
		}
	}

	/** The rewards for beating a Kraken or a Sea King Lord. Called from VoyageFeature's death hook. */
	static void onDeath(ServerLevel level, LivingEntity entity, DamageSource source) {
		boolean kraken = entity.entityTags().contains(KRAKEN_TAG);
		boolean lord = entity.entityTags().contains(LORD_TAG);
		if (!kraken && !lord) {
			return;
		}
		RandomSource random = level.getRandom();
		Vec3 at = new Vec3(entity.getX(), Math.max(entity.getY(), level.getSeaLevel()) + 0.5, entity.getZ());
		ServerPlayer winner = source.getEntity() instanceof ServerPlayer p ? p
				: level.getNearestPlayer(entity, 48) instanceof ServerPlayer p ? p : null;
		if (kraken) {
			drop(level, at, new ItemStack(Resources.KRAKEN_INK, 3 + random.nextInt(4)));
			drop(level, at, new ItemStack(CharacterFeature.BERRY, 20 + random.nextInt(25)));
			drop(level, at, new ItemStack(Resources.SEA_PEARL, 1 + random.nextInt(2)));
			if (random.nextBoolean()) {
				drop(level, at, new ItemStack(VoyageFeature.MESSAGE_BOTTLE));
			}
			if (winner != null) {
				winner.sendSystemMessage(Component.literal("The Kraken lets go of your ship and sinks, beaten! Its treasures float up.")
						.withStyle(ChatFormatting.GOLD));
				com.onepiecemod.advancement.AdvancementFeature.grant(winner, "journey/kraken");
			}
		} else {
			drop(level, at, new ItemStack(Resources.SEA_KING_SCALE, 5 + random.nextInt(5)));
			drop(level, at, new ItemStack(Resources.SEA_PEARL, 3 + random.nextInt(3)));
			drop(level, at, new ItemStack(CharacterFeature.BERRY, 64));
			drop(level, at, new ItemStack(CharacterFeature.BERRY, 40 + random.nextInt(40)));
			drop(level, at, new ItemStack(Items.DIAMOND, 2 + random.nextInt(3)));
			if (random.nextFloat() < 0.5f) {
				drop(level, at, new ItemStack(TreasureFeature.HOARD_MAP));
			}
			if (random.nextFloat() < 0.25f) {
				drop(level, at, new ItemStack(Items.HEART_OF_THE_SEA));
			}
			if (winner != null) {
				winner.sendSystemMessage(Component.literal("The Sea King Lord crashes into the waves and doesn't come back up. Sailors will talk about this for years!")
						.withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
				com.onepiecemod.advancement.AdvancementFeature.grant(winner, "journey/sea_king_lord");
				com.onepiecemod.news.NewsLog.report(level.getServer(), "SEA KING LORD SLAIN",
						winner.getName().getString() + " brought down a Sea King Lord in the New World.", false);
			}
		}
	}

	// ---- Helpers ----

	@Nullable
	private static Vec3 deepSpotBeside(ServerLevel level, ShipEntity ship, double out, double under) {
		for (int attempt = 0; attempt < 6; attempt++) {
			Vec3 at = SeaSpots.beside(level, ship, out + attempt, under);
			if (SeaKingSpawner.isDeepWater(level, BlockPos.containing(at.x, level.getSeaLevel() - 5, at.z))) {
				return at;
			}
		}
		return null;
	}

	@Nullable
	private static CreatureEntity creature(ServerLevel level, String species, Vec3 at) {
		var type = Creatures.TYPES.get(species);
		CreatureEntity mob = type == null ? null : type.create(level, EntitySpawnReason.EVENT);
		if (mob == null) {
			return null;
		}
		mob.snapTo(at.x, at.y, at.z, level.getRandom().nextFloat() * 360, 0);
		mob.addTag(TAG);
		return mob;
	}

	private static void boost(LivingEntity mob, double health, double attack) {
		if (mob.getAttribute(Attributes.MAX_HEALTH) != null) {
			mob.getAttribute(Attributes.MAX_HEALTH).setBaseValue(health);
			mob.setHealth((float) health);
		}
		if (attack > 0 && mob.getAttribute(Attributes.ATTACK_DAMAGE) != null) {
			mob.getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(attack);
		}
	}

	private static void geyser(ServerLevel level, Vec3 at, float size) {
		double y = level.getSeaLevel();
		level.sendParticles(ParticleTypes.SPLASH, at.x, y + 1, at.z, (int) (60 * size), 1.2 * size, 2.5 * size, 1.2 * size, 0.3);
		level.sendParticles(ParticleTypes.BUBBLE_COLUMN_UP, at.x, y - 2, at.z, 20, size, 1, size, 0.1);
		level.playSound(null, at.x, y, at.z, SoundEvents.GENERIC_SPLASH, SoundSource.HOSTILE, 3.0f, 0.6f);
	}

	private static void spout(ServerLevel level, Entity whale) {
		double y = Math.max(whale.getY() + whale.getBbHeight(), level.getSeaLevel() + 1);
		level.sendParticles(ParticleTypes.SPLASH, whale.getX(), y + 2, whale.getZ(), 80, 0.6, 3, 0.6, 0.4);
		level.sendParticles(ParticleTypes.CLOUD, whale.getX(), y + 4, whale.getZ(), 15, 0.8, 1.5, 0.8, 0.05);
		level.playSound(null, whale.getX(), y, whale.getZ(), SoundEvents.DOLPHIN_SPLASH, SoundSource.NEUTRAL, 4.0f, 0.4f);
	}

	/** What the whale leaves behind: a drifting supply boat, or a bottle bobbing on the waves. */
	private static void leaveGift(ServerLevel level, Vec3 at, @Nullable ShipEntity ship) {
		Vec3 surface = new Vec3(at.x, level.getSeaLevel(), at.z);
		if (level.getRandom().nextBoolean() && Flotsam.spawnAt(level, surface, level.getRandom().nextFloat() * 360) != null) {
			if (ship != null) {
				tellNear(level, ship, Component.literal("The Island Whale dives. Where it was, an old supply boat bobs to the surface!")
						.withStyle(ChatFormatting.GREEN));
			}
			return;
		}
		drop(level, surface.add(0, 0.5, 0), new ItemStack(VoyageFeature.MESSAGE_BOTTLE));
		if (ship != null) {
			tellNear(level, ship, Component.literal("The Island Whale dives. A bottle with a message inside bobs up where it was!")
					.withStyle(ChatFormatting.GREEN));
		}
	}

	static void drop(ServerLevel level, Vec3 at, ItemStack stack) {
		ItemEntity item = new ItemEntity(level, at.x, at.y, at.z, stack);
		item.setDeltaMovement((level.getRandom().nextDouble() - 0.5) * 0.2, 0.3, (level.getRandom().nextDouble() - 0.5) * 0.2);
		level.addFreshEntity(item);
	}

	static List<ServerPlayer> playersNear(ServerLevel level, Entity near, double within) {
		List<ServerPlayer> found = new ArrayList<>();
		for (ServerPlayer player : level.players()) {
			if (!player.isSpectator() && player.distanceToSqr(near) < within * within) {
				found.add(player);
			}
		}
		return found;
	}

	static void tellNear(ServerLevel level, Entity near, Component message) {
		for (ServerPlayer player : playersNear(level, near, 96)) {
			player.sendSystemMessage(message);
		}
	}

}
