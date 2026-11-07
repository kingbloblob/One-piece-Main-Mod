package com.onepiecemod.farm;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.FarmlandBlock;
import net.minecraft.world.level.block.LevelEvent;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

import com.onepiecemod.crew.CrewMode;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.crew.job.JobHelpers;
import com.onepiecemod.crew.job.WorkGoal;

/**
 * Crew farm plots. Any crewmate (whatever their role) set to Work within a few blocks of a Straw Hat
 * Scarecrow farms there before doing their usual job. In order of importance they:
 * 1. Harvest grown crops and replant them (helping two other crops along each time).
 * 2. Sow empty farmland with seeds from their bag.
 * 3. Top up Ranch Troughs with fodder from their bag.
 * 4. Fetch seeds from a nearby chest when they have none and farmland lies empty.
 * The harvest goes into the nearest chest (WorkGoal does the walking and storing).
 */
public class FarmhandGoal extends WorkGoal {
	public static final int SCARECROW_REACH = 6;
	private static final int KEEP_SEEDS = 16;
	private static final int TOP_UP_BELOW = 32;

	private boolean scarecrowNear;
	private long checkedAt = -1000;

	public FarmhandGoal(CrewmateEntity worker) {
		super(worker, CrewRole.COOK); // The role is ignored: isWorking() below accepts every role.
	}

	@Override
	protected boolean isWorking() {
		if (worker.getTarget() != null && !worker.getTarget().isAlive()) {
			worker.setTarget(null);
		}
		return worker.getMode() == CrewMode.WORK
				&& worker.getWorkPos() != null
				&& worker.getTarget() == null
				&& worker.level() instanceof ServerLevel level
				&& scarecrowNear(level, worker.getWorkPos());
	}

	private boolean scarecrowNear(ServerLevel level, BlockPos post) {
		if (level.getGameTime() - checkedAt >= 100) {
			checkedAt = level.getGameTime();
			scarecrowNear = JobHelpers.nearest(level, post, SCARECROW_REACH, post,
					(pos, state, be) -> state.is(FarmBlocks.SCARECROW)) != null;
		}
		return scarecrowNear;
	}

	@Override
	protected BlockPos findTarget(ServerLevel level, BlockPos post) {
		SimpleContainer bag = worker.getInventory();
		BlockPos crop = JobHelpers.nearest(level, post, RANGE, worker.blockPosition(),
				(pos, state, be) -> state.getBlock() instanceof CropBlock block && block.isMaxAge(state));
		if (crop != null) {
			return crop;
		}
		boolean hasSeeds = JobHelpers.hasAny(bag, FarmhandGoal::isSeed);
		if (hasSeeds) {
			BlockPos soil = JobHelpers.nearest(level, post, RANGE, worker.blockPosition(),
					(pos, state, be) -> isEmptyFarmland(level, pos, state));
			if (soil != null) {
				return soil;
			}
		}
		if (JobHelpers.hasAny(bag, FarmhandGoal::isFodder)) {
			BlockPos trough = JobHelpers.nearest(level, post, RANGE, worker.blockPosition(),
					(pos, state, be) -> be instanceof RanchTroughBlockEntity t && t.fodder() < TOP_UP_BELOW);
			if (trough != null) {
				return trough;
			}
		}
		if (!hasSeeds && JobHelpers.count(level, post, RANGE, state -> state.getBlock() instanceof FarmlandBlock) > 0) {
			return JobHelpers.nearest(level, post, RANGE, worker.blockPosition(),
					(pos, state, be) -> JobHelpers.isChest(be) && JobHelpers.hasAny((Container) be, FarmhandGoal::isSeed)
							&& JobHelpers.nearest(level, post, RANGE, pos, (p, s, b) -> isEmptyFarmland(level, p, s)) != null);
		}
		return null;
	}

	@Override
	protected void act(ServerLevel level, BlockPos pos) {
		BlockState state = level.getBlockState(pos);
		BlockEntity blockEntity = level.getBlockEntity(pos);
		SimpleContainer bag = worker.getInventory();

		if (state.getBlock() instanceof CropBlock crop && crop.isMaxAge(state)) {
			for (ItemStack drop : Block.getDrops(state, level, pos, null)) {
				JobHelpers.putInBag(worker, bag, drop);
			}
			level.levelEvent(LevelEvent.PARTICLES_DESTROY_BLOCK, pos, Block.getId(state));
			level.setBlock(pos, crop.getStateForAge(0), Block.UPDATE_ALL);
			// A careful farmhand: the neighbours get a little help too.
			for (int i = 0; i < 2; i++) {
				FarmHelpers.boost(level, pos.offset(level.getRandom().nextInt(5) - 2, 0, level.getRandom().nextInt(5) - 2));
			}
		} else if (isEmptyFarmland(level, pos, state)) {
			for (int i = 0; i < bag.getContainerSize(); i++) {
				ItemStack seed = bag.getItem(i);
				if (isSeed(seed)) {
					BlockState planted = ((BlockItem) seed.getItem()).getBlock().defaultBlockState();
					if (planted.canSurvive(level, pos.above())) {
						level.setBlock(pos.above(), planted, Block.UPDATE_ALL);
						seed.shrink(1);
						return;
					}
				}
			}
		} else if (blockEntity instanceof RanchTroughBlockEntity trough) {
			for (int i = 0; i < bag.getContainerSize() && trough.fodder() < RanchTroughBlockEntity.MAX_FODDER; i++) {
				ItemStack stack = bag.getItem(i);
				if (isFodder(stack)) {
					int each = stack.is(Items.HAY_BLOCK) ? 9 : 1;
					int used = Math.min(stack.getCount(), (RanchTroughBlockEntity.MAX_FODDER - trough.fodder()) / each);
					trough.addFodder(used * each);
					stack.shrink(used);
				}
			}
		} else if (JobHelpers.isChest(blockEntity)) {
			JobHelpers.takeFirst((Container) blockEntity, bag, FarmhandGoal::isSeed);
			blockEntity.setChanged();
		}
	}

	@Override
	protected boolean shouldStore(ItemStack stack) {
		if (isSeed(stack)) {
			return countInBag(stack) > KEEP_SEEDS; // Keep a handful for sowing.
		}
		return true;
	}

	private int countInBag(ItemStack like) {
		int total = 0;
		SimpleContainer bag = worker.getInventory();
		for (int i = 0; i < bag.getContainerSize(); i++) {
			if (bag.getItem(i).is(like.getItem())) {
				total += bag.getItem(i).getCount();
			}
		}
		return total;
	}

	private static boolean isSeed(ItemStack stack) {
		return stack.getItem() instanceof BlockItem item && item.getBlock() instanceof CropBlock;
	}

	private static boolean isFodder(ItemStack stack) {
		return stack.is(Ranching.FODDER) && !isSeed(stack);
	}

	private static boolean isEmptyFarmland(ServerLevel level, BlockPos pos, BlockState state) {
		return state.getBlock() instanceof FarmlandBlock && level.getBlockState(pos.above()).isAir();
	}
}
