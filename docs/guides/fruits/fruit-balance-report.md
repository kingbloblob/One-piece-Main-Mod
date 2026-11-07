# Devil Fruit balance pass (2026-10-25)

Every one of the 107 Devil Fruits was tested in the game against training dummies, before and after the changes.
Raw numbers: `fruit-balance-before.csv` and `fruit-balance-after.csv` in this folder.

## How the test works

`FruitBench` (in `power/FruitBench.java`) only runs when the server is started with `-Donepiece.fruitbench=true`,
so players never see it. Each fruit gets a fake player that uses both moves whenever they are ready, in three
30-second tests:

| Test | What happens | What is measured |
|---|---|---|
| Duel | One 1000-HP dummy marked as a boss, 3 blocks away. Strength from the fruit counts as extra sword damage. | Damage per second from the fruit |
| Crowd | Six dummies around the player | Damage per second to all of them |
| Survive | An enemy hits the player for 3 hearts every second | Health saved per second (shields, dodges, healing) |

It also records how much of the duel the boss dummy spent stunned (heavy Slowness).
Score = duel dps + 0.4 x extra crowd dps + 1.5 x health saved/s + 0.03 x stun %.

## What was wrong

- **16 fruits did no damage at all** (Ope Ope, Jiki Jiki, Nomi Nomi, Mira Mira, Fuwa Fuwa, Toki Toki, Memo Memo,
  Wapu Wapu, Sui Sui, Modo Modo, Chiyu Chiyu, Kibi Kibi, Pteranodon, Falcon, Awa Awa, Woshu Woshu).
- **Zoans were about twice as strong as everything else.** Strength II on top of a sword made every Zoan form
  the best fruit in the game (median score 9.6 vs 4.0 for Paramecia).
- **18 fruits could keep a boss stunned forever** (Noro Noro, Hobi Hobi, Hie Hie, Yuki Yuki, Numa Numa, Beta Beta,
  Ito Ito, Okuchi no Makami, Zushi Zushi...). Fights became a free hit while the boss stood still.
- **Chiyu Chiyu's healing beam healed the enemy you were looking at.**
- **Fruit damage never grew.** A level-1 Gomu Gomu Pistol and a fully mastered one both did 8 damage, so fruits
  fell behind the 1000+ HP bosses late in the story.

## What changed

1. **Fruit damage grows with mastery.** Every fruit move now does x1.0 at 0 mastery up to x1.75 at 1,000 mastery,
   and x2.0 once awakened (`FruitAbilities.power`). The mastery message shows the current multiplier.
   This keeps early progression slow and lets fruits keep up with late bosses.
2. **Zoan forms give at most Strength I** (`zoanEffect`). Zoans still have the best sustained melee, but no longer
   double everyone else.
3. **Bosses and players resist stuns** (`FruitControl`). Ordinary mobs are stunned as before. Bosses and other
   players get at most 3 seconds of stun, then 4 seconds where only a light slow gets through; Weakness is
   capped at level I. Poison, fire, wither and blindness are not changed.
4. **25 weak fruits got damage on their moves**, chosen to fit the fruit: Ope Ope's Shambles cuts on the swap,
   Jiki Jiki's Repel hurts as it throws, Mira Mira strikes out of the mirror, Bane Bane and Uma Uma hit on
   their dash, Pteranodon/Falcon/Toki Toki/Nomi Nomi get Strength, Yami Yami's pulls crush, and the pure
   debuff beams (Noro Noro, Hobi Hobi, Ori Ori, Ato Ato, Nui Nui, Awa Awa, Woshu Woshu, Shiku Shiku,
   Memo Memo, Modo Modo, Fuwa Fuwa, Pero Pero, Doru Doru, Horo Horo, Wara Wara, Mero Mero, Ito Ito, Nikyu
   Nikyu, Sabi Sabi, Kage Kage) now do 4 to 9 damage as well.
5. **Top fruits trimmed a little**: Supa Supa 11 -> 8, Riki Riki Strength III -> II, Magu Magu fist 13 -> 10 and
   meteors 9 -> 6, Mera Mera Hiken cooldown 3 -> 4 s, Gasu Gasu 6 -> 4, King Cobra poison III -> II.
6. **Chiyu Chiyu** heals only players and your own pets, otherwise yourself.
7. **Toshi Toshi / Modo Modo** can't turn bosses or players into babies (they get Weakness instead).

## Results

| | Before | After |
|---|---|---|
| Lowest score | 0.0 | 0.15 (Kibi Kibi, a taming fruit) |
| 10th percentile | 0.0 | 1.9 |
| Median | 5.3 | 4.9 |
| 90th percentile | 11.4 | 8.5 |
| Highest score | 13.6 (Mammoth) | 10.3 (Mera Mera) |
| Fruits with no damage | 16 | 1 |
| Fruits scoring over 9 | 20 | 2 |
| Fruits that stun-lock a boss | 18 | 0 |
| Median by type | Paramecia 4.0 / Logia 8.4 / Zoan 9.6 | Paramecia 4.0 / Logia 7.2 / Zoan 6.8 |

Logia stay a bit ahead on purpose: they also dodge half of all non-Haki hits, which the bench does not count.

## Every fruit, sorted by score after the pass

| Fruit | Type | Score before | Score after | Duel dps | Crowd dps | HP saved/s | Boss stunned % |
|---|---|---|---|---|---|---|---|
| mera_mera_no_mi | Logia | 10.7 | 10.3 | 4.1 | 10.6 | 2.4 | 0 |
| hebi_hebi_no_mi_yamata_no_orochi | Zoan | 12.1 | 9.1 | 6.3 | 10.2 | 0.8 | 0 |
| ryu_ryu_no_mi_pachycephalosaurus | Zoan | 13.6 | 9.0 | 6.6 | 2.0 | 1.6 | 0 |
| zou_zou_no_mi_mammoth | Zoan | 13.6 | 9.0 | 6.6 | 2.0 | 1.6 | 0 |
| zou_zou_no_mi | Zoan | 9.0 | 9.0 | 6.6 | 2.0 | 1.6 | 0 |
| ryu_ryu_no_mi_triceratops | Zoan | 13.4 | 8.8 | 6.4 | 1.8 | 1.6 | 0 |
| supa_supa_no_mi | Paramecia | 10.2 | 8.7 | 7.1 | 4.0 | 1.1 | 0 |
| hebi_hebi_no_mi_king_cobra | Zoan | 10.2 | 8.6 | 7.4 | 2.8 | 0.8 | 0 |
| magu_magu_no_mi | Logia | 10.9 | 8.5 | 3.8 | 8.2 | 2.0 | 0 |
| uo_uo_no_mi_seiryu | Zoan | 13.1 | 8.5 | 7.3 | 2.7 | 0.8 | 0 |
| inu_inu_no_mi_okuchi_no_makami | Zoan | 10.6 | 8.5 | 6.4 | 1.8 | 0.8 | 30 |
| goro_goro_no_mi | Logia | 8.5 | 8.4 | 1.3 | 12.0 | 1.9 | 0 |
| riki_riki_no_mi | Paramecia | 10.4 | 8.1 | 8.1 | 3.5 | 0.0 | 0 |
| hie_hie_no_mi | Logia | 9.2 | 8.0 | 2.7 | 3.0 | 2.7 | 39 |
| gasu_gasu_no_mi | Logia | 9.5 | 7.9 | 2.7 | 8.7 | 1.9 | 0 |
| ryu_ryu_no_mi_brachiosaurus | Zoan | 12.5 | 7.9 | 5.5 | 5.4 | 1.6 | 0 |
| hito_hito_no_mi_daibutsu | Zoan | 12.4 | 7.8 | 5.4 | 4.8 | 1.6 | 0 |
| ryu_ryu_no_mi_allosaurus | Zoan | 12.4 | 7.8 | 6.6 | 2.0 | 0.8 | 0 |
| ushi_ushi_no_mi_bison | Zoan | 12.4 | 7.8 | 6.6 | 2.0 | 0.8 | 0 |
| hebi_hebi_no_mi_anaconda | Zoan | 8.3 | 7.7 | 5.6 | 1.0 | 0.8 | 30 |
| yuki_yuki_no_mi | Logia | 8.7 | 7.4 | 2.5 | 3.9 | 2.1 | 39 |
| netsu_netsu_no_mi | Paramecia | 7.3 | 7.3 | 5.5 | 10.0 | 0.0 | 0 |
| kage_kage_no_mi | Paramecia | 7.5 | 7.2 | 6.6 | 0.5 | 0.4 | 0 |
| doku_doku_no_mi | Paramecia | 7.1 | 7.1 | 4.6 | 10.9 | 0.0 | 0 |
| bisu_bisu_no_mi | Paramecia | 6.9 | 6.9 | 4.5 | 4.5 | 1.6 | 0 |
| mori_mori_no_mi | Logia | 8.3 | 6.9 | 1.2 | 1.2 | 3.2 | 30 |
| neko_neko_no_mi_saber_tiger | Zoan | 11.4 | 6.8 | 6.8 | 2.2 | 0.0 | 0 |
| ryu_ryu_no_mi_spinosaurus | Zoan | 11.4 | 6.8 | 6.8 | 2.2 | 0.0 | 0 |
| ushi_ushi_no_mi_giraffe | Zoan | 6.8 | 6.8 | 6.8 | 2.2 | 0.0 | 0 |
| toshi_toshi_no_mi | Paramecia | 6.8 | 6.8 | 6.0 | 0.0 | 0.5 | 0 |
| suna_suna_no_mi | Logia | 6.1 | 6.7 | 2.6 | 3.9 | 2.4 | 0 |
| fude_fude_no_mi | Paramecia | 6.8 | 6.7 | 2.1 | 13.6 | 0.0 | 0 |
| neko_neko_no_mi_leopard | Zoan | 11.2 | 6.6 | 6.6 | 2.0 | 0.0 | 0 |
| inu_inu_no_mi_wolf | Zoan | 6.4 | 6.4 | 6.4 | 1.8 | 0.0 | 0 |
| inu_inu_no_mi_jackal | Zoan | 6.4 | 6.4 | 6.4 | 1.8 | 0.0 | 0 |
| choki_choki_no_mi | Paramecia | 6.3 | 6.3 | 5.0 | 5.0 | 0.8 | 0 |
| yami_yami_no_mi | Logia | 3.8 | 6.2 | 2.0 | 4.0 | 2.3 | 0 |
| kumo_kumo_no_mi_rosamygale_grauvogeli | Zoan | 6.2 | 6.2 | 5.0 | 0.4 | 0.8 | 0 |
| hira_hira_no_mi | Paramecia | 6.1 | 6.1 | 4.5 | 4.5 | 1.1 | 0 |
| baku_baku_no_mi | Paramecia | 6.0 | 6.0 | 4.2 | 2.7 | 1.2 | 0 |
| bomu_bomu_no_mi | Paramecia | 5.9 | 6.0 | 4.3 | 8.4 | 0.0 | 0 |
| soru_soru_no_mi | Paramecia | 7.9 | 5.9 | 2.5 | 11.1 | 0.0 | 0 |
| ton_ton_no_mi | Paramecia | 5.9 | 5.9 | 1.6 | 6.4 | 1.6 | 0 |
| sube_sube_no_mi | Paramecia | 4.9 | 5.9 | 3.5 | 3.5 | 1.6 | 0 |
| sara_sara_no_mi_axolotl | Zoan | 5.3 | 5.9 | 1.3 | 7.6 | 1.4 | 0 |
| gura_gura_no_mi | Paramecia | 5.8 | 5.8 | 3.8 | 8.8 | 0.0 | 0 |
| hito_hito_no_mi | Zoan | 5.8 | 5.8 | 4.6 | 0.0 | 0.8 | 0 |
| tori_tori_no_mi_phoenix | Zoan | 0.9 | 5.5 | 4.6 | 0.0 | 0.6 | 0 |
| kira_kira_no_mi | Paramecia | 5.5 | 5.5 | 3.7 | 3.7 | 1.2 | 0 |
| pamu_pamu_no_mi | Paramecia | 5.4 | 5.4 | 3.6 | 8.1 | 0.0 | 0 |
| fuku_fuku_no_mi | Paramecia | 5.2 | 5.2 | 3.7 | 3.7 | 1.0 | 0 |
| ishi_ishi_no_mi | Paramecia | 5.1 | 5.1 | 3.3 | 3.3 | 1.2 | 0 |
| pika_pika_no_mi | Logia | 5.4 | 5.0 | 2.0 | 2.0 | 2.0 | 0 |
| bara_bara_no_mi | Paramecia | 5.7 | 4.9 | 3.5 | 3.5 | 0.9 | 0 |
| buki_buki_no_mi | Paramecia | 4.8 | 4.9 | 4.9 | 4.9 | 0.0 | 0 |
| jiki_jiki_no_mi | Paramecia | 0.0 | 4.8 | 1.6 | 9.6 | 0.0 | 0 |
| bane_bane_no_mi | Paramecia | 2.0 | 4.7 | 4.7 | 4.7 | 0.0 | 0 |
| beta_beta_no_mi | Paramecia | 6.5 | 4.7 | 1.7 | 6.2 | 0.0 | 39 |
| moku_moku_no_mi | Logia | 3.9 | 4.7 | 1.7 | 1.7 | 2.0 | 0 |
| ryu_ryu_no_mi_pteranodon | Zoan | 0.0 | 4.6 | 4.6 | 0.0 | 0.0 | 0 |
| mogu_mogu_no_mi | Zoan | 4.6 | 4.6 | 4.6 | 0.0 | 0.0 | 0 |
| tori_tori_no_mi_falcon | Zoan | 0.0 | 4.6 | 4.6 | 0.0 | 0.0 | 0 |
| inu_inu_no_mi_kyubi_no_kitsune | Zoan | 4.6 | 4.6 | 4.6 | 0.0 | 0.0 | 0 |
| mane_mane_no_mi | Paramecia | 4.5 | 4.5 | 4.5 | 4.5 | 0.0 | 0 |
| mochi_mochi_no_mi | Paramecia | 6.5 | 4.5 | 1.2 | 1.2 | 1.6 | 30 |
| doru_doru_no_mi | Paramecia | 5.4 | 4.5 | 1.2 | 1.2 | 1.6 | 30 |
| numa_numa_no_mi | Logia | 7.9 | 4.4 | 1.3 | 2.3 | 1.1 | 39 |
| bari_bari_no_mi | Paramecia | 4.3 | 4.3 | 2.7 | 2.7 | 1.1 | 0 |
| hana_hana_no_mi | Paramecia | 5.0 | 4.2 | 2.7 | 4.0 | 0.0 | 33 |
| guru_guru_no_mi | Paramecia | 4.1 | 4.1 | 1.9 | 7.5 | 0.0 | 0 |
| zushi_zushi_no_mi | Paramecia | 5.9 | 4.1 | 2.4 | 3.7 | 0.0 | 39 |
| kilo_kilo_no_mi | Paramecia | 4.0 | 4.0 | 1.8 | 7.3 | 0.0 | 0 |
| gomu_gomu_no_mi | Paramecia | 4.0 | 4.0 | 4.0 | 4.0 | 0.0 | 0 |
| horu_horu_no_mi | Paramecia | 3.9 | 3.9 | 3.6 | 2.1 | 0.2 | 0 |
| shiro_shiro_no_mi | Paramecia | 3.9 | 3.9 | 2.1 | 2.1 | 1.2 | 0 |
| oto_oto_no_mi | Paramecia | 3.8 | 3.9 | 2.9 | 5.4 | 0.0 | 0 |
| nagi_nagi_no_mi | Paramecia | 3.5 | 3.5 | 3.5 | 3.5 | 0.0 | 0 |
| uma_uma_no_mi | Zoan | 1.2 | 3.3 | 2.1 | 2.1 | 0.8 | 0 |
| pero_pero_no_mi | Paramecia | 4.2 | 3.3 | 1.2 | 1.2 | 0.8 | 30 |
| yomi_yomi_no_mi | Paramecia | 4.8 | 3.0 | 1.9 | 1.9 | 0.0 | 39 |
| ope_ope_no_mi | Paramecia | 0.0 | 3.0 | 3.0 | 3.0 | 0.0 | 0 |
| mato_mato_no_mi | Paramecia | 2.7 | 3.0 | 3.0 | 3.0 | 0.0 | 0 |
| nomi_nomi_no_mi | Paramecia | 0.0 | 3.0 | 3.0 | 0.0 | 0.0 | 0 |
| wara_wara_no_mi | Paramecia | 2.2 | 2.9 | 1.5 | 1.5 | 0.9 | 0 |
| sabi_sabi_no_mi | Paramecia | 2.0 | 2.7 | 2.7 | 2.7 | 0.0 | 0 |
| nui_nui_no_mi | Paramecia | 3.0 | 2.5 | 1.4 | 1.4 | 0.1 | 30 |
| horo_horo_no_mi | Paramecia | 1.8 | 2.5 | 1.3 | 4.3 | 0.0 | 0 |
| toki_toki_no_mi | Paramecia | 0.0 | 2.3 | 2.3 | 0.0 | 0.0 | 0 |
| ori_ori_no_mi | Paramecia | 3.4 | 2.3 | 1.4 | 1.4 | 0.0 | 30 |
| mero_mero_no_mi | Paramecia | 2.9 | 2.2 | 1.3 | 1.3 | 0.0 | 30 |
| shiku_shiku_no_mi | Paramecia | 1.2 | 2.2 | 2.2 | 2.2 | 0.0 | 0 |
| nikyu_nikyu_no_mi | Paramecia | 1.2 | 2.1 | 2.1 | 2.1 | 0.0 | 0 |
| mira_mira_no_mi | Paramecia | 0.0 | 2.1 | 2.1 | 2.1 | 0.0 | 0 |
| fuwa_fuwa_no_mi | Paramecia | 0.0 | 2.1 | 2.1 | 2.1 | 0.0 | 0 |
| ato_ato_no_mi | Paramecia | 3.0 | 2.1 | 1.2 | 1.2 | 0.0 | 30 |
| noro_noro_no_mi | Paramecia | 3.0 | 1.9 | 1.0 | 1.0 | 0.0 | 30 |
| awa_awa_no_mi | Paramecia | 0.4 | 1.9 | 1.9 | 1.9 | 0.0 | 0 |
| woshu_woshu_no_mi | Paramecia | 0.4 | 1.9 | 1.9 | 1.9 | 0.0 | 0 |
| doa_doa_no_mi | Paramecia | 1.8 | 1.8 | 0.0 | 0.0 | 1.2 | 0 |
| hobi_hobi_no_mi | Paramecia | 3.0 | 1.7 | 0.8 | 0.8 | 0.0 | 30 |
| ito_ito_no_mi | Paramecia | 3.8 | 1.6 | 1.6 | 1.6 | 0.0 | 0 |
| sui_sui_no_mi | Paramecia | 0.0 | 1.5 | 1.5 | 1.5 | 0.0 | 0 |
| memo_memo_no_mi | Paramecia | 0.0 | 1.4 | 1.4 | 1.4 | 0.0 | 0 |
| modo_modo_no_mi | Paramecia | 0.0 | 1.4 | 1.4 | 1.4 | 0.0 | 0 |
| chiyu_chiyu_no_mi | Paramecia | 0.0 | 0.8 | 0.0 | 0.0 | 0.5 | 0 |
| wapu_wapu_no_mi | Paramecia | 0.0 | 0.5 | 0.5 | 0.5 | 0.0 | 0 |
| kibi_kibi_no_mi | Paramecia | 0.2 | 0.2 | 0.0 | 0.0 | 0.1 | 0 |
