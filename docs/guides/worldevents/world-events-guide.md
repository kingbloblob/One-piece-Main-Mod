# World events: Buster Calls, Marine fleets, Emperor territories, the Reverie

## Trouble and Buster Calls
Each island you cause trouble on gets a Trouble meter (0-100). Type **/island** to see it.
- Raises it: beating Marines (+4, officers +8, Vice Admirals +15), sinking a Marine ship nearby (+12), hurting villagers/townsfolk (+10), iron golems (+5), beating a boss there (+10, Marine/World Government bosses +25), breaking blocks inside a town or structure (+0.15 each).
- Bigger bounty = more trouble per deed (+15% per threat level). It cools down by 2 a minute.
- **35**: Marine HQ sends a squad. **70**: a Vice Admiral warns you he wants a Buster Call. **100**: a **Buster Call** if you have 50,000,000+ bounty (smaller pirates get a Navy raid instead).

A Buster Call: 60 s warning, then 150 s of bombardment from a fleet of battleships. Shells blow real craters. 40 s in, Vice Admirals and elite Marines land (and an Admiral if your bounty is 1B+).
**Break it**: sink or capture every ship of the fleet before the shelling ends for a big bounty and a headline.
**Rebuilding**: every block the shells destroy is saved, and 10 minutes after the Buster Call the island rebuilds itself block by block. Chests and other blocks with contents are never destroyed. If you placed a block in a crater, yours stays.

## Marine fleets
While you sail, a fleet of 3-5 Marine ships sometimes crosses the sea, with a Vice Admiral's flagship in front. They hold their course and ignore you, unless you fire on them or you are a wanted pirate who comes within 60 blocks. Then the whole fleet attacks. Fleets are bigger further from spawn.

## Emperor territories
Kaido: Wano, Onigashima. Big Mom: Whole Cake, Cacao Island, Fish-Man Island. Blackbeard: Hachinosu. Shanks: Elbaph.
Each Emperor has a standing with you (-100 to 100, shown by /island):
- **Hostile** (-30 or less): war parties and warships hunt you there. At -70 a commander (King or Katakuri) comes for you.
- **Wary**: Big Mom and Blackbeard demand Berries (type **/tribute** within 90 s, or standing drops). Kaido's Headliners challenge you to a duel (win = respect). Shanks's crew just asks you to keep the peace.
- **Friendly** (30+): their crews leave you alone and sometimes share Berries.
- **Conquered** (you beat that Emperor): the crew bows and pays you tribute.
Killing their crew lowers standing. If you hold the Emperor title, the other Emperors treat you as a rival.

## The Reverie
Every 4 in-game days the kings meet at Mary Geoise for 10 minutes (pink bar at the top). Marine fleets sail 3x as often, many escorting a **Royal Galleon** full of treasure (attacking it = big bounty and world news). Trouble counts 50% more. At the end the kings decide something for the next hour: twice the fleets, quicker Buster Calls, or +10% bounty for pirates over 100M (some decisions are just news).

## Operator commands
/worldevent trouble <0-100>, bustercall [stop], restore, fleet [royal], reverie start|stop, standing <emperor> <value>, news
