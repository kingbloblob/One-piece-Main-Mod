"""
Original music for the One Piece mod. Every melody here was written for this mod.
Each song function returns mono samples. Songs that loop (battle themes) wrap their echo
tail back to the start so the loop has no gap.
"""
import numpy as np

from synth import (SR, Song, accordion, brass, choir, crash, fiddle, finish, hat, hz, kick, midi, piano,
				   pluck_bass, reverb, snare, strings, synth_bass, tambourine, timpani, tom, whistle)


def loop_render(song, wet=0.2, size=1.8, decay=0.6):
	L = int(song.length * SR)
	full = reverb(song.buf, size, decay, wet)
	out = full[:L].copy()
	rest = full[L:L * 2]
	out[:len(rest)] += rest
	return out


def chord_notes(name, octave=3):
	"""'Dm' -> ['D3','F3','A3'] etc. Supports m, dim, 7, sus4, and plain major."""
	root = name[0] + (name[1] if len(name) > 1 and name[1] in "#b" else "")
	q = name[len(root):]
	r = midi(root + str(octave))
	steps = {"": [0, 4, 7], "m": [0, 3, 7], "dim": [0, 3, 6], "7": [0, 4, 7, 10], "m7": [0, 3, 7, 10],
			 "sus4": [0, 5, 7], "5": [0, 7, 12]}[q]
	return [r + s for s in steps]


def name_of(m):
	names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
	return names[m % 12] + str(m // 12 - 1)


def pad(song, start, chords, beats_per, inst, gain=1.0, octave=3, **kw):
	b = start
	for c in chords:
		song.chord(b, " ".join(name_of(m) for m in chord_notes(c, octave)), beats_per * 0.98, inst, gain, **kw)
		b += beats_per
	return b


# ===================================================================== Clash on the Grand Line
# Boss battle. D minor, 152 bpm, driving bass, brass melody. Loops.

def boss_battle():
	bpm = 152
	A_chords = ["Dm", "Dm", "Bb", "C", "Dm", "Dm", "Gm", "A"]
	B_chords = ["Bb", "C", "Am", "Dm", "Bb", "C", "E", "A"]
	A_mel = ("D5:1.5 A4:0.5 D5:0.5 E5:0.5 F5:1 "
			 "E5:1 D5:0.5 C5:0.5 A4:2 "
			 "Bb4:1.5 D5:0.5 F5:1 Bb5:1 "
			 "A5:1.5 G5:0.5 E5:1 C5:1 "
			 "D5:1.5 A4:0.5 D5:0.5 E5:0.5 F5:1 "
			 "G5:1 F5:0.5 E5:0.5 D5:1 F5:1 "
			 "G5:1.5 Bb5:0.5 A5:1 G5:1 "
			 "A5:3 E5:0.5 C#5:0.5")
	B_mel = ("F5:2 G5:1 A5:1 "
			 "G5:2 E5:1 C5:1 "
			 "E5:2 C5:1 A4:1 "
			 "D5:3 r:1 "
			 "F5:1 G5:1 A5:1 Bb5:1 "
			 "C6:2 Bb5:1 G5:1 "
			 "G#5:2 B5:1 D6:1 "
			 "C#6:4")
	form = [("intro", ["Dm", "Dm", "Dm", "A"]), ("A", A_chords), ("B", B_chords), ("A2", A_chords),
			("bridge", ["Gm", "A", "Bb", "A"])]
	total = sum(len(c) for _, c in form) * 4
	s = Song(bpm, total)
	bar = 0
	for part, chords in form:
		b0 = bar * 4
		for i, c in enumerate(chords):
			r = chord_notes(c, 2)[0]
			pattern = [0, 0, 12, 0, 7, 0, 10 if "m" in c else 11, 12]
			if part == "bridge" and i >= 2:
				pattern = [0, 0, 0, 0, 0, 0, 0, 0]
			for k, step in enumerate(pattern):
				s.add(b0 + i * 4 + k * 0.5, synth_bass(hz(r + step), 0.45 * s.spb, 0.9), 0.8)
			# drums
			beat0 = b0 + i * 4
			for k in range(8):
				s.add(beat0 + k * 0.5, hat(0.7 if k % 2 else 1.0), 0.6)
			s.add(beat0, kick(), 0.9)
			s.add(beat0 + 1.5, kick(0.7), 0.9)
			s.add(beat0 + 2, kick(), 0.9)
			s.add(beat0 + 1, snare(), 0.8)
			s.add(beat0 + 3, snare(), 0.8)
			if i == len(chords) - 1:  # tom fill into the next part
				for k, f in enumerate((180, 150, 120, 95)):
					s.add(beat0 + 3 + k * 0.25, tom(f, 0.9), 0.7)
		if part == "intro":
			pad(s, b0, chords, 4, strings, 0.9, octave=3)
			s.add(b0, crash(), 0.8)
			# brass stabs on the off-beats of the last two bars
			for k in (8, 9.5, 11, 12, 13.5, 15):
				s.chord(b0 + k, "D4 F4 A4", 0.3 * s.spb, brass, 0.6)
		elif part in ("A", "A2"):
			s.add(b0, crash(), 0.7)
			s.line(b0, A_mel, brass, 0.75)
			if part == "A2":
				s.line(b0, A_mel, strings, 0.5, transpose=12)
				s.line(b0, A_mel, brass, 0.35, transpose=-12)
			pad(s, b0, chords, 4, strings, 0.6, octave=3)
		elif part == "B":
			s.add(b0, crash(), 0.7)
			s.line(b0, B_mel, strings, 0.9)
			s.line(b0, B_mel, brass, 0.45, transpose=-12)
			pad(s, b0, chords, 4, choir, 0.8, octave=3)
		elif part == "bridge":
			pad(s, b0, chords, 4, brass, 0.6, octave=3)
			for k in range(16):  # snare build
				s.add(b0 + 8 + k * 0.5, snare(0.4 + k * 0.035, 0.15), 0.7)
		bar += len(chords)
	return finish(loop_render(s, 0.18, 1.6, 0.5))


# ===================================================================== Clash of Emperors
# Battle with an Emperor or an Admiral. C minor with a dark Db, 108 bpm, timpani and choir. Loops.

def emperor_battle():
	bpm = 108
	chords = ["Cm", "Db", "Cm", "G", "Ab", "Fm", "Db", "G"]
	mel = ("C5:2 Eb5:1 G5:1 "
		   "Ab5:3 G5:1 "
		   "F5:1 Eb5:1 D5:1 Eb5:1 "
		   "D5:3 B4:1 "
		   "C5:2 Eb5:1 Ab5:1 "
		   "C6:2 Bb5:1 Ab5:1 "
		   "Ab5:1.5 G5:0.5 F5:1 Db5:1 "
		   "B4:1 D5:1 G5:2")
	form = [("intro", chords[:4]), ("A", chords), ("A2", chords), ("quiet", ["Cm", "Db", "Cm", "G"]), ("A3", chords)]
	total = sum(len(c) for _, c in form) * 4
	s = Song(bpm, total)
	bar = 0
	for part, cs in form:
		b0 = bar * 4
		for i, c in enumerate(cs):
			r = chord_notes(c, 2)[0]
			beat0 = b0 + i * 4
			# low strings ostinato in 8ths
			for k in range(8):
				step = [0, 0, 12, 0, 0, 0, 7, 0][k]
				s.add(beat0 + k * 0.5, strings(hz(r + step), 0.42 * s.spb, 0.9 if k % 2 == 0 else 0.6), 1.2)
			if part != "quiet":
				s.add(beat0, timpani(hz(r), 1.0, 1.0), 0.9)
				s.add(beat0 + 2.5, timpani(hz(r), 0.6, 0.6), 0.9)
				s.add(beat0 + 3, timpani(hz(r + 7 - 12), 0.6, 0.7), 0.9)
				s.add(beat0, kick(0.8), 0.7)
				s.add(beat0 + 2, snare(0.7), 0.6)
			else:
				s.add(beat0, timpani(hz(r), 1.0, 0.5), 0.8)
		if part == "intro":
			pad(s, b0, cs, 4, choir, 1.0, octave=3)
			s.add(b0, crash(), 0.6)
		elif part == "A":
			s.line(b0, mel, brass, 0.8, transpose=-12)
			pad(s, b0, cs, 4, choir, 0.8, octave=3)
			s.add(b0, crash(), 0.7)
		elif part == "A2":
			s.line(b0, mel, brass, 0.75)
			s.line(b0, mel, strings, 0.6)
			pad(s, b0, cs, 4, choir, 0.9, octave=3)
			pad(s, b0, cs, 4, brass, 0.35, octave=2)
			s.add(b0, crash(), 0.8)
		elif part == "quiet":
			s.line(b0, "G4:4 Ab4:4 G4:4 B4:4", choir, 0.8, vowel="oo")
			for k in range(16):
				s.add(b0 + 12 + k * 0.25, timpani(hz(midi("G1")), 0.2, 0.25 + k * 0.04), 0.8)
		elif part == "A3":
			s.line(b0, mel, brass, 0.8)
			s.line(b0, mel, brass, 0.5, transpose=-12)
			s.line(b0, mel, strings, 0.5, transpose=12)
			pad(s, b0, cs, 4, choir, 1.0, octave=3)
			s.add(b0, crash(), 0.9)
		bar += len(cs)
	return finish(loop_render(s, 0.28, 2.4, 0.9))


# ===================================================================== Fair Winds
# Sailing song. G major jig in 6/8; one beat here = one eighth note. Plays once, then rests.

def fair_winds():
	bpm = 330  # eighth notes per minute
	A_chords = ["G", "C", "G", "D", "G", "C", "D", "G"]
	B_chords = ["Em", "C", "G", "D", "Em", "C", "D", "G"]
	A_mel = ("D5:2 B4:1 G4:2 B4:1 "
			 "C5:2 E5:1 G5:2 E5:1 "
			 "D5:2 B4:1 D5:1 C5:1 B4:1 "
			 "A4:3 F#4:2 A4:1 "
			 "G4:1 B4:1 D5:1 G5:2 F#5:1 "
			 "E5:2 G5:1 E5:2 C5:1 "
			 "D5:1 E5:1 F#5:1 A5:2 F#5:1 "
			 "G5:6")
	B_mel = ("B5:2 A5:1 G5:2 E5:1 "
			 "G5:2 E5:1 C5:3 "
			 "D5:1 E5:1 D5:1 B4:2 G4:1 "
			 "A4:2 B4:1 C5:1 D5:1 E5:1 "
			 "B5:2 A5:1 G5:1 F#5:1 E5:1 "
			 "E5:2 G5:1 C6:2 B5:1 "
			 "A5:2 F#5:1 D5:2 F#5:1 "
			 "G5:3 D5:1 B4:1 G4:1")
	form = [("intro", ["G", "D"]), ("A", A_chords), ("A2", A_chords), ("B", B_chords), ("B2", B_chords),
			("A3", A_chords), ("outro", ["C", "D", "G"])]
	total = sum(len(c) for _, c in form) * 6
	s = Song(bpm, total)
	bar = 0
	for part, cs in form:
		b0 = bar * 6
		for i, c in enumerate(cs):
			notes = chord_notes(c, 3)
			beat0 = b0 + i * 6
			# oom-pah: bass on 1 and 4, chord on 3 and 6
			s.add(beat0, pluck_bass(hz(notes[0] - 12), 1.8 * s.spb), 0.9)
			s.add(beat0 + 3, pluck_bass(hz(notes[0] - 12 + 7), 1.8 * s.spb), 0.8)
			for k in (2, 5):
				s.chord(beat0 + k, " ".join(name_of(m) for m in notes), 0.9 * s.spb, accordion, 0.5)
			for k in (0, 3):
				s.add(beat0 + k, tambourine(1.0), 0.8)
			s.add(beat0 + 2, tambourine(0.5), 0.8)
			s.add(beat0 + 5, tambourine(0.5), 0.8)
			if part != "intro" and part != "outro":
				s.add(beat0, kick(0.6), 0.5)
		if part == "A":
			s.line(b0, A_mel, accordion, 1.0)
		elif part == "A2":
			s.line(b0, A_mel, accordion, 0.9)
			s.line(b0, A_mel, whistle, 0.5, transpose=12)
		elif part == "B":
			s.line(b0, B_mel, fiddle, 0.9)
		elif part == "B2":
			s.line(b0, B_mel, fiddle, 0.8)
			s.line(b0, B_mel, accordion, 0.6, transpose=-12)
		elif part == "A3":
			s.line(b0, A_mel, accordion, 0.9)
			s.line(b0, A_mel, fiddle, 0.6, transpose=12)
		elif part == "outro":
			s.line(b0, "E5:3 G5:3 F#5:3 A5:3 G5:6", fiddle, 0.8)
			s.line(b0, "C5:3 E5:3 D5:3 F#5:3 B4:6", accordion, 0.7)
		bar += len(cs)
	return finish(s.render(0.22, 1.8, 0.6, tail=2.0))


# ===================================================================== Justice Marches
# Navy raid. G minor march, 116 bpm, snare and bugle-like brass. Loops.

def justice_marches():
	bpm = 116
	chords = ["Gm", "Gm", "Eb", "D", "Gm", "Cm", "D", "Gm"]
	mel = ("G4:1 G4:0.5 G4:0.5 Bb4:1 D5:1 "
		   "G5:2 F5:1 D5:1 "
		   "Eb5:1 Eb5:0.5 F5:0.5 G5:1 Eb5:1 "
		   "D5:3 A4:1 "
		   "G4:1 Bb4:0.5 D5:0.5 G5:1 Bb5:1 "
		   "A5:1 G5:1 Eb5:1 C5:1 "
		   "D5:1 F#5:1 A5:1 C6:1 "
		   "Bb5:2 G5:2")
	form = [("intro", ["Gm", "D", "Gm", "D"]), ("A", chords), ("drums", ["Gm", "Eb", "Cm", "D"]), ("A2", chords)]
	total = sum(len(c) for _, c in form) * 4
	s = Song(bpm, total)
	bar = 0
	for part, cs in form:
		b0 = bar * 4
		for i, c in enumerate(cs):
			r = chord_notes(c, 2)[0]
			beat0 = b0 + i * 4
			for k, step in enumerate((0, 7, 0, 7)):
				s.add(beat0 + k, pluck_bass(hz(r + step), 0.8 * s.spb), 0.9)
			# marching snare: rat-a-tat pattern
			for t, v in ((0, 1.0), (0.75, 0.5), (1, 0.8), (1.5, 0.6), (2, 1.0), (2.5, 0.5), (2.75, 0.5), (3, 0.9), (3.5, 0.6)):
				s.add(beat0 + t, snare(v, 0.18), 0.6)
			s.add(beat0, kick(0.9), 0.7)
			s.add(beat0 + 2, kick(0.8), 0.7)
			s.add(beat0, crash(0.3) if i % 4 == 0 else np.zeros(1), 0.5)
		if part == "intro":
			pad(s, b0, cs, 4, brass, 0.5, octave=3)
		elif part == "A":
			s.line(b0, mel, brass, 0.85)
			pad(s, b0, cs, 4, strings, 0.6, octave=3)
		elif part == "drums":
			s.line(b0, "G3:1 G3:1 D3:1 G3:1 Eb3:2 Bb2:2 C3:1 C3:1 Eb3:1 G3:1 D3:4", brass, 0.7)
			for k in range(8):
				s.add(b0 + 12 + k * 0.5, tom(160 - k * 10, 0.8), 0.6)
		elif part == "A2":
			s.line(b0, mel, brass, 0.8)
			s.line(b0, mel, brass, 0.45, transpose=-12)
			s.line(b0, mel, whistle, 0.35, transpose=12)
			pad(s, b0, cs, 4, strings, 0.7, octave=3)
		bar += len(cs)
	return finish(loop_render(s, 0.18, 1.6, 0.5))


# ===================================================================== Toward the Grand Line
# Adventure theme. D major, 128 bpm. Music disc and sailing alternate.

def toward_the_grand_line():
	bpm = 128
	V_chords = ["D", "A", "Bm", "G", "D", "A", "G", "A"]
	C_chords = ["G", "A", "F#m", "Bm", "G", "A", "D", "D"]
	verse = ("F#5:1 A5:1 D6:1.5 C#6:0.5 "
			 "B5:1 A5:1 E5:2 "
			 "F#5:1 D5:1 B4:1 D5:1 "
			 "G5:2 F#5:1 E5:1 "
			 "F#5:1 A5:1 D6:1.5 E6:0.5 "
			 "C#6:1 B5:1 A5:2 "
			 "B5:1 A5:1 G5:1 B5:1 "
			 "A5:4")
	chorus = ("B5:1.5 A5:0.5 G5:1 B5:1 "
			  "C#6:1.5 B5:0.5 A5:2 "
			  "A5:1 F#5:1 C#6:1 A5:1 "
			  "B5:3 D6:1 "
			  "D6:1.5 C#6:0.5 B5:1 G5:1 "
			  "A5:1 B5:1 C#6:1 E6:1 "
			  "D6:4 "
			  "r:2 A5:1 C#6:1")
	form = [("intro", ["D", "G", "D", "A"]), ("V", V_chords), ("C", C_chords), ("V2", V_chords), ("C2", C_chords),
			("outro", ["G", "A", "D", "D"])]
	total = sum(len(c) for _, c in form) * 4
	s = Song(bpm, total)
	bar = 0
	for part, cs in form:
		b0 = bar * 4
		for i, c in enumerate(cs):
			notes = chord_notes(c, 3)
			r = chord_notes(c, 2)[0]
			beat0 = b0 + i * 4
			for k in range(4):
				s.add(beat0 + k, pluck_bass(hz(r + (0 if k % 2 == 0 else 7)), 0.9 * s.spb), 0.8)
			# piano arpeggio in 8ths
			arp = notes + [notes[0] + 12] + notes[::-1][:3] + [notes[1]]
			for k in range(8):
				s.add(beat0 + k * 0.5, piano(hz(arp[k % len(arp)] + 12), 0.45 * s.spb, 0.6), 0.45)
			if part not in ("intro",):
				s.add(beat0, kick(0.8), 0.6)
				s.add(beat0 + 2, kick(0.7), 0.6)
				s.add(beat0 + 1, snare(0.6), 0.5)
				s.add(beat0 + 3, snare(0.6), 0.5)
				for k in range(4):
					s.add(beat0 + k + 0.5, hat(0.6), 0.5)
		if part == "intro":
			pad(s, b0, cs, 4, strings, 0.8, octave=3)
			s.line(b0, "A5:4 B5:4 A5:4 E5:4", whistle, 0.6)
		elif part == "V":
			s.line(b0, verse, whistle, 0.8)
			pad(s, b0, cs, 4, strings, 0.6, octave=3)
		elif part == "C":
			s.add(b0, crash(), 0.6)
			s.line(b0, chorus, brass, 0.75)
			s.line(b0, chorus, strings, 0.5, transpose=-12)
			pad(s, b0, cs, 4, choir, 0.6, octave=3)
		elif part == "V2":
			s.line(b0, verse, fiddle, 0.75)
			s.line(b0, verse, whistle, 0.4, transpose=-12)
			pad(s, b0, cs, 4, strings, 0.7, octave=3)
		elif part == "C2":
			s.add(b0, crash(), 0.8)
			s.line(b0, chorus, brass, 0.8)
			s.line(b0, chorus, fiddle, 0.5)
			s.line(b0, chorus, brass, 0.4, transpose=-12)
			pad(s, b0, cs, 4, choir, 0.7, octave=3)
		elif part == "outro":
			s.line(b0, "B5:4 C#6:4 D6:8", brass, 0.75)
			pad(s, b0, cs, 4, strings, 0.8, octave=3)
			s.add(b0 + 8, crash(), 0.7)
			s.add(b0 + 8, timpani(hz(midi("D2")), 2.0, 1.0), 0.8)
		bar += len(cs)
	return finish(s.render(0.22, 2.0, 0.7, tail=2.5))


ALL = {
	"boss_battle": boss_battle,
	"emperor_battle": emperor_battle,
	"fair_winds": fair_winds,
	"justice_marches": justice_marches,
	"toward_the_grand_line": toward_the_grand_line,
}
