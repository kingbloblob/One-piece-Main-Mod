package com.onepiecemod.building;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;

import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.item.ModItems;

/**
 * All the player-built buildings (besides the Pirate Tavern, which lives with the crew code).
 * Each one has a core block and a blueprint. To add a new building: write a Multiblock subclass,
 * then add one register(...) line below, plus its block model, blueprint picture, name and recipes.
 */
public class Buildings {
	private static final Map<String, Multiblock> BUILDINGS = new LinkedHashMap<>();
	private static final Map<String, Item> BLUEPRINTS = new LinkedHashMap<>();
	private static final Map<String, Item> CORE_ITEMS = new LinkedHashMap<>();

	static {
		register(new RelayBuilding(), MapColor.COLOR_ORANGE, SoundType.COPPER);
		register(new ShipyardBuilding(), MapColor.WOOD, SoundType.WOOD);
		register(new DojoBuilding(), MapColor.COLOR_RED, SoundType.WOOD);
		register(new WatchtowerBuilding(), MapColor.STONE, SoundType.METAL);
		register(new FeastBuilding(), MapColor.COLOR_YELLOW, SoundType.WOOD);
		register(new VaultBuilding(), MapColor.METAL, SoundType.METAL);
		register(new com.onepiecemod.seatrain.TicketBoothBuilding(), MapColor.COLOR_BLUE, SoundType.WOOD); // Sea Train Station (seatrain package)
	}

	public static Multiblock get(String id) {
		return BUILDINGS.get(id);
	}

	public static Iterable<Multiblock> all() {
		return BUILDINGS.values();
	}

	private static void register(Multiblock building, MapColor color, SoundType sound) {
		String coreName = building.id();
		ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, OnePieceMod.id(coreName));
		Block core = Registry.register(BuiltInRegistries.BLOCK, blockKey,
				new BuildingCoreBlock(building.id(), BlockBehaviour.Properties.of().mapColor(color).strength(3.0f)
						.sound(sound).setId(blockKey)));
		building.setCore(core);
		BUILDINGS.put(building.id(), building);
		CORE_ITEMS.put(building.id(), registerItem(coreName, properties -> new BlockItem(core, properties),
				new Item.Properties().useBlockDescriptionPrefix()));
		BLUEPRINTS.put(building.id(), registerItem(building.id() + "_blueprint",
				properties -> new BlueprintItem(building.id(), properties), new Item.Properties().stacksTo(1)));
	}

	private static Item registerItem(String name, java.util.function.Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = factory.apply(properties.setId(key));
		Registry.register(BuiltInRegistries.ITEM, key, item);
		return item;
	}

	// ---------- Running the finished buildings ----------

	private static final int TICK_EVERY = 20; // Once a second.
	private static final int RECHECK_EVERY = 100; // Re-check a building's blocks every 5 seconds.

	/** Whether each building was finished the last time we looked, and when that was. */
	private record Known(boolean complete, int checkedAt) {}

	private static final Map<String, Known> KNOWN = new HashMap<>();

	public static void initialize() {
		java.util.Objects.requireNonNull(BuildingRegistry.BUILDINGS); // Registers the saved building list before worlds load (.class alone doesn't run the class, so buildings were forgotten on restart).
		VaultBuilding.initialize();
		RelayBuilding.initialize();
		BuildingOutlines.initialize();
		GhostPayload.register();

		CreativeModeTabEvents.modifyOutputEvent(ModItems.ONE_PIECE_TAB_KEY).register(output -> {
			for (String id : BUILDINGS.keySet()) {
				output.accept(BLUEPRINTS.get(id));
				output.accept(CORE_ITEMS.get(id));
			}
		});

		ServerTickEvents.END_SERVER_TICK.register(server -> {
			int now = server.getTickCount();
			if (now % TICK_EVERY != 0) {
				return;
			}
			for (ServerLevel level : server.getAllLevels()) {
				for (BuildingRegistry.Entry entry : BuildingRegistry.all(level)) {
					BlockPos pos = entry.pos();
					if (!level.isLoaded(pos) || !level.hasNearbyAlivePlayer(pos.getX(), pos.getY(), pos.getZ(), 64.0)) {
						continue;
					}
					Multiblock building = get(entry.type());
					if (building == null || !level.getBlockState(pos).is(building.core())) {
						BuildingRegistry.remove(level, pos); // The core was broken.
						continue;
					}
					if (isComplete(level, building, pos, now)) {
						building.tick(level, entry);
					}
				}
			}
		});
	}

	private static boolean isComplete(ServerLevel level, Multiblock building, BlockPos pos, int now) {
		String key = level.dimension() + "|" + pos.asLong();
		Known known = KNOWN.get(key);
		if (known == null || now - known.checkedAt() >= RECHECK_EVERY) {
			known = new Known(building.check(level, pos).complete(), now);
			KNOWN.put(key, known);
		}
		return known.complete();
	}
}
