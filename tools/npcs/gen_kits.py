import json
def lo(style, weapons=None, weight=1, off=None):
    d = {"style": style, "weight": weight}
    if weapons: d["weapons"] = weapons
    if off: d["offhand"] = off
    return d
SW = "minecraft:"; OP = "onepiece:"
kits = [
 # ---------------- Marines and the World Government (entity onepiece:marine)
 dict(id="marine_recruit", faction="marine", crews=["Marines"], name="{rank} {surname}", ranks=["Seaman Recruit", "Seaman Apprentice"],
      skins=["marine_grunt"], loadouts=[lo("sword", [SW+"wooden_sword", SW+"stone_sword"], 3), lo("gunner", [OP+"flintlock_pistol"], 1)],
      health=18, damage=3, berries=1, bounty=200000),
 dict(id="marine", faction="marine", crews=["Marines"], name="{rank} {surname}", ranks=["Seaman", "Petty Officer", "Chief Petty Officer"],
      skins=["marine_grunt"], loadouts=[lo("sword", [SW+"iron_sword", SW+"stone_sword"], 4), lo("brawler", None, 1),
      lo("heavy", [OP+"seastone_jitte", SW+"iron_axe"], 1), lo("gunner", [OP+"flintlock_pistol"], 2)],
      health=24, damage=5, berries=2, bounty=400000),
 dict(id="marine_rifle", faction="marine", crews=["Marines"], name="{rank} {surname}", ranks=["Seaman", "Petty Officer", "Master Chief Petty Officer"],
      skins=["marine_rifle"], loadouts=[lo("gunner", [OP+"marine_rifle", OP+"flintlock_pistol"], 4), lo("sniper", [OP+"marine_rifle"], 1),
      lo("bomber", None, 1)], health=20, damage=5, berries=2, bounty=400000),
 dict(id="marine_officer", faction="marine", crews=["Marines"], name="{rank} {surname}", ranks=["Ensign", "Lieutenant Junior Grade", "Lieutenant", "Lieutenant Commander"],
      skins=["marine_officer"], loadouts=[lo("sword", [SW+"iron_sword", SW+"diamond_sword"], 3), lo("haki", [SW+"iron_sword"], 1),
      lo("gunner", [OP+"flintlock_pistol"], 1), lo("heavy", [OP+"seastone_jitte"], 1)],
      health=40, damage=7, armor=4, berries=3, bounty=1000000),
 dict(id="elite_marine", faction="marine", crews=["Marines"], name="{rank} {surname}", ranks=["Commander", "Captain"],
      skins=["marine_captain"], loadouts=[lo("sword", [SW+"diamond_sword"], 3), lo("haki", [SW+"diamond_sword", None], 2),
      lo("heavy", [OP+"seastone_jitte", SW+"diamond_axe"], 1), lo("brawler", None, 1), lo("gunner", [OP+"tommy_gun"], 1)],
      health=70, damage=10, armor=6, berries=8, bounty=3000000),
 dict(id="vice_admiral", faction="marine", crews=["Marines"], name="{rank} {surname}", ranks=["Rear Admiral", "Vice Admiral"],
      skins=["vice_admiral"], loadouts=[lo("haki", [SW+"netherite_sword", None], 3), lo("brawler", None, 1),
      lo("heavy", [SW+"netherite_axe", SW+"mace"], 1), lo("sword", [SW+"netherite_sword"], 1)],
      health=140, damage=13, armor=10, berries=25, bounty=30000000, knockbackResistance=0.6),
 dict(id="cp_agent", faction="marine", crews=["CP1", "CP2", "CP5", "CP7", "CP9"], name="{crew} Agent {name}", ranks=["Agent"],
      skins=["cp_agent"], loadouts=[lo("rokushiki", None, 3), lo("sword", [SW+"iron_sword"], 1), lo("gunner", [OP+"flintlock_pistol"], 1)],
      health=40, damage=8, armor=4, berries=6, bounty=2000000, speed=0.33),
 dict(id="cp0_agent", faction="marine", crews=["CP0"], name="CP0 Agent {name}", ranks=["Agent"],
      skins=["cp0_agent"], loadouts=[lo("rokushiki", None, 3), lo("haki", [SW+"netherite_sword"], 1)],
      health=80, damage=12, armor=8, berries=15, bounty=15000000, speed=0.34),
 dict(id="pacifista", faction="marine", crews=["World Government"], name="Pacifista PX-{num}", ranks=["Pacifista"],
      skins=["pacifista"], loadouts=[lo("beam", None, 3), lo("brawler", None, 1)],
      health=120, damage=14, armor=12, berries=20, bounty=20000000, knockbackResistance=0.9, speed=0.26, scale=3.83),   # Kuma-sized, 689 cm (HumanNpc shrinks them to fit indoors)
 dict(id="seraphim", faction="marine", crews=["World Government"], name="Seraphim S-{name}", ranks=["Seraphim"],
      skins=["seraphim"], loadouts=[lo("beam", None, 2), lo("haki", [SW+"netherite_sword"], 1), lo("sword", [SW+"netherite_sword"], 1)],
      health=110, damage=14, armor=10, berries=25, bounty=40000000, knockbackResistance=0.6),
 dict(id="jailer", faction="marine", crews=["Impel Down"], name="{rank} {surname}", ranks=["Guard", "Jailer", "Head Jailer"],
      skins=["jailer"], loadouts=[lo("heavy", [SW+"iron_axe", SW+"mace", OP+"seastone_jitte"], 3), lo("sword", [SW+"iron_sword"], 1),
      lo("gunner", [OP+"marine_rifle"], 1)], health=40, damage=7, armor=6, berries=4, bounty=1000000),
 # ---------------- Pirates and outlaws (entity onepiece:sea_pirate)
 dict(id="bandit", faction="pirate", crews=["Higuma Bandits", "Mountain Bandits", "Dadan Family"], name="{crew} {name}", ranks=["Bandit"],
      skins=["bandit"], loadouts=[lo("heavy", [SW+"wooden_axe", SW+"stone_axe"], 2), lo("sword", [SW+"stone_sword"], 1), lo("brawler", None, 1)],
      health=18, damage=3, berries=1),
 dict(id="rookie_pirate", faction="pirate", crews=["*"], name="{crew} {name}", ranks=["Deckhand"],
      skins=["rookie"], loadouts=[lo("sword", [SW+"wooden_sword", SW+"stone_sword"], 3), lo("brawler", None, 1), lo("gunner", [OP+"flintlock_pistol"], 1)],
      health=18, damage=3, berries=1),
 dict(id="buggy_pirate", faction="pirate", crews=["Buggy Pirates"], name="{crew} {name}", ranks=["Clown"],
      skins=["buggy"], loadouts=[lo("bomber", None, 2), lo("sword", [SW+"stone_sword", OP+"buggy_knife"], 2), lo("brawler", None, 1)],
      health=20, damage=4, berries=2),
 dict(id="pirate", faction="pirate", crews=["*"], name="{crew} {name}", ranks=["Deckhand", "Gunner's Mate", "Bosun"],
      skins=["deckhand"], loadouts=[lo("sword", [SW+"iron_sword", SW+"stone_sword"], 3), lo("heavy", [SW+"iron_axe"], 2), lo("brawler", None, 1),
      lo("gunner", [OP+"flintlock_pistol"], 1), lo("bomber", None, 1)], health=24, damage=5, berries=2),
 dict(id="pirate_gunner", faction="pirate", crews=["*"], name="{crew} {name}", ranks=["Gunner"],
      skins=["deckhand"], loadouts=[lo("gunner", [OP+"flintlock_pistol", OP+"tommy_gun"], 3), lo("sniper", [OP+"marine_rifle"], 1), lo("bomber", None, 1)],
      health=22, damage=5, berries=2),
 dict(id="pirate_captain", faction="pirate", crews=["*"], name="Captain {epithet} {name}", ranks=["Captain"],
      skins=["pirate_captain"], loadouts=[lo("sword", [SW+"diamond_sword", SW+"iron_sword"], 2), lo("haki", [SW+"iron_sword", None], 1),
      lo("gunner", [OP+"flintlock_pistol"], 1), lo("heavy", [SW+"iron_axe"], 1)],
      health=60, damage=8, armor=4, berries=12, knockbackResistance=0.3),
 dict(id="fishman", faction="pirate", crews=["Arlong Pirates", "New Fish-Man Pirates", "Flying Pirates"], name="{crew} {name}", ranks=["Fish-Man"],
      skins=["fishman"], loadouts=[lo("fishman", [SW+"trident", None, SW+"iron_sword"], 3), lo("sword", [OP+"kiribachi", SW+"iron_sword"], 1)],
      health=34, damage=6, armor=2, berries=3, knockbackResistance=0.3),
 dict(id="baroque_agent", faction="pirate", crews=["Baroque Works"], name="{rank} {name}", ranks=["Billions", "Millions", "Frontier Agent"],
      skins=["baroque"], loadouts=[lo("sword", [SW+"iron_sword"], 2), lo("gunner", [OP+"flintlock_pistol"], 1), lo("bomber", None, 1),
      lo("brawler", None, 1)], health=26, damage=5, berries=3),
 dict(id="bounty_hunter", faction="pirate", crews=[""], name="{epithet} {name}", ranks=["Bounty Hunter"],
      skins=["bounty_hunter"], loadouts=[lo("sword", [SW+"iron_sword"], 2), lo("gunner", [OP+"flintlock_pistol"], 2), lo("sniper", [OP+"marine_rifle"], 1)],
      health=26, damage=6, berries=4),
 dict(id="gifter", faction="pirate", crews=["Beasts Pirates"], name="{rank} {name}", ranks=["Waiter", "Pleasure", "Gifter"],
      skins=["gifter"], loadouts=[lo("heavy", [SW+"diamond_axe", SW+"iron_axe", SW+"mace"], 3), lo("brawler", None, 1), lo("sword", [SW+"iron_sword"], 1)],
      health=40, damage=8, armor=4, berries=5, knockbackResistance=0.3),
 dict(id="headliner", faction="pirate", crews=["Beasts Pirates"], name="Headliner {epithet} {name}", ranks=["Headliner"],
      skins=["headliner"], loadouts=[lo("heavy", [SW+"netherite_axe", SW+"mace"], 2), lo("haki", [SW+"diamond_sword"], 1), lo("sword", [SW+"diamond_sword"], 1)],
      health=60, damage=10, armor=6, berries=10, knockbackResistance=0.5, scale=1.15),
 dict(id="donquixote", faction="pirate", crews=["Donquixote Pirates"], name="{crew} {name}", ranks=["Underling", "Officer"],
      skins=["donquixote"], loadouts=[lo("gunner", [OP+"flintlock_pistol", OP+"tommy_gun"], 2), lo("sword", [SW+"iron_sword"], 1), lo("sniper", [OP+"marine_rifle"], 1)],
      health=30, damage=6, armor=2, berries=4),
 dict(id="whitebeard_pirate", faction="pirate", crews=["Whitebeard Pirates"], name="{crew} {name}", ranks=["Division Member", "Division Veteran"],
      skins=["whitebeard"], loadouts=[lo("sword", [SW+"diamond_sword"], 2), lo("haki", [SW+"diamond_sword", None], 1), lo("brawler", None, 1),
      lo("heavy", [SW+"diamond_axe"], 1)], health=50, damage=9, armor=6, berries=8, knockbackResistance=0.3),
 dict(id="blackbeard_pirate", faction="pirate", crews=["Blackbeard Pirates"], name="{crew} {name}", ranks=["Crewman"],
      skins=["blackbeard"], loadouts=[lo("sword", [SW+"netherite_sword", SW+"diamond_sword"], 2), lo("gunner", [OP+"tommy_gun"], 1), lo("heavy", [SW+"netherite_axe"], 1)],
      health=50, damage=9, armor=6, berries=8),
]
for k in kits:
    for l in k["loadouts"]:
        if "weapons" in l: l["weapons"] = [w or "" for w in l["weapons"]]
P = ["rookie_pirate", "pirate", "pirate_gunner"]; M = ["marine", "marine_rifle"]
def g(kits_, leader=None, weight=1, size=(2, 4)):
    d = {"kits": kits_, "weight": weight, "min": size[0], "max": size[1]}
    if leader: d["leader"] = leader
    return d
patrols = {
 "default": [g(P, "pirate_captain", 3), g(M, "marine_officer", 2)],
 "onepiece:east_blue": [g(["rookie_pirate", "rookie_pirate", "pirate"], "pirate_captain", 3), g(["buggy_pirate"], None, 2),
                        g(["bandit"], None, 1), g(["marine_recruit", "marine_recruit", "marine"], "marine_officer", 2)],
 "onepiece:alabasta": [g(["baroque_agent"], None, 3), g(M, "marine_officer", 1), g(["bandit"], None, 1)],
 "onepiece:jaya": [g(P, "pirate_captain", 2), g(["blackbeard_pirate"], None, 1), g(["bounty_hunter"], None, 1, (1, 3))],
 "onepiece:sabaody": [g(P, "pirate_captain", 2), g(M, "elite_marine", 2), g(["bounty_hunter"], None, 1, (1, 3)), g(["pacifista"], None, 1, (1, 1))],
 "onepiece:fishman_reef": [g(["fishman"], None, 3)],
 "onepiece:dressrosa": [g(["donquixote"], None, 3), g(P, "pirate_captain", 1)],
 "onepiece:whole_cake": [g(P, "pirate_captain", 1)],
 "onepiece:wano": [g(["gifter"], "headliner", 3)],
 "onepiece:onigashima": [g(["gifter"], "headliner", 3)],
 "onepiece:punk_hazard_frozen": [g(["marine", "marine_rifle"], "elite_marine", 1)],
 "onepiece:punk_hazard_burning": [g(["marine", "marine_rifle"], "elite_marine", 1)],
 "onepiece:egghead": [g(["cp_agent", "marine"], "cp0_agent", 2), g(["pacifista"], None, 1, (1, 2)), g(["seraphim"], None, 1, (1, 1))],
 "onepiece:red_line": [g(M, "vice_admiral", 1), g(["cp_agent"], "cp0_agent", 1)],
 "onepiece:amazon_lily": [],
 "onepiece:skypiea": [],
 "onepiece:elbaph": [],
 "onepiece:zou": [],
 "onepiece:little_garden": [],
}
kits += [
 # ---------------- Dungeon guards and mini-bosses (tools/dungeons; the bosses' real stats are in onepiece/dungeon_bosses.json)
 dict(id="tomb_guard", faction="pirate", crews=["Tomb Raiders"], name="{rank} {name}", ranks=["Tomb Raider", "Raider Veteran"],
      skins=["tomb_guard"], loadouts=[lo("sword", [SW+"iron_sword", SW+"golden_sword"], 3), lo("heavy", [SW+"iron_axe"], 2), lo("gunner", [OP+"flintlock_pistol"], 1)],
      health=32, damage=6, armor=3, berries=4),
 dict(id="tomb_warden", faction="pirate", crews=["Tomb Raiders"], name="Tomb Warden Hassad", ranks=["Warden"],
      skins=["tomb_guard"], loadouts=[lo("heavy", [SW+"diamond_axe"], 1)], health=160, damage=9, armor=6, berries=30, knockbackResistance=0.6, scale=1.2),
 dict(id="undead_pirate", faction="pirate", crews=["the Restless Dead"], name="Restless {name}", ranks=["Restless Dead"],
      skins=["undead"], loadouts=[lo("sword", [SW+"iron_sword", SW+"stone_sword"], 3), lo("brawler", None, 1)],
      health=30, damage=6, armor=2, berries=3),
 dict(id="sword_shade", faction="pirate", crews=["the Restless Dead"], name="Shade of the Sword God", ranks=["Shade"],
      skins=["undead"], loadouts=[lo("sword", [SW+"diamond_sword"], 1)], health=220, damage=11, armor=6, berries=40, speed=0.34, knockbackResistance=0.5, scale=1.1),
 dict(id="ronin", faction="pirate", crews=["Wandering Ronin"], name="Ronin {name}", ranks=["Ronin", "Ronin Veteran"],
      skins=["ronin"], loadouts=[lo("sword", [SW+"iron_sword", SW+"diamond_sword"], 3), lo("haki", [SW+"diamond_sword"], 1)],
      health=45, damage=8, armor=4, berries=5, knockbackResistance=0.2),
 dict(id="ronin_lord", faction="pirate", crews=["Wandering Ronin"], name="Ronin Lord Kagemaru", ranks=["Ronin Lord"],
      skins=["ronin"], loadouts=[lo("haki", [SW+"netherite_sword"], 1, SW+"diamond_sword")], health=320, damage=14, armor=8, berries=60, knockbackResistance=0.5, scale=1.1),
 dict(id="cursed_smith", faction="pirate", crews=["Beasts Pirates"], name="Kurogane the Cursed Smith", ranks=["Cursed Smith"],
      skins=["smith"], loadouts=[lo("heavy", [SW+"mace", SW+"netherite_axe"], 1)], health=320, damage=15, armor=10, berries=60, knockbackResistance=0.8, scale=1.3),
 dict(id="rocks_pirate", faction="pirate", crews=["Rocks Pirates"], name="{crew} {name}", ranks=["Old Guard", "Veteran"],
      skins=["rocks"], loadouts=[lo("sword", [SW+"netherite_sword", SW+"diamond_sword"], 2), lo("haki", [SW+"diamond_sword"], 1),
      lo("gunner", [OP+"tommy_gun"], 1), lo("heavy", [SW+"netherite_axe"], 1)], health=60, damage=10, armor=7, berries=8, knockbackResistance=0.3),
 dict(id="rocks_captain", faction="pirate", crews=["Rocks Pirates"], name="Gorvak the Undying", ranks=["Captain"],
      skins=["rocks"], loadouts=[lo("haki", [SW+"netherite_axe"], 1)], health=450, damage=17, armor=12, berries=100, knockbackResistance=0.9, scale=1.35),
]

out = {"_comment": "Pirate and Marine NPC kits (com.onepiecemod.npc). Each kit picks a skin from a skin group (tools/npcs/gen_npc_skins.py), "
       "a crew ('*' = a random made-up crew), a rank and a loadout (combat style + weapon). Styles: sword, brawler, heavy, haki, rokushiki, fishman, "
       "gunner, sniper, bomber, beam. patrols = which groups walk around each biome ('default' for any other island or beach).",
       "kits": kits, "patrols": patrols}
import os, sys
SRC = sys.argv[1] if len(sys.argv) > 1 else '/mnt/project-files/one-piece-mod/source'
json.dump(out, open(os.path.join(SRC, 'src/main/resources/onepiece/npc_kits.json'), 'w'), indent=1)
print(len(kits))
