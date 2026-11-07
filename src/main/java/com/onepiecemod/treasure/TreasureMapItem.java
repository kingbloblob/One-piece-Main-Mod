package com.onepiecemod.treasure;

import java.util.List;
import java.util.Optional;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUtils;
import net.minecraft.world.item.MapItem;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.saveddata.maps.MapDecorationTypes;
import net.minecraft.world.level.saveddata.maps.MapItemSavedData;

import com.onepiecemod.character.Locations;

/**
 * A folded treasure map. Right-click it to unfold it: it picks a spot a few hundred blocks away and turns into
 * a real Minecraft map with a red X on it. The treasure is only built when someone gets close, so the spot is
 * chosen from the terrain shape alone (no structure search, which would freeze the server).
 */
public class TreasureMapItem extends Item {
	private final TreasureKind kind;

	public TreasureMapItem(TreasureKind kind, Properties properties) {
		super(properties);
		this.kind = kind;
	}

	public TreasureKind kind() {
		return kind;
	}

	@Override
	public Component getName(ItemStack stack) {
		return Component.literal(kind.closedName);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (!(level instanceof ServerLevel serverLevel)) {
			return InteractionResult.SUCCESS;
		}
		if (level.dimension() != Level.OVERWORLD) {
			player.sendSystemMessage(Component.literal("The ink swims in front of your eyes. This map only works in the seas of the Overworld.")
					.withStyle(ChatFormatting.RED));
			return InteractionResult.FAIL;
		}
		player.sendSystemMessage(Component.literal("You unfold the map and work out where it points...").withStyle(ChatFormatting.GRAY));

		TreasureKind used = kind;
		Optional<BlockPos> spot = TreasureSites.pickSpot(serverLevel, player.blockPosition(), used);
		if (spot.isEmpty() && kind != TreasureKind.HOARD) {
			// No island (or no deep sea) out here: the other kind of map fits these waters better.
			used = kind == TreasureKind.WRECK ? TreasureKind.BURIED : TreasureKind.WRECK;
			spot = TreasureSites.pickSpot(serverLevel, player.blockPosition(), used);
			if (spot.isEmpty() && kind == TreasureKind.CASTAWAY) {
				used = TreasureKind.BURIED;
				spot = TreasureSites.pickSpot(serverLevel, player.blockPosition(), used);
			}
		}
		if (spot.isEmpty()) {
			player.sendSystemMessage(Component.literal("The map doesn't match any coast around here. Try again somewhere else.")
					.withStyle(ChatFormatting.RED));
			return InteractionResult.FAIL;
		}

		BlockPos pos = spot.get();
		TreasureSites.add(serverLevel, new TreasureSites.Site(used.id, pos.getX(), pos.getY(), pos.getZ(), TreasureSites.WAITING,
				player.getUUID().toString()));

		ItemStack map = MapItem.create(serverLevel, pos.getX(), pos.getZ(), (byte) 1, true, true);
		MapItem.renderBiomePreviewMap(serverLevel, map);
		MapItemSavedData.addTargetDecoration(map, pos, "+", MapDecorationTypes.RED_X);
		map.set(DataComponents.ITEM_NAME, Component.literal(used.openName));
		map.set(DataComponents.LORE, new ItemLore(List.of(
				Component.literal(hint(used)).withStyle(ChatFormatting.GRAY),
				Component.literal(where(player.blockPosition(), pos)).withStyle(ChatFormatting.DARK_GRAY))));

		player.sendSystemMessage(Component.literal(hint(used) + " " + where(player.blockPosition(), pos)).withStyle(ChatFormatting.GOLD));
		level.playSound(null, player.blockPosition(), SoundEvents.UI_CARTOGRAPHY_TABLE_TAKE_RESULT, SoundSource.PLAYERS, 1.0f, 0.8f);

		// Like filling a bucket: the folded map becomes the open one (in creative you keep the folded one too).
		ItemStack open = ItemUtils.createFilledResult(player.getItemInHand(hand), player, map);
		return InteractionResult.SUCCESS.heldItemTransformedTo(open);
	}

	private static String hint(TreasureKind kind) {
		return switch (kind) {
			case BURIED -> "X marks the spot. Dig three blocks down.";
			case WRECK -> "A ship went down here with its treasure. Look on the sea floor.";
			case HOARD -> "A captain's hoard, buried deep. Their old crew still guards it.";
			case CASTAWAY -> "A lone palm on a sandbar in the shallows. The cache is under the X.";
		};
	}

	/** "About 420 blocks to the north-east." Distance is rounded, the X on the map is exact. */
	private static String where(BlockPos from, BlockPos to) {
		int distance = Math.round(Locations.distance(from, to) / 10.0f) * 10;
		return "About " + distance + " blocks to the " + Locations.direction(from, to) + ".";
	}
}
