package com.onepiecemod.fruitdex.client;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.item.ItemStack;

import com.onepiecemod.character.CharacterData;
import com.onepiecemod.fruitdex.FruitLore;
import com.onepiecemod.fruitdex.FruitdexPayloads;
import com.onepiecemod.item.ModItems;
import com.onepiecemod.power.DevilFruit;
import com.onepiecemod.power.DevilFruits;
import com.onepiecemod.power.Awakening;

/**
 * The Devil Fruit Encyclopedia screen. Every fruit has a square in the grid on the left;
 * fruits you haven't found yet show a "?", and fruits you've only seen a boss use show as a dark shadow.
 * Click a square to read its page on the right. The search box finds fruits by name or user.
 */
public class FruitdexScreen extends Screen {
	private static final int CELL = 20;
	private static final int COLUMNS = 7;
	private static final int GRID_WIDTH = COLUMNS * CELL;
	private static final int GAP = 12;
	private static final int MAX_PANEL_WIDTH = 220;
	private static final int WHITE = 0xFFFFFFFF, GREY = 0xFFA0A0A0, GOLD = 0xFFFFD75E, PURPLE = 0xFFD58CFF, RED = 0xFFFF7070;

	private final Set<String> discovered;
	private final Set<String> sighted;
	/** Fruit id -> the boss who has eaten it (from characters.json), for "where to find it" hints. */
	private static Map<String, CharacterData> holders;
	private final String eaten;
	private final boolean awakened;
	private final int mastery;

	/** null = show every type. */
	private DevilFruit.Type filter = null;
	private String query = "";
	private EditBox searchBox;
	private List<DevilFruit> shown = DevilFruits.ALL;
	private DevilFruit selected;
	private int page = 0;

	// Layout, worked out in init() because it depends on the window size.
	private int gridX, gridY, rows, panelX, panelWidth, top;
	private Button prev, next;

	public FruitdexScreen(FruitdexPayloads.Open data) {
		super(Component.literal("Devil Fruit Encyclopedia"));
		this.discovered = new HashSet<>(data.discovered());
		this.sighted = new HashSet<>(data.sighted());
		this.eaten = data.eaten();
		this.awakened = data.awakened();
		this.mastery = data.mastery();
		// Open on your own fruit if you have one, otherwise on the first fruit you found.
		this.selected = DevilFruits.ALL.stream().filter(f -> f.id().equals(eaten)).findFirst()
				.orElse(DevilFruits.ALL.stream().filter(f -> discovered.contains(f.id())).findFirst().orElse(DevilFruits.ALL.get(0)));
	}

	@Override
	protected void init() {
		panelWidth = Math.min(MAX_PANEL_WIDTH, width - GRID_WIDTH - GAP - 16);
		gridX = Math.max(8, (width - GRID_WIDTH - GAP - panelWidth) / 2);
		panelX = gridX + GRID_WIDTH + GAP;
		top = 30;
		gridY = top + 46;
		rows = Math.max(2, (height - gridY - 34) / CELL);

		clearWidgets();
		searchBox = new EditBox(font, gridX, top, GRID_WIDTH, 18, Component.literal("Search"));
		searchBox.setHint(Component.literal("Search name or user"));
		searchBox.setValue(query);
		searchBox.setResponder(text -> {
			query = text.trim().toLowerCase(Locale.ROOT);
			refilter();
		});
		addRenderableWidget(searchBox);
		// Type filters above the grid.
		String[] labels = {"All", "Para", "Logia", "Zoan"};
		DevilFruit.Type[] types = {null, DevilFruit.Type.PARAMECIA, DevilFruit.Type.LOGIA, DevilFruit.Type.ZOAN};
		int buttonWidth = GRID_WIDTH / labels.length;
		for (int i = 0; i < labels.length; i++) {
			DevilFruit.Type type = types[i];
			Button button = Button.builder(Component.literal(labels[i]), b -> setFilter(type))
					.pos(gridX + i * buttonWidth, top + 22).size(buttonWidth - 2, 18).build();
			button.active = filter != type;
			addRenderableWidget(button);
		}
		prev = addRenderableWidget(Button.builder(Component.literal("<"), b -> turn(-1))
				.pos(gridX, gridY + rows * CELL + 4).size(20, 18).build());
		next = addRenderableWidget(Button.builder(Component.literal(">"), b -> turn(1))
				.pos(gridX + GRID_WIDTH - 20, gridY + rows * CELL + 4).size(20, 18).build());
		turn(0);
	}

	private void setFilter(DevilFruit.Type type) {
		filter = type;
		refilter();
		init();
	}

	private void refilter() {
		shown = DevilFruits.ALL.stream().filter(f -> filter == null || f.type() == filter).filter(this::matches).toList();
		page = 0;
		if (prev != null) {
			turn(0);
		}
	}

	/** Search only looks at fruits you know something about, so it can't spoil the rest. */
	private boolean matches(DevilFruit fruit) {
		if (query.isEmpty()) {
			return true;
		}
		if (!discovered.contains(fruit.id()) && !sighted.contains(fruit.id())) {
			return false;
		}
		FruitLore.Entry lore = FruitLore.get(fruit.id());
		return fruit.name().toLowerCase(Locale.ROOT).contains(query) || lore.english().toLowerCase(Locale.ROOT).contains(query)
				|| lore.user().toLowerCase(Locale.ROOT).contains(query);
	}

	/** The boss who has eaten this fruit, or null if it only grows wild. */
	private static CharacterData holder(DevilFruit fruit) {
		if (holders == null) {
			holders = new HashMap<>();
			try {
				for (CharacterData character : CharacterData.all().values()) {
					if (character.fruitItem != null && character.fruitItem.startsWith("onepiece:") && character.isBossRole()) {
						holders.putIfAbsent(character.fruitItem.substring("onepiece:".length()), character);
					}
				}
			} catch (RuntimeException e) {
				// No hints if the character list can't be read.
			}
		}
		return holders.get(fruit.id());
	}

	private static String tierName(int tier) {
		return switch (tier) {
			case 1 -> "an East Blue";
			case 2 -> "a Paradise";
			case 3 -> "a Grand Line";
			case 4 -> "a New World";
			default -> "a legendary";
		};
	}

	private int perPage() {
		return rows * COLUMNS;
	}

	private int pages() {
		return Math.max(1, (shown.size() + perPage() - 1) / perPage());
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

		graphics.centeredText(font, "Devil Fruit Encyclopedia", width / 2, 6, GOLD);
		String progress = discovered.size() + " of " + DevilFruits.ALL.size() + " fruits found";
		if (!sighted.isEmpty()) {
			progress += ", " + sighted.size() + " more sighted";
		}
		graphics.centeredText(font, progress, width / 2, 17, GREY);

		// The grid of fruits.
		graphics.fill(gridX - 2, gridY - 2, gridX + GRID_WIDTH + 2, gridY + rows * CELL + 2, 0xA0000000);
		if (shown.isEmpty()) {
			graphics.centeredText(font, "No fruits match", gridX + GRID_WIDTH / 2, gridY + 10, GREY);
		}
		int start = page * perPage();
		Component tooltip = null;
		for (int i = 0; i < perPage() && start + i < shown.size(); i++) {
			DevilFruit fruit = shown.get(start + i);
			int x = gridX + (i % COLUMNS) * CELL, y = gridY + (i / COLUMNS) * CELL;
			boolean hover = mouseX >= x && mouseX < x + CELL && mouseY >= y && mouseY < y + CELL;
			if (fruit == selected) {
				graphics.fill(x, y, x + CELL, y + CELL, 0x80FFFFFF);
			} else if (hover) {
				graphics.fill(x, y, x + CELL, y + CELL, 0x40FFFFFF);
			}
			if (fruit.id().equals(eaten)) {
				graphics.fill(x, y + CELL - 2, x + CELL, y + CELL, 0xFFFFD75E); // Gold line under your own fruit.
			}
			if (discovered.contains(fruit.id())) {
				graphics.fakeItem(stack(fruit), x + 2, y + 2);
			} else if (sighted.contains(fruit.id())) {
				graphics.fakeItem(stack(fruit), x + 2, y + 2);
				graphics.fill(x + 2, y + 2, x + 18, y + 18, 0xC0101018); // Only a shadow until you have it.
			} else {
				graphics.centeredText(font, "?", x + CELL / 2, y + 6, 0xFF606060);
			}
			if (hover) {
				tooltip = Component.literal(discovered.contains(fruit.id()) ? fruit.name()
						: sighted.contains(fruit.id()) ? fruit.name() + " (sighted)" : "???");
			}
		}
		if (tooltip != null) {
			graphics.setTooltipForNextFrame(font, tooltip, mouseX, mouseY);
		}
		graphics.centeredText(font, "Page " + (page + 1) + "/" + pages(), gridX + GRID_WIDTH / 2, gridY + rows * CELL + 9, GREY);

		drawPage(graphics);
	}

	/** The right side: everything we know about the selected fruit. */
	private void drawPage(GuiGraphicsExtractor graphics) {
		int bottom = height - 10;
		graphics.fill(panelX - 4, top - 4, panelX + panelWidth + 4, bottom, 0xA0000000);
		int color = 0xFF000000 | selected.color();
		graphics.fill(panelX - 4, top - 4, panelX + panelWidth + 4, top - 2, color);

		int y = top + 2;
		String typeName = typeName(selected.type());
		CharacterData holder = holder(selected);
		if (sighted.contains(selected.id()) && !discovered.contains(selected.id())) {
			FruitLore.Entry lore = FruitLore.get(selected.id());
			graphics.text(font, selected.name(), panelX, y, color, true);
			y += font.lineHeight + 6;
			if (!lore.english().isEmpty()) {
				y = wrapped(graphics, lore.english(), y, GREY);
			}
			y = wrapped(graphics, "Type: " + typeName, y, PURPLE);
			y = wrapped(graphics, "Known user: " + lore.user(), y, GREY);
			y += 5;
			y = wrapped(graphics, "Sighted! You've seen this power in a fight, but you don't have the fruit.", y, WHITE);
			if (holder != null) {
				y += 5;
				wrapped(graphics, "Beat " + holder.name + " as a boss to take it.", y, GOLD);
			}
			return;
		}
		if (!discovered.contains(selected.id())) {
			graphics.text(font, "??? no Mi", panelX, y, GREY, true);
			y += font.lineHeight + 6;
			y = wrapped(graphics, "You haven't found this fruit yet. Its page fills in once one is in your inventory.", y, GREY);
			y += 6;
			y = wrapped(graphics, "Rumor says it is a " + typeName + " fruit.", y, PURPLE);
			y += 6;
			wrapped(graphics, holder != null
					? "They say " + tierName(holder.tier) + " fighter ate it. Beat them and it's yours. Get close to them in a fight to learn who."
					: "No one famous holds it. It could turn up anywhere: buried treasure, Sea Kings, or growing wild on a tree.", y, GOLD);
			return;
		}

		FruitLore.Entry lore = FruitLore.get(selected.id());
		graphics.fakeItem(stack(selected), panelX, y - 2);
		graphics.text(font, selected.name(), panelX + 20, y + 2, color, true);
		y += 20;
		if (!lore.english().isEmpty()) {
			y = wrapped(graphics, lore.english(), y, GREY);
		}
		y = wrapped(graphics, "Type: " + typeName, y, PURPLE);
		y = wrapped(graphics, "Known user: " + lore.user(), y, GREY);
		y += 5;
		y = wrapped(graphics, Component.translatable("fruit.onepiece." + selected.id() + ".desc").getString(), y, WHITE);
		y += 5;
		y = wrapped(graphics, "R: " + selected.primary(), y, GOLD);
		y = wrapped(graphics, "Sneak + R: " + selected.secondary(), y, GOLD);
		try {
			y = wrapped(graphics, "Awakening: " + Awakening.formName(selected), y, RED);
		} catch (RuntimeException e) {
			// Leave the line out rather than break the page.
		}
		if (holder != null) {
			y = wrapped(graphics, "Boss drop: " + holder.name, y, GREY);
		}
		if (!lore.lore().isEmpty()) {
			y += 5;
			y = wrapped(graphics, lore.lore(), y, 0xFFB8B8C8);
		}
		if (selected.id().equals(eaten)) {
			y += 5;
			y = wrapped(graphics, "This is your power.", y, GOLD);
			if (awakened) {
				wrapped(graphics, "Awakened!", y, RED);
			} else {
				y = wrapped(graphics, "Mastery: " + mastery + " / 1000", y, GREY);
				int barWidth = Math.min(panelWidth, 120);
				graphics.fill(panelX, y + 1, panelX + barWidth, y + 5, 0xFF303030);
				graphics.fill(panelX, y + 1, panelX + barWidth * Math.min(1000, mastery) / 1000, y + 5, GOLD);
			}
		}
	}

	@Override
	public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
		if (super.mouseClicked(event, doubleClick)) {
			return true;
		}
		int column = (int) Math.floor((event.x() - gridX) / CELL);
		int row = (int) Math.floor((event.y() - gridY) / CELL);
		if (column >= 0 && column < COLUMNS && row >= 0 && row < rows) {
			int index = page * perPage() + row * COLUMNS + column;
			if (index < shown.size()) {
				selected = shown.get(index);
				return true;
			}
		}
		return false;
	}

	@Override
	public boolean keyPressed(net.minecraft.client.input.KeyEvent event) {
		// Typing in the search box shouldn't close the book when a letter matches the inventory key.
		if (searchBox != null && searchBox.isFocused()) {
			if (event.isEscape() || event.isConfirmation()) {
				setFocused(null);
				searchBox.setFocused(false);
				return true;
			}
			searchBox.keyPressed(event);
			return true;
		}
		return super.keyPressed(event);
	}

	@Override
	public boolean mouseScrolled(double mouseX, double mouseY, double scrollX, double scrollY) {
		turn(scrollY > 0 ? -1 : 1);
		return true;
	}

	private static ItemStack stack(DevilFruit fruit) {
		return new ItemStack(ModItems.DEVIL_FRUITS.get(fruit.id()));
	}

	static String typeName(DevilFruit.Type type) {
		return Component.translatable("fruit_type.onepiece." + type.name().toLowerCase()).getString();
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
