package com.onepiecemod.guide.client;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.item.ItemStack;

import com.onepiecemod.guide.GuideData;

/**
 * The Pirate's Handbook screen. Chapters are listed on the left (scroll the list with the mouse wheel);
 * the right side shows the chosen chapter one page at a time. The text comes from onepiece/guide.json.
 */
public class GuideScreen extends Screen {
	private static final int LIST_WIDTH = 118;
	private static final int ROW = 16;
	private static final int GAP = 10;
	private static final int MAX_PANEL_WIDTH = 260;
	private static final int TOP = 30;

	private static final int TEXT = 0xFFE0E0E0;
	private static final int GREY = 0xFFAAAAAA;
	private static final int TIP = 0xFF7FE0FF;

	/** Remembered while the game runs, so the book opens where you left off. */
	private static int lastChapter = 0;
	private static int lastPage = 0;

	/** One line of text on a page, already wrapped to fit. */
	private record Line(FormattedCharSequence text, int color, int indent, int spaceBefore) {}

	private final List<GuideData.Chapter> chapters = GuideData.chapters();
	private final List<List<Line>> pages = new ArrayList<>();
	private int chapter, page, listScroll;
	private Button previous, next;

	// Where things are on screen. Worked out in init(), because it depends on the window size.
	private int listX, panelX, panelWidth, bottom, visibleRows;

	public GuideScreen() {
		super(Component.literal("Pirate's Handbook"));
		chapter = Math.min(lastChapter, Math.max(0, chapters.size() - 1));
		page = lastPage;
	}

	@Override
	protected void init() {
		panelWidth = Math.min(MAX_PANEL_WIDTH, width - LIST_WIDTH - GAP - 16);
		listX = Math.max(8, (width - LIST_WIDTH - GAP - panelWidth) / 2);
		panelX = listX + LIST_WIDTH + GAP;
		bottom = height - 30;
		visibleRows = Math.max(1, (bottom - TOP) / ROW);
		// Keep the open chapter's button in view.
		listScroll = Math.max(0, Math.min(chapter - visibleRows / 2, chapters.size() - visibleRows));

		layoutPages();
		page = Math.max(0, Math.min(page, pages.size() - 1));
		layoutButtons();
	}

	/** (Re)creates the chapter buttons for the part of the list that's scrolled into view, plus the page arrows. */
	private void layoutButtons() {
		clearWidgets();
		for (int row = 0; row < visibleRows && listScroll + row < chapters.size(); row++) {
			int index = listScroll + row;
			Button button = Button.builder(Component.literal(chapters.get(index).title), b -> openChapter(index))
					.pos(listX, TOP + row * ROW).size(LIST_WIDTH, ROW - 2).build();
			// The open chapter's button is greyed out, to show it is the one selected.
			button.active = index != chapter;
			addRenderableWidget(button);
		}
		previous = addRenderableWidget(Button.builder(Component.literal("<"), b -> turn(-1))
				.pos(panelX, height - 26).size(20, 20).build());
		next = addRenderableWidget(Button.builder(Component.literal(">"), b -> turn(1))
				.pos(panelX + panelWidth - 20, height - 26).size(20, 20).build());
		addRenderableWidget(Button.builder(Component.literal("Close"), b -> onClose())
				.pos(panelX + panelWidth / 2 - 30, height - 26).size(60, 20).build());
		previous.active = page > 0;
		next.active = page < pages.size() - 1;
	}

	private void openChapter(int index) {
		chapter = index;
		page = 0;
		layoutPages();
		layoutButtons();
	}

	private void turn(int by) {
		page = Math.max(0, Math.min(page + by, pages.size() - 1));
		previous.active = page > 0;
		next.active = page < pages.size() - 1;
	}

	/** Wraps the chapter's text to the panel width and cuts it into pages. */
	private void layoutPages() {
		pages.clear();
		List<Line> lines = new ArrayList<>();
		if (!chapters.isEmpty()) {
			GuideData.Chapter current = chapters.get(chapter);
			int space = 0;
			for (String raw : current.text) {
				if (raw.isBlank()) {
					space = 5;
					continue;
				}
				String text = raw;
				int color = TEXT;
				String prefix = "";
				int before = space;
				if (raw.startsWith("# ")) {
					text = raw.substring(2);
					color = current.colorArgb();
					before = lines.isEmpty() ? 0 : Math.max(space, 4);
				} else if (raw.startsWith("- ")) {
					text = raw.substring(2);
					prefix = "• ";
				} else if (raw.startsWith("> ")) {
					text = raw.substring(2);
					color = TIP;
					prefix = "Tip: ";
				}
				space = 0;
				int indent = font.width(prefix);
				boolean first = true;
				for (FormattedCharSequence wrapped : font.split(Component.literal(text), panelWidth - indent)) {
					if (first) {
						lines.add(new Line(prefix.isEmpty() ? wrapped
								: FormattedCharSequence.composite(Component.literal(prefix).getVisualOrderText(), wrapped), color, 0, before));
					} else {
						lines.add(new Line(wrapped, color, indent, 0));
					}
					first = false;
				}
			}
		}

		// Fill pages from the top of the panel (below the title) to the bottom.
		int pageHeight = bottom - (TOP + 22) - 4;
		List<Line> current = new ArrayList<>();
		int used = 0;
		for (int i = 0; i < lines.size(); i++) {
			Line line = lines.get(i);
			int h = (current.isEmpty() ? 0 : line.spaceBefore) + font.lineHeight + 1;
			boolean isHeading = line.spaceBefore > 0 && line.color != TEXT && line.color != TIP;
			// Don't leave a heading alone at the bottom of a page.
			int need = isHeading && i + 1 < lines.size() ? h + font.lineHeight + 1 : h;
			if (!current.isEmpty() && used + need > pageHeight) {
				pages.add(current);
				current = new ArrayList<>();
				used = 0;
				h = font.lineHeight + 1;
			}
			current.add(line);
			used += h;
		}
		pages.add(current);
	}

	@Override
	public boolean mouseScrolled(double mouseX, double mouseY, double scrollX, double scrollY) {
		if (mouseX < panelX - GAP / 2) {
			int max = Math.max(0, chapters.size() - visibleRows);
			int scrolled = Math.max(0, Math.min(max, listScroll - (int) Math.signum(scrollY)));
			if (scrolled != listScroll) {
				listScroll = scrolled;
				layoutButtons();
			}
		} else if (scrollY != 0) {
			turn(scrollY > 0 ? -1 : 1);
		}
		return true;
	}

	@Override
	public void onClose() {
		lastChapter = chapter;
		lastPage = page;
		super.onClose();
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);

		graphics.centeredText(font, "Pirate's Handbook", width / 2, 8, 0xFFFFD75E);
		if (chapters.size() > visibleRows) {
			graphics.centeredText(font, "scroll for more", listX + LIST_WIDTH / 2, bottom + 4, GREY);
		}
		if (chapters.isEmpty()) {
			graphics.text(font, "The pages are blank... (guide.json is missing)", panelX, TOP, GREY);
			return;
		}

		GuideData.Chapter current = chapters.get(chapter);
		int color = current.colorArgb();
		// Dark box behind the page, with a coloured strip on top.
		graphics.fill(panelX - 6, TOP - 4, panelX + panelWidth + 6, bottom, 0xC0101018);
		graphics.fill(panelX - 6, TOP - 4, panelX + panelWidth + 6, TOP - 2, color);

		graphics.fakeItem(icon(current), panelX, TOP + 1);
		graphics.text(font, current.title, panelX + 20, TOP + 5, color, true);
		graphics.fill(panelX, TOP + 19, panelX + panelWidth, TOP + 20, 0x60FFFFFF);

		int y = TOP + 24;
		boolean first = true;
		for (Line line : pages.get(page)) {
			if (!first) {
				y += line.spaceBefore;
			}
			graphics.text(font, line.text, panelX + line.indent, y, line.color, false);
			y += font.lineHeight + 1;
			first = false;
		}

		String pageText = (page + 1) + " / " + pages.size();
		graphics.text(font, pageText, panelX + panelWidth - font.width(pageText), TOP + 5, GREY, false);
	}

	private static ItemStack icon(GuideData.Chapter chapter) {
		Identifier id = Identifier.tryParse(chapter.icon);
		return id == null ? ItemStack.EMPTY : new ItemStack(BuiltInRegistries.ITEM.getValue(id));
	}
}
