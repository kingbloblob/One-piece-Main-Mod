"""
Tiny synthesizer used to make every sound and song in the One Piece mod from scratch.
Nothing is sampled or copied: all audio is math (sine waves, filtered noise), so it is
safe to publish. Needs numpy and ffmpeg (with libvorbis).
"""
import os
import subprocess
import tempfile
import wave

import numpy as np

SR = 44100
RNG = np.random.default_rng(1234)


def secs(n):
	return np.arange(int(n * SR)) / SR


def silence(d):
	return np.zeros(int(d * SR))


def midi(name):
	"""'C#4' -> midi number. 'r' is a rest (None)."""
	if name in ("r", "-"):
		return None
	notes = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
	n = notes[name[0]]
	i = 1
	while i < len(name) and name[i] in "#b":
		n += 1 if name[i] == "#" else -1
		i += 1
	return n + 12 * (int(name[i:]) + 1)


def hz(m):
	return 440.0 * 2 ** ((m - 69) / 12)


def env(n, a=0.01, d=0.1, s=0.7, r=0.1, hold=None):
	"""ADSR envelope, n samples long. The release starts at `hold` seconds (default: end - r)."""
	t = np.arange(n) / SR
	total = n / SR
	hold = total - r if hold is None else hold
	e = np.where(t < a, t / max(a, 1e-6), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-6)))
	rel = np.clip(1 - (t - hold) / max(r, 1e-6), 0, 1)
	return e * np.where(t > hold, rel, 1)


def phase_of(freq, n, vib=0.0, vib_rate=5.5, vib_delay=0.15, glide=None):
	t = np.arange(n) / SR
	f = np.full(n, float(freq))
	if glide is not None:  # glide = (start_freq, time)
		f0, gt = glide
		k = np.clip(t / gt, 0, 1)
		f = f0 * (freq / f0) ** k
	if vib:
		depth = vib * np.clip((t - vib_delay) / 0.3, 0, 1)
		f = f * (1 + depth * np.sin(2 * np.pi * vib_rate * t))
	return 2 * np.pi * np.cumsum(f) / SR


def additive(freq, n, amp_fn, max_h=60, **kw):
	"""Sum of harmonics; amp_fn(k, t) gives each harmonic's level (k = 1, 2, ...)."""
	ph = phase_of(freq, n, **kw)
	t = np.arange(n) / SR
	out = np.zeros(n)
	for k in range(1, max_h + 1):
		if k * freq > SR * 0.45:
			break
		a = amp_fn(k, t)
		if np.isscalar(a) and a < 1e-4:
			continue
		out += a * np.sin(k * ph)
	return out


def fft_filter(x, lo=0.0, hi=None, slope=None):
	"""Band-pass in the frequency domain (soft edges)."""
	X = np.fft.rfft(x)
	f = np.fft.rfftfreq(len(x), 1 / SR)
	g = np.ones_like(f)
	if lo > 0:
		g *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
	if hi:
		g *= 1 / (1 + (f / hi) ** 4)
	return np.fft.irfft(X * g, len(x))


def noise(d):
	return RNG.standard_normal(int(d * SR))


def reverb(x, size=1.6, decay=0.5, wet=0.22, tone=6000):
	n = int(size * SR)
	ir = noise(size) * np.exp(-np.arange(n) / SR / decay)
	ir = fft_filter(ir, 200, tone)
	ir /= np.sqrt(np.sum(ir ** 2))
	L = len(x) + n
	N = 1 << (L - 1).bit_length()
	y = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:L]
	out = np.concatenate([x, np.zeros(n)])
	return out * (1 - wet * 0.5) + y * wet


def finish(x, peak=0.89, tail=0.0):
	x = np.tanh(x / (np.max(np.abs(x)) + 1e-9) * 1.4) / np.tanh(1.4)
	x *= peak
	# Tiny fades so there is never a click at the start or end.
	f = int(0.004 * SR)
	x[:f] *= np.linspace(0, 1, f)
	x[-f:] *= np.linspace(1, 0, f)
	if tail:
		x = np.concatenate([x, silence(tail)])
	return x


def save_ogg(x, path, quality=4, rate=None):
	os.makedirs(os.path.dirname(path), exist_ok=True)
	pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
	with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
		wav = tmp.name
	with wave.open(wav, "wb") as w:
		w.setnchannels(1)
		w.setsampwidth(2)
		w.setframerate(SR)
		w.writeframes(pcm.tobytes())
	resample = ["-ar", str(rate)] if rate else []
	subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, *resample, "-c:a", "libvorbis", "-q:a", str(quality),
					"-ac", "1", path], check=True)
	os.remove(wav)


# ------------------------------------------------------------------ instruments
# Each takes (frequency, duration in seconds, velocity 0-1) and returns samples.

def brass(f, d, v=1.0, vib=0.006):
	n = int((d + 0.12) * SR)
	att = 0.04

	def amp(k, t):
		bright = 2 + 10 * v * np.clip(t / att, 0, 1) * (0.75 + 0.25 * np.exp(-t / 0.4))
		return np.exp(-(k - 1) / bright) / k ** 0.3
	x = additive(f, n, amp, max_h=30, vib=vib, vib_rate=5.2)
	return x * env(n, att, 0.25, 0.8, 0.1, hold=d) * v * 0.35


def strings(f, d, v=1.0):
	n = int((d + 0.3) * SR)
	x = np.zeros(n)
	for det in (-0.006, 0.0, 0.0065):
		x += additive(f * (1 + det), n, lambda k, t: np.exp(-(k - 1) / 7) / k, max_h=24, vib=0.004, vib_rate=4.8)
	return x * env(n, 0.18, 0.4, 0.85, 0.3, hold=d) * v * 0.16


def choir(f, d, v=1.0, vowel="ah"):
	n = int((d + 0.4) * SR)
	formants = {"ah": [(700, 1.0), (1220, 0.5), (2600, 0.25)], "oo": [(300, 1.0), (870, 0.35), (2240, 0.1)]}[vowel]
	x = np.zeros(n)
	for det in (-0.005, 0.004, 0.0):
		def amp(k, t, fr=f * (1 + det)):
			hf = k * fr
			return sum(g * np.exp(-((hf - F) / (F * 0.18)) ** 2) for F, g in formants) + 0.02 / k
		x += additive(f * (1 + det), n, amp, max_h=40, vib=0.008, vib_rate=5.0)
	return x * env(n, 0.25, 0.4, 0.9, 0.4, hold=d) * v * 0.14


def accordion(f, d, v=1.0):
	n = int((d + 0.06) * SR)
	x = np.zeros(n)
	for det in (-0.004, 0.004):  # two reeds, slightly apart: the accordion "wobble"
		x += additive(f * (1 + det), n, lambda k, t: (1.0 if k % 2 else 0.55) / k ** 0.9, max_h=30)
	x = fft_filter(x, 150, 4500)
	return x * env(n, 0.02, 0.15, 0.8, 0.06, hold=d) * v * 0.2


def fiddle(f, d, v=1.0):
	n = int((d + 0.08) * SR)
	x = additive(f, n, lambda k, t: np.exp(-(k - 1) / 9) / k ** 0.8, max_h=30, vib=0.007, vib_rate=6.0, vib_delay=0.08)
	return x * env(n, 0.05, 0.2, 0.85, 0.08, hold=d) * v * 0.25


def whistle(f, d, v=1.0):
	n = int((d + 0.05) * SR)
	x = additive(f, n, lambda k, t: [1, 0.12, 0.05][k - 1] if k <= 3 else 0, max_h=3, vib=0.006, vib_rate=5.5)
	x += fft_filter(RNG.standard_normal(n), 2000, 8000) * 0.015
	return x * env(n, 0.03, 0.1, 0.85, 0.05, hold=d) * v * 0.3


def pluck_bass(f, d, v=1.0):
	n = int((d + 0.05) * SR)
	x = additive(f, n, lambda k, t: np.exp(-(k - 1) / (1 + 7 * np.exp(-t / 0.08))) / k, max_h=30)
	return x * env(n, 0.005, 0.25, 0.45, 0.05, hold=d) * v * 0.55


def synth_bass(f, d, v=1.0):
	n = int((d + 0.03) * SR)
	x = additive(f, n, lambda k, t: np.exp(-(k - 1) / (2.5 + 5 * np.exp(-t / 0.06))) / k, max_h=30)
	x += 0.5 * np.sin(phase_of(f / 2, n))
	return x * env(n, 0.005, 0.12, 0.7, 0.03, hold=d) * v * 0.5


def piano(f, d, v=1.0):
	n = int((d + 0.5) * SR)
	x = additive(f, n, lambda k, t: np.exp(-t * (1.5 + 0.9 * k)) * np.exp(-(k - 1) / 4) / k, max_h=20)
	return x * env(n, 0.003, 1.0, 0.0, 0.4, hold=d) * v * 0.45


def bell(f, d, v=1.0, decay=1.2):
	n = int((d + decay) * SR)
	t = np.arange(n) / SR
	x = np.zeros(n)
	for ratio, g, dk in ((1, 1, 1), (2.0, 0.5, 0.7), (2.76, 0.4, 0.5), (5.4, 0.25, 0.3), (8.93, 0.12, 0.2)):
		if f * ratio < SR * 0.45:
			x += g * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t / (decay * dk))
	return x * np.minimum(t / 0.002, 1) * v * 0.3


def timpani(f, d, v=1.0):
	n = int(max(d, 1.2) * SR)
	t = np.arange(n) / SR
	ph = 2 * np.pi * np.cumsum(f * (1 + 0.08 * np.exp(-t / 0.05))) / SR
	x = (np.sin(ph) + 0.4 * np.sin(1.5 * ph) * np.exp(-t / 0.2)) * np.exp(-t / 0.7)
	x += fft_filter(noise(n / SR), 60, 600) * np.exp(-t / 0.03) * 0.5
	return x * v * 0.7


def kick(v=1.0):
	n = int(0.4 * SR)
	t = np.arange(n) / SR
	f = 45 + 90 * np.exp(-t / 0.03)
	x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18)
	x += fft_filter(noise(0.4), 1000, 6000) * np.exp(-t / 0.004) * 0.3
	return x * v * 0.9


def snare(v=1.0, length=0.25):
	n = int(length * SR)
	t = np.arange(n) / SR
	x = fft_filter(noise(length), 900, 9000) * np.exp(-t / 0.07) * 0.6
	x += np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.04) * 0.6
	return x * v * 0.55


def hat(v=1.0, open_=False):
	d = 0.3 if open_ else 0.06
	n = int(d * SR)
	t = np.arange(n) / SR
	return fft_filter(noise(d), 7000, None) * np.exp(-t / (0.12 if open_ else 0.018)) * v * 0.25


def crash(v=1.0):
	n = int(2.0 * SR)
	t = np.arange(n) / SR
	return fft_filter(noise(2.0), 3500, 14000) * np.exp(-t / 0.6) * np.minimum(t / 0.003, 1) * v * 0.35


def tambourine(v=1.0):
	n = int(0.18 * SR)
	t = np.arange(n) / SR
	jingle = 1 + 0.6 * np.sin(2 * np.pi * 70 * t)
	return fft_filter(noise(0.18), 5000, 13000) * np.exp(-t / 0.05) * jingle * v * 0.3


def tom(f, v=1.0):
	n = int(0.5 * SR)
	t = np.arange(n) / SR
	ph = 2 * np.pi * np.cumsum(f * (1 + 0.5 * np.exp(-t / 0.04))) / SR
	return (np.sin(ph) * np.exp(-t / 0.2) + fft_filter(noise(0.5), 200, 3000) * np.exp(-t / 0.02) * 0.3) * v * 0.7


# ------------------------------------------------------------------ sequencing

class Song:
	"""Places notes on a timeline. Times are in beats; bpm sets the speed."""

	def __init__(self, bpm, beats):
		self.spb = 60.0 / bpm
		self.buf = np.zeros(int((beats * self.spb + 4) * SR))
		self.length = beats * self.spb

	def add(self, beat, samples, gain=1.0):
		i = int(beat * self.spb * SR)
		j = min(len(self.buf), i + len(samples))
		self.buf[i:j] += samples[: j - i] * gain

	def line(self, start, notes, inst, gain=1.0, legato=0.92, transpose=0, **kw):
		"""notes: 'D5:1.5 A4:0.5 r:1' (name:beats). Returns the beat after the last note."""
		b = start
		for tok in notes.split():
			name, dur = tok.split(":")
			dur = float(dur)
			m = midi(name)
			if m is not None:
				self.add(b, inst(hz(m + transpose), dur * self.spb * legato, **kw), gain)
			b += dur
		return b

	def chord(self, beat, names, dur, inst, gain=1.0, **kw):
		for nm in names.split():
			self.add(beat, inst(hz(midi(nm)), dur * self.spb, **kw), gain / len(names.split()) ** 0.5)

	def render(self, wet=0.2, size=1.8, decay=0.6, tail=1.0):
		x = self.buf[: int((self.length + tail) * SR)]
		x = reverb(x, size, decay, wet)
		return x[: int((self.length + tail) * SR)]
