"""Sound effects for the One Piece mod. Each function returns mono samples."""
import numpy as np

from synth import (SR, additive, bell, brass, choir, env, fft_filter, finish, hz, midi, noise, phase_of, reverb,
				   silence, snare, strings, timpani, crash)


def place(buf, at, x, gain=1.0):
	i = int(at * SR)
	j = min(len(buf), i + len(x))
	buf[i:j] += x[: j - i] * gain


def boom(d=2.5, f0=38, sweep=70, v=1.0):
	n = int(d * SR)
	t = np.arange(n) / SR
	f = f0 + sweep * np.exp(-t / 0.08)
	x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (d * 0.3))
	x += fft_filter(noise(d), 20, 300) * np.exp(-t / (d * 0.25)) * 0.8
	x += fft_filter(noise(d), 300, 3000) * np.exp(-t / 0.05) * 0.4
	return x * v


def metal(f, d=0.9, v=1.0):
	n = int(d * SR)
	t = np.arange(n) / SR
	x = np.zeros(n)
	for r, g, dk in ((1, 1, 1), (2.41, 0.7, 0.8), (3.93, 0.5, 0.6), (5.62, 0.35, 0.45), (7.1, 0.25, 0.35), (9.3, 0.15, 0.25)):
		x += g * np.sin(2 * np.pi * f * r * t + r) * np.exp(-t / (d * 0.35 * dk))
	return x * np.minimum(t / 0.001, 1) * v


def crackle(d, density=60, v=1.0):
	"""Electric sparks: lots of tiny bright clicks."""
	buf = np.zeros(int(d * SR))
	rng = np.random.default_rng(7)
	for _ in range(int(d * density)):
		at = rng.uniform(0, d - 0.03)
		ln = rng.uniform(0.002, 0.012)
		click = fft_filter(noise(ln + 0.01), 2500, 12000)[: int(ln * SR)]
		click *= np.exp(-np.arange(len(click)) / SR / (ln / 3))
		place(buf, at, click, rng.uniform(0.3, 1.0))
	return buf * v


def sweep_noise(d, f_start, f_end, v=1.0):
	"""Whoosh: noise whose brightness glides from f_start to f_end."""
	n = int(d * SR)
	x = noise(d)
	out = np.zeros(n)
	seg = 2048
	for s in range(0, n, seg // 2):
		k = s / n
		fc = f_start * (f_end / f_start) ** k
		chunk = x[s:s + seg]
		if len(chunk) < 64:
			break
		y = fft_filter(chunk, fc * 0.6, fc * 1.6) * np.hanning(len(chunk))
		out[s:s + len(y)] += y
	return out * v


# ------------------------------------------------------------------ Haki

def conqueror_burst():
	d = 3.2
	buf = silence(d)
	place(buf, 0.0, sweep_noise(0.35, 300, 3000, 0.5))
	place(buf, 0.3, boom(2.8, 34, 80, 1.4))
	place(buf, 0.3, crackle(2.2, 90, 0.5))
	# A dark, clashing chord swells under it: the "pressure" of a king's will.
	for m in ("C2", "F#2", "C3", "C#3"):
		x = brass(hz(midi(m)), 1.6, 0.9, vib=0.0)
		place(buf, 0.32, x, 0.5)
	return finish(reverb(buf, 2.2, 0.8, 0.35))


def conqueror_awaken():
	d = 4.0
	buf = silence(d)
	place(buf, 0.0, sweep_noise(1.6, 150, 4000, 0.35))
	for m in ("C3", "G3", "C4", "Eb4", "G4"):
		place(buf, 0.0, choir(hz(midi(m)), 1.8, 0.9), 0.6)
	place(buf, 1.7, boom(2.2, 36, 70, 1.2))
	place(buf, 1.7, crackle(1.5, 70, 0.4))
	for m in ("C3", "G3", "C4", "E4", "G4"):  # resolves to major: the will awakens
		place(buf, 1.7, brass(hz(midi(m)), 1.4, 1.0), 0.45)
	return finish(reverb(buf, 2.5, 0.9, 0.35))


def armament_on():
	d = 1.4
	buf = silence(d)
	place(buf, 0.0, sweep_noise(0.3, 1500, 6000, 0.35))
	place(buf, 0.22, metal(330, 1.1, 0.8))
	place(buf, 0.22, metal(165, 1.0, 0.5))
	place(buf, 0.2, boom(0.6, 60, 80, 0.6))
	return finish(reverb(buf, 1.0, 0.3, 0.2))


def armament_hit():
	d = 0.6
	buf = silence(d)
	place(buf, 0.0, metal(220, 0.5, 0.7))
	place(buf, 0.0, boom(0.4, 70, 120, 0.9))
	return finish(reverb(buf, 0.6, 0.2, 0.15))


def observation_on():
	d = 1.8
	buf = silence(d)
	n = int(1.2 * SR)
	t = np.arange(n) / SR
	for i, base in enumerate((880, 1320, 1760)):
		ph = phase_of(base, n, glide=(base * 0.5, 0.9))
		place(buf, i * 0.04, np.sin(ph) * np.sin(np.pi * t / 1.2) ** 2 * 0.3)
	for i, m in enumerate(("E6", "B6", "E7")):
		place(buf, 0.5 + i * 0.12, bell(hz(midi(m)), 0.1, 0.5, decay=0.8))
	return finish(reverb(buf, 1.6, 0.6, 0.4, tone=9000))


# ------------------------------------------------------------------ Den Den Mushi

def den_den_mushi_call():
	"""'Puru puru puru... gacha!' A warbling snail ring, then the click of picking up."""
	buf = silence(2.6)
	for r in range(3):
		d = 0.42
		n = int(d * SR)
		t = np.arange(n) / SR
		warble = np.where(np.sin(2 * np.pi * 17 * t) > 0, 1, 1.22)  # two tones flipping fast: "purururu"
		f = 1250 * warble * (1 + 0.015 * np.sin(2 * np.pi * 5 * t))
		x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.25 + np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5
		x = fft_filter(x, 500, 5000) * env(n, 0.01, 0.1, 0.9, 0.05)
		place(buf, r * 0.6, x, 0.6)
	# Gacha!
	for k, at in enumerate((1.95, 2.02)):
		ln = 0.06
		click = fft_filter(noise(ln), 800, 5000) * np.exp(-np.arange(int(ln * SR)) / SR / 0.008)
		click += np.sin(2 * np.pi * (400 + 200 * k) * np.arange(int(ln * SR)) / SR) * np.exp(-np.arange(int(ln * SR)) / SR / 0.01) * 0.5
		place(buf, at, click, 0.9)
	return finish(reverb(buf, 0.5, 0.15, 0.12))


# ------------------------------------------------------------------ Devil Fruits

def fruit_eat():
	d = 3.0
	buf = silence(d)
	rng = np.random.default_rng(3)
	for i in range(3):  # three big crunchy bites
		ln = 0.16
		grain = fft_filter(noise(ln), 800, 7000) * (rng.random(int(ln * SR)) > 0.6)
		grain *= np.exp(-np.arange(int(ln * SR)) / SR / 0.05)
		place(buf, 0.05 + i * 0.32, grain, 0.9)
	# Then an eerie, wobbling shimmer: the fruit's power settles in (and it tastes awful).
	n = int(2.0 * SR)
	t = np.arange(n) / SR
	x = np.zeros(n)
	for f in (523, 554, 784, 831, 1046):
		ph = phase_of(f, n, glide=(f * 1.5, 1.6))
		x += np.sin(ph + 3 * np.sin(2 * np.pi * 4.5 * t))
	x *= np.sin(np.pi * np.clip(t / 2.0, 0, 1)) ** 1.5 * 0.12
	place(buf, 0.9, x)
	place(buf, 0.9, choir(hz(midi("C3")), 1.5, 0.6, vowel="oo"), 0.5)
	return finish(reverb(buf, 2.0, 0.7, 0.4))


def fruit_awaken():
	d = 4.5
	buf = silence(d)
	place(buf, 0.0, sweep_noise(1.5, 100, 6000, 0.5))
	for m in ("D3", "A3", "D4", "F#4", "A4", "D5"):
		place(buf, 1.4, brass(hz(midi(m)), 2.0, 1.0), 0.4)
		place(buf, 1.4, choir(hz(midi(m)), 2.2, 1.0), 0.5)
	place(buf, 1.4, boom(2.5, 32, 90, 1.3))
	place(buf, 1.4, crash(1.0), 0.8)
	# Heartbeat drum before the burst: "Drums of Liberation" style, our own rhythm.
	for at in (0.2, 0.42, 0.8, 1.02):
		place(buf, at, timpani(55, 0.5, 0.9))
	return finish(reverb(buf, 2.5, 0.9, 0.3))


# ------------------------------------------------------------------ Bounties and Navy

def bounty_raise():
	d = 1.8
	buf = silence(d)
	rng = np.random.default_rng(11)
	for i in range(9):  # Berries clinking
		place(buf, 0.03 + i * 0.07 + rng.uniform(0, 0.03), metal(rng.uniform(2400, 3600), 0.25, 0.25))
	place(buf, 0.6, brass(hz(midi("D4")), 0.15, 0.8), 0.6)
	place(buf, 0.75, brass(hz(midi("A4")), 0.7, 1.0), 0.7)
	place(buf, 0.75, brass(hz(midi("D4")), 0.7, 0.8), 0.5)
	return finish(reverb(buf, 1.2, 0.4, 0.25))


def news_coo():
	"""A News Coo squawk plus a dramatic sting: the whole world now knows your name."""
	d = 3.0
	buf = silence(d)
	for i, at in enumerate((0.0, 0.35)):
		n = int(0.28 * SR)
		t = np.arange(n) / SR
		f = 1400 + 900 * np.sin(np.pi * t / 0.28) - 400 * t / 0.28
		f *= 1 + 0.03 * np.sin(2 * np.pi * 40 * t)
		ph = 2 * np.pi * np.cumsum(f) / SR
		x = (np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.3 * np.sin(3 * ph)) * np.sin(np.pi * t / 0.28)
		place(buf, at, fft_filter(x, 700, 6000), 0.45)
	for m in ("D3", "F3", "A3", "D4"):
		place(buf, 0.9, brass(hz(midi(m)), 0.25, 1.0), 0.5)
	for m in ("Bb2", "F3", "Bb3", "D4"):
		place(buf, 1.2, brass(hz(midi(m)), 1.2, 1.0), 0.5)
	place(buf, 1.2, timpani(hz(midi("Bb1")), 1.2, 1.0))
	return finish(reverb(buf, 1.6, 0.6, 0.3))


def navy_bugle():
	"""A Marine bugle call. Bugles only play the natural notes of one tube, so it sounds military."""
	s = silence(3.6)
	notes = [("Bb3", 0.18), ("F4", 0.18), ("Bb4", 0.36), ("Bb4", 0.18), ("D5", 0.18), ("F5", 0.6),
			 ("D5", 0.18), ("Bb4", 0.18), ("F5", 1.0)]
	at = 0.0
	for m, ln in notes:
		place(s, at, brass(hz(midi(m)), ln * 0.9, 1.0, vib=0.003))
		at += ln + 0.02
	place(s, 0.0, snare(0.6, 0.2))
	return finish(reverb(s, 2.0, 0.8, 0.35))


def cannon_fire():
	d = 3.0
	buf = silence(d)
	place(buf, 0.0, boom(2.8, 30, 110, 1.5))
	place(buf, 0.0, fft_filter(noise(0.25), 200, 8000) * np.exp(-np.arange(int(0.25 * SR)) / SR / 0.04), 1.0)
	return finish(reverb(buf, 2.5, 1.0, 0.35, tone=3000))


# ------------------------------------------------------------------ Bosses, story, quests

def boss_defeated():
	d = 5.0
	buf = silence(d)
	seq = [("G4", 0.16), ("C5", 0.16), ("E5", 0.16), ("G5", 0.5), ("E5", 0.16), ("G5", 1.6)]
	at = 0.0
	for m, ln in seq:
		place(buf, at, brass(hz(midi(m)), ln * 0.95, 1.0))
		place(buf, at, brass(hz(midi(m)) / 2, ln * 0.95, 0.7), 0.5)
		at += ln + 0.03
	for m in ("C3", "G3", "C4", "E4"):
		place(buf, at - 1.63, strings(hz(midi(m)), 1.6, 1.0), 0.8)
	for i in range(10):  # timpani roll into the last note
		place(buf, 0.75 + i * 0.05, timpani(hz(midi("C2")), 0.2, 0.3 + i * 0.05))
	place(buf, at - 1.63, timpani(hz(midi("C2")), 1.5, 1.0))
	place(buf, at - 1.63, crash(0.9))
	return finish(reverb(buf, 2.0, 0.8, 0.3))


def story_goal():
	buf = silence(1.4)
	place(buf, 0.0, bell(hz(midi("E6")), 0.1, 0.8, 0.6))
	place(buf, 0.12, bell(hz(midi("B6")), 0.1, 0.8, 0.8))
	return finish(reverb(buf, 1.2, 0.5, 0.3), peak=0.7)


def story_chapter():
	d = 4.0
	buf = silence(d)
	seq = [("D5", 0.3), ("A4", 0.15), ("D5", 0.15), ("F#5", 0.3), ("A5", 1.4)]
	at = 0.0
	for m, ln in seq:
		place(buf, at, brass(hz(midi(m)), ln * 0.95, 1.0))
		at += ln
	for m in ("D3", "A3", "D4", "F#4"):
		place(buf, at - 1.4, strings(hz(midi(m)), 1.6, 1.0), 0.9)
	place(buf, at - 1.4, crash(0.7))
	place(buf, at - 1.4, timpani(hz(midi("D2")), 1.2, 0.9))
	return finish(reverb(buf, 2.0, 0.8, 0.3))


def quest_complete():
	buf = silence(1.8)
	for i, m in enumerate(("C6", "E6", "G6", "C7")):
		place(buf, i * 0.09, bell(hz(midi(m)), 0.1, 0.7, 0.8))
	return finish(reverb(buf, 1.2, 0.5, 0.3), peak=0.7)


ALL = {
	"haki/conqueror_burst": conqueror_burst,
	"haki/conqueror_awaken": conqueror_awaken,
	"haki/armament_on": armament_on,
	"haki/armament_hit": armament_hit,
	"haki/observation_on": observation_on,
	"den_den_mushi/call": den_den_mushi_call,
	"devil_fruit/eat": fruit_eat,
	"devil_fruit/awaken": fruit_awaken,
	"bounty/raise": bounty_raise,
	"bounty/news_coo": news_coo,
	"navy/bugle": navy_bugle,
	"navy/cannon": cannon_fire,
	"boss/defeated": boss_defeated,
	"story/goal": story_goal,
	"story/chapter": story_chapter,
	"story/quest_complete": quest_complete,
}
