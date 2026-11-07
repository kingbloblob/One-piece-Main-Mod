"""
More Devil Fruit move sounds: each kind of Zoan animal gets its own cry (wolves howl, cats snarl, snakes hiss...),
plus Barrier walls, Nagi Nagi silence, and an awakening sound for each fruit type. Same tools as sfx_moves.py.
"""
import numpy as np

from synth import SR, bell, choir, fft_filter, finish, hz, midi, noise, phase_of, reverb, silence
from sfx import boom, crackle, metal, place, sweep_noise
from sfx_combat import rumble, thud, whoosh
from sfx_moves import roar_tone
from sfx_world import chitter, hiss, mix, voiced


def t_of(d):
	return np.arange(int(d * SR)) / SR


def lunge(buf, at=0.0, v=0.5):
	"""The rush of air as the animal pounces."""
	place(buf, at, whoosh(0.35, 400, 2500), v)


def howl():
	"""Wolf, jackal and fox Zoans: a rising howl and a snapping lunge."""
	buf = silence(1.8)
	place(buf, 0.0, voiced(330, 1.3, (600, 1600), rough=0.15, glide=1.6, breath=0.15), 0.8)
	place(buf, 0.05, voiced(660, 1.2, (900, 2400), rough=0.1, glide=1.5, breath=0.1), 0.25)
	lunge(buf, 1.15, 0.6)
	place(buf, 1.4, voiced(500, 0.15, (900, 2500), rough=0.9, glide=0.8), 0.6)  # snap
	return finish(reverb(buf, 1.4, 0.45, 0.25))


def snarl():
	"""Leopard and saber-tooth Zoans: a growl that bursts into a snarl."""
	buf = silence(1.3)
	place(buf, 0.0, roar_tone(120, 0.5, rough=1.0, formant=(400, 1200)), 0.5)
	place(buf, 0.4, roar_tone(170, 0.6, rough=0.9, formant=(700, 2200)), 1.0)
	place(buf, 0.4, hiss(0.4, 2000, 7000), 0.3)
	lunge(buf, 0.35, 0.5)
	return finish(reverb(buf, 1.0, 0.35, 0.18))


def snake():
	"""Snake Zoans: a long hiss and a fast strike."""
	buf = silence(1.2)
	t = t_of(0.8)
	place(buf, 0.0, hiss(0.8, 2500, 11000) * (0.8 + 0.2 * np.sin(2 * np.pi * 9 * t)), 0.7)
	place(buf, 0.75, whoosh(0.2, 800, 5000), 0.8)
	place(buf, 0.92, thud(0.25, 90, 0.6), 0.7)
	return finish(reverb(buf, 0.9, 0.3, 0.15))


def neigh():
	"""Horse Zoans: a whinny and galloping hooves."""
	buf = silence(1.6)
	t = t_of(0.8)
	place(buf, 0.0, voiced(520, 0.8, (900, 2500), rough=0.4, glide=0.65) * (1 + 0.7 * np.sin(2 * np.pi * 15 * t)), 0.8)
	for i, at in enumerate((0.85, 0.97, 1.15, 1.27)):
		place(buf, at, thud(0.12, 120 + 20 * (i % 2), 0.6), 0.6)
	return finish(reverb(buf, 1.0, 0.35, 0.18))


def bellow():
	"""Bison and giraffe Zoans: a deep bellow, a snort and a charge."""
	buf = silence(1.6)
	place(buf, 0.0, voiced(95, 0.9, (350, 1000), rough=0.6, glide=1.15), 0.9)
	place(buf, 0.85, hiss(0.25, 300, 2500), 0.5)
	for i in range(4):
		place(buf, 1.0 + i * 0.13, thud(0.15, 70, 0.7), 0.6)
	return finish(reverb(buf, 1.2, 0.4, 0.2))


def trumpet():
	"""Elephant and mammoth Zoans: a blaring trumpet call and a heavy stomp."""
	buf = silence(2.0)
	n = int(1.0 * SR)
	t = t_of(1.0)
	f = 420 * (1 + 0.25 * np.sin(np.pi * t)) * (1 + 0.02 * np.sin(2 * np.pi * 7 * t))
	ph = 2 * np.pi * np.cumsum(f) / SR
	call = sum(np.sin(k * ph) / k ** 0.8 for k in range(1, 14)) * (1 + 0.5 * fft_filter(noise(1.0), 30, 120) * 3)
	call = fft_filter(call, 300, 4000) * np.sin(np.pi * t) ** 0.4
	place(buf, 0.0, call, 0.45)
	place(buf, 1.05, boom(0.9, 40, 60, 1.0), 0.8)
	place(buf, 1.05, rumble(0.6), 0.3)
	return finish(reverb(buf, 1.6, 0.5, 0.25))


def spider():
	"""Spider Zoans: clicking legs, a hiss and silk shooting out."""
	buf = silence(1.2)
	place(buf, 0.0, chitter(0.5, 45, 3500, 4), 0.9)
	place(buf, 0.3, hiss(0.3, 3000, 9000), 0.4)
	place(buf, 0.6, sweep_noise(0.35, 6000, 1500), 0.6)
	return finish(reverb(buf, 0.8, 0.3, 0.15))


def stomp():
	"""Triceratops and Pachycephalosaurus Zoans: a snort, a charge and a skull-crack headbutt."""
	buf = silence(1.6)
	place(buf, 0.0, roar_tone(80, 0.6, rough=1.0, formant=(300, 900)), 0.7)
	for i in range(3):
		place(buf, 0.45 + i * 0.16, thud(0.18, 60, 0.8), 0.7)
	place(buf, 0.95, boom(0.6, 50, 140, 1.0), 0.9)
	place(buf, 0.95, fft_filter(noise(0.08), 500, 5000) * np.exp(-t_of(0.08) / 0.015), 0.9)
	return finish(reverb(buf, 1.2, 0.4, 0.2))


def dig():
	"""Mole Zoans: fast scratching claws, then bursting out of the ground."""
	buf = silence(1.3)
	rng = np.random.default_rng(3)
	for i in range(10):
		place(buf, i * 0.06, fft_filter(noise(0.05), 800, 4000) * np.exp(-t_of(0.05) / 0.012), rng.uniform(0.5, 0.9))
	place(buf, 0.7, boom(0.5, 60, 90, 0.8), 0.7)
	place(buf, 0.7, fft_filter(noise(0.5), 200, 3000) * np.exp(-t_of(0.5) / 0.15), 0.6)
	return finish(reverb(buf, 0.9, 0.3, 0.15))


def barrier():
	"""Bari Bari no Mi: a glassy wall snapping into place, ringing."""
	buf = silence(1.6)
	place(buf, 0.0, sweep_noise(0.15, 1500, 7000), 0.4)
	for f, v in ((880, 0.6), (1320, 0.4), (1760, 0.3), (2640, 0.2)):
		place(buf, 0.1, bell(f, 1.3, v, decay=0.6), 1.0)
	place(buf, 0.1, metal(1200, 0.5, 0.5), 0.5)
	return finish(reverb(buf, 1.6, 0.5, 0.3))


def hush():
	"""Nagi Nagi no Mi: every sound around you drains away into silence."""
	buf = silence(1.5)
	t = t_of(1.2)
	x = fft_filter(noise(1.2), 300, 6000) * np.exp(-t / 0.25)
	place(buf, 0.0, x, 0.5)
	place(buf, 0.0, sweep_noise(1.0, 5000, 200) * np.exp(-t_of(1.0) / 0.3), 0.4)
	return finish(reverb(buf, 2.0, 0.6, 0.35))


def awaken_logia():
	"""A Logia awakens: the user's element floods out in a widening rush."""
	buf = silence(2.6)
	place(buf, 0.0, sweep_noise(1.6, 150, 6000) * np.sin(np.pi * t_of(1.6) / 1.6) ** 0.7, 0.7)
	place(buf, 0.3, crackle(1.2, 40, 0.5), 0.4)
	place(buf, 1.3, boom(1.2, 34, 60, 1.0), 0.8)
	for m in ("D4", "A4", "D5", "F5"):
		place(buf, 1.3, choir(hz(midi(m)), 1.0, 0.8), 0.5)
	return finish(reverb(buf, 2.2, 0.7, 0.3))


def awaken_zoan():
	"""A Zoan awakens: the body swells, bones creak and a giant beast roars."""
	buf = silence(2.6)
	place(buf, 0.0, rumble(1.0, 1.0), 0.5)
	for i in range(6):
		place(buf, 0.1 + i * 0.13, thud(0.15, 90 - i * 8, 0.6), 0.5)
	place(buf, 0.9, roar_tone(70, 1.5, rough=1.0, formant=(320, 1000)), 1.0)
	place(buf, 0.95, roar_tone(140, 1.2, rough=0.7, formant=(600, 1700)), 0.4)
	return finish(reverb(buf, 2.0, 0.6, 0.28))


def awaken_paramecia():
	"""A Paramecia awakens: the ground and walls around you start to change."""
	buf = silence(2.6)
	place(buf, 0.0, rumble(1.4, 1.0), 0.6)
	rng = np.random.default_rng(9)
	for i in range(8):
		place(buf, 0.2 + i * 0.12, fft_filter(noise(0.1), 300, 3000) * np.exp(-t_of(0.1) / 0.03), rng.uniform(0.4, 0.8))
	place(buf, 1.2, boom(1.0, 40, 90, 1.0), 0.8)
	for m in ("A3", "E4", "A4", "C#5"):
		place(buf, 1.2, bell(hz(midi(m)), 1.2, 0.6), 0.4)
	return finish(reverb(buf, 2.0, 0.6, 0.28))


ALL = {
	"fruit_move/howl": howl,
	"fruit_move/snarl": snarl,
	"fruit_move/snake": snake,
	"fruit_move/neigh": neigh,
	"fruit_move/bellow": bellow,
	"fruit_move/trumpet": trumpet,
	"fruit_move/spider": spider,
	"fruit_move/stomp": stomp,
	"fruit_move/dig": dig,
	"fruit_move/barrier": barrier,
	"fruit_move/hush": hush,
	"devil_fruit/awaken_logia": awaken_logia,
	"devil_fruit/awaken_zoan": awaken_zoan,
	"devil_fruit/awaken_paramecia": awaken_paramecia,
}

SUBTITLES = {
	"fruit_move/howl": "A wolf howls",
	"fruit_move/snarl": "A big cat snarls",
	"fruit_move/snake": "A snake strikes",
	"fruit_move/neigh": "A horse charges",
	"fruit_move/bellow": "A beast charges",
	"fruit_move/trumpet": "An elephant trumpets",
	"fruit_move/spider": "A spider strikes",
	"fruit_move/stomp": "A dinosaur charges",
	"fruit_move/dig": "Something burrows",
	"fruit_move/barrier": "A barrier forms",
	"fruit_move/hush": "Sound goes silent",
	"devil_fruit/awaken_logia": "An element surges",
	"devil_fruit/awaken_zoan": "A beast awakens",
	"devil_fruit/awaken_paramecia": "The world reshapes",
}
