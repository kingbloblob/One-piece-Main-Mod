package com.onepiecemod.character;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import io.netty.buffer.ByteBuf;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;

/**
 * The quest steps that happen out in the world, plus the "!" and "?" over quest givers' heads.
 *
 * - explore: reach the location in "target". Checked every 2 seconds.
 * - escort:  the character in "target" follows you until you both reach the location in "place".
 *            Friendly characters can't be hurt, so the escort is about getting them there, not keeping them alive.
 *            If they get lost (you log out, or sail off), they show up next to you again.
 * - quest markers: every second each player is told which nearby quest givers have a job for them ("!"),
 *   are waiting on one ("?" grey) or are ready for a hand-in ("?" gold). CharacterRenderer draws them.
 */
public class QuestJourneys {
	/** Scoreboard tag on escort characters, so they can be found again after a restart. */
	private static final String ESCORT_TAG = "onepiece_escort_";
	/** Player -> the escort following them right now. */
	private static final Map<UUID, Entity> ESCORTS = new HashMap<>();

	public static final int MARKER_NEW = 1;
	public static final int MARKER_WAITING = 2;
	public static final int MARKER_READY = 3;

	/** Server -> one player: marker kinds for nearby quest givers (entity ids and MARKER_ values, same order). */
	public record Markers(List<Integer> ids, List<Integer> kinds) implements CustomPacketPayload {
		public static final Type<Markers> TYPE = new Type<>(OnePieceMod.id("quest_markers"));
		public static final StreamCodec<ByteBuf, Markers> CODEC = StreamCodec.composite(
				ByteBufCodecs.VAR_INT.apply(ByteBufCodecs.list(512)), Markers::ids,
				ByteBufCodecs.VAR_INT.apply(ByteBufCodecs.list(512)), Markers::kinds,
				Markers::new);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	public static void initialize() {
		PayloadTypeRegistry.clientboundPlay().register(Markers.TYPE, Markers.CODEC);
		ServerLifecycleEvents.SERVER_STOPPED.register(QuestJourneys::clear);
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			int tick = server.getTickCount();
			if (tick % 20 == 0) {
				for (ServerPlayer player : server.getPlayerList().getPlayers()) {
					sendMarkers(player);
					updateEscort(player);
				}
			}
			if (tick % 40 == 10) {
				for (ServerPlayer player : server.getPlayerList().getPlayers()) {
					checkExplore(player);
				}
			}
		});
	}

	// ---- Escort ----

	/** Spawns the escort next to the player (or reuses the one already following them). */
	public static void startEscort(ServerPlayer player, CharacterData.Quest quest) {
		Entity old = ESCORTS.remove(player.getUUID());
		if (old != null && old.isAlive()) {
			old.discard();
		}
		spawnEscort(player, quest);
	}

	private static Entity spawnEscort(ServerPlayer player, CharacterData.Quest quest) {
		ServerLevel level = player.level();
		CharacterEntity escort = CharacterFeature.CHARACTER.create(level, EntitySpawnReason.TRIGGERED);
		if (escort == null) {
			return null;
		}
		Vec3 spot = player.position().add(player.getLookAngle().multiply(2, 0, 2));
		BlockPos ground = level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, BlockPos.containing(spot));
		escort.setPos(ground.getX() + 0.5, Math.max(ground.getY(), player.getY()), ground.getZ() + 0.5);
		escort.setCharacter(quest.target, false);
		escort.addTag(ESCORT_TAG + player.getUUID());
		level.addFreshEntity(escort);
		ESCORTS.put(player.getUUID(), escort);
		return escort;
	}

	/** The escort step this player is on right now, or null. */
	private static CharacterData.Quest activeStep(ServerPlayer player, String type) {
		for (CharacterData giver : CharacterData.all().values()) {
			int step = QuestHandler.currentStep(player, giver);
			if (step < giver.quests.size()) {
				CharacterData.Quest quest = giver.quests.get(step);
				if (type.equals(quest.type) && QuestHandler.isStarted(player, giver, step) && !QuestHandler.isComplete(player, quest)) {
					return quest;
				}
			}
		}
		return null;
	}

	private static void updateEscort(ServerPlayer player) {
		CharacterData.Quest quest = activeStep(player, "escort");
		Entity escort = ESCORTS.get(player.getUUID());
		if (quest == null) {
			// Step finished or abandoned: the escort heads home.
			if (escort != null) {
				escort.discard();
				ESCORTS.remove(player.getUUID());
			}
			return;
		}
		if (escort == null || !escort.isAlive()) {
			escort = findTagged(player);
			if (escort == null) {
				escort = spawnEscort(player, quest);
				if (escort == null) {
					return;
				}
				player.sendSystemMessage(Component.literal(CharacterData.get(quest.target).name + " catches up with you.")
						.withStyle(ChatFormatting.GRAY));
			}
			ESCORTS.put(player.getUUID(), escort);
		}

		// Arrived?
		if (quest.place != null && at(player, quest.place) && escort.distanceTo(player) < 16) {
			QuestHandler.markProgress(player, quest);
			CharacterData who = CharacterData.get(quest.target);
			player.sendSystemMessage(Component.literal("<" + who.name + "> ").withStyle(ChatFormatting.GOLD)
					.append(Component.literal("We made it! Thank you. Go tell them I'm safe.").withStyle(ChatFormatting.WHITE)));
			player.level().playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.7f, 1.3f);
			escort.discard();
			ESCORTS.remove(player.getUUID());
			return;
		}

		// Follow: walk when close, catch up by teleporting when far or in another world.
		if (escort.level() != player.level() || escort.distanceTo(player) > 24) {
			escort.discard();
			ESCORTS.put(player.getUUID(), spawnEscort(player, quest));
		} else if (escort.distanceTo(player) > 4 && escort instanceof CharacterEntity mob) {
			mob.getNavigation().moveTo(player, 1.1);
		}
	}

	private static Entity findTagged(ServerPlayer player) {
		String tag = ESCORT_TAG + player.getUUID();
		List<CharacterEntity> found = player.level().getEntitiesOfClass(CharacterEntity.class,
				player.getBoundingBox().inflate(48), entity -> entity.entityTags().contains(tag));
		for (int i = 1; i < found.size(); i++) {
			found.get(i).discard(); // Never two.
		}
		return found.isEmpty() ? null : found.get(0);
	}

	// ---- Explore ----

	private static void checkExplore(ServerPlayer player) {
		CharacterData.Quest quest = activeStep(player, "explore");
		if (quest != null && at(player, quest.target)) {
			QuestHandler.markProgress(player, quest);
			player.sendSystemMessage(Component.literal("You found " + Locations.name(quest.target) + "! Go back and tell them what you saw.")
					.withStyle(ChatFormatting.GOLD));
			player.level().playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, 0.7f, 1.3f);
		}
	}

	/** True when the player is inside (or right on top of) the given location, like "ohara_library". */
	public static boolean at(ServerPlayer player, String locationId) {
		ServerLevel level = player.level();
		Optional<Holder.Reference<Structure>> structure = level.registryAccess().lookupOrThrow(Registries.STRUCTURE)
				.get(ResourceKey.create(Registries.STRUCTURE, OnePieceMod.id(locationId)));
		if (structure.isEmpty()) {
			return false;
		}
		BlockPos pos = player.blockPosition();
		for (int dy : new int[] {0, -10, 10}) {
			StructureStart start = level.structureManager().getStructureAt(pos.offset(0, dy, 0), structure.get().value());
			if (start.isValid()) {
				return true;
			}
		}
		return false;
	}

	// ---- Quest markers ----

	private static void sendMarkers(ServerPlayer player) {
		if (!ServerPlayNetworking.canSend(player, Markers.TYPE)) {
			return;
		}
		List<Integer> ids = new ArrayList<>();
		List<Integer> kinds = new ArrayList<>();
		for (CharacterEntity character : player.level().getEntitiesOfClass(CharacterEntity.class, player.getBoundingBox().inflate(48),
				entity -> !entity.isBoss())) {
			CharacterData data = character.getData();
			if (data == null || data.quests.isEmpty() || ids.size() >= 512) {
				continue;
			}
			int step = QuestHandler.currentStep(player, data);
			if (step >= data.quests.size()) {
				continue;
			}
			int kind;
			if (!QuestHandler.isStarted(player, data, step)) {
				kind = MARKER_NEW;
			} else {
				kind = QuestHandler.isComplete(player, data.quests.get(step)) ? MARKER_READY : MARKER_WAITING;
			}
			ids.add(character.getId());
			kinds.add(kind);
		}
		ServerPlayNetworking.send(player, new Markers(ids, kinds));
	}

	/** Forgets escorts when the server stops (they are found again by their tag). */
	public static void clear(MinecraftServer server) {
		ESCORTS.clear();
	}
}
