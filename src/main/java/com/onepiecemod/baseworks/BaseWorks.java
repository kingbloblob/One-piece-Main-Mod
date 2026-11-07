package com.onepiecemod.baseworks;

import java.util.Map;
import java.util.UUID;
import java.util.function.Function;

import com.mojang.brigadier.arguments.StringArgumentType;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.crew.CrewmateEntity;
import com.onepiecemod.hideout.Hideouts;
import com.onepiecemod.item.ModItems;

/**
 * Base building tools:
 *  - Deck Plans and Island Base Plans: plan books whose pages show a room or a hideout piece as ghost blocks
 *    ({@link PlanBookItem}, {@link PlanBooks}, {@link LayoutPlan}, {@link PlanOutlines}).
 *  - The Builder's Ledger: hideout upgrades that need a big enough bounty and cost Berries ({@link BaseUpgrades}),
 *    plus your town's treasury (settlement package). Command: /base, /base build <upgrade>.
 * OnePieceMod calls initialize() once, after the hideout and town features.
 */
public final class BaseWorks {
	public static final Item DECK_PLANS = item("deck_plans", p -> new PlanBookItem(PlanBookItem.Book.DECK, p),
			new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON));
	public static final Item BASE_PLANS = item("island_base_plans", p -> new PlanBookItem(PlanBookItem.Book.BASE, p),
			new Item.Properties().stacksTo(1).rarity(Rarity.UNCOMMON));
	public static final Item LEDGER = item("builders_ledger", LedgerItem::new, new Item.Properties().stacksTo(1));

	private BaseWorks() {
	}

	private static Item item(String name, Function<Item.Properties, Item> factory, Item.Properties properties) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		return Registry.register(BuiltInRegistries.ITEM, key, factory.apply(properties.setId(key)));
	}

	public static void initialize() {
		java.util.Objects.requireNonNull(PlanOutlines.PLANS_BUILT);
		java.util.Objects.requireNonNull(BaseUpgrades.UPGRADES);

		CreativeModeTabEvents.modifyOutputEvent(ModItems.ONE_PIECE_TAB_KEY).register(output -> {
			output.accept(DECK_PLANS);
			output.accept(BASE_PLANS);
			output.accept(LEDGER);
		});

		ServerTickEvents.END_SERVER_TICK.register(server -> {
			PlanOutlines.tick(server);
			if (server.getTickCount() % 40 == 0) {
				healCrews(server);
			}
		});

		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("base")
						.executes(context -> {
							BaseUpgrades.menu(context.getSource().getPlayerOrException());
							return 1;
						})
						.then(Commands.literal("build")
								.then(Commands.argument("upgrade", StringArgumentType.word())
										.suggests((context, builder) -> {
											for (BaseUpgrades.Upgrade upgrade : BaseUpgrades.Upgrade.values()) {
												builder.suggest(upgrade.id);
											}
											return builder.buildFuture();
										})
										.executes(context -> {
											ServerPlayer player = context.getSource().getPlayerOrException();
											String problem = BaseUpgrades.build(player, StringArgumentType.getString(context, "upgrade"));
											if (problem != null) {
												player.sendSystemMessage(Component.literal(problem).withStyle(ChatFormatting.RED));
												return 0;
											}
											return 1;
										})))
						.then(Commands.literal("set")
								.requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
								.then(Commands.argument("upgrade", StringArgumentType.word())
										.then(Commands.argument("tier", com.mojang.brigadier.arguments.IntegerArgumentType.integer(0, 3))
												.executes(context -> {
													ServerPlayer player = context.getSource().getPlayerOrException();
													BaseUpgrades.Upgrade upgrade = BaseUpgrades.Upgrade.byId(StringArgumentType.getString(context, "upgrade"));
													if (upgrade == null) {
														return 0;
													}
													int tier = Math.min(upgrade.maxTier(), com.mojang.brigadier.arguments.IntegerArgumentType.getInteger(context, "tier"));
													BaseUpgrades.setTier(player.level().getServer(), player.getUUID(), upgrade, tier);
													context.getSource().sendSuccess(() -> Component.literal(upgrade.title + " set to tier " + tier), false);
													return 1;
												}))))
		));
	}

	/** Sick Bay II: crewmates who live in the hideout get back 1 heart every 2 seconds. */
	private static void healCrews(MinecraftServer server) {
		ServerLevel level = server.overworld();
		for (Map.Entry<String, Hideouts.Hideout> entry : Hideouts.all(server).entrySet()) {
			UUID captain = UUID.fromString(entry.getKey());
			if (!BaseUpgrades.crewHealing(server, captain)) {
				continue;
			}
			BlockPos flag = entry.getValue().pos();
			if (!level.isLoaded(flag)) {
				continue;
			}
			AABB box = new AABB(flag).inflate(Hideouts.RADIUS, 24, Hideouts.RADIUS);
			for (CrewmateEntity crewmate : level.getEntitiesOfClass(CrewmateEntity.class, box,
					c -> captain.equals(c.getCaptainId()) && c.isAlive() && c.getHealth() < c.getMaxHealth())) {
				crewmate.heal(2.0f);
			}
		}
	}

	/** The Builder's Ledger: use it to see your upgrades and hire builders. */
	static class LedgerItem extends Item {
		LedgerItem(Properties properties) {
			super(properties);
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			if (player instanceof ServerPlayer serverPlayer) {
				BaseUpgrades.menu(serverPlayer);
			}
			return InteractionResult.SUCCESS;
		}
	}
}
