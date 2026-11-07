package com.onepiecemod;

import net.minecraft.resources.Identifier;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.fabricmc.api.ModInitializer;

import com.onepiecemod.sound.SoundFeature;

import com.onepiecemod.bounty.BountyFeature;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.crafting.CraftingFeature;
import com.onepiecemod.creature.Creatures;
import com.onepiecemod.crew.CrewFeature;
import com.onepiecemod.deco.DecoFeature;
import com.onepiecemod.empire.EmpireFeature;
import com.onepiecemod.guide.GuideFeature;
import com.onepiecemod.fruitdex.FruitdexFeature;
import com.onepiecemod.haki.HakiFeature;
import com.onepiecemod.item.ModItems;
import com.onepiecemod.item.ModLootTables;
import com.onepiecemod.multiplayer.MultiplayerFeature;
import com.onepiecemod.power.DevilFruitPowers;
import com.onepiecemod.power.ModAttachments;
import com.onepiecemod.race.RaceFeature;
import com.onepiecemod.body.BodyFeature;
import com.onepiecemod.resource.Resources;
import com.onepiecemod.sea.SeaFeature;
import com.onepiecemod.ship.ShipFeature;
import com.onepiecemod.stats.StatsFeature;
import com.onepiecemod.story.StoryFeature;
import com.onepiecemod.style.StyleFeature;
import com.onepiecemod.weapon.WeaponFeature;
import com.onepiecemod.world.WorldFeature;

/**
 * The starting point of the mod. Minecraft calls onInitialize() once while the game is loading.
 */
public class OnePieceMod implements ModInitializer {
	public static final String MOD_ID = "onepiece";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	@Override
	public void onInitialize() {
		com.onepiecemod.config.ModConfig.load(); // First: other features read the settings while they start.
		ModAttachments.initialize();
		ModItems.initialize();
		SoundFeature.initialize();
		ModLootTables.initialize();
		DevilFruitPowers.initialize();
		CharacterFeature.initialize();
		BountyFeature.initialize();
		CrewFeature.initialize();
		HakiFeature.initialize();
		RaceFeature.initialize();
		BodyFeature.initialize();
		ShipFeature.initialize();
		com.onepiecemod.ship.ShipModels.initialize(); // the famous ships from the show (Going Merry, Thousand Sunny, enemy ships)
		SeaFeature.initialize();
		StyleFeature.initialize();
		WorldFeature.initialize();
		DecoFeature.initialize();
		com.onepiecemod.deco.WoodExtras.initialize(); // Signs and boats for the island woods.
		com.onepiecemod.flora.FloraFeature.initialize(); // Island plants and soils (after deco: shares its soil tag).
		com.onepiecemod.furnish.Furnish.initialize();
		CraftingFeature.initialize();
		com.onepiecemod.workshop.WorkshopFeature.initialize(); // After crafting: station upgrade trees, Skypiea Dials, cooking tiers II-III, rare drops.
		com.onepiecemod.furniture.Furniture.initialize(); // Tables, chairs, shelves, rugs and other props for builds.
		WeaponFeature.initialize();
		Creatures.initialize();
		Resources.initialize();
		com.onepiecemod.underground.UndergroundFeature.initialize(); // Cave zones, underground blocks (structures are data).
		StoryFeature.initialize();
		EmpireFeature.initialize();
		MultiplayerFeature.initialize();
		GuideFeature.initialize();
		com.onepiecemod.power.SeaPurgeItem.initialize();
		FruitdexFeature.initialize();
		com.onepiecemod.collection.CollectionFeature.initialize(); // Collector's Log: fish, food, ships, swords and island goals with rewards.
		StatsFeature.initialize();
		com.onepiecemod.questtree.QuestTreeFeature.initialize();
		com.onepiecemod.building.Buildings.initialize();
		com.onepiecemod.fx.FxFeature.initialize();
		com.onepiecemod.weather.WeatherFeature.initialize(); // After SeaFeature: it builds on the Calm Belt's wind.
		com.onepiecemod.hud.HudFeature.initialize();
		com.onepiecemod.shipcombat.ShipCombatFeature.initialize();
		com.onepiecemod.deepsea.DeepSeaFeature.initialize(); // After ships and ship combat: submarines, ship coating, deep trenches.
		com.onepiecemod.npc.NpcFeature.initialize(); // After bounty, ship combat and world: pirate and Marine NPCs.
		com.onepiecemod.news.NewsFeature.initialize(); // Newspapers, wall Wanted Posters, incoming Den Den Mushi calls.
		com.onepiecemod.town.TownFeature.initialize(); // After NPCs: townsfolk, markets, bar brawls and festivals.
		com.onepiecemod.worldevent.WorldEvents.initialize(); // After ship combat and NPCs: Buster Calls, fleets, Emperor territories, the Reverie.
		com.onepiecemod.anim.CombatAnims.initialize(); // Custom attack animations (sword slashes, punches, casting...).
		com.onepiecemod.tutorial.TutorialFeature.initialize(); // New player guide (First Voyage).
		com.onepiecemod.dialogue.DialogueFeature.initialize(); // Talk screen for friendly characters.
		com.onepiecemod.career.CareerFeature.initialize(); // Play as a Marine or a Revolutionary instead of a pirate.
		com.onepiecemod.endgame.EndgameFeature.initialize(); // After story and world events: Laugh Tale finale, raids, New Game+.
		com.onepiecemod.arena.ArenaFeature.initialize(); // Corrida Colosseum tournaments and Davy Back Fights.
		com.onepiecemod.progression.PathTraining.initialize(); // Branching Haki and fighting style upgrades from trainers.
		com.onepiecemod.treasure.TreasureFeature.initialize(); // Treasure maps, buried loot and sunken wrecks.
		com.onepiecemod.voyage.VoyageFeature.initialize(); // After treasure and ship combat: sea monsters, wandering ships, flotsam, bottles.
		com.onepiecemod.cuisine.CuisineFeature.initialize(); // Fishing by sea, Sanji's dishes with long buffs, the All Blue.
		com.onepiecemod.farm.FarmFeature.initialize(); // After cuisine: island crops, Seed Vault, sprinklers, ranch troughs, crew farm plots.
		com.onepiecemod.season.Seasons.initialize(); // After farming: seasons that speed up or slow down crops and change the sea weather.
		com.onepiecemod.hideout.HideoutFeature.initialize(); // Pirate hideouts: claim an island, your crew lives there, the Navy attacks it.
		com.onepiecemod.crewship.CrewShipFeature.initialize(); // Home ships: a Ship's Log makes a ship the crew's home, with rooms, bunks and levels.
		com.onepiecemod.vegapunk.VegapunkFeature.initialize(); // After NPCs and story: Pacifista/Seraphim hunts, cyborg upgrades.
		com.onepiecemod.seatrain.SeaTrainFeature.initialize(); // The Puffing Tom and Sea Train Stations (fast travel).
		com.onepiecemod.sidejob.SideJobs.initialize(); // Town requests and Wanted contracts for the mid-game.
		com.onepiecemod.questlog.QuestLogFeature.initialize(); // Quest journal (O key) and the compass bar with the Log Pose needle.
		com.onepiecemod.config.ConfigCommand.initialize(); // /onepiece_config for server admins.
		com.onepiecemod.dungeon.DungeonBosses.initialize(); // After NPCs: dungeon mini-bosses, their moves and legendary drops.
		com.onepiecemod.cutscene.CutsceneFeature.initialize(); // Boss intros and story flashbacks (cutscenes.json, /flashback).
		com.onepiecemod.baseworks.BaseWorks.initialize(); // After hideouts and towns: plan books and the Builder's Ledger (hideout upgrades).
		com.onepiecemod.settlement.Settlements.initialize(); // Player towns: the Town Planner, plots, townsfolk moving in, rent.
		com.onepiecemod.mining.MiningFeature.initialize(); // Tool tiers, island ores, Mining Drill + Ore Cart, miner crew job.
		com.onepiecemod.lifeskill.LifeSkills.initialize(); // Life skills: Farming, Mining, Cooking, Smithing levels and perks.
		com.onepiecemod.poneglyph.PoneglyphHunt.initialize(); // Twelve Lost Poneglyphs to hunt, Ohara Survey Notes, /poneglyphs.
		com.onepiecemod.advancement.AdvancementFeature.initialize(); // Last: achievements read what every other feature saves.

		LOGGER.info("The One Piece is real!");
	}

	/** Turns a name like "gomu_gomu_no_mi" into the id "onepiece:gomu_gomu_no_mi". */
	public static Identifier id(String path) {
		return Identifier.fromNamespaceAndPath(MOD_ID, path);
	}
}
