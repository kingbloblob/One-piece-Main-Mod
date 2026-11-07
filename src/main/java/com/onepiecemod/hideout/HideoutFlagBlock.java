package com.onepiecemod.hideout;

import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

import com.onepiecemod.career.Career;
import com.onepiecemod.career.Careers;
import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.empire.KingdomFlagBlockEntity;

/**
 * The Hideout Flag. Plant it on an island to claim the land around it (a 32 block circle) as your crew's hideout.
 * Right-click it for the hideout screen: its level, what the next level needs, who lives there, and the stash.
 *
 * You need a crew. One hideout per captain; break the flag to move (the stash drops).
 */
public class HideoutFlagBlock extends BaseEntityBlock {
	public static final EnumProperty<Direction> FACING = HorizontalDirectionalBlock.FACING;
	private static final VoxelShape POLE = Block.box(6, 0, 6, 10, 16, 10);

	public HideoutFlagBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FACING);
	}

	@Override
	public BlockState getStateForPlacement(BlockPlaceContext context) {
		return defaultBlockState().setValue(FACING, context.getHorizontalDirection().getOpposite());
	}

	@Override
	protected BlockState rotate(BlockState state, Rotation rotation) {
		return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
	}

	@Override
	protected BlockState mirror(BlockState state, Mirror mirror) {
		return state.rotate(mirror.getRotation(state.getValue(FACING)));
	}

	@Override
	public void setPlacedBy(Level level, BlockPos pos, BlockState state, LivingEntity placer, ItemStack stack) {
		super.setPlacedBy(level, pos, state, placer, stack);
		if (!(level instanceof ServerLevel serverLevel) || !(placer instanceof ServerPlayer player)) {
			return;
		}
		String problem = whyNot(serverLevel, player, pos);
		if (problem != null) {
			player.sendSystemMessage(Component.literal(problem).withStyle(ChatFormatting.RED));
			level.destroyBlock(pos, !player.isCreative());
			return;
		}
		if (level.getBlockEntity(pos) instanceof HideoutFlagBlockEntity flag) {
			flag.claim(player);
			Crew crew = player.getAttached(CrewAttachments.CREW);
			String name = crew != null ? crew.name() : player.getName().getString() + "'s crew";
			Hideouts.put(serverLevel.getServer(), player.getUUID(),
					new Hideouts.Hideout(pos, name, 0, 0, com.onepiecemod.bounty.Bounty.threatLevel(player), serverLevel.getGameTime(),
							0, 0, "", 0, 0));
			level.playSound(null, pos, SoundEvents.PLAYER_LEVELUP, SoundSource.BLOCKS, 0.8f, 0.7f);
			player.sendSystemMessage(Component.literal("You planted your flag! This land is now the hideout of the " + name + ".")
					.withStyle(ChatFormatting.GOLD));
			player.sendSystemMessage(Component.literal("Make camp: put down a bed and a campfire nearby. Then set crewmates to Work here "
					+ "and they'll live at the hideout. Right-click the flag to see what to build next.").withStyle(ChatFormatting.YELLOW));
		}
	}

	/** Why this player can't plant a hideout flag here, or null if they can. */
	private static String whyNot(ServerLevel level, ServerPlayer player, BlockPos pos) {
		if (level != level.getServer().overworld()) {
			return "A hideout has to be in the Overworld, out at sea.";
		}
		if (player.getAttached(CrewAttachments.CREW) == null) {
			return "You need a crew to found a hideout. Start one with /crew create <name>.";
		}
		if (Careers.career(player) == Career.MARINE) {
			return "Marines don't run pirate hideouts.";
		}
		Hideouts.Hideout mine = Hideouts.of(level.getServer(), player.getUUID());
		if (mine != null) {
			BlockPos at = mine.pos();
			if (level.isLoaded(at) && !(level.getBlockEntity(at) instanceof HideoutFlagBlockEntity)) {
				Hideouts.remove(level.getServer(), player.getUUID()); // The old flag is gone (broken some odd way): free to move.
			} else {
				return "You already have a hideout at " + at.getX() + " " + at.getY() + " " + at.getZ() + ". Break its flag first to move.";
			}
		}
		for (java.util.Map.Entry<String, Hideouts.Hideout> entry : Hideouts.all(level.getServer()).entrySet()) {
			if (entry.getValue().pos().closerThan(pos, Hideouts.SPACING)) {
				return "Too close to the " + entry.getValue().crewName() + " hideout. Find land at least " + Hideouts.SPACING + " blocks away.";
			}
		}
		if (kingdomNear(level, pos)) {
			return "That land belongs to a pirate kingdom. Find land at least " + Hideouts.SPACING + " blocks from its flag.";
		}
		if (insideStructure(level, pos)) {
			return "You can't claim land inside a town, base or landmark. Find a quiet island of your own.";
		}
		return null;
	}

	private static boolean kingdomNear(ServerLevel level, BlockPos pos) {
		int chunks = Hideouts.SPACING / 16 + 1;
		ChunkPos center = ChunkPos.containing(pos);
		for (int cx = -chunks; cx <= chunks; cx++) {
			for (int cz = -chunks; cz <= chunks; cz++) {
				LevelChunk chunk = level.getChunkSource().getChunkNow(center.x() + cx, center.z() + cz);
				if (chunk == null) {
					continue;
				}
				for (BlockEntity entity : chunk.getBlockEntities().values()) {
					if (entity instanceof KingdomFlagBlockEntity && entity.getBlockPos().closerThan(pos, Hideouts.SPACING)) {
						return true;
					}
				}
			}
		}
		return false;
	}

	private static boolean insideStructure(ServerLevel level, BlockPos pos) {
		for (var structure : level.structureManager().getAllStructuresAt(pos).keySet()) {
			if (level.structureManager().getStructureAt(pos, structure).isValid()) {
				return true;
			}
		}
		return false;
	}

	@Override
	public InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (player instanceof ServerPlayer serverPlayer && level.getBlockEntity(pos) instanceof HideoutFlagBlockEntity flag) {
			flag.use(serverPlayer);
		}
		return InteractionResult.SUCCESS;
	}

	/** Only the crew can take the flag down (see HideoutFeature for the check that stops others). */
	static boolean mayBreak(ServerPlayer player, HideoutFlagBlockEntity flag) {
		UUID owner = flag.owner();
		return owner == null || player.isCreative() || flag.isCrew(player);
	}

	@Override
	public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new HideoutFlagBlockEntity(pos, state);
	}

	@Override
	public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		if (level.isClientSide()) {
			return null;
		}
		return createTickerHelper(type, HideoutFeature.HIDEOUT_FLAG_ENTITY, HideoutFlagBlockEntity::serverTick);
	}

	@Override
	public RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}

	@Override
	public VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return POLE;
	}
}
