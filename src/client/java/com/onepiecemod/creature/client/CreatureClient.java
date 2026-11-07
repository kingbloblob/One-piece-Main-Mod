package com.onepiecemod.creature.client;

import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.entity.EntityRenderers;

import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.creature.CreatureSpecies;
import com.onepiecemod.creature.Creatures;

/**
 * Client-only setup for the creatures: their models and how they're drawn. OnePieceModClient calls initialize().
 */
public class CreatureClient {
	public static void initialize() {
		for (CreatureSpecies species : CreatureSpecies.ALL) {
			ModelLayerLocation layer = new ModelLayerLocation(OnePieceMod.id(species.id()), "main");
			ModelLayerRegistry.registerModelLayer(layer, () -> CreatureModels.create(species.id()));
			EntityRenderers.register(Creatures.TYPES.get(species.id()), context -> new CreatureRenderer(context, species, layer));
		}
	}
}
