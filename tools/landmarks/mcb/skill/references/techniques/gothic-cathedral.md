# Technique card: twin-spired Gothic cathedral (studied from a user-supplied model)

Source: a Minecraft cathedral build supplied by the user (permission confirmed), analysed with
`scripts/mesh_analyze.py`. These are measurements and observations for learning proportions
and methods. Do not recreate the model itself. Numbers are blocks above the ground plane.
**Measured** = read from the geometry. **Inferred** = judged from textures or shapes.

## Contents
- Overall proportions
- Height system (tiers)
- Towers and spires
- Roofs, gables and rhythm
- Surface and palette
- Reusable recipe
- Scaling rules

## Overall proportions (measured)
- Footprint 53 wide x 113 long (1 : 2.1), cruciform: nave with two aisles, transept, apse.
- Total height 113 (2.1 x the width). The two west towers are the tallest points; a spire over
  the crossing reaches +74.
- Cross-section widths: whole 53; nave about 15 (inner roof base x30-44); each aisle about 10;
  a 5-block zone on each side holds the outer buttress piers.
- Whole site is a plaza with a thick ground slab (ground at y=20 of 133) and low houses around it.

## Height system (measured, nave cross-section)
| Element | Height | Notes |
|---|---|---|
| Outer buttress piers | +7 to +12 (one at +15) | 3 wide, every 6-7 blocks along the nave |
| Aisle roofs | +12 to +13, then stepping 18, 20, 21 | a stepped lean-to rising toward the nave (flying-buttress zone) |
| Clerestory wall | +21 to +34 | about 13 tall vertical wall above the aisle roof |
| Nave eaves | +34 | |
| Nave ridge | +44 | roof rises 1 block per block across (45 degrees); steeper last 2 layers |
| Ridge crest | alternates +41 / +44 along the ridge | a 3-block sawtooth every 2 blocks (inferred: iron bars) |
| Crossing spire | +57, +64, +74 | 5-wide pyramid on the ridge |
| West towers | +113 | see below |
Ratios: ridge / nave width about 3 : 1 (interior nave 15 wide, 44 high); clerestory about 13
high between aisle roof and eaves; aisle height about 1/3 of ridge height.

## Towers and spires (measured)
- Tower centres 22 apart (x = 26 and 48), facade width 53; gap between towers about 6.
- Tower shaft 17 x 17 square from about +31 to +55 (about 25 tall), then 15 at +60.
- Spire taper (width at height): 15 @+60, 9 @+70, 7 @+80, 5 @+90, 3 @+100, finial 3x1 @+110.
  So: a large step from 15 to 9 (octagon-like transition), then 2 blocks narrower per 10 up.
- Aspect: whole tower 6.6 : 1; spire about 3.4 : 1 (height : base width).
- Use `mcparts.square_spire(b, cx, cz, y0, base_w, height, block)` and `pinnacle(...)` for corner pinnacles.

## Roofs, gables and rhythm (measured)
- Transept ends have a **triple gable**: central peak +40 flanked by two at +38, stepped
  profile 30-36-38-36-30 / 35-40-35 / 30-36-38-36-30; overall about 36 wide.
- Buttress piers repeat every 6 to 7 blocks (3 wide, peak +11/+12, rare +15 near the transept).
  Facade rhythm detector found bay spacing 12-13 in the nave sides (two buttress bays).
- Symmetry of the cathedral about its long axis is very high; the surrounding buildings break it.
- About 54% of surface faces are sub-block geometry (stairs, slabs, walls, bars): half of the
  detail is half-steps, not full cubes.

## Surface and palette (identified from the atlas by eye; names are inferred)
- Walls: stone bricks (about 19% of all surface blocks) and stone-slab side panels (about 9%).
- Dark spruce planks (12%) laid as thin vertical lines over the stone: Gothic tracery/bundled shafts
  (inferred). Oak/birch planks and bricks dominate the surrounding houses.
- Roofs and spire skins: teal oxidized/weathered copper tiles (nave roof about 56%).
- Pinnacles, finials and the ridge crest: iron bars (nave roof top about 16%, spire tops about 37%).
- Role split: stone grey for mass, dark wood for linework, teal copper for roofs, iron for spikes.

## Reusable recipe (half-scale demo: `examples/gothic_church_demo.py`)
1. Footprint 1 : 2 cross plan; nave:aisle width about 3 : 2 each side; buttress zone about 1/10.
2. Five height tiers: buttress piers, aisle roofs (stepped lean-to), clerestory wall, 45-degree
   nave roof with crested ridge, then towers and crossing spire above everything.
3. Piers every 6-7 blocks, 3 wide, each topped by a pinnacle and joined to the clerestory by a
   stepped `flying_buttress`.
4. Twin towers about 1/3 of the facade width each, shaft then taper; central portal gable between.
5. Pointed (lancet) windows with a slab trim ring: `pointed_opening(...)`.
6. Dark vertical lines on stone for tracery; iron bars for every spike; copper stairs/slabs
   for roofs.

## Scaling rules
- Keep ratios, not block counts: width : length 1 : 2, tower height : facade width about 2 : 1,
  spire : base 3.4 : 1, pier spacing about 1/8 of the nave side per bay.
- Below about half scale, drop the stepped 15-to-9 transition and use a straight taper, and merge
  the flying buttresses into plain sloped piers.
- Never go below 3 blocks for a pier or a lancet window opening.
