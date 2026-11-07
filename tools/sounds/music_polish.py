"""
Polish pass (2026-11-03): music for moments that had none.
- storm_at_sea: sailing through a storm (rain or thunder while you're aboard a ship). Loops.
- deep_sea: swimming deep under the sea. Loops.
- sea_king: a Sea King surfaces near you. Loops.
- victory: a short brass fanfare when a boss falls (played once, not a disc).
All melodies written for this mod. Same tools as music.py.
"""
import numpy as np

from synth import (SR, Song, bell, brass, choir, crash, fft_filter, finish, hz, kick, midi, noise, pluck_bass, snare,
				   strings, synth_bass, timpani, tom)
from music import chord_notes, loop_render, pad
from music_islands import harp, play_form
from music_more import arp, bars, bass, drums
from music_shanties import check
from sfx import boom


def thunder(seed=0):
	"""A far-off thunder roll: a low boom with a crackling tail."""
	rng = np.random.default_rng(seed)
	d = 3.0
	t = np.arange(int(d * SR)) / SR
	x = boom(d, 28, 30, 1.0) * 0.8
	x += fft_filter(noise(d), 40, 400) * np.exp(-t / 0.9) * (0.6 + 0.4 * np.sin(2 * np.pi * rng.uniform(2, 4) * t))
	return x * 0.5


# ===================================================================== Storm at Sea
# Tense and driving: tremolo strings, pounding timpani, a brass call over the wind. A minor. Loops.

def storm_at_sea():
	bpm = 132
	A = ["Am", "Am", "F", "E", "Am", "Dm", "F", "E"]
	B = ["F", "G", "Em", "Am", "F", "G", "E", "E"]
	A_mel = ("A4:1 C5:1 E5:1.5 D5:0.5 C5:1 B4:1 A4:2 F5:1.5 E5:0.5 D5:1 C5:1 B4:2 G#4:2 "
			 "A4:1 C5:1 E5:1 A5:1 G5:1.5 F5:0.5 E5:1 D5:1 F5:1 E5:1 D5:1 C5:1 B4:2 E5:2")
	B_mel = ("C6:2 B5:1 A5:1 G5:2 D5:2 E5:1 G5:1 B5:1 E6:1 C6:4 "
			 "A5:1.5 G5:0.5 F5:1 A5:1 G5:1 F5:1 E5:1 D5:1 E5:1 G#5:1 B5:1 D6:1 E6:4")
	check(A_mel, 8, 4, "storm A")
	check(B_mel, 8, 4, "storm B")
	form = [("intro", ["Am", "Am", "F", "E"]), ("A", A), ("B", B), ("A2", A), ("bridge", ["Dm", "E", "Dm", "E"])]
	s = Song(bpm, bars(form) * 4)

	def part(p, cs, b0):
		for i, c in enumerate(cs):
			r = chord_notes(c, 2)[0]
			for k in range(16):  # the sea heaving: tremolo strings on the root
				s.add(b0 + i * 4 + k * 0.25, strings(hz(r + (12 if k % 8 >= 4 else 0)), 0.22 * s.spb, 0.8), 0.75)
			s.add(b0 + i * 4, timpani(hz(r), 0.9, 1.0), 0.75)
			s.add(b0 + i * 4 + 2.5, timpani(hz(r), 0.5, 0.7), 0.55)
		drums(s, b0, len(cs), 4, [(lambda: kick(0.8), (0, 2), 0.5), (lambda: snare(0.6, 0.15), (1, 3), 0.35)])
		if p == "intro":
			s.add(b0, thunder(1), 0.8)
			pad(s, b0, cs, 4, choir, 0.55, octave=3, vowel="oo")
		elif p == "A":
			s.add(b0, crash(), 0.6)
			s.line(b0, A_mel, brass, 0.7)
			pad(s, b0, cs, 4, strings, 0.4, octave=3)
		elif p == "B":
			s.add(b0, thunder(2), 0.6)
			s.line(b0, B_mel, strings, 0.8)
			s.line(b0, B_mel, brass, 0.35, transpose=-12)
			pad(s, b0, cs, 4, choir, 0.55, octave=3)
		elif p == "A2":
			s.add(b0, crash(), 0.7)
			s.line(b0, A_mel, brass, 0.7)
			s.line(b0, A_mel, strings, 0.4, transpose=12)
		elif p == "bridge":
			s.add(b0, thunder(3), 0.7)
			pad(s, b0, cs, 4, brass, 0.55, octave=3)
	play_form(s, form, 4, part)
	return finish(loop_render(s, 0.22, 1.8, 0.6))


# ===================================================================== The Deep
# Dark, slow and floating: rippling harp, soft choir, distant whale calls and rising bubbles. D minor. Loops.

def whale(f0, f1, d):
	n = int(d * SR)
	t = np.arange(n) / SR
	f = f0 * (f1 / f0) ** (t / d) * (1 + 0.01 * np.sin(2 * np.pi * 5 * t))
	ph = 2 * np.pi * np.cumsum(f) / SR
	x = (np.sin(ph) + 0.3 * np.sin(2 * ph)) * np.sin(np.pi * t / d) ** 1.5
	return fft_filter(x, 60, 1500) * 0.3


def deep_sea():
	bpm = 66
	A = ["Dm", "Bb", "Gm", "A", "Dm", "F", "Gm", "A"]
	A_mel = "A4:4 F4:2 G4:2 A4:3 C5:1 D5:4 E5:2 D5:2 C5:2 A4:2 Bb4:4 A4:4"
	check(A_mel, 8, 4, "deep A")
	form = [("intro", ["Dm", "Dm", "Bb", "A"]), ("A", A), ("A2", A), ("outro", ["Gm", "A", "Dm", "Dm"])]
	s = Song(bpm, bars(form) * 4)
	rng = np.random.default_rng(21)

	def part(p, cs, b0):
		arp(s, b0, cs, 4, (0, 1, 2, 4, 3, 2, 1, 2), 0.5, harp, 0.35, octave=3)
		bass(s, b0, cs, 4, [(0, 0, 3.8)], inst=synth_bass, gain=0.4)
		pad(s, b0, cs, 4, choir, 0.45, octave=3, vowel="oo")
		for i in range(len(cs)):  # bubbles drifting up
			for _ in range(2):
				s.add(b0 + i * 4 + rng.uniform(0, 4), bell(rng.uniform(1800, 3200), 0.08, 0.5, decay=0.12), 0.25)
		if p == "intro":
			s.add(b0 + 4, whale(220, 140, 3.5), 0.8)
		elif p == "A":
			s.line(b0, A_mel, choir, 0.55, vowel="oo")
		elif p == "A2":
			s.line(b0, A_mel, bell, 0.3, transpose=12)
			s.line(b0, A_mel, strings, 0.4)
			s.add(b0 + 16, whale(180, 260, 3.0), 0.7)
		elif p == "outro":
			s.add(b0 + 2, whale(200, 110, 4.0), 0.7)
	play_form(s, form, 4, part)
	return finish(loop_render(s, 0.35, 2.6, 0.9))


# ===================================================================== Sea King
# Something huge under the boat: a slow heartbeat on the drums, low brass and a looming choir. C minor. Loops.

def sea_king():
	bpm = 100
	A = ["Cm", "Cm", "Ab", "G", "Cm", "Fm", "Ab", "G"]
	B = ["Fm", "Cm", "Ab", "G", "Fm", "Cm", "Db", "G"]
	A_mel = "C4:2 Eb4:1 G4:1 F4:2 Eb4:2 Ab4:2 G4:1 F4:1 G4:4 C5:2 Bb4:1 Ab4:1 G4:2 F4:1 Eb4:1 F4:2 Ab4:2 G4:4"
	B_mel = "F5:4 Eb5:4 C5:4 G4:4 Ab4:2 C5:2 F5:4 Db5:4 D5:4"
	check(A_mel, 8, 4, "sea king A")
	check(B_mel, 8, 4, "sea king B")
	form = [("intro", ["Cm", "Cm", "Ab", "G"]), ("A", A), ("B", B), ("A2", A)]
	s = Song(bpm, bars(form) * 4)

	def part(p, cs, b0):
		bass(s, b0, cs, 4, [(0, 0, 0.9), (1, 0, 0.4), (1.5, 7, 0.4), (2, 0, 0.9), (3, 6, 0.4), (3.5, 7, 0.4)],
			 inst=synth_bass, octave=2, gain=0.7)
		for i, c in enumerate(cs):
			r = chord_notes(c, 2)[0]
			s.add(b0 + i * 4, timpani(hz(r), 0.6, 1.0), 0.8)  # the heartbeat: thump-thump
			s.add(b0 + i * 4 + 0.45, timpani(hz(r), 0.4, 0.7), 0.6)
			if i % 2 == 1:
				s.add(b0 + i * 4 + 3, tom(110, 0.8), 0.5)
				s.add(b0 + i * 4 + 3.5, tom(85, 0.9), 0.5)
		if p == "intro":
			pad(s, b0, cs, 4, strings, 0.5, octave=2)
		elif p == "A":
			s.add(b0, crash(), 0.5)
			s.line(b0, A_mel, brass, 0.8)
			pad(s, b0, cs, 4, strings, 0.4, octave=3)
		elif p == "B":
			s.add(b0, crash(), 0.6)
			s.line(b0, B_mel, choir, 0.8)
			s.line(b0, B_mel, brass, 0.45, transpose=-12)
			drums(s, b0, len(cs), 4, [(lambda: snare(0.7), (1, 3), 0.35)])
		elif p == "A2":
			s.add(b0, crash(), 0.7)
			s.line(b0, A_mel, brass, 0.8)
			s.line(b0, A_mel, choir, 0.5, transpose=12)
			pad(s, b0, cs, 4, choir, 0.45, octave=3)
	play_form(s, form, 4, part)
	return finish(loop_render(s, 0.24, 2.0, 0.7))


# ===================================================================== Victory fanfare (stinger)
# A short, bright brass fanfare in C when a boss falls.

def victory():
	s = Song(120, 10)
	s.line(0, "G4:0.33 G4:0.33 G4:0.34 C5:1.5 E5:0.5 G5:1 E5:0.5 G5:0.5 C6:4", brass, 0.9)
	s.line(0, "E4:0.33 E4:0.33 E4:0.34 G4:1.5 C5:0.5 E5:1 C5:0.5 E5:0.5 G5:4", brass, 0.5)
	s.chord(1, "C3 G3 C4 E4", 2.0, strings, 0.7)
	s.chord(3, "F3 A3 C4 F4", 1.0, strings, 0.7)
	s.chord(4, "C3 G3 C4 E4 G4", 4.0, strings, 0.8)
	for k in range(8):
		s.add(3 + k * 0.125, timpani(hz(midi("G2")), 0.12, 0.3 + k * 0.08), 0.7)
	s.add(4, timpani(hz(midi("C2")), 1.0, 1.0), 0.9)
	s.add(4, crash(), 0.7)
	s.add(4, bell(hz(midi("C6")), 1.5, 0.7), 0.4)
	return finish(s.render(0.28, 2.0, 0.7, tail=2.0))


SONGS = {
	"storm_at_sea": storm_at_sea,
	"deep_sea": deep_sea,
	"sea_king": sea_king,
}
ALL = dict(SONGS)
