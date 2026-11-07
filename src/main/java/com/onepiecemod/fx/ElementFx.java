package com.onepiecemod.fx;

import io.netty.buffer.ByteBuf;

import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentSyncPredicate;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.power.DevilFruit;

/**
 * Two big-moment visuals:
 * - a Logia user's body turning into their element (fire, sand, smoke, ice...) when an attack passes through them;
 * - the red and black shockwave of Conqueror's Haki.
 */
public final class ElementFx {
	/** The last time an attack passed through this Logia user (game tick) and their element's color. */
	public record Flash(long tick, int color) {
		static final StreamCodec<ByteBuf, Flash> STREAM_CODEC = StreamCodec.composite(
				ByteBufCodecs.VAR_LONG, Flash::tick, ByteBufCodecs.INT, Flash::color, Flash::new);
	}

	/** Sent to everyone nearby so they can draw it; not saved. */
	public static final AttachmentType<Flash> LOGIA_FLASH = AttachmentRegistry.create(
			OnePieceMod.id("logia_flash"),
			builder -> builder.syncWith(Flash.STREAM_CODEC, AttachmentSyncPredicate.all()));

	/** How long the body stays turned into the element, in ticks. */
	public static final int FLASH_TICKS = 14;

	private static final int CONQUEROR_RED = 0xFFE01030, CONQUEROR_BLACK = 0xFF0A0006;

	private ElementFx() {
	}

	/** Loads the class early, so the attachment is registered before any player joins. */
	public static void initialize() {
	}

	/** Ticks since the body last turned into its element, or -1 if not right now. */
	public static float flashAge(Entity entity, float partialTick) {
		Flash flash = entity.getAttached(LOGIA_FLASH);
		if (flash == null) {
			return -1;
		}
		float age = entity.level().getGameTime() - flash.tick() + partialTick;
		return age >= 0 && age < FLASH_TICKS ? age : -1;
	}

	/** An attack just passed through a Logia user: their body bursts into their element for a moment. */
	public static void logiaDodge(ServerPlayer player, DevilFruit fruit) {
		ServerLevel level = (ServerLevel) player.level();
		player.setAttached(LOGIA_FLASH, new Flash(level.getGameTime(), fruit.color()));
		Vec3 middle = player.position().add(0, player.getBbHeight() / 2, 0);
		level.sendParticles(element(fruit), middle.x, middle.y, middle.z, 30, 0.35, 0.7, 0.35, 0.04);
		level.sendParticles(new DustParticleOptions(fruit.color(), 1.6f), middle.x, middle.y, middle.z, 25, 0.4, 0.8, 0.4, 0.0);
		MoveFx.at(level, MoveStyle.SPHERE, middle, Vec3.ZERO, 0xFF000000 | fruit.accent(), 0xFF000000 | fruit.color(), 1.1f, 8, null);
	}

	/** The particle that matches each Logia's element. */
	private static ParticleOptions element(DevilFruit fruit) {
		String id = fruit.id();
		if (id.startsWith("mera") || id.startsWith("netsu")) {
			return ParticleTypes.FLAME;
		} else if (id.startsWith("magu")) {
			return ParticleTypes.LAVA;
		} else if (id.startsWith("hie") || id.startsWith("yuki")) {
			return ParticleTypes.SNOWFLAKE;
		} else if (id.startsWith("goro")) {
			return ParticleTypes.ELECTRIC_SPARK;
		} else if (id.startsWith("pika")) {
			return ParticleTypes.END_ROD;
		} else if (id.startsWith("yami") || id.startsWith("numa")) {
			return ParticleTypes.SQUID_INK;
		} else if (id.startsWith("moku") || id.startsWith("gasu")) {
			return ParticleTypes.LARGE_SMOKE;
		}
		return ParticleTypes.CLOUD; // Sand, mochi and the rest: a puff in the fruit's colors (the dust above).
	}

	/** Conqueror's Haki: a red-black dome bursts out, rings race across the ground and black lightning crackles. */
	public static void conqueror(ServerPlayer player, ServerLevel level, double radius) {
		Vec3 feet = player.position();
		MoveFx.at(level, MoveStyle.SPHERE, feet.add(0, 1, 0), Vec3.ZERO, CONQUEROR_BLACK, CONQUEROR_RED, (float) radius * 0.7f, 14, null);
		MoveFx.at(level, MoveStyle.RING, feet.add(0, 0.1, 0), new Vec3(radius, 0, 0), CONQUEROR_RED, CONQUEROR_BLACK, 1.8f, 20, null);
		MoveFx.at(level, MoveStyle.RING, feet.add(0, 0.6, 0), new Vec3(radius * 0.6, 0, 0), CONQUEROR_BLACK, CONQUEROR_RED, 1.2f, 14, null);
		for (int i = 0; i < 8; i++) {
			double angle = i * Math.PI / 4 + level.getRandom().nextDouble() * 0.5;
			double dist = radius * (0.35 + level.getRandom().nextDouble() * 0.5);
			Vec3 ground = feet.add(Math.cos(angle) * dist, 0, Math.sin(angle) * dist);
			Vec3 top = feet.add(0, 2.2, 0);
			MoveFx.at(level, MoveStyle.BOLT, top, ground.subtract(top), CONQUEROR_RED, CONQUEROR_BLACK, 0.6f, 10 + i % 3, null);
		}
		level.sendParticles(new DustParticleOptions(0xE01030, 2.0f), feet.x, feet.y + 1, feet.z, 60, radius / 2, 0.8, radius / 2, 0.0);
		level.sendParticles(new DustParticleOptions(0x100008, 2.0f), feet.x, feet.y + 1, feet.z, 60, radius / 2, 0.8, radius / 2, 0.0);
	}
}
