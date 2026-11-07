package com.onepiecemod.item;

import java.util.function.Consumer;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;

import com.onepiecemod.fruitdex.FirstBite;
import com.onepiecemod.power.DevilFruit;
import com.onepiecemod.power.DevilFruitPowers;
import com.onepiecemod.power.ModAttachments;

/**
 * A Devil Fruit. Eating one gives the player its power for good.
 * Just like in One Piece, eating a second fruit is deadly.
 */
public class DevilFruitItem extends Item {
	private final DevilFruit fruit;

	public DevilFruitItem(DevilFruit fruit, Properties properties) {
		super(properties);
		this.fruit = fruit;
	}

	public DevilFruit getFruit() {
		return fruit;
	}

	// Called when the player finishes eating the item.
	@Override
	public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) {
		// Powers are handled on the server only, so every player sees the same thing.
		if (level instanceof ServerLevel serverLevel && entity instanceof ServerPlayer player) {
			if (DevilFruitPowers.hasAnyFruit(player)) {
				// A body can only hold one Devil Fruit power.
				player.sendSystemMessage(Component.translatable("message.onepiece.second_fruit").withStyle(ChatFormatting.DARK_RED));
				player.kill(serverLevel);
			} else {
				player.setAttached(ModAttachments.DEVIL_FRUIT, fruit.id());
				player.sendSystemMessage(Component.translatable("message.onepiece.ate_fruit", Component.translatable(getDescriptionId())).withStyle(ChatFormatting.GOLD));
				player.sendSystemMessage(Component.translatable("fruit.onepiece." + fruit.id() + ".desc").withStyle(ChatFormatting.YELLOW));
				player.sendSystemMessage(Component.translatable("message.onepiece.power_key_hint").withStyle(ChatFormatting.GRAY));
				FirstBite.start(player, fruit);
			}
		}

		// Let Minecraft do the normal eating work, like removing the fruit from your hand.
		return super.finishUsingItem(stack, level, entity);
	}

	// The text shown when you hover over the fruit in your inventory.
	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay displayComponent, Consumer<Component> textConsumer, TooltipFlag type) {
		textConsumer.accept(Component.translatable("fruit_type.onepiece." + fruit.type().name().toLowerCase()).withStyle(ChatFormatting.DARK_PURPLE));
		textConsumer.accept(Component.translatable("tooltip.onepiece.primary_move", fruit.primary()).withStyle(ChatFormatting.GRAY));
		textConsumer.accept(Component.translatable("tooltip.onepiece.secondary_move", fruit.secondary()).withStyle(ChatFormatting.GRAY));
	}
}
