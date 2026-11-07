package com.onepiecemod.questlog.client;

import java.lang.reflect.Field;
import java.util.Map;

import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.BossHealthOverlay;
import net.minecraft.util.Mth;

import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElement;

import com.onepiecemod.character.CharacterData;
import com.onepiecemod.hud.HudPayload;
import com.onepiecemod.hud.client.HudClient;
import com.onepiecemod.questlog.QuestLogFeature;

/**
 * The compass bar at the top of the screen:
 * a strip with N / E / S / W that turns as you look around, the Log Pose needle as a red marker on it,
 * which sea you're in, how far the next island is, and the quest you track in the journal.
 *
 * It moves down under boss bars (Sea Kings, story bosses) so they never overlap, and hides with F1, F3
 * or while a screen is open. Settings: One Piece Settings > Screen, or config/onepiece-client.properties.
 */
public class NavigationOverlay implements HudElement {
	private static final int STRIP = 160;
	/** How many degrees of the compass the strip shows, left edge to right edge. */
	private static final float SPAN = 120f;
	private static final int ROW = 10;
	private static final int PAD = 3;

	private static final int BG_TOP = 0x9E1B2640;
	private static final int BG_BOTTOM = 0x9E0D1322;
	private static final int GOLD = 0xFFF2C14E;
	private static final int WHITE = 0xFFFFFFFF;
	private static final int GRAY = 0xFFA8B0C0;
	private static final int GREEN = 0xFF7EE081;
	private static final int NEEDLE = 0xFFFF4D4D;

	private static final String[] POINTS = {"N", "NE", "E", "SE", "S", "SW", "W", "NW"};

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, DeltaTracker deltaTracker) {
		Minecraft client = Minecraft.getInstance();
		QuestLogFeature.Nav nav = QuestLogClient.nav();
		if (nav == null || client.player == null || client.gui.screen() != null || client.getDebugOverlay().showDebugScreen()
				|| ClientConfig.is(ClientConfig.NAV_BAR, "off")
				|| ClientConfig.is(ClientConfig.NAV_BAR, "log_pose") && !nav.logPose()) {
			return;
		}
		Font font = client.font;
		float partial = deltaTracker.getGameTimeDeltaPartialTick(false);

		// Text lines under the strip.
		String sea = QuestLogText.sea(nav.sea());
		String needle = needleText(client, nav);
		String coords = ClientConfig.is(ClientConfig.COORDINATES, "on")
				? "X " + client.player.getBlockX() + "  Z " + client.player.getBlockZ() : "";
		String line1 = sea + (sea.isEmpty() || needle.isEmpty() ? "" : "  ·  ") + needle;
		String tracked = ClientConfig.is(ClientConfig.QUEST_TRACKER, "on") ? trackedText(nav) : "";
		boolean ready = nav.trackedReady();

		int width = STRIP;
		width = Math.max(width, font.width(line1) + PAD * 2);
		width = Math.max(width, font.width(coords) + PAD * 2);
		int maxWidth = Math.max(STRIP, graphics.guiWidth() / 2);
		String trackedShown = tracked.isEmpty() ? "" : shorten(font, (ready ? "✔ " : "◆ ") + tracked, maxWidth - PAD * 2);
		width = Math.min(maxWidth, Math.max(width, font.width(trackedShown) + PAD * 2));
		int lines = (line1.isEmpty() ? 0 : 1) + (coords.isEmpty() ? 0 : 1) + (trackedShown.isEmpty() ? 0 : 1);
		int height = 14 + lines * ROW + (lines > 0 ? PAD : 1);

		// Big GUI scales get a little smaller, then the "Compass bar size" setting (small by default).
		int guiScale = client.getWindow().getGuiScale();
		float scale = (guiScale > 3 ? 3f / guiScale : 1f) * ClientConfig.navigationScale();
		float x;
		float y = 2;
		String place = ClientConfig.get(ClientConfig.NAV_POSITION);
		if (place.equals("top_left")) {
			// Under the main HUD if that's in the top left too.
			x = 2;
			y = Math.max(2, com.onepiecemod.hud.client.HudOverlay.topBottomEdge() + 3);
		} else if (place.equals("top_right")) {
			x = graphics.guiWidth() - 2 - width * scale;
		} else {
			x = (graphics.guiWidth() - width * scale) / 2f;
			y = bossBarsBottom(client) + 2;
		}

		graphics.pose().pushMatrix();
		graphics.pose().translate(x, y);
		graphics.pose().scale(scale, scale);

		// A thin, see-through frame so the bar stays out of the way.
		graphics.fill(0, 0, width, height, 0x806B4E14);
		graphics.fillGradient(1, 1, width - 1, height - 1, BG_TOP, BG_BOTTOM);

		strip(graphics, font, client, nav, (width - STRIP) / 2, 2, partial);

		int textY = 15;
		if (!line1.isEmpty()) {
			int lx = (width - font.width(line1)) / 2;
			if (!sea.isEmpty()) {
				graphics.text(font, sea, lx, textY, QuestLogText.seaColour(nav.sea()), true);
				lx += font.width(sea);
				if (!needle.isEmpty()) {
					graphics.text(font, "  ·  ", lx, textY, GRAY, true);
					lx += font.width("  ·  ");
				}
			}
			if (!needle.isEmpty()) {
				graphics.text(font, needle, lx, textY, nav.hasTarget() ? WHITE : GRAY, true);
			}
			textY += ROW;
		}
		if (!coords.isEmpty()) {
			graphics.centeredText(font, coords, width / 2, textY, GRAY);
			textY += ROW;
		}
		if (!trackedShown.isEmpty()) {
			graphics.centeredText(font, trackedShown, width / 2, textY, ready ? GREEN : GOLD);
		}
		graphics.pose().popMatrix();
	}

	/** The turning compass strip, with the Log Pose needle as a red diamond (or an arrow at the edge when it's behind you). */
	private static void strip(GuiGraphicsExtractor graphics, Font font, Minecraft client, QuestLogFeature.Nav nav,
			int left, int top, float partial) {
		float heading = Mth.wrapDegrees(client.player.getViewYRot(partial) + 180f); // 0 = north, 90 = east
		float perDegree = STRIP / SPAN;
		int mid = left + STRIP / 2;
		graphics.fill(left, top + 10, left + STRIP, top + 11, 0x60FFFFFF);

		for (int degree = 0; degree < 360; degree += 15) {
			float offset = Mth.wrapDegrees(degree - heading);
			if (Math.abs(offset) > SPAN / 2 - 2) {
				continue;
			}
			int px = Math.round(mid + offset * perDegree);
			if (degree % 45 == 0) {
				String point = POINTS[degree / 45];
				int colour = degree == 0 ? NEEDLE : degree % 90 == 0 ? WHITE : GRAY;
				graphics.text(font, point, px - font.width(point) / 2, top + 1, colour, true);
			} else {
				graphics.fill(px, top + 7, px + 1, top + 10, 0x90FFFFFF);
			}
		}

		// Where you're facing.
		graphics.fill(mid, top + 9, mid + 1, top + 12, GOLD);

		if (nav.hasTarget()) {
			double dx = nav.targetX() + 0.5 - client.player.getX();
			double dz = nav.targetZ() + 0.5 - client.player.getZ();
			float bearing = (float) Math.toDegrees(Math.atan2(dx, -dz));
			float offset = Mth.wrapDegrees(bearing - heading);
			if (Math.abs(offset) <= SPAN / 2 - 3) {
				int px = Math.round(mid + offset * perDegree);
				diamond(graphics, px, top + 9);
			} else {
				// Behind you: an arrow at the edge shows which way to turn.
				String arrow = offset < 0 ? "◀" : "▶";
				int px = offset < 0 ? left + 1 : left + STRIP - 1 - font.width(arrow);
				graphics.text(font, arrow, px, top + 1, NEEDLE, true);
			}
		}
	}

	private static void diamond(GuiGraphicsExtractor graphics, int x, int y) {
		graphics.fill(x - 1, y - 3, x + 2, y + 4, 0xFF4A0E0E);
		graphics.fill(x - 2, y - 2, x + 3, y + 3, 0xFF4A0E0E);
		graphics.fill(x, y - 2, x + 1, y + 3, NEEDLE);
		graphics.fill(x - 1, y - 1, x + 2, y + 2, NEEDLE);
	}

	/** "Log Pose ➤ Alabasta, 820 m", "Recording island 12/45 s", or a hint. Empty without a Log Pose. */
	private static String needleText(Minecraft client, QuestLogFeature.Nav nav) {
		if (!nav.logPose()) {
			return "";
		}
		if (nav.sea().isEmpty()) {
			return "The needle spins";
		}
		if (nav.recording() > 0) {
			return "Recording island " + nav.recording() + "/" + nav.recordNeeded() + " s";
		}
		if (!nav.hasTarget()) {
			return "Stay " + nav.recordNeeded() + " s on an island to set it";
		}
		double dx = nav.targetX() - client.player.getX();
		double dz = nav.targetZ() - client.player.getZ();
		int distance = (int) Math.sqrt(dx * dx + dz * dz);
		return "➤ " + QuestLogText.island(nav.targetBiome()) + "  " + distance + " m";
	}

	/** The tracked quest in a few words: "Beat Buggy 2/5 (Luffy)", or "Hand in to Luffy" when done. */
	private static String trackedText(QuestLogFeature.Nav nav) {
		String key = nav.tracked();
		if (key.isEmpty()) {
			return "";
		}
		if (QuestLogText.isStory(key)) {
			HudPayload hud = HudClient.data();
			return hud == null || hud.goalText().isEmpty() ? "" : hud.goalText();
		}
		CharacterData.Quest quest = QuestLogFeature.quest(key);
		if (quest == null) {
			return "";
		}
		if (nav.trackedReady()) {
			return "Done! Hand it in to " + QuestLogText.giver(key);
		}
		String progress = QuestLogText.itemProgress(quest);
		return QuestLogText.summary(quest) + (progress != null ? " " + progress : "") + " (" + QuestLogText.giver(key) + ")";
	}

	private static String shorten(Font font, String text, int maxWidth) {
		if (font.width(text) <= maxWidth) {
			return text;
		}
		while (!text.isEmpty() && font.width(text + "...") > maxWidth) {
			text = text.substring(0, text.length() - 1);
		}
		return text + "...";
	}

	// ---- Boss bars: the bar moves down under them so they don't overlap ----

	private static Field eventsField;
	private static boolean eventsFieldMissing;

	/** The bottom of the boss bars at the top of the screen, or 0 when there are none. */
	private static int bossBarsBottom(Minecraft client) {
		if (eventsFieldMissing) {
			return 0;
		}
		try {
			BossHealthOverlay overlay = client.gui.hud.getBossOverlay();
			if (eventsField == null) {
				for (Field field : BossHealthOverlay.class.getDeclaredFields()) {
					if (Map.class.isAssignableFrom(field.getType())) {
						field.setAccessible(true);
						eventsField = field;
						break;
					}
				}
				if (eventsField == null) {
					eventsFieldMissing = true;
					return 0;
				}
			}
			int bars = ((Map<?, ?>) eventsField.get(overlay)).size();
			// Vanilla draws the first bar 12 pixels down and one every 19 pixels, at most a third of the screen.
			return bars == 0 ? 0 : Math.min(12 + bars * 19 - 7, client.getWindow().getGuiScaledHeight() / 3 + 10);
		} catch (ReflectiveOperationException | RuntimeException e) {
			eventsFieldMissing = true;
			return 0;
		}
	}
}
