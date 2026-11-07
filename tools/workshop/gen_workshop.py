"""Writes the data for the workshop feature (com.onepiecemod.workshop):
station upgrade trees, the new station recipes (Dials, cooking tiers II-III, Fang Blade...), item models,
the milky cloud block, lang, item descriptions and "how to get it" cards for the rare drops.

Station recipes and descriptions are MERGED by id into the shared files, so other features' entries stay.
Usage: python3 tools/workshop/gen_workshop.py <path to src/main/resources>"""
import json, os, sys

RES = sys.argv[1] if len(sys.argv) > 1 else 'src/main/resources'

def I(item, count=1): return {"item": item, "count": count}
def T(tag, icon, name, count=1): return {"tag": tag, "icon": icon, "name": name, "count": count}
PLANKS = lambda n: T("minecraft:planks", "minecraft:oak_planks", "Any Planks", n)
op = lambda s: "onepiece:" + s
mc = lambda s: "minecraft:" + s

AMMO = ["bullet", "bullet_from_sulfur", "cannonball", "cannonball_from_sulfur", "lead_star", "exploding_star",
        "chain_shot", "fire_shot", "grapeshot"]
SHIP_PARTS = ["hull_plating", "hull_plating_adam", "reinforced_sailcloth", "heavy_gun_carriage", "ship_coating",
              "ballast_tank", "cola_engine"]
CYBORG = ["cyborg_iron_frame_plating", "cyborg_strong_right_arm", "cyborg_cola_engine_core", "cyborg_radical_beam_emitter",
          "cyborg_coup_de_vent_cannon", "cyborg_lunarian_plating", "radical_beam_emitter_from_core"]
FORGE_SMALL = ["skillful_whetstone", "great_whetstone", "scope", "long_barrel", "hair_trigger"]
DIALS = ["tone_dial", "water_dial", "milky_dial", "jet_dial", "axe_dial", "eisen_dial", "reject_dial",
         "flash_dial", "breath_dial", "flame_dial", "impact_dial"]
TIER2 = ["takoyaki", "sea_king_ramen", "kibi_dango"]
TIER3 = ["wedding_cake_slice", "ambergris_roast", "diable_flambe"]

def perk(kind, chance, recipes=None, label=None):
    p = {"type": kind, "chance": chance}
    if recipes: p["recipes"] = recipes
    if label: p["label"] = label
    return p

UPGRADES = [
    # ---- Swordsmith's Forge: the blacksmith tree ----
    dict(id="stoked_bellows", station="swordsmith_forge", name="Stoked Bellows", icon=mc("blast_furnace"),
         description="A big leather bellows keeps the fire white-hot. Small parts come out in pairs more often.",
         cost=[I(mc("iron_ingot"), 8), I(mc("coal"), 16), I(mc("leather"), 4)],
         perks=[perk("bonus", 0.25, FORGE_SMALL, "whetstones and gun parts")]),
    dict(id="tempering_anvil", station="swordsmith_forge", name="Tempering Anvil", icon=mc("anvil"),
         parents=["stoked_bellows"], requires={"bounty": 30000000},
         description="A Wano-style anvil for folding steel. Lets you forge Sea King fangs into a blade.",
         cost=[I(mc("anvil")), I(op("tamahagane_ingot"), 8), I(op("sea_king_fang"), 2)]),
    dict(id="quench_trough", station="swordsmith_forge", name="Seawater Quench Trough", icon=mc("cauldron"),
         parents=["stoked_bellows"], requires={"boss": "smoker"},
         description="Quenching in seawater makes cleaner steel, so less of it is wasted.",
         cost=[I(mc("iron_block"), 6), I(mc("prismarine_shard"), 8), I(op("sea_pearl"), 2)],
         perks=[perk("save", 0.10)]),
    dict(id="dragon_hearth", station="swordsmith_forge", name="Dragon Hearth", icon=op("dragon_heartstone"),
         parents=["tempering_anvil", "quench_trough"], requires={"bounty": 500000000},
         description="A Punk Hazard dragon's heartstone burns forever. Master smiths waste almost nothing and sometimes make two.",
         cost=[I(op("dragon_heartstone")), I(op("kokuto_ingot"), 4), I(mc("magma_block"), 8)],
         perks=[perk("save", 0.20), perk("bonus", 0.10)]),

    # ---- Shipwright's Bench ----
    dict(id="sturdy_workbench", station="shipwright_bench", name="Sturdy Workbench", icon=mc("crafting_table"),
         description="A proper shipwright's bench with clamps and a good saw. Sometimes there's wood left for one more.",
         cost=[PLANKS(16), I(mc("iron_ingot"), 8), I(op("rope_coil"), 2)],
         perks=[perk("bonus", 0.10)]),
    dict(id="powder_room", station="shipwright_bench", name="Powder Room", icon=mc("tnt"),
         parents=["sturdy_workbench"], requires={"boss": "buggy"},
         description="A dry, safe room for gunpowder. Ammo batches come out bigger.",
         cost=[I(mc("gunpowder"), 16), I(op("sulfur"), 8), I(op("cannon"))],
         perks=[perk("bonus", 0.35, AMMO, "ammo")]),
    dict(id="drydock_crane", station="shipwright_bench", name="Drydock Crane", icon=op("anchor"),
         parents=["sturdy_workbench"], requires={"crew": "shipwright"},
         description="A crane like Water 7's docks. Ship parts waste less, and Adam wood makes hull plating in bulk.",
         cost=[I(mc("iron_block"), 4), I(op("rope_coil"), 8), I(op("anchor"))],
         perks=[perk("save", 0.20, SHIP_PARTS, "ship parts")]),
    dict(id="frankys_workshop", station="shipwright_bench", name="Franky's Workshop", icon=op("pacifista_core"),
         parents=["powder_room", "drydock_crane"], requires={"boss": "lucci"},
         description="SUPER! Pacifista cores and cola power a real cyborg workshop. Cyborg parts waste less, and a core replaces laser cores.",
         cost=[I(op("pacifista_core"), 2), I(op("cola_crate"), 4), I(mc("iron_block"), 4)],
         perks=[perk("save", 0.25, CYBORG, "cyborg parts")]),

    # ---- Ship's Galley: cooking tiers ----
    dict(id="brick_oven", station="ships_galley", name="Brick Oven (Cooking Tier II)", icon=mc("smoker"),
         requires={"islands": 3},
         description="A real oven for the galley. Unlocks Tier II dishes: Takoyaki, Sea King Ramen and Kibi Dango.",
         cost=[I(mc("bricks"), 24), I(mc("iron_ingot"), 4), I(mc("furnace"))],
         perks=[perk("bonus", 0.10)]),
    dict(id="spice_rack", station="ships_galley", name="Spice Rack", icon=mc("cocoa_beans"),
         parents=["brick_oven"],
         description="Spices from every island. Dishes stretch further.",
         cost=[I(mc("sweet_berries"), 8), I(mc("cocoa_beans"), 4), I(mc("sugar"), 8), I(mc("honey_bottle"), 2)],
         perks=[perk("bonus", 0.20)]),
    dict(id="sanjis_kitchen", station="ships_galley", name="Sanji's Kitchen (Cooking Tier III)", icon=op("ambergris"),
         parents=["brick_oven"], requires={"crew": "cook", "bounty": 100000000},
         description="A kitchen fit for the Baratie. Unlocks Tier III dishes: Wedding Cake, Ambergris Roast and Diable Flambe.",
         cost=[I(op("ambergris")), I(mc("gold_block"), 2), I(mc("cauldron")), I(mc("iron_block"), 2)],
         perks=[perk("save", 0.10)]),
    dict(id="all_blue_pantry", station="ships_galley", name="All Blue Pantry", icon=op("all_blue_kingfish"),
         parents=["spice_rack", "sanjis_kitchen"], requires={"islands": 10},
         description="Fish from every sea, kept fresh. The best cooks waste nothing.",
         cost=[I(op("all_blue_kingfish")), I(mc("blue_ice"), 8), I(mc("barrel"), 4)],
         perks=[perk("save", 0.15), perk("bonus", 0.10)]),

    # ---- Navigator's Desk: Dials ----
    dict(id="dial_bench", station="navigators_desk", name="Dial Bench", icon=op("dial_shell"),
         requires={"islands": 3},
         description="Tools for opening and charging Skypiea Dial shells. Unlocks the Tone, Water and Milky Dials.",
         cost=[I(op("dial_shell"), 4), I(mc("gold_ingot"), 2), I(mc("spyglass"))]),
    dict(id="weatheria_lab", station="navigators_desk", name="Weatheria Lab", icon=op("breath_dial"),
         parents=["dial_bench"], requires={"boss": "enel"},
         description="Weather science from the sky island Weatheria. Unlocks the Jet, Axe, Eisen and Reject Dials, and Dials waste fewer shells.",
         cost=[I(op("dial_shell"), 8), I(op("breath_dial")), I(op("flash_dial")), I(mc("copper_block"), 4)],
         perks=[perk("save", 0.20, DIALS, "Dials")]),
]

def R(id, station, result, ingredients, count=1, upgrade=None, **req):
    r = {"id": id, "station": station, "result": result, "count": count, "ingredients": ingredients}
    requires = dict(req)
    if upgrade: requires["upgrade"] = upgrade
    if requires: r["requires"] = requires
    return r

RECIPES = [
    R("sea_king_fang_blade", "swordsmith_forge", op("sea_king_fang_blade"),
      [I(op("sea_king_fang"), 3), I(op("tamahagane_ingot"), 2), I(mc("stick")), I(mc("leather"))], upgrade="tempering_anvil"),
    R("hull_plating_adam", "shipwright_bench", op("hull_plating"),
      [I(op("adam_planks"), 2), I(mc("iron_ingot"), 4), I(mc("iron_block"))], count=3, upgrade="drydock_crane"),
    R("radical_beam_emitter_from_core", "shipwright_bench", op("radical_beam_emitter"),
      [I(op("pacifista_core")), I(op("pacifista_scrap"), 2), I(mc("redstone"), 8)], upgrade="frankys_workshop"),
    # Dials
    R("tone_dial", "navigators_desk", op("tone_dial"), [I(op("dial_shell")), I(mc("note_block")), I(mc("amethyst_shard"), 2)], upgrade="dial_bench"),
    R("water_dial", "navigators_desk", op("water_dial"), [I(op("dial_shell")), I(mc("prismarine_shard"), 2), I(mc("kelp"), 4)], upgrade="dial_bench"),
    R("milky_dial", "navigators_desk", op("milky_dial"), [I(op("dial_shell")), I(mc("white_wool"), 4), I(mc("snowball"), 4)], upgrade="dial_bench"),
    R("jet_dial", "navigators_desk", op("jet_dial"), [I(op("dial_shell"), 2), I(op("breath_dial")), I(mc("feather"), 8), I(mc("phantom_membrane"))], upgrade="weatheria_lab"),
    R("axe_dial", "navigators_desk", op("axe_dial"), [I(op("dial_shell")), I(mc("iron_axe")), I(mc("feather"), 4), I(mc("flint"), 4)], upgrade="weatheria_lab"),
    R("eisen_dial", "navigators_desk", op("eisen_dial"), [I(op("dial_shell"), 2), I(mc("white_wool"), 8), I(mc("iron_ingot"), 4)], upgrade="weatheria_lab"),
    R("reject_dial", "navigators_desk", op("reject_dial"), [I(op("dial_shell"), 4), I(op("impact_dial")), I(mc("obsidian"), 4), I(mc("diamond"), 2)],
      upgrade="weatheria_lab", bounty=100000000),
    # Cooking tier II
    R("takoyaki", "ships_galley", op("takoyaki"), [I(mc("ink_sac")), I(mc("wheat"), 2), I(mc("egg"))], count=3, upgrade="brick_oven"),
    R("sea_king_ramen", "ships_galley", op("sea_king_ramen"), [I(op("cooked_sea_king_meat")), I(mc("wheat"), 3), I(mc("egg")), I(mc("bowl"))], upgrade="brick_oven"),
    R("kibi_dango", "ships_galley", op("kibi_dango"), [I(mc("wheat"), 2), I(mc("sugar"), 2), I(mc("sweet_berries"), 2)], count=3, upgrade="brick_oven"),
    # Cooking tier III
    R("wedding_cake_slice", "ships_galley", op("wedding_cake_slice"), [I(mc("cake")), I(mc("sugar"), 4), I(mc("glow_berries"), 2), I(mc("gold_ingot"))],
      count=4, upgrade="sanjis_kitchen"),
    R("ambergris_roast", "ships_galley", op("ambergris_roast"), [I(op("ambergris")), I(op("cooked_sea_king_meat"), 2), I(mc("golden_carrot"))],
      upgrade="sanjis_kitchen"),
    R("diable_flambe", "ships_galley", op("diable_flambe"), [I(op("cooked_sea_king_meat")), I(mc("blaze_powder")), I(mc("baked_potato"), 2)],
      upgrade="sanjis_kitchen"),
]

NAMES = {
    "sea_king_fang": "Sea King Fang", "ambergris": "Ambergris", "dragon_heartstone": "Dragon Heartstone",
    "pacifista_core": "Pacifista Core", "tone_dial": "Tone Dial", "jet_dial": "Jet Dial", "water_dial": "Water Dial",
    "milky_dial": "Milky Dial", "reject_dial": "Reject Dial", "axe_dial": "Axe Dial", "eisen_dial": "Eisen Dial",
    "sea_king_fang_blade": "Sea King Fang Blade", "takoyaki": "Takoyaki", "sea_king_ramen": "Sea King Ramen",
    "kibi_dango": "Kibi Dango", "wedding_cake_slice": "Wedding Cake Slice", "ambergris_roast": "Ambergris Roast",
    "diable_flambe": "Diable Flambe",
}
DESCRIPTIONS = {
    "sea_king_fang": "Rare Sea King drop. Forged into a blade at the Swordsmith's Forge (Tempering Anvil).",
    "ambergris": "Rare Island Whale drop. Needed for Sanji's Kitchen and the Ambergris Roast at the Ship's Galley.",
    "dragon_heartstone": "Rare Punk Hazard Dragon drop. Lights the Dragon Hearth at the Swordsmith's Forge.",
    "pacifista_core": "Rare Pacifista drop. Powers Franky's Workshop at the Shipwright's Bench.",
    "tone_dial": "Sneak + use to record a chat message (or a music disc in your other hand). Use to play it back.",
    "jet_dial": "Blasts you far forward, then lets you float down. Much stronger than a Breath Dial.",
    "water_dial": "Puts out fire on you and around you. Aim at a block to pour out water.",
    "milky_dial": "Lays a road of solid cloud ahead of you, even over water. It melts after 30 seconds.",
    "reject_dial": "Use to brace: hits in the next 3 s are stored. Use again to slam them back, double. It hurts you too.",
    "axe_dial": "A blade of wind that cuts everything in a line ahead.",
    "eisen_dial": "Puts up a wall of solid cloud in front of you. It melts after 30 seconds.",
    "sea_king_fang_blade": "A sword forged from Sea King fangs. Sharper than diamond.",
    "takoyaki": "Cooking Tier II. Haste and Water Breathing.",
    "sea_king_ramen": "Cooking Tier II. Strength II and a little Regeneration.",
    "kibi_dango": "Cooking Tier II. Luck and Speed.",
    "wedding_cake_slice": "Cooking Tier III. Absorption III, Regeneration II and Strength.",
    "ambergris_roast": "Cooking Tier III. Strength II, Resistance II and Fire Resistance for 6 minutes.",
    "diable_flambe": "Cooking Tier III. Fire Resistance, Speed II and Strength II.",
}
SOURCES = [
    ("sea_king_fang", "Rare drop: Sea King", "12% when you defeat a Sea King.", "Used at the Swordsmith's Forge after building the Tempering Anvil."),
    ("ambergris", "Rare drop: Island Whale", "20% when you defeat an Island Whale.", "Used at the Ship's Galley: Sanji's Kitchen upgrade and Ambergris Roast."),
    ("dragon_heartstone", "Rare drop: Punk Hazard Dragon", "8% when you defeat a Punk Hazard Dragon.", "Used to build the Dragon Hearth at the Swordsmith's Forge."),
    ("pacifista_core", "Rare drop: Pacifista", "15% when you defeat a Pacifista, or in lab chests.", "Used at the Shipwright's Bench: Franky's Workshop."),
]

def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False); f.write('\n')

def merge_list(path, entries, key):
    data = json.load(open(path))
    ids = {e[key] for e in entries}
    kept = [e for e in data if e.get(key) not in ids]
    write(path, kept + entries)

def main():
    for u in UPGRADES:
        u.setdefault("parents", []); u.setdefault("perks", [])
    write(os.path.join(RES, 'onepiece/station_upgrades.json'), UPGRADES)
    merge_list(os.path.join(RES, 'onepiece/station_recipes.json'), RECIPES, "id")

    a = os.path.join(RES, 'assets/onepiece')
    for name in NAMES:
        write(f'{a}/items/{name}.json', {"model": {"type": "minecraft:model", "model": f"onepiece:item/{name}"}})
        parent = "minecraft:item/handheld" if name == "sea_king_fang_blade" else "minecraft:item/generated"
        write(f'{a}/models/item/{name}.json', {"parent": parent, "textures": {"layer0": f"onepiece:item/{name}"}})
    write(f'{a}/blockstates/milky_cloud.json', {"variants": {"": {"model": "onepiece:block/milky_cloud"}}})
    write(f'{a}/models/block/milky_cloud.json', {"parent": "minecraft:block/cube_all", "textures": {"all": "onepiece:block/milky_cloud"}})

    lang = {f"item.onepiece.{k}": v for k, v in NAMES.items()}
    lang["block.onepiece.milky_cloud"] = "Milky Cloud"
    write(os.path.join(RES, 'assets/onepiece_workshop/lang/en_us.json'), lang)

    desc_path = os.path.join(RES, 'onepiece/item_descriptions.json')
    desc = json.load(open(desc_path))
    for k, v in DESCRIPTIONS.items():
        desc[op(k)] = v
    write(desc_path, desc)

    src_path = os.path.join(RES, 'onepiece/item_sources.json')
    cards = [{"item": op(item), "title": title, "icon": op(item), "notes": [a1, a2]} for item, title, a1, a2 in SOURCES]
    merge_list(src_path, cards, "item")
    print(f"{len(UPGRADES)} upgrades, {len(RECIPES)} recipes, {len(NAMES)} items")

main()
