package com.onepiecemod.crew.job;

import java.util.List;
import java.util.function.Predicate;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Container;
import net.minecraft.world.Containers;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BarrelBlockEntity;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.block.entity.HopperBlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Small tools the crew jobs share: searching nearby blocks, moving items between bags and chests,
 * and simple recipes.
 */
public class JobHelpers {
	/** A recipe a crewmate makes from their bag without a crafting table. */
	public record Recipe(Item result, int count, List<ItemStack> ingredients) {}

	/** A test on a block: its position, its state, and its block entity (may be null). */
	public interface BlockTest {
		boolean test(BlockPos pos, BlockState state, BlockEntity blockEntity);
	}

	/** The block around `center` closest to `from` that passes the test, or null. */
	public static BlockPos nearest(ServerLevel level, BlockPos center, int range, BlockPos from, BlockTest test) {
		BlockPos best = null;
		double bestDistance = Double.MAX_VALUE;
		for (BlockPos pos : BlockPos.betweenClosed(center.offset(-range, -3, -range), center.offset(range, 3, range))) {
			BlockState state = level.getBlockState(pos);
			BlockEntity blockEntity = state.hasBlockEntity() ? level.getBlockEntity(pos) : null;
			if (test.test(pos, state, blockEntity)) {
				double distance = pos.distSqr(from);
				if (distance < bestDistance) {
					best = pos.immutable(); // betweenClosed reuses one position object, so copy it.
					bestDistance = distance;
				}
			}
		}
		return best;
	}

	/** How many blocks around `center` pass the test. */
	public static int count(ServerLevel level, BlockPos center, int range, Predicate<BlockState> test) {
		int total = 0;
		for (BlockPos pos : BlockPos.betweenClosed(center.offset(-range, -3, -range), center.offset(range, 3, range))) {
			if (test.test(level.getBlockState(pos))) {
				total++;
			}
		}
		return total;
	}

	public static boolean isChest(BlockEntity blockEntity) {
		return blockEntity instanceof ChestBlockEntity || blockEntity instanceof BarrelBlockEntity;
	}

	public static BlockPos nearestChest(ServerLevel level, BlockPos center, int range) {
		return nearest(level, center, range, center, (pos, state, be) -> isChest(be));
	}

	public static boolean hasAny(Container container, Predicate<ItemStack> test) {
		for (int i = 0; i < container.getContainerSize(); i++) {
			ItemStack stack = container.getItem(i);
			if (!stack.isEmpty() && test.test(stack)) {
				return true;
			}
		}
		return false;
	}

	/** Moves everything that passes the test from the bag into the chest, as far as it fits. */
	public static void deposit(SimpleContainer bag, Container chest, Predicate<ItemStack> test) {
		for (int i = 0; i < bag.getContainerSize(); i++) {
			ItemStack stack = bag.getItem(i);
			if (!stack.isEmpty() && test.test(stack)) {
				bag.setItem(i, HopperBlockEntity.addItem(null, chest, stack, null));
			}
		}
	}

	/** Moves the first matching stack from one container into a specific slot of another. */
	public static void moveFirst(Container from, Container to, int toSlot, Predicate<ItemStack> test) {
		for (int i = 0; i < from.getContainerSize(); i++) {
			ItemStack stack = from.getItem(i);
			if (!stack.isEmpty() && test.test(stack)) {
				to.setItem(toSlot, from.removeItemNoUpdate(i));
				return;
			}
		}
	}

	/** Takes the first matching stack from a chest into the bag. */
	public static void takeFirst(Container chest, SimpleContainer bag, Predicate<ItemStack> test) {
		for (int i = 0; i < chest.getContainerSize(); i++) {
			ItemStack stack = chest.getItem(i);
			if (!stack.isEmpty() && test.test(stack)) {
				chest.setItem(i, bag.addItem(stack.copy()));
				return;
			}
		}
	}

	/** Puts an item in the bag. If the bag is full, it drops on the ground instead of being lost. */
	public static void putInBag(Entity owner, SimpleContainer bag, ItemStack stack) {
		ItemStack leftover = bag.addItem(stack);
		if (!leftover.isEmpty()) {
			Containers.dropItemStack(owner.level(), owner.getX(), owner.getY(), owner.getZ(), leftover);
		}
	}

	/** Makes every recipe as many times as the bag allows. */
	public static void craft(Entity owner, SimpleContainer bag, List<Recipe> recipes) {
		for (Recipe recipe : recipes) {
			while (canMake(bag, recipe)) {
				for (ItemStack ingredient : recipe.ingredients()) {
					bag.removeItemType(ingredient.getItem(), ingredient.getCount());
				}
				putInBag(owner, bag, new ItemStack(recipe.result(), recipe.count()));
			}
		}
	}

	private static boolean canMake(SimpleContainer bag, Recipe recipe) {
		for (ItemStack ingredient : recipe.ingredients()) {
			if (bag.countItem(ingredient.getItem()) < ingredient.getCount()) {
				return false;
			}
		}
		return true;
	}

	/** True if the stack is one of a recipe's ingredients, so the crewmate keeps it. */
	public static boolean isIngredient(ItemStack stack, List<Recipe> recipes) {
		for (Recipe recipe : recipes) {
			for (ItemStack ingredient : recipe.ingredients()) {
				if (stack.is(ingredient.getItem())) {
					return true;
				}
			}
		}
		return false;
	}

	/** True if the chest holds an ingredient the bag doesn't have enough of yet. */
	public static boolean chestHasMissingIngredient(Container chest, SimpleContainer bag, List<Recipe> recipes) {
		for (Recipe recipe : recipes) {
			for (ItemStack ingredient : recipe.ingredients()) {
				if (bag.countItem(ingredient.getItem()) < ingredient.getCount() && chest.countItem(ingredient.getItem()) > 0) {
					return true;
				}
			}
		}
		return false;
	}

	/** Takes ingredients the bag is short of out of the chest. */
	public static void takeMissingIngredients(Container chest, SimpleContainer bag, List<Recipe> recipes) {
		for (Recipe recipe : recipes) {
			for (ItemStack ingredient : recipe.ingredients()) {
				if (bag.countItem(ingredient.getItem()) < ingredient.getCount()) {
					takeFirst(chest, bag, stack -> stack.is(ingredient.getItem()));
				}
			}
		}
	}

	/** Picks one item from a list where each entry has a weight: higher weight = more common. */
	public static Item weightedPick(RandomSource random, List<Weighted> table) {
		int total = 0;
		for (Weighted entry : table) {
			total += entry.weight();
		}
		int roll = random.nextInt(total);
		for (Weighted entry : table) {
			roll -= entry.weight();
			if (roll < 0) {
				return entry.item();
			}
		}
		return table.get(0).item();
	}

	public record Weighted(Item item, int weight) {}
}
