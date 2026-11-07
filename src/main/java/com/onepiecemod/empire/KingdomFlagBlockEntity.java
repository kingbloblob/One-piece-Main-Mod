package com.onepiecemod.empire;

import java.util.List;
import java.util.UUID;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.UUIDUtil;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.ai.village.poi.PoiManager;
import net.minecraft.world.entity.ai.village.poi.PoiTypes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;

import com.onepiecemod.bounty.NavyRaids;
import com.onepiecemod.character.CharacterFeature;

/**
 * The heart of a pirate kingdom. While its chunk is loaded it:
 *  - brings in pirate guards, like a village gets iron golems: 1, plus 1 for every 3 beds nearby,
 *    up to the owner's title limit (4 without a title, 10 for the King of the World);
 *  - collects taxes once per Minecraft day into its treasury (up to a week's worth),
 *    except on days the owner is fighting off the Navy.
 */
public class KingdomFlagBlockEntity extends BlockEntity {
	public static final double RADIUS = 48.0;
	private static final int GUARD_CHECK_TICKS = 20 * 30;
	private static final int BEDS_PER_GUARD = 3;
	private static final int MAX_DAYS_SAVED = 7;

	private UUID owner;
	private String ownerName = "";
	private int treasury = 0;
	private long lastTaxDay = -1;

	public KingdomFlagBlockEntity(BlockPos pos, BlockState state) {
		super(EmpireFeature.KINGDOM_FLAG_ENTITY, pos, state);
	}

	public UUID owner() {
		return owner;
	}

	void claim(ServerPlayer player) {
		owner = player.getUUID();
		ownerName = player.getName().getString();
		lastTaxDay = day(player.level());
		setChanged();
	}

	private static long day(Level level) {
		return level.getOverworldClockTime() / 24000L;
	}

	/** The owner's title, even while they are offline. */
	private Title ownerTitle(ServerLevel level) {
		if (owner == null) {
			return Title.NONE;
		}
		return Title.byLevel(EmpireData.holders(level.getServer()).getOrDefault(owner.toString(), 0));
	}

	public static void serverTick(Level level, BlockPos pos, BlockState state, KingdomFlagBlockEntity flag) {
		if (!(level instanceof ServerLevel serverLevel) || flag.owner == null) {
			return;
		}
		flag.collectTaxes(serverLevel);
		if ((level.getGameTime() + pos.asLong()) % GUARD_CHECK_TICKS == 0) {
			flag.recruitGuard(serverLevel);
		}
	}

	// ---- Guards ----

	List<PirateGuardEntity> guards(ServerLevel level) {
		return level.getEntitiesOfClass(PirateGuardEntity.class, new AABB(worldPosition).inflate(RADIUS + 16),
				guard -> worldPosition.equals(guard.home()));
	}

	int beds(ServerLevel level) {
		return (int) level.getPoiManager().getCountInRange(holder -> holder.is(PoiTypes.HOME), worldPosition,
				(int) RADIUS, PoiManager.Occupancy.ANY);
	}

	int guardLimit(ServerLevel level) {
		return Math.min(ownerTitle(level).maxGuards, 1 + beds(level) / BEDS_PER_GUARD);
	}

	private void recruitGuard(ServerLevel level) {
		if (guards(level).size() >= guardLimit(level)) {
			return;
		}
		BlockPos spot = spawnSpot(level);
		if (spot == null) {
			return;
		}
		PirateGuardEntity guard = EmpireFeature.PIRATE_GUARD.create(level, EntitySpawnReason.MOB_SUMMONED);
		if (guard == null) {
			return;
		}
		guard.setPos(spot.getX() + 0.5, spot.getY(), spot.getZ() + 0.5);
		guard.setHome(worldPosition, owner, ownerTitle(level));
		level.addFreshEntity(guard);
	}

	private BlockPos spawnSpot(ServerLevel level) {
		for (int attempt = 0; attempt < 10; attempt++) {
			int x = worldPosition.getX() + level.getRandom().nextInt(17) - 8;
			int z = worldPosition.getZ() + level.getRandom().nextInt(17) - 8;
			BlockPos pos = new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z);
			if (level.getBlockState(pos.below()).isSolid() && level.getFluidState(pos.below()).isEmpty()
					&& level.getBlockState(pos).isAir() && level.getBlockState(pos.above()).isAir()
					&& Math.abs(pos.getY() - worldPosition.getY()) < 12) {
				return pos;
			}
		}
		return null;
	}

	// ---- Taxes ----

	private void collectTaxes(ServerLevel level) {
		long today = day(level);
		if (lastTaxDay < 0) {
			lastTaxDay = today;
			setChanged();
			return;
		}
		if (today <= lastTaxDay) {
			return;
		}
		long days = Math.min(MAX_DAYS_SAVED, today - lastTaxDay);
		lastTaxDay = today;
		setChanged();

		ServerPlayer ruler = level.getServer().getPlayerList().getPlayer(owner);
		if (ruler != null && (NavyRaids.isRaiding(ruler) || BusterCall.isActive(ruler))) {
			ruler.sendSystemMessage(Component.literal("Your kingdom paid no taxes today: everyone is hiding from the Navy.")
					.withStyle(ChatFormatting.GRAY));
			return;
		}
		Title title = ownerTitle(level);
		int perDay = title.taxPerDay + guards(level).size();
		int cap = (title.taxPerDay + title.maxGuards) * MAX_DAYS_SAVED;
		treasury = Mth.clamp(treasury + (int) (perDay * days), 0, cap);
		if (ruler != null && ruler.distanceToSqr(net.minecraft.world.phys.Vec3.atCenterOf(worldPosition)) < RADIUS * RADIUS * 4) {
			ruler.sendOverlayMessage(Component.literal("Your kingdom paid " + perDay * days + " Berries in taxes.")
					.withStyle(ChatFormatting.GOLD));
		}
	}

	// ---- Right-click ----

	void use(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		if (owner == null) {
			player.sendSystemMessage(Component.literal("This flag has no ruler.").withStyle(ChatFormatting.GRAY));
			return;
		}
		if (!owner.equals(player.getUUID())) {
			player.sendSystemMessage(Component.literal("This land belongs to " + ownerName + ". Its guards are watching you.")
					.withStyle(ChatFormatting.YELLOW));
			return;
		}
		Title title = ownerTitle(level);
		player.sendSystemMessage(Component.literal("=== Your kingdom ===").withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal("Guards: " + guards(level).size() + " / " + guardLimit(level)
				+ " (beds nearby: " + beds(level) + ", title limit: " + title.maxGuards + ")"));
		player.sendSystemMessage(Component.literal("Taxes: " + (title.taxPerDay + guards(level).size())
				+ " Berries a day. Saved up to " + MAX_DAYS_SAVED + " days."));
		if (treasury <= 0) {
			player.sendSystemMessage(Component.literal("The treasury is empty. Come back tomorrow.").withStyle(ChatFormatting.GRAY));
			return;
		}
		int paid = treasury;
		while (treasury > 0) {
			int amount = Math.min(64, treasury);
			ItemStack berries = new ItemStack(CharacterFeature.BERRY, amount);
			if (!player.getInventory().add(berries)) {
				player.spawnAtLocation(level, berries);
			}
			treasury -= amount;
		}
		setChanged();
		level.playSound(null, worldPosition, SoundEvents.PLAYER_LEVELUP, SoundSource.BLOCKS, 0.8f, 1.4f);
		player.sendSystemMessage(Component.literal("You collected " + paid + " Berries from the treasury.").withStyle(ChatFormatting.GOLD));
	}

	// ---- Saving ----

	@Override
	public void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		if (owner != null) {
			output.store("Owner", UUIDUtil.CODEC, owner);
		}
		output.putString("OwnerName", ownerName);
		output.putInt("Treasury", treasury);
		output.putLong("LastTaxDay", lastTaxDay);
	}

	@Override
	public void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		owner = input.read("Owner", UUIDUtil.CODEC).orElse(null);
		ownerName = input.getStringOr("OwnerName", "");
		treasury = input.getIntOr("Treasury", 0);
		lastTaxDay = input.getLongOr("LastTaxDay", -1L);
	}
}
