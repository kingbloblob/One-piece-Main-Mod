package com.onepiecemod.multiplayer.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;

import com.llamalad7.mixinextras.injector.ModifyExpressionValue;

import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.dedicated.DedicatedServerProperties;
import net.minecraft.world.level.levelgen.presets.WorldPreset;

import com.onepiecemod.OnePieceMod;

/**
 * A new dedicated server makes a Grand Line world (the One Piece seas and the starting island), like the Create World
 * screen does in single player (sea.client.mixin.WorldCreationUiStateMixin). This only changes the default: a
 * server.properties that names a level-type keeps it, and the first start writes level-type=onepiece:grand_line there.
 */
@Mixin(DedicatedServerProperties.class)
public abstract class ServerWorldTypeMixin {
	private static final ResourceKey<WorldPreset> GRAND_LINE = ResourceKey.create(Registries.WORLD_PRESET, OnePieceMod.id("grand_line"));

	@ModifyExpressionValue(method = "<init>",
			at = @At(value = "FIELD", target = "Lnet/minecraft/world/level/levelgen/presets/WorldPresets;NORMAL:Lnet/minecraft/resources/ResourceKey;"))
	private ResourceKey<WorldPreset> onepiece$grandLineByDefault(ResourceKey<WorldPreset> normal) {
		return GRAND_LINE;
	}
}
