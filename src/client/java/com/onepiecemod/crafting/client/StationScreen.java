package com.onepiecemod.crafting.client;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.crafting.Station;
import com.onepiecemod.crafting.StationBlock;
import com.onepiecemod.crafting.StationPayloads;
import com.onepiecemod.crafting.StationRecipe;
import com.onepiecemod.workshop.StationUpgrade;

/**
 * The screen of a crafting station. The list on the left shows everything the station can make:
 * white = ready to craft, yellow = missing ingredients, red = locked (the right side says why).
 * Ready recipes are listed first and locked ones last; type in the box to search.
 * Click a recipe to see what it needs, then press Craft (shift-click to craft as many as you can).
 *
 * The "Upgrades" button switches to the station's upgrade tree (see StationUpgrade): green = built,
 * white = ready to build, yellow = missing items, red = locked. Upgrades unlock recipes and give perks.
 */
public class StationScreen extends Screen {
	private static final int ROW = 20;
	private static final int LIST_WIDTH = 140;
	private static final int WHITE = 0xFFFFFFFF, GREY = 0xFFA0A0A0, RED = 0xFFFF5555, GREEN = 0xFF55FF55, YELLOW = 0xFFFFD75E;

	private final BlockPos pos;
	private final Station station;
	private final List<StationRecipe> allRecipes;
	/** The recipes shown in the list: search matches, sorted ready / missing items / locked. */
	private List<StationRecipe> recipes = List.of();
	/** Why each recipe is locked, by recipe id, from the server. "" means unlocked. */
	private final Map<String, String> lockReasons = new HashMap<>();

	private int selected = 0;
	private int scroll = 0;
	private String search = "";
	/** Whether Shift was held for the last mouse click (read from the click itself, which is more reliable than the key state). */
	private boolean shiftClick;
	private Button craftButton;
	private Button modeButton;
	private EditBox searchBox;

	/** The upgrade tree the server sent with the last station it opened (see CraftingClient). */
	public static StationPayloads.UpgradeState upgradeState;
	/** Whether the last station screen showed upgrades, so it stays on that page when it refreshes after building one. */
	private static BlockPos lastPos;
	private static boolean lastUpgradeMode;

	private final List<StationUpgrade> upgrades;
	private final List<String> owned = new ArrayList<>();
	private final Map<String, String> upgradeReasons = new HashMap<>();
	private boolean upgradeMode;

	// Where things are on screen. Worked out in init(), because it depends on the window size.
	private int left, top, panelWidth, panelHeight, visibleRows;

	public StationScreen(BlockPos pos, Station station, List<String> lockReasons) {
		super(Component.literal(station.title()));
		this.pos = pos;
		this.station = station;
		this.allRecipes = StationRecipe.forStation(station);
		for (int i = 0; i < allRecipes.size() && i < lockReasons.size(); i++) {
			this.lockReasons.put(allRecipes.get(i).id, lockReasons.get(i));
		}
		this.upgrades = StationUpgrade.forStation(station);
		if (upgradeState != null && upgradeState.station().equals(station.id())) {
			owned.addAll(upgradeState.owned());
			for (int i = 0; i < upgrades.size() && i < upgradeState.lockReasons().size(); i++) {
				upgradeReasons.put(upgrades.get(i).id, upgradeState.lockReasons().get(i));
			}
		}
		this.upgradeMode = pos.equals(lastPos) && lastUpgradeMode && !upgrades.isEmpty();
		lastPos = pos;
		lastUpgradeMode = upgradeMode;
	}

	private int listSize() {
		return upgradeMode ? upgrades.size() : recipes.size();
	}

	private int builtCount() {
		int built = 0;
		for (StationUpgrade upgrade : upgrades) {
			built += owned.contains(upgrade.id) ? 1 : 0;
		}
		return built;
	}

	private void setMode(boolean upgrades) {
		upgradeMode = upgrades;
		lastUpgradeMode = upgrades;
		selected = 0;
		scroll = 0;
		init();
	}

	/** Rebuilds the shown list from the search text. Done on open and when the search changes, not every
	 * frame, so the list doesn't jump around while you craft. */
	private void refreshList() {
		StationRecipe current = selected < recipes.size() ? recipes.get(selected) : null;
		String needle = search.trim().toLowerCase(Locale.ROOT);
		List<StationRecipe> shown = new ArrayList<>();
		for (StationRecipe recipe : allRecipes) {
			if (needle.isEmpty() || matchesSearch(recipe, needle)) {
				shown.add(recipe);
			}
		}
		shown.sort(Comparator.comparingInt(this::rank)); // A stable sort: the file's order within each group.
		recipes = shown;
		selected = Math.max(0, current != null ? recipes.indexOf(current) : 0);
		scroll = Math.max(0, Math.min(scroll, recipes.size() - visibleRows));
	}

	private boolean matchesSearch(StationRecipe recipe, String needle) {
		if (recipe.resultStack().getHoverName().getString().toLowerCase(Locale.ROOT).contains(needle)) {
			return true;
		}
		for (StationRecipe.Ingredient ingredient : recipe.ingredients) {
			if (ingredient.displayName().toLowerCase(Locale.ROOT).contains(needle)) {
				return true;
			}
		}
		return false;
	}

	/** 0 = ready to craft, 1 = missing ingredients, 2 = locked. */
	private int rank(StationRecipe recipe) {
		return isLocked(recipe) ? 2 : hasIngredients(recipe) ? 0 : 1;
	}

	@Override
	protected void init() {
		panelWidth = Math.min(340, width - 20);
		panelHeight = Math.min(240, height - 20);
		left = (width - panelWidth) / 2;
		top = (height - panelHeight) / 2;
		visibleRows = Math.max(1, (panelHeight - 52) / ROW);

		clearWidgets();
		searchBox = new EditBox(font, left + 6, top + 21, LIST_WIDTH, 14, Component.literal("Search"));
		searchBox.setMaxLength(40);
		searchBox.setHint(Component.literal("Search..."));
		searchBox.setValue(search);
		searchBox.setResponder(text -> {
			search = text;
			scroll = 0;
			refreshList();
		});
		addRenderableWidget(searchBox);
		searchBox.visible = !upgradeMode;
		craftButton = addRenderableWidget(Button.builder(Component.literal(upgradeMode ? "Build" : "Craft"), b -> craft())
				.pos(left + panelWidth - 90, top + panelHeight - 26).size(80, 18)
				.tooltip(Tooltip.create(Component.literal(upgradeMode ? "Build this upgrade. It uses up the items listed."
						: "Shift-click to craft as many as you can")))
				.build());
		if (!upgrades.isEmpty()) {
			modeButton = addRenderableWidget(Button.builder(
							Component.literal(upgradeMode ? "Recipes" : "Upgrades " + builtCount() + "/" + upgrades.size()), b -> setMode(!upgradeMode))
					.pos(left + panelWidth - 90, top + 4).size(84, 16)
					.tooltip(Tooltip.create(Component.literal(upgradeMode ? "Back to this station's recipes"
							: "This station's upgrade tree: new recipes and crafting perks")))
					.build());
		}
		refreshList();
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	private boolean isLocked(int index) {
		return index < recipes.size() && isLocked(recipes.get(index));
	}

	private boolean isLocked(StationRecipe recipe) {
		return !lockReasons.getOrDefault(recipe.id, "").isEmpty();
	}

	private boolean hasIngredients(StationRecipe recipe) {
		return minecraft.player != null && recipe.hasIngredients(minecraft.player);
	}

	private void craft() {
		if (upgradeMode) {
			if (selected < upgrades.size()) {
				ClientPlayNetworking.send(new StationPayloads.BuildUpgrade(pos, upgrades.get(selected).id));
			}
			return;
		}
		if (selected < recipes.size() && !isLocked(selected)) {
			ClientPlayNetworking.send(new StationPayloads.Craft(pos, recipes.get(selected).id, shiftClick || minecraft.hasShiftDown()));
		}
	}

	// ---- Drawing the screen ----

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		// (The game draws the blurred background itself before calling this.)
		// Panel and title.
		graphics.fill(left, top, left + panelWidth, top + panelHeight, 0xE0201A14);
		outline(graphics, left, top, panelWidth, panelHeight, 0xFF8B6B3E);
		graphics.text(font, station.title() + "  (Tier " + station.tier() + ")", left + 8, top + 8, YELLOW);
		if (upgradeMode) {
			extractUpgrades(graphics, mouseX, mouseY);
			super.extractRenderState(graphics, mouseX, mouseY, partialTick);
			return;
		}

		if (recipes.isEmpty()) {
			graphics.text(font, allRecipes.isEmpty() ? "This station has no recipes yet." : "Nothing matches your search.",
					left + 8, top + 42, GREY);
			craftButton.active = false;
			super.extractRenderState(graphics, mouseX, mouseY, partialTick);
			return;
		}

		// Recipe list on the left.
		int listX = left + 6, listY = top + 40;
		for (int row = 0; row < visibleRows && scroll + row < recipes.size(); row++) {
			int index = scroll + row;
			StationRecipe recipe = recipes.get(index);
			int y = listY + row * ROW;
			if (index == selected) {
				graphics.fill(listX, y, listX + LIST_WIDTH, y + ROW - 1, 0x60FFFFFF);
			} else if (mouseX >= listX && mouseX < listX + LIST_WIDTH && mouseY >= y && mouseY < y + ROW - 1) {
				graphics.fill(listX, y, listX + LIST_WIDTH, y + ROW - 1, 0x30FFFFFF);
			}
			graphics.fakeItem(recipe.resultStack(), listX + 2, y + 1);
			int colour = isLocked(index) ? RED : hasIngredients(recipe) ? WHITE : YELLOW;
			graphics.text(font, shorten(recipe.resultStack().getHoverName().getString(), LIST_WIDTH - 24), listX + 22, y + 6, colour);
		}
		if (recipes.size() > visibleRows) {
			graphics.text(font, (scroll + 1) + "-" + Math.min(recipes.size(), scroll + visibleRows) + " of " + recipes.size() + " (scroll)",
					listX, top + panelHeight - 12, GREY);
		}

		// Details of the chosen recipe on the right.
		StationRecipe recipe = recipes.get(selected);
		int x = left + LIST_WIDTH + 16, y = top + 24;
		ItemStack result = recipe.resultStack();
		graphics.fakeItem(result, x, y);
		graphics.itemDecorations(font, result, x, y);
		graphics.text(font, result.getHoverName().getString(), x + 20, y + 5, WHITE);
		y += 24;

		graphics.text(font, "Needs:", x, y, GREY);
		y += 12;
		Inventory inventory = minecraft.player.getInventory();
		for (StationRecipe.Ingredient ingredient : recipe.ingredients) {
			int have = StationRecipe.countIn(inventory, ingredient);
			graphics.fakeItem(ingredient.display(), x, y - 4);
			graphics.text(font, Math.min(have, ingredient.count) + "/" + ingredient.count + "  " + ingredient.displayName(),
					x + 20, y, have >= ingredient.count ? GREEN : RED);
			y += 18;
			if (have < ingredient.count && StationRecipe.hasKeptSafe(inventory, ingredient)) {
				// Enchanted, renamed or upgraded ones are never used up (see StationRecipe.isPlain).
				graphics.text(font, "Yours is kept safe", x + 20, y - 7, GREY);
				y += 6;
			}
		}

		if (isLocked(selected)) {
			y += 2;
			graphics.text(font, "Locked. You still need to:", x, y, RED);
			for (String reason : lockReasons.get(recipe.id).split("; ")) {
				y += 11;
				graphics.text(font, "- " + reason, x, y, RED);
			}
		}

		craftButton.active = !isLocked(selected) && hasIngredients(recipe);
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
	}

	// ---- The upgrade tree ----

	/** "" = can build, "Built" = owned, anything else = why it is locked. */
	private String upgradeReason(StationUpgrade upgrade) {
		if (owned.contains(upgrade.id)) {
			return "Built";
		}
		return upgradeReasons.getOrDefault(upgrade.id, "");
	}

	private boolean hasCost(StationUpgrade upgrade) {
		for (StationRecipe.Ingredient ingredient : upgrade.cost) {
			if (StationRecipe.countIn(minecraft.player.getInventory(), ingredient) < ingredient.count) {
				return false;
			}
		}
		return true;
	}

	private void extractUpgrades(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
		graphics.text(font, "Upgrade tree", left + 8, top + 24, GREY);
		int listX = left + 6, listY = top + 40;
		for (int row = 0; row < visibleRows && scroll + row < upgrades.size(); row++) {
			int index = scroll + row;
			StationUpgrade upgrade = upgrades.get(index);
			int y = listY + row * ROW;
			if (index == selected) {
				graphics.fill(listX, y, listX + LIST_WIDTH, y + ROW - 1, 0x60FFFFFF);
			} else if (mouseX >= listX && mouseX < listX + LIST_WIDTH && mouseY >= y && mouseY < y + ROW - 1) {
				graphics.fill(listX, y, listX + LIST_WIDTH, y + ROW - 1, 0x30FFFFFF);
			}
			int indent = Math.min(3, upgrade.depth()) * 8;
			if (indent > 0) {
				graphics.fill(listX + indent - 5, y + 9, listX + indent - 1, y + 10, GREY); // A little branch line.
			}
			graphics.fakeItem(CharacterDataIcon.of(upgrade.icon), listX + 2 + indent, y + 1);
			String reason = upgradeReason(upgrade);
			int colour = reason.equals("Built") ? GREEN : !reason.isEmpty() ? RED : hasCost(upgrade) ? WHITE : YELLOW;
			graphics.text(font, shorten(upgrade.name, LIST_WIDTH - 24 - indent), listX + 22 + indent, y + 6, colour);
		}
		if (upgrades.size() > visibleRows) {
			graphics.text(font, (scroll + 1) + "-" + Math.min(upgrades.size(), scroll + visibleRows) + " of " + upgrades.size() + " (scroll)",
					listX, top + panelHeight - 12, GREY);
		}

		StationUpgrade upgrade = upgrades.get(Math.min(selected, upgrades.size() - 1));
		String reason = upgradeReason(upgrade);
		int x = left + LIST_WIDTH + 16, y = top + 24;
		int textWidth = left + panelWidth - 8 - x;
		graphics.fakeItem(CharacterDataIcon.of(upgrade.icon), x, y);
		y = wrapped(graphics, upgrade.name, x + 20, y + (font.width(upgrade.name) > textWidth - 20 ? 0 : 5), textWidth - 20, WHITE, 2) + 6;
		y = wrapped(graphics, upgrade.description, x, y, textWidth, GREY, 3) + 3;
		for (StationUpgrade.Perk perk : upgrade.perks) {
			y = wrapped(graphics, "+ " + perk.describe(), x, y, textWidth, 0xFF7FDBFF, 2);
		}
		List<String> unlocks = new ArrayList<>();
		for (StationRecipe recipe : allRecipes) {
			if (recipe.requires != null && upgrade.id.equals(recipe.requires.upgrade)) {
				unlocks.add(recipe.resultStack().getHoverName().getString());
			}
		}
		if (!unlocks.isEmpty()) {
			y = wrapped(graphics, "Unlocks: " + String.join(", ", unlocks), x, y, textWidth, 0xFF7FDBFF, 3);
		}
		y += 4;

		if (reason.equals("Built")) {
			graphics.text(font, "Built. Its perks work every time you craft here.", x, y, GREEN);
			craftButton.active = false;
			return;
		}
		Inventory inventory = minecraft.player.getInventory();
		for (StationRecipe.Ingredient ingredient : upgrade.cost) {
			int have = StationRecipe.countIn(inventory, ingredient);
			graphics.fakeItem(ingredient.display(), x, y - 4);
			graphics.text(font, shorten(Math.min(have, ingredient.count) + "/" + ingredient.count + "  " + ingredient.displayName(), textWidth - 20),
					x + 20, y, have >= ingredient.count ? GREEN : RED);
			y += 16;
		}
		if (!reason.isEmpty()) {
			// Keep clear of the Build button: the lines next to it are narrower.
			int bottom = top + panelHeight - 30;
			for (String part : reason.split("; ")) {
				y = wrapped(graphics, "- " + part, x, y, y + 20 > bottom ? textWidth - 96 : textWidth, RED, 2);
			}
		}
		craftButton.active = reason.isEmpty() && hasCost(upgrade);
	}

	/** Draws text wrapped to a width, at most maxLines lines. Returns the y below it. */
	private int wrapped(GuiGraphicsExtractor graphics, String text, int x, int y, int width, int colour, int maxLines) {
		List<String> lines = new ArrayList<>();
		StringBuilder line = new StringBuilder();
		for (String word : text.split(" ")) {
			String next = line.isEmpty() ? word : line + " " + word;
			if (font.width(next) > width && !line.isEmpty()) {
				lines.add(line.toString());
				line = new StringBuilder(word);
			} else {
				line = new StringBuilder(next);
			}
		}
		if (!line.isEmpty()) {
			lines.add(line.toString());
		}
		for (int i = 0; i < lines.size() && i < maxLines; i++) {
			String shown = i == maxLines - 1 && lines.size() > maxLines ? shorten(lines.get(i) + "...", width) : lines.get(i);
			graphics.text(font, shown, x, y, colour);
			y += 10;
		}
		return y;
	}

	/** Item icons for upgrades, built once per id (never in a static initializer: items need their components first). */
	private static final class CharacterDataIcon {
		private static final Map<String, ItemStack> CACHE = new HashMap<>();

		static ItemStack of(String id) {
			return CACHE.computeIfAbsent(id == null ? "minecraft:barrier" : id, key -> com.onepiecemod.character.CharacterData.stack(key, 1));
		}
	}

	private void outline(GuiGraphicsExtractor graphics, int x, int y, int w, int h, int colour) {
		graphics.fill(x, y, x + w, y + 1, colour);
		graphics.fill(x, y + h - 1, x + w, y + h, colour);
		graphics.fill(x, y + 1, x + 1, y + h - 1, colour);
		graphics.fill(x + w - 1, y + 1, x + w, y + h - 1, colour);
	}

	/** Cuts long names so they fit in the list. */
	private String shorten(String text, int maxWidth) {
		if (font.width(text) <= maxWidth) {
			return text;
		}
		while (text.length() > 1 && font.width(text + "...") > maxWidth) {
			text = text.substring(0, text.length() - 1);
		}
		return text + "...";
	}

	// ---- Mouse ----

	@Override
	public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
		shiftClick = event.hasShiftDown();
		if (super.mouseClicked(event, doubleClick)) {
			return true;
		}
		int listX = left + 6, listY = top + 40;
		if (event.x() >= listX && event.x() < listX + LIST_WIDTH && event.y() >= listY) {
			int index = scroll + (int) ((event.y() - listY) / ROW);
			if (index < listSize() && index < scroll + visibleRows) {
				selected = index;
				return true;
			}
		}
		return false;
	}

	@Override
	public boolean mouseScrolled(double mouseX, double mouseY, double scrollX, double scrollY) {
		int maxScroll = Math.max(0, listSize() - visibleRows);
		scroll = Math.max(0, Math.min(maxScroll, scroll - (int) Math.signum(scrollY)));
		return true;
	}

	/** Closes the screen if the player walks away from the station. A station on a sailing ship isn't a block
	 * at pos (pos is just where you stood), and it moves with you, so then only the server's check counts. */
	@Override
	public void tick() {
		super.tick();
		Minecraft client = Minecraft.getInstance();
		if (client.player == null) {
			onClose();
			return;
		}
		boolean stationBlockHere = client.level != null && client.level.getBlockState(pos).getBlock() instanceof StationBlock;
		if (stationBlockHere && client.player.distanceToSqr(pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5) > 64.0) {
			onClose();
		}
	}
}
