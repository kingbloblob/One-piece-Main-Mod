package com.onepiecemod.hideout.client;

import java.util.List;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.hideout.HideoutLevels;
import com.onepiecemod.hideout.HideoutPayloads;

/**
 * The hideout screen, opened by right-clicking the Hideout Flag: the level and what the next one needs on the
 * left; the crew living here, defences and the Navy on the right; the last daily haul at the bottom.
 */
public class HideoutScreen extends Screen {
	private static final int PANEL_W = 360;
	private static final int PANEL_H = 232;
	private static final int GOLD = 0xFFFFD75E;

	private HideoutPayloads.Sync data;
	private int left, top, panelW;

	public HideoutScreen(HideoutPayloads.Sync data) {
		super(Component.literal("Hideout"));
		this.data = data;
	}

	public void refresh(HideoutPayloads.Sync data) {
		this.data = data;
	}

	@Override
	protected void init() {
		panelW = Math.min(PANEL_W, width - 16);
		left = (width - panelW) / 2;
		top = Math.max(4, (height - PANEL_H) / 2);
		int y = top + PANEL_H - 24;
		int w = (panelW - 24) / 3;
		clearWidgets();
		addRenderableWidget(Button.builder(Component.literal("Open stash"), b -> send("stash"))
				.pos(left + 6, y).size(w, 18).build());
		addRenderableWidget(Button.builder(Component.literal("Move crew in"), b -> send("station"))
				.pos(left + 12 + w, y).size(w, 18).build());
		addRenderableWidget(Button.builder(Component.literal("Close"), b -> onClose())
				.pos(left + 18 + 2 * w, y).size(w, 18).build());
	}

	private void send(String action) {
		ClientPlayNetworking.send(new HideoutPayloads.Action(data.pos(), action));
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		graphics.fill(left, top, left + panelW, top + PANEL_H, 0xE0141018);
		graphics.fill(left, top, left + panelW, top + 2, GOLD);
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);

		int level = Math.max(0, Math.min(HideoutLevels.MAX, data.level()));
		graphics.text(font, data.crewName() + " Hideout", left + 8, top + 8, GOLD, true);
		String levelText = "Level " + level + ": " + HideoutLevels.NAMES[level];
		graphics.text(font, levelText, left + panelW - 8 - font.width(levelText), top + 8, 0xFFFFFFFF, false);
		// Five stars for the five levels.
		for (int i = 0; i < HideoutLevels.MAX; i++) {
			int x = left + panelW - 8 - (HideoutLevels.MAX - i) * 9;
			graphics.fill(x, top + 19, x + 7, top + 22, i < level ? GOLD : 0xFF404040);
		}

		int half = (panelW - 24) / 2;
		int lx = left + 8;
		int rx = left + 16 + half;
		int y = top + 28;
		y = wrap(graphics, data.perk(), lx, y, half, 0xFFCCCCCC);
		y += 4;
		if (level >= HideoutLevels.MAX) {
			y = wrap(graphics, "Your hideout is a full Pirate Fortress.", lx, y, half, GOLD);
		} else {
			y = wrap(graphics, "Next: " + HideoutLevels.NAMES[level + 1], lx, y, half, 0xFFFFFFFF);
			for (String need : data.needs()) {
				boolean done = need.startsWith("1");
				y = wrap(graphics, (done ? "✔ " : "✘ ") + need.substring(1), lx + 4, y, half - 4, done ? 0xFF7CFC7C : 0xFFFF9A6A);
			}
		}

		int ry = top + 28;
		ry = wrap(graphics, "Living here (" + data.crew().size() + ")", rx, ry, half, 0xFFFFFFFF);
		if (data.crew().isEmpty()) {
			ry = wrap(graphics, "Nobody yet. Set crewmates to Work inside the claim, or press Move crew in.", rx + 4, ry, half - 4, 0xFF8A8A8A);
		}
		for (String line : data.crew()) {
			ry = wrap(graphics, line, rx + 4, ry, half - 4, 0xFFAADDFF);
		}
		ry += 4;
		for (String line : data.stats()) {
			ry = wrap(graphics, line, rx, ry, half, line.contains("ATTACK") ? 0xFFFF5050 : 0xFFCCCCCC);
		}

		// The last report along the bottom.
		int by = Math.max(y, ry) + 6;
		List<String> report = data.report();
		int bottom = top + PANEL_H - 28;
		if (!report.isEmpty() && by < bottom) {
			graphics.fill(left + 6, by - 3, left + panelW - 6, by - 2, 0xFF404040);
			for (String line : report) {
				if (by >= bottom) {
					break;
				}
				by = wrap(graphics, line, lx, by, panelW - 16, 0xFFBBBBBB);
			}
		}
	}

	private int wrap(GuiGraphicsExtractor graphics, String text, int x, int y, int w, int color) {
		for (FormattedCharSequence line : font.split(Component.literal(text), w)) {
			graphics.text(font, line, x, y, color, false);
			y += font.lineHeight + 1;
		}
		return y;
	}
}
