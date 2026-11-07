"""Adds the hideout's one-line hooks to other packages. Safe to run twice. Usage: python3 -I hooks.py <source dir>"""
import sys

src = sys.argv[1] + "/src"
HOOKS = [
    (src + "/main/java/com/onepiecemod/OnePieceMod.java",
     "\t\tcom.onepiecemod.cuisine.CuisineFeature.initialize();",
     "\t\tcom.onepiecemod.hideout.HideoutFeature.initialize(); // Pirate hideouts: claim an island, your crew lives there, the Navy attacks it.\n"),
    (src + "/client/java/com/onepiecemod/client/OnePieceModClient.java",
     "\t\tcom.onepiecemod.career.client.CareerClient.initialize();",
     "\t\tcom.onepiecemod.hideout.client.HideoutClient.initialize();\n"),
    (src + "/main/java/com/onepiecemod/crew/CrewmateEntity.java",
     "\t\tthis.goalSelector.addGoal(2, new SitWhenOrderedToGoal(this)); // Wait mode.",
     "\t\tthis.goalSelector.addGoal(3, new com.onepiecemod.hideout.HideoutLifeGoal(this)); // At a hideout: campfire at dusk, beds at night.\n"),
]
# Replacements (old text -> new text), skipped when the new text is already there.
SWAPS = [
    # Crash fix: a job that finished on an even tick got one more tick() with no target (goals only re-check
    # canContinueToUse every other tick), so Vec3.atCenterOf(null) crashed the server. Seen in the hideout test.
    (src + "/main/java/com/onepiecemod/crew/job/WorkGoal.java",
     "\tpublic void tick() {\n\t\tticksTrying++;",
     "\tpublic void tick() {\n\t\tif (target == null) {\n\t\t\treturn; // Finished last tick; the goal stops on the next check.\n\t\t}\n\t\tticksTrying++;"),
    (src + "/main/java/com/onepiecemod/crew/CrewmateEntity.java",
     'String doing = isKnockedOut() ? "Knocked out" : switch (getMode()) {',
     'String doing = isKnockedOut() ? "Knocked out" : isSleeping() ? "Asleep" : switch (getMode()) {'),
]
for path, old, new in SWAPS:
    text = open(path).read()
    if new in text:
        print("already there:", path.split("/")[-1])
        continue
    if old not in text:
        raise SystemExit("anchor not found in " + path)
    open(path, "w").write(text.replace(old, new, 1))
    print("swapped:", path.split("/")[-1])

for path, anchor, line in HOOKS:
    text = open(path).read()
    if line.strip() in text:
        print("already there:", path.split("/")[-1])
        continue
    i = text.index(anchor)
    end = text.index("\n", i) + 1
    text = text[:end] + line + text[end:]
    open(path, "w").write(text)
    print("hooked:", path.split("/")[-1])
