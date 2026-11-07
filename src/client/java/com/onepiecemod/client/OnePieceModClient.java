package com.onepiecemod.client;

import net.fabricmc.api.ClientModInitializer;

import com.onepiecemod.sound.client.SoundClient;

import com.onepiecemod.ship.client.ShipClient;
import com.onepiecemod.bounty.client.BountyClient;
import com.onepiecemod.character.client.CharacterClient;
import com.onepiecemod.crafting.client.CraftingClient;
import com.onepiecemod.crew.client.CrewClient;
import com.onepiecemod.empire.client.EmpireClient;
import com.onepiecemod.creature.client.CreatureClient;
import com.onepiecemod.guide.client.GuideClient;
import com.onepiecemod.fruitdex.client.FruitdexClient;
import com.onepiecemod.haki.client.HakiClient;
import com.onepiecemod.race.client.RaceClient;
import com.onepiecemod.body.client.BodyClient;
import com.onepiecemod.recipeview.client.RecipeViewClient;
import com.onepiecemod.sea.client.SeaClient;
import com.onepiecemod.stats.client.StatsClient;
import com.onepiecemod.style.client.StyleClient;
import com.onepiecemod.weapon.client.WeaponClient;
import com.onepiecemod.client.power.DevilFruitKeys;

/**
 * Code that only runs on the player's game client (not on servers) goes here,
 * for example key bindings for Devil Fruit attacks.
 */
public class OnePieceModClient implements ClientModInitializer {
	@Override
	public void onInitializeClient() {
		SoundClient.initialize();
		CharacterClient.initialize();
		BountyClient.initialize();
		CrewClient.initialize();
		EmpireClient.initialize();
		HakiClient.initialize();
		RaceClient.initialize();
		BodyClient.initialize();
		ShipClient.initialize();
		SeaClient.initialize();
		StyleClient.initialize();
		CraftingClient.initialize();
		RecipeViewClient.initialize();
		WeaponClient.initialize();
		CreatureClient.initialize();
		DevilFruitKeys.initialize();
		FruitdexClient.initialize();
		com.onepiecemod.collection.client.CollectionClient.initialize();
		GuideClient.initialize();
		StatsClient.initialize();
		com.onepiecemod.questtree.client.QuestTreeClient.initialize();
		com.onepiecemod.building.client.GhostRenderer.initialize();
		com.onepiecemod.fx.client.FxClient.initialize();
		com.onepiecemod.weather.client.WeatherClient.initialize();
		com.onepiecemod.hud.client.HudClient.initialize();
		com.onepiecemod.shipcombat.client.ShipCombatClient.initialize();
		com.onepiecemod.deepsea.client.DeepSeaClient.initialize(); // Dive keys and the depth gauge.
		com.onepiecemod.menus.client.PirateMenus.initialize();
		com.onepiecemod.menus.client.AnimeLook.initialize();
		com.onepiecemod.anim.client.AnimClient.initialize();
		com.onepiecemod.zoan.client.ZoanClient.initialize(); // Full-body Zoan forms (leopard, phoenix, dragon, Heavy Point).
		com.onepiecemod.tutorial.client.TutorialClient.initialize();
		com.onepiecemod.dialogue.client.DialogueClient.initialize();
		com.onepiecemod.career.client.CareerClient.initialize();
		com.onepiecemod.hideout.client.HideoutClient.initialize();
		com.onepiecemod.config.client.SettingsClient.initialize();
		com.onepiecemod.town.client.TownClient.initialize();
		com.onepiecemod.furniture.client.FurnitureClient.initialize();
		com.onepiecemod.deco.client.WoodExtrasClient.initialize();
		com.onepiecemod.vegapunk.client.VegapunkClient.initialize(); // C key: Radical Beam / Coup de Vent.
		com.onepiecemod.seatrain.client.SeaTrainClient.initialize(); // The Puffing Tom (its carriages are block displays).
		com.onepiecemod.questlog.client.QuestLogClient.initialize();
		com.onepiecemod.cutscene.client.CutsceneClient.initialize(); // Boss intros and flashbacks; Enter skips. // O key: quest journal. Compass bar at the top of the screen.
	}
}
