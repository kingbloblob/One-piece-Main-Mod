package com.onepiecemod.dialogue;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;

import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.QuestHandler;
import com.onepiecemod.style.FightingStyle;
import com.onepiecemod.story.StoryData;
import com.onepiecemod.story.StoryProgress;

/**
 * Talking to a friendly character. Right-click one and a talk screen opens with their name, a line
 * in their own voice and some choices: take or hand in a job, trade, ask about the island, ask for advice
 * on the story, try to recruit them, or say goodbye.
 *
 * The server decides everything: the player's game only shows the page it gets and sends back which
 * choice was clicked (see DialogueFeature). The lines come from dialogue.json (DialogueData),
 * the jobs from characters.json (QuestHandler does the rewards, posters and Vivre Cards).
 */
public class Dialogue {
	/** How far away you can be and still talk, in blocks. */
	private static final double REACH = 8.0;

	// The choices. Their ids go to the player's game and come back when clicked.
	public static final String JOB = "job";
	public static final String ACCEPT = "accept";
	public static final String DECLINE = "decline";
	public static final String HAND_IN = "handin";
	public static final String TRADE = "trade";
	public static final String TRAIN = "train";
	public static final String ISLAND = "island";
	public static final String SELF = "self";
	public static final String ADVICE = "advice";
	public static final String RECRUIT = "recruit";
	public static final String BYE = "bye";
	public static final String CAREER = "career";
	public static final String CAREER_JOIN = "career_join";

	/** A choice on the screen: its id and the words on the button. */
	private record Choice(String id, String label) {
	}

	/** Called when a player right-clicks a friendly character. */
	public static void open(ServerPlayer player, CharacterEntity character) {
		character.getLookControl().setLookAt(player);
		DialogueData.Lines lines = lines(character);
		List<String> hello = lines.hello != null && !lines.hello.isEmpty() ? lines.hello : List.of(character.getData().greeting);
		String text = hello.get(player.getRandom().nextInt(hello.size()));
		send(player, character, text, hubHint(player, character.getData()), hub(player, character));
	}

	/** Called when the player clicks a choice on the talk screen. */
	public static void choose(ServerPlayer player, int entityId, String choice) {
		Entity entity = player.level().getEntity(entityId);
		if (!(entity instanceof CharacterEntity character) || character.isBoss() || !character.isAlive()
				|| player.distanceToSqr(character) > REACH * REACH) {
			return; // Walked away, or the character is gone: the screen just stays as it is.
		}
		CharacterData data = character.getData();
		DialogueData.Lines lines = lines(character);
		DialogueData.Lines defaults = DialogueData.get().defaults;
		int step = QuestHandler.currentStep(player, data);
		boolean hasJob = step < data.quests.size();

		switch (choice) {
			case JOB -> {
				if (!hasJob) {
					reply(player, character, DialogueData.pick(data.thanks, data.greeting), null);
				} else if (!QuestHandler.isStarted(player, data, step)) {
					// A new job: they explain it, and you choose whether to take it.
					CharacterData.Quest quest = data.quests.get(step);
					send(player, character, QuestHandler.label(data, step) + quest.start, offerHint(quest),
							List.of(new Choice(ACCEPT, "I'll do it."), new Choice(DECLINE, "Not right now.")));
				} else {
					CharacterData.Quest quest = data.quests.get(step);
					String waiting = DialogueData.pick(lines.waiting, defaults.waiting);
					reply(player, character, waiting + " " + quest.start, progressHint(player, quest));
				}
			}
			case ACCEPT -> {
				if (hasJob && !QuestHandler.isStarted(player, data, step)) {
					QuestHandler.beginStep(player, data, step);
					reply(player, character, DialogueData.pick(lines.accept, defaults.accept), takenHint(data.quests.get(step)));
				} else {
					open(player, character);
				}
			}
			case DECLINE -> reply(player, character, DialogueData.pick(lines.decline, defaults.decline), null);
			case HAND_IN -> {
				if (hasJob && QuestHandler.isStarted(player, data, step) && QuestHandler.isComplete(player, data.quests.get(step))) {
					CharacterData.Quest quest = data.quests.get(step);
					QuestHandler.handIn(player, data, step);
					String hint = rewardHint(quest);
					if (step + 1 >= data.quests.size()) {
						hint = (hint == null ? "" : hint + "  ") + "That was their last job.";
					}
					reply(player, character, quest.done, hint);
				} else {
					open(player, character);
				}
			}
			case TRADE -> {
				if (!CharacterData.TRADER.equals(data.role)) {
					return;
				}
				if (character.openShop(player)) {
					// The shop screen replaces the talk screen. Their line goes to chat so it isn't lost.
					QuestHandler.say(player, data, fill(player, DialogueData.pick(lines.trade, defaults.trade)));
				} else {
					reply(player, character, "I'm with another customer right now. Come back in a moment.", null);
				}
			}
			case TRAIN -> reply(player, character, DialogueData.pick(lines.train, defaults.train), trainHint(data));
			case ISLAND -> reply(player, character, DialogueData.pick(lines.island, defaults.island), null);
			case SELF -> reply(player, character, DialogueData.pick(lines.self, defaults.self), null);
			case RECRUIT -> reply(player, character, DialogueData.pick(lines.recruit, defaults.recruit),
					"Crewmates are hired at your Pirate Tavern's recruitment board (/crew blueprint).");
			case ADVICE -> advice(player, character, lines, defaults);
			case CAREER, CAREER_JOIN -> {
				// Joining the Marines or the Revolutionary Army (career package).
				com.onepiecemod.career.CareerTalk.Answer answer = CAREER.equals(choice)
						? com.onepiecemod.career.CareerTalk.talk(player, data.id)
						: com.onepiecemod.career.CareerTalk.join(player, data.id);
				if (answer.offerJoin()) {
					send(player, character, answer.text(), answer.hint(),
							List.of(new Choice(CAREER_JOIN, "Sign me up!"), new Choice(DECLINE, "Let me think about it.")));
				} else {
					reply(player, character, answer.text(), answer.hint());
				}
			}
			case BYE -> send(player, character, DialogueData.pick(lines.bye, defaults.bye), null, List.of());
			default -> {
			}
		}
	}

	/** Advice for the story chapter the player is on, plus what the chapter wants next. */
	private static void advice(ServerPlayer player, CharacterEntity character, DialogueData.Lines lines, DialogueData.Lines defaults) {
		StoryProgress progress = StoryProgress.orStart(player);
		StoryData.Chapter chapter = StoryData.chapter(progress.chapter());
		if (chapter == null) {
			reply(player, character, DialogueData.pick(lines.advice, defaults.advice), "Story: you found the One Piece. The sea is yours.");
			return;
		}
		String text = lines.chapters != null ? lines.chapters.get(chapter.id) : null;
		if (text == null) {
			text = DialogueData.pick(lines.advice, defaults.advice);
		}
		String next = null;
		for (int i = 0; i < chapter.goals.size(); i++) {
			if (!progress.goalDone(i)) {
				next = chapter.goals.get(i).text;
				break;
			}
		}
		reply(player, character, text, "Story: " + chapter.title + "." + (next != null ? " Next: " + next + "." : ""));
	}

	// ---- The main choices ----

	/** The choices you get when you start talking, and again after each answer. */
	private static List<Choice> hub(ServerPlayer player, CharacterEntity character) {
		CharacterData data = character.getData();
		List<Choice> choices = new ArrayList<>();
		int step = QuestHandler.currentStep(player, data);
		if (step < data.quests.size()) {
			if (!QuestHandler.isStarted(player, data, step)) {
				choices.add(new Choice(JOB, step == 0 ? "Got any work for me?" : "Any more work?"));
			} else if (QuestHandler.isComplete(player, data.quests.get(step))) {
				choices.add(new Choice(HAND_IN, "It's done!"));
			} else {
				choices.add(new Choice(JOB, "About that job..."));
			}
		}
		if (CharacterData.TRADER.equals(data.role)) {
			choices.add(new Choice(TRADE, "Let's trade."));
		}
		if (isTeacher(data.id)) {
			choices.add(new Choice(TRAIN, "Teach me to fight."));
		}
		choices.add(new Choice(ISLAND, "What's this place like?"));
		choices.add(new Choice(SELF, "Tell me about yourself."));
		choices.add(new Choice(ADVICE, "Any advice for the voyage?"));
		String career = com.onepiecemod.career.CareerTalk.choiceLabel(player, data.id);
		if (career != null) {
			choices.add(new Choice(CAREER, career));
		}
		choices.add(new Choice(RECRUIT, "Join my crew!"));
		choices.add(new Choice(BYE, "Goodbye."));
		return choices;
	}

	private static String hubHint(ServerPlayer player, CharacterData data) {
		int step = QuestHandler.currentStep(player, data);
		if (!data.quests.isEmpty() && step >= data.quests.size()) {
			return "You finished every job " + data.name + " had.";
		}
		return null;
	}

	/** Rayleigh teaches Haki; the fighting-style masters teach their style. */
	private static boolean isTeacher(String id) {
		return "rayleigh".equals(id) || FightingStyle.byMaster(id) != null;
	}

	// ---- The small grey hint under the line ----

	private static String offerHint(CharacterData.Quest quest) {
		String reward = rewardHint(quest);
		String gives = switch (quest.type) {
			case "defeat" -> "You'll get their Wanted Poster and a Sea Chart to their lair.";
			case "talk" -> "You'll get a Vivre Card that points the way.";
			case "deliver" -> "You'll get the package and a Vivre Card that points the way.";
			case "explore" -> "You'll get a Sea Chart to the place.";
			case "escort" -> "They'll follow you. You'll get a Sea Chart to where they're going.";
			default -> null;
		};
		if (gives == null) {
			return reward;
		}
		return reward == null ? gives : gives + "  " + reward;
	}

	private static String takenHint(CharacterData.Quest quest) {
		return switch (quest.type) {
			case "defeat" -> "Wanted Poster and Sea Chart added. Track the job with J.";
			case "talk" -> "Vivre Card added: right-click it to see the way. Track the job with J.";
			case "deliver" -> "Package and Vivre Card added. Track the job with J.";
			case "explore", "escort" -> "Sea Chart added: right-click it to mark the way. Track the job with J.";
			default -> "Track the job with J.";
		};
	}

	private static String progressHint(ServerPlayer player, CharacterData.Quest quest) {
		if ("fetch".equals(quest.type)) {
			Item item = CharacterData.item(quest.item);
			int have = Math.min(quest.count, player.getInventory().countItem(item));
			return "You have " + have + "/" + quest.count + " " + itemName(quest.item) + ".";
		}
		if ("talk".equals(quest.type)) {
			CharacterData target = CharacterData.get(quest.target);
			return "Find " + (target != null ? target.name : quest.target) + ". Their Vivre Card points the way.";
		}
		if ("deliver".equals(quest.type)) {
			CharacterData target = CharacterData.get(quest.target);
			return "Bring the package to " + (target != null ? target.name : quest.target) + ". Their Vivre Card points the way.";
		}
		if ("explore".equals(quest.type)) {
			return "Follow the Sea Chart to " + com.onepiecemod.character.Locations.name(quest.target) + ".";
		}
		if ("escort".equals(quest.type)) {
			return "Take them to " + com.onepiecemod.character.Locations.name(quest.place) + ". The Sea Chart shows the way.";
		}
		return "Their Sea Chart shows the way to the lair.";
	}

	private static String rewardHint(CharacterData.Quest quest) {
		List<String> parts = new ArrayList<>();
		if (quest.berries > 0) {
			parts.add(quest.berries + " Berries");
		}
		if (quest.xpReward() > 0) {
			parts.add(quest.xpReward() + " Pirate XP");
		}
		Item item = CharacterData.item(quest.rewardItem);
		if (item != Items.AIR) {
			parts.add((quest.rewardCount > 1 ? quest.rewardCount + " x " : "") + itemName(quest.rewardItem));
		}
		return parts.isEmpty() ? null : "Reward: " + String.join(", ", parts) + ".";
	}

	private static String trainHint(CharacterData data) {
		if ("rayleigh".equals(data.id)) {
			return "Sneak and right-click Rayleigh for a Haki lesson.";
		}
		FightingStyle style = FightingStyle.byMaster(data.id);
		return "Sneak and right-click " + data.name + " to learn " + style.title() + ".";
	}

	/**
	 * An item's name in hints. The server can't translate mod item names, so it sends "{item:minecraft:bread}"
	 * and the player's game swaps in the name in their own language (DialogueScreen.names).
	 */
	private static String itemName(String id) {
		return "{item:" + id + "}";
	}

	// ---- Sending ----

	/** An answer, with the main choices under it so you can keep talking. */
	private static void reply(ServerPlayer player, CharacterEntity character, String text, String hint) {
		send(player, character, text, hint, hub(player, character));
	}

	private static void send(ServerPlayer player, CharacterEntity character, String text, String hint, List<Choice> choices) {
		List<String> ids = new ArrayList<>();
		List<String> labels = new ArrayList<>();
		for (Choice choice : choices) {
			ids.add(choice.id());
			labels.add(choice.label());
		}
		ServerPlayNetworking.send(player, new DialogueFeature.Page(character.getId(), character.getData().name,
				fill(player, text), hint == null ? "" : hint, ids, labels));
	}

	/** Lines can say {player} for the player's name. */
	private static String fill(ServerPlayer player, String text) {
		return text == null ? "" : text.replace("{player}", player.getName().getString());
	}

	private static DialogueData.Lines lines(CharacterEntity character) {
		return DialogueData.of(character.getCharacterId());
	}
}
