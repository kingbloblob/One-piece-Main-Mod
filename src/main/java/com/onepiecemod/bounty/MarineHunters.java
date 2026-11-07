package com.onepiecemod.bounty;

import com.onepiecemod.sound.ModSounds;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.Difficulty;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.CharacterFeature;

/**
 * Sends Marines after players with a bounty. The higher your bounty, the more often they come,
 * the bigger the squad, and the tougher its leader. At high bounties a famous Marine may lead the hunt.
 *
 * Every 20 seconds each wanted player in the Overworld (survival or adventure, not Peaceful) rolls a chance.
 * After a squad arrives there is a 2 minute break before the next one.
 */
public class MarineHunters {
	private static final int CHECK_EVERY_TICKS = 20 * 20;
	private static final int BREAK_TICKS = 20 * 120;

	/** Chance per check at threat level 0..5. Level 1 is about one squad every 3 minutes. */
	private static final float[] CHANCE = {0f, 0.10f, 0.15f, 0.20f, 0.25f, 0.33f};

	/** Famous Marines who might lead the hunt, from threat level 3, 4 and 5. Ids from characters.json. */
	private static final String[][] FAMOUS_HUNTERS = {
			{}, {}, {},
			{"smoker"},
			{"smoker", "lucci"},
			{"kizaru", "akainu", "fujitora", "ryokugyu"}
	};
	private static final float FAMOUS_CHANCE = 0.2f;
	/** Tag put on famous Marines sent by the spawner, so they leave if the pirate gets away. */
	public static final String HUNTER_TAG = "onepiece_bounty_hunter";

	private static final Map<UUID, Integer> nextHuntTick = new HashMap<>();
	/** Which famous Marine is chasing which player right now, so only one comes at a time. */
	private static final Map<UUID, UUID> famousHunter = new HashMap<>();

	/** Lets /bounty hunt test a squad without waiting. */
	public static boolean forceHunt(ServerPlayer player) {
		return sendSquad(player);
	}

	public static void initialize() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % CHECK_EVERY_TICKS != 0) {
				return;
			}
			int now = server.getTickCount();
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				int level = Bounty.threatLevel(player);
				if (level == 0 || !canBeHunted(player) || !NavyCalm.canStart(player)) {
					continue;
				}
				if (now < nextHuntTick.getOrDefault(player.getUUID(), 0)) {
					continue;
				}
				if (player.getRandom().nextFloat() < CHANCE[level] * com.onepiecemod.empire.EmpireRanks.navyChance(player) * com.onepiecemod.config.ModConfig.marineHuntRate()
						&& sendSquad(player)) {
					// Emperors and up get shorter breaks between hunts.
					nextHuntTick.put(player.getUUID(), now + com.onepiecemod.empire.EmpireRanks.navyBreak(player, BREAK_TICKS));
				}
			}
			sendFamousHuntersHome(server.getPlayerList().getPlayers());
		});
	}

	static boolean canBeHunted(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		return level.dimension() == Level.OVERWORLD
				&& level.getDifficulty() != Difficulty.PEACEFUL
				&& !player.isCreative() && !player.isSpectator()
				&& storyBossesBeaten(player) >= com.onepiecemod.config.ModConfig.safeUntilBosses();
	}

	/** Different story bosses beaten (Hard and Expert wins of the same boss count once). For the "Navy waits for" setting. */
	static int storyBossesBeaten(ServerPlayer player) {
		int count = 0;
		for (String id : player.getAttachedOrElse(com.onepiecemod.character.CharacterAttachments.BOSSES_DEFEATED, List.<String>of())) {
			if (id.indexOf(':') < 0) {
				count++;
			}
		}
		return count;
	}

	/** Which ranks come at each threat level. The first one is the leader. */
	private static List<MarineRank> squadFor(int level) {
		List<MarineRank> squad = new ArrayList<>();
		switch (level) {
			case 1 -> squad.addAll(List.of(MarineRank.RECRUIT, MarineRank.RECRUIT));
			case 2 -> squad.addAll(List.of(MarineRank.RECRUIT, MarineRank.RIFLEMAN, MarineRank.RECRUIT));
			case 3 -> squad.addAll(List.of(MarineRank.LIEUTENANT, MarineRank.RECRUIT, MarineRank.RIFLEMAN, MarineRank.RECRUIT));
			case 4 -> squad.addAll(List.of(MarineRank.CAPTAIN, MarineRank.LIEUTENANT, MarineRank.RIFLEMAN, MarineRank.RIFLEMAN, MarineRank.RECRUIT));
			default -> squad.addAll(List.of(MarineRank.CAPTAIN, MarineRank.CAPTAIN, MarineRank.LIEUTENANT,
					MarineRank.RIFLEMAN, MarineRank.RIFLEMAN, MarineRank.RECRUIT));
		}
		return squad;
	}

	private static boolean sendSquad(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		int threat = Math.max(1, Bounty.threatLevel(player));

		// Don't pile up squads: if one is still around, wait.
		List<MarineEntity> alreadyHere = level.getEntitiesOfClass(MarineEntity.class, player.getBoundingBox().inflate(96.0),
				marine -> MarineEntity.isHunting(marine, player));
		if (!alreadyHere.isEmpty()) {
			return false;
		}

		BlockPos spot = findSpot(level, player);
		if (spot == null) {
			return false;
		}

		int spawned = 0;
		for (MarineRank rank : squadFor(threat)) {
			MarineEntity marine = BountyFeature.MARINE.create(level, EntitySpawnReason.EVENT);
			if (marine == null) {
				continue;
			}
			// Spread the squad out a little around the landing spot.
			BlockPos pos = surface(level, spot.getX() + player.getRandom().nextInt(5) - 2, spot.getZ() + player.getRandom().nextInt(5) - 2);
			marine.setPos(pos.getX() + 0.5, pos.getY(), pos.getZ() + 0.5);
			marine.setRank(rank);
			marine.setHunted(player);
			level.addFreshEntity(marine);
			spawned++;
		}
		if (spawned == 0) {
			return false;
		}

		String leader = maybeSendFamousHunter(level, player, spot, threat);
		player.sendSystemMessage(Component.literal(leader != null
				? leader + " and a Marine squad are after your " + Bounty.format(Bounty.get(player)) + " bounty!"
				: "Marines spotted! They're after your " + Bounty.format(Bounty.get(player)) + " bounty!")
				.withStyle(ChatFormatting.DARK_AQUA));
		level.playSound(null, player.blockPosition(), ModSounds.NAVY_BUGLE, SoundSource.HOSTILE, 2.0f, 1.0f);
		return true;
	}

	/** Returns the famous Marine's name if one joined the hunt. */
	private static String maybeSendFamousHunter(ServerLevel level, ServerPlayer player, BlockPos spot, int threat) {
		String[] choices = FAMOUS_HUNTERS[threat];
		if (choices.length == 0 || player.getRandom().nextFloat() >= FAMOUS_CHANCE) {
			return null;
		}
		UUID current = famousHunter.get(player.getUUID());
		if (current != null) {
			Entity existing = level.getEntity(current);
			if (existing != null && existing.isAlive()) {
				return null; // One famous Marine at a time.
			}
		}

		CharacterEntity hunter = CharacterFeature.CHARACTER.create(level, EntitySpawnReason.EVENT);
		if (hunter == null) {
			return null;
		}
		String id = choices[player.getRandom().nextInt(choices.length)];
		hunter.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
		hunter.setCharacter(id, true); // The normal boss version, with its boss bar and special attack.
		hunter.addTag(HUNTER_TAG);
		EventBosses.mark(hunter);
		hunter.setTarget(player);
		level.addFreshEntity(hunter);
		famousHunter.put(player.getUUID(), hunter.getUUID());
		return hunter.getData().name;
	}

	/**
	 * Boss characters never despawn, so a famous Marine sent by the spawner leaves
	 * once no player is within 128 blocks. Bosses you place with a Wanted Poster are not touched.
	 */
	private static void sendFamousHuntersHome(List<ServerPlayer> players) {
		for (ServerPlayer player : players) {
			UUID id = famousHunter.get(player.getUUID());
			if (id == null) {
				continue;
			}
			Entity hunter = ((ServerLevel) player.level()).getEntity(id);
			if (hunter == null || !hunter.isAlive()) {
				famousHunter.remove(player.getUUID());
				EventBosses.forget(id); // Not loaded any more: if it loads again later, it's gone.
			} else if (hunter.distanceToSqr(player) > 128.0 * 128.0) {
				hunter.discard();
				famousHunter.remove(player.getUUID());
				player.sendSystemMessage(Component.literal("You lost the Marines. For now.").withStyle(ChatFormatting.GRAY));
			}
		}
	}

	/** A dry, open spot on the ground 20 to 32 blocks from the player, or null if none was found. */
	private static BlockPos findSpot(ServerLevel level, ServerPlayer player) {
		RandomSource random = player.getRandom();
		for (int attempt = 0; attempt < 12; attempt++) {
			double angle = random.nextDouble() * Math.PI * 2;
			int distance = 20 + random.nextInt(13);
			int x = (int) Math.floor(player.getX() + Math.cos(angle) * distance);
			int z = (int) Math.floor(player.getZ() + Math.sin(angle) * distance);
			if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
				continue;
			}
			BlockPos pos = surface(level, x, z);
			boolean dryGround = level.getFluidState(pos).isEmpty() && level.getFluidState(pos.below()).isEmpty()
					&& level.getBlockState(pos.below()).isSolid();
			if (dryGround && Math.abs(pos.getY() - player.getY()) < 16) {
				return pos;
			}
		}
		return null;
	}

	private static BlockPos surface(ServerLevel level, int x, int z) {
		return new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z);
	}
}
