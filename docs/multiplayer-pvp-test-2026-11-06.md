# Multiplayer crews and PvP test (2026-11-06)

Tested on a real dedicated server with three real clients at once: **Luffy** and **Zoro** (Straw Hats) and **Usopp** (Usopp Pirates).
Every exploit below was first reproduced on the old build, then re-tested on the fixed build.

## What was broken, and what changed

| # | Problem | Seen in game? | Fix |
|---|---|---|---|
| 1 | **Bounty farm:** a friend challenges you, you accept and instantly `/crew surrender`. The winners got +5M bounty every time (Usopp went 0 to 10M in two seconds). | Yes | A battle shorter than 2 minutes, or a rematch between the same two crews within 30 minutes, still pays the wagers but adds **no bounty**. The winners are told why. |
| 2 | **Free Berries in creative:** a creative-mode officer didn't pay their wager but still won the whole pot (Luffy got 200 Berries for nothing). | Yes | Wagers need both officers in survival. Battles without a wager work in any mode. |
| 3 | **Peace mid-war:** two crews at war could ally. Allies can't hurt each other, so the battle could never end except by the 20-minute timer. | Yes | `/crew ally` refuses while the two crews are in a sea battle. |
| 4 | **Crew breaks up mid-battle:** after `/crew disband` the battle carried on against a crew that no longer existed ("Luffy's crew"). | Yes | Disbanding now ends the battle: the other crew wins. |
| 5 | **Switching sides:** a player could `/crew join` a crew in the middle of its sea battle (as a turncoat or as reinforcements). | Fix confirmed in game | `/crew join` waits until that crew's battle is over. |
| 6 | **Allies looting your ship:** an allied player *walking on your deck* could open your ship's chests and stations while your crew was at the helm. The check only looked at players sitting in a seat. | Code path traced; fix confirmed in game ("Only the Straw Hats can use their ship's storage and helm.") | Uses `ShipEntity.aboard()` (seat or deck), like the rest of the mod. |
| 7 | **Free Haki XP from crewmates:** a crewmate's punch was blocked by the friendly-fire rule only *after* Observation Haki had already dodged it (and given XP), Future Sight had struck back, a Logia had dodged, Kami-e had triggered or a Reject Dial had stored it. Two crewmates could punch each other to train Haki. | Code (event order) | The friendly-fire check now runs in its own phase, before every other damage listener. Hired crewmates' "same crew" check moved there too. |
| 8 | **Boarding Hook in a sea battle:** it always said "That ship belongs to another crew", even during a battle with that crew. | Code | In a battle the hook works like boarding by hand (below half hull), from the hook's 24-block range. |
| 9 | `/crew unally Straw Hats` failed: the argument took one word, so crew names with spaces couldn't be typed. | Yes | The name takes the rest of the line; tab completion offers captain and crew names. |
| 10 | Text: "The Luffy's crew won", "The Usopp Pirates's ship was taken". | Yes | Unnamed crews read "Luffy Pirates"; possessives read "Usopp Pirates' ship". |

## What worked fine (no change needed)

- Crew create / invite / join / members, `[Straw Hats]` name tags over heads and in the Tab list on the other clients.
- Friendly fire between crewmates is blocked (`/damage ... by Luffy` on Zoro: "invulnerable").
- PvP kill bounty: Usopp killed Zoro (5.75M) and got 10% of it, once; the 30-minute cooldown held.
- Sea battle hull bars (blue/red) show on both crews' screens and update.
- Boarding capture: hull below half, Usopp's crew off the deck, Zoro aboard for 20 s: "The Usopp Pirates' ship was taken by boarders! The Straw Hats won".
- No crashes or exceptions on the server or the three clients in about 30 minutes of play.

## Known, not changed

- An allied player standing on your deck still sees the "1 cannon ready" hint. The server refuses to let them fire ("Only the ship's own crew can fire her cannons"); the hint is only on their screen because the client doesn't know who owns the ship.
- Kill-bounty and battle-reward cooldowns are kept in memory, so a server restart resets them.
- A captured ship stays with its crew after the battle (taking someone's home ship for good felt too harsh). Easy to change if wanted.
- Not covered this time: Devil Fruit moves as seen by the other player, trading between players.
