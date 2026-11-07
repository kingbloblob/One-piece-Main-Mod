package com.onepiecemod.stats.client;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.stats.PlayerStat;
import com.onepiecemod.stats.StatsData;
import com.onepiecemod.stats.StatsPayloads;

/**
 * The stat tree screen (K key), drawn as a real tree: your Pirate Level at the top is the root, and the five
 * stats branch down from it. Each branch is a line of 20 rank nodes; the big gold nodes at ranks 10 and 20
 * are milestone perks. Click a branch's "+" (or its next node) to spend a point; hover a branch to read about it.
 * "Reset" hands all your points back (the first time is free, then it costs Berries).
 */
public class StatTreeScreen extends Screen {
	private static final int PANEL_WIDTH = 340;
	private static final int GOLD = 0xFFFFD75E;
	private static final int LINE = 0xFF6A5A3A;

	private final List<Button> plusButtons = new ArrayList<>();
	private PlayerStat selected = PlayerStat.STRENGTH;
	private boolean confirmReset;
	private Button resetButton;

	// Where things are on screen. Worked out in init(), because it depends on the window size.
	private int left, top, panelWidth, rootY, iconY, nodesTop, nodeStep, plusY, detailsY, bottom;

	public StatTreeScreen() {
		super(Component.literal("Stat Tree"));
	}

	@Override
	protected void init() {
		panelWidth = Math.min(PANEL_WIDTH, width - 16);
		// Squeeze the branches on small windows (big GUI scale) so everything still fits.
		nodeStep = Math.max(4, Math.min(7, (height - 170) / PlayerStat.MAX_RANK));
		int treeHeight = 38 + 16 + 30 + PlayerStat.MAX_RANK * nodeStep + 22 + 44 + 24;
		left = (width - panelWidth) / 2;
		top = Math.max(4, (height - treeHeight) / 2);
		rootY = top + 42;
		iconY = rootY + 16;
		nodesTop = iconY + 30;
		plusY = nodesTop + PlayerStat.MAX_RANK * nodeStep + 4;
		detailsY = plusY + 20;
		bottom = detailsY + 44;

		clearWidgets();
		plusButtons.clear();
		PlayerStat[] stats = PlayerStat.values();
		for (int i = 0; i < stats.length; i++) {
			PlayerStat stat = stats[i];
			Button plus = Button.builder(Component.literal("+"), b -> spend(stat))
					.pos(columnX(i) - 9, plusY).size(18, 16).build();
			plusButtons.add(addRenderableWidget(plus));
		}
		int buttonsY = Math.min(height - 22, bottom + 2);
		resetButton = addRenderableWidget(Button.builder(Component.empty(), b -> reset())
				.pos(width / 2 - 124, buttonsY).size(160, 20).build());
		addRenderableWidget(Button.builder(Component.literal("Done"), b -> onClose())
				.pos(width / 2 + 40, buttonsY).size(84, 20).build());
	}

	private int columnX(int index) {
		int columns = PlayerStat.values().length;
		return left + panelWidth * (2 * index + 1) / (2 * columns);
	}

	private void spend(PlayerStat stat) {
		selected = stat;
		ClientPlayNetworking.send(new StatsPayloads.Spend(stat.id));
	}

	private void reset() {
		if (StatsClient.data().spentPoints() == 0) {
			return;
		}
		if (!confirmReset) {
			confirmReset = true; // Ask once: "Click again to confirm".
			return;
		}
		confirmReset = false;
		ClientPlayNetworking.send(new StatsPayloads.Respec(true));
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	private static ItemStack icon(PlayerStat stat) {
		return new ItemStack(switch (stat) {
			case STRENGTH -> Items.IRON_AXE;
			case TOUGHNESS -> Items.IRON_CHESTPLATE;
			case SPEED -> Items.FEATHER;
			case STAMINA -> Items.COOKED_BEEF;
			case SWORDSMANSHIP -> Items.IRON_SWORD;
		});
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		StatsData data = StatsClient.data();
		PlayerStat[] stats = PlayerStat.values();
		for (int i = 0; i < plusButtons.size(); i++) {
			plusButtons.get(i).active = data.canRaise(stats[i]);
		}
		int cost = StatsClient.respecCost();
		resetButton.active = data.spentPoints() > 0;
		resetButton.setMessage(Component.literal(confirmReset ? "Click again to reset"
				: "Reset points" + (cost > 0 ? " (" + cost + " Berries)" : " (free)")));

		graphics.fill(left - 6, top - 6, left + panelWidth + 6, bottom, 0xC0000000);
		graphics.fill(left - 6, top - 6, left + panelWidth + 6, top - 4, GOLD);
		header(graphics, data);

		// The root node, and the branch line that joins every stat to it.
		int rootX = left + panelWidth / 2;
		graphics.fill(columnX(0), rootY + 7, columnX(stats.length - 1) + 1, rootY + 9, LINE);
		graphics.fill(rootX - 1, rootY, rootX + 1, rootY + 8, LINE);
		node(graphics, rootX, rootY, 7, GOLD, true);

		for (int i = 0; i < stats.length; i++) {
			int x = columnX(i);
			int columnLeft = x - panelWidth / (2 * stats.length);
			int columnRight = x + panelWidth / (2 * stats.length);
			if (mouseX >= columnLeft && mouseX < columnRight && mouseY >= iconY && mouseY < plusY + 16) {
				selected = stats[i];
			}
			branch(graphics, stats[i], data.rank(stats[i]), x);
		}

		details(graphics, data, detailsY);
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
	}

	@Override
	public boolean mouseClicked(net.minecraft.client.input.MouseButtonEvent event, boolean doubleClick) {
		// Clicking a branch's next node spends a point there too.
		PlayerStat[] stats = PlayerStat.values();
		StatsData data = StatsClient.data();
		for (int i = 0; i < stats.length; i++) {
			int next = data.rank(stats[i]) + 1;
			if (next > PlayerStat.MAX_RANK || !data.canRaise(stats[i])) {
				continue;
			}
			int y = nodesTop + (next - 1) * nodeStep + nodeStep / 2;
			if (Math.abs(event.x() - columnX(i)) <= 6 && Math.abs(event.y() - y) <= Math.max(3, nodeStep / 2)) {
				spend(stats[i]);
				return true;
			}
		}
		if (confirmReset && !resetButton.isMouseOver(event.x(), event.y())) {
			confirmReset = false;
		}
		return super.mouseClicked(event, doubleClick);
	}

	private void header(GuiGraphicsExtractor graphics, StatsData data) {
		int level = data.level();
		graphics.text(font, "Pirate Level " + level, left, top, GOLD, true);
		String points = data.freePoints() + " point" + (data.freePoints() == 1 ? "" : "s") + " to spend";
		graphics.text(font, points, left + panelWidth - font.width(points), top,
				data.freePoints() > 0 ? 0xFF55FF55 : 0xFFAAAAAA, true);

		// XP bar towards the next level.
		int barY = top + 13;
		graphics.fill(left, barY, left + panelWidth, barY + 5, 0xFF303030);
		String label;
		if (level >= StatsData.MAX_LEVEL) {
			graphics.fill(left, barY, left + panelWidth, barY + 5, GOLD);
			label = "Max level! You are a true monster of the seas.";
		} else {
			int need = StatsData.xpForNextLevel(level);
			int filled = (int) ((long) panelWidth * data.xpIntoLevel() / need);
			graphics.fill(left, barY, left + filled, barY + 5, 0xFF7ED957);
			label = data.xpIntoLevel() + " / " + need + " XP. Fight and train to level up.";
		}
		graphics.text(font, label, left, barY + 8, 0xFFCCCCCC, false);
	}

	/** One stat: its icon and rank at the top, then a line of 20 nodes going down. */
	private void branch(GuiGraphicsExtractor graphics, PlayerStat stat, int rank, int x) {
		int color = 0xFF000000 | stat.color;
		if (stat == selected) {
			graphics.fill(x - 14, iconY - 2, x + 14, plusY - 2, 0x28FFFFFF);
		}
		graphics.fill(x - 1, rootY + 8, x + 1, nodesTop + PlayerStat.MAX_RANK * nodeStep, LINE);
		graphics.fill(x - 9, iconY - 1, x + 9, iconY + 17, 0xFF202020);
		graphics.fakeItem(icon(stat), x - 8, iconY);
		String ranks = rank + "/" + PlayerStat.MAX_RANK;
		graphics.text(font, ranks, x - font.width(ranks) / 2, iconY + 19, rank > 0 ? color : 0xFF888888, false);

		for (int r = 1; r <= PlayerStat.MAX_RANK; r++) {
			int y = nodesTop + (r - 1) * nodeStep + nodeStep / 2;
			boolean milestone = r == PlayerStat.FIRST_MILESTONE || r == PlayerStat.SECOND_MILESTONE;
			boolean owned = r <= rank;
			if (owned) {
				// The filled part of the branch glows in the stat's colour.
				graphics.fill(x - 1, y - nodeStep, x + 1, y + 1, color);
			}
			if (milestone) {
				node(graphics, x, y, 5, owned ? GOLD : 0xFF7A6A3A, owned);
			} else {
				node(graphics, x, y, nodeStep >= 6 ? 2 : 1, owned ? color : 0xFF444444, owned);
			}
		}
	}

	/** A square node centred on x, y with a dark border. */
	private static void node(GuiGraphicsExtractor graphics, int x, int y, int radius, int color, boolean bright) {
		graphics.fill(x - radius - 1, y - radius - 1, x + radius + 2, y + radius + 2, 0xFF101010);
		graphics.fill(x - radius, y - radius, x + radius + 1, y + radius + 1, color);
		if (bright && radius >= 3) {
			graphics.fill(x - radius + 1, y - radius + 1, x, y, 0x60FFFFFF); // A little shine.
		}
	}

	private void details(GuiGraphicsExtractor graphics, StatsData data, int y) {
		PlayerStat stat = selected;
		int rank = data.rank(stat);
		graphics.fill(left, y, left + panelWidth, y + 1, 0xFF000000 | stat.color);
		y += 3;
		y = wrapped(graphics, stat.displayName + ": " + stat.description + " Each rank: " + stat.perRank, y, 0xFFDDDDDD);
		y = milestone(graphics, PlayerStat.FIRST_MILESTONE, stat.firstMilestone, rank, y);
		milestone(graphics, PlayerStat.SECOND_MILESTONE, stat.secondMilestone, rank, y);
	}

	private int milestone(GuiGraphicsExtractor graphics, int needed, String text, int rank, int y) {
		boolean unlocked = rank >= needed;
		String prefix = unlocked ? "Unlocked: " : "Rank " + needed + ": ";
		return wrapped(graphics, prefix + text, y, unlocked ? GOLD : 0xFF777777);
	}

	/** Draws text that wraps onto more lines if it is wider than the panel. Returns the y below it. */
	private int wrapped(GuiGraphicsExtractor graphics, String text, int y, int color) {
		for (FormattedCharSequence line : font.split(Component.literal(text), panelWidth)) {
			graphics.text(font, line, left, y, color, false);
			y += font.lineHeight;
		}
		return y;
	}
}
