package com.onepiecemod.career.client;

import net.minecraft.client.renderer.entity.EntityRenderers;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

import com.onepiecemod.career.Career;
import com.onepiecemod.career.CareerFeature;
import com.onepiecemod.career.CareerPayloads;

/**
 * Client-only setup for careers. OnePieceModClient calls initialize().
 * Keeps the latest career the server sent, for the career screen and the HUD.
 */
public class CareerClient {
	private static CareerPayloads.Sync data;

	public static CareerPayloads.Sync data() {
		return data;
	}

	public static void initialize() {
		EntityRenderers.register(CareerFeature.CAREER_ALLY, CareerAllyRenderer::new);
		ClientPlayNetworking.registerGlobalReceiver(CareerPayloads.Sync.TYPE, (payload, context) -> {
			data = payload;
			if (payload.open()) {
				context.client().gui.setScreen(new CareerScreen());
			} else if (context.client().gui.screen() instanceof CareerScreen screen) {
				screen.refresh();
			}
		});
		ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> data = null);
	}

	/** For the HUD: "Lt." for a Marine Lieutenant, null for pirates (the HUD shows the bounty instead). */
	public static String hudLabel() {
		if (data == null) {
			return null;
		}
		Career career = Career.byId(data.career());
		return career == Career.PIRATE ? null : career.rank(data.rank()).shortName();
	}

	/** Marines have no bounty, so the HUD shows their rank in its place. */
	public static boolean hidesBounty() {
		return data != null && Career.byId(data.career()) == Career.MARINE;
	}

	/** The career's colour as 0xAARRGGBB. */
	public static int color() {
		if (data == null) {
			return 0xFFFFFFFF;
		}
		return switch (Career.byId(data.career())) {
			case MARINE -> 0xFF55C8FF;
			case REVOLUTIONARY -> 0xFF62E07A;
			default -> 0xFFFFD75E;
		};
	}
}
