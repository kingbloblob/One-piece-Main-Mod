package com.onepiecemod.crewship;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.WeakHashMap;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.advancement.AdvancementFeature;
import com.onepiecemod.crew.CrewMode;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.multiplayer.PlayerCrews;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipFeature;
import com.onepiecemod.ship.ShipInteractions;
import com.onepiecemod.ship.ShipLayout;
import com.onepiecemod.shipcombat.ShipHull;

/**
 * Life aboard a crew's home ship. About once a second, for every home ship that is loaded:
 *  1. find her (docked as blocks, or sailing as a ship) and look over her rooms;
 *  2. station the captain's crewmates who were set to Work aboard, and hand each a post and a bunk;
 *  3. give the crew aboard the perks of her level and rooms;
 *  4. once a day, put the crew's haul in the Ship's Log.
 */
public final class CrewShipLife {
	/** A loaded home ship, as found this second. */
	public static final class Home {
		public final UUID owner;
		public final UUID homeId;
		public final ServerLevel level;
		/** Null while docked. */
		public final ShipEntity ship;
		public final CrewShipSurvey survey;
		public final CrewShipSurvey.Frame frame;
		/** Ship's Log position (world while docked, ship grid while sailing). */
		public final BlockPos log;
		/** Docked only: every block of the ship, to tell who stands aboard. */
		final Set<BlockPos> dockedBlocks;
		public final List<CrewmateEntity> stationed = new ArrayList<>();
		public int shipLevel;

		Home(UUID owner, UUID homeId, ServerLevel level, ShipEntity ship, CrewShipSurvey survey, BlockPos log, Set<BlockPos> dockedBlocks) {
			this.owner = owner;
			this.homeId = homeId;
			this.level = level;
			this.ship = ship;
			this.survey = survey;
			this.frame = ship != null ? new CrewShipSurvey.Frame(ship) : CrewShipSurvey.Frame.DOCKED;
			this.log = log;
			this.dockedBlocks = dockedBlocks;
		}

		/** True if the entity stands on this ship. */
		public boolean aboard(Entity entity) {
			if (entity.level() != level) {
				return false;
			}
			if (ship != null) {
				return ShipEntity.aboard(entity) == ship;
			}
			BlockPos feet = entity.blockPosition();
			for (int down = 0; down <= 2; down++) {
				if (dockedBlocks.contains(feet.below(down))) {
					return true;
				}
			}
			return false;
		}

		public boolean has(ShipRoom room) {
			return survey.has(room) && (room.role == null || stationedAs(room.role) != null);
		}

		public CrewmateEntity stationedAs(CrewRole role) {
			for (CrewmateEntity crewmate : stationed) {
				if (crewmate.getRole() == role) {
					return crewmate;
				}
			}
			return null;
		}

		/** A box around the whole ship in the world. */
		AABB box() {
			if (ship != null) {
				return ship.getBoundingBox().inflate(2, 4, 2);
			}
			int minX = Integer.MAX_VALUE, minY = Integer.MAX_VALUE, minZ = Integer.MAX_VALUE;
			int maxX = Integer.MIN_VALUE, maxY = Integer.MIN_VALUE, maxZ = Integer.MIN_VALUE;
			for (BlockPos pos : dockedBlocks) {
				minX = Math.min(minX, pos.getX());
				minY = Math.min(minY, pos.getY());
				minZ = Math.min(minZ, pos.getZ());
				maxX = Math.max(maxX, pos.getX());
				maxY = Math.max(maxY, pos.getY());
				maxZ = Math.max(maxZ, pos.getZ());
			}
			return new AABB(minX - 1, minY - 1, minZ - 1, maxX + 2, maxY + 4, maxZ + 2);
		}
	}

	/** Where a stationed crewmate works and sleeps. Positions are in the home's frame. */
	public record Assignment(Home home, BlockPos post, BlockPos lookAt, CrewShipSurvey.Bunk bunk, ShipRoom room) {}

	/** A sailing ship's Ship's Log, read once per layout. */
	private record Scan(ShipLayout layout, int logIndex, UUID owner, UUID homeId) {}

	private static final Set<ShipEntity> LOADED = Collections.newSetFromMap(new WeakHashMap<>());
	private static final Map<ShipEntity, Scan> SCANS = new WeakHashMap<>();
	private static final Map<ShipLayout, CrewShipSurvey> SAILING_SURVEYS = new WeakHashMap<>();
	/** Docked surveys, redone every DOCKED_RESURVEY ticks. */
	private static final Map<UUID, Object[]> DOCKED = new HashMap<>();
	private static final int DOCKED_RESURVEY = 200;

	private static final Map<UUID, Home> HOMES = new HashMap<>();
	private static final Map<UUID, Assignment> ASSIGNMENTS = new HashMap<>();

	private CrewShipLife() {
	}

	static void initialize() {
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity instanceof ShipEntity ship) {
				LOADED.add(ship);
			}
		});
		ServerTickEvents.END_SERVER_TICK.register(CrewShipLife::tick);
	}

	// ---- What the rest of the mod reads ----

	/** The captain's home ship if it's loaded right now, or null. */
	public static Home home(UUID owner) {
		return owner == null ? null : HOMES.get(owner);
	}

	public static Assignment assignment(CrewmateEntity crewmate) {
		return ASSIGNMENTS.get(crewmate.getUUID());
	}

	/** Extra top speed for a sailing ship from her home-ship level and Chart Room (1 = none). */
	public static float speedBonus(ShipEntity ship) {
		Home home = homeOfShip(ship);
		if (home == null) {
			return 1f;
		}
		return CrewShipLevels.speedBonus(home.shipLevel) * (home.has(ShipRoom.CHART_ROOM) ? 1.10f : 1f);
	}

	/** Extra turning for a sailing ship from her home-ship level and Helm (1 = none). */
	public static float turnBonus(ShipEntity ship) {
		Home home = homeOfShip(ship);
		if (home == null) {
			return 1f;
		}
		return CrewShipLevels.turnBonus(home.shipLevel) * (home.has(ShipRoom.HELM) ? 1.15f : 1f);
	}

	private static Home homeOfShip(ShipEntity ship) {
		for (Home home : HOMES.values()) {
			if (home.ship == ship) {
				return home;
			}
		}
		return null;
	}

	// ---- Every second ----

	private static void tick(MinecraftServer server) {
		int now = server.getTickCount();
		if (now % 20 != 7) {
			return;
		}
		HOMES.clear();
		ASSIGNMENTS.clear();
		for (Map.Entry<String, HomeShips.HomeShip> entry : HomeShips.all(server).entrySet()) {
			UUID owner;
			try {
				owner = UUID.fromString(entry.getKey());
			} catch (IllegalArgumentException e) {
				continue;
			}
			Home home = find(server, owner, entry.getValue(), now);
			if (home == null) {
				continue;
			}
			HOMES.put(owner, home);
			live(server, home, entry.getValue(), now);
		}
	}

	private static Home find(MinecraftServer server, UUID owner, HomeShips.HomeShip saved, int now) {
		// Sailing?
		for (ShipEntity ship : new ArrayList<>(LOADED)) {
			if (ship.isRemoved()) {
				LOADED.remove(ship);
				continue;
			}
			if (!(ship.level() instanceof ServerLevel level)) {
				continue;
			}
			Scan scan = scan(ship);
			if (scan.logIndex >= 0 && owner.equals(scan.owner) && saved.homeId().equals(scan.homeId)) {
				ShipLayout layout = ship.getLayout();
				CrewShipSurvey survey = SAILING_SURVEYS.computeIfAbsent(layout, l -> {
					Map<BlockPos, BlockState> blocks = new HashMap<>();
					for (ShipLayout.ShipBlock block : l.blocks) {
						blocks.put(block.pos(), block.state());
					}
					return CrewShipSurvey.of(blocks, l.helm);
				});
				return new Home(owner, saved.homeId(), level, ship, survey, layout.blocks.get(scan.logIndex).pos(), Set.of());
			}
		}
		// Docked?
		if (saved.dockPos().isEmpty() || saved.dimension().isEmpty()) {
			return null;
		}
		ServerLevel level = server.getLevel(ResourceKey.create(Registries.DIMENSION, Identifier.parse(saved.dimension())));
		BlockPos logPos = saved.dockPos().get();
		if (level == null || !level.isLoaded(logPos) || !(level.getBlockEntity(logPos) instanceof ShipLogBlockEntity log)
				|| !saved.homeId().equals(log.homeId())) {
			DOCKED.remove(owner);
			return null;
		}
		Object[] cached = DOCKED.get(owner);
		if (cached == null || !logPos.equals(cached[0]) || now - (int) cached[3] > DOCKED_RESURVEY || now < (int) cached[3]) {
			Map<BlockPos, BlockState> blocks = floodFill(level, logPos);
			BlockPos helm = null;
			for (Map.Entry<BlockPos, BlockState> block : blocks.entrySet()) {
				if (block.getValue().is(ShipFeature.HELM)) {
					helm = block.getKey();
					break;
				}
			}
			cached = new Object[] {logPos, CrewShipSurvey.of(blocks, helm), new HashSet<>(blocks.keySet()), now};
			DOCKED.put(owner, cached);
		}
		@SuppressWarnings("unchecked")
		Set<BlockPos> blocks = (Set<BlockPos>) cached[2];
		return new Home(owner, saved.homeId(), level, null, (CrewShipSurvey) cached[1], logPos, blocks);
	}

	/** Forget the docked survey so the next look-over is fresh (the log was just claimed or used). */
	static void resurvey(UUID owner) {
		DOCKED.remove(owner);
	}

	private static Scan scan(ShipEntity ship) {
		ShipLayout layout = ship.getLayout();
		Scan scan = SCANS.get(ship);
		if (scan != null && scan.layout == layout) {
			return scan;
		}
		int index = -1;
		UUID owner = null;
		UUID homeId = null;
		for (int i = 0; i < layout.blocks.size(); i++) {
			ShipLayout.ShipBlock block = layout.blocks.get(i);
			if (block.state().is(CrewShipFeature.SHIP_LOG) && block.nbt().isPresent()) {
				BlockEntity saved = BlockEntity.loadStatic(BlockPos.ZERO, block.state(), block.nbt().get(), ship.level().registryAccess());
				if (saved instanceof ShipLogBlockEntity log && log.owner() != null) {
					index = i;
					owner = log.owner();
					homeId = log.homeId();
					break;
				}
				if (index < 0) {
					index = i; // An unclaimed log: remember it, but keep looking for a claimed one.
				}
			}
		}
		scan = new Scan(layout, index, owner, homeId);
		SCANS.put(ship, scan);
		return scan;
	}

	/** Re-reads a sailing ship's log next time (it was just claimed). */
	static void rescan(ShipEntity ship) {
		SCANS.remove(ship);
	}

	/** Every ship block connected to the log, like the Ship's Wheel does when setting sail. */
	static Map<BlockPos, BlockState> floodFill(Level level, BlockPos start) {
		Map<BlockPos, BlockState> found = new HashMap<>();
		ArrayDeque<BlockPos> toCheck = new ArrayDeque<>();
		found.put(start.immutable(), level.getBlockState(start));
		toCheck.add(start.immutable());
		while (!toCheck.isEmpty() && found.size() < com.onepiecemod.ship.ShipAssembler.MAX_BLOCKS) {
			BlockPos pos = toCheck.poll();
			for (BlockPos next : BlockPos.betweenClosed(pos.offset(-1, -1, -1), pos.offset(1, 1, 1))) {
				if (found.containsKey(next) || !level.isLoaded(next)) {
					continue;
				}
				BlockState state = level.getBlockState(next);
				if (!state.isAir() && !state.liquid() && !state.is(ShipFeature.NOT_SHIP)) {
					BlockPos copy = next.immutable();
					found.put(copy, state);
					toCheck.add(copy);
				}
			}
		}
		return found;
	}

	// ---- Living aboard ----

	private static void live(MinecraftServer server, Home home, HomeShips.HomeShip saved, int now) {
		// 1. Who's stationed: the captain's crewmates set to Work while aboard.
		for (CrewmateEntity crewmate : home.level.getEntitiesOfClass(CrewmateEntity.class, home.box(),
				c -> home.owner.equals(c.getCaptainId()) && c.isAlive())) {
			UUID station = crewmate.getAttached(CrewShipFeature.STATIONED);
			if (crewmate.getMode() != CrewMode.WORK) {
				if (station != null) {
					crewmate.removeAttached(CrewShipFeature.STATIONED);
				}
				continue;
			}
			if (station == null && home.aboard(crewmate)) {
				crewmate.setAttached(CrewShipFeature.STATIONED, home.homeId);
				station = home.homeId;
				crewmate.tellCaptain(crewmate.getDisplayName().getString() + " moved aboard the ship. "
						+ (home.survey.has(ShipRoom.forRole(crewmate.getRole())) ? "Off to the " + ShipRoom.forRole(crewmate.getRole()).title + "!"
						: "No " + ShipRoom.forRole(crewmate.getRole()).title + " yet, so they'll help out on deck."));
			}
			if (home.homeId.equals(station)) {
				home.stationed.add(crewmate);
			}
		}
		home.stationed.sort(Comparator.comparing(Entity::getUUID));
		home.shipLevel = CrewShipLevels.levelFor(home.survey, home.stationed.size());

		// 2. Posts and bunks.
		int deck = 0;
		for (int i = 0; i < home.stationed.size(); i++) {
			CrewmateEntity crewmate = home.stationed.get(i);
			ShipRoom room = ShipRoom.forRole(crewmate.getRole());
			CrewShipSurvey.Room built = room != null ? home.survey.rooms.get(room) : null;
			BlockPos post;
			BlockPos look;
			if (built != null) {
				post = built.post();
				look = built.core();
			} else if (!home.survey.deckSpots.isEmpty()) {
				post = home.survey.deckSpots.get(deck++ % home.survey.deckSpots.size());
				look = null;
			} else {
				post = home.log.above();
				look = home.log;
			}
			CrewShipSurvey.Bunk bunk = i < home.survey.bunks.size() ? home.survey.bunks.get(i) : null;
			ASSIGNMENTS.put(crewmate.getUUID(), new Assignment(home, post, look, bunk, built != null ? room : null));
		}

		// 3. Level changes.
		if (home.shipLevel != saved.level()) {
			HomeShips.put(server, home.owner, saved.withLevel(home.shipLevel));
			if (home.shipLevel > saved.best()) {
				String name = CrewShipLevels.NAMES[home.shipLevel];
				PlayerCrews.tell(server, home.owner, Component.literal("Your home ship is now a " + name + "! "
						+ CrewShipLevels.perk(home.shipLevel)).withStyle(ChatFormatting.GOLD));
				ServerPlayer captain = server.getPlayerList().getPlayer(home.owner);
				if (captain != null) {
					captain.level().playSound(null, captain.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.8f, 0.8f);
					if (home.shipLevel >= CrewShipLevels.MAX) {
						AdvancementFeature.grant(captain, "pirate/dream_ship");
					}
				}
			}
			saved = HomeShips.of(server, home.owner);
		}

		// 4. Perks.
		perks(home, now);

		// 5. The daily haul.
		long today = home.level.getOverworldClockTime() / 24000L;
		if (saved.lastHaulDay() < 0 || (today > saved.lastHaulDay() && home.shipLevel < 1)) {
			HomeShips.put(server, home.owner, saved.hauled(today));
		} else if (today > saved.lastHaulDay()) {
			CrewShipHaul.Haul haul = CrewShipHaul.roll(home, home.level.getRandom());
			boolean full = false;
			for (ItemStack stack : haul.items()) {
				full |= !deliver(home, stack).isEmpty();
			}
			HomeShips.put(server, home.owner, saved.hauled(today));
			ServerPlayer captain = server.getPlayerList().getPlayer(home.owner);
			if (captain != null) {
				captain.sendSystemMessage(Component.literal("Day's work aboard your " + CrewShipLevels.NAMES[home.shipLevel]
						+ ": the haul is in the Ship's Log.").withStyle(ChatFormatting.GOLD));
				for (String line : haul.lines()) {
					captain.sendSystemMessage(Component.literal("  " + line).withStyle(ChatFormatting.YELLOW));
				}
				if (full) {
					captain.sendSystemMessage(Component.literal("  The Ship's Log locker is full! Some of the haul was lost.").withStyle(ChatFormatting.RED));
				}
			}
		}
	}

	private static void perks(Home home, int now) {
		ServerLevel level = home.level;
		boolean everyTwo = now % 40 == 7;
		List<ServerPlayer> crew = new ArrayList<>();
		for (ServerPlayer player : level.players()) {
			if (!player.isSpectator() && home.aboard(player) && isCrew(level.getServer(), player, home.owner)) {
				crew.add(player);
			}
		}

		for (ServerPlayer player : crew) {
			// Resting aboard (level 2+): heal once out of a fight for 10 s.
			if (home.shipLevel >= 2 && player.getHealth() < player.getMaxHealth() && player.getLastHurtByMobTimestamp() + 200 < player.tickCount) {
				addEffect(player, MobEffects.REGENERATION, 50, 0);
			}
			if (home.has(ShipRoom.INFIRMARY) && player.getHealth() < player.getMaxHealth() * 0.75f) {
				addEffect(player, MobEffects.REGENERATION, 50, 1);
			}
			if (home.has(ShipRoom.GALLEY) && now % 400 == 7 && player.getFoodData().getFoodLevel() < 20) {
				player.getFoodData().eat(2, 0.4f);
			}
			if (home.has(ShipRoom.GYM)) {
				addEffect(player, MobEffects.STRENGTH, 50, 0);
			}
			if (home.has(ShipRoom.BATH)) {
				CrewShipSurvey.Room bath = home.survey.rooms.get(ShipRoom.BATH);
				if (player.position().distanceToSqr(home.frame.center(bath.core())) < 2.5 * 2.5) {
					List<Holder<MobEffect>> bad = new ArrayList<>();
					for (MobEffectInstance effect : player.getActiveEffects()) {
						if (effect.getEffect().value().getCategory() == MobEffectCategory.HARMFUL) {
							bad.add(effect.getEffect());
						}
					}
					bad.forEach(player::removeEffect);
				}
			}
		}

		for (CrewmateEntity crewmate : home.stationed) {
			if (home.has(ShipRoom.INFIRMARY) && everyTwo && crewmate.getHealth() < crewmate.getMaxHealth()) {
				crewmate.heal(1f);
			}
			// Training (Training Room with its Swordsman, or a Dream Ship): a little XP every minute.
			if ((home.has(ShipRoom.GYM) || home.shipLevel >= CrewShipLevels.MAX) && now % 1200 == 7 && home.aboard(crewmate)) {
				crewmate.addXp(1);
			}
		}

		// The Workshop's Shipwright patches the hull even during a battle.
		if (home.ship != null && home.has(ShipRoom.WORKSHOP)) {
			ShipHull.mend(home.ship, 0.5f);
		}
	}

	private static void addEffect(ServerPlayer player, Holder<MobEffect> effect, int ticks, int amplifier) {
		MobEffectInstance current = player.getEffect(effect);
		if (current == null || current.getAmplifier() < amplifier || current.getDuration() < ticks / 2) {
			player.addEffect(new MobEffectInstance(effect, ticks, amplifier, true, false, true));
		}
	}

	/** The captain, anyone in their player crew, or an allied crew. */
	static boolean isCrew(MinecraftServer server, ServerPlayer player, UUID owner) {
		if (owner == null) {
			return false;
		}
		if (owner.equals(player.getUUID())) {
			return true;
		}
		UUID ownerCrew = PlayerCrews.captainOf(server, owner);
		UUID key = ownerCrew != null ? ownerCrew : owner;
		UUID theirs = PlayerCrews.crewKey(server, player);
		return key.equals(theirs) || (theirs != null && PlayerCrews.allied(server, key, theirs));
	}

	/** Puts the stack in the home ship's Ship's Log. Returns what didn't fit. */
	static ItemStack deliver(Home home, ItemStack stack) {
		if (home.ship == null) {
			return home.level.getBlockEntity(home.log) instanceof ShipLogBlockEntity log ? log.store(stack) : stack;
		}
		ShipLayout layout = home.ship.getLayout();
		int index = layout.indexAt(home.log);
		if (index < 0 || layout.blocks.get(index).nbt().isEmpty()) {
			return stack;
		}
		Container open = ShipInteractions.openStorage(home.ship, index);
		if (open instanceof SimpleContainer chest) {
			return chest.addItem(stack);
		}
		ShipLayout.ShipBlock block = layout.blocks.get(index);
		BlockEntity saved = BlockEntity.loadStatic(BlockPos.ZERO, block.state(), block.nbt().get(), home.level.registryAccess());
		if (!(saved instanceof ShipLogBlockEntity log)) {
			return stack;
		}
		ItemStack rest = log.store(stack);
		layout.setNbt(index, log.saveWithFullMetadata(home.level.registryAccess()));
		return rest;
	}

	/** Small flourishes while a crewmate works: music notes from the Musician, smoke from the Cook. */
	static void workFlourish(CrewmateEntity crewmate, ShipRoom room) {
		if (!(crewmate.level() instanceof ServerLevel level)) {
			return;
		}
		Vec3 at = crewmate.position().add(0, 2.1, 0);
		if (room == ShipRoom.BAR) {
			level.sendParticles(ParticleTypes.NOTE, at.x, at.y, at.z, 1, 0.3, 0.2, 0.3, 1);
		} else if (room == ShipRoom.GALLEY) {
			level.sendParticles(ParticleTypes.SMOKE, at.x, at.y - 0.6, at.z, 3, 0.3, 0.1, 0.3, 0.01);
		} else if (room == ShipRoom.INFIRMARY) {
			level.sendParticles(ParticleTypes.HAPPY_VILLAGER, at.x, at.y - 0.6, at.z, 2, 0.4, 0.3, 0.4, 0);
		}
	}
}
