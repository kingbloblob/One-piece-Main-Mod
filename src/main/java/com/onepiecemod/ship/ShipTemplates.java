package com.onepiecemod.ship;

import java.io.BufferedReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.TreeMap;

import com.google.gson.Gson;

import org.jetbrains.annotations.Nullable;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderGetter;
import net.minecraft.core.Vec3i;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.packs.resources.Resource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;

import com.onepiecemod.OnePieceMod;

/**
 * The famous ships, built block by block to look like they do in the show (Going Merry, Thousand Sunny, Marine
 * warships, Buggy's Big Top...). Each one is a structure template plus a little json file:
 *
 *   data/onepiece/structure/ships/<id>.nbt   the blocks (made by tools/ships/build.py)
 *   data/onepiece/ships/<id>.json            name, which way the bow points, how deep it sits, who sails it
 *
 * layout() turns a template into a ShipLayout that ShipEntity can sail. Data packs can add ships the same way.
 */
public class ShipTemplates {
	/** One ship's json file. */
	public static class Spec {
		public String name = "Ship";
		public String template;
		public String bow = "east";
		public float waterline = 3;
		public String faction = "pirate";
		public List<Integer> tiers = List.of();
		@Nullable
		public String crew;
		public int length;
		public int beam;
		public int height;
		public int blocks;

		public String id = "";

		public Direction bowDirection() {
			Direction direction = Direction.byName(bow);
			return direction == null || direction.getAxis().isVertical() ? Direction.EAST : direction;
		}

		/** The ship's name tag: "Big Top (Buggy Pirates)" or just "Marine Warship". */
		public Component displayName() {
			return Component.literal(crew == null || crew.isBlank() || crew.equals(name) ? name : name + " (" + crew + ")");
		}
	}

	private static final Gson GSON = new Gson();
	private static Map<String, Spec> specs = null;
	private static final Map<String, List<ShipLayout.ShipBlock>> BLOCKS = new HashMap<>();
	private static final Map<String, BlockPos> HELMS = new HashMap<>();

	public static void initialize() {
		// Ships are data, so forget them whenever the data packs change.
		ServerLifecycleEvents.END_DATA_PACK_RELOAD.register((server, resources, success) -> clear());
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> clear());
	}

	private static synchronized void clear() {
		specs = null;
		BLOCKS.clear();
		HELMS.clear();
	}

	/** Every ship the server knows, by id (sorted). */
	public static synchronized Map<String, Spec> specs(MinecraftServer server) {
		if (specs == null) {
			Map<String, Spec> found = new TreeMap<>();
			Map<Identifier, Resource> files = server.getResourceManager().listResources("ships", id -> id.getPath().endsWith(".json"));
			for (Map.Entry<Identifier, Resource> entry : files.entrySet()) {
				String path = entry.getKey().getPath();
				String id = path.substring("ships/".length(), path.length() - ".json".length());
				try (BufferedReader reader = entry.getValue().openAsReader()) {
					Spec spec = GSON.fromJson(reader, Spec.class);
					if (spec == null || spec.template == null) {
						continue;
					}
					spec.id = id;
					if (spec.tiers == null) {
						spec.tiers = List.of();
					}
					found.put(id, spec);
				} catch (Exception e) {
					OnePieceMod.LOGGER.warn("Bad ship file {}: {}", entry.getKey(), e.toString());
				}
			}
			specs = found;
		}
		return specs;
	}

	@Nullable
	public static Spec spec(MinecraftServer server, String id) {
		return specs(server).get(id);
	}

	/** Ships of one faction ("pirate" or "marine") that show up at an enemy tier. */
	public static List<Spec> forTier(MinecraftServer server, String faction, int tier) {
		List<Spec> result = new ArrayList<>();
		for (Spec spec : specs(server).values()) {
			if (faction.equals(spec.faction) && spec.tiers.contains(tier)) {
				result.add(spec);
			}
		}
		return result;
	}

	/**
	 * A fresh layout of a ship, ready for ShipEntity.setLayout. Null if the ship or its template is missing.
	 * Every call gives its own copy, because chest contents are written into the layout while the ship sails.
	 */
	@Nullable
	public static ShipLayout layout(ServerLevel level, String id) {
		Spec spec = spec(level.getServer(), id);
		if (spec == null) {
			return null;
		}
		List<ShipLayout.ShipBlock> blocks;
		BlockPos helm;
		synchronized (ShipTemplates.class) {
			if (!BLOCKS.containsKey(id)) {
				if (!read(level, spec)) {
					return null;
				}
			}
			blocks = BLOCKS.get(id);
			helm = HELMS.get(id);
		}
		List<ShipLayout.ShipBlock> copy = new ArrayList<>(blocks.size());
		for (ShipLayout.ShipBlock block : blocks) {
			copy.add(new ShipLayout.ShipBlock(block.pos(), block.state(), block.nbt().map(CompoundTag::copy)));
		}
		return new ShipLayout(copy, List.of(), helm, spec.bowDirection(), spec.waterline);
	}

	/** Reads the template's blocks once. Positions become relative to the ship's centre, like ShipAssembler does it. */
	private static boolean read(ServerLevel level, Spec spec) {
		Identifier templateId = Identifier.tryParse(spec.template);
		Optional<StructureTemplate> template = templateId == null ? Optional.empty() : level.getStructureTemplateManager().get(templateId);
		if (template.isEmpty()) {
			OnePieceMod.LOGGER.warn("Ship {} has no template {}", spec.id, spec.template);
			return false;
		}
		CompoundTag tag = template.get().save(new CompoundTag());
		HolderGetter<Block> blockLookup = level.registryAccess().lookupOrThrow(Registries.BLOCK);

		// A template with one palette stores it as "palette"; a randomised one as "palettes" (we take the first).
		ListTag palette = tag.getList("palette").orElse(null);
		if (palette == null) {
			ListTag palettes = tag.getListOrEmpty("palettes");
			palette = palettes.size() > 0 && palettes.get(0) instanceof ListTag first ? first : new ListTag();
		}
		List<BlockState> states = new ArrayList<>();
		for (int i = 0; i < palette.size(); i++) {
			states.add(NbtUtils.readBlockState(blockLookup, palette.getCompoundOrEmpty(i)));
		}

		Vec3i size = template.get().getSize();
		BlockPos anchor = new BlockPos(Math.floorDiv(size.getX() - 1, 2), 0, Math.floorDiv(size.getZ() - 1, 2));
		Direction bow = spec.bowDirection();
		List<ShipLayout.ShipBlock> blocks = new ArrayList<>();
		BlockPos helm = null;
		ListTag list = tag.getListOrEmpty("blocks");
		for (int i = 0; i < list.size(); i++) {
			CompoundTag entry = list.getCompoundOrEmpty(i);
			ListTag pos = entry.getListOrEmpty("pos");
			int stateIndex = entry.getIntOr("state", -1);
			if (pos.size() < 3 || stateIndex < 0 || stateIndex >= states.size()) {
				continue;
			}
			BlockState state = states.get(stateIndex);
			if (state.isAir()) {
				continue;
			}
			BlockPos at = new BlockPos(pos.getIntOr(0, 0), pos.getIntOr(1, 0), pos.getIntOr(2, 0)).subtract(anchor);
			if (state.is(ShipFeature.HELM)) {
				state = state.setValue(HelmBlock.FACING, bow);
				if (helm == null || at.getY() > helm.getY()) {
					helm = at;
				}
			}
			Optional<CompoundTag> nbt = entry.getCompound("nbt");
			blocks.add(new ShipLayout.ShipBlock(at, state, nbt));
		}
		if (helm == null) {
			OnePieceMod.LOGGER.warn("Ship {} has no Ship's Wheel; the captain will stand at its centre", spec.id);
			helm = new BlockPos(0, size.getY(), 0);
		}
		BLOCKS.put(spec.id, List.copyOf(blocks));
		HELMS.put(spec.id, helm);
		return true;
	}

	/**
	 * Puts a ship on the sea with its waterline at `surface` (the Y of the water's top), heading `yaw` degrees.
	 * Returns null if the ship is unknown.
	 */
	@Nullable
	public static ShipEntity spawn(ServerLevel level, String id, double x, double surface, double z, float yaw) {
		ShipLayout layout = layout(level, id);
		if (layout == null) {
			return null;
		}
		ShipEntity ship = ShipFeature.SHIP.create(level, EntitySpawnReason.EVENT);
		if (ship == null) {
			return null;
		}
		ship.setLayout(layout);
		ship.snapTo(Mth.floor(x) + 0.5, surface - layout.waterline, Mth.floor(z) + 0.5, yaw, 0);
		Spec spec = spec(level.getServer(), id);
		if (spec != null) {
			ship.setCustomName(spec.displayName());
		}
		level.addFreshEntity(ship);
		return ship;
	}

	/** How much open water a ship needs around its centre to be launched or to appear. */
	public static int clearance(Spec spec) {
		return Math.max(spec.length, spec.beam) / 2 + 2;
	}
}
