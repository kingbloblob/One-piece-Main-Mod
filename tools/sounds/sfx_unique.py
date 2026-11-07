"""
2026-11-05: 18 more Devil Fruit move sounds, for fruits that still shared a sound with other fruits
(Bubble, Warp, Curse groups and others). Same tools as sfx_polish.py: pure math, no samples.
Which fruit plays which: source/.../sound/FruitSounds.java.
"""
import numpy as np

from synth import SR, bell, choir, fft_filter, finish, hz, midi, noise, phase_of, reverb, silence
from sfx import boom, crackle, metal, place, sweep_noise
from sfx_combat import drop, rumble, thud, tone_glide, whoosh
from sfx_world import creak, hiss, voiced


def t_of(d):
	return np.arange(int(d * SR)) / SR


def glide(f0, f1, d, shape=2.0):
	t = t_of(d)
	return np.sin(phase_of(f1, len(t), glide=(f0, d))) * np.sin(np.pi * t / d) ** shape


def wash():
	"""Woshu Woshu no Mi: a soapy scrub, sloshing water and squeaky-clean bubbles."""
	buf = silence(1.4)
	rng = np.random.default_rng(31)
	for i in range(6):  # scrub, scrub
		place(buf, i * 0.11, fft_filter(noise(0.09), 1500, 7000) * np.sin(np.pi * t_of(0.09) / 0.09), 0.5)
	place(buf, 0.3, whoosh(0.5, 300, 1500), 0.5)
	for i in range(10):
		place(buf, 0.35 + i * 0.05 + rng.uniform(0, 0.03), drop(rng.uniform(700, 1600), 0.08), 0.35)
	place(buf, 0.8, glide(2400, 3200, 0.18), 0.12)  # squeak
	return finish(reverb(buf, 1.0, 0.35, 0.2))


def float_up():
	"""Fuwa Fuwa no Mi: things lift off the ground with a soft, rising, airy shimmer."""
	buf = silence(1.8)
	place(buf, 0.0, sweep_noise(1.2, 300, 3500) * np.sin(np.pi * t_of(1.2) / 1.2), 0.4)
	place(buf, 0.0, glide(220, 660, 1.2, 1.0), 0.18)
	for i, m in enumerate(("C5", "E5", "G5", "C6", "E6")):
		place(buf, 0.25 + i * 0.15, bell(hz(midi(m)), 0.3, 0.6, decay=0.7), 0.3)
	return finish(reverb(buf, 1.8, 0.55, 0.32))


def hormone():
	"""Horu Horu no Mi: a syringe's hiss, a pump, and a heartbeat speeding up."""
	buf = silence(1.6)
	place(buf, 0.0, hiss(0.35, 4000, 12000), 0.4)
	click = fft_filter(noise(0.03), 1500, 6000) * np.exp(-t_of(0.03) / 0.005)
	place(buf, 0.36, click, 0.6)
	for i, at in enumerate((0.5, 0.75, 0.95, 1.1, 1.22, 1.32)):
		place(buf, at, thud(0.2, 50, 0.8), 0.6)
		place(buf, at + 0.09, thud(0.15, 45, 0.5), 0.4)
	return finish(reverb(buf, 0.8, 0.3, 0.15))


def swim():
	"""Sui Sui no Mi: diving into solid ground as if it were water, a deep splash and ripples."""
	buf = silence(1.6)
	place(buf, 0.0, whoosh(0.25, 400, 3000), 0.5)
	place(buf, 0.2, thud(0.4, 60, 0.7), 0.6)
	place(buf, 0.2, fft_filter(noise(0.4), 300, 4000) * np.exp(-t_of(0.4) / 0.1), 0.6)
	rng = np.random.default_rng(12)
	for i in range(8):
		place(buf, 0.3 + i * 0.09, drop(rng.uniform(300, 700), 0.15), 0.4 * (1 - i / 10))
	return finish(reverb(buf, 1.2, 0.4, 0.25))


def spin():
	"""Guru Guru no Mi: a propeller whirring up to full speed."""
	buf = silence(1.6)
	d = 1.3
	t = t_of(d)
	rate = 6 + 34 * (t / d) ** 0.7
	chop = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * np.cumsum(rate) / SR))
	x = fft_filter(noise(d), 200, 3000) * chop * np.sin(np.pi * t / d) ** 0.4
	place(buf, 0.0, x, 0.7)
	place(buf, 0.0, tone_glide(80, 220, d, 0.25) * np.sin(np.pi * t / d), 1.0)
	return finish(reverb(buf, 0.8, 0.3, 0.15))


def crunch():
	"""Bisu Bisu no Mi: biscuit armor forming with crunchy, crumbly snaps."""
	buf = silence(1.2)
	rng = np.random.default_rng(17)
	for i in range(14):
		ln = rng.uniform(0.02, 0.05)
		f = rng.uniform(800, 3000)
		x = fft_filter(noise(ln + 0.02), f, f * 3)[: int(ln * SR)] * np.exp(-np.arange(int(ln * SR)) / SR / (ln / 3))
		place(buf, i * 0.045 + rng.uniform(0, 0.02), x, rng.uniform(0.5, 1.0))
	place(buf, 0.6, thud(0.3, 80, 0.6), 0.6)
	return finish(reverb(buf, 0.7, 0.3, 0.15))


def copy():
	"""Mane Mane no Mi: a face shifting into someone else's, a rubbery wobble and a pop."""
	buf = silence(1.4)
	t = t_of(0.8)
	f = 300 * (1 + 0.25 * np.sin(2 * np.pi * 9 * t) * np.exp(-t / 0.4))
	ph = 2 * np.pi * np.cumsum(f) / SR
	place(buf, 0.0, (np.sin(ph) + 0.4 * np.sin(2 * ph)) * np.sin(np.pi * t / 0.8), 0.3)
	place(buf, 0.75, glide(400, 1200, 0.08, 0.5), 0.4)  # pop
	place(buf, 0.8, bell(hz(midi("A6")), 0.3, 0.5, decay=0.4), 0.3)
	return finish(reverb(buf, 0.9, 0.3, 0.2))


def memory():
	"""Memo Memo no Mi: a film reel clicking as memories are cut and spliced."""
	buf = silence(1.6)
	for i in range(16):
		tick = fft_filter(noise(0.02), 2000, 8000) * np.exp(-t_of(0.02) / 0.003)
		place(buf, i * 0.05, tick, 0.5 if i % 4 else 0.8)
	place(buf, 0.0, fft_filter(noise(0.8), 60, 400) * 0.6, 0.5)  # the projector's hum
	place(buf, 0.85, fft_filter(noise(0.06), 1000, 9000) * np.exp(-t_of(0.06) / 0.01), 0.8)  # snip
	for i, m in enumerate(("E6", "B5", "G5")):
		place(buf, 0.9 + i * 0.12, bell(hz(midi(m)), 0.4, 0.5, decay=0.6), 0.3)
	return finish(reverb(buf, 1.4, 0.45, 0.28))


def toy():
	"""Hobi Hobi no Mi: a wind-up key turning and a little toy tune."""
	buf = silence(1.8)
	for i in range(6):  # wind-up ratchet
		place(buf, i * 0.07, fft_filter(noise(0.03), 1500, 6000) * np.exp(-t_of(0.03) / 0.004), 0.6)
	for i, m in enumerate(("C6", "E6", "G6", "E6", "C7")):
		place(buf, 0.5 + i * 0.12, bell(hz(midi(m)), 0.3, 0.7, decay=0.45), 0.4)
	place(buf, 1.15, glide(900, 300, 0.25, 0.5), 0.2)  # boing
	return finish(reverb(buf, 1.0, 0.35, 0.22))


def love():
	"""Mero Mero no Mi: a sweet, swooning chime and a heart-shaped beam that hums."""
	buf = silence(1.8)
	for i, m in enumerate(("A5", "C#6", "E6", "A6")):
		place(buf, i * 0.07, bell(hz(midi(m)), 0.5, 0.6, decay=0.8), 0.35)
	place(buf, 0.0, choir(hz(midi("A4")), 1.1, 0.6, vowel="oo"), 0.4)
	t = t_of(0.9)
	place(buf, 0.35, np.sin(phase_of(880, len(t), glide=(1320, 0.9))) * np.sin(np.pi * t / 0.9) ** 2
		  * (0.7 + 0.3 * np.sin(2 * np.pi * 6 * t)), 0.18)
	return finish(reverb(buf, 1.8, 0.55, 0.35, tone=9000))


def ghost():
	"""Horo Horo no Mi: little ghosts giggling and a hollow, sinking wail."""
	buf = silence(1.8)
	place(buf, 0.0, voiced(520, 1.2, (500, 1500), rough=0.05, glide=0.5, breath=0.5, buzz=6), 0.4)
	for i in range(5):  # giggles
		place(buf, 0.9 + i * 0.09, glide(900 + i * 60, 1200 + i * 60, 0.07, 1.0), 0.2)
	place(buf, 0.0, fft_filter(noise(1.4), 200, 900) * np.sin(np.pi * t_of(1.4) / 1.4), 0.25)
	return finish(reverb(buf, 2.0, 0.6, 0.4))


def straw():
	"""Wara Wara no Mi: dry straw rustling and twisting into a doll."""
	buf = silence(1.4)
	rng = np.random.default_rng(41)
	for i in range(30):
		ln = rng.uniform(0.01, 0.04)
		x = fft_filter(noise(ln + 0.01), 2500, 9000)[: int(ln * SR)]
		place(buf, rng.uniform(0, 0.9), x * np.hanning(len(x)), rng.uniform(0.2, 0.7))
	place(buf, 0.0, creak(260, 0.5, seed=8), 0.25)
	place(buf, 0.9, thud(0.2, 120, 0.5), 0.4)
	return finish(reverb(buf, 0.8, 0.3, 0.15))


def room():
	"""Ope Ope no Mi: the blue Room dome spreads out with a low hum, then a bright Shambles swap."""
	buf = silence(1.8)
	t = t_of(1.2)
	hum = (np.sin(2 * np.pi * 110 * t) + 0.5 * np.sin(2 * np.pi * 165 * t)) * np.sin(np.pi * t / 1.2) ** 0.5
	place(buf, 0.0, hum, 0.3)
	place(buf, 0.0, sweep_noise(1.0, 400, 2500) * np.sin(np.pi * t_of(1.0) / 1.0), 0.3)
	place(buf, 0.9, glide(1800, 600, 0.12, 0.5), 0.35)  # the swap
	place(buf, 0.9, fft_filter(noise(0.05), 3000, 10000) * np.exp(-t_of(0.05) / 0.008), 0.6)
	place(buf, 1.0, glide(600, 1800, 0.12, 0.5), 0.35)
	return finish(reverb(buf, 1.4, 0.45, 0.25))


def sticky():
	"""Mochi Mochi no Mi: thick, stretchy mochi pulling and slapping."""
	buf = silence(1.4)
	t = t_of(0.6)
	stretch = fft_filter(noise(0.6), 150, 1200) * (0.6 + 0.4 * np.sin(2 * np.pi * 13 * t)) * np.sin(np.pi * t / 0.6)
	place(buf, 0.0, stretch, 0.7)
	place(buf, 0.0, glide(140, 80, 0.6, 1.0), 0.3)
	place(buf, 0.6, thud(0.4, 70, 0.9), 0.8)
	place(buf, 0.62, fft_filter(noise(0.12), 400, 3000) * np.exp(-t_of(0.12) / 0.03), 0.5)  # splat
	return finish(reverb(buf, 0.8, 0.3, 0.15))


def soul():
	"""Yomi Yomi no Mi: a mournful violin note and the chill of the underworld."""
	buf = silence(2.0)
	from synth import fiddle
	place(buf, 0.0, fiddle(hz(midi("E5")), 0.9, 0.8), 0.5)
	place(buf, 0.6, fiddle(hz(midi("B4")), 0.8, 0.7), 0.4)
	rng = np.random.default_rng(3)
	for i in range(8):  # ice forming
		place(buf, 0.4 + i * 0.08, bell(rng.uniform(3000, 5000), 0.15, 0.6, decay=0.25), 0.25)
	place(buf, 0.0, sweep_noise(1.4, 3000, 800) * np.sin(np.pi * t_of(1.4) / 1.4), 0.25)
	return finish(reverb(buf, 1.8, 0.55, 0.35))


def gas():
	"""Gasu Gasu no Mi: a hissing poison-gas cloud rolling out, with a sharp flick of flame."""
	buf = silence(1.6)
	place(buf, 0.0, hiss(1.2, 1500, 8000), 0.6)
	place(buf, 0.0, fft_filter(noise(1.2), 80, 500) * np.sin(np.pi * t_of(1.2) / 1.2), 0.5)
	place(buf, 0.9, crackle(0.3, 80), 0.5)
	return finish(reverb(buf, 1.2, 0.4, 0.2))


def bloom():
	"""Hana Hana no Mi: arms bloom like flowers with soft petal flutters, then a sharp clutch."""
	buf = silence(1.4)
	rng = np.random.default_rng(23)
	for i in range(8):
		f = rng.uniform(700, 1400)
		place(buf, i * 0.06, fft_filter(noise(0.08), f, f * 3) * np.sin(np.pi * t_of(0.08) / 0.08), 0.4)
		place(buf, i * 0.06, bell(rng.uniform(1500, 2500), 0.15, 0.5, decay=0.3), 0.15)
	place(buf, 0.65, thud(0.3, 90, 0.8), 0.7)
	place(buf, 0.66, fft_filter(noise(0.05), 1000, 6000) * np.exp(-t_of(0.05) / 0.01), 0.6)  # crack
	return finish(reverb(buf, 1.0, 0.35, 0.22))


def magnet():
	"""Jiki Jiki no Mi: a buzzing magnetic hum and scrap metal clanking together."""
	buf = silence(1.6)
	t = t_of(1.1)
	buzz = np.sign(np.sin(2 * np.pi * 60 * t)) * 0.3 + np.sin(2 * np.pi * 120 * t) * 0.4
	place(buf, 0.0, fft_filter(buzz, 50, 2000) * np.sin(np.pi * t / 1.1) ** 0.5, 0.45)
	rng = np.random.default_rng(29)
	for i in range(6):
		place(buf, 0.3 + i * 0.1 + rng.uniform(0, 0.03), metal(rng.uniform(400, 1100), 0.4, 0.6), 0.35)
	place(buf, 0.95, thud(0.3, 80, 0.7), 0.6)
	return finish(reverb(buf, 0.9, 0.3, 0.18))


ALL = {
	"fruit_move/wash": wash,
	"fruit_move/float": float_up,
	"fruit_move/hormone": hormone,
	"fruit_move/swim": swim,
	"fruit_move/spin": spin,
	"fruit_move/crunch": crunch,
	"fruit_move/copy": copy,
	"fruit_move/memory": memory,
	"fruit_move/toy": toy,
	"fruit_move/love": love,
	"fruit_move/ghost": ghost,
	"fruit_move/straw": straw,
	"fruit_move/room": room,
	"fruit_move/sticky": sticky,
	"fruit_move/soul": soul,
	"fruit_move/gas": gas,
	"fruit_move/bloom": bloom,
	"fruit_move/magnet": magnet,
}

SUBTITLES = {
	"fruit_move/wash": "Something is scrubbed clean",
	"fruit_move/float": "Something floats up",
	"fruit_move/hormone": "Hormones pump",
	"fruit_move/swim": "Someone dives into the ground",
	"fruit_move/spin": "A propeller whirs",
	"fruit_move/crunch": "Biscuits crunch",
	"fruit_move/copy": "A face changes",
	"fruit_move/memory": "A memory is cut",
	"fruit_move/toy": "A toy winds up",
	"fruit_move/love": "A love beam hums",
	"fruit_move/ghost": "Ghosts wail",
	"fruit_move/straw": "Straw rustles",
	"fruit_move/room": "A Room spreads out",
	"fruit_move/sticky": "Mochi stretches",
	"fruit_move/soul": "A ghostly violin plays",
	"fruit_move/gas": "Gas hisses",
	"fruit_move/bloom": "Arms bloom",
	"fruit_move/magnet": "Magnetism hums",
}
