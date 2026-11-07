"""Writes sounds.json, subtitles, music disc items/songs/textures for the onepiece_sounds namespace.
Usage: python3 make_assets.py <generated sounds dir> <mod src/main/resources dir>"""
import json, os, shutil, struct, sys, zlib, wave, subprocess
import numpy as np

gen, res = sys.argv[1], sys.argv[2]
A = f"{res}/assets/onepiece_sounds"
D = f"{res}/data/onepiece_sounds"

SFX = {
    "haki/conqueror_burst": "Conqueror's Haki bursts",
    "haki/conqueror_awaken": "A king's will awakens",
    "haki/armament_on": "Armament Haki hardens",
    "haki/armament_hit": "Armament Haki strikes",
    "haki/observation_on": "Observation Haki senses",
    "den_den_mushi/call": "Den Den Mushi rings",
    "devil_fruit/eat": "Devil Fruit eaten",
    "devil_fruit/awaken": "Devil Fruit awakens",
    "bounty/raise": "Bounty rises",
    "bounty/news_coo": "News Coo spreads the word",
    "navy/bugle": "Marine bugle call",
    "navy/cannon": "Cannon fires",
    "boss/defeated": "Boss defeated",
    "story/goal": "Story goal done",
    "story/chapter": "Chapter complete",
    "story/quest_complete": "Quest complete",
}
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfx_moves import SUBTITLES as MOVE_SUBTITLES
SFX.update(MOVE_SUBTITLES)
from sfx_combat import SUBTITLES as COMBAT_SUBTITLES
SFX.update(COMBAT_SUBTITLES)
from sfx_hits import SUBTITLES as HIT_SUBTITLES
SFX.update(HIT_SUBTITLES)
from sfx_world import SUBTITLES as WORLD_SUBTITLES
SFX.update(WORLD_SUBTITLES)
from sfx_zoan import SUBTITLES as ZOAN_SUBTITLES
SFX.update(ZOAN_SUBTITLES)
from sfx_polish import SUBTITLES as POLISH_SUBTITLES
SFX.update(POLISH_SUBTITLES)
from sfx_unique import SUBTITLES as UNIQUE_SUBTITLES
SFX.update(UNIQUE_SUBTITLES)
SONGS = {  # file: (title, disc color rgb, comparator)
    "toward_the_grand_line": ("Toward the Grand Line", (230, 170, 40), 1),
    "fair_winds": ("Fair Winds", (60, 160, 220), 2),
    "boss_battle": ("Clash on the Grand Line", (200, 50, 40), 3),
    "emperor_battle": ("Clash of Emperors", (120, 40, 160), 4),
    "justice_marches": ("Justice Marches", (235, 235, 245), 5),
    "drink_to_the_horizon": ("Drink to the Horizon", (240, 120, 40), 6),
    "haul_the_anchor": ("Haul the Anchor", (110, 80, 50), 7),
    "lantern_on_the_waves": ("Lantern on the Waves", (40, 50, 120), 8),
    "admiral_battle": ("Absolute Justice", (90, 170, 230), 9),
    "warlord_battle": ("Warlord of the Sea", (60, 120, 60), 10),
    "final_battle": ("Dawn of the Void Century", (20, 20, 30), 11),
    "storm_at_sea": ("Storm on the Grand Line", (70, 80, 110), 12),
    "deep_sea": ("Ten Thousand Meters Down", (20, 60, 90), 13),
    "sea_king": ("Something Beneath the Waves", (40, 110, 90), 14),
    "whitebeard_battle": ("Father of the Seas", (235, 235, 225), 15),
    "big_mom_battle": ("Sweet Tyrant", (240, 110, 170), 15),
    "kaido_battle": ("The Strongest Creature", (90, 60, 140), 15),
    "blackbeard_battle": ("Darkness Rising", (30, 25, 40), 15),
    "elder_star_battle": ("Five Elders", (210, 190, 120), 15),
    "supernova_battle": ("Worst Generation", (220, 90, 40), 15),
}
# Island themes: background music for island biomes (no discs). Sound event music.island.<name>.
ISLANDS = ["winter", "desert", "wano", "sky", "spooky", "marine", "tropical",
           "east_blue", "fishman", "sabaody", "dressrosa", "whole_cake", "egghead", "giants", "jungle", "prison",
           "holy", "ancient", "newkama",
           "punk_hazard", "loguetown", "enies_lobby", "onigashima", "zou", "amazon_lily", "jaya", "little_garden",
           "kuraigana", "hachinosu"]

sounds, lang = {}, {}
for path, sub in SFX.items():
    ev = path.replace("/", ".")
    sounds[ev] = {"subtitle": f"subtitles.onepiece_sounds.{ev}", "sounds": [f"onepiece_sounds:{path}"]}
    lang[f"subtitles.onepiece_sounds.{ev}"] = sub
for name, (title, _, _) in SONGS.items():
    sounds[f"music.{name}"] = {"sounds": [{"name": f"onepiece_sounds:music/{name}", "stream": True}]}
for name in ISLANDS:
    sounds[f"music.island.{name}"] = {"sounds": [{"name": f"onepiece_sounds:music/island_{name}", "stream": True}]}

def length(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                         capture_output=True, text=True, check=True).stdout
    return round(float(out), 1)

def png(path, rgba):
    h, w, _ = rgba.shape
    raw = b"".join(b"\x00" + rgba[y].astype(np.uint8).tobytes() for y in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) \
        + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(data)

def disc_texture(color):
    img = np.zeros((16, 16, 4))
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            if d > 7.3:
                continue
            if d < 1.1:
                c = (20, 20, 20)  # hole
            elif d < 3.2:
                c = color  # label
                if d > 2.6:
                    c = tuple(int(v * 0.7) for v in color)
            else:
                g = 34 if (int(d * 2) % 2) else 46  # grooves
                c = (g, g, g + 4)
                if d > 6.6:
                    c = (18, 18, 22)
            img[y, x] = (*c, 255)
    img[4, 5, :3] = img[5, 4, :3] = (110, 110, 120)  # shine
    return img

for path in SFX:
    os.makedirs(os.path.dirname(f"{A}/sounds/{path}.ogg"), exist_ok=True)
    shutil.copy(f"{gen}/{path}.ogg", f"{A}/sounds/{path}.ogg")
os.makedirs(f"{A}/sounds/music", exist_ok=True)
os.makedirs(f"{A}/items", exist_ok=True)
os.makedirs(f"{A}/models/item", exist_ok=True)
os.makedirs(f"{D}/jukebox_song", exist_ok=True)
for name, (title, color, comp) in SONGS.items():
    shutil.copy(f"{gen}/music/{name}.ogg", f"{A}/sounds/music/{name}.ogg")
    item = f"music_disc_{name}"
    lang[f"item.onepiece_sounds.{item}"] = "Music Disc"
    lang[f"jukebox_song.onepiece_sounds.{name}"] = f"One Piece Mod - {title}"
    json.dump({"sound_event": f"onepiece_sounds:music.{name}",
               "description": {"translate": f"jukebox_song.onepiece_sounds.{name}"},
               "length_in_seconds": length(f"{gen}/music/{name}.ogg"), "comparator_output": comp},
              open(f"{D}/jukebox_song/{name}.json", "w"), indent=2)
    json.dump({"model": {"type": "minecraft:model", "model": f"onepiece_sounds:item/{item}"}},
              open(f"{A}/items/{item}.json", "w"), indent=2)
    json.dump({"parent": "minecraft:item/generated", "textures": {"layer0": f"onepiece_sounds:item/{item}"}},
              open(f"{A}/models/item/{item}.json", "w"), indent=2)
    png(f"{A}/textures/item/{item}.png", disc_texture(color))

for name in ISLANDS:
    shutil.copy(f"{gen}/music/island_{name}.ogg", f"{A}/sounds/music/island_{name}.ogg")

json.dump(sounds, open(f"{A}/sounds.json", "w"), indent=2)
os.makedirs(f"{A}/lang", exist_ok=True)
json.dump(lang, open(f"{A}/lang/en_us.json", "w"), indent=2, ensure_ascii=False)
print("assets written:", len(SFX), "effects,", len(SONGS), "songs,", len(ISLANDS), "island themes")
