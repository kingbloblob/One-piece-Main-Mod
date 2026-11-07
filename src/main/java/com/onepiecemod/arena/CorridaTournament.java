package com.onepiecemod.arena;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.BossEvent;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.creature.CreatureEntity;
import com.onepiecemod.creature.Creatures;
import com.onepiecemod.npc.HumanNpc;

/**
 * A tournament at the Corrida Colosseum in Dressrosa. Three rounds, fought alone (no crewmates):
 *  1. Block battle royale: every gladiator for themselves, last one standing wins.
 *  2. A duel against a famous gladiator.
 *  3. The final against the cup's champion.
 * Falling in the arena (running out of health) or stepping out of the ring loses the tournament,
 * but nobody dies: the medics carry you out.
 *
 * Three cups, each unlocked by winning the one before: Rookie, Veteran and Champion.
 * The first Champion Cup win pays the prize from the show: the Mera Mera no Mi.
 */
public class CorridaTournament extends ArenaMatch {
	/** One fighter in a round: an NPC kit (or "beast:<creature>"), a name (null = the kit's own) and its strength. */
	private record Entry(String kit, String name, double health, double damage, double scale) {
		static Entry crowd(String kit) {
			return new Entry(kit, null, 1, 1, 0);
		}
	}

	private record Round(String title, List<Entry> fighters) {}

	public enum Cup {
		ROOKIE("Rookie Cup", 1, 1.0, 40, 5_000_000L,
				new Round("Block Battle Royale", List.of(Entry.crowd("rookie_pirate"), Entry.crowd("bandit"),
						Entry.crowd("bounty_hunter"), Entry.crowd("rookie_pirate"))),
				new Round("Duel: Ideo the Destroyer Cannon", List.of(new Entry("pirate", "Ideo the Destroyer Cannon", 70, 7, 1.15))),
				new Round("Final: Ucy the Fighting Bull", List.of(new Entry("beast:fighting_bull", "Ucy the Fighting Bull", 90, 9, 0)))),
		VETERAN("Veteran Cup", 2, 1.4, 120, 30_000_000L,
				new Round("Block Battle Royale", List.of(Entry.crowd("pirate"), Entry.crowd("pirate_gunner"), Entry.crowd("fishman"),
						Entry.crowd("baroque_agent"), Entry.crowd("bounty_hunter"))),
				new Round("Duel: Bartolomeo the Cannibal", List.of(new Entry("pirate_captain", "Bartolomeo the Cannibal", 130, 10, 0))),
				new Round("Final: Jesus Burgess, the Champion", List.of(new Entry("blackbeard_pirate", "Jesus Burgess, the Champion", 200, 13, 1.35)))),
		CHAMPION("Champion Cup", 3, 1.9, 300, 150_000_000L,
				new Round("Block Battle Royale", List.of(Entry.crowd("gifter"), Entry.crowd("headliner"), Entry.crowd("whitebeard_pirate"),
						Entry.crowd("donquixote"), Entry.crowd("fishman"), Entry.crowd("pirate_captain"))),
				new Round("Duel: Cavendish of the White Horse", List.of(new Entry("pirate_captain", "Cavendish of the White Horse", 220, 15, 0))),
				new Round("Final: Diamante, Hero of the Colosseum", List.of(new Entry("donquixote", "Diamante, Hero of the Colosseum", 340, 18, 1.25))));

		final String title;
		final int tickets;
		final double crowdStrength;
		final int berries;
		final long bounty;
		final List<Round> rounds;

		Cup(String title, int tickets, double crowdStrength, int berries, long bounty, Round... rounds) {
			this.title = title;
			this.tickets = tickets;
			this.crowdStrength = crowdStrength;
			this.berries = berries;
			this.bounty = bounty;
			this.rounds = List.of(rounds);
		}

		public String title() {
			return title;
		}

		public int tickets() {
			return tickets;
		}

		public static Cup byName(String name) {
			for (Cup cup : values()) {
				if (cup.name().equalsIgnoreCase(name)) {
					return cup;
				}
			}
			return null;
		}
	}

	private static final int COUNTDOWN = 100;
	private static final int BREAK = 120;
	private static final double MAX_RING = 15;

	private final Cup cup;
	/** Ring size: up to 15 blocks, smaller when the arena floor ends sooner (a moat, a wall). */
	private final double ring;

	@Override
	protected double clearRadius() {
		return ring + 1;
	}
	private int round = 0;
	private int timer = COUNTDOWN;
	private boolean fighting = false;
	private final List<Mob> fighters = new ArrayList<>();
	private float roundHealth = 1;
	private boolean over = false;

	public CorridaTournament(ServerPlayer player, BlockPos center, Cup cup) {
		super(player, center, "Corrida Colosseum: " + cup.title, BossEvent.BossBarColor.YELLOW);
		this.cup = cup;
		this.ring = floorRadius(MAX_RING);
		if (distance(player) > ring - 3 || Math.abs(player.getY() - center.getY()) > 3) {
			// Walk out onto the sand: the gate opens and the challenger is led into the ring.
			BlockPos start = spot(0, 3);
			player.teleportTo(start.getX() + 0.5, start.getY(), start.getZ() + 0.5);
		}
		say(player, "Gatz", "Ladies and gentlemen, welcome to the Corrida Colosseum! A new challenger enters the " + cup.title + "!");
		player.sendSystemMessage(Component.literal("Rules: fight alone, stay inside the ring, and the last one standing wins. "
				+ "If you fall, the medics carry you out.").withStyle(ChatFormatting.GRAY));
		announceRound(player);
	}

	@Override
	protected int leashRadius() {
		return 40;
	}

	private void announceRound(ServerPlayer player) {
		Round next = cup.rounds.get(round);
		bar.setName(Component.literal(cup.title + ": round " + (round + 1) + "/" + cup.rounds.size() + ", " + next.title() + " (get ready)"));
		bar.setProgress(1);
		title(player, "Round " + (round + 1), next.title());
	}

	@Override
	protected boolean tick(ServerPlayer player) {
		if (over) {
			return false;
		}
		if (ticks % 4 == 0) {
			drawRing(ring, fighting ? ParticleTypes.FLAME : ParticleTypes.END_ROD);
		}
		if (!fighting) {
			if (--timer <= 0) {
				startRound(player);
			} else if (timer % 20 == 0 && timer <= 60) {
				player.sendSystemMessage(Component.literal(String.valueOf(timer / 20)).withStyle(ChatFormatting.GOLD), true);
				sound(SoundEvents.NOTE_BLOCK_BELL.value(), 1.0f, 1.0f);
			}
			return true;
		}

		// Ring out: stepping over the edge loses the tournament.
		double out = distance(player);
		if (ringOut(player, ring + 1.5)) {
			lose(player, "You stepped out of the ring!");
			return false;
		}
		if (out > ring - 2 && ticks % 20 == 0) {
			player.sendSystemMessage(Component.literal("Careful: the edge of the ring!").withStyle(ChatFormatting.RED), true);
		}

		fighters.removeIf(mob -> !mob.isAlive());
		if (ticks % 20 == 0) {
			pickTargets(player);
		}
		for (Mob mob : fighters) {
			keepInside(mob, ring + 1);
		}
		float total = 0;
		for (Mob mob : fighters) {
			total += mob.getHealth() / mob.getMaxHealth();
		}
		bar.setProgress(Math.max(0, Math.min(1, total / Math.max(1, roundHealth))));
		bar.setName(Component.literal(cup.title + ": round " + (round + 1) + "/" + cup.rounds.size() + ", "
				+ cup.rounds.get(round).title() + (fighters.size() > 1 ? " (" + fighters.size() + " left)" : "")));

		if (fighters.isEmpty()) {
			roundWon(player);
		}
		return !over;
	}

	private void startRound(ServerPlayer player) {
		fighting = true;
		Round current = cup.rounds.get(round);
		int count = current.fighters().size();
		for (int i = 0; i < count; i++) {
			Entry entry = current.fighters().get(i);
			BlockPos pos = spot(360.0 * i / count + 30, ring * 0.6);
			Mob mob = spawn(entry, pos);
			if (mob != null) {
				fighters.add(mob);
			}
		}
		roundHealth = fighters.size();
		title(player, "FIGHT!", current.title());
		sound(SoundEvents.RAID_HORN.value(), 1.5f, 1.2f);
		pickTargets(player);
	}

	private Mob spawn(Entry entry, BlockPos pos) {
		if (entry.kit().startsWith("beast:")) {
			EntityType<CreatureEntity> type = Creatures.TYPES.get(entry.kit().substring(6));
			CreatureEntity beast = type == null ? null : type.create(level, EntitySpawnReason.EVENT);
			if (beast == null) {
				return null;
			}
			beast.snapTo(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5, 0, 0);
			setBase(beast, Attributes.MAX_HEALTH, entry.health());
			setBase(beast, Attributes.ATTACK_DAMAGE, entry.damage());
			beast.setHealth(beast.getMaxHealth());
			beast.setCustomName(Component.literal(entry.name()).withStyle(ChatFormatting.GOLD));
			beast.setCustomNameVisible(true);
			level.addFreshEntity(beast);
			mark(beast);
			return beast;
		}
		HumanNpc npc = entry.name() == null
				? fighter(entry.kit(), pos, null, cup.crowdStrength, 1 + (cup.crowdStrength - 1) * 0.6)
				: fighter(entry.kit(), pos, entry.name(), entry.health(), entry.damage());
		if (npc != null && entry.scale() > 0) {
			setBase(npc, Attributes.SCALE, entry.scale());
		}
		if (npc != null && entry.name() != null) {
			setBase(npc, Attributes.ARMOR, 4 + 4 * cup.ordinal());
			setBase(npc, Attributes.KNOCKBACK_RESISTANCE, 0.5);
		}
		return npc;
	}

	/** Everyone for themselves: each gladiator goes for the nearest other fighter or the player. */
	private void pickTargets(ServerPlayer player) {
		for (Mob mob : fighters) {
			LivingEntity current = mob.getTarget();
			if (current != null && current.isAlive() && (current == player || fighters.contains(current))
					&& mob.getRandom().nextInt(4) != 0) {
				continue;
			}
			LivingEntity best = player.isCreative() || player.isSpectator() ? null : player;
			double bestDistance = best == null ? Double.MAX_VALUE : mob.distanceToSqr(player) * 1.3;
			for (Mob other : fighters) {
				double d = mob.distanceToSqr(other);
				if (other != mob && d < bestDistance) {
					best = other;
					bestDistance = d;
				}
			}
			mob.setTarget(best);
		}
	}

	private void roundWon(ServerPlayer player) {
		fighting = false;
		round++;
		sound(SoundEvents.PLAYER_LEVELUP, 1.0f, 1.0f);
		if (round >= cup.rounds.size()) {
			win(player);
			return;
		}
		player.heal(player.getMaxHealth() * 0.3f);
		say(player, "Gatz", "What a fight! The crowd goes wild! Next up: " + cup.rounds.get(round).title() + "!");
		timer = BREAK;
		announceRound(player);
	}

	private void win(ServerPlayer player) {
		over = true;
		ArenaRecord record = ArenaFeature.record(player);
		boolean firstTime = record.corridaBest() < cup.ordinal();
		player.setAttached(ArenaFeature.RECORD, record.withCorridaWin(cup.ordinal()));
		title(player, "CHAMPION!", "You won the " + cup.title);
		say(player, "Gatz", player.getName().getString() + " wins the " + cup.title + "! What a warrior!");
		sound(SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, 1.0f, 1.0f);
		level.sendParticles(ParticleTypes.TOTEM_OF_UNDYING, player.getX(), player.getY() + 1, player.getZ(), 60, 0.6, 1.0, 0.6, 0.3);

		int berries = firstTime ? cup.berries : cup.berries / 2;
		giveBerries(player, berries);
		player.sendSystemMessage(Component.literal("Prize: " + berries + " Berries.").withStyle(ChatFormatting.GOLD));
		if (cup == Cup.CHAMPION && firstTime) {
			// The prize of the Dressrosa tournament: Ace's Flame-Flame Fruit.
			Item fruit = BuiltInRegistries.ITEM.getOptional(Identifier.fromNamespaceAndPath("onepiece", "mera_mera_no_mi")).orElse(null);
			if (fruit != null) {
				ItemStack stack = new ItemStack(fruit);
				if (!player.getInventory().add(stack)) {
					player.drop(stack, false, net.minecraft.util.Prediction.SERVER_ONLY);
				}
				player.sendSystemMessage(Component.literal("Grand prize: the Mera Mera no Mi, the Flame-Flame Fruit!").withStyle(ChatFormatting.RED));
			}
			player.level().getServer().getPlayerList().broadcastSystemMessage(Component.literal("[News Coo] "
					+ player.getName().getString() + " has won the Corrida Colosseum and claimed the Flame-Flame Fruit!")
					.withStyle(ChatFormatting.GOLD), false);
		}
		long bounty = firstTime ? cup.bounty : cup.bounty / 10;
		Bounty.raise(player, bounty, "The world heard about your win at the Corrida Colosseum.", false);
		if (cup.ordinal() + 1 < Cup.values().length && firstTime) {
			player.sendSystemMessage(Component.literal("The " + Cup.values()[cup.ordinal() + 1].title + " is now open to you ("
					+ Cup.values()[cup.ordinal() + 1].tickets + " Colosseum Tickets).").withStyle(ChatFormatting.YELLOW));
		}
	}

	private void lose(ServerPlayer player, String why) {
		over = true;
		title(player, "Defeated", why);
		say(player, "Gatz", "Oh no! " + player.getName().getString() + " is out of the " + cup.title + "! Better luck next time!");
		sound(SoundEvents.VILLAGER_NO, 1.0f, 0.8f);
		player.sendSystemMessage(Component.literal("You lost in round " + (round + 1) + ". Buy another ticket to try again.")
				.withStyle(ChatFormatting.GRAY));
	}

	@Override
	protected void playerDown(ServerPlayer player) {
		revive(player);
		lose(player, "The medics carried you out of the arena.");
	}

	@Override
	protected void forfeit(ServerPlayer player, String why) {
		over = true;
		player.sendSystemMessage(Component.literal(why + " The " + cup.title + " is over.").withStyle(ChatFormatting.GRAY));
	}
}
