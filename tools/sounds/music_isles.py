"""
2026-11-05: ten more island themes, so islands that used to share a theme now sound like themselves
(Punk Hazard, Loguetown, Enies Lobby, Onigashima, Zou, Amazon Lily, Jaya, Little Garden, Kuraigana, Hachinosu).
All melodies written for this mod. Same tools as music_more.py; each song is a small "spec" played by island().
"""
import numpy as np

from synth import (SR, Song, accordion, bell, brass, choir, crash, fiddle, finish, hat, hz, kick, midi, piano,
				   pluck_bass, snare, strings, synth_bass, tambourine, timpani, tom, whistle)
from music import chord_notes, pad
from music_islands import harp, marimba, play_form
from music_more import arp, bass, bars, chain, chip, clap, drums, music_box, organ, strum
from music_shanties import check


def mel(*bar_list):
	"""A melody written one bar per argument (keeps the beat counts easy to check)."""
	return " ".join(bar_list)


def island(name, bpm, A, B, A_mel, B_mel, *, lead, lead_b, layer, intro, outro, beat=None, pad_inst=strings,
		   pad_gain=0.35, lead_gain=0.6, b_gain=0.55, octave_pad=3, wet=(0.3, 2.2, 0.9), extra=None, intro_cs=None,
		   outro_cs=None):
	"""Calm island form: intro, A, B, A again (lead doubled), outro. layer(s, b0, cs) plays the accompaniment,
	beat(s, b0, cs, part) the percussion, extra(s, b0, cs, part) anything special to that island."""
	check(A_mel, len(A), 4, name + " A")
	check(B_mel, len(B), 4, name + " B")
	intro_cs = intro_cs or A[:2]
	outro_cs = outro_cs or [A[-2], A[0]]
	form = [("intro", intro_cs), ("A", A), ("B", B), ("A2", A), ("outro", outro_cs)]
	s = Song(bpm, bars(form) * 4)

	def part(p, cs, b0):
		layer(s, b0, cs)
		if beat and p != "intro":
			beat(s, b0, cs, p)
		if p == "intro":
			pad(s, b0, cs, 4, pad_inst, pad_gain, octave=octave_pad)
			s.line(b0, intro, lead, lead_gain * 0.75)
		elif p == "A":
			s.line(b0, A_mel, lead, lead_gain)
			pad(s, b0, cs, 4, pad_inst, pad_gain * 0.8, octave=octave_pad)
		elif p == "B":
			s.line(b0, B_mel, lead_b, b_gain)
			pad(s, b0, cs, 4, pad_inst, pad_gain, octave=octave_pad)
		elif p == "A2":
			s.line(b0, A_mel, lead, lead_gain * 0.9)
			s.line(b0, A_mel, lead_b, b_gain * 0.45, transpose=-12)
			pad(s, b0, cs, 4, pad_inst, pad_gain * 0.8, octave=octave_pad)
		elif p == "outro":
			pad(s, b0, cs, 4, pad_inst, pad_gain, octave=octave_pad)
			s.line(b0, outro, lead, lead_gain * 0.7)
		if extra:
			extra(s, b0, cs, p)
	play_form(s, form, 4, part)
	return finish(s.render(*wet, tail=3.0))


# ===================================================================== Punk Hazard
# Half fire, half ice, and a mad scientist's lab: a cold bell melody over a ticking lab synth. E minor.

def punk_hazard():
	def layer(s, b0, cs):
		arp(s, b0, cs, 4, [0, 2, 1, 2, 3, 2, 1, 2], 0.5, chip, 0.18)
		bass(s, b0, cs, 4, [(0, 0, 1.5), (2, 0, 0.5), (3, 7, 1)], inst=synth_bass, gain=0.45)

	def beat(s, b0, cs, p):
		drums(s, b0, len(cs), 4, [(lambda: hat(0.3), (0.5, 1.5, 2.5, 3.5), 0.25), (lambda: kick(0.5), (0, 2), 0.35)])

	return island("punk hazard", 84,
		["Em", "C", "Am", "B", "Em", "C", "D", "B"], ["C", "G", "Am", "Em", "C", "G", "B", "B"],
		mel("E5:2 G5:1 B5:1", "C6:2 B5:1 A5:1", "A5:1 C6:1 E6:2", "D#6:3 r:1",
			"E6:1 D6:1 B5:2", "C6:1 B5:1 G5:2", "A5:1 F#5:1 D5:2", "B4:4"),
		mel("E6:1 D6:1 C6:2", "B5:2 D6:2", "C6:1 B5:1 A5:2", "G5:2 E5:2",
			"G5:1 A5:1 C6:2", "D6:2 B5:2", "A5:1 B5:1 D#6:2", "F#5:4"),
		lead=bell, lead_b=brass, layer=layer, beat=beat, pad_inst=strings, b_gain=0.45,
		intro="B4:4 E5:4", outro="E5:4 B4:4")


# ===================================================================== Loguetown
# The town of the beginning and the end: a busy, hopeful market tune, with a bell tolling from the execution square.

def loguetown():
	def layer(s, b0, cs):
		bass(s, b0, cs, 4, [(0, 0, 0.9), (1, 7, 0.9), (2, 0, 0.9), (3, 7, 0.9)], gain=0.5)
		strum(s, b0, cs, 4, (1, 3), piano, 0.35)

	def beat(s, b0, cs, p):
		drums(s, b0, len(cs), 4, [(lambda: tambourine(0.4), (1, 3), 0.3), (lambda: kick(0.5), (0, 2), 0.3)])

	def extra(s, b0, cs, p):
		if p in ("A", "A2", "outro"):
			s.add(b0, bell(hz(midi("C4")), 3.0, 0.8, decay=2.0), 0.35)  # the square's bell

	return island("loguetown", 104,
		["C", "Am", "F", "G", "C", "Em", "F", "G"], ["F", "G", "Em", "Am", "F", "G", "C", "C"],
		mel("G4:1 C5:1 E5:1 G5:1", "A5:2 E5:2", "F5:1 A5:1 C6:1 A5:1", "G5:3 r:1",
			"E5:1 G5:1 C6:1.5 B5:0.5", "B5:2 G5:2", "A5:1 F5:1 D5:1 F5:1", "G5:4"),
		mel("A5:1.5 G5:0.5 F5:2", "D5:1 E5:1 G5:2", "E5:1.5 D5:0.5 C5:1 E5:1", "A5:4",
			"C6:1.5 B5:0.5 A5:2", "B5:1 C6:1 D6:2", "E6:2 D6:1 B5:1", "C6:4"),
		lead=accordion, lead_b=whistle, layer=layer, beat=beat, pad_inst=accordion, pad_gain=0.2, extra=extra,
		intro="E5:4 D5:4", outro="D5:4 C5:4", outro_cs=["G", "C"])


# ===================================================================== Enies Lobby
# The island where it is always day and the law is cold: church organ, a marching snare and a stern brass line. D minor.

def enies_lobby():
	def layer(s, b0, cs):
		for i, c in enumerate(cs):
			r = chord_notes(c, 3)[0]
			for k in range(8):
				s.add(b0 + i * 4 + k * 0.5, strings(hz(r + [0, 7, 12, 7][k % 4]), 0.42 * s.spb, 0.6), 0.45)
		bass(s, b0, cs, 4, [(0, 0, 2), (2, 7, 2)], gain=0.4)

	def beat(s, b0, cs, p):
		drums(s, b0, len(cs), 4, [(lambda: snare(0.4, 0.1), (0, 0.5, 0.75, 1, 2, 2.5, 2.75, 3), 0.3),
								  (lambda: kick(0.6), (0, 2), 0.35)])

	return island("enies lobby", 96,
		["Dm", "Gm", "A", "Dm", "Bb", "Gm", "A", "A"], ["Bb", "F", "C", "Dm", "Bb", "F", "Gm", "A"],
		mel("D5:1 F5:1 A5:2", "Bb5:2 G5:2", "A5:1 G5:1 E5:1 C#5:1", "D5:4",
			"F5:1 A5:1 D6:2", "C6:1 Bb5:1 G5:2", "E5:1 G5:1 A5:2", "A5:4"),
		mel("D6:2 C6:1 Bb5:1", "A5:2 F5:2", "G5:1 A5:1 C6:2", "A5:4",
			"D6:1.5 E6:0.5 F6:2", "C6:2 A5:2", "Bb5:1 A5:1 G5:2", "E5:4"),
		lead=brass, lead_b=strings, layer=layer, beat=beat, pad_inst=organ, pad_gain=0.5, lead_gain=0.55,
		intro="A4:4 D5:4", outro="C#5:4 D5:4", outro_cs=["A", "Dm"], wet=(0.35, 2.6, 1.0))


# ===================================================================== Onigashima
# The Beasts' island fortress: slow war drums, a plucked shamisen and a lonely flute, darker than Wano. A minor with Bb.

def onigashima():
	def layer(s, b0, cs):
		for i, c in enumerate(cs):
			r = chord_notes(c, 4)[0]
			for k, st in enumerate([0, 7, 12, 7, 1 if c == "Bb" else 0, 7, 12, 15]):
				s.add(b0 + i * 4 + k * 0.5, harp(hz(r + st), 0.3 * s.spb, 0.7), 0.35)

	def beat(s, b0, cs, p):
		for i in range(len(cs)):
			s.add(b0 + i * 4, timpani(hz(midi("A1")), 1.2, 1.0), 0.6)  # taiko
			s.add(b0 + i * 4 + 1.5, tom(hz(midi("E2")), 0.8), 0.45)
			s.add(b0 + i * 4 + 2, timpani(hz(midi("A1")), 0.8, 0.8), 0.45)
			if i % 2 == 1:
				for k in range(4):
					s.add(b0 + i * 4 + 3 + k * 0.25, tom(hz(midi("A2")), 0.6 + k * 0.1), 0.35)

	def extra(s, b0, cs, p):
		if p == "B":
			for i in range(0, len(cs), 4):
				s.add(b0 + i * 4, chain(0.8, seed=i), 0.6)

	return island("onigashima", 92,
		["Am", "Bb", "Am", "G", "Am", "Bb", "G", "Am"], ["F", "G", "Am", "Am", "F", "G", "E", "E"],
		mel("A4:1 C5:1 E5:2", "F5:3 E5:1", "D5:1 E5:1 C5:2", "B4:2 G4:2",
			"A4:1 E5:1 A5:2", "Bb5:2 A5:1 F5:1", "G5:1 F5:1 D5:2", "E5:4"),
		mel("A5:2 C6:2", "B5:1 A5:1 G5:2", "A5:1 E5:1 C5:2", "E5:4",
			"F5:1 A5:1 C6:2", "D6:2 B5:2", "G#5:1 B5:1 E6:2", "E5:4"),
		lead=whistle, lead_b=fiddle, layer=layer, beat=beat, pad_inst=strings, pad_gain=0.3, extra=extra,
		intro="E5:3 F5:1 E5:4", outro="E5:4 A4:4", outro_cs=["E", "Am"])


# ===================================================================== Zou
# A forest on the back of a walking elephant, home of the Minks: warm marimba, hand drums and the elephant's call.

def zou():
	def layer(s, b0, cs):
		strum(s, b0, cs, 4, (0.5, 1.5, 2.5, 3.5), harp, 0.3)
		bass(s, b0, cs, 4, [(0, 0, 1), (1.5, 7, 0.5), (2, 12, 1), (3, 7, 1)], gain=0.5)

	def beat(s, b0, cs, p):
		drums(s, b0, len(cs), 4, [(lambda: tom(180, 0.6), (0, 1.5, 2), 0.35), (lambda: tom(260, 0.5), (1, 3, 3.5), 0.3),
								  (lambda: clap(0.6), (1, 3), 0.15)])

	def extra(s, b0, cs, p):
		if p in ("intro", "outro"):  # the elephant's distant trumpet call
			s.add(b0 + 4, brass(hz(midi("F2")), 2.0, 0.9, vib=0.02), 0.5)
			s.add(b0 + 4, brass(hz(midi("C3")), 2.0, 0.7, vib=0.02), 0.35)

	return island("zou", 100,
		["G", "F", "C", "G", "G", "F", "D", "G"], ["C", "C", "G", "G", "F", "F", "D", "D"],
		mel("D5:1 G5:1 A5:1 B5:1", "C6:2 A5:2", "G5:1 E5:1 C5:2", "D5:4",
			"B5:1 D6:1 B5:1 G5:1", "F5:2 A5:2", "F#5:1 A5:1 C6:1 A5:1", "G5:4"),
		mel("E5:1 G5:1 C6:2", "E6:2 C6:2", "D6:1 B5:1 G5:2", "D5:4",
			"C5:1 F5:1 A5:2", "C6:1 A5:1 F5:2", "A5:1 F#5:1 D5:1 F#5:1", "A5:4"),
		lead=marimba, lead_b=whistle, layer=layer, beat=beat, pad_inst=strings, pad_gain=0.25, lead_gain=0.7,
		extra=extra, intro="B4:4 D5:4", outro="D5:4 G5:4", outro_cs=["D", "G"])


# ===================================================================== Amazon Lily
# The island of warrior women: proud and exotic, a fiddle over rippling harp and hand drums. D harmonic minor.

def amazon_lily():
	def layer(s, b0, cs):
		arp(s, b0, cs, 4, [0, 1, 2, 3, 4, 3, 2, 1], 0.5, harp, 0.35)
		bass(s, b0, cs, 4, [(0, 0, 1.5), (1.5, 7, 0.5), (2, 0, 2)], gain=0.45)

	def beat(s, b0, cs, p):
		drums(s, b0, len(cs), 4, [(lambda: tom(150, 0.7), (0, 0.75, 2), 0.4), (lambda: tom(230, 0.5), (1.5, 2.75, 3.5), 0.3),
								  (lambda: tambourine(0.35), (1, 3), 0.25)])

	return island("amazon lily", 88,
		["Dm", "Gm", "A", "Dm", "Dm", "Bb", "A", "A"], ["Bb", "C", "F", "Dm", "Bb", "C", "A", "A"],
		mel("A4:1 D5:1 F5:1 A5:1", "Bb5:2 G5:2", "A5:1 G5:1 F5:1 E5:1", "D5:4",
			"F5:1 A5:1 D6:2", "D6:1 C#6:1 Bb5:2", "A5:1 G5:1 E5:1 C#5:1", "A4:4"),
		mel("D6:2 Bb5:2", "C6:1 Bb5:1 A5:1 G5:1", "A5:2 F5:2", "D5:4",
			"F5:1 G5:1 Bb5:2", "E5:1 G5:1 C6:2", "C#6:1 E6:1 D6:1 C#6:1", "A5:4"),
		lead=fiddle, lead_b=whistle, layer=layer, beat=beat, pad_inst=strings, pad_gain=0.3,
		intro="A4:4 C#5:4", outro="C#5:4 D5:4", outro_cs=["A", "Dm"])


# ===================================================================== Jaya
# Mock Town and the dreamers' island: a rowdy tavern piano, swinging bass and brushed drums. Bb major.

def jaya():
	def layer(s, b0, cs):
		bass(s, b0, cs, 4, [(0, 0, 0.9), (1, 7, 0.9), (2, 12, 0.9), (3, 7, 0.9)], gain=0.5)
		strum(s, b0, cs, 4, (0.67, 1.67, 2.67, 3.67), piano, 0.3, ln=0.3)

	def beat(s, b0, cs, p):
		drums(s, b0, len(cs), 4, [(lambda: hat(0.35), (0, 0.67, 1, 1.67, 2, 2.67, 3, 3.67), 0.25),
								  (lambda: snare(0.3, 0.1), (1, 3), 0.3), (lambda: kick(0.5), (0, 2.67), 0.3)])

	return island("jaya", 120,
		["Bb", "Gm", "Eb", "F", "Bb", "Gm", "C7", "F7"], ["Eb", "Eb", "Bb", "Bb", "C7", "C7", "F7", "F7"],
		mel("F5:1 D5:1 Bb4:1 D5:1", "G5:2 D5:2", "Eb5:1 G5:1 Bb5:1 G5:1", "F5:4",
			"Bb5:1 A5:1 G5:1 F5:1", "D5:1 G5:1 Bb5:2", "C6:1 Bb5:1 G5:1 E5:1", "F5:4"),
		mel("G5:1 Bb5:1 Eb6:2", "D6:1 C6:1 Bb5:2", "F5:1 Bb5:1 D6:2", "Bb5:4",
			"G5:1 Bb5:1 C6:1 E6:1", "D6:1 C6:1 Bb5:2", "A5:1 C6:1 F6:1 Eb6:1", "C6:4"),
		lead=piano, lead_b=accordion, layer=layer, beat=beat, pad_inst=accordion, pad_gain=0.15, lead_gain=0.65,
		intro="D5:2 F5:2 Bb5:4", outro="C6:4 Bb5:4", outro_cs=["F7", "Bb"], wet=(0.22, 1.6, 0.6))


# ===================================================================== Little Garden
# A prehistoric jungle where two giants have dueled for a hundred years: heavy, lumbering and proud. C minor.

def little_garden():
	def layer(s, b0, cs):
		bass(s, b0, cs, 4, [(0, 0, 1.8), (2, 7, 1.8)], gain=0.55)
		strum(s, b0, cs, 4, (1, 3), strings, 0.25, octave=3, ln=0.9)

	def beat(s, b0, cs, p):
		for i, c in enumerate(cs):
			r = chord_notes(c, 2)[0]
			s.add(b0 + i * 4, timpani(hz(r), 1.0, 1.0), 0.6)  # giant footsteps
			s.add(b0 + i * 4 + 2, timpani(hz(r), 0.8, 0.8), 0.45)

	def extra(s, b0, cs, p):
		if p == "B":  # the volcano rumbles: the duel goes on
			s.add(b0 + 12, crash(0.5), 0.3)

	return island("little garden", 76,
		["Cm", "Ab", "Bb", "Cm", "Cm", "Ab", "Gm", "G"], ["Ab", "Bb", "Eb", "Cm", "Ab", "Bb", "G", "G"],
		mel("C4:2 Eb4:1 G4:1", "Ab4:3 G4:1", "F4:1 G4:1 Bb4:2", "G4:4",
			"C5:2 Bb4:1 G4:1", "Ab4:2 Eb4:2", "D4:1 F4:1 G4:2", "G4:4"),
		mel("Eb5:2 C5:2", "D5:1 F5:1 Bb4:2", "G4:1 Bb4:1 Eb5:2", "C5:4",
			"C5:1 Eb5:1 Ab5:2", "F5:2 D5:2", "B4:1 D5:1 G5:2", "G4:4"),
		lead=brass, lead_b=fiddle, layer=layer, beat=beat, pad_inst=choir, pad_gain=0.3, lead_gain=0.7, b_gain=0.6,
		extra=extra, intro="G3:4 C4:4", outro="G4:4 C4:4", outro_cs=["G", "Cm"])


# ===================================================================== Kuraigana
# A ruined castle on a gloomy island, home of the world's greatest swordsman: gothic organ, slow piano, sad strings.

def kuraigana():
	def layer(s, b0, cs):
		arp(s, b0, cs, 4, [0, 1, 2, 1, 3, 1, 2, 1], 0.5, piano, 0.3)

	def extra(s, b0, cs, p):
		if p in ("A", "A2"):  # the castle bell, far away
			s.add(b0 + 28, bell(hz(midi("E4")), 3.0, 0.6, decay=2.5), 0.25)

	return island("kuraigana", 64,
		["Am", "F", "Dm", "E", "Am", "F", "G", "E"], ["Dm", "Am", "E", "Am", "Dm", "Am", "B7", "E"],
		mel("E5:3 C5:1", "A5:2 F5:2", "D5:1 E5:1 F5:2", "G#5:4",
			"A5:1 B5:1 C6:2", "A5:2 F5:2", "G5:1 F5:1 D5:2", "E5:4"),
		mel("F5:2 A5:2", "C6:2 E5:2", "G#5:1 B5:1 E6:2", "C6:4",
			"D6:1 C6:1 A5:2", "E5:1 A5:1 C6:2", "D#6:2 B5:2", "E5:4"),
		lead=strings, lead_b=whistle, layer=layer, pad_inst=organ, pad_gain=0.45, lead_gain=0.65, b_gain=0.45,
		extra=extra, intro="E5:4 C5:4", outro="G#4:4 A4:4", outro_cs=["E", "Am"], wet=(0.38, 2.8, 1.1))


# ===================================================================== Hachinosu
# The pirate island fortress: a sly, menacing swagger. Accordion over low strings and a pulsing bass. F minor.

def hachinosu():
	def layer(s, b0, cs):
		bass(s, b0, cs, 4, [(k * 0.5, [0, 0, 7, 0, 12, 0, 7, 0][k], 0.45) for k in range(8)], inst=synth_bass, gain=0.5)
		strum(s, b0, cs, 4, (0.5, 1.5, 2.5, 3.5), accordion, 0.22, ln=0.3)

	def beat(s, b0, cs, p):
		drums(s, b0, len(cs), 4, [(lambda: kick(0.7), (0, 1.5, 2), 0.45), (lambda: snare(0.5), (1, 3), 0.35)])

	def extra(s, b0, cs, p):
		if p == "B":
			for i in range(0, len(cs), 2):
				s.add(b0 + i * 4 + 3.5, chain(0.6, seed=7 + i), 0.4)

	return island("hachinosu", 100,
		["Fm", "Db", "Eb", "C", "Fm", "Db", "Bbm", "C"], ["Db", "Eb", "Fm", "Fm", "Db", "Eb", "C", "C"],
		mel("C5:1 F5:1 Ab5:2", "Db6:2 C6:2", "Bb5:1 G5:1 Eb5:2", "E5:4",
			"F5:1 Ab5:1 C6:1 F6:1", "Eb6:1 Db6:1 Ab5:2", "Bb5:1 Db6:1 F5:2", "G5:4"),
		mel("Ab5:2 F5:2", "G5:1 Bb5:1 Eb6:2", "C6:1 Ab5:1 F5:2", "C5:4",
			"Db5:1 F5:1 Ab5:2", "Bb5:2 G5:2", "E5:1 G5:1 C6:2", "C6:4"),
		lead=fiddle, lead_b=brass, layer=layer, beat=beat, pad_inst=strings, pad_gain=0.3, b_gain=0.45,
		extra=extra, intro="C5:4 F4:4", outro="E5:4 F5:4", outro_cs=["C", "Fm"])


ISLANDS = {
	"island_punk_hazard": punk_hazard,
	"island_loguetown": loguetown,
	"island_enies_lobby": enies_lobby,
	"island_onigashima": onigashima,
	"island_zou": zou,
	"island_amazon_lily": amazon_lily,
	"island_jaya": jaya,
	"island_little_garden": little_garden,
	"island_kuraigana": kuraigana,
	"island_hachinosu": hachinosu,
}
ALL = dict(ISLANDS)
