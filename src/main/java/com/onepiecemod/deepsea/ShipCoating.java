package com.onepiecemod.deepsea;

import java.util.List;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.structure.Structure;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.ship.ShipEntity;

/**
 * Sabaody's ship coating, like the one Rayleigh puts on the Thousand Sunny. Only the coaters of the Sabaody
 * Archipelago (and Fish-Man Island, for the way back up) know the craft, so you coat your ship there: sail close,
 * climb aboard and right-click her holding Ship Coating.
 *
 * A coated ship carries a bubble of air around her whole hull and can dive as deep as the sea goes (see ShipDive).
 * The coating wears while she's under the sea; when it runs out the bubble bursts and she shoots back up.
 */
public final class ShipCoating {
	private ShipCoating() {
	}

	/** How long a fresh coating lasts under the sea: 30 minutes. Time on the surface doesn't count. */
	public static final int FULL_TICKS = 20 * 60 * 30;
	/** The warning comes when this much is left. */
	public static final int WARN_TICKS = 20 * 60;

	/** Biomes where coaters work. */
	private static final List<ResourceKey<Biome>> COATER_BIOMES = List.of(
			ResourceKey.create(Registries.BIOME, OnePieceMod.id("sabaody")),
			ResourceKey.create(Registries.BIOME, OnePieceMod.id("fishman_reef")));
	/** Places with coaters even out at sea (data/onepiece/tags/worldgen/structure/coaters.json). */
	private static final TagKey<Structure> COATER_PLACES = TagKey.create(Registries.STRUCTURE, OnePieceMod.id("coaters"));
	/** How far from the ship to look for Sabaody's shore. */
	private static final int SHORE_REACH = 64;

	static void initialize() {
	}

	/** The captain (or any crewmate aboard) coats the ship with the Ship Coating in hand. */
	static void apply(ShipEntity ship, ServerPlayer player) {
		if (ShipEntity.aboard(player) != ship) {
			player.sendOverlayMessage(Component.literal("Climb aboard first, then right-click her with the coating.").withStyle(ChatFormatting.YELLOW));
			return;
		}
		if (ship.sinking) {
			return;
		}
		if (ShipDive.isDown(ship)) {
			player.sendOverlayMessage(Component.literal("You can't coat a ship under the sea.").withStyle(ChatFormatting.YELLOW));
			return;
		}
		ServerLevel level = (ServerLevel) ship.level();
		if (!nearCoaters(level, ship.blockPosition()) && !nearCoaters(level, player.blockPosition())) {
			player.sendOverlayMessage(Component.literal("Only Sabaody's coaters know how to coat a ship. Sail her right up to the Sabaody Archipelago.")
					.withStyle(ChatFormatting.YELLOW));
			return;
		}
		boolean fresh = ship.coating() <= 0;
		ship.setCoating(FULL_TICKS);
		player.getMainHandItem().consume(1, player);
		level.playSound(null, ship.getX(), ship.getY() + ship.getLayout().waterline, ship.getZ(),
				SoundEvents.BUBBLE_COLUMN_UPWARDS_AMBIENT, SoundSource.NEUTRAL, 3.0f, 0.8f);
		level.playSound(null, ship.getX(), ship.getY() + ship.getLayout().waterline, ship.getZ(),
				SoundEvents.SLIME_BLOCK_PLACE, SoundSource.NEUTRAL, 2.0f, 0.6f);
		for (ServerPlayer aboard : ShipEntity.playersAboard(ship)) {
			aboard.sendSystemMessage(Component.literal(fresh
					? "The ship is coated! A bubble of air wraps her from keel to masthead. At the wheel, hold Sprint to dive and Jump to rise. The coating lasts about 30 minutes under the sea."
					: "Fresh coating! The bubble will hold another 30 minutes under the sea.").withStyle(ChatFormatting.AQUA));
		}
	}

	/** True near Sabaody or Fish-Man Island, where coaters work. */
	public static boolean nearCoaters(ServerLevel level, BlockPos at) {
		if (level.structureManager().getStructureWithPieceAt(at, COATER_PLACES).isValid()) {
			return true;
		}
		for (int dx = -SHORE_REACH; dx <= SHORE_REACH; dx += SHORE_REACH / 2) {
			for (int dz = -SHORE_REACH; dz <= SHORE_REACH; dz += SHORE_REACH / 2) {
				BlockPos sample = at.offset(dx, 0, dz);
				for (ResourceKey<Biome> biome : COATER_BIOMES) {
					if (level.getBiome(sample).is(biome)) {
						return true;
					}
				}
			}
		}
		return false;
	}

	/** "Coating 12:30 left" for the HUD, or null if the ship isn't coated. */
	public static String describe(int ticks) {
		if (ticks <= 0) {
			return null;
		}
		int seconds = ticks / 20;
		return String.format(java.util.Locale.ROOT, "Coating %d:%02d", seconds / 60, seconds % 60);
	}
}
