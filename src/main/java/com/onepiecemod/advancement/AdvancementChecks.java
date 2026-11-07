package com.onepiecemod.advancement;

import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.function.Predicate;

import com.mojang.serialization.Codec;

import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.arena.ArenaFeature;
import com.onepiecemod.arena.CorridaTournament;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.bounty.NavyRaids;
import com.onepiecemod.building.BuildingRegistry;
import com.onepiecemod.building.Buildings;
import com.onepiecemod.career.Career;
import com.onepiecemod.career.Careers;
import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.QuestHandler;
import com.onepiecemod.creature.CreatureEntity;
import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.cuisine.Fish;
import com.onepiecemod.cuisine.Fishing;
import com.onepiecemod.empire.EmpireData;
import com.onepiecemod.empire.Title;
import com.onepiecemod.endgame.EndgameData;
import com.onepiecemod.endgame.NewGamePlus;
import com.onepiecemod.endgame.RaidDef;
import com.onepiecemod.fruitdex.FruitdexFeature;
import com.onepiecemod.furniture.SeatEntity;
import com.onepiecemod.haki.HakiAttachments;
import com.onepiecemod.haki.HakiData;
import com.onepiecemod.hideout.HideoutLevels;
import com.onepiecemod.hideout.Hideouts;
import com.onepiecemod.pet.Pets;
import com.onepiecemod.power.Awakening;
import com.onepiecemod.power.DevilFruit;
import com.onepiecemod.power.DevilFruits;
import com.onepiecemod.power.ModAttachments;
import com.onepiecemod.race.RaceAttachments;
import com.onepiecemod.sea.CalmBelt;
import com.onepiecemod.sea.LogPoseTracker;
import com.onepiecemod.sea.SeaKingEntity;
import com.onepiecemod.seatrain.Stations;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.stats.PlayerStat;
import com.onepiecemod.stats.StatsAttachments;
import com.onepiecemod.story.StoryData;
import com.onepiecemod.story.StoryProgress;
import com.onepiecemod.style.FightingStyle;
import com.onepiecemod.style.StyleAttachments;
import com.onepiecemod.weather.SeaEvent;
import com.onepiecemod.weather.SeaEventType;
import com.onepiecemod.weather.SeaEvents;
import com.onepiecemod.vegapunk.Cyborg;
import com.onepiecemod.vegapunk.CyborgUpgrade;

/**
 * The advancements that can't be described in JSON. Each one has an "impossible" criterion called "done",
 * and AdvancementFeature awards it when the check below becomes true for a player.
 * The JSON files are written by tools/advancements/gen_advancements.py: keep the ids here in step with it.
 */
public final class AdvancementChecks {
	public static final Map<String, Predicate<ServerPlayer>> CHECKS = new LinkedHashMap<>();
	/**
	 * Each player's bounty while a Navy raid is on them. A raid that ends with the bounty going up was won.
	 * Saved on the player, so leaving the game or a server restart in the middle of a raid doesn't lose it.
	 */
	private static final AttachmentType<Long> RAID_BOUNTY = AttachmentRegistry.create(OnePieceMod.id("raid_start_bounty"),
			builder -> builder.persistent(Codec.LONG).copyOnDeath());

	private AdvancementChecks() {
	}

	private static void check(String id, Predicate<ServerPlayer> test) {
		CHECKS.put(id, test);
	}

	static {
		// The tab roots: everyone has these, so the tabs show up from the start.
		check("journey/root", player -> true);
		check("powers/root", player -> true);
		check("pirate/root", player -> true);
		check("wonders/root", player -> true);

		// The Grand Line tab: story chapters.
		chapter("journey/romance_dawn", "set_sail");
		chapter("journey/baratie", "baratie");
		chapter("journey/east_blue", "arlong_park");
		chapter("journey/loguetown", "loguetown");
		chapter("journey/reverse_mountain", "reverse_mountain");
		chapter("journey/drum_island", "drum_island");
		chapter("journey/alabasta", "alabasta");
		chapter("journey/sky_island", "sky_island");
		chapter("journey/enies_lobby", "enies_lobby");
		chapter("journey/thriller_bark", "thriller_bark");
		chapter("journey/sabaody", "sabaody");
		chapter("journey/amazon_lily", "amazon_lily");
		chapter("journey/impel_down_escape", "impel_down");
		chapter("journey/marineford", "marineford");
		chapter("journey/paramount_war", "paramount_war");
		chapter("journey/training", "training");
		chapter("journey/fishman_island", "fishman_island");
		chapter("journey/punk_hazard", "punk_hazard");
		chapter("journey/dressrosa", "dressrosa");
		chapter("journey/zou", "zou");
		chapter("journey/whole_cake", "whole_cake");
		chapter("journey/wano", "wano");
		chapter("journey/egghead", "egghead_incident");
		chapter("journey/elbaph", "holy_knights");
		chapter("journey/hachinosu", "hachinosu");
		check("journey/laugh_tale", player -> {
			StoryProgress progress = StoryProgress.of(player);
			return progress != null && progress.finished();
		});
		// Post-game saga in the End.
		chapter("journey/red_line", "red_line");
		chapter("journey/void_century", "void_century");
		chapter("journey/god_knights", "god_knights");
		chapter("journey/empty_throne", "empty_throne");
		chapter("journey/dawn", "dawn");

		// Navigation and the sea.
		check("journey/log_pose", player -> islands(player) >= 1);
		check("journey/five_islands", player -> islands(player) >= 5);
		check("journey/ten_islands", player -> islands(player) >= 10);
		check("journey/sail", player -> ShipEntity.aboard(player) != null);
		check("journey/calm_belt", player -> ShipEntity.aboard(player) instanceof ShipEntity ship
				&& CalmBelt.isCalmBelt(ship.level(), ship.blockPosition()));
		check("journey/vivre_card", player -> hasItemStartingWith(player, "vivre_card_"));

		// Sea events (the weather package): be inside one while it is really happening.
		seaEvent("journey/storm", SeaEventType.STORM);
		seaEvent("journey/whirlpool", SeaEventType.WHIRLPOOL);
		seaEvent("journey/aqua_laguna", SeaEventType.AQUA_LAGUNA);
		seaEvent("journey/florian_mist", SeaEventType.FLORIAN_MIST);
		seaEvent("journey/blizzard", SeaEventType.BLIZZARD);
		seaEvent("journey/heat_wave", SeaEventType.HEAT_WAVE);
		seaEvent("journey/sea_king_ambush", SeaEventType.CALM_BELT_AMBUSH);
		seaEvent("journey/waterspout", SeaEventType.WATERSPOUT);
		seaEvent("journey/rogue_wave", SeaEventType.ROGUE_WAVE);
		seaEvent("journey/hailstorm", SeaEventType.HAILSTORM);
		check("journey/all_weather", player -> hasAll(player, "journey/storm", "journey/whirlpool", "journey/aqua_laguna",
				"journey/florian_mist", "journey/blizzard", "journey/heat_wave", "journey/sea_king_ambush"));

		// Powers tab: race and Devil Fruits.
		check("powers/race", player -> RaceAttachments.get(player) != null);
		check("powers/devil_fruit", player -> fruit(player) != null);
		check("powers/paramecia", player -> fruitType(player) == DevilFruit.Type.PARAMECIA);
		check("powers/logia", player -> fruitType(player) == DevilFruit.Type.LOGIA);
		check("powers/zoan", player -> fruitType(player) == DevilFruit.Type.ZOAN);
		// Mastery stops counting at the "Mastery to awaken" setting, so both goals follow that setting.
		check("powers/mastery", player -> Awakening.getMastery(player) >= Math.max(1, Awakening.masteryNeeded() / 4));
		check("powers/mastery_max", player -> Awakening.getMastery(player) >= Awakening.masteryNeeded());
		check("powers/awakening", player -> player.getAttachedOrElse(ModAttachments.AWAKENED, false));

		// Haki.
		check("powers/observation", player -> haki(player).observationLevel() >= 1);
		check("powers/observation_max", player -> haki(player).observationLevel() >= HakiData.MAX_LEVEL);
		check("powers/armament", player -> haki(player).armamentLevel() >= 1);
		check("powers/armament_max", player -> haki(player).armamentLevel() >= HakiData.MAX_LEVEL);
		check("powers/conqueror", player -> haki(player).conqueror());
		check("powers/conqueror_max", player -> haki(player).conquerorLevel() >= HakiData.MAX_LEVEL);

		// Fighting styles.
		check("powers/style", player -> styles(player) >= 1);
		check("powers/three_styles", player -> styles(player) >= 3);
		check("powers/all_styles", player -> styles(player) >= FightingStyle.values().length);

		// Pirate Level and the stat tree.
		check("powers/level_10", player -> StatsAttachments.get(player).level() >= 10);
		check("powers/level_25", player -> StatsAttachments.get(player).level() >= 25);
		check("powers/level_40", player -> StatsAttachments.get(player).level() >= 40);
		check("powers/level_60", player -> StatsAttachments.get(player).level() >= 60);
		check("powers/stat_max", player -> {
			for (PlayerStat stat : PlayerStat.values()) {
				if (StatsAttachments.rank(player, stat) >= PlayerStat.MAX_RANK) {
					return true;
				}
			}
			return false;
		});

		// Devil Fruit encyclopedia.
		check("powers/fruitdex_15", player -> FruitdexFeature.discovered(player).size() >= 15);
		check("powers/fruitdex_50", player -> FruitdexFeature.discovered(player).size() >= 50);
		check("powers/fruitdex_all", player -> FruitdexFeature.discovered(player).size() >= DevilFruits.ALL.size());

		// Pirate Life tab: bounty.
		check("pirate/bounty", player -> Bounty.get(player) > 0);
		check("pirate/bounty_10m", player -> Bounty.get(player) >= 10_000_000L);
		check("pirate/bounty_100m", player -> Bounty.get(player) >= 100_000_000L);
		check("pirate/bounty_500m", player -> Bounty.get(player) >= 500_000_000L);
		check("pirate/bounty_1b", player -> Bounty.get(player) >= 1_000_000_000L);
		check("pirate/bounty_3b", player -> Bounty.get(player) >= 3_000_000_000L);

		// Bosses (beaten ones are saved as "buggy", "buggy:hard", "buggy:expert").
		check("pirate/first_boss", player -> bosses(player).stream().anyMatch(id -> !id.contains(":")));
		check("pirate/hard_boss", player -> bosses(player).stream().anyMatch(id -> id.endsWith(":hard")));
		check("pirate/expert_boss", player -> bosses(player).stream().anyMatch(id -> id.endsWith(":expert")));
		check("pirate/worst_generation", player -> beatAll(player, "kid", "killer", "hawkins"));
		check("pirate/warlords", player -> beatAll(player, "crocodile", "moria", "doflamingo", "mihawk"));
		check("pirate/admirals", player -> beatAll(player, "akainu", "kizaru", "fujitora", "ryokugyu", "aokiji"));
		check("pirate/emperors", player -> beatAll(player, "whitebeard", "big_mom", "kaido", "blackbeard"));
		check("pirate/all_bosses", AdvancementChecks::beatEveryBoss);
		check("pirate/magellan", player -> beatAll(player, "magellan"));
		check("pirate/hody", player -> beatAll(player, "hody"));
		check("pirate/queen", player -> beatAll(player, "queen"));
		check("pirate/saturn", player -> beatAll(player, "saturn"));
		check("pirate/gunko", player -> beatAll(player, "gunko"));
		check("pirate/shamrock", player -> beatAll(player, "shamrock"));
		check("pirate/loki", player -> beatAll(player, "loki"));
		check("pirate/imu", player -> beatAll(player, "imu"));
		check("pirate/xebec", player -> beatAll(player, "xebec"));
		check("pirate/navy_raid", AdvancementChecks::wonNavyRaid);

		// Character quests ("giver:step" keys in QUESTS_DONE).
		check("pirate/quest", player -> !player.getAttachedOrElse(CharacterAttachments.QUESTS_DONE, List.of()).isEmpty());
		check("pirate/quest_line", player -> questLinesDone(player) >= 1);
		check("pirate/quest_lines_5", player -> questLinesDone(player) >= 5);
		check("pirate/quest_lines_all", player -> {
			int lines = 0;
			for (CharacterData character : CharacterData.all().values()) {
				if (!character.quests.isEmpty()) {
					lines++;
				}
			}
			return lines > 0 && questLinesDone(player) >= lines;
		});
		check("pirate/met_10", player -> player.getAttachedOrElse(CharacterAttachments.MET, List.of()).size() >= 10);

		// Blueprint buildings.
		check("pirate/building", player -> !buildingsOwned(player).isEmpty());
		check("pirate/all_buildings", player -> buildingsOwned(player).size() >= buildingKinds());

		// Crew.
		check("pirate/crew", player -> crew(player) != null);
		check("pirate/crew_3", player -> crew(player) != null && crew(player).size() >= 3);
		check("pirate/crew_full", player -> crew(player) != null && crew(player).size() >= CrewRole.values().length);

		// Kingdoms and titles.
		check("pirate/kingdom", player -> !EmpireData.kingdoms(player).isEmpty());
		check("pirate/emperor", player -> EmpireData.title(player).atLeast(Title.EMPEROR));
		check("pirate/pirate_king", player -> EmpireData.title(player).atLeast(Title.PIRATE_KING));
		check("pirate/king_of_the_world", player -> EmpireData.title(player).atLeast(Title.KING_OF_THE_WORLD));

		// Wonders of the World tab: creatures.
		check("wonders/ride", player -> player.getVehicle() instanceof CreatureEntity);
		// Submarines and coated ships (deepsea).
		check("wonders/coated", player -> ShipEntity.aboard(player) instanceof ShipEntity ship && com.onepiecemod.deepsea.ShipDive.isCoated(ship));
		check("wonders/submarine", player -> ShipEntity.aboard(player) instanceof ShipEntity ship && com.onepiecemod.deepsea.ShipDive.canDive(ship)
				&& com.onepiecemod.deepsea.ShipDive.depth(ship) >= 20);
		check("wonders/abyss", player -> ShipEntity.aboard(player) instanceof ShipEntity ship && com.onepiecemod.deepsea.ShipDive.canDive(ship)
				&& com.onepiecemod.deepsea.ShipDive.depth(ship) >= 100);
		check("wonders/tame", player -> !player.level().getEntitiesOfClass(CreatureEntity.class,
				player.getBoundingBox().inflate(16), creature -> creature.getOwner() == player).isEmpty());
		check("wonders/cave_mole", player -> player.getVehicle() instanceof CreatureEntity creature
				&& creature.species().id().equals("cave_mole"));

		// Furniture
		check("pirate/take_a_seat", player -> player.getVehicle() instanceof SeatEntity);

		// After the story: raids and New Game+
		check("pirate/first_raid", player -> !EndgameData.of(player).cleared().isEmpty());
		check("pirate/all_raids", player -> EndgameData.of(player).cleared().containsAll(RaidDef.all().keySet()));
		check("journey/new_game_plus", player -> EndgameData.of(player).cycle() >= 1);
		check("journey/new_game_plus_max", player -> EndgameData.of(player).cycle() >= NewGamePlus.MAX_CYCLE);


		// Fishing: the fish log.
		check("journey/first_catch", player -> !fishCaught(player).isEmpty());
		check("journey/fish_log_10", player -> fishCaught(player).size() >= 10);
		check("journey/all_blue", player -> fishCaught(player).stream().anyMatch(id -> {
			for (Fish fish : Fish.values()) {
				if (fish.id.equals(id) && fish.where == Fish.Where.ALL_BLUE) {
					return true;
				}
			}
			return false;
		}));
		check("journey/every_fish", player -> fishCaught(player).size() >= Fish.values().length);
		check("journey/commuter", player -> Stations.known(player).size() >= 5);

		// Marine and Revolutionary careers.
		check("pirate/join_marines", player -> Careers.career(player) == Career.MARINE);
		check("pirate/marine_captain", player -> Careers.career(player) == Career.MARINE && Careers.get(player).rank() >= 5);
		check("pirate/fleet_admiral", player -> Careers.career(player) == Career.MARINE
				&& Careers.get(player).rank() >= Career.MARINE.ranks.size() - 1);
		check("pirate/join_revolution", player -> Careers.career(player) == Career.REVOLUTIONARY);
		check("pirate/army_commander", player -> Careers.career(player) == Career.REVOLUTIONARY && Careers.get(player).rank() >= 5);
		check("pirate/right_hand", player -> Careers.career(player) == Career.REVOLUTIONARY
				&& Careers.get(player).rank() >= Career.REVOLUTIONARY.ranks.size() - 1);
		check("pirate/orders_10", player -> Careers.get(player).missionsDone() >= 10);

		// Corrida Colosseum and Davy Back Fights.
		check("pirate/colosseum", player -> ArenaFeature.record(player).corridaWins() >= 1);
		check("pirate/colosseum_champion", player -> ArenaFeature.record(player).corridaBest() >= CorridaTournament.Cup.values().length - 1);
		check("pirate/davy_back", player -> ArenaFeature.record(player).dbfWins() >= 1);
		check("pirate/beat_foxy", player -> ArenaFeature.record(player).foxyBeaten());
		check("pirate/davy_back_10", player -> ArenaFeature.record(player).dbfWins() >= 10);

		// Hideouts.
		check("pirate/hideout", player -> hideout(player) != null);
		check("pirate/pirate_fort", player -> hideout(player) != null && hideout(player).level() >= 3);
		check("pirate/pirate_fortress", player -> hideout(player) != null && hideout(player).level() >= HideoutLevels.MAX);
		check("pirate/hold_the_fort", player -> hideout(player) != null && hideout(player).held() >= 1);

		// Pets.
		check("wonders/sea_king_pet", player -> !player.level().getEntitiesOfClass(SeaKingEntity.class,
				player.getBoundingBox().inflate(32), seaKing -> player.getUUID().equals(seaKing.getOwnerId())).isEmpty());
		check("wonders/menagerie", player -> Pets.petsOf(player, 32).size() >= 3);

		// Cyborg upgrades. (wonders/pacifista, mark_iii, seraphim and all_seraphim are granted by VegapunkHunts.)
		check("wonders/cyborg", player -> !Cyborg.get(player).tiers().isEmpty());
		check("wonders/cyborg_tier3", player -> Cyborg.get(player).tiers().values().stream()
				.anyMatch(tier -> tier >= CyborgUpgrade.MAX_TIER));
		check("wonders/full_cyborg", player -> {
			for (CyborgUpgrade upgrade : CyborgUpgrade.values()) {
				if (Cyborg.get(player).tiers().getOrDefault(upgrade.id, 0) < CyborgUpgrade.MAX_TIER) {
					return false;
				}
			}
			return true;
		});

		// journey/sink_ship, capture_ship, win_naval_battle and repel_boarders have no check: ship combat calls AdvancementFeature.grant.
	}

	/** Awarded once the story chapter with this id is finished. Chapters missing from story.json never count. */
	private static void chapter(String id, String chapterId) {
		check(id, player -> {
			if (StoryData.indexOf(chapterId) < 0) {
				return false;
			}
			StoryProgress progress = StoryProgress.of(player);
			return progress != null && progress.completed(chapterId);
		});
	}

	/** Awarded while the player is inside a sea event of this kind that has started (not just its warning). */
	private static void seaEvent(String id, SeaEventType type) {
		check(id, player -> {
			if (player.level().dimension() != Level.OVERWORLD) {
				return false;
			}
			long time = player.level().getGameTime();
			for (SeaEvent event : SeaEvents.ACTIVE) {
				if (event.type == type && event.isActive(time) && event.isInside(player.getX(), player.getZ())) {
					return true;
				}
			}
			return false;
		});
	}

	/** True once the player has every one of these advancements. */
	private static boolean hasAll(ServerPlayer player, String... ids) {
		MinecraftServer server = player.level().getServer();
		for (String id : ids) {
			AdvancementHolder holder = server.getAdvancements().get(OnePieceMod.id(id));
			if (holder == null || !player.getAdvancements().getOrStartProgress(holder).isDone()) {
				return false;
			}
		}
		return true;
	}

	private static boolean hasItemStartingWith(ServerPlayer player, String prefix) {
		for (int slot = 0; slot < player.getInventory().getContainerSize(); slot++) {
			ItemStack stack = player.getInventory().getItem(slot);
			if (!stack.isEmpty() && BuiltInRegistries.ITEM.getKey(stack.getItem()).getPath().startsWith(prefix)) {
				return true;
			}
		}
		return false;
	}

	/**
	 * NavyRaids has no "raid won" event, so this watches it: winning the last wave raises the bounty as the raid ends,
	 * while running away or the Marines finding no place to land leave it as it was.
	 */
	private static boolean wonNavyRaid(ServerPlayer player) {
		long bounty = Bounty.get(player);
		if (NavyRaids.isRaiding(player)) {
			if (!player.hasAttached(RAID_BOUNTY)) {
				player.setAttached(RAID_BOUNTY, bounty);
			}
			return false;
		}
		Long before = player.removeAttached(RAID_BOUNTY);
		return before != null && bounty > before;
	}

	private static int questLinesDone(ServerPlayer player) {
		int done = 0;
		for (CharacterData character : CharacterData.all().values()) {
			if (!character.quests.isEmpty() && QuestHandler.currentStep(player, character) >= character.quests.size()) {
				done++;
			}
		}
		return done;
	}

	/** The kinds of blueprint building this player has finished, in any dimension. */
	private static Set<String> buildingsOwned(ServerPlayer player) {
		Set<String> types = new HashSet<>();
		for (ServerLevel level : player.level().getServer().getAllLevels()) {
			for (BuildingRegistry.Entry entry : BuildingRegistry.all(level)) {
				if (player.getUUID().equals(entry.owner())) {
					types.add(entry.type());
				}
			}
		}
		return types;
	}

	private static int buildingKinds() {
		int kinds = 0;
		for (Object building : Buildings.all()) {
			kinds++;
		}
		return kinds;
	}

	private static int islands(ServerPlayer player) {
		return LogPoseTracker.journey(player).visited().size();
	}

	private static DevilFruit fruit(ServerPlayer player) {
		return DevilFruits.get(player.getAttached(ModAttachments.DEVIL_FRUIT));
	}

	private static DevilFruit.Type fruitType(ServerPlayer player) {
		DevilFruit fruit = fruit(player);
		return fruit == null ? null : fruit.type();
	}

	private static HakiData haki(ServerPlayer player) {
		return HakiAttachments.get(player);
	}

	private static int styles(ServerPlayer player) {
		return player.getAttachedOrElse(StyleAttachments.KNOWN_STYLES, List.<String>of()).size();
	}

	private static List<String> bosses(ServerPlayer player) {
		return player.getAttachedOrElse(CharacterAttachments.BOSSES_DEFEATED, List.of());
	}

	private static boolean beatAll(ServerPlayer player, String... ids) {
		List<String> beaten = bosses(player);
		for (String id : ids) {
			if (!beaten.contains(id)) {
				return false;
			}
		}
		return true;
	}

	private static boolean beatEveryBoss(ServerPlayer player) {
		List<String> beaten = bosses(player);
		boolean any = false;
		for (Map.Entry<String, CharacterData> entry : CharacterData.all().entrySet()) {
			if (entry.getValue().isBossRole()) {
				any = true;
				if (!beaten.contains(entry.getKey())) {
					return false;
				}
			}
		}
		return any;
	}

	private static Crew crew(ServerPlayer player) {
		return player.getAttached(CrewAttachments.CREW);
	}

	private static List<String> fishCaught(ServerPlayer player) {
		return player.getAttachedOrElse(Fishing.CAUGHT, List.of());
	}

	private static Hideouts.Hideout hideout(ServerPlayer player) {
		return Hideouts.of(player.level().getServer(), player.getUUID());
	}
}
