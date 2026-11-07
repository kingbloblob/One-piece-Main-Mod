package com.onepiecemod.tutorial.client;

import java.util.ArrayList;
import java.util.List;

import com.mojang.blaze3d.platform.InputConstants;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;

import com.onepiecemod.tutorial.TutorialFeature;
import com.onepiecemod.tutorial.TutorialStep;
import com.onepiecemod.tutorial.TutorialTips;

/**
 * The Voyage Log: a book with every First Voyage step and every tip the player has seen, to read again later.
 * Left page: the steps by part (done, current, still ahead); click one to read its hint.
 * Right page: the chosen step, or the Tips tab with each tip seen so far.
 * Opened from the book button in the inventory or by clicking the guide panel (TutorialOverlay).
 */
public class TutorialBookScreen extends Screen {
	private static final int COVER = 0xFF5C3A1E, PAPER = 0xFFF3E6C4, PAPER_EDGE = 0xFFD9C7A0;
	private static final int TEXT = 0xFF2E2216, FAINT = 0xFF7A6850, LINK = 0xFF1F4FA0, DONE = 0xFF2E7D32, NOW = 0xFFB0600A, PART = 0xFF20707A;
	private static final int ROW = 11;

	private final Screen parent;
	private int bookX, bookY, bookW, bookH, pageW, leftX, rightX, pageTop, pageBottom;
	/** The step shown on the right page, or -1 for the Tips tab. */
	private int selected;
	private int leftScroll, rightScroll;

	public TutorialBookScreen(Screen parent) {
		super(Component.literal("Voyage Log"));
		this.parent = parent;
		TutorialFeature.Sync data = TutorialClient.data();
		selected = data == null ? 0 : Math.min(data.step(), TutorialStep.COUNT - 1);
	}

	@Override
	protected void init() {
		bookW = Math.min(420, width - 40);
		bookH = Math.min(240, height - 20);
		bookX = (width - bookW) / 2;
		bookY = (height - bookH) / 2;
		pageW = bookW / 2 - 24;
		leftX = bookX + 12;
		rightX = bookX + bookW / 2 + 12;
		pageTop = bookY + 10;
		pageBottom = bookY + bookH - 10;
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	@Override
	public void onClose() {
		minecraft.gui.setScreen(parent);
	}

	private TutorialFeature.Sync data() {
		return TutorialClient.data();
	}

	private int done() {
		TutorialFeature.Sync data = data();
		return data == null ? 0 : data.step();
	}

	private List<TutorialTips> tips() {
		List<TutorialTips> tips = new ArrayList<>();
		TutorialFeature.Sync data = data();
		if (data != null) {
			for (String id : data.tips()) {
				TutorialTips tip = TutorialTips.byId(id);
				if (tip != null) {
					tips.add(tip);
				}
			}
		}
		return tips;
	}

	// ---- Drawing ----

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		graphics.fill(bookX - 4, bookY - 4, bookX + bookW + 4, bookY + bookH + 4, COVER);
		graphics.fill(bookX, bookY, bookX + bookW, bookY + bookH, PAPER);
		graphics.fill(bookX + bookW / 2 - 1, bookY, bookX + bookW / 2 + 1, bookY + bookH, PAPER_EDGE);
		drawSteps(graphics, mouseX, mouseY);
		drawRight(graphics, mouseX, mouseY);
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
	}

	/** One line on the left page: a part heading or a step. */
	private record Line(TutorialStep.Part part, TutorialStep step) {}

	private List<Line> lines() {
		List<Line> lines = new ArrayList<>();
		TutorialStep.Part part = null;
		for (TutorialStep step : TutorialStep.values()) {
			if (step.part != part) {
				part = step.part;
				lines.add(new Line(part, null));
			}
			lines.add(new Line(null, step));
		}
		return lines;
	}

	private int stepsTop() {
		return pageTop + 24;
	}

	private int visibleRows() {
		return (pageBottom - stepsTop()) / ROW;
	}

	private void drawSteps(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
		int done = done();
		graphics.text(font, "⚓ Voyage Log", leftX, pageTop, TEXT, false);
		String count = Math.min(done, TutorialStep.COUNT) + "/" + TutorialStep.COUNT;
		graphics.text(font, count, leftX + pageW - font.width(count), pageTop, done >= TutorialStep.COUNT ? DONE : FAINT, false);
		// Progress bar under the title.
		graphics.fill(leftX, pageTop + 12, leftX + pageW, pageTop + 15, PAPER_EDGE);
		graphics.fill(leftX, pageTop + 12, leftX + pageW * Math.min(done, TutorialStep.COUNT) / TutorialStep.COUNT, pageTop + 15, DONE);

		List<Line> lines = lines();
		int rows = visibleRows();
		leftScroll = Math.max(0, Math.min(leftScroll, lines.size() - rows));
		int y = stepsTop();
		for (int i = leftScroll; i < lines.size() && i < leftScroll + rows; i++) {
			Line line = lines.get(i);
			if (line.part != null) {
				graphics.text(font, "Part " + (line.part.ordinal() + 1) + ": " + line.part.title, leftX, y + 1, PART, false);
			} else {
				int index = line.step.ordinal();
				boolean over = over(mouseX, mouseY, leftX, y, pageW, ROW);
				String mark = index < done ? "✔ " : index == done ? "➜ " : "• ";
				int color = over ? LINK : index < done ? DONE : index == done ? NOW : FAINT;
				if (index == selected) {
					graphics.fill(leftX - 2, y - 1, leftX + pageW + 2, y + ROW - 1, 0x30A07840);
				}
				graphics.text(font, mark + shorten(line.step.title, pageW - 14), leftX + 6, y + 1, color, false);
			}
			y += ROW;
		}
		if (lines.size() > rows) {
			graphics.text(font, leftScroll > 0 ? "▲" : " ", leftX + pageW - 6, stepsTop() - 10, FAINT, false);
			graphics.text(font, leftScroll + rows < lines.size() ? "▼" : " ", leftX + pageW - 6, pageBottom - 4, FAINT, false);
		}
	}

	private void drawRight(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
		// Two tabs at the top of the right page: the chosen step and Tips.
		List<TutorialTips> tips = tips();
		String stepLabel = "Step";
		String tipsLabel = "Tips (" + tips.size() + ")";
		int tipsX = rightX + font.width(stepLabel) + 12;
		graphics.text(font, stepLabel, rightX, pageTop, selected >= 0 ? TEXT : over(mouseX, mouseY, rightX, pageTop - 2, font.width(stepLabel), 12) ? LINK : FAINT, false);
		graphics.text(font, tipsLabel, tipsX, pageTop, selected < 0 ? TEXT : over(mouseX, mouseY, tipsX, pageTop - 2, font.width(tipsLabel), 12) ? LINK : FAINT, false);
		int underX = selected >= 0 ? rightX : tipsX;
		int underW = font.width(selected >= 0 ? stepLabel : tipsLabel);
		graphics.fill(underX, pageTop + 10, underX + underW, pageTop + 11, TEXT);

		List<Text> body = new ArrayList<>();
		if (selected >= 0) {
			TutorialStep step = TutorialStep.at(selected);
			int done = done();
			body.add(new Text(Component.literal("Part " + (step.part.ordinal() + 1) + ": " + step.part.title), PART));
			body.add(new Text(Component.literal(step.title).withStyle(style -> style.withBold(true)), TEXT));
			String status = selected < done ? "✔ Done" : selected == done ? "➜ Your current step" : "Still ahead";
			TutorialFeature.Sync data = data();
			if (selected == done && data != null && !data.progress().isEmpty()) {
				status += " (" + data.progress() + ")";
			}
			body.add(new Text(Component.literal(status), selected < done ? DONE : selected == done ? NOW : FAINT));
			body.add(null);
			body.add(new Text(Component.literal(step.hintText(TutorialClient::keyName)), TEXT));
			body.add(null);
			body.add(new Text(Component.literal("/tutorial skip skips your current step. /tutorial off hides the guide."), FAINT));
		} else if (tips.isEmpty()) {
			body.add(new Text(Component.literal("No tips yet. The first time you find a Devil Fruit, awaken Haki, learn a fighting style or take a ship's helm, a tip shows in chat and is kept here."), FAINT));
		} else {
			for (TutorialTips tip : tips) {
				body.add(new Text(Component.literal(tip.title).withStyle(style -> style.withBold(true)), PART));
				body.add(new Text(Component.literal(TutorialStep.keysText(tip.text, TutorialClient::keyName)), TEXT));
				body.add(null);
			}
		}

		List<FormattedCharSequence> wrapped = new ArrayList<>();
		List<Integer> colors = new ArrayList<>();
		for (Text text : body) {
			if (text == null) {
				wrapped.add(null);
				colors.add(0);
				continue;
			}
			for (FormattedCharSequence line : font.split(text.text, pageW)) {
				wrapped.add(line);
				colors.add(text.color);
			}
		}
		int top = pageTop + 18;
		int rows = (pageBottom - top) / 10;
		rightScroll = Math.max(0, Math.min(rightScroll, wrapped.size() - rows));
		int y = top;
		for (int i = rightScroll; i < wrapped.size() && i < rightScroll + rows; i++) {
			if (wrapped.get(i) != null) {
				graphics.text(font, wrapped.get(i), rightX, y, colors.get(i), false);
			}
			y += 10;
		}
		if (wrapped.size() > rows) {
			graphics.text(font, rightScroll > 0 ? "▲" : " ", rightX + pageW - 6, pageTop, FAINT, false);
			graphics.text(font, rightScroll + rows < wrapped.size() ? "▼" : " ", rightX + pageW - 6, pageBottom - 4, FAINT, false);
		}
	}

	private record Text(Component text, int color) {}

	private String shorten(String text, int maxWidth) {
		if (font.width(text) <= maxWidth) {
			return text;
		}
		while (!text.isEmpty() && font.width(text + "...") > maxWidth) {
			text = text.substring(0, text.length() - 1);
		}
		return text + "...";
	}

	private static boolean over(double mouseX, double mouseY, int x, int y, int w, int h) {
		return mouseX >= x && mouseX < x + w && mouseY >= y && mouseY < y + h;
	}

	// ---- Mouse ----

	@Override
	public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
		if (event.button() != InputConstants.MOUSE_BUTTON_LEFT) {
			return super.mouseClicked(event, doubleClick);
		}
		double mx = event.x(), my = event.y();
		// Tabs.
		String stepLabel = "Step";
		String tipsLabel = "Tips (" + tips().size() + ")";
		int tipsX = rightX + font.width(stepLabel) + 12;
		if (over(mx, my, rightX, pageTop - 2, font.width(stepLabel), 12) && selected < 0) {
			selected = Math.min(done(), TutorialStep.COUNT - 1);
			rightScroll = 0;
			return true;
		}
		if (over(mx, my, tipsX, pageTop - 2, font.width(tipsLabel), 12)) {
			selected = -1;
			rightScroll = 0;
			return true;
		}
		// Steps on the left page.
		if (mx >= leftX && mx < leftX + pageW && my >= stepsTop() && my < stepsTop() + visibleRows() * ROW) {
			int index = leftScroll + (int) ((my - stepsTop()) / ROW);
			List<Line> lines = lines();
			if (index < lines.size() && lines.get(index).step != null) {
				selected = lines.get(index).step.ordinal();
				rightScroll = 0;
				return true;
			}
		}
		return super.mouseClicked(event, doubleClick);
	}

	@Override
	public boolean mouseScrolled(double mouseX, double mouseY, double scrollX, double scrollY) {
		int step = scrollY > 0 ? -1 : scrollY < 0 ? 1 : 0;
		if (mouseX < bookX + bookW / 2) {
			leftScroll += step;
		} else {
			rightScroll += step;
		}
		return true;
	}
}
