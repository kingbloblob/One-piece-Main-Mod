package com.onepiecemod.power;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.onepiecemod.power.DevilFruit.Type;

/**
 * The list of every Devil Fruit in the mod. To add a fruit, add a line here, give it moves in
 * FruitAbilities, and add a texture and name (see the README).
 */
public class DevilFruits {
	public static final List<DevilFruit> ALL = List.of(
			// Paramecia
			new DevilFruit("gomu_gomu_no_mi", "Gomu Gomu no Mi", Type.PARAMECIA, 0x9646C8, 0xC88CF0, "Gomu Gomu no Pistol", "Gomu Gomu no Rocket"),
			new DevilFruit("ope_ope_no_mi", "Ope Ope no Mi", Type.PARAMECIA, 0xE0507A, 0xF5D04A, "Shambles", "Scan and Heal"),
			new DevilFruit("bara_bara_no_mi", "Bara Bara no Mi", Type.PARAMECIA, 0xD03A2E, 0xF0C040, "Bara Bara Cannon", "Bara Bara Escape"),
			new DevilFruit("gura_gura_no_mi", "Gura Gura no Mi", Type.PARAMECIA, 0xE8E8F0, 0x5A8CD8, "Quake Punch", "Shockwave"),
			new DevilFruit("soru_soru_no_mi", "Soru Soru no Mi", Type.PARAMECIA, 0xE070B0, 0x8A3CA0, "Soul Pocus", "Zeus Strike"),
			new DevilFruit("jiki_jiki_no_mi", "Jiki Jiki no Mi", Type.PARAMECIA, 0xB03030, 0x9098A0, "Repel", "Magnetic Pull"),
			new DevilFruit("wara_wara_no_mi", "Wara Wara no Mi", Type.PARAMECIA, 0xD8B850, 0x8A6A28, "Straw Man Curse", "Straw Body"),
			new DevilFruit("toshi_toshi_no_mi", "Toshi Toshi no Mi", Type.PARAMECIA, 0xF0A0C0, 0xFFF0F5, "Age Down", "Grown-Up Form"),
			new DevilFruit("ito_ito_no_mi", "Ito Ito no Mi", Type.PARAMECIA, 0xE860A8, 0xF8F8F8, "Parasite", "Sky Walk"),
			new DevilFruit("mero_mero_no_mi", "Mero Mero no Mi", Type.PARAMECIA, 0xF06080, 0xC01848, "Slave Arrow", "Perfume Femur"),
			new DevilFruit("nikyu_nikyu_no_mi", "Nikyu Nikyu no Mi", Type.PARAMECIA, 0xC8C8D0, 0xF0A0B0, "Pad Ho", "Where Would You Like to Go?"),
			new DevilFruit("kage_kage_no_mi", "Kage Kage no Mi", Type.PARAMECIA, 0x403848, 0x9080A0, "Shadow Steal", "Shadow Asgard"),
			new DevilFruit("zushi_zushi_no_mi", "Zushi Zushi no Mi", Type.PARAMECIA, 0x6A3C9A, 0x2A1840, "Gravity Blade", "Gravity Field"),
			new DevilFruit("mochi_mochi_no_mi", "Mochi Mochi no Mi", Type.PARAMECIA, 0xF0E8D8, 0xC8A878, "Mochi Bind", "Mochi Armor"),
			new DevilFruit("fuku_fuku_no_mi", "Fuku Fuku no Mi", Type.PARAMECIA, 0x3C6CB0, 0xE8C060, "Fox Fire Slash", "Dress Up"),
			new DevilFruit("nomi_nomi_no_mi", "Nomi Nomi no Mi", Type.PARAMECIA, 0xF0A8B8, 0xB06070, "Scan", "Instant Learning"),
			new DevilFruit("hana_hana_no_mi", "Hana Hana no Mi", Type.PARAMECIA, 0xB86CD0, 0xF0A0D8, "Clutch", "Mil Fleur"),
			new DevilFruit("yomi_yomi_no_mi", "Yomi Yomi no Mi", Type.PARAMECIA, 0x282830, 0xE8E8E8, "Soul King's Chill", "Soul Out"),
			new DevilFruit("horo_horo_no_mi", "Horo Horo no Mi", Type.PARAMECIA, 0xFFB0D8, 0x303030, "Negative Hollow", "Ghost Rap"),
			new DevilFruit("bisu_bisu_no_mi", "Bisu Bisu no Mi", Type.PARAMECIA, 0xD8A050, 0xF0D090, "Biscuit Punch", "Biscuit Armor"),
			new DevilFruit("pero_pero_no_mi", "Pero Pero no Mi", Type.PARAMECIA, 0xF06090, 0xF8F8F8, "Candy Trap", "Candy Wall"),
			new DevilFruit("mira_mira_no_mi", "Mira Mira no Mi", Type.PARAMECIA, 0xC0E0F0, 0xF8F8F8, "Mirror World", "Mirror Copy"),
			new DevilFruit("netsu_netsu_no_mi", "Netsu Netsu no Mi", Type.PARAMECIA, 0xF05020, 0xF8A040, "Heat Fist", "Heat Wave"),
			new DevilFruit("bari_bari_no_mi", "Bari Bari no Mi", Type.PARAMECIA, 0x60C0F0, 0xF8F8FF, "Barrier Bash", "Barrier"),
			new DevilFruit("hobi_hobi_no_mi", "Hobi Hobi no Mi", Type.PARAMECIA, 0xF0A040, 0x80C060, "Toy Touch", "Forgotten"),
			new DevilFruit("doru_doru_no_mi", "Doru Doru no Mi", Type.PARAMECIA, 0xF8F0D8, 0xC0B090, "Candle Lock", "Candle Armor"),
			new DevilFruit("bomu_bomu_no_mi", "Bomu Bomu no Mi", Type.PARAMECIA, 0x404040, 0xF0A020, "Nose Fancy Cannon", "Kick Bomb"),
			new DevilFruit("kilo_kilo_no_mi", "Kilo Kilo no Mi", Type.PARAMECIA, 0xF0E040, 0xF070A0, "10,000 Kilo Press", "1 Kilo Float"),
			new DevilFruit("supa_supa_no_mi", "Supa Supa no Mi", Type.PARAMECIA, 0xA0A8B0, 0xE0E8F0, "Spiral Hollow", "Steel Body"),
			new DevilFruit("mane_mane_no_mi", "Mane Mane no Mi", Type.PARAMECIA, 0xF0F0F0, 0xE060A0, "Okama Kenpo Kick", "Memoir"),
			new DevilFruit("noro_noro_no_mi", "Noro Noro no Mi", Type.PARAMECIA, 0xF0D060, 0xF08030, "Noro Noro Beam", "Noroma Mirror"),
			new DevilFruit("doa_doa_no_mi", "Doa Doa no Mi", Type.PARAMECIA, 0xA07040, 0xE0C080, "Door", "Air Door"),
			new DevilFruit("awa_awa_no_mi", "Awa Awa no Mi", Type.PARAMECIA, 0xF0F8FF, 0x80C0F0, "Golden Rush", "Soap Sheep"),
			new DevilFruit("fuwa_fuwa_no_mi", "Fuwa Fuwa no Mi", Type.PARAMECIA, 0x80C0E0, 0xF8F8F8, "Float", "Lion's Flight"),
			new DevilFruit("ishi_ishi_no_mi", "Ishi Ishi no Mi", Type.PARAMECIA, 0x909090, 0x606060, "Stone Fist", "Stone Merge"),
			new DevilFruit("hira_hira_no_mi", "Hira Hira no Mi", Type.PARAMECIA, 0xE0D0A0, 0xC04040, "Flag Cape Slash", "Flutter Shield"),
			new DevilFruit("nagi_nagi_no_mi", "Nagi Nagi no Mi", Type.PARAMECIA, 0xF8F0F8, 0x202020, "Silent Strike", "Calm"),
			new DevilFruit("horu_horu_no_mi", "Horu Horu no Mi", Type.PARAMECIA, 0xE06080, 0x8040A0, "Death Wink", "Tension Hormones"),
			new DevilFruit("doku_doku_no_mi", "Doku Doku no Mi", Type.PARAMECIA, 0x6A2A8A, 0x40C040, "Hydra", "Venom Demon"),
			new DevilFruit("bane_bane_no_mi", "Bane Bane no Mi", Type.PARAMECIA, 0xD0A040, 0x707070, "Spring Hopper", "Spring Snipe"),
			new DevilFruit("kira_kira_no_mi", "Kira Kira no Mi", Type.PARAMECIA, 0xE0F8FF, 0xA0C8E0, "Diamond Fist", "Diamond Body"),
			new DevilFruit("woshu_woshu_no_mi", "Woshu Woshu no Mi", Type.PARAMECIA, 0xD0E8F8, 0xF8F8F8, "Wash", "Hang to Dry"),
			new DevilFruit("oto_oto_no_mi", "Oto Oto no Mi", Type.PARAMECIA, 0xF0A060, 0x603020, "Sound Slash", "Battle Song"),
			new DevilFruit("shiro_shiro_no_mi", "Shiro Shiro no Mi", Type.PARAMECIA, 0x808070, 0xC0A060, "Cannon Barrage", "Big Father"),
			new DevilFruit("baku_baku_no_mi", "Baku Baku no Mi", Type.PARAMECIA, 0xC0A0D0, 0x505050, "Munch", "Feast"),
			new DevilFruit("choki_choki_no_mi", "Choki Choki no Mi", Type.PARAMECIA, 0x4060C0, 0xF0F0F0, "Scissor Cut", "Paper Wall"),
			new DevilFruit("fude_fude_no_mi", "Fude Fude no Mi", Type.PARAMECIA, 0xF0E8D0, 0x202020, "Ink Strike", "Living Drawing"),
			new DevilFruit("kibi_kibi_no_mi", "Kibi Kibi no Mi", Type.PARAMECIA, 0xF0D0A0, 0xC08040, "Kibi Dango", "Snack Time"),
			new DevilFruit("toki_toki_no_mi", "Toki Toki no Mi", Type.PARAMECIA, 0xF0C0E0, 0x8080F0, "Time Jump", "Speed of Time"),
			new DevilFruit("memo_memo_no_mi", "Memo Memo no Mi", Type.PARAMECIA, 0xE8A060, 0xF070A0, "Memory Edit", "Forget Me"),
			new DevilFruit("riki_riki_no_mi", "Riki Riki no Mi", Type.PARAMECIA, 0xB06030, 0xF0C060, "Champion Punch", "Superhuman Strength"),
			new DevilFruit("wapu_wapu_no_mi", "Wapu Wapu no Mi", Type.PARAMECIA, 0x60A0F0, 0xF0F0F0, "Warp", "Warp Away"),
			new DevilFruit("shiku_shiku_no_mi", "Shiku Shiku no Mi", Type.PARAMECIA, 0x709050, 0xF0F0E0, "Disease", "Cure"),
			new DevilFruit("beta_beta_no_mi", "Beta Beta no Mi", Type.PARAMECIA, 0x80A040, 0xC0E080, "Beta Shot", "Burning Mucus"),
			new DevilFruit("pamu_pamu_no_mi", "Pamu Pamu no Mi", Type.PARAMECIA, 0xD04040, 0xF0F0F0, "Burst", "Rupture"),
			new DevilFruit("sui_sui_no_mi", "Sui Sui no Mi", Type.PARAMECIA, 0x80C0F0, 0xF080A0, "Ground Swim", "Dive"),
			new DevilFruit("buki_buki_no_mi", "Buki Buki no Mi", Type.PARAMECIA, 0xE0E0E0, 0xE04070, "Arm Gun", "Missile"),
			new DevilFruit("guru_guru_no_mi", "Guru Guru no Mi", Type.PARAMECIA, 0xE0A040, 0x606060, "Spin Attack", "Propeller Flight"),
			new DevilFruit("modo_modo_no_mi", "Modo Modo no Mi", Type.PARAMECIA, 0xA0C8F0, 0xF0F0F0, "Return", "Rewind"),
			new DevilFruit("sube_sube_no_mi", "Sube Sube no Mi", Type.PARAMECIA, 0xF0E0F0, 0xF0A0C0, "Slip Punch", "Slippery Skin"),
			new DevilFruit("ori_ori_no_mi", "Ori Ori no Mi", Type.PARAMECIA, 0xA060A0, 0x505050, "Iron Bars", "Black Cage"),
			new DevilFruit("chiyu_chiyu_no_mi", "Chiyu Chiyu no Mi", Type.PARAMECIA, 0xF8D0E0, 0xF0F0A0, "Healing Tears", "Healing Rain"),
			new DevilFruit("nui_nui_no_mi", "Nui Nui no Mi", Type.PARAMECIA, 0xF0C060, 0x70A040, "Stitch", "Stitch Wounds"),
			new DevilFruit("ton_ton_no_mi", "Ton Ton no Mi", Type.PARAMECIA, 0x8A6040, 0x404040, "Ton Drop", "Heavy Body"),
			new DevilFruit("ato_ato_no_mi", "Ato Ato no Mi", Type.PARAMECIA, 0xF070D0, 0x60D0F0, "Art Curse", "Masterpiece"),
			new DevilFruit("sabi_sabi_no_mi", "Sabi Sabi no Mi", Type.PARAMECIA, 0xA05030, 0x707070, "Rust Touch", "Rust Cloud"),
			new DevilFruit("mato_mato_no_mi", "Mato Mato no Mi", Type.PARAMECIA, 0xFFC0A0, 0x402060, "Homing Throw", "Mark"),

			// Logia
			new DevilFruit("mera_mera_no_mi", "Mera Mera no Mi", Type.LOGIA, 0xF07820, 0xF8D040, "Hiken (Fire Fist)", "Flame Ring"),
			new DevilFruit("hie_hie_no_mi", "Hie Hie no Mi", Type.LOGIA, 0x90D0F0, 0xF0F8FF, "Ice Saber", "Ice Age"),
			new DevilFruit("yami_yami_no_mi", "Yami Yami no Mi", Type.LOGIA, 0x302040, 0x6A3C8A, "Kurouzu", "Black Hole"),
			new DevilFruit("suna_suna_no_mi", "Suna Suna no Mi", Type.LOGIA, 0xD8C080, 0xA88848, "Desert Spada", "Sables"),
			new DevilFruit("magu_magu_no_mi", "Magu Magu no Mi", Type.LOGIA, 0xB02010, 0xF08020, "Great Eruption", "Meteor Volcano"),
			new DevilFruit("pika_pika_no_mi", "Pika Pika no Mi", Type.LOGIA, 0xF8E040, 0xFFFFF0, "Light Speed", "Yasakani Beam"),
			new DevilFruit("mori_mori_no_mi", "Mori Mori no Mi", Type.LOGIA, 0x3C8C3C, 0x7A5A30, "Root Drain", "Forest Growth"),
			new DevilFruit("moku_moku_no_mi", "Moku Moku no Mi", Type.LOGIA, 0xD0D0D0, 0x808080, "White Blow", "Smoke Flight"),
			new DevilFruit("goro_goro_no_mi", "Goro Goro no Mi", Type.LOGIA, 0x3050C0, 0xF8E040, "El Thor", "Thunder Storm"),
			new DevilFruit("numa_numa_no_mi", "Numa Numa no Mi", Type.LOGIA, 0x5A4A2A, 0x3A5A2A, "Swamp Grab", "Bottomless Swamp"),
			new DevilFruit("gasu_gasu_no_mi", "Gasu Gasu no Mi", Type.LOGIA, 0xA0C040, 0x604080, "Gastanet", "Shinokuni"),
			new DevilFruit("yuki_yuki_no_mi", "Yuki Yuki no Mi", Type.LOGIA, 0xF8F8FF, 0xB0D0F0, "Snow Rabbit", "Blizzard"),

			// Zoan
			new DevilFruit("hito_hito_no_mi", "Hito Hito no Mi", Type.ZOAN, 0x8A5A3C, 0xF0A0B0, "Rumble Ball", "Doctor's Care"),
			new DevilFruit("hito_hito_no_mi_daibutsu", "Hito Hito no Mi, Model: Daibutsu", Type.ZOAN, 0xE0B040, 0xFFF0B0, "Buddha Form", "Buddha Shockwave"),
			new DevilFruit("uo_uo_no_mi_seiryu", "Uo Uo no Mi, Model: Seiryu", Type.ZOAN, 0x2A70C0, 0x60D0E0, "Dragon Form", "Bolo Breath"),
			new DevilFruit("ryu_ryu_no_mi_allosaurus", "Ryu Ryu no Mi, Model: Allosaurus", Type.ZOAN, 0x5A8030, 0x8A6A40, "Allosaurus Form", "Dino Bite"),
			new DevilFruit("ryu_ryu_no_mi_pteranodon", "Ryu Ryu no Mi, Model: Pteranodon", Type.ZOAN, 0xD06030, 0x702818, "Pteranodon Form", "Sky Dive"),
			new DevilFruit("neko_neko_no_mi_leopard", "Neko Neko no Mi, Model: Leopard", Type.ZOAN, 0xE0B040, 0x302010, "Leopard Form", "Shigan Pounce"),
			new DevilFruit("tori_tori_no_mi_phoenix", "Tori Tori no Mi, Model: Phoenix", Type.ZOAN, 0x30A0F0, 0xF8D040, "Phoenix Form", "Healing Flames"),
			new DevilFruit("inu_inu_no_mi_okuchi_no_makami", "Inu Inu no Mi, Model: Okuchi no Makami", Type.ZOAN, 0xF0F4F8, 0x80B8E0, "Wolf God Form", "Frost Breath"),
			new DevilFruit("mogu_mogu_no_mi", "Mogu Mogu no Mi", Type.ZOAN, 0x6A5040, 0xF0B0A0, "Mole Form", "Mole Dig"),
			new DevilFruit("uma_uma_no_mi", "Uma Uma no Mi", Type.ZOAN, 0xC0A070, 0xF0F0F0, "Horse Form", "Gallop"),
			new DevilFruit("sara_sara_no_mi_axolotl", "Sara Sara no Mi, Model: Axolotl", Type.ZOAN, 0xF0A0C0, 0xF0F0F0, "Axolotl Form", "Poison Cloud"),
			new DevilFruit("inu_inu_no_mi_wolf", "Inu Inu no Mi, Model: Wolf", Type.ZOAN, 0x707070, 0xF0F0F0, "Wolf Form", "Wolf Pounce"),
			new DevilFruit("inu_inu_no_mi_jackal", "Inu Inu no Mi, Model: Jackal", Type.ZOAN, 0xC09050, 0x402010, "Jackal Form", "Jackal Pounce"),
			new DevilFruit("neko_neko_no_mi_saber_tiger", "Neko Neko no Mi, Model: Saber Tiger", Type.ZOAN, 0xE0A030, 0x202020, "Saber Tiger Form", "Fang Strike"),
			new DevilFruit("ryu_ryu_no_mi_pachycephalosaurus", "Ryu Ryu no Mi, Model: Pachycephalosaurus", Type.ZOAN, 0x4080C0, 0xF0A040, "Pachycephalosaurus Form", "Headbutt"),
			new DevilFruit("ryu_ryu_no_mi_triceratops", "Ryu Ryu no Mi, Model: Triceratops", Type.ZOAN, 0x40A060, 0xF0D080, "Triceratops Form", "Horn Charge"),
			new DevilFruit("ryu_ryu_no_mi_spinosaurus", "Ryu Ryu no Mi, Model: Spinosaurus", Type.ZOAN, 0x507040, 0xC04030, "Spinosaurus Form", "Spino Bite"),
			new DevilFruit("ryu_ryu_no_mi_nidhogg", "Ryu Ryu no Mi, Model: Nidhogg", Type.ZOAN, 0x1E3A34, 0xD8B040, "Nidhogg Form", "Dragon Thunder"),
			new DevilFruit("ryu_ryu_no_mi_brachiosaurus", "Ryu Ryu no Mi, Model: Brachiosaurus", Type.ZOAN, 0x5070A0, 0x909090, "Brachiosaurus Form", "Neck Slam"),
			new DevilFruit("zou_zou_no_mi_mammoth", "Zou Zou no Mi, Model: Mammoth", Type.ZOAN, 0x806040, 0xF0F0E0, "Mammoth Form", "Tusk Charge"),
			new DevilFruit("zou_zou_no_mi", "Zou Zou no Mi", Type.ZOAN, 0xA0A0B0, 0x707080, "Elephant Form", "Trunk Smash"),
			new DevilFruit("ushi_ushi_no_mi_giraffe", "Ushi Ushi no Mi, Model: Giraffe", Type.ZOAN, 0xF0C040, 0x8A5A20, "Giraffe Form", "Neck Hammer"),
			new DevilFruit("ushi_ushi_no_mi_bison", "Ushi Ushi no Mi, Model: Bison", Type.ZOAN, 0x6A4020, 0x303030, "Bison Form", "Bison Charge"),
			new DevilFruit("tori_tori_no_mi_falcon", "Tori Tori no Mi, Model: Falcon", Type.ZOAN, 0xC08040, 0xF0E0C0, "Falcon Form", "Sky Dive"),
			new DevilFruit("hebi_hebi_no_mi_anaconda", "Hebi Hebi no Mi, Model: Anaconda", Type.ZOAN, 0x40A060, 0xF0D040, "Anaconda Form", "Constrict"),
			new DevilFruit("hebi_hebi_no_mi_king_cobra", "Hebi Hebi no Mi, Model: King Cobra", Type.ZOAN, 0xC04040, 0xF0D040, "King Cobra Form", "Venom Fang"),
			new DevilFruit("hebi_hebi_no_mi_yamata_no_orochi", "Hebi Hebi no Mi, Model: Yamata no Orochi", Type.ZOAN, 0x6A2A8A, 0x40C040, "Orochi Form", "Eight Heads"),
			new DevilFruit("inu_inu_no_mi_kyubi_no_kitsune", "Inu Inu no Mi, Model: Kyubi no Kitsune", Type.ZOAN, 0xF0E0F0, 0xF08040, "Nine-Tailed Fox Form", "Perfect Disguise"),
			new DevilFruit("kumo_kumo_no_mi_rosamygale_grauvogeli", "Kumo Kumo no Mi, Model: Rosamygale Grauvogeli", Type.ZOAN, 0x2A2030, 0xF07090, "Spider Form", "Web Shot")
	);

	private static final Map<String, DevilFruit> BY_ID = new LinkedHashMap<>();

	static {
		for (DevilFruit fruit : ALL) {
			BY_ID.put(fruit.id(), fruit);
		}
	}

	/** Finds a fruit by its id, or returns null if there is no such fruit. */
	public static DevilFruit get(String id) {
		return id == null ? null : BY_ID.get(id);
	}
}
