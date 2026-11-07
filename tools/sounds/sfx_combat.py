"""Boss fight and fighting style sounds. Made from scratch like the rest of sfx.py (no samples).
Boss sounds: sound/BossSounds.java. Fighting style sounds: sound/StyleSounds.java."""
import numpy as np

from synth import SR, bell, brass, choir, env, fft_filter, finish, fiddle, hz, midi, noise, phase_of, reverb, silence, \
	timpani, crash, kick
from sfx import boom, crackle, metal, place, sweep_noise
from sfx_moves import roar_tone


def t_of(d):
	return np.arange(int(d * SR)) / SR


def thud(d=0.5, f0=55, v=1.0):
	"""A body blow: short low thump with a dull slap on top."""
	t = t_of(d)
	x = np.sin(2 * np.pi * np.cumsum(f0 + 120 * np.exp(-t / 0.02)) / SR) * np.exp(-t / 0.09)
	x += fft_filter(noise(d), 200, 2500) * np.exp(-t / 0.012) * 0.6
	return x * v


def whoosh(d, lo, hi, v=1.0):
	"""Air rushing past: a brightness sweep that swells and fades."""
	return sweep_noise(d, lo, hi, v) * np.sin(np.pi * np.clip(t_of(d) / d, 0, 1)) ** 0.8


def rumble(d, v=1.0):
	t = t_of(d)
	return fft_filter(noise(d), 18, 160) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.5 * 3 * v


def tone_glide(f0, f1, d, v=1.0, square=False):
	n = int(d * SR)
	ph = phase_of(f1, n, glide=(f0, d))
	x = np.sign(np.sin(ph)) * 0.5 if square else np.sin(ph)
	return x * v


# ------------------------------------------------------------------ bosses

def boss_intro():
	"""A boss steps up: timpani roll, a dark brass stab, a cymbal."""
	buf = silence(3.0)
	for i in range(14):  # roll that gets louder
		place(buf, i * 0.045, timpani(hz(midi("C2")), 0.3, 0.2 + 0.05 * i), 0.6)
	for m in ("C3", "Eb3", "Gb3", "C4"):
		place(buf, 0.65, brass(hz(midi(m)), 1.2, 1.0), 0.9)
	place(buf, 0.65, timpani(hz(midi("C2")), 1.5, 1.0), 1.2)
	place(buf, 0.65, crash(0.9))
	place(buf, 0.65, boom(1.6, 34, 60, 0.6))
	return finish(reverb(buf, 2.0, 0.8, 0.3))


def boss_phase():
	"""The boss gets serious: a huge roar over a rumble and a blast."""
	buf = silence(2.6)
	place(buf, 0.0, roar_tone(62, 1.7, rough=0.9, formant=(350, 1100)), 1.0)
	place(buf, 0.05, roar_tone(93, 1.5, rough=0.7, formant=(500, 1500)), 0.5)
	place(buf, 0.0, boom(2.2, 30, 70, 1.0))
	place(buf, 0.1, rumble(2.0, 0.8))
	return finish(reverb(buf, 2.0, 0.7, 0.3, tone=4000))


def boss_windup():
	"""Power building up: a rising buzz and a swelling hiss. About as long as a Normal wind-up."""
	d = 1.0
	buf = silence(d + 0.4)
	t = t_of(d)
	trem = 0.6 + 0.4 * np.sin(2 * np.pi * (6 + 18 * t / d) * t)
	place(buf, 0.0, fft_filter(tone_glide(70, 280, d, 1.0, square=True), 60, 3000) * trem * (t / d) ** 1.5, 0.6)
	place(buf, 0.0, tone_glide(140, 560, d, 0.4) * (t / d) ** 2)
	place(buf, 0.0, sweep_noise(d, 300, 4000, 0.5) * (t / d) ** 2)
	place(buf, 0.3, crackle(0.7, 40, 0.25))
	return finish(reverb(buf, 1.0, 0.3, 0.2))


def boss_signature():
	"""The boss calls its signature move: a deep gong, a dark choir and rising wind."""
	buf = silence(2.6)
	place(buf, 0.0, metal(62, 2.4, 1.0))
	place(buf, 0.0, metal(93, 2.0, 0.5))
	for m in ("C2", "G2", "Db3"):
		place(buf, 0.1, choir(hz(midi(m)), 1.6, 0.9), 0.7)
	place(buf, 0.2, whoosh(1.4, 200, 3500, 0.7))
	place(buf, 0.0, boom(1.5, 32, 40, 0.6))
	return finish(reverb(buf, 2.2, 0.8, 0.35, tone=5000))


def boss_strike_land():
	"""A marked strike lands: heavy blast and falling debris."""
	buf = silence(1.8)
	place(buf, 0.0, boom(1.5, 36, 110, 1.3))
	place(buf, 0.0, fft_filter(noise(0.05), 800, 9000) * np.exp(-t_of(0.05) / 0.01), 1.0)
	rng = np.random.default_rng(31)
	for _ in range(12):
		at = rng.uniform(0.2, 1.1)
		place(buf, at, thud(0.15, rng.uniform(150, 400), 0.15))
	return finish(reverb(buf, 1.4, 0.5, 0.2))


def boss_slash_line():
	"""A giant flying slash: long tearing whoosh and a low ringing blade."""
	buf = silence(1.8)
	place(buf, 0.0, whoosh(0.7, 500, 6000, 1.2))
	place(buf, 0.05, whoosh(0.9, 200, 1800, 0.8))
	place(buf, 0.35, metal(440, 1.2, 0.5))
	place(buf, 0.35, metal(1320, 0.8, 0.3))
	place(buf, 0.4, fft_filter(noise(0.6), 1500, 8000) * np.exp(-t_of(0.6) / 0.12), 0.5)
	return finish(reverb(buf, 1.4, 0.5, 0.25, tone=8000))


def boss_black_hole():
	"""Everything is sucked in, then a deep thump as it collapses."""
	buf = silence(2.4)
	d = 1.3
	t = t_of(d)
	suck = sweep_noise(d, 6000, 150, 1.0) * (t / d) ** 2
	place(buf, 0.0, suck)
	place(buf, 0.0, tone_glide(220, 40, d, 0.7) * (t / d))
	place(buf, d, boom(1.1, 26, 40, 1.6))
	place(buf, d, fft_filter(noise(0.4), 30, 400) * np.exp(-t_of(0.4) / 0.1), 1.2)
	return finish(reverb(buf, 2.0, 0.6, 0.3, tone=2500))


def boss_ground_wave():
	"""A shockwave rolling across the ground: cracking stone over a long rumble."""
	buf = silence(2.2)
	place(buf, 0.0, boom(1.8, 30, 60, 1.0))
	place(buf, 0.0, rumble(1.8, 1.0))
	rng = np.random.default_rng(12)
	for i in range(10):
		f = rng.uniform(600, 2000)
		place(buf, 0.05 + i * 0.1, fft_filter(noise(0.06), f, f * 4) * np.exp(-t_of(0.06) / 0.012), 0.6 - i * 0.04)
	return finish(reverb(buf, 1.6, 0.5, 0.2))


def boss_enrage():
	"""Rage: a snarl over a pounding heartbeat."""
	buf = silence(2.2)
	for i in range(4):
		place(buf, i * 0.42, kick(1.0), 0.9)
		place(buf, i * 0.42 + 0.14, kick(0.6), 0.6)
	place(buf, 0.1, roar_tone(80, 1.4, rough=1.0, formant=(400, 1300)), 0.8)
	return finish(reverb(buf, 1.2, 0.4, 0.2, tone=3500))


def boss_leap():
	"""A huge jump: wind rushing up, then a heavy landing."""
	buf = silence(1.4)
	place(buf, 0.0, thud(0.4, 60, 0.6))
	place(buf, 0.02, whoosh(0.5, 300, 2500, 0.8))
	place(buf, 0.55, boom(0.8, 40, 70, 0.9))
	return finish(reverb(buf, 1.0, 0.3, 0.15))


def boss_petrify():
	"""Turned to stone: a shimmer, then stone grinding shut."""
	buf = silence(1.8)
	for i, m in enumerate(("E6", "G#6", "B6", "E7")):
		place(buf, i * 0.05, bell(hz(midi(m)), 0.05, 0.4, decay=0.6))
	t = t_of(1.0)
	grind = fft_filter(noise(1.0), 150, 1800) * (1 + 0.8 * np.sin(2 * np.pi * 31 * t)) * np.sin(np.pi * t)
	place(buf, 0.3, grind, 0.8)
	place(buf, 1.2, thud(0.4, 90, 0.8))
	return finish(reverb(buf, 1.2, 0.4, 0.2))


def boss_paw():
	"""Air squeezed into a paw shape and released: a pressure whine, then a soft but huge whump."""
	buf = silence(1.6)
	d = 0.4
	place(buf, 0.0, tone_glide(300, 1200, d, 0.3) * (t_of(d) / d))
	place(buf, 0.0, sweep_noise(d, 1000, 5000, 0.4))
	place(buf, d, boom(1.1, 45, 90, 1.2))
	place(buf, d, fft_filter(noise(0.5), 60, 800) * np.exp(-t_of(0.5) / 0.12), 1.0)
	return finish(reverb(buf, 1.4, 0.4, 0.25))


def boss_heal():
	"""Blue flames of rebirth: a soft rush of fire under rising chimes."""
	buf = silence(2.0)
	t = t_of(1.4)
	place(buf, 0.0, fft_filter(noise(1.4), 200, 2500) * np.sin(np.pi * t / 1.4) * 0.5)
	for i, m in enumerate(("A5", "C#6", "E6", "A6", "C#7")):
		place(buf, 0.1 + i * 0.12, bell(hz(midi(m)), 0.1, 0.5, decay=0.9))
	for m in ("A3", "E4"):
		place(buf, 0.0, choir(hz(midi(m)), 1.0, 0.6), 0.4)
	return finish(reverb(buf, 1.8, 0.6, 0.35, tone=9000))


# ------------------------------------------------------------------ fighting styles

def style_dash_slash():
	"""Oni Giri: dash past and cut."""
	buf = silence(1.2)
	place(buf, 0.0, whoosh(0.3, 400, 3000, 0.8))
	for i, f in enumerate((2400, 2900, 3500)):
		place(buf, 0.18 + i * 0.05, whoosh(0.15, 1500, 8000, 0.7))
		place(buf, 0.22 + i * 0.05, metal(f, 0.5, 0.35))
	return finish(reverb(buf, 0.9, 0.3, 0.2, tone=9000))


def style_tornado():
	"""Tatsumaki: spinning blades whip the air into a tornado."""
	d = 1.4
	buf = silence(d + 0.4)
	t = t_of(d)
	wind = fft_filter(noise(d), 300, 3000) * (0.5 + 0.5 * np.sin(2 * np.pi * (4 + 6 * t) * t)) * np.sin(np.pi * t / d)
	place(buf, 0.0, wind, 1.0)
	place(buf, 0.0, sweep_noise(d, 300, 2000, 0.6))
	for i in range(4):
		place(buf, 0.1 + i * 0.25, metal(2600 + 200 * i, 0.4, 0.2))
	return finish(reverb(buf, 1.2, 0.4, 0.2))


def style_big_slash():
	"""A flying slash (108 Pound Cannon, Rankyaku, Togen Totsuka): sharp cut, then air tearing away."""
	buf = silence(1.5)
	place(buf, 0.0, whoosh(0.2, 1500, 9000, 1.0))
	place(buf, 0.08, metal(1800, 0.7, 0.5))
	place(buf, 0.08, metal(2700, 0.5, 0.3))
	place(buf, 0.12, whoosh(0.9, 3000, 300, 1.0))
	place(buf, 0.12, thud(0.4, 50, 0.5))
	return finish(reverb(buf, 1.3, 0.4, 0.25, tone=8000))


def style_power_up():
	"""Gathering will (Asura, Boiling Will, Oden's Scar): a low swell, a heartbeat and a burst."""
	buf = silence(2.0)
	d = 1.0
	t = t_of(d)
	for m in ("D2", "A2", "D3"):
		place(buf, 0.0, brass(hz(midi(m)), 1.0, 0.8) * 0.8)
	place(buf, 0.0, tone_glide(60, 120, d, 0.5) * (t / d))
	place(buf, 0.0, kick(0.8))
	place(buf, 0.5, kick(0.9))
	place(buf, 1.0, boom(0.9, 40, 80, 0.8))
	place(buf, 1.0, whoosh(0.6, 800, 5000, 0.6))
	return finish(reverb(buf, 1.6, 0.6, 0.3, tone=5000))


def style_kick():
	"""A heavy spinning kick (Party Table, Concasse)."""
	buf = silence(1.0)
	place(buf, 0.0, whoosh(0.25, 300, 2500, 0.9))
	place(buf, 0.2, thud(0.5, 60, 1.0))
	place(buf, 0.2, fft_filter(noise(0.03), 1500, 7000) * np.exp(-t_of(0.03) / 0.006), 0.6)
	return finish(reverb(buf, 0.7, 0.2, 0.12))


def style_fire_kick():
	"""A leg bursting into flame (Diable Jambe, Ifrit Jambe)."""
	buf = silence(1.5)
	place(buf, 0.0, whoosh(0.3, 600, 4000, 0.7))
	t = t_of(1.1)
	flame = fft_filter(noise(1.1), 100, 2500) * (1 + 0.7 * fft_filter(noise(1.1), 5, 30) * 6)
	place(buf, 0.15, flame * np.exp(-t / 0.5) * np.minimum(t / 0.06, 1), 0.9)
	place(buf, 0.15, crackle(0.9, 30, 0.3))
	place(buf, 0.15, boom(0.6, 60, 80, 0.5))
	return finish(reverb(buf, 1.0, 0.3, 0.2))


def style_fire_slash():
	"""A flaming sword cut (Homura Giri, Kitsunebi blade)."""
	buf = silence(1.4)
	place(buf, 0.0, whoosh(0.22, 1500, 8000, 0.9))
	place(buf, 0.1, metal(2200, 0.5, 0.35))
	t = t_of(0.9)
	place(buf, 0.1, fft_filter(noise(0.9), 150, 3000) * np.exp(-t / 0.35) * np.minimum(t / 0.04, 1), 0.8)
	place(buf, 0.1, crackle(0.7, 30, 0.3))
	return finish(reverb(buf, 1.0, 0.3, 0.2))


def style_shock_punch():
	"""A shock that goes right through you (Thousand Brick Fist, Rokuogan, Galaxy Impact)."""
	buf = silence(1.6)
	place(buf, 0.0, thud(0.5, 50, 1.0))
	n = int(0.6 * SR)
	t = t_of(0.6)
	ring = np.sin(phase_of(70, n)) * np.exp(-t / 0.25) * (1 + 0.5 * np.sin(2 * np.pi * 9 * t))
	place(buf, 0.03, ring, 0.7)
	place(buf, 0.03, boom(1.2, 32, 80, 0.9))
	place(buf, 0.05, whoosh(0.6, 3000, 300, 0.5))
	return finish(reverb(buf, 1.4, 0.4, 0.2, tone=4000))


def style_ground_crush():
	"""Ryu no Ibuki: the ground around you cracks and caves in."""
	buf = silence(1.6)
	place(buf, 0.0, thud(0.4, 70, 0.8))
	place(buf, 0.05, boom(1.2, 34, 60, 0.9))
	rng = np.random.default_rng(4)
	for i in range(8):
		f = rng.uniform(500, 1800)
		place(buf, 0.05 + i * 0.06, fft_filter(noise(0.06), f, f * 4) * np.exp(-t_of(0.06) / 0.01), 0.6)
	place(buf, 0.3, rumble(1.0, 0.6))
	return finish(reverb(buf, 1.2, 0.4, 0.2))


def drop(f, d=0.12):
	"""A water drop or splash 'plip'."""
	t = t_of(d)
	return np.sin(2 * np.pi * np.cumsum(f * (1 + 1.8 * t / d)) / SR) * np.exp(-t / (d / 4))


def style_water_shot():
	"""Uchimizu: water drops flicked fast as bullets."""
	buf = silence(1.0)
	place(buf, 0.0, whoosh(0.12, 1500, 6000, 0.6))
	rng = np.random.default_rng(9)
	for i in range(5):
		at = 0.04 + i * 0.07
		place(buf, at, fft_filter(noise(0.04), 2000, 9000) * np.exp(-t_of(0.04) / 0.006), 0.7)  # snap
		place(buf, at + 0.03, drop(rng.uniform(600, 1100)), 0.4)
	return finish(reverb(buf, 0.8, 0.3, 0.2))


def style_water_wave():
	"""Buraikan: a huge wave of water smashes forward."""
	buf = silence(2.0)
	d = 1.5
	t = t_of(d)
	surge = fft_filter(noise(d), 80, 4000) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.6
	place(buf, 0.0, surge, 1.0)
	place(buf, 0.0, sweep_noise(d, 200, 1200, 0.6))
	place(buf, 0.5, boom(1.0, 40, 50, 0.8))
	rng = np.random.default_rng(10)
	for _ in range(12):
		place(buf, rng.uniform(0.4, 1.4), drop(rng.uniform(400, 1200)), 0.2)
	return finish(reverb(buf, 1.4, 0.5, 0.25))


def style_hard_skin():
	"""Samehada: skin hardening like shark scales, a rough grinding scrape."""
	buf = silence(1.2)
	t = t_of(0.7)
	scrape = fft_filter(noise(0.7), 800, 6000) * (np.random.default_rng(3).random(len(t)) > 0.6)
	place(buf, 0.0, scrape * np.sin(np.pi * t / 0.7), 0.7)
	place(buf, 0.0, tone_glide(90, 60, 0.7, 0.4) * np.sin(np.pi * t / 0.7))
	place(buf, 0.6, metal(900, 0.4, 0.3))
	return finish(reverb(buf, 0.8, 0.3, 0.15))


def style_soru():
	"""Soru: gone in a blink. A sharp crack of air and a fast whoosh."""
	buf = silence(0.8)
	place(buf, 0.0, fft_filter(noise(0.03), 1000, 10000) * np.exp(-t_of(0.03) / 0.005), 1.0)
	place(buf, 0.0, thud(0.2, 90, 0.4))
	place(buf, 0.01, whoosh(0.22, 4000, 800, 1.0))
	return finish(reverb(buf, 0.6, 0.2, 0.15))


def style_shigan():
	"""Shigan: a finger jab fast as a bullet. A tiny whip-crack and a punch-through."""
	buf = silence(0.7)
	place(buf, 0.0, whoosh(0.08, 3000, 9000, 0.6))
	place(buf, 0.07, fft_filter(noise(0.02), 2000, 12000) * np.exp(-t_of(0.02) / 0.003), 1.0)
	place(buf, 0.08, thud(0.25, 110, 0.7))
	return finish(reverb(buf, 0.5, 0.2, 0.12))


def style_tekkai():
	"""Tekkai: the body turns hard as iron, a dull clang."""
	buf = silence(1.3)
	place(buf, 0.0, metal(180, 1.0, 0.9))
	place(buf, 0.0, metal(270, 0.8, 0.4))
	place(buf, 0.0, thud(0.3, 60, 0.6))
	return finish(reverb(buf, 1.0, 0.3, 0.15))


def style_geppo():
	"""Geppo / air jump: kicking off thin air."""
	buf = silence(0.6)
	place(buf, 0.0, thud(0.2, 120, 0.6))
	place(buf, 0.0, fft_filter(noise(0.15), 300, 2500) * np.exp(-t_of(0.15) / 0.04), 0.8)
	place(buf, 0.02, whoosh(0.2, 600, 2500, 0.5))
	return finish(reverb(buf, 0.5, 0.2, 0.12))


def style_claw():
	"""Ryu no Kagizume: a dragon claw grip that crushes."""
	buf = silence(1.0)
	place(buf, 0.0, whoosh(0.15, 500, 3000, 0.6))
	rng = np.random.default_rng(6)
	for i in range(6):
		f = rng.uniform(300, 1200)
		place(buf, 0.12 + i * 0.03, fft_filter(noise(0.05), f, f * 3) * np.exp(-t_of(0.05) / 0.01), 0.7)
	place(buf, 0.12, thud(0.4, 70, 0.9))
	return finish(reverb(buf, 0.7, 0.2, 0.12))


def style_cut_flames():
	"""Cutting the flames: a swift cut, then fire hissing out."""
	buf = silence(1.4)
	place(buf, 0.0, whoosh(0.2, 1500, 8000, 0.9))
	place(buf, 0.1, metal(2500, 0.4, 0.3))
	t = t_of(1.0)
	place(buf, 0.15, fft_filter(noise(1.0), 2000, 9000) * np.exp(-t / 0.35), 0.7)
	return finish(reverb(buf, 1.0, 0.3, 0.2))


def style_sheathe():
	"""Yahazu Giri: walk past, slide the sword home with a click... and the cut lands."""
	buf = silence(1.2)
	t = t_of(0.35)
	place(buf, 0.0, fft_filter(noise(0.35), 3000, 9000) * np.sin(np.pi * t / 0.35) * 0.4)  # blade sliding in
	place(buf, 0.35, metal(3200, 0.2, 0.5))  # click
	place(buf, 0.36, fft_filter(noise(0.02), 2000, 10000) * np.exp(-t_of(0.02) / 0.004), 0.6)
	place(buf, 0.55, whoosh(0.2, 1500, 9000, 0.8))
	place(buf, 0.6, metal(2600, 0.5, 0.35))
	return finish(reverb(buf, 1.0, 0.3, 0.2, tone=9000))


def style_lunge():
	"""Gavotte: a long fencing lunge, a thin blade hissing forward."""
	buf = silence(0.9)
	place(buf, 0.0, whoosh(0.3, 2000, 9000, 0.8))
	place(buf, 0.25, metal(3600, 0.4, 0.4))
	return finish(reverb(buf, 0.8, 0.3, 0.2, tone=10000))


def style_chill_blade():
	"""Soul Solid: a blade cold as the underworld. Frost creeping, a ghostly hum."""
	buf = silence(1.6)
	rng = np.random.default_rng(13)
	for i in range(7):
		place(buf, 0.05 + i * 0.05, metal(rng.uniform(2500, 4500), 0.3, 0.3))
	for m in ("E4", "B4"):
		place(buf, 0.0, choir(hz(midi(m)), 1.0, 0.5, vowel="oo"), 0.5)
	place(buf, 0.0, sweep_noise(0.6, 4000, 9000, 0.3))
	return finish(reverb(buf, 1.6, 0.6, 0.35, tone=10000))


def style_lullaby():
	"""A sad little violin tune that makes enemies too sleepy to fight."""
	buf = silence(3.4)
	at = 0.0
	for name, beats in (("E5", 1), ("D5", 0.5), ("C5", 0.5), ("B4", 1), ("A4", 1.5), ("E4", 2)):
		d = beats * 0.42
		place(buf, at, fiddle(hz(midi(name)), d * 0.95, 0.8))
		at += d
	return finish(reverb(buf, 2.0, 0.8, 0.35))


def style_punch():
	"""Fist of Love: a big, honest punch."""
	buf = silence(0.9)
	place(buf, 0.0, whoosh(0.18, 400, 3000, 0.7))
	place(buf, 0.15, thud(0.5, 55, 1.0))
	place(buf, 0.15, boom(0.5, 50, 90, 0.4))
	return finish(reverb(buf, 0.7, 0.2, 0.12))


def style_throw():
	"""Throwing cannonballs by hand: a grunt of effort and a heavy whoosh."""
	buf = silence(1.0)
	place(buf, 0.0, thud(0.25, 80, 0.4))
	place(buf, 0.05, whoosh(0.6, 200, 1200, 1.0))
	return finish(reverb(buf, 0.7, 0.2, 0.12))


def style_slingshot():
	"""Kabuto slingshot: the band stretches, twangs, and the shot whistles away."""
	buf = silence(1.0)
	t = t_of(0.25)
	place(buf, 0.0, fft_filter(np.sin(phase_of(180, len(t), glide=(120, 0.25))) * t / 0.25, 80, 2000) * 0.3)  # stretch
	tw = t_of(0.35)
	place(buf, 0.25, np.sin(phase_of(110, len(tw))) * np.exp(-tw / 0.1) * (1 + 0.5 * np.sin(2 * np.pi * 28 * tw)), 0.8)
	place(buf, 0.27, whoosh(0.35, 3000, 1200, 0.6))
	place(buf, 0.27, np.sin(phase_of(1800, int(0.35 * SR), glide=(2600, 0.35))) * np.exp(-t_of(0.35) / 0.15) * 0.15)
	return finish(reverb(buf, 0.8, 0.3, 0.15))


ALL = {
	"boss/intro": boss_intro,
	"boss/phase": boss_phase,
	"boss/windup": boss_windup,
	"boss/signature": boss_signature,
	"boss/strike_land": boss_strike_land,
	"boss/slash_line": boss_slash_line,
	"boss/black_hole": boss_black_hole,
	"boss/ground_wave": boss_ground_wave,
	"boss/enrage": boss_enrage,
	"boss/leap": boss_leap,
	"boss/petrify": boss_petrify,
	"boss/paw": boss_paw,
	"boss/heal": boss_heal,
	"style/dash_slash": style_dash_slash,
	"style/tornado": style_tornado,
	"style/big_slash": style_big_slash,
	"style/power_up": style_power_up,
	"style/kick": style_kick,
	"style/fire_kick": style_fire_kick,
	"style/fire_slash": style_fire_slash,
	"style/shock_punch": style_shock_punch,
	"style/ground_crush": style_ground_crush,
	"style/water_shot": style_water_shot,
	"style/water_wave": style_water_wave,
	"style/hard_skin": style_hard_skin,
	"style/soru": style_soru,
	"style/shigan": style_shigan,
	"style/tekkai": style_tekkai,
	"style/geppo": style_geppo,
	"style/claw": style_claw,
	"style/cut_flames": style_cut_flames,
	"style/sheathe": style_sheathe,
	"style/lunge": style_lunge,
	"style/chill_blade": style_chill_blade,
	"style/lullaby": style_lullaby,
	"style/punch": style_punch,
	"style/throw": style_throw,
	"style/slingshot": style_slingshot,
}

SUBTITLES = {
	"boss/intro": "A powerful foe appears",
	"boss/phase": "The boss roars",
	"boss/windup": "The boss gathers power",
	"boss/signature": "The boss unleashes its signature move",
	"boss/strike_land": "A strike lands",
	"boss/slash_line": "A giant slash tears the air",
	"boss/black_hole": "Darkness collapses",
	"boss/ground_wave": "A shockwave rolls across the ground",
	"boss/enrage": "The boss is enraged",
	"boss/leap": "The boss leaps",
	"boss/petrify": "Turning to stone",
	"boss/paw": "Air bursts",
	"boss/heal": "Healing flames",
	"style/dash_slash": "A blade dashes past",
	"style/tornado": "Blades whirl into a tornado",
	"style/big_slash": "A flying slash",
	"style/power_up": "Fighting spirit rises",
	"style/kick": "A heavy kick",
	"style/fire_kick": "A leg bursts into flame",
	"style/fire_slash": "A flaming blade",
	"style/shock_punch": "A shockwave punch",
	"style/ground_crush": "The ground caves in",
	"style/water_shot": "Water shots fly",
	"style/water_wave": "A wave crashes",
	"style/hard_skin": "Skin hardens",
	"style/soru": "Someone vanishes",
	"style/shigan": "A finger jab pierces",
	"style/tekkai": "A body turns to iron",
	"style/geppo": "Kicking off the air",
	"style/claw": "A dragon claw crushes",
	"style/cut_flames": "Flames are cut",
	"style/sheathe": "A sword is sheathed",
	"style/lunge": "A fencing lunge",
	"style/chill_blade": "A chilling blade",
	"style/lullaby": "A sad violin plays",
	"style/punch": "A fist of love",
	"style/throw": "Something heavy is thrown",
	"style/slingshot": "A slingshot fires",
}
