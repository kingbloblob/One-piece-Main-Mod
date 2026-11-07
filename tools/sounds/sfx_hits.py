"""Devil Fruit hit sounds (played where a move lands) and a few special fruit sounds (Gear 5, healing).
Made from scratch like the rest of sfx.py. Which fruit uses which: sound/FruitSounds.java."""
import numpy as np

from synth import SR, bell, brass, choir, fft_filter, finish, hz, midi, noise, phase_of, reverb, silence, timpani, crash, \
	kick, snare, tom
from sfx import boom, crackle, metal, place, sweep_noise
from sfx_combat import drop, thud, whoosh, tone_glide


def t_of(d):
	return np.arange(int(d * SR)) / SR


def burn():
	buf = silence(1.0)
	place(buf, 0.0, thud(0.3, 70, 0.8))
	t = t_of(0.7)
	place(buf, 0.02, fft_filter(noise(0.7), 1500, 9000) * np.exp(-t / 0.25), 0.6)  # sizzle
	place(buf, 0.02, crackle(0.5, 40, 0.3))
	return finish(reverb(buf, 0.6, 0.2, 0.12))


def freeze():
	buf = silence(1.0)
	place(buf, 0.0, fft_filter(noise(0.05), 2000, 12000) * np.exp(-t_of(0.05) / 0.008), 1.0)
	rng = np.random.default_rng(21)
	for i in range(5):
		place(buf, 0.02 + i * 0.03, metal(rng.uniform(2500, 5000), 0.3, 0.3))
	place(buf, 0.0, thud(0.25, 100, 0.4))
	return finish(reverb(buf, 0.9, 0.3, 0.2, tone=10000))


def shock():
	buf = silence(0.9)
	place(buf, 0.0, crackle(0.35, 200, 0.9))
	n = int(0.3 * SR)
	buzz = np.sign(np.sin(phase_of(90, n))) * np.exp(-t_of(0.3) / 0.1)
	place(buf, 0.0, fft_filter(buzz, 100, 4000), 0.4)
	place(buf, 0.0, thud(0.25, 80, 0.5))
	return finish(reverb(buf, 0.6, 0.2, 0.15))


def flash():
	buf = silence(0.9)
	n = int(0.25 * SR)
	place(buf, 0.0, np.sin(phase_of(2400, n, glide=(4000, 0.2))) * np.exp(-t_of(0.25) / 0.08), 0.4)
	place(buf, 0.0, fft_filter(noise(0.1), 3000, 14000) * np.exp(-t_of(0.1) / 0.02), 0.8)
	place(buf, 0.02, thud(0.25, 90, 0.5))
	return finish(reverb(buf, 0.8, 0.3, 0.2, tone=11000))


def dark():
	buf = silence(1.0)
	place(buf, 0.0, thud(0.4, 45, 1.0))
	place(buf, 0.0, tone_glide(160, 50, 0.5, 0.5) * np.exp(-t_of(0.5) / 0.2))
	place(buf, 0.0, fft_filter(noise(0.5), 60, 600) * np.exp(-t_of(0.5) / 0.15), 0.6)
	return finish(reverb(buf, 1.0, 0.4, 0.2, tone=2500))


def blunt():
	buf = silence(0.8)
	place(buf, 0.0, thud(0.45, 52, 1.0))
	place(buf, 0.0, boom(0.6, 50, 100, 0.5))
	return finish(reverb(buf, 0.6, 0.2, 0.12))


def cut():
	buf = silence(0.7)
	place(buf, 0.0, whoosh(0.08, 3000, 9000, 0.7))
	place(buf, 0.05, fft_filter(noise(0.08), 600, 5000) * np.exp(-t_of(0.08) / 0.015), 1.0)
	place(buf, 0.05, thud(0.2, 120, 0.5))
	place(buf, 0.05, metal(3000, 0.3, 0.2))
	return finish(reverb(buf, 0.5, 0.2, 0.12))


def splat():
	buf = silence(0.8)
	place(buf, 0.0, fft_filter(noise(0.12), 300, 3000) * np.exp(-t_of(0.12) / 0.03), 1.0)
	rng = np.random.default_rng(22)
	for _ in range(6):
		place(buf, rng.uniform(0.0, 0.25), drop(rng.uniform(300, 900), 0.1), 0.4)
	place(buf, 0.0, thud(0.25, 90, 0.4))
	return finish(reverb(buf, 0.6, 0.2, 0.12))


def thorn():
	buf = silence(0.8)
	rng = np.random.default_rng(23)
	for i in range(4):
		f = rng.uniform(400, 1400)
		place(buf, i * 0.025, fft_filter(noise(0.05), f, f * 3) * np.exp(-t_of(0.05) / 0.01), 0.8)
	place(buf, 0.0, thud(0.3, 90, 0.7))
	return finish(reverb(buf, 0.6, 0.2, 0.12))


def dust():
	buf = silence(0.9)
	t = t_of(0.5)
	place(buf, 0.0, fft_filter(noise(0.5), 500, 6000) * np.exp(-t / 0.15) * (np.random.default_rng(24).random(len(t)) > 0.5), 0.9)
	place(buf, 0.0, thud(0.3, 70, 0.6))
	place(buf, 0.0, whoosh(0.4, 2000, 600, 0.4))
	return finish(reverb(buf, 0.7, 0.3, 0.15))


def bite():
	buf = silence(0.9)
	rng = np.random.default_rng(25)
	for i in range(5):  # crunch
		f = rng.uniform(300, 1200)
		place(buf, 0.02 + i * 0.02, fft_filter(noise(0.04), f, f * 3) * np.exp(-t_of(0.04) / 0.008), 0.8)
	place(buf, 0.0, thud(0.35, 60, 0.9))
	from sfx_moves import roar_tone
	place(buf, 0.05, roar_tone(110, 0.4, rough=1.0), 0.4)
	return finish(reverb(buf, 0.6, 0.2, 0.12))


def gear_five():
	"""Gear 5: a joyful pounding drum rhythm, like a heartbeat turned into a festival, and a bright brass call."""
	buf = silence(4.0)
	beat = 0.2
	pattern = [0, 2, 3, 4, 6, 7, 8, 10, 11, 12, 13, 14, 15]  # don, don-don-don, ... speeding up
	for step in pattern:
		place(buf, step * beat, tom(hz(midi("A2")), 0.9), 0.9)
		place(buf, step * beat, kick(0.7), 0.6)
	for step in (4, 8, 12, 14, 15):
		place(buf, step * beat, snare(0.6), 0.5)
	place(buf, 16 * beat, crash(1.0))
	for m in ("D4", "F#4", "A4", "D5"):
		place(buf, 16 * beat, brass(hz(midi(m)), 0.7, 1.0), 0.8)
	place(buf, 16 * beat, timpani(hz(midi("D2")), 1.0, 1.0))
	return finish(reverb(buf, 1.6, 0.6, 0.25))


def heal():
	"""Healing: soft chimes and a warm hum."""
	buf = silence(2.0)
	for i, m in enumerate(("C6", "E6", "G6", "C7")):
		place(buf, i * 0.1, bell(hz(midi(m)), 0.1, 0.5, decay=0.8))
	for m in ("C4", "G4"):
		place(buf, 0.0, choir(hz(midi(m)), 1.0, 0.5), 0.5)
	return finish(reverb(buf, 1.6, 0.6, 0.35, tone=9000))


def zoan_shift():
	"""Turning into a beast: bones creaking and stretching, then a snort."""
	buf = silence(1.6)
	rng = np.random.default_rng(26)
	for i in range(9):
		f = rng.uniform(150, 700)
		place(buf, 0.05 + i * 0.07, fft_filter(noise(0.06), f, f * 3) * np.exp(-t_of(0.06) / 0.015), 0.6)
	t = t_of(0.9)
	place(buf, 0.0, tone_glide(70, 45, 0.9, 0.6) * np.sin(np.pi * t / 0.9))
	place(buf, 0.8, fft_filter(noise(0.25), 200, 2500) * np.exp(-t_of(0.25) / 0.06), 0.8)  # snort
	return finish(reverb(buf, 0.9, 0.3, 0.15))


ALL = {
	"fruit_hit/burn": burn,
	"fruit_hit/freeze": freeze,
	"fruit_hit/shock": shock,
	"fruit_hit/flash": flash,
	"fruit_hit/dark": dark,
	"fruit_hit/blunt": blunt,
	"fruit_hit/cut": cut,
	"fruit_hit/splat": splat,
	"fruit_hit/thorn": thorn,
	"fruit_hit/dust": dust,
	"fruit_hit/bite": bite,
	"fruit_move/gear_five": gear_five,
	"fruit_move/heal": heal,
	"fruit_move/zoan_shift": zoan_shift,
}

SUBTITLES = {
	"fruit_hit/burn": "Something burns",
	"fruit_hit/freeze": "Something freezes",
	"fruit_hit/shock": "Something is shocked",
	"fruit_hit/flash": "A flash hits",
	"fruit_hit/dark": "Darkness hits",
	"fruit_hit/blunt": "A heavy hit",
	"fruit_hit/cut": "Something is cut",
	"fruit_hit/splat": "A wet hit",
	"fruit_hit/thorn": "Thorns stab",
	"fruit_hit/dust": "Dust bursts",
	"fruit_hit/bite": "A savage bite",
	"fruit_move/gear_five": "The drums of liberation",
	"fruit_move/heal": "Healing power",
	"fruit_move/zoan_shift": "A body changes shape",
}
