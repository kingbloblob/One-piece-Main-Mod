package com.onepiecemod.crew.job;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.LevelEvent;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.FurnaceBlockEntity;
import net.minecraft.world.level.block.entity.SmokerBlockEntity;
import net.minecraft.world.level.block.state.BlockState;

import com.onepiecemod.anim.Anim;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewmateEntity;

/**
 * The cook's job (like Sanji). Around their post the cook:
 * 1. Keeps nearby smokers and furnaces going: puts in raw food and fuel, takes out cooked food.
 * 2. Harvests fully grown crops (wheat, carrots, potatoes, beetroot) and replants them.
 * 3. Cooks simple recipes from what they carry (bread, pumpkin pie, mushroom stew).
 * 4. Drops finished food into a nearby chest or barrel, and takes raw food and fuel out of it.
 */
public class CookWorkGoal extends WorkGoal {
	private static final List<Item> RAW_FOOD = List.of(
			Items.BEEF, Items.PORKCHOP, Items.CHICKEN, Items.MUTTON, Items.RABBIT,
			Items.COD, Items.SALMON, Items.POTATO, Items.KELP);

	private static final List<JobHelpers.Recipe> RECIPES = List.of(
			new JobHelpers.Recipe(Items.BREAD, 1, List.of(new ItemStack(Items.WHEAT, 3))),
			new JobHelpers.Recipe(Items.PUMPKIN_PIE, 1, List.of(new ItemStack(Items.PUMPKIN), new ItemStack(Items.SUGAR), new ItemStack(Items.EGG))),
			new JobHelpers.Recipe(Items.MUSHROOM_STEW, 1, List.of(new ItemStack(Items.BOWL), new ItemStack(Items.RED_MUSHROOM), new ItemStack(Items.BROWN_MUSHROOM))));

	public CookWorkGoal(CrewmateEntity cook) {
		super(cook, CrewRole.COOK);
	}

	@Override
	protected void workTick(ServerLevel level, BlockPos post) {
		JobHelpers.craft(worker, worker.getInventory(), RECIPES);
	}

	@Override
	protected BlockPos findTarget(ServerLevel level, BlockPos post) {
		// Most important first: the kitchen, then the farm, then fetching supplies.
		BlockPos furnace = JobHelpers.nearest(level, post, RANGE, worker.blockPosition(),
				(pos, state, be) -> isCookingBlock(be) && furnaceNeedsMe((Container) be));
		if (furnace != null) {
			return furnace;
		}
		BlockPos crop = JobHelpers.nearest(level, post, RANGE, worker.blockPosition(),
				(pos, state, be) -> state.getBlock() instanceof CropBlock block && block.isMaxAge(state));
		if (crop != null) {
			return crop;
		}
		return JobHelpers.nearest(level, post, RANGE, worker.blockPosition(),
				(pos, state, be) -> JobHelpers.isChest(be) && chestHasSuppliesINeed((Container) be));
	}

	// Chopping and stirring.
	@Override
	protected Anim workAnim() {
		return Anim.CHOP;
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
			level.levelEvent(LevelEvent.PARTICLES_DESTROY_BLOCK, pos, Block.getId(state)); // Break particles and sound.
			level.setBlock(pos, crop.getStateForAge(0), Block.UPDATE_ALL); // Replant.
		} else if (isCookingBlock(blockEntity)) {
			tendFurnace((Container) blockEntity);
			blockEntity.setChanged();
		} else if (JobHelpers.isChest(blockEntity)) {
			Container chest = (Container) blockEntity;
			if (!JobHelpers.hasAny(bag, CookWorkGoal::isRawFood)) {
				JobHelpers.takeFirst(chest, bag, CookWorkGoal::isRawFood);
			}
			if (!JobHelpers.hasAny(bag, CookWorkGoal::isFuel)) {
				JobHelpers.takeFirst(chest, bag, CookWorkGoal::isFuel);
			}
			blockEntity.setChanged();
		}
	}

	/** Everything except supplies the cook still needs goes into the chest. */
	@Override
	protected boolean shouldStore(ItemStack stack) {
		return !isRawFood(stack) && !isFuel(stack) && !JobHelpers.isIngredient(stack, RECIPES);
	}

	private static boolean isCookingBlock(BlockEntity blockEntity) {
		return blockEntity instanceof SmokerBlockEntity || blockEntity instanceof FurnaceBlockEntity;
	}

	// Furnace slots: 0 = food going in, 1 = fuel, 2 = cooked food coming out.
	private boolean furnaceNeedsMe(Container furnace) {
		SimpleContainer bag = worker.getInventory();
		boolean hasFood = !furnace.getItem(0).isEmpty() || JobHelpers.hasAny(bag, CookWorkGoal::isRawFood);
		return !furnace.getItem(2).isEmpty()
				|| (furnace.getItem(0).isEmpty() && JobHelpers.hasAny(bag, CookWorkGoal::isRawFood))
				|| (furnace.getItem(1).isEmpty() && hasFood && JobHelpers.hasAny(bag, CookWorkGoal::isFuel));
	}

	private boolean chestHasSuppliesINeed(Container chest) {
		SimpleContainer bag = worker.getInventory();
		return (!JobHelpers.hasAny(bag, CookWorkGoal::isRawFood) && JobHelpers.hasAny(chest, CookWorkGoal::isRawFood))
				|| (!JobHelpers.hasAny(bag, CookWorkGoal::isFuel) && JobHelpers.hasAny(chest, CookWorkGoal::isFuel));
	}

	private void tendFurnace(Container furnace) {
		SimpleContainer bag = worker.getInventory();

		// Take out cooked food. Whatever doesn't fit in the bag stays in the furnace.
		ItemStack cooked = furnace.getItem(2);
		if (!cooked.isEmpty()) {
			furnace.setItem(2, bag.addItem(cooked.copy()));
		}

		// Put in raw food and fuel if those slots are empty.
		if (furnace.getItem(0).isEmpty()) {
			JobHelpers.moveFirst(bag, furnace, 0, CookWorkGoal::isRawFood);
		}
		if (furnace.getItem(1).isEmpty() && !furnace.getItem(0).isEmpty()) {
			JobHelpers.moveFirst(bag, furnace, 1, CookWorkGoal::isFuel);
		}
	}

	private static boolean isRawFood(ItemStack stack) {
		return RAW_FOOD.contains(stack.getItem());
	}

	private static boolean isFuel(ItemStack stack) {
		return stack.is(Items.COAL) || stack.is(Items.CHARCOAL) || stack.is(Items.COAL_BLOCK)
				|| stack.is(ItemTags.LOGS) || stack.is(ItemTags.PLANKS);
	}
}
