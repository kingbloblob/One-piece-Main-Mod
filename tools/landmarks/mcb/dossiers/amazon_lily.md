# Amazon Lily (structure id amazon_lily) dossier

Sources: anime/manga memory of the Amazon Lily arc (ch. 514-524), the old v1 build.

## Recognisable features
- Island of women in the Calm Belt; the Kuja capital in a basin ringed by sheer jungle cliffs, open to a cove.
- Kuja Palace: white walls, purple and gold onion domes, giant coiled snake statues at the gate; Hancock's throne
  hall and bath; the Kuja Battle Arena (amphitheatre) where the snakes were petrified; round huts with conical
  thatch roofs; the Perfume Yuda, the snake-head ship pulled by two Yuda serpents.

## Scale (site 168, v1 112)
Palace 65 x 39 on a quartz plinth: throne hall 25 wide, 22 high, onion dome r 12 on a drum (~y 55); wings 3 floors of
6; corner towers r4 to y 30 with gold onion domes r5. Arena r 19 with 8 rising seat rows. Cliffs to ~40.

## Palette roles
walls: purple terracotta with quartz pillars and smooth quartz bands; domes: purple concrete / gold blocks;
huts: mud bricks/packed mud, striped purple wool + hay thatch; arena: sandstone family; accent: gold, lanterns.

## v2 additions
Furnished wing floors (bsp rooms, stair cores), Hancock's bath on the top floor, colonnade and grand stair, arena
gates and royal box, 14 furnished 1-2 floor huts, stalls on both sides of the market street, longhouse, archery
range, training yard, jungle trees on the cliffs.

## v2.1 fixes (ryan's batch 4 feedback, 2026-10-29)
- Edges: cliff_h() puts the crest at ring_d 0.92 (pulled in on the north side), a steep inner face and a long outer
  slope capped at 2.1 x (distance to the site edge - noisy 3..10 margin), so the ring runs out into rolling ground
  instead of ending in a wall. The cliffs dip smoothly for the cove; sand beach round it; the cove floor shelves up.
- Ship: the Perfume Yuda is now built with the ship kit (mcb/perfume_yuda.py): lofted purple hull with gold wale and
  scale band, white bulwark, stern castle with Hancock's cabin and an onion-dome pavilion, paddle wheels, scarlet
  sails with the Kuja mark, rigging, twin gold serpent figureheads. Two Yuda serpents (yuda()) weave through the cove
  with their necks reared and gold harness collars roped to the bow.
