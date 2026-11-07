package com.onepiecemod.cuisine;

import java.util.List;
import java.util.function.Consumer;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;

import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.crew.CrewRole;

/**
 * One of Sanji's dishes: a meal whose buffs last a long time (8 to 20 minutes), plus Well Fed.
 * With a Cook in your crew every buff lasts half as long again, like eating at Sanji's own table.
 */
public class DishItem extends Item {
	/** How much longer the buffs last with a Cook in your crew. */
	public static final float COOK_BONUS = 1.5f;

	private final List<MobEffectInstance> effects;
	private final int wellFedLevel;

	public DishItem(Properties properties, int wellFedLevel, List<MobEffectInstance> effects) {
		super(properties);
		this.effects = effects;
		this.wellFedLevel = wellFedLevel;
	}

	@Override
	public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) {
		if (!level.isClientSide() && entity instanceof ServerPlayer player) {
			boolean cook = hasCook(player);
			float scale = cook ? COOK_BONUS : 1.0f;
			int longest = 0;
			for (MobEffectInstance effect : effects) {
				int ticks = Math.round(effect.getDuration() * scale);
				longest = Math.max(longest, ticks);
				player.addEffect(new MobEffectInstance(effect.getEffect(), ticks, effect.getAmplifier()));
			}
			player.addEffect(new MobEffectInstance(CuisineEffects.WELL_FED, longest, wellFedLevel));
			if (cook) {
				player.sendOverlayMessage(Component.literal("Your crew's cook made it even better: the buffs last longer.")
						.withStyle(ChatFormatting.GOLD));
			}
		}
		return super.finishUsingItem(stack, level, entity);
	}

	public static boolean hasCook(ServerPlayer player) {
		Crew crew = player.getAttached(CrewAttachments.CREW);
		return crew != null && crew.member(CrewRole.COOK) != null;
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> lines, TooltipFlag flag) {
		super.appendHoverText(stack, context, display, lines, flag);
		for (MobEffectInstance effect : effects) {
			lines.accept(line(effect.getEffect().value().getDisplayName(), effect.getAmplifier(), effect.getDuration()));
		}
		int longest = effects.stream().mapToInt(MobEffectInstance::getDuration).max().orElse(0);
		lines.accept(line(CuisineEffects.WELL_FED.value().getDisplayName(), wellFedLevel, longest));
		lines.accept(Component.literal("x1.5 as long with a Cook in your crew").withStyle(ChatFormatting.DARK_GRAY));
	}

	private static Component line(Component name, int amplifier, int ticks) {
		int seconds = ticks / 20;
		String time = seconds >= 60 ? (seconds / 60) + ":" + String.format("%02d", seconds % 60) : seconds + "s";
		String level = new String[] {"", " II", " III", " IV"}[Math.min(amplifier, 3)];
		return Component.empty().append(name).append(level + " (" + time + ")").withStyle(ChatFormatting.BLUE);
	}
}
