"""Side quests 2026-11-02 (thread "Add side quests, pets and furniture variety").
Gives the nine traders (Nami, Usopp, Sanji, Chopper, Franky, Brook, Sengoku, Tashigi, Vegapunk) their own
short quest lines, so every friendly character has work for you. Traders keep their shops.
Safe to run again: it only sets a character's quests if they have none yet.

    python3 add_side_quests.py [source dir, default: the shared source]
"""
import json, os, sys

root = sys.argv[1] if len(sys.argv) > 1 else "/mnt/project-files/one-piece-mod/source"
path = os.path.join(root, "src/main/resources/onepiece/characters.json")


def fetch(item, count, berries, start, done, reward=None, rc=1):
    q = {"type": "fetch", "berries": berries, "start": start, "done": done, "item": item, "count": count}
    return with_reward(q, reward, rc)


def talk(target, berries, start, done, reward=None, rc=1):
    return with_reward({"type": "talk", "berries": berries, "start": start, "done": done, "target": target}, reward, rc)


def defeat(target, berries, start, done, reward=None, rc=1):
    return with_reward({"type": "defeat", "berries": berries, "start": start, "done": done, "target": target}, reward, rc)


def explore(target, berries, start, done, reward=None, rc=1):
    return with_reward({"type": "explore", "berries": berries, "start": start, "done": done, "target": target}, reward, rc)


def deliver(target, item, count, berries, start, done, reward=None, rc=1):
    q = {"type": "deliver", "berries": berries, "start": start, "done": done, "item": item, "count": count, "target": target}
    return with_reward(q, reward, rc)


def with_reward(q, reward, rc):
    if reward:
        q["rewardItem"] = reward
        q["rewardCount"] = rc
    return q


SIDE = {
    "nami": ([
        fetch("minecraft:paper", 24, 20, "I'm going to draw a map of the whole world. Bring me 24 sheets of paper!",
              "Perfect! The first page of my world map starts today."),
        explore("weatheria", 60, "Up in the sky there's a little island where old men study the weather. Weatheria! Go and find it for me.",
                "It's real? I'm going there to learn everything about the weather!", "minecraft:compass", 1),
        defeat("enel", 120, "That so-called god Enel kidnapped me on his golden ark. Here's his poster. Ground him!",
               "Ha! Not so godly now. Here, take this. ...You can pay me back later.", "minecraft:gold_ingot", 6),
    ], "Got any treasure for me? I'll take care of it. Just a small fee."),
    "usopp": ([
        fetch("minecraft:egg", 16, 15, "I'm brave, I'm just... preparing! Bring me 16 eggs for my Rotten Egg Star ammo.",
              "Hissatsu! Rotten Egg Star! ...After they go rotten, anyway."),
        explore("going_merry_farewell", 50, "I never said a proper goodbye to the Going Merry. Go see the place where she rests, please.",
                "She's still there? ...Thank you. She was the best ship in the world."),
        talk("shanks", 60, "My dad Yasopp sails with Red-Haired Shanks. Tell him his son is a brave warrior of the sea!",
             "Dad said he's proud of me? I-I'm not crying, there's sand in my eye!", "minecraft:arrow", 32),
    ], "I once fought a goldfish so big its poop was an island. True story!"),
    "sanji": ([
        fetch("onepiece:blue_sea_bream", 8, 25, "A cook is only as good as his fish. Catch me 8 Blue Sea Bream.",
              "Beautiful fish. Now watch a master at work."),
        deliver("nami", "onepiece:sea_bream_sashimi", 4, 30, "Take this sashimi to my beautiful Nami-swan. Careful! Don't you dare eat any.",
                "She smiled?! Mellorine~! You've done a great service."),
        fetch("onepiece:all_blue_kingfish", 1, 150, "Somewhere out there is the All Blue, where every fish in the world swims. Bring me proof: an All Blue Kingfish.",
              "It's real... The All Blue is real! I'll cook you the best meal of your life.", "minecraft:golden_carrot", 16),
    ], "Hungry? Never be shy in my kitchen."),
    "chopper": ([
        fetch("onepiece:winter_rose", 8, 15, "I'm making a new medicine. Bring me 8 Winter Roses from the snowy islands, please.",
              "Thank you! This will help a lot of people. ...D-don't thank me, jerk!"),
        talk("law", 25, "Torao is an amazing surgeon. Could you ask him if he'd teach me a little?",
             "He said yes?! I'm going to be a doctor who can cure any disease!"),
        explore("drum_castle", 40, "Doctor Hiriluk's flag flies over Drum Castle. Go and see that it's still there, for me.",
                "It's still flying... Doctor, your dream lives on.", "minecraft:golden_apple", 2),
    ], "If you get hurt, come see me! I'm a doctor!"),
    "franky": ([
        fetch("onepiece:cola", 8, 20, "I run on cola, bro! Bring me 8 bottles and I'm SUUUPER!",
              "SUUUPER! My tank's full again!"),
        fetch("onepiece:adam_log", 16, 60, "Real ships need real wood. Bring me 16 Adam logs from the Treasure Tree Adam.",
              "That's the stuff! A ship of Adam wood can sail anywhere.", "onepiece:adam_planks", 16),
        defeat("lucci", 150, "CP9 tore up Iceburg and took Tom's blueprints. Lucci's their top dog. Here's his poster!",
               "The pigeon guy's down? That's what I call SUPER!", "minecraft:iron_block", 4),
    ], "Need a ship fixed? Franky House does it all!"),
    "brook": ([
        fetch("minecraft:milk_bucket", 3, 20, "Milk is good for your bones! Could you bring me 3 buckets? Yohohoho!",
              "Ahh, my bones feel stronger already! Not that I have muscles. Yohohoho!"),
        explore("twin_capes_lighthouse", 50, "I promised a little whale, Laboon, that I would come back to the Twin Capes. Please go and see if he still waits.",
                "He's still waiting... After fifty years. My eyes are full of tears! Though I have no eyes. Yohoho...", "minecraft:jukebox", 1),
        defeat("moria", 120, "Gecko Moria stole my shadow and left me in the dark. Here is his poster. Help me get it back!",
               "I can walk in the sun again! Thank you! Yohohoho!", "minecraft:golden_apple", 3),
    ], "Shall I play you a song? Binks' Sake, perhaps?"),
    "sengoku": ([
        fetch("minecraft:wheat", 16, 20, "My goat is hungry and the Marine kitchen is out of hay. Bring me 16 wheat.",
              "She thanks you. So do I."),
        talk("garp", 20, "Garp ate my rice crackers again. Go tell that fool to stay out of my office!",
             "He laughed and ate another one? ...Typical."),
        defeat("blackbeard", 300, "Blackbeard stole Whitebeard's power at Marineford. I'm retired, but you aren't. Here's his poster.",
               "The man who started this era of chaos, beaten. Well done.", "minecraft:diamond", 4),
    ], "Have a rice cracker. Don't tell Garp."),
    "tashigi": ([
        fetch("onepiece:tamahagane_katana", 1, 40, "Famous swords shouldn't be in the hands of pirates. Forge or find me a Tamahagane Katana.",
              "A fine blade. I'll keep it safe from pirates."),
        talk("koby", 20, "Tell Captain Koby that G-5 is ready if he needs us.", "Good. G-5 is rough, but they're loyal."),
        defeat("crocodile", 80, "Crocodile nearly took over Alabasta and a pirate had to stop him. Not this time. Here's his poster.",
               "Justice was served by... you. I suppose I should thank you.", "minecraft:iron_sword", 1),
    ], "Have you seen my glasses? ...Oh, they're on my head."),
    "vegapunk": ([
        fetch("onepiece:wapometal_ingot", 8, 40, "Science needs materials! Bring me 8 Wapometal ingots for my next invention.",
              "Excellent! The lab will put these to good use."),
        explore("void_century_ruins", 100, "The Void Century hides the truth of this world. Go to its ruins and tell me what you see.",
                "So the ruins remain... The world deserves to know what happened.", "minecraft:book", 8),
        defeat("kizaru", 250, "Kizaru was sent to Egghead to silence me. He's not a bad man, but he follows orders. Stop him.",
               "You stopped a light-speed Admiral? My data never predicted that!", "minecraft:netherite_scrap", 2),
    ], "Knowledge belongs to everyone. Stop by any time."),
}

with open(path, encoding="utf-8") as f:
    chars = json.load(f)
added = 0
for c in chars:
    if c["id"] in SIDE and not c.get("quests"):
        c["quests"], c["thanks"] = SIDE[c["id"]]
        added += len(c["quests"])
with open(path, "w", encoding="utf-8") as f:
    f.write(json.dumps(chars, indent=2, ensure_ascii=False) + "\n")
print("added", added, "quest steps")
