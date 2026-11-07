package com.onepiecemod.building;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

import com.onepiecemod.crew.CrewBlocks;
import com.onepiecemod.crew.CrewTavern;

/**
 * Lets the Pirate Tavern (which lives in the crew code) show ghost blocks like the other buildings.
 * It asks CrewTavern what's missing and picks a block to suggest for each spot:
 * planks for the floor and roof, logs for the corner posts, and the Recruitment Board in the middle.
 */
public class TavernPlan implements GhostPlan {
	public static final TavernPlan INSTANCE = new TavernPlan();

	@Override
	public String name() {
		return "Pirate Tavern";
	}

	@Override
	public String purpose() {
		return "Right-click the Recruitment Board to meet the recruits.";
	}

	@Override
	public Check check(ServerLevel level, BlockPos boardPos) {
		CrewTavern.Check tavern = CrewTavern.check(level, boardPos);
		List<Ghost> ghosts = new ArrayList<>();
		if (!level.getBlockState(boardPos).is(CrewBlocks.RECRUITMENT_BOARD)) {
			ghosts.add(new Ghost(boardPos, CrewBlocks.RECRUITMENT_BOARD.defaultBlockState()));
		}
		for (BlockPos pos : tavern.missingBlocks()) {
			int dy = pos.getY() - boardPos.getY();
			// The floor is just under the board and the roof is on top of the posts; everything in between is a post.
			BlockState suggestion = dy < 0 || dy >= 3 ? Blocks.OAK_PLANKS.defaultBlockState() : Blocks.OAK_LOG.defaultBlockState();
			ghosts.add(new Ghost(pos, suggestion));
		}
		return new Check(ghosts, tavern.missingThings());
	}
}
