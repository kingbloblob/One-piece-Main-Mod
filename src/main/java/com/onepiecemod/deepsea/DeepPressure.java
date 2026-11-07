package com.onepiecemod.deepsea;

import com.mojang.serialization.Codec;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.race.Race;
import com.onepiecemod.race.RaceAttachments;
import com.onepiecemod.resource.Resources;

/**
 * The deep sea crushes anyone who swims too far down. Normal seas and the floor of most of the ocean are fine;
 * the trenches (DeepTrenchStructure) and the way down to Fish-Man Island are not.
 *
 * Safe down there: Fish-Men, anyone inside a submarine or a coated ship's bubble (they aren't in the water at all,
 * see ship.ShipHold), and anyone wrapped in their own Bubble Coating. A Diving Helmet lets you go a bit deeper.
 */
public final class DeepPressure {
	private DeepPressure() {
	}

	/** Blocks under the sea's surface where the pressure starts. Most of the ocean floor is shallower. */
	public static final int SAFE_DEPTH = 48;
	/** A Diving Helmet holds out this much further. */
	public static final int HELMET_DEPTH = 80;
	private static final float DAMAGE = 2.0f;

	/** Game time until which this player's own Bubble Coating keeps the pressure off. */
	public static final AttachmentType<Long> COATED_UNTIL = AttachmentRegistry.create(
			OnePieceMod.id("bubble_coated_until"),
			builder -> builder.persistent(Codec.LONG));

	static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 20 != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				tick(player);
			}
		});
	}

	/** Wraps the player in a bubble for this many ticks (resource.BubbleCoatingItem calls this). */
	public static void coat(Player player, int ticks) {
		player.setAttached(COATED_UNTIL, player.level().getGameTime() + ticks);
	}

	public static boolean isCoated(Player player) {
		Long until = player.getAttached(COATED_UNTIL);
		return until != null && player.level().getGameTime() < until;
	}

	/** How deep this player's eyes are under the sea's surface, in blocks. */
	public static double depth(Player player) {
		return player.level().getSeaLevel() - player.getEyeY();
	}

	/** True if the sea's weight is crushing this player right now. */
	public static boolean crushing(Player player) {
		if (player.isCreative() || player.isSpectator() || !player.isUnderWater()) {
			return false;
		}
		double depth = depth(player);
		if (depth < SAFE_DEPTH) {
			return false;
		}
		if (player.getItemBySlot(EquipmentSlot.HEAD).is(Resources.DIVING_HELMET) && depth < HELMET_DEPTH) {
			return false;
		}
		return !RaceAttachments.is(player, Race.FISHMAN) && !isCoated(player);
	}

	private static void tick(ServerPlayer player) {
		if (!crushing(player)) {
			return;
		}
		player.hurtServer(player.level(), player.damageSources().drown(), DAMAGE);
		player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1, false, false, true));
		player.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 60, 0, false, false, true));
		player.sendOverlayMessage(Component.literal("The weight of the deep sea crushes you! Only Fish-Men, submarines and bubble coating come this deep.")
				.withStyle(ChatFormatting.DARK_AQUA));
	}
}
