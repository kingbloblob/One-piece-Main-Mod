package com.onepiecemod.sea.client.mixin;

import java.nio.file.Path;
import java.util.Optional;
import java.util.OptionalLong;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import net.minecraft.client.gui.screens.worldselection.WorldCreationContext;
import net.minecraft.client.gui.screens.worldselection.WorldCreationUiState;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.levelgen.presets.WorldPreset;
import net.minecraft.world.level.levelgen.presets.WorldPresets;

import com.onepiecemod.OnePieceMod;

/**
 * Makes "Grand Line" the world type a new world starts with on the Create World screen,
 * so players get the One Piece seas and the starting island without hunting for the setting.
 * The vanilla "Default" type is still in the list.
 */
@Mixin(WorldCreationUiState.class)
public abstract class WorldCreationUiStateMixin {
	@Shadow
	public abstract WorldCreationContext getSettings();

	@Shadow
	public abstract void setWorldType(WorldCreationUiState.WorldTypeEntry worldType);

	@Inject(method = "<init>", at = @At("RETURN"))
	private void onepiece$startOnGrandLine(Path savesFolder, WorldCreationContext settings,
			Optional<ResourceKey<WorldPreset>> preset, OptionalLong seed, CallbackInfo info) {
		if (!preset.equals(Optional.of(WorldPresets.NORMAL))) {
			return; // Flat worlds, re-created worlds and so on keep what they asked for.
		}
		ResourceKey<WorldPreset> grandLine = ResourceKey.create(Registries.WORLD_PRESET, OnePieceMod.id("grand_line"));
		getSettings().worldgenLoadContext().lookupOrThrow(Registries.WORLD_PRESET).get(grandLine)
				.ifPresent(holder -> setWorldType(new WorldCreationUiState.WorldTypeEntry(holder)));
	}
}
