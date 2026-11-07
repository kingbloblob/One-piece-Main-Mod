package com.onepiecemod.crew.job;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.entity.BlockEntity;

import com.onepiecemod.anim.Anim;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewmateEntity;

/**
 * The navigator's job (like Nami). At their post the navigator:
 * 1. Watches the sky and tells the captain when rain, a thunderstorm or clear skies arrive.
 * 2. Makes paper from sugar cane, compasses from iron and redstone, and empty maps from paper and a compass.
 * 3. Takes those supplies from a nearby chest and puts the finished maps back in it.
 */
public class NavigatorWorkGoal extends WorkGoal {
	private static final List<JobHelpers.Recipe> RECIPES = List.of(
			new JobHelpers.Recipe(Items.PAPER, 3, List.of(new ItemStack(Items.SUGAR_CANE, 3))),
			new JobHelpers.Recipe(Items.COMPASS, 1, List.of(new ItemStack(Items.IRON_INGOT, 4), new ItemStack(Items.REDSTONE))),
			new JobHelpers.Recipe(Items.MAP, 1, List.of(new ItemStack(Items.PAPER, 8), new ItemStack(Items.COMPASS))));

	private Boolean wasRaining;
	private Boolean wasThundering;

	public NavigatorWorkGoal(CrewmateEntity navigator) {
		super(navigator, CrewRole.NAVIGATOR);
	}

	@Override
	protected void workTick(ServerLevel level, BlockPos post) {
		watchTheSky(level);
		JobHelpers.craft(worker, worker.getInventory(), RECIPES);
	}

	private void watchTheSky(ServerLevel level) {
		boolean raining = level.isRaining();
		boolean thundering = level.isThundering();
		if (wasRaining != null) {
			if (thundering && !wasThundering) {
				worker.tellCaptain("A thunderstorm is here! Watch out for lightning, Captain.");
			} else if (raining && !wasRaining) {
				worker.tellCaptain("I felt it coming. Rain is starting.");
			} else if (!raining && wasRaining) {
				worker.tellCaptain("The skies are clear again. Good sailing weather!");
			}
		}
		wasRaining = raining;
		wasThundering = thundering;
	}

	@Override
	protected BlockPos findTarget(ServerLevel level, BlockPos post) {
		return JobHelpers.nearest(level, post, RANGE, worker.blockPosition(),
				(pos, state, be) -> JobHelpers.isChest(be)
						&& JobHelpers.chestHasMissingIngredient((Container) be, worker.getInventory(), RECIPES));
	}

	// Pointing out the way.
	@Override
	protected Anim workAnim() {
		return Anim.POINT;
	}

	@Override
	protected void act(ServerLevel level, BlockPos pos) {
		BlockEntity blockEntity = level.getBlockEntity(pos);
		if (JobHelpers.isChest(blockEntity)) {
			JobHelpers.takeMissingIngredients((Container) blockEntity, worker.getInventory(), RECIPES);
			blockEntity.setChanged();
		}
	}

	@Override
	protected boolean shouldStore(ItemStack stack) {
		return stack.is(Items.MAP);
	}
}
