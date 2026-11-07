package com.onepiecemod.island;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BiomeTags;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.biome.Biome;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;

import com.onepiecemod.weather.SeaEventEffects;
import com.onepiecemod.world.RingBiomeSource;

/**
 * Makes each island feel like its own place:
 * - a big title ("Drum Island / A Winter Island") when you arrive, like a chapter card in the show;
 * - its climate while you're there. On a Winter Island you slowly freeze outdoors unless you wear leather
 *   or stand near a fire. On a Summer Island the midday sun makes you hungry, and metal armor makes it worse.
 * The sky, fog and music of each island live in its biome file (see tools/islands/island_look.py).
 * In a Grand Line world, plain Minecraft snow biomes are Winter too, and deserts and badlands are Summer (no title).
 * WeatherFeature calls initialize().
 */
public class IslandFeature {
	/** How long you must stay on an island before its title shows, so walking along a border doesn't flicker. */
	private static final int ARRIVE_AFTER_SECONDS = 2;
	/** Coming back to the same island within this many minutes doesn't show the title again. */
	private static final int REPEAT_TITLE_MINUTES = 5;
	/** Frost added every half second on a Winter Island. The game melts 20 in the same time, so you freeze in about 45 s. */
	private static final int WINTER_FROST = 23;
	/** Hunger from the sun every half second on a Summer Island: about one hunger point every 40 s. */
	private static final float SUMMER_EXHAUSTION = 0.05f;

	private static class Visit {
		Islands.Island island;
		String biome;
		int seconds;
		String titledBiome;
		long titledAt;
	}

	/** The climate of a plain Minecraft biome with no island of its own (no title, just the cold or the heat). */
	private static final Islands.Island WILD_WINTER = wild("winter");
	private static final Islands.Island WILD_SUMMER = wild("summer");
	/** Snow biomes are this cold or colder (snowy plains and taiga, ice spikes, groves, frozen peaks). */
	private static final float WINTER_BELOW = 0.1f;

	private static final Map<UUID, Visit> VISITS = new HashMap<>();
	/** Which climates each player has had explained this session. */
	private static final Map<UUID, Set<Islands.Climate>> TOLD = new HashMap<>();

	public static void initialize() {
		Islands.byBiome(""); // Load islands.json now, so a typo shows up at startup.
		ServerTickEvents.END_SERVER_TICK.register(IslandFeature::tick);
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
			VISITS.remove(handler.getPlayer().getUUID());
			TOLD.remove(handler.getPlayer().getUUID());
		});
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			VISITS.clear();
			TOLD.clear();
		});
	}

	private static void tick(MinecraftServer server) {
		int tick = server.getTickCount();
		if (tick % 10 != 0) {
			return;
		}
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			if (player.isSpectator() || !player.isAlive()) {
				continue;
			}
			ServerLevel level = player.level();
			Holder<Biome> holder = level.getBiome(player.blockPosition());
			String biome = holder.unwrapKey().map(key -> key.identifier().toString()).orElse("");
			Islands.Island island = Islands.byBiome(biome);
			Visit visit = VISITS.computeIfAbsent(player.getUUID(), id -> new Visit());
			if (tick % 20 == 0) {
				arrive(player, visit, biome, island, level.getGameTime());
			}
			Islands.Island climate = island != null ? island : wildClimate(level, holder, biome);
			if (climate != null && !player.isCreative()) {
				if (island == null) {
					explain(player, climate.climate());
				}
				switch (climate.climate()) {
					case WINTER -> winter(level, player, climate);
					case SUMMER -> summer(level, player, climate);
					default -> {
					}
				}
			}
		}
	}

	// ---- Arrival titles ----

	private static void arrive(ServerPlayer player, Visit visit, String biome, Islands.Island island, long now) {
		if (!biome.equals(visit.biome)) {
			visit.biome = biome;
			visit.island = island;
			visit.seconds = 0;
			return;
		}
		if (island == null || ++visit.seconds != ARRIVE_AFTER_SECONDS) {
			return;
		}
		// Both halves of Punk Hazard share a name: crossing between them is one island, so only the subtitle changes.
		boolean recently = biome.equals(visit.titledBiome) && now - visit.titledAt < REPEAT_TITLE_MINUTES * 60 * 20L;
		if (recently) {
			return;
		}
		visit.titledBiome = biome;
		visit.titledAt = now;
		player.connection.send(new ClientboundSetTitlesAnimationPacket(15, 70, 25));
		player.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal(island.subtitle).withStyle(ChatFormatting.GRAY, ChatFormatting.ITALIC)));
		player.connection.send(new ClientboundSetTitleTextPacket(Component.literal(island.name).withStyle(ChatFormatting.GOLD)));
		player.level().playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.AMBIENT, 1.0f, 0.7f);

		explain(player, island.climate());
	}

	/** The first time this session a player meets a climate, say what it does and how to beat it. */
	private static void explain(ServerPlayer player, Islands.Climate climate) {
		if (climate != Islands.Climate.MILD && TOLD.computeIfAbsent(player.getUUID(), id -> new HashSet<>()).add(climate)) {
			player.sendSystemMessage(Component.literal(climate == Islands.Climate.WINTER
					? "It's bitterly cold here. Out in the open you'll slowly freeze: wear any leather armor, or stay close to a fire."
					: "The sun here is scorching. Out in the open by day you get hungry fast, and metal armor heats up like an oven. Find shade or water.")
					.withStyle(climate == Islands.Climate.WINTER ? ChatFormatting.AQUA : ChatFormatting.GOLD));
		}
	}

	// ---- Climates ----

	private static Islands.Island wild(String climate) {
		Islands.Island island = new Islands.Island();
		island.climate = climate;
		return island;
	}

	/** Plain Minecraft biomes in a Grand Line world: snow is a Winter Island, desert and badlands a Summer Island. Seas and rivers stay mild. */
	private static Islands.Island wildClimate(ServerLevel level, Holder<Biome> holder, String biome) {
		if (!biome.startsWith("minecraft:") || !(level.getChunkSource().getGenerator().getBiomeSource() instanceof RingBiomeSource)
				|| holder.is(BiomeTags.IS_OCEAN) || holder.is(BiomeTags.IS_RIVER)) {
			return null;
		}
		if (holder.value().getBaseTemperature() < WINTER_BELOW) {
			return WILD_WINTER;
		}
		if (biome.equals("minecraft:desert") || holder.is(BiomeTags.IS_BADLANDS)) {
			return WILD_SUMMER;
		}
		return null;
	}

	private static boolean outdoors(ServerLevel level, ServerPlayer player, Islands.Island island) {
		return island.everywhere || level.canSeeSky(player.blockPosition().above());
	}

	private static void winter(ServerLevel level, ServerPlayer player, Islands.Island island) {
		if (!outdoors(level, player, island) || SeaEventEffects.isWarm(level, player)
				|| SeaEventEffects.hasFruit(player, "hie_hie_no_mi", "mera_mera_no_mi", "magu_magu_no_mi", "yuki_yuki_no_mi")) {
			return;
		}
		int frozen = player.getTicksFrozen();
		if (frozen == 0) {
			player.sendOverlayMessage(Component.literal("Brr... it's freezing here! Leather armor or a fire will warm you up.").withStyle(ChatFormatting.AQUA));
		}
		// Like standing in powder snow, only slower. Once fully frozen, the cold starts to hurt.
		player.setTicksFrozen(Math.min(player.getTicksRequiredToFreeze() + 20, frozen + WINTER_FROST));
	}

	private static void summer(ServerLevel level, ServerPlayer player, Islands.Island island) {
		if (player.isInWater() || !outdoors(level, player, island) || (!island.everywhere && !level.isBrightOutside())
				|| SeaEventEffects.hasFruit(player, "mera_mera_no_mi", "magu_magu_no_mi")) {
			return;
		}
		float exhaustion = SUMMER_EXHAUSTION * (1 + metalPieces(player) * 0.5f);
		if (SeaEventEffects.hasFruit(player, "hie_hie_no_mi", "yuki_yuki_no_mi")) {
			exhaustion *= 2; // Ice and snow users melt.
		}
		player.causeFoodExhaustion(exhaustion);
	}

	/** Iron, gold, chainmail, diamond and netherite armor pieces worn: they bake in the sun. */
	private static int metalPieces(ServerPlayer player) {
		int count = 0;
		for (EquipmentSlot slot : new EquipmentSlot[] {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET}) {
			ItemStack stack = player.getItemBySlot(slot);
			String id = BuiltInRegistries.ITEM.getKey(stack.getItem()).getPath();
			if (!stack.isEmpty() && (id.contains("iron_") || id.contains("golden_") || id.contains("chainmail_")
					|| id.contains("diamond_") || id.contains("netherite_"))) {
				count++;
			}
		}
		return count;
	}
}
