package com.onepiecemod.shipcombat;

import java.util.function.Function;

import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.state.BlockState;

import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.event.Event;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.ship.ShipEntity;
import com.onepiecemod.ship.ShipFeature;
import com.onepiecemod.weapon.WeaponItems;

/**
 * Ship combat at sea: cannons that fire, ship hulls that break and sink, boarding,
 * and Marine and pirate ships that sail around, hunt you and fight each other.
 *
 * The pieces:
 *  - Cannons: press M aboard a ship to fire a broadside from the Cannon blocks on the side you look at.
 *  - ShipHull: every ship has hull points. Cannonballs knock blocks off; at zero the ship sinks.
 *  - Boarding: right-click an enemy ship (or use a Boarding Hook) to jump aboard and fight its crew.
 *  - ShipBrain: steers and fires for Marine and pirate ships.
 *  - SeaEncounters: sends those ships at players who are out sailing.
 * OnePieceMod calls initialize() once while the game loads.
 */
public class ShipCombatFeature {
	// ---- Items ----

	/** The weapons feature's cannonball (also Hand Cannon ammo), made at the Shipwright's Bench. */
	public static final Item CANNONBALL = WeaponItems.CANNONBALL;
	public static final Item BOARDING_HOOK = registerItem("boarding_hook", BoardingHookItem::new, new Item.Properties().durability(48));

	// Special cannon ammo: hold it in your hand when you fire (C) and every cannon loads it instead of cannonballs.
	public static final Item CHAIN_SHOT = registerItem("chain_shot", Item::new, new Item.Properties());
	public static final Item FIRE_SHOT = registerItem("fire_shot", Item::new, new Item.Properties());
	public static final Item GRAPESHOT = registerItem("grapeshot", Item::new, new Item.Properties());

	// Ship upgrade kits, fitted at a Galley-La Shipyard (see ShipyardUpgrades).
	public static final Item HULL_PLATING = registerItem("hull_plating", Item::new, new Item.Properties().stacksTo(16));
	public static final Item REINFORCED_SAILCLOTH = registerItem("reinforced_sailcloth", Item::new, new Item.Properties().stacksTo(16));
	public static final Item HEAVY_GUN_CARRIAGE = registerItem("heavy_gun_carriage", Item::new, new Item.Properties().stacksTo(16));

	// ---- Entities ----

	public static final ResourceKey<EntityType<?>> CANNONBALL_KEY = ResourceKey.create(Registries.ENTITY_TYPE, OnePieceMod.id("cannonball"));
	public static final EntityType<CannonballEntity> CANNONBALL_ENTITY = Registry.register(
			BuiltInRegistries.ENTITY_TYPE,
			CANNONBALL_KEY,
			EntityType.Builder.<CannonballEntity>of(CannonballEntity::new, MobCategory.MISC)
					.sized(0.5f, 0.5f)
					.clientTrackingRange(8)
					.updateInterval(2)
					.build(CANNONBALL_KEY)
	);

	public static final ResourceKey<EntityType<?>> SEA_PIRATE_KEY = ResourceKey.create(Registries.ENTITY_TYPE, OnePieceMod.id("sea_pirate"));
	public static final EntityType<SeaPirateEntity> SEA_PIRATE = Registry.register(
			BuiltInRegistries.ENTITY_TYPE,
			SEA_PIRATE_KEY,
			EntityType.Builder.<SeaPirateEntity>of(SeaPirateEntity::new, MobCategory.MONSTER)
					.sized(0.6f, 1.95f)
					.clientTrackingRange(8)
					.build(SEA_PIRATE_KEY)
	);

	/** Runs before the crew-ship check in multiplayer.SharedShips, so enemy ships are boarded, not claimed. */
	private static final Identifier EARLY = OnePieceMod.id("ship_combat");

	public static void initialize() {
		// A fleet battle is enough on its own: no Navy raid or bounty squad on top of it.
		com.onepiecemod.bounty.NavyCalm.register(NavalBattles::inBattle);
		ShipHull.initialize(); // Registers the hull attachments now, before any world loads ships that carry them.
		FabricDefaultAttributeRegistry.register(SEA_PIRATE, SeaPirateEntity.createAttributes());

		PayloadTypeRegistry.serverboundPlay().register(FireCannonsPayload.TYPE, FireCannonsPayload.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(FireCannonsPayload.TYPE, (payload, context) -> Cannons.fireFromKey(context.player()));
		PayloadTypeRegistry.clientboundPlay().register(CannonReloadPayload.TYPE, CannonReloadPayload.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(ShipSpecialPayload.TYPE, ShipSpecialPayload.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(ShipSpecialPayload.TYPE, (payload, context) -> ShipSpecials.use(context.player(), payload.gaon()));

		// Right-clicking a ship: board enemy ships, or patch your own hull with planks.
		UseEntityCallback.EVENT.addPhaseOrdering(EARLY, OnePieceMod.id("shared_ships"));
		UseEntityCallback.EVENT.addPhaseOrdering(EARLY, Event.DEFAULT_PHASE);
		UseEntityCallback.EVENT.register(EARLY, (player, level, hand, entity, hitResult) -> {
			if (hand != InteractionHand.MAIN_HAND || !(entity instanceof ShipEntity ship) || level.isClientSide()) {
				return InteractionResult.PASS;
			}
			return ShipCombat.onRightClickShip(ship, (net.minecraft.server.level.ServerPlayer) player);
		});

		// Right-clicking a Cannon block (or an add-on's cannon, see CannonAddons) on land with a cannonball fires it.
		UseBlockCallback.EVENT.register((player, level, hand, hitResult) -> {
			BlockState state = level.getBlockState(hitResult.getBlockPos());
			if (!CannonAddons.isCannon(state) || !CannonAddons.isAmmo(player.getItemInHand(hand))) {
				return InteractionResult.PASS;
			}
			if (!level.isClientSide()) {
				Cannons.fireLandCannon((net.minecraft.server.level.ServerPlayer) player, hand, hitResult.getBlockPos(), state);
			}
			return InteractionResult.SUCCESS;
		});

		CreativeModeTabEvents.modifyOutputEvent(ShipFeature.TAB_KEY).register(output -> {
			output.accept(BOARDING_HOOK);
			output.accept(CHAIN_SHOT);
			output.accept(FIRE_SHOT);
			output.accept(GRAPESHOT);
			output.accept(HULL_PLATING);
			output.accept(REINFORCED_SAILCLOTH);
			output.accept(HEAVY_GUN_CARRIAGE);
		});

		ShipCombat.initialize();
		SeaBattleCommand.initialize();
	}

	private static Item registerItem(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = factory.apply(properties.setId(key));
		return Registry.register(BuiltInRegistries.ITEM, key, item);
	}
}
