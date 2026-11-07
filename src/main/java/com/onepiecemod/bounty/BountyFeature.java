package com.onepiecemod.bounty;

import java.util.HashSet;
import java.util.Set;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.Item;

import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterEntity;

/**
 * Sets up bounties: every player has a bounty that rises when they beat bosses and Marines,
 * and the Marines hunt (and raid) them harder as it grows. OnePieceMod calls initialize() once while the game loads.
 */
public class BountyFeature {
	public static final ResourceKey<EntityType<?>> MARINE_KEY = ResourceKey.create(Registries.ENTITY_TYPE, OnePieceMod.id("marine"));
	public static final EntityType<MarineEntity> MARINE = Registry.register(
			BuiltInRegistries.ENTITY_TYPE,
			MARINE_KEY,
			EntityType.Builder.of(MarineEntity::new, MobCategory.MONSTER)
					.sized(0.6f, 1.95f) // Same size as a player.
					.clientTrackingRange(10)
					.build(MARINE_KEY)
	);

	public static final ResourceKey<EntityType<?>> BOUNTY_HUNTER_KEY = ResourceKey.create(Registries.ENTITY_TYPE, OnePieceMod.id("bounty_hunter"));
	public static final EntityType<BountyHunterEntity> BOUNTY_HUNTER = Registry.register(
			BuiltInRegistries.ENTITY_TYPE,
			BOUNTY_HUNTER_KEY,
			EntityType.Builder.of(BountyHunterEntity::new, MobCategory.MONSTER)
					.sized(0.6f, 1.95f)
					.clientTrackingRange(10)
					.build(BOUNTY_HUNTER_KEY)
	);

	public static final ResourceKey<Item> BOUNTY_POSTER_KEY = ResourceKey.create(Registries.ITEM, OnePieceMod.id("bounty_poster"));
	public static final Item BOUNTY_POSTER = Registry.register(BuiltInRegistries.ITEM, BOUNTY_POSTER_KEY,
			new BountyPosterItem(new Item.Properties().stacksTo(16).setId(BOUNTY_POSTER_KEY)));

	/** How close you must be to a boss when it dies to share the bounty, so friends can team up. */
	private static final double CREDIT_RANGE = 32.0;

	public static void initialize() {
		Bounty.initialize();
		FabricDefaultAttributeRegistry.register(MARINE, MarineEntity.createAttributes());
		FabricDefaultAttributeRegistry.register(BOUNTY_HUNTER, BountyHunterEntity.createAttributes());
		EventBosses.initialize();
		BountyCommands.initialize();
		MarineHunters.initialize();
		NavyRaids.initialize();
		BountyHunters.initialize();

		// Something died. If it was a boss or a Marine, raise the bounty of whoever beat it.
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (!(entity.level() instanceof ServerLevel level)) {
				return;
			}
			if (entity instanceof CharacterEntity boss && boss.isBoss()) {
				for (ServerPlayer player : creditedPlayers(level, entity, source.getEntity())) {
					String id = boss.getCharacterId();
					boolean firstTime = Bounty.countBoss(player, id);
					long reward = firstTime ? Bounty.bossReward(id) : Bounty.repeatReward(id);
					Bounty.raise(player, reward, "The Marines heard you beat " + boss.getData().name + ".", firstTime);
				}
			} else if (entity instanceof BountyHunterEntity hunter && source.getEntity() instanceof ServerPlayer player) {
				Bounty.raise(player, hunter.bountyReward(), "You beat a bounty hunter with the " + hunter.getFruit().name() + ".", false);
			} else if (entity instanceof MarineEntity marine && source.getEntity() instanceof ServerPlayer player) {
				Bounty.raise(player, marine.bountyReward(), "You beat " + marine.title() + ".", false);
			}
		});
	}

	/** The player who landed the last hit, plus every other player close by. */
	private static Set<ServerPlayer> creditedPlayers(ServerLevel level, Entity boss, Entity killer) {
		Set<ServerPlayer> players = new HashSet<>();
		if (killer instanceof ServerPlayer player) {
			players.add(player);
		}
		for (ServerPlayer player : level.players()) {
			if (player.isAlive() && !player.isSpectator() && player.distanceToSqr(boss) < CREDIT_RANGE * CREDIT_RANGE) {
				players.add(player);
			}
		}
		return players;
	}
}
