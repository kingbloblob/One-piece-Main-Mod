"""Writes the player list of achievements from gen_advancements.py.

Run:  python3 gen_guide.py OUTPUT.md
Ones listed in NEW get a **new** mark; change NEW when you add more.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_advancements as g  # noqa: E402

NEW_DATE = "2026-10-30"
NEW_FROM = "journey/first_catch"  # everything defined from here on is new

TABS = [
    ("journey", "The Grand Line (story, navigation, sea events, ship fights, fishing, Sea Train, New Game+)"),
    ("powers", "Hidden Power (fruits, Haki, styles, Pirate Level)"),
    ("pirate", "A Pirate's Life (bounty, bosses, crew, careers, Colosseum, Davy Back Fights, hideouts, raids)"),
    ("wonders", "Wonders of the World (landmarks, dungeons, creatures, pets, Vegapunk hunts, cyborgs, the deep sea)"),
]


def main(out):
    ids = [a["id"] for a in g.A]
    start = ids.index(NEW_FROM)
    new = set(ids[start:])
    shown = [a for a in g.A if a["parent"] is not None]
    lines = ["# One Piece Mod Achievements", "",
             f"{len(shown)} achievements in 4 tabs (press L in game). Ones marked **new** were added on {NEW_DATE} "
             f"({len(new)} of them). Hidden ones stay secret until earned.", ""]
    for tab, title in TABS:
        lines += [f"## {title}", ""]
        for a in shown:
            if not a["id"].startswith(tab + "/"):
                continue
            line = f"- **{a['title']}**"
            if a["frame"] != "task":
                line += f" [{a['frame']}]"
            if a.get("hidden"):
                line += " (hidden)"
            line += f": {a['desc']}"
            if a["id"] in new:
                line += " **new**"
            lines.append(line)
        lines.append("")
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(len(shown), "achievements written to", out)


if __name__ == "__main__":
    main(sys.argv[1])
