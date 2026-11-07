package com.onepiecemod.bounty;

import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

import net.minecraft.world.entity.Entity;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;

/**
 * Bosses that only exist for one event: Kizaru at Sabaody, Akainu at Marineford, a famous Marine leading a hunt
 * or a raid. Boss characters never despawn, so without this one left behind by quitting the world mid-event
 * would stay in the world for good. The list of live ones is only in memory: anything marked that loads
 * after a restart (or after its event let go of it) is removed.
 */
public final class EventBosses {
	public static final String TAG = "onepiece_event_boss";
	private static final Set<UUID> LIVE = ConcurrentHashMap.newKeySet();
	/** Live ones nothing keeps track of: they also go once their chunk unloads (everyone walked away). */
	private static final Set<UUID> UNTIL_UNLOADED = ConcurrentHashMap.newKeySet();

	private EventBosses() {
	}

	/** Call before adding the boss to the world. */
	public static void mark(Entity boss) {
		boss.addTag(TAG);
		LIVE.add(boss.getUUID());
	}

	/** For a boss no event keeps track of: like {@link #mark}, and it also leaves once nobody is near it any more. */
	public static void markUntilUnloaded(Entity boss) {
		mark(boss);
		UNTIL_UNLOADED.add(boss.getUUID());
	}

	/** The event is done with this boss: if it ever loads again, it is removed. */
	public static void forget(UUID boss) {
		LIVE.remove(boss);
		UNTIL_UNLOADED.remove(boss);
	}

	public static void initialize() {
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity.entityTags().contains(TAG) && !LIVE.contains(entity.getUUID())) {
				entity.discard();
			}
		});
		ServerEntityEvents.ENTITY_UNLOAD.register((entity, level) -> {
			if (UNTIL_UNLOADED.contains(entity.getUUID())) {
				forget(entity.getUUID());
			}
		});
	}
}
