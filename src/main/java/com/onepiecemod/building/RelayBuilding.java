package com.onepiecemod.building;

import java.util.ArrayList;
import java.util.List;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;

import net.minecraft.ChatFormatting;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.block.Blocks;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

import com.onepiecemod.character.CharacterFeature;
import com.onepiecemod.sound.ModSounds;

/**
 * Den Den Mushi Relay: a radio mast with a big snail phone at the bottom.
 * Build two or more and you can "call a ride" from one to another, for a few Berries.
 * Only your own relays, and only in the same world (the Overworld can't call the Nether).
 */
public class RelayBuilding extends Multiblock {
	private static final int MIN_PRICE = 5; // Berries
	private static final int BLOCKS_PER_BERRY = 200; // Longer trips cost more.

	public RelayBuilding() {
		super("den_den_relay", "Den Den Mushi Relay");
		fill("stone or brick blocks for the 3x3 base under the Relay", Parts.STONE, Parts.block("onepiece:marine_bricks", Blocks.STONE_BRICKS), square(-1, 1));
		fill("fences, walls or iron bars for the mast (4 tall, on top of the Relay)", Parts.RAIL, Blocks.IRON_BARS.defaultBlockState(), column(0, 0, 1, 4));
		fill("Lightning Rod on top of the mast (the antenna)", Parts.LIGHTNING_ROD, Parts.block("minecraft:lightning_rod", Blocks.IRON_BARS), column(0, 0, 5, 5));

		planLine("Base: a 3x3 square of any stone or brick blocks (Marine Bricks look great).");
		planLine("The Den Den Mushi Relay goes in the middle of the base.");
		planLine("Mast: 4 fences, walls or iron bars stacked on top of the Relay.");
		planLine("Antenna: a Lightning Rod on top of the mast.");
		planLine("Build a second Relay somewhere else, then right-click one to travel to the other.");
	}

	@Override
	public String purpose() {
		return "Right-click it to travel to your other Relays for a few Berries.";
	}

	@Override
	public void use(ServerPlayer player, BuildingRegistry.Entry here) {
		ServerLevel level = (ServerLevel) player.level();
		level.playSound(null, here.pos(), ModSounds.DEN_DEN_MUSHI_CALL, SoundSource.BLOCKS, 1.0f, 1.0f);
		List<BuildingRegistry.Entry> others = new ArrayList<>();
		for (BuildingRegistry.Entry entry : BuildingRegistry.all(level)) {
			if (entry.type().equals(id()) && entry.owner().equals(player.getUUID()) && !entry.pos().equals(here.pos())) {
				others.add(entry);
			}
		}
		if (others.isEmpty()) {
			player.sendSystemMessage(Component.literal("Puru puru puru... No other Relay picks up. Build a second Den Den Mushi Relay somewhere else in this world.")
					.withStyle(ChatFormatting.GRAY));
			return;
		}
		player.sendSystemMessage(Component.literal("Puru puru puru... gacha! Where to? (you have " + Parts.count(player, CharacterFeature.BERRY) + " Berries)")
				.withStyle(ChatFormatting.GOLD));
		for (BuildingRegistry.Entry entry : others) {
			BlockPos pos = entry.pos();
			int distance = (int) Math.sqrt(pos.distSqr(here.pos()));
			int price = price(distance);
			String command = "/relay " + pos.getX() + " " + pos.getY() + " " + pos.getZ();
			MutableComponent line = Component.literal("  [Travel] ").withStyle(style -> style.withColor(ChatFormatting.GREEN)
					.withClickEvent(new ClickEvent.RunCommand(command))
					.withHoverEvent(new HoverEvent.ShowText(Component.literal("Go there for " + price + " Berries"))));
			line.append(Component.literal("Relay at " + pos.getX() + ", " + pos.getY() + ", " + pos.getZ() + " " + direction(here.pos(), pos)
					+ ", " + distance + " blocks away, " + price + " Berries").withStyle(ChatFormatting.YELLOW));
			player.sendSystemMessage(line);
		}
	}

	private static int price(int distance) {
		return Math.max(MIN_PRICE, distance / BLOCKS_PER_BERRY);
	}

	/** "to the north-east" and so on. */
	public static String direction(BlockPos from, BlockPos to) {
		int dx = to.getX() - from.getX();
		int dz = to.getZ() - from.getZ();
		String ns = Math.abs(dz) * 2 > Math.abs(dx) ? (dz < 0 ? "north" : "south") : "";
		String ew = Math.abs(dx) * 2 > Math.abs(dz) ? (dx < 0 ? "west" : "east") : "";
		return "to the " + (ns.isEmpty() || ew.isEmpty() ? ns + ew : ns + "-" + ew);
	}

	// ---------- The /relay command that the [Travel] link runs ----------

	public static void initialize() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
				Commands.literal("relay")
						.then(Commands.argument("x", IntegerArgumentType.integer())
								.then(Commands.argument("y", IntegerArgumentType.integer())
										.then(Commands.argument("z", IntegerArgumentType.integer())
												.executes(RelayBuilding::travel))))));
	}

	private static int travel(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
		ServerPlayer player = context.getSource().getPlayerOrException();
		ServerLevel level = (ServerLevel) player.level();
		Multiblock relay = Buildings.get("den_den_relay");
		BlockPos target = new BlockPos(IntegerArgumentType.getInteger(context, "x"), IntegerArgumentType.getInteger(context, "y"),
				IntegerArgumentType.getInteger(context, "z"));

		BuildingRegistry.Entry here = null;
		for (BuildingRegistry.Entry entry : BuildingRegistry.all(level)) {
			if (entry.type().equals(relay.id()) && entry.pos().distSqr(player.blockPosition()) <= 36
					&& relay.check(level, entry.pos()).complete()) {
				here = entry;
			}
		}
		if (here == null) {
			player.sendSystemMessage(Component.literal("You need to stand next to a finished Den Den Mushi Relay to make a call.").withStyle(ChatFormatting.RED));
			return 0;
		}
		BuildingRegistry.Entry there = BuildingRegistry.at(level, target);
		if (there == null || !there.type().equals(relay.id()) || !there.owner().equals(player.getUUID())) {
			player.sendSystemMessage(Component.literal("That's not one of your Relays.").withStyle(ChatFormatting.RED));
			return 0;
		}
		if (!relay.check(level, target).complete()) {
			player.sendSystemMessage(Component.literal("The Relay over there is broken or unfinished, so nobody picks up.").withStyle(ChatFormatting.RED));
			return 0;
		}
		int price = price((int) Math.sqrt(target.distSqr(here.pos())));
		if (!player.isCreative()) {
			if (Parts.count(player, CharacterFeature.BERRY) < price) {
				player.sendSystemMessage(Component.literal("The trip costs " + price + " Berries.").withStyle(ChatFormatting.RED));
				return 0;
			}
			Parts.take(player, CharacterFeature.BERRY, price);
		}

		level.sendParticles(ParticleTypes.REVERSE_PORTAL, player.getX(), player.getY() + 1, player.getZ(), 30, 0.4, 0.8, 0.4, 0.05);
		BlockPos landing = landingSpot(level, target);
		player.teleportTo(landing.getX() + 0.5, landing.getY(), landing.getZ() + 0.5);
		level.playSound(null, landing, ModSounds.DEN_DEN_MUSHI_CALL, SoundSource.PLAYERS, 1.0f, 1.2f);
		level.sendParticles(ParticleTypes.REVERSE_PORTAL, landing.getX() + 0.5, landing.getY() + 1, landing.getZ() + 0.5, 30, 0.4, 0.8, 0.4, 0.05);
		player.sendSystemMessage(Component.literal("Gacha. You arrive at your Relay.").withStyle(ChatFormatting.GREEN));
		return 1;
	}

	/** A free spot next to the Relay, on its base. */
	private static BlockPos landingSpot(ServerLevel level, BlockPos relay) {
		for (Direction direction : Direction.Plane.HORIZONTAL) {
			BlockPos spot = relay.relative(direction);
			if (level.getBlockState(spot).isAir() && level.getBlockState(spot.above()).isAir()) {
				return spot;
			}
		}
		return relay.above(6); // Every side is walled in: land on top of the antenna.
	}
}
