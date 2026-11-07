package com.onepiecemod.worldevent;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import org.jetbrains.annotations.Nullable;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.bounty.MarineHunters;
import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.empire.EmpireData;
import com.onepiecemod.empire.Title;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.npc.NpcFeature;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.shipcombat.SeaEncounters;
import com.onepiecemod.shipcombat.ShipBrain;
import com.onepiecemod.sound.ModSounds;

/**
 * The Four Emperors' territories, and how each Emperor feels about you (your "standing", -100 to 100).
 *
 *  Kaido (Beasts Pirates):      Wano, Onigashima. Respects strength: his Headliners challenge you to a duel.
 *  Big Mom (Big Mom Pirates):   Whole Cake, Cacao Island, Fish-Man Island. Demands tribute in Berries.
 *  Blackbeard (Blackbeard P.):  Hachinosu. Demands a cut of your Berries.
 *  Shanks (Red Hair Pirates):   Elbaph. Keeps the peace: no demands, but don't make trouble.
 *
 * Standing:  Hostile (-30 or lower): war parties hunt you, their warships attack at sea, and at -70 a commander
 *            (King, Katakuri) comes for you.  Wary: demands, duels, warnings.  Friendly (30+): their crews leave you
 *            alone and sometimes share spoils.  Conquered (you beat that Emperor): the crew bows and pays YOU tribute.
 * Killing their crew lowers it (-6, commanders -25). Paying tribute (/tribute) and winning duels raise it.
 * Emperors (title holders) are rivals: the other Emperors treat them as hostile unless conquered.
 */
public class EmperorTerritories {
	public enum Mood { HOSTILE, WARY, FRIENDLY, CONQUERED }

	private enum Way { DUEL, TRIBUTE, PEACE }

	public record Territory(String id, String emperor, String crew, Set<String> biomes, List<String> kits, @Nullable String leaderKit,
			@Nullable String commander, String crewTitle, Way way, int startStanding, ChatFormatting color) {
	}

	private static final List<Territory> TERRITORIES = List.of(
			new Territory("kaido", "Kaido", "Beasts Pirates", Set.of("onepiece:wano", "onepiece:onigashima"),
					List.of("gifter"), "headliner", "king", "", Way.DUEL, 0, ChatFormatting.DARK_PURPLE),
			new Territory("big_mom", "Big Mom", "Big Mom Pirates", Set.of("onepiece:whole_cake", "onepiece:cacao_island", "onepiece:fishman_reef"),
					List.of("pirate", "pirate_gunner"), "pirate_captain", "katakuri", "Big Mom Pirates", Way.TRIBUTE, 0, ChatFormatting.LIGHT_PURPLE),
			new Territory("blackbeard", "Blackbeard", "Blackbeard Pirates", Set.of("onepiece:hachinosu"),
					List.of("blackbeard_pirate"), null, null, "", Way.TRIBUTE, -10, ChatFormatting.DARK_GRAY),
			new Territory("shanks", "Shanks", "Red Hair Pirates", Set.of("onepiece:elbaph"),
					List.of("pirate", "pirate_gunner"), "pirate_captain", null, "Red Hair Pirates", Way.PEACE, 20, ChatFormatting.RED)
	);

	public static final String CREW_TAG = "onepiece_emperor_crew_";
	private static final String DUEL_TAG = "onepiece_emperor_duel";

	/** Standing with each Emperor, by territory id. Kept on death. */
	public static final AttachmentType<Map<String, Integer>> STANDING = AttachmentRegistry.create(
			OnePieceMod.id("emperor_standing"),
			builder -> builder.persistent(Codec.unboundedMap(Codec.STRING, Codec.INT)).copyOnDeath()
	);

	private static final int CHECK_EVERY = 20;
	private static final int ACTION_EVERY = 20 * 60;
	private static final int DEMAND_TIME = 20 * 90;
	private static final int DUEL_TIME = 20 * 180;
	private static final int COMMANDER_BREAK = 20 * 60 * 20;

	/** What's going on with each player (in memory). */
	private static class Visit {
		String territory;
		long nextAction;
		long demandUntil;
		int demandAmount;
		UUID duelist;
		long duelUntil;
		long nextCommander;
	}

	private static final Map<UUID, Visit> VISITS = new HashMap<>();

	static void initialize() {
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (!(source.getEntity() instanceof ServerPlayer player)) {
				return;
			}
			Territory territory = crewOf(entity);
			if (territory == null) {
				return;
			}
			Visit visit = VISITS.get(player.getUUID());
			if (visit != null && entity.getUUID().equals(visit.duelist)) {
				visit.duelist = null;
				change(player, territory, 15);
				WorldNews.call(player, territory.emperor(), ("kaido".equals(territory.id()) ? "Uororororo! " : "")
						+ "Not bad. You've got strength. My men will remember that.", territory.color());
				return;
			}
			if (mood(player, territory) == Mood.CONQUERED) {
				return;
			}
			boolean commander = entity instanceof CharacterEntity;
			change(player, territory, commander ? -25 : -6);
		});
	}

	// ---- Who belongs to whom ----

	@Nullable
	static Territory byId(String id) {
		for (Territory territory : TERRITORIES) {
			if (territory.id().equals(id)) {
				return territory;
			}
		}
		return null;
	}

	static List<Territory> all() {
		return TERRITORIES;
	}

	@Nullable
	static Territory territoryAt(ServerLevel level, BlockPos pos) {
		if (level.dimension() != Level.OVERWORLD) {
			return null;
		}
		String biome = level.getBiome(pos).unwrapKey().map(ResourceKey::identifier).map(Object::toString).orElse("");
		for (Territory territory : TERRITORIES) {
			if (territory.biomes().contains(biome)) {
				return territory;
			}
		}
		return null;
	}

	/** Which Emperor's crew this is (by our tag, or by the NPC's crew name), or null. */
	@Nullable
	static Territory crewOf(Entity entity) {
		for (Territory territory : TERRITORIES) {
			if (entity.entityTags().contains(CREW_TAG + territory.id())) {
				return territory;
			}
			if (entity instanceof HumanNpc npc && !npc.isMarineSide() && territory.crew().equals(npc.getCrew())) {
				return territory;
			}
			if (entity instanceof CharacterEntity character && character.getCharacterId().equals(territory.commander())) {
				return territory;
			}
		}
		return null;
	}

	// ---- Standing ----

	public static int standing(Player player, Territory territory) {
		return player.getAttachedOrElse(STANDING, Map.of()).getOrDefault(territory.id(), territory.startStanding());
	}

	static void set(Player player, Territory territory, int value) {
		Map<String, Integer> map = new HashMap<>(player.getAttachedOrElse(STANDING, Map.of()));
		map.put(territory.id(), Mth.clamp(value, -100, 100));
		player.setAttached(STANDING, map);
	}

	static void change(ServerPlayer player, Territory territory, int by) {
		Mood before = mood(player, territory);
		set(player, territory, standing(player, territory) + by);
		Mood after = mood(player, territory);
		if (after != before) {
			String text = switch (after) {
				case HOSTILE -> territory.emperor() + " has marked you as an enemy. The " + territory.crew() + " will hunt you in their waters.";
				case WARY -> territory.emperor() + "'s crew is watching you.";
				case FRIENDLY -> territory.emperor() + " counts you as a friend. The " + territory.crew() + " will let you be.";
				case CONQUERED -> "";
			};
			if (!text.isEmpty()) {
				player.sendSystemMessage(Component.literal(text).withStyle(territory.color()));
			}
		}
	}

	public static Mood mood(Player player, Territory territory) {
		if (CharacterAttachments.has(player, CharacterAttachments.BOSSES_DEFEATED, territory.id())) {
			return Mood.CONQUERED;
		}
		int value = standing(player, territory);
		// Another Emperor in their sea is a rival (Shanks is only wary of them).
		if (EmpireData.title(player).atLeast(Title.EMPEROR)) {
			value = Math.min(value, territory.way() == Way.PEACE ? 0 : -40);
		}
		return value <= -30 ? Mood.HOSTILE : value >= 30 ? Mood.FRIENDLY : Mood.WARY;
	}

	// ---- Every second ----

	static void tick(MinecraftServer server) {
		if (server.getTickCount() % CHECK_EVERY != 0) {
			return;
		}
		ServerLevel level = server.overworld();
		long now = level.getGameTime();
		for (ServerPlayer player : level.players()) {
			if (player.isSpectator()) {
				continue;
			}
			Visit visit = VISITS.computeIfAbsent(player.getUUID(), id -> new Visit());
			Territory territory = territoryAt(level, player.blockPosition());
			String id = territory == null ? null : territory.id();
			if (!java.util.Objects.equals(id, visit.territory)) {
				Territory old = visit.territory == null ? null : byId(visit.territory);
				leave(player, visit, old);
				visit.territory = id;
				if (territory != null) {
					enter(player, visit, territory, now);
				}
			}
			if (territory == null || player.isCreative() || level.getDifficulty() == Difficulty.PEACEFUL) {
				continue;
			}
			Mood mood = mood(player, territory);
			if (mood == Mood.FRIENDLY || mood == Mood.CONQUERED) {
				calmCrew(level, player, territory);
			}
			if (visit.demandUntil > 0 && now >= visit.demandUntil) {
				visit.demandUntil = 0;
				refuse(player, territory);
			}
			if (visit.duelist != null && now >= visit.duelUntil) {
				Entity duelist = level.getEntity(visit.duelist);
				if (duelist != null) {
					duelist.discard();
				}
				visit.duelist = null;
				WorldNews.call(player, territory.crew(), "Ha! You ran from a duel? Kaido doesn't need cowards.", territory.color());
				change(player, territory, -5);
			}
			if (now >= visit.nextAction) {
				visit.nextAction = now + ACTION_EVERY + player.getRandom().nextInt(ACTION_EVERY);
				act(level, player, visit, territory, mood, now);
			}
		}
		VISITS.keySet().removeIf(uuid -> server.getPlayerList().getPlayer(uuid) == null);
	}

	private static void enter(ServerPlayer player, Visit visit, Territory territory, long now) {
		visit.nextAction = now + 20 * 20; // Something happens about 20 s after you arrive.
		Mood mood = mood(player, territory);
		String line = switch (mood) {
			case HOSTILE -> "The " + territory.crew() + " want your head. Watch your back.";
			case WARY -> "The " + territory.crew() + " are watching you.";
			case FRIENDLY -> "The " + territory.crew() + " wave you through. You're welcome here.";
			case CONQUERED -> "You beat " + territory.emperor() + ". The " + territory.crew() + " bow as you pass.";
		};
		player.sendSystemMessage(Component.literal("You've entered " + territory.emperor() + "'s territory. ").withStyle(territory.color(), ChatFormatting.BOLD)
				.append(Component.literal(line).withStyle(territory.color())));
		player.sendOverlayMessage(Component.literal(territory.emperor() + "'s territory").withStyle(territory.color()));
		ModSounds.play(player, ModSounds.DEN_DEN_MUSHI_CALL, 0.4f);
	}

	private static void leave(ServerPlayer player, Visit visit, @Nullable Territory old) {
		if (old == null) {
			return;
		}
		if (visit.demandUntil > 0) {
			visit.demandUntil = 0;
			refuse(player, old);
		}
		if (visit.duelist != null && player.level() instanceof ServerLevel level) {
			Entity duelist = level.getEntity(visit.duelist);
			if (duelist != null) {
				duelist.discard();
			}
			visit.duelist = null;
			change(player, old, -5);
		}
		player.sendOverlayMessage(Component.literal("You've left " + old.emperor() + "'s territory").withStyle(ChatFormatting.GRAY));
	}

	private static void act(ServerLevel level, ServerPlayer player, Visit visit, Territory territory, Mood mood, long now) {
		RandomSource random = player.getRandom();
		switch (mood) {
			case HOSTILE -> {
				boolean atSea = ShipEntity.aboard(player) != null;
				if (atSea) {
					ShipEntity ship = SeaEncounters.spawnAt(level, player.position(), player.getYRot(), 90, ShipBrain.Faction.PIRATE, 4, null);
					if (ship != null) {
						ship.setCustomName(Component.literal(territory.crew() + " Warship"));
						WorldNews.call(player, territory.crew(), "You're in " + territory.emperor() + "'s waters. Sink them!", territory.color());
					}
				} else {
					warParty(level, player, territory, 3 + random.nextInt(3));
					WorldNews.call(player, territory.crew(), "There's the one " + territory.emperor() + " wants! Get them!", territory.color());
				}
				if (standing(player, territory) <= -70 && territory.commander() != null && now >= visit.nextCommander && !atSea) {
					visit.nextCommander = now + COMMANDER_BREAK;
					sendCommander(level, player, territory);
				}
			}
			case WARY -> {
				switch (territory.way()) {
					case TRIBUTE -> {
						if (visit.demandUntil == 0) {
							visit.demandAmount = 5 + 5 * Bounty.threatLevel(player);
							visit.demandUntil = now + DEMAND_TIME;
							String line = "big_mom".equals(territory.id())
									? "Mama demands tribute from everyone in her territory. " + visit.demandAmount + " Berries, or your lifespan!"
									: "Zehahaha! Nobody passes through here free. " + visit.demandAmount + " Berries, or we take it from your corpse.";
							WorldNews.call(player, territory.crew(), line, territory.color());
							player.sendSystemMessage(Component.literal("Type /tribute within 90 seconds to pay " + visit.demandAmount + " Berries.")
									.withStyle(ChatFormatting.YELLOW));
						}
					}
					case DUEL -> {
						if (visit.duelist == null && player.getVehicle() == null) {
							HumanNpc duelist = spawnCrew(level, player, territory, territory.leaderKit() != null ? territory.leaderKit() : territory.kits().get(0), 10, 18);
							if (duelist != null) {
								duelist.addTag(DUEL_TAG);
								duelist.setTarget(player);
								visit.duelist = duelist.getUUID();
								visit.duelUntil = now + DUEL_TIME;
								WorldNews.call(player, territory.crew(), "Kaido only respects strength. Beat me, or get off our island!", territory.color());
							}
						}
					}
					case PEACE -> {
						WorldNews.call(player, territory.crew(), "Captain's orders: no trouble on Elbaph. Enjoy your stay.", territory.color());
						change(player, territory, 2);
					}
				}
			}
			case FRIENDLY -> {
				if (random.nextFloat() < 0.25f) {
					int berries = 2 + random.nextInt(5);
					give(player, berries);
					WorldNews.call(player, territory.crew(), "Here, friend, a share of our spoils. (" + berries + " Berries)", territory.color());
				}
			}
			case CONQUERED -> {
				int berries = 5 + Bounty.threatLevel(player) * 2;
				give(player, berries);
				WorldNews.call(player, territory.crew(), "Our tribute to the one who beat " + territory.emperor() + ". (" + berries + " Berries)",
						territory.color());
			}
		}
	}

	private static void refuse(ServerPlayer player, Territory territory) {
		WorldNews.call(player, territory.crew(), "You dare refuse " + territory.emperor() + "? You'll pay for that!", territory.color());
		change(player, territory, -15);
		if (mood(player, territory) == Mood.HOSTILE && player.level() instanceof ServerLevel level && player.getVehicle() == null) {
			warParty(level, player, territory, 3);
		}
	}

	/** /tribute: pay the Berries an Emperor's crew asked for. */
	static Component payTribute(ServerPlayer player) {
		Visit visit = VISITS.get(player.getUUID());
		Territory territory = visit == null || visit.territory == null ? null : byId(visit.territory);
		if (territory == null || visit.demandUntil == 0) {
			return Component.literal("Nobody is asking you for tribute right now.").withStyle(ChatFormatting.GRAY);
		}
		int have = player.getInventory().countItem(CharacterFeature.BERRY);
		if (have < visit.demandAmount) {
			return Component.literal("You need " + visit.demandAmount + " Berries (you have " + have + ").").withStyle(ChatFormatting.RED);
		}
		int left = visit.demandAmount;
		for (int slot = 0; slot < player.getInventory().getContainerSize() && left > 0; slot++) {
			ItemStack stack = player.getInventory().getItem(slot);
			if (stack.is(CharacterFeature.BERRY)) {
				int take = Math.min(left, stack.getCount());
				stack.shrink(take);
				left -= take;
			}
		}
		visit.demandUntil = 0;
		change(player, territory, 12);
		return Component.literal("You paid " + visit.demandAmount + " Berries. The " + territory.crew() + " let you be... for now.")
				.withStyle(territory.color());
	}

	// ---- Crews ----

	private static void calmCrew(ServerLevel level, ServerPlayer player, Territory territory) {
		for (HumanNpc npc : level.getEntitiesOfClass(HumanNpc.class, player.getBoundingBox().inflate(40),
				npc -> npc.getTarget() == player && crewOf(npc) == territory && !npc.entityTags().contains(DUEL_TAG)
						&& npc.getLastHurtByMob() != player)) {
			npc.setTarget(null);
		}
	}

	private static void warParty(ServerLevel level, ServerPlayer player, Territory territory, int size) {
		for (int i = 0; i < size; i++) {
			String kit = i == 0 && territory.leaderKit() != null ? territory.leaderKit() : territory.kits().get(player.getRandom().nextInt(territory.kits().size()));
			HumanNpc npc = spawnCrew(level, player, territory, kit, 18, 30);
			if (npc != null) {
				npc.setTarget(player);
			}
		}
	}

	@Nullable
	private static HumanNpc spawnCrew(ServerLevel level, ServerPlayer player, Territory territory, String kit, int min, int max) {
		BlockPos spot = WorldEvents.landingSpot(level, player.blockPosition(), min, max, player.getRandom());
		if (spot == null) {
			return null;
		}
		HumanNpc npc = NpcFeature.spawn(level, kit, spot, player.getRandom().nextFloat() * 360f);
		if (npc == null) {
			return null;
		}
		npc.addTag(CREW_TAG + territory.id());
		if (!territory.crewTitle().isEmpty() && npc.getCustomName() != null) {
			// Generic pirate kits wear this Emperor's colours: "Big Mom Pirates Charlotte...".
			String name = npc.getCustomName().getString();
			int space = name.lastIndexOf(' ');
			npc.setCustomName(Component.literal(territory.crewTitle() + " " + (space >= 0 ? name.substring(space + 1) : name)));
		}
		return npc;
	}

	private static void sendCommander(ServerLevel level, ServerPlayer player, Territory territory) {
		BlockPos spot = WorldEvents.landingSpot(level, player.blockPosition(), 14, 24, player.getRandom());
		CharacterEntity boss = spot == null ? null : CharacterFeature.CHARACTER.create(level, EntitySpawnReason.EVENT);
		if (boss == null) {
			return;
		}
		boss.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
		boss.setCharacter(territory.commander(), true);
		boss.addTag(MarineHunters.HUNTER_TAG); // Leaves when you get far away, like the Navy's hunters.
		boss.addTag(CREW_TAG + territory.id());
		boss.setTarget(player);
		com.onepiecemod.bounty.EventBosses.markUntilUnloaded(boss); // Nothing else tracks it: gone once you leave, or after a restart.
		level.addFreshEntity(boss);
		WorldNews.report(level.getServer(), territory.emperor() + " has sent " + boss.getData().name + " after " + player.getName().getString() + "!",
				territory.color());
	}

	private static void give(ServerPlayer player, int berries) {
		ItemStack stack = new ItemStack(CharacterFeature.BERRY, berries);
		if (!player.getInventory().add(stack)) {
			player.spawnAtLocation((ServerLevel) player.level(), stack);
		}
	}

	/** Lines for /island. */
	static void describe(ServerPlayer player, java.util.function.Consumer<Component> out) {
		for (Territory territory : TERRITORIES) {
			Mood mood = mood(player, territory);
			out.accept(Component.literal(" " + territory.emperor() + ": " + mood.name().toLowerCase() + " (" + standing(player, territory) + ")")
					.withStyle(territory.color()));
		}
	}
}
