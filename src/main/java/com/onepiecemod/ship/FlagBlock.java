package com.onepiecemod.ship;


import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * A placed Jolly Roger, sail or plaque. The block itself is invisible: the painting is drawn by
 * FlagRenderer on the client, using the design saved in FlagBlockEntity.
 *
 * Right-click a placed one while holding another Jolly Roger to copy its painting onto the one in your hand.
 */
public class FlagBlock extends BaseEntityBlock {	public static final EnumProperty<Direction> FACING = BlockStateProperties.HORIZONTAL_FACING;

	// A small knot in the middle, so you can see where the block is and break it.
	private static final VoxelShape KNOT = Block.box(5, 5, 5, 11, 11, 11);

	public FlagBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
	}

	@Override
	public void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		FlagDesign design = context.getItemInHand().get(ShipFeature.FLAG_DESIGN);
		int style = design != null ? design.style() : FlagDesign.STYLE_FLAG;
		Direction clicked = context.getClickedFace();
		Direction facing;
		if (style == FlagDesign.STYLE_SAIL) {
			// Sails face the way you are looking, which should be the front of your ship.
			facing = context.getHorizontalDirection();
		} else if (clicked.getAxis().isHorizontal()) {
			// Flags stick out of the side you clicked; plaques lie flat on it.
			facing = clicked;
		} else {
			facing = context.getHorizontalDirection().getClockWise();
		}
		return defaultBlockState().setValue(FACING, facing);
	}

	@Override
	public InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand, BlockHitResult hit) {
		if (!stack.is(ShipFeature.JOLLY_ROGER_ITEM)) {
			return InteractionResult.TRY_WITH_EMPTY_HAND;
		}
		if (!level.isClientSide() && level.getBlockEntity(pos) instanceof FlagBlockEntity flag) {
			stack.set(ShipFeature.FLAG_DESIGN, flag.getDesign());
			player.sendOverlayMessage(Component.literal("Copied this design onto your Jolly Roger."));
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new FlagBlockEntity(pos, state);
	}

	@Override
	public RenderShape getRenderShape(BlockState state) {
		return RenderShape.INVISIBLE;
	}

	@Override
	public VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return KNOT;
	}

	@Override
	public VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return Shapes.empty();
	}

	@Override
	public BlockState rotate(BlockState state, Rotation rotation) {
		return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
	}

	@Override
	public BlockState mirror(BlockState state, Mirror mirror) {
		return state.rotate(mirror.getRotation(state.getValue(FACING)));
	}
}
