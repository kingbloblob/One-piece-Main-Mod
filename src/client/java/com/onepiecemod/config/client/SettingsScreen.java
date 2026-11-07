package com.onepiecemod.config.client;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.InputWithModifiers;
import net.minecraft.network.chat.Component;

import com.onepiecemod.config.ModConfig;
import com.onepiecemod.config.ModConfig.Setting;
import com.onepiecemod.hud.client.HudClient;
import com.onepiecemod.hud.client.KeysScreen;
import com.onepiecemod.questlog.client.ClientConfig;

/**
 * "One Piece Settings": the settings file as buttons. One tab per category, one button per setting.
 * Click a button for the next value, Shift+click for the one before. Hover for what it does.
 * Done saves config/onepiece.properties.
 */
public class SettingsScreen extends Screen {
	private static final int BUTTON_WIDTH = 260;
	private static final int ROW = 22;

	private final Screen parent;
	private final Map<String, List<Setting>> pages = new LinkedHashMap<>();
	private static String page = "Difficulty";
	/** The extra tab for the on-screen HUD. Those choices live on this computer (config/onepiece-hud.txt), even on a server. */
	private static final String HUD_PAGE = "HUD";
	/** Another computer-only tab: the compass bar, quest tracker and panels (config/onepiece-client.properties). */
	private static final String SCREEN_PAGE = "Screen";
	/** The page with Simple mode, which also gets a row of preset buttons (Story, Simple, Standard, Challenge). */
	private static final String EASY_PAGE = "Easy Play";

	public SettingsScreen(Screen parent) {
		super(Component.literal("One Piece Settings"));
		this.parent = parent;
		for (Setting setting : ModConfig.settings()) {
			pages.computeIfAbsent(setting.category(), c -> new ArrayList<>()).add(setting);
		}
		// On a server only the HUD tab does anything, so start there.
		Minecraft client = Minecraft.getInstance();
		if (client.level != null && !client.isLocalServer()) {
			page = HUD_PAGE;
		}
		if (!pages.containsKey(page) && !isClientPage(page)) {
			page = pages.keySet().iterator().next();
		}
	}

	@Override
	protected void init() {
		clearWidgets();

		// Tabs, narrower when the window is small so they all fit.
		List<String> tabs = new ArrayList<>(pages.keySet());
		tabs.add(HUD_PAGE);
		tabs.add(SCREEN_PAGE);
		int tabWidth = Math.max(40, Math.min(78, (width - 8) / tabs.size() - 4));
		int tabsLeft = (width - tabs.size() * (tabWidth + 4) + 4) / 2;
		int i = 0;
		for (String name : tabs) {
			// Long names that don't fit (like "Devil Fruits" on a small window) show their last word.
			String shown = font.width(name) > tabWidth - 2 && name.contains(" ") ? name.substring(name.lastIndexOf(' ') + 1) : name;
			Button tab = addRenderableWidget(Button.builder(Component.literal(shown), b -> {
				page = name;
				init();
			}).pos(tabsLeft + i * (tabWidth + 4), 30).size(tabWidth, 20).build());
			tab.active = !name.equals(page);
			i++;
		}

		// One button per setting on this page.
		int left = (width - BUTTON_WIDTH) / 2;
		int top = 58;
		int rows;
		if (page.equals(HUD_PAGE)) {
			rows = hudButtons(left, top);
		} else if (page.equals(SCREEN_PAGE)) {
			rows = screenButtons(left, top);
		} else {
			int extra = 0;
			if (page.equals(EASY_PAGE)) {
				presetButtons(left, top);
				top += ROW + 6;
				extra = 1;
			}
			List<Setting> settings = pages.get(page);
			for (int row = 0; row < settings.size(); row++) {
				ValueButton button = addRenderableWidget(new ValueButton(settings.get(row), left, top + row * ROW,
						page.equals(EASY_PAGE) ? this::init : null)); // Re-check which preset matches.
				button.active = !ModConfig.locked();
			}
			rows = settings.size() + extra;
		}

		int bottom = Math.max(top + rows * ROW + 8, height - 28);
		int half = (BUTTON_WIDTH - 4) / 2;
		boolean hud = page.equals(HUD_PAGE);
		boolean screen = page.equals(SCREEN_PAGE);
		Button reset = addRenderableWidget(Button.builder(Component.literal(hud ? "Reset HUD to default" : screen ? "Reset this tab" : "Reset all to default"), b -> {
			if (hud) {
				HudClient.reset();
			} else if (screen) {
				ClientConfig.reset();
			} else {
				ModConfig.resetAll();
			}
			init();
		}).pos(left, bottom).size(half, 20).build());
		reset.active = hud || screen || !ModConfig.locked();
		addRenderableWidget(Button.builder(Component.literal("Done"), b -> onClose())
				.pos(left + half + 4, bottom).size(half, 20).build());
	}

	/** One button per preset. The preset that matches the current settings is greyed out. */
	private void presetButtons(int left, int top) {
		List<ModConfig.Preset> presets = ModConfig.presets();
		int gap = 4;
		int width = (BUTTON_WIDTH - gap * (presets.size() - 1)) / presets.size();
		ModConfig.Preset current = ModConfig.currentPreset();
		for (int i = 0; i < presets.size(); i++) {
			ModConfig.Preset preset = presets.get(i);
			Button button = addRenderableWidget(Button.builder(Component.literal(preset.label()), b -> {
				ModConfig.apply(preset);
				init();
			}).pos(left + i * (width + gap), top).size(width, 20)
					.tooltip(Tooltip.create(Component.literal(preset.help() + (preset == current ? "\n(Your current settings.)" : ""))))
					.build());
			button.active = preset != current && !ModConfig.locked();
		}
	}

	/** The HUD tab: what it shows (same as the H key), which corner, and how big. Changes show right away. */
	private int hudButtons(int left, int top) {
		addRenderableWidget(Button.builder(hudLabel("Show", HudClient.mode()), b -> {
			HudClient.cycleMode();
			b.setMessage(hudLabel("Show", HudClient.mode()));
		}).pos(left, top).size(BUTTON_WIDTH, 20)
				.tooltip(Tooltip.create(Component.literal("Full: everything plus key reminders. Small: no key reminders. Off: hidden. The H key does the same.")))
				.build());
		addRenderableWidget(Button.builder(hudLabel("Corner", HudClient.position()), b -> {
			HudClient.cyclePosition();
			b.setMessage(hudLabel("Corner", HudClient.position()));
		}).pos(left, top + ROW).size(BUTTON_WIDTH, 20)
				.tooltip(Tooltip.create(Component.literal("Bottom right sits beside the hotbar. Bottom left moves the chat up above the HUD. Top left suits modpacks with other HUDs.")))
				.build());
		addRenderableWidget(Button.builder(hudLabel("Size", HudClient.size()), b -> {
			HudClient.cycleSize();
			b.setMessage(hudLabel("Size", HudClient.size()));
		}).pos(left, top + ROW * 2).size(BUTTON_WIDTH, 20)
				.tooltip(Tooltip.create(Component.literal("On top of the automatic size for your GUI scale. It still never covers the hotbar.")))
				.build());
		addRenderableWidget(Button.builder(Component.literal("See all One Piece keys..."),
				b -> minecraft.gui.setScreen(new KeysScreen(this))).pos(left, top + ROW * 3 + 6).size(BUTTON_WIDTH, 20).build());
		return 4;
	}

	/** The Screen tab: one button per choice in config/onepiece-client.properties. Click = next, Shift+click = previous. */
	private int screenButtons(int left, int top) {
		int row = 0;
		for (ClientConfig.Option option : ClientConfig.options()) {
			addRenderableWidget(new ChoiceButton(option, left, top + row * ROW));
			row++;
		}
		return row;
	}

	private static boolean isClientPage(String name) {
		return name.equals(HUD_PAGE) || name.equals(SCREEN_PAGE);
	}

	/** Shows "Label: choice" for a screen setting. */
	private static class ChoiceButton extends Button.Plain {
		private final ClientConfig.Option option;

		ChoiceButton(ClientConfig.Option option, int x, int y) {
			super(x, y, BUTTON_WIDTH, 20, Component.empty(), b -> {}, DEFAULT_NARRATION);
			this.option = option;
			setTooltip(Tooltip.create(Component.literal(option.help() + "\nDefault: " + option.choices().get(0))));
			refresh();
		}

		@Override
		public void onPress(InputWithModifiers input) {
			ClientConfig.cycle(option.key(), input.hasShiftDown());
			refresh();
		}

		private void refresh() {
			String value = ClientConfig.get(option.key());
			String shown = value.replace('_', ' ');
			boolean changed = !value.equals(option.choices().get(0));
			setMessage(Component.literal(option.label() + ": " + Character.toUpperCase(shown.charAt(0)) + shown.substring(1))
					.withStyle(style -> changed ? style.withColor(0xFFD75E) : style));
		}
	}

	/** "Corner: Bottom left" from an enum value like BOTTOM_LEFT. */
	private static Component hudLabel(String what, Enum<?> value) {
		String name = value.name().replace('_', ' ').toLowerCase(java.util.Locale.ROOT);
		return Component.literal(what + ": " + Character.toUpperCase(name.charAt(0)) + name.substring(1));
	}

	@Override
	public void onClose() {
		ModConfig.save();
		minecraft.gui.setScreen(parent);
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
		graphics.centeredText(font, "One Piece Settings", width / 2, 8, 0xFFFFD75E);
		String note = isClientPage(page) ? "These are saved on this computer and work on any world or server."
				: ModConfig.locked() ? "Locked by your modpack (lock_settings in config/onepiece.properties)."
				: minecraft.isLocalServer() || minecraft.level == null
				? "Click for the next value, Shift+click for the one before. Hover to learn more."
				: "You're on a server: its own settings are used, not these.";
		graphics.centeredText(font, note, width / 2, 18, 0xFFAAAAAA);
	}

	/** Shows "Label: value". Click steps up through the setting's values, Shift+click steps down. */
	private static class ValueButton extends Button.Plain {
		private final Setting setting;
		private final Runnable afterChange;

		ValueButton(Setting setting, int x, int y, Runnable afterChange) {
			super(x, y, BUTTON_WIDTH, 20, Component.empty(), b -> {}, DEFAULT_NARRATION);
			this.setting = setting;
			this.afterChange = afterChange;
			String help = setting.comment().replace("\n", " ") + "\nDefault: " + setting.format(setting.defaultValue())
					+ (setting.needsRestart() ? "\nRestart the game for this to take effect." : "");
			setTooltip(Tooltip.create(Component.literal(help)));
			refresh();
		}

		@Override
		public void onPress(InputWithModifiers input) {
			ModConfig.set(setting.key(), step(ModConfig.get(setting.key()), input.hasShiftDown()));
			refresh();
			if (afterChange != null) {
				afterChange.run();
			}
		}

		/** The next (or previous) value in the setting's list, wrapping around at the ends. */
		private double step(double current, boolean back) {
			double[] steps = setting.steps();
			if (back) {
				for (int i = steps.length - 1; i >= 0; i--) {
					if (steps[i] < current - 1e-9) {
						return steps[i];
					}
				}
				return steps[steps.length - 1];
			}
			for (double step : steps) {
				if (step > current + 1e-9) {
					return step;
				}
			}
			return steps[0];
		}

		private void refresh() {
			double value = ModConfig.get(setting.key());
			String shown = setting.format(value);
			if (!setting.isChoice() && setting.key().endsWith("_chance")) {
				shown = value <= 0 ? "never" : value >= 1 ? "always" : "1 in " + String.format("%,d", Math.round(1 / value));
			} else if (!setting.isChoice()) {
				shown = (setting.key().endsWith("_share") || setting.key().endsWith("_loss") ? Math.round(value * 100) + "%" : "x" + shown);
				if (setting.key().equals("awakening_mastery")) {
					shown = setting.format(value);
				} else if (setting.key().equals("safe_until_bosses")) {
					long bosses = Math.round(value);
					shown = bosses == 0 ? "no one" : bosses + (bosses == 1 ? " boss" : " bosses");
				}
			}
			boolean changed = Math.abs(value - setting.defaultValue()) > 1e-9;
			setMessage(Component.literal(setting.label() + (setting.needsRestart() ? "*" : "") + ": " + shown)
					.withStyle(style -> changed ? style.withColor(0xFFD75E) : style));
		}
	}
}
