import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth import save_ogg, SR
import music, music_shanties, music_islands, music_more, music_polish, music_isles, music_rivals
music.ALL.update(music_shanties.ALL)
music.ALL.update(music_islands.ALL)
music.ALL.update(music_more.ALL)
music.ALL.update(music_polish.ALL)
music.ALL.update(music_isles.ALL)
music.ALL.update(music_rivals.ALL)
# Kept small so the mod (and its source zip) stays light: songs 32 kHz, calm island themes 24 kHz, both mono q0.
SONG = dict(quality=0, rate=32000)
ISLAND = dict(quality=0, rate=24000)
out = sys.argv[1]
only = sys.argv[2:] or list(music.ALL)
for name in only:
    t=time.time(); x = music.ALL[name](); save_ogg(x, f"{out}/music/{name}.ogg", **(ISLAND if name.startswith("island_") else SONG))
    print(name, round(len(x)/SR,1), "s, took", round(time.time()-t,1))
