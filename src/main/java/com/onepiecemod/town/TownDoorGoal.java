package com.onepiecemod.town;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

import net.minecraft.core.BlockPos;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.level.block.FenceGateBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.level.pathfinder.Node;
import net.minecraft.world.level.pathfinder.Path;

/**
 * Opens the wooden doors and fence gates on a townsperson's path, and closes them again behind them, like anyone
 * with manners. Only doors they opened themselves get closed, so a door a player left open stays open.
 * Runs alongside the routine (it takes no movement flags).
 */
public class TownDoorGoal extends Goal {
	private final TownsfolkEntity mob;
	/** Doors and gates we opened, and the tick we may start trying to close them. */
	private final Map<BlockPos, Integer> opened = new HashMap<>();

	public TownDoorGoal(TownsfolkEntity mob) {
		this.mob = mob;
	}

	@Override
	public boolean canUse() {
		return !mob.isSleeping() && (!opened.isEmpty() || !mob.getNavigation().isDone());
	}

	@Override
	public boolean requiresUpdateEveryTick() {
		return true;
	}

	@Override
	public void stop() {
		// Never leave the house standing open if we got interrupted on the doorstep.
		for (BlockPos pos : opened.keySet()) {
			setOpen(mob.level(), pos, false);
		}
		opened.clear();
	}

	@Override
	public void tick() {
		Level level = mob.level();
		Path path = mob.getNavigation().getPath();
		if (path != null && !path.isDone()) {
			int next = path.getNextNodeIndex();
			for (int i = Math.max(0, next - 1); i <= Math.min(path.getNodeCount() - 1, next + 1); i++) {
				Node node = path.getNode(i);
				BlockPos pos = new BlockPos(node.x, node.y, node.z);
				if (mob.distanceToSqr(pos.getX() + 0.5, mob.getY(), pos.getZ() + 0.5) > 2.6 * 2.6) {
					continue;
				}
				openIfClosed(level, pos);
				openIfClosed(level, pos.above()); // A gate on a step or a door seen from the step below.
			}
		}
		Iterator<Map.Entry<BlockPos, Integer>> it = opened.entrySet().iterator();
		while (it.hasNext()) {
			Map.Entry<BlockPos, Integer> entry = it.next();
			BlockPos pos = entry.getKey();
			if (mob.tickCount < entry.getValue()) {
				continue;
			}
			boolean far = mob.distanceToSqr(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5) > 3.0 * 3.0;
			if (far && !someoneInTheWay(level, pos)) {
				setOpen(level, pos, false);
				it.remove();
			} else if (mob.distanceToSqr(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5) > 32 * 32) {
				it.remove(); // Teleported away: leave it.
			}
		}
	}

	private void openIfClosed(Level level, BlockPos pos) {
		BlockState state = level.getBlockState(pos);
		boolean closedDoor = state.getBlock() instanceof DoorBlock door && door.type().canOpenByHand() && !state.getValue(DoorBlock.OPEN);
		boolean closedGate = state.getBlock() instanceof FenceGateBlock && !state.getValue(FenceGateBlock.OPEN);
		if (!closedDoor && !closedGate) {
			return;
		}
		if (closedDoor && state.getValue(DoorBlock.HALF) == net.minecraft.world.level.block.state.properties.DoubleBlockHalf.UPPER) {
			pos = pos.below();
		}
		setOpen(level, pos, true);
		opened.put(pos.immutable(), mob.tickCount + 20);
	}

	private boolean someoneInTheWay(Level level, BlockPos pos) {
		return !level.getEntitiesOfClass(LivingEntity.class, new net.minecraft.world.phys.AABB(pos).expandTowards(0, 1, 0), LivingEntity::isAlive).isEmpty();
	}

	private void setOpen(Level level, BlockPos pos, boolean open) {
		BlockState state = level.getBlockState(pos);
		if (state.getBlock() instanceof DoorBlock door) {
			if (state.getValue(DoorBlock.OPEN) != open) {
				door.setOpen(mob, level, state, pos, open);
			}
		} else if (state.getBlock() instanceof FenceGateBlock) {
			if (state.getValue(FenceGateBlock.OPEN) != open) {
				net.minecraft.core.Direction walking = net.minecraft.core.Direction.fromYRot(mob.getYRot());
				if (open && state.getValue(FenceGateBlock.FACING) == walking.getOpposite()) {
					state = state.setValue(FenceGateBlock.FACING, walking); // Swing it away from us, like a player would.
				}
				level.setBlock(pos, state.setValue(FenceGateBlock.OPEN, open), 10);
				level.playSound(null, pos, open ? SoundEvents.FENCE_GATE_OPEN : SoundEvents.FENCE_GATE_CLOSE, SoundSource.BLOCKS, 1.0f,
						level.getRandom().nextFloat() * 0.1f + 0.9f);
				level.gameEvent(mob, open ? GameEvent.BLOCK_OPEN : GameEvent.BLOCK_CLOSE, pos);
			}
		}
	}
}
