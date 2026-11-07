package com.onepiecemod.mining;

import java.util.function.Predicate;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.vehicle.minecart.AbstractMinecartContainer;
import net.minecraft.core.registries.Registries;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;

import net.fabricmc.fabric.api.tag.convention.v2.ConventionalItemTags;

import com.onepiecemod.anim.Anim;
import com.onepiecemod.crew.CrewMode;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.crew.job.JobHelpers;
import com.onepiecemod.crew.job.WorkGoal;

/**
 * The miner's job. Any crewmate, whatever their role, set to Work within 6 blocks of a Mining Drill runs the drill
 * instead of their usual job:
 * 1. keeps it fuelled (from their bag or a chest nearby),
 * 2. fits a new drill bit from a chest when the old one wears out,
 * 3. empties Ore Carts and chest minecarts that are half full into the chests nearby,
 * 4. and while standing by, makes it dig 40% faster.
 * When the drill has nothing for them to do they go back to their own role's job.
 */
public class MinerWorkGoal extends WorkGoal {
	private static final int DRILL_RANGE = 6;
	private static final Predicate<ItemStack> FUEL = s -> MiningDrillBlockEntity.fuelValue(s) > 0;
	/** Our mined materials that aren't in the common c: tags (onepiece:mined_materials). */
	private static final TagKey<Item> MINED = TagKey.create(Registries.ITEM, com.onepiecemod.OnePieceMod.id("mined_materials"));
	private static final Predicate<ItemStack> BIT = s -> MiningFeature.bitTier(s) > 0;

	private enum Task { FUEL, FETCH_FUEL, FIT, FETCH_BIT, HAUL }

	private BlockPos drillPos;
	private long drillCheckedAt = -1000;
	private Task task;
	private AbstractMinecartContainer haulCart;

	public MinerWorkGoal(CrewmateEntity worker) {
		super(worker, null);
	}

	@Override
	protected boolean isWorking() {
		if (worker.getTarget() != null && !worker.getTarget().isAlive()) {
			worker.setTarget(null);
		}
		return worker.getMode() == CrewMode.WORK && worker.getWorkPos() != null && worker.getTarget() == null
				&& worker.level() instanceof ServerLevel && drill() != null;
	}

	/** The drill near the work post, re-found every 10 seconds. */
	private MiningDrillBlockEntity drill() {
		ServerLevel level = (ServerLevel) worker.level();
		BlockPos post = worker.getWorkPos();
		if (drillPos != null && level.getBlockEntity(drillPos) instanceof MiningDrillBlockEntity d && drillPos.closerThan(post, DRILL_RANGE + 1)) {
			return d;
		}
		if (level.getGameTime() - drillCheckedAt < 200) {
			return null;
		}
		drillCheckedAt = level.getGameTime();
		drillPos = JobHelpers.nearest(level, post, DRILL_RANGE, post, (pos, state, be) -> be instanceof MiningDrillBlockEntity);
		return drillPos == null ? null : (MiningDrillBlockEntity) level.getBlockEntity(drillPos);
	}

	@Override
	protected void workTick(ServerLevel level, BlockPos post) {
		MiningDrillBlockEntity d = drill();
		if (d != null && d.isOn() && drillPos.closerToCenterThan(worker.position(), 5.0)) {
			d.boost(level.getGameTime() + 60);
		}
	}

	@Override
	protected BlockPos findTarget(ServerLevel level, BlockPos post) {
		MiningDrillBlockEntity d = drill();
		task = null;
		haulCart = null;
		if (d == null) {
			return null;
		}
		SimpleContainer bag = worker.getInventory();
		if (d.fuel() < 64) {
			if (JobHelpers.hasAny(bag, FUEL)) {
				task = Task.FUEL;
				return drillPos;
			}
			BlockPos chest = chestWith(level, post, FUEL);
			if (chest != null) {
				task = Task.FETCH_FUEL;
				return chest;
			}
		}
		if (d.bitTier() == 0) {
			if (JobHelpers.hasAny(bag, BIT)) {
				task = Task.FIT;
				return drillPos;
			}
			BlockPos chest = chestWith(level, post, BIT);
			if (chest != null) {
				task = Task.FETCH_BIT;
				return chest;
			}
		}
		if (!JobHelpers.hasAny(bag, this::shouldStore) && JobHelpers.nearestChest(level, post, RANGE) != null) {
			for (Container c : d.outputs()) {
				if ((c instanceof OreCartBlockEntity || c instanceof AbstractMinecartContainer) && halfFull(c)) {
					task = Task.HAUL;
					if (c instanceof AbstractMinecartContainer cart) {
						haulCart = cart;
						return cart.blockPosition();
					}
					return ((BlockEntity) c).getBlockPos();
				}
			}
		}
		return null;
	}

	@Override
	protected void act(ServerLevel level, BlockPos pos) {
		if (task == null) {
			return;
		}
		SimpleContainer bag = worker.getInventory();
		switch (task) {
			case FUEL -> {
				if (level.getBlockEntity(pos) instanceof MiningDrillBlockEntity d) {
					for (int i = 0; i < bag.getContainerSize(); i++) {
						ItemStack s = bag.getItem(i);
						if (FUEL.test(s)) {
							d.addFuel(s, s.getCount(), false);
						}
					}
				}
			}
			case FIT -> {
				if (level.getBlockEntity(pos) instanceof MiningDrillBlockEntity d) {
					for (int i = 0; i < bag.getContainerSize(); i++) {
						if (BIT.test(bag.getItem(i))) {
							d.fitBit(bag.getItem(i), null);
							break;
						}
					}
				}
			}
			case FETCH_FUEL, FETCH_BIT -> {
				if (level.getBlockEntity(pos) instanceof Container chest) {
					JobHelpers.takeFirst(chest, bag, task == Task.FUEL || task == Task.FETCH_FUEL ? FUEL : BIT);
					chest.setChanged();
				}
			}
			case HAUL -> {
				Container from = haulCart != null && haulCart.isAlive() ? haulCart
						: level.getBlockEntity(pos) instanceof OreCartBlockEntity cart ? cart : null;
				if (from != null) {
					for (int i = 0; i < from.getContainerSize(); i++) {
						ItemStack s = from.getItem(i);
						if (!s.isEmpty() && shouldStore(s)) {
							from.setItem(i, bag.addItem(s.copy()));
						}
					}
					from.setChanged();
				}
			}
		}
		task = null;
	}

	@Override
	protected boolean shouldStore(ItemStack stack) {
		// Only what comes out of the ground: blocks, ores, raw metal, gems, dusts (coal is kept for the drill).
		return !FUEL.test(stack) && !BIT.test(stack) && (stack.getItem() instanceof BlockItem
				|| stack.is(ConventionalItemTags.RAW_MATERIALS) || stack.is(ConventionalItemTags.GEMS)
				|| stack.is(ConventionalItemTags.DUSTS) || stack.is(ConventionalItemTags.ORES)
				|| stack.is(MINED));
	}

	@Override
	protected Anim workAnim() {
		return null;
	}

	private static BlockPos chestWith(ServerLevel level, BlockPos post, Predicate<ItemStack> test) {
		return JobHelpers.nearest(level, post, RANGE, post,
				(pos, state, be) -> JobHelpers.isChest(be) && JobHelpers.hasAny((Container) be, test));
	}

	private static boolean halfFull(Container c) {
		int used = 0;
		for (int i = 0; i < c.getContainerSize(); i++) {
			if (!c.getItem(i).isEmpty()) {
				used++;
			}
		}
		return used * 2 >= c.getContainerSize();
	}
}
