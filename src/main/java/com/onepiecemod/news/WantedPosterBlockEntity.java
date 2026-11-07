package com.onepiecemod.news;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.joml.Quaternionf;
import org.joml.Vector3f;

import com.mojang.math.Transformation;

import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.ResolvableProfile;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

import com.onepiecemod.bounty.Bounty;

/**
 * Keeps a wall poster's picture up to date. The face and text are vanilla display entities
 * standing just in front of the poster (tagged onepiece_wall_poster), so nothing extra is needed on the client.
 *
 * Which pirate: "slot" N = the Nth entry of [players with a bounty, highest first] + [famous pirates that
 * fit the story so far]. Slot 0 is the most wanted pirate in the world.
 */
public class WantedPosterBlockEntity extends BlockEntity {
	public static final String TAG = "onepiece_wall_poster";
	private static final int UPDATE_TICKS = 100;

	private int slot;
	/** What the poster shows now, so it only redraws when something changed. */
	private String shown = "";

	public WantedPosterBlockEntity(BlockPos pos, BlockState state) {
		super(NewsFeature.WANTED_POSTER_ENTITY, pos, state);
	}

	public void setSlot(int slot) {
		this.slot = Math.max(0, slot);
		this.shown = "";
		setChanged();
	}

	/** One pirate on a poster. uuid is null for famous (non-player) pirates. */
	public record Subject(String name, long bounty, String race, UUID uuid) {
		String key() {
			return name + "|" + bounty + "|" + race + "|" + uuid;
		}
	}

	public static void serverTick(Level level, BlockPos pos, BlockState state, WantedPosterBlockEntity poster) {
		if ((level.getGameTime() + pos.asLong()) % UPDATE_TICKS != 0 || !(level instanceof ServerLevel serverLevel)) {
			return;
		}
		if (serverLevel.getNearestPlayer(pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 64.0, false) == null) {
			return;
		}
		poster.refresh(serverLevel, state);
	}

	/** The pirates posters can show, most wanted first. */
	public static List<Subject> subjects(ServerLevel level, BlockPos near) {
		List<Subject> list = new ArrayList<>();
		for (Map.Entry<String, NewsLog.Wanted> e : NewsLog.mostWanted(level.getServer())) {
			UUID uuid;
			try {
				uuid = UUID.fromString(e.getKey());
			} catch (IllegalArgumentException ex) {
				uuid = null;
			}
			list.add(new Subject(e.getValue().name(), e.getValue().bounty(), e.getValue().race(), uuid));
		}
		Player reader = level.getNearestPlayer(near.getX(), near.getY(), near.getZ(), 128.0, false);
		int saga = reader instanceof ServerPlayer sp ? Newspaper.sagaNumber(sp) : 0;
		List<NewsData.Canon> canon = new ArrayList<>(NewsData.get().canon);
		canon.removeIf(c -> c.saga > saga);
		// Newest first, so a town shows the pirates people are talking about right now.
		canon.sort((a, b) -> b.saga != a.saga ? b.saga - a.saga : Long.compare(b.bounty, a.bounty));
		List<String> names = new ArrayList<>();
		for (NewsData.Canon c : canon) {
			if (!names.contains(c.name)) {
				names.add(c.name);
				list.add(new Subject(c.name, c.bounty, "", null));
			}
		}
		return list;
	}

	public Subject subject(ServerLevel level) {
		List<Subject> list = subjects(level, worldPosition);
		if (list.isEmpty()) {
			return new Subject("Unknown Pirate", 0, "", null);
		}
		return list.get(slot % list.size());
	}

	private void refresh(ServerLevel level, BlockState state) {
		Subject subject = subject(level);
		List<Display> displays = displays(level);
		boolean missing = displays.size() != (subject.uuid() != null ? 2 : 1);
		if (!missing && subject.key().equals(shown)) {
			return;
		}
		for (Display d : displays) {
			d.discard();
		}
		shown = subject.key();
		Direction facing = state.getValue(WantedPosterBlock.FACING);
		spawnText(level, facing, subject);
		if (subject.uuid() != null) {
			spawnFace(level, facing, subject.uuid());
		}
	}

	/** A point on the poster's front: across = -0.5..0.5 left to right, up = 0..1 from the bottom. */
	private Vec3 onPoster(Direction facing, double across, double up) {
		Vec3 center = Vec3.atBottomCenterOf(worldPosition);
		Direction right = facing.getCounterClockWise();
		double out = -0.5 + 1.0 / 16.0 + 0.01; // Just in front of the 1-pixel-thick poster.
		return center.add(facing.getStepX() * out + right.getStepX() * across, up, facing.getStepZ() * out + right.getStepZ() * across);
	}

	private void spawnText(ServerLevel level, Direction facing, Subject subject) {
		Display.TextDisplay text = EntityTypes.TEXT_DISPLAY.create(level, EntitySpawnReason.LOAD);
		if (text == null) {
			return;
		}
		Component lines = Component.literal(subject.name()).withStyle(ChatFormatting.BLACK, ChatFormatting.BOLD)
				.append(Component.literal("\n฿ " + String.format("%,d", subject.bounty()) + "-").withStyle(s -> s.withBold(false).withColor(0x3A1A0A)));
		if (!subject.race().isEmpty()) {
			lines = lines.copy().append(Component.literal("\n" + subject.race()).withStyle(s -> s.withBold(false).withColor(0x6B4A2A)));
		}
		text.setText(lines);
		text.setBackgroundColor(0);
		text.setLineWidth(200);
		// Fit long names: about 6 font pixels per letter, 0.025 blocks per pixel, 0.8 blocks of room.
		int longest = Math.max(subject.name().length() + 1, 12);
		float scale = Math.min(0.36f, 0.8f / (longest * 6 * 0.025f));
		text.setTransformation(new Transformation(new Vector3f(), new Quaternionf(), new Vector3f(scale, scale, scale), new Quaternionf()));
		text.setBillboardConstraints(Display.BillboardConstraints.FIXED);
		Vec3 at = onPoster(facing, 0, 0.06);
		text.setPos(at.x, at.y, at.z);
		text.setYRot(facing.toYRot());
		text.setViewRange(0.5f);
		text.addTag(TAG);
		level.addFreshEntity(text);
	}

	private void spawnFace(ServerLevel level, Direction facing, UUID uuid) {
		Display.ItemDisplay face = EntityTypes.ITEM_DISPLAY.create(level, EntitySpawnReason.LOAD);
		if (face == null) {
			return;
		}
		ItemStack head = new ItemStack(Items.PLAYER_HEAD);
		head.set(DataComponents.PROFILE, ResolvableProfile.createUnresolved(uuid));
		face.setItemStack(head);
		face.setItemTransform(ItemDisplayContext.FIXED);
		face.setTransformation(new Transformation(new Vector3f(), new Quaternionf(),
				new Vector3f(0.62f, 0.62f, 0.12f), new Quaternionf()));
		face.setBillboardConstraints(Display.BillboardConstraints.FIXED);
		Vec3 at = onPoster(facing, 0, 0.625);
		face.setPos(at.x, at.y, at.z);
		face.setYRot(facing.toYRot());
		face.setViewRange(0.5f);
		face.addTag(TAG);
		level.addFreshEntity(face);
	}

	private List<Display> displays(ServerLevel level) {
		return level.getEntitiesOfClass(Display.class, new AABB(worldPosition).inflate(0.05), d -> d.entityTags().contains(TAG));
	}

	/** Right-click: read who's on it. */
	public void read(ServerPlayer player) {
		Subject subject = subject((ServerLevel) player.level());
		player.sendSystemMessage(Component.literal("+--------- WANTED ---------+").withStyle(ChatFormatting.GOLD));
		player.sendSystemMessage(Component.literal("  " + subject.name()).withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD));
		player.sendSystemMessage(Component.literal("  DEAD OR ALIVE: " + Bounty.format(subject.bounty())).withStyle(ChatFormatting.YELLOW));
		if (!subject.race().isEmpty()) {
			player.sendSystemMessage(Component.literal("  " + subject.race() + ", " + Bounty.levelName(Bounty.threatLevel(subject.bounty())))
					.withStyle(ChatFormatting.GRAY));
		}
		if (subject.uuid() != null && subject.uuid().equals(player.getUUID())) {
			player.sendSystemMessage(Component.literal("  That's you! The poster updates whenever your bounty rises.").withStyle(ChatFormatting.GREEN));
		}
		player.sendSystemMessage(Component.literal("+--------------------------+").withStyle(ChatFormatting.GOLD));
	}

	/** Sneak + right-click: show the next pirate on the list. */
	public void nextPirate(ServerPlayer player) {
		ServerLevel level = (ServerLevel) player.level();
		int count = Math.max(1, subjects(level, worldPosition).size());
		setSlot((slot + 1) % count);
		refresh(level, getBlockState());
		player.sendSystemMessage(Component.literal("You pin up the poster of " + subject(level).name() + ".").withStyle(ChatFormatting.GRAY));
	}

	@Override
	public void preRemoveSideEffects(BlockPos pos, BlockState state) {
		super.preRemoveSideEffects(pos, state);
		if (level instanceof ServerLevel serverLevel) {
			for (Display d : displays(serverLevel)) {
				d.discard();
			}
		}
	}

	@Override
	public void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.putInt("Slot", slot);
	}

	@Override
	public void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		slot = input.getIntOr("Slot", 0);
		shown = "";
	}
}
