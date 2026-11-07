package com.onepiecemod.furniture;

import net.minecraft.core.BlockPos;
import net.minecraft.core.NonNullList;
import net.minecraft.network.chat.Component;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.RandomizableContainerBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * The inside of a storage furniture block. Its size comes from the block (9 or 27 slots).
 * It is a RandomizableContainerBlockEntity, so a structure can give it a loot table like a chest.
 */
public class FurnitureStorageBlockEntity extends RandomizableContainerBlockEntity {
	private NonNullList<ItemStack> items;

	public FurnitureStorageBlockEntity(BlockPos pos, BlockState state) {
		super(Furniture.STORAGE, pos, state);
		this.items = NonNullList.withSize(slotsFor(state), ItemStack.EMPTY);
	}

	private static int slotsFor(BlockState state) {
		return state.getBlock() instanceof StorageFurnitureBlock block ? block.slots() : 27;
	}

	@Override
	public int getContainerSize() {
		return items.size();
	}

	@Override
	protected NonNullList<ItemStack> getItems() {
		return items;
	}

	@Override
	protected void setItems(NonNullList<ItemStack> items) {
		this.items = items;
	}

	@Override
	protected Component getDefaultName() {
		return getBlockState().getBlock().getName();
	}

	@Override
	protected AbstractContainerMenu createMenu(int id, Inventory inventory) {
		if (items.size() == 9) {
			return new ChestMenu(MenuType.GENERIC_9x1, id, inventory, this, 1);
		}
		return ChestMenu.threeRows(id, inventory, this);
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		if (!trySaveLootTable(output)) {
			ContainerHelper.saveAllItems(output, items);
		}
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		items = NonNullList.withSize(getContainerSize(), ItemStack.EMPTY);
		if (!tryLoadLootTable(input)) {
			ContainerHelper.loadAllItems(input, items);
		}
	}
}
