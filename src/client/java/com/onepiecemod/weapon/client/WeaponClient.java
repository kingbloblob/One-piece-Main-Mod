package com.onepiecemod.weapon.client;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.client.Minecraft;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.item.ItemStack;

import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.item.v1.ItemTooltipCallback;

import com.onepiecemod.weapon.GunItem;
import com.onepiecemod.weapon.WeaponItems;
import com.onepiecemod.weapon.WeaponUpgrades;

/**
 * Client-only setup for weapons (OnePieceModClient calls initialize()):
 *  - a weapon's grade, gun parts and Dial on its tooltip (for every sword, including vanilla ones and Zoro's),
 *  - gun kick: each shot jolts your view up a little, and it drifts most of the way back,
 *  - zoom while aiming (sneaking) with the Senriku or a scoped gun (see mixin/GunZoomMixin).
 */
public class WeaponClient {
	/** How much of each kick drifts back down by itself, and how fast (share per tick). */
	private static final float RECOVER = 0.75f;
	private static final float RECOVER_SPEED = 0.25f;

	/** Burst rounds still to kick: ticks to wait, and how hard. */
	private record Kick(int ticks, float degrees) {}

	private static final List<Kick> KICKS = new ArrayList<>();
	private static float toRecover;

	public static void initialize() {
		ItemTooltipCallback.EVENT.register((stack, context, flag, lines) -> {
			// Guns list their own upgrades in GunItem.appendHoverText.
			if (!(stack.getItem() instanceof GunItem)) {
				lines.addAll(Math.min(1, lines.size()), WeaponUpgrades.describe(stack));
			}
		});

		GunItem.clientRecoil = (degrees, rounds, ticksBetween) -> {
			kick(degrees);
			for (int round = 1; round < rounds; round++) {
				KICKS.add(new Kick(round * ticksBetween, degrees));
			}
		};

		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			LocalPlayer player = client.player;
			if (player == null) {
				KICKS.clear();
				toRecover = 0;
				return;
			}
			if (!KICKS.isEmpty()) {
				List<Kick> later = new ArrayList<>();
				for (Kick kick : KICKS) {
					if (kick.ticks() <= 1) {
						kick(kick.degrees());
					} else {
						later.add(new Kick(kick.ticks() - 1, kick.degrees()));
					}
				}
				KICKS.clear();
				KICKS.addAll(later);
			}
			if (toRecover > 0.01f) {
				float step = toRecover * RECOVER_SPEED;
				toRecover -= step;
				player.setXRot(Mth.clamp(player.getXRot() + step, -90.0f, 90.0f));
			}
		});
	}

	/** Tips your view up by this many degrees, with a tiny sideways wobble. */
	private static void kick(float degrees) {
		LocalPlayer player = Minecraft.getInstance().player;
		if (player == null || degrees <= 0) {
			return;
		}
		float wobble = (player.getRandom().nextFloat() - 0.5f) * degrees * 0.4f;
		player.setXRot(Mth.clamp(player.getXRot() - degrees, -90.0f, 90.0f));
		player.setYRot(player.getYRot() + wobble);
		toRecover += degrees * RECOVER;
	}

	/** How much to narrow the view: 1 = normal, smaller = zoomed in. */
	public static float zoom(AbstractClientPlayer player, boolean firstPerson) {
		if (!firstPerson || player != Minecraft.getInstance().player || !player.isShiftKeyDown()) {
			return 1.0f;
		}
		ItemStack held = player.getMainHandItem();
		if (held.getItem() instanceof GunItem gun && gun.zooms(held)) {
			return held.is(WeaponItems.SENRIKU) ? 0.25f : 0.5f;
		}
		return 1.0f;
	}
}
