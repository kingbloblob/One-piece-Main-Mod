package com.onepiecemod.questlog.client;

import java.util.ArrayList;
import java.util.List;

import com.mojang.blaze3d.platform.InputConstants;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.item.ItemStack;

import com.onepiecemod.character.CharacterData;
import com.onepiecemod.hud.HudPayload;
import com.onepiecemod.hud.client.HudClient;
import com.onepiecemod.questlog.QuestLogFeature;
import com.onepiecemod.sea.CalmBelt;
import com.onepiecemod.story.StoryData;

/**
 * The quest journal (O key or /questlog). Three pages:
 * - Active: the story chapter you're on and every quest step you've been given, ready ones in green.
 * - Finished: every quest step you've handed in.
 * - Voyage log: the islands your Log Pose recorded, newest first, and where the needle points now.
 *
 * Click a line on the left for its details on the right. "Track" pins an active quest under the compass
 * at the top of the screen. The quest tree (J) shows the whole story; this is your to-do list.
 */
public class QuestJournalScreen extends Screen {
	private static final int TOP = 44;
	private static final int ROW = 12;

	private static final int GOLD = 0xFFFFD75E;
	private static final int WHITE = 0xFFFFFFFF;
	private static final int GREY = 0xFFA8B0C0;
	private static final int DARK = 0xFF707888;
	private static final int GREEN = 0xFF7EE081;
	private static final int AQUA = 0xFF6FE3F0;

	private enum Page { ACTIVE, FINISHED, VOYAGE }

	/** One line on the left: what it says, its colour, the details on the right, and the quest key it tracks (or null). */
	private record Entry(String label, int colour, List<Detail> details, String trackKey) {
	}

	private record Detail(String text, int colour) {
	}

	private static Page page = Page.ACTIVE;

	private final QuestLogFeature.Open data;
	private final List<Entry> active = new ArrayList<>();
	private final List<Entry> finished = new ArrayList<>();
	private final List<Entry> voyage = new ArrayList<>();
	private String tracked;
	private int selected;
	private int scroll;

	private int left, panelWidth, listWidth, bottom;
	private Button trackButton;

	public QuestJournalScreen(QuestLogFeature.Open data) {
		super(Component.literal("Quest Journal"));
		this.data = data;
		this.tracked = data.tracked();
		buildActive();
		buildFinished();
		buildVoyage();
	}

	// ---- What each page lists ----

	private void buildActive() {
		StoryData.Chapter chapter = StoryData.chapter(data.chapter());
		if (chapter != null) {
			List<Detail> details = new ArrayList<>();
			details.add(new Detail("Main story", GOLD));
			details.add(new Detail("Chapter " + (chapter.index + 1) + ": " + chapter.title, WHITE));
			if (chapter.saga != null) {
				details.add(new Detail(chapter.saga.title, GREY));
			}
			HudPayload hud = HudClient.data();
			if (hud != null && !hud.goalText().isEmpty()) {
				details.add(new Detail("", WHITE));
				details.add(new Detail("Next: " + hud.goalText(), AQUA));
			}
			details.add(new Detail("", WHITE));
			details.add(new Detail("Every goal of this chapter is in the quest tree (J).", GREY));
			active.add(new Entry("★ Story: " + chapter.title, GOLD, details, QuestLogFeature.STORY));
		}
		for (String key : data.active()) {
			CharacterData.Quest quest = QuestLogFeature.quest(key);
			if (quest == null) {
				continue;
			}
			boolean ready = data.ready().contains(key);
			List<Detail> details = new ArrayList<>();
			details.add(new Detail(QuestLogText.giver(key) + "  ·  " + QuestLogText.stepOf(key), GOLD));
			details.add(new Detail(QuestLogText.summary(quest), WHITE));
			String progress = QuestLogText.itemProgress(quest);
			if (ready) {
				details.add(new Detail("✔ Done! Go back to " + QuestLogText.giver(key) + " to hand it in.", GREEN));
			} else if (progress != null) {
				details.add(new Detail("Carrying " + progress, AQUA));
			}
			String home = QuestLogText.home(key);
			if (home != null) {
				details.add(new Detail(QuestLogText.giver(key) + ": " + home, GREY));
			}
			if (quest.start != null && !quest.start.isEmpty()) {
				details.add(new Detail("", WHITE));
				details.add(new Detail("\"" + quest.start + "\"", GREY));
			}
			String reward = reward(quest);
			if (!reward.isEmpty()) {
				details.add(new Detail("", WHITE));
				details.add(new Detail("Reward: " + reward, AQUA));
			}
			active.add(new Entry((ready ? "✔ " : "◆ ") + QuestLogText.summary(quest), ready ? GREEN : WHITE, details, key));
		}
	}

	private void buildFinished() {
		List<String> done = data.done();
		for (int i = done.size() - 1; i >= 0; i--) { // Newest first.
			String key = done.get(i);
			CharacterData.Quest quest = QuestLogFeature.quest(key);
			if (quest == null) {
				continue;
			}
			List<Detail> details = new ArrayList<>();
			details.add(new Detail(QuestLogText.giver(key) + "  ·  " + QuestLogText.stepOf(key), GOLD));
			details.add(new Detail(QuestLogText.summary(quest), WHITE));
			if (quest.done != null && !quest.done.isEmpty()) {
				details.add(new Detail("", WHITE));
				details.add(new Detail("\"" + quest.done + "\"", GREY));
			}
			String reward = reward(quest);
			if (!reward.isEmpty()) {
				details.add(new Detail("", WHITE));
				details.add(new Detail("You got: " + reward, AQUA));
			}
			finished.add(new Entry("✔ " + QuestLogText.giver(key) + ": " + QuestLogText.summary(quest), DARK, details, null));
		}
	}

	private void buildVoyage() {
		if (!data.target().isEmpty()) {
			String[] parts = data.target().split(",", 3);
			voyage.add(island("➤ Next: ", parts, AQUA, "Your Log Pose points here. Sail there and stay a while to record it."));
		}
		List<String> islands = data.islands();
		for (int i = islands.size() - 1; i >= 0; i--) {
			String[] parts = islands.get(i).split(",", 3);
			voyage.add(island((i + 1) + ". ", parts, WHITE, i == islands.size() - 1 ? "The island you recorded last." : null));
		}
	}

	private static Entry island(String prefix, String[] parts, int colour, String note) {
		int x = Integer.parseInt(parts[0]);
		int z = Integer.parseInt(parts[1]);
		String name = QuestLogText.island(parts.length > 2 ? parts[2] : "");
		String sea = QuestLogText.sea(CalmBelt.seaByDistance(new BlockPos(x, 0, z)).name());
		List<Detail> details = new ArrayList<>();
		details.add(new Detail(name, GOLD));
		details.add(new Detail("In the " + sea, QuestLogText.seaColour(CalmBelt.seaByDistance(new BlockPos(x, 0, z)).name())));
		details.add(new Detail("X " + x + "  Z " + z, WHITE));
		net.minecraft.client.player.LocalPlayer player = net.minecraft.client.Minecraft.getInstance().player;
		if (player != null) {
			double dx = x - player.getX();
			double dz = z - player.getZ();
			details.add(new Detail((int) Math.sqrt(dx * dx + dz * dz) + " blocks from you", GREY));
		}
		if (note != null) {
			details.add(new Detail("", WHITE));
			details.add(new Detail(note, GREY));
		}
		return new Entry(prefix + name, colour, details, null);
	}

	private static String reward(CharacterData.Quest quest) {
		List<String> parts = new ArrayList<>();
		if (quest.berries > 0) {
			parts.add(quest.berries + " Berries");
		}
		if (quest.rewardItem != null && !quest.rewardItem.isEmpty()) {
			ItemStack stack = CharacterData.stack(quest.rewardItem, quest.rewardCount);
			if (!stack.isEmpty()) {
				parts.add((stack.getCount() > 1 ? stack.getCount() + " " : "") + stack.getHoverName().getString());
			}
		}
		if (quest.xpReward() > 0) {
			parts.add(quest.xpReward() + " Pirate XP");
		}
		return String.join(", ", parts);
	}

	private List<Entry> entries() {
		return switch (page) {
			case ACTIVE -> active;
			case FINISHED -> finished;
			case VOYAGE -> voyage;
		};
	}

	// ---- Layout ----

	@Override
	protected void init() {
		panelWidth = Math.min(width - 16, 460);
		left = (width - panelWidth) / 2;
		listWidth = Math.min(220, panelWidth / 2);
		bottom = height - 30;

		clearWidgets();
		String[] names = {"Active (" + active.size() + ")", "Finished (" + finished.size() + ")", "Voyage log (" + data.islands().size() + ")"};
		int tabWidth = Math.min(110, (panelWidth - 8) / 3);
		int tabsLeft = width / 2 - (tabWidth * 3 + 8) / 2;
		for (Page tab : Page.values()) {
			Button button = addRenderableWidget(Button.builder(Component.literal(names[tab.ordinal()]), b -> {
				page = tab;
				selected = 0;
				scroll = 0;
				init();
			}).pos(tabsLeft + tab.ordinal() * (tabWidth + 4), 20).size(tabWidth, 18).build());
			button.active = tab != page;
		}

		int detailX = left + listWidth + 8;
		int detailWidth = left + panelWidth - detailX;
		trackButton = addRenderableWidget(Button.builder(Component.empty(), b -> toggleTrack())
				.pos(detailX + 4, bottom - 24).size(Math.min(160, detailWidth - 8), 20).build());
		refreshTrackButton();

		addRenderableWidget(Button.builder(Component.literal("Close"), b -> onClose())
				.pos(width / 2 - 30, height - 24).size(60, 20).build());
	}

	private Entry selectedEntry() {
		List<Entry> entries = entries();
		return selected >= 0 && selected < entries.size() ? entries.get(selected) : null;
	}

	private void refreshTrackButton() {
		Entry entry = selectedEntry();
		trackButton.visible = entry != null && entry.trackKey() != null;
		if (trackButton.visible) {
			boolean on = entry.trackKey().equals(tracked);
			trackButton.setMessage(Component.literal(on ? "Stop tracking" : "Track on compass bar"));
		}
	}

	private void toggleTrack() {
		Entry entry = selectedEntry();
		if (entry == null || entry.trackKey() == null) {
			return;
		}
		tracked = entry.trackKey().equals(tracked) ? "" : entry.trackKey();
		QuestLogClient.track(tracked);
		refreshTrackButton();
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
		graphics.centeredText(font, "Quest Journal", width / 2, 7, GOLD);

		// The list on the left.
		box(graphics, left, TOP, listWidth, bottom - TOP);
		List<Entry> entries = entries();
		int fits = Math.max(1, (bottom - TOP - 8) / ROW);
		scroll = Math.max(0, Math.min(scroll, entries.size() - fits));
		if (entries.isEmpty()) {
			String empty = switch (page) {
				case ACTIVE -> "No quests yet. Talk to characters with a ! over their head.";
				case FINISHED -> "Nothing handed in yet.";
				case VOYAGE -> "Carry a Log Pose and stay on an island to record it.";
			};
			int y = TOP + 6;
			for (FormattedCharSequence line : font.split(Component.literal(empty), listWidth - 12)) {
				graphics.text(font, line, left + 6, y, GREY, false);
				y += font.lineHeight + 1;
			}
		}
		for (int i = scroll; i < entries.size() && i < scroll + fits; i++) {
			Entry entry = entries.get(i);
			int y = TOP + 4 + (i - scroll) * ROW;
			boolean hover = mouseX >= left && mouseX < left + listWidth && mouseY >= y - 1 && mouseY < y + ROW - 1;
			if (i == selected) {
				graphics.fill(left + 2, y - 2, left + listWidth - 2, y + ROW - 2, 0x60D4A537);
			} else if (hover) {
				graphics.fill(left + 2, y - 2, left + listWidth - 2, y + ROW - 2, 0x30FFFFFF);
			}
			String label = shorten(entry.label(), listWidth - 22);
			graphics.text(font, label, left + 6, y, entry.colour(), false);
			if (entry.trackKey() != null && entry.trackKey().equals(tracked)) {
				graphics.text(font, "◉", left + listWidth - 12, y, 0xFFFF4D4D, false); // Tracked.
			}
		}
		if (scroll + fits < entries.size()) {
			graphics.text(font, "scroll for more", left + 4, bottom + 3, GREY, false);
		}

		// The details on the right.
		int detailX = left + listWidth + 8;
		int detailWidth = left + panelWidth - detailX;
		box(graphics, detailX, TOP, detailWidth, bottom - TOP);
		Entry entry = selectedEntry();
		if (entry != null) {
			int y = TOP + 6;
			int maxY = trackButton.visible ? bottom - 28 : bottom - 4;
			for (Detail detail : entry.details()) {
				if (detail.text().isEmpty()) {
					y += 4;
					continue;
				}
				for (FormattedCharSequence line : font.split(Component.literal(detail.text()), detailWidth - 12)) {
					if (y + font.lineHeight > maxY) {
						break;
					}
					graphics.text(font, line, detailX + 6, y, detail.colour(), false);
					y += font.lineHeight + 1;
				}
			}
		}
	}

	private String shorten(String text, int maxWidth) {
		if (font.width(text) <= maxWidth) {
			return text;
		}
		while (!text.isEmpty() && font.width(text + "...") > maxWidth) {
			text = text.substring(0, text.length() - 1);
		}
		return text + "...";
	}

	private static void box(GuiGraphicsExtractor graphics, int x, int y, int w, int h) {
		graphics.fill(x - 1, y - 1, x + w + 1, y + h + 1, 0xFF6B4E14);
		graphics.fill(x, y, x + w, y + h, 0xFFD4A537);
		graphics.fillGradient(x + 1, y + 1, x + w - 1, y + h - 1, 0xF01B2640, 0xF00D1322);
	}

	@Override
	public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
		if (event.button() == InputConstants.MOUSE_BUTTON_LEFT && event.x() >= left && event.x() < left + listWidth
				&& event.y() >= TOP + 2 && event.y() < bottom) {
			int index = scroll + (int) ((event.y() - TOP - 2) / ROW);
			if (index < entries().size()) {
				selected = index;
				refreshTrackButton();
				return true;
			}
		}
		return super.mouseClicked(event, doubleClick);
	}

	@Override
	public boolean mouseScrolled(double mouseX, double mouseY, double scrollX, double scrollY) {
		scroll = Math.max(0, scroll - (int) Math.signum(scrollY) * 2);
		return true;
	}
}
