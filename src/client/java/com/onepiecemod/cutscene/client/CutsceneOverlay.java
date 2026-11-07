package com.onepiecemod.cutscene.client;

import java.util.List;

import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;

import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElement;

import com.onepiecemod.cutscene.CutsceneFeature;

/**
 * Draws the cutscene that is playing: black cinema bars top and bottom, and
 *  - for a boss intro: the boss's name sliding in big, their title under it, and their line typed out in the bottom bar;
 *  - for a flashback: an old-photo sepia tint, the title, then each memory line typed out one after another.
 * Only text and flat rectangles, so it costs next to nothing. Hidden with F1 like the rest of the HUD.
 */
public class CutsceneOverlay implements HudElement {

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, DeltaTracker deltaTracker) {
		CutsceneClient.Playing playing = CutsceneClient.current();
		Minecraft client = Minecraft.getInstance();
		if (playing == null || playing.age < 0 || client.player == null) {
			CutsceneClient.resetFrameClock();
			return;
		}
		float partial = deltaTracker.getGameTimeDeltaPartialTick(false);
		float t = playing.age + partial;
		float bars = playing.bars(partial);
		int w = graphics.guiWidth();
		int h = graphics.guiHeight();
		Font font = client.font;
		CutsceneFeature.Play play = playing.play;

		CutsceneClient.turnCamera(client, playing);

		if (play.kind() == CutsceneFeature.FLASHBACK) {
			// Old photograph: warm brown wash and darker edges.
			int a = (int) (bars * 0x88);
			graphics.fill(0, 0, w, h, (a << 24) | 0x3A2810);
			int edge = (int) (bars * 0x90);
			graphics.fillGradient(0, 0, w, h / 4, (edge << 24) | 0x1A1208, 0x001A1208);
			graphics.fillGradient(0, h - h / 4, w, h, 0x001A1208, (edge << 24) | 0x1A1208);
		}

		// The cinema bars.
		int barH = Math.round(Math.max(24, h / 7f) * bars);
		graphics.fill(0, 0, w, barH, 0xFF000000);
		graphics.fill(0, h - barH, w, h, 0xFF000000);
		int accent = 0xFF000000 | play.color();
		if (barH > 2) {
			graphics.fill(0, barH, w, barH + 1, withAlpha(accent, bars * 0.8f));
			graphics.fill(0, h - barH - 1, w, h - barH, withAlpha(accent, bars * 0.8f));
		}

		float fadeOut = playing.ending ? Math.max(0f, 1f - (t - playing.endAge) / 6f) : 1f;
		if (play.kind() == CutsceneFeature.BOSS_INTRO) {
			bossIntro(graphics, font, play, t, w, h, barH, accent, fadeOut);
		} else {
			flashback(graphics, font, play, t, w, h, barH, accent, fadeOut);
		}

		// Skip hint, top right inside the bar (the bottom bar holds the spoken lines).
		if (barH > 14 && !playing.ending) {
			String hint = "[" + CutsceneClient.skipKey().getTranslatedKeyMessage().getString() + "] Skip";
			graphics.text(font, hint, w - font.width(hint) - 6, 6, withAlpha(0xFF8890A0, fadeOut), false);
		}
	}

	private static void bossIntro(GuiGraphicsExtractor graphics, Font font, CutsceneFeature.Play play, float t,
			int w, int h, int barH, int accent, float fade) {
		// The name slides in from the left over half a second, then drifts slowly.
		float slide = Math.min(1f, Math.max(0f, (t - 4) / 10f));
		slide = 1f - (1f - slide) * (1f - slide) * (1f - slide);
		float nameScale = w < 360 ? 2f : 3f;
		int nameWidth = Math.round(font.width(play.title()) * nameScale);
		float x = -nameWidth + (w * 0.08f + nameWidth) * slide + t * 0.15f;
		float y = h * 0.36f;

		// A streak of colour behind the name.
		float streak = Math.min(1f, Math.max(0f, (t - 2) / 8f));
		int streakEnd = Math.round(w * 0.75f * streak);
		int bandTop = Math.round(y - 4);
		int bandBottom = Math.round(y + 9 * nameScale + 16);
		graphics.fill(0, bandTop, streakEnd, bandBottom, withAlpha(0xFF000000, 0.45f * fade));
		graphics.fill(0, bandTop, streakEnd, bandTop + 1, withAlpha(accent, fade));
		graphics.fill(0, bandBottom - 1, Math.round(streakEnd * 0.8f), bandBottom, withAlpha(accent, fade * 0.7f));

		graphics.pose().pushMatrix();
		graphics.pose().translate(x, y);
		graphics.pose().scale(nameScale, nameScale);
		graphics.text(font, play.title(), 0, 0, withAlpha(0xFFFFFFFF, fade), true);
		graphics.pose().popMatrix();

		if (!play.subtitle().isEmpty()) {
			float subAlpha = Math.min(1f, Math.max(0f, (t - 12) / 8f)) * fade;
			if (subAlpha > 0.02f) {
				graphics.pose().pushMatrix();
				graphics.pose().translate(w * 0.08f + 2 + t * 0.1f, y + 9 * nameScale + 4);
				graphics.pose().scale(1.25f, 1.25f);
				graphics.text(font, play.subtitle(), 0, 0, withAlpha(accent, subAlpha), true);
				graphics.pose().popMatrix();
			}
		}

		if (!play.lines().isEmpty()) {
			spokenLine(graphics, font, play.lines().get(0), (t - 22) * 2f, w, h, barH, accent, fade);
		}
	}

	private static void flashback(GuiGraphicsExtractor graphics, Font font, CutsceneFeature.Play play, float t,
			int w, int h, int barH, int accent, float fade) {
		// "Flashback" and when it happened, in the top bar.
		if (barH > 14) {
			graphics.text(font, "— Flashback —", 8, Math.max(4, barH / 2 - 9), withAlpha(accent, fade), false);
			graphics.text(font, play.subtitle(), 8, Math.max(14, barH / 2 + 1), withAlpha(0xFFBFAF8F, fade), false);
		}

		// The title, big in the middle for the first couple of seconds.
		float titleAlpha = Math.min(1f, Math.max(0f, (t - 6) / 10f)) * Math.min(1f, Math.max(0f, (60 - t) / 12f)) * fade;
		if (titleAlpha > 0.02f) {
			float scale = w < 360 ? 1.5f : 2f;
			graphics.pose().pushMatrix();
			graphics.pose().translate(w / 2f, h * 0.42f);
			graphics.pose().scale(scale, scale);
			graphics.centeredText(font, play.title(), 0, 0, withAlpha(0xFFF4E6C8, titleAlpha));
			graphics.pose().popMatrix();
		}

		// Which line is being told now.
		float start = 50;
		List<String> lines = play.lines();
		for (int i = 0; i < lines.size(); i++) {
			float length = 50 + lines.get(i).length();
			if (t < start + length || i == lines.size() - 1) {
				if (t >= start) {
					float lineFade = Math.min(1f, (t - start) / 5f) * fade;
					spokenLine(graphics, font, lines.get(i), (t - start) * 1.6f, w, h, barH, accent, lineFade);
				}
				break;
			}
			start += length;
		}
	}

	/** One line in the bottom bar: "Speaker: text" gets the speaker's name in colour; plain text is narration. */
	private static void spokenLine(GuiGraphicsExtractor graphics, Font font, String line, float letters,
			int w, int h, int barH, int accent, float alpha) {
		if (letters <= 0 || alpha <= 0.02f) {
			return;
		}
		String speaker = "";
		String text = line;
		int colon = line.indexOf(": ");
		if (colon > 0 && colon <= 32) {
			speaker = line.substring(0, colon);
			text = line.substring(colon + 2);
		}
		String shown = text.substring(0, Math.min(text.length(), (int) letters));
		int maxWidth = Math.min(w - 40, 360);
		List<FormattedCharSequence> wrapped = font.split(speaker.isEmpty()
				? Component.literal(shown).withStyle(net.minecraft.ChatFormatting.ITALIC)
				: Component.literal(shown), maxWidth);
		int rows = wrapped.size() + (speaker.isEmpty() ? 0 : 1);
		int top = h - barH / 2 - rows * 10 / 2;
		top = Math.max(h - barH - rows * 10 - 4, top); // Long lines grow up out of the bar rather than off the screen.
		if (!speaker.isEmpty()) {
			graphics.centeredText(font, speaker, w / 2, top, withAlpha(accent, alpha));
			top += 10;
		}
		int color = speaker.isEmpty() ? 0xFFE8DCC0 : 0xFFFFFFFF;
		for (FormattedCharSequence row : wrapped) {
			graphics.text(font, row, (w - font.width(row)) / 2, top, withAlpha(color, alpha), true);
			top += 10;
		}
	}

	private static int withAlpha(int argb, float alpha) {
		int a = Math.round(((argb >>> 24) & 0xFF) * Math.max(0f, Math.min(1f, alpha)));
		return (Math.max(a, 1) << 24) | (argb & 0xFFFFFF);
	}
}
