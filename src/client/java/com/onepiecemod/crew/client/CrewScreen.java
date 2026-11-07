package com.onepiecemod.crew.client;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.components.PlayerFaceExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.crew.CrewMode;
import com.onepiecemod.crew.CrewPayloads;
import com.onepiecemod.crew.CrewPersonality;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewVariant;

/**
 * The crew window (U key, or right-click a Recruitment Board in a finished tavern).
 *
 * Three pages:
 * - No crew yet: type a name and set sail.
 * - Roster: one row per role. Hired crewmates show their face, level, health and XP, with Follow / Wait / Work
 *   buttons and an X to dismiss (click twice). Open roles show what they need and a Recruits button.
 * - Recruits: today's three candidates for a role, each with a Hire button.
 * Hover a row or a recruit for details. Everything is decided by the server; this only shows it.
 */
public class CrewScreen extends Screen {
	private static final int GOLD = 0xFFFFD75E;
	private static final int GREY = 0xFFAAAAAA;
	private static final int DARK = 0xFF777777;
	private static final int RED = 0xFFFF6B6B;
	private static final int BUTTONS_WIDTH = 3 * 36 + 18;

	private enum Page { NO_CREW, ROSTER, RECRUITS }

	private CrewPayloads.View view;
	private CrewPayloads.Recruits recruits;
	private Page page;
	private CrewRole confirmDismiss;
	private EditBox nameBox;
	private int refreshTimer;

	private int left, top, panelWidth, rowHeight, rowsTop;

	public CrewScreen(CrewPayloads.View view) {
		super(Component.literal("Crew"));
		this.view = view;
		this.page = view.hasCrew() ? Page.ROSTER : Page.NO_CREW;
	}

	/** New crew data from the server. */
	public void update(CrewPayloads.View newView) {
		this.view = newView;
		if (!view.hasCrew()) {
			page = Page.NO_CREW;
		} else if (page == Page.NO_CREW) {
			page = Page.ROSTER;
		} else if (page == Page.RECRUITS && recruits != null && view.notice().isEmpty()
				&& view.member(CrewRole.byId(recruits.role())) != null) {
			page = Page.ROSTER; // Hired! Back to the roster to see them.
		}
		rebuildWidgets();
	}

	/** The server sent a role's recruits: show them. */
	public void showRecruits(CrewPayloads.Recruits newRecruits) {
		this.recruits = newRecruits;
		this.page = Page.RECRUITS;
		rebuildWidgets();
	}

	private void send(String action, CrewRole role, int arg, int code, String text) {
		ClientPlayNetworking.send(new CrewPayloads.Action(action, role == null ? "" : role.id(), arg, code, text));
	}

	@Override
	public void tick() {
		// Ask for fresh health, XP and distances every 2 seconds while the window is open.
		if (++refreshTimer % 40 == 0 && page == Page.ROSTER) {
			send("open", null, 0, 0, "");
		}
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	@Override
	protected void init() {
		panelWidth = Math.min(380, width - 16);
		left = (width - panelWidth) / 2;
		rowHeight = Math.max(18, Math.min(22, (height - 96) / CrewRole.values().length));
		top = Math.max(6, (height - (rowHeight * CrewRole.values().length + 80)) / 2);
		rowsTop = top + 30;
		int bottomY = rowsTop + rowHeight * CrewRole.values().length + 18;

		switch (page) {
			case NO_CREW -> {
				String oldName = nameBox != null ? nameBox.getValue() : "";
				nameBox = new EditBox(font, width / 2 - 100, top + 60, 200, 20, Component.literal("Crew name"));
				nameBox.setMaxLength(32);
				nameBox.setHint(Component.literal("Straw Hat Pirates"));
				nameBox.setValue(oldName);
				addRenderableWidget(nameBox);
				setInitialFocus(nameBox);
				addRenderableWidget(Button.builder(Component.literal("Set sail!"),
						b -> send("create", null, 0, 0, nameBox.getValue())).pos(width / 2 - 50, top + 88).size(100, 20).build());
			}
			case ROSTER -> {
				CrewRole[] roles = CrewRole.values();
				for (int i = 0; i < roles.length; i++) {
					addRowButtons(roles[i], rowsTop + i * rowHeight);
				}
			}
			case RECRUITS -> addRecruitButtons();
		}

		if (page == Page.RECRUITS) {
			addRenderableWidget(Button.builder(Component.literal("Back"), b -> {
				page = Page.ROSTER;
				rebuildWidgets();
			}).pos(width / 2 - 84, Math.min(height - 24, bottomY)).size(80, 20).build());
			addRenderableWidget(Button.builder(Component.literal("Done"), b -> onClose())
					.pos(width / 2 + 4, Math.min(height - 24, bottomY)).size(80, 20).build());
		} else if (page == Page.ROSTER) {
			addRenderableWidget(Button.builder(Component.literal("Call crew"), b -> send("call", null, 0, 0, ""))
					.pos(width / 2 - 84, Math.min(height - 24, bottomY)).size(80, 20).build());
			addRenderableWidget(Button.builder(Component.literal("Done"), b -> onClose())
					.pos(width / 2 + 4, Math.min(height - 24, bottomY)).size(80, 20).build());
		} else {
			addRenderableWidget(Button.builder(Component.literal("Done"), b -> onClose())
					.pos(width / 2 - 40, Math.min(height - 24, bottomY)).size(80, 20).build());
		}
	}

	private void addRowButtons(CrewRole role, int y) {
		int buttonHeight = rowHeight - 4;
		int x = left + panelWidth - BUTTONS_WIDTH;
		CrewPayloads.Member member = view.member(role);
		if (member == null) {
			Button recruitsButton = Button.builder(Component.literal("Recruits"), b -> send("recruits", role, 0, 0, ""))
					.pos(x + BUTTONS_WIDTH - 72, y + 2).size(72, buttonHeight).build();
			recruitsButton.active = role.minCrew() <= view.members().size();
			addRenderableWidget(recruitsButton);
			return;
		}
		CrewMode[] modes = CrewMode.values();
		String[] labels = {"Follow", "Wait", "Work"};
		for (int m = 0; m < modes.length; m++) {
			int modeIndex = m;
			Button modeButton = Button.builder(Component.literal(labels[m]), b -> send("mode", role, modeIndex, 0, ""))
					.pos(x + m * 36, y + 2).size(34, buttonHeight).build();
			modeButton.active = member.nearby() && member.mode() != m; // The current mode shows greyed out.
			addRenderableWidget(modeButton);
		}
		boolean confirming = confirmDismiss == role;
		addRenderableWidget(Button.builder(Component.literal(confirming ? "?" : "x"), b -> {
			if (confirmDismiss == role) {
				confirmDismiss = null;
				send("dismiss", role, 0, 0, "");
			} else {
				confirmDismiss = role;
				rebuildWidgets();
			}
		}).pos(x + 3 * 36, y + 2).size(16, buttonHeight).build());
	}

	private void addRecruitButtons() {
		if (recruits == null) {
			return;
		}
		CrewRole role = CrewRole.byId(recruits.role());
		int cardWidth = (panelWidth - 8) / 3;
		int buttonY = rowsTop + 140;
		for (int i = 0; i < recruits.recruits().size(); i++) {
			int choice = i;
			CrewPayloads.Recruit recruit = recruits.recruits().get(i);
			Button hire = Button.builder(Component.literal("Hire (" + recruit.price() + " Berries)"),
							b -> send("hire", role, choice, recruits.listCode(), ""))
					.pos(left + i * (cardWidth + 4) + 4, buttonY).size(cardWidth - 8, 20).build();
			hire.active = recruits.problem().isEmpty();
			addRenderableWidget(hire);
		}
	}

	// ---------- Drawing ----------

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		int bottom = rowsTop + rowHeight * CrewRole.values().length + 14;
		graphics.fill(left - 6, top - 6, left + panelWidth + 6, bottom, 0xC0000000);
		graphics.fill(left - 6, top - 6, left + panelWidth + 6, top - 4, GOLD);

		switch (page) {
			case NO_CREW -> drawNoCrew(graphics);
			case ROSTER -> drawRoster(graphics, mouseX, mouseY);
			case RECRUITS -> drawRecruits(graphics, mouseX, mouseY);
		}

		String notice = confirmDismiss != null && page == Page.ROSTER
				? "Click ? to dismiss your " + confirmDismiss.title() + ". Their bag drops where they stand."
				: view.notice();
		if (!notice.isEmpty() && page != Page.RECRUITS) {
			wrapped(graphics, notice, left, bottom - 12, panelWidth, RED);
		}
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);
	}

	private void drawNoCrew(GuiGraphicsExtractor graphics) {
		centered(graphics, "Start a Pirate Crew", top + 4, GOLD);
		centered(graphics, "Name your crew. You'll be its captain.", top + 20, 0xFFDDDDDD);
		centered(graphics, "Then build a Pirate Tavern to hire crewmates.", top + 32, GREY);
		centered(graphics, "First hire costs " + view.nextPrice() + " Berries. You have " + view.berries() + ".", top + 116, GREY);
	}

	private void drawRoster(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
		graphics.text(font, view.crewName(), left, top, GOLD, true);
		String summary = view.members().size() + "/9 crew   Next hire: " + view.nextPrice() + " Berries   You have: " + view.berries();
		graphics.text(font, summary, left, top + 12, GREY, false);
		String hint = "Right-click a crewmate to change mode, sneak + right-click for their bag.";
		graphics.text(font, font.plainSubstrByWidth(hint, panelWidth), left, top + 21, DARK, false);

		CrewRole[] roles = CrewRole.values();
		for (int i = 0; i < roles.length; i++) {
			int y = rowsTop + i * rowHeight;
			boolean hover = mouseX >= left && mouseX < left + panelWidth - BUTTONS_WIDTH && mouseY >= y && mouseY < y + rowHeight;
			if (hover) {
				graphics.fill(left - 2, y, left + panelWidth - BUTTONS_WIDTH - 2, y + rowHeight - 1, 0x30FFFFFF);
			}
			CrewPayloads.Member member = view.member(roles[i]);
			if (member != null) {
				drawMember(graphics, roles[i], member, y);
				if (hover) {
					tooltip(graphics, memberTooltip(roles[i], member), mouseX, mouseY);
				}
			} else {
				drawOpenRole(graphics, roles[i], y);
				if (hover) {
					tooltip(graphics, openRoleTooltip(roles[i]), mouseX, mouseY);
				}
			}
		}
	}

	private void drawMember(GuiGraphicsExtractor graphics, CrewRole role, CrewPayloads.Member member, int y) {
		face(graphics, role, member.variant(), left, y + (rowHeight - 16) / 2, 16, true);
		int textLeft = left + 20;
		int barsLeft = left + panelWidth - BUTTONS_WIDTH - 74;
		graphics.text(font, font.plainSubstrByWidth(member.name(), barsLeft - textLeft - 4), textLeft, y + 1, 0xFFFFFFFF, true);
		if (!member.nearby()) {
			graphics.text(font, "Far away. Right-click them to give orders.", textLeft, y + 10, DARK, false);
			return;
		}
		CrewPersonality personality = CrewPersonality.byName(member.personality());
		String sub = member.where().equals("Knocked out") ? "Lv " + member.level() + "  Knocked out!"
				: "Lv " + member.level() + "  " + personality.title() + " " + CrewVariant.of(role, member.variant()).title();
		graphics.text(font, font.plainSubstrByWidth(sub, barsLeft - textLeft - 4), textLeft, y + 10, GREY, false);

		// Health bar, then a thin XP bar under it.
		int barWidth = 68;
		float health = member.maxHealth() > 0 ? member.health() / member.maxHealth() : 0;
		graphics.fill(barsLeft, y + 3, barsLeft + barWidth, y + 9, 0xFF3A1A1A);
		graphics.fill(barsLeft, y + 3, barsLeft + Math.round(barWidth * health), y + 9, health > 0.5f ? 0xFF55CC55 : health > 0.25f ? 0xFFE0C040 : 0xFFDD4444);
		graphics.fill(barsLeft, y + 11, barsLeft + barWidth, y + 13, 0xFF202040);
		float xp = member.xpNeeded() > 0 ? (float) member.xp() / member.xpNeeded() : 1f;
		graphics.fill(barsLeft, y + 11, barsLeft + Math.round(barWidth * xp), y + 13, member.xpNeeded() > 0 ? 0xFF6FA8FF : GOLD);
	}

	private void drawOpenRole(GuiGraphicsExtractor graphics, CrewRole role, int y) {
		graphics.fill(left, y + (rowHeight - 16) / 2, left + 16, y + (rowHeight - 16) / 2 + 16, 0xFF2A2A2A);
		graphics.text(font, "?", left + 6, y + (rowHeight - 16) / 2 + 4, DARK, false);
		int textLeft = left + 20;
		graphics.text(font, role.title() + " (" + role.inspiredBy() + ")", textLeft, y + 1, GREY, false);
		String needs = role.minCrew() > view.members().size()
				? "Joins once you have " + role.minCrew() + " crewmates"
				: "Open. Recruits want " + role.trialCount() + " " + new ItemStack(role.trialItem()).getHoverName().getString();
		graphics.text(font, font.plainSubstrByWidth(needs, panelWidth - BUTTONS_WIDTH - 24), textLeft, y + 10, DARK, false);
	}

	private List<Component> memberTooltip(CrewRole role, CrewPayloads.Member member) {
		List<Component> lines = new ArrayList<>();
		lines.add(Component.literal(member.name()).withColor(GOLD));
		if (member.nearby()) {
			CrewPersonality personality = CrewPersonality.byName(member.personality());
			lines.add(Component.literal(member.xpNeeded() > 0
					? "Level " + member.level() + " (" + member.xp() + "/" + member.xpNeeded() + " XP)"
					: "Level " + member.level() + " (max)"));
			lines.add(Component.literal("Health " + Math.round(member.health()) + "/" + Math.round(member.maxHealth())));
			lines.add(Component.literal(personality.title() + ": " + personality.description()).withColor(GREY));
			lines.add(Component.literal("Mode: " + CrewMode.values()[member.mode()].name().charAt(0)
					+ CrewMode.values()[member.mode()].name().substring(1).toLowerCase()).withColor(GREY));
		}
		lines.add(Component.literal("Where: " + member.where()).withColor(GREY));
		lines.add(Component.literal("Work job: " + role.job()).withColor(GREY));
		lines.add(Component.literal("Perk: " + role.perk()).withColor(0xFFFFFF55));
		lines.add(Component.literal("Levels up by fighting and working. Gives armor and weapons from their bag.").withColor(DARK));
		return lines;
	}

	private List<Component> openRoleTooltip(CrewRole role) {
		List<Component> lines = new ArrayList<>();
		lines.add(Component.literal(role.title() + " (" + role.inspiredBy() + ")").withColor(GOLD));
		lines.add(Component.literal("Work job: " + role.job()).withColor(GREY));
		lines.add(Component.literal("Perk: " + role.perk()).withColor(0xFFFFFF55));
		lines.add(Component.literal("Trial: " + role.trialCount() + " " + new ItemStack(role.trialItem()).getHoverName().getString()).withColor(GREY));
		if (role.minCrew() > 0) {
			lines.add(Component.literal("Only joins a crew with " + role.minCrew() + "+ crewmates").withColor(GREY));
		}
		return lines;
	}

	private void drawRecruits(GuiGraphicsExtractor graphics, int mouseX, int mouseY) {
		if (recruits == null) {
			return;
		}
		CrewRole role = CrewRole.byId(recruits.role());
		if (role == null) {
			return;
		}
		graphics.text(font, role.title() + " recruits (" + role.inspiredBy() + ")", left, top, GOLD, true);
		int y = wrapped(graphics, "Each also asks for " + role.trialCount() + " " + new ItemStack(role.trialItem()).getHoverName().getString()
				+ ". Job: " + role.job() + ". Perk: " + role.perk() + ".", left, top + 12, panelWidth, GREY);

		int cardWidth = (panelWidth - 8) / 3;
		int cardTop = Math.max(y + 4, rowsTop);
		for (int i = 0; i < recruits.recruits().size(); i++) {
			CrewPayloads.Recruit recruit = recruits.recruits().get(i);
			CrewVariant variant = CrewVariant.of(role, recruit.variant());
			CrewPersonality personality = CrewPersonality.byName(recruit.personality());
			int x = left + i * (cardWidth + 4) + 4;
			graphics.fill(x - 2, cardTop, x + cardWidth - 6, rowsTop + 136, 0x40FFFFFF);
			face(graphics, role, recruit.variant(), x + (cardWidth - 8) / 2 - 16, cardTop + 6, 32, true);
			int ty = cardTop + 44;
			ty = centeredIn(graphics, recruit.name(), x, cardWidth - 8, ty, 0xFFFFFFFF);
			ty = centeredIn(graphics, variant.title(), x, cardWidth - 8, ty, 0xFF55FFFF);
			ty = centeredIn(graphics, personality.title(), x, cardWidth - 8, ty, GOLD);
			ty = centeredIn(graphics, recruit.health() + " health", x, cardWidth - 8, ty + 4, GREY);
			ty = centeredIn(graphics, recruit.damage() + " strength", x, cardWidth - 8, ty, GREY);
			centeredIn(graphics, variant.speedWord(), x, cardWidth - 8, ty, GREY);
			if (mouseX >= x - 2 && mouseX < x + cardWidth - 6 && mouseY >= cardTop && mouseY < rowsTop + 136) {
				tooltip(graphics, List.of(Component.literal(personality.title()).withColor(GOLD),
						Component.literal(personality.description())), mouseX, mouseY);
			}
		}
		int infoY = rowsTop + 166;
		if (!recruits.problem().isEmpty()) {
			infoY = wrapped(graphics, recruits.problem(), left, infoY, panelWidth, RED);
		} else if (!view.notice().isEmpty()) {
			infoY = wrapped(graphics, view.notice(), left, infoY, panelWidth, RED);
		}
		wrapped(graphics, "You have " + view.berries() + " Berries. New recruits arrive every day.", left, infoY, panelWidth, DARK);
	}

	// ---------- Small drawing helpers ----------

	private void face(GuiGraphicsExtractor graphics, CrewRole role, int variant, int x, int y, int size, boolean hat) {
		String suffix = variant == 0 ? "" : "_" + variant;
		Identifier skin = OnePieceMod.id("textures/entity/crewmate/" + role.id() + suffix + ".png");
		PlayerFaceExtractor.extractRenderState(graphics, skin, x, y, size, hat, false, -1);
	}

	private void tooltip(GuiGraphicsExtractor graphics, List<Component> lines, int mouseX, int mouseY) {
		graphics.setTooltipForNextFrame(font, lines, Optional.empty(), mouseX, mouseY);
	}

	private void centered(GuiGraphicsExtractor graphics, String text, int y, int color) {
		graphics.text(font, text, (width - font.width(text)) / 2, y, color, true);
	}

	private int centeredIn(GuiGraphicsExtractor graphics, String text, int x, int boxWidth, int y, int color) {
		String fitted = font.plainSubstrByWidth(text, boxWidth);
		graphics.text(font, fitted, x + (boxWidth - font.width(fitted)) / 2, y, color, false);
		return y + font.lineHeight + 1;
	}

	/** Draws text that wraps onto more lines. Returns the y below it. */
	private int wrapped(GuiGraphicsExtractor graphics, String text, int x, int y, int maxWidth, int color) {
		for (FormattedCharSequence line : font.split(Component.literal(text), maxWidth)) {
			graphics.text(font, line, x, y, color, false);
			y += font.lineHeight + 1;
		}
		return y;
	}
}
