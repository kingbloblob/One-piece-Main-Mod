"""scaling.py: turn real-world dimensions (metres) into a block plan.

CLI:  python scaling.py --max 400 --world-height 300 \
          island_diameter=520 h_tower=150 door_width=2.5 h_door=4
Dimensions named h_* are vertical (checked against the world height limit); all
others are horizontal. Choose either --bpm (blocks per metre) or --max (largest
horizontal extent in blocks). Prints a table with warnings for features that
fall below playable minimums.

Python:  from scaling import plan; rows, bpm = plan({...}, max_extent=400)
"""
import argparse

MIN_BLOCKS = {  # playable minimums (blocks), matched on keyword in the feature name
    "door_width": 1, "h_door": 3, "window": 1, "h_window": 2, "corridor": 3,
    "h_ceiling": 3, "stair": 1, "wall_thickness": 1, "h_floor": 3,
}


def plan(dims, bpm=None, max_extent=None, world_height=384):
    horiz = {k: v for k, v in dims.items() if not k.startswith("h_")}
    vert = {k: v for k, v in dims.items() if k.startswith("h_")}
    if bpm is None:
        if not max_extent:
            raise ValueError("give bpm or max_extent")
        biggest = max(horiz.values()) if horiz else 1
        bpm = max_extent / biggest
    if vert:
        cap = (world_height - 8) / max(vert.values())
        if bpm > cap:
            bpm = cap
    rows = []
    for k, v in dims.items():
        raw = v * bpm
        n = max(1, round(raw))
        note = ""
        for key, mn in MIN_BLOCKS.items():
            if key in k and n < mn:
                note = f"raised to playable minimum {mn}"
                n = mn
        if not note and raw < 0.75:
            note = "below 1 block: detail lost, abstract it"
        rows.append((k, v, round(raw, 2), n, note))
    return rows, bpm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dims", nargs="+", help="name=metres")
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--max", type=float, dest="max_extent")
    ap.add_argument("--world-height", type=int, default=384)
    a = ap.parse_args()
    dims = {k: float(v) for k, v in (d.split("=") for d in a.dims)}
    rows, bpm = plan(dims, a.bpm, a.max_extent, a.world_height)
    print(f"scale: {bpm:.3f} blocks per metre ({1 / bpm:.2f} m per block)")
    print(f"{'feature':24s}{'metres':>9s}{'exact':>9s}{'blocks':>8s}  note")
    for k, v, raw, n, note in rows:
        print(f"{k:24s}{v:9.1f}{raw:9.2f}{n:8d}  {note}")
    if bpm < 0.5:
        print("WARNING: under 0.5 blocks/m. Expect strongly simplified architecture.")


if __name__ == "__main__":
    main()
