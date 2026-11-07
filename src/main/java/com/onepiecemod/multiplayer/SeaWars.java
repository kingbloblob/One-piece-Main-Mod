package com.onepiecemod.multiplayer;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.WeakHashMap;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import org.jetbrains.annotations.Nullable;

import net.minecraft.ChatFormatting;
import net.minecraft.core.UUIDUtil;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Prediction;
import net.minecraft.world.BossEvent;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.advancement.AdvancementFeature;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.config.ModConfig;
import com.onepiecemod.crew.CrewMode;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.ship.ShipDecks;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.shipcombat.ShipCombat;
import com.onepiecemod.shipcombat.ShipHull;

/**
 * Sea battles between two player crews, agreed by both captains (/crew challenge, /crew challenge accept).
 *
 * While the battle runs the two crews' ships can cannon each other (normally another crew's ship is safe,
 * see ModConfig open_sea_pvp), their gun crews fire at each other, and a ship battered below half hull can be boarded.
 * A crew wins when:
 *  - the other crew's ship sinks,
 *  - they take the other crew's ship: boarders on her deck with nobody of her crew left aboard for 20 seconds,
 *  - or the other crew surrenders (/crew surrender).
 * After 20 minutes, or when one side has nobody online for a minute, it's a draw and wagers go back.
 * The winners get a bounty raise (a tenth of the losers' crew bounty, at least 5M) and both wagers.
 * Battles are saved, so a server restart doesn't lose the Berries at stake.
 */
public class SeaWars {
	public static final long MAX_TICKS = 20L * 60 * 20;
	private static final long CHALLENGE_TICKS = 20L * 60 * 3;
	private static final long CAPTURE_TICKS = 20L * 20;
	private static final long OFFLINE_TICKS = 20L * 60;
	private static final double DOCK_BLOCK_RANGE = 160;
	private static final double BOARD_RANGE = 12;
	private static final double PARTY_RANGE = 48;
	private static final int PARTY_SIZE = 4;
	private static final long MIN_REWARD = 5_000_000L;
	/** A battle won faster than this (say, by an instant surrender) pays the wagers but no bounty: no farming with a friend. */
	private static final long MIN_FIGHT_TICKS = 20L * 60 * 2;
	/** The same two crews earn a bounty from a battle at most once per 30 minutes. */
	private static final long REWARD_COOLDOWN_TICKS = 20L * 60 * 30;

	/** A running battle between crew a (the challenger) and crew b. Both are captain ids. started is in game ticks. */
	public record War(UUID a, UUID b, long wager, long started) {
		public static final Codec<War> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				UUIDUtil.CODEC.fieldOf("a").forGetter(War::a),
				UUIDUtil.CODEC.fieldOf("b").forGetter(War::b),
				Codec.LONG.fieldOf("wager").forGetter(War::wager),
				Codec.LONG.fieldOf("started").forGetter(War::started)
		).apply(instance, War::new));

		boolean involves(UUID crew) {
			return a.equals(crew) || b.equals(crew);
		}

		UUID other(UUID crew) {
			return a.equals(crew) ? b : a;
		}
	}

	public static final AttachmentType<List<War>> WARS = AttachmentRegistry.create(
			OnePieceMod.id("sea_wars"), builder -> builder.persistent(War.CODEC.listOf()));
	/** Berries owed to players who were offline when a battle ended (wager payouts and refunds). */
	public static final AttachmentType<Map<UUID, Long>> BERRIES_OWED = AttachmentRegistry.create(
			OnePieceMod.id("sea_war_berries"), builder -> builder.persistent(Codec.unboundedMap(UUIDUtil.STRING_CODEC, Codec.LONG)));

	private record Challenge(long until, long wager) {
	}

	/** challenged captain -> (challenging captain -> challenge). Not saved: challenges are quick. */
	private static final Map<UUID, Map<UUID, Challenge>> CHALLENGES = new HashMap<>();
	/** A ship being taken by boarders -> game tick they started holding her deck. */
	private static final Map<ShipEntity, Long> CAPTURING = new WeakHashMap<>();
	/** A battle side with nobody online -> game tick it was first seen empty. Key: captain id. */
	private static final Map<UUID, Long> EMPTY_SINCE = new HashMap<>();
	/** One hull bar per side of a battle. Key: captain id. */
	private static final Map<UUID, ServerBossEvent> BARS = new HashMap<>();
	/** "crewA|crewB" (sorted) -> game tick the next bounty reward for a battle between them is allowed. Not saved. */
	private static final Map<String, Long> REWARD_COOLDOWN = new HashMap<>();

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 20 == 0) {
				tick(server);
			}
		});
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> server.execute(() -> payOwed(handler.getPlayer())));
	}

	// ---- Looking up battles ----

	public static List<War> wars(MinecraftServer server) {
		return server.overworld().getAttachedOrElse(WARS, List.of());
	}

	private static void save(MinecraftServer server, List<War> wars) {
		server.overworld().setAttached(WARS, new ArrayList<>(wars));
	}

	@Nullable
	public static War warOf(MinecraftServer server, @Nullable UUID crew) {
		if (crew == null) {
			return null;
		}
		for (War war : wars(server)) {
			if (war.involves(crew)) {
				return war;
			}
		}
		return null;
	}

	public static boolean crewsAtWar(MinecraftServer server, @Nullable UUID crewA, @Nullable UUID crewB) {
		if (crewA == null || crewB == null || crewA.equals(crewB)) {
			return false;
		}
		War war = warOf(server, crewA);
		return war != null && war.involves(crewB);
	}

	/** True if these two (players, crewmates, guards) fight for crews that are in a sea battle with each other. */
	public static boolean atWar(MinecraftServer server, Entity a, Entity b) {
		return crewsAtWar(server, PlayerCrews.crewKey(server, a), PlayerCrews.crewKey(server, b));
	}

	/** True if the two ships belong to crews in a sea battle with each other. Gun crews fire on such ships. */
	public static boolean isRivalShip(ShipEntity ship, ShipEntity other) {
		if (ship == other || !(ship.level() instanceof ServerLevel level)) {
			return false;
		}
		return crewsAtWar(level.getServer(), ship.getAttached(SharedShips.OWNER), other.getAttached(SharedShips.OWNER));
	}

	// ---- Rules for cannon fire on player ships ----

	/**
	 * Called by ShipHull.damage. A crew's ship can't be hurt by its own crew or allies, and other players can only
	 * hurt it during a sea battle (unless the server turned on open_sea_pvp). Monsters, storms and AI ships always can.
	 */
	public static boolean allowHullDamage(ShipEntity target, @Nullable ServerPlayer attacker, @Nullable ShipEntity fromShip) {
		UUID owner = target.getAttached(SharedShips.OWNER);
		if (owner == null || !(target.level() instanceof ServerLevel level)) {
			return true;
		}
		MinecraftServer server = level.getServer();
		UUID from = attacker != null ? PlayerCrews.crewKey(server, attacker) : fromShip != null ? fromShip.getAttached(SharedShips.OWNER) : null;
		if (from == null) {
			return true;
		}
		if (from.equals(owner) || (attacker != null && owner.equals(attacker.getUUID())) || PlayerCrews.allied(server, from, owner)) {
			return false;
		}
		if (crewsAtWar(server, from, owner) || ModConfig.openSeaPvp()) {
			return true;
		}
		if (attacker != null) {
			attacker.sendOverlayMessage(Component.literal("That ship sails under the " + PlayerCrews.crewName(server, owner)
					+ ". Challenge them first: /crew challenge <their captain>").withStyle(ChatFormatting.YELLOW));
		}
		return false;
	}

	/** Called by ShipCombat.dockBlockedReason: no dropping anchor (and a fresh hull) with the enemy crew close by. */
	@Nullable
	public static String dockBlockedReason(ShipEntity ship) {
		if (!(ship.level() instanceof ServerLevel level)) {
			return null;
		}
		MinecraftServer server = level.getServer();
		UUID owner = ship.getAttached(SharedShips.OWNER);
		War war = warOf(server, owner);
		if (war == null) {
			return null;
		}
		UUID rival = war.other(owner);
		for (ServerPlayer player : level.players()) {
			if (player.distanceToSqr(ship) < DOCK_BLOCK_RANGE * DOCK_BLOCK_RANGE && rival.equals(PlayerCrews.crewKey(server, player))) {
				return "You're in a sea battle with the " + PlayerCrews.crewName(server, rival)
						+ "! Win, sail " + (int) DOCK_BLOCK_RANGE + " blocks away from them, or /crew surrender.";
			}
		}
		return null;
	}

	// ---- Boarding a rival crew's ship ----

	/**
	 * Right-clicking a ship of a crew you're at war with: once her hull is below half, you (and up to 4 following
	 * crewmates) swing aboard. Returns true if this was a boarding attempt (handled, with a message), false if not at war.
	 */
	public static boolean tryBoard(ShipEntity ship, ServerPlayer player, UUID owner) {
		return tryBoard(ship, player, owner, BOARD_RANGE);
	}

	/** Same, from further off (a Boarding Hook reaches 24 blocks). */
	public static boolean tryBoard(ShipEntity ship, ServerPlayer player, UUID owner, double range) {
		MinecraftServer server = player.level().getServer();
		if (!crewsAtWar(server, owner, PlayerCrews.crewKey(server, player))) {
			return false;
		}
		if (ShipEntity.aboard(player) == ship) {
			player.sendOverlayMessage(Component.literal("You're on her deck! Clear her crew off to take her.").withStyle(ChatFormatting.GOLD));
			return true;
		}
		if (ship.sinking) {
			return true;
		}
		float hull = ShipHull.get(ship);
		float max = ShipHull.max(ship);
		if (hull > max * 0.5f && !player.isCreative()) {
			player.sendOverlayMessage(Component.literal("Her hull is too strong to board (" + Math.round(100 * hull / max)
					+ "%). Cannon her below 50% first!").withStyle(ChatFormatting.YELLOW));
			return true;
		}
		if (player.distanceToSqr(ship) > Math.pow(ship.getBbWidth() / 2 + range, 2)) {
			player.sendOverlayMessage(Component.literal("Get closer to board her!").withStyle(ChatFormatting.YELLOW));
			return true;
		}
		List<CrewmateEntity> party = new ArrayList<>(player.level().getEntitiesOfClass(CrewmateEntity.class, player.getBoundingBox().inflate(PARTY_RANGE),
				mate -> mate.isAlive() && !mate.isKnockedOut() && mate.getMode() == CrewMode.FOLLOW && player.getUUID().equals(mate.getCaptainId())));
		party.sort(java.util.Comparator.comparingDouble(mate -> mate.distanceToSqr(player)));
		ship.boardOnDeck(player);
		for (int i = 0; i < Math.min(PARTY_SIZE, party.size()); i++) {
			ship.boardOnDeck(party.get(i));
			party.get(i).getNavigation().stop();
		}
		player.level().playSound(null, player.blockPosition(), com.onepiecemod.sound.WorldSounds.BOARDING,
				net.minecraft.sounds.SoundSource.PLAYERS, 1.5f, 1.0f);
		PlayerCrews.tell(server, owner, Component.literal(player.getName().getString() + " has boarded your ship! Drive them off!")
				.withStyle(ChatFormatting.RED));
		player.sendSystemMessage(Component.literal("You boarded the " + possessive(PlayerCrews.crewName(server, owner))
				+ " ship! Hold her deck with none of her crew aboard for " + CAPTURE_TICKS / 20 + " seconds to take her.")
				.withStyle(ChatFormatting.GOLD));
		return true;
	}

	// ---- Challenges ----

	/** challenger and target are both captain ids. Returns a problem, or null if the challenge was sent. */
	@Nullable
	static String challenge(MinecraftServer server, ServerPlayer sender, UUID challenger, UUID target, long wager) {
		if (challenger.equals(target)) {
			return "You can't challenge your own crew.";
		}
		if (PlayerCrews.allied(server, challenger, target)) {
			return "You're allied with the " + PlayerCrews.crewName(server, target) + ". End the alliance first with /crew unally.";
		}
		if (warOf(server, challenger) != null) {
			return "Your crew is already in a sea battle. Finish it first (/crew battle).";
		}
		if (warOf(server, target) != null) {
			return "The " + PlayerCrews.crewName(server, target) + " are already in a sea battle.";
		}
		if (wager > 0 && sender.isCreative()) {
			return "Creative-mode players can't wager Berries (they'd win Berries they never put up). Switch to survival or drop the wager.";
		}
		if (wager > 0 && berries(sender.getInventory()) < wager) {
			return "You need " + wager + " Berries on you to wager that much.";
		}
		CHALLENGES.computeIfAbsent(target, id -> new HashMap<>()).put(challenger, new Challenge(server.getTickCount() + CHALLENGE_TICKS, wager));
		String from = PlayerCrews.crewName(server, challenger);
		String stake = wager > 0 ? " Each side puts up " + wager + " Berries; the winner takes all." : "";
		Component call = Component.literal("[Sea Battle] The " + from + " challenge your crew to a sea battle!" + stake
				+ " Your captain or first mate types /crew challenge accept " + nameOf(server, challenger) + " within 3 minutes.")
				.withStyle(ChatFormatting.GOLD);
		PlayerCrews.tell(server, target, call);
		PlayerCrews.tell(server, challenger, Component.literal("Challenge sent to the " + PlayerCrews.crewName(server, target) + "." + stake)
				.withStyle(ChatFormatting.AQUA));
		return null;
	}

	/** Names of captains who challenged this crew, for tab completion. */
	static List<String> challengers(MinecraftServer server, UUID target) {
		List<String> names = new ArrayList<>();
		Map<UUID, Challenge> mine = CHALLENGES.getOrDefault(target, Map.of());
		for (Map.Entry<UUID, Challenge> entry : mine.entrySet()) {
			if (entry.getValue().until() > server.getTickCount()) {
				names.add(nameOf(server, entry.getKey()));
			}
		}
		return names;
	}

	@Nullable
	static String accept(MinecraftServer server, ServerPlayer sender, UUID target, String challengerName) {
		Map<UUID, Challenge> mine = CHALLENGES.getOrDefault(target, Map.of());
		UUID challenger = null;
		for (UUID id : mine.keySet()) {
			if (nameOf(server, id).equalsIgnoreCase(challengerName)) {
				challenger = id;
			}
		}
		Challenge challenge = challenger == null ? null : mine.get(challenger);
		if (challenge == null || challenge.until() <= server.getTickCount()) {
			return "No challenge from that captain, or it ran out. Ask them for a new one.";
		}
		if (warOf(server, challenger) != null || warOf(server, target) != null) {
			return "One of the crews is already in a sea battle.";
		}
		long wager = challenge.wager();
		ServerPlayer challengerOfficer = onlineOfficer(server, challenger);
		if (wager > 0) {
			if (challengerOfficer == null) {
				return "The challenging crew's captain (or first mate) has to be online to put up their Berries.";
			}
			if (sender.isCreative() || challengerOfficer.isCreative()) {
				return "Wagers need both officers in survival mode, so nobody wins Berries they never put up.";
			}
			if (berries(sender.getInventory()) < wager) {
				return "You need " + wager + " Berries on you to accept this wager.";
			}
			if (berries(challengerOfficer.getInventory()) < wager) {
				return "The " + PlayerCrews.crewName(server, challenger) + " can't cover their wager any more.";
			}
			takeBerries(sender.getInventory(), wager);
			takeBerries(challengerOfficer.getInventory(), wager);
		}
		mine.remove(challenger);
		List<War> wars = new ArrayList<>(wars(server));
		wars.add(new War(challenger, target, wager, server.overworld().getGameTime()));
		save(server, wars);

		server.getPlayerList().broadcastSystemMessage(Component.literal("[News Coo] The " + PlayerCrews.crewName(server, challenger)
				+ " and the " + PlayerCrews.crewName(server, target) + " are at war on the open sea!").withStyle(ChatFormatting.GOLD), false);
		Component rules = Component.literal("Sea battle! Sink their ship, or batter her below half hull, board her and hold her deck. "
				+ "Your gun crews fire on their ships. 20 minutes; /crew battle shows how it's going, /crew surrender gives up.")
				.withStyle(ChatFormatting.YELLOW);
		PlayerCrews.tell(server, challenger, rules);
		PlayerCrews.tell(server, target, rules);
		return null;
	}

	/** A crew in a battle broke up (its captain disbanded): the other side wins. Call before the crew is removed. */
	static void crewGone(MinecraftServer server, UUID captain) {
		War war = warOf(server, captain);
		if (war != null) {
			end(server, war, war.other(captain), "The " + PlayerCrews.crewName(server, captain) + " broke up mid-battle");
		}
	}

	@Nullable
	static String surrender(MinecraftServer server, UUID crew) {
		War war = warOf(server, crew);
		if (war == null) {
			return "Your crew isn't in a sea battle.";
		}
		end(server, war, war.other(crew), "The " + PlayerCrews.crewName(server, crew) + " surrendered");
		return null;
	}

	static void status(MinecraftServer server, ServerPlayer player, UUID crew) {
		War war = warOf(server, crew);
		if (war == null) {
			player.sendSystemMessage(Component.literal("Your crew isn't in a sea battle. Start one with /crew challenge <captain> [berries].")
					.withStyle(ChatFormatting.YELLOW));
			return;
		}
		long left = Math.max(0, MAX_TICKS - (server.overworld().getGameTime() - war.started())) / 20;
		player.sendSystemMessage(Component.literal("=== Sea battle: " + PlayerCrews.crewName(server, war.a()) + " vs "
				+ PlayerCrews.crewName(server, war.b()) + " ===").withStyle(ChatFormatting.GOLD));
		for (UUID side : List.of(war.a(), war.b())) {
			ShipEntity ship = flagship(server, side);
			String hull = ship == null ? "no ship at sea" : ship.getName().getString() + ", hull " + Math.round(ShipHull.get(ship)) + " / " + Math.round(ShipHull.max(ship));
			player.sendSystemMessage(Component.literal(PlayerCrews.crewName(server, side) + ": " + online(server, side).size() + " online, " + hull)
					.withStyle(ChatFormatting.WHITE));
		}
		player.sendSystemMessage(Component.literal((war.wager() > 0 ? "Wager: " + war.wager() + " Berries each. " : "") + left / 60 + " min "
				+ left % 60 + " s left.").withStyle(ChatFormatting.GRAY));
	}

	// ---- Every second ----

	private static void tick(MinecraftServer server) {
		List<War> wars = wars(server);
		if (wars.isEmpty()) {
			if (!BARS.isEmpty()) {
				BARS.values().forEach(ServerBossEvent::removeAllPlayers);
				BARS.clear();
			}
			return;
		}
		long now = server.overworld().getGameTime();
		for (War war : new ArrayList<>(wars)) {
			if (!wars(server).contains(war)) {
				continue;
			}
			if (now - war.started() > MAX_TICKS) {
				end(server, war, null, "Time ran out");
				continue;
			}
			UUID loser = sunkSide(war);
			if (loser != null) {
				end(server, war, war.other(loser), "The " + possessive(PlayerCrews.crewName(server, loser)) + " ship went down");
				continue;
			}
			UUID taken = capturedSide(server, war, now);
			if (taken != null) {
				end(server, war, war.other(taken), "The " + possessive(PlayerCrews.crewName(server, taken)) + " ship was taken by boarders");
				continue;
			}
			if (abandoned(server, war.a(), now) || abandoned(server, war.b(), now)) {
				end(server, war, null, "One crew left the sea");
				continue;
			}
			updateBars(server, war);
		}
	}

	/** A side whose ship is sinking right now, or null. */
	@Nullable
	private static UUID sunkSide(War war) {
		for (ShipEntity ship : ShipCombat.loadedShips()) {
			UUID owner = ship.getAttached(SharedShips.OWNER);
			if (ship.sinking && owner != null && war.involves(owner)) {
				return owner;
			}
		}
		return null;
	}

	/** A side whose ship has been held by boarders long enough, or null. Also tells the boarders how it's going. */
	@Nullable
	private static UUID capturedSide(MinecraftServer server, War war, long now) {
		for (ShipEntity ship : ShipCombat.loadedShips()) {
			UUID owner = ship.getAttached(SharedShips.OWNER);
			if (owner == null || !war.involves(owner) || ship.sinking || ship.isRemoved()) {
				continue;
			}
			UUID rival = war.other(owner);
			List<ServerPlayer> boarders = new ArrayList<>();
			int defenders = 0;
			for (ServerPlayer player : ShipEntity.playersAboard(ship)) {
				UUID key = PlayerCrews.crewKey(server, player);
				if (rival.equals(key) && player.isAlive()) {
					boarders.add(player);
				} else if (owner.equals(key) && player.isAlive()) {
					defenders++;
				}
			}
			for (Entity walker : ShipDecks.onDeck(ship)) {
				if (walker instanceof CrewmateEntity mate && mate.isAlive() && !mate.isKnockedOut() && owner.equals(PlayerCrews.crewKey(server, mate))) {
					defenders++;
				}
			}
			boolean weak = ShipHull.get(ship) <= ShipHull.max(ship) * 0.5f;
			if (boarders.isEmpty() || defenders > 0 || !weak) {
				CAPTURING.remove(ship);
				continue;
			}
			long since = CAPTURING.computeIfAbsent(ship, s -> now);
			long left = (CAPTURE_TICKS - (now - since)) / 20;
			if (left <= 0) {
				CAPTURING.remove(ship);
				return owner;
			}
			for (ServerPlayer boarder : boarders) {
				boarder.sendOverlayMessage(Component.literal("Taking her: " + left + " s").withStyle(ChatFormatting.GOLD));
			}
		}
		return null;
	}

	private static boolean abandoned(MinecraftServer server, UUID side, long now) {
		if (!online(server, side).isEmpty()) {
			EMPTY_SINCE.remove(side);
			return false;
		}
		return now - EMPTY_SINCE.computeIfAbsent(side, s -> now) > OFFLINE_TICKS;
	}

	/** Ends a battle. winner null = a draw: the wagers go back. */
	private static void end(MinecraftServer server, War war, @Nullable UUID winner, String why) {
		List<War> wars = new ArrayList<>(wars(server));
		wars.remove(war);
		save(server, wars);
		EMPTY_SINCE.remove(war.a());
		EMPTY_SINCE.remove(war.b());
		removeBar(war.a());
		removeBar(war.b());

		if (winner == null) {
			if (war.wager() > 0) {
				payCrew(server, war.a(), war.wager());
				payCrew(server, war.b(), war.wager());
			}
			server.getPlayerList().broadcastSystemMessage(Component.literal("[News Coo] " + why + ": the sea battle between the "
					+ PlayerCrews.crewName(server, war.a()) + " and the " + PlayerCrews.crewName(server, war.b()) + " ended in a draw.")
					.withStyle(ChatFormatting.GOLD), false);
			return;
		}
		UUID loser = war.other(winner);
		long now = server.overworld().getGameTime();
		String pair = war.a().compareTo(war.b()) < 0 ? war.a() + "|" + war.b() : war.b() + "|" + war.a();
		REWARD_COOLDOWN.values().removeIf(until -> until < now);
		boolean earned = now - war.started() >= MIN_FIGHT_TICKS && !REWARD_COOLDOWN.containsKey(pair);
		if (earned) {
			REWARD_COOLDOWN.put(pair, now + REWARD_COOLDOWN_TICKS);
			long reward = Math.max(MIN_REWARD, CrewBounties.crewBounty(server, loser) / 10);
			for (ServerPlayer player : online(server, winner)) {
				Bounty.raise(player, reward, "You won a sea battle against the " + PlayerCrews.crewName(server, loser) + "!", false);
				AdvancementFeature.grant(player, "journey/win_naval_battle");
			}
		}
		if (war.wager() > 0) {
			payCrew(server, winner, war.wager() * 2);
		}
		server.getPlayerList().broadcastSystemMessage(Component.literal("[News Coo] " + why + "! The " + PlayerCrews.crewName(server, winner)
				+ " won the sea battle against the " + PlayerCrews.crewName(server, loser) + "!").withStyle(ChatFormatting.GOLD), false);
		String spoils = war.wager() > 0 ? " You took " + war.wager() * 2 + " Berries in wagers." : "";
		PlayerCrews.tell(server, winner, Component.literal(earned ? "Victory! Your bounty rose." + spoils
				: "Victory!" + spoils + " The Marines shrug it off, though: a battle that short (or a rematch this soon) adds no bounty.")
				.withStyle(ChatFormatting.GREEN));
		PlayerCrews.tell(server, loser, Component.literal("Defeat... Train harder and challenge them again.").withStyle(ChatFormatting.RED));
	}

	// ---- Hull bars: each side's ship, shown to both crews ----

	private static void updateBars(MinecraftServer server, War war) {
		List<ServerPlayer> viewers = new ArrayList<>(online(server, war.a()));
		viewers.addAll(online(server, war.b()));
		for (UUID side : List.of(war.a(), war.b())) {
			ServerBossEvent bar = BARS.computeIfAbsent(side, s -> new ServerBossEvent(UUID.randomUUID(), Component.empty(),
					side.equals(war.a()) ? BossEvent.BossBarColor.BLUE : BossEvent.BossBarColor.RED, BossEvent.BossBarOverlay.NOTCHED_10));
			ShipEntity ship = flagship(server, side);
			if (ship == null) {
				bar.setName(Component.literal(PlayerCrews.crewName(server, side) + "  (no ship at sea)"));
				bar.setProgress(1f);
			} else {
				float max = ShipHull.max(ship);
				float hull = Math.max(0, ShipHull.get(ship));
				bar.setName(Component.literal(PlayerCrews.crewName(server, side) + "  " + Math.round(hull) + " / " + Math.round(max)));
				bar.setProgress(max <= 0 ? 0 : Math.min(1f, hull / max));
			}
			for (ServerPlayer player : new ArrayList<>(bar.getPlayers())) {
				if (!viewers.contains(player)) {
					bar.removePlayer(player);
				}
			}
			for (ServerPlayer player : viewers) {
				if (!bar.getPlayers().contains(player)) {
					bar.addPlayer(player);
				}
			}
		}
	}

	private static void removeBar(UUID side) {
		ServerBossEvent bar = BARS.remove(side);
		if (bar != null) {
			bar.removeAllPlayers();
		}
	}

	/** The crew's biggest ship at sea right now, or null. */
	@Nullable
	private static ShipEntity flagship(MinecraftServer server, UUID side) {
		ShipEntity best = null;
		for (ShipEntity ship : ShipCombat.loadedShips()) {
			if (!ship.isRemoved() && side.equals(ship.getAttached(SharedShips.OWNER))
					&& (best == null || ship.getLayout().size() > best.getLayout().size())) {
				best = ship;
			}
		}
		return best;
	}

	// ---- Crews, Berries ----

	/** Online players of a crew, captain included. */
	static List<ServerPlayer> online(MinecraftServer server, UUID captain) {
		List<ServerPlayer> players = new ArrayList<>();
		ServerPlayer leader = server.getPlayerList().getPlayer(captain);
		if (leader != null) {
			players.add(leader);
		}
		PirateCrew crew = PlayerCrews.get(server, captain);
		if (crew != null) {
			for (UUID member : crew.members) {
				ServerPlayer player = server.getPlayerList().getPlayer(member);
				if (player != null) {
					players.add(player);
				}
			}
		}
		return players;
	}

	@Nullable
	private static ServerPlayer onlineOfficer(MinecraftServer server, UUID captain) {
		for (ServerPlayer player : online(server, captain)) {
			if (captain.equals(PlayerRoles.officerOf(server, player))) {
				return player;
			}
		}
		return null;
	}

	/** "Usopp Pirates" -> "Usopp Pirates'", "Red Force" -> "Red Force's". */
	static String possessive(String name) {
		return name.endsWith("s") ? name + "'" : name + "'s";
	}

	static String nameOf(MinecraftServer server, UUID captain) {
		ServerPlayer player = server.getPlayerList().getPlayer(captain);
		if (player != null) {
			return player.getName().getString();
		}
		PirateCrew crew = PlayerCrews.get(server, captain);
		return crew != null ? crew.nameOf(captain) : "?";
	}

	private static int berries(Inventory inventory) {
		int count = 0;
		for (int slot = 0; slot < inventory.getContainerSize(); slot++) {
			ItemStack stack = inventory.getItem(slot);
			if (stack.is(CharacterFeature.BERRY)) {
				count += stack.getCount();
			}
		}
		return count;
	}

	private static void takeBerries(Inventory inventory, long amount) {
		for (int slot = 0; slot < inventory.getContainerSize() && amount > 0; slot++) {
			ItemStack stack = inventory.getItem(slot);
			if (stack.is(CharacterFeature.BERRY)) {
				int take = (int) Math.min(amount, stack.getCount());
				stack.shrink(take);
				amount -= take;
			}
		}
	}

	/** Pays Berries to the crew's captain, or their first mate, or saves them for the captain's next login. */
	private static void payCrew(MinecraftServer server, UUID captain, long amount) {
		ServerPlayer officer = onlineOfficer(server, captain);
		if (officer != null) {
			giveBerries(officer, amount);
			return;
		}
		Map<UUID, Long> owed = new HashMap<>(server.overworld().getAttachedOrElse(BERRIES_OWED, Map.of()));
		owed.merge(captain, amount, Long::sum);
		server.overworld().setAttached(BERRIES_OWED, owed);
	}

	private static void payOwed(ServerPlayer player) {
		MinecraftServer server = player.level().getServer();
		Map<UUID, Long> owed = server.overworld().getAttachedOrElse(BERRIES_OWED, Map.of());
		Long amount = owed.get(player.getUUID());
		if (amount == null || amount <= 0) {
			return;
		}
		Map<UUID, Long> rest = new HashMap<>(owed);
		rest.remove(player.getUUID());
		server.overworld().setAttached(BERRIES_OWED, rest);
		giveBerries(player, amount);
		player.sendSystemMessage(Component.literal("You collected " + amount + " Berries from a sea battle while you were away.")
				.withStyle(ChatFormatting.GOLD));
	}

	private static void giveBerries(ServerPlayer player, long amount) {
		while (amount > 0) {
			int count = (int) Math.min(amount, 64);
			amount -= count;
			ItemStack stack = new ItemStack(CharacterFeature.BERRY, count);
			if (!player.getInventory().add(stack)) {
				player.drop(stack, false, Prediction.SERVER_ONLY);
			}
		}
	}
}
