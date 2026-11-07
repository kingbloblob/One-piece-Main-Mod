"""
Island themes: calm background music, one per kind of island (the islands' biomes play them like vanilla
biome music). All melodies written for this mod. Same tools as music.py.
"""
from synth import (Song, accordion, bell, brass, choir, crash, fiddle, finish, hat, hz, kick, midi, piano, pluck_bass,
				   snare, strings, tambourine, timpani, tom, whistle)
from music import chord_notes, name_of, pad
from music_shanties import check, chord


def marimba(f, d, v=1.0):
	return bell(f, d, v, decay=0.35)


def harp(f, d, v=1.0):
	return pluck_bass(f, d, v) * 0.7


def play_form(s, form, per_bar, fn):
	bar = 0
	for part, cs in form:
		fn(part, cs, bar * per_bar)
		bar += len(cs)


# ===================================================================== Winter (Drum, Punk Hazard, Elbaph)
# Slow, cold and glassy: bells over soft strings, D minor.

def winter():
	bpm = 66
	A = ["Dm", "Bb", "F", "C", "Dm", "Bb", "Gm", "A"]
	B = ["Bb", "F", "Gm", "Dm", "Bb", "F", "Gm", "A"]
	A_mel = "A5:2 F5:1 D5:1 D6:3 C6:1 A5:2 F5:2 G5:4 A5:2 D6:1 C6:1 Bb5:3 A5:1 G5:2 E5:2 C#6:4"
	check(A_mel, 8, 4, "winter A")
	B_mel = "D6:2 C6:1 Bb5:1 A5:2 C6:2 Bb5:1 A5:1 G5:2 F5:2 A5:2 D6:2 F6:3 E6:1 D6:2 Bb5:2 C#6:2 E6:4"
	check(B_mel, 8, 4, "winter B")
	form = [("intro", ["Dm", "Bb"]), ("A", A), ("B", B), ("A2", A), ("outro", ["Bb", "A", "Dm", "Dm"])]
	s = Song(bpm, sum(len(c) for _, c in form) * 4)

	def part(p, cs, b0):
		pad(s, b0, cs, 4, strings, 0.55 if p != "intro" else 0.45, octave=3)
		for i, c in enumerate(cs):
			n = chord_notes(c, 4)
			for k, m in enumerate([n[0], n[2], n[1] + 12, n[2]]):
				s.add(b0 + i * 4 + k, harp(hz(m), 0.9 * s.spb, 0.5), 0.35)
		if p == "A":
			s.line(b0, A_mel, bell, 0.6)
		elif p == "B":
			s.line(b0, B_mel, whistle, 0.5)
			pad(s, b0, cs, 4, choir, 0.35, octave=3, vowel="oo")
		elif p == "A2":
			s.line(b0, A_mel, whistle, 0.45)
			s.line(b0, A_mel, bell, 0.35, transpose=12)
		elif p == "outro":
			s.line(b0, "D6:4 C#6:4 D6:8", bell, 0.5)
	play_form(s, form, 4, part)
	return finish(s.render(0.38, 2.8, 1.2, tail=4.0))


# ===================================================================== Desert (Alabasta, Kuri)
# Hot and dusty: a fiddle in an Eastern-sounding scale (E Phrygian dominant), drums and tambourine.

def desert():
	bpm = 96
	A_mel = ("E5:1 F5:0.5 G#5:0.5 A5:1 G#5:1 F5:1 E5:1 F5:1 D5:1 "
			 "E5:1.5 F5:0.5 E5:1 D5:1 C5:1 B4:1 E5:2 "
			 "A5:1 B5:0.5 C6:0.5 B5:1 A5:1 G#5:1 A5:1 F5:2 "
			 "E5:1 F5:1 G#5:1 B5:1 A5:1 G#5:1 E5:2")
	B_mel = ("C6:2 B5:1 A5:1 B5:2 A5:1 G#5:1 "
			 "A5:1 G#5:1 F5:1 E5:1 F5:2 E5:2 "
			 "D5:1 E5:1 F5:1 A5:1 G#5:2 F5:1 E5:1 "
			 "F5:1 E5:1 D5:1 C5:1 E5:4")
	check(A_mel, 8, 4, "desert A")
	check(B_mel, 8, 4, "desert B")
	drone = ["E", "E", "F", "E", "Am", "Am", "F", "E"]
	form = [("intro", ["E", "E", "F", "E"]), ("A", drone), ("B", ["Am", "E", "F", "E", "Dm", "E", "F", "E"]),
			("A2", drone), ("B2", ["Am", "E", "F", "E", "Dm", "E", "F", "E"]), ("outro", ["F", "E"])]
	s = Song(bpm, sum(len(c) for _, c in form) * 4)

	def part(p, cs, b0):
		for i, c in enumerate(cs):
			beat0 = b0 + i * 4
			r = chord_notes(c, 2)[0]
			s.add(beat0, pluck_bass(hz(r), 1.5 * s.spb, 0.8), 0.7)
			s.add(beat0 + 2.5, pluck_bass(hz(r), 1.0 * s.spb, 0.6), 0.6)
			for k, v in ((0, 1.0), (1.5, 0.6), (2, 0.8), (3, 0.6), (3.5, 0.5)):  # a darbuka-style pattern
				s.add(beat0 + k, tom(hz(r + 24), v), 0.35)
			s.add(beat0 + 1, tambourine(0.6), 0.6)
			s.add(beat0 + 3, tambourine(0.6), 0.6)
		pad(s, b0, cs, 4, strings, 0.35, octave=3)
		if p == "intro":
			s.line(b0, "E5:4 F5:2 E5:2 G#5:4 E5:4", whistle, 0.45)
		elif p == "A":
			s.line(b0, A_mel, fiddle, 0.85)
		elif p == "B":
			s.line(b0, B_mel, whistle, 0.6)
			s.line(b0, B_mel, fiddle, 0.4, transpose=-12)
		elif p == "A2":
			s.line(b0, A_mel, fiddle, 0.8)
			s.line(b0, A_mel, accordion, 0.4, transpose=-12)
		elif p == "B2":
			s.line(b0, B_mel, fiddle, 0.8)
		elif p == "outro":
			s.line(b0, "F5:2 G#5:2 E5:4", fiddle, 0.7)
	play_form(s, form, 4, part)
	return finish(s.render(0.25, 2.0, 0.7, tail=3.0))


# ===================================================================== Wano
# A five-note Japanese-style scale (E F A B C): harp-like plucks for a koto, a breathy flute and taiko drums.

def wano():
	bpm = 80
	A_mel = ("E5:1 F5:1 A5:2 B5:1 A5:1 F5:2 "
			 "E5:1 C5:1 B4:2 E5:4 "
			 "A5:1 B5:1 C6:2 B5:1 A5:1 F5:2 "
			 "A5:1 F5:1 E5:6")
	B_mel = ("E6:3 C6:1 B5:2 A5:2 "
			 "B5:1 C6:1 B5:1 A5:1 F5:4 "
			 "E5:2 F5:2 A5:2 B5:2 "
			 "C6:1 B5:1 F5:2 E5:4")
	check(A_mel, 8, 4, "wano A")
	check(B_mel, 8, 4, "wano B")
	koto = ["E4", "B4", "C5", "E5", "F5", "E5", "C5", "B4"]
	form = [("intro", ["Am"] * 2), ("A", ["Am"] * 8), ("B", ["F"] * 2 + ["Am"] * 2 + ["F"] * 2 + ["E"] * 2),
			("A2", ["Am"] * 8), ("outro", ["F", "Am"])]
	s = Song(bpm, sum(len(c) for _, c in form) * 4)

	def part(p, cs, b0):
		for i, c in enumerate(cs):
			beat0 = b0 + i * 4
			for k in range(8):
				m = midi(koto[k]) + (-4 if c == "F" and k % 4 == 0 else 0)
				s.add(beat0 + k * 0.5, harp(hz(m), 0.45 * s.spb, 0.6), 0.45)
			if p != "intro":
				s.add(beat0, timpani(hz(midi("E2")), 1.0, 0.8), 0.5)  # taiko
				s.add(beat0 + 2.5, tom(hz(midi("B2")), 0.7), 0.4)
				s.add(beat0 + 3, tom(hz(midi("E3")), 0.6), 0.35)
		if p == "intro":
			s.line(b0, "E5:3 F5:1 E5:4", whistle, 0.5)
		elif p == "A":
			s.line(b0, A_mel, whistle, 0.8)
		elif p == "B":
			s.line(b0, B_mel, fiddle, 0.6)
			pad(s, b0, cs, 4, strings, 0.4, octave=3)
		elif p == "A2":
			s.line(b0, A_mel, whistle, 0.7)
			s.line(b0, A_mel, harp, 0.5, transpose=-12)
		elif p == "outro":
			s.add(b0 + 4, timpani(hz(midi("E2")), 2.0, 1.0), 0.6)
	play_form(s, form, 4, part)
	return finish(s.render(0.3, 2.2, 0.9, tail=3.0))


# ===================================================================== Sky Island (Skypiea)
# Floating and bright: a choir and harp in F Lydian.

def sky():
	bpm = 72
	chords_a = ["F", "G", "F", "G", "Am", "G", "F", "C"]
	A_mel = "C6:2 B5:1 A5:1 G5:4 A5:1 B5:1 C6:1 D6:1 E6:4 F6:2 E6:1 D6:1 C6:2 G5:2 A5:3 G5:1 F5:2 E5:2"
	B_mel = "A5:2 C6:2 F6:4 E6:2 D6:2 B5:4 C6:1 D6:1 E6:2 D6:2 C6:2 B5:2 G5:2 C6:4"
	check(A_mel, 8, 4, "sky A")
	check(B_mel, 8, 4, "sky B")
	chords_b = ["F", "F", "G", "G", "Am", "G", "Dm", "C"]
	form = [("intro", ["F", "G"]), ("A", chords_a), ("B", chords_b), ("A2", chords_a), ("outro", ["F", "G", "F", "F"])]
	s = Song(bpm, sum(len(c) for _, c in form) * 4)

	def part(p, cs, b0):
		pad(s, b0, cs, 4, choir, 0.5, octave=3)
		for i, c in enumerate(cs):
			n = chord_notes(c, 4)
			arp = [n[0], n[1], n[2], n[0] + 12, n[1] + 12, n[0] + 12, n[2], n[1]]
			for k in range(8):
				s.add(b0 + i * 4 + k * 0.5, harp(hz(arp[k]), 0.5 * s.spb, 0.45), 0.35)
			s.add(b0 + i * 4, pluck_bass(hz(n[0] - 24), 3.5 * s.spb, 0.5), 0.5)
		if p == "A":
			s.line(b0, A_mel, whistle, 0.65)
		elif p == "B":
			s.line(b0, B_mel, bell, 0.5)
			s.line(b0, B_mel, strings, 0.5, transpose=-12)
		elif p == "A2":
			s.line(b0, A_mel, whistle, 0.55)
			s.line(b0, A_mel, bell, 0.35, transpose=12)
		elif p == "outro":
			s.line(b0, "A5:4 B5:4 C6:8", bell, 0.5)
	play_form(s, form, 4, part)
	return finish(s.render(0.4, 3.0, 1.3, tail=4.0))


# ===================================================================== Spooky (Thriller Bark, Kuraigana, Florian Triangle)
# A wobbly, creepy waltz in C minor: off-kilter accordion, bells and pizzicato bass.

def spooky():
	bpm = 104
	A = ["Cm", "Cm", "Fm", "Cm", "Ab", "Fm", "G", "G"]
	A_mel = "G5:2 Ab5:1 G5:2 Eb5:1 F#5:2 G5:1 C5:3 Eb5:2 F5:1 Ab5:2 G5:1 F5:1 Eb5:1 D5:1 B4:3"
	B_mel = "C6:2 B5:1 Bb5:2 A5:1 Ab5:3 G5:3 F5:1 Ab5:1 C6:1 B5:2 G5:1 D5:3 B4:3"
	check(A_mel, 8, 3, "spooky A")
	check(B_mel, 8, 3, "spooky B")
	B = ["Ab", "Ab", "Fm", "Cm", "Fm", "G", "G", "G"]
	form = [("intro", ["Cm", "G"]), ("A", A), ("B", B), ("A2", A), ("B2", B), ("outro", ["Cm", "Cm"])]
	s = Song(bpm, sum(len(c) for _, c in form) * 3)

	def part(p, cs, b0):
		for i, c in enumerate(cs):
			beat0 = b0 + i * 3
			n = chord_notes(c, 3)
			s.add(beat0, pluck_bass(hz(n[0] - 12), 0.6 * s.spb, 0.8), 0.7)
			for k in (1, 2):
				chord(s, beat0 + k, c, 0.5 * s.spb, accordion, 0.25)
		if p == "intro":
			s.line(b0, "G5:3 F#5:3", bell, 0.5)
		elif p == "A":
			s.line(b0, A_mel, bell, 0.55)
			s.line(b0, A_mel, accordion, 0.4, transpose=-12)
		elif p == "B":
			s.line(b0, B_mel, fiddle, 0.6)
			pad(s, b0, cs, 3, choir, 0.35, octave=3, vowel="oo")
		elif p == "A2":
			s.line(b0, A_mel, whistle, 0.5)
			s.line(b0, A_mel, bell, 0.35, transpose=12)
		elif p == "B2":
			s.line(b0, B_mel, fiddle, 0.55)
			s.line(b0, B_mel, bell, 0.3)
		elif p == "outro":
			s.line(b0, "C5:3 C4:3", bell, 0.5)
	play_form(s, form, 3, part)
	return finish(s.render(0.35, 2.6, 1.1, tail=3.0))


# ===================================================================== Marine base (Marineford, Enies Lobby, Loguetown)
# Proud and orderly: a calm Bb major march for horns and snare (gentler than the raid theme).

def marine():
	bpm = 100
	A = ["Bb", "F", "Gm", "Eb", "Bb", "F", "Eb", "F"]
	A_mel = "D5:1.5 Eb5:0.5 F5:2 Bb5:2 A5:1 G5:1 F5:2 G5:1 F5:1 Eb5:2 C5:2 D5:1.5 Eb5:0.5 F5:2 D6:2 C6:1 Bb5:1 G5:2 F5:2 A5:4"
	B_mel = "Bb5:2 A5:1 G5:1 F5:3 D5:1 Eb5:2 G5:2 Bb5:3 A5:1 G5:2 F5:1 Eb5:1 D5:2 Bb4:2 C5:1 D5:1 Eb5:1 C5:1 Bb4:4"
	check(A_mel, 8, 4, "marine A")
	check(B_mel, 8, 4, "marine B")
	B = ["Eb", "Bb", "Eb", "Bb", "Gm", "Bb", "F", "Bb"]
	form = [("intro", ["Bb", "F"]), ("A", A), ("B", B), ("A2", A), ("B2", B)]
	s = Song(bpm, sum(len(c) for _, c in form) * 4)

	def part(p, cs, b0):
		for i, c in enumerate(cs):
			beat0 = b0 + i * 4
			r = chord_notes(c, 2)[0]
			s.add(beat0, pluck_bass(hz(r), 0.9 * s.spb), 0.6)
			s.add(beat0 + 2, pluck_bass(hz(r + 7), 0.9 * s.spb), 0.5)
			for k, v in ((0, 0.4), (1, 0.6), (1.5, 0.3), (2, 0.4), (3, 0.6), (3.5, 0.35), (3.75, 0.3)):
				s.add(beat0 + k, snare(v, 0.15), 0.4)
		pad(s, b0, cs, 4, strings, 0.45, octave=3)
		if p == "intro":
			s.line(b0, "F4:2 Bb4:2 C5:2 F5:2", brass, 0.5)
		elif p == "A":
			s.line(b0, A_mel, brass, 0.55)
		elif p == "B":
			s.line(b0, B_mel, whistle, 0.5)
			s.line(b0, B_mel, brass, 0.3, transpose=-12)
		elif p == "A2":
			s.line(b0, A_mel, brass, 0.55)
			s.line(b0, A_mel, strings, 0.4, transpose=12)
		elif p == "B2":
			s.line(b0, B_mel, brass, 0.5)
			s.add(b0 + 32, timpani(hz(midi("Bb1")), 2.0, 0.8), 0.5)
	play_form(s, form, 4, part)
	return finish(s.render(0.28, 2.2, 0.8, tail=3.0))


# ===================================================================== Tropical (every other island)
# Sunny and easy-going: marimba, plucked strings and a whistled tune in C major.

def tropical():
	bpm = 108
	A = ["C", "Am", "F", "G", "C", "Am", "F", "G"]
	A_mel = "E5:1 G5:1 A5:1.5 G5:0.5 E5:2 C5:2 F5:1 A5:1 C6:1.5 A5:0.5 G5:4 E5:1 G5:1 A5:1.5 C6:0.5 D6:2 C6:1 A5:1 G5:1 E5:1 D5:1 F5:1 E5:2 D5:2"
	B_mel = "F5:1.5 E5:0.5 F5:1 A5:1 G5:2 E5:2 F5:1.5 E5:0.5 F5:1 A5:1 G5:4 A5:1 C6:1 D6:1 C6:1 A5:2 G5:2 F5:1 E5:1 D5:1 E5:1 C5:4"
	check(A_mel, 8, 4, "tropical A")
	check(B_mel, 8, 4, "tropical B")
	B = ["F", "C", "F", "C", "F", "C", "G", "C"]
	form = [("intro", ["C", "G"]), ("A", A), ("B", B), ("A2", A), ("B2", B), ("outro", ["F", "G", "C"])]
	s = Song(bpm, sum(len(c) for _, c in form) * 4)

	def part(p, cs, b0):
		for i, c in enumerate(cs):
			beat0 = b0 + i * 4
			n = chord_notes(c, 4)
			s.add(beat0, pluck_bass(hz(n[0] - 24), 1.4 * s.spb), 0.7)
			s.add(beat0 + 1.5, pluck_bass(hz(n[0] - 17), 0.9 * s.spb), 0.55)
			s.add(beat0 + 2, pluck_bass(hz(n[0] - 24), 1.4 * s.spb), 0.6)
			for k in (0.5, 1, 2.5, 3, 3.5):  # strummed off-beats, like a ukulele
				chord(s, beat0 + k, c, 0.35 * s.spb, harp, 0.45, octave=4)
			if p != "intro":
				s.add(beat0 + 1, tambourine(0.5), 0.45)
				s.add(beat0 + 3, tambourine(0.5), 0.45)
				for k in range(8):
					s.add(beat0 + k * 0.5, hat(0.3), 0.3)
		if p == "intro":
			s.line(b0, "G5:2 E5:2 D5:4", marimba, 0.6)
		elif p == "A":
			s.line(b0, A_mel, whistle, 0.6)
		elif p == "B":
			s.line(b0, B_mel, marimba, 0.7)
		elif p == "A2":
			s.line(b0, A_mel, marimba, 0.6)
			s.line(b0, A_mel, whistle, 0.4, transpose=12)
		elif p == "B2":
			s.line(b0, B_mel, whistle, 0.55)
			s.line(b0, B_mel, marimba, 0.4, transpose=-12)
		elif p == "outro":
			s.line(b0, "A5:4 B5:4 C6:4", marimba, 0.6)
	play_form(s, form, 4, part)
	return finish(s.render(0.22, 1.8, 0.6, tail=2.5))


ALL = {
	"island_winter": winter,
	"island_desert": desert,
	"island_wano": wano,
	"island_sky": sky,
	"island_spooky": spooky,
	"island_marine": marine,
	"island_tropical": tropical,
}
