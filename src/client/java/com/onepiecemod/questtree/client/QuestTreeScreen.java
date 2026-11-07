package com.onepiecemod.questtree.client;

import java.util.List;

import com.mojang.blaze3d.platform.InputConstants;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;

import com.onepiecemod.questtree.QuestTreeFeature;

/**
 * The big quest tree screen (J or /quests): the tree on the left, the details of the clicked line on the right.
 * The tree itself (lines, colours, details) is in QuestTree; this class only lays it out.
 */
public class QuestTreeScreen extends Screen {
	private static final int TOP = 44;

	private final QuestTree tree;

	// Where things are on screen. Worked out in init(), because it depends on the window size.
	private int left, panelWidth, treeWidth, bottom;

	public QuestTreeScreen(QuestTreeFeature.Open data) {
		super(Component.literal("Quest Tree"));
		this.tree = new QuestTree(data);
	}

	@Override
	protected void init() {
		panelWidth = Math.min(width - 16, 500);
		left = (width - panelWidth) / 2;
		treeWidth = Math.min(240, panelWidth / 2);
		bottom = height - 30;

		clearWidgets();
		Button storyButton = addRenderableWidget(Button.builder(Component.literal("Story"), b -> switchTab(true))
				.pos(width / 2 - 102, 20).size(100, 18).build());
		Button questButton = addRenderableWidget(Button.builder(Component.literal("Character quests"), b -> switchTab(false))
				.pos(width / 2 + 2, 20).size(100, 18).build());
		storyButton.active = !QuestTree.storyTab();
		questButton.active = QuestTree.storyTab();
		addRenderableWidget(Button.builder(Component.literal("Close"), b -> onClose())
				.pos(width / 2 - 30, height - 24).size(60, 20).build());

		// Start with the selected line (the line you're on now) in view.
		tree.scrollToSelected(Math.max(1, (bottom - TOP - 8) / QuestTree.ROW));
	}

	private void switchTab(boolean story) {
		tree.switchTab(story);
		init();
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
		graphics.centeredText(font, "Quest Tree", width / 2, 7, QuestTree.YELLOW);

		tree.drawTree(graphics, font, left, TOP, treeWidth, bottom - TOP, mouseX, mouseY);

		// The details of the selected line.
		int detailX = left + treeWidth + 8;
		int detailWidth = left + panelWidth - detailX;
		QuestTree.box(graphics, detailX, TOP, detailWidth, bottom - TOP);
		QuestTree.Node selected = tree.selected;
		if (selected == null) {
			return;
		}
		if (!selected.icon.isEmpty()) {
			graphics.fakeItem(selected.icon, detailX + detailWidth - 22, TOP + 4);
		}
		// Leave room for the icon in the top right corner.
		int textWidth = detailWidth - 12 - 22;
		List<QuestTree.DetailRow> rows = tree.detailRows(font, selected, textWidth);
		int y = TOP + 6;
		int fits = Math.max(1, (bottom - y - 4) / (font.lineHeight + 1));
		tree.detailScroll = Math.max(0, Math.min(tree.detailScroll, rows.size() - fits));
		for (int i = tree.detailScroll; i < rows.size() && i < tree.detailScroll + fits; i++) {
			QuestTree.DetailRow row = rows.get(i);
			if (row.text() != null) {
				graphics.text(font, row.text(), detailX + 6, y, QuestTree.WHITE, false);
			} else {
				// A progress bar, with how far along it is at the end.
				String label = row.have() + "/" + row.need() + "  " + QuestTree.percent(row.have(), row.need()) + "%";
				int barWidth = Math.min(140, textWidth - font.width(label) - 6);
				QuestTree.bar(graphics, detailX + 8, y + 1, barWidth, 7, row.have(), row.need());
				graphics.text(font, label, detailX + 8 + barWidth + 5, y, QuestTree.GREY, false);
			}
			y += font.lineHeight + 1;
		}
		if (tree.detailScroll + fits < rows.size()) {
			graphics.text(font, "scroll for more", detailX + 6, bottom + 3, QuestTree.GREY);
		}

		drawOverall(graphics);

		// A tree line that was cut off with "..." shows its full text when hovered.
		if (tree.hovered != null && tree.hoveredCut) {
			graphics.setTooltipForNextFrame(font, font.split(Component.literal(tree.hovered.label), 220), mouseX, mouseY);
		}
	}

	/** How far through the whole story (or all quest lines) you are, under the tree. */
	private void drawOverall(GuiGraphicsExtractor graphics) {
		int have = 0, need = 0;
		for (QuestTree.Node root : tree.roots()) {
			if (QuestTree.storyTab()) {
				have += root.have;
				need += root.need;
			} else {
				for (QuestTree.Node character : root.children) {
					have += character.state == QuestTree.State.DONE ? 1 : 0;
					need++;
				}
			}
		}
		if (need == 0) {
			return;
		}
		String label = (QuestTree.storyTab() ? "Story: " + have + "/" + need + " chapters" : "Quest lines: " + have + "/" + need + " done")
				+ "  " + QuestTree.percent(have, need) + "%";
		int space = width / 2 - 36 - left;
		int barWidth = Math.min(90, space - font.width(label) - 6);
		int y = bottom + 7;
		if (barWidth >= 20) {
			QuestTree.bar(graphics, left, y, barWidth, 7, have, need);
			graphics.text(font, label, left + barWidth + 5, y, QuestTree.GREY, false);
		} else {
			graphics.text(font, QuestTree.shorten(font, label, space), left, y, QuestTree.GREY, false);
		}
	}

	@Override
	public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
		if (event.button() == InputConstants.MOUSE_BUTTON_LEFT && tree.click(event.x(), event.y())) {
			return true;
		}
		return super.mouseClicked(event, doubleClick);
	}

	@Override
	public boolean mouseScrolled(double mouseX, double mouseY, double scrollX, double scrollY) {
		int by = -(int) Math.signum(scrollY);
		if (mouseX < left + treeWidth + 4) {
			tree.scroll(by * 3);
		} else {
			tree.detailScroll = Math.max(0, tree.detailScroll + by * 2);
		}
		return true;
	}
}
