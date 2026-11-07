package com.onepiecemod.shipcombat;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.bounty.Bounty;
import com.onepiecemod.bounty.BountyFeature;
import com.onepiecemod.bounty.MarineEntity;
import com.onepiecemod.bounty.MarineRank;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.crew.CrewMode;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.ship.ShipAssembler;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.sound.ModSounds;

/**
 * Boarding an enemy ship. Right-click it when you're alongside (or throw a Boarding Hook from further off):
 * the enemy ship drops anchor right there, becomes real blocks you can walk on, and its crew rushes you.
 * Beat the whole crew and the ship is yours: right-click her Ship's Wheel to set sail in her.
 * Crewmates following you (within 48 blocks) swing across with you and join the fight.
 */
public class Boarding {
	private static final int GIVE_UP_TICKS = 20 * 60 * 5;
	/** Enemy ships can only be boarded once their hull is below this share of full. */
	public static final float BOARD_BELOW = 0.5f;
	/** Crewmates following you within this many blocks board with you, at most PARTY_SIZE of them. */
	private static final double PARTY_RANGE = 48;
	private static final int PARTY_SIZE = 4;

	private record Fight(ServerLevel level, UUID player, List<UUID> crew, ShipBrain.Faction faction, int tier, Vec3 where, long started) {
	}

	private static final List<Fight> FIGHTS = new ArrayList<>();

	static InteractionResult board(ServerPlayer player, ShipEntity ship) {
		if (!(ship.level() instanceof ServerLevel level)) {
			return InteractionResult.PASS;
		}
		if (ship.sinking) {
			player.sendOverlayMessage(Component.literal("She's going down! Nothing left to board.").withStyle(ChatFormatting.YELLOW));
			return InteractionResult.FAIL;
		}
		// A ship in good shape fights off boarders: batter her with cannons first.
		float hull = ShipHull.get(ship);
		float max = ShipHull.max(ship);
		if (hull > max * BOARD_BELOW && !player.isCreative()) {
			player.sendOverlayMessage(Component.literal("Her hull is too strong to board (" + Math.round(100 * hull / max)
					+ "%). Cannon her below " + Math.round(BOARD_BELOW * 100) + "% first!").withStyle(ChatFormatting.YELLOW));
			return InteractionResult.FAIL;
		}
		ShipBrain.Faction faction = ShipBrain.factionOf(ship);
		int tier = ShipBrain.tierOf(ship);
		String name = ship.getName().getString();
		List<Vec3> deck = deckSpots(ship);

		// Drop the enemy's anchor: the ship turns back into blocks where it is.
		String problem = ShipAssembler.dock(level, ship);
		if (problem != null) {
			player.sendOverlayMessage(Component.literal("Can't board yet: she's up against something. Wait for open water.").withStyle(ChatFormatting.YELLOW));
			return InteractionResult.FAIL;
		}

		// Your crew (the ones following you) swing across with you.
		List<CrewmateEntity> party = boardingParty(level, player);

		// Land on her deck, by the wheel.
		player.stopRiding();
		Vec3 landing = deck.get(0);
		player.teleportTo(landing.x, landing.y, landing.z);
		player.resetFallDistance();
		level.playSound(null, player.blockPosition(), com.onepiecemod.sound.WorldSounds.BOARDING, SoundSource.PLAYERS, 1.5f, 1.0f);

		// Her crew comes at you from all over the deck.
		int crewSize = Math.min(deck.size() - 1, 3 + tier + level.getRandom().nextInt(2));
		List<UUID> crew = new ArrayList<>();
		for (int i = 0; i < crewSize; i++) {
			Vec3 spot = deck.get(deck.size() - 1 - i); // Furthest from the wheel first.
			Mob sailor = faction == ShipBrain.Faction.MARINE ? marine(level, player, i, tier) : pirate(level, i, tier);
			if (sailor == null) {
				continue;
			}
			sailor.snapTo(spot.x, spot.y, spot.z, level.getRandom().nextFloat() * 360f, 0);
			sailor.setTarget(player);
			level.addFreshEntity(sailor);
			crew.add(sailor.getUUID());
		}

		for (int i = 0; i < party.size(); i++) {
			CrewmateEntity mate = party.get(i);
			Vec3 spot = deck.get(Math.min(deck.size() - 1, 1 + i));
			mate.stopRiding();
			mate.teleportTo(spot.x, spot.y, spot.z);
			mate.resetFallDistance();
			mate.getNavigation().stop();
			if (!crew.isEmpty() && level.getEntity(crew.get(i % crew.size())) instanceof Mob sailor) {
				mate.setTarget(sailor);
			}
		}

		if (faction == ShipBrain.Faction.MARINE) {
			ModSounds.play(player, ModSounds.NAVY_BUGLE);
		}
		player.sendSystemMessage(Component.literal("You boarded the " + name + "! Defeat her crew to take her."
				+ (party.isEmpty() ? "" : " " + party.size() + (party.size() == 1 ? " crewmate is" : " crewmates are") + " right behind you!"))
				.withStyle(ChatFormatting.GOLD));
		FIGHTS.add(new Fight(level, player.getUUID(), crew, faction, tier, landing, level.getGameTime()));
		return InteractionResult.SUCCESS;
	}

	/** Up to PARTY_SIZE of the player's crewmates who are following them, close by and on their feet. */
	private static List<CrewmateEntity> boardingParty(ServerLevel level, ServerPlayer player) {
		List<CrewmateEntity> party = new ArrayList<>(level.getEntitiesOfClass(CrewmateEntity.class, player.getBoundingBox().inflate(PARTY_RANGE),
				mate -> mate.isAlive() && !mate.isKnockedOut() && mate.getMode() == CrewMode.FOLLOW && player.getUUID().equals(mate.getCaptainId())));
		party.sort(java.util.Comparator.comparingDouble(mate -> mate.distanceToSqr(player)));
		return party.size() > PARTY_SIZE ? party.subList(0, PARTY_SIZE) : party;
	}

	private static Mob marine(ServerLevel level, ServerPlayer player, int index, int tier) {
		MarineEntity marine = BountyFeature.MARINE.create(level, EntitySpawnReason.EVENT);
		if (marine == null) {
			return null;
		}
		MarineRank rank;
		if (index == 0) {
			rank = tier >= 3 ? MarineRank.CAPTAIN : MarineRank.LIEUTENANT;
		} else {
			rank = index % 2 == 0 ? MarineRank.RIFLEMAN : MarineRank.RECRUIT;
		}
		marine.setRank(rank);
		marine.setHunted(player);
		return marine;
	}

	private static Mob pirate(ServerLevel level, int index, int tier) {
		SeaPirateEntity pirate = ShipCombatFeature.SEA_PIRATE.create(level, EntitySpawnReason.EVENT);
		if (pirate == null) {
			return null;
		}
		pirate.setup(index == 0, tier, level.getRandom());
		return pirate;
	}

	/**
	 * Where people can stand on the ship once it has docked, captain's spot first. Docking turns the ship to the nearest
	 * quarter turn, so this works the spots out the same way ShipAssembler.dock places the blocks.
	 */
	private static List<Vec3> deckSpots(ShipEntity ship) {
		int quarterTurns = Math.floorMod(Math.round(Mth.wrapDegrees(ship.rotationSinceBuilt(1.0f)) / 90f), 4);
		Rotation rotation = switch (quarterTurns) {
			case 1 -> Rotation.CLOCKWISE_90;
			case 2 -> Rotation.CLOCKWISE_180;
			case 3 -> Rotation.COUNTERCLOCKWISE_90;
			default -> Rotation.NONE;
		};
		BlockPos anchor = BlockPos.containing(ship.getX(), Math.round(ship.getY()), ship.getZ());
		List<Vec3> spots = new ArrayList<>();
		for (Vec3 seat : ship.getLayout().seats) {
			BlockPos local = BlockPos.containing(seat.x, seat.y, seat.z).rotate(rotation);
			BlockPos world = anchor.offset(local);
			spots.add(new Vec3(world.getX() + 0.5, world.getY() + 0.05, world.getZ() + 0.5));
		}
		if (spots.isEmpty()) {
			spots.add(ship.position().add(0, ship.getLayout().waterline + 1, 0));
		}
		return spots;
	}

	/** Once a second: has anyone won a boarding fight? */
	static void tick(MinecraftServer server) {
		Iterator<Fight> it = FIGHTS.iterator();
		while (it.hasNext()) {
			Fight fight = it.next();
			ServerPlayer player = server.getPlayerList().getPlayer(fight.player());
			int alive = 0;
			for (UUID id : fight.crew()) {
				Entity sailor = fight.level().getEntity(id);
				if (sailor != null && sailor.isAlive()) {
					alive++;
				}
			}
			boolean playerHere = player != null && player.isAlive() && player.level() == fight.level()
					&& player.position().distanceToSqr(fight.where()) < 128 * 128;
			if (alive == 0 && playerHere) {
				win(player, fight);
				it.remove();
			} else if (!playerHere || fight.level().getGameTime() - fight.started() > GIVE_UP_TICKS) {
				it.remove(); // You left (or the fight dragged on). The crew stays aboard.
			}
		}
	}

	private static void win(ServerPlayer player, Fight fight) {
		com.onepiecemod.advancement.AdvancementFeature.grant(player, "journey/capture_ship");
		player.sendSystemMessage(Component.literal("The ship is yours! Right-click her Ship's Wheel to set sail, and check the hold for treasure.")
				.withStyle(ChatFormatting.GOLD));
		fight.level().playSound(null, player.blockPosition(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 1.0f, 1.0f);
		ItemStack berries = new ItemStack(CharacterFeature.BERRY, 8 + fight.tier() * 4);
		if (!player.getInventory().add(berries)) {
			player.spawnAtLocation(fight.level(), berries);
		}
		if (fight.faction() == ShipBrain.Faction.MARINE) {
			Bounty.raise(player, 12_000_000L * (fight.tier() + 1), "You captured a Marine warship!", false);
		}
	}
}
