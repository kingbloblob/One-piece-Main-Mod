package com.onepiecemod.farm;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;

/** The trough's fodder and the ranch timer. See RanchTroughBlock. */
public class RanchTroughBlockEntity extends BlockEntity {
	public static final int MAX_FODDER = 64;
	public static final int RANGE = 8;
	/** How often the animals come to eat, in ticks. */
	private static final int INTERVAL = 200;
	/** Each visit, each animal has a 1 in this chance to leave its product (about every 3 minutes). */
	private static final int PRODUCT_ONE_IN = 18;
	private static final int BREED_ONE_IN = 30;
	/** No more breeding once this many of one kind live around the trough. */
	private static final int HERD_CAP = 10;

	private int fodder;

	public RanchTroughBlockEntity(BlockPos pos, BlockState state) {
		super(FarmBlocks.TROUGH_ENTITY, pos, state);
	}

	public int fodder() {
		return fodder;
	}

	public void addFodder(int amount) {
		setFodder(Math.min(MAX_FODDER, fodder + amount));
	}

	private void setFodder(int value) {
		fodder = value;
		setChanged();
		if (level != null) {
			BlockState state = getBlockState();
			boolean full = fodder > 0;
			if (state.hasProperty(RanchTroughBlock.FULL) && state.getValue(RanchTroughBlock.FULL) != full) {
				level.setBlock(worldPosition, state.setValue(RanchTroughBlock.FULL, full), Block.UPDATE_CLIENTS);
			}
		}
	}

	private List<LivingEntity> animals() {
		return level.getEntitiesOfClass(LivingEntity.class, new AABB(worldPosition).inflate(RANGE), Ranching::isRanchAnimal);
	}

	public int countAnimals() {
		return level == null ? 0 : animals().size();
	}

	public static void serverTick(Level level, BlockPos pos, BlockState state, RanchTroughBlockEntity trough) {
		if (!(level instanceof ServerLevel server) || trough.fodder <= 0 || (level.getGameTime() + pos.asLong()) % INTERVAL != 0) {
			return;
		}
		List<LivingEntity> animals = trough.animals();
		List<ItemStack> made = new ArrayList<>();
		for (LivingEntity animal : animals) {
			if (trough.fodder <= 0) {
				break;
			}
			if (server.getRandom().nextInt(PRODUCT_ONE_IN) == 0) {
				trough.fodder--;
				made.add(Ranching.product(animal));
				if (server.getRandom().nextInt(5) == 0) {
					made.add(new ItemStack(FarmItems.RANCH_MANURE));
				}
				server.sendParticles(ParticleTypes.HAPPY_VILLAGER, animal.getX(), animal.getY() + animal.getBbHeight(), animal.getZ(),
						4, 0.3, 0.3, 0.3, 0.0);
			}
			if (animal instanceof Animal farm && trough.fodder >= 2 && farm.getAge() == 0 && farm.canFallInLove()
					&& server.getRandom().nextInt(BREED_ONE_IN) == 0
					&& animals.stream().filter(a -> a.getType() == farm.getType()).count() < HERD_CAP) {
				trough.fodder -= 2;
				farm.setInLove(null);
			}
		}
		trough.setFodder(trough.fodder);
		for (ItemStack stack : made) {
			trough.deliver(server, stack);
		}
	}

	/** Into a chest under or beside the trough, or on top of it if there is none. */
	private void deliver(ServerLevel server, ItemStack stack) {
		for (Direction direction : new Direction[] {Direction.DOWN, Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST}) {
			if (server.getBlockEntity(worldPosition.relative(direction)) instanceof Container chest && !(chest instanceof RanchTroughBlockEntity)) {
				stack = insert(chest, stack);
				if (stack.isEmpty()) {
					return;
				}
			}
		}
		Block.popResource(server, worldPosition.above(), stack);
	}

	private static ItemStack insert(Container chest, ItemStack stack) {
		for (int i = 0; i < chest.getContainerSize() && !stack.isEmpty(); i++) {
			ItemStack slot = chest.getItem(i);
			if (slot.isEmpty() && chest.canPlaceItem(i, stack)) {
				chest.setItem(i, stack.copy());
				stack = ItemStack.EMPTY;
			} else if (ItemStack.isSameItemSameComponents(slot, stack) && slot.getCount() < slot.getMaxStackSize()) {
				int move = Math.min(stack.getCount(), slot.getMaxStackSize() - slot.getCount());
				slot.grow(move);
				stack.shrink(move);
			}
		}
		chest.setChanged();
		return stack;
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putInt("Fodder", fodder);
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		fodder = input.getIntOr("Fodder", 0);
	}
}
