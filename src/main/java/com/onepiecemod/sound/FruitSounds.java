package com.onepiecemod.sound;

import java.util.HashMap;
import java.util.Map;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;

import com.onepiecemod.power.DevilFruit;

/**
 * The extra sound each Devil Fruit move makes, on top of the move's normal sound: fire roars, ice crackles,
 * rubber stretches and Zoans roar. Fruits not listed here get a sound from their type.
 */
public class FruitSounds {
	private static final Map<String, SoundEvent> MOVE = new HashMap<>();
	/** Fruits whose Sneak+R move sounds different from their R move. */
	private static final Map<String, SoundEvent> SECONDARY = new HashMap<>();
	/** The sound where a move lands, by the move's sound: fire burns, ice cracks, blades cut. */
	private static final Map<SoundEvent, SoundEvent> HIT = new HashMap<>();

	public static final SoundEvent HIT_BURN = ModSounds.register("fruit_hit.burn");
	public static final SoundEvent HIT_FREEZE = ModSounds.register("fruit_hit.freeze");
	public static final SoundEvent HIT_SHOCK = ModSounds.register("fruit_hit.shock");
	public static final SoundEvent HIT_FLASH = ModSounds.register("fruit_hit.flash");
	public static final SoundEvent HIT_DARK = ModSounds.register("fruit_hit.dark");
	public static final SoundEvent HIT_BLUNT = ModSounds.register("fruit_hit.blunt");
	public static final SoundEvent HIT_CUT = ModSounds.register("fruit_hit.cut");
	public static final SoundEvent HIT_SPLAT = ModSounds.register("fruit_hit.splat");
	public static final SoundEvent HIT_THORN = ModSounds.register("fruit_hit.thorn");
	public static final SoundEvent HIT_DUST = ModSounds.register("fruit_hit.dust");
	public static final SoundEvent HIT_BITE = ModSounds.register("fruit_hit.bite");
	/** Gear 5 awakening: the drums of liberation. */
	public static final SoundEvent GEAR_FIVE = ModSounds.register("fruit_move.gear_five");
	public static final SoundEvent HEAL = ModSounds.register("fruit_move.heal");
	/** A Zoan user changing shape. */
	public static final SoundEvent ZOAN_SHIFT = ModSounds.register("fruit_move.zoan_shift");

	static {
		fruits(ModSounds.MOVE_FIRE, "mera_mera_no_mi", "fuku_fuku_no_mi", "netsu_netsu_no_mi", "tori_tori_no_mi_phoenix");
		fruits(ModSounds.MOVE_MAGMA, "magu_magu_no_mi");
		fruits(ModSounds.MOVE_ICE, "hie_hie_no_mi", "yuki_yuki_no_mi", "yomi_yomi_no_mi");
		fruits(ModSounds.MOVE_LIGHTNING, "goro_goro_no_mi");
		fruits(ModSounds.MOVE_LIGHT, "pika_pika_no_mi", "kira_kira_no_mi", "shiro_shiro_no_mi");
		fruits(ModSounds.MOVE_DARKNESS, "yami_yami_no_mi", "kage_kage_no_mi", "numa_numa_no_mi");
		fruits(ModSounds.MOVE_SMOKE, "moku_moku_no_mi", "gasu_gasu_no_mi");
		fruits(ModSounds.MOVE_SAND, "suna_suna_no_mi", "sabi_sabi_no_mi");
		fruits(ModSounds.MOVE_QUAKE, "gura_gura_no_mi", "hito_hito_no_mi_daibutsu");
		fruits(ModSounds.MOVE_RUBBER, "gomu_gomu_no_mi", "bane_bane_no_mi", "mochi_mochi_no_mi", "beta_beta_no_mi");
		fruits(ModSounds.MOVE_BLADE, "supa_supa_no_mi", "hira_hira_no_mi", "choki_choki_no_mi", "buki_buki_no_mi",
				"bara_bara_no_mi", "ori_ori_no_mi", "mato_mato_no_mi");
		fruits(ModSounds.MOVE_GRAVITY, "zushi_zushi_no_mi", "kilo_kilo_no_mi", "jiki_jiki_no_mi", "ton_ton_no_mi",
				"nikyu_nikyu_no_mi");
		fruits(ModSounds.MOVE_PLANT, "mori_mori_no_mi", "hana_hana_no_mi");
		fruits(ModSounds.MOVE_POISON, "doku_doku_no_mi");
		fruits(ModSounds.MOVE_EXPLOSION, "bomu_bomu_no_mi", "pamu_pamu_no_mi", "baku_baku_no_mi");
		fruits(ModSounds.MOVE_BUBBLE, "awa_awa_no_mi", "fuwa_fuwa_no_mi", "woshu_woshu_no_mi", "bisu_bisu_no_mi",
				"chiyu_chiyu_no_mi", "horu_horu_no_mi", "sui_sui_no_mi",
				"guru_guru_no_mi");
		fruits(ModSounds.MOVE_WARP, "ope_ope_no_mi", "wapu_wapu_no_mi",
				"mane_mane_no_mi", "nomi_nomi_no_mi", "memo_memo_no_mi", "toshi_toshi_no_mi");
		fruits(ModSounds.MOVE_STRING, "ito_ito_no_mi", "nui_nui_no_mi", "fude_fude_no_mi", "shiku_shiku_no_mi");
		fruits(ModSounds.MOVE_CURSE, "horo_horo_no_mi", "wara_wara_no_mi", "soru_soru_no_mi", "mero_mero_no_mi",
				"hobi_hobi_no_mi", "kibi_kibi_no_mi", "ato_ato_no_mi");
		fruits(ModSounds.MOVE_DRAGON_ROAR, "uo_uo_no_mi_seiryu", "hebi_hebi_no_mi_yamata_no_orochi",
				"ryu_ryu_no_mi_spinosaurus", "ryu_ryu_no_mi_brachiosaurus", "ryu_ryu_no_mi_allosaurus",
				"ryu_ryu_no_mi_nidhogg");
		fruits(ModSounds.MOVE_BIRD_CRY, "ryu_ryu_no_mi_pteranodon", "tori_tori_no_mi_falcon");
		fruits(ModSounds.MOVE_HOWL, "inu_inu_no_mi_wolf", "inu_inu_no_mi_jackal", "inu_inu_no_mi_kyubi_no_kitsune",
				"inu_inu_no_mi_okuchi_no_makami");
		fruits(ModSounds.MOVE_SNARL, "neko_neko_no_mi_leopard", "neko_neko_no_mi_saber_tiger");
		fruits(ModSounds.MOVE_SNAKE, "hebi_hebi_no_mi_anaconda", "hebi_hebi_no_mi_king_cobra");
		fruits(ModSounds.MOVE_NEIGH, "uma_uma_no_mi");
		fruits(ModSounds.MOVE_BELLOW, "ushi_ushi_no_mi_bison", "ushi_ushi_no_mi_giraffe");
		fruits(ModSounds.MOVE_TRUMPET, "zou_zou_no_mi", "zou_zou_no_mi_mammoth");
		fruits(ModSounds.MOVE_SPIDER, "kumo_kumo_no_mi_rosamygale_grauvogeli");
		fruits(ModSounds.MOVE_STOMP, "ryu_ryu_no_mi_triceratops", "ryu_ryu_no_mi_pachycephalosaurus");
		fruits(ModSounds.MOVE_DIG, "mogu_mogu_no_mi");
		fruits(ModSounds.MOVE_BUBBLE, "sara_sara_no_mi_axolotl");
		fruits(ModSounds.MOVE_BARRIER, "bari_bari_no_mi");
		fruits(ModSounds.MOVE_HUSH, "nagi_nagi_no_mi");
		fruits(ModSounds.MOVE_SOUND_WAVE, "oto_oto_no_mi");
		fruits(ModSounds.MOVE_CLOCK, "toki_toki_no_mi", "modo_modo_no_mi");
		fruits(ModSounds.MOVE_MIRROR, "mira_mira_no_mi");
		fruits(ModSounds.MOVE_DOOR, "doa_doa_no_mi");
		fruits(ModSounds.MOVE_HARDEN, "doru_doru_no_mi", "pero_pero_no_mi", "ishi_ishi_no_mi");
		fruits(ModSounds.MOVE_SLIP, "sube_sube_no_mi");
		fruits(ModSounds.MOVE_HEAVY_BLOW, "riki_riki_no_mi");
		fruits(ModSounds.MOVE_PHOTON, "noro_noro_no_mi");
		fruits(ModSounds.MOVE_BEAST_ROAR, "hito_hito_no_mi");
		// 2026-11-05: these used to share a group sound; each now has its own (put after the groups, so they win).
		fruits(ModSounds.MOVE_WASH, "woshu_woshu_no_mi");
		fruits(ModSounds.MOVE_FLOAT, "fuwa_fuwa_no_mi");
		fruits(ModSounds.MOVE_HORMONE, "horu_horu_no_mi");
		fruits(ModSounds.MOVE_SWIM, "sui_sui_no_mi");
		fruits(ModSounds.MOVE_SPIN, "guru_guru_no_mi");
		fruits(ModSounds.MOVE_CRUNCH, "bisu_bisu_no_mi");
		fruits(ModSounds.MOVE_COPY, "mane_mane_no_mi");
		fruits(ModSounds.MOVE_MEMORY, "memo_memo_no_mi");
		fruits(ModSounds.MOVE_TOY, "hobi_hobi_no_mi");
		fruits(ModSounds.MOVE_LOVE, "mero_mero_no_mi");
		fruits(ModSounds.MOVE_GHOST, "horo_horo_no_mi");
		fruits(ModSounds.MOVE_STRAW, "wara_wara_no_mi");
		fruits(ModSounds.MOVE_ROOM, "ope_ope_no_mi");
		fruits(ModSounds.MOVE_STICKY, "mochi_mochi_no_mi");
		fruits(ModSounds.MOVE_SOUL, "yomi_yomi_no_mi");
		fruits(ModSounds.MOVE_GAS, "gasu_gasu_no_mi");
		fruits(ModSounds.MOVE_BLOOM, "hana_hana_no_mi");
		fruits(ModSounds.MOVE_MAGNET, "jiki_jiki_no_mi");
		fruits(BossSounds.PAW, "nikyu_nikyu_no_mi"); // Kuma's paw pop, same as his boss fight
		MOVE.put("chiyu_chiyu_no_mi", HEAL);
		SECONDARY.put("soru_soru_no_mi", ModSounds.MOVE_LIGHTNING); // Zeus
		SECONDARY.put("tori_tori_no_mi_phoenix", ModSounds.MOVE_BIRD_CRY);
		SECONDARY.put("yami_yami_no_mi", ModSounds.MOVE_GRAVITY); // Black Hole
		SECONDARY.put("ope_ope_no_mi", HEAL); // Scan and Heal
		SECONDARY.put("mochi_mochi_no_mi", ModSounds.MOVE_HARDEN); // Mochi Armor
		SECONDARY.put("bisu_bisu_no_mi", ModSounds.MOVE_HARDEN); // Biscuit Armor
		SECONDARY.put("horo_horo_no_mi", ModSounds.MOVE_CURSE); // Ghost Rap
		SECONDARY.put("jiki_jiki_no_mi", ModSounds.MOVE_GRAVITY); // Magnetic Pull

		hits(HIT_BURN, ModSounds.MOVE_FIRE, ModSounds.MOVE_MAGMA, ModSounds.MOVE_EXPLOSION);
		hits(HIT_FREEZE, ModSounds.MOVE_ICE);
		hits(HIT_SHOCK, ModSounds.MOVE_LIGHTNING);
		hits(HIT_FLASH, ModSounds.MOVE_LIGHT, ModSounds.MOVE_WARP);
		hits(HIT_DARK, ModSounds.MOVE_DARKNESS, ModSounds.MOVE_CURSE, ModSounds.MOVE_GRAVITY);
		hits(HIT_CUT, ModSounds.MOVE_BLADE, ModSounds.MOVE_STRING);
		hits(HIT_SPLAT, ModSounds.MOVE_POISON, ModSounds.MOVE_BUBBLE);
		hits(HIT_THORN, ModSounds.MOVE_PLANT);
		hits(HIT_DUST, ModSounds.MOVE_SMOKE, ModSounds.MOVE_SAND);
		hits(HIT_BITE, ModSounds.MOVE_BEAST_ROAR, ModSounds.MOVE_DRAGON_ROAR, ModSounds.MOVE_BIRD_CRY, ModSounds.MOVE_HOWL,
				ModSounds.MOVE_SNARL, ModSounds.MOVE_SNAKE, ModSounds.MOVE_SPIDER, ModSounds.MOVE_NEIGH, ModSounds.MOVE_BELLOW);
		hits(HIT_DUST, ModSounds.MOVE_DIG);
		hits(HIT_FLASH, ModSounds.MOVE_CLOCK, ModSounds.MOVE_MIRROR, ModSounds.MOVE_DOOR, ModSounds.MOVE_PHOTON);
		hits(HIT_CUT, ModSounds.MOVE_SLIP);
		hits(HIT_SPLAT, ModSounds.MOVE_WASH, ModSounds.MOVE_HORMONE, ModSounds.MOVE_SWIM, ModSounds.MOVE_STICKY);
		hits(HIT_FLASH, ModSounds.MOVE_COPY, ModSounds.MOVE_MEMORY, ModSounds.MOVE_LOVE, ModSounds.MOVE_FLOAT);
		hits(HIT_DARK, ModSounds.MOVE_GHOST, ModSounds.MOVE_STRAW);
		hits(HIT_CUT, ModSounds.MOVE_ROOM);
		hits(HIT_FREEZE, ModSounds.MOVE_SOUL);
		hits(HIT_DUST, ModSounds.MOVE_GAS);
		hits(HIT_THORN, ModSounds.MOVE_BLOOM);
		// Everything else (rubber, quake, impact...) lands with a heavy blunt hit.
	}

	private static void hits(SoundEvent hit, SoundEvent... moves) {
		for (SoundEvent move : moves) {
			HIT.put(move, hit);
		}
	}

	private static void fruits(SoundEvent sound, String... ids) {
		for (String id : ids) {
			MOVE.put(id, sound);
		}
	}

	public static SoundEvent forMove(DevilFruit fruit, boolean secondary) {
		SoundEvent sound = secondary ? SECONDARY.get(fruit.id()) : null;
		if (sound == null) {
			sound = MOVE.get(fruit.id());
		}
		if (sound == null) {
			sound = switch (fruit.type()) {
				case ZOAN -> ModSounds.MOVE_BEAST_ROAR;
				case LOGIA -> ModSounds.MOVE_SMOKE;
				case PARAMECIA -> ModSounds.MOVE_IMPACT;
			};
		}
		return sound;
	}

	/** Loads the class at startup so its sounds register before the registries freeze (lazy loading crashed the first hit). */
	static void initialize() {
	}

	/** Called by FruitAbilities the first time a move hits something: the sound of it landing. */
	public static void playHit(LivingEntity target, DevilFruit fruit) {
		SoundEvent hit = HIT.getOrDefault(forMove(fruit, false), HIT_BLUNT);
		float pitch = 0.9f + target.getRandom().nextFloat() * 0.2f;
		target.level().playSound(null, target.getX(), target.getY(), target.getZ(), hit, SoundSource.PLAYERS, 1.0f, pitch);
	}

	/** The sound of a fruit's awakened form: one per fruit type. Gear 5 gets its drums. */
	public static SoundEvent awakening(DevilFruit fruit) {
		if (fruit.id().equals("gomu_gomu_no_mi")) {
			return GEAR_FIVE;
		}
		return switch (fruit.type()) {
			case LOGIA -> ModSounds.AWAKEN_LOGIA;
			case ZOAN -> ModSounds.AWAKEN_ZOAN;
			case PARAMECIA -> ModSounds.AWAKEN_PARAMECIA;
		};
	}

	/** Called by FruitAbilities each time a move goes off. */
	public static void playMove(ServerPlayer player, DevilFruit fruit, boolean secondary) {
		float pitch = 0.92f + player.getRandom().nextFloat() * 0.16f;
		player.level().playSound(null, player.getX(), player.getY(), player.getZ(), forMove(fruit, secondary),
				SoundSource.PLAYERS, 0.9f, pitch);
	}
}
