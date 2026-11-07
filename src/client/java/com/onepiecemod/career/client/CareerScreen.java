package com.onepiecemod.career.client;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.career.Career;
import com.onepiecemod.career.CareerPayloads;
import com.onepiecemod.career.Careers;

/**
 * The career screen, opened with the Den Den Mushi: the rank ladder on the left, progress to the next
 * promotion, salary, backup and orders on the right, and buttons for orders, backup and leaving.
 */
public class CareerScreen extends Screen {
	private static final int PANEL_W = 330;
	private static final int PANEL_H = 214;
	private static final int LADDER_W = 118;

	private int left, top;
	private Button ordersButton, backupButton, leaveButton;
	private boolean leaveArmed = false;

	public CareerScreen() {
		super(Component.literal("Career"));
	}

	@Override
	protected void init() {
		int panelW = Math.min(PANEL_W, width - 16);
		left = (width - panelW) / 2;
		top = Math.max(4, (height - PANEL_H) / 2);
		int y = top + PANEL_H - 34;
		int x = left + LADDER_W + 8;
		int w = (left + panelW - 6 - x - 8) / 3;
		clearWidgets();
		ordersButton = addRenderableWidget(Button.builder(Component.empty(), b -> send(hasOrders() ? "abandon" : "orders"))
				.pos(x, y).size(w, 18).build());
		backupButton = addRenderableWidget(Button.builder(Component.literal("Call backup"), b -> send("backup"))
				.pos(x + w + 4, y).size(w, 18).build());
		leaveButton = addRenderableWidget(Button.builder(Component.empty(), b -> leave())
				.pos(x + 2 * (w + 4), y).size(w, 18).build());
		refresh();
	}

	/** New data from the server: update the buttons. */
	public void refresh() {
		if (ordersButton == null) {
			return;
		}
		CareerPayloads.Sync data = CareerClient.data();
		boolean member = data != null && Career.byId(data.career()) != Career.PIRATE;
		ordersButton.active = member;
		backupButton.active = member && data.backupSeconds() <= 0;
		leaveButton.active = member;
		ordersButton.setMessage(Component.literal(hasOrders() ? "Call off orders" : "Get orders"));
		backupButton.setMessage(Component.literal(member && data.backupSeconds() > 0 ? "Backup " + data.backupSeconds() + "s" : "Call backup"));
		leaveButton.setMessage(Component.literal(leaveArmed ? "Click to confirm" : "Leave"));
	}

	private boolean hasOrders() {
		CareerPayloads.Sync data = CareerClient.data();
		return data != null && !data.mission().isEmpty();
	}

	private void send(String action) {
		ClientPlayNetworking.send(new CareerPayloads.Action(action));
		if (action.equals("orders") || action.equals("backup")) {
			onClose(); // Chat says what happened; get out of the way.
		}
	}

	private void leave() {
		if (!leaveArmed) {
			leaveArmed = true;
			refresh();
			return;
		}
		send("leave");
		onClose();
	}

	@Override
	public boolean isPauseScreen() {
		return false;
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick) {
		CareerPayloads.Sync data = CareerClient.data();
		int panelW = Math.min(PANEL_W, width - 16);
		int color = CareerClient.color();
		graphics.fill(left, top, left + panelW, top + PANEL_H, 0xE0101820);
		graphics.fill(left, top, left + panelW, top + 2, color);
		super.extractRenderState(graphics, mouseX, mouseY, partialTick);

		if (data == null || Career.byId(data.career()) == Career.PIRATE) {
			graphics.centeredText(font, "You're a free pirate.", left + panelW / 2, top + 12, 0xFFFFD75E);
			return;
		}
		Career career = Career.byId(data.career());
		Career.Rank rank = career.rank(data.rank());

		// Title.
		graphics.text(font, career.displayName + " " + rank.name(), left + 8, top + 8, color, true);
		String count = data.points() + " " + career.points;
		graphics.text(font, count, left + panelW - 8 - font.width(count), top + 8, 0xFFDDDDDD, false);

		// Rank ladder, top rank at the top.
		int y = top + 24;
		int rows = career.ranks.size();
		int step = Math.min(15, (PANEL_H - 52) / rows);
		for (int i = rows - 1; i >= 0; i--) {
			Career.Rank r = career.ranks.get(i);
			int rowY = y + (rows - 1 - i) * step;
			boolean current = i == data.rank();
			if (current) {
				graphics.fill(left + 6, rowY - 2, left + LADDER_W, rowY + step - 3, 0x40FFFFFF);
			}
			int textColor = i < data.rank() ? 0xFF8A8A8A : current ? color : 0xFFCCCCCC;
			graphics.text(font, (r.trialCount() > 0 ? "* " : "  ") + r.name(), left + 8, rowY, textColor, false);
		}

		// Details on the right.
		int x = left + LADDER_W + 8;
		int textW = left + panelW - 8 - x;
		y = top + 24;
		Career.Rank next = data.rank() + 1 < career.ranks.size() ? career.ranks.get(data.rank() + 1) : null;
		if (next == null) {
			y = wrap(graphics, "You've reached the top of the ladder.", x, y, textW, 0xFFFFD75E);
		} else {
			y = wrap(graphics, "Next: " + next.name(), x, y, textW, 0xFFFFFFFF);
			int from = rank.need();
			float progress = Math.min(1f, (data.points() - from) / (float) Math.max(1, next.need() - from));
			graphics.fill(x, y + 1, x + textW, y + 7, 0xFF303030);
			graphics.fill(x, y + 1, x + (int) (textW * Math.max(0f, progress)), y + 7, color);
			y += 10;
			y = wrap(graphics, data.points() + " / " + next.need() + " " + career.points, x, y, textW, 0xFFAAAAAA);
			if (next.trialCount() > 0) {
				boolean done = data.trialDone() >= next.trialCount();
				y = wrap(graphics, "* " + Careers.trialText(career, next) + " (" + Math.min(data.trialDone(), next.trialCount()) + "/" + next.trialCount() + ")",
						x, y, textW, done ? 0xFF7CFC7C : 0xFFFFC060);
			}
		}
		y += 4;
		y = wrap(graphics, "Salary: " + rank.salary() + " Berries a day", x, y, textW, 0xFFFFE27A);
		y = wrap(graphics, "Backup: " + rank.backup() + (rank.backup() == 1 ? " soldier" : " soldiers")
				+ (data.backupSeconds() > 0 ? " (ready in " + data.backupSeconds() + "s)" : " (ready)"), x, y, textW, 0xFFCCCCCC);
		y = wrap(graphics, "Orders carried out: " + data.missionsDone(), x, y, textW, 0xFFCCCCCC);
		if (career == Career.MARINE && data.strikes() > 0) {
			y = wrap(graphics, "Strikes: " + data.strikes() + "/" + Careers.MAX_STRIKES + " (3 = court-martial)", x, y, textW, 0xFFFF6060);
		}
		y += 4;
		if (data.mission().isEmpty()) {
			wrap(graphics, "No orders. Get some below, or ask a recruiter.", x, y, textW, 0xFF8A8A8A);
		} else {
			y = wrap(graphics, "Orders: " + data.mission(), x, y, textW, color);
			wrap(graphics, "Reward: " + data.missionReward() + " " + career.points, x, y, textW, 0xFFAAAAAA);
		}
		graphics.text(font, "* boss trial needed.  Sneak + use Den Den Mushi: backup", left + 8, top + PANEL_H - 10, 0xFF707070, false);
	}

	private int wrap(GuiGraphicsExtractor graphics, String text, int x, int y, int w, int color) {
		for (FormattedCharSequence line : font.split(Component.literal(text), w)) {
			graphics.text(font, line, x, y, color, false);
			y += font.lineHeight + 1;
		}
		return y;
	}
}
