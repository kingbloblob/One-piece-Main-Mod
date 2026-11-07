package com.onepiecemod.career.client;

import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.Identifier;

import com.onepiecemod.OnePieceMod;
import com.onepiecemod.career.CareerAllyEntity;
import com.onepiecemod.npc.client.NpcRenderer;

/**
 * Draws backup soldiers. Marines wear normal Marine NPC skins; Revolutionaries wear their own,
 * from textures/entity/career/ (painted by tools/careers/gen_career_skins.py).
 */
public class CareerAllyRenderer extends NpcRenderer<CareerAllyEntity> {
	public CareerAllyRenderer(EntityRendererProvider.Context context) {
		super(context);
	}

	@Override
	public void extractRenderState(CareerAllyEntity entity, State state, float partialTick) {
		super.extractRenderState(entity, state, partialTick);
		String skin = entity.getCareerSkin();
		if (skin.startsWith("rev_")) {
			state.skin = skin;
		}
	}

	@Override
	public Identifier getTextureLocation(State state) {
		if (state.skin.startsWith("rev_")) {
			return OnePieceMod.id("textures/entity/career/" + state.skin + ".png");
		}
		return super.getTextureLocation(state);
	}
}
