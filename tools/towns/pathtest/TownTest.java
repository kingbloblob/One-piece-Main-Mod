package com.onepiecemod.town;

import java.lang.reflect.Field;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.ai.goal.GoalSelector;
import net.minecraft.world.entity.ai.goal.WrappedGoal;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureStart;
import net.minecraft.world.phys.Vec3;

/** TEST ONLY (never shipped): /towntest x z keeps the town there visited and logs how well its people move. */
public class TownTest {
	static Town town;
	static int samples, away, stuck, longStuck, arrivedSamples;
	static Map<Integer, Vec3> last = new HashMap<>();
	static Map<Integer, Integer> streak = new HashMap<>();
	static Map<String, int[]> perActivity = new HashMap<>();

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(TownTest::tick);
		CommandRegistrationCallback.EVENT.register((d, r, e) -> d.register(Commands.literal("towntest")
				.then(Commands.argument("x", com.mojang.brigadier.arguments.IntegerArgumentType.integer())
						.then(Commands.argument("z", com.mojang.brigadier.arguments.IntegerArgumentType.integer()).executes(c -> {
							int x = com.mojang.brigadier.arguments.IntegerArgumentType.getInteger(c, "x");
							int z = com.mojang.brigadier.arguments.IntegerArgumentType.getInteger(c, "z");
							ServerLevel level = c.getSource().getLevel();
							for (int y = 140; y > -20; y -= 4) {
								if (find(level, new BlockPos(x, y, z))) break;
							}
							System.out.println("TOWNTEST town=" + (town == null ? "none" : town.key + " box=" + town.box));
							if (town != null) {
								var b = town.box;
								for (int cx = (b.minX() >> 4) - 1; cx <= (b.maxX() >> 4) + 1; cx++)
									for (int cz = (b.minZ() >> 4) - 1; cz <= (b.maxZ() >> 4) + 1; cz++)
										level.setChunkForced(cx, cz, true);
							}
							return 1;
						})))
				.then(Commands.literal("report").executes(c -> { report(); return 1; }))
				.then(Commands.literal("doors").executes(c -> {
					int open = 0, closed = 0, gopen = 0, gclosed = 0;
					var b = town.box;
					for (BlockPos p : BlockPos.betweenClosed(b.minX(), b.minY(), b.minZ(), b.maxX(), b.maxY(), b.maxZ())) {
						var st = town.level.getBlockState(p);
						if (st.getBlock() instanceof net.minecraft.world.level.block.DoorBlock && st.getValue(net.minecraft.world.level.block.DoorBlock.HALF) == net.minecraft.world.level.block.state.properties.DoubleBlockHalf.LOWER) {
							if (st.getValue(net.minecraft.world.level.block.DoorBlock.OPEN)) open++; else closed++;
						}
						if (st.getBlock() instanceof net.minecraft.world.level.block.FenceGateBlock) {
							if (st.getValue(net.minecraft.world.level.block.FenceGateBlock.OPEN)) gopen++; else gclosed++;
						}
					}
					System.out.println("TOWNTEST doors open=" + open + " closed=" + closed + " gates open=" + gopen + " closed=" + gclosed);
					return 1;
				}))
				.then(Commands.literal("dump").then(Commands.argument("p", net.minecraft.commands.arguments.coordinates.BlockPosArgument.blockPos()).executes(c -> {
					dump(c.getSource().getLevel(), net.minecraft.commands.arguments.coordinates.BlockPosArgument.getBlockPos(c, "p"));
					return 1;
				})))));
	}

	static boolean find(ServerLevel level, BlockPos pos) {
		for (Map.Entry<Structure, it.unimi.dsi.fastutil.longs.LongSet> entry : level.structureManager().getAllStructuresAt(pos).entrySet()) {
			Identifier id = level.registryAccess().lookupOrThrow(Registries.STRUCTURE).getKey(entry.getKey());
			System.out.println("TOWNTEST saw " + id + " at " + pos);
			TownData.TownDef def = id == null ? null : TownData.town(id.getPath());
			if (def == null) continue;
			List<StructureStart> starts = new java.util.ArrayList<>();
			level.structureManager().fillStartsForStructure(entry.getKey(), entry.getValue(), starts::add);
			for (StructureStart start : starts) {
				String key = id.getPath() + "@" + start.getChunkPos().x() + "," + start.getChunkPos().z();
				town = Towns.testRegister(key, () -> new Town(id.getPath(), def, level, start.getBoundingBox(), key));
				return true;
			}
		}
		return false;
	}

	static void tick(MinecraftServer server) {
		if (town == null) return;
		town.lastVisited = town.level.getGameTime();
		if (!town.scanned || town.level.getGameTime() % 200 != 0) return;
		for (TownsfolkEntity t : Towns.residents(town)) {
			Object goal = routine(t);
			if (goal == null) continue;
			try {
				Field tf = goal.getClass().getDeclaredField("target"); tf.setAccessible(true);
				Field af = goal.getClass().getDeclaredField("activity"); af.setAccessible(true);
				BlockPos target = (BlockPos) tf.get(goal);
				Object act = af.get(goal);
				if (target == null) continue;
				samples++;
				int[] pa = perActivity.computeIfAbsent(String.valueOf(act), k -> new int[3]);
				pa[0]++;
				double dist = Math.sqrt(t.distanceToSqr(Vec3.atBottomCenterOf(target)));
				Vec3 prev = last.put(t.getId(), t.position());
				boolean busy = t.isSleeping() || t.isTrading() || t.isPassenger();
				if (dist > 4 && !busy) {
					away++;
					pa[1]++;
					if (prev != null && prev.distanceTo(t.position()) < 1.5) {
						stuck++;
						pa[2]++;
						int s = streak.merge(t.getId(), 1, Integer::sum);
						if (s == 3) {
							longStuck++;
							var path = t.getNavigation().getPath();
							System.out.println("TOWNTEST stuck30s " + t.getName().getString() + " at " + t.position() + " -> " + target + " " + act + " d=" + (int) dist
									+ " path=" + (path == null ? "null" : path.getNodeCount() + " nodes next=" + path.getNextNodeIndex() + " end=" + path.getEndNode() + " reach=" + path.canReach())
									+ " navDone=" + t.getNavigation().isDone());
							if (dumps++ < 6) dump(t.level(), t.blockPosition());
						}
					} else streak.remove(t.getId());
				} else {
					arrivedSamples++;
					streak.remove(t.getId());
				}
			} catch (Exception ex) {
				ex.printStackTrace();
			}
		}
	}

	static int dumps;

	static void dump(net.minecraft.world.level.Level level, BlockPos c) {
		StringBuilder sb = new StringBuilder("TOWNTEST dump around " + c + " (rows z, cols x; layers y-1..y+2)\n");
		Map<String, Character> legend = new java.util.LinkedHashMap<>();
		String chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
		for (int dy = -1; dy <= 2; dy++) {
			sb.append("y=").append(c.getY() + dy).append('\n');
			for (int dz = -7; dz <= 7; dz++) {
				for (int dx = -7; dx <= 7; dx++) {
					var st = level.getBlockState(c.offset(dx, dy, dz));
					char ch;
					if (st.isAir()) ch = '.';
					else {
						String id = net.minecraft.core.registries.BuiltInRegistries.BLOCK.getKey(st.getBlock()).getPath();
						if (st.hasProperty(net.minecraft.world.level.block.DoorBlock.OPEN)) id += st.getValue(net.minecraft.world.level.block.DoorBlock.OPEN) ? "(open)" : "(closed)";
						ch = legend.computeIfAbsent(id, k -> chars.charAt(Math.min(legend.size(), chars.length() - 1)));
					}
					if (dx == 0 && dz == 0) sb.append('@'); else sb.append(ch);
				}
				sb.append('\n');
			}
		}
		legend.forEach((k, v) -> sb.append(v).append('=').append(k).append(' '));
		for (int dy = -1; dy <= 2; dy++) sb.append("\n center y=" + (c.getY() + dy) + ": " + level.getBlockState(c.offset(0, dy, 0)));
		System.out.println(sb);
	}

	static Object routine(TownsfolkEntity t) {
		try {
			Field f = net.minecraft.world.entity.Mob.class.getDeclaredField("goalSelector");
			f.setAccessible(true);
			GoalSelector gs = (GoalSelector) f.get(t);
			for (WrappedGoal w : gs.getAvailableGoals()) {
				if (w.getGoal() instanceof TownRoutineGoal g) return g;
			}
		} catch (Exception e) {
			e.printStackTrace();
		}
		return null;
	}

	static String extra() {
		try {
			return "forcedArrivals=" + TownRoutineGoal.class.getField("forced").get(null) + " climbOuts=" + TownRoutineGoal.class.getField("climbs").get(null);
		} catch (Exception e) {
			return "";
		}
	}

	static void report() {
		System.out.println("TOWNTEST report residents=" + Towns.residents(town).size() + " samples=" + samples + " atTarget=" + arrivedSamples
				+ " away=" + away + " stuckSamples=" + stuck + " stuck30sEvents=" + longStuck + " " + extra());
		perActivity.forEach((k, v) -> System.out.println("TOWNTEST   " + k + " samples=" + v[0] + " away=" + v[1] + " stuck=" + v[2]));
	}
}
