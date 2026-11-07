package com.onepiecemod.crew;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.monster.Enemy;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;

import com.onepiecemod.character.CharacterEntity;

/**
 * Sets up the pirate crew feature: create a crew, hire one crewmate per role, and get their perks.
 * OnePieceMod calls initialize() once while the game loads.
 */
public class CrewFeature {
	public static void initialize() {
		CrewAttachments.initialize();
		CrewEntities.initialize();
		CrewBlocks.initialize();
		CrewTavern.initialize();
		CrewCommands.initialize();
		CrewPerks.initialize();
		CrewRoster.initialize();
		CrewPayloads.initialize();

		// No friendly fire: captains and crewmates can't hurt anyone in their own crew,
		// including stray arrows from the sniper.
		ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) ->
				source.getEntity() == entity || !CrewmateEntity.sameCrew(entity, source.getEntity()));

		// Crewmates who run out of health are knocked out for a while instead of dying (see CrewmateEntity.tryKnockOut).
		ServerLivingEntityEvents.ALLOW_DEATH.register((entity, source, amount) ->
				!(entity instanceof CrewmateEntity crewmate) || !crewmate.tryKnockOut(source));

		// Crewmates earn XP for defeating enemies. Crewmates who were fighting it when someone else
		// (like the captain) landed the last hit get half.
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			boolean enemy = entity instanceof Enemy
					|| (entity instanceof CharacterEntity character && character.isBoss());
			if (!enemy || !(entity.level() instanceof ServerLevel level)) {
				return;
			}
			int xp = CrewLevels.xpForKill(entity);
			CrewmateEntity killer = source.getEntity() instanceof CrewmateEntity crewmate ? crewmate : null;
			if (killer != null) {
				killer.addXp(xp);
			}
			for (CrewmateEntity helper : level.getEntitiesOfClass(CrewmateEntity.class, entity.getBoundingBox().inflate(24.0),
					crewmate -> crewmate != killer && crewmate.getTarget() == entity)) {
				helper.addXp(xp / 2);
			}
		});
	}
}
