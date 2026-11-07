"""
2026-11-05: six more boss battle themes (each loops, each has a music disc): one for each Emperor who fights you
(Whitebeard, Big Mom, Kaido, Blackbeard), one for the Five Elders and one for the Worst Generation rivals.
Which boss plays which: source/.../sound/BossMusic.java. All melodies written for this mod.
"""
import numpy as np

from synth import (SR, Song, accordion, bell, brass, choir, crash, fiddle, finish, hat, hz, kick, midi, piano,
				   pluck_bass, snare, strings, synth_bass, tambourine, timpani, tom, whistle)
from music import chord_notes, loop_render, pad
from music_islands import harp, play_form
from music_more import bass, bars, chain, chip, drums, music_box, organ, strum
from music_isles import mel
from music_shanties import check
from sfx import boom


def battle(name, bpm, A, B, A_mel, B_mel, *, lead, lead_b, layer, beat, intro, bridge_cs, pad_inst=strings,
		   pad_b=choir, lead_gain=0.75, b_gain=0.7, extra=None, wet=(0.18, 1.6, 0.5)):
	"""Loop form: intro, A, B, A again (doubled an octave up), bridge. layer/beat/extra(s, b0, cs, part)."""
	check(A_mel, len(A), 4, name + " A")
	check(B_mel, len(B), 4, name + " B")
	form = [("intro", A[:4]), ("A", A), ("B", B), ("A2", A), ("bridge", bridge_cs)]
	s = Song(bpm, bars(form) * 4)

	def part(p, cs, b0):
		layer(s, b0, cs, p)
		beat(s, b0, cs, p)
		if p in ("intro", "A", "B", "A2"):
			s.add(b0, crash(), 0.7)
		if p == "intro":
			pad(s, b0, cs, 4, pad_inst, 0.5, octave=3)
			s.line(b0, intro, lead, lead_gain * 0.8)
		elif p == "A":
			s.line(b0, A_mel, lead, lead_gain)
			pad(s, b0, cs, 4, pad_inst, 0.45, octave=3)
		elif p == "B":
			s.line(b0, B_mel, lead_b, b_gain)
			s.line(b0, B_mel, lead, lead_gain * 0.35, transpose=-12)
			pad(s, b0, cs, 4, pad_b, 0.55, octave=3)
		elif p == "A2":
			s.line(b0, A_mel, lead, lead_gain)
			s.line(b0, A_mel, lead_b, b_gain * 0.5, transpose=12)
			pad(s, b0, cs, 4, pad_b, 0.45, octave=3)
		elif p == "bridge":
			pad(s, b0, cs, 4, brass, 0.55, octave=3)
			for i, c in enumerate(cs):
				s.add(b0 + i * 4, timpani(hz(chord_notes(c, 2)[0]), 1.0, 1.0), 0.8)
		if extra:
			extra(s, b0, cs, p)
	play_form(s, form, 4, part)
	return finish(loop_render(s, *wet))


def rock_beat(s, b0, cs, kicks=(0, 1.5, 2), snares=(1, 3), hats=8, last_fill=True):
	drums(s, b0, len(cs), 4, [(lambda: kick(0.9), kicks, 0.75), (lambda: snare(0.85), snares, 0.65),
							  (lambda: hat(0.55), tuple(k * 4 / hats for k in range(hats)), 0.4)])
	if last_fill:
		i = len(cs) - 1
		for k, f in enumerate((210, 170, 140, 110)):
			s.add(b0 + i * 4 + 3 + k * 0.25, tom(f, 0.9), 0.55)


def ostinato(s, b0, cs, steps, inst=strings, octave=2, gain=1.0, per=0.5, length=0.42):
	for i, c in enumerate(cs):
		r = chord_notes(c, octave)[0]
		for k, st in enumerate(steps):
			s.add(b0 + i * 4 + k * per, inst(hz(r + st), length * s.spb, 0.9), gain)


# ===================================================================== Father of the Seas (Whitebeard)
# Huge and heroic: brass and choir over pounding timpani, and the sea itself cracking on the downbeats. E minor.

def whitebeard_battle():
	def layer(s, b0, cs, p):
		ostinato(s, b0, cs, [0, 12, 0, 7, 0, 12, 0, 10])

	def beat(s, b0, cs, p):
		rock_beat(s, b0, cs, kicks=(0, 2, 2.5), hats=4)
		for i, c in enumerate(cs):
			s.add(b0 + i * 4, timpani(hz(chord_notes(c, 2)[0]), 0.8, 1.0), 0.55)

	def extra(s, b0, cs, p):
		if p in ("A", "A2"):  # the quake: the air itself cracks
			for i in (0, 4):
				s.add(b0 + i * 4, boom(1.2, 34, 60, 1.0), 0.45)

	return battle("whitebeard", 136,
		["Em", "C", "D", "B", "Em", "C", "Am", "B"], ["C", "D", "Em", "Em", "C", "D", "B", "B"],
		mel("E5:1.5 B4:0.5 E5:1 G5:1", "G5:1.5 E5:0.5 C6:2", "A5:1 F#5:1 D5:1 F#5:1", "B5:3 r:1",
			"E5:1 G5:1 B5:1 E6:1", "E6:1.5 D6:0.5 C6:2", "A5:1 B5:1 C6:1 E6:1", "D#6:4"),
		mel("G5:2 E5:1 G5:1", "A5:2 F#5:2", "G5:1 A5:1 B5:2", "E5:4",
			"C6:1.5 B5:0.5 A5:1 G5:1", "A5:1 B5:1 D6:2", "F#6:2 D#6:2", "B5:4"),
		lead=brass, lead_b=choir, layer=layer, beat=beat, extra=extra, intro="E4:4 G4:4 F#4:4 B4:4",
		bridge_cs=["C", "D", "C", "B"], b_gain=0.85)


# ===================================================================== Sweet Tyrant (Big Mom)
# A carnival gone wrong: a music box and organ oom-pah, then the brass comes in hungry. C minor.

def big_mom_battle():
	def layer(s, b0, cs, p):
		for i, c in enumerate(cs):
			n = chord_notes(c, 3)
			r = n[0]
			for k in range(4):  # oom-pah
				if k % 2 == 0:
					s.add(b0 + i * 4 + k, pluck_bass(hz(r - 12 + (7 if k == 2 else 0)), 0.8 * s.spb, 0.9), 0.65)
				else:
					s.chord(b0 + i * 4 + k, " ".join(_n(m + 12) for m in n), 0.45 * s.spb, organ, 0.55)
			for k in range(8):  # the music box, sweet and creepy
				s.add(b0 + i * 4 + k * 0.5, music_box(hz(n[k % 3] + 24 + (12 if k == 7 else 0)), 0.3, 0.6), 0.22)

	def beat(s, b0, cs, p):
		if p != "intro":
			rock_beat(s, b0, cs, kicks=(0, 2), snares=(1, 3), hats=8)

	def extra(s, b0, cs, p):
		if p == "B":
			for i in range(len(cs)):
				s.add(b0 + i * 4 + 3, tambourine(0.6), 0.4)

	return battle("big mom", 144,
		["Cm", "G", "Cm", "G", "Ab", "Eb", "F", "G"], ["Fm", "Cm", "G", "Cm", "Fm", "Cm", "D", "G"],
		mel("G5:1 C6:1 Eb6:1 C6:1", "B5:1 D6:1 F6:1 D6:1", "Eb6:1 D6:1 C6:1 G5:1", "B5:4",
			"C6:1 Ab5:1 Eb5:1 Ab5:1", "G5:1 Eb5:1 Bb4:1 Eb5:1", "F5:1 A5:1 C6:1 Eb6:1", "D6:4"),
		mel("Ab5:2 F5:2", "G5:2 Eb5:2", "D5:1 F5:1 B5:2", "C6:4",
			"C6:2 Ab5:2", "G5:1 Eb5:1 C6:2", "A5:1 C6:1 F#6:2", "G6:4"),
		lead=music_box, lead_b=brass, layer=layer, beat=beat, extra=extra, intro="G5:4 B5:4 C6:4 D6:4",
		bridge_cs=["Ab", "G", "Ab", "G"], lead_gain=0.8, pad_inst=organ)


def _n(m):
	from music import name_of
	return name_of(m)


# ===================================================================== The Strongest Creature (Kaido and his All-Stars)
# Thundering taiko, a fast plucked shamisen and a roaring brass line. A minor.

def kaido_battle():
	def layer(s, b0, cs, p):
		for i, c in enumerate(cs):
			r = chord_notes(c, 4)[0]
			for k, st in enumerate([0, 12, 7, 12, 0, 12, 10, 7]):
				s.add(b0 + i * 4 + k * 0.5, harp(hz(r + st), 0.35 * s.spb, 0.9), 0.5)
		bass(s, b0, cs, 4, [(k * 0.5, [0, 0, 12, 0, 0, 7, 12, 0][k], 0.45) for k in range(8)], inst=synth_bass, gain=0.6)

	def beat(s, b0, cs, p):
		for i in range(len(cs)):
			s.add(b0 + i * 4, timpani(hz(midi("A1")), 1.0, 1.0), 0.8)  # taiko
			s.add(b0 + i * 4 + 1.5, timpani(hz(midi("A1")), 0.6, 0.8), 0.6)
			s.add(b0 + i * 4 + 2, timpani(hz(midi("E2")), 0.8, 0.9), 0.7)
			s.add(b0 + i * 4 + 1, snare(0.8), 0.5)
			s.add(b0 + i * 4 + 3, snare(0.8), 0.5)
			for k in range(8):
				s.add(b0 + i * 4 + k * 0.5, hat(0.45), 0.3)
		for k in range(8):  # the drum roll into each part
			s.add(b0 + len(cs) * 4 - 2 + k * 0.25, tom(hz(midi("A2")) * (1 + k * 0.05), 0.5 + k * 0.06), 0.45)

	def extra(s, b0, cs, p):
		if p == "bridge":  # the dragon's roar
			s.add(b0, brass(hz(midi("A2")), 3.5, 1.0, vib=0.03), 0.7)
			s.add(b0, brass(hz(midi("E3")), 3.5, 0.8, vib=0.03), 0.5)

	return battle("kaido", 148,
		["Am", "F", "G", "Am", "Am", "F", "E", "E"], ["Dm", "Am", "F", "E", "Dm", "Am", "Bb", "E"],
		mel("A4:1 C5:1 E5:1 A5:1", "F5:2 E5:1 C5:1", "D5:1 B4:1 G5:2", "A5:4",
			"C6:1 B5:1 A5:1 E5:1", "F5:1 A5:1 C6:2", "B5:1 G#5:1 E5:2", "E5:4"),
		mel("D6:2 F5:2", "E5:1 A5:1 C6:2", "A5:1 C6:1 F6:2", "E6:4",
			"D6:1 C6:1 A5:2", "E5:1 A5:1 C6:2", "D6:1 Bb5:1 F5:2", "G#5:4"),
		lead=brass, lead_b=whistle, layer=layer, beat=beat, extra=extra, intro="A4:4 C5:4 B4:4 A4:4",
		bridge_cs=["F", "E", "F", "E"], b_gain=0.75)


# ===================================================================== Darkness Rising (Blackbeard)
# Greedy, chaotic and laughing: church organ, a dirty synth bass and a brass line that slides into darkness. Bb minor.

def blackbeard_battle():
	def layer(s, b0, cs, p):
		bass(s, b0, cs, 4, [(k * 0.5, [0, 12, 0, 0, 13, 0, 12, 7][k], 0.45) for k in range(8)], inst=synth_bass, gain=0.75)
		pad(s, b0, cs, 4, organ, 0.4, octave=4)

	def beat(s, b0, cs, p):
		rock_beat(s, b0, cs, kicks=(0, 0.75, 2, 2.75), snares=(1, 3), hats=8)

	def extra(s, b0, cs, p):
		if p in ("A2", "bridge"):  # the dark pulls everything in
			for i in range(0, len(cs), 4):
				x = np.sin(2 * np.pi * np.cumsum(np.linspace(220, 40, int(2.0 * SR))) / SR) * np.linspace(0, 1, int(2.0 * SR)) ** 2
				s.add(b0 + i * 4 + 2, x * 0.5, 0.4)

	return battle("blackbeard", 128,
		["Bbm", "Gb", "Ebm", "F", "Bbm", "Gb", "Cdim", "F"], ["Gb", "Ab", "Bbm", "Bbm", "Gb", "Ab", "F", "F"],
		mel("Bb4:1 Db5:1 F5:1 Bb5:1", "Bb5:1 Ab5:1 Gb5:2", "Eb5:1 Gb5:1 Bb5:2", "A5:4",
			"Db6:1 C6:1 Bb5:1 F5:1", "Gb5:1 Bb5:1 Db6:2", "C6:1 Eb6:1 Gb6:2", "F6:4"),
		mel("Db6:2 Bb5:2", "C6:2 Ab5:2", "Bb5:1 Db6:1 F6:2", "Bb5:4",
			"Gb5:1 Bb5:1 Db6:2", "Eb6:1 C6:1 Ab5:2", "A5:1 C6:1 F6:2", "F5:4"),
		lead=brass, lead_b=fiddle, layer=layer, beat=beat, extra=extra, intro="F4:4 Gb4:4 F4:4 A4:4",
		bridge_cs=["Gb", "F", "Gb", "F"], pad_inst=choir, pad_b=organ)


# ===================================================================== Five Elders (the Elder Stars)
# Cold and holy and far too powerful: choir, organ and tolling bells over slow, crushing drums. F# minor.

def elder_star_battle():
	def layer(s, b0, cs, p):
		ostinato(s, b0, cs, [0, 0, 12, 0, 7, 0, 12, 7, 0, 0, 12, 0, 7, 12, 7, 0], per=0.25, length=0.22, gain=0.8)
		for i, c in enumerate(cs):
			s.add(b0 + i * 4, bell(hz(chord_notes(c, 3)[0] + 24), 2.5, 0.8), 0.25)

	def beat(s, b0, cs, p):
		for i, c in enumerate(cs):
			r = chord_notes(c, 2)[0]
			s.add(b0 + i * 4, timpani(hz(r), 1.0, 1.0), 0.8)
			s.add(b0 + i * 4 + 2.5, timpani(hz(r + 7 - 12), 0.6, 0.8), 0.6)
			s.add(b0 + i * 4, kick(0.9), 0.6)
			s.add(b0 + i * 4 + 2, snare(0.9), 0.55)

	return battle("elder stars", 108,
		["F#m", "D", "E", "C#", "F#m", "D", "Bm", "C#"], ["D", "E", "F#m", "F#m", "D", "E", "C#", "C#"],
		mel("F#5:2 A5:1 C#6:1", "D6:2 A5:2", "B5:1 G#5:1 E5:2", "C#6:4",
			"F#5:1 A5:1 C#6:1 F#6:1", "F#6:1 E6:1 D6:2", "B5:1 D6:1 F#5:2", "F5:4"),
		mel("A5:2 F#5:2", "G#5:1 B5:1 E6:2", "C#6:1 A5:1 F#5:2", "F#5:4",
			"D6:1 C#6:1 A5:2", "B5:1 G#5:1 E6:2", "G#6:2 F6:2", "C#6:4"),
		lead=choir, lead_b=brass, layer=layer, beat=beat, intro="C#5:4 D5:4 B4:4 C#5:4",
		bridge_cs=["D", "C#", "D", "C#"], pad_inst=organ, pad_b=organ, lead_gain=0.9, wet=(0.28, 2.4, 0.9))


# ===================================================================== Worst Generation (rival Supernovas)
# Young, loud and reckless: a fast rock beat, a growling bass, fiddle and brass trading the lead. B minor.

def supernova_battle():
	def layer(s, b0, cs, p):
		bass(s, b0, cs, 4, [(k * 0.5, [0, 0, 12, 0, 0, 12, 10, 7][k], 0.4) for k in range(8)], inst=synth_bass, gain=0.75)
		strum(s, b0, cs, 4, (0, 0.75, 1.5, 2.5, 3.25), brass, 0.25, octave=3, ln=0.3)

	def beat(s, b0, cs, p):
		rock_beat(s, b0, cs, kicks=(0, 0.75, 1.5, 2, 2.75), snares=(1, 3), hats=8)

	return battle("worst generation", 160,
		["Bm", "G", "D", "A", "Bm", "G", "Em", "F#"], ["G", "A", "Bm", "Bm", "G", "A", "F#", "F#"],
		mel("B4:0.5 D5:0.5 F#5:1 B5:1 A5:1", "G5:1 B5:1 D6:2", "D6:1 C#6:1 A5:2", "C#6:3 r:1",
			"B5:1 F#5:1 D5:1 F#5:1", "G5:1 B5:1 E6:2", "E6:1 D6:1 B5:1 G5:1", "F#5:4"),
		mel("D6:2 B5:2", "C#6:2 A5:2", "B5:1 D6:1 F#6:2", "B5:4",
			"G5:1 B5:1 D6:2", "E6:1 C#6:1 A5:2", "A#5:1 C#6:1 F#6:2", "F#5:4"),
		lead=fiddle, lead_b=brass, layer=layer, beat=beat, intro="F#4:4 G4:4 A4:4 C#5:4",
		bridge_cs=["G", "F#", "G", "F#"], lead_gain=0.85)


BOSSES = {
	"whitebeard_battle": whitebeard_battle,
	"big_mom_battle": big_mom_battle,
	"kaido_battle": kaido_battle,
	"blackbeard_battle": blackbeard_battle,
	"elder_star_battle": elder_star_battle,
	"supernova_battle": supernova_battle,
}
ALL = dict(BOSSES)
