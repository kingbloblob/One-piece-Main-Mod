package com.onepiecemod.shipcombat;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.jetbrains.annotations.Nullable;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerBossEvent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.BossEvent;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.sound.ModSounds;

/**
 * Naval battles: a whole fleet instead of one ship.
 *  - Marine fleets hunt well-known pirates (bounty 50,000,000+) on the Grand Line: a flagship one tier tougher than
 *    the rest, and two or three warships sailing with her.
 *  - Pirate armadas roam the Grand Line now and then, and go after anyone.
 * A bar at the top of the screen counts the ships left. Sink or capture every one of them to win the battle: a big
 * bonus on top of what each ship pays (bounty for Marine fleets, berries and treasure for both).
 * Sail more than 300 blocks away (or take longer than 15 minutes) and the fleet loses you: no bonus.
 */
public class NavalBattles {
	/** Every ship in a fleet carries this tag (ShipCombat shows their own hull bars only up close, so the screen stays readable). */
	public static final String TAG_FLEET = "onepiece_fleet";

	// ---- How often. Change these to meet more or fewer fleets. ----
	/** Chance that a sea encounter on the Grand Line is a Marine fleet, for players with at least this bounty level. */
	private static final float MARINE_FLEET_CHANCE = 0.2f;
	private static final int MARINE_FLEET_THREAT = 2; // Bounty level "Known Pirate" (50,000,000)
	/** Chance that a sea encounter on the Grand Line is a pirate armada. */
	private static final float ARMADA_CHANCE = 0.06f;
	/**
	 * Fleets only come for a ship that can fight back. Playtest 2026-11-01: a tier 1 Marine fleet (about 2,800 hull
	 * between three warships) sank a one-cannon Going Merry in 20-70 seconds, with no way to win. Smaller ships still
	 * meet single enemy ships as before.
	 */
	private static final int FLEET_MIN_GUNS = 4;

	private static final int GIVE_UP_TICKS = 20 * 60 * 15;
	private static final double LOSE_YOU = 300;
	/** A fleet ship that vanishes this close to the player was sunk or boarded, not left behind. */
	private static final double SAW_IT_GO = 128;

	private static final class Battle {
		final ServerLevel level;
		final UUID player;
		final ShipBrain.Faction faction;
		final int tier;
		final String title;
		final Map<UUID, Vec3> ships = new HashMap<>(); // Still afloat, with where each was last seen.
		final int total;
		final long started;
		final ServerBossEvent bar;
		int beaten;

		Battle(ServerLevel level, ServerPlayer player, ShipBrain.Faction faction, int tier, List<ShipEntity> fleet) {
			this.level = level;
			this.player = player.getUUID();
			this.faction = faction;
			this.tier = tier;
			this.title = faction == ShipBrain.Faction.MARINE ? "Marine Fleet" : "Pirate Armada";
			for (ShipEntity ship : fleet) {
				ships.put(ship.getUUID(), ship.position());
			}
			this.total = fleet.size();
			this.started = level.getGameTime();
			this.bar = new ServerBossEvent(UUID.randomUUID(), Component.literal(title),
					faction == ShipBrain.Faction.MARINE ? BossEvent.BossBarColor.BLUE : BossEvent.BossBarColor.PURPLE,
					BossEvent.BossBarOverlay.NOTCHED_6);
			bar.addPlayer(player);
			updateBar();
		}

		void updateBar() {
			bar.setName(Component.literal(title + ":  " + ships.size() + " of " + total + " ships left"));
			bar.setProgress(total == 0 ? 0 : (float) ships.size() / total);
		}
	}

	private static final List<Battle> BATTLES = new ArrayList<>();

	public static boolean isFleetShip(ShipEntity ship) {
		return ship.entityTags().contains(TAG_FLEET);
	}

	/** True if this player is already fighting a fleet. */
	public static boolean inBattle(ServerPlayer player) {
		for (Battle battle : BATTLES) {
			if (battle.player.equals(player.getUUID())) {
				return true;
			}
		}
		return false;
	}

	/**
	 * Called by SeaEncounters for each meeting: sometimes the meeting is a whole fleet. Returns true if one set out
	 * (then SeaEncounters sends nothing else).
	 */
	static boolean maybeMeet(ServerLevel level, ServerPlayer player, ShipEntity playerShip, boolean grandLine) {
		if (!grandLine || inBattle(player) || Cannons.guns(playerShip).size() < FLEET_MIN_GUNS) {
			return false;
		}
		RandomSource random = level.getRandom();
		int threat = Bounty.threatLevel(player);
		if (threat >= MARINE_FLEET_THREAT && random.nextFloat() < MARINE_FLEET_CHANCE) {
			return start(level, player, player.position(), playerShip.getYRot(), 90, ShipBrain.Faction.MARINE, Mth.clamp(threat - 1, 1, 4)) != null;
		}
		if (random.nextFloat() < ARMADA_CHANCE) {
			return start(level, player, player.position(), playerShip.getYRot(), 90, ShipBrain.Faction.PIRATE, Mth.clamp(2 + threat / 2, 2, 4)) != null;
		}
		return false;
	}

	/**
	 * Sends a fleet at a player: a flagship (tier + 1) about `distance` blocks from `center`, and escorts at `tier`
	 * around her. Returns the flagship, or null if there was no open sea for her.
	 */
	@Nullable
	public static ShipEntity start(ServerLevel level, ServerPlayer player, Vec3 center, float heading, double distance, ShipBrain.Faction faction, int tier) {
		int flagTier = Math.min(5, tier + 1);
		ShipEntity flagship = SeaEncounters.spawnAt(level, center, heading, distance, faction, flagTier, null);
		if (flagship == null) {
			return null;
		}
		List<ShipEntity> fleet = new ArrayList<>();
		fleet.add(flagship);
		int escorts = 2 + (tier >= 3 ? 1 : 0);
		for (int i = 0; i < escorts; i++) {
			ShipEntity escort = SeaEncounters.spawnAt(level, center, heading, distance, faction, tier, flagship.position());
			if (escort != null) {
				fleet.add(escort);
			}
		}
		for (ShipEntity ship : fleet) {
			ship.addTag(TAG_FLEET);
		}
		String name = flagship.getName().getString();
		flagship.setCustomName(Component.literal("Flagship " + name)
				.withStyle(ChatFormatting.GOLD));

		Battle battle = new Battle(level, player, faction, tier, fleet);
		BATTLES.add(battle);
		if (faction == ShipBrain.Faction.MARINE) {
			ModSounds.play(player, ModSounds.NAVY_BUGLE);
			player.sendSystemMessage(Component.literal("A Marine fleet of " + fleet.size() + " warships is closing in! Sink or board every one of them.")
					.withStyle(ChatFormatting.RED, ChatFormatting.BOLD));
		} else {
			player.sendSystemMessage(Component.literal("A pirate armada of " + fleet.size() + " ships, led by the " + name
					+ ", is coming for you! Sink or board every one of them.").withStyle(ChatFormatting.RED, ChatFormatting.BOLD));
		}
		return flagship;
	}

	/** Once a second: which fleet ships are gone, and has anyone won? */
	static void tick(MinecraftServer server) {
		Iterator<Battle> it = BATTLES.iterator();
		while (it.hasNext()) {
			Battle battle = it.next();
			ServerPlayer player = server.getPlayerList().getPlayer(battle.player);
			boolean playerHere = player != null && player.isAlive() && player.level() == battle.level;

			Iterator<Map.Entry<UUID, Vec3>> ships = battle.ships.entrySet().iterator();
			double nearest = Double.MAX_VALUE;
			while (ships.hasNext()) {
				Map.Entry<UUID, Vec3> entry = ships.next();
				Entity entity = battle.level.getEntity(entry.getKey());
				if (entity instanceof ShipEntity ship && !ship.isRemoved() && !ship.sinking && ShipBrain.isAi(ship)) {
					entry.setValue(ship.position());
					if (playerHere) {
						nearest = Math.min(nearest, player.distanceTo(ship));
					}
					continue;
				}
				// Sinking, boarded (a boarded ship turns into blocks), or gone. It counts if the player was there to see it.
				boolean sank = entity instanceof ShipEntity ship && ship.sinking;
				if (sank || playerHere && player.position().distanceTo(entry.getValue()) < SAW_IT_GO) {
					battle.beaten++;
				}
				ships.remove();
			}
			battle.updateBar();

			if (battle.ships.isEmpty()) {
				if (playerHere && battle.beaten > 0) {
					win(player, battle);
				}
				battle.bar.removeAllPlayers();
				it.remove();
			} else if (!playerHere || nearest > LOSE_YOU || battle.level.getGameTime() - battle.started > GIVE_UP_TICKS) {
				if (player != null) {
					player.sendSystemMessage(Component.literal("The " + battle.title + " has lost sight of you.").withStyle(ChatFormatting.GRAY));
				}
				battle.bar.removeAllPlayers();
				it.remove();
			}
		}
	}

	private static void win(ServerPlayer player, Battle battle) {
		com.onepiecemod.advancement.AdvancementFeature.grant(player, "journey/win_naval_battle");
		battle.level.playSound(null, player.blockPosition(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 1.0f, 1.0f);
		give(player, new ItemStack(CharacterFeature.BERRY, 24 + battle.tier * 12));
		give(player, new ItemStack(Items.GOLD_INGOT, 4 + battle.tier * 2));
		if (battle.tier >= 2) {
			give(player, new ItemStack(Items.DIAMOND, battle.tier - 1));
		}
		if (battle.faction == ShipBrain.Faction.MARINE) {
			Bounty.raise(player, 40_000_000L * (battle.tier + 1), "You defeated a whole Marine fleet!", true);
		} else {
			player.sendSystemMessage(Component.literal("The armada is beaten! The seas are yours... for now.").withStyle(ChatFormatting.GOLD));
		}
	}

	private static void give(ServerPlayer player, ItemStack stack) {
		if (!player.getInventory().add(stack)) {
			player.spawnAtLocation((ServerLevel) player.level(), stack);
		}
	}
}
