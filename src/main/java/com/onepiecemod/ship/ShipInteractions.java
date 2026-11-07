package com.onepiecemod.ship;

import java.util.HashMap;
import java.util.Map;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.Container;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.CraftingMenu;
import net.minecraft.world.inventory.HopperMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.crafting.StationBlock;
import com.onepiecemod.crafting.StationPayloads;

/**
 * Using blocks on a ship while it sails: chests, barrels and other storage, crafting tables,
 * ender chests and the mod's crafting stations (Shipwright's Bench, Ship's Galley...).
 *
 * While sailing, the ship's blocks aren't real blocks, so right-clicking anywhere hits the ship itself.
 * We work out which ship block you are looking at by following your line of sight through the ship.
 */
public class ShipInteractions {
	/** How far you can reach a block on your ship, in blocks (same as normal). */
	private static final double REACH = 5.0;

	/** Lets other features handle their own blocks on a sailing ship first (the crewship package's Ship's Log). */
	public interface BlockUse {
		/** True if handled. index = the block's place in the ship's layout. */
		boolean use(ShipEntity ship, int index, ServerPlayer player);
	}

	public static BlockUse blockUse = (ship, index, player) -> false;

	/** Chests that are open right now, per ship, so friends looking in the same chest see the same items. */
	private static final Map<ShipEntity, Map<Integer, ShipStorage>> OPEN = new HashMap<>();

	public static void initialize() {
		// A crafting station on the ship you're aboard counts as "nearby" for crafting.
		StationPayloads.stationNearby = (player, station) ->
				ShipEntity.aboard(player) instanceof ShipEntity ship && ship.getLayout().blocks.stream()
						.anyMatch(block -> block.state().getBlock() instanceof StationBlock stationBlock && stationBlock.station() == station);
	}

	/**
	 * Tries to use the ship block the player is looking at. Returns true if something opened
	 * (so the right-click shouldn't also do anything else, like dropping anchor).
	 */
	public static boolean tryUse(ShipEntity ship, ServerPlayer player) {
		int index = lookedAtBlock(ship, player);
		if (index < 0) {
			return false;
		}
		if (blockUse.use(ship, index, player)) {
			return true;
		}
		ShipLayout.ShipBlock block = ship.getLayout().blocks.get(index);
		BlockState state = block.state();
		Component name = state.getBlock().getName();

		// The mod's crafting stations: open their normal screen.
		if (state.getBlock() instanceof StationBlock station) {
			StationPayloads.open(player, player.blockPosition(), station.station());
			return true;
		}

		// Crafting table: the normal 3x3 crafting screen.
		if (state.is(Blocks.CRAFTING_TABLE)) {
			ContainerLevelAccess access = ContainerLevelAccess.create(player.level(), player.blockPosition());
			player.openMenu(new SimpleMenuProvider((id, inventory, p) -> new CraftingMenu(id, inventory, access) {
				@Override
				public boolean stillValid(Player viewer) {
					return !ship.isRemoved() && viewer.distanceToSqr(ship) < Math.pow(ship.getBbWidth() + 8, 2);
				}
			}, name));
			return true;
		}

		// Ender chest: your own ender chest, as always.
		if (state.is(Blocks.ENDER_CHEST)) {
			player.openMenu(new SimpleMenuProvider((id, inventory, p) -> ChestMenu.threeRows(id, inventory, p.getEnderChestInventory()), name));
			return true;
		}

		// Storage: anything with an inventory saved inside it (chests, barrels, shulker boxes, hoppers...).
		if (block.nbt().isEmpty()) {
			return false;
		}
		ShipStorage storage = OPEN.computeIfAbsent(ship, s -> new HashMap<>()).get(index);
		if (storage == null) {
			BlockEntity saved = BlockEntity.loadStatic(BlockPos.ZERO, state, block.nbt().get(), player.level().registryAccess());
			if (!(saved instanceof Container container)) {
				return false;
			}
			int size = container.getContainerSize();
			if (size != 5 && (size % 9 != 0 || size > 54)) {
				// Furnaces, brewing stands and so on need the real block to work.
				player.sendOverlayMessage(Component.literal("This only works once the ship has docked.").withStyle(ChatFormatting.YELLOW));
				return true;
			}
			storage = new ShipStorage(ship, index, saved);
			OPEN.get(ship).put(index, storage);
		}
		ShipStorage chest = storage;
		player.openMenu(new SimpleMenuProvider((id, inventory, p) -> menuFor(id, inventory, chest), name));
		return true;
	}

	private static AbstractContainerMenu menuFor(int id, Inventory inventory, ShipStorage chest) {
		int size = chest.getContainerSize();
		if (size == 5) {
			return new HopperMenu(id, inventory, chest);
		}
		int rows = size / 9;
		MenuType<ChestMenu> type = switch (rows) {
			case 1 -> MenuType.GENERIC_9x1;
			case 2 -> MenuType.GENERIC_9x2;
			case 3 -> MenuType.GENERIC_9x3;
			case 4 -> MenuType.GENERIC_9x4;
			case 5 -> MenuType.GENERIC_9x5;
			default -> MenuType.GENERIC_9x6;
		};
		return new ChestMenu(type, id, inventory, chest, rows);
	}

	/**
	 * Called just before a ship docks. Closes every chest screen open on it, so the items are all saved
	 * into the ship's blocks before they become real chests again.
	 */
	public static void closeAll(ShipEntity ship, ServerLevel level) {
		Map<Integer, ShipStorage> open = OPEN.remove(ship);
		if (open == null) {
			return;
		}
		for (ServerPlayer player : level.players()) {
			boolean viewing = player.containerMenu.slots.stream().anyMatch(slot -> slot.container instanceof ShipStorage storage && open.containsValue(storage));
			if (viewing) {
				player.closeContainer();
			}
		}
		open.values().forEach(ShipStorage::close);
	}

	/** The chest of this ship block that someone has open right now, or null. Items put in it are saved into the ship. */
	public static Container openStorage(ShipEntity ship, int index) {
		Map<Integer, ShipStorage> open = OPEN.get(ship);
		return open == null ? null : open.get(index);
	}

	/** Forget a ship's open chests when it is gone (unloaded or removed). */
	public static void forget(ShipEntity ship) {
		Map<Integer, ShipStorage> open = OPEN.remove(ship);
		if (open != null) {
			open.values().forEach(ShipStorage::close);
		}
	}

	/** True if the player is looking at this ship's wheel. */
	static boolean lookingAtHelm(ShipEntity ship, Player player) {
		int index = lookedAtBlock(ship, player);
		return index >= 0 && ship.getLayout().blocks.get(index).pos().equals(ship.getLayout().helm);
	}

	/**
	 * Follows the player's line of sight into the ship and returns the index of the first ship block it
	 * hits (see ShipLayout.blocks), or -1 if it hits nothing within reach.
	 */
	private static int lookedAtBlock(ShipEntity ship, Player player) {
		// Turn the player's eye and view into the ship's own unturned coordinates.
		float radians = -ship.rotationSinceBuilt(1.0f) * Mth.DEG_TO_RAD;
		float cos = Mth.cos(radians), sin = Mth.sin(radians);
		Vec3 eye = player.getEyePosition().subtract(ship.position());
		Vec3 look = player.getViewVector(1.0f);
		Vec3 start = new Vec3(eye.x * cos - eye.z * sin, eye.y, eye.x * sin + eye.z * cos);
		Vec3 direction = new Vec3(look.x * cos - look.z * sin, look.y, look.x * sin + look.z * cos);

		// Step along the line in small steps until it lands inside a ship block.
		BlockPos last = null;
		for (double distance = 0; distance <= REACH; distance += 0.05) {
			Vec3 point = start.add(direction.scale(distance));
			// Ship blocks are centred on whole numbers sideways (the ship turns around a block's middle).
			BlockPos cell = BlockPos.containing(point.x + 0.5, point.y, point.z + 0.5);
			if (cell.equals(last)) {
				continue;
			}
			last = cell;
			int index = ship.getLayout().indexAt(cell);
			if (index >= 0) {
				return index;
			}
		}
		return -1;
	}
}
