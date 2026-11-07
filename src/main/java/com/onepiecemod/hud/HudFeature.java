package com.onepiecemod.hud;

import net.minecraft.server.level.ServerPlayer;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.haki.HakiAttachments;
import com.onepiecemod.haki.HakiData;
import com.onepiecemod.haki.HakiPowers;
import com.onepiecemod.power.Awakening;
import com.onepiecemod.power.DevilFruit;
import com.onepiecemod.power.DevilFruits;
import com.onepiecemod.power.FruitAbilities;
import com.onepiecemod.power.ModAttachments;
import com.onepiecemod.stats.StatsAttachments;
import com.onepiecemod.stats.StatsData;
import com.onepiecemod.story.StoryData;
import com.onepiecemod.story.StoryGoals;
import com.onepiecemod.story.StoryProgress;
import com.onepiecemod.style.FightingStyle;
import com.onepiecemod.style.StyleAttachments;
import com.onepiecemod.style.StyleMoves;
import com.onepiecemod.style.StyleState;
import com.onepiecemod.style.Technique;

/**
 * The on-screen HUD. Twice a second the server gathers each player's Haki, Devil Fruit cooldowns,
 * bounty, Pirate Level, fighting style and story goal, and sends it to their game to draw (see HudClient).
 */
public class HudFeature {
	/** How often the HUD updates, in ticks (20 ticks = 1 second). */
	private static final int EVERY = 10;

	public static void initialize() {
		PayloadTypeRegistry.clientboundPlay().register(HudPayload.TYPE, HudPayload.CODEC);

		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % EVERY != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				// Players without the mod installed can't read it, so don't send it to them.
				if (ServerPlayNetworking.canSend(player, HudPayload.TYPE)) {
					ServerPlayNetworking.send(player, snapshot(player));
				}
			}
		});
	}

	private static HudPayload snapshot(ServerPlayer player) {
		HakiData haki = HakiAttachments.get(player);

		DevilFruit fruit = DevilFruits.get(player.getAttached(ModAttachments.DEVIL_FRUIT));
		String fruitName = fruit != null ? fruit.name() : "";
		String primary = fruit != null ? fruit.primary() : "";
		String secondary = fruit != null ? fruit.secondary() : "";

		StatsData stats = StatsAttachments.get(player);
		int level = stats.level();
		int needed = level >= StatsData.MAX_LEVEL ? 0 : StatsData.xpForNextLevel(level);

		FightingStyle style = StyleAttachments.active(player);
		Technique technique = StyleMoves.selected(player);
		int techniqueCooldown = technique == null ? 0
				: StyleState.of(player).secondsLeft(technique, player.level().getGameTime());

		String chapterTitle = "";
		String goalText = "";
		StoryProgress progress = StoryProgress.orStart(player);
		StoryData.Chapter chapter = StoryData.chapter(progress.chapter());
		if (chapter != null) {
			chapterTitle = chapter.title;
			for (int i = 0; i < chapter.goals.size(); i++) {
				if (!progress.goalDone(i)) {
					StoryData.Goal goal = chapter.goals.get(i);
					String count = StoryGoals.progressText(player, progress, goal);
					goalText = goal.text + (count != null ? " (" + count + ")" : "");
					break;
				}
			}
		}

		return new HudPayload(
				haki.observationLevel(), haki.armamentLevel(), haki.conquerorLevel(),
				haki.observationOn(), haki.armamentOn(), HakiPowers.conquerorSecondsLeft(player),
				fruit != null ? fruit.id() : "", fruitName, primary, secondary,
				fruit != null ? FruitAbilities.secondsLeft(player, false) : 0,
				fruit != null ? FruitAbilities.secondsLeft(player, true) : 0,
				Awakening.getMastery(player), Awakening.isAwakened(player), Awakening.isFormActive(player),
				Bounty.get(player), level, stats.xpIntoLevel(), needed,
				style != null ? style.title() : "", technique != null ? technique.title() : "", techniqueCooldown,
				chapterTitle, goalText);
	}
}
