package com.onepiecemod.ship;


import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * The Ship's Wheel. Place it on your ship's deck facing the front of the ship (it faces the way you look
 * when you place it), then right-click it to set sail. The whole build turns into one moving ship.
 */
public class HelmBlock extends HorizontalDirectionalBlock {
	private static final VoxelShape SHAPE = Block.box(1, 0, 1, 15, 16, 15);

	/**
	 * Ship upgrades fitted at a Galley-La Shipyard (see ShipUpgrades). They live on the wheel, so they sail with the ship
	 * and stay when she docks. Mining the wheel drops a plain one: the upgrades belong to the ship they were fitted to.
	 */
	public static final IntegerProperty HULL = IntegerProperty.create("hull", 0, ShipUpgrades.MAX_LEVEL);
	public static final IntegerProperty SAILS = IntegerProperty.create("sails", 0, ShipUpgrades.MAX_LEVEL);
	public static final IntegerProperty GUNS = IntegerProperty.create("guns", 0, ShipUpgrades.MAX_LEVEL);

	public HelmBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH).setValue(HULL, 0).setValue(SAILS, 0).setValue(GUNS, 0));
	}

	@Override
	public void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING, HULL, SAILS, GUNS);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		// You stand behind the wheel, so it points the way you are looking: toward the front of the ship.
		return defaultBlockState().setValue(FACING, context.getHorizontalDirection());
	}

	@Override
	public InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (level instanceof ServerLevel serverLevel) {
			String problem = ShipAssembler.assemble(serverLevel, pos, player);
			if (problem != null) {
				player.sendOverlayMessage(Component.literal(problem).withStyle(ChatFormatting.RED));
			} else {
				String fitted = ShipUpgrades.describe(state);
				player.sendOverlayMessage(Component.literal("Set sail! W/S to sail, A/D to turn." + (fitted.isEmpty() ? "" : "  " + fitted)));
			}
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}
}
