package com.onepiecemod.character;

import java.util.List;
import java.util.Optional;
import java.util.function.BiConsumer;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.MapItem;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.ItemLore;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.saveddata.maps.MapDecorationTypes;
import net.minecraft.world.level.saveddata.maps.MapItemSavedData;

/**
 * A Sea Chart. Right-click it and it becomes a real Minecraft map with a red X on a One Piece location,
 * just like a vanilla treasure map.
 * - A blank chart (crafted) finds the nearest location that nobody has charted yet.
 * - A chart with a target (from traders and quests) always finds that place, like "Sea Chart: Alabasta".
 */
public class SeaChartItem extends Item {
	public SeaChartItem(Properties properties) {
		super(properties);
	}

	/** A chart that leads to one location, like forTarget("rain_dinners"). */
	public static ItemStack forTarget(String structureId) {
		ItemStack stack = new ItemStack(CharacterFeature.SEA_CHART);
		CompoundTag tag = new CompoundTag();
		tag.putString("Target", structureId);
		stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
		return stack;
	}

	public static String target(ItemStack stack) {
		CustomData data = stack.get(DataComponents.CUSTOM_DATA);
		return data == null ? "" : data.copyTag().getStringOr("Target", "");
	}

	@Override
	public Component getName(ItemStack stack) {
		String target = target(stack);
		return Component.literal(target.isEmpty() ? "Blank Sea Chart" : "Sea Chart: " + Locations.name(target));
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (!(level instanceof ServerLevel) || !(player instanceof ServerPlayer serverPlayer)) {
			return InteractionResult.SUCCESS;
		}
		String target = target(player.getItemInHand(hand));
		// The search runs in the background (a far one can take a while); the chart is used up when the answer comes.
		BiConsumer<ServerPlayer, Optional<Locations.Found>> done = (who, found) -> chart(who, hand, target, found);
		boolean started = target.isEmpty()
				? Locations.findUnexploredLater(serverPlayer, done)
				: Locations.findLater(serverPlayer, target, done);
		player.sendSystemMessage(Component.literal(started ? "You study the chart..." : "You're still studying a chart.").withStyle(ChatFormatting.GRAY));
		return InteractionResult.SUCCESS;
	}

	private static void chart(ServerPlayer player, InteractionHand hand, String target, Optional<Locations.Found> found) {
		ServerLevel serverLevel = (ServerLevel) player.level();
		if (found.isEmpty()) {
			player.sendSystemMessage(Component.literal(target.isEmpty()
					? "There's nothing new to chart in these seas."
					: Locations.name(target) + " isn't anywhere in these seas.").withStyle(ChatFormatting.RED));
			return;
		}

		BlockPos pos = found.get().pos();
		String name = Locations.name(found.get().id());
		player.sendSystemMessage(Component.literal(name + " is " + Locations.distance(player.blockPosition(), pos) + " blocks to the "
				+ Locations.direction(player.blockPosition(), pos) + ".").withStyle(ChatFormatting.AQUA));

		// The chart may have moved while the search ran: use the one in that hand, or any like it.
		ItemStack chart = player.getItemInHand(hand);
		if (!(chart.getItem() instanceof SeaChartItem) || !target(chart).equals(target)) {
			chart = ItemStack.EMPTY;
			for (int slot = 0; slot < player.getInventory().getContainerSize(); slot++) {
				ItemStack stack = player.getInventory().getItem(slot);
				if (stack.getItem() instanceof SeaChartItem && target(stack).equals(target)) {
					chart = stack;
					break;
				}
			}
		}
		if (chart.isEmpty()) {
			return;
		}

		// Make a vanilla map centered on the place, with a red X on it.
		ItemStack map = MapItem.create(serverLevel, pos.getX(), pos.getZ(), (byte) 2, true, true);
		MapItem.renderBiomePreviewMap(serverLevel, map);
		MapItemSavedData.addTargetDecoration(map, pos, "+", MapDecorationTypes.RED_X);
		map.set(DataComponents.ITEM_NAME, Component.literal("Sea Chart: " + name));
		map.set(DataComponents.LORE, new ItemLore(List.of(
				Component.literal("X marks " + name + " at " + pos.getX() + ", " + pos.getZ()).withStyle(ChatFormatting.GRAY))));

		serverLevel.playSound(null, player.blockPosition(), SoundEvents.UI_CARTOGRAPHY_TABLE_TAKE_RESULT, SoundSource.PLAYERS, 1.0f, 1.0f);

		boolean inHand = chart == player.getItemInHand(hand);
		chart.shrink(1);
		if (inHand && chart.isEmpty()) {
			player.setItemInHand(hand, map);
		} else if (!player.getInventory().add(map)) {
			player.drop(map, false, net.minecraft.util.Prediction.SERVER_ONLY);
		}
	}
}
