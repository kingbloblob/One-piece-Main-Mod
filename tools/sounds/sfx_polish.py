"""
Polish pass (2026-11-03): move sounds for fruits that used to borrow another fruit's sound.
Oto Oto plays music, Toki Toki and Modo Modo tick like clocks, Mira Mira rings like glass, Doa Doa opens doors,
Doru Doru / Pero Pero / Ishi Ishi harden, Sube Sube slips, Riki Riki hits like a truck and Noro Noro hums.
Same tools as sfx_zoan.py: pure math, no samples.
"""
import numpy as np

from synth import SR, bell, fft_filter, finish, hz, midi, noise, phase_of, reverb, silence
from sfx import boom, metal, place, sweep_noise
from sfx_combat import rumble, thud, whoosh
from sfx_world import creak


def t_of(d):
	return np.arange(int(d * SR)) / SR


def sound_wave():
	"""Oto Oto no Mi: a booming bass chord that ripples outward in waves."""
	buf = silence(2.0)
	for m, v in (("C2", 1.0), ("G2", 0.6), ("C3", 0.5), ("E3", 0.35)):
		f = hz(midi(m))
		t = t_of(1.6)
		x = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(4 * np.pi * f * t)
		x *= np.exp(-t / 0.7) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * t))  # the pulsing "wub" of the waves
		place(buf, 0.0, x, 0.35 * v)
	for i, m in enumerate(("G5", "C6", "E6")):
		place(buf, 0.05 + i * 0.09, bell(hz(midi(m)), 0.6, 0.6, decay=0.5), 0.45)
	place(buf, 0.0, boom(0.8, 45, 60, 0.8), 0.5)
	return finish(reverb(buf, 1.8, 0.55, 0.3))


def clock():
	"""Toki Toki and Modo Modo: a quick run of ticks, a wind-up and a chime as time bends."""
	buf = silence(1.8)
	for i in range(8):
		tick = fft_filter(noise(0.03), 2500, 9000) * np.exp(-t_of(0.03) / 0.004)
		place(buf, i * 0.07 * (1 - i * 0.05), tick, 0.8 if i % 2 == 0 else 0.5)
	place(buf, 0.35, sweep_noise(0.4, 400, 4000) * np.sin(np.pi * t_of(0.4) / 0.4), 0.35)
	for m, v in (("E5", 0.8), ("B5", 0.5), ("E6", 0.35)):
		place(buf, 0.75, bell(hz(midi(m)), 1.0, v, decay=0.9), 1.0)
	return finish(reverb(buf, 1.8, 0.55, 0.32))


def mirror():
	"""Mira Mira no Mi: a bright glassy shimmer, then stepping through the mirror."""
	buf = silence(1.6)
	rng = np.random.default_rng(11)
	for i in range(14):
		f = rng.uniform(2200, 5200)
		place(buf, i * 0.035, bell(f, 0.2, 1.0, decay=0.25), rng.uniform(0.3, 0.7))
	t = t_of(0.8)
	glide = np.sin(phase_of(1800, len(t), glide=(900, 0.8))) * np.sin(np.pi * t / 0.8) ** 2
	place(buf, 0.3, glide, 0.2)
	place(buf, 0.8, whoosh(0.35, 1500, 6000), 0.5)
	return finish(reverb(buf, 1.6, 0.5, 0.35))


def door():
	"""Doa Doa no Mi: a door creaks open in thin air, a whoosh through it, and it thunks shut."""
	buf = silence(1.6)
	place(buf, 0.0, creak(180, 0.6, seed=4), 0.7)
	place(buf, 0.45, whoosh(0.35, 300, 2500), 0.6)
	place(buf, 0.9, thud(0.4, 70, 0.9), 0.9)
	click = fft_filter(noise(0.04), 1500, 6000) * np.exp(-t_of(0.04) / 0.006)
	place(buf, 0.93, click, 0.6)
	return finish(reverb(buf, 1.0, 0.35, 0.2))


def harden():
	"""Doru Doru, Pero Pero, Ishi Ishi: something soft sets hard with a crackle and a ring."""
	buf = silence(1.4)
	rng = np.random.default_rng(5)
	for i in range(16):
		ln = rng.uniform(0.01, 0.03)
		x = fft_filter(noise(ln + 0.01), 1200, 7000)[: int(ln * SR)] * np.exp(-np.arange(int(ln * SR)) / SR / (ln / 3))
		place(buf, 0.03 * i + rng.uniform(0, 0.02), x, rng.uniform(0.3, 0.9))
	place(buf, 0.5, metal(700, 0.6, 0.6), 0.5)
	place(buf, 0.5, thud(0.3, 90, 0.6), 0.6)
	return finish(reverb(buf, 1.0, 0.35, 0.22))


def slip():
	"""Sube Sube no Mi: a slick, squeaky-smooth glide."""
	buf = silence(1.0)
	t = t_of(0.5)
	squeak = np.sin(phase_of(2600, len(t), glide=(1400, 0.5))) * np.sin(np.pi * t / 0.5) ** 2
	place(buf, 0.0, whoosh(0.6, 1200, 9000), 0.7)
	place(buf, 0.1, squeak, 0.15)
	return finish(reverb(buf, 0.8, 0.3, 0.18))


def heavy_blow():
	"""Riki Riki no Mi: a huge wind-up and a punch heavy enough to shake the ground."""
	buf = silence(1.6)
	place(buf, 0.0, whoosh(0.45, 150, 1200), 0.7)
	place(buf, 0.4, boom(1.1, 32, 90, 1.0), 1.0)
	place(buf, 0.4, thud(0.5, 50, 1.0), 0.8)
	place(buf, 0.45, rumble(0.9), 0.4)
	return finish(reverb(buf, 1.4, 0.45, 0.22))


def photon():
	"""Noro Noro no Mi: the slow, warbling hum of the Noroi beam."""
	buf = silence(1.6)
	t = t_of(1.3)
	f = 330 * (1 + 0.03 * np.sin(2 * np.pi * 2.5 * t))
	ph = 2 * np.pi * np.cumsum(f) / SR
	x = (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3.01 * ph)) * np.sin(np.pi * t / 1.3) ** 0.6
	x *= 0.7 + 0.3 * np.sin(2 * np.pi * 5 * t)
	place(buf, 0.0, x, 0.4)
	place(buf, 0.0, sweep_noise(1.2, 3000, 600) * np.sin(np.pi * t_of(1.2) / 1.2), 0.25)
	return finish(reverb(buf, 1.6, 0.5, 0.3))


ALL = {
	"fruit_move/sound_wave": sound_wave,
	"fruit_move/clock": clock,
	"fruit_move/mirror": mirror,
	"fruit_move/door": door,
	"fruit_move/harden": harden,
	"fruit_move/slip": slip,
	"fruit_move/heavy_blow": heavy_blow,
	"fruit_move/photon": photon,
	"music_stinger/victory": lambda: __import__("music_polish").victory(),
}

SUBTITLES = {
	"fruit_move/sound_wave": "A sound wave booms",
	"fruit_move/clock": "Time bends",
	"fruit_move/mirror": "A mirror shimmers",
	"fruit_move/door": "A door opens in the air",
	"fruit_move/harden": "Something hardens",
	"fruit_move/slip": "Something slips past",
	"fruit_move/heavy_blow": "A crushing blow",
	"fruit_move/photon": "A slow beam hums",
	"music_stinger/victory": "Victory fanfare",
}
