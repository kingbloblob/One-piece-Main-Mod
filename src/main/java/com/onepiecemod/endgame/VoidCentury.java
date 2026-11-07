package com.onepiecemod.endgame;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.Locations;
import com.onepiecemod.story.StoryProgress;
import com.onepiecemod.story.StoryTracker;
import com.onepiecemod.worldevent.WorldNews;

/**
 * The Void Century quest line: thirteen pages of the true history. Ten are read from Poneglyphs all over the world
 * (you need an archaeologist in your crew, see PoneglyphBlock), two are written by the story (Oden's log when Wano
 * is free, Vegapunk's broadcast after Egghead) and one is taken from Imu's throne. The post-game story chapters ask for them.
 *
 * With every page read and Imu beaten, reading the Poneglyph at Laugh Tale plays the Dawn: the true ending, where the
 * Drums of Liberation sound across the sea. That finishes the "dawn" chapter and opens New Game+.
 *
 * Pages are kept for good (New Game+ too), so you only hunt them down once.
 */
public class VoidCentury {
	/**
	 * One page. place = the structure whose Poneglyph tells it. A page with no place is either written by finishing a
	 * story chapter (chapter = that chapter's id: Oden's log after Wano, Vegapunk's broadcast after Egghead) or, with
	 * no chapter either, taken from Imu.
	 */
	public record Page(String id, String place, String chapter, String title, String text) {
		Page(String id, String place, String title, String text) {
			this(id, place, null, title, text);
		}
	}

	public static final List<Page> PAGES = List.of(
			new Page("ohara", "ohara_library", "The Tree of Knowledge",
					"Ohara's scholars read the stones for generations. They learned that a Great Kingdom once stood for a hundred years, "
							+ "and that the World Government was founded by the ones who destroyed it. For knowing that, Ohara burned."),
			new Page("shandora", "shandora", "The Golden City",
					"Under Roger's carving the old text goes on: Shandora guarded this stone for the Great Kingdom, and kept its secret "
							+ "even after the Knock Up Stream threw the city into the sky."),
			new Page("pluton", "alubarna_palace", "Pluton",
					"A warship that can sink an island with one shot, built long ago and hidden away. The royal family of Alabasta "
							+ "swore to guard where it lies, and never to let it fall into the wrong hands."),
			new Page("poseidon", "ryugu_palace", "Joy Boy's Apology",
					"Joy Boy wrote to the mermaid princess of his time. He promised to bring her people up into the sunlight, and "
							+ "couldn't keep it. A princess who can speak to Sea Kings is a weapon too: Poseidon."),
			new Page("zou", "mokomo_dukedom", "The Elephant's Stone",
					"The minks have carried this red stone on Zunesha's back for eight hundred years. The elephant once served "
							+ "Joy Boy, and still walks the sea as punishment for a crime the stone won't name."),
			new Page("whole_cake", "whole_cake_chateau", "The Kingdom's Allies",
					"Big Mom treats this Road Poneglyph like a jewel, but the text doesn't care who owns it. It lists the peoples "
							+ "who stood with the Great Kingdom: giants, fishmen, minks, and the dancers of the moon."),
			new Page("wano", "onigashima", "The Stonemasons",
					"The Kozuki family carved the Poneglyphs from stone nothing can break, and only they could write the ancient "
							+ "script. They stood with the Great Kingdom. That is why Wano shut its borders to the world."),
			new Page("hachinosu", "hachinosu", "The Drum",
					"Pirates have held this island for decades. The stone speaks of a D who will come again when the dawn breaks, "
							+ "and of a drumbeat that will be heard across every sea."),
			// Added November 6 2026 with the Elbaph chapters: the giants' stone, and two pages the story itself writes,
			// so Wano and Egghead feed into the true history too.
			new Page("oden_log", null, "wano", "Oden's Log",
					"Kozuki Oden sailed with Roger to the very end. His log says they came too early: the one Joy Boy promised "
							+ "had not come yet. Wano must open its borders when the time is right, and be ready to fight beside them."),
			new Page("vegapunk_message", null, "egghead_incident", "Vegapunk's Broadcast",
					"Before Labophase fell, Vegapunk spoke to every Den Den Mushi in the world. The sea rose two hundred meters "
							+ "in the Void Century, raised by the ancient weapons. The Mother Flame can raise it again, and drown the islands."),
			new Page("elbaph", "elbaph_tree", "The Sun God's Island",
					"Under the Great Tree the giants keep their oldest stone. Their warriors fought beside Joy Boy, and their songs "
							+ "still tell of the Sun God Nika, the warrior of liberation who makes people laugh. The Holy Knights never forgot."),
			new Page("twenty_kings", "void_century_ruins", "The Twenty Kings",
					"Twenty kings joined forces and won the war. They became the World Nobles and moved up onto the Red Line. "
							+ "One of the twenty never came down from the throne."),
			new Page("empty_throne", null, "The Empty Throne",
					"Under Imu's throne lies a sealed record: the twenty kings' own story of the war, and the order to erase "
							+ "every word of it. Now you hold both sides of the history."));

	/** The ids of the pages a player has read. */
	public static final AttachmentType<List<String>> READ = AttachmentRegistry.create(
			OnePieceMod.id("void_history"),
			builder -> builder.persistent(Codec.STRING.listOf()).copyOnDeath()
	);

	public static final String DAWN_CHAPTER = "dawn";
	private static final String DAWN_EVENT = "event:dawn";

	private static final Map<UUID, Integer> SCENES = new HashMap<>();
	private static final int SCENE_END = 20 * 20;

	public static void initialize() {
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (entity instanceof CharacterEntity boss && boss.isBoss() && boss.getCharacterId().equals("imu")
					&& entity.level() instanceof ServerLevel level) {
				for (ServerPlayer player : level.players()) {
					if (player.distanceToSqr(boss) < 64 * 64) {
						learn(player, page("empty_throne"));
					}
				}
			}
		});
		ServerTickEvents.END_SERVER_TICK.register(VoidCentury::tickScenes);
		ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> catchUp(handler.player));
	}

	/** A story chapter was just finished: write the page it gives, if any. */
	public static void chapterDone(ServerPlayer player, String chapterId) {
		for (Page page : PAGES) {
			if (chapterId.equals(page.chapter()) && !read(player).contains(page.id())) {
				learn(player, page);
			}
		}
	}

	/** Saves from before a chapter gave its page: hand over the pages of chapters already finished, quietly. */
	public static void catchUp(ServerPlayer player) {
		StoryProgress story = StoryProgress.of(player);
		if (story == null) {
			return;
		}
		List<String> list = new ArrayList<>(read(player));
		boolean changed = false;
		for (Page page : PAGES) {
			if (page.chapter() != null && !list.contains(page.id()) && story.completed(page.chapter())) {
				list.add(page.id());
				changed = true;
			}
		}
		if (changed) {
			player.setAttached(READ, list);
		}
	}

	public static Page page(String id) {
		for (Page page : PAGES) {
			if (page.id().equals(id)) {
				return page;
			}
		}
		return null;
	}

	/** The page a structure's Poneglyph tells, or null. */
	public static Page pageAt(String structureId) {
		for (Page page : PAGES) {
			if (structureId.equals(page.place())) {
				return page;
			}
		}
		return null;
	}

	public static List<String> read(Player player) {
		return player.getAttachedOrElse(READ, List.of());
	}

	public static int pagesRead(Player player) {
		int count = 0;
		for (Page page : PAGES) {
			if (read(player).contains(page.id())) {
				count++;
			}
		}
		return count;
	}

	/** Shows a page. The first time, it is written into the player's history (and the story is told). */
	public static void learn(ServerPlayer player, Page page) {
		boolean known = read(player).contains(page.id());
		if (!known) {
			List<String> list = new ArrayList<>(read(player));
			list.add(page.id());
			player.setAttached(READ, list);
		}
		player.sendSystemMessage(Component.literal((known ? "" : "New page of the true history: ") + page.title())
				.withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
		player.sendSystemMessage(Component.literal(page.text()).withStyle(ChatFormatting.YELLOW, ChatFormatting.ITALIC));
		if (!known) {
			ServerLevel level = (ServerLevel) player.level();
			level.playSound(null, player.blockPosition(), SoundEvents.BOOK_PAGE_TURN, SoundSource.PLAYERS, 1.0f, 0.7f);
			level.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.0f, 0.6f);
			int count = pagesRead(player);
			player.sendSystemMessage(Component.literal("True history: " + count + "/" + PAGES.size() + " pages. Type /endgame history to read them again.")
					.withStyle(ChatFormatting.GRAY));
			StoryTracker.check(player);
		}
	}

	/** Lists every page: read ones in full, missing ones with a hint where to look. */
	public static void showHistory(ServerPlayer player) {
		player.sendSystemMessage(Component.literal("=== The True History (" + pagesRead(player) + "/" + PAGES.size() + ") ===")
				.withStyle(ChatFormatting.GOLD));
		for (Page page : PAGES) {
			if (read(player).contains(page.id())) {
				player.sendSystemMessage(Component.literal(page.title() + ": ").withStyle(ChatFormatting.GOLD)
						.append(Component.literal(page.text()).withStyle(ChatFormatting.YELLOW)));
			} else {
				String hint = page.place() != null ? "A Poneglyph at " + Locations.name(page.place()) + ". Bring an archaeologist."
						: page.chapter() != null ? "The story writes this one. Keep going: " + chapterTitle(page.chapter()) + "."
						: "Take it from whoever sits on the Empty Throne.";
				player.sendSystemMessage(Component.literal("??? ").withStyle(ChatFormatting.DARK_GRAY)
						.append(Component.literal(hint).withStyle(ChatFormatting.GRAY)));
			}
		}
	}

	private static String chapterTitle(String id) {
		int index = com.onepiecemod.story.StoryData.indexOf(id);
		com.onepiecemod.story.StoryData.Chapter chapter = index < 0 ? null : com.onepiecemod.story.StoryData.chapter(index);
		return chapter != null ? chapter.title : id;
	}

	// ---- The Dawn ----

	/**
	 * Someone (with an archaeologist) reads the Poneglyph at Laugh Tale. Returns false if nothing special happens,
	 * so the stone just shows its usual text.
	 */
	public static boolean readLaughTale(ServerPlayer player) {
		StoryProgress story = StoryProgress.of(player);
		if (story == null || !story.reached(DAWN_CHAPTER) || story.hasFlag(DAWN_EVENT) || SCENES.containsKey(player.getUUID())) {
			return false;
		}
		int missing = PAGES.size() - pagesRead(player);
		if (missing > 0) {
			player.sendSystemMessage(Component.literal("The last Poneglyph only makes sense with the whole story beside it. You are missing "
					+ missing + (missing == 1 ? " page" : " pages") + " of the true history (/endgame history).").withStyle(ChatFormatting.GRAY));
			return true;
		}
		startDawn(player);
		return true;
	}

	/** Starts the Dawn scene. Also used by /endgame dawn. */
	public static void startDawn(ServerPlayer player) {
		SCENES.put(player.getUUID(), 0);
	}

	private static void tickScenes(MinecraftServer server) {
		SCENES.entrySet().removeIf(entry -> {
			ServerPlayer player = server.getPlayerList().getPlayer(entry.getKey());
			if (player == null) {
				return true; // Leaving mid-scene: read the stone again to replay it.
			}
			int tick = entry.getValue();
			entry.setValue(tick + 1);
			dawnStep(server, player, tick);
			return tick >= SCENE_END;
		});
	}

	/** Don! Don! Dodon! The beat of the Drums of Liberation, as tick offsets. */
	private static final int[] DRUM = {0, 10, 18, 22};

	private static void dawnStep(MinecraftServer server, ServerPlayer player, int tick) {
		ServerLevel level = (ServerLevel) player.level();
		BlockPos at = player.blockPosition();
		if (tick >= 120 && tick < 320) {
			int beat = (tick - 120) % 30;
			for (int hit : DRUM) {
				if (beat == hit) {
					level.playSound(null, at, SoundEvents.NOTE_BLOCK_BASEDRUM.value(), SoundSource.AMBIENT, 2.0f, 0.5f + 0.1f * (tick - 120) / 60);
				}
			}
		}
		switch (tick) {
			case 0 -> {
				player.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal("The last Poneglyph").withStyle(ChatFormatting.GRAY)));
				player.connection.send(new ClientboundSetTitleTextPacket(Component.literal("Laugh Tale").withStyle(ChatFormatting.GOLD)));
				narrate(player, "Your archaeologist lays every page of the true history beside the last stone, and starts to read aloud.");
			}
			case 60 -> say(player, "Joy Boy", "To whoever reads this: I couldn't keep my promise. I'm sorry. But someone will come who can.");
			case 120 -> {
				say(player, "Joy Boy", "When that day comes, you'll hear it. The drums will sound again, and the whole world will dance.");
				level.playSound(null, at, SoundEvents.BEACON_ACTIVATE, SoundSource.AMBIENT, 1.5f, 0.5f);
			}
			case 200 -> {
				narrate(player, "Don! Don! Dodon! The Drums of Liberation roll out across the island, and out over the sea.");
				player.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.REGENERATION, 400, 2, false, false));
			}
			case 160 -> narrate(player, "On every Den Den Mushi in the world, Vegapunk's recording plays to its end. Under the Great Tree of Elbaph, the giants start to sing.");
			case 280 -> say(player, "Roger", "Wahahaha! That's the sound! Eight hundred years he waited for someone to hear that.");
			case SCENE_END -> finish(server, player);
			default -> {
			}
		}
		if (tick > 120 && tick % 4 == 0) {
			level.sendParticles(ParticleTypes.END_ROD, at.getX() + 0.5, at.getY() + 1.5, at.getZ() + 0.5, 6, 3.0, 2.0, 3.0, 0.05);
			level.sendParticles(ParticleTypes.CLOUD, at.getX() + 0.5, at.getY() + 0.2, at.getZ() + 0.5, 4, 4.0, 0.1, 4.0, 0.02);
		}
	}

	private static void finish(MinecraftServer server, ServerPlayer player) {
		StoryProgress.set(player, StoryProgress.orStart(player).withFlag(DAWN_EVENT));
		player.connection.send(new ClientboundSetSubtitleTextPacket(Component.literal("The world is free").withStyle(ChatFormatting.YELLOW)));
		player.connection.send(new ClientboundSetTitleTextPacket(Component.literal("THE DAWN").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD)));
		ServerLevel level = (ServerLevel) player.level();
		level.playSound(null, player.blockPosition(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 1.5f, 0.6f);
		Finale.fireworks(level, player.blockPosition(), 14, 0xfff4c2);
		WorldNews.report(server, "The Drums of Liberation were heard on every sea. " + player.getName().getString()
				+ " has told the world the true history!", ChatFormatting.YELLOW);
		narrate(player, "Somewhere far away, a Den Den Mushi laughs. The Void Century is over.");
		StoryTracker.check(player);
	}

	private static void say(ServerPlayer player, String who, String line) {
		player.sendSystemMessage(Component.literal(who + ": ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(line).withStyle(ChatFormatting.ITALIC, ChatFormatting.WHITE)));
	}

	private static void narrate(ServerPlayer player, String line) {
		player.sendSystemMessage(Component.literal(line).withStyle(ChatFormatting.ITALIC, ChatFormatting.GRAY));
	}
}
