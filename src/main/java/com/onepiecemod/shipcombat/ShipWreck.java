package com.onepiecemod.shipcombat;

import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.levelgen.Heightmap;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.multiplayer.SharedShips;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipLayout;

/**
 * When a player's ship sinks it isn't gone for good: it settles on the sea floor as a wreck.
 * Some planks and sails are smashed, but the chests keep everything that was in them,
 * so you can dive down, take back your loot and salvage the blocks to build her again.
 * (Marine and pirate ships still break up and float their loot to the surface, see ShipHull.)
 */
public class ShipWreck {
	/** Share of plain blocks smashed in the sinking. Chests, flags and the wheel always survive. */
	private static final float SMASHED = 0.2f;
	private static final float SAILS_TORN = 0.5f;

	private static final int QUIET = Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE | Block.UPDATE_SUPPRESS_DROPS;

	/** Puts the ship's blocks on the sea floor below where it is now and tells its crew where. */
	static void settle(ServerLevel level, ShipEntity ship) {
		ShipLayout layout = ship.getLayout();
		if (layout.size() == 0) {
			return;
		}
		int quarterTurns = Math.floorMod(Math.round(Mth.wrapDegrees(ship.rotationSinceBuilt(1.0f)) / 90f), 4);
		Rotation rotation = switch (quarterTurns) {
			case 1 -> Rotation.CLOCKWISE_90;
			case 2 -> Rotation.CLOCKWISE_180;
			case 3 -> Rotation.COUNTERCLOCKWISE_90;
			default -> Rotation.NONE;
		};
		int x = Mth.floor(ship.getX());
		int z = Mth.floor(ship.getZ());
		int floor = level.getHeight(Heightmap.Types.OCEAN_FLOOR, x, z);
		// Never higher than where she went down (a ship that sank against a cliff stays in the water).
		BlockPos anchor = new BlockPos(x, Math.min(floor, Mth.floor(ship.getY())), z);
		RandomSource random = level.getRandom();

		int placed = 0;
		for (ShipLayout.ShipBlock block : layout.blocks) {
			boolean keep = block.nbt().isPresent() || block.pos().equals(layout.helm);
			if (!keep) {
				float smash = block.state().is(BlockTags.WOOL) ? SAILS_TORN : SMASHED;
				if (random.nextFloat() < smash) {
					continue;
				}
			}
			BlockPos target = anchor.offset(block.pos().rotate(rotation));
			if (!level.isInWorldBounds(target) || !level.getBlockState(target).canBeReplaced()) {
				continue; // Rock or coral there already: the wreck breaks around it.
			}
			BlockState state = block.state().rotate(rotation);
			if (state.hasProperty(BlockStateProperties.WATERLOGGED)) {
				state = state.setValue(BlockStateProperties.WATERLOGGED, level.getFluidState(target).is(FluidTags.WATER));
			}
			level.setBlock(target, state, QUIET);
			if (block.nbt().isPresent()) {
				BlockEntity restored = BlockEntity.loadStatic(target, level.getBlockState(target), block.nbt().get(), level.registryAccess());
				if (restored != null) {
					level.setBlockEntity(restored);
				}
			}
			placed++;
		}
		OnePieceMod.LOGGER.info("Wreck of '{}' ({} blocks) settled at {}", ship.getName().getString(), placed, anchor.toShortString());

		Component where = Component.literal("The wreck of your ship lies on the sea floor at " + anchor.getX() + ", " + anchor.getY() + ", "
				+ anchor.getZ() + ". Her chests are still full: dive down and salvage her!").withStyle(ChatFormatting.AQUA);
		UUID owner = ship.getAttached(SharedShips.OWNER);
		for (ServerPlayer player : level.players()) {
			boolean crew = owner != null && SharedShips.isCrew(level.getServer(), owner, player);
			if (crew || player.distanceToSqr(ship) < 64 * 64) {
				player.sendSystemMessage(where);
			}
		}
	}
}
