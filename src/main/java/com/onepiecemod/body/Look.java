package com.onepiecemod.body;

import java.util.List;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import io.netty.buffer.ByteBuf;

import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;

/**
 * The looks picked on the body screen besides the sliders: a 3D hairstyle and its colour, a scar and an outfit.
 * Each value is an index into the lists below (0 = none). Only looks, no gameplay.
 * The ids must match the groups in tools/skins/appearance.py ("hair:spiky", "scar:eye", "outfit:straw_hat"...).
 */
public record Look(int hair, int hairColor, int scar, int outfit) {
	public static final Look DEFAULT = new Look(0, 0, 0, 0);

	public record Option(String id, String name) {
	}

	public static final List<Option> HAIR = List.of(
			new Option("none", "Your skin's hair"), new Option("spiky", "Spiky"), new Option("long", "Long"),
			new Option("afro", "Afro"), new Option("topknot", "Topknot"), new Option("pompadour", "Pompadour"),
			new Option("ponytail", "Ponytail"));

	/** Hair colours: name and RGB. */
	public static final List<Option> HAIR_COLORS = List.of(
			new Option("1a1a1e", "Black"), new Option("5a3a22", "Brown"), new Option("f0d860", "Blonde"),
			new Option("f07a2a", "Orange"), new Option("c02828", "Red"), new Option("4aa04a", "Green"),
			new Option("3a6ad0", "Blue"), new Option("f080b0", "Pink"), new Option("ececec", "White"),
			new Option("7a4ab0", "Purple"));

	public static final List<Option> SCARS = List.of(
			new Option("none", "None"), new Option("eye", "Over the eye"), new Option("cheek", "Under the eye"),
			new Option("chest_x", "X on the chest"), new Option("burn", "Burn by the eye"), new Option("forehead", "Forehead"));

	public static final List<Option> OUTFITS = List.of(
			new Option("none", "None"), new Option("straw_hat", "Straw Hat"), new Option("marine_coat", "Marine coat"),
			new Option("captain_cape", "Captain's cape"), new Option("bandana", "Bandana"), new Option("headband", "Headband"),
			new Option("tricorn", "Pirate hat"), new Option("haramaki", "Haramaki"));

	public static final Codec<Look> CODEC = RecordCodecBuilder.create(instance -> instance.group(
			Codec.INT.optionalFieldOf("hair", 0).forGetter(Look::hair),
			Codec.INT.optionalFieldOf("hair_color", 0).forGetter(Look::hairColor),
			Codec.INT.optionalFieldOf("scar", 0).forGetter(Look::scar),
			Codec.INT.optionalFieldOf("outfit", 0).forGetter(Look::outfit)
	).apply(instance, Look::new));

	public static final StreamCodec<ByteBuf, Look> STREAM_CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, Look::hair,
			ByteBufCodecs.VAR_INT, Look::hairColor,
			ByteBufCodecs.VAR_INT, Look::scar,
			ByteBufCodecs.VAR_INT, Look::outfit,
			Look::new
	);

	/** Keeps every index inside its list, so a modified game can't send nonsense. */
	public Look clamped() {
		return new Look(fit(hair, HAIR), fit(hairColor, HAIR_COLORS), fit(scar, SCARS), fit(outfit, OUTFITS));
	}

	private static int fit(int value, List<?> list) {
		return value < 0 || value >= list.size() ? 0 : value;
	}

	/** The hair colour as 0xFFRRGGBB, for tinting. */
	public int hairArgb() {
		return 0xFF000000 | Integer.parseInt(HAIR_COLORS.get(fit(hairColor, HAIR_COLORS)).id(), 16);
	}

	public String hairId() {
		return HAIR.get(fit(hair, HAIR)).id();
	}

	public String scarId() {
		return SCARS.get(fit(scar, SCARS)).id();
	}

	public String outfitId() {
		return OUTFITS.get(fit(outfit, OUTFITS)).id();
	}

	/** Outfits worn on the head (hidden under a helmet). */
	public boolean outfitOnHead() {
		String id = outfitId();
		return id.equals("straw_hat") || id.equals("bandana") || id.equals("headband") || id.equals("tricorn");
	}
}
