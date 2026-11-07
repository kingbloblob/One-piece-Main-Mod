"""Adds the life skill hook lines to files owned by other features. Safe to run again (skips lines already there).

Usage: python3 tools/lifeskills/hooks.py <project root>
"""
import sys, pathlib

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
J = root / "src/main/java/com/onepiecemod"

def patch(path, marker, anchor, insert, before=True):
    text = path.read_text(encoding="utf-8")
    if marker in text:
        print("ok   ", path.name); return
    if anchor not in text:
        sys.exit(f"FAIL  {path}: anchor not found: {anchor!r}")
    i = text.index(anchor)
    if not before:
        i = text.index("\n", i) + 1
    else:
        i = text.rfind("\n", 0, i) + 1
    path.write_text(text[:i] + insert + text[i:], encoding="utf-8")
    print("added", path.name)

patch(J / "OnePieceMod.java", "lifeskill.LifeSkills.initialize",
      "com.onepiecemod.advancement.AdvancementFeature.initialize();",
      "\t\tcom.onepiecemod.lifeskill.LifeSkills.initialize(); // Life skills: Farming, Mining, Cooking, Smithing levels and perks.\n")
patch(J / "crafting/StationPayloads.java", "LifeSkillHooks.onStationCraft",
      "ItemStack stack = recipe.resultStack();",
      "\t\t\tcom.onepiecemod.lifeskill.LifeSkillHooks.onStationCraft(player, recipe.stationType().id(), stack);\n", before=False)
patch(root / "src/main/resources/fabric.mod.json", "onepiece.lifeskill.mixins.json",
      '"onepiece.ship.mixins.json",',
      '\t\t"onepiece.lifeskill.mixins.json",\n', before=False)
