package com.onepiecemod.body;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.util.Mth;

/**
 * How a player's body looks, picked with the sliders on the body screen.
 * Every value goes from -1 to 1, and 0 is a normal Minecraft body.
 *
 *   height  short .. tall     (the only one that changes the hitbox, by up to 10%)
 *   weight  skinny .. heavy   (whole body, arms and legs get thinner or thicker)
 *   chest   small .. big
 *   arms    thin .. muscly
 *   legs    skinny .. big
 *   head    small .. big
 */
public record Body(float height, float weight, float chest, float arms, float legs, float head) {
	public static final Body DEFAULT = new Body(0, 0, 0, 0, 0, 0);

	/** How much taller or shorter the tallest and shortest settings are (0.1 = 10%). */
	public static final float MAX_HEIGHT_CHANGE = 0.1f;

	/** Saves the body to disk. */
	public static final Codec<Body> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.FLOAT.fieldOf("height").forGetter(Body::height),
			Codec.FLOAT.fieldOf("weight").forGetter(Body::weight),
			Codec.FLOAT.fieldOf("chest").forGetter(Body::chest),
			Codec.FLOAT.fieldOf("arms").forGetter(Body::arms),
			Codec.FLOAT.fieldOf("legs").forGetter(Body::legs),
			Codec.FLOAT.fieldOf("head").forGetter(Body::head)
	).apply(instance, Body::new));

	/** Sends the body over the network. */
	public static final StreamCodec<ByteBuf, Body> STREAM_CODEC = StreamCodec.composite(
			ByteBufCodecs.FLOAT, Body::height,
			ByteBufCodecs.FLOAT, Body::weight,
			ByteBufCodecs.FLOAT, Body::chest,
			ByteBufCodecs.FLOAT, Body::arms,
			ByteBufCodecs.FLOAT, Body::legs,
			ByteBufCodecs.FLOAT, Body::head,
			Body::new
	);

	/** Keeps every value between -1 and 1, so a modified game can't send a giant head. */
	public Body clamped() {
		return new Body(c(height), c(weight), c(chest), c(arms), c(legs), c(head));
	}

	/** 0.9 for the shortest setting, 1.0 for normal, 1.1 for the tallest. */
	public float heightScale() {
		return 1 + c(height) * MAX_HEIGHT_CHANGE;
	}

	private static float c(float value) {
		return Float.isNaN(value) ? 0 : Mth.clamp(value, -1, 1);
	}
}
