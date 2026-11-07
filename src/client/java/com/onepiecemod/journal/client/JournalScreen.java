package com.onepiecemod.journal.client;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.item.ItemStack;

import com.onepiecemod.recipeview.client.RecipeCards;
import com.onepiecemod.recipeview.client.ViewRecipe;

/**
 * The Crafter's Journal: a book with bookmark tabs down both sides (Crafting, Devil Fruits, Creatures, Bosses...).
 *
 * - A tab's left page explains the topic; its right page lists the entries, with a search box on top.
 * - An entry's left page describes it; its right page shows how to get it (recipes, drops, trades)
 *   and what it's used in. Click any item in a recipe to jump to that item's page; right-click for its uses.
 * - Esc (or "< Back") goes back a page. The mouse wheel turns pages and scrolls lists.
 */
public class JournalScreen extends Screen {
	private static final int ROW = 18, TAB = 22;
	private static final int COVER = 0xFF5C3A1E, PAPER = 0xFFF3E6C4, PAPER_EDGE = 0xFFD9C7A0;
	private static final int TEXT = 0xFF2E2216, FAINT = 0xFF7A6850, LINK = 0xFF1F4FA0, TIP = 0xFF20707A;

	/** Where the journal was left, so it opens there again. */
	private static int lastTab = 0;
	private static JournalData.Entry lastEntry;
	private static boolean lastUses;

	private final JournalData data = JournalData.get();
	private final Deque<State> history = new ArrayDeque<>();

	private int tab;
	private JournalData.Entry entry;
	private boolean uses;
	private int textPage, cardPage, listScroll;
	private String search = "";
	/** A real text box: in 26.3 the game only sends typed letters to proper text widgets. */
	private EditBox searchBox;

	private ItemStack hovered = ItemStack.EMPTY;
	private JournalData.Entry hoveredEntry;

	// Layout, worked out in init().
	private int bookX, bookY, bookW, bookH, pageW, leftX, rightX, pageTop, pageBottom, tabsPerSide;

	private record State(int tab, JournalData.Entry entry, boolean uses) {}

	/** One wrapped line of text on a page. */
	private record Line(FormattedCharSequence text, int color, int indent, int spaceBefore) {}

	public JournalScreen() {
		super(Component.literal("Crafter's Journal"));
		tab = Math.min(lastTab, Math.max(0, data.tabs.size() - 1));
		entry = lastEntry;
		uses = lastUses;
	}

	@Override
	protected void init() {
		bookW = Math.min(420, width - 60);
		bookH = Math.min(240, height - 20);
		bookX = (width - bookW) / 2;
		bookY = (height - bookH) / 2;
		pageW = bookW / 2 - 22;
		leftX = bookX + 12;
		rightX = bookX + bookW / 2 + 10;
		pageTop = bookY + 10;
		pageBottom = bookY + bookH - 20;
		tabsPerSide = Math.max(1, (bookH - 8) / TAB);

		searchBox = new EditBox(font, rightX + 3, pageTop + 3, pageW - 6, 9, Component.literal("Search"));
		searchBox.setBordered(false);
		searchBox.setTextColor(TEXT);
		searchBox.setMaxLength(40);
		searchBox.setHint(Component.literal("Search the whole journal..."));
		searchBox.setValue(search);
		searchBox.setResponder(text -> {
			search = text;
			listScroll = 0;
		});
		addRenderableWidget(searchBox);
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	@Override
	public void onClose() {
		lastTab = tab;
		lastEntry = entry;
		lastUses = uses;
		super.onClose();
	}

	// ---- Moving around ----

	private void openTab(int index) {
		if (index == tab && entry == null) {
			return;
		}
		history.push(new State(tab, entry, uses));
		tab = index;
		entry = null;
		textPage = 0;
		listScroll = 0;
	}

	private void openEntry(JournalData.Entry target, boolean showUses) {
		if (target == null) {
			return;
		}
		history.push(new State(tab, entry, uses));
		JournalData.Tab owner = data.tabOf(target);
		if (owner != null && !currentTab().entries.contains(target)) {
			tab = data.tabs.indexOf(owner);
		}
		entry = target;
		uses = showUses && !target.usedIn().isEmpty();
		textPage = 0;
		cardPage = 0;
	}

	private boolean back() {
		if (history.isEmpty()) {
			if (entry != null) {
				entry = null;
				textPage = 0;
				return true;
			}
			return false;
		}
		State state = history.pop();
		tab = state.tab;
		entry = state.entry;
		uses = state.uses;
		textPage = 0;
		cardPage = 0;
		return true;
	}

	private JournalData.Tab currentTab() {
		return data.tabs.get(tab);
	}

	private List<JournalData.Entry> listed() {
		return search.isBlank() ? currentTab().entries : data.search(search);
	}

	private List<ViewRecipe> cards() {
		return entry == null ? List.of() : uses ? entry.usedIn() : entry.howToGet();
	}

	// ---- Drawing ----

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		hovered = ItemStack.EMPTY;
		hoveredEntry = null;
		RecipeCards.hovered = ItemStack.EMPTY;
		if (data.tabs.isEmpty()) {
			graphics.centeredText(font, "The journal is blank (journal.json is missing).", width / 2, height / 2, 0xFFFFFFFF);
			return;
		}

		drawTabs(graphics, mouseX, mouseY);
		// Cover, pages and spine.
		graphics.fill(bookX - 4, bookY - 4, bookX + bookW + 4, bookY + bookH + 4, COVER);
		graphics.fill(bookX, bookY, bookX + bookW, bookY + bookH, PAPER);
		graphics.fill(bookX + bookW / 2 - 1, bookY, bookX + bookW / 2 + 1, bookY + bookH, PAPER_EDGE);

		if (entry == null) {
			drawTabIntro(graphics, mouseX, mouseY);
			drawEntryList(graphics, mouseX, mouseY);
		} else {
			drawEntryText(graphics, mouseX, mouseY);
			drawCards(graphics, mouseX, mouseY);
		}

		if (!RecipeCards.hovered.isEmpty()) {
			hovered = RecipeCards.hovered;
		}
		if (!hovered.isEmpty()) {
			graphics.setTooltipForNextFrame(font, hovered, mouseX, mouseY);
		}
		// The search box (a widget) is drawn last, on top of the page.
		searchBox.visible = entry == null;
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
	}

	private void drawTabs(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
		for (int i = 0; i < data.tabs.size(); i++) {
			JournalData.Tab t = data.tabs.get(i);
			int[] box = tabBox(i);
			boolean selected = i == tab;
			boolean over = inside(mouseX, mouseY, box);
			int color = selected ? t.colorArgb() : over ? lighten(t.colorArgb()) : darken(t.colorArgb());
			graphics.fill(box[0], box[1], box[0] + box[2], box[1] + box[3], 0xFF3A2410);
			graphics.fill(box[0] + 1, box[1] + 1, box[0] + box[2] - 1, box[1] + box[3] - 1, color);
			graphics.fakeItem(t.iconStack, box[0] + (box[2] - 16) / 2, box[1] + 2);
			if (over) {
				graphics.setTooltipForNextFrame(font, Component.literal(t.title), mouseX, mouseY);
			}
		}
	}

	/** x, y, width, height of a bookmark tab. The first half sit on the left of the book, the rest on the right. */
	private int[] tabBox(int index) {
		boolean left = index < tabsPerSide;
		int row = left ? index : index - tabsPerSide;
		int y = bookY + 4 + row * TAB;
		return left ? new int[] {bookX - 26, y, 24, TAB - 2} : new int[] {bookX + bookW + 2, y, 24, TAB - 2};
	}

	private void drawTabIntro(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
		JournalData.Tab t = currentTab();
		graphics.fakeItem(t.iconStack, leftX, pageTop);
		graphics.text(font, RecipeCards.shorten(font, t.title, pageW - 20), leftX + 20, pageTop + 4, darken(t.colorArgb()), false);
		graphics.fill(leftX, pageTop + 18, leftX + pageW, pageTop + 19, PAPER_EDGE);
		List<List<Line>> pages = paginate(t.lines, darken(t.colorArgb()), pageTop + 22);
		textPage = Math.max(0, Math.min(textPage, pages.size() - 1));
		drawLines(graphics, pages.get(textPage), pageTop + 22);
		drawPager(graphics, leftX, textPage, pages.size(), mouseX, mouseY);
	}

	private void drawEntryList(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
		// Search box.
		int boxY = pageTop;
		graphics.fill(rightX, boxY, rightX + pageW, boxY + 13, searchBox.isFocused() ? 0xFF3A2410 : PAPER_EDGE);
		graphics.fill(rightX + 1, boxY + 1, rightX + pageW - 1, boxY + 12, 0xFFFFF8E8);

		List<JournalData.Entry> list = listed();
		int top = pageTop + 17;
		int rows = Math.max(1, (pageBottom - top) / ROW);
		listScroll = Math.max(0, Math.min(listScroll, Math.max(0, list.size() - rows)));
		if (list.isEmpty()) {
			graphics.text(font, search.isBlank() ? "Nothing here yet." : "Nothing found.", rightX + 2, top + 4, FAINT, false);
		}
		for (int row = 0; row < rows && listScroll + row < list.size(); row++) {
			JournalData.Entry e = list.get(listScroll + row);
			int y = top + row * ROW;
			boolean over = mouseX >= rightX && mouseX < rightX + pageW && mouseY >= y && mouseY < y + ROW;
			if (over) {
				graphics.fill(rightX, y, rightX + pageW, y + ROW, 0x30000000);
				hoveredEntry = e;
			}
			graphics.fakeItem(e.icon, rightX + 1, y + 1);
			graphics.text(font, RecipeCards.shorten(font, e.title, pageW - 22), rightX + 20, y + 5, over ? LINK : TEXT, false);
		}
		if (list.size() > rows) {
			String count = (listScroll + 1) + "-" + Math.min(list.size(), listScroll + rows) + " of " + list.size() + " (scroll)";
			graphics.text(font, count, rightX + pageW - font.width(count), pageBottom + 5, FAINT, false);
		}
	}

	private void drawEntryText(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
		JournalData.Tab t = currentTab();
		boolean overBack = mouseX >= leftX && mouseX < leftX + 40 && mouseY >= pageTop && mouseY < pageTop + 10;
		graphics.text(font, "< Back", leftX, pageTop, overBack ? LINK : FAINT, false);
		graphics.text(font, RecipeCards.shorten(font, t.title, pageW - 50), leftX + pageW - Math.min(pageW - 50, font.width(t.title)), pageTop, FAINT, false);

		int y = pageTop + 13;
		graphics.fakeItem(entry.icon, leftX, y);
		List<FormattedCharSequence> title = font.split(Component.literal(entry.title), pageW - 22);
		for (int i = 0; i < title.size() && i < 2; i++) {
			graphics.text(font, title.get(i), leftX + 20, y + (title.size() == 1 ? 4 : i * 9), darken(t.colorArgb()), false);
		}
		if (mouseX >= leftX && mouseX < leftX + 16 && mouseY >= y && mouseY < y + 16 && !entry.item.isEmpty()) {
			hovered = entry.item;
		}
		y += 20;
		graphics.fill(leftX, y - 2, leftX + pageW, y - 1, PAPER_EDGE);
		List<String> lines = entry.lines.isEmpty() ? List.of("No notes about this one yet.") : entry.lines;
		List<List<Line>> pages = paginate(lines, darken(t.colorArgb()), y + 2);
		textPage = Math.max(0, Math.min(textPage, pages.size() - 1));
		drawLines(graphics, pages.get(textPage), y + 2);
		drawPager(graphics, leftX, textPage, pages.size(), mouseX, mouseY);
	}

	private void drawCards(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
		// The two lists: "How to get" (or "Drops"...) and "Used in".
		List<ViewRecipe> get = entry.howToGet();
		List<ViewRecipe> use = entry.usedIn();
		String first = entry.cardsTitle + " (" + get.size() + ")";
		graphics.text(font, first, rightX, pageTop, !uses ? TEXT : overFirstLabel(mouseX, mouseY) ? LINK : FAINT, false);
		if (!uses) {
			graphics.fill(rightX, pageTop + 9, rightX + font.width(first), pageTop + 10, TEXT);
		}
		if (!use.isEmpty()) {
			String second = "Used in (" + use.size() + ")";
			int x = rightX + pageW - font.width(second);
			graphics.text(font, second, x, pageTop, uses ? TEXT : overSecondLabel(mouseX, mouseY) ? LINK : FAINT, false);
			if (uses) {
				graphics.fill(x, pageTop + 9, x + font.width(second), pageTop + 10, TEXT);
			}
		}

		List<ViewRecipe> cards = cards();
		int top = pageTop + 14;
		int perPage = Math.max(1, (pageBottom - top) / RecipeCards.HEIGHT);
		int pages = Math.max(1, (cards.size() + perPage - 1) / perPage);
		cardPage = Math.max(0, Math.min(cardPage, pages - 1));
		if (cards.isEmpty()) {
			List<FormattedCharSequence> text = font.split(Component.literal(emptyText()), pageW);
			for (int i = 0; i < text.size(); i++) {
				graphics.text(font, text.get(i), rightX, top + 4 + i * 10, FAINT, false);
			}
		}
		for (int i = 0; i < perPage; i++) {
			int index = cardPage * perPage + i;
			if (index >= cards.size()) {
				break;
			}
			RecipeCards.draw(graphics, font, cards.get(index), rightX, top + i * RecipeCards.HEIGHT, pageW, mouseX, mouseY);
		}
		drawPager(graphics, rightX, cardPage, pages, mouseX, mouseY);
	}

	private String emptyText() {
		if (uses) {
			return "Nothing uses this.";
		}
		if (entry.item.isEmpty()) {
			return entry.cardsTitle.equals("Loot") ? "Open its chest to see what's inside!" : "Nothing listed.";
		}
		String id = net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(entry.item.getItem()).getPath();
		if (id.startsWith("wanted_poster_")) {
			return "Nobody hands out this poster in Survival: this character isn't a boss. Creative menu only.";
		}
		return "This can't be crafted. Look for it in the world: in chests, from creatures and bosses, or at traders.";
	}

	private boolean overFirstLabel(double mx, double my) {
		return my >= pageTop && my < pageTop + 10 && mx >= rightX && mx < rightX + pageW / 2;
	}

	private boolean overSecondLabel(double mx, double my) {
		return my >= pageTop && my < pageTop + 10 && mx >= rightX + pageW / 2 && mx < rightX + pageW;
	}

	/** "< 2 / 5 >" at the bottom of a page. */
	private void drawPager(GuiGraphicsExtractor graphics, int x, int page, int pages, int mouseX, int mouseY) {
		if (pages <= 1) {
			return;
		}
		int y = pageBottom + 5;
		graphics.text(font, "<", x, y, page > 0 ? (overPrev(x, mouseX, mouseY) ? LINK : TEXT) : PAPER_EDGE, false);
		String text = (page + 1) + " / " + pages;
		graphics.text(font, text, x + (pageW - font.width(text)) / 2, y, FAINT, false);
		graphics.text(font, ">", x + pageW - 6, y, page < pages - 1 ? (overNext(x, mouseX, mouseY) ? LINK : TEXT) : PAPER_EDGE, false);
	}

	private boolean overPrev(int x, double mx, double my) {
		return my >= pageBottom + 2 && my < pageBottom + 16 && mx >= x - 3 && mx < x + 12;
	}

	private boolean overNext(int x, double mx, double my) {
		return my >= pageBottom + 2 && my < pageBottom + 16 && mx >= x + pageW - 12 && mx < x + pageW + 3;
	}

	private void drawLines(GuiGraphicsExtractor graphics, List<Line> lines, int y) {
		boolean first = true;
		for (Line line : lines) {
			if (!first) {
				y += line.spaceBefore;
			}
			graphics.text(font, line.text, leftX + line.indent, y, line.color, false);
			y += font.lineHeight + 1;
			first = false;
		}
	}

	/** Wraps text lines ("# " heading, "- " bullet, "> " tip) to the page width and cuts them into pages. */
	private List<List<Line>> paginate(List<String> raw, int headingColor, int top) {
		List<Line> lines = new ArrayList<>();
		int space = 0;
		for (String text : raw) {
			if (text.isBlank()) {
				space = 5;
				continue;
			}
			int color = TEXT;
			String prefix = "";
			int before = space;
			if (text.startsWith("# ")) {
				text = text.substring(2);
				color = headingColor;
				before = lines.isEmpty() ? 0 : Math.max(space, 4);
			} else if (text.startsWith("- ")) {
				text = text.substring(2);
				prefix = "• ";
			} else if (text.startsWith("> ")) {
				text = text.substring(2);
				color = TIP;
				prefix = "Tip: ";
			}
			space = 0;
			int indent = font.width(prefix);
			boolean firstLine = true;
			for (FormattedCharSequence wrapped : font.split(Component.literal(text), pageW - indent)) {
				if (firstLine) {
					lines.add(new Line(prefix.isEmpty() ? wrapped
							: FormattedCharSequence.composite(Component.literal(prefix).getVisualOrderText(), wrapped), color, 0, before));
				} else {
					lines.add(new Line(wrapped, color, indent, 0));
				}
				firstLine = false;
			}
		}
		int pageHeight = pageBottom - top;
		List<List<Line>> pages = new ArrayList<>();
		List<Line> current = new ArrayList<>();
		int used = 0;
		for (int i = 0; i < lines.size(); i++) {
			Line line = lines.get(i);
			int h = (current.isEmpty() ? 0 : line.spaceBefore) + font.lineHeight + 1;
			boolean heading = line.color == headingColor && line.color != TEXT;
			int need = heading && i + 1 < lines.size() ? h + font.lineHeight + 1 : h;
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
		return pages;
	}

	private static int darken(int argb) {
		int r = (argb >> 16 & 0xFF) * 55 / 100, g = (argb >> 8 & 0xFF) * 55 / 100, b = (argb & 0xFF) * 55 / 100;
		return 0xFF000000 | r << 16 | g << 8 | b;
	}

	private static int lighten(int argb) {
		int r = (argb >> 16 & 0xFF) * 80 / 100, g = (argb >> 8 & 0xFF) * 80 / 100, b = (argb & 0xFF) * 80 / 100;
		return 0xFF000000 | r << 16 | g << 8 | b;
	}

	private static boolean inside(double x, double y, int[] box) {
		return x >= box[0] && x < box[0] + box[2] && y >= box[1] && y < box[1] + box[3];
	}

	// ---- Mouse and keys ----

	@Override
	public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
		double mx = event.x(), my = event.y();
		for (int i = 0; i < data.tabs.size(); i++) {
			if (inside(mx, my, tabBox(i))) {
				openTab(i);
				return true;
			}
		}
		if (entry == null) {
			boolean onSearch = mx >= rightX && mx < rightX + pageW && my >= pageTop && my < pageTop + 13;
			if (onSearch) {
				if (event.button() == 1) {
					searchBox.setValue(""); // Right-click clears the search, like in creative.
				}
				setFocused(searchBox);
				searchBox.setFocused(true);
				return super.mouseClicked(event, doubleClick) || true;
			}
			setFocused(null);
			searchBox.setFocused(false);
			if (hoveredEntry != null) {
				openEntry(hoveredEntry, false);
				return true;
			}
			if (overPrev(leftX, mx, my)) {
				textPage--;
				return true;
			}
			if (overNext(leftX, mx, my)) {
				textPage++;
				return true;
			}
		} else {
			if (mx >= leftX && mx < leftX + 40 && my >= pageTop && my < pageTop + 10) {
				back();
				return true;
			}
			if (overFirstLabel(mx, my) && uses) {
				uses = false;
				cardPage = 0;
				return true;
			}
			if (overSecondLabel(mx, my) && !uses && !entry.usedIn().isEmpty()) {
				uses = true;
				cardPage = 0;
				return true;
			}
			if (overPrev(leftX, mx, my)) {
				textPage--;
				return true;
			}
			if (overNext(leftX, mx, my)) {
				textPage++;
				return true;
			}
			if (overPrev(rightX, mx, my)) {
				cardPage--;
				return true;
			}
			if (overNext(rightX, mx, my)) {
				cardPage++;
				return true;
			}
			if (!hovered.isEmpty() && (event.button() == 0 || event.button() == 1)) {
				JournalData.Entry target = data.entryFor(hovered);
				if (target == entry) {
					uses = event.button() == 1 && !entry.usedIn().isEmpty();
					cardPage = 0;
				} else {
					openEntry(target, event.button() == 1);
				}
				return true;
			}
		}
		return super.mouseClicked(event, doubleClick);
	}

	@Override
	public boolean mouseScrolled(double mouseX, double mouseY, double scrollX, double scrollY) {
		if (scrollY == 0) {
			return true;
		}
		int step = scrollY > 0 ? -1 : 1;
		boolean right = mouseX >= bookX + bookW / 2;
		if (entry == null) {
			if (right) {
				listScroll = Math.max(0, listScroll + step * 3);
			} else {
				textPage = Math.max(0, textPage + step);
			}
		} else if (right) {
			cardPage = Math.max(0, cardPage + step);
		} else {
			textPage = Math.max(0, textPage + step);
		}
		return true;
	}

	@Override
	public boolean keyPressed(KeyEvent event) {
		if (searchBox.isFocused()) {
			if (event.isEscape() || event.isConfirmation()) {
				setFocused(null);
				searchBox.setFocused(false);
				return true;
			}
			searchBox.keyPressed(event);
			return true; // Typing letters must never close or change the book.
		}
		if (event.isEscape() && back()) {
			return true;
		}
		return super.keyPressed(event);
	}
}
