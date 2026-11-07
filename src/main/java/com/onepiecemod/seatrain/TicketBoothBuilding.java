package com.onepiecemod.seatrain;

import java.util.List;
import java.util.Map;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.block.Blocks;

import com.onepiecemod.advancement.AdvancementFeature;
import com.onepiecemod.building.BuildingRegistry;
import com.onepiecemod.building.Multiblock;
import com.onepiecemod.building.Parts;

/**
 * Sea Train Station: your own stop on the Sea Train. A Ticket Booth on a 5x5 platform,
 * a stretch of track along the front, a bell to call the train, lamps and a little canopy.
 * Iceburg's crews only run lines for pirates who finished the Water 7 chapter.
 */
public class TicketBoothBuilding extends Multiblock {
	public TicketBoothBuilding() {
		super(Stations.BOOTH, "Sea Train Station");
		fill("stone, brick or plank blocks for the 5x5 platform under the Ticket Booth",
				state -> Parts.STONE.test(state) || Parts.PLANKS.test(state),
				Blocks.SMOOTH_STONE.defaultBlockState(), square(-1, 2));
		atLeastAt("rails along the front edge of the platform (the track)", state -> state.is(BlockTags.RAILS),
				ring(0, 2), 5, Map.of(
						new BlockPos(-2, 0, 2), Blocks.RAIL.defaultBlockState(),
						new BlockPos(-1, 0, 2), Blocks.RAIL.defaultBlockState(),
						new BlockPos(0, 0, 2), Blocks.RAIL.defaultBlockState(),
						new BlockPos(1, 0, 2), Blocks.RAIL.defaultBlockState(),
						new BlockPos(2, 0, 2), Blocks.RAIL.defaultBlockState()));
		fill("posts for the canopy (fences, walls or logs, 2 tall) in the back corners",
				state -> Parts.RAIL.test(state) || Parts.POST.test(state),
				Blocks.DARK_OAK_FENCE.defaultBlockState(), List.of(
						new BlockPos(-2, 0, -2), new BlockPos(-2, 1, -2), new BlockPos(2, 0, -2), new BlockPos(2, 1, -2)));
		fill("planks or slabs for the canopy roof (3x5, over the back of the platform)", Parts.ROOF,
				Blocks.DARK_OAK_SLAB.defaultBlockState(), canopy());
		contains("Bell to call the train", state -> state.is(Blocks.BELL), new BlockPos(-3, -1, -3), new BlockPos(3, 3, 3), 1);
		contains("lanterns or lamps", Parts.LANTERN, new BlockPos(-3, -1, -3), new BlockPos(3, 3, 3), 2);

		planLine("Platform: a 5x5 square of stone, bricks or planks.");
		planLine("The Ticket Booth goes in the middle of the platform.");
		planLine("Track: at least 5 rails on the edge of the platform (the ghosts show the front edge).");
		planLine("Canopy: a fence post 2 tall in each back corner, and a 3x5 roof of planks or slabs on top.");
		planLine("Hang a Bell and 2 lanterns anywhere on the station.");
		planLine("Needs the Water 7 chapter finished. Then ride to any Sea Train stop you've visited, for Coal.");
	}

	/** The roof: 5 wide, 3 deep, 2 blocks over the platform's back half. */
	private static List<BlockPos> canopy() {
		List<BlockPos> list = new java.util.ArrayList<>();
		for (int dx = -2; dx <= 2; dx++) {
			for (int dz = -2; dz <= 0; dz++) {
				list.add(new BlockPos(dx, 2, dz));
			}
		}
		return list;
	}

	@Override
	public String purpose() {
		return "Right-click the Ticket Booth to ride the Sea Train to any stop you've visited.";
	}

	@Override
	public void use(ServerPlayer player, BuildingRegistry.Entry here) {
		ServerLevel level = (ServerLevel) player.level();
		Stations.Station station = Stations.here(player);
		if (station == null || !station.id().equals(Stations.boothId(here.pos()))) {
			player.sendSystemMessage(Component.literal("Stand on the platform to buy a ticket.").withStyle(ChatFormatting.RED));
			return;
		}
		Stations.learn(player, station.id());
		if (here.owner().equals(player.getUUID())) {
			AdvancementFeature.grant(player, "journey/station_master");
		}
		if (!Trips.ownLinesOpen(player)) {
			player.sendSystemMessage(Component.literal("The station is ready, but nobody here can drive a Sea Train yet. "
					+ "Finish the Water 7 chapter and Iceburg's crews will run your line.").withStyle(ChatFormatting.GOLD));
			return;
		}
		level.playSound(null, here.pos(), net.minecraft.sounds.SoundEvents.BELL_BLOCK, net.minecraft.sounds.SoundSource.BLOCKS, 1.0f, 1.2f);
		SeaTrainCommands.timetable(player, station);
	}
}
