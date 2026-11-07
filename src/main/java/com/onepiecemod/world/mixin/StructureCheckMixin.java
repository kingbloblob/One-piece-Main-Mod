package com.onepiecemod.world.mixin;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Mutable;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import com.llamalad7.mixinextras.injector.ModifyReturnValue;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;

import it.unimi.dsi.fastutil.longs.Long2BooleanFunction;
import it.unimi.dsi.fastutil.longs.Long2BooleanMap;
import it.unimi.dsi.fastutil.longs.Long2BooleanMaps;
import it.unimi.dsi.fastutil.longs.Long2ObjectMap;
import it.unimi.dsi.fastutil.longs.Long2ObjectMaps;
import it.unimi.dsi.fastutil.longs.LongSet;
import it.unimi.dsi.fastutil.longs.LongSets;
import it.unimi.dsi.fastutil.objects.Object2IntMap;

import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.StructureCheck;

/**
 * Makes the game's "is there a structure here?" memory safe to use from more than one thread. Sea Charts, Vivre
 * Cards and story events search for places in the background (character.Locations), so a far search never freezes
 * the server; the game's own chunk workers already touch this memory from their threads too.
 */
@Mixin(StructureCheck.class)
public abstract class StructureCheckMixin {
	@Shadow @Final @Mutable private Long2ObjectMap<Object2IntMap<Structure>> loadedChunks;
	@Shadow @Final @Mutable private Map<Structure, Long2BooleanMap> featureChecks;
	@Shadow @Final @Mutable private LongSet chunksWithoutStartsInStorage;

	@Inject(method = "<init>", at = @At("RETURN"))
	private void onepiece$threadSafe(CallbackInfo ci) {
		loadedChunks = Long2ObjectMaps.synchronize(loadedChunks);
		featureChecks = new ConcurrentHashMap<>(featureChecks);
		chunksWithoutStartsInStorage = LongSets.synchronize(chunksWithoutStartsInStorage);
	}

	/**
	 * "Could this structure start in this chunk?" is slow to work out. The synchronized map would work it out while
	 * holding its lock, so the server thread could wait a long time on a background search. Work it out outside
	 * the lock instead: two threads may then both work out the same answer, which is the same either way.
	 */
	@WrapOperation(method = "checkStart", at = @At(value = "INVOKE",
			target = "Lit/unimi/dsi/fastutil/longs/Long2BooleanMap;computeIfAbsent(JLit/unimi/dsi/fastutil/longs/Long2BooleanFunction;)Z"))
	private boolean onepiece$computeOutsideLock(Long2BooleanMap map, long key, Long2BooleanFunction compute, Operation<Boolean> original) {
		synchronized (map) {
			if (map.containsKey(key)) {
				return map.get(key);
			}
		}
		boolean result = compute.get(key);
		map.put(key, result);
		return result;
	}

	/** The per-structure memory made inside checkStart. */
	@ModifyReturnValue(method = "lambda$checkStart$0", at = @At("RETURN"))
	private static Long2BooleanMap onepiece$threadSafeChecks(Long2BooleanMap map) {
		return Long2BooleanMaps.synchronize(map);
	}
}
