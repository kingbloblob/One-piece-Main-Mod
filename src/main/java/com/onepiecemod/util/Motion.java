package com.onepiecemod.util;

import net.minecraft.network.protocol.game.ClientboundSetEntityMotionPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;

/** Makes sure a push we gave something on the server actually moves it on screen. */
public final class Motion {
	private Motion() {
	}

	/**
	 * Call after setDeltaMovement. Marking needsSync is enough for mobs, but it doesn't reach a
	 * player's own game, which moves the player itself. So players also get their new speed sent
	 * straight to them, or dashes, leaps and knockbacks on players would do nothing.
	 */
	public static void sync(Entity entity) {
		entity.needsSync = true;
		if (entity instanceof ServerPlayer player && player.connection != null) {
			player.connection.send(new ClientboundSetEntityMotionPacket(player));
		}
	}
}
