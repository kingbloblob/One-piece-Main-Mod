"""Applies the career package's one-line hooks to a source tree. Idempotent. Usage: python3 hooks.py <root with src/>"""
import sys, os
root = sys.argv[1]
J = os.path.join(root, 'src/main/java/com/onepiecemod')
C = os.path.join(root, 'src/client/java/com/onepiecemod')

def patch(path, old, new, marker):
    s = open(path).read()
    if marker in s:
        print('already:', os.path.basename(path), marker[:40]); return
    if s.count(old) != 1:
        raise SystemExit('anchor not found once in %s: %r' % (path, old))
    open(path, 'w').write(s.replace(old, new))
    print('patched:', os.path.basename(path))

patch(os.path.join(J, 'OnePieceMod.java'),
      "\t\tcom.onepiecemod.dialogue.DialogueFeature.initialize(); // Talk screen for friendly characters.\n",
      "\t\tcom.onepiecemod.dialogue.DialogueFeature.initialize(); // Talk screen for friendly characters.\n"
      "\t\tcom.onepiecemod.career.CareerFeature.initialize(); // Play as a Marine or a Revolutionary instead of a pirate.\n",
      'career.CareerFeature')
patch(os.path.join(C, 'client/OnePieceModClient.java'),
      "\t\tcom.onepiecemod.dialogue.client.DialogueClient.initialize();\n",
      "\t\tcom.onepiecemod.dialogue.client.DialogueClient.initialize();\n"
      "\t\tcom.onepiecemod.career.client.CareerClient.initialize();\n",
      'CareerClient')
patch(os.path.join(J, 'bounty/Bounty.java'),
      "\tpublic static void raise(ServerPlayer player, long amount, String reason, boolean newPoster) {\n",
      "\tpublic static void raise(ServerPlayer player, long amount, String reason, boolean newPoster) {\n"
      "\t\tif (com.onepiecemod.career.Careers.interceptBounty(player, amount, reason)) {\n"
      "\t\t\treturn; // Marines never get a bounty (career package).\n"
      "\t\t}\n",
      'interceptBounty')
patch(os.path.join(J, 'bounty/MarineEntity.java'),
      "(target, level) -> isGuard() && target.distanceToSqr(this) < GUARD_RANGE * GUARD_RANGE));",
      "(target, level) -> isGuard() && !com.onepiecemod.career.Careers.isMarine(target) && target.distanceToSqr(this) < GUARD_RANGE * GUARD_RANGE));",
      'Careers.isMarine')
p = os.path.join(J, 'story/StoryGoals.java')
s = open(p).read()
if 'Careers.renown' not in s:
    a = 'case "bounty" -> Bounty.get(player) >= goal.amount;'
    b = 'case "bounty" -> Bounty.format(Math.min(goal.amount, Bounty.get(player))) + " / " + Bounty.format(goal.amount);'
    assert s.count(a) == 1 and s.count(b) == 1, 'StoryGoals anchors'
    s = s.replace(a, 'case "bounty" -> com.onepiecemod.career.Careers.renown(player) >= goal.amount; // Marines count Merit.')
    s = s.replace(b, 'case "bounty" -> Bounty.format(Math.min(goal.amount, com.onepiecemod.career.Careers.renown(player))) + " / " + Bounty.format(goal.amount);')
    open(p, 'w').write(s); print('patched: StoryGoals')
p = os.path.join(J, 'dialogue/Dialogue.java')
patch(p, '\tpublic static final String BYE = "bye";\n',
      '\tpublic static final String BYE = "bye";\n'
      '\tpublic static final String CAREER = "career";\n'
      '\tpublic static final String CAREER_JOIN = "career_join";\n', 'CAREER_JOIN')
patch(p, "\t\t\tcase ADVICE -> advice(player, character, lines, defaults);\n",
      "\t\t\tcase ADVICE -> advice(player, character, lines, defaults);\n"
      "\t\t\tcase CAREER, CAREER_JOIN -> {\n"
      "\t\t\t\t// Joining the Marines or the Revolutionary Army (career package).\n"
      "\t\t\t\tcom.onepiecemod.career.CareerTalk.Answer answer = CAREER.equals(choice)\n"
      "\t\t\t\t\t\t? com.onepiecemod.career.CareerTalk.talk(player, data.id)\n"
      "\t\t\t\t\t\t: com.onepiecemod.career.CareerTalk.join(player, data.id);\n"
      "\t\t\t\tif (answer.offerJoin()) {\n"
      "\t\t\t\t\tsend(player, character, answer.text(), answer.hint(),\n"
      "\t\t\t\t\t\t\tList.of(new Choice(CAREER_JOIN, \"Sign me up!\"), new Choice(DECLINE, \"Let me think about it.\")));\n"
      "\t\t\t\t} else {\n"
      "\t\t\t\t\treply(player, character, answer.text(), answer.hint());\n"
      "\t\t\t\t}\n"
      "\t\t\t}\n", 'CareerTalk.talk')
patch(p, '\t\tchoices.add(new Choice(RECRUIT, "Join my crew!"));\n',
      '\t\tString career = com.onepiecemod.career.CareerTalk.choiceLabel(player, data.id);\n'
      '\t\tif (career != null) {\n'
      '\t\t\tchoices.add(new Choice(CAREER, career));\n'
      '\t\t}\n'
      '\t\tchoices.add(new Choice(RECRUIT, "Join my crew!"));\n', 'CareerTalk.choiceLabel')
p = os.path.join(C, 'hud/client/HudOverlay.java')
patch(p, "\t\t// Bounty.\n\t\tpieces.add(pen -> {\n\t\t\tpen.icon(icon(CharacterFeature.BERRY));\n\t\t\tpen.text(shortBerries(hud.bounty()), 0xFFFFE27A);\n\t\t});\n",
      "\t\t// Bounty, and the career rank for Marines and Revolutionaries (Marines have no bounty).\n"
      "\t\tString careerRank = com.onepiecemod.career.client.CareerClient.hudLabel();\n"
      "\t\tpieces.add(pen -> {\n"
      "\t\t\tif (!com.onepiecemod.career.client.CareerClient.hidesBounty()) {\n"
      "\t\t\t\tpen.icon(icon(CharacterFeature.BERRY));\n"
      "\t\t\t\tpen.text(shortBerries(hud.bounty()), 0xFFFFE27A);\n"
      "\t\t\t}\n"
      "\t\t\tif (careerRank != null) {\n"
      "\t\t\t\tif (!com.onepiecemod.career.client.CareerClient.hidesBounty()) {\n"
      "\t\t\t\t\tpen.space(3);\n"
      "\t\t\t\t}\n"
      "\t\t\t\tpen.text(careerRank, com.onepiecemod.career.client.CareerClient.color());\n"
      "\t\t\t}\n"
      "\t\t});\n", 'CareerClient.hudLabel')
