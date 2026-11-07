"""Devil Fruit move sounds: one per element or kind of power. Played on top of each move's normal sound
(see sound/FruitSounds.java for which fruit uses which). All made from scratch like the rest of sfx.py."""
import numpy as np

from synth import SR, additive, bell, brass, choir, env, fft_filter, finish, hz, midi, noise, phase_of, reverb, silence
from sfx import boom, crackle, metal, place, sweep_noise


def t_of(d):
	return np.arange(int(d * SR)) / SR


def roar_tone(f0, d, rough=0.6, formant=(500, 1400)):
	"""A growl: low buzzy tone with a wobbly pitch, shaped by two mouth formants."""
	n = int(d * SR)
	t = t_of(d)
	f = f0 * (1 + 0.25 * np.sin(np.pi * t / d)) * (1 + 0.04 * np.sin(2 * np.pi * 23 * t))
	ph = 2 * np.pi * np.cumsum(f) / SR
	x = np.zeros(n)
	for k in range(1, 40):
		x += np.sin(k * ph) / k
	x *= 1 + rough * fft_filter(noise(d), 20, 90) * 3  # gravelly amplitude flutter
	x = fft_filter(x, formant[0] * 0.5, formant[1] * 2)
	x += fft_filter(noise(d), formant[0], formant[1] * 2.5) * 0.3
	return x * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.6


def fire():
	d = 1.3
	buf = silence(d)
	place(buf, 0.0, sweep_noise(0.5, 400, 2500, 0.8))
	n = int(1.1 * SR)
	t = t_of(1.1)
	roar = fft_filter(noise(1.1), 80, 1800) * (1 + 0.8 * fft_filter(noise(1.1), 5, 40) * 6)
	place(buf, 0.12, roar * np.exp(-t / 0.4) * np.minimum(t / 0.05, 1), 1.0)
	place(buf, 0.12, crackle(0.9, 40, 0.35))
	place(buf, 0.1, boom(0.8, 55, 60, 0.6))
	return finish(reverb(buf, 1.0, 0.3, 0.2))


def magma():
	d = 1.8
	buf = silence(d)
	place(buf, 0.0, boom(1.6, 32, 50, 1.2))
	t = t_of(1.5)
	gurgle = np.zeros(len(t))
	rng = np.random.default_rng(11)
	for _ in range(14):  # thick bubbles popping
		at = rng.uniform(0.0, 1.2)
		f = rng.uniform(70, 160)
		ln = 0.12
		tt = t_of(ln)
		b = np.sin(2 * np.pi * np.cumsum(f * (1 + 1.5 * tt / ln)) / SR) * np.sin(np.pi * tt / ln)
		place(gurgle, at, b, rng.uniform(0.3, 0.7))
	place(buf, 0.15, gurgle)
	place(buf, 0.1, fft_filter(noise(1.5), 60, 900) * np.exp(-t / 0.6), 0.6)
	return finish(reverb(buf, 1.2, 0.4, 0.2))


def ice():
	d = 1.4
	buf = silence(d)
	place(buf, 0.0, sweep_noise(0.3, 3000, 9000, 0.5))
	rng = np.random.default_rng(5)
	for i in range(9):  # crystals cracking into place
		f = rng.uniform(1800, 4200)
		place(buf, 0.08 + i * 0.045, metal(f, 0.35, 0.5) * 0.4)
	for m in ("E6", "B6", "G#7"):
		place(buf, 0.3, bell(hz(midi(m)), 0.1, 0.5, decay=0.9))
	t = t_of(0.6)
	place(buf, 0.06, fft_filter(noise(0.6), 2500, 12000) * np.exp(-t / 0.1), 0.6)
	return finish(reverb(buf, 1.6, 0.5, 0.35, tone=10000))


def lightning():
	d = 1.6
	buf = silence(d)
	place(buf, 0.0, crackle(0.4, 160, 0.8))
	t = t_of(0.12)
	place(buf, 0.35, fft_filter(noise(0.12), 500, 14000) * np.exp(-t / 0.02), 1.5)  # the strike
	place(buf, 0.37, boom(1.2, 40, 120, 1.0))
	place(buf, 0.4, crackle(0.8, 50, 0.4))
	n = int(0.5 * SR)
	hum = np.sign(np.sin(phase_of(120, n))) * 0.15 * np.exp(-t_of(0.5) / 0.2)
	place(buf, 0.35, fft_filter(hum, 100, 3000))
	return finish(reverb(buf, 1.6, 0.6, 0.25))


def light():
	d = 1.3
	buf = silence(d)
	n = int(0.5 * SR)
	t = t_of(0.5)
	for f in (1200, 1800, 2400):  # bright rising zap
		place(buf, 0.0, np.sin(phase_of(f, n, glide=(f * 0.4, 0.18))) * np.exp(-t / 0.25) * 0.3)
	place(buf, 0.0, sweep_noise(0.25, 2000, 10000, 0.4))
	for i, m in enumerate(("A6", "E7", "A7")):
		place(buf, 0.12 + i * 0.03, bell(hz(midi(m)), 0.05, 0.5, decay=0.7))
	return finish(reverb(buf, 1.4, 0.5, 0.35, tone=11000))


def darkness():
	d = 1.8
	buf = silence(d)
	n = int(1.6 * SR)
	t = t_of(1.6)
	place(buf, 0.0, np.sin(phase_of(55, n, glide=(110, 1.2))) * np.sin(np.pi * t / 1.6) * 0.8)
	place(buf, 0.0, sweep_noise(1.4, 3000, 120, 0.7))  # sucked inward
	for m in ("C2", "C#2", "G2"):
		place(buf, 0.1, choir(hz(midi(m)), 1.2, 0.8, vowel="oo"), 0.6)
	return finish(reverb(buf, 2.0, 0.7, 0.35, tone=3000))


def smoke():
	d = 1.4
	buf = silence(d)
	t = t_of(1.2)
	hiss = fft_filter(noise(1.2), 600, 5000) * np.sin(np.pi * np.clip(t / 1.2, 0, 1)) ** 0.7
	place(buf, 0.0, hiss, 0.8)
	place(buf, 0.0, sweep_noise(1.2, 300, 900, 0.6))
	return finish(reverb(buf, 1.4, 0.6, 0.3, tone=4000))


def sand():
	d = 1.5
	buf = silence(d)
	t = t_of(1.3)
	grains = fft_filter(noise(1.3), 1500, 9000) * (np.random.default_rng(2).random(len(t)) > 0.75)
	place(buf, 0.0, grains * np.sin(np.pi * t / 1.3), 0.9)
	place(buf, 0.0, sweep_noise(1.3, 400, 2500, 0.6))
	place(buf, 0.0, fft_filter(noise(1.3), 80, 400) * np.sin(np.pi * t / 1.3) * 0.5)
	return finish(reverb(buf, 1.2, 0.4, 0.2))


def quake():
	d = 2.2
	buf = silence(d)
	t = t_of(0.08)
	for at in (0.0, 0.05, 0.11):  # glass-like cracks in the air
		place(buf, at, fft_filter(noise(0.08), 1500, 9000) * np.exp(-t / 0.015), 1.0)
		place(buf, at, metal(900 + at * 3000, 0.4, 0.4))
	place(buf, 0.1, boom(2.0, 28, 60, 1.5))
	n = int(1.8 * SR)
	tt = t_of(1.8)
	place(buf, 0.15, np.sin(phase_of(22, n)) * fft_filter(noise(1.8), 20, 200) * np.exp(-tt / 0.8) * 2)
	return finish(reverb(buf, 1.8, 0.6, 0.25))


def rubber():
	"""Stretch (a rising, wobbly boing), then the snap back."""
	d = 1.0
	buf = silence(d)
	n = int(0.45 * SR)
	t = t_of(0.45)
	f = 140 * (1 + 2.2 * t / 0.45) * (1 + 0.06 * np.sin(2 * np.pi * 18 * t))
	x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sin(4 * np.pi * np.cumsum(f) / SR)
	place(buf, 0.0, x * env(n, 0.02, 0.2, 0.8, 0.08) * 0.6)
	tt = t_of(0.3)
	snap = np.sin(2 * np.pi * np.cumsum(500 * np.exp(-tt / 0.05) + 90) / SR) * np.exp(-tt / 0.07)
	place(buf, 0.45, snap, 0.9)
	place(buf, 0.45, fft_filter(noise(0.05), 1000, 6000) * np.exp(-t_of(0.05) / 0.01), 0.7)
	return finish(reverb(buf, 0.6, 0.2, 0.12))


def blade():
	d = 0.9
	buf = silence(d)
	place(buf, 0.0, sweep_noise(0.22, 1200, 7000, 1.0))
	place(buf, 0.12, metal(2600, 0.6, 0.5))
	place(buf, 0.12, metal(1730, 0.5, 0.3))
	return finish(reverb(buf, 0.8, 0.3, 0.2, tone=9000))


def gravity():
	d = 1.8
	buf = silence(d)
	n = int(0.9 * SR)
	t = t_of(0.9)
	place(buf, 0.0, np.sin(phase_of(60, n, glide=(400, 0.8))) * env(n, 0.05, 0.4, 0.8, 0.1) * 0.7)  # pressing down
	place(buf, 0.8, boom(1.0, 30, 40, 1.4))
	place(buf, 0.8, fft_filter(noise(0.6), 100, 1200) * np.exp(-t_of(0.6) / 0.15), 0.6)
	return finish(reverb(buf, 1.4, 0.5, 0.2))


def plant():
	d = 1.3
	buf = silence(d)
	rng = np.random.default_rng(8)
	for i in range(10):  # wood creaking and roots cracking up through the ground
		f = rng.uniform(90, 260)
		ln = 0.12
		tt = t_of(ln)
		creak = np.sign(np.sin(2 * np.pi * np.cumsum(f * (1 + 0.3 * tt / ln)) / SR)) * np.sin(np.pi * tt / ln)
		place(buf, i * 0.08, fft_filter(creak, 200, 2500), 0.35)
	place(buf, 0.0, fft_filter(noise(1.0), 100, 1200) * np.exp(-t_of(1.0) / 0.5), 0.5)
	place(buf, 0.6, boom(0.6, 60, 40, 0.5))
	return finish(reverb(buf, 1.0, 0.3, 0.2))


def poison():
	d = 1.3
	buf = silence(d)
	t = t_of(1.0)
	place(buf, 0.0, fft_filter(noise(1.0), 1200, 7000) * np.sin(np.pi * t / 1.0), 0.6)  # hiss
	rng = np.random.default_rng(13)
	for _ in range(10):  # sizzling drips
		at = rng.uniform(0.0, 1.0)
		f = rng.uniform(500, 1200)
		tt = t_of(0.07)
		place(buf, at, np.sin(2 * np.pi * np.cumsum(f * (1 + 2 * tt / 0.07)) / SR) * np.sin(np.pi * tt / 0.07), 0.3)
	n = int(1.0 * SR)
	place(buf, 0.0, np.sin(phase_of(180, n) + 2 * np.sin(2 * np.pi * 7 * t)) * np.sin(np.pi * t) * 0.15)
	return finish(reverb(buf, 1.2, 0.4, 0.25))


def explosion():
	d = 2.0
	buf = silence(d)
	place(buf, 0.0, boom(1.9, 36, 100, 1.5))
	t = t_of(0.4)
	place(buf, 0.0, fft_filter(noise(0.4), 300, 8000) * np.exp(-t / 0.06), 1.0)
	place(buf, 0.05, crackle(1.2, 30, 0.3))
	return finish(reverb(buf, 1.5, 0.5, 0.2))


def bubble():
	"""Soft, light powers: bubbles, mochi, floating, clouds."""
	d = 1.2
	buf = silence(d)
	rng = np.random.default_rng(4)
	for _ in range(12):
		at = rng.uniform(0.0, 0.8)
		f = rng.uniform(400, 1100)
		ln = rng.uniform(0.05, 0.1)
		tt = t_of(ln)
		place(buf, at, np.sin(2 * np.pi * np.cumsum(f * (1 + 1.8 * tt / ln)) / SR) * np.sin(np.pi * tt / ln), 0.4)
	place(buf, 0.0, sweep_noise(0.6, 500, 1500, 0.3))
	return finish(reverb(buf, 1.0, 0.4, 0.3))


def warp():
	"""Teleports and swaps (Room, mirrors, doors)."""
	d = 1.0
	buf = silence(d)
	n = int(0.35 * SR)
	t = t_of(0.35)
	place(buf, 0.0, np.sin(phase_of(1600, n, glide=(200, 0.3))) * np.sin(np.pi * t / 0.35) * 0.5)
	place(buf, 0.3, np.sin(phase_of(150, n, glide=(1800, 0.3))) * np.sin(np.pi * t / 0.35) * 0.4)
	place(buf, 0.3, bell(hz(midi("E6")), 0.05, 0.5, decay=0.5))
	place(buf, 0.0, sweep_noise(0.65, 600, 5000, 0.3))
	return finish(reverb(buf, 1.2, 0.4, 0.3, tone=9000))


def string():
	"""Strings and threads: sharp, twangy whips."""
	d = 0.9
	buf = silence(d)
	for i, f in enumerate((660, 990, 1320)):
		n = int(0.5 * SR)
		t = t_of(0.5)
		tw = additive(f, n, lambda k, tt: np.exp(-tt * (6 + 2 * k)) / k, max_h=12, glide=(f * 1.15, 0.05))
		place(buf, i * 0.05, tw, 0.5)
	place(buf, 0.0, sweep_noise(0.15, 3000, 9000, 0.6))
	return finish(reverb(buf, 0.8, 0.3, 0.2, tone=9000))


def curse():
	"""Ghosts, souls, curses and charms: eerie wavering tones."""
	d = 1.8
	buf = silence(d)
	n = int(1.5 * SR)
	t = t_of(1.5)
	for f in (440, 466, 660):
		ph = phase_of(f, n) + 6 * np.sin(2 * np.pi * 3.3 * t)
		place(buf, 0.0, np.sin(ph) * np.sin(np.pi * t / 1.5) ** 2 * 0.25)
	place(buf, 0.1, choir(hz(midi("A3")), 1.2, 0.6, vowel="oo"), 0.5)
	place(buf, 0.0, sweep_noise(1.5, 2000, 600, 0.2))
	return finish(reverb(buf, 2.2, 0.8, 0.45, tone=5000))


def impact():
	"""Plain superhuman hits (default for body-power Paramecia)."""
	d = 0.8
	buf = silence(d)
	place(buf, 0.0, sweep_noise(0.15, 600, 3000, 0.6))
	place(buf, 0.12, boom(0.6, 55, 120, 1.2))
	place(buf, 0.12, fft_filter(noise(0.08), 400, 4000) * np.exp(-t_of(0.08) / 0.015), 0.9)
	return finish(reverb(buf, 0.7, 0.25, 0.15))


def beast_roar():
	d = 1.6
	buf = silence(d)
	place(buf, 0.0, roar_tone(95, 1.4, 0.8, (450, 1300)), 1.0)
	place(buf, 0.0, roar_tone(190, 1.2, 0.5, (700, 1800)), 0.4)
	return finish(reverb(buf, 1.2, 0.4, 0.2))


def dragon_roar():
	d = 2.4
	buf = silence(d)
	place(buf, 0.0, roar_tone(60, 2.1, 1.0, (300, 1000)), 1.0)
	place(buf, 0.1, roar_tone(130, 1.8, 0.7, (600, 1600)), 0.5)
	place(buf, 0.3, boom(1.6, 34, 40, 0.6))
	return finish(reverb(buf, 2.0, 0.7, 0.3))


def bird_cry():
	"""Bird Zoans (Phoenix and friends): a soaring screech with wing flaps."""
	d = 1.5
	buf = silence(d)
	n = int(0.8 * SR)
	t = t_of(0.8)
	f = 1400 * (1 + 0.5 * np.sin(np.pi * t / 0.8)) * (1 + 0.03 * np.sin(2 * np.pi * 30 * t))
	ph = 2 * np.pi * np.cumsum(f) / SR
	cry = (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)) * np.sin(np.pi * t / 0.8) ** 0.5
	place(buf, 0.0, fft_filter(cry, 600, 7000), 0.6)
	for at in (0.75, 1.0, 1.25):
		place(buf, at, fft_filter(noise(0.15), 150, 1500) * np.sin(np.pi * t_of(0.15) / 0.15), 0.5)
	return finish(reverb(buf, 1.4, 0.5, 0.3))


ALL = {
	"fruit_move/fire": fire,
	"fruit_move/magma": magma,
	"fruit_move/ice": ice,
	"fruit_move/lightning": lightning,
	"fruit_move/light": light,
	"fruit_move/darkness": darkness,
	"fruit_move/smoke": smoke,
	"fruit_move/sand": sand,
	"fruit_move/quake": quake,
	"fruit_move/rubber": rubber,
	"fruit_move/blade": blade,
	"fruit_move/gravity": gravity,
	"fruit_move/plant": plant,
	"fruit_move/poison": poison,
	"fruit_move/explosion": explosion,
	"fruit_move/bubble": bubble,
	"fruit_move/warp": warp,
	"fruit_move/string": string,
	"fruit_move/curse": curse,
	"fruit_move/impact": impact,
	"fruit_move/beast_roar": beast_roar,
	"fruit_move/dragon_roar": dragon_roar,
	"fruit_move/bird_cry": bird_cry,
}

SUBTITLES = {
	"fruit_move/fire": "Flames roar",
	"fruit_move/magma": "Magma bubbles",
	"fruit_move/ice": "Ice crackles",
	"fruit_move/lightning": "Lightning strikes",
	"fruit_move/light": "Light flashes",
	"fruit_move/darkness": "Darkness pulls",
	"fruit_move/smoke": "Smoke billows",
	"fruit_move/sand": "Sand swirls",
	"fruit_move/quake": "The air shatters",
	"fruit_move/rubber": "Rubber stretches",
	"fruit_move/blade": "A blade slices",
	"fruit_move/gravity": "Gravity crushes",
	"fruit_move/plant": "Roots burst out",
	"fruit_move/poison": "Poison hisses",
	"fruit_move/explosion": "Something explodes",
	"fruit_move/bubble": "Bubbles pop",
	"fruit_move/warp": "Space warps",
	"fruit_move/string": "Strings whip",
	"fruit_move/curse": "An eerie power stirs",
	"fruit_move/impact": "A powerful blow",
	"fruit_move/beast_roar": "A beast roars",
	"fruit_move/dragon_roar": "A dragon roars",
	"fruit_move/bird_cry": "A great bird cries",
}
