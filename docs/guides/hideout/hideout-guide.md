# Pirate Hideouts

Claim an island, build it up from a beach camp into a fortress, let your crew live there, and hold it when the Navy comes.

## Claiming land
- Craft a **Hideout Flag**: a Jolly Roger on top, a stick in the middle, cobblestone at the bottom (one column).
- You need a crew (`/crew create <name>`). Marines can't have one; Revolutionaries can.
- Plant it on open land. The claim is a **32 block circle** around the flag.
- One hideout per captain. Hideouts and pirate kingdoms must be **96 blocks** apart, and you can't claim inside a town, base or landmark.
- Break the flag to move. The stash drops, and the land stops being yours. Only your crew (and allies) can break it.

## The hideout screen
Right-click the flag: level, what the next level needs (ticked off live), who lives there, defences, Navy interest and the last daily report.
- **Open stash**: 27 slots. The daily haul goes here, and cannons take their cannonballs from here.
- **Move crew in**: every crewmate of yours inside the claim switches to Work mode where they stand. `/hideout` shows the same in chat.

## Levels
Each level needs everything from the ones before it. "Living here" = crewmates set to **Work** inside the claim.

| Level | Needs | What it gives |
|---|---|---|
| 1 Pirate Camp | 1 bed, a campfire | Crew sleep here, small daily haul. The Navy now notices it. |
| 2 Hideout | 3 beds, 2 chests or barrels, crafting table, furnace/smoker/stove, 3 crew living here | Hauls x1.25. Resting in the claim heals you. |
| 3 Pirate Fort | 5 beds, 2 cannons, a finished Marine Watchtower, 5 crew | Cannons fire at attackers. Cook adds a proper dish. |
| 4 Stronghold | 7 beds, 4 cannons, 2 more finished buildings (Dojo, Shipyard, Feast Table, Vault, Relay), 7 crew | Hauls x1.75, crewmates heal faster, one extra attack wave. |
| 5 Pirate Fortress | 9 beds, 8 cannons, 4 more buildings with a Treasure Vault among them, all 9 crew | Hauls x2. |

## Crew life
- Crew living there gather round a **campfire at dusk** and **sleep in the beds at night** (one each), then go back to their jobs in the morning.
- **Daily haul** (once a Minecraft day, up to 3 days piles up while you're away), into the stash:
  - Cook: grilled fish (+ a dish from Pirate Fort)
  - Navigator: paper, sometimes a Treasure Map (from level 2)
  - Sniper: arrows, gunpowder
  - Swordsman: bones, string, iron
  - Doctor: Potion of Healing, golden carrots
  - Shipwright: **cannonballs** and planks (keeps your cannons fed)
  - Archaeologist: gold nuggets, sometimes an emerald
  - Helmsman: cod, salmon, sometimes a Wreck Chart
  - Musician: no items, everyone else +20%
  - Plus a few Berries of crew dues per level.
- Higher hideout levels and higher crewmate levels bring in more.

## Navy attacks
- Need a bounty and a level 1+ hideout. At least 2 Minecraft days apart (3 while you're away). The Navy raid rate setting scales how often.
- **While you're within 160 blocks**: a Den Den Mushi warning, then **60 seconds** later waves of Marines land just outside the claim (2 to 5 waves by bounty). From a 50M bounty a warship anchors offshore and shells the hideout; from 100M the last wave has a famous officer (Tashigi, Smoker, Lucci).
- Marines fight your crew, then march on the flag. If Marines stand at the flag for **30 seconds** with nobody of yours beside it, the hideout **falls**: they carry off a third of the stash and the crew spends the next day patching up (no haul).
- **Cannons** in the claim fire by themselves at the nearest Marine in front of them (about 70 degrees each side of the barrel), every 4 seconds, one cannonball from the stash per shot. Cannon shells only hurt the Navy. With no Marines in reach they shoot at the warship.
- Win: a captured Navy supply crate (Marine loot + cannonballs) and Berries in the stash, and a bounty raise (crew who helped get half).
- Leave for a minute during an attack and the rest is settled by numbers.
- **While you're away**: the attack is settled by the **defence rating** (level, cannons with ammo, crew living there, fighters count double, Watchtower) against the Navy's strength. You hear about it on the Den Den Mushi.

## Commands
- `/hideout`: where it is, its level and what's next.
- Cheats (operator): `/hideout attack` (attack now), `/hideout attack stop`, `/hideout away` (an away attack now), `/hideout haul [days]` (haul now).

## Difference from a pirate kingdom
Kingdoms (Kingdom Flag) are for Emperors: taxes and hired guards over a 48 block circle. A hideout is any crew's home base, defended by your own crewmates and cannons.
