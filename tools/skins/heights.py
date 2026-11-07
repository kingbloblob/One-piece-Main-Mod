"""Life-size heights for the story characters, and a script that writes them into characters.json.

Run:  python3 heights.py [path to source/]
Only changes each character's "scale" line. 1.0 = 180 cm (a Minecraft player is 1.8 blocks).
Heights are the official ones (Vivre Cards / databooks / SBS) where known; ones marked
'estimate' have no official number and are guessed from how they look next to others.
"""
import os
import re
import sys

BASE_CM = 180.0

HEIGHTS = {
    'luffy': 174, 'zoro': 181, 'nami': 170, 'usopp': 176, 'sanji': 180, 'chopper': 90, 'robin': 188,
    'franky': 240, 'brook': 277, 'jinbe': 301, 'shanks': 199, 'blackbeard': 344, 'buggy': 192,
    'whitebeard': 666, 'big_mom': 880, 'kaido': 710, 'law': 191, 'kid': 205, 'killer': 195,
    'hawkins': 210, 'drake': 233, 'bonney': 174, 'mihawk': 198, 'crocodile': 253, 'doflamingo': 305,
    'hancock': 300, 'kuma': 689, 'moria': 692, 'garp': 287, 'sengoku': 278, 'akainu': 306,
    'kizaru': 302, 'fujitora': 270, 'aokiji': 298, 'smoker': 209, 'koby': 167, 'tashigi': 170,
    'lucci': 212, 'sabo': 187, 'ace': 185, 'marco': 203, 'rayleigh': 188, 'roger': 274, 'oden': 382,
    'yamato': 263, 'katakuri': 509, 'enel': 266,
    # ryan's choice (2026-10-31): Hancock about 3 blocks tall (canon 191 cm)
    # estimates
    'ryokugyu': 300, 'dragon': 255, 'king': 612, 'kinemon': 190, 'vegapunk': 260,
    'magellan': 300, 'ivankov': 409, 'imu': 300,
    'queen': 610, 'saturn': 400, 'hody': 330, 'shamrock': 199, 'gunko': 175,
    # Loki is a giant far taller than this in the manga; capped at 8 m so he still fits arenas and doors.
    'loki': 800,
}
# Models that are not the normal 32 px tall (giants.py reshapes them): their scale is corrected so the
# whole model, head to feet (not counting hats), still comes out at the canon height.
MODEL_PX = {'chopper': 27, 'ivankov': 49, 'vegapunk': 49, 'moria': 38,
            'doflamingo': 36, 'aokiji': 36, 'katakuri': 36, 'kizaru': 35, 'hancock': 37, 'big_mom': 44}   # long legs: 32 + LEGS

ESTIMATES = {'loki', 'ryokugyu', 'dragon', 'king', 'kinemon', 'vegapunk', 'magellan', 'ivankov', 'imu', 'saturn'}


def scale(cid):
    return max(0.25, round(HEIGHTS[cid] / BASE_CM * 32.0 / MODEL_PX.get(cid, 32), 2))


def main():
    src = next((a for a in sys.argv[1:]), '/mnt/project-files/one-piece-mod/source')
    path = os.path.join(src, 'src/main/resources/onepiece/characters.json')
    lines = open(path).read().split('\n')
    cur = None
    changed = 0
    for i, line in enumerate(lines):
        m = re.match(r'^    "id": "([a-z_]+)"', line)
        if m:
            cur = m.group(1)
        m = re.match(r'^(    "scale": )[0-9.]+(,?)$', line)
        if m and cur in HEIGHTS:
            lines[i] = '%s%s%s' % (m.group(1), scale(cur), m.group(2))
            changed += 1
    open(path, 'w').write('\n'.join(lines))
    print('set %d scales' % changed)


if __name__ == '__main__':
    main()
