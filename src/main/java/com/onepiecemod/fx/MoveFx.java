package com.onepiecemod.fx;

import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.haki.HakiPowers;
import com.onepiecemod.power.DevilFruit;

/**
 * Spawns the visible shapes of Devil Fruit moves. FruitAbilities calls these; nothing here hurts anyone.
 *
 * Each move either picks a "Look" on purpose (the famous ones, like Luffy's stretchy arm or Ace's fire
 * fist), or gets one picked automatically from its particle and its fruit's type and colors.
 *
 * Colors are written 0xAARRGGBB: two letters each for see-through-ness, red, green and blue.
 */
public class MoveFx {
	/**
	 * How a move looks.
	 *
	 * @param style  the shape
	 * @param color  the bright inner color
	 * @param color2 the outer color
	 * @param size   how thick it is (1 = normal)
	 * @param trail  particles left behind while it flies, or null for none
	 */
	public record Look(MoveStyle style, int color, int color2, float size, ParticleOptions trail) {
		public Look sized(float newSize) {
			return new Look(style, color, color2, newSize, trail);
		}
	}

	// ---- Element colors (inner, outer) ----
	public static final int FIRE = 0xFFFFE27A, FIRE_OUT = 0xFFFF5A0A;
	public static final int BLUE_FIRE = 0xFFC8FFFF, BLUE_FIRE_OUT = 0xFF2A8CFF;
	public static final int MAGMA = 0xFFFFD060, MAGMA_OUT = 0xFFFF4010;
	public static final int ICE = 0xFFF0FFFF, ICE_OUT = 0xFF7FCFFF;
	public static final int LIGHT = 0xFFFFFFFF, LIGHT_OUT = 0xFFFFE040;
	public static final int SPARK = 0xFFFFFFFF, SPARK_OUT = 0xFF5AC8FF;
	public static final int DARK = 0xFF7A3AA8, DARK_OUT = 0xFF0C0612;
	public static final int SMOKE = 0xFFF4F4F4, SMOKE_OUT = 0xFF9C9CA6;
	public static final int SAND = 0xFFF2DCA6, SAND_OUT = 0xFFB88E50;
	public static final int POISON = 0xFFD478FF, POISON_OUT = 0xFF5A1478;
	public static final int SKIN = 0xFFF2C49A, SKIN_OUT = 0xFFD2946A;
	public static final int HAKI = 0xFF3A2C46, HAKI_OUT = 0xFF0E0814;
	public static final int QUAKE = 0xFFFFFFFF, QUAKE_OUT = 0xFFB4D2FF;
	public static final int ROOM = 0xFFBFE8FF, ROOM_OUT = 0xFF3C8CE6;
	public static final int PLANT = 0xFFA6E070, PLANT_OUT = 0xFF5A3A1E;
	public static final int LOVE = 0xFFFFC0D8, LOVE_OUT = 0xFFF04880;
	public static final int GOLD = 0xFFFFF2A0, GOLD_OUT = 0xFFE0A020;

	// ---- Looks for the famous moves ----
	public static final Look GOMU_ARM = new Look(MoveStyle.ARM, SKIN, SKIN_OUT, 1.0f, null);
	public static final Look FIRE_FIST = new Look(MoveStyle.FIST, FIRE, FIRE_OUT, 1.7f, ParticleTypes.FLAME);
	public static final Look MAGMA_FIST = new Look(MoveStyle.FIST, MAGMA, MAGMA_OUT, 2.0f, ParticleTypes.LAVA);
	public static final Look SMOKE_FIST = new Look(MoveStyle.FIST, SMOKE, SMOKE_OUT, 1.4f, ParticleTypes.CLOUD);
	public static final Look FLYING_FIST = new Look(MoveStyle.FIST, SKIN, SKIN_OUT, 0.7f, null);
	public static final Look ICE_SPEAR = new Look(MoveStyle.SPEAR, ICE, ICE_OUT, 1.2f, ParticleTypes.SNOWFLAKE);
	public static final Look LASER = new Look(MoveStyle.BEAM, 0xFFFFFFB0, 0xFFFFC000, 1.2f, null);
	public static final Look DARK_PULL = new Look(MoveStyle.BEAM, DARK, DARK_OUT, 1.0f, null);
	public static final Look SAND_BLADE = new Look(MoveStyle.SLASH, SAND, SAND_OUT, 1.3f, null);
	public static final Look QUAKE_CRACK = new Look(MoveStyle.CRACK, QUAKE, QUAKE_OUT, 1.6f, null);
	public static final Look STRING = new Look(MoveStyle.BEAM, 0xFFFFFFFF, 0xFFF0B8E0, 0.12f, null);
	public static final Look HEART_ORB = new Look(MoveStyle.ORB, LOVE, LOVE_OUT, 1.0f, ParticleTypes.HEART);
	public static final Look PAW_ORB = new Look(MoveStyle.ORB, 0xFFFFFFFF, 0xFFF5A0C0, 1.6f, ParticleTypes.CLOUD);
	public static final Look DRAGON_BREATH = new Look(MoveStyle.BEAM, FIRE, FIRE_OUT, 2.0f, ParticleTypes.FLAME);
	/** Loki's Nidhogg breath: a thick yellow-white thunder beam. */
	public static final Look THUNDER_BREATH = new Look(MoveStyle.BEAM, 0xFFFFFFC0, 0xFFF0D020, 2.0f, ParticleTypes.ELECTRIC_SPARK);
	public static final Look FROST_BREATH = new Look(MoveStyle.BEAM, ICE, ICE_OUT, 1.4f, null);
	public static final Look ROOM_LINE = new Look(MoveStyle.BEAM, ROOM, ROOM_OUT, 0.15f, null);
	public static final Look GRAVITY_BLADE = new Look(MoveStyle.SLASH, 0xFFD8B8FF, 0xFF4A2080, 1.4f, null);
	public static final Look ROOTS = new Look(MoveStyle.BEAM, PLANT, PLANT_OUT, 0.5f, null);
	public static final Look CLAWS = new Look(MoveStyle.CLAW, 0xFFFFFFFF, 0xFFE03030, 1.0f, null);
	public static final Look MAGMA_BALL = new Look(MoveStyle.ORB, MAGMA, MAGMA_OUT, 2.4f, ParticleTypes.LAVA);

	// ---- Spawning ----

	/** Puts one shape into the world. reach is the direction and distance it goes from start. */
	public static MoveEffectEntity spawn(ServerLevel level, MoveStyle style, Vec3 start, Vec3 reach,
			int color, int color2, float size, int life, Entity owner, ParticleOptions trail) {
		MoveEffectEntity fx = FxFeature.MOVE_EFFECT.create(level, EntitySpawnReason.TRIGGERED);
		if (fx == null) {
			return null;
		}
		fx.setPos(start);
		fx.setup(style, color, color2, reach, size, life, owner);
		if (trail != null) {
			fx.setTrail(trail);
		}
		level.addFreshEntity(fx);
		return fx;
	}

	private static MoveEffectEntity spawn(ServerLevel level, Look look, Vec3 start, Vec3 reach, int life, Entity owner) {
		return spawn(level, look.style(), start, reach, look.color(), look.color2(), look.size(), life, owner, look.trail());
	}

	/** Roughly where your hand is when you throw a move: in front of you, a little right and down. */
	public static Vec3 hand(LivingEntity user) {
		Vec3 look = user.getLookAngle();
		Vec3 right = new Vec3(-look.z, 0, look.x);
		right = right.lengthSqr() < 1.0e-4 ? Vec3.ZERO : right.normalize();
		return user.getEyePosition().add(look.scale(0.5)).add(right.scale(0.35)).add(0, -0.35, 0);
	}

	/**
	 * The shape for a move that goes from you to a point: a target you hit, or the wall or end of its range.
	 * Uses the given look, or picks one from the fruit and particle when look is null.
	 */
	public static void beam(LivingEntity user, ServerLevel level, DevilFruit fruit, ParticleOptions particle,
			Vec3 end, boolean hit, Look look) {
		if (look == null) {
			look = fruitLook(fruit);
		}
		if (look == null) {
			look = autoLook(fruit, particle, user.getEyePosition().distanceTo(end));
		}
		com.onepiecemod.anim.CombatAnims.fruitMove(user, look.style());
		Vec3 start = hand(user);
		Vec3 reach = end.subtract(start);
		switch (look.style()) {
			case ARM -> arm(user, level, end, false);
			case FIST -> spawn(level, look, start, reach, 18, user);
			case ORB -> {
				spawn(level, look, start, reach, 18, user);
				if (hit) {
					// A small pop where it lands, a moment later.
					spawn(level, MoveStyle.SPHERE, end, Vec3.ZERO, look.color(), look.color2(), 1.4f * look.size(), 9, null, null);
				}
			}
			case SPEAR -> spawn(level, look, start, reach, 15, user);
			case BOLT -> spawn(level, look, start, reach, 8, user);
			case BEAM -> spawn(level, look, start, reach, 12, user);
			case SLASH, CLAW -> {
				// Cuts appear right in front of you, facing the way you look.
				double radius = Math.min(3.2, Math.max(1.8, reach.length() * 0.5));
				spawn(level, look, user.getEyePosition().add(0, -0.4, 0), user.getLookAngle().scale(radius), look.style() == MoveStyle.SLASH ? 10 : 9, user);
				if (hit && reach.length() > 4) {
					spawn(level, look, end.subtract(user.getLookAngle().scale(1.2)), user.getLookAngle().scale(1.6), 8, null);
				}
			}
			case CRACK -> {
				Vec3 at = hit ? end.subtract(reach.normalize().scale(0.8)) : end;
				spawn(level, look, at, reach.normalize().scale(2.5 * look.size()), 22, null);
				spawn(level, MoveStyle.SPHERE, at, Vec3.ZERO, look.color(), look.color2(), 2.2f * look.size(), 12, null, null);
			}
			case WAVES -> spawn(level, look, start, reach, 16, user);
			default -> spawn(level, look, end, reach.normalize(), 14, user);
		}
		beamExtras(user, level, fruit, particle, look, start, end, hit);
	}

	/** The finishing touches some moves get on top of their main shape: explosions, portals, webs, walls. */
	private static void beamExtras(LivingEntity user, ServerLevel level, DevilFruit fruit, ParticleOptions particle, Look look,
			Vec3 start, Vec3 end, boolean hit) {
		Vec3 dir = end.subtract(start);
		dir = dir.lengthSqr() < 1.0e-4 ? user.getLookAngle() : dir.normalize();
		if ((particle == ParticleTypes.EXPLOSION || particle == ParticleTypes.EXPLOSION_EMITTER) && look.style() != MoveStyle.CRACK) {
			// Whatever it was, it blows up where it lands, a moment after it gets there.
			MoveEffectEntity boom = spawn(level, MoveStyle.BURST, end, new Vec3(1.6 * look.size(), 0, 0), 0xFFFFF4C0, 0xFF5A4A40,
					Math.max(0.8f, look.size()), 16, null, null);
			if (boom != null) {
				boom.delay(4);
			}
		}
		String id = fruit != null ? fruit.id() : "";
		switch (id) {
			case "wapu_wapu_no_mi" -> spawn(level, MoveStyle.GATE, end, dir.scale(1.3), 0xFFE8D8FF, 0xFF7A40D0, 1.0f, 20, null, null);
			case "mira_mira_no_mi" -> spawn(level, MoveStyle.GATE, start.add(dir.scale(0.6)), dir.scale(1.1), 0xFFFFFFFF, 0xFF9CD8FF, 0.8f, 16, null, null);
			case "kumo_kumo_no_mi_rosamygale_grauvogeli", "ori_ori_no_mi", "nui_nui_no_mi" -> {
				if (hit) {
					int c = id.startsWith("ori") ? 0xFFD8D8E0 : id.startsWith("nui") ? 0xFFFFD0E8 : 0xFFFFFFFF;
					spawn(level, MoveStyle.WEB, end.subtract(dir.scale(0.4)), dir.scale(1.6), c, 0xFF9090A0, 1.0f, 30, null, null);
				}
			}
			case "bari_bari_no_mi" -> spawn(level, MoveStyle.SHIELD, end.subtract(dir.scale(0.6)), dir, 0xFFF0FFFF, 0xFF7FE0FF, 1.4f, 18, null, null);
			case "awa_awa_no_mi", "woshu_woshu_no_mi" -> {
				// A spray of soap bubbles that drift alongside the main one.
				for (int i = 0; i < 4; i++) {
					Vec3 wobble = new Vec3(level.getRandom().nextDouble() - 0.5, level.getRandom().nextDouble() * 0.6, level.getRandom().nextDouble() - 0.5);
					spawn(level, MoveStyle.ORB, start, end.subtract(start).add(wobble.scale(2.5)), 0xFFFFFFFF, 0xFFB8E8FF, 0.45f, 20 + i * 3, null, null);
				}
			}
			default -> {
			}
		}
	}

	/** Looks for the fruits whose moves should look like themselves, not like "a ball in the fruit's colors". */
	public static Look fruitLook(DevilFruit fruit) {
		if (fruit == null) {
			return null;
		}
		return switch (fruit.id()) {
			case "oto_oto_no_mi" -> new Look(MoveStyle.WAVES, 0xFFFFF0FF, 0xFF8A50E0, 1.0f, ParticleTypes.NOTE);
			case "noro_noro_no_mi" -> new Look(MoveStyle.BEAM, 0xFFFFE0F4, 0xFFE070C8, 0.9f, null);
			case "modo_modo_no_mi" -> new Look(MoveStyle.ORB, 0xFFFFF6D0, 0xFFC8A040, 1.0f, ParticleTypes.END_ROD);
			case "pero_pero_no_mi" -> new Look(MoveStyle.SPEAR, 0xFFFFF0F6, 0xFFFF70B0, 1.2f, null);
			case "doru_doru_no_mi" -> new Look(MoveStyle.SPEAR, 0xFFFFFFF4, 0xFFE0D0A8, 1.2f, null);
			case "buki_buki_no_mi" -> new Look(MoveStyle.SPEAR, 0xFFF0F4FF, 0xFF8090A8, 1.0f, null);
			case "kira_kira_no_mi" -> new Look(MoveStyle.FIST, 0xFFF0FFFF, 0xFF9CE8FF, 1.1f, ParticleTypes.END_ROD);
			case "ishi_ishi_no_mi" -> new Look(MoveStyle.FIST, 0xFFD6D6D6, 0xFF6E6E70, 1.4f, null);
			case "bisu_bisu_no_mi" -> new Look(MoveStyle.FIST, 0xFFF6D9A0, 0xFFB8803A, 1.2f, null);
			case "riki_riki_no_mi" -> new Look(MoveStyle.FIST, SKIN, 0xFFC04030, 1.6f, null);
			case "kumo_kumo_no_mi_rosamygale_grauvogeli" -> new Look(MoveStyle.BEAM, 0xFFFFFFFF, 0xFFC0C0C8, 0.15f, null);
			case "ori_ori_no_mi" -> new Look(MoveStyle.BEAM, 0xFFE0E0E8, 0xFF606070, 0.2f, null);
			case "nui_nui_no_mi" -> new Look(MoveStyle.BEAM, 0xFFFFFFFF, 0xFFF080B0, 0.12f, null);
			case "fude_fude_no_mi" -> new Look(MoveStyle.BEAM, 0xFF505050, 0xFF101010, 0.5f, ParticleTypes.SQUID_INK);
			case "memo_memo_no_mi" -> new Look(MoveStyle.BEAM, 0xFFFFF0D0, 0xFF6A4A2A, 0.4f, null);
			case "mira_mira_no_mi" -> new Look(MoveStyle.BEAM, 0xFFFFFFFF, 0xFF9CD8FF, 0.5f, null);
			case "baku_baku_no_mi" -> new Look(MoveStyle.CLAW, 0xFFFFFFFF, 0xFFD04040, 1.0f, null);
			case "sabi_sabi_no_mi" -> new Look(MoveStyle.SLASH, 0xFFE8A878, 0xFF8A4020, 1.1f, null);
			case "horo_horo_no_mi" -> new Look(MoveStyle.ORB, 0xFFF4F4FF, 0xFFB0B8E0, 1.0f, ParticleTypes.SOUL);
			case "beta_beta_no_mi" -> new Look(MoveStyle.ORB, 0xFFE8F4A0, 0xFF8A9A30, 1.1f, ParticleTypes.ITEM_SLIME);
			case "awa_awa_no_mi", "woshu_woshu_no_mi" -> new Look(MoveStyle.ORB, 0xFFFFFFFF, 0xFFB8E8FF, 0.9f, null);
			default -> null;
		};
	}

	/** A stretchy rubber arm reaching from your shoulder to a point. Black if Armament Haki is on. */
	public static void arm(LivingEntity user, ServerLevel level, Vec3 end, boolean left) {
		com.onepiecemod.anim.CombatAnims.play(user, left ? com.onepiecemod.anim.Anim.PUNCH_LEFT : com.onepiecemod.anim.Anim.PUNCH);
		boolean haki = HakiPowers.hasArmamentActive(user);
		Vec3 start = user.position().add(0, user.getBbHeight() * 0.78, 0);
		spawn(level, MoveStyle.ARM, start, end.subtract(start), haki ? HAKI : SKIN, haki ? HAKI_OUT : SKIN_OUT,
				left ? -1.0f : 1.0f, 11, user, null);
	}

	/** A burst all around you: a shockwave ring, plus a shape that fits the element. */
	public static void area(LivingEntity user, ServerLevel level, DevilFruit fruit, ParticleOptions particle, double radius) {
		com.onepiecemod.anim.CombatAnims.play(user, com.onepiecemod.anim.Anim.GROUND_SLAM);
		int[] c = colors(fruit, particle);
		Vec3 feet = user.position().add(0, 0.1, 0);
		float r = (float) radius;
		spawn(level, MoveStyle.RING, feet, new Vec3(r, 0, 0), c[0], c[1], 1.0f, 14, null, null);

		if (particle == ParticleTypes.SNOWFLAKE) {
			spawn(level, MoveStyle.SPIKES, feet, new Vec3(r, 0, 0), c[0], c[1], 1.0f, 40, null, null);
		} else if (particle == ParticleTypes.HAPPY_VILLAGER) {
			spawn(level, MoveStyle.SPIKES, feet, new Vec3(r, 0, 0), PLANT, PLANT_OUT, 0.7f, 40, null, null);
		} else if (particle == ParticleTypes.WHITE_ASH || particle == ParticleTypes.LARGE_SMOKE || particle == ParticleTypes.CLOUD
				|| particle == ParticleTypes.WITCH) {
			spawn(level, MoveStyle.TORNADO, feet, new Vec3(0, Math.max(4, r * 0.7), 0), c[0], c[1], r * 0.5f, 36, user, null);
		} else if (particle == ParticleTypes.FLAME || particle == ParticleTypes.LAVA || particle == ParticleTypes.SOUL_FIRE_FLAME) {
			ring(level, feet, r * 0.7, 6, MoveStyle.PILLAR, c[0], c[1], 0.8f, 3.5f, 24, particle);
		} else if (particle == ParticleTypes.ELECTRIC_SPARK) {
			for (int i = 0; i < 4; i++) {
				double angle = i * Math.PI / 2 + level.getRandom().nextDouble();
				Vec3 out = new Vec3(Math.cos(angle) * r, 0.5, Math.sin(angle) * r);
				spawn(level, MoveStyle.BOLT, user.position().add(0, 1, 0), out, SPARK, SPARK_OUT, 0.5f, 8, null, null);
			}
		} else if (particle == ParticleTypes.EXPLOSION || particle == ParticleTypes.EXPLOSION_EMITTER) {
			spawn(level, MoveStyle.BURST, user.position().add(0, 0.6, 0), new Vec3(Math.min(3.5, r * 0.5), 0, 0), 0xFFFFF4C0, 0xFF5A4A40, 1.4f, 18, null, null);
		} else if (particle == ParticleTypes.NOTE) {
			// Sound rolling out in rings, one beat after another.
			for (int i = 0; i < 3; i++) {
				spawn(level, MoveStyle.RING, feet.add(0, 0.6 * i, 0), new Vec3(r * (0.6 + 0.2 * i), 0, 0), c[0], c[1], 0.7f, 14 + i * 5, null, null);
			}
			spawn(level, MoveStyle.WAVES, user.position().add(0, 1, 0), new Vec3(0, 4, 0), 0xFFFFF0FF, 0xFF8A50E0, 1.2f, 18, null, null);
		} else if (fruit != null && fruit.id().equals("ori_ori_no_mi")) {
			spawn(level, MoveStyle.WEB, feet, new Vec3(0, r, 0), 0xFFD8D8E0, 0xFF606070, 1.2f, 40, null, null);
		} else {
			float sphere = particle == ParticleTypes.SQUID_INK ? r * 0.9f : r * 0.7f;
			spawn(level, MoveStyle.SPHERE, user.position().add(0, 1, 0), Vec3.ZERO, c[0], c[1], sphere, 14, null, null);
		}
	}

	/** A ring rolling out from you, once a second while an awakened form hurts everything nearby. */
	public static void pulse(LivingEntity user, ServerLevel level, ParticleOptions particle, double radius) {
		int[] c = colors(null, particle);
		spawn(level, MoveStyle.RING, user.position().add(0, 0.1, 0), new Vec3(radius, 0, 0), c[0], c[1], 0.8f, 16, null, null);
	}

	/** A glow around you for a power-up. It follows you around for a moment. */
	public static void aura(LivingEntity user, ServerLevel level, DevilFruit fruit, ParticleOptions particle) {
		com.onepiecemod.anim.CombatAnims.play(user, com.onepiecemod.anim.Anim.POWER_UP);
		int[] c = colors(fruit, particle);
		spawn(level, MoveStyle.SPHERE, user.position(), Vec3.ZERO, c[0], c[1], 1.6f, 16, user, null);
		spawn(level, MoveStyle.RING, user.position().add(0, 0.1, 0), new Vec3(2.5, 0, 0), c[0], c[1], 0.6f, 12, null, null);
		spawn(level, MoveStyle.HELIX, user.position(), new Vec3(0, user.getBbHeight() + 0.6, 0), c[0], c[1], 0.9f, 26, user, null);
		int[] skin = fruit != null ? shieldColors(fruit.id()) : null;
		if (skin != null) {
			shell(user, level, skin[0], skin[1]);
		}
	}

	/** Colors for fruits whose power-up hardens you or puts up a wall, or null for the rest. */
	private static int[] shieldColors(String id) {
		return switch (id) {
			case "bari_bari_no_mi" -> new int[]{0xFFF0FFFF, 0xFF7FE0FF};
			case "kira_kira_no_mi" -> new int[]{0xFFF0FFFF, 0xFF9CE8FF};
			case "shiro_shiro_no_mi", "ishi_ishi_no_mi" -> new int[]{0xFFE0E0E0, 0xFF707074};
			case "doru_doru_no_mi" -> new int[]{0xFFFFFFF4, 0xFFE0D0A8};
			case "bisu_bisu_no_mi" -> new int[]{0xFFF6D9A0, 0xFFB8803A};
			case "pero_pero_no_mi" -> new int[]{0xFFFFF0F6, 0xFFFF70B0};
			case "supa_supa_no_mi" -> new int[]{0xFFF0F4FF, 0xFF8090A8};
			default -> null;
		};
	}

	/** Six panels of hexagons standing in a ring around you, like a barrier box (or a hard shell of skin). */
	public static void shell(LivingEntity user, ServerLevel level, int color, int color2) {
		Vec3 middle = user.position().add(0, user.getBbHeight() * 0.5, 0);
		for (int i = 0; i < 6; i++) {
			double angle = i * Math.PI / 3 + user.getYRot() * Math.PI / 180;
			Vec3 out = new Vec3(Math.cos(angle), 0, Math.sin(angle));
			spawn(level, MoveStyle.SHIELD, middle.add(out.scale(1.3)), out, color, color2, 1.1f, 22 + i, null, null);
		}
	}

	/** A healing move: green ribbons spiraling up, a soft glow and a ring. */
	public static void heal(LivingEntity user, ServerLevel level, int color, int color2) {
		com.onepiecemod.anim.CombatAnims.play(user, com.onepiecemod.anim.Anim.POWER_UP);
		spawn(level, MoveStyle.HELIX, user.position(), new Vec3(0, user.getBbHeight() + 0.8, 0), color, color2, 1.0f, 30, user, null);
		spawn(level, MoveStyle.SPHERE, user.position(), Vec3.ZERO, color, color2, 1.3f, 18, user, null);
		spawn(level, MoveStyle.RING, user.position().add(0, 0.1, 0), new Vec3(3, 0, 0), color, color2, 0.5f, 16, null, null);
	}

	/** A door (or ripple) opening in front of you as you step through a wall. */
	public static void door(LivingEntity user, ServerLevel level, int color, int color2) {
		Vec3 dir = user.getLookAngle().multiply(1, 0, 1);
		dir = dir.lengthSqr() < 1.0e-4 ? new Vec3(0, 0, 1) : dir.normalize();
		spawn(level, MoveStyle.GATE, user.position().add(0, 1, 0).add(dir.scale(0.8)), dir.scale(1.1), color, color2, 1.0f, 16, null, null);
	}

	/** A Zoan transformation: a big burst in the fruit's colors, and a swirl of energy. */
	public static void transform(LivingEntity user, ServerLevel level, DevilFruit fruit) {
		com.onepiecemod.anim.CombatAnims.play(user, com.onepiecemod.anim.Anim.POWER_UP);
		int a = opaque(fruit != null ? fruit.accent() : 0xFFFFFF);
		int b = opaque(fruit != null ? fruit.color() : 0xC0C0C0);
		spawn(level, MoveStyle.SPHERE, user.position().add(0, 1, 0), Vec3.ZERO, a, b, 3.0f, 14, null, null);
		spawn(level, MoveStyle.RING, user.position().add(0, 0.1, 0), new Vec3(5, 0, 0), a, b, 1.2f, 16, null, null);
		spawn(level, MoveStyle.TORNADO, user.position(), new Vec3(0, 3.2, 0), a, b, 1.3f, 20, user, null);
	}

	/** A trail of light from where you were to where you ended up (teleports and blinks). */
	public static void trail(ServerLevel level, Vec3 from, Vec3 to, DevilFruit fruit) {
		int a = fruit != null ? opaque(fruit.accent()) : LIGHT;
		int b = fruit != null ? opaque(fruit.color()) : LIGHT_OUT;
		Vec3 lift = new Vec3(0, 1, 0);
		spawn(level, MoveStyle.BEAM, from.add(lift), to.subtract(from), a, b, 0.5f, 8, null, null);
		// A small portal where you vanish and another where you come out.
		Vec3 dir = to.subtract(from);
		dir = dir.lengthSqr() < 1.0e-4 ? new Vec3(0, 0, 1) : dir.normalize();
		spawn(level, MoveStyle.GATE, from.add(lift), dir.scale(0.9), a, b, 0.8f, 12, null, null);
		spawn(level, MoveStyle.GATE, to.add(lift), dir.scale(0.9), a, b, 0.8f, 14, null, null);
	}

	/** A bolt of lightning crashing down on a spot. */
	public static void bolt(ServerLevel level, Vec3 at, float size) {
		Vec3 top = at.add(level.getRandom().nextDouble() * 4 - 2, 22, level.getRandom().nextDouble() * 4 - 2);
		spawn(level, MoveStyle.BOLT, top, at.subtract(top), SPARK, SPARK_OUT, size, 9, null, null);
		spawn(level, MoveStyle.RING, at.add(0, 0.1, 0), new Vec3(3 * size, 0, 0), SPARK, SPARK_OUT, 0.6f, 10, null, null);
	}

	/** A ball of something (like magma) falling from the sky onto a spot. */
	public static void meteor(ServerLevel level, Vec3 at, Look look) {
		Vec3 top = at.add(level.getRandom().nextDouble() * 6 - 3, 14, level.getRandom().nextDouble() * 6 - 3);
		spawn(level, look.style(), top, at.subtract(top), look.color(), look.color2(), look.size(), 16, null, look.trail());
	}

	/** Magma (or anything) raining down on random spots around a center. */
	public static void meteors(ServerLevel level, Vec3 center, double radius, int count, Look look) {
		for (int i = 0; i < count; i++) {
			double angle = level.getRandom().nextDouble() * Math.PI * 2;
			double dist = level.getRandom().nextDouble() * radius;
			meteor(level, center.add(Math.cos(angle) * dist, 0, Math.sin(angle) * dist), look);
		}
	}

	/** A flat shockwave plus a bubble, in two colors. */
	public static void shockwave(ServerLevel level, Vec3 feet, double radius, int color, int color2) {
		spawn(level, MoveStyle.RING, feet.add(0, 0.1, 0), new Vec3(radius, 0, 0), color, color2, 1.4f, 16, null, null);
		spawn(level, MoveStyle.SPHERE, feet.add(0, 1, 0), Vec3.ZERO, color, color2, (float) radius * 0.6f, 12, null, null);
	}

	/** Gura Gura: the air in front of you cracks like glass, and a shockwave rolls out. */
	public static void quake(LivingEntity user, ServerLevel level, double radius) {
		com.onepiecemod.anim.CombatAnims.play(user, com.onepiecemod.anim.Anim.PUNCH);
		Vec3 look = user.getLookAngle();
		spawn(level, MoveStyle.CRACK, user.getEyePosition().add(look.scale(2.2)), look.scale(4.5), QUAKE, QUAKE_OUT, 2.2f, 24, null, null);
		shockwave(level, user.position(), radius, QUAKE, QUAKE_OUT);
	}

	/** Yami Yami: a sphere of darkness that sucks everything toward you. */
	public static void blackHole(LivingEntity user, ServerLevel level, double radius) {
		com.onepiecemod.anim.CombatAnims.play(user, com.onepiecemod.anim.Anim.SUMMON);
		spawn(level, MoveStyle.SPHERE, user.position().add(0, 0.6, 0), Vec3.ZERO, DARK, DARK_OUT, (float) -radius, 30, null, null);
		spawn(level, MoveStyle.RING, user.position().add(0, 0.1, 0), new Vec3(radius, 0, 0), DARK, DARK_OUT, 0.8f, 18, null, null);
	}

	/** Ope Ope: the see-through blue dome of a ROOM. */
	public static void room(LivingEntity user, ServerLevel level, double radius) {
		com.onepiecemod.anim.CombatAnims.play(user, com.onepiecemod.anim.Anim.POINT);
		spawn(level, MoveStyle.SPHERE, user.position().add(0, 0.5, 0), Vec3.ZERO, ROOM, ROOM_OUT, (float) radius, 24, null, null);
	}

	/** Several shapes placed evenly in a circle around a center. */
	public static void ring(ServerLevel level, Vec3 center, double radius, int count, MoveStyle style,
			int color, int color2, float size, float height, int life, ParticleOptions trail) {
		for (int i = 0; i < count; i++) {
			double angle = i * Math.PI * 2 / count;
			Vec3 at = center.add(Math.cos(angle) * radius, 0, Math.sin(angle) * radius);
			spawn(level, style, at, new Vec3(0, height, 0), color, color2, size, life + i, null, trail);
		}
	}

	/** Any shape, centered on a spot, with explicit colors. Handy for one-off effects. */
	public static void at(ServerLevel level, MoveStyle style, Vec3 at, Vec3 reach, int color, int color2, float size, int life, Entity owner) {
		spawn(level, style, at, reach, color, color2, size, life, owner, null);
	}

	// ---- Picking a look automatically ----

	/** Chooses a shape and colors for a ranged move from its particle, its fruit's type and its range. */
	public static Look autoLook(DevilFruit fruit, ParticleOptions particle, double range) {
		int[] c = colors(fruit, particle);
		boolean zoan = fruit != null && fruit.type() == DevilFruit.Type.ZOAN;
		if (particle == ParticleTypes.FLAME) {
			return range > 8 ? new Look(MoveStyle.ORB, FIRE, FIRE_OUT, 1.2f, ParticleTypes.FLAME) : new Look(MoveStyle.FIST, FIRE, FIRE_OUT, 1.1f, ParticleTypes.FLAME);
		}
		if (particle == ParticleTypes.LAVA) {
			return MAGMA_FIST.sized(1.4f);
		}
		if (particle == ParticleTypes.SNOWFLAKE) {
			return zoan ? FROST_BREATH : ICE_SPEAR;
		}
		if (particle == ParticleTypes.END_ROD || particle == ParticleTypes.ENCHANT) {
			return new Look(MoveStyle.BEAM, c[0], c[1], 0.65f, null);
		}
		if (particle == ParticleTypes.ELECTRIC_SPARK) {
			return new Look(MoveStyle.BOLT, SPARK, SPARK_OUT, 0.7f, null);
		}
		if (particle == ParticleTypes.SWEEP_ATTACK) {
			return new Look(MoveStyle.SLASH, 0xFFFFFFFF, c[1], 1.0f, null);
		}
		if (particle == ParticleTypes.CRIT) {
			if (zoan) {
				return CLAWS;
			}
			if (range <= 8) {
				return new Look(MoveStyle.FIST, c[0], c[1], 0.9f, null);
			}
			return new Look(MoveStyle.BEAM, c[0], c[1], 0.2f, null);
		}
		if (particle == ParticleTypes.EXPLOSION) {
			return new Look(MoveStyle.ORB, 0xFFFFF0C0, 0xFFFF7A20, 1.3f, ParticleTypes.SMOKE);
		}
		if (particle == ParticleTypes.HAPPY_VILLAGER) {
			return ROOTS;
		}
		ParticleOptions trail = particle == ParticleTypes.WITCH || particle == ParticleTypes.SQUID_INK || particle == ParticleTypes.CLOUD
				|| particle == ParticleTypes.LARGE_SMOKE || particle == ParticleTypes.HEART || particle == ParticleTypes.NOTE
				|| particle == ParticleTypes.SOUL || particle == ParticleTypes.WHITE_ASH ? particle : null;
		return new Look(MoveStyle.ORB, c[0], c[1], 1.0f, trail);
	}

	/** Inner and outer colors for an element (picked from the particle), or else the fruit's own colors. */
	public static int[] colors(DevilFruit fruit, ParticleOptions particle) {
		if (particle == ParticleTypes.FLAME) return new int[]{FIRE, FIRE_OUT};
		if (particle == ParticleTypes.SOUL_FIRE_FLAME) return new int[]{BLUE_FIRE, BLUE_FIRE_OUT};
		if (particle == ParticleTypes.LAVA) return new int[]{MAGMA, MAGMA_OUT};
		if (particle == ParticleTypes.SNOWFLAKE) return new int[]{ICE, ICE_OUT};
		if (particle == ParticleTypes.ELECTRIC_SPARK) return new int[]{SPARK, SPARK_OUT};
		if (particle == ParticleTypes.SQUID_INK) return new int[]{DARK, DARK_OUT};
		if (particle == ParticleTypes.WITCH) return new int[]{POISON, POISON_OUT};
		if (particle == ParticleTypes.WHITE_ASH) return new int[]{SAND, SAND_OUT};
		if (particle == ParticleTypes.LARGE_SMOKE) return new int[]{SMOKE, SMOKE_OUT};
		if (particle == ParticleTypes.HEART) return new int[]{LOVE, LOVE_OUT};
		if (particle == ParticleTypes.HAPPY_VILLAGER) return new int[]{PLANT, 0xFF3C8A2A};
		if (particle == ParticleTypes.EXPLOSION || particle == ParticleTypes.EXPLOSION_EMITTER) return new int[]{0xFFFFF4D0, 0xFFFF8A30};
		if (fruit != null) {
			return new int[]{lighten(opaque(fruit.accent())), opaque(fruit.color())};
		}
		return new int[]{0xFFFFFFFF, 0xFFC0C0C0};
	}

	private static int opaque(int rgb) {
		return 0xFF000000 | rgb;
	}

	/** Mixes a color halfway toward white, so the bright middle of a shape stands out. */
	private static int lighten(int argb) {
		int r = (((argb >> 16) & 0xFF) + 255) / 2;
		int g = (((argb >> 8) & 0xFF) + 255) / 2;
		int b = ((argb & 0xFF) + 255) / 2;
		return 0xFF000000 | (r << 16) | (g << 8) | b;
	}
}
