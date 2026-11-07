package com.onepiecemod.arena;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.BossEvent;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.crew.Crew;
import com.onepiecemod.crew.CrewAttachments;
import com.onepiecemod.crew.CrewEntities;
import com.onepiecemod.crew.CrewHiring;
import com.onepiecemod.crew.CrewLevels;
import com.onepiecemod.crew.CrewPayloads;
import com.onepiecemod.crew.CrewPersonality;
import com.onepiecemod.crew.CrewRole;
import com.onepiecemod.crew.CrewRoster;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.npc.HumanNpc;

/**
 * A Davy Back Fight, the pirate game from Long Ring Long Land: three games between two crews.
 * Whoever wins a game takes one crewmate from the losing crew, who changes sides on the spot.
 *  1. Donut Race: reach the four buoys and come back before the rival crew's racers do (any boat, ship or your own legs).
 *  2. Groggy Ring: your crew against their Groggy Monsters. Knock out the Ball Man to win; fall and you lose.
 *  3. Combat: you against their captain, alone, inside the ring.
 * Win and you choose one of their members (a free role in your crew) or Berries. Lose and they take your best crewmate,
 * who then waits in a rival crew until you win them back in a later fight.
 */
public class DavyBackFight extends ArenaMatch {
	private enum Phase { INTRO, COUNTDOWN, RACE, GROGGY, COMBAT, PICK, DONE }

	private static final String[] GAMES = {"Donut Race", "Groggy Ring", "Combat"};
	private static final int RACE_RADIUS = 28;
	private static final double GROGGY_RING = 20;
	private static final double COMBAT_RING = 14;
	private static final int PICK_TICKS = 600;

	private final RivalCrew rival;
	private final Map<RivalCrew.Member, HumanNpc> lineup = new LinkedHashMap<>();
	private HumanNpc captain;
	private Phase phase = Phase.INTRO;
	private int timer = 160;
	private int game = 0;
	private int wins = 0;
	private int losses = 0;

	// Donut Race
	private final List<BlockPos> buoys = new ArrayList<>();
	private int nextBuoy = 0;
	private int raceTicks = 0;
	private int rivalTime = 0;
	private boolean beamUsed = false;

	// Groggy Ring
	private final List<Mob> groggy = new ArrayList<>();
	private Mob ballMan;

	// Combat
	private int beamCooldown = 160;

	// Picking a crewmate
	private final List<RivalCrew.Member> options = new ArrayList<>();
	private int pickCode = 0;
	private boolean lastWon = false;

	public DavyBackFight(ServerPlayer player, BlockPos center, RivalCrew rival) {
		super(player, center, "Davy Back Fight vs the " + rival.crewName, BossEvent.BossBarColor.PINK);
		this.rival = rival;
		spawnLineup();
		say(player, "Itomimizu", "Davy Back Fight! The " + rival.crewName + " against the "
				+ crewName(player) + "! Three games, and the winner of each game takes one crewmate from the loser!");
		player.sendSystemMessage(Component.literal("Games: Donut Race, Groggy Ring and Combat. Your crewmates may help in the Groggy Ring only.")
				.withStyle(ChatFormatting.GRAY));
		bar.setName(Component.literal("Davy Back Fight vs the " + rival.crewName + ": the crews line up"));
	}

	private static String crewName(ServerPlayer player) {
		Crew crew = player.getAttached(CrewAttachments.CREW);
		return crew != null ? crew.name() : player.getName().getString() + "'s crew";
	}

	@Override
	protected int leashRadius() {
		return phase == Phase.RACE ? RACE_RADIUS + 40 : 48;
	}

	@Override
	protected boolean crewMayFight(net.minecraft.world.entity.Entity fighter) {
		return phase == Phase.GROGGY && groggy.contains(fighter);
	}

	// ---------- Line-up ----------

	private void spawnLineup() {
		BlockPos front = spot(180, 7);
		captain = fighter("pirate_captain", front, rival.captainName + " (" + rival.crewName + ")",
				120 * rival.strength(), 9 * (1 + 0.25 * rival.tier));
		if (captain != null) {
			setBase(captain, Attributes.ARMOR, 4 + 2 * rival.tier);
			setBase(captain, Attributes.KNOCKBACK_RESISTANCE, 0.4);
			wait(captain);
		}
		for (RivalCrew.Member member : rival.members) {
			addToLineup(member);
		}
	}

	private void addToLineup(RivalCrew.Member member) {
		int index = lineup.size();
		BlockPos pos = spot(150 + (index % 2 == 0 ? -1 : 1) * (10 + 9 * (index / 2 + 1)), 9);
		HumanNpc npc = fighter(member.taken != null ? "rookie_pirate" : "pirate", pos,
				member.fullName() + " (Lv " + member.level + ")", 30, 4);
		if (npc != null) {
			wait(npc);
			lineup.put(member, npc);
		}
	}

	/** Line-up members stand still, can't be hurt and don't fight until their game. */
	private static void wait(HumanNpc npc) {
		npc.setNoAi(true);
		npc.setPermanentlyInvulnerable(true);
	}

	private static void wake(Mob mob) {
		mob.setNoAi(false);
		mob.setPermanentlyInvulnerable(false);
	}

	// ---------- Ticking ----------

	@Override
	protected boolean tick(ServerPlayer player) {
		switch (phase) {
			case INTRO, COUNTDOWN -> {
				if (--timer <= 0) {
					startGame(player);
				} else if (timer % 20 == 0 && timer <= 60) {
					player.sendSystemMessage(Component.literal(String.valueOf(timer / 20)).withStyle(ChatFormatting.GOLD), true);
					sound(SoundEvents.NOTE_BLOCK_BELL.value(), 1.0f, 1.2f);
				}
			}
			case RACE -> tickRace(player);
			case GROGGY -> tickGroggy(player);
			case COMBAT -> tickCombat(player);
			case PICK -> {
				if (--timer <= 0) {
					pick(player, -1);
				}
			}
			case DONE -> {
				return false;
			}
		}
		return phase != Phase.DONE;
	}

	private void startGame(ServerPlayer player) {
		title(player, GAMES[game], "Game " + (game + 1) + " of 3");
		sound(SoundEvents.RAID_HORN.value(), 1.5f, 1.3f);
		switch (game) {
			case 0 -> startRace(player);
			case 1 -> startGroggy(player);
			default -> startCombat(player);
		}
	}

	private void updateBar(String detail, float progress) {
		bar.setName(Component.literal("Davy Back Fight (" + wins + "-" + losses + ") " + GAMES[game] + ": " + detail));
		bar.setProgress(Math.max(0, Math.min(1, progress)));
	}

	// ---------- 1. Donut Race ----------

	private void startRace(ServerPlayer player) {
		phase = Phase.RACE;
		buoys.clear();
		for (int i = 0; i < 4; i++) {
			double angle = Math.toRadians(90 * i);
			buoys.add(surface(center.getX() + (int) Math.round(Math.sin(angle) * RACE_RADIUS),
					center.getZ() + (int) Math.round(Math.cos(angle) * RACE_RADIUS)));
		}
		buoys.add(center);
		nextBuoy = 0;
		raceTicks = 0;
		rivalTime = (75 - 6 * rival.tier) * 20;
		beamUsed = false;
		say(player, "Itomimizu", "The Donut Race! Touch all four buoys (follow the light) and come back here before their racers!");
	}

	private void tickRace(ServerPlayer player) {
		raceTicks++;
		BlockPos target = buoys.get(nextBuoy);
		if (ticks % 4 == 0) {
			for (int y = 0; y < 24; y += 2) {
				level.sendParticles(ParticleTypes.END_ROD, true, true, target.getX() + 0.5, target.getY() + y, target.getZ() + 0.5,
						1, 0.1, 0.4, 0.1, 0.0);
			}
		}
		if (ticks % 20 == 0) {
			for (int i = nextBuoy + 1; i < buoys.size(); i++) {
				BlockPos later = buoys.get(i);
				level.sendParticles(ParticleTypes.HAPPY_VILLAGER, true, true, later.getX() + 0.5, later.getY() + 2, later.getZ() + 0.5,
						6, 0.3, 1.5, 0.3, 0.0);
			}
		}
		Vec3 at = player.position();
		double dx = at.x - (target.getX() + 0.5);
		double dz = at.z - (target.getZ() + 0.5);
		if (dx * dx + dz * dz < 16 && Math.abs(at.y - target.getY()) < 8) {
			nextBuoy++;
			sound(SoundEvents.EXPERIENCE_ORB_PICKUP, 1.0f, 1.0f + nextBuoy * 0.1f);
			if (nextBuoy >= buoys.size()) {
				gameOver(player, true, "You crossed the finish line first!");
				return;
			}
			player.sendSystemMessage(Component.literal(nextBuoy < 4 ? "Buoy " + nextBuoy + " of 4! Next one: follow the light."
					: "All four buoys! Back to the start!").withStyle(ChatFormatting.AQUA), true);
		}

		int rivalBuoys = Math.min(buoys.size(), raceTicks * buoys.size() / rivalTime);
		updateBar("you " + nextBuoy + "/5, their racers " + rivalBuoys + "/5", 1 - raceTicks / (float) rivalTime);

		// Foxy cheats, just like in the show.
		if (rival.foxy && !beamUsed && raceTicks > rivalTime * 0.35) {
			beamUsed = true;
			noroBeam(player);
		}
		if (raceTicks >= rivalTime) {
			gameOver(player, false, "Their racers crossed the finish line first.");
		}
	}

	private void noroBeam(ServerPlayer player) {
		player.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 4));
		say(player, "Foxy", "Noro Noro Beam! Fehehehe! You're sooo slow!");
		Vec3 from = captain != null && captain.isAlive() ? captain.getEyePosition() : Vec3.atCenterOf(center.above(3));
		Vec3 to = player.getEyePosition();
		for (int i = 0; i <= 20; i++) {
			Vec3 p = from.lerp(to, i / 20.0);
			level.sendParticles(ParticleTypes.GLOW, p.x, p.y, p.z, 2, 0.05, 0.05, 0.05, 0.0);
		}
		sound(SoundEvents.BEACON_ACTIVATE, 1.0f, 1.8f);
	}

	// ---------- 2. Groggy Ring ----------

	private void startGroggy(ServerPlayer player) {
		phase = Phase.GROGGY;
		timer = 180 * 20;
		groggy.clear();
		for (int i = 0; i < 3; i++) {
			HumanNpc monster = fighter("pirate", spot(150 + 30 * i, 10), "Groggy Monster " + (i + 1),
					34 * rival.strength() * 1.4, 5 * (1 + 0.2 * rival.tier));
			if (monster != null) {
				setBase(monster, Attributes.SCALE, 1.3);
				groggy.add(monster);
			}
		}
		ballMan = fighter("rookie_pirate", spot(180, 12), "Ball Man", 26 * rival.strength() * 1.3, 3 * (1 + 0.2 * rival.tier));
		if (ballMan != null) {
			ballMan.addEffect(new MobEffectInstance(MobEffects.GLOWING, 20 * 600, 0, false, false));
			groggy.add(ballMan);
		}
		for (Mob mob : groggy) {
			mob.setTarget(player);
		}
		say(player, "Itomimizu", "The Groggy Ring! Knock out their Ball Man (the glowing one) to win! Your crewmates may join in!");
	}

	private void tickGroggy(ServerPlayer player) {
		timer--;
		groggy.removeIf(mob -> !mob.isAlive());
		if (ticks % 4 == 0) {
			drawRing(GROGGY_RING, ParticleTypes.HAPPY_VILLAGER);
		}
		if (ticks % 20 == 0) {
			for (Mob mob : groggy) {
				keepInside(mob, GROGGY_RING + 1);
				if (mob.getTarget() == null || !mob.getTarget().isAlive()) {
					mob.setTarget(player);
				}
			}
		}
		if (ballMan == null || !ballMan.isAlive()) {
			gameOver(player, true, "The Ball Man is down!");
			return;
		}
		if (ringOut(player, GROGGY_RING + 3)) {
			gameOver(player, false, "You ran out of the Groggy Ring.");
			return;
		}
		updateBar("Ball Man " + (int) Math.ceil(ballMan.getHealth()) + " HP, " + timer / 20 + "s left", ballMan.getHealth() / ballMan.getMaxHealth());
		if (timer <= 0) {
			gameOver(player, false, "Time's up! The Ball Man is still standing.");
		}
	}

	// ---------- 3. Combat ----------

	private void startCombat(ServerPlayer player) {
		phase = Phase.COMBAT;
		beamCooldown = 160;
		if (captain == null || !captain.isAlive()) {
			gameOver(player, true, "Their captain didn't show up!");
			return;
		}
		captain.teleportTo(spot(180, 5).getX() + 0.5, spot(180, 5).getY(), spot(180, 5).getZ() + 0.5);
		wake(captain);
		captain.setTarget(player);
		say(player, rival.foxy ? "Foxy" : rival.captainName, "Captain against captain! No crewmates, no running. Let's go!");
		player.sendSystemMessage(Component.literal("Stay inside the ring (the flames). Your crewmates can't help here.").withStyle(ChatFormatting.GRAY));
	}

	private void tickCombat(ServerPlayer player) {
		if (ticks % 4 == 0) {
			drawRing(COMBAT_RING, ParticleTypes.FLAME);
		}
		if (captain == null || !captain.isAlive()) {
			gameOver(player, true, "You knocked out " + rival.captainName + "!");
			return;
		}
		if (ringOut(player, COMBAT_RING + 1.5)) {
			gameOver(player, false, "Ring out!");
			return;
		}
		keepInside(captain, COMBAT_RING);
		if (ticks % 20 == 0 && captain.getTarget() != player) {
			captain.setTarget(player);
		}
		if (rival.foxy && --beamCooldown <= 0 && captain.hasLineOfSight(player)) {
			beamCooldown = 200;
			noroBeam(player);
		}
		updateBar(rival.captainName + " " + (int) Math.ceil(captain.getHealth()) + " HP", captain.getHealth() / captain.getMaxHealth());
	}

	// ---------- Results ----------

	private void gameOver(ServerPlayer player, boolean won, String why) {
		for (Mob mob : groggy) {
			poof(mob);
			mob.discard();
		}
		groggy.clear();
		ballMan = null;
		if (game == 2 && captain != null && captain.isAlive()) {
			wait(captain);
		}

		lastWon = won;
		player.sendSystemMessage(Component.literal(GAMES[game] + ": " + (won ? "you win! " : "you lose. ") + why)
				.withStyle(won ? ChatFormatting.GREEN : ChatFormatting.RED));
		if (won) {
			wins++;
			title(player, "You win!", GAMES[game] + ": " + why);
			sound(SoundEvents.PLAYER_LEVELUP, 1.0f, 1.0f);
			offerPick(player);
		} else {
			losses++;
			title(player, "You lose!", GAMES[game] + ": " + why);
			sound(SoundEvents.VILLAGER_NO, 1.0f, 0.8f);
			rivalTakes(player);
			phase = Phase.PICK;
			timer = 100;
		}
	}

	private void offerPick(ServerPlayer player) {
		phase = Phase.PICK;
		timer = PICK_TICKS;
		options.clear();
		Crew crew = player.getAttached(CrewAttachments.CREW);
		for (RivalCrew.Member member : rival.members) {
			if (crew != null && crew.member(member.role) == null) {
				options.add(member);
			}
		}
		pickCode++;
		say(player, "Itomimizu", "The winner picks one member of the " + rival.crewName + "!");
		int berries = berryPrize();
		if (options.isEmpty()) {
			player.sendSystemMessage(Component.literal(crew == null ? "You have no crew to take anyone into, so you take Berries."
					: "Every role they have is already filled in your crew, so you take Berries.").withStyle(ChatFormatting.GRAY));
			pick(player, -1);
			return;
		}
		MutableComponent menu = Component.literal("Choose (30 s): ").withStyle(ChatFormatting.GOLD);
		for (int i = 0; i < options.size(); i++) {
			RivalCrew.Member member = options.get(i);
			int index = i;
			String label = member.taken != null ? "[Win back " + member.fullName() + "]" : "[" + member.fullName() + ", Lv " + member.level + "]";
			menu.append(Component.literal(label + " ").withStyle(style -> style
					.withColor(member.taken != null ? ChatFormatting.GREEN : ChatFormatting.AQUA)
					.withClickEvent(new ClickEvent.RunCommand("/davyback pick " + pickCode + " " + index))
					.withHoverEvent(new HoverEvent.ShowText(Component.literal(member.personality.title() + " " + member.role.title()
							+ ". Perk: " + member.role.perk() + ".")))));
		}
		menu.append(Component.literal("[" + berries + " Berries instead]").withStyle(style -> style
				.withColor(ChatFormatting.YELLOW)
				.withClickEvent(new ClickEvent.RunCommand("/davyback pick " + pickCode + " berries"))));
		player.sendSystemMessage(menu);
	}

	private int berryPrize() {
		return 15 * (rival.tier + 1);
	}

	/** From /davyback pick: `code` must match the menu the player clicked, so an old menu does nothing. */
	public void pickCommand(ServerPlayer player, int code, String choice) {
		if (phase != Phase.PICK || code != pickCode || options.isEmpty()) {
			player.sendSystemMessage(Component.literal("That choice has passed.").withStyle(ChatFormatting.GRAY));
			return;
		}
		if ("berries".equals(choice)) {
			pick(player, -1);
			return;
		}
		try {
			int index = Integer.parseInt(choice);
			if (index >= 0 && index < options.size()) {
				pick(player, index);
			}
		} catch (NumberFormatException ignored) {
			// Not a number: ignore it.
		}
	}

	/** Takes option `index` (-1 = Berries) if the player won the game, then moves on to the next game. */
	private void pick(ServerPlayer player, int index) {
		if (phase != Phase.PICK) {
			return;
		}
		if (lastWon) {
			RivalCrew.Member member = index >= 0 && index < options.size() ? options.get(index) : null;
			if (member != null) {
				recruit(player, member);
			} else {
				giveBerries(player, berryPrize());
				player.sendSystemMessage(Component.literal("You took " + berryPrize() + " Berries from the " + rival.crewName + ".")
						.withStyle(ChatFormatting.GOLD));
			}
		}
		options.clear();
		pickCode++;
		next(player);
	}

	private void next(ServerPlayer player) {
		game++;
		if (game >= GAMES.length) {
			finish(player);
			return;
		}
		phase = Phase.COUNTDOWN;
		timer = 100;
		updateBar("next game in 5 seconds", 1);
		bar.setName(Component.literal("Davy Back Fight (" + wins + "-" + losses + ") next: " + GAMES[game]));
	}

	/** The member joins the player's crew as a normal crewmate (without counting as a hire). */
	private void recruit(ServerPlayer player, RivalCrew.Member member) {
		Crew crew = player.getAttached(CrewAttachments.CREW);
		HumanNpc standIn = lineup.remove(member);
		rival.members.remove(member);
		if (crew == null || crew.member(member.role) != null) {
			return;
		}
		CrewmateEntity crewmate = CrewEntities.CREWMATE.create(level, EntitySpawnReason.MOB_SUMMONED);
		if (crewmate == null) {
			return;
		}
		Vec3 at = standIn != null ? standIn.position() : player.position();
		if (standIn != null) {
			poof(standIn);
			standIn.discard();
		}
		crewmate.setPos(at.x, at.y, at.z);
		crewmate.setProfile(member.role, member.variant, member.personality);
		int xp = 0;
		for (int l = 1; l < member.level; l++) {
			xp += CrewLevels.xpToNext(l);
		}
		crewmate.addXp(xp); // Before setCaptain, so the level-ups don't flood the chat.
		crewmate.setCaptain(player);
		crewmate.setHealth(crewmate.getMaxHealth());
		crewmate.setCustomName(Component.literal(member.fullName()));
		crewmate.setCustomNameVisible(true);
		crewmate.setPersistenceRequired();
		level.addFreshEntity(crewmate);

		Map<String, UUID> members = new HashMap<>(crew.members());
		members.put(member.role.id(), crewmate.getUUID());
		player.setAttached(CrewAttachments.CREW, new Crew(crew.name(), members, crew.hires()));
		if (member.taken != null) {
			player.setAttached(ArenaFeature.RECORD, ArenaFeature.record(player).withoutTaken(member.taken));
			crewmate.tellCaptain("Captain! You won me back! I knew you would!");
		} else {
			crewmate.tellCaptain("Fine, fine, a deal's a deal. I'm with the " + crew.name() + " now!");
		}
		player.sendSystemMessage(Component.literal(member.fullName() + " joined the " + crew.name() + "! Perk: " + member.role.perk() + ".")
				.withStyle(ChatFormatting.GOLD));
		CrewPayloads.refresh(player);
	}

	/** The rival crew takes the player's best crewmate (or some Berries if the crew is empty). */
	private void rivalTakes(ServerPlayer player) {
		Crew crew = player.getAttached(CrewAttachments.CREW);
		if (crew == null || crew.members().isEmpty()) {
			int taken = takeBerries(player, berryPrize());
			say(player, rival.captainName, taken > 0 ? "No crewmates to take? Then I'll take " + taken + " Berries!"
					: "No crewmates, no Berries... what a sad crew!");
			return;
		}
		CrewmateEntity best = null;
		CrewRole bestRole = null;
		for (Map.Entry<String, UUID> entry : crew.members().entrySet()) {
			CrewmateEntity crewmate = CrewRoster.find(level.getServer(), entry.getValue());
			if (crewmate != null && (best == null || crewmate.getCrewLevel() > best.getCrewLevel())) {
				best = crewmate;
				bestRole = CrewRole.byId(entry.getKey());
			}
		}
		ArenaRecord.Taken taken;
		UUID id;
		if (best != null && bestRole != null) {
			taken = new ArenaRecord.Taken(bestRole.id(), best.getVariantIndex(), best.getPersonality().name(),
					best.hasCustomName() ? best.getCustomName().getString() : bestRole.title(), best.getCrewLevel(), rival.crewName);
			id = best.getUUID();
		} else {
			// Nobody is loaded nearby: they take whoever is first on the list, as a fresh recruit.
			Map.Entry<String, UUID> first = crew.members().entrySet().iterator().next();
			bestRole = CrewRole.byId(first.getKey());
			if (bestRole == null) {
				return;
			}
			taken = new ArenaRecord.Taken(bestRole.id(), 0, CrewPersonality.STEADY.name(), bestRole.title(), 1, rival.crewName);
			id = first.getValue();
		}
		player.setAttached(CrewAttachments.CREW, crew.withoutMember(bestRole));
		CrewHiring.dismiss(level.getServer(), id);
		player.setAttached(ArenaFeature.RECORD, ArenaFeature.record(player).withTaken(taken));
		rival.addWon(taken);
		addToLineup(rival.members.get(0));
		say(player, rival.captainName, "I'll take " + taken.name() + "! Welcome to the " + rival.crewName + "!");
		player.sendSystemMessage(Component.literal(taken.name() + " has to join the " + rival.crewName
				+ ". Win a Davy Back Fight game to take them back (/davyback record).").withStyle(ChatFormatting.RED));
		CrewPayloads.refresh(player);
	}

	private static int takeBerries(ServerPlayer player, int amount) {
		int left = amount;
		var inventory = player.getInventory();
		for (int i = 0; i < inventory.getContainerSize() && left > 0; i++) {
			ItemStack stack = inventory.getItem(i);
			if (stack.is(CharacterFeature.BERRY)) {
				int take = Math.min(left, stack.getCount());
				stack.shrink(take);
				left -= take;
			}
		}
		inventory.setChanged();
		return amount - left;
	}

	private void finish(ServerPlayer player) {
		phase = Phase.DONE;
		boolean won = wins >= 2;
		ArenaRecord record = ArenaFeature.record(player);
		boolean firstFoxy = rival.foxy && won && !record.foxyBeaten();
		player.setAttached(ArenaFeature.RECORD, record.withFight(won, rival.foxy && won));
		if (won) {
			title(player, "Victory!", "You won the Davy Back Fight " + wins + "-" + losses);
			int berries = 30 * (rival.tier + 1);
			giveBerries(player, berries);
			player.sendSystemMessage(Component.literal("The " + rival.crewName + " pay up: " + berries + " Berries.").withStyle(ChatFormatting.GOLD));
			Bounty.raise(player, 8_000_000L * (rival.tier + 1) + (firstFoxy ? 20_000_000L : 0),
					"You beat the " + rival.crewName + " in a Davy Back Fight.", false);
			if (firstFoxy) {
				level.getServer().getPlayerList().broadcastSystemMessage(Component.literal("[News Coo] The " + crewName(player)
						+ " beat Foxy the Silver Fox at his own game on Long Ring Long Land!").withStyle(ChatFormatting.GOLD), false);
			}
		} else {
			title(player, "Defeat", "You lost the Davy Back Fight " + wins + "-" + losses);
		}
		say(player, rival.foxy ? "Foxy" : rival.captainName, won ? "Grr... we'll get you next time!" : "Fehehe! Come back when you're stronger!");
	}

	@Override
	protected void playerDown(ServerPlayer player) {
		revive(player);
		switch (phase) {
			case RACE, GROGGY, COMBAT -> gameOver(player, false, "You were knocked out.");
			default -> { }
		}
	}

	@Override
	protected void forfeit(ServerPlayer player, String why) {
		phase = Phase.DONE;
		player.sendSystemMessage(Component.literal(why + " The " + rival.crewName + " sail off. The Davy Back Fight is over.")
				.withStyle(ChatFormatting.GRAY));
	}
}
