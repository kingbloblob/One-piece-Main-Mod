package com.onepiecemod.hud.client;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;

import net.minecraft.client.DeltaTracker;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElement;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.hud.HudPayload;

/**
 * Draws the HUD as a flat bar in the bottom-right corner, right of the hotbar (bottom-left and top-left can be picked instead):
 * a straw-hat Jolly Roger, then Pirate Level, bounty, Haki, the next story goal, Devil Fruit and
 * fighting style moves with cooldown bars, and key reminders (full HUD only). Key names are read
 * from your real key binds, so the reminders stay right if you change them in Options > Controls.
 *
 * The bar never reaches the hotbar or the off-hand slot. When there isn't room for everything on
 * one line, the pieces wrap onto more lines instead of the text getting tiny.
 */
public class HudOverlay implements HudElement {
	private static final int ROW = 10;
	private static final int PAD = 3;
	private static final int GAP = 6;
	/** Space kept free beside the hotbar for the off-hand slot (it is 29 wide). */
	private static final int OFFHAND = 31;
	/** Space kept free right of the hotbar for the attack strength indicator, when the off-hand isn't there. */
	private static final int ATTACK_INDICATOR = 22;

	private static final int BG_TOP = 0xE81B2640;
	private static final int BG_BOTTOM = 0xE80D1322;
	private static final int TRIM = 0xFFD4A537;
	private static final int TRIM_DARK = 0xFF6B4E14;
	private static final int GOLD = 0xFFF2C14E;
	private static final int WHITE = 0xFFFFFFFF;
	private static final int GRAY = 0xFFA8B0C0;
	private static final int GREEN = 0xFF7EE081;
	private static final int RED = 0xFFFF6B6B;
	private static final int PURPLE = 0xFFE29BFF;
	private static final int AQUA = 0xFF6FE3F0;
	private static final int KEY = 0xFFC9A86A;

	// Pixel art. Each letter is a color from COLORS, '.' is see-through.
	private static final String[] JOLLY_ROGER = {
			"....YYYY....",
			"...YYYYYY...",
			"...RRRRRR...",
			"YYYYYYYYYYYY",
			"..WWWWWWWW..",
			".WWWWWWWWWW.",
			".WKKWWWWKKW.",
			".WKKWWWWKKW.",
			".WWWWKKWWWW.",
			"..WWWWWWWW..",
			"WW.W.WW.W.WW",
			"..WW....WW..",
			"....WWWW....",
			"..WW....WW..",
			"WW........WW",
	};
	private static final String[] EYE = {
			"..AAA..",
			".A...A.",
			"A..K..A",
			".A...A.",
			"..AAA..",
	};
	private static final String[] FIST = {
			".PPPP.",
			"PKKKKP",
			"PKKKKP",
			".KKKK.",
			"..KK..",
	};
	private static final String[] CROWN = {
			"G.G.G",
			"GGGGG",
			"GRGRG",
			"GGGGG",
	};
	private static final Map<Character, Integer> COLORS = Map.of(
			'Y', 0xFFF0C93A, 'R', 0xFFD63A3A, 'W', 0xFFF4F1E8, 'K', 0xFF15151C,
			'A', 0xFF6FE3F0, 'P', 0xFF9B6BFF, 'G', 0xFFF2C14E);

	/** The biggest cooldown seen for each move since it was last ready, so the bar knows how full to be. */
	private final Map<String, Integer> longestCooldown = new HashMap<>();
	private final Map<Item, ItemStack> icons = new HashMap<>();

	/** How far chat must move up this frame so it sits above the HUD (see HudClient). Chat normally ends 40 above the bottom. */
	private static int chatLift;
	/** Where the bottom of the HUD was last frame, in GUI pixels (0 when hidden). The First Voyage panel sits under it. */
	private static int bottomEdge;
	/** Seconds since the server last sent HUD data, so cooldowns tick down smoothly instead of every half second. */
	private float sinceData;

	public static int chatLift() {
		return chatLift;
	}

	/** The bottom edge of the HUD when it is at the top of the screen, else 0. */
	public static int topBottomEdge() {
		return bottomEdge;
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, DeltaTracker deltaTracker) {
		Minecraft client = Minecraft.getInstance();
		HudPayload hud = HudClient.data();
		// Screens like the inventory draw their own panels, so hide the HUD while one is open.
		if (hud == null || client.player == null || client.gui.screen() != null || HudClient.mode() == HudClient.Mode.OFF
				|| client.getDebugOverlay().showDebugScreen()) {
			chatLift = 0;
			bottomEdge = 0;
			return;
		}
		sinceData = HudClient.ticksSinceData(deltaTracker.getGameTimeDeltaPartialTick(false)) / 20f;
		boolean top = HudClient.position() == HudClient.Position.TOP_LEFT;
		boolean right = HudClient.position() == HudClient.Position.BOTTOM_RIGHT;
		boolean full = HudClient.mode() == HudClient.Mode.FULL;
		// The off-hand slot sits on the side opposite your main arm (left for most players).
		boolean offhandRight = client.player.getMainArm() == HumanoidArm.LEFT;
		int reserve = right ? (offhandRight ? OFFHAND : ATTACK_INDICATOR) : (offhandRight ? 4 : OFFHAND);

		// Big GUI scales get a little smaller, but text never drops below 3 screen pixels per font pixel.
		int guiScale = client.getWindow().getGuiScale();
		float scale = (guiScale > 3 ? 3f / guiScale : 1f) * HudClient.size().factor;
		int available = graphics.guiWidth() / 2 - 91 - reserve - 2;
		int maxWidth = (int) (available / scale);

		int emblem = 2 * ROW + PAD * 2 - 4; // The Jolly Roger is two lines tall.
		int side = emblem + 6; // Room for the flag, on the outer edge of the bar.
		int left = right ? PAD + 2 : side;
		int lineWidth = Math.max(60, maxWidth - side - PAD - 1);

		// Lay the pieces out left to right, starting a new line when the next one doesn't fit.
		Pen measure = new Pen(graphics, client.font, false);
		List<List<Consumer<Pen>>> lines = new ArrayList<>();
		List<Consumer<Pen>> line = new ArrayList<>();
		int used = 0;
		int contentWidth = 0;
		for (Consumer<Pen> piece : pieces(hud, full, lineWidth, client.font)) {
			measure.at(0, 0);
			piece.accept(measure);
			int w = measure.x;
			if (!line.isEmpty() && used + GAP + w > lineWidth) {
				lines.add(line);
				line = new ArrayList<>();
				used = 0;
			}
			used += (line.isEmpty() ? 0 : GAP) + w;
			contentWidth = Math.max(contentWidth, used);
			line.add(piece);
		}
		lines.add(line);

		int height = Math.max(lines.size(), 2) * ROW + PAD * 2;
		int width = side + contentWidth + PAD + 1;
		// A very long move name on a tiny window could still be too wide: then shrink, never overlap the hotbar.
		if (width * scale > available) {
			scale = Math.max(0.1f, available / (float) width);
		}

		// At the bottom the chat moves up out of the way; at the top the First Voyage panel moves down instead.
		chatLift = top || right ? 0 : Math.max(0, (int) Math.ceil(height * scale) + 5 - 40);
		bottomEdge = top ? 2 + (int) Math.ceil(height * scale) + 2 : 0;

		graphics.pose().pushMatrix();
		graphics.pose().translate(right ? graphics.guiWidth() - 2 - width * scale : 2,
				top ? 2 : graphics.guiHeight() - 2 - height * scale);
		graphics.pose().scale(scale, scale);

		// The frame: a dark sea-blue plank with gold trim, and a red flag behind the Jolly Roger.
		graphics.fill(-1, -1, width + 1, height + 1, TRIM_DARK);
		graphics.fill(0, 0, width, height, TRIM);
		graphics.fillGradient(1, 1, width - 1, height - 1, BG_TOP, BG_BOTTOM);
		int flag = right ? width - emblem - 4 : 1; // Left edge of the red flag.
		graphics.fill(flag, 1, flag + emblem + 2, height - 1, 0xC0601818);
		graphics.fill(right ? flag - 1 : flag + emblem + 2, 1, right ? flag : flag + emblem + 3, height - 1, TRIM);
		float art = emblem / (float) JOLLY_ROGER.length;
		pixelArt(graphics, JOLLY_ROGER, flag + 1 + (emblem - 12 * art) / 2, height - 2 - emblem, art, false);

		Pen pen = new Pen(graphics, client.font, true);
		int y = PAD + 1;
		for (List<Consumer<Pen>> row : lines) {
			pen.at(left, y);
			for (int i = 0; i < row.size(); i++) {
				if (i > 0) {
					pen.space(GAP);
				}
				row.get(i).accept(pen);
			}
			y += ROW;
		}
		graphics.pose().popMatrix();
	}

	/** Everything the HUD shows, as pieces that each stay on one line. */
	private List<Consumer<Pen>> pieces(HudPayload hud, boolean full, int lineWidth, Font font) {
		List<Consumer<Pen>> pieces = new ArrayList<>();

		// Pirate Level and XP bar.
		pieces.add(pen -> {
			pen.text("Lv " + hud.pirateLevel(), GOLD);
			pen.space(3);
			float xp = hud.levelXpNeeded() > 0 ? hud.levelXp() / (float) hud.levelXpNeeded() : 1f;
			pen.bar(16, 4, xp, GOLD, 2);
		});

		// Bounty, and the career rank for Marines and Revolutionaries (Marines have no bounty).
		String careerRank = com.onepiecemod.career.client.CareerClient.hudLabel();
		pieces.add(pen -> {
			if (!com.onepiecemod.career.client.CareerClient.hidesBounty()) {
				pen.icon(icon(CharacterFeature.BERRY));
				pen.text(shortBerries(hud.bounty()), 0xFFFFE27A);
			}
			if (careerRank != null) {
				if (!com.onepiecemod.career.client.CareerClient.hidesBounty()) {
					pen.space(3);
				}
				pen.text(careerRank, com.onepiecemod.career.client.CareerClient.color());
			}
		});

		// Haki, with its keys in the full HUD.
		pieces.add(pen -> {
			pen.haki(EYE, full ? key("key.onepiece.observation_haki") : null, hud.observationLevel(), hud.observationOn(), 0);
			pen.haki(FIST, full ? key("key.onepiece.armament_haki") : null, hud.armamentLevel(), hud.armamentOn(), 0);
			if (hud.conquerorLevel() > 0) {
				pen.haki(CROWN, full ? key("key.onepiece.conquerors_haki") : null, hud.conquerorLevel(), true, secondsLeft(hud.conquerorCooldown()));
			}
		});

		// Devil Fruit moves.
		if (!hud.fruitName().isEmpty()) {
			Item fruit = BuiltInRegistries.ITEM.getValue(OnePieceMod.id(hud.fruitId()));
			String power = key("key.onepiece.use_fruit_power");
			pieces.add(pen -> {
				pen.icon(icon(fruit));
				move(pen, "fruit1", power, hud.primaryMove(), hud.primaryCooldown());
			});
			pieces.add(pen -> move(pen, "fruit2", sneak() + "+" + power, hud.secondaryMove(), hud.secondaryCooldown()));
			if (hud.awakened()) {
				pieces.add(pen -> {
					pen.key(key("key.onepiece.awaken_fruit"));
					pen.text(hud.formActive() ? "Awakened!" : "Awaken", hud.formActive() ? GOLD : PURPLE);
				});
			}
		}

		// Fighting style move.
		if (!hud.styleName().isEmpty()) {
			String name = hud.techniqueName().isEmpty() ? hud.styleName() : hud.techniqueName();
			pieces.add(pen -> {
				pen.icon(icon(Items.IRON_SWORD));
				move(pen, "style", key("key.onepiece_styles.technique"), name, hud.techniqueCooldown());
			});
		}

		// Next story goal, cut short so it always fits on one line.
		if (!hud.goalText().isEmpty()) {
			int room = Math.min(240, lineWidth - 12);
			String goal = font.plainSubstrByWidth(hud.goalText(), room - font.width("..."));
			String text = goal.length() < hud.goalText().length() ? goal + "..." : hud.goalText();
			pieces.add(pen -> {
				pen.icon(icon(Items.MAP));
				pen.text(text, WHITE);
			});
		}

		// Reminders for the other keys.
		if (full) {
			if (!hud.styleName().isEmpty()) {
				pieces.add(pen -> hint(pen, sneak() + "+" + key("key.onepiece_styles.technique"), "Next move"));
			}
			// Kept together so they fill one line instead of spreading over several.
			pieces.add(pen -> {
				hint(pen, key("key.onepiece_stats.stat_tree"), "Stats");
				pen.space(4);
				hint(pen, key("key.onepiece.quest_tree"), "Quests");
				pen.space(4);
				hint(pen, key("key.onepiece.toggle_hud"), "HUD");
			});
		}
		return pieces;
	}

	private static void hint(Pen pen, String key, String what) {
		pen.key(key);
		pen.text(what, GRAY);
	}

	/** Whole seconds left on a cooldown the server sent, counted down since it arrived (shown like the server does: 0.2 s left is "1s"). */
	private int secondsLeft(int cooldown) {
		return cooldown <= 0 ? 0 : (int) Math.ceil(Math.max(0, cooldown - sinceData));
	}

	/** "[R] Gum-Gum Pistol" then a tick when ready, or the seconds left and a shrinking red bar. */
	private void move(Pen pen, String id, String key, String name, int cooldown) {
		pen.key(key);
		// Remember the longest cooldown per move name, so switching fruit or technique starts a fresh bar.
		id = id + ":" + name;
		float left = cooldown <= 0 ? 0 : Math.max(0, cooldown - sinceData);
		// Every move takes as much room as it needs while on cooldown, so the HUD doesn't jump when it's ready again.
		int end = pen.x + pen.font.width(name) + 3 + 16 + 2 + pen.font.width("88s");
		if (left <= 0) {
			if (pen.paint) {
				longestCooldown.remove(id);
			}
			pen.text(name, WHITE);
			pen.space(2);
			pen.text("✔", GREEN);
		} else {
			int longest = Math.max(cooldown, longestCooldown.getOrDefault(id, 0));
			if (pen.paint) {
				longestCooldown.put(id, longest);
			}
			pen.text(name, GRAY);
			pen.space(3);
			pen.bar(16, 3, left / longest, RED, 3);
			pen.space(2);
			pen.text((int) Math.ceil(left) + "s", RED);
		}
		pen.x = Math.max(pen.x, end);
	}

	/** Item stacks for the little pictures, made once (not while the game is still loading). */
	private ItemStack icon(Item item) {
		return icons.computeIfAbsent(item, ItemStack::new);
	}

	/** Draws pixel art with each pixel "size" wide. Dimmed art is drawn see-through. */
	private static void pixelArt(GuiGraphicsExtractor graphics, String[] art, float x, float y, float size, boolean dim) {
		graphics.pose().pushMatrix();
		graphics.pose().translate(x, y);
		graphics.pose().scale(size, size);
		for (int row = 0; row < art.length; row++) {
			for (int col = 0; col < art[row].length(); col++) {
				Integer color = COLORS.get(art[row].charAt(col));
				if (color != null) {
					graphics.fill(col, row, col + 1, row + 1, dim ? (color & 0x00FFFFFF) | 0x50000000 : color);
				}
			}
		}
		graphics.pose().popMatrix();
	}

	/** Writes things left to right. When "paint" is false it only measures. */
	private static class Pen {
		final GuiGraphicsExtractor graphics;
		final Font font;
		final boolean paint;
		int x;
		int y;

		Pen(GuiGraphicsExtractor graphics, Font font, boolean paint) {
			this.graphics = graphics;
			this.font = font;
			this.paint = paint;
		}

		void at(int x, int y) {
			this.x = x;
			this.y = y;
		}

		void space(int amount) {
			x += amount;
		}

		void text(String text, int color) {
			if (paint) {
				graphics.text(font, text, x, y, color, true);
			}
			x += font.width(text);
		}

		/** A key name in a little gold-edged box, like [R]. */
		void key(String key) {
			int w = font.width(key) + 4;
			if (paint) {
				graphics.fill(x, y - 1, x + w, y + 9, 0xFF3A2C10);
				graphics.outline(x, y - 1, w, 10, KEY);
				graphics.text(font, key, x + 2, y, 0xFFFFE9B8, false);
			}
			x += w + 3;
		}

		/** A small bar, "offset" pixels below the top of the text. */
		void bar(int width, int height, float filled, int color, int offset) {
			if (paint) {
				graphics.fill(x, y + offset, x + width, y + offset + height, 0xFF2A2F3A);
				graphics.fill(x, y + offset, x + Math.round(width * Math.max(0, Math.min(1, filled))), y + offset + height, color);
			}
			x += width;
		}

		/** A 16px item picture drawn at 10px. */
		void icon(ItemStack stack) {
			if (paint && !stack.isEmpty()) {
				graphics.pose().pushMatrix();
				graphics.pose().translate(x, y - 1.5f);
				graphics.pose().scale(0.625f, 0.625f);
				graphics.item(stack, 0, 0);
				graphics.pose().popMatrix();
			}
			x += 12;
		}

		/** A Haki icon and its level: bright when on, faded when off or locked, red while recovering. */
		void haki(String[] art, String key, int level, boolean on, int cooldown) {
			if (key != null) {
				key(key);
			}
			boolean lit = level > 0 && on && cooldown <= 0;
			if (paint) {
				pixelArt(graphics, art, x, y + (9 - art.length * 1.2f) / 2f, 1.2f, !lit);
			}
			x += Math.round(art[0].length() * 1.2f) + 2;
			if (level <= 0) {
				x -= 2; // Not learned yet: the faded icon says it, no number needed.
			} else if (cooldown > 0) {
				text(cooldown + "s", RED);
			} else {
				text(Integer.toString(level), lit ? AQUA : GRAY);
			}
			x += 3;
		}
	}

	/** The key currently bound to this key bind, like "R", or "-" if nothing is bound. */
	private static String key(String name) {
		for (KeyMapping mapping : Minecraft.getInstance().options.keyMappings) {
			if (mapping.getName().equals(name)) {
				return mapping.isUnbound() ? "-" : shorten(mapping.getTranslatedKeyMessage().getString());
			}
		}
		return "?";
	}

	/** The sneak key, usually "Shift". */
	private static String sneak() {
		KeyMapping shift = Minecraft.getInstance().options.keyShift;
		return shift.isUnbound() ? "-" : shorten(shift.getTranslatedKeyMessage().getString());
	}

	private static String shorten(String key) {
		key = key.replace("Left ", "").replace("Right ", "");
		return key.length() > 8 ? key.substring(0, 8) : key;
	}

	/** 30,000,000 becomes "30M", 1,500,000,000 becomes "1.5B". */
	private static String shortBerries(long amount) {
		if (amount >= 1_000_000_000L) {
			return trim(amount / 1_000_000_000.0) + "B";
		}
		if (amount >= 1_000_000L) {
			return trim(amount / 1_000_000.0) + "M";
		}
		if (amount >= 1_000L) {
			return trim(amount / 1_000.0) + "K";
		}
		return Long.toString(amount);
	}

	private static String trim(double value) {
		return value >= 100 || value == Math.floor(value) ? Long.toString((long) value) : String.format("%.1f", value);
	}
}
