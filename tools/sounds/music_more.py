"""
More island themes (so most islands sound like themselves) and three more boss themes
(Admirals, Warlords, and the final enemies). All melodies written for this mod. Same tools as music.py.
"""
import numpy as np

from synth import (SR, Song, accordion, bell, brass, choir, crash, env, fft_filter, fiddle, finish, hat, hz, kick,
				   midi, noise, piano, pluck_bass, snare, strings, synth_bass, tambourine, timpani, tom, whistle)
from music import chord_notes, loop_render, pad
from music_islands import harp, marimba, play_form
from music_shanties import check, chord


# ------------------------------------------------------------------ extra instruments

def organ(f, d, v=1.0):
	n = int((d + 0.12) * SR)
	t = np.arange(n) / SR
	x = np.zeros(n)
	for k, a in ((0.5, 0.5), (1, 1.0), (2, 0.6), (3, 0.35), (4, 0.3), (6, 0.15), (8, 0.12)):
		if f * k < 9000:
			x += a * np.sin(2 * np.pi * f * k * t)
	x *= 1 + 0.08 * np.sin(2 * np.pi * 6.2 * t)  # a slow rotating-speaker wobble
	return x * env(n, 0.03, 0.1, 0.9, 0.12, hold=d) * v * 0.1


def chip(f, d, v=1.0):
	"""A bright square-wave synth, for Egghead's lab computers."""
	n = int((d + 0.05) * SR)
	t = np.arange(n) / SR
	x = np.zeros(n)
	for k in range(1, 16, 2):
		if f * k < 12000:
			x += np.sin(2 * np.pi * f * k * t) / k
	return x * env(n, 0.004, 0.08, 0.6, 0.04, hold=d) * v * 0.16


def music_box(f, d, v=1.0):
	return bell(f, d, v, decay=0.45)


def clap(v=1.0):
	d = 0.2
	t = np.arange(int(d * SR)) / SR
	e = sum(np.exp(-np.clip(t - o, 0, None) / 0.006) * (t >= o) for o in (0, 0.01, 0.022)) + np.exp(-t / 0.05) * 0.6
	return fft_filter(noise(d), 900, 7000) * e * v * 0.4


def chain(v=1.0, seed=0):
	"""A distant chain rattle: a few small metal clinks."""
	rng = np.random.default_rng(seed)
	buf = np.zeros(int(0.6 * SR))
	for i in range(6):
		f = rng.uniform(1800, 3200)
		n = int(0.12 * SR)
		t = np.arange(n) / SR
		x = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t)) * np.exp(-t / 0.03)
		i0 = int((i * 0.08 + rng.uniform(0, 0.03)) * SR)
		buf[i0:i0 + n] += x[: len(buf) - i0] * rng.uniform(0.4, 1.0)
	return fft_filter(buf, 600, 8000) * v * 0.25


# ------------------------------------------------------------------ helpers

def bass(s, b0, cs, per, steps, inst=pluck_bass, octave=2, gain=0.65):
	"""steps: (beat, semitones above the root, length in beats) for each bar."""
	for i, c in enumerate(cs):
		r = chord_notes(c, octave)[0]
		for at, step, ln in steps:
			s.add(b0 + i * per + at, inst(hz(r + step), ln * s.spb, 0.8), gain)


def strum(s, b0, cs, per, offs, inst, gain, octave=4, ln=0.4):
	for i, c in enumerate(cs):
		for at in offs:
			chord(s, b0 + i * per + at, c, ln * s.spb, inst, gain, octave=octave)


def arp(s, b0, cs, per, order, step, inst, gain, octave=4, ln=None):
	for i, c in enumerate(cs):
		n = chord_notes(c, octave)
		tones = [n[0], n[1], n[2], n[0] + 12, n[1] + 12, n[2] + 12]
		for k, idx in enumerate(order):
			s.add(b0 + i * per + k * step, inst(hz(tones[idx]), (ln or step) * s.spb, 0.7), gain)


def drums(s, b0, bars, per, hits):
	"""hits: (sound function, beats within the bar, gain)."""
	for i in range(bars):
		for fn, beats, g in hits:
			for at in beats:
				s.add(b0 + i * per + at, fn(), g)


def bars(form):
	return sum(len(c) for _, c in form)


# ===================================================================== East Blue (home seas)
# Gentle and warm, like the first morning at sea: accordion, whistle and a soft harp, G major.

def east_blue():
	bpm = 92
	A = ["G", "D", "Em", "C", "G", "D", "C", "D"]
	B = ["C", "G", "Am", "Em", "C", "G", "Am", "D"]
	A_mel = "B4:1 D5:1 G5:1.5 F#5:0.5 E5:1 D5:1 B4:2 E5:1 F#5:1 G5:1 B5:1 A5:3 G5:1 B5:1.5 A5:0.5 G5:1 D5:1 E5:1 F#5:1 A5:2 G5:1 E5:1 C5:1 E5:1 D5:4"
	B_mel = "E5:2 G5:1 C6:1 B5:2 G5:2 A5:1 B5:1 C6:1 E6:1 B5:4 C6:1.5 B5:0.5 A5:1 G5:1 D5:1 G5:1 B5:2 C6:1 B5:1 A5:1 G5:1 F#5:2 A5:2"
	check(A_mel, 8, 4, "east blue A")
	check(B_mel, 8, 4, "east blue B")
	form = [("intro", ["G", "C", "G", "D"]), ("A", A), ("B", B), ("A2", A), ("outro", ["C", "D", "G", "G"])]
	s = Song(bpm, bars(form) * 4)

	def part(p, cs, b0):
		bass(s, b0, cs, 4, [(0, 0, 1.5), (2, 7, 1.5)])
		strum(s, b0, cs, 4, (1, 2.5, 3), harp, 0.4)
		if p == "intro":
			pad(s, b0, cs, 4, accordion, 0.35, octave=4)
			s.line(b0, "D5:4 E5:4 D5:4 F#5:4", whistle, 0.4)
		elif p == "A":
			s.line(b0, A_mel, whistle, 0.6)
			pad(s, b0, cs, 4, strings, 0.3, octave=3)
		elif p == "B":
			s.line(b0, B_mel, accordion, 0.55)
			drums(s, b0, len(cs), 4, [(lambda: tambourine(0.4), (1, 3), 0.35)])
		elif p == "A2":
			s.line(b0, A_mel, whistle, 0.55)
			s.line(b0, A_mel, bell, 0.3, transpose=12)
			pad(s, b0, cs, 4, accordion, 0.25, octave=4)
		elif p == "outro":
			s.line(b0, "E5:4 F#5:4 G5:8", whistle, 0.45)
	play_form(s, form, 4, part)
	return finish(s.render(0.3, 2.2, 0.9, tail=3.0))


# ===================================================================== Fishman Island
# Underwater and dreamy: rippling harp and bells, slow strings, a floating whistle. D Dorian.

def fishman():
	bpm = 70
	A = ["Dm", "G", "Dm", "G", "F", "C", "G", "Am"]
	B = ["C", "G", "Dm", "Am", "C", "G", "Em", "A"]
	A_mel = "A5:3 B5:1 D6:2 B5:2 A5:2 F5:1 E5:1 D5:4 C5:1 D5:1 F5:1 A5:1 G5:2 E5:2 D5:1 E5:1 G5:1 B5:1 A5:4"
	B_mel = "E6:2 D6:1 C6:1 B5:2 G5:2 A5:1 F5:1 D5:2 E5:4 G5:1 A5:1 C6:2 D6:2 B5:2 G5:1 B5:1 E6:2 C#6:4"
	check(A_mel, 8, 4, "fishman A")
	check(B_mel, 8, 4, "fishman B")
	form = [("intro", ["Dm", "G"]), ("A", A), ("B", B), ("A2", A), ("outro", ["Dm", "G", "Dm", "Dm"])]
	s = Song(bpm, bars(form) * 4)
	rng = np.random.default_rng(5)

	def part(p, cs, b0):
		pad(s, b0, cs, 4, strings, 0.45, octave=3)
		arp(s, b0, cs, 4, [0, 1, 2, 3, 4, 3, 2, 1], 0.5, harp, 0.35)
		bass(s, b0, cs, 4, [(0, 0, 3.5)], gain=0.45)
		for k in range(len(cs) * 2):  # little bubbles rising
			s.add(b0 + k * 2 + rng.uniform(0, 1.5), music_box(hz(midi("D7") + int(rng.choice([0, 2, 5, 7, 9]))), 0.2, 0.4), 0.18)
		if p == "intro":
			s.line(b0, "A5:4 B5:4", bell, 0.45)
		elif p == "A":
			s.line(b0, A_mel, whistle, 0.55)
		elif p == "B":
			s.line(b0, B_mel, bell, 0.5)
			pad(s, b0, cs, 4, choir, 0.3, octave=3, vowel="oo")
		elif p == "A2":
			s.line(b0, A_mel, whistle, 0.5)
			s.line(b0, A_mel, marimba, 0.3, transpose=-12)
		elif p == "outro":
			s.line(b0, "A5:4 B5:4 D6:8", bell, 0.45)
	play_form(s, form, 4, part)
	return finish(s.render(0.45, 3.2, 1.4, tail=4.5))


# ===================================================================== Sabaody (bubble park town)
# Bouncy and a bit jazzy: walking bass, piano chords, brushed drums. F major.

def sabaody():
	bpm = 116
	A = ["F", "Dm", "Gm7", "C7", "F", "Dm", "Gm7", "C7"]
	B = ["Bb", "Bb", "F", "F", "G7", "G7", "C7", "C7"]
	A_mel = ("C5:0.5 F5:0.5 A5:1 G5:0.5 F5:0.5 D5:1 F5:1 A5:1 D6:2 C6:0.5 Bb5:0.5 A5:1 G5:1 Bb5:1 A5:1 G5:1 E5:2 "
			 "C5:0.5 F5:0.5 A5:1 C6:1 A5:1 D6:1 C6:1 A5:1 F5:1 G5:1 A5:0.5 Bb5:0.5 D6:1 E5:1 F5:4")
	B_mel = "D6:2 C6:1 Bb5:1 D6:1 C6:1 Bb5:1 G5:1 C6:2 A5:1 F5:1 A5:3 r:1 B5:1 D6:1 F6:1 D6:1 B5:2 G5:2 C6:1 Bb5:1 G5:1 E5:1 G5:4"
	check(A_mel, 8, 4, "sabaody A")
	check(B_mel, 8, 4, "sabaody B")
	form = [("intro", ["F", "C7"]), ("A", A), ("B", B), ("A2", A), ("outro", ["Gm7", "C7", "F"])]
	s = Song(bpm, bars(form) * 4)

	def part(p, cs, b0):
		bass(s, b0, cs, 4, [(0, 0, 0.9), (1, 4, 0.9), (2, 7, 0.9), (3, 9, 0.9)], gain=0.55)
		strum(s, b0, cs, 4, (1, 3), piano, 0.4)
		if p != "intro":
			drums(s, b0, len(cs), 4, [(lambda: hat(0.35), (0, 0.67, 1, 1.67, 2, 2.67, 3, 3.67), 0.3),
									  (lambda: snare(0.25, 0.1), (1, 3), 0.3)])
		if p == "intro":
			s.line(b0, "A5:2 G5:2 E5:4", whistle, 0.45)
		elif p == "A":
			s.line(b0, A_mel, whistle, 0.6)
		elif p == "B":
			s.line(b0, B_mel, piano, 0.6)
			s.line(b0, B_mel, marimba, 0.3)
		elif p == "A2":
			s.line(b0, A_mel, accordion, 0.5)
			s.line(b0, A_mel, bell, 0.3, transpose=12)
		elif p == "outro":
			s.line(b0, "D6:2 Bb5:2 C6:2 E5:2 F5:4", whistle, 0.5)
	play_form(s, form, 4, part)
	return finish(s.render(0.25, 1.8, 0.6, tail=2.5))


# ===================================================================== Dressrosa (and Green Bit)
# Hot-blooded and proud: strummed guitar, hand claps and a fiddle, in an Andalusian A minor.

def dressrosa():
	bpm = 120
	A = ["Am", "G", "F", "E", "Am", "G", "F", "E"]
	B = ["Dm", "Am", "G", "C", "F", "Dm", "E", "E"]
	A_mel = ("E5:1 F5:0.5 E5:0.5 D5:1 C5:1 B4:1 D5:1 G5:2 A5:1 G5:0.5 F5:0.5 E5:1 F5:1 E5:3 r:1 "
			 "C6:1 B5:0.5 A5:0.5 G5:1 F5:1 E5:1 D5:1 B4:2 A5:1 G5:1 F5:1 D5:1 E5:1 G#5:1 B5:2")
	B_mel = "F5:1 A5:1 D6:2 C6:1 B5:0.5 A5:0.5 E5:2 D5:1 G5:1 B5:2 C6:1 B5:1 G5:2 A5:1.5 G5:0.5 F5:1 A5:1 D6:1 C6:1 A5:1 F5:1 E5:1 F5:1 G#5:1 B5:1 E6:4"
	check(A_mel, 8, 4, "dressrosa A")
	check(B_mel, 8, 4, "dressrosa B")
	form = [("intro", ["Am", "G", "F", "E"]), ("A", A), ("B", B), ("A2", A), ("outro", ["F", "E", "Am"])]
	s = Song(bpm, bars(form) * 4)

	def part(p, cs, b0):
		bass(s, b0, cs, 4, [(0, 0, 1.2), (1.5, 0, 1.2), (3, 7, 0.9)], gain=0.6)
		strum(s, b0, cs, 4, (0, 0.5, 1.5, 2, 3, 3.5), harp, 0.45, ln=0.3)  # 3+3+2 accents
		drums(s, b0, len(cs), 4, [(lambda: clap(0.7), (1.5, 3), 0.45), (lambda: tambourine(0.3), (0.5, 2.5), 0.3)])
		if p == "intro":
			s.line(b0, "E5:4 D5:4 C5:4 B4:4", fiddle, 0.5)
		elif p == "A":
			s.line(b0, A_mel, fiddle, 0.75)
		elif p == "B":
			s.line(b0, B_mel, whistle, 0.55)
			s.line(b0, B_mel, fiddle, 0.35, transpose=-12)
		elif p == "A2":
			s.line(b0, A_mel, fiddle, 0.7)
			s.line(b0, A_mel, accordion, 0.35, transpose=-12)
		elif p == "outro":
			s.line(b0, "A5:2 G5:2 G#5:4 A5:4", fiddle, 0.65)
	play_form(s, form, 4, part)
	return finish(s.render(0.24, 1.8, 0.7, tail=2.5))


# ===================================================================== Whole Cake Island (and Cacao Island)
# Sweet and a little too cheerful: a music-box waltz with pizzicato bass and accordion. Eb major, 3/4.

def whole_cake():
	bpm = 138
	A = ["Eb", "Cm", "Ab", "Bb", "Eb", "Cm", "Fm", "Bb"]
	B = ["Ab", "Bb", "Gm", "Cm", "Ab", "Bb", "Eb", "Eb"]
	A_mel = "G5:1 Bb5:1 Eb6:1 D6:2 C6:1 C6:1 Ab5:1 F5:1 D5:3 Eb5:1 G5:1 Bb5:1 C6:2 Bb5:1 Ab5:1 F5:1 D5:1 Eb5:3"
	B_mel = "C6:1.5 Bb5:0.5 Ab5:1 F5:1 Bb5:1 D6:1 Bb5:2 G5:1 C6:3 Eb6:1 C6:1 Ab5:1 F5:1 D5:1 Bb5:1 G5:2 F5:1 Eb5:3"
	check(A_mel, 8, 3, "whole cake A")
	check(B_mel, 8, 3, "whole cake B")
	form = [("intro", ["Eb", "Bb"]), ("A", A), ("B", B), ("A2", A), ("B2", B), ("outro", ["Bb", "Eb"])]
	s = Song(bpm, bars(form) * 3)

	def part(p, cs, b0):
		bass(s, b0, cs, 3, [(0, 0, 0.6)], gain=0.7)
		strum(s, b0, cs, 3, (1, 2), accordion, 0.22, ln=0.5)
		if p != "intro":
			drums(s, b0, len(cs), 3, [(lambda: tambourine(0.3), (1, 2), 0.25)])
		if p == "intro":
			s.line(b0, "Bb5:3 D6:3", music_box, 0.55, transpose=12)
		elif p == "A":
			s.line(b0, A_mel, music_box, 0.6, transpose=12)
			s.line(b0, A_mel, whistle, 0.3)
		elif p == "B":
			s.line(b0, B_mel, fiddle, 0.55)
			pad(s, b0, cs, 3, strings, 0.3, octave=3)
		elif p == "A2":
			s.line(b0, A_mel, music_box, 0.6, transpose=12)
			s.line(b0, A_mel, accordion, 0.35)
		elif p == "B2":
			s.line(b0, B_mel, music_box, 0.5, transpose=12)
			s.line(b0, B_mel, fiddle, 0.4)
		elif p == "outro":
			s.line(b0, "D6:3 Eb6:3", music_box, 0.55, transpose=12)
	play_form(s, form, 3, part)
	return finish(s.render(0.3, 2.2, 0.9, tail=3.0))


# ===================================================================== Egghead (the island of the future)
# Clean and electronic: square-wave arpeggios, synth bass, a light electronic beat. E minor.

def egghead():
	bpm = 112
	A = ["Em", "C", "G", "D", "Em", "C", "Am", "B"]
	B = ["C", "D", "Em", "Em", "C", "D", "B", "B"]
	A_mel = "E5:1 G5:1 B5:1.5 A5:0.5 G5:2 E5:2 C5:1 E5:1 G5:1 C6:1 B5:4 E5:1 G5:1 B5:1 E6:1 D6:2 B5:2 C6:1 B5:1 A5:1 E5:1 D#5:4"
	B_mel = "G5:2 A5:2 B5:1 D6:1 F#6:2 G6:1 F#6:1 E6:1 B5:1 E6:4 C6:1 D6:1 E6:2 F#6:1 E6:1 D6:2 D#6:2 F#6:2 B5:4"
	check(A_mel, 8, 4, "egghead A")
	check(B_mel, 8, 4, "egghead B")
	form = [("intro", ["Em", "C", "Em", "B"]), ("A", A), ("B", B), ("A2", A), ("outro", ["C", "B", "Em", "Em"])]
	s = Song(bpm, bars(form) * 4)

	def part(p, cs, b0):
		arp(s, b0, cs, 4, [0, 2, 3, 1, 4, 2, 3, 5] * 2, 0.25, chip, 0.28)
		bass(s, b0, cs, 4, [(k * 0.5, 0 if k % 4 != 3 else 12, 0.4) for k in range(8)], inst=synth_bass, gain=0.5)
		if p != "intro":
			drums(s, b0, len(cs), 4, [(lambda: kick(0.7), (0, 2), 0.6), (lambda: clap(0.5), (1, 3), 0.35),
									  (lambda: hat(0.4), (0.5, 1.5, 2.5, 3.5), 0.3)])
		if p == "A":
			s.line(b0, A_mel, bell, 0.55)
		elif p == "B":
			s.line(b0, B_mel, chip, 0.45, transpose=-12)
			pad(s, b0, cs, 4, strings, 0.35, octave=3)
		elif p == "A2":
			s.line(b0, A_mel, bell, 0.5)
			s.line(b0, A_mel, chip, 0.3)
		elif p == "outro":
			s.line(b0, "E6:4 D#6:4 E6:8", bell, 0.5)
	play_form(s, form, 4, part)
	return finish(s.render(0.22, 1.6, 0.6, tail=2.5))


# ===================================================================== Giants (Elbaph, Little Garden)
# Huge and heroic: war drums, horns and a choir of warriors. D Mixolydian.

def giants():
	bpm = 84
	A = ["D", "C", "G", "D", "D", "C", "G", "D"]
	B = ["Bm", "G", "A", "D", "Bm", "G", "C", "A"]
	A_mel = "D5:1.5 E5:0.5 F#5:1 A5:1 G5:1.5 E5:0.5 C5:2 B4:1 D5:1 G5:1 B5:1 A5:4 D6:1.5 C6:0.5 A5:1 F#5:1 G5:1 E5:1 C5:1 E5:1 D5:1 G5:1 B5:1 G5:1 A5:3 r:1"
	B_mel = "F#5:2 B5:2 D6:2 B5:2 C#6:1 B5:1 A5:2 F#5:4 B5:2 D6:1 C#6:1 B5:2 G5:2 G5:1 A5:1 C6:2 A5:4"
	check(A_mel, 8, 4, "giants A")
	check(B_mel, 8, 4, "giants B")
	form = [("intro", ["D", "C", "D", "D"]), ("A", A), ("B", B), ("A2", A), ("outro", ["C", "G", "D", "D"])]
	s = Song(bpm, bars(form) * 4)

	def part(p, cs, b0):
		for i, c in enumerate(cs):
			r = chord_notes(c, 1)[0]
			s.add(b0 + i * 4, timpani(hz(r + 12), 1.2, 0.9), 0.6)
			s.add(b0 + i * 4 + 2, timpani(hz(r + 12), 0.8, 0.6), 0.45)
		drums(s, b0, len(cs), 4, [(lambda: tom(90, 0.8), (1.5, 3, 3.5), 0.45), (lambda: kick(0.6), (0,), 0.5)])
		bass(s, b0, cs, 4, [(0, 0, 3.5)], inst=strings, gain=0.8)
		if p == "intro":
			pad(s, b0, cs, 4, brass, 0.4, octave=3)
			s.add(b0, crash(0.6), 0.5)
		elif p == "A":
			s.line(b0, A_mel, brass, 0.6)
			pad(s, b0, cs, 4, strings, 0.4, octave=3)
		elif p == "B":
			s.line(b0, B_mel, strings, 0.7)
			pad(s, b0, cs, 4, choir, 0.6, octave=3)
		elif p == "A2":
			s.line(b0, A_mel, brass, 0.6)
			s.line(b0, A_mel, brass, 0.35, transpose=-12)
			pad(s, b0, cs, 4, choir, 0.5, octave=3)
			s.add(b0, crash(0.7), 0.5)
		elif p == "outro":
			s.line(b0, "E5:4 D5:4 D5:8", brass, 0.55)
	play_form(s, form, 4, part)
	return finish(s.render(0.32, 2.6, 1.0, tail=3.5))


# ===================================================================== Jungle (Zou, Amazon Lily, Jaya)
# Wild and green: hand drums, a marimba pattern and a bamboo flute. A minor pentatonic.

def jungle():
	bpm = 100
	A = ["Am", "Am", "G", "Am", "F", "G", "Am", "Am"]
	B = ["F", "G", "Em", "Am", "F", "G", "E", "E"]
	A_mel = "A5:1 C6:1 D6:0.5 C6:0.5 A5:1 G5:2 E5:2 D5:1 E5:1 G5:1 A5:1 E5:4 A5:1 C6:1 E6:1 D6:1 C6:1 A5:1 G5:2 E5:1 G5:1 A5:1 C6:1 A5:4"
	B_mel = "C6:1 A5:1 F5:2 D6:1 B5:1 G5:2 E6:1 D6:1 B5:1 G5:1 A5:4 C6:1.5 D6:0.5 C6:1 A5:1 B5:1 G5:1 D5:2 E5:1 G#5:1 B5:1 D6:1 E6:4"
	check(A_mel, 8, 4, "jungle A")
	check(B_mel, 8, 4, "jungle B")
	form = [("intro", ["Am", "Am"]), ("A", A), ("B", B), ("A2", A), ("outro", ["F", "G", "Am"])]
	s = Song(bpm, bars(form) * 4)

	def part(p, cs, b0):
		arp(s, b0, cs, 4, [0, 2, 3, 2, 1, 2, 3, 4], 0.5, marimba, 0.35)
		bass(s, b0, cs, 4, [(0, 0, 1), (1.5, 7, 0.5), (2.5, 0, 1)], gain=0.55)
		drums(s, b0, len(cs), 4, [(lambda: tom(150, 0.7), (0, 1.5, 2.5), 0.4), (lambda: tom(220, 0.5), (0.75, 3, 3.5), 0.35),
								  (lambda: hat(0.25), (0.5, 1, 2, 3.25), 0.3)])
		if p == "intro":
			s.line(b0, "E5:4 A5:4", whistle, 0.45)
		elif p == "A":
			s.line(b0, A_mel, whistle, 0.6)
		elif p == "B":
			s.line(b0, B_mel, marimba, 0.6)
			pad(s, b0, cs, 4, strings, 0.3, octave=3)
		elif p == "A2":
			s.line(b0, A_mel, whistle, 0.55)
			s.line(b0, A_mel, marimba, 0.35, transpose=-12)
		elif p == "outro":
			s.line(b0, "C6:4 B5:4 A5:4", whistle, 0.5)
	play_form(s, form, 4, part)
	return finish(s.render(0.3, 2.0, 0.8, tail=3.0))


# ===================================================================== Impel Down (both hells)
# Heavy and hopeless: low strings, a slow heartbeat drum, far-off chains. C minor.

def prison():
	bpm = 60
	A = ["Cm", "Cm", "Ab", "G", "Fm", "Cm", "Db", "G"]
	B = ["Ab", "Fm", "Cm", "G", "Ab", "Db", "G", "G"]
	A_mel = "G4:4 Ab4:2 G4:2 Eb4:3 D4:1 B3:4 C4:2 Eb4:2 G4:2 F4:1 Eb4:1 Db4:3 F4:1 D4:4"
	B_mel = "C5:2 Eb5:2 F5:3 Ab5:1 G5:2 Eb5:2 D5:4 Eb5:2 C5:2 Db5:2 F5:2 D5:1 F5:1 B4:2 G4:4"
	check(A_mel, 8, 4, "prison A")
	check(B_mel, 8, 4, "prison B")
	form = [("intro", ["Cm", "Cm"]), ("A", A), ("B", B), ("A2", A), ("outro", ["Db", "Cm"])]
	s = Song(bpm, bars(form) * 4)

	def part(p, cs, b0):
		pad(s, b0, cs, 4, strings, 0.55, octave=2)
		for i in range(len(cs)):
			s.add(b0 + i * 4, timpani(hz(midi("C2")), 0.6, 0.6), 0.45)  # heartbeat
			s.add(b0 + i * 4 + 0.4, timpani(hz(midi("C2")), 0.5, 0.4), 0.35)
			if i % 2 == 1:
				s.add(b0 + i * 4 + 2.5, chain(0.7, seed=b0 + i), 0.5)
		if p == "intro":
			s.line(b0, "C4:8", choir, 0.4, vowel="oo")
		elif p == "A":
			s.line(b0, A_mel, strings, 0.75)
		elif p == "B":
			s.line(b0, B_mel, choir, 0.55, vowel="oo")
			s.line(b0, B_mel, bell, 0.25, transpose=-12)
		elif p == "A2":
			s.line(b0, A_mel, strings, 0.7)
			s.line(b0, A_mel, organ, 0.4, transpose=12)
		elif p == "outro":
			s.line(b0, "Db4:4 C4:4", strings, 0.6)
	play_form(s, form, 4, part)
	return finish(s.render(0.45, 3.0, 1.4, tail=4.5))


# ===================================================================== Holy Land (Red Line, Mary Geoise)
# Grand and cold: church organ, choir and fanfare brass. Bb major.

def holy():
	bpm = 76
	A = ["Bb", "F", "Gm", "Eb", "Bb", "Eb", "F", "F"]
	B = ["Eb", "Bb", "Cm", "F", "Eb", "Bb", "Cm7", "F"]
	A_mel = "F5:2 Bb5:2 C6:1.5 Bb5:0.5 A5:2 Bb5:1 G5:1 D5:2 Eb5:3 G5:1 F5:1 D5:1 Bb4:2 G5:2 Bb5:1 G5:1 F5:1 Eb5:1 C5:1 Eb5:1 F5:4"
	B_mel = "G5:2 Bb5:2 F5:2 D5:2 Eb5:1 G5:1 C6:2 A5:4 Bb5:2 G5:1 Eb5:1 F5:2 D6:2 C6:1 Bb5:1 G5:1 Eb5:1 F5:2 A5:2"
	check(A_mel, 8, 4, "holy A")
	check(B_mel, 8, 4, "holy B")
	form = [("intro", ["Bb", "Eb", "F", "Bb"]), ("A", A), ("B", B), ("A2", A), ("outro", ["Eb", "F", "Bb", "Bb"])]
	s = Song(bpm, bars(form) * 4)

	def part(p, cs, b0):
		pad(s, b0, cs, 4, organ, 0.6, octave=3)
		bass(s, b0, cs, 4, [(0, 0, 3.8)], inst=organ, octave=2, gain=0.5)
		for i, c in enumerate(cs):
			s.add(b0 + i * 4, bell(hz(chord_notes(c, 5)[0]), 1.5, 0.5), 0.2)
		if p == "intro":
			s.line(b0, "Bb4:1 D5:1 F5:2 G5:1 Bb5:1 Eb5:2 F5:2 A4:2 Bb4:4", brass, 0.5)
		elif p == "A":
			s.line(b0, A_mel, brass, 0.55)
		elif p == "B":
			s.line(b0, B_mel, choir, 0.6)
			s.add(b0, timpani(hz(midi("Bb1")), 1.0, 0.6), 0.4)
		elif p == "A2":
			s.line(b0, A_mel, brass, 0.55)
			pad(s, b0, cs, 4, choir, 0.45, octave=3)
		elif p == "outro":
			s.line(b0, "G5:4 A5:4 Bb5:8", brass, 0.5)
			s.add(b0 + 8, timpani(hz(midi("Bb1")), 2.0, 0.8), 0.5)
	play_form(s, form, 4, part)
	return finish(s.render(0.42, 3.2, 1.4, tail=4.5))


# ===================================================================== Ancient ruins (Void Century ruins, God Valley)
# Mysterious and old: a low drone, a far-off choir and stone-tablet bells. E Phrygian.

def ancient():
	bpm = 64
	A = ["Em", "F", "Em", "Em", "Am", "F", "Em", "Em"]
	B = ["Am", "G", "F", "Em", "Am", "G", "F", "E"]
	A_mel = "E5:2 F5:1 G5:1 A5:4 G5:1 F5:1 E5:2 B4:4 C5:1 E5:1 A5:2 G5:1 F5:1 C5:2 D5:1 F5:1 E5:2 E5:4"
	B_mel = "C6:2 B5:2 D6:2 B5:1 G5:1 A5:2 F5:2 G5:1 F5:1 E5:2 A5:1 C6:1 E6:2 D6:1 B5:1 G5:2 F5:2 A5:1 C6:1 B5:4"
	check(A_mel, 8, 4, "ancient A")
	check(B_mel, 8, 4, "ancient B")
	form = [("intro", ["Em", "F"]), ("A", A), ("B", B), ("A2", A), ("outro", ["F", "Em"])]
	s = Song(bpm, bars(form) * 4)

	def part(p, cs, b0):
		for i in range(len(cs)):
			s.add(b0 + i * 4, strings(hz(midi("E2")), 4 * s.spb, 0.7), 0.6)  # the drone never moves
			s.add(b0 + i * 4, strings(hz(midi("B2")), 4 * s.spb, 0.5), 0.35)
		arp(s, b0, cs, 4, [0, 2, 4, 2], 1, harp, 0.3)
		for i, c in enumerate(cs):
			if i % 2 == 0:
				s.add(b0 + i * 4 + 3, bell(hz(chord_notes(c, 5)[2]), 2.0, 0.5), 0.2)
		if p == "intro":
			s.line(b0, "E5:4 F5:4", choir, 0.4, vowel="oo")
		elif p == "A":
			s.line(b0, A_mel, whistle, 0.5)
			pad(s, b0, cs, 4, choir, 0.3, octave=3, vowel="oo")
		elif p == "B":
			s.line(b0, B_mel, choir, 0.6)
		elif p == "A2":
			s.line(b0, A_mel, whistle, 0.45)
			s.line(b0, A_mel, bell, 0.3, transpose=12)
		elif p == "outro":
			s.line(b0, "F5:4 E5:4", choir, 0.5, vowel="oo")
	play_form(s, form, 4, part)
	return finish(s.render(0.5, 3.4, 1.5, tail=5.0))


# ===================================================================== Newkama Land
# A non-stop party: four-on-the-floor drums, octave bass and brass hits. C major.

def newkama():
	bpm = 124
	A = ["C", "Am", "F", "G", "C", "Am", "F", "G"]
	B = ["F", "G", "Em", "Am", "Dm", "G", "C", "C"]
	A_mel = ("E5:0.5 G5:0.5 C6:1 B5:0.5 A5:0.5 G5:1 A5:1 F5:1 C5:2 F5:0.5 A5:0.5 C6:1 D6:1 C6:1 B5:2 G5:2 "
			 "E5:0.5 G5:0.5 C6:1 E6:1 D6:1 C6:1 A5:1 E5:2 F5:1 A5:1 G5:1 F5:1 D5:2 G5:2")
	B_mel = "A5:1 C6:1 F6:2 D6:1 B5:1 G5:2 G5:1 B5:1 E6:2 C6:2 A5:2 F5:1 A5:1 D6:2 B5:1 D6:1 G6:2 E6:1 D6:1 C6:1 G5:1 C6:4"
	check(A_mel, 8, 4, "newkama A")
	check(B_mel, 8, 4, "newkama B")
	form = [("intro", ["C", "Am", "F", "G"]), ("A", A), ("B", B), ("A2", A), ("B2", B)]
	s = Song(bpm, bars(form) * 4)

	def part(p, cs, b0):
		bass(s, b0, cs, 4, [(k * 0.5, 12 * (k % 2), 0.4) for k in range(8)], inst=synth_bass, gain=0.5)
		drums(s, b0, len(cs), 4, [(lambda: kick(0.8), (0, 1, 2, 3), 0.55), (lambda: hat(0.5, True), (0.5, 1.5, 2.5, 3.5), 0.3)])
		if p != "intro":
			drums(s, b0, len(cs), 4, [(lambda: clap(0.7), (1, 3), 0.4)])
			strum(s, b0, cs, 4, (0.5, 1.5, 2.5, 3.5), piano, 0.3)
		if p == "intro":
			pad(s, b0, cs, 4, strings, 0.4, octave=3)
		elif p == "A":
			s.line(b0, A_mel, brass, 0.55)
		elif p == "B":
			s.line(b0, B_mel, whistle, 0.55)
			pad(s, b0, cs, 4, strings, 0.4, octave=3)
		elif p == "A2":
			s.line(b0, A_mel, brass, 0.55)
			s.line(b0, A_mel, brass, 0.3, transpose=-12)
		elif p == "B2":
			s.line(b0, B_mel, brass, 0.5)
			s.line(b0, B_mel, strings, 0.35, transpose=12)
			s.add(b0 + 28, crash(0.7), 0.5)
	play_form(s, form, 4, part)
	return finish(s.render(0.2, 1.6, 0.6, tail=2.5))


# ===================================================================== Absolute Justice (boss: Admirals)
# Cold and unstoppable: a military snare, string ostinato and brass in F minor. Loops.

def admiral_battle():
	bpm = 140
	A = ["Fm", "Fm", "Db", "C", "Fm", "Bbm", "Db", "C"]
	B = ["Bbm", "Fm", "Db", "C", "Bbm", "Fm", "Db", "C"]
	A_mel = "F5:1.5 C5:0.5 F5:1 Ab5:1 G5:1.5 F5:0.5 E5:2 Db5:1 F5:1 Ab5:1 Db6:1 C6:3 r:1 F5:1.5 C5:0.5 F5:1 Ab5:1 Bb5:1.5 Ab5:0.5 Db6:2 C6:1 Bb5:1 Ab5:1 F5:1 E5:2 G5:2"
	B_mel = "Db6:2 C6:1 Bb5:1 Ab5:2 F5:2 Ab5:1 Bb5:1 C6:1 Db6:1 E5:2 G5:2 F6:2 Eb6:1 Db6:1 C6:2 Ab5:2 Db6:1 C6:1 Bb5:1 Ab5:1 G5:2 C6:2"
	check(A_mel, 8, 4, "admiral A")
	check(B_mel, 8, 4, "admiral B")
	form = [("intro", ["Fm", "Fm", "Db", "C"]), ("A", A), ("B", B), ("A2", A), ("bridge", ["Db", "C", "Db", "C"])]
	s = Song(bpm, bars(form) * 4)

	def part(p, cs, b0):
		for i, c in enumerate(cs):
			r = chord_notes(c, 2)[0]
			for k in range(8):
				s.add(b0 + i * 4 + k * 0.5, strings(hz(r + [0, 12, 0, 7, 0, 12, 0, 8][k]), 0.42 * s.spb, 0.9), 1.0)
		drums(s, b0, len(cs), 4, [(lambda: kick(0.9), (0, 2, 2.5), 0.7),
								  (lambda: snare(0.5, 0.12), (0.5, 1, 1.25, 1.5, 3, 3.25, 3.5, 3.75), 0.45),
								  (lambda: snare(0.9), (1, 3), 0.6)])
		if p == "intro":
			s.add(b0, crash(), 0.7)
			for k in (0, 1.5, 3, 4, 5.5, 7, 8, 9.5, 11, 12, 13, 14, 15):
				s.chord(b0 + k, "F3 C4 F4 Ab4", 0.3 * s.spb, brass, 0.6)
		elif p == "A":
			s.add(b0, crash(), 0.7)
			s.line(b0, A_mel, brass, 0.75)
			pad(s, b0, cs, 4, strings, 0.5, octave=3)
		elif p == "B":
			s.add(b0, crash(), 0.7)
			s.line(b0, B_mel, strings, 0.85)
			s.line(b0, B_mel, brass, 0.4, transpose=-12)
			pad(s, b0, cs, 4, choir, 0.6, octave=3)
		elif p == "A2":
			s.add(b0, crash(), 0.8)
			s.line(b0, A_mel, brass, 0.75)
			s.line(b0, A_mel, strings, 0.45, transpose=12)
			pad(s, b0, cs, 4, choir, 0.5, octave=3)
		elif p == "bridge":
			pad(s, b0, cs, 4, brass, 0.6, octave=3)
			for i, c in enumerate(cs):
				s.add(b0 + i * 4, timpani(hz(chord_notes(c, 2)[0]), 1.0, 1.0), 0.8)
	play_form(s, form, 4, part)
	return finish(loop_render(s, 0.18, 1.6, 0.5))


# ===================================================================== Warlord of the Sea (boss: Warlords and World Government elites)
# Dangerous swagger: a pirate fiddle and accordion over pounding drums, G harmonic minor. Loops.

def warlord_battle():
	bpm = 132
	A = ["Gm", "Gm", "Eb", "D", "Gm", "Cm", "D", "D"]
	B = ["Cm", "Gm", "Eb", "D", "Cm", "Gm", "Ab", "D"]
	A_mel = ("G5:0.5 A5:0.5 Bb5:1 A5:0.5 G5:0.5 F#5:1 G5:1 D5:1 Bb4:2 Eb5:1 G5:1 Bb5:1 Eb6:1 D6:3 C6:0.5 A5:0.5 "
			 "Bb5:0.5 A5:0.5 G5:1 D5:1 G5:1 C6:1 Bb5:0.5 A5:0.5 G5:1 Eb5:1 D5:1 F#5:1 A5:1 C6:1 D6:4")
	B_mel = "Eb5:2 G5:1 C6:1 Bb5:2 G5:2 G5:1 Bb5:1 Eb6:2 D6:2 A5:2 C6:1.5 Bb5:0.5 A5:1 G5:1 Bb5:1 A5:1 G5:1 D5:1 Eb5:1 Ab5:1 C6:2 F#5:2 A5:2"
	check(A_mel, 8, 4, "warlord A")
	check(B_mel, 8, 4, "warlord B")
	form = [("intro", ["Gm", "Gm", "Eb", "D"]), ("A", A), ("B", B), ("A2", A), ("bridge", ["Cm", "D", "Eb", "D"])]
	s = Song(bpm, bars(form) * 4)

	def part(p, cs, b0):
		bass(s, b0, cs, 4, [(k * 0.5, [0, 0, 12, 0, 7, 0, 12, 7][k], 0.45) for k in range(8)], inst=synth_bass, gain=0.7)
		drums(s, b0, len(cs), 4, [(lambda: kick(0.9), (0, 1.5, 2), 0.8), (lambda: snare(0.85), (1, 3), 0.7),
								  (lambda: hat(0.6), tuple(k * 0.5 for k in range(8)), 0.45)])
		for i in range(len(cs)):
			if i == len(cs) - 1:
				for k, f in enumerate((200, 160, 130, 100)):
					s.add(b0 + i * 4 + 3 + k * 0.25, tom(f, 0.9), 0.6)
		strum(s, b0, cs, 4, (0.5, 1.5, 2.5, 3.5), accordion, 0.3, ln=0.3)
		if p == "intro":
			s.add(b0, crash(), 0.7)
			s.line(b0, "G4:4 Bb4:4 Eb5:4 D5:4", fiddle, 0.6)
		elif p == "A":
			s.add(b0, crash(), 0.7)
			s.line(b0, A_mel, fiddle, 0.8)
		elif p == "B":
			s.add(b0, crash(), 0.7)
			s.line(b0, B_mel, brass, 0.65)
			pad(s, b0, cs, 4, strings, 0.5, octave=3)
		elif p == "A2":
			s.add(b0, crash(), 0.8)
			s.line(b0, A_mel, fiddle, 0.75)
			s.line(b0, A_mel, brass, 0.4, transpose=-12)
		elif p == "bridge":
			pad(s, b0, cs, 4, brass, 0.55, octave=3)
	play_form(s, form, 4, part)
	return finish(loop_render(s, 0.18, 1.6, 0.5))


# ===================================================================== Dawn of the Void Century (boss: Imu, Rocks D. Xebec)
# The last fight: a huge choir, church organ, tolling bells and pounding timpani. D minor. Loops.

def final_battle():
	bpm = 96
	A = ["Dm", "Bb", "Gm", "A", "Dm", "F", "C", "A"]
	B = ["Bb", "C", "Am", "Dm", "Bb", "C", "Gm", "A"]
	A_mel = "D5:2 F5:1 A5:1 D6:3 C6:1 Bb5:2 G5:1 D5:1 E5:2 C#5:2 D5:1 E5:1 F5:1 A5:1 C6:2 A5:2 G5:1 E5:1 C5:1 E5:1 A5:4"
	B_mel = "F5:1 Bb5:1 D6:2 E6:2 C6:2 C6:1 B5:0.5 A5:0.5 E5:2 F5:2 A5:2 Bb5:1 D6:1 F6:2 E6:2 G6:2 F6:1 D6:1 Bb5:1 G5:1 E6:2 C#6:2"
	check(A_mel, 8, 4, "final A")
	check(B_mel, 8, 4, "final B")
	form = [("intro", ["Dm", "Dm", "Bb", "A"]), ("A", A), ("B", B), ("quiet", ["Dm", "Bb", "Gm", "A"]), ("A2", A)]
	s = Song(bpm, bars(form) * 4)

	def part(p, cs, b0):
		for i, c in enumerate(cs):
			r = chord_notes(c, 2)[0]
			if p != "quiet":
				for k in range(16):
					s.add(b0 + i * 4 + k * 0.25, strings(hz(r + [0, 0, 12, 0][k % 4]), 0.22 * s.spb, 0.8), 0.9)
				s.add(b0 + i * 4, timpani(hz(r), 1.0, 1.0), 0.85)
				s.add(b0 + i * 4 + 1.5, timpani(hz(r), 0.6, 0.6), 0.7)
				s.add(b0 + i * 4 + 2.5, timpani(hz(r + 7 - 12), 0.6, 0.7), 0.7)
				s.add(b0 + i * 4, kick(0.8), 0.6)
				s.add(b0 + i * 4 + 2, snare(0.8), 0.5)
			s.add(b0 + i * 4, bell(hz(r + 24), 2.5, 0.8), 0.25)  # the toll
		if p == "intro":
			pad(s, b0, cs, 4, organ, 0.8, octave=3)
			pad(s, b0, cs, 4, choir, 0.9, octave=3)
			s.add(b0, crash(), 0.7)
		elif p == "A":
			s.add(b0, crash(), 0.7)
			s.line(b0, A_mel, choir, 0.9)
			s.line(b0, A_mel, brass, 0.5, transpose=-12)
			pad(s, b0, cs, 4, organ, 0.5, octave=3)
		elif p == "B":
			s.add(b0, crash(), 0.7)
			s.line(b0, B_mel, brass, 0.7)
			pad(s, b0, cs, 4, choir, 0.9, octave=3)
		elif p == "quiet":
			pad(s, b0, cs, 4, organ, 0.6, octave=3)
			s.line(b0, "A4:4 Bb4:4 D5:4 C#5:4", choir, 0.7, vowel="oo")
			for k in range(16):
				s.add(b0 + 12 + k * 0.25, timpani(hz(midi("A1")), 0.2, 0.25 + k * 0.045), 0.8)
		elif p == "A2":
			s.add(b0, crash(), 0.9)
			s.line(b0, A_mel, brass, 0.75)
			s.line(b0, A_mel, choir, 0.7)
			s.line(b0, A_mel, strings, 0.45, transpose=12)
			pad(s, b0, cs, 4, organ, 0.5, octave=3)
	play_form(s, form, 4, part)
	return finish(loop_render(s, 0.28, 2.4, 0.9))


ISLANDS = {
	"island_east_blue": east_blue,
	"island_fishman": fishman,
	"island_sabaody": sabaody,
	"island_dressrosa": dressrosa,
	"island_whole_cake": whole_cake,
	"island_egghead": egghead,
	"island_giants": giants,
	"island_jungle": jungle,
	"island_prison": prison,
	"island_holy": holy,
	"island_ancient": ancient,
	"island_newkama": newkama,
}
BOSSES = {
	"admiral_battle": admiral_battle,
	"warlord_battle": warlord_battle,
	"final_battle": final_battle,
}
ALL = {**ISLANDS, **BOSSES}
