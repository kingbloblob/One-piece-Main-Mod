"""
Three more sea shanties for sailing, written for this mod (original melodies, nothing copied).
Same tools as music.py: melodies are 'NOTE:beats' strings.
"""
from synth import (Song, accordion, brass, choir, fiddle, finish, hat, hz, kick, midi, piano, pluck_bass, snare,
				   strings, tambourine, tom, whistle)
from music import chord_notes, name_of, pad


def beats(line):
	return sum(float(tok.split(":")[1]) for tok in line.split())


def check(line, bars, per_bar, name):
	got = beats(line)
	assert abs(got - bars * per_bar) < 1e-6, f"{name}: {got} beats, want {bars * per_bar}"


def chord(s, beat, c, dur, inst, gain, octave=3, **kw):
	s.chord(beat, " ".join(name_of(m) for m in chord_notes(c, octave)), dur, inst, gain, **kw)


# ===================================================================== Drink to the Horizon
# A quick 6/8 jig in D: fiddle and accordion, foot stomps and tambourine. Played once.

def drink_to_the_horizon():
	bpm = 330  # eighth notes per minute; a bar is 6 eighths
	A_chords = ["D", "G", "D", "A", "D", "G", "A", "D"]
	B_chords = ["Bm", "G", "D", "A", "Bm", "G", "A", "D"]
	A_mel = ("A4:1 D5:1 F#5:1 A5:2 F#5:1 "
			 "G5:1 B5:1 G5:1 D5:2 B4:1 "
			 "A4:1 D5:1 F#5:1 A5:1 B5:1 A5:1 "
			 "G5:1 F#5:1 E5:1 C#5:2 A4:1 "
			 "A4:1 D5:1 F#5:1 A5:2 D6:1 "
			 "B5:2 G5:1 D5:2 G5:1 "
			 "F#5:1 E5:1 D5:1 E5:1 F#5:1 G5:1 "
			 "F#5:3 D5:3")
	B_mel = ("B5:2 C#6:1 D6:2 B5:1 "
			 "G5:2 A5:1 B5:2 G5:1 "
			 "F#5:1 G5:1 A5:1 D6:2 A5:1 "
			 "E5:2 F#5:1 G5:2 E5:1 "
			 "F#5:1 B5:1 D6:1 F#6:2 D6:1 "
			 "E6:1 D6:1 B5:1 G5:2 B5:1 "
			 "A5:1 G5:1 F#5:1 E5:2 C#5:1 "
			 "D5:6")
	check(A_mel, 8, 6, "jig A")
	check(B_mel, 8, 6, "jig B")
	form = [("intro", ["D", "A"]), ("A", A_chords), ("A2", A_chords), ("B", B_chords), ("A3", A_chords),
			("B2", B_chords), ("A4", A_chords), ("B3", B_chords), ("A5", A_chords), ("outro", ["G", "A", "D"])]
	total = sum(len(c) for _, c in form) * 6
	s = Song(bpm, total)
	bar = 0
	for part, cs in form:
		b0 = bar * 6
		for i, c in enumerate(cs):
			notes = chord_notes(c, 3)
			beat0 = b0 + i * 6
			s.add(beat0, pluck_bass(hz(notes[0] - 12), 1.6 * s.spb), 0.9)
			s.add(beat0 + 3, pluck_bass(hz(notes[0] - 5), 1.6 * s.spb), 0.75)
			for k in (1, 2, 4, 5):
				chord(s, beat0 + k, c, 0.7 * s.spb, accordion, 0.35)
			s.add(beat0, kick(0.7), 0.55)  # stomp
			s.add(beat0 + 3, kick(0.6), 0.5)
			for k in range(6):
				s.add(beat0 + k, tambourine(1.0 if k in (0, 3) else 0.45), 0.7)
		if part == "intro":
			s.line(b0, "A4:3 D5:3 E5:3 C#5:3", fiddle, 0.7)
		elif part == "A":
			s.line(b0, A_mel, fiddle, 1.0)
		elif part == "A2":
			s.line(b0, A_mel, fiddle, 0.9)
			s.line(b0, A_mel, whistle, 0.45, transpose=12)
		elif part == "B":
			s.line(b0, B_mel, accordion, 1.0)
			s.line(b0, B_mel, fiddle, 0.4, transpose=-12)
		elif part == "A3":
			s.line(b0, A_mel, whistle, 0.8)
			s.line(b0, A_mel, accordion, 0.6, transpose=-12)
		elif part == "B2":
			s.line(b0, B_mel, fiddle, 0.9)
			s.line(b0, B_mel, whistle, 0.4, transpose=12)
		elif part == "A4":  # quieter: just accordion and stomps
			s.line(b0, A_mel, accordion, 0.8)
		elif part == "B3":
			s.line(b0, B_mel, whistle, 0.7)
			s.line(b0, B_mel, accordion, 0.5, transpose=-12)
		elif part == "A5":
			s.line(b0, A_mel, fiddle, 1.0)
			s.line(b0, A_mel, accordion, 0.6)
			s.line(b0, A_mel, whistle, 0.4, transpose=12)
		elif part == "outro":
			s.line(b0, "B5:3 G5:3 A5:3 C#6:3 D6:6", fiddle, 0.9)
			s.line(b0, "G4:3 D5:3 E5:3 A4:3 F#5:6", accordion, 0.6)
		bar += len(cs)
	return finish(s.render(0.2, 1.6, 0.55, tail=2.0))


# ===================================================================== Haul the Anchor
# A slow, heavy work song in A minor. A lone horn calls, the whole crew answers. Stomp, stomp, clap.

def haul_the_anchor():
	bpm = 96
	chords = ["Am", "Am", "G", "Am", "Am", "C", "G", "Am"]
	call = ("E4:1.5 A4:0.5 A4:1 B4:1 "
			"C5:2 B4:1 A4:1 "
			"G4:1.5 B4:0.5 D5:1 B4:1 "
			"A4:3 r:1 ")
	answer = ("E5:1.5 E5:0.5 D5:1 C5:1 "
			  "E5:2 G5:1 E5:1 "
			  "D5:1.5 C5:0.5 B4:1 G4:1 "
			  "A4:3 r:1")
	verse = call + answer
	bridge_chords = ["F", "G", "Em", "Am", "F", "G", "E", "E"]
	bridge = ("A4:1 C5:1 F5:2 "
			  "D5:1 E5:1 G5:2 "
			  "E5:1 D5:1 B4:2 "
			  "C5:2 A4:2 "
			  "A4:1 C5:1 F5:2 "
			  "G5:1 F5:1 D5:2 "
			  "E5:2 G#5:2 "
			  "B5:4")
	check(verse, 8, 4, "anchor verse")
	check(bridge, 8, 4, "anchor bridge")
	form = [("intro", ["Am", "Am"]), ("V1", chords), ("V2", chords), ("bridge", bridge_chords), ("V3", chords),
			("V4", chords), ("outro", ["Am", "G", "Am"])]
	total = sum(len(c) for _, c in form) * 4
	s = Song(bpm, total)
	bar = 0
	for part, cs in form:
		b0 = bar * 4
		for i, c in enumerate(cs):
			beat0 = b0 + i * 4
			r = chord_notes(c, 2)[0]
			# Stomp, stomp, CLAP: the rhythm of hauling a rope.
			s.add(beat0, kick(1.0), 0.8)
			s.add(beat0 + 1, kick(0.8), 0.7)
			s.add(beat0 + 2, snare(0.9, 0.18), 0.7)
			s.add(beat0, tom(hz(r), 0.8), 0.4)
			if part not in ("intro",):
				s.add(beat0, pluck_bass(hz(r), 1.8 * s.spb), 0.8)
				s.add(beat0 + 2, pluck_bass(hz(r + 7), 1.8 * s.spb), 0.65)
			if part in ("V2", "V3", "V4", "bridge"):
				chord(s, beat0, c, 3.9 * s.spb, accordion, 0.45)
		if part == "intro":
			s.line(b0 + 4, "r:2 E4:1 A4:1", brass, 0.6)
		elif part in ("V1", "V2", "V3", "V4"):
			loud = {"V1": 0.7, "V2": 0.85, "V3": 0.95, "V4": 1.0}[part]
			# The call: one voice (a horn), then the crew answers in a big choir.
			s.line(b0, call, brass if part != "V3" else fiddle, 0.7)
			s.line(b0 + 16, answer, choir, 1.2 * loud, legato=0.98)
			s.line(b0 + 16, answer, choir, 0.8 * loud, legato=0.98, transpose=-12)
			if part == "V4":
				s.line(b0 + 16, answer, brass, 0.4)
				s.line(b0, call, choir, 0.5, legato=0.98, transpose=12)
		elif part == "bridge":
			s.line(b0, bridge, fiddle, 0.9)
			pad(s, b0, cs, 4, strings, 0.6, octave=3)
		elif part == "outro":
			s.line(b0, "E5:2 C5:2 D5:2 B4:2 A4:4", choir, 1.2, legato=0.98)
			s.line(b0, "C5:2 A4:2 B4:2 G4:2 E4:4", choir, 0.8, legato=0.98)
		bar += len(cs)
	return finish(s.render(0.25, 2.0, 0.7, tail=2.5))


# ===================================================================== Lantern on the Waves
# A gentle night waltz in E minor for sailing under the stars. Played once.

def lantern_on_the_waves():
	bpm = 88
	A_chords = ["Em", "C", "G", "D", "Em", "C", "Am", "B"]
	B_chords = ["C", "G", "Am", "Em", "C", "G", "B", "Em"]
	A_mel = ("B4:2 E5:1 "
			 "G5:2 E5:1 "
			 "D5:2 B4:1 "
			 "A4:3 "
			 "B4:2 E5:1 "
			 "G5:1 A5:1 G5:1 "
			 "E5:2 C5:1 "
			 "D#5:3")
	B_mel = ("E5:1 G5:1 C6:1 "
			 "B5:2 G5:1 "
			 "A5:1 C6:1 E6:1 "
			 "B5:3 "
			 "E5:1 G5:1 C6:1 "
			 "D6:2 B5:1 "
			 "A5:2 F#5:1 "
			 "E5:3")
	check(A_mel, 8, 3, "waltz A")
	check(B_mel, 8, 3, "waltz B")
	form = [("intro", ["Em", "C", "Em", "B"]), ("A", A_chords), ("B", B_chords), ("A2", A_chords),
			("B2", B_chords), ("outro", ["C", "B", "Em", "Em"])]
	total = sum(len(c) for _, c in form) * 3
	s = Song(bpm, total)
	bar = 0
	for part, cs in form:
		b0 = bar * 3
		for i, c in enumerate(cs):
			notes = chord_notes(c, 3)
			beat0 = b0 + i * 3
			s.add(beat0, pluck_bass(hz(notes[0] - 12), 2.6 * s.spb, 0.7), 0.7)
			# The waves: a slow rolling piano arpeggio.
			arp = [notes[0], notes[1], notes[2], notes[0] + 12, notes[2], notes[1]]
			for k in range(6):
				s.add(beat0 + k * 0.5, piano(hz(arp[k] + 12), 0.8 * s.spb, 0.5), 0.35)
			if part != "intro":
				chord(s, beat0 + 1, c, 1.8 * s.spb, accordion, 0.22)
		if part == "intro":
			pad(s, b0, cs, 3, strings, 0.6, octave=3)
		elif part == "A":
			s.line(b0, A_mel, whistle, 0.75)
			pad(s, b0, cs, 3, strings, 0.45, octave=3)
		elif part == "B":
			s.line(b0, B_mel, fiddle, 0.7)
			pad(s, b0, cs, 3, strings, 0.5, octave=3)
		elif part == "A2":
			s.line(b0, A_mel, accordion, 0.7)
			s.line(b0, A_mel, whistle, 0.35, transpose=12)
			pad(s, b0, cs, 3, choir, 0.4, octave=3, vowel="oo")
		elif part == "B2":
			s.line(b0, B_mel, fiddle, 0.75)
			s.line(b0, B_mel, whistle, 0.35, transpose=-12)
			pad(s, b0, cs, 3, choir, 0.45, octave=3, vowel="oo")
		elif part == "outro":
			s.line(b0, "E5:3 D#5:3 E5:6", whistle, 0.6)
			pad(s, b0, cs, 3, strings, 0.55, octave=3)
		bar += len(cs)
	return finish(s.render(0.3, 2.4, 0.9, tail=3.0))


ALL = {
	"drink_to_the_horizon": drink_to_the_horizon,
	"haul_the_anchor": haul_the_anchor,
	"lantern_on_the_waves": lantern_on_the_waves,
}
