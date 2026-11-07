package com.onepiecemod.crafting;

import java.util.ArrayList;
import java.util.List;
import java.util.function.BiPredicate;

import io.netty.buffer.ByteBuf;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Prediction;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.workshop.StationUpgrade;
import com.onepiecemod.workshop.StationUpgrades;

/**
 * Messages between the server and the player's game for crafting stations.
 *
 * Opening: the server works out which recipes are still locked for this player and sends them along,
 * because only the server knows your bounty, beaten bosses and so on.
 * Crafting: the player's game asks "craft this recipe here", and the server checks everything again.
 */
public class StationPayloads {
	/** Server -> player: "open this station". lockReasons has one entry per recipe ("" = unlocked). */
	public record OpenStation(BlockPos pos, String station, List<String> lockReasons) implements CustomPacketPayload {
		public static final Type<OpenStation> TYPE = new Type<>(OnePieceMod.id("open_station"));
		public static final StreamCodec<ByteBuf, OpenStation> CODEC = StreamCodec.composite(
				BlockPos.STREAM_CODEC, OpenStation::pos,
				ByteBufCodecs.STRING_UTF8, OpenStation::station,
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), OpenStation::lockReasons,
				OpenStation::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Player -> server: "craft this recipe at the station here". all = as many as they can afford (shift-click). */
	public record Craft(BlockPos pos, String recipe, boolean all) implements CustomPacketPayload {
		public static final Type<Craft> TYPE = new Type<>(OnePieceMod.id("station_craft"));
		public static final StreamCodec<ByteBuf, Craft> CODEC = StreamCodec.composite(
				BlockPos.STREAM_CODEC, Craft::pos,
				ByteBufCodecs.STRING_UTF8, Craft::recipe,
				ByteBufCodecs.BOOL, Craft::all,
				Craft::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Server -> player: "you just unlocked these station recipes" (recipe ids). Shown as a pop-up. */
	public record Unlocked(List<String> recipes) implements CustomPacketPayload {
		public static final Type<Unlocked> TYPE = new Type<>(OnePieceMod.id("station_unlocked"));
		public static final StreamCodec<ByteBuf, Unlocked> CODEC = StreamCodec.composite(
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), Unlocked::recipes,
				Unlocked::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/**
	 * Server -> player, sent just before OpenStation: this station's upgrade tree for this player.
	 * owned = upgrade ids built; lockReasons has one entry per upgrade of the station ("" = can build it, "Built" = owned).
	 */
	public record UpgradeState(String station, List<String> owned, List<String> lockReasons) implements CustomPacketPayload {
		public static final Type<UpgradeState> TYPE = new Type<>(OnePieceMod.id("station_upgrade_state"));
		public static final StreamCodec<ByteBuf, UpgradeState> CODEC = StreamCodec.composite(
				ByteBufCodecs.STRING_UTF8, UpgradeState::station,
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), UpgradeState::owned,
				ByteBufCodecs.STRING_UTF8.apply(ByteBufCodecs.list()), UpgradeState::lockReasons,
				UpgradeState::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Player -> server: "build this upgrade at the station here". */
	public record BuildUpgrade(BlockPos pos, String upgrade) implements CustomPacketPayload {
		public static final Type<BuildUpgrade> TYPE = new Type<>(OnePieceMod.id("station_build_upgrade"));
		public static final StreamCodec<ByteBuf, BuildUpgrade> CODEC = StreamCodec.composite(
				BlockPos.STREAM_CODEC, BuildUpgrade::pos,
				ByteBufCodecs.STRING_UTF8, BuildUpgrade::upgrade,
				BuildUpgrade::new
		);

		@Override
		public Type<? extends CustomPacketPayload> type() {
			return TYPE;
		}
	}

	/** Shift-click crafts at most this many times in one go. */
	private static final int MAX_BATCH = 64;

	/** Players must stand within this many blocks of the station. */
	private static final double REACH = 8.0;

	/**
	 * Lets a station that isn't a normal block in the world count too, like one on a sailing ship
	 * (whose blocks aren't in the world while it sails). The ship code fills this in.
	 */
	public static BiPredicate<ServerPlayer, Station> stationNearby = (player, station) -> false;

	public static void initialize() {
		PayloadTypeRegistry.clientboundPlay().register(OpenStation.TYPE, OpenStation.CODEC);
		PayloadTypeRegistry.clientboundPlay().register(Unlocked.TYPE, Unlocked.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(Craft.TYPE, Craft.CODEC);
		PayloadTypeRegistry.clientboundPlay().register(UpgradeState.TYPE, UpgradeState.CODEC);
		PayloadTypeRegistry.serverboundPlay().register(BuildUpgrade.TYPE, BuildUpgrade.CODEC);

		ServerPlayNetworking.registerGlobalReceiver(Craft.TYPE, (payload, context) -> craft(context.player(), payload));
		ServerPlayNetworking.registerGlobalReceiver(BuildUpgrade.TYPE, (payload, context) -> buildUpgrade(context.player(), payload));
	}

	/** Sends the station screen to the player. Called by StationBlock when it is right-clicked. */
	public static void open(ServerPlayer player, BlockPos pos, Station station) {
		List<String> reasons = new ArrayList<>();
		for (StationRecipe recipe : StationRecipe.forStation(station)) {
			String reason = recipe.lockReason(player);
			reasons.add(reason == null ? "" : reason);
		}
		// The upgrade tree first, so the screen has it when it opens.
		List<String> upgradeReasons = new ArrayList<>();
		for (StationUpgrade upgrade : StationUpgrade.forStation(station)) {
			String reason = StationUpgrades.lockReason(player, upgrade);
			upgradeReasons.add(reason == null ? "" : reason);
		}
		if (ServerPlayNetworking.canSend(player, UpgradeState.TYPE)) {
			ServerPlayNetworking.send(player, new UpgradeState(station.id(), StationUpgrades.owned(player), upgradeReasons));
		}
		ServerPlayNetworking.send(player, new OpenStation(pos, station.id(), reasons));
	}

	private static void give(ServerPlayer player, ItemStack stack) {
		if (!player.getInventory().add(stack)) {
			player.drop(stack, false, Prediction.SERVER_ONLY); // Inventory full: drop it at their feet.
		}
	}

	/** True if the player stands at a station of this kind: the block at pos, or one on their ship. */
	private static boolean atStation(ServerPlayer player, BlockPos pos, Station station) {
		BlockState state = player.level().getBlockState(pos);
		boolean here = state.getBlock() instanceof StationBlock block && block.station() == station
				&& player.distanceToSqr(Vec3.atCenterOf(pos)) <= REACH * REACH;
		return here || stationNearby.test(player, station);
	}

	private static void buildUpgrade(ServerPlayer player, BuildUpgrade payload) {
		StationUpgrade upgrade = StationUpgrade.get(payload.upgrade());
		if (upgrade == null || upgrade.stationType() == null || !atStation(player, payload.pos(), upgrade.stationType())) {
			return;
		}
		if (StationUpgrades.build(player, upgrade)) {
			open(player, payload.pos(), upgrade.stationType()); // Refresh the screen: new recipes may be open now.
		}
	}

	private static void craft(ServerPlayer player, Craft payload) {
		StationRecipe recipe = StationRecipe.get(payload.recipe());
		BlockState state = player.level().getBlockState(payload.pos());
		// Never trust the player's game: check the station is really there, close by, and the right kind.
		if (recipe == null) {
			return;
		}
		boolean atStation = state.getBlock() instanceof StationBlock block
				&& block.station() == recipe.stationType()
				&& player.distanceToSqr(Vec3.atCenterOf(payload.pos())) <= REACH * REACH;
		if (!atStation && !stationNearby.test(player, recipe.stationType())) {
			return;
		}
		String locked = recipe.lockReason(player);
		if (locked != null) {
			player.sendOverlayMessage(Component.literal("Locked: " + locked).withStyle(ChatFormatting.RED));
			return;
		}
		if (!recipe.hasIngredients(player)) {
			player.sendOverlayMessage(Component.literal("You don't have everything you need.").withStyle(ChatFormatting.RED));
			return;
		}

		int times = payload.all() ? Math.min(MAX_BATCH, recipe.timesCraftable(player)) : 1;
		int made = 0, bonus = 0, saved = 0;
		ItemStack result = recipe.resultStack();
		for (int i = 0; i < times && recipe.hasIngredients(player); i++) {
			// Station upgrade perks (see StationUpgrades): keep the ingredients, or get one extra.
			if (StationUpgrades.rollSave(player, recipe)) {
				saved++;
			} else {
				recipe.takeIngredients(player);
			}
			ItemStack stack = recipe.resultStack();
			com.onepiecemod.lifeskill.LifeSkillHooks.onStationCraft(player, recipe.stationType().id(), stack);
			made += stack.getCount();
			give(player, stack);
			if (StationUpgrades.rollBonus(player, recipe)) {
				give(player, recipe.resultStack().copyWithCount(1)); // Its own stack: swords and Dials don't stack.
				made++;
				bonus++;
			}
		}
		String extra = (bonus > 0 ? ", " + bonus + " extra" : "") + (saved > 0 ? ", ingredients kept " + saved + "x" : "");
		player.sendOverlayMessage(Component.literal("Crafted " + made + " x " + result.getHoverName().getString() + extra)
				.withStyle(bonus > 0 || saved > 0 ? ChatFormatting.GOLD : ChatFormatting.WHITE));
		player.level().playSound(null, atStation ? payload.pos() : player.blockPosition(), recipe.stationType().sound(), SoundSource.BLOCKS, 1.0f, 1.0f);
	}
}
