# Seasons, the Great Cyclone and rare world events

This pack adds three things: seasons that change how crops grow, a new giant storm at sea, and rare big events
that News Coo tells the whole world about.

## Seasons

The world turns through **spring, summer, autumn and winter**, one season every **5 in-game days** (a year is 20
days). Sleeping skips days, so it skips season time too. When the season changes, everyone gets a chat message.

Type **/season** to see:
- the world's season and how many days are left,
- the season where you're standing (it can be different, see below),
- how fast crops grow right here, and which island crops are "in season".

The island title you see when you arrive on an island also shows its season now.

### Every island has its own season

Like in the show, the Grand Line's islands keep their own seasons:
- **Winter Islands** (Drum, the frozen half of Punk Hazard...) are always in winter.
- **Summer Islands** (Alabasta, Jaya...) are always in summer.
- **Sky islands and the islands under the sea** (Skypiea, Fishman Island) and Totto Land are always in spring.
- **Snowy lands** (vanilla snowy biomes) stay frozen all year.
- **Every other Grand Line island** is a fixed number of seasons ahead of the world. So when it's autumn in the
  East Blue, the next island along may be in spring. The same island is always in step with itself.
- The **East Blue** and plain land follow the world's season. The Nether, the End and the mod's other
  dimensions have no seasons.

### What seasons do to crops

| Season | Crops outdoors grow at |
|---|---|
| Spring | 125% |
| Summer | 100% |
| Autumn | 90%, but harvests are bigger |
| Winter | 30% |

- This works for vanilla crops (wheat, carrots, potatoes, beetroot) and the 14 island crops.
- **Greenhouses beat winter.** A crop with a roof over it, or lit by a lantern or torch (block light 12 or more,
  so a lantern right next to it), grows at 90% even in winter. Glass roofs still count as open sky, so add lights.
- **Autumn harvests:** breaking a fully grown crop in autumn has a 35% chance to drop one extra piece of produce.
- **Each island crop loves one season** and grows 50% faster then (even more in spring). The seed's tooltip says which.

| Loves spring | Loves summer | Loves autumn | Loves winter |
|---|---|---|---|
| East Blue Cabbage, Cloud Wheat, Sea Grapes, Mink Tea | Sand Melon, Snake Pepper, Dressrosa Tomato, Jungle Yam | Wano Rice, Kibi Millet, Elbaph Barley, Ghost Pumpkin, Totland Cacao | Frost Turnip |

This stacks with the farming rules you already know: an island crop is still fastest on its home island, and
Sprinklers, the Watering Can and bone meal all still help.

### What seasons do to the sea

- **Autumn is storm season:** sea events happen 40% more often, storms are more common, and the **Great Cyclone** can appear.
- **Winter:** more blizzards and hailstorms.
- **Summer:** more heat waves and waterspouts.
- **Spring:** calmer seas (20% fewer events).

The season that counts is the one where you are, so a Winter Island's waters always have winter weather.

## The Great Cyclone

A giant **tornado** that crosses the sea for 5 minutes. A black funnel twists down from a huge spinning cloud
ceiling (about 80 blocks up and 240 across) to the sea, with a churning skirt of spray and wreckage (planks,
kelp, seawater) whirling around its foot. You can see it coming from far away. A Navigator in your crew warns you a
full minute ahead (30 seconds without one).

- **Anywhere under the cloud (120 blocks from the funnel):** dark sky and heavy rain, winds that swirl your ship
  around the funnel, huge waves that strain the hull, and lightning about every second and a half, sometimes right
  on your mast. A Clima-Tact still pulls lightning away from you. Like all weather, it never drops your hull below
  25% and never knocks blocks off.
- **Near the funnel (within ~27 blocks):** it sucks you in and spins you faster and faster.
- **In the funnel itself (9 blocks):** it lifts and whirls anyone not on a ship, makes the crew dizzy, strains
  the hull, then flings you back out. The reward for daring it: treasure sucked up off the sea bed rains down around you.
- **When it's over,** everyone still in its path finds wreckage and treasure floating around them.
- **Where:** out at sea, aboard a ship. Mostly in autumn (more often in the New World), or as a rare world event.

New advancements: **Into the Black Wall** (be caught in one), **Into the Funnel** (sail into the funnel), **Rode It Out**
(still be there when it blows over). Operators: `/seaevent start cyclone`.

## Rare world events

About once every three or four in-game days, something big happens near one of the players, and News Coo tells
everyone. Never in a world's first two days, and at least two days apart.

| Event | Where | What happens |
|---|---|---|
| **Surprise Buster Call** | On an island, with a bounty of 30,000,000 or more | The Five Elders decide to make an example of you. A full Buster Call on the island you're on, even if you didn't make trouble there. Break it by sinking the fleet, as usual. Craters rebuild after 10 minutes. |
| **Meteor shower** | Under open sky | Admiral Fujitora "prays" at the sky. 15 seconds of red glow, then 6 burning meteors over half a minute, 15 to 55 blocks around you. Each one burns and hurts anything close and blows a crater (rebuilt 10 minutes later). Dig through the wreck for meteorite ore: raw iron, gold, Kokuto ore, amethyst, sometimes a diamond or netherite scrap. Advancement **Falling Stars**. |
| **Treasure convoy** | Aboard a ship at sea | A World Government fleet escorts a Royal Galleon full of tribute past you. Attack it for loot, if you can take the bounty. |
| **Pirate armada** | Aboard a ship on the Grand Line | A big pirate fleet comes for you. Sink or board every ship to win the battle bonus. |
| **Great Cyclone** | Aboard a ship at sea | A Great Cyclone crosses your course (three times as likely in autumn). |

Operators: `/worldevent rare` (a random one that fits where you are), `/worldevent rare <id>` (buster_call,
meteor_shower, treasure_convoy, pirate_armada, great_cyclone), `/worldevent rare status`.

## Commands

| Command | Who | What |
|---|---|---|
| `/season` | Everyone | Season here and in the world, crop speed, crops in season |
| `/season set <season>` | Operators | Move the calendar to the start of that season |
| `/season next` | Operators | Skip to the next season |
| `/seaevent start cyclone` | Operators | Start a Great Cyclone next to you |
| `/worldevent rare [id]` | Operators | Start a rare world event |

## Tuning

The numbers are at the top of each file: `season/Seasons.java` (days per season, growth speeds, greenhouse
light, autumn bonus), `weather/SeaEventType.java` (cyclone size, length, wind, drift speed),
`worldevent/RareEvents.java` (daily chance, days between events, Buster Call bounty).
