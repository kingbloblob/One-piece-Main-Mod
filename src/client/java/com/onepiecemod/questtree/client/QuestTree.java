package com.onepiecemod.questtree.client;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Supplier;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.item.ItemStack;

import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.Locations;
import com.onepiecemod.questtree.QuestTreeFeature;
import com.onepiecemod.story.StoryData;

/**
 * The quest tree itself: the lines, what's done, and the details of each line. Two tabs:
 *   Story             sagas > chapters > goals, from onepiece/story.json
 *   Character quests  In progress / Not started / Complete > characters > their quest steps, from onepiece/characters.json
 * Green ✔ = done, yellow ➤ = what you're on now, aqua ! = done, go hand it in, grey = locked or not started yet.
 *
 * Progress shows as bars: under each goal in the details, and as a small bar at the end of each tree line.
 *
 * Drawn in two places: the big screen (QuestTreeScreen, J or /quests) and the panel beside the inventory (QuestTreePanel).
 */
public class QuestTree {
	static final int ROW = 12;
	static final int INDENT = 10;

	static final int WHITE = 0xFFFFFFFF, GREY = 0xFFA0A0A0, DARK = 0xFF707070, GOLD = 0xFFFFC23C,
			YELLOW = 0xFFFFD75E, GREEN = 0xFF7CE07C, AQUA = 0xFF6FE3FF, BORDER = 0xFF8B6B3E, LINE = 0xFF6B5638;
	static final int BAR_BACK = 0xFF3A2E22, BAR_FILL = 0xFF5FBF5F, BAR_DONE = 0xFF7CE07C;
	/** Room kept at the end of a tree line for its small progress bar. */
	static final int MINI_BAR = 26;
	private static final Pattern PROGRESS = Pattern.compile("([\\d,]+)[^/\\d]*/\\s*([\\d,]+)");
	enum State { DONE, CURRENT, READY, LOCKED, GROUP }

	/** One line in the tree. Its details are worked out only when it's clicked. */
	static class Node {
		final String key;
		final String label;
		final State state;
		final List<Node> children = new ArrayList<>();
		Supplier<List<Line>> detail = List::of;
		ItemStack icon = ItemStack.EMPTY;
		/** Progress for the small bar at the end of the line; no bar when need is 0. */
		int have, need;

		Node(String key, String label, State state) {
			this.key = key;
			this.label = label;
			this.state = state;
		}
	}

	/** One line of the details panel. A line with no text and a need above 0 is a progress bar. */
	record Line(String text, int color, int have, int need) {
		Line(String text, int color) {
			this(text, color, 0, 0);
		}

		static Line bar(int have, int need) {
			return new Line("", WHITE, have, need);
		}

		boolean isBar() {
			return text.isEmpty() && need > 0;
		}
	}

	/** A details line as drawn: wrapped text, or a progress bar when text is null. */
	record DetailRow(FormattedCharSequence text, int have, int need) {}

	/** A tree line as drawn: how deep it is, and which of its parents still have lines below them (for the connecting lines). */
	record Row(Node node, int depth, boolean[] continues, boolean last) {}

	// Remembered while the game runs, so the tree opens the way you left it.
	private static boolean storyTab = true;
	private static final Set<String> expanded = new HashSet<>();
	private static String selectedKey = null;
	private final QuestTreeFeature.Open data;
	private final List<Node> story = new ArrayList<>();
	private final List<Node> characters = new ArrayList<>();
	private final List<Row> rows = new ArrayList<>();
	Node selected;
	int scroll, detailScroll;

	/** Where the tree was last drawn, for mouse clicks. */
	private int treeX, treeY, treeWidth, visibleRows = 1;
	/** The line under the mouse in the last frame, or null. */
	Node hovered;
	/** True if the hovered line's text was too long and got cut off with "...". */
	boolean hoveredCut;

	public QuestTree(QuestTreeFeature.Open data) {
		this.data = data;
		buildStory();
		buildCharacters();
		layoutRows();
	}

	static boolean storyTab() {
		return storyTab;
	}

	void switchTab(boolean story) {
		storyTab = story;
		selectedKey = null;
		selected = null;
		scroll = 0;
		layoutRows();
	}

	// ---- Building the tree ----

	private void buildStory() {
		int current = data.chapter();
		int total = StoryData.chapters().size();
		for (StoryData.Saga saga : StoryData.get().sagas) {
			int done = 0;
			boolean hasCurrent = false;
			for (StoryData.Chapter chapter : saga.chapters) {
				done += chapter.index < current ? 1 : 0;
				hasCurrent |= chapter.index == current;
			}
			State sagaState = done == saga.chapters.size() ? State.DONE : hasCurrent ? State.CURRENT : State.LOCKED;
			Node sagaNode = new Node("saga:" + saga.id, saga.title + "  " + done + "/" + saga.chapters.size(), sagaState);
			sagaNode.have = done;
			sagaNode.need = saga.chapters.size();
			sagaNode.detail = () -> sagaDetail(saga, current);
			if (hasCurrent) {
				expanded.add(sagaNode.key);
			}

			for (StoryData.Chapter chapter : saga.chapters) {
				State state = chapter.index < current ? State.DONE : chapter.index == current ? State.CURRENT : State.LOCKED;
				Node chapterNode = new Node("chapter:" + chapter.id, (chapter.index + 1) + ". " + chapter.title, state);
				chapterNode.detail = () -> chapterDetail(chapter, state, total);
				chapterNode.icon = state == State.LOCKED ? ItemStack.EMPTY : chapterIcon(chapter);
				if (state != State.LOCKED) {
					chapterNode.have = state == State.DONE ? chapter.goals.size() : goalsDone(chapter);
					chapterNode.need = chapter.goals.size();
				}
				if (state != State.LOCKED) {
					// Locked chapters keep their goals secret.
					for (int i = 0; i < chapter.goals.size(); i++) {
						StoryData.Goal goal = chapter.goals.get(i);
						boolean goalDone = state == State.DONE || data.goalsDone().contains(Integer.toString(i));
						String progress = !goalDone && state == State.CURRENT ? goalProgress(i) : "";
						Node goalNode = new Node(chapterNode.key + ":" + i, goal.text + (progress.isEmpty() ? "" : " (" + progress + ")"),
								goalDone ? State.DONE : State.CURRENT);
						goalNode.detail = chapterNode.detail;
						goalNode.icon = chapterNode.icon;
						int[] counts = parseProgress(progress);
						if (counts != null) {
							goalNode.have = counts[0];
							goalNode.need = counts[1];
						}
						chapterNode.children.add(goalNode);
					}
				}
				if (state == State.CURRENT) {
					expanded.add(chapterNode.key);
				}
				sagaNode.children.add(chapterNode);
			}
			story.add(sagaNode);
		}
	}

	private void buildCharacters() {
		Node inProgress = new Node("group:progress", "In progress", State.GROUP);
		Node notStarted = new Node("group:new", "Not started", State.GROUP);
		Node complete = new Node("group:done", "Complete", State.GROUP);
		expanded.add(inProgress.key);

		for (CharacterData character : CharacterData.all().values()) {
			if (character.quests.isEmpty()) {
				continue;
			}
			int steps = character.quests.size();
			int done = 0;
			boolean started = false;
			for (int i = 0; i < steps; i++) {
				done += isDone(character, i) ? 1 : 0;
				started |= isStarted(character, i);
			}
			boolean ready = data.questsReady().contains(character.id);
			State state = done == steps ? State.DONE : ready ? State.READY : started ? State.CURRENT : State.LOCKED;

			Node node = new Node("character:" + character.id, character.name + "  " + done + "/" + steps, state);
			node.detail = () -> characterDetail(character, state);
			node.icon = CharacterData.stack("onepiece:vivre_card_" + character.id, 1);
			if (state != State.LOCKED) {
				node.have = done;
				node.need = steps;
			}
			for (int i = 0; i < steps; i++) {
				int step = i;
				State stepState = stepState(character, step, ready);
				String text = stepState == State.LOCKED ? (step == 0 ? "Find " + character.name + " to start" : "???") : stepSummary(character.quests.get(step));
				Node stepNode = new Node(node.key + ":" + step, "Step " + (step + 1) + ": " + text, stepState);
				stepNode.detail = () -> stepDetail(character, step, stepState);
				stepNode.icon = node.icon;
				int[] counts = stepState == State.CURRENT ? itemProgress(character.quests.get(step)) : null;
				if (counts != null) {
					stepNode.have = counts[0];
					stepNode.need = counts[1];
				}
				node.children.add(stepNode);
			}
			(state == State.DONE ? complete : state == State.LOCKED ? notStarted : inProgress).children.add(node);
		}

		for (Node group : List.of(inProgress, notStarted, complete)) {
			Node labelled = new Node(group.key, group.label + " (" + group.children.size() + ")", State.GROUP);
			labelled.children.addAll(group.children);
			labelled.detail = () -> List.of(
					new Line(group.label, GOLD),
					new Line("", WHITE),
					new Line("Characters with a quest line. Talk to one (right-click) to start their first step, "
							+ "then go back to them each time a step is done for your reward and the next step.", GREY),
					new Line("", WHITE),
					new Line("A green ✔ means done, a yellow ➤ means you're on it, and an aqua ! means it's done: go back and hand it in.", GREY));
			characters.add(labelled);
		}
	}

	private boolean isDone(CharacterData character, int step) {
		return data.questsDone().contains(character.id + ":" + step);
	}

	private boolean isStarted(CharacterData character, int step) {
		return data.questsStarted().contains(character.id + ":" + step);
	}

	private State stepState(CharacterData character, int step, boolean ready) {
		if (isDone(character, step)) {
			return State.DONE;
		}
		if (isStarted(character, step)) {
			return ready ? State.READY : State.CURRENT;
		}
		return State.LOCKED;
	}

	private String goalProgress(int goal) {
		String text = goal < data.goalProgress().size() ? data.goalProgress().get(goal) : "";
		return text == null ? "" : text;
	}

	private int goalsDone(StoryData.Chapter chapter) {
		int done = 0;
		for (int i = 0; i < chapter.goals.size(); i++) {
			done += data.goalsDone().contains(Integer.toString(i)) ? 1 : 0;
		}
		return done;
	}

	/** "3/16", "120/500 blocks" or "1,000 Berries / 5,000 Berries" as {3, 16}; null if it has no numbers to show. */
	static int[] parseProgress(String text) {
		if (text == null || text.isEmpty()) {
			return null;
		}
		Matcher matcher = PROGRESS.matcher(text);
		if (!matcher.find()) {
			return null;
		}
		try {
			long have = Long.parseLong(matcher.group(1).replace(",", ""));
			long need = Long.parseLong(matcher.group(2).replace(",", ""));
			if (need <= 0) {
				return null;
			}
			// Big numbers (bounties) are scaled down so they fit in an int.
			while (need > Integer.MAX_VALUE / 2) {
				have /= 10;
				need /= 10;
			}
			return new int[] { (int) Math.min(have, need), (int) need };
		} catch (NumberFormatException e) {
			return null;
		}
	}

	/** How many of a "bring" step's items you're carrying, or null for other steps. */
	private static int[] itemProgress(CharacterData.Quest quest) {
		if (!quest.type.equals("fetch") || quest.count <= 0 || Minecraft.getInstance().player == null) {
			return null;
		}
		int have = Minecraft.getInstance().player.getInventory().countItem(CharacterData.item(quest.item));
		return new int[] { Math.min(have, quest.count), quest.count };
	}

	// ---- Details panel text ----

	List<Line> sagaDetail(StoryData.Saga saga, int current) {
		List<Line> lines = new ArrayList<>();
		lines.add(new Line(saga.title, GOLD));
		int sagaDone = 0;
		for (StoryData.Chapter chapter : saga.chapters) {
			sagaDone += chapter.index < current ? 1 : 0;
		}
		lines.add(new Line(sagaDone + " of " + saga.chapters.size() + " chapters done", GREY));
		lines.add(Line.bar(sagaDone, saga.chapters.size()));
		lines.add(new Line("", WHITE));
		for (StoryData.Chapter chapter : saga.chapters) {
			boolean done = chapter.index < current;
			boolean now = chapter.index == current;
			lines.add(new Line((done ? "✔ " : now ? "➤ " : "· ") + (chapter.index + 1) + ". " + chapter.title,
					done ? GREEN : now ? YELLOW : DARK));
		}
		return lines;
	}

	private List<Line> chapterDetail(StoryData.Chapter chapter, State state, int total) {
		List<Line> lines = new ArrayList<>();
		lines.add(new Line(chapter.title, GOLD));
		lines.add(new Line("Chapter " + (chapter.index + 1) + " of " + total + " · " + chapter.saga.title, GREY));
		lines.add(new Line(state == State.DONE ? "Done" : state == State.CURRENT ? "You are on this chapter" : "Locked",
				colour(state)));
		lines.add(new Line("", WHITE));
		if (state == State.LOCKED) {
			lines.add(new Line("Finish the chapters before this one to unlock it. Its goals stay secret until then!", GREY));
			return lines;
		}
		if (!chapter.intro.isEmpty()) {
			lines.add(new Line(chapter.intro, GREY));
			lines.add(new Line("", WHITE));
		}
		int goalsDone = state == State.DONE ? chapter.goals.size() : goalsDone(chapter);
		lines.add(new Line("Goals: " + goalsDone + " of " + chapter.goals.size() + " done", WHITE));
		lines.add(Line.bar(goalsDone, chapter.goals.size()));
		for (int i = 0; i < chapter.goals.size(); i++) {
			boolean done = state == State.DONE || data.goalsDone().contains(Integer.toString(i));
			String progress = done ? "" : goalProgress(i);
			lines.add(new Line((done ? "✔ " : "• ") + chapter.goals.get(i).text + (progress.isEmpty() ? "" : " (" + progress + ")"),
					done ? GREEN : WHITE));
			int[] counts = parseProgress(progress);
			if (counts != null) {
				lines.add(Line.bar(counts[0], counts[1]));
			}
		}
		String reward = rewardText(chapter.reward.berries, chapter.reward.items.stream().map(item -> CharacterData.stack(item.item, item.count)).toList());
		if (!reward.isEmpty()) {
			lines.add(new Line("", WHITE));
			lines.add(new Line("Reward: " + reward, AQUA));
		}
		if (state == State.CURRENT && !chapter.charts.isEmpty()) {
			lines.add(new Line("", WHITE));
			List<String> places = chapter.charts.stream().map(Locations::name).toList();
			lines.add(new Line("Sea Chart to: " + String.join(", ", places) + ". Lost it? Type /story chart.", GREY));
		}
		if (state == State.DONE && !chapter.outro.isEmpty()) {
			lines.add(new Line("", WHITE));
			lines.add(new Line(chapter.outro, GREY));
		}
		return lines;
	}

	private List<Line> characterDetail(CharacterData character, State state) {
		List<Line> lines = new ArrayList<>();
		lines.add(new Line(character.name, GOLD));
		lines.add(new Line(switch (state) {
			case DONE -> "Quest line complete";
			case READY -> "Step done: go back to " + character.name + " to hand it in";
			case CURRENT -> "Quest line in progress";
			default -> "Not started yet";
		}, colour(state)));
		String home = Locations.home(character.id);
		if (home != null) {
			lines.add(new Line((Locations.onlyLastSeen(character.id) ? "Last seen at: " : "Found at: ") + Locations.name(home), GREY));
		}
		int stepsDone = 0;
		for (int i = 0; i < character.quests.size(); i++) {
			stepsDone += isDone(character, i) ? 1 : 0;
		}
		lines.add(new Line("", WHITE));
		lines.add(new Line("Steps: " + stepsDone + " of " + character.quests.size() + " done", WHITE));
		lines.add(Line.bar(stepsDone, character.quests.size()));
		for (int i = 0; i < character.quests.size(); i++) {
			State stepState = stepState(character, i, state == State.READY);
			String text = stepState == State.LOCKED ? "???" : stepSummary(character.quests.get(i));
			lines.add(new Line(symbol(stepState) + " Step " + (i + 1) + ": " + text, colour(stepState)));
		}
		// Story chapters that need this quest line.
		for (StoryData.Chapter chapter : StoryData.chapters()) {
			for (StoryData.Goal goal : chapter.goals) {
				for (StoryData.Goal option : goal.of.isEmpty() ? List.of(goal) : goal.of) {
					if ("quest".equals(option.type) && character.id.equals(option.character)) {
						lines.add(new Line("", WHITE));
						lines.add(new Line("The story needs step " + option.step + " in chapter " + (chapter.index + 1)
								+ (chapter.index <= data.chapter() ? " (" + chapter.title + ")" : "") + ".", YELLOW));
					}
				}
			}
		}
		if (state == State.LOCKED) {
			lines.add(new Line("", WHITE));
			lines.add(new Line("Find " + character.name + " and right-click them to start.", GREY));
		}
		return lines;
	}

	private List<Line> stepDetail(CharacterData character, int step, State state) {
		CharacterData.Quest quest = character.quests.get(step);
		List<Line> lines = new ArrayList<>();
		lines.add(new Line(character.name + ": step " + (step + 1) + " of " + character.quests.size(), GOLD));
		if (state == State.LOCKED) {
			lines.add(new Line("Locked", DARK));
			lines.add(new Line("", WHITE));
			lines.add(new Line(step == 0 ? "Find " + character.name + " and right-click them to start their quest line."
					: "Finish the step before this one to find out what " + character.name + " wants next.", GREY));
			return lines;
		}
		lines.add(new Line(stepSummary(quest), WHITE));
		lines.add(new Line(state == State.DONE ? "Done" : state == State.READY ? "Done! Go back to " + character.name + " to hand it in."
				: "You are on this step", colour(state)));
		lines.add(new Line("", WHITE));
		if (!quest.start.isEmpty()) {
			lines.add(new Line("\"" + quest.start + "\"", GREY));
		}
		if (state == State.CURRENT) {
			lines.add(new Line("", WHITE));
			lines.add(new Line(switch (quest.type) {
				case "defeat" -> "Use the Wanted Poster " + character.name + " gave you, or follow the Sea Chart to the boss's lair.";
				case "talk" -> "Right-click the Vivre Card " + character.name + " gave you to see which way to go.";
				case "deliver" -> "Carry the package to " + name(quest.target) + " and talk to them. Their Vivre Card points the way.";
				case "explore" -> "Follow the Sea Chart to " + com.onepiecemod.character.Locations.name(quest.target) + ".";
				case "escort" -> name(quest.target) + " follows you. Follow the Sea Chart to "
						+ com.onepiecemod.character.Locations.name(quest.place) + " together.";
				default -> "You have " + Math.min(quest.count, Minecraft.getInstance().player.getInventory().countItem(CharacterData.item(quest.item)))
						+ "/" + quest.count + ".";
			}, AQUA));
			int[] counts = itemProgress(quest);
			if (counts != null) {
				lines.add(Line.bar(counts[0], counts[1]));
			}
		}
		if (state == State.DONE && !quest.done.isEmpty()) {
			lines.add(new Line("", WHITE));
			lines.add(new Line("\"" + quest.done + "\"", GREY));
		}
		String reward = rewardText(quest.berries, List.of(CharacterData.stack(quest.rewardItem, quest.rewardCount)));
		if (!reward.isEmpty()) {
			lines.add(new Line("", WHITE));
			lines.add(new Line("Reward: " + reward, AQUA));
		}
		return lines;
	}

	/** "Beat Buggy", "Talk to Koby" or "Bring 16 Cooked Beef". */
	private static String stepSummary(CharacterData.Quest quest) {
		return switch (quest.type) {
			case "defeat" -> "Beat " + name(quest.target);
			case "talk" -> "Talk to " + name(quest.target);
			case "deliver" -> "Deliver a package to " + name(quest.target);
			case "explore" -> "Explore " + com.onepiecemod.character.Locations.name(quest.target);
			case "escort" -> "Escort " + name(quest.target) + " to " + com.onepiecemod.character.Locations.name(quest.place);
			default -> {
				ItemStack stack = CharacterData.stack(quest.item, 1);
				yield "Bring " + quest.count + " " + (stack.isEmpty() ? quest.item : stack.getHoverName().getString());
			}
		};
	}

	private static String name(String characterId) {
		CharacterData character = CharacterData.get(characterId);
		return character != null ? character.name : characterId;
	}

	private static String rewardText(int berries, List<ItemStack> items) {
		List<String> parts = new ArrayList<>();
		if (berries > 0) {
			parts.add(berries + " Berries");
		}
		for (ItemStack stack : items) {
			if (!stack.isEmpty()) {
				parts.add((stack.getCount() > 1 ? stack.getCount() + " " : "") + stack.getHoverName().getString());
			}
		}
		return String.join(", ", parts);
	}

	private static ItemStack chapterIcon(StoryData.Chapter chapter) {
		for (StoryData.ItemReward item : chapter.reward.items) {
			ItemStack stack = CharacterData.stack(item.item, 1);
			if (!stack.isEmpty()) {
				return stack;
			}
		}
		return CharacterData.stack("onepiece:captains_log", 1);
	}

	private static int colour(State state) {
		return switch (state) {
			case DONE -> GREEN;
			case CURRENT -> YELLOW;
			case READY -> AQUA;
			case LOCKED -> DARK;
			case GROUP -> GOLD;
		};
	}

	private static String symbol(State state) {
		return switch (state) {
			case DONE -> "✔";
			case CURRENT -> "➤";
			case READY -> "!";
			case LOCKED -> "·";
			case GROUP -> "";
		};
	}

	// ---- Tree lines ----

	List<Node> roots() {
		return storyTab ? story : characters;
	}

	/** Turns the tree into the list of lines that are showing (children of closed lines are skipped). */
	private void layoutRows() {
		rows.clear();
		flatten(roots(), 0, new boolean[0]);
		selected = null;
		for (Row row : rows) {
			if (row.node.key.equals(selectedKey)) {
				selected = row.node;
			}
		}
		if (selected == null) {
			selectDefault();
		}
	}

	private void flatten(List<Node> nodes, int depth, boolean[] continues) {
		for (int i = 0; i < nodes.size(); i++) {
			Node node = nodes.get(i);
			boolean last = i == nodes.size() - 1;
			rows.add(new Row(node, depth, continues, last));
			if (!node.children.isEmpty() && expanded.contains(node.key)) {
				boolean[] next = Arrays.copyOf(continues, depth + 1);
				next[depth] = !last;
				flatten(node.children, depth + 1, next);
			}
		}
	}

	/** Picks the line you're on now: the current chapter, or the first quest line in progress. */
	private void selectDefault() {
		for (Row row : rows) {
			if (row.node.state == State.CURRENT || row.node.state == State.READY) {
				if (row.node.children.isEmpty() || row.node.key.startsWith("chapter:") || row.node.key.startsWith("character:")) {
					select(row.node);
					return;
				}
			}
		}
		if (!rows.isEmpty()) {
			select(rows.get(0).node);
		}
	}

	private void select(Node node) {
		if (node != selected) {
			detailScroll = 0;
		}
		selected = node;
		selectedKey = node.key;
	}

	private int indexOf(Node node) {
		for (int i = 0; i < rows.size(); i++) {
			if (rows.get(i).node == node) {
				return i;
			}
		}
		return -1;
	}

	private void clampScroll() {
		scroll = Math.max(0, Math.min(scroll, rows.size() - visibleRows));
	}


	/** The details of a line, wrapped to a width, in colour, with progress bars as their own rows. */
	List<DetailRow> detailRows(Font font, Node node, int width) {
		List<DetailRow> rows = new ArrayList<>();
		for (Line line : node.detail.get()) {
			if (line.isBar()) {
				rows.add(new DetailRow(null, line.have, line.need));
			} else if (line.text.isEmpty()) {
				rows.add(new DetailRow(FormattedCharSequence.EMPTY, 0, 0));
			} else {
				for (FormattedCharSequence text : font.split(Component.literal(line.text).withColor(line.color), width)) {
					rows.add(new DetailRow(text, 0, 0));
				}
			}
		}
		return rows;
	}

	/** The details as plain text lines, for tooltips: bars become a row of coloured | marks with a percentage. */
	List<FormattedCharSequence> detailLines(Font font, Node node, int width) {
		List<FormattedCharSequence> lines = new ArrayList<>();
		for (DetailRow row : detailRows(font, node, width)) {
			lines.add(row.text != null ? row.text : textBar(row.have, row.need));
		}
		return lines;
	}

	private static FormattedCharSequence textBar(int have, int need) {
		int marks = 20;
		int filled = need <= 0 ? 0 : Math.round(marks * (float) have / need);
		return Component.literal("|".repeat(filled)).withColor(have >= need ? BAR_DONE : BAR_FILL)
				.append(Component.literal("|".repeat(marks - filled)).withColor(BAR_BACK))
				.append(Component.literal(" " + percent(have, need) + "%").withColor(GREY))
				.getVisualOrderText();
	}

	static int percent(int have, int need) {
		return need <= 0 ? 0 : (int) (100L * have / need);
	}

	/** A progress bar: dark back, green fill (brighter when full). */
	static void bar(GuiGraphicsExtractor graphics, int x, int y, int w, int h, int have, int need) {
		graphics.fill(x, y, x + w, y + h, BAR_BACK);
		int filled = need <= 0 ? 0 : (int) ((long) (w - 2) * Math.min(have, need) / need);
		if (filled > 0) {
			graphics.fill(x + 1, y + 1, x + 1 + filled, y + h - 1, have >= need ? BAR_DONE : BAR_FILL);
		}
	}

	/** Brings the selected line into view, for when a tree opens. */
	void scrollToSelected(int rowsShown) {
		int index = indexOf(selected);
		if (index >= 0 && (index < scroll || index >= scroll + rowsShown)) {
			scroll = index - rowsShown / 2;
		}
		scroll = Math.max(0, Math.min(scroll, rows.size() - rowsShown));
	}

	// ---- Drawing the tree ----

	/** Draws the tree lines in a box. Remembers where, so clicks and scrolling work. */
	void drawTree(GuiGraphicsExtractor graphics, Font font, int x, int y, int w, int h, int mouseX, int mouseY) {
		treeX = x;
		treeY = y;
		treeWidth = w;
		visibleRows = Math.max(1, (h - 8) / ROW);
		clampScroll();
		box(graphics, x, y, w, h);

		int hoveredRow = rowAt(mouseX, mouseY);
		hovered = hoveredRow >= 0 ? rows.get(hoveredRow).node : null;
		for (int i = scroll; i < rows.size() && i < scroll + visibleRows; i++) {
			Row row = rows.get(i);
			int rowY = y + 4 + (i - scroll) * ROW;
			if (row.node == selected) {
				graphics.fill(x + 1, rowY - 1, x + w - 1, rowY + ROW - 1, 0x50FFFFFF);
			} else if (i == hoveredRow) {
				graphics.fill(x + 1, rowY - 1, x + w - 1, rowY + ROW - 1, 0x25FFFFFF);
			}

			// Connecting lines: one down from each parent that has more lines below, and a short one into this line.
			for (int d = 1; d < row.depth; d++) {
				if (row.continues[d]) {
					int lineX = x + 4 + (d - 1) * INDENT + 3;
					graphics.fill(lineX, rowY - 1, lineX + 1, rowY + ROW - 1, LINE);
				}
			}
			if (row.depth > 0) {
				int lineX = x + 4 + (row.depth - 1) * INDENT + 3;
				graphics.fill(lineX, rowY - 1, lineX + 1, row.last ? rowY + 5 : rowY + ROW - 1, LINE);
				graphics.fill(lineX, rowY + 4, lineX + 6, rowY + 5, LINE);
			}

			int textX = x + 4 + row.depth * INDENT;
			if (!row.node.children.isEmpty()) {
				graphics.text(font, expanded.contains(row.node.key) ? "-" : "+", textX, rowY, WHITE);
			}
			textX += 8;
			String symbol = symbol(row.node.state);
			if (!symbol.isEmpty()) {
				graphics.text(font, symbol, textX, rowY, colour(row.node.state));
				textX += 9;
			}
			int labelColour = row.node.state == State.GROUP ? GOLD : row.node.state == State.LOCKED ? GREY : WHITE;
			boolean miniBar = row.node.need > 0 && w >= 140;
			int textRight = x + w - 4 - (miniBar ? MINI_BAR + 4 : 0);
			if (miniBar) {
				bar(graphics, textRight + 2, rowY + 2, MINI_BAR, 5, row.node.have, row.node.need);
			}
			String shown = shorten(font, row.node.label, textRight - textX);
			if (i == hoveredRow) {
				hoveredCut = !shown.equals(row.node.label);
			}
			graphics.text(font, shown, textX, rowY, labelColour);
		}
		if (rows.size() > visibleRows) {
			// A small scroll bar.
			int barHeight = Math.max(10, h * visibleRows / rows.size());
			int barY = y + (h - barHeight) * scroll / Math.max(1, rows.size() - visibleRows);
			graphics.fill(x + w - 3, barY, x + w - 1, barY + barHeight, BORDER);
		}
	}

	static void box(GuiGraphicsExtractor graphics, int x, int y, int w, int h) {
		graphics.fill(x, y, x + w, y + h, 0xE0201A14);
		graphics.fill(x, y, x + w, y + 1, BORDER);
		graphics.fill(x, y + h - 1, x + w, y + h, BORDER);
		graphics.fill(x, y + 1, x + 1, y + h - 1, BORDER);
		graphics.fill(x + w - 1, y + 1, x + w, y + h - 1, BORDER);
	}

	static String shorten(Font font, String text, int maxWidth) {
		if (font.width(text) <= maxWidth) {
			return text;
		}
		while (text.length() > 1 && font.width(text + "...") > maxWidth) {
			text = text.substring(0, text.length() - 1);
		}
		return text + "...";
	}

	// ---- Mouse ----

	boolean isOverTree(double mouseX, double mouseY) {
		return mouseX >= treeX && mouseX < treeX + treeWidth && mouseY >= treeY && mouseY < treeY + 8 + visibleRows * ROW;
	}

	/** The tree line under the mouse, or -1. */
	private int rowAt(double mouseX, double mouseY) {
		if (!isOverTree(mouseX, mouseY) || mouseY < treeY + 3) {
			return -1;
		}
		int index = scroll + (int) ((mouseY - treeY - 3) / ROW);
		return index < rows.size() && index < scroll + visibleRows ? index : -1;
	}

	/**
	 * Selects the line under the mouse. Clicking a closed line opens it; clicking the selected line (or its +/-) opens or closes it.
	 * Returns false if the mouse isn't over a line.
	 */
	boolean click(double mouseX, double mouseY) {
		int index = rowAt(mouseX, mouseY);
		if (index < 0) {
			return false;
		}
		Node node = rows.get(index).node;
		boolean onToggle = mouseX < treeX + 4 + rows.get(index).depth * INDENT + 8;
		if (!node.children.isEmpty() && (node == selected || onToggle || !expanded.contains(node.key))) {
			if (!expanded.remove(node.key)) {
				expanded.add(node.key);
			}
		}
		select(node);
		layoutRows();
		clampScroll();
		return true;
	}

	void scroll(int lines) {
		scroll += lines;
		clampScroll();
	}
}
