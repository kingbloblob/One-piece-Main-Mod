package com.onepiecemod.news;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.bounty.NavyRaids;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.empire.BusterCall;
import com.onepiecemod.empire.EmpireData;
import com.onepiecemod.empire.Title;
import com.onepiecemod.power.DevilFruit;
import com.onepiecemod.power.DevilFruits;
import com.onepiecemod.power.ModAttachments;
import com.onepiecemod.story.StoryData;
import com.onepiecemod.story.StoryProgress;

/**
 * Watches what players do and writes it into tomorrow's paper. It only reads other features' saved data
 * (bounty, story, crew, title, Devil Fruit), so nothing else needs to call it.
 */
public class NewsWatcher {
	/** What the paper last knew about a player. crew = -1 means no crew. */
	public record Seen(long bounty, int chapter, int title, int crew, String fruit) {
		public static final Codec<Seen> CODEC = RecordCodecBuilder.create(instance -> instance.group(
				Codec.LONG.fieldOf("bounty").forGetter(Seen::bounty),
				Codec.INT.fieldOf("chapter").forGetter(Seen::chapter),
				Codec.INT.fieldOf("title").forGetter(Seen::title),
				Codec.INT.fieldOf("crew").forGetter(Seen::crew),
				Codec.STRING.fieldOf("fruit").forGetter(Seen::fruit)
		).apply(instance, Seen::new));
	}

	public static final AttachmentType<Seen> SEEN = AttachmentRegistry.create(
			OnePieceMod.id("news_seen"),
			builder -> builder.persistent(Seen.CODEC).copyOnDeath()
	);

	/** Bosses the paper already wrote about for this player (rematches don't make the news). */
	public static final AttachmentType<List<String>> BOSSES = AttachmentRegistry.create(
			OnePieceMod.id("news_bosses"),
			builder -> builder.persistent(Codec.STRING.listOf()).copyOnDeath()
	);

	/** Players fighting a Navy raid / Buster Call right now (to report how it ended). */
	private static final Set<UUID> IN_RAID = new HashSet<>();
	private static final Set<UUID> IN_BUSTER_CALL = new HashSet<>();

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 100 != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				check(server, player);
				NewsLog.updateWanted(player);
			}
		});

		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (!(entity.level() instanceof ServerLevel level) || !(entity instanceof CharacterEntity boss) || !boss.isBoss()) {
				return;
			}
			if (!(source.getEntity() instanceof ServerPlayer player)) {
				return;
			}
			String id = boss.getCharacterId();
			List<String> done = new ArrayList<>(player.getAttachedOrElse(BOSSES, List.of()));
			if (done.contains(id)) {
				return;
			}
			done.add(id);
			player.setAttached(BOSSES, done);
			String name = player.getName().getString();
			String bossName = boss.getData().name;
			NewsLog.report(level.getServer(), name.toUpperCase() + " DEFEATS " + shortName(bossName).toUpperCase() + "!",
					"Witnesses say " + name + " beat " + bossName + " in a fight that shook the whole island. "
							+ "The Marines are already printing a new poster.", true);
		});
	}

	private static void check(MinecraftServer server, ServerPlayer player) {
		String name = player.getName().getString();
		Seen now = snapshot(player);
		Seen seen = player.getAttached(SEEN);
		if (seen == null) {
			player.setAttached(SEEN, now);
			return;
		}
		long reportedBounty = seen.bounty();

		// Bounty: a new threat level, or a big jump.
		if (now.bounty() > seen.bounty()) {
			int oldLevel = Bounty.threatLevel(seen.bounty());
			int newLevel = Bounty.threatLevel(now.bounty());
			if (newLevel > oldLevel || now.bounty() >= seen.bounty() + Math.max(5_000_000L, seen.bounty() / 4)) {
				String head = seen.bounty() == 0 ? "NEW PIRATE ON THE WANTED LIST" : "BOUNTY RAISED: " + name.toUpperCase();
				NewsLog.report(server, head, "The World Government now offers " + Bounty.format(now.bounty())
						+ " for " + name + ", " + Bounty.levelName(newLevel).toLowerCase() + ". Wanted posters are going up across the seas.", false);
				reportedBounty = now.bounty();
			}
		} else {
			reportedBounty = now.bounty();
		}

		// Story chapters finished.
		if (now.chapter() > seen.chapter()) {
			List<StoryData.Chapter> chapters = StoryData.chapters();
			int done = seen.chapter();
			if (done >= 0 && done < chapters.size()) {
				String place = chapters.get(done).title;
				NewsLog.report(server, "ROOKIE MAKES WAVES: " + name.toUpperCase(),
						"Sailors say " + name + " was behind the uproar of \"" + place + "\". Nobody there will forget it soon.", false);
			}
		}

		// A new title, like Emperor of the Sea.
		if (now.title() > seen.title()) {
			Title title = Title.values()[Math.min(now.title(), Title.values().length - 1)];
			NewsLog.report(server, "A NEW " + title.displayName.toUpperCase() + "!",
					name + " has been named " + title.displayName + ". The Navy calls an emergency meeting at Marineford.", true);
		}

		// Crews.
		Crew crew = player.getAttached(CrewAttachments.CREW);
		if (seen.crew() < 0 && now.crew() >= 0 && crew != null) {
			NewsLog.report(server, "NEW PIRATE CREW SETS SAIL",
					"The " + crew.name() + " fly their Jolly Roger for the first time, with " + name + " as captain.", false);
		} else if (now.crew() > seen.crew() && seen.crew() >= 0 && crew != null) {
			NewsLog.report(server, crew.name().toUpperCase() + " GROW STRONGER",
					"Captain " + name + " has a new crewmate. The crew now counts " + now.crew() + " members besides the captain.", false);
		}

		// Devil Fruits.
		if (!now.fruit().isEmpty() && !now.fruit().equals(seen.fruit())) {
			DevilFruit fruit = DevilFruits.get(now.fruit());
			String fruitName = fruit != null ? fruit.name() : "a Devil Fruit";
			NewsLog.report(server, "DEVIL FRUIT EATEN",
					"Rumour says " + name + " ate the " + fruitName + ". Fishermen are told to keep an eye on the water: they can't swim now.", false);
		}

		// Navy raids and Buster Calls: report how they ended.
		boolean raiding = NavyRaids.isRaiding(player);
		if (raiding) {
			IN_RAID.add(player.getUUID());
		} else if (IN_RAID.remove(player.getUUID()) && player.isAlive()) {
			NewsLog.report(server, "NAVY RAID FAILS", "A Marine fleet sent after " + name + " sailed home with broken masts and empty cells.", false);
		}
		boolean busterCall = BusterCall.isActive(player);
		if (busterCall) {
			IN_BUSTER_CALL.add(player.getUUID());
		} else if (IN_BUSTER_CALL.remove(player.getUUID()) && player.isAlive()) {
			NewsLog.report(server, "BUSTER CALL BEATEN!", "Ten warships and five Vice Admirals could not stop " + name
					+ ". The Five Elders are said to be furious.", true);
		}

		player.setAttached(SEEN, new Seen(reportedBounty, now.chapter(), now.title(), now.crew(), now.fruit()));
	}

	private static Seen snapshot(ServerPlayer player) {
		Crew crew = player.getAttached(CrewAttachments.CREW);
		String fruit = player.getAttachedOrElse(ModAttachments.DEVIL_FRUIT, "");
		return new Seen(Bounty.get(player), StoryProgress.orStart(player).chapter(), EmpireData.title(player).ordinal(),
				crew != null ? crew.size() : -1, fruit == null ? "" : fruit);
	}

	/** "Sir Crocodile" stays, "Marshall D. Teach (Blackbeard)" becomes "Blackbeard". */
	private static String shortName(String name) {
		int open = name.indexOf('(');
		int close = name.indexOf(')');
		if (open >= 0 && close > open) {
			return name.substring(open + 1, close);
		}
		return name;
	}
}
