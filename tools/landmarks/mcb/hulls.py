"""Procedural sailing hulls for wrecks and beached ships (not for sailable ships: those come from tools/ships templates).

galleon() builds a ship in its own BigBuild (stern at x 0, keel at y 0, centre line z 0, bow +x) on top of
mcparts.ship, adding a stern castle with windows, gun ports with cannons and a figurehead. transfer() copies part
of it into a site with an offset, a list (sideways lean, a z shift per block of height), sinking and decay, so one
hull can become a ship broken in two on the sea floor or a caravel run up on a beach. Same coordinates as kit:
x east+, z south+."""
import math

import numpy as np

from mcb.kit import BigBuild, P, AIR
from mcb import nature as NT


def galleon(length=46, beam=13, depth=9, masts=3, hull="minecraft:dark_oak_planks", deck="minecraft:spruce_planks",
            sail="minecraft:white_wool", trim="minecraft:stripped_dark_oak_log[axis=x]", castle=True, guns=True,
            figure="minecraft:gold_block"):
    s = BigBuild(seed=1, y_min=-2, y_max=length + 20)
    P.ship(s, 0, 0, 0, length=length, beam=beam, depth=depth, masts=masts, hull=hull, deck=deck,
           rail="minecraft:dark_oak_fence", mast="minecraft:stripped_spruce_log", sail=sail, cabin=False)
    dy = depth - 2                                    # main deck
    hw = (beam - 1) // 2
    if castle:
        cl = int(length * 0.24)
        for t, (x2, w) in enumerate(((cl, hw - 1), (cl - 4, hw - 2))):
            y1 = dy + 1 + 4 * t
            s.fill(0, y1, -w, x2, y1 + 3, w, hull)
            s.fill(1, y1, -w + 1, x2 - 1, y1 + 2, w - 1, AIR)
            s.fill(0, y1 + 3, -w, x2, y1 + 3, w, deck)
            for z in range(-w + 2, w - 1, 3):
                s.set(0, y1 + 1, z, "minecraft:yellow_stained_glass_pane")
            for x in range(2, x2 - 1, 3):
                s.set(x, y1 + 1, -w, "minecraft:glass_pane"); s.set(x, y1 + 1, w, "minecraft:glass_pane")
            s.fill(0, y1 + 4, -w, x2, y1 + 4, -w, "minecraft:dark_oak_fence")
            s.fill(0, y1 + 4, w, x2, y1 + 4, w, "minecraft:dark_oak_fence")
        s.fill(cl, dy + 1, -1, cl, dy + 2, 1, AIR)
        s.fill(0, dy + 9, -hw + 3, 0, dy + 10, hw - 3, "minecraft:dark_oak_planks")
        s.fill(0, dy + 9, -1, 0, dy + 9, 1, "minecraft:gold_block")
    if guns:                                          # a gun deck one level under the main deck, ports with cannons
        gy = dy - 2
        for x in range(int(length * 0.28), int(length * 0.82), 4):
            col = s.get_region(x, gy, -hw - 1, x, gy, hw + 1)[0, 0, :]
            nz = np.nonzero(col)[0]
            if len(nz) < 2:
                continue
            zl, zr = int(nz[0]) - hw - 1, int(nz[-1]) - hw - 1
            s.set(x, gy, zl, "minecraft:black_concrete"); s.set(x, gy, zr, "minecraft:black_concrete")
            s.set(x, gy, zl + 1, "onepiece:cannon[facing=north]"); s.set(x, gy, zr - 1, "onepiece:cannon[facing=south]")
        s.fill(int(length * 0.25), gy - 1, -hw + 3, int(length * 0.85), gy - 1, hw - 3, deck)
    # figurehead: a mermaid-ish gold bust on the stem
    for k in range(5):
        s.set(length + k // 2, dy - 2 + k, 0, figure if k > 1 else trim)
    s.set(length + 2, dy + 3, 0, figure)
    return s


def transfer(dst, src, x1, x2, dx, dy, dz, lean=0.0, yaw=0.0, pivot=(0, 0), decay=0.0, seed=0, drop_above=None, keep=None):
    """Copy the src blocks with x1 <= x <= x2 into dst at (x + dx, y + dy, z + dz), leaning sideways (z += lean * y)
    and turned by `yaw` radians round `pivot` (x, z in src). decay: share of blocks lost (more near the top);
    drop_above: blocks above this src y are left out (snapped masts). Returns a function mapping a src point to dst."""
    rng = np.random.default_rng(seed)
    bx1, by1, bz1 = x1, src.y_min, -40
    reg = src.get_region(x1, src.y_min, -40, x2, src.y_max, 40)
    ca, sa = math.cos(yaw), math.sin(yaw)

    def where(x, y, z):
        px, pz = x - pivot[0], z - pivot[1]
        rx, rz = px * ca - pz * sa + pivot[0], px * sa + pz * ca + pivot[1]
        return int(round(rx + dx)), int(round(y + dy)), int(round(rz + dz + lean * y))
    ymax = src.y_max - src.y_min
    for (i, j, k) in zip(*np.nonzero(reg)):
        bid = reg[i, j, k]
        if bid == 1:
            continue
        x, y, z = bx1 + int(i), by1 + int(j), bz1 + int(k)
        if drop_above is not None and y > drop_above:
            continue
        if keep is not None and not keep(x, y, z):
            continue
        if decay and rng.random() < decay * (0.4 + 1.2 * (j / max(ymax, 1))):
            continue
        name = src.names[bid]
        dst.set(*where(x, y, z), name)
    return where


def tatter(bb, x1, y1, z1, x2, y2, z2, seed, share=0.55):
    """Rot sails: remove a share of the wool, darken the rest in patches."""
    reg = bb.get_region(x1, y1, z1, x2, y2, z2)
    rng = np.random.default_rng(seed)
    out = reg.copy()
    for i, name in enumerate(bb.names):
        if i > 1 and name.endswith("_wool"):
            m = reg == i
            r = rng.random(reg.shape)
            out[m & (r < share)] = 0
            out[m & (r >= share) & (r < share + 0.2)] = bb.register("minecraft:brown_wool")
            out[m & (r >= share + 0.2) & (r < share + 0.3)] = bb.register("minecraft:light_gray_wool")
    ch = out != reg
    if ch.any():
        bb._write(x1, y1, z1, x2, y2, z2, out, mask=ch)


def air_to_water(bb, top=None):
    """Seafloor builds: every air cell becomes sea water (unset cells stay the world's own). Above `top` air is left
    unset instead, so a build that reaches above a shallow sea never carries water sources up into the open air."""
    wid = bb.register("minecraft:water")
    for t in bb.tiles.values():
        if top is not None:
            k = top - bb.y_min + 1
            hi = t[:, k:, :]
            hi[hi == 1] = 0
        t[t == 1] = wid
