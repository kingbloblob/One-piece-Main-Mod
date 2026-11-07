package com.onepiecemod.ship;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.component.DataComponentGetter;
import net.minecraft.core.component.DataComponentMap;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * Remembers the painting on a placed Jolly Roger block, and sends it to players so they can see it.
 */
public class FlagBlockEntity extends BlockEntity {
	private FlagDesign design = FlagDesign.blank();

	public FlagBlockEntity(BlockPos pos, BlockState state) {
		super(ShipFeature.FLAG_BLOCK_ENTITY, pos, state);
	}

	public FlagDesign getDesign() {
		return design;
	}

	public void setDesign(FlagDesign design) {
		this.design = design;
		setChanged();
		if (level != null) {
			level.sendBlockUpdated(worldPosition, getBlockState(), getBlockState(), 3);
		}
	}

	// ---- Saving ----

	@Override
	public void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.store("Design", FlagDesign.CODEC, design);
	}

	@Override
	public void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		design = input.read("Design", FlagDesign.CODEC).orElse(FlagDesign.blank());
	}

	// ---- Item <-> block: the painting moves from the item to the block when placed, and back when broken ----

	@Override
	public void applyImplicitComponents(DataComponentGetter components) {
		super.applyImplicitComponents(components);
		FlagDesign fromItem = components.get(ShipFeature.FLAG_DESIGN);
		if (fromItem != null) {
			design = fromItem;
		}
	}

	@Override
	public void collectImplicitComponents(DataComponentMap.Builder components) {
		super.collectImplicitComponents(components);
		components.set(ShipFeature.FLAG_DESIGN, design);
	}

	// ---- Sending to players ----

	@Override
	public Packet<ClientGamePacketListener> getUpdatePacket() {
		return ClientboundBlockEntityDataPacket.create(this);
	}

	@Override
	public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
		return saveCustomOnly(registries);
	}
}
