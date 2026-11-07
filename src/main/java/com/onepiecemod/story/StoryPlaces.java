package com.onepiecemod.story;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.levelgen.structure.Structure;

import com.onepiecemod.OnePieceMod;

/**
 * "Is this spot inside Foosha Village?" for the story's "reach" goals and events.
 * Structure ids are the ones in structures.md, like "foosha_village".
 */
public class StoryPlaces {
	public static boolean isInside(ServerLevel level, BlockPos pos, String structureId) {
		ResourceKey<Structure> key = ResourceKey.create(Registries.STRUCTURE, OnePieceMod.id(structureId));
		// Also look a few blocks down, so standing on a roof or a ship's deck still counts.
		return level.structureManager().getStructureWithPieceAt(pos, holder -> holder.is(key)).isValid()
				|| level.structureManager().getStructureWithPieceAt(pos.below(4), holder -> holder.is(key)).isValid();
	}
}
