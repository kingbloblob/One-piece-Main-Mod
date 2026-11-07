package com.onepiecemod.race.client;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.body.client.BodyEditorScreen;
import com.onepiecemod.race.Race;
import com.onepiecemod.race.RacePayloads;

/**
 * The "Choose your race" screen that shows the first time you join.
 * Races are listed on the left; the right side shows the chosen race's perks and drawbacks.
 * You can't close it with Escape, because every pirate needs a race.
 */
public class RacePickerScreen extends Screen {
	private static final int LIST_WIDTH = 110;
	private static final int GAP = 12;
	private static final int MAX_PANEL_WIDTH = 230;

	private Race selected = Race.HUMAN;
	private final List<Button> raceButtons = new ArrayList<>();
	private Button confirm;

	// Where things are on screen. Worked out in init(), because it depends on the window size.
	private int listX, panelX, panelWidth, top;

	public RacePickerScreen() {
		super(Component.literal("Choose your race"));
	}

	@Override
	protected void init() {
		panelWidth = Math.min(MAX_PANEL_WIDTH, width - LIST_WIDTH - GAP - 16);
		listX = Math.max(8, (width - LIST_WIDTH - GAP - panelWidth) / 2);
		panelX = listX + LIST_WIDTH + GAP;
		top = 36;

		Race[] races = Race.values();
		// Squeeze the buttons together on small windows so all races fit.
		int step = Math.max(13, Math.min(20, (height - top - 10) / races.length));

		clearWidgets();
		raceButtons.clear();
		for (int i = 0; i < races.length; i++) {
			Race race = races[i];
			Button button = Button.builder(Component.literal(race.displayName), b -> select(race))
					.pos(listX, top + i * step).size(LIST_WIDTH, step - 2).build();
			raceButtons.add(addRenderableWidget(button));
		}
		confirm = addRenderableWidget(Button.builder(Component.empty(), b -> choose())
				.pos(panelX, height - 28).size(panelWidth, 20).build());
		select(selected);
	}

	private void select(Race race) {
		selected = race;
		Race[] races = Race.values();
		for (int i = 0; i < raceButtons.size(); i++) {
			// The picked race's button is greyed out, to show it is the one selected.
			raceButtons.get(i).active = races[i] != race;
		}
		confirm.setMessage(Component.literal("Become " + race.withArticle()));
	}

	private void choose() {
		ClientPlayNetworking.send(new RacePayloads.Choose(selected.id));
		// Next step: shape your body (height, weight, and so on).
		minecraft.gui.setScreen(new BodyEditorScreen(true));
	}

	@Override
	public boolean shouldCloseOnEsc() {
		return false;
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);

		graphics.centeredText(font, "Choose your race", width / 2, 8, 0xFFFFD75E);
		graphics.centeredText(font, "Every race has perks and drawbacks. You only pick once!", width / 2, 20, 0xFFAAAAAA);

		// Dark box behind the details.
		int bottom = height - 34;
		graphics.fill(panelX - 4, top - 4, panelX + panelWidth + 4, bottom, 0xA0000000);
		graphics.fill(panelX - 4, top - 4, panelX + panelWidth + 4, top - 2, 0xFF000000 | selected.color);

		int y = top + 2;
		graphics.text(font, selected.displayName, panelX, y, 0xFF000000 | selected.color, true);
		y += font.lineHeight + 4;
		y = wrapped(graphics, selected.description, y, 0xFFCCCCCC);
		y += 6;

		graphics.text(font, "Perks", panelX, y, 0xFF55FF55, true);
		y += font.lineHeight + 2;
		for (String perk : selected.perks) {
			y = wrapped(graphics, "+ " + perk, y, 0xFFB5FFB5);
		}
		y += 6;

		graphics.text(font, "Drawbacks", panelX, y, 0xFFFF5555, true);
		y += font.lineHeight + 2;
		for (String drawback : selected.drawbacks) {
			y = wrapped(graphics, "- " + drawback, y, 0xFFFFB5B5);
		}
	}

	/** Draws text that wraps onto more lines if it is wider than the panel. Returns the y below it. */
	private int wrapped(GuiGraphicsExtractor graphics, String text, int y, int color) {
		for (FormattedCharSequence line : font.split(Component.literal(text), panelWidth)) {
			graphics.text(font, line, panelX, y, color, false);
			y += font.lineHeight + 1;
		}
		return y;
	}
}
