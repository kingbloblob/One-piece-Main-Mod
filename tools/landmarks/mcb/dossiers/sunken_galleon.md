# Sunken Treasure Galleon
Refs: Jaya salvage dive (ep 145-146, the Flying Pirates' wreck), generic treasure wrecks. Three-master broken apart on the sea floor.
Silhouette: hull broken in two at the mainmast; stern half heeled hard over with its 2-tier castle; bow half apart, turned, sunk nose-down with the gold figurehead; snapped masts on the sand, one mast with rags.
v2: 120x84 seafloor. mcb/hulls.py galleon() + transfer(lean/yaw/decay/drop_above) + tatter(); treasure spill (gold, barrels, cannons, pots), sea-lantern ring, coral on timber tops, kelp, Fish-Man guards on the first free cells above the sand.
Gotchas: air->water only up to y 12 (air_to_water(top=12)) so a tall wreck in a shallow sea never lifts water into open air; check every sea pickle/coral has a solid block under it.
