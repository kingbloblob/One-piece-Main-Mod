package com.onepiecemod.crew.job;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LevelEvent;
import net.minecraft.world.level.block.state.BlockState;

import com.onepiecemod.anim.Anim;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewmateEntity;

/**
 * The archaeologist's job (like Robin). Around their post the archaeologist:
 * 1. Digs up Suspicious Sand and Suspicious Gravel and keeps what she finds.
 * 2. Studies: every few minutes she discovers something. Bookshelves nearby make her faster
 *    (3 minutes with none, down to 30 seconds with 15 or more).
 * Finds go into a nearby chest. Rare finds include diamonds and a Heart of the Sea.
 */
public class ArchaeologistWorkGoal extends WorkGoal {
	private static final List<JobHelpers.Weighted> FINDS = List.of(
			new JobHelpers.Weighted(Items.BONE, 25),
			new JobHelpers.Weighted(Items.GOLD_NUGGET, 15),
			new JobHelpers.Weighted(Items.BRICK, 10),
			new JobHelpers.Weighted(Items.EMERALD, 10),
			new JobHelpers.Weighted(Items.EXPERIENCE_BOTTLE, 6),
			new JobHelpers.Weighted(Items.ARCHER_POTTERY_SHERD, 4),
			new JobHelpers.Weighted(Items.PRIZE_POTTERY_SHERD, 4),
			new JobHelpers.Weighted(Items.SKULL_POTTERY_SHERD, 4),
			new JobHelpers.Weighted(Items.ARMS_UP_POTTERY_SHERD, 4),
			new JobHelpers.Weighted(Items.NAME_TAG, 3),
			new JobHelpers.Weighted(Items.DIAMOND, 2),
			new JobHelpers.Weighted(Items.HEART_OF_THE_SEA, 1));

	private int secondsStudied;
	private int studyTime = 180;

	public ArchaeologistWorkGoal(CrewmateEntity archaeologist) {
		super(archaeologist, CrewRole.ARCHAEOLOGIST);
	}

	@Override
	protected void workTick(ServerLevel level, BlockPos post) {
		secondsStudied++;
		if (secondsStudied % 30 == 0) {
			// Count the library every 30 seconds rather than every second; it's a big area to look at.
			int shelves = JobHelpers.count(level, post, RANGE,
					state -> state.is(Blocks.BOOKSHELF) || state.is(Blocks.CHISELED_BOOKSHELF));
			studyTime = Math.max(30, 180 - shelves * 10);
		}
		if (secondsStudied >= studyTime) {
			secondsStudied = 0;
			discover(level, "My research turned something up");
		}
	}

	@Override
	protected BlockPos findTarget(ServerLevel level, BlockPos post) {
		return JobHelpers.nearest(level, post, RANGE, worker.blockPosition(),
				(pos, state, be) -> state.is(Blocks.SUSPICIOUS_SAND) || state.is(Blocks.SUSPICIOUS_GRAVEL));
	}

	// Digging carefully.
	@Override
	protected Anim workAnim() {
		return Anim.CHOP;
	}

	@Override
	protected void act(ServerLevel level, BlockPos pos) {
		BlockState state = level.getBlockState(pos);
		Block plain = state.is(Blocks.SUSPICIOUS_SAND) ? Blocks.SAND : state.is(Blocks.SUSPICIOUS_GRAVEL) ? Blocks.GRAVEL : null;
		if (plain == null) {
			return;
		}
		level.levelEvent(LevelEvent.PARTICLES_DESTROY_BLOCK, pos, Block.getId(state));
		level.setBlock(pos, plain.defaultBlockState(), Block.UPDATE_ALL);
		level.playSound(null, pos, state.is(Blocks.SUSPICIOUS_SAND) ? SoundEvents.BRUSH_SAND_COMPLETED : SoundEvents.BRUSH_GRAVEL_COMPLETED,
				SoundSource.NEUTRAL, 1.0f, 1.0f);
		discover(level, "Look what was buried here");
	}

	private void discover(ServerLevel level, String message) {
		Item find = JobHelpers.weightedPick(level.getRandom(), FINDS);
		JobHelpers.putInBag(worker, worker.getInventory(), new ItemStack(find));
		if (find == Items.DIAMOND || find == Items.HEART_OF_THE_SEA || find == Items.NAME_TAG) {
			worker.tellCaptain(message + ": a " + new ItemStack(find).getHoverName().getString() + "!");
		}
	}

	// Everything she finds goes in the chest.
	@Override
	protected boolean shouldStore(ItemStack stack) {
		return true;
	}
}
