package com.onepiecemod.character.client;

import java.util.HashMap;
import java.util.Map;

import com.mojang.blaze3d.vertex.PoseStack;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.HumanoidMobRenderer;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;

import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.character.CharacterEntity;
import com.onepiecemod.client.RenderGuard;
import com.onepiecemod.mesh.client.MeshForms;
import net.minecraft.client.renderer.texture.OverlayTexture;

/**
 * Draws a character as a player-shaped mob, with the skin
 * assets/onepiece/textures/entity/character/<id>.png (a normal 64x64 Minecraft skin).
 * Giants (see GiantModels) get their own bulkier model and a 128x128 skin. Characters listed in
 * CharacterSkinFormats have full player skins (3D outer layer, slim arms for some) and use the player model shape.
 */
public class CharacterRenderer extends HumanoidMobRenderer<CharacterEntity, CharacterRenderer.State, HumanoidModel<CharacterRenderer.State>> {
	/** What the renderer needs to know about the mob this frame. */
	public static class State extends HumanoidRenderState {
		public String characterId = "luffy";
		/** Monster form (Kaido's dragon...), or "" to draw the person. */
		public String form = "";
		public float formAge = -1;
		/** 0 to 1 while an attack plays, otherwise -1. */
		public float formAttack = -1;
	}

	@Override
	public void submit(State state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
		// A boss in its monster form is drawn as the monster (BossForms), not as a person.
		if (!state.form.isEmpty() && BossForms.submit(state, poseStack, collector)) {
			return;
		}
		// A few characters (Loki) have a smooth-mesh look instead of a skin on cubes.
		MeshForms.Mesh look = MeshForms.get("character/" + state.characterId);
		if (look != null) {
			if (!state.isInvisible) {
				MeshForms.Input in = BossForms.input(state, false);
				in.attack = state.swingAnimation > 0 ? state.swingAnimation : -1;
				in.formAge = -1;
				RenderGuard.run("character mesh " + state.characterId, poseStack, () -> MeshForms.submit(look, in, poseStack, collector,
						state.bodyRot, state.scale / look.scale(), state.deathTime, state.lightCoords,
						OverlayTexture.pack(OverlayTexture.u(0.0f), OverlayTexture.v(state.hasRedOverlay))));
			}
			if (state.nameTag != null) {
				submitNameDisplay(state, poseStack, collector, camera);
			}
			return;
		}
		super.submit(state, poseStack, collector, camera);
	}

	public CharacterRenderer(EntityRendererProvider.Context context) {
		// The zombie model is the same shape as a player and uses the same skin layout.
		super(context, new HumanoidModel<>(context.bakeLayer(ModelLayers.ZOMBIE)), 0.5f);
		this.normalModel = this.model;
		this.wideModel = new HumanoidModel<>(context.bakeLayer(WIDE_LAYER));
		this.slimModel = new HumanoidModel<>(context.bakeLayer(SLIM_LAYER));
		for (String id : GiantModels.IDS) {
			giantModels.put(id, new GiantModel(context.bakeLayer(GiantModels.layer(id)), id));
		}
	}

	/** Player-shaped models with the 3D outer layer, for characters with player-layout skins (CharacterSkinFormats). */
	public static final ModelLayerLocation WIDE_LAYER = new ModelLayerLocation(OnePieceMod.id("character_wide"), "main");
	public static final ModelLayerLocation SLIM_LAYER = new ModelLayerLocation(OnePieceMod.id("character_slim"), "main");

	/** Registers the two player-shaped layers. CharacterClient calls this. */
	public static void registerLayers() {
		ModelLayerRegistry.registerModelLayer(WIDE_LAYER, () -> LayerDefinition.create(PlayerModel.createMesh(CubeDeformation.NONE, false), 64, 64));
		ModelLayerRegistry.registerModelLayer(SLIM_LAYER, () -> LayerDefinition.create(PlayerModel.createMesh(CubeDeformation.NONE, true), 64, 64));
	}

	private final HumanoidModel<State> normalModel;
	private final HumanoidModel<State> wideModel;
	private final HumanoidModel<State> slimModel;
	private final Map<String, HumanoidModel<State>> giantModels = new HashMap<>();

	@Override
	protected RenderType getRenderType(State state, boolean bodyVisible, boolean translucent, boolean glowing) {
		// Pick this character's model (one renderer draws every character). This has to happen here and not in
		// submit(): the parent class's submit() puts the normal model back first, then calls this just before drawing.
		this.model = modelFor(state.characterId);
		return super.getRenderType(state, bodyVisible, translucent, glowing);
	}

	private HumanoidModel<State> modelFor(String id) {
		HumanoidModel<State> giant = giantModels.get(id);
		if (giant != null) {
			return giant;
		}
		if (CharacterSkinFormats.SLIM.contains(id)) {
			return slimModel;
		}
		return CharacterSkinFormats.WIDE.contains(id) ? wideModel : normalModel;
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(CharacterEntity entity, State state, float partialTick) {
		super.extractRenderState(entity, state, partialTick);
		state.characterId = entity.getCharacterId();
		state.form = entity.getForm();
		if (!state.form.isEmpty()) {
			state.formAge = entity.getFormAge() + partialTick;
			float swing = entity.getSwingAnimation(partialTick);
			state.formAttack = swing > 0 ? swing : -1;
		}
		// Quest givers: "!" (a job for you), grey "?" (waiting on you) or gold "?" (ready to hand in) above the name.
		Component marker = QuestMarkerClient.markerFor(entity.getId());
		if (marker != null && state.nameTag != null) {
			state.scoreText = state.nameTag;
			state.nameTag = marker;
		}
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return OnePieceMod.id("textures/entity/character/" + state.characterId + ".png");
	}
}
