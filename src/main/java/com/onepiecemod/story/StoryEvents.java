package com.onepiecemod.story;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.levelgen.Heightmap;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.bounty.BountyFeature;
import com.onepiecemod.bounty.EventBosses;
import com.onepiecemod.bounty.NavyCalm;
import com.onepiecemod.bounty.MarineEntity;
import com.onepiecemod.bounty.MarineRank;
import com.onepiecemod.character.CharacterAttachments;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.character.Locations;
import com.onepiecemod.haki.HakiAttachments;
import com.onepiecemod.haki.HakiData;

/**
 * The story's set pieces, the parts a normal quest can't do:
 * - Sabaody: Kizaru attacks. Survive 2 minutes (or beat him) and Kuma sends you flying far across the sea.
 * - Marineford: hold out against 5 waves of Marines. Akainu joins the last one.
 * - Sky Island: sneak at Montblanc Cricket's house and the Knock Up Stream shoots you up to Skypiea.
 * - Amazon Lily: one extra chance to awaken Conqueror's Haki.
 * - The end: everyone on the server hears that a new Pirate King was crowned.
 *
 * Events only start in Survival or Adventure. If you die during one, it stops; go back to try again.
 */
public class StoryEvents {
	private static final int KIZARU_SECONDS = 120;
	private static final int WAVES = 5;
	private static final int WAVE_SECONDS = 60;
	private static final int LAUNCH_COOLDOWN_SECONDS = 60;

	/** Kizaru's attack on one player. */
	private static class Kizaru {
		UUID boss;
		int secondsLeft = KIZARU_SECONDS;
	}

	/** The Marineford siege of one player. */
	private static class Siege {
		BlockPos start;
		int wave = 0;
		int secondsLeft = 0;
		final List<UUID> marines = new ArrayList<>();
		UUID akainu;
	}

	private static final Map<UUID, Kizaru> kizaru = new HashMap<>();
	private static final Map<UUID, Siege> sieges = new HashMap<>();
	private static final Map<UUID, Integer> launchReadyAt = new HashMap<>();

	public static void initialize() {
		// No Marine hunts, Navy raids or bounty hunters on top of Kizaru or the Marineford siege.
		NavyCalm.register(player -> kizaru.containsKey(player.getUUID()) || sieges.containsKey(player.getUUID()));

		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 20 != 0) {
				return;
			}
			for (ServerPlayer player : server.getPlayerList().getPlayers()) {
				StoryProgress progress = StoryProgress.of(player);
				if (progress == null || !player.isAlive()) {
					continue;
				}
				tick(player, progress, server.getTickCount());
			}
		});

		// Dying ends whatever event you were in.
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (entity instanceof ServerPlayer player) {
				failKizaru(player);
				failSiege(player);
			}
		});
	}

	private static void tick(ServerPlayer player, StoryProgress progress, int now) {
		ServerLevel level = (ServerLevel) player.level();
		StoryData.Chapter chapter = StoryData.chapter(progress.chapter());
		String id = chapter == null ? "" : chapter.id;
		boolean canStart = !player.isCreative() && !player.isSpectator();

		// Sabaody: Kizaru.
		Kizaru attack = kizaru.get(player.getUUID());
		if (attack != null) {
			tickKizaru(player, attack);
		} else if ("sabaody".equals(id) && canStart && !progress.hasFlag("event:kizaru_escape")
				&& CharacterAttachments.has(player, CharacterAttachments.MET, "rayleigh")
				&& (StoryPlaces.isInside(level, player.blockPosition(), "sabaody_park")
				|| StoryPlaces.isInside(level, player.blockPosition(), "shakky_bar"))) {
			startKizaru(player);
		}

		// Marineford: the siege.
		Siege siege = sieges.get(player.getUUID());
		if (siege != null) {
			tickSiege(player, siege);
		} else if ("marineford".equals(id) && canStart && !progress.hasFlag("event:marineford_siege")
				&& StoryPlaces.isInside(level, player.blockPosition(), "marineford")) {
			startSiege(player);
		}

		// Sky Island: the Knock Up Stream, from that chapter on.
		if (progress.reached("sky_island") && player.isShiftKeyDown()
				&& now >= launchReadyAt.getOrDefault(player.getUUID(), 0)
				&& StoryPlaces.isInside(level, player.blockPosition(), "cricket_house")) {
			launchToSky(player);
			launchReadyAt.put(player.getUUID(), now + LAUNCH_COOLDOWN_SECONDS * 20);
		}
	}

	// ---- Sabaody: Kizaru ----

	private static void startKizaru(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		CharacterEntity boss = CharacterFeature.CHARACTER.create(level, EntitySpawnReason.EVENT);
		if (boss == null) {
			return;
		}
		BlockPos spot = spotNear(level, player, 10, 14);
		boss.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
		boss.setCharacter("kizaru", true);
		boss.setTarget(player);
		EventBosses.mark(boss);
		level.addFreshEntity(boss);

		Kizaru attack = new Kizaru();
		attack.boss = boss.getUUID();
		kizaru.put(player.getUUID(), attack);
		say(player, "Borsalino (Kizaru)", "Ooh, how scary... a pirate with a bounty, right here on Sabaody.");
		event(player, "An Admiral is here! Survive for 2 minutes, or beat him if you dare!");
		level.playSound(null, player.blockPosition(), SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 2.0f, 1.0f);
	}

	private static void tickKizaru(ServerPlayer player, Kizaru attack) {
		Entity boss = ((ServerLevel) player.level()).getEntity(attack.boss);
		attack.secondsLeft--;
		if (boss == null || !boss.isAlive() || attack.secondsLeft <= 0) {
			finishKizaru(player, boss);
		} else if (attack.secondsLeft % 30 == 0) {
			player.sendOverlayMessage(Component.literal("Hold on! " + attack.secondsLeft + " seconds...").withStyle(ChatFormatting.YELLOW));
		}
	}

	private static void finishKizaru(ServerPlayer player, Entity boss) {
		kizaru.remove(player.getUUID());
		if (boss != null && boss.isAlive()) {
			boss.discard();
		}
		setFlag(player, "event:kizaru_escape");
		say(player, "Bartholomew Kuma", "If you could take a trip... where would you go?");
		event(player, "Kuma's paw hits you, and you fly far, far across the sea...");

		// Like Luffy in the show, you come down near Amazon Lily, the next chapter. If there's none,
		// somewhere 2,500 to 4,000 blocks away. Either way, falling slowly from the sky. (The search for Amazon Lily
		// runs in the background, so a far one doesn't freeze the server.)
		if (!Locations.findLater(player, "amazon_lily", StoryEvents::kumaLanding)) {
			kumaLanding(player, Optional.empty());
		}
	}

	private static void kumaLanding(ServerPlayer player, Optional<Locations.Found> lily) {
		RandomSource random = player.getRandom();
		double angle = random.nextDouble() * Math.PI * 2;
		double x;
		double z;
		if (lily.isPresent()) {
			int distance = 20 + random.nextInt(41);
			x = lily.get().pos().getX() + 0.5 + Math.cos(angle) * distance;
			z = lily.get().pos().getZ() + 0.5 + Math.sin(angle) * distance;
		} else {
			int distance = 2500 + random.nextInt(1501);
			x = player.getX() + Math.cos(angle) * distance;
			z = player.getZ() + Math.sin(angle) * distance;
		}
		player.stopRiding();
		player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 20 * 160, 0));
		player.teleportTo(x, 250, z);
	}

	private static void failKizaru(ServerPlayer player) {
		Kizaru attack = kizaru.remove(player.getUUID());
		if (attack == null) {
			return;
		}
		Entity boss = ((ServerLevel) player.level()).getEntity(attack.boss);
		if (boss != null) {
			boss.discard();
		}
		event(player, "Kizaru got you. Go back to Sabaody to try again.");
	}

	// ---- Marineford: the siege ----

	private static void startSiege(ServerPlayer player) {
		Siege siege = new Siege();
		siege.start = player.blockPosition();
		sieges.put(player.getUUID(), siege);
		event(player, "The Marines have seen you! Hold the plaza against " + WAVES + " waves.");
		nextWave(player, siege);
	}

	private static void tickSiege(ServerPlayer player, Siege siege) {
		ServerLevel level = (ServerLevel) player.level();
		if (player.blockPosition().distSqr(siege.start) > 96 * 96) {
			failSiege(player);
			return;
		}
		siege.marines.removeIf(id -> {
			Entity marine = level.getEntity(id);
			return marine == null || !marine.isAlive();
		});
		siege.secondsLeft--;
		if (!siege.marines.isEmpty() && siege.secondsLeft > 0) {
			return;
		}
		if (siege.wave >= WAVES) {
			finishSiege(player, siege);
		} else {
			nextWave(player, siege);
		}
	}

	private static void nextWave(ServerPlayer player, Siege siege) {
		ServerLevel level = (ServerLevel) player.level();
		siege.wave++;
		siege.secondsLeft = WAVE_SECONDS;
		List<MarineRank> squad = switch (siege.wave) {
			case 1 -> List.of(MarineRank.RECRUIT, MarineRank.RECRUIT, MarineRank.RECRUIT, MarineRank.RECRUIT);
			case 2 -> List.of(MarineRank.RECRUIT, MarineRank.RECRUIT, MarineRank.RECRUIT, MarineRank.RIFLEMAN, MarineRank.RIFLEMAN);
			case 3 -> List.of(MarineRank.LIEUTENANT, MarineRank.RECRUIT, MarineRank.RECRUIT, MarineRank.RIFLEMAN, MarineRank.RIFLEMAN);
			case 4 -> List.of(MarineRank.CAPTAIN, MarineRank.LIEUTENANT, MarineRank.RIFLEMAN, MarineRank.RIFLEMAN, MarineRank.RIFLEMAN);
			default -> List.of(MarineRank.CAPTAIN, MarineRank.CAPTAIN, MarineRank.LIEUTENANT, MarineRank.LIEUTENANT, MarineRank.RIFLEMAN, MarineRank.RIFLEMAN);
		};
		for (MarineRank rank : squad) {
			MarineEntity marine = BountyFeature.MARINE.create(level, EntitySpawnReason.EVENT);
			if (marine == null) {
				continue;
			}
			BlockPos spot = spotNear(level, player, 12, 20);
			marine.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
			marine.setRank(rank);
			marine.setHunted(player);
			level.addFreshEntity(marine);
			siege.marines.add(marine.getUUID());
		}
		event(player, "Wave " + siege.wave + " of " + WAVES + "!");
		level.playSound(null, player.blockPosition(), SoundEvents.RAID_HORN.value(), SoundSource.HOSTILE, 2.0f, 1.2f);

		if (siege.wave == WAVES) {
			// Akainu comes for the last wave, unless he's already standing in his lair nearby.
			boolean here = !level.getEntitiesOfClass(CharacterEntity.class, player.getBoundingBox().inflate(64),
					character -> character.isBoss() && "akainu".equals(character.getCharacterId())).isEmpty();
			if (!here) {
				CharacterEntity akainu = CharacterFeature.CHARACTER.create(level, EntitySpawnReason.EVENT);
				if (akainu != null) {
					BlockPos spot = spotNear(level, player, 14, 20);
					akainu.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
					akainu.setCharacter("akainu", true);
					akainu.setTarget(player);
					EventBosses.mark(akainu);
					level.addFreshEntity(akainu);
					siege.akainu = akainu.getUUID();
				}
			}
			say(player, "Sakazuki (Akainu)", "Absolute justice! Not one pirate leaves this plaza alive!");
			siege.secondsLeft = WAVE_SECONDS + 30;
		}
	}

	private static void finishSiege(ServerPlayer player, Siege siege) {
		sieges.remove(player.getUUID());
		discardAkainu(player, siege);
		setFlag(player, "event:marineford_siege");
		event(player, "You held Marineford! The Marines sound the retreat, and you slip away in the smoke.");
	}

	private static void failSiege(ServerPlayer player) {
		Siege siege = sieges.remove(player.getUUID());
		if (siege == null) {
			return;
		}
		ServerLevel level = (ServerLevel) player.level();
		for (UUID id : siege.marines) {
			Entity marine = level.getEntity(id);
			if (marine != null) {
				marine.discard();
			}
		}
		discardAkainu(player, siege);
		event(player, "The siege broke you. Go back to Marineford to try again.");
	}

	private static void discardAkainu(ServerPlayer player, Siege siege) {
		if (siege.akainu != null) {
			Entity akainu = ((ServerLevel) player.level()).getEntity(siege.akainu);
			if (akainu != null && akainu.isAlive()) {
				akainu.discard();
			}
		}
	}

	// ---- Sky Island: the Knock Up Stream ----

	private static void launchToSky(ServerPlayer player) {
		// The searches run in the background, so a far one doesn't freeze the server.
		Locations.findLater(player, "shandora", (who, shandora) -> {
			if (shandora.isPresent() || !Locations.findLater(who, "angel_beach", StoryEvents::launchToSky)) {
				launchToSky(who, shandora);
			}
		});
	}

	private static void launchToSky(ServerPlayer player, Optional<Locations.Found> sky) {
		ServerLevel level = (ServerLevel) player.level();
		if (sky.isEmpty()) {
			event(player, "The sea rumbles... but there's no sky island above these waters.");
			return;
		}
		BlockPos target = sky.get().pos();
		say(player, "Montblanc Cricket", "Hold on tight! The Knock Up Stream is coming!");
		level.playSound(null, player.blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 2.0f, 0.6f);
		player.addEffect(new MobEffectInstance(MobEffects.SLOW_FALLING, 20 * 90, 0));
		player.teleportTo(target.getX() + 0.5, 215, target.getZ() + 0.5);
		event(player, "You burst through the clouds above " + Locations.name(sky.get().id()) + "! To get back down, just jump off the edge.");
	}

	// ---- Chapter hooks ----

	/** Called by StoryTracker when a chapter is done, for rewards that aren't items. */
	static void onChapterFinished(ServerPlayer player, StoryData.Chapter chapter) {
		if ("amazon_lily".equals(chapter.id)) {
			HakiData haki = HakiAttachments.get(player);
			if (haki.conqueror()) {
				return;
			}
			if (player.getRandom().nextInt(3) == 0) {
				HakiAttachments.set(player, haki.withConqueror(true));
				event(player, "Standing before the Empress, the will of a king awakens in you! You have Conqueror's Haki. Press G to release it.");
				player.level().playSound(null, player.blockPosition(), SoundEvents.ENDER_DRAGON_GROWL, SoundSource.PLAYERS, 1.0f, 0.6f);
			} else {
				event(player, "Hancock's presence is crushing, but no king's will stirs in you. Not yet. Beating a new boss might still wake it.");
			}
		}
	}

	/** Called when the main story is done (the Laugh Tale chapter). */
	static void onStoryFinished(ServerPlayer player) {
		if (StoryProgress.orStart(player).hasFlag("pirate_king")) {
			return;
		}
		setFlag(player, "pirate_king");
		Component news = Component.literal("News Coo: " + player.getName().getString()
				+ " reached Laugh Tale and found the One Piece!").withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD);
		for (ServerPlayer other : player.level().getServer().getPlayerList().getPlayers()) {
			other.sendSystemMessage(news);
		}
		player.sendSystemMessage(Component.literal("Thanks for playing the story! The post-game saga is next in your Captain's Log: the Red Line "
				+ "and the Void Century in the End. Mihawk, Whitebeard, the Admirals, Hard and Expert rematches, and the legendary Rocks D. Xebec at God Valley are waiting too.").withStyle(ChatFormatting.YELLOW));
	}

	// ---- Helpers ----

	public static void setFlag(ServerPlayer player, String flag) {
		StoryProgress.set(player, StoryProgress.orStart(player).withFlag(flag));
	}

	static void say(ServerPlayer player, String who, String text) {
		player.sendSystemMessage(Component.literal("<" + who + "> ").withStyle(ChatFormatting.GOLD)
				.append(Component.literal(text).withStyle(ChatFormatting.WHITE)));
	}

	static void event(ServerPlayer player, String text) {
		player.sendSystemMessage(Component.literal(text).withStyle(ChatFormatting.LIGHT_PURPLE));
	}

	/** A spot on the ground between min and max blocks from the player (or right next to them if none is found). */
	static BlockPos spotNear(ServerLevel level, LivingEntity player, int min, int max) {
		RandomSource random = player.getRandom();
		for (int attempt = 0; attempt < 12; attempt++) {
			double angle = random.nextDouble() * Math.PI * 2;
			int distance = min + random.nextInt(max - min + 1);
			int x = (int) Math.floor(player.getX() + Math.cos(angle) * distance);
			int z = (int) Math.floor(player.getZ() + Math.sin(angle) * distance);
			if (!level.hasChunkAt(new BlockPos(x, 0, z))) {
				continue;
			}
			BlockPos pos = new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z);
			if (Math.abs(pos.getY() - player.getY()) < 12 && level.getFluidState(pos.below()).isEmpty()) {
				return pos;
			}
		}
		return player.blockPosition();
	}
}
