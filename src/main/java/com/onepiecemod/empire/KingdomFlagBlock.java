package com.onepiecemod.empire;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;

/**
 * The Kingdom Flag. Plant it to claim the land around it (a 48 block circle) as your pirate kingdom.
 * Pirate guards move in and protect it, and every day it collects taxes. Right-click it to take the Berries.
 *
 * You need a crew to plant one. How many you may have depends on your title (1 at first, up to 8).
 */
public class KingdomFlagBlock extends BaseEntityBlock {
	private static final VoxelShape POLE = Block.box(6, 0, 6, 10, 16, 10);

	public KingdomFlagBlock(Properties properties) {
		super(properties);
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
		if (level.getBlockEntity(pos) instanceof KingdomFlagBlockEntity flag) {
			flag.claim(player);
		}
		EmpireData.addKingdom(player, pos);
		Crew crew = player.getAttached(CrewAttachments.CREW);
		String name = crew != null ? crew.name() : player.getName().getString();
		player.sendSystemMessage(Component.literal("You planted your flag! This land now belongs to the " + name + ".")
				.withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal("Pirate guards will move in (more if you build beds), and the flag collects taxes every day.")
				.withStyle(ChatFormatting.YELLOW));
	}

	/** Why this player can't plant a flag here, or null if they can. */
	private static String whyNot(ServerLevel level, ServerPlayer player, BlockPos pos) {
		if (level != level.getServer().overworld()) {
			return "A pirate kingdom has to be in the Overworld.";
		}
		if (player.getAttached(CrewAttachments.CREW) == null) {
			return "You need a crew to found a kingdom. Start one with /crew create <name>.";
		}
		EmpireRanks.forgetMissingFlags(player);
		Title title = EmpireData.title(player);
		int count = EmpireData.kingdoms(player).size();
		if (count >= title.maxKingdoms) {
			Title next = title.next();
			return "You already rule " + count + " kingdom" + (count == 1 ? "" : "s") + ", the most a "
					+ (title == Title.NONE ? "pirate without a title" : title.displayName) + " can hold."
					+ (next != null ? " Become " + next.displayName + " to rule more." : "");
		}
		for (BlockPos other : EmpireData.kingdoms(player)) {
			if (other.closerThan(pos, KingdomFlagBlockEntity.RADIUS * 2)) {
				return "Too close to your other kingdom. Plant it at least " + (int) (KingdomFlagBlockEntity.RADIUS * 2) + " blocks away.";
			}
		}
		return null;
	}

	@Override
	public InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
		if (player instanceof ServerPlayer serverPlayer && level.getBlockEntity(pos) instanceof KingdomFlagBlockEntity flag) {
			flag.use(serverPlayer);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new KingdomFlagBlockEntity(pos, state);
	}

	@Override
	public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
		if (level.isClientSide()) {
			return null;
		}
		return createTickerHelper(type, EmpireFeature.KINGDOM_FLAG_ENTITY, KingdomFlagBlockEntity::serverTick);
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
