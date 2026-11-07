package com.onepiecemod.building;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.BlockHitResult;

/**
 * The heart of a building (Relay, Training Post, Alarm Bell...). Right-click it:
 * if the building isn't finished it shows what's missing, otherwise the building does its job.
 */
public class BuildingCoreBlock extends HorizontalDirectionalBlock {
	private final String buildingId;

	public BuildingCoreBlock(String buildingId, Properties properties) {
		super(properties);
		this.buildingId = buildingId;
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
	}

	public Multiblock building() {
		return Buildings.get(buildingId);
	}

	@Override
	public void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
	}

	@Override
	public void setPlacedBy(Level level, BlockPos pos, BlockState state, LivingEntity placer, ItemStack stack) {
		super.setPlacedBy(level, pos, state, placer, stack);
		if (level instanceof ServerLevel serverLevel && placer instanceof ServerPlayer player) {
			BuildingRegistry.put(serverLevel, new BuildingRegistry.Entry(buildingId, pos.immutable(), player.getUUID(), -1L));
			BuildingOutlines.explain(player, building(), pos.immutable());
		}
	}

	@Override
	public InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (!(player instanceof ServerPlayer serverPlayer) || !(level instanceof ServerLevel serverLevel)) {
			return InteractionResult.SUCCESS;
		}
		Multiblock building = building();
		if (!building.check(serverLevel, pos).complete()) {
			BuildingOutlines.explain(serverPlayer, building, pos.immutable());
			return InteractionResult.SUCCESS;
		}
		BuildingRegistry.Entry entry = BuildingRegistry.at(serverLevel, pos);
		if (entry == null || !entry.type().equals(buildingId)) {
			// Placed some other way (like a command): whoever uses it first owns it.
			entry = new BuildingRegistry.Entry(buildingId, pos.immutable(), player.getUUID(), -1L);
			BuildingRegistry.put(serverLevel, entry);
		}
		building.use(serverPlayer, entry);
		return InteractionResult.SUCCESS;
	}
}
