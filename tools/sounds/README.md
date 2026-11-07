# Sounds and music generator
Every sound effect and song in the mod (namespace `onepiece_sounds`) is made from scratch by these scripts:
pure math (sine waves, filtered noise), no samples, no copied music. Safe to publish.

Needs python3 + numpy + ffmpeg (with libvorbis).

    python3 gen_sfx.py out          # 16 effects  -> out/<group>/<name>.ogg
    python3 gen_music.py out        # 5 songs     -> out/music/<name>.ogg  (or: gen_music.py out boss_battle)
    python3 gen_moves.py out        # 23 Devil Fruit move sounds (sfx_moves.py) -> out/fruit_move/<name>.ogg
    python3 gen_combat.py out       # 13 boss + 25 fighting style sounds (sfx_combat.py) -> out/boss, out/style
    python3 gen_hits.py out         # 11 fruit hit sounds + Gear 5, heal, Zoan shift (sfx_hits.py)
    python3 gen_world.py out        # ships, sea, and 19 creature voices x ambient/hurt/death (sfx_world.py)
    python3 gen_zoan.py out         # 11 more move sounds (Zoan animals, Barrier, Nagi) + 3 awakenings (sfx_zoan.py)
    python3 gen_unique.py out       # 18 more move sounds, one per fruit that used to share (sfx_unique.py)
    python3 make_assets.py out ../../source/src/main/resources   # copies audio, writes sounds.json, lang, discs

gen_music.py also knows the 3 extra shanties (music_shanties.py), 7 island themes (music_islands.py) and
music_more.py: 12 more island themes plus the Admiral, Warlord and final boss themes (files music/island_<name>.ogg,
sound events music.island.<name>). Which island plays which theme: MUSIC in tools/islands/island_look.py (rerun it
after adding a theme). Which boss gets which battle theme: source/.../sound/BossMusic.java. 2026-11-05: music_isles.py adds 10 more island themes (Punk Hazard, Loguetown, Enies Lobby, Onigashima, Zou, Amazon Lily,
Jaya, Little Garden, Kuraigana, Hachinosu) and music_rivals.py 6 boss themes with discs (Whitebeard, Big Mom, Kaido,
Blackbeard, Five Elders, Worst Generation). make_assets needs every .ogg in out/: copy the ones you
didn't regenerate from source/src/main/resources/assets/onepiece_sounds/sounds/ first.
Which fruit plays which move sound: source/.../sound/FruitSounds.java.

To change a song, edit its melody strings in music.py (format NOTE:beats, e.g. "D5:1.5 r:0.5").
Adding a sound: add a function to sfx.py ALL, a subtitle in make_assets.py SFX, and a field in ModSounds.java.

Where they play: sound/BossSounds (CharacterEntity, BossAbility, BossStrikes), sound/StyleSounds (StyleMoves: one per
technique, the vanilla sounds there are passed as null), FruitSounds.playHit (first hit of each fruit move; vanilla
sounds played at the user during a move are muted by FruitAbilities.quietVanilla), sound/WorldSounds (ships, sea
events, Sea Kings; creatures use voice("bear") in CreatureSpecies). gen_combat.py trims silent reverb tails.

make_assets.py rewrites every disc texture: back up assets/onepiece_sounds/textures/item first and put the old ones back
afterwards (several were hand-edited). island_look.py writes island music with 30 s to 2 min between songs.
