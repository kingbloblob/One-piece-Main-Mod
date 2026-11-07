package com.onepiecemod.dialogue.client;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.lwjgl.sdl.SDLScancode;

import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.client.input.KeyEvent;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.dialogue.Dialogue;
import com.onepiecemod.dialogue.DialogueFeature;

/**
 * The talk screen: a box at the bottom of the screen with the character standing on the left,
 * their name, their line (typed out letter by letter; click to show it all at once) and the choices.
 * Number keys 1-9 pick a choice too. The world stays visible behind it and the game doesn't pause.
 */
public class DialogueScreen extends Screen {
	private static final int MAX_PANEL_WIDTH = 460;
	private static final int PORTRAIT_WIDTH = 74;
	private static final int BUTTON_HEIGHT = 18;
	private static final int LINE = 10;
	/** Letters typed out per tick (20 ticks = 1 second). */
	private static final float LETTERS_PER_TICK = 2.5f;

	private static final Pattern ITEM_TOKEN = Pattern.compile("\\{item:([a-z0-9_.:/-]+)}");

	private DialogueFeature.Page page;
	private final List<Button> choiceButtons = new ArrayList<>();
	private List<FormattedCharSequence> textLines = List.of();
	private List<FormattedCharSequence> hintLines = List.of();
	private int panelX, panelY, panelWidth, panelHeight, contentX, contentWidth;
	private float age = 0;
	private boolean waiting = false; // A choice was sent and the answer isn't here yet.

	public DialogueScreen(DialogueFeature.Page page) {
		super(Component.literal(page.speaker()));
		this.page = page;
	}

	/** A new page from the server for the same conversation: swap it in without closing the screen. */
	public void show(DialogueFeature.Page next) {
		this.page = next;
		this.age = 0;
		this.waiting = false;
		init(width, height);
	}

	public int entityId() {
		return page.entityId();
	}

	@Override
	protected void init() {
		panelWidth = Math.min(MAX_PANEL_WIDTH, width - 16);
		panelX = (width - panelWidth) / 2;
		contentX = panelX + PORTRAIT_WIDTH + 8;
		contentWidth = panelWidth - PORTRAIT_WIDTH - 16;

		textLines = font.split(Component.literal(page.text()), contentWidth);
		hintLines = page.hint().isEmpty() ? List.of()
				: font.split(Component.literal(names(page.hint())).withStyle(ChatFormatting.ITALIC), contentWidth);

		int count = Math.max(1, page.choiceIds().size());
		int columns = count > 3 && contentWidth >= 240 ? 2 : 1;
		int rows = (count + columns - 1) / columns;
		int textHeight = 14 + textLines.size() * LINE + (hintLines.isEmpty() ? 0 : 3 + hintLines.size() * LINE) + 6;
		panelHeight = Math.max(92, 8 + textHeight + rows * (BUTTON_HEIGHT + 2) + 4);
		panelY = height - panelHeight - 8;

		clearWidgets();
		choiceButtons.clear();
		int columnWidth = (contentWidth - (columns - 1) * 4) / columns;
		int top = panelY + 8 + textHeight;
		if (page.choiceIds().isEmpty()) {
			// A goodbye: just a button to walk away.
			choiceButtons.add(addRenderableWidget(Button.builder(Component.literal("[Leave]"), b -> onClose())
					.pos(contentX, top).size(columnWidth, BUTTON_HEIGHT).build()));
			return;
		}
		for (int i = 0; i < page.choiceIds().size(); i++) {
			String id = page.choiceIds().get(i);
			Component label = Component.literal((i + 1) + ". " + page.choiceLabels().get(i));
			if (Dialogue.HAND_IN.equals(id)) {
				label = label.copy().withStyle(ChatFormatting.GOLD);
			} else if (Dialogue.ACCEPT.equals(id)) {
				label = label.copy().withStyle(ChatFormatting.GREEN);
			}
			int column = i % columns, row = i / columns;
			Button button = Button.builder(label, b -> pick(id))
					.pos(contentX + column * (columnWidth + 4), top + row * (BUTTON_HEIGHT + 2))
					.size(columnWidth, BUTTON_HEIGHT).build();
			choiceButtons.add(addRenderableWidget(button));
		}
	}

	/** Swaps "{item:minecraft:bread}" in a hint for the item's name, in the player's language. */
	private static String names(String hint) {
		Matcher matcher = ITEM_TOKEN.matcher(hint);
		StringBuilder out = new StringBuilder();
		while (matcher.find()) {
			Item item = BuiltInRegistries.ITEM.getValue(Identifier.parse(matcher.group(1)));
			matcher.appendReplacement(out, Matcher.quoteReplacement(new ItemStack(item).getHoverName().getString()));
		}
		matcher.appendTail(out);
		return out.toString();
	}

	private void pick(String id) {
		if (waiting) {
			return;
		}
		if (!fullyShown()) {
			age = 1000; // First click on a half-typed line just shows the rest.
		}
		waiting = true;
		ClientPlayNetworking.send(new DialogueFeature.Choose(page.entityId(), id));
	}

	private int lettersShown() {
		return (int) (age * LETTERS_PER_TICK);
	}

	private boolean fullyShown() {
		return lettersShown() >= page.text().length();
	}

	@Override
	public void tick() {
		age++;
		Entity entity = minecraft.level == null ? null : minecraft.level.getEntity(page.entityId());
		if (entity == null || !entity.isAlive() || minecraft.player == null || minecraft.player.distanceToSqr(entity) > 100) {
			onClose(); // They're gone, or you walked off.
		}
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	@Override
	public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
		if (super.mouseClicked(event, doubleClick)) {
			return true;
		}
		if (!fullyShown()) {
			age = 1000;
			return true;
		}
		return false;
	}

	@Override
	public boolean keyPressed(KeyEvent event) {
		int number = event.input() - SDLScancode.SDL_SCANCODE_1; // Keys report scancodes: 1 to 9 are in a row.
		if (number >= 0 && number < 9 && number < choiceButtons.size()) {
			choiceButtons.get(number).onPress(event);
			return true;
		}
		if ((event.isConfirmation() || event.input() == SDLScancode.SDL_SCANCODE_SPACE) && !fullyShown()) {
			age = 1000;
			return true;
		}
		return super.keyPressed(event);
	}

	/** No blur: a soft shadow at the bottom so the box stands out and the world stays visible. */
	@Override
	public void extractBackground(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		graphics.fillGradient(0, height / 2, width, height, 0x00000000, 0x90000000);
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		// The box: dark wood with a brass edge.
		graphics.fill(panelX, panelY, panelX + panelWidth, panelY + panelHeight, 0xE01A120C);
		graphics.outline(panelX, panelY, panelWidth, panelHeight, 0xFFC8A040);
		graphics.outline(panelX + 2, panelY + 2, panelWidth - 4, panelHeight - 4, 0x60C8A040);
		graphics.fill(panelX + 4, panelY + 4, panelX + PORTRAIT_WIDTH, panelY + panelHeight - 4, 0x60000000);

		// The character, looking at your mouse.
		Entity entity = minecraft.level == null ? null : minecraft.level.getEntity(page.entityId());
		if (entity instanceof LivingEntity living) {
			int top = panelY + 6, bottom = panelY + panelHeight - 4;
			int size = (int) ((bottom - top) * 0.8f / 1.95f);
			InventoryScreen.extractEntityInInventoryFollowsMouse(graphics, panelX + 4, top, panelX + PORTRAIT_WIDTH, bottom,
					size, 0.0625f, mouseX, mouseY, living);
		}

		super.extractRenderState(graphics, mouseX, mouseY, partialTick);

		// Name plate.
		int y = panelY + 8;
		graphics.text(font, Component.literal(page.speaker()).withStyle(ChatFormatting.BOLD), contentX, y, 0xFFFFD75E);
		y += 14;

		// Their line, typed out.
		int letters = (int) ((age + partialTick) * LETTERS_PER_TICK);
		int used = 0;
		String text = page.text();
		List<FormattedCharSequence> typed = letters >= text.length() ? textLines
				: font.split(Component.literal(text.substring(0, Math.max(0, letters))), contentWidth);
		for (FormattedCharSequence line : typed) {
			graphics.text(font, line, contentX, y + used, 0xFFF4EBDD);
			used += LINE;
		}
		y += textLines.size() * LINE;

		if (!hintLines.isEmpty() && letters >= text.length()) {
			y += 3;
			for (FormattedCharSequence line : hintLines) {
				graphics.text(font, line, contentX, y, 0xFF9A9A9A);
				y += LINE;
			}
		}
	}
}
