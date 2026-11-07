package com.onepiecemod.body.client;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.AbstractSliderButton;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.network.chat.Component;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.body.Body;
import com.onepiecemod.body.BodyAttachments;
import com.onepiecemod.body.BodyFeature;
import com.onepiecemod.body.Look;

/**
 * The "Shape your body" screen: a live preview of your player on the left, sliders on the right.
 * It shows after the race picker. The first time it can't be skipped with Escape; after that
 * (opened with /body) Escape cancels without changing anything.
 */
public class BodyEditorScreen extends Screen {
	private static final int SLIDER_WIDTH = 160;
	private static final int LOOK_WIDTH = 140;
	private static final int ROW = 24;

	/** One slider: its name and the words for the low, middle and high ends. */
	private record Part(String name, String low, String mid, String high) {}

	private static final Part[] PARTS = {
			new Part("Height", "Short", "Average", "Tall"),
			new Part("Weight", "Skinny", "Average", "Heavy"),
			new Part("Chest", "Small", "Average", "Big"),
			new Part("Arms", "Thin", "Average", "Muscly"),
			new Part("Legs", "Skinny", "Average", "Big"),
			new Part("Head", "Small", "Average", "Big"),
	};

	private final boolean firstTime;
	/** Slider values from -1 to 1, in the same order as PARTS. */
	private final float[] values = new float[PARTS.length];
	private final List<Slider> sliders = new ArrayList<>();
	private int previewLeft, previewRight, slidersX, looksX, top;
	/** Hair, hair colour, scar and outfit, as indexes into the lists in Look. */
	private final int[] look = new int[4];
	private static final String[] LOOK_NAMES = {"Hair", "Hair colour", "Scar", "Outfit"};

	public BodyEditorScreen(boolean firstTime) {
		super(Component.literal("Shape your body"));
		this.firstTime = firstTime;
	}

	@Override
	protected void init() {
		// Start from your saved body, or a normal one. Only the first init: resizing the window keeps your changes.
		if (BodyClient.preview == null) {
			Body saved = minecraft.player != null ? BodyAttachments.get(minecraft.player) : null;
			setValues(saved != null ? saved : Body.DEFAULT);
			Look savedLook = minecraft.player != null ? BodyAttachments.look(minecraft.player) : Look.DEFAULT;
			look[0] = savedLook.hair();
			look[1] = savedLook.hairColor();
			look[2] = savedLook.scar();
			look[3] = savedLook.outfit();
			updatePreview();
		}

		// Preview | sliders | looks. Narrow windows get a smaller preview.
		int previewWidth = width >= 120 + 12 + SLIDER_WIDTH + 8 + LOOK_WIDTH + 16 ? 120 : 80;
		int total = previewWidth + 12 + SLIDER_WIDTH + 8 + LOOK_WIDTH;
		previewLeft = Math.max(4, (width - total) / 2);
		previewRight = previewLeft + previewWidth;
		slidersX = previewRight + 12;
		looksX = slidersX + SLIDER_WIDTH + 8;
		top = Math.max(46, (height - PARTS.length * ROW - 30) / 2);

		clearWidgets();
		sliders.clear();
		for (int i = 0; i < PARTS.length; i++) {
			sliders.add(addRenderableWidget(new Slider(i, slidersX, top + i * ROW)));
		}

		for (int i = 0; i < LOOK_NAMES.length; i++) {
			int index = i;
			Button cycle = Button.builder(Component.literal(lookLabel(i)), b -> {
				look[index] = (look[index] + 1) % lookOptions(index).size();
				b.setMessage(Component.literal(lookLabel(index)));
				updatePreview();
			}).pos(looksX, top + i * ROW).size(LOOK_WIDTH, 20).build();
			addRenderableWidget(cycle);
		}

		int buttonsY = top + PARTS.length * ROW + 6;
		int third = (SLIDER_WIDTH - 8) / 3;
		addRenderableWidget(Button.builder(Component.literal("Reset"), b -> setAll(Body.DEFAULT))
				.pos(slidersX, buttonsY).size(third, 20).build());
		addRenderableWidget(Button.builder(Component.literal("Random"), b -> randomize())
				.pos(slidersX + third + 4, buttonsY).size(third, 20).build());
		addRenderableWidget(Button.builder(Component.literal("Done"), b -> done())
				.pos(slidersX + 2 * (third + 4), buttonsY).size(SLIDER_WIDTH - 2 * (third + 4), 20).build());
		updatePreview();
	}

	private Body body() {
		return new Body(values[0], values[1], values[2], values[3], values[4], values[5]);
	}

	private void setValues(Body body) {
		values[0] = body.height();
		values[1] = body.weight();
		values[2] = body.chest();
		values[3] = body.arms();
		values[4] = body.legs();
		values[5] = body.head();
		updatePreview();
	}

	private void setAll(Body body) {
		setValues(body);
		for (Slider slider : sliders) {
			slider.refresh();
		}
	}

	private void randomize() {
		RandomSource random = RandomSource.create();
		// Average of two rolls, so most random bodies are closer to normal than to the extremes.
		float[] rolled = new float[PARTS.length];
		for (int i = 0; i < rolled.length; i++) {
			rolled[i] = (random.nextFloat() + random.nextFloat()) - 1;
		}
		setAll(new Body(rolled[0], rolled[1], rolled[2], rolled[3], rolled[4], rolled[5]));
	}

	private static List<Look.Option> lookOptions(int index) {
		return switch (index) {
			case 0 -> Look.HAIR;
			case 1 -> Look.HAIR_COLORS;
			case 2 -> Look.SCARS;
			default -> Look.OUTFITS;
		};
	}

	private String lookLabel(int index) {
		List<Look.Option> options = lookOptions(index);
		return LOOK_NAMES[index] + ": " + options.get(Math.floorMod(look[index], options.size())).name();
	}

	private Look lookValue() {
		return new Look(look[0], look[1], look[2], look[3]).clamped();
	}

	private void updatePreview() {
		BodyClient.preview = body();
		BodyClient.previewLook = lookValue();
	}

	private void done() {
		ClientPlayNetworking.send(new BodyFeature.Choose(body().clamped()));
		ClientPlayNetworking.send(new BodyFeature.ChooseLook(lookValue()));
		onClose();
	}

	@Override
	public void removed() {
		// Stop drawing the preview; from now on your player is drawn with the body the server saved.
		BodyClient.preview = null;
		BodyClient.previewLook = null;
		super.removed();
	}

	@Override
	public boolean shouldCloseOnEsc() {
		return !firstTime;
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);

		graphics.centeredText(font, "Shape your body", width / 2, 8, 0xFFFFD75E);
		graphics.centeredText(font, firstTime
				? "Only height changes your size. Type /body to change this later."
				: "Only height changes your size. The rest is just looks.", width / 2, 20, 0xFFAAAAAA);
		graphics.text(font, "Looks (click to change)", looksX, top - 11, 0xFFFFD75E);

		// Your player, turning to follow the mouse, drawn with the slider values.
		int previewTop = top - 4;
		int previewBottom = top + PARTS.length * ROW + 26;
		graphics.fill(previewLeft, previewTop, previewRight, previewBottom, 0xA0000000);
		if (minecraft.player != null) {
			InventoryScreen.extractEntityInInventoryFollowsMouse(graphics, previewLeft, previewTop, previewRight, previewBottom,
					(previewBottom - previewTop) / 3, 0.0625f, mouseX, mouseY, minecraft.player);
		}
	}

	/** A slider for one body part. The bar goes from 0 to 1; the body value goes from -1 to 1. */
	private class Slider extends AbstractSliderButton {
		private final int index;

		Slider(int index, int x, int y) {
			super(x, y, SLIDER_WIDTH, 20, Component.empty(), (values[index] + 1) / 2);
			this.index = index;
			updateMessage();
		}

		void refresh() {
			value = (values[index] + 1) / 2;
			updateMessage();
		}

		@Override
		protected void updateMessage() {
			Part part = PARTS[index];
			float v = values[index];
			String word;
			if (Math.abs(v) < 0.1f) {
				word = part.mid();
			} else {
				word = (Math.abs(v) < 0.6f ? "A bit " + (v < 0 ? part.low() : part.high()).toLowerCase()
						: (v < 0 ? part.low() : part.high()));
			}
			if (index == 0) {
				// Height also shows the actual size, since it changes your hitbox.
				word += " (" + Math.round((1 + v * Body.MAX_HEIGHT_CHANGE) * 100) + "%)";
			}
			setMessage(Component.literal(part.name() + ": " + word));
		}

		@Override
		protected void applyValue() {
			// Snap to the middle when close, so "Average" is easy to hit.
			float v = (float) (value * 2 - 1);
			values[index] = Math.abs(v) < 0.04f ? 0 : Mth.clamp(v, -1, 1);
			updatePreview();
		}
	}
}
