package com.onepiecemod.crew.job;

import java.util.Map;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Container;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.AnvilBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewmateEntity;

/**
 * The shipwright's job (like Franky). Around their post the shipwright:
 * 1. Repairs damaged tools, weapons and armor in their bag or in a nearby chest.
 *    Each Iron Ingot fixes a quarter of an item's durability.
 * 2. Fixes cracked bricks (stone, deepslate, nether, blackstone) for free.
 * 3. Fixes damaged anvils, one step per Iron Ingot.
 * Iron comes from the shipwright's bag first, then from the chest.
 */
public class ShipwrightWorkGoal extends WorkGoal {
	private static final Map<Block, Block> CRACKED_TO_FIXED = Map.of(
			Blocks.CRACKED_STONE_BRICKS, Blocks.STONE_BRICKS,
			Blocks.CRACKED_DEEPSLATE_BRICKS, Blocks.DEEPSLATE_BRICKS,
			Blocks.CRACKED_DEEPSLATE_TILES, Blocks.DEEPSLATE_TILES,
			Blocks.CRACKED_NETHER_BRICKS, Blocks.NETHER_BRICKS,
			Blocks.CRACKED_POLISHED_BLACKSTONE_BRICKS, Blocks.POLISHED_BLACKSTONE_BRICKS);

	private static final Map<Block, Block> ANVIL_REPAIRS = Map.of(
			Blocks.DAMAGED_ANVIL, Blocks.CHIPPED_ANVIL,
			Blocks.CHIPPED_ANVIL, Blocks.ANVIL);

	/** At most this many repairs per chest visit, so it takes a little time. */
	private static final int REPAIRS_PER_VISIT = 4;

	public ShipwrightWorkGoal(CrewmateEntity shipwright) {
		super(shipwright, CrewRole.SHIPWRIGHT);
	}

	@Override
	protected void workTick(ServerLevel level, BlockPos post) {
		// Fix one thing in the bag each second, if there's iron for it.
		Container bag = worker.getInventory();
		for (int i = 0; i < bag.getContainerSize(); i++) {
			ItemStack stack = bag.getItem(i);
			if (needsRepair(stack) && useIron(null)) {
				repair(stack);
				playRepairSound(level, worker.blockPosition());
				return;
			}
		}
	}

	@Override
	protected BlockPos findTarget(ServerLevel level, BlockPos post) {
		BlockPos cracked = JobHelpers.nearest(level, post, RANGE, worker.blockPosition(),
				(pos, state, be) -> CRACKED_TO_FIXED.containsKey(state.getBlock()));
		if (cracked != null) {
			return cracked;
		}
		boolean hasIronInBag = worker.getInventory().countItem(Items.IRON_INGOT) > 0;
		BlockPos anvil = hasIronInBag ? JobHelpers.nearest(level, post, RANGE, worker.blockPosition(),
				(pos, state, be) -> ANVIL_REPAIRS.containsKey(state.getBlock())) : null;
		if (anvil != null) {
			return anvil;
		}
		return JobHelpers.nearest(level, post, RANGE, worker.blockPosition(),
				(pos, state, be) -> JobHelpers.isChest(be) && chestHasRepairWork((Container) be, hasIronInBag));
	}

	@Override
	protected void act(ServerLevel level, BlockPos pos) {
		BlockState state = level.getBlockState(pos);
		Block fixed = CRACKED_TO_FIXED.get(state.getBlock());
		if (fixed != null) {
			level.setBlock(pos, fixed.defaultBlockState(), Block.UPDATE_ALL);
			playRepairSound(level, pos);
			return;
		}

		Block betterAnvil = ANVIL_REPAIRS.get(state.getBlock());
		if (betterAnvil != null && useIron(null)) {
			level.setBlock(pos, betterAnvil.defaultBlockState().setValue(AnvilBlock.FACING, state.getValue(AnvilBlock.FACING)), Block.UPDATE_ALL);
			playRepairSound(level, pos);
			return;
		}

		BlockEntity blockEntity = level.getBlockEntity(pos);
		if (JobHelpers.isChest(blockEntity)) {
			Container chest = (Container) blockEntity;
			int repairs = 0;
			for (int i = 0; i < chest.getContainerSize() && repairs < REPAIRS_PER_VISIT; i++) {
				ItemStack stack = chest.getItem(i);
				while (needsRepair(stack) && repairs < REPAIRS_PER_VISIT && useIron(chest)) {
					repair(stack);
					repairs++;
				}
			}
			if (repairs > 0) {
				playRepairSound(level, pos);
			}
			blockEntity.setChanged();
		}
	}

	// Fully repaired gear from the bag goes back in the chest.
	@Override
	protected boolean shouldStore(ItemStack stack) {
		return stack.isDamageableItem() && !stack.isDamaged();
	}

	private static boolean needsRepair(ItemStack stack) {
		return !stack.isEmpty() && stack.isDamageableItem() && stack.isDamaged();
	}

	private static void repair(ItemStack stack) {
		stack.setDamageValue(Math.max(0, stack.getDamageValue() - Math.max(1, stack.getMaxDamage() / 4)));
	}

	private boolean chestHasRepairWork(Container chest, boolean hasIronInBag) {
		return JobHelpers.hasAny(chest, ShipwrightWorkGoal::needsRepair)
				&& (hasIronInBag || chest.countItem(Items.IRON_INGOT) > 0);
	}

	// Uses one Iron Ingot from the bag, or from the chest if the bag has none. False if there's no iron.
	private boolean useIron(Container chest) {
		if (worker.getInventory().countItem(Items.IRON_INGOT) > 0) {
			worker.getInventory().removeItemType(Items.IRON_INGOT, 1);
			return true;
		}
		if (chest != null) {
			for (int i = 0; i < chest.getContainerSize(); i++) {
				if (chest.getItem(i).is(Items.IRON_INGOT)) {
					chest.removeItem(i, 1);
					return true;
				}
			}
		}
		return false;
	}

	private static void playRepairSound(ServerLevel level, BlockPos pos) {
		level.playSound(null, pos, SoundEvents.ANVIL_USE, SoundSource.NEUTRAL, 0.5f, 1.0f);
	}
}
