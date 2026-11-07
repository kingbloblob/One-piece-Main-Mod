package com.onepiecemod.story;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.bounty.EventBosses;
import com.onepiecemod.bounty.NavyCalm;
import com.onepiecemod.character.CharacterData;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.character.Locations;
import com.onepiecemod.npc.HumanNpc;
import com.onepiecemod.npc.NpcFeature;

/**
 * The wave set pieces, next to the older ones in StoryEvents (Kizaru at Sabaody, the Marineford siege):
 * - Sabaody: the Human Auctioning House riot ("sabaody_arrival", "auction_house_riot").
 * - Marineford: break through to Ace's execution platform, Akainu joins the last wave ("paramount_war", "ace_rescue").
 * - Fish-Man Island: hold the Ryugu Palace against Hody's crew ("fishman_coup", "ryugu_coup").
 * - Dressrosa: the SMILE Factory ("smile_factory", "smile_factory_raid") and the Birdcage, Fujitora joins the last
 *   wave ("dressrosa", "birdcage").
 * - Whole Cake: crash the Tea Party, Big Mom joins the last wave ("tea_party", "tea_party").
 * - Onigashima: storm the island through 4 waves of Beast Pirates (chapter "wano", event "onigashima_raid").
 * - Egghead: hold Labophase against 4 waves of Marines, Pacifista, CP0 and Seraphim; Kizaru joins the last one
 *   (chapter "egghead_incident", event "egghead_escape").
 * - Elbaph: hold the Great Tree against the Holy Knights ("holy_knights", "holy_knights_raid"), then Saint Gunko and Shamrock come.
 * - Laugh Tale: Blackbeard followed your rubbings; hold the shore, he joins the last wave ("laugh_tale", "laugh_tale_race").
 * - Post-game: break through the gates of Pangaea Castle ("god_knights", "pangaea_siege"), then Shamrock on Hard.
 * - Story summons: a "boss" or "talk" goal with "summon": true brings that character to its place once every
 *   earlier goal of the chapter is done. Queen and Saturn aren't placed by any structure, and Vegapunk has moved
 *   to Egghead, so the story brings them. Hody Jones, Sabo, Marco and Sanji come the same way.
 *
 * A raid only starts once every goal listed before its event goal is done.
 * Like the Marineford siege: only in Survival or Adventure, dying or running more than 96 blocks away ends it,
 * and you can go back to try again.
 */
public final class StoryRaids {
	/** Every NPC a raid spawns has this tag. Ones that load after a restart are removed. */
	public static final String TAG = "onepiece_story_raid";
	private static final int WAVE_SECONDS = 60;
	private static final int LEAVE_DISTANCE = 96;
	private static final int SUMMON_COOLDOWN_SECONDS = 30;

	/** One raid: which chapter and place start it, and who comes in each wave (NPC kit ids, see npc_kits.json). */
	private record Def(String event, String chapter, String place, String start, String win, String fail,
			List<List<String>> waves, String lastBoss, String lastBossLine) {
	}

	private static final List<Def> RAIDS = List.of(
			new Def("onigashima_raid", "wano", "onigashima",
					"The Fire Festival is on, and the Beast Pirates have seen you! Fight your way through 4 waves.",
					"The Beast Pirates break and run. Kaido is waiting on the rooftop.",
					"The Beast Pirates threw you off Onigashima. Go back to try again.",
					List.of(List.of("gifter", "gifter", "gifter", "gifter"),
							List.of("gifter", "gifter", "gifter", "gifter", "gifter"),
							List.of("headliner", "headliner", "gifter", "gifter", "gifter"),
							List.of("headliner", "headliner", "headliner", "headliner", "gifter", "gifter")),
					null, null),
			new Def("egghead_escape", "egghead_incident", "egghead_lab",
					"The Navy's ring of warships opens fire on Egghead! Hold Labophase for 4 waves while Vegapunk records his message.",
					"Vegapunk's broadcast is out. The Navy's line breaks, and the warships pull back.",
					"Labophase fell. Go back to Egghead to try again.",
					List.of(List.of("marine", "marine", "marine", "pacifista"),
							List.of("pacifista", "pacifista", "cp0_agent", "cp0_agent"),
							List.of("seraphim", "seraphim", "pacifista", "pacifista"),
							List.of("seraphim", "seraphim", "seraphim", "cp0_agent", "cp0_agent")),
					"kizaru", "Ooh... I'm sorry, doctor. These are my orders."),
			// Added November 5 2026 with the Sabaody, Marineford, Fish-Man Island, Dressrosa and Whole Cake arcs.
			new Def("auction_house_riot", "sabaody_arrival", "auction_house",
					"You punched a World Noble in front of everyone! The Navy surrounds the Auctioning House: hold out for 4 waves.",
					"The Marines fall back to wait for an Admiral. You get out of the Auctioning House in the smoke.",
					"The Marines dragged you out of the Auctioning House. Go back to try again.",
					List.of(List.of("marine", "marine", "marine_rifle", "marine_rifle"),
							List.of("marine", "marine", "marine_officer", "marine_rifle", "marine_rifle"),
							List.of("marine_officer", "marine_officer", "elite_marine", "marine_rifle"),
							List.of("pacifista", "marine_officer", "marine_officer")),
					null, null),
			new Def("ace_rescue", "paramount_war", "marineford",
					"The siege wall goes up and the Pacifista march! Break through 4 waves to reach the execution platform.",
					"You're on the platform! Ace's cuffs come off, and the two of you jump into the fire together.",
					"The Navy pushed you back off the plaza. Go back to Marineford to try again.",
					List.of(List.of("elite_marine", "elite_marine", "marine_officer", "marine_rifle", "marine_rifle"),
							List.of("pacifista", "pacifista", "elite_marine", "elite_marine"),
							List.of("vice_admiral", "vice_admiral", "pacifista", "marine_officer"),
							List.of("vice_admiral", "vice_admiral", "vice_admiral", "pacifista", "pacifista")),
					"akainu", "Pirates are evil. And so is anyone with Roger's blood. I'll burn it out of this world."),
			new Def("ryugu_coup", "fishman_coup", "ryugu_palace",
					"The New Fish-Man Pirates storm the Ryugu Palace to take the throne! Hold them off for 4 waves.",
					"The New Fish-Man Pirates are scattered. But their captain is still coming for the king.",
					"Hody's crew took the palace. Go back to the Ryugu Palace to try again.",
					List.of(List.of("fishman", "fishman", "fishman", "fishman"),
							List.of("fishman", "fishman", "fishman", "fishman", "fishman"),
							List.of("fishman", "fishman", "fishman", "fishman", "pirate_captain"),
							List.of("fishman", "fishman", "fishman", "fishman", "fishman", "fishman")),
					null, null),
			new Def("smile_factory_raid", "smile_factory", "smile_factory",
					"Alarms! The Donquixote Family guards the SMILE Factory. Wreck it through 4 waves.",
					"The factory's machines go up in smoke. Somewhere above, the Sugar who made the toys faints.",
					"The Family threw you out of the factory. Go back to try again.",
					List.of(List.of("donquixote", "donquixote", "donquixote", "donquixote"),
							List.of("donquixote", "donquixote", "donquixote", "pirate_gunner", "pirate_gunner"),
							List.of("donquixote", "donquixote", "donquixote", "donquixote", "pirate_captain"),
							List.of("donquixote", "donquixote", "donquixote", "donquixote", "donquixote", "pirate_captain")),
					null, null),
			new Def("birdcage", "dressrosa", "dressrosa_palace",
					"The Birdcage is shrinking! Fight up to the palace through 4 waves before the strings cut the country apart.",
					"You're at the top of the palace. Fujitora puts his sword away: 'The dice say... you go on.' Doflamingo is waiting.",
					"The strings pushed you back down the hill. Go back to the palace to try again.",
					List.of(List.of("donquixote", "donquixote", "donquixote", "donquixote", "donquixote"),
							List.of("donquixote", "donquixote", "pirate_captain", "donquixote", "donquixote"),
							List.of("marine", "marine", "marine_officer", "donquixote", "donquixote"),
							List.of("donquixote", "donquixote", "pirate_captain", "pirate_captain", "marine_officer")),
					"fujitora", "I can't see who's right here. So let us roll the dice and see where they land."),
			new Def("tea_party", "tea_party", "whole_cake_chateau",
					"The wedding cake is cut, and so is the Tea Party! The Big Mom Pirates close in: survive 4 waves.",
					"The party is ruined, and you are out of the chateau before the Charlotte family can stop you.",
					"The Big Mom Pirates caught you at the Tea Party. Go back to Whole Cake Chateau to try again.",
					List.of(List.of("big_mom_pirate", "big_mom_pirate", "big_mom_pirate", "big_mom_pirate"),
							List.of("big_mom_pirate", "big_mom_pirate", "big_mom_pirate", "big_mom_pirate", "big_mom_pirate"),
							List.of("big_mom_pirate", "big_mom_pirate", "big_mom_pirate", "headliner", "pirate_captain"),
							List.of("big_mom_pirate", "big_mom_pirate", "big_mom_pirate", "big_mom_pirate", "headliner", "headliner")),
					"big_mom", "Mama mama mama! Who ruined my Tea Party?! LIFE or TREAT?!"),
			// Added November 6 2026 with the Elbaph chapters and the longer road to Laugh Tale.
			new Def("holy_knights_raid", "holy_knights", "elbaph_tree",
					"White sails off Elbaph! The Holy Knights of Mary Geoise have come for the giants: hold the Great Tree for 4 waves.",
					"The last Holy Knight falls back to the ships. Saint Gunko steps off the gangplank herself.",
					"The Holy Knights drove you from the Great Tree. Go back to Elbaph to try again.",
					List.of(List.of("holy_knight", "holy_knight", "cp0_agent", "cp0_agent"),
							List.of("holy_knight", "holy_knight", "holy_knight", "seraphim"),
							List.of("holy_knight", "holy_knight", "seraphim", "seraphim", "cp0_agent"),
							List.of("holy_knight", "holy_knight", "holy_knight", "holy_knight", "seraphim", "seraphim")),
					null, null),
			new Def("laugh_tale_race", "laugh_tale", "laugh_tale",
					"Black sails behind you! Blackbeard followed your rubbings to the last island. Hold the shore for 4 waves.",
					"The Blackbeard Pirates are thrown back into the sea. Teach is rowing away and laughing. The island is yours.",
					"Blackbeard's crew drove you off Laugh Tale. Go back to try again.",
					List.of(List.of("blackbeard_pirate", "blackbeard_pirate", "blackbeard_pirate", "blackbeard_pirate"),
							List.of("blackbeard_pirate", "blackbeard_pirate", "blackbeard_pirate", "pirate_gunner", "pirate_gunner"),
							List.of("blackbeard_pirate", "blackbeard_pirate", "blackbeard_pirate", "blackbeard_pirate", "pirate_captain"),
							List.of("blackbeard_pirate", "blackbeard_pirate", "blackbeard_pirate", "blackbeard_pirate", "blackbeard_pirate", "pirate_captain")),
					"blackbeard", "Zehahahaha! You did all the work for me! Thanks for the map, rookie. Now hand over the treasure!"),
			new Def("pangaea_siege", "god_knights", "pangaea_castle",
					"Bells ring all over the Holy Land. The Holy Knights close the gates of Pangaea Castle: break through 4 waves.",
					"The gate guards are down. The throne room is close, and the Holy Knights' commander is waiting in front of it.",
					"The Holy Knights threw you out of Pangaea Castle. Go back to try again.",
					List.of(List.of("holy_knight", "holy_knight", "holy_knight", "cp0_agent", "cp0_agent"),
							List.of("holy_knight", "holy_knight", "holy_knight", "seraphim", "seraphim"),
							List.of("holy_knight", "holy_knight", "holy_knight", "holy_knight", "seraphim", "cp0_agent"),
							List.of("holy_knight", "holy_knight", "holy_knight", "holy_knight", "seraphim", "seraphim", "seraphim")),
					null, null));

	private static final class Raid {
		final Def def;
		final BlockPos start;
		int wave = 0;
		int secondsLeft = 0;
		final List<UUID> enemies = new ArrayList<>();
		UUID boss;

		Raid(Def def, BlockPos start) {
			this.def = def;
			this.start = start;
		}
	}

	private static final Map<UUID, Raid> raids = new HashMap<>();
	/** Raid NPCs alive right now (in memory only, so a restart clears them). */
	private static final Set<UUID> LIVE = ConcurrentHashMap.newKeySet();
	/** When each player may next get a summon, by server tick. */
	private static final Map<UUID, Integer> summonReadyAt = new HashMap<>();

	private StoryRaids() {
	}

	public static void initialize() {
		NavyCalm.register(player -> raids.containsKey(player.getUUID()));

		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 20 != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				StoryProgress progress = StoryProgress.of(player);
				if (progress == null || !player.isAlive() || player.isSpectator()) {
					continue;
				}
				tick(player, progress, server.getTickCount());
			}
		});

		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (entity instanceof ServerPlayer player) {
				fail(player);
			}
		});

		// Talking to a summoned character counts for this chapter's "talk" goal (see StoryGoals).
		UseEntityCallback.EVENT.register((player, world, hand, entity, hit) -> {
			if (player instanceof ServerPlayer serverPlayer && entity instanceof CharacterEntity character && !character.isBoss()) {
				StoryProgress progress = StoryProgress.of(serverPlayer);
				StoryData.Chapter chapter = progress == null ? null : StoryData.chapter(progress.chapter());
				if (chapter != null) {
					for (StoryData.Goal goal : chapter.goals) {
						if ("talk".equals(goal.type) && goal.summon && character.getCharacterId().equals(goal.character)
								&& !progress.hasFlag(metFlag(chapter, goal.character))) {
							StoryEvents.setFlag(serverPlayer, metFlag(chapter, goal.character));
						}
					}
				}
			}
			return InteractionResult.PASS;
		});

		// Raiders left over from before a restart go away.
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity instanceof HumanNpc && entity.entityTags().contains(TAG) && !LIVE.contains(entity.getUUID())) {
				entity.discard();
			}
		});
	}

	private static void tick(ServerPlayer player, StoryProgress progress, int now) {
		ServerLevel level = (ServerLevel) player.level();
		StoryData.Chapter chapter = StoryData.chapter(progress.chapter());
		Raid raid = raids.get(player.getUUID());
		if (raid != null) {
			tickRaid(player, raid);
			return;
		}
		if (chapter == null) {
			return;
		}
		boolean canStart = !player.isCreative();
		for (Def def : RAIDS) {
			if (def.chapter.equals(chapter.id) && canStart && !progress.hasFlag("event:" + def.event)
					&& earlierGoalsDone(progress, chapter, def.event)
					&& StoryPlaces.isInside(level, player.blockPosition(), def.place)) {
				start(player, def);
				return;
			}
		}
		summon(player, progress, chapter, now);
	}

	/** The story flag for "talked to this summoned character during this chapter". */
	static String metFlag(StoryData.Chapter chapter, String character) {
		return "met:" + (chapter == null ? "" : chapter.id) + ":" + character;
	}

	/** True when every goal listed before the chapter's goal for this event is done (so the raid comes in story order). */
	private static boolean earlierGoalsDone(StoryProgress progress, StoryData.Chapter chapter, String event) {
		for (int i = 0; i < chapter.goals.size(); i++) {
			StoryData.Goal goal = chapter.goals.get(i);
			if ("event".equals(goal.type) && event.equals(goal.event)) {
				return true;
			}
			if (!progress.goalDone(i)) {
				return false;
			}
		}
		return true;
	}

	// ---- Summons ----

	/** The first goal of the chapter that isn't done yet: if it's a summon, bring that character. */
	private static void summon(ServerPlayer player, StoryProgress progress, StoryData.Chapter chapter, int now) {
		StoryData.Goal goal = null;
		for (int i = 0; i < chapter.goals.size(); i++) {
			if (!progress.goalDone(i)) {
				goal = chapter.goals.get(i);
				break;
			}
		}
		if (goal == null || !goal.summon || now < summonReadyAt.getOrDefault(player.getUUID(), 0)) {
			return;
		}
		boolean boss = "boss".equals(goal.type);
		String id = boss ? goal.boss : goal.character;
		CharacterData data = id == null ? null : CharacterData.get(id);
		if (data == null) {
			return;
		}
		String place = goal.place != null ? goal.place : Locations.home(id);
		ServerLevel level = (ServerLevel) player.level();
		if (place == null || !StoryPlaces.isInside(level, player.blockPosition(), place)) {
			return;
		}
		boolean here = !level.getEntitiesOfClass(CharacterEntity.class, player.getBoundingBox().inflate(LEAVE_DISTANCE),
				character -> id.equals(character.getCharacterId()) && character.isBoss() == boss).isEmpty();
		if (here) {
			return;
		}
		CharacterEntity entity = CharacterFeature.CHARACTER.create(level, EntitySpawnReason.EVENT);
		if (entity == null) {
			return;
		}
		summonReadyAt.put(player.getUUID(), now + SUMMON_COOLDOWN_SECONDS * 20);
		BlockPos spot = StoryEvents.spotNear(level, player, boss ? 9 : 4, boss ? 14 : 7);
		entity.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
		entity.setCharacter(id, boss);
		if (boss && goal.difficulty > 0) {
			entity.setDifficulty(goal.difficulty);
		}
		if (boss) {
			entity.setTarget(player);
		}
		EventBosses.markUntilUnloaded(entity);
		level.addFreshEntity(entity);
		if (data.greeting != null && !data.greeting.isEmpty()) {
			StoryEvents.say(player, data.name, data.greeting);
		}
		if (boss) {
			level.playSound(null, player.blockPosition(), SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 2.0f, 0.9f);
		} else {
			StoryEvents.event(player, data.name + " came to meet you. Right-click to talk.");
		}
	}

	// ---- Raids ----

	private static void start(ServerPlayer player, Def def) {
		Raid raid = new Raid(def, player.blockPosition());
		raids.put(player.getUUID(), raid);
		StoryEvents.event(player, def.start);
		nextWave(player, raid);
	}

	private static void tickRaid(ServerPlayer player, Raid raid) {
		ServerLevel level = (ServerLevel) player.level();
		if (player.blockPosition().distSqr(raid.start) > LEAVE_DISTANCE * LEAVE_DISTANCE) {
			fail(player);
			return;
		}
		raid.enemies.removeIf(id -> {
			Entity enemy = level.getEntity(id);
			boolean gone = enemy == null || !enemy.isAlive();
			if (gone) {
				LIVE.remove(id);
			}
			return gone;
		});
		raid.secondsLeft--;
		if (!raid.enemies.isEmpty() && raid.secondsLeft > 0) {
			if (raid.secondsLeft % 20 == 0) {
				player.sendOverlayMessage(Component.literal("Wave " + raid.wave + ": " + raid.enemies.size() + " left").withStyle(ChatFormatting.YELLOW));
			}
			return;
		}
		if (raid.wave >= raid.def.waves.size()) {
			finish(player, raid);
		} else {
			nextWave(player, raid);
		}
	}

	private static void nextWave(ServerPlayer player, Raid raid) {
		ServerLevel level = (ServerLevel) player.level();
		raid.wave++;
		raid.secondsLeft = WAVE_SECONDS;
		for (String kit : raid.def.waves.get(raid.wave - 1)) {
			BlockPos spot = StoryEvents.spotNear(level, player, 10, 18);
			HumanNpc npc = NpcFeature.spawn(level, kit, spot, player.getRandom().nextFloat() * 360f);
			if (npc == null) {
				continue;
			}
			npc.addTag(TAG);
			npc.setPersistenceRequired();
			npc.setTarget(player);
			LIVE.add(npc.getUUID());
			raid.enemies.add(npc.getUUID());
		}
		int total = raid.def.waves.size();
		StoryEvents.event(player, "Wave " + raid.wave + " of " + total + "!");
		level.playSound(null, player.blockPosition(), SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 2.0f, 1.2f);

		if (raid.wave == total && raid.def.lastBoss != null) {
			// The boss comes for the last wave, unless they're already standing nearby.
			String id = raid.def.lastBoss;
			boolean here = !level.getEntitiesOfClass(CharacterEntity.class, player.getBoundingBox().inflate(64),
					character -> character.isBoss() && id.equals(character.getCharacterId())).isEmpty();
			if (!here) {
				CharacterEntity boss = CharacterFeature.CHARACTER.create(level, EntitySpawnReason.EVENT);
				if (boss != null) {
					BlockPos spot = StoryEvents.spotNear(level, player, 14, 20);
					boss.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
					boss.setCharacter(id, true);
					boss.setTarget(player);
					EventBosses.mark(boss);
					level.addFreshEntity(boss);
					raid.boss = boss.getUUID();
				}
			}
			CharacterData data = CharacterData.get(id);
			StoryEvents.say(player, data != null ? data.name : id, raid.def.lastBossLine);
			raid.secondsLeft = WAVE_SECONDS + 30;
		}
	}

	private static void finish(ServerPlayer player, Raid raid) {
		raids.remove(player.getUUID());
		cleanUp(player, raid);
		StoryEvents.setFlag(player, "event:" + raid.def.event);
		StoryEvents.event(player, raid.def.win);
	}

	private static void fail(ServerPlayer player) {
		Raid raid = raids.remove(player.getUUID());
		if (raid == null) {
			return;
		}
		cleanUp(player, raid);
		StoryEvents.event(player, raid.def.fail);
	}

	/** Whoever is left of the raid leaves, and the event boss with them. */
	private static void cleanUp(ServerPlayer player, Raid raid) {
		ServerLevel level = (ServerLevel) player.level();
		for (UUID id : raid.enemies) {
			LIVE.remove(id);
			Entity enemy = level.getEntity(id);
			if (enemy != null) {
				enemy.discard();
			}
		}
		if (raid.boss != null) {
			EventBosses.forget(raid.boss);
			Entity boss = level.getEntity(raid.boss);
			if (boss != null && boss.isAlive()) {
				boss.discard();
			}
		}
	}
}
