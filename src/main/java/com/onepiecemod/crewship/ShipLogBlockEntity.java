package com.onepiecemod.crewship;

import java.util.UUID;

import net.minecraft.core.BlockPos;
import net.minecraft.core.NonNullList;
import net.minecraft.core.UUIDUtil;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BaseContainerBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * The Ship's Log: which crew calls this ship home (owner + homeId), and a 27-slot locker where the
 * crew's daily haul lands. It sails with the ship (its data rides in the ship's saved blocks).
 */
public class ShipLogBlockEntity extends BaseContainerBlockEntity {
	private NonNullList<ItemStack> items = NonNullList.withSize(27, ItemStack.EMPTY);
	private UUID owner;
	private UUID homeId;
	private String ownerName = "";

	public ShipLogBlockEntity(BlockPos pos, BlockState state) {
		super(CrewShipFeature.SHIP_LOG_ENTITY, pos, state);
	}

	public UUID owner() {
		return owner;
	}

	public UUID homeId() {
		return homeId;
	}

	public String ownerName() {
		return ownerName;
	}

	void claim(UUID newOwner, String name, UUID newHomeId) {
		owner = newOwner;
		ownerName = name;
		homeId = newHomeId;
		setChanged();
	}

	/** Puts a stack in the locker. Returns what didn't fit (empty if everything did). */
	public ItemStack store(ItemStack stack) {
		ItemStack rest = stack.copy();
		for (int i = 0; i < items.size() && !rest.isEmpty(); i++) {
			ItemStack slot = items.get(i);
			if (slot.isEmpty()) {
				items.set(i, rest);
				rest = ItemStack.EMPTY;
			} else if (ItemStack.isSameItemSameComponents(slot, rest) && slot.getCount() < slot.getMaxStackSize()) {
				int move = Math.min(rest.getCount(), slot.getMaxStackSize() - slot.getCount());
				slot.grow(move);
				rest.shrink(move);
			}
		}
		setChanged();
		return rest;
	}

	/** While docked: tell the saved list where the home ship is moored now. */
	public static void serverTick(Level level, BlockPos pos, BlockState state, ShipLogBlockEntity log) {
		if (!(level instanceof ServerLevel server) || log.owner == null || level.getGameTime() % 40 != 0) {
			return;
		}
		HomeShips.HomeShip home = HomeShips.of(server.getServer(), log.owner);
		if (home == null || !home.homeId().equals(log.homeId)) {
			return;
		}
		String dimension = server.dimension().identifier().toString();
		if (!dimension.equals(home.dimension()) || home.dockPos().isEmpty() || !home.dockPos().get().equals(pos)) {
			HomeShips.put(server.getServer(), log.owner, home.dockedAt(dimension, pos));
		}
	}

	// ---- Container ----

	@Override
	public int getContainerSize() {
		return items.size();
	}

	@Override
	protected NonNullList<ItemStack> getItems() {
		return items;
	}

	@Override
	protected void setItems(NonNullList<ItemStack> newItems) {
		this.items = newItems;
	}

	@Override
	protected Component getDefaultName() {
		return Component.literal("Ship's Log Locker");
	}

	@Override
	protected AbstractContainerMenu createMenu(int id, Inventory inventory) {
		return ChestMenu.threeRows(id, inventory, this);
	}

	// ---- Saving ----

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		ContainerHelper.saveAllItems(output, items);
		if (owner != null) {
			output.store("Owner", UUIDUtil.CODEC, owner);
		}
		if (homeId != null) {
			output.store("HomeId", UUIDUtil.CODEC, homeId);
		}
		output.putString("OwnerName", ownerName);
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		items = NonNullList.withSize(getContainerSize(), ItemStack.EMPTY);
		ContainerHelper.loadAllItems(input, items);
		owner = input.read("Owner", UUIDUtil.CODEC).orElse(null);
		homeId = input.read("HomeId", UUIDUtil.CODEC).orElse(null);
		ownerName = input.getStringOr("OwnerName", "");
	}
}
