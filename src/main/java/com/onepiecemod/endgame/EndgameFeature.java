package com.onepiecemod.endgame;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

import net.minecraft.ChatFormatting;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;

import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.sound.ModSounds;

/**
 * The endgame, for after the story: the Laugh Tale finale and the Final War (Finale), the Emperor raids (RaidDef, Raids)
 * and New Game+ (NewGamePlus). OnePieceMod calls initialize() once while the game loads.
 */
public class EndgameFeature {
	/** Calls out a raid. Right-click to pick which crew, sneak + right-click to start the raid where you stand. */
	public static final Item RAID_DEN_DEN_MUSHI = registerItem("raid_den_den_mushi", properties -> new Item(properties) {
		@Override
		public Component getName(ItemStack stack) {
			return Component.literal("Raid Den Den Mushi").withStyle(ChatFormatting.RED);
		}

		@Override
		public InteractionResult use(Level level, Player player, InteractionHand hand) {
			if (player instanceof ServerPlayer serverPlayer) {
				if (player.isShiftKeyDown()) {
					startTuned(serverPlayer);
				} else {
					tuneNext(serverPlayer);
				}
			}
			return InteractionResult.SUCCESS;
		}
	}, new Item.Properties().stacksTo(1).rarity(Rarity.EPIC));

	/** Joy Boy's Treasure Chest: the final treasure at Laugh Tale, and a fancy storage chest for players (see JoyBoyChestBlock). */
	public static final ResourceKey<net.minecraft.world.level.block.Block> JOY_BOY_CHEST_KEY =
			ResourceKey.create(Registries.BLOCK, OnePieceMod.id("joy_boy_chest"));
	public static final JoyBoyChestBlock JOY_BOY_CHEST = Registry.register(BuiltInRegistries.BLOCK, JOY_BOY_CHEST_KEY,
			new JoyBoyChestBlock(BlockBehaviour.Properties.of().mapColor(MapColor.GOLD).strength(3.0f, 3600000.0f)
					.sound(SoundType.METAL).lightLevel(state -> 10).noOcclusion().pushReaction(PushReaction.IMMOVEABLE).setId(JOY_BOY_CHEST_KEY)));
	public static final Item JOY_BOY_CHEST_ITEM = registerItem("joy_boy_chest", properties -> new BlockItem(JOY_BOY_CHEST, properties) {
		@Override
		public Component getName(ItemStack stack) {
			return Component.literal("Joy Boy's Treasure Chest").withStyle(ChatFormatting.GOLD);
		}
	}, new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).useBlockDescriptionPrefix());

	public static final net.minecraft.world.level.block.entity.BlockEntityType<JoyBoyChestBlockEntity> JOY_BOY_CHEST_ENTITY = Registry.register(
			BuiltInRegistries.BLOCK_ENTITY_TYPE, OnePieceMod.id("joy_boy_chest"),
			net.fabricmc.fabric.api.object.builder.v1.block.entity.FabricBlockEntityTypeBuilder.create(JoyBoyChestBlockEntity::new, JOY_BOY_CHEST).build());

	/** One trophy per raid, for the first win. */
	private static final Map<String, Item> TROPHIES = new LinkedHashMap<>();

	static {
		for (RaidDef raid : RaidDef.all().values()) {
			String name = raid.trophyName();
			TROPHIES.put(raid.id(), registerItem("trophy_" + raid.id(), properties -> new Item(properties) {
				@Override
				public Component getName(ItemStack stack) {
					return Component.literal(name).withStyle(raid.color());
				}
			}, new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).fireResistant()));
		}
	}

	public static final ResourceKey<CreativeModeTab> TAB_KEY = ResourceKey.create(
			BuiltInRegistries.CREATIVE_MODE_TAB.key(), OnePieceMod.id("endgame")
	);

	public static void initialize() {
		EndgameData.EMPTY.cycle(); // Loading EndgameData registers its attachment.
		Raids.initialize();
		NewGamePlus.initialize();
		Finale.initialize();
		VoidCentury.initialize();
		PoneglyphSites.initialize();
		NewWorldTier.initialize();
		EndgameCommands.initialize();

		Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, TAB_KEY, FabricCreativeModeTab.builder()
				.icon(() -> new ItemStack(RAID_DEN_DEN_MUSHI))
				.title(Component.literal("One Piece: Endgame"))
				.displayItems((params, output) -> {
					output.accept(RAID_DEN_DEN_MUSHI);
					output.accept(JOY_BOY_CHEST_ITEM);
					TROPHIES.values().forEach(output::accept);
				})
				.build());
	}

	public static ItemStack trophy(String raid) {
		Item item = TROPHIES.get(raid);
		return item == null ? ItemStack.EMPTY : new ItemStack(item);
	}

	// ---- The Raid Den Den Mushi ----

	/** Raids this player has unlocked, in order. */
	static List<RaidDef> unlocked(ServerPlayer player) {
		List<RaidDef> list = new ArrayList<>();
		for (RaidDef raid : RaidDef.all().values()) {
			if (raid.unlocked().test(player)) {
				list.add(raid);
			}
		}
		return list;
	}

	private static void tuneNext(ServerPlayer player) {
		List<RaidDef> open = unlocked(player);
		if (open.isEmpty()) {
			player.sendSystemMessage(Component.literal("Static... No crew answers yet. Finish the story at Laugh Tale first.").withStyle(ChatFormatting.GRAY));
			EndgameCommands.listRaids(player);
			return;
		}
		EndgameData data = EndgameData.of(player);
		int index = -1;
		for (int i = 0; i < open.size(); i++) {
			if (open.get(i).id().equals(data.selected())) {
				index = i;
			}
		}
		RaidDef next = open.get((index + 1) % open.size());
		EndgameData.set(player, data.withSelected(next.id()));
		ModSounds.play(player, ModSounds.DEN_DEN_MUSHI_CALL, 0.6f);
		player.sendSystemMessage(Component.literal("Tuned to: " + next.name() + " (" + next.crew() + ", " + next.waves().size()
				+ " waves). Sneak + right-click to start the raid here.").withStyle(next.color()));
	}

	private static void startTuned(ServerPlayer player) {
		RaidDef raid = RaidDef.get(EndgameData.of(player).selected());
		if (raid == null || !raid.unlocked().test(player)) {
			tuneNext(player);
			return;
		}
		String problem = Raids.start(player, raid);
		if (problem != null) {
			player.sendSystemMessage(Component.literal(problem).withStyle(ChatFormatting.RED));
		}
	}

	private static Item registerItem(String name, Function<Item.Properties, Item> itemFactory, Item.Properties properties) {
		ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, OnePieceMod.id(name));
		Item item = itemFactory.apply(properties.setId(itemKey));
		Registry.register(BuiltInRegistries.ITEM, itemKey, item);
		return item;
	}
}
