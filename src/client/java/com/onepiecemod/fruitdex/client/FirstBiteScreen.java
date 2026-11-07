package com.onepiecemod.fruitdex.client;

import java.util.List;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.util.Mth;
import net.minecraft.world.item.ItemStack;

import com.onepiecemod.fruitdex.FruitLore;
import com.onepiecemod.item.ModItems;
import com.onepiecemod.power.DevilFruit;
import com.onepiecemod.power.DevilFruits;

/**
 * The first-bite cutscene, shown once when you eat your first Devil Fruit.
 * The screen goes dark, the fruit shakes as you bite, a wave of the fruit's colors bursts out,
 * and then its name and powers are revealed. Click (after the bite) or press Escape to skip.
 *
 * Timeline in ticks (20 = 1 second), matched to the sounds in FirstBite on the server:
 *   0-15 fade in    15-50 bite and taste    50-75 color burst    60-190 reveal    190-210 fade out
 */
public class FirstBiteScreen extends Screen {
	private static final int END = 210;

	private final DevilFruit fruit;
	private final ItemStack stack;
	private int age = 0;

	public FirstBiteScreen(String fruitId) {
		super(Component.literal("First bite"));
		this.fruit = DevilFruits.ALL.stream().filter(f -> f.id().equals(fruitId)).findFirst().orElse(DevilFruits.ALL.get(0));
		this.stack = new ItemStack(ModItems.DEVIL_FRUITS.get(fruit.id()));
	}

	@Override
	public void tick() {
		if (++age >= END) {
			onClose();
		}
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	@Override
	public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
		if (age > 60) {
			onClose();
		}
		return true;
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		float t = age + partialTick;
		int cx = width / 2, cy = height / 2;

		// Dark curtain over the world.
		float fade = Math.min(1f, t / 15f) * Math.min(1f, (END - t) / 20f);
		graphics.fill(0, 0, width, height, alpha(0xD8 * fade) | 0x000000);

		// The fruit, big in the middle. It shakes while you bite into it.
		if (t < 55) {
			float shake = t > 18 ? (float) Math.sin(t * 2.7) * 3f : 0f;
			float scale = 3f + Math.min(t, 18f) / 18f * 2f;
			graphics.pose().pushMatrix();
			graphics.pose().translate(cx + shake, cy - 20);
			graphics.pose().scale(scale, scale);
			graphics.fakeItem(stack, -8, -8);
			graphics.pose().popMatrix();
		}
		if (t >= 20 && t < 55) {
			big(graphics, "*CHOMP*", cy + 30, 0xFFFFFFFF, 2f);
		}
		if (t >= 32 && t < 55) {
			graphics.centeredText(font, Component.literal("...it tastes horrible.").withStyle(s -> s.withItalic(true)), cx, cy + 52, 0xFFA0A0A0);
		}

		// The power bursts out in the fruit's colors.
		if (t >= 50 && t < 78) {
			float p = (t - 50) / 28f;
			graphics.fill(0, 0, width, height, alpha(0xC0 * (1 - p)) | (fruit.color() & 0xFFFFFF));
			for (int ring = 0; ring < 3; ring++) {
				float r = (p * 1.4f - ring * 0.18f) * Math.max(width, height) * 0.6f;
				if (r > 0) {
					square(graphics, cx, cy - 20, (int) r, 4, alpha(0xE0 * (1 - p)) | ((ring == 1 ? fruit.accent() : fruit.color()) & 0xFFFFFF));
				}
			}
		}

		// The reveal: name, type and powers, one line after another.
		if (t >= 60) {
			int textAlpha = alpha(255 * Math.min(1f, (t - 60) / 10f) * Math.min(1f, (END - t) / 20f));
			graphics.pose().pushMatrix();
			graphics.pose().translate(cx, cy - 20);
			graphics.pose().scale(2.5f, 2.5f);
			graphics.fakeItem(stack, -8, -8);
			graphics.pose().popMatrix();
			int y = cy + 6;

			int shown = Mth.clamp((int) ((t - 60) * 0.8f), 0, fruit.name().length());
			big(graphics, fruit.name().substring(0, shown), y, textAlpha | (fruit.color() & 0xFFFFFF), 2f);
			y += 22;
			if (t >= 85) {
				String type = FruitdexScreen.typeName(fruit.type());
				String user = FruitLore.get(fruit.id()).user();
				graphics.centeredText(font, type + " fruit  -  once eaten by " + user, cx, y, textAlpha | 0xD58CFF);
			}
			y += 14;
			if (t >= 100) {
				for (FormattedCharSequence line : wrap(Component.translatable("fruit.onepiece." + fruit.id() + ".desc").getString())) {
					graphics.centeredText(font, line, cx, y, textAlpha | 0xFFFFFF);
					y += font.lineHeight + 1;
				}
			}
			y += 6;
			if (t >= 120) {
				graphics.centeredText(font, "R: " + fruit.primary() + "     Sneak + R: " + fruit.secondary(), cx, y, textAlpha | 0xFFD75E);
			}
			y += 14;
			if (t >= 140) {
				graphics.centeredText(font, "The sea will never embrace you again.", cx, y, textAlpha | 0x6FB8FF);
			}
			graphics.centeredText(font, "Click to continue", cx, height - 16, alpha(120 * Math.min(1f, (END - t) / 20f)) | 0xFFFFFF);
		}
	}

	private List<FormattedCharSequence> wrap(String text) {
		return font.split(Component.literal(text), Math.min(300, width - 40));
	}

	/** Centered text drawn bigger than normal. */
	private void big(GuiGraphicsExtractor graphics, String text, int y, int color, float scale) {
		graphics.pose().pushMatrix();
		graphics.pose().translate(width / 2f, y);
		graphics.pose().scale(scale, scale);
		graphics.centeredText(font, text, 0, 0, color);
		graphics.pose().popMatrix();
	}

	/** The outline of a square around (x, y), used for the burst rings. */
	private static void square(GuiGraphicsExtractor graphics, int x, int y, int r, int thickness, int color) {
		graphics.fill(x - r, y - r, x + r, y - r + thickness, color);
		graphics.fill(x - r, y + r - thickness, x + r, y + r, color);
		graphics.fill(x - r, y - r + thickness, x - r + thickness, y + r - thickness, color);
		graphics.fill(x + r - thickness, y - r + thickness, x + r, y + r - thickness, color);
	}

	/** Turns 0-255 into the alpha part of a color. Never fully 0, since text treats that as "solid". */
	private static int alpha(float value) {
		return Mth.clamp((int) value, 4, 255) << 24;
	}
}
