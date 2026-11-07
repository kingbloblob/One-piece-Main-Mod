package com.onepiecemod.building;

import java.util.List;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Anything a blueprint can show as ghost blocks: the buildings in this package, and the Pirate Tavern.
 */
public interface GhostPlan {
	/** One see-through block to draw: "put this block here". */
	record Ghost(BlockPos pos, BlockState state) {}

	/**
	 * What's still missing.
	 *
	 * @param ghosts        blocks to draw as see-through ghosts
	 * @param missingThings things to list in chat, like "2 more Barrels"
	 */
	record Check(List<Ghost> ghosts, List<String> missingThings) {
		public boolean complete() {
			return ghosts.isEmpty() && missingThings.isEmpty();
		}
	}

	String name();

	/** Said when the building is done, like "Right-click the Recruitment Board to meet the recruits." */
	String purpose();

	Check check(ServerLevel level, BlockPos corePos);
}
