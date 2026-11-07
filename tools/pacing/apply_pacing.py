"""Pacing pass 2026-10-29 (thread "Improve pacing of story and progression").
Edits story.json and characters.json in the source tree given as argv[1] (default: the shared source).
Safe to run again: it sets values, and only appends a goal if a goal of that type isn't in the chapter yet.
"""
import json, os, sys

root = sys.argv[1] if len(sys.argv) > 1 else "/mnt/project-files/one-piece-mod/source"
res = os.path.join(root, "src/main/resources/onepiece")

def load(name):
    with open(os.path.join(res, name), encoding="utf-8") as f:
        return json.load(f)

def save(name, data):
    with open(os.path.join(res, name), "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

# ---- Story: bigger Berry rewards, Pirate XP per chapter, goals for the newer features ----
BERRIES = {
    "dream": 30, "koby": 40, "set_sail": 50,
    "orange_town": 60, "syrup_village": 60, "baratie": 70, "arlong_park": 80, "loguetown": 100, "reverse_mountain": 120,
    "drum_island": 150, "alabasta": 180, "sky_island": 200, "enies_lobby": 250, "thriller_bark": 250, "sabaody": 250,
    "amazon_lily": 300, "impel_down": 300, "marineford": 400, "training": 400,
    "fishman_island": 400, "punk_hazard": 400, "dressrosa": 500, "zou": 400, "whole_cake": 700, "wano": 900,
    "hachinosu": 1200, "laugh_tale": 2500,
    "red_line": 800, "void_century": 1000, "empty_throne": 2500,
}
# Goals appended at the END of a chapter (saved progress keeps goal numbers, so never insert in the middle).
EXTRA_GOALS = {
    "orange_town": [{"type": "treasure", "text": "Dig up a buried treasure (Buggy drops his treasure map)", "count": 1}],
    "baratie": [
        {"type": "fish", "text": "Catch 2 kinds of fish (/fishlog)", "count": 2},
        {"type": "item", "text": "Cook Sea Bream Sashimi at the Ship's Galley", "item": "onepiece:sea_bream_sashimi"},
    ],
    "sky_island": [{"type": "davyback", "text": "Take on a crew in a Davy Back Fight, win or lose (Foxy waits at Long Ring Long Land)", "count": 1}],
    "dressrosa": [{"type": "colosseum", "text": "Win the Champion Cup at the Corrida Colosseum", "level": 2}],
}

story = load("story.json")
index = 0
for saga in story["sagas"]:
    for chapter in saga["chapters"]:
        cid = chapter["id"]
        if cid in BERRIES:
            chapter["reward"]["berries"] = BERRIES[cid]
        # 100 Pirate XP for the first chapter, +25 per chapter after: about 14,000 XP over the whole story.
        chapter["reward"]["xp"] = 100 + 25 * index
        index += 1
        have = {g["type"] for g in chapter["goals"]}
        for goal in EXTRA_GOALS.get(cid, []):
            if goal["type"] not in have or (goal["type"] == "item" and not any(g.get("item") == goal.get("item") for g in chapter["goals"])):
                chapter["goals"].append(goal)
save("story.json", story)

# ---- Traders: they pay less for ores and gems, so mining doesn't out-earn the voyage ----
ORE_SALES = {  # (trader, buy item) -> (buyCount, Berries paid)
    ("nami", "minecraft:gold_ingot"): (4, 2),
    ("nami", "minecraft:emerald"): (2, 2),
    ("nami", "minecraft:diamond"): (2, 4),
    ("nami", "minecraft:gold_block"): (4, 12),
    ("tashigi", "minecraft:iron_ingot"): (8, 1),
    ("tashigi", "minecraft:diamond"): (2, 4),
    ("vegapunk", "minecraft:diamond"): (4, 8),
}
chars = load("characters.json")
for character in chars:
    for level in character.get("levels") or []:
        for trade in level:
            key = (character["id"], trade["buy"])
            if trade["sell"] == "onepiece:berry" and key in ORE_SALES:
                trade["buyCount"], trade["sellCount"] = ORE_SALES[key]
save("characters.json", chars)
print("story chapters:", index)
