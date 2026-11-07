# Grand Line weather and sea events

The Grand Line is famous for weather that changes without warning. Now it does in the mod too.
About every 15 minutes at sea, something happens near you. After each event you get about
8 calm minutes before the next one can start.

## The events

| Event | Where | What happens | How to survive it | Reward |
|---|---|---|---|---|
| **Grand Line Storm** | Grand Line (rarely the Blue seas) | Sky goes dark, lightning every few seconds, wind shoves ships and swimmers sideways in gusts. Lightning likes ships. | Sails fill extra in a storm, so sail out fast. Holding a **Clima-Tact** pulls lightning away from you. | Speed, if you ride the wind |
| **Whirlpool** | Grand Line, deep water | A spinning whirlpool opens 25 to 40 blocks ahead. It drags in ships, swimmers, mobs and items. The eye pulls swimmers under and makes the crew dizzy. | Hold W with lots of sails to break free. Small boats with few sails may get stuck until it ends. | When it closes it spits out treasure (gold, iron, sea pearls, sometimes diamonds or a Heart of the Sea) |
| **Aqua Laguna** | On a Grand Line beach | A 45 second countdown, then a giant wave rolls in from the sea and slams everything low down: 2.5 hearts of damage and a big shove. | Climb 9+ blocks above the sea, or get under a roof. | Treasure washes up on the beach afterwards |
| **Sea King Ambush** | Calm Belt, while sailing or swimming | Dead calm, then 2 or 3 Sea Kings burst out of the water around you. The ship lurches. | Fight or flee. No wind here, so you can't outrun them with sails. | Sea King loot |
| **Sudden Blizzard** | Grand Line | Snow everywhere. You start freezing and then take freeze damage. | Wear any leather armor piece, or stand within 4 blocks of a fire, campfire, lava or magma. Mera, Magu and Hie fruit users don't freeze. | None, just survive |
| **Scorching Heat Wave** | Grand Line | The wind dies (ships slow down) and you get hungry fast in the sun. | Stand in shade or water, bring food. Fire fruit users are fine; Hie users get hungry twice as fast. | None |
| **Florian Triangle Mist** | Grand Line, at night | Thick mist, spooky whispers, a violin far away... and "Lost Souls" (drowned) rising from the water. | Fight them off. The mist and any Lost Souls vanish when it ends. | Lost Souls drop gold |

**Navigator tip:** if you have a crewmate with the Navigator job within 48 blocks, they warn you
30 seconds early (instead of 8) and tell you what's coming, like Nami does.

## Testing it quickly (needs cheats on)

1. Go out to sea in the Overworld (best: on a ship).
2. Type `/seaevent start storm` (or `whirlpool`, `aqua_laguna`, `calm_belt_ambush`, `blizzard`, `heat_wave`, `florian_mist`).
3. `/seaevent list` shows what's running. `/seaevent stop` ends everything.

Aqua Laguna needs you standing on land near the ocean. A whirlpool needs deep open water nearby.

## Good to know

- The seas are rings around spawn: the East Blue out to 1400 blocks, the Calm Belt from 1400 to 1650, the Grand Line (Paradise) to 3500, then the New World. Events are a bit more common in the New World.
- The moment you sail out of the Calm Belt into the Grand Line, the sky can flip to a storm, blizzard or heat wave (always the first time each session). Same when you reach the New World.
- A storm's rain and dark sky only show near the storm (they fade in about 40 blocks past its edge). The rest of the world keeps its own weather, so friends on a server far away aren't caught in it.
- Events are forgotten if you quit the world. Nothing breaks blocks.
- The Knock Up Stream is still the story event at Montblanc Cricket's house; it isn't a random event.

## Islands

Every named island now feels like its own place.

- **Arrival title:** stay on an island for 2 seconds and its name appears on screen, like "Drum Island / A Winter Island". It won't repeat if you come back within 5 minutes.
- **Winter Islands** (Drum Island, Punk Hazard's frozen half, Elbaph, Impel Down Level 5): out in the open you slowly freeze, then take damage. Any leather armor piece or a fire within 4 blocks keeps you warm. Hie, Yuki, Mera and Magu users don't feel it.
- **Summer Islands** (Alabasta, Jaya, Kuri, Punk Hazard's burning half, Hachinosu, Impel Down Level 4): in the sun by day you get hungry faster. Each piece of iron, gold, chainmail, diamond or netherite armor makes it worse. Shade or water stops it. Fire users are fine; ice users melt twice as fast.
- **Look and sound:** each island has its own fog colour, haze and drifting particles (snow on Drum, cherry petals in Wano, sand on Alabasta) and its own music (winter, desert, Wano, sky, spooky, Marine and tropical themes).
- The island list is in `src/main/resources/onepiece/islands.json`; the fog, particles and music are set by `tools/islands/island_look.py`.
