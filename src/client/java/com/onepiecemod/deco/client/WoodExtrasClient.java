package com.onepiecemod.deco.client;

import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.object.boat.BoatModel;
import net.minecraft.client.renderer.entity.BoatRenderer;
import net.minecraft.client.renderer.entity.EntityRenderers;

import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.deco.WoodExtras;

/**
 * Draws the island-wood boats with the vanilla boat model. Each one's texture is
 * textures/entity/boat/<wood>.png (or chest_boat/<wood>.png), picked from its model layer's name.
 */
public final class WoodExtrasClient {
	private WoodExtrasClient() {
	}

	public static void initialize() {
		for (WoodExtras.Wood wood : WoodExtras.ALL) {
			ModelLayerLocation boat = new ModelLayerLocation(OnePieceMod.id("boat/" + wood.name()), "main");
			ModelLayerLocation chestBoat = new ModelLayerLocation(OnePieceMod.id("chest_boat/" + wood.name()), "main");
			ModelLayerRegistry.registerModelLayer(boat, BoatModel::createBoatModel);
			ModelLayerRegistry.registerModelLayer(chestBoat, BoatModel::createChestBoatModel);
			EntityRenderers.register(wood.boat(), context -> new BoatRenderer(context, boat));
			EntityRenderers.register(wood.chestBoat(), context -> new BoatRenderer(context, chestBoat));
		}
	}
}
