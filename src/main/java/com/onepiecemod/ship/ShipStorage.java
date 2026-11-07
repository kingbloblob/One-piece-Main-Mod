package com.onepiecemod.ship;

import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.entity.BlockEntity;

/**
 * A chest (or barrel, shulker box...) on a sailing ship, opened by a player.
 *
 * While the ship sails, the chest isn't a real block, so we load its saved contents into this box.
 * Every change is written straight back into the ship's saved blocks, so nothing is lost when you dock,
 * leave the game, or the server restarts. Everyone who opens the same chest shares one ShipStorage.
 */
public class ShipStorage extends SimpleContainer {
	private final ShipEntity ship;
	private final int blockIndex;
	private final BlockEntity savedChest; // the chest, rebuilt from the ship's saved data, used for saving
	private boolean closed;

	public ShipStorage(ShipEntity ship, int blockIndex, BlockEntity savedChest) {
		super(((Container) savedChest).getContainerSize());
		this.ship = ship;
		this.blockIndex = blockIndex;
		this.savedChest = savedChest;
		Container chest = (Container) savedChest;
		for (int i = 0; i < getContainerSize(); i++) {
			setItem(i, chest.getItem(i).copy());
		}
	}

	@Override
	public void setChanged() {
		super.setChanged();
		if (closed) {
			return; // the ship has docked: the real chest has the items now
		}
		Container chest = (Container) savedChest;
		for (int i = 0; i < getContainerSize(); i++) {
			chest.setItem(i, getItem(i).copy());
		}
		ship.getLayout().setNbt(blockIndex, savedChest.saveWithFullMetadata(ship.level().registryAccess()));
	}

	@Override
	public boolean stillValid(Player player) {
		return !closed && !ship.isRemoved() && player.distanceToSqr(ship) < Math.pow(ship.getBbWidth() + 8, 2);
	}

	/** Called when the ship docks: the real chest takes over, so this box stops working. */
	public void close() {
		closed = true;
	}
}
