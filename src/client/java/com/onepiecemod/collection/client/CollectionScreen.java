package com.onepiecemod.collection.client;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import com.onepiecemod.collection.CollectionData;
import com.onepiecemod.collection.CollectionPayloads;
import com.onepiecemod.cuisine.Fish;

/**
 * The Collector's Log screen. Tabs along the top (Fish, Food, Ships, Swords, Islands).
 * The first four are a grid of squares like the Devil Fruit Encyclopedia: what you haven't found shows a "?".
 * Islands is a list grouped by sea, with each island's goals on the right.
 */
public class CollectionScreen extends Screen {
	private static final int CELL = 20;
	private static final int COLUMNS = 7;
	private static final int GRID_WIDTH = COLUMNS * CELL;
	private static final int GAP = 12;
	private static final int MAX_PANEL_WIDTH = 230;
	private static final int ROW = 11;
	private static final int WHITE = 0xFFFFFFFF, GREY = 0xFFA0A0A0, DARK = 0xFF606060, GOLD = 0xFFFFD75E, GREEN = 0xFF7CFC7C,
			AQUA = 0xFF6FE3FF, PURPLE = 0xFFD58CFF;

	/** One square of a grid tab. */
	private record Entry(String id, ItemStack icon, String name, String hint, boolean found, String extra) {
	}

	/** One line of the islands list: a sea heading or an island. */
	private record Line(CollectionData.Region region, CollectionData.Island island) {
	}

	private final Map<String, List<String>> lists;
	private final Map<String, Integer> counters;
	private final Set<String> goals;

	private String tab = CollectionData.FISH;
	private List<Entry> entries = List.of();
	private List<Line> lines = List.of();
	private int selected = 0;
	private int page = 0;

	private int gridX, gridY, rows, panelX, panelWidth, top, listWidth;
	private Button prev, next;

	public CollectionScreen(CollectionPayloads.Open data) {
		super(Component.literal("Collector's Log"));
		this.lists = data.lists();
		this.counters = data.counters();
		this.goals = new HashSet<>(list("goals"));
	}

	private List<String> list(String key) {
		return lists.getOrDefault(key, List.of());
	}

	@Override
	protected void init() {
		boolean islands = tab.equals(CollectionData.ISLANDS);
		listWidth = islands ? 180 : GRID_WIDTH;
		panelWidth = Math.min(MAX_PANEL_WIDTH, width - listWidth - GAP - 16);
		gridX = Math.max(8, (width - listWidth - GAP - panelWidth) / 2);
		panelX = gridX + listWidth + GAP;
		top = 30;
		gridY = top + 24;
		int area = height - gridY - 34;
		rows = Math.max(2, islands ? area / ROW : area / CELL);

		clearWidgets();
		int tabWidth = Math.min(84, (width - 16) / CollectionData.TABS.size());
		int tabsX = (width - tabWidth * CollectionData.TABS.size()) / 2;
		for (int i = 0; i < CollectionData.TABS.size(); i++) {
			String id = CollectionData.TABS.get(i);
			Button button = Button.builder(Component.literal(tabLabel(id)), b -> setTab(id))
					.pos(tabsX + i * tabWidth, top).size(tabWidth - 2, 18).build();
			button.active = !tab.equals(id);
			addRenderableWidget(button);
		}
		prev = addRenderableWidget(Button.builder(Component.literal("<"), b -> turn(-1))
				.pos(gridX, gridY + listHeight() + 4).size(20, 18).build());
		next = addRenderableWidget(Button.builder(Component.literal(">"), b -> turn(1))
				.pos(gridX + listWidth - 20, gridY + listHeight() + 4).size(20, 18).build());
		build();
		turn(0);
	}

	private int listHeight() {
		return tab.equals(CollectionData.ISLANDS) ? rows * ROW : rows * CELL;
	}

	private void setTab(String id) {
		tab = id;
		page = 0;
		selected = 0;
		init();
	}

	private String tabLabel(String id) {
		int have = switch (id) {
			case CollectionData.ISLANDS -> list(CollectionData.ISLANDS).size();
			default -> list(id).size();
		};
		String name = switch (id) {
			case CollectionData.FISH -> "Fish";
			case CollectionData.FOOD -> "Food";
			case CollectionData.SHIPS -> "Ships";
			case CollectionData.SWORDS -> "Swords";
			default -> "Islands";
		};
		return name + " " + have + "/" + CollectionData.size(id);
	}

	/** Fills entries (grid tabs) or lines (islands) for the current tab. */
	private void build() {
		List<Entry> list = new ArrayList<>();
		switch (tab) {
			case CollectionData.FISH -> {
				Set<String> caught = new HashSet<>(list(CollectionData.FISH));
				for (Fish fish : Fish.values()) {
					Item item = com.onepiecemod.cuisine.CuisineItems.fish(fish);
					list.add(new Entry(fish.id, new ItemStack(item), fish.title, "Bites in " + fish.habitat() + ".",
							caught.contains(fish.id), ""));
				}
			}
			case CollectionData.FOOD -> {
				Set<String> tasted = new HashSet<>(list(CollectionData.FOOD));
				for (Item item : CollectionData.foods()) {
					String id = BuiltInRegistries.ITEM.getKey(item).toString();
					ItemStack stack = new ItemStack(item);
					list.add(new Entry(id, stack, stack.getHoverName().getString(),
							"Not tasted yet. The Crafter's Journal shows how to cook or find it.", tasted.contains(id), ""));
				}
			}
			case CollectionData.SHIPS -> {
				Set<String> spotted = new HashSet<>(list(CollectionData.SHIPS));
				Set<String> sailed = new HashSet<>(list("sailed"));
				for (CollectionData.Ship ship : CollectionData.ships()) {
					String extra = (ship.crew.isBlank() ? "" : "Crew: " + ship.crew + "\n") + "Length: " + ship.length + " blocks\n"
							+ (sailed.contains(ship.id) ? "You've been aboard her." : "You haven't been aboard yet.");
					list.add(new Entry(ship.id, new ItemStack(CollectionData.item(ship.icon)), ship.name, ship.hint,
							spotted.contains(ship.id), extra));
				}
			}
			case CollectionData.SWORDS -> {
				Set<String> held = new HashSet<>(list(CollectionData.SWORDS));
				for (CollectionData.Sword sword : CollectionData.swords()) {
					ItemStack stack = new ItemStack(CollectionData.item(sword.item));
					list.add(new Entry(sword.item, stack, stack.getHoverName().getString(), sword.hint, held.contains(sword.item), ""));
				}
			}
			default -> {
				List<Line> islandLines = new ArrayList<>();
				for (CollectionData.Region region : CollectionData.regions()) {
					islandLines.add(new Line(region, null));
					for (CollectionData.Island island : CollectionData.islands()) {
						if (island.region.equals(region.id)) {
							islandLines.add(new Line(region, island));
						}
					}
				}
				lines = islandLines;
				if (selected == 0 && lines.size() > 1) {
					selected = 1;
				}
			}
		}
		entries = list;
	}

	private int perPage() {
		return tab.equals(CollectionData.ISLANDS) ? rows : rows * COLUMNS;
	}

	private int size() {
		return tab.equals(CollectionData.ISLANDS) ? lines.size() : entries.size();
	}

	private int pages() {
		return Math.max(1, (size() + perPage() - 1) / perPage());
	}

	private void turn(int by) {
		page = Math.max(0, Math.min(pages() - 1, page + by));
		prev.active = page > 0;
		next.active = page < pages() - 1;
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
		graphics.centeredText(font, "Collector's Log", width / 2, 6, GOLD);
		graphics.centeredText(font, "Fill every page for Berries and treasure", width / 2, 17, GREY);

		graphics.fill(gridX - 2, gridY - 2, gridX + listWidth + 2, gridY + listHeight() + 2, 0xA0000000);
		if (tab.equals(CollectionData.ISLANDS)) {
			drawIslandList(graphics, mouseX, mouseY);
		} else {
			drawGrid(graphics, mouseX, mouseY);
		}
		graphics.centeredText(font, "Page " + (page + 1) + "/" + pages(), gridX + listWidth / 2, gridY + listHeight() + 9, GREY);

		int bottom = height - 10;
		graphics.fill(panelX - 4, top + 20, panelX + panelWidth + 4, bottom, 0xA0000000);
		if (tab.equals(CollectionData.ISLANDS)) {
			drawIslandPage(graphics);
		} else {
			drawEntryPage(graphics);
		}
	}

	private void drawGrid(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
		int start = page * perPage();
		for (int i = 0; i < perPage() && start + i < entries.size(); i++) {
			Entry entry = entries.get(start + i);
			int x = gridX + (i % COLUMNS) * CELL, y = gridY + (i / COLUMNS) * CELL;
			boolean hover = mouseX >= x && mouseX < x + CELL && mouseY >= y && mouseY < y + CELL;
			if (start + i == selected) {
				graphics.fill(x, y, x + CELL, y + CELL, 0x80FFFFFF);
			} else if (hover) {
				graphics.fill(x, y, x + CELL, y + CELL, 0x40FFFFFF);
			}
			if (entry.found()) {
				graphics.fakeItem(entry.icon(), x + 2, y + 2);
			} else {
				graphics.centeredText(font, "?", x + CELL / 2, y + 6, DARK);
			}
		}
	}

	private void drawEntryPage(GuiGraphicsExtractor graphics) {
		if (selected >= entries.size()) {
			return;
		}
		Entry entry = entries.get(selected);
		int y = top + 26;
		int have = (int) entries.stream().filter(Entry::found).count();
		y = wrapped(graphics, have + " of " + entries.size() + " collected", y, GREY);
		y = drawMilestones(graphics, y + 2, have);
		y += 6;
		if (!entry.found()) {
			graphics.text(font, tab.equals(CollectionData.FOOD) || tab.equals(CollectionData.SHIPS) ? entry.name() : "???",
					panelX, y, GREY, true);
			y += font.lineHeight + 6;
			wrapped(graphics, entry.hint(), y, PURPLE);
			return;
		}
		graphics.fakeItem(entry.icon(), panelX, y - 2);
		graphics.text(font, entry.name(), panelX + 20, y + 2, GOLD, true);
		y += 20;
		if (!entry.extra().isEmpty()) {
			for (String line : entry.extra().split("\n")) {
				y = wrapped(graphics, line, y, AQUA);
			}
			y += 4;
		}
		if (!tab.equals(CollectionData.FISH) && !tab.equals(CollectionData.FOOD)) {
			y = wrapped(graphics, entry.hint(), y, GREY);
			y += 4;
		}
		List<Component> tooltip = Screen.getTooltipFromItem(minecraft, entry.icon());
		for (int i = 1; i < tooltip.size() && y < height - 20; i++) {
			y = wrapped(graphics, tooltip.get(i), y);
		}
	}

	/** The tab's reward ladder, one line per milestone: "✔ 5 found: 300 Berries". */
	private int drawMilestones(GuiGraphicsExtractor graphics, int y, int have) {
		CollectionData.Tab data = CollectionData.tab(tab);
		Set<String> claimed = new HashSet<>(list("claimed"));
		for (Map.Entry<String, Integer> milestone : data.milestones.entrySet()) {
			int need = CollectionData.threshold(tab, milestone.getKey());
			boolean done = claimed.contains(tab + ":" + milestone.getKey()) || have >= need;
			StringBuilder text = new StringBuilder((done ? "✔ " : "• ") + need + " found: " + milestone.getValue() + " Berries");
			if (need >= CollectionData.size(tab)) {
				for (String spec : data.items) {
					ItemStack stack = CollectionData.stack(spec);
					if (!stack.isEmpty()) {
						text.append(", ").append(stack.getCount()).append(" ").append(stack.getHoverName().getString());
					}
				}
				if (data.xp > 0) {
					text.append(", ").append(data.xp).append(" Pirate XP");
				}
			}
			y = wrapped(graphics, text.toString(), y, done ? GREEN : 0xFFB0D8B0);
		}
		return y;
	}

	private void drawIslandList(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
		Set<String> done = new HashSet<>(list(CollectionData.ISLANDS));
		Set<String> visited = new HashSet<>(list("visited"));
		int start = page * perPage();
		for (int i = 0; i < perPage() && start + i < lines.size(); i++) {
			Line line = lines.get(start + i);
			int y = gridY + i * ROW;
			if (line.island() == null) {
				int total = 0, finished = 0;
				for (CollectionData.Island island : CollectionData.islands()) {
					if (island.region.equals(line.region().id)) {
						total++;
						finished += done.contains(island.id) ? 1 : 0;
					}
				}
				String title = font.plainSubstrByWidth(line.region().title, listWidth - 40);
				graphics.text(font, title, gridX + 1, y + 1, GOLD, false);
				String count = finished + "/" + total;
				graphics.text(font, count, gridX + listWidth - font.width(count) - 1, y + 1, finished == total ? GREEN : GREY, false);
				continue;
			}
			boolean hover = mouseX >= gridX && mouseX < gridX + listWidth && mouseY >= y && mouseY < y + ROW;
			if (start + i == selected) {
				graphics.fill(gridX, y, gridX + listWidth, y + ROW, 0x80FFFFFF);
			} else if (hover) {
				graphics.fill(gridX, y, gridX + listWidth, y + ROW, 0x40FFFFFF);
			}
			CollectionData.Island island = line.island();
			boolean seen = visited.contains(island.id);
			String mark = done.contains(island.id) ? "✔ " : "  ";
			String name = seen ? island.name : "???";
			name = font.plainSubstrByWidth(mark + name, listWidth - 34);
			graphics.text(font, name, gridX + 6, y + 1, done.contains(island.id) ? GREEN : seen ? WHITE : DARK, false);
			String count = goalsDone(island) + "/" + island.goals.size();
			graphics.text(font, count, gridX + listWidth - font.width(count) - 1, y + 1, GREY, false);
		}
	}

	private int goalsDone(CollectionData.Island island) {
		int n = 0;
		for (int i = 0; i < island.goals.size(); i++) {
			n += goals.contains(island.id + ":" + i) ? 1 : 0;
		}
		return n;
	}

	private void drawIslandPage(GuiGraphicsExtractor graphics) {
		int y = top + 26;
		int done = list(CollectionData.ISLANDS).size();
		y = wrapped(graphics, done + " of " + CollectionData.islands().size() + " islands complete", y, GREY);
		y = drawMilestones(graphics, y + 2, done);
		y += 6;
		if (selected >= lines.size()) {
			return;
		}
		Line line = lines.get(selected);
		if (line.island() == null) {
			graphics.text(font, line.region().title, panelX, y, GOLD, true);
			y += font.lineHeight + 4;
			y = wrapped(graphics, "Finish every island of this sea for:", y, GREY);
			wrapped(graphics, rewardText(line.region().reward), y, GREEN);
			return;
		}
		CollectionData.Island island = line.island();
		boolean seen = list("visited").contains(island.id);
		boolean finished = list(CollectionData.ISLANDS).contains(island.id);
		graphics.fakeItem(new ItemStack(finished ? Items.FILLED_MAP : Items.MAP), panelX, y - 2);
		graphics.text(font, seen ? island.name : "An island you haven't found", panelX + 20, y + 2, finished ? GREEN : GOLD, true);
		y += 20;
		for (CollectionData.Region region : CollectionData.regions()) {
			if (region.id.equals(island.region)) {
				y = wrapped(graphics, region.title, y, AQUA);
			}
		}
		y += 4;
		for (int i = 0; i < island.goals.size(); i++) {
			CollectionData.Goal goal = island.goals.get(i);
			boolean ok = goals.contains(island.id + ":" + i);
			String text = goal.text;
			if (goal.type.equals("explore") && !ok) {
				text += " (" + Math.min(goal.seconds, counters.getOrDefault("explore:" + island.id, 0)) + "/" + goal.seconds + " s)";
			}
			if (!seen && !goal.type.equals("visit") && !goal.type.equals("explore")) {
				text = "???";
			}
			y = wrapped(graphics, (ok ? "✔ " : "• ") + text, y, ok ? GREEN : WHITE);
		}
		y += 6;
		y = wrapped(graphics, finished ? "Complete! You got:" : "Reward:", y, GREY);
		wrapped(graphics, rewardText(island.reward), y, GOLD);
	}

	private static String rewardText(CollectionData.Reward reward) {
		StringBuilder text = new StringBuilder();
		if (reward.berries > 0) {
			text.append(reward.berries).append(" Berries");
		}
		for (String spec : reward.items) {
			ItemStack stack = CollectionData.stack(spec);
			if (!stack.isEmpty()) {
				text.append(text.isEmpty() ? "" : ", ").append(stack.getCount()).append(" ").append(stack.getHoverName().getString());
			}
		}
		if (reward.xp > 0) {
			text.append(text.isEmpty() ? "" : ", ").append(reward.xp).append(" Pirate XP");
		}
		return text.toString();
	}

	@Override
	public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
		if (super.mouseClicked(event, doubleClick)) {
			return true;
		}
		if (tab.equals(CollectionData.ISLANDS)) {
			if (event.x() >= gridX && event.x() < gridX + listWidth && event.y() >= gridY) {
				int row = (int) Math.floor((event.y() - gridY) / ROW);
				int index = page * perPage() + row;
				if (row < rows && index < lines.size()) {
					selected = index;
					return true;
				}
			}
			return false;
		}
		int column = (int) Math.floor((event.x() - gridX) / CELL);
		int row = (int) Math.floor((event.y() - gridY) / CELL);
		if (column >= 0 && column < COLUMNS && row >= 0 && row < rows) {
			int index = page * perPage() + row * COLUMNS + column;
			if (index < entries.size()) {
				selected = index;
				return true;
			}
		}
		return false;
	}

	@Override
	public boolean mouseScrolled(double mouseX, double mouseY, double scrollX, double scrollY) {
		turn(scrollY > 0 ? -1 : 1);
		return true;
	}

	private int wrapped(GuiGraphicsExtractor graphics, String text, int y, int color) {
		return wrapped(graphics, Component.literal(text), y, color);
	}

	private int wrapped(GuiGraphicsExtractor graphics, Component text, int y) {
		return wrapped(graphics, text, y, GREY);
	}

	private int wrapped(GuiGraphicsExtractor graphics, Component text, int y, int color) {
		for (FormattedCharSequence line : font.split(text, panelWidth)) {
			graphics.text(font, line, panelX, y, color, false);
			y += font.lineHeight + 1;
		}
		return y;
	}
}
