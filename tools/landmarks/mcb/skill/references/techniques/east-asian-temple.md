# Technique card: two-tier East Asian temple hall (studied from a user-supplied model)

Source: "Thunderclap Temple" by patrix (https://sketchfab.com/3d-models/thunderclap-temple-5ad2c436655e41ee923d358de0fafeeb),
CC-BY-SA-4.0, supplied by the user, read with `scripts/mesh_analyze.py` (one atlas material, so block
names come from texture tiles identified by eye). Measurements for learning; do not recreate the model.
CC-BY-SA: a build shared that is based on it must credit the author and use the same licence.
**Measured** = from the block grid. **Inferred** = judged from textures or shapes.
Heights are above the plaza (plaza = 0).

## Contents
- Overall layout
- Height system
- Plan and column rhythm
- Roofs (the part that makes the style)
- Walls, brackets and details
- Palette roles
- Reusable recipe (mcasian parts)
- Scaling rules
- Japanese vs Chinese variations

## Overall layout (measured)
- Whole site 69 x 73 incl. plaza, 47 tall (height : width 0.64). Perfectly mirror-symmetric on both axes.
- Enclosed hall about 43 x 23 (long axis = facade), wrapped by a veranda of free-standing columns
  (ring about 49 x 33). Lower eaves cover about 61 x 45. Upper storey about 35 x 17.
- Four stone lanterns on the plaza; a flight of steps on the axis of the widest (centre) bay.
- About 66% of all faces are partial blocks (stairs, slabs, walls, fences, trapdoors): the style lives
  in half steps.

## Height system (measured)
| Element | Height | Notes |
|---|---|---|
| Plaza paving | 0 to 3 | cobble / andesite / stone mix, snow patches |
| Stone platform | 4 to 6 | 3 high, capped with stone bricks |
| Ground storey | 7 to 16 | 10 high, red columns + lattice panels |
| Lower (pent) roof | 17 to 23 | eave tip at +19/+20, corners +1-2 higher; rises to the upper floor |
| Upper storey | 24 to 31 | 8 high, inset 4-6 from the hall walls |
| Upper eave | 32 to 33 | overhang 9 (ends) to 11 (front) past the upper walls ~= upper storey height |
| Upper roof to ridge | 33 to 44 | rise 11 over a half depth of 19 (0.55-0.6), concave |
| Ridge crest + ornaments | 44 to 46 | 2-block crest; end horns and a centre finial reach +46 |
Ratios: ground storey : upper storey = 10 : 8; roof zone (both roofs) = about half the total height.

## Plan and column rhythm (measured)
- Facade bays (veranda columns): 8, 10, 12, 10, 8 -> centre bay widest, then symmetric shrinking.
  `bay_positions(start, end, 5)` reproduces this.
- Short side: columns about every 10 (3 bays).
- Upper storey: tighter rhythm, columns every 5.
- Veranda margin 3-4 blocks outside the hall walls; lower eave overhang about 6 past the veranda.

## Roofs (measured; this is the signature)
- Concave profile: flat at the eaves, steep near the ridge. Front slope of the upper roof climbs only
  ~1 block over its first 10 blocks, then 1:1 for the last 3-4 before the ridge.
  Model: height = rise x (distance from eave / half depth) ^ 2 (`power=2`).
- Hip-and-gable (irimoya / xieshan) upper roof: hipped skirt at the ends (7 deep at full size), then a
  vertical gable triangle and a long ridge running nearly the full building length (39 of 53).
- Lower roof is a hipped pent roof that stops against the upper storey wall (`max_y` clip).
- Corners lift 1-2 blocks above the mid-eave line (upturned eaves), fading over ~8 blocks.
- Roof top = dark grey tiles; eave edges and hip lines in a lighter stone (smooth stone) so the roof
  outline reads; underside is wooden (soffit) - from below you see wood, from above grey.
- Ridge: 2-block crest with end ornaments (horns / chiwei / shibi) and a centre finial.

## Walls, brackets and details (measured / inferred)
- Ground storey walls: red columns and red lower panels, white lattice panels above (white paper
  with a dark grid; the studied rows alternate white and dark).
- Stripped-log brackets (dougong / tokyo) under the eaves at each column, stepping outward (~15% of the
  roof underside faces are log, inferred as brackets and rafters).
- Stone lanterns (toro): ~7 tall: base, thin post, firebox with a light, wide 5x5 cap, finial.
  Keep them on open ground (beside the steps or at plaza corners) where they clear the eaves.
- Light snow and moss on the paving add age (optional `mcparts.weather`).

## Palette roles (inferred names; tiles identified by eye)
- Roof top: deepslate tiles + deepslate bricks (~3:2), with smooth stone along eaves and hips.
- Underside / soffit / beams: spruce planks; brackets and rafters: stripped spruce (or dark) logs.
- Columns and accents: red (mangrove / red terracotta); ornaments on the ridge: mangrove planks.
- Panels: white (white wool or white concrete) with a dark wooden grid.
- Base: andesite / cobblestone / stone mix, stone-brick capping, stone-brick stairs.

## Reusable recipe (`scripts/mcasian.py`, demo `examples/asian_temple_demo.py`)
1. `temple_hall(b, x0, y0, z0, w=43, d=23, bays=5, two_storey=True)` builds platform, steps, hall,
   veranda, brackets, pent roof, upper storey and the irimoya roof with all ratios above, plus lanterns.
2. For custom buildings use the parts: `curved_roof(... style='hip'|'gable'|'irimoya', power=2,
   corner_lift=2, max_y=...)`, `bay_positions`, `column_row`, `brackets`, `lattice_wall`,
   `stone_platform`, `front_steps`, `stone_lantern`.
3. Check `render_elevations` (front: two tiers and lifted corners; side: gable triangle on top) and a
   `render_section` across the short axis (concave roof curve).

## Scaling rules
- Keep: centre bay widest; eave overhang ~ storey height; roof rise 0.55 x half depth; power 2.
- Hall depth below ~15: single storey (`two_storey=False`), 3 bays, corner_lift 1, platform 2 high.
  The roof then becomes visually dominant (about half the height), which is correct for small shrines.
- Never fewer than 3 bays on a facade; keep columns 1 wide with a stone base block.
- Pagodas: stack `curved_roof(style='hip')` tiers with each tier ~85% of the one below.

## Japanese vs Chinese variations (general knowledge, not measured from this model)
- Chinese halls: stronger corner upturn (raise corner_lift), brighter red and gold, glazed yellow or
  green roof tiles for important halls, more ridge figures.
- Japanese temples: subtler curve, darker unpainted wood or vermilion only on shrines, grey tiles or
  cypress-bark roofs, deeper eaves. Shinto shrines use gable roofs (`style='gable'`).
- For a named building, run `references/research-workflow.md` first.
