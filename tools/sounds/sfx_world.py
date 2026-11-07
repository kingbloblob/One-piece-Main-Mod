"""Ship, sea and creature sounds. Made from scratch like the rest of sfx.py (no samples).
Ships and sea: sound/ShipSounds.java. Creatures: creature/CreatureSpecies.java voice("...")."""
import numpy as np

from synth import SR, bell, fft_filter, finish, hz, midi, noise, phase_of, reverb, silence
from sfx import boom, crackle, metal, place, sweep_noise
from sfx_combat import drop, rumble, thud, tone_glide, whoosh
from sfx_moves import roar_tone


def t_of(d):
	return np.arange(int(d * SR)) / SR


# ------------------------------------------------------------------ ships and the sea

def creak(f0=140, d=0.7, seed=0):
	"""Wood under strain: a slow stick-slip buzz whose pitch bends."""
	rng = np.random.default_rng(seed)
	n = int(d * SR)
	t = t_of(d)
	f = f0 * (1 + 0.35 * np.sin(np.pi * t / d + rng.uniform(0, 1))) * (1 + 0.03 * fft_filter(noise(d), 1, 20) * 20)
	ph = 2 * np.pi * np.cumsum(f) / SR
	x = (np.sin(ph) > 0.85).astype(float) - 0.15  # stick-slip pulses
	x = fft_filter(x, 150, 3000)
	return x * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5


def ship_creak():
	buf = silence(2.2)
	place(buf, 0.0, creak(120, 1.0, 1), 0.8)
	place(buf, 0.7, creak(190, 0.8, 2), 0.5)
	place(buf, 0.0, fft_filter(noise(1.8), 100, 700) * np.sin(np.pi * t_of(1.8) / 1.8) * 0.15)  # water against the hull
	return finish(reverb(buf, 1.0, 0.4, 0.2, tone=3000), peak=0.7)


def ship_sail():
	"""Canvas filling with wind: a soft flap, then a whoosh."""
	buf = silence(2.0)
	for at, v in ((0.0, 0.8), (0.12, 0.5), (0.5, 0.6)):
		place(buf, at, fft_filter(noise(0.1), 200, 2500) * np.exp(-t_of(0.1) / 0.02), v)
	place(buf, 0.1, whoosh(1.5, 300, 900, 0.6))
	return finish(reverb(buf, 1.0, 0.4, 0.15), peak=0.6)


def ship_wake():
	"""Water rushing along the hull while sailing."""
	d = 2.5
	t = t_of(d)
	x = fft_filter(noise(d), 200, 3000) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.8 * t)) * np.sin(np.pi * t / d) ** 0.5
	buf = silence(d + 0.3)
	place(buf, 0.0, x)
	rng = np.random.default_rng(40)
	for _ in range(8):
		place(buf, rng.uniform(0.2, 2.2), drop(rng.uniform(300, 800), 0.1), 0.15)
	return finish(reverb(buf, 0.8, 0.3, 0.15), peak=0.6)


def ship_launch():
	"""A ship slides into the sea: a long wooden groan and a big splash."""
	buf = silence(2.6)
	place(buf, 0.0, creak(90, 1.0, 3), 0.8)
	t = t_of(1.4)
	place(buf, 0.8, fft_filter(noise(1.4), 150, 5000) * np.exp(-t / 0.35) * np.minimum(t / 0.03, 1), 1.0)
	place(buf, 0.8, boom(1.0, 45, 60, 0.6))
	rng = np.random.default_rng(41)
	for _ in range(14):
		place(buf, rng.uniform(1.0, 2.2), drop(rng.uniform(300, 1000), 0.12), 0.3)
	return finish(reverb(buf, 1.4, 0.5, 0.2))


def splinter(seed=0, n_cracks=10, spread=0.25):
	rng = np.random.default_rng(seed)
	buf = silence(spread + 0.2)
	for _ in range(n_cracks):
		f = rng.uniform(500, 2500)
		place(buf, rng.uniform(0, spread), fft_filter(noise(0.05), f, f * 3) * np.exp(-t_of(0.05) / 0.01), rng.uniform(0.3, 0.9))
	return buf


def ship_hull_hit():
	"""A cannonball smashes into the hull: a heavy thump and wood splintering."""
	buf = silence(1.6)
	place(buf, 0.0, thud(0.5, 50, 1.0))
	place(buf, 0.0, boom(1.0, 40, 90, 0.7))
	place(buf, 0.02, splinter(42, 14, 0.3), 0.9)
	place(buf, 0.1, creak(160, 0.5, 4), 0.4)
	return finish(reverb(buf, 1.0, 0.3, 0.15))


def ship_repair():
	"""Patching the hull: hammer knocks on wood."""
	buf = silence(1.2)
	for i, f in enumerate((420, 400, 440)):
		at = i * 0.28
		place(buf, at, thud(0.15, f * 0.4, 0.5))
		t = t_of(0.15)
		place(buf, at, np.sin(2 * np.pi * f * t) * np.exp(-t / 0.03) * 0.6)
		place(buf, at, fft_filter(noise(0.03), 1500, 6000) * np.exp(-t_of(0.03) / 0.005), 0.4)
	return finish(reverb(buf, 0.6, 0.2, 0.12))


def ship_sink():
	"""A ship goes down: an explosion, the keel cracking in two and water rushing in."""
	buf = silence(4.0)
	place(buf, 0.0, boom(2.5, 30, 80, 1.2))
	place(buf, 0.3, splinter(43, 20, 0.6), 0.8)
	place(buf, 0.6, creak(70, 1.6, 5), 1.0)
	t = t_of(2.5)
	gurgle = fft_filter(noise(2.5), 80, 1500) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t)) * np.sin(np.pi * t / 2.5)
	place(buf, 1.2, gurgle, 0.8)
	rng = np.random.default_rng(44)
	for _ in range(16):
		place(buf, rng.uniform(1.4, 3.4), drop(rng.uniform(80, 300), 0.2), 0.4)
	return finish(reverb(buf, 1.8, 0.6, 0.2))


def ship_break():
	"""More of the hull giving way while it sinks."""
	buf = silence(1.6)
	place(buf, 0.0, creak(85, 0.9, 6), 0.9)
	place(buf, 0.6, splinter(45, 8, 0.3), 0.8)
	place(buf, 0.6, thud(0.4, 45, 0.6))
	return finish(reverb(buf, 1.0, 0.4, 0.15))


def cannonball_splash():
	"""A cannonball misses and plunges into the sea: a plume of water."""
	buf = silence(1.8)
	t = t_of(1.0)
	place(buf, 0.0, fft_filter(noise(1.0), 300, 7000) * np.exp(-t / 0.25) * np.minimum(t / 0.01, 1), 1.0)
	place(buf, 0.0, thud(0.3, 60, 0.6))
	rng = np.random.default_rng(46)
	for _ in range(16):
		place(buf, rng.uniform(0.3, 1.3), drop(rng.uniform(400, 1300), 0.1), 0.3)
	return finish(reverb(buf, 1.0, 0.4, 0.15))


def grapple():
	"""A boarding hook flies out on its rope and bites into the rail."""
	buf = silence(1.2)
	place(buf, 0.0, whoosh(0.5, 400, 2000, 0.8))
	n = int(0.4 * SR)
	place(buf, 0.05, fft_filter(noise(0.4), 1000, 4000) * (np.sin(2 * np.pi * 30 * t_of(0.4)) > 0) * np.exp(-t_of(0.4) / 0.2), 0.3)  # rope
	place(buf, 0.5, metal(1300, 0.4, 0.5))
	place(buf, 0.5, thud(0.2, 120, 0.5))
	return finish(reverb(buf, 0.8, 0.3, 0.15))


def boarding_charge():
	"""Swinging across to board: a rope whoosh and a heavy landing on deck."""
	buf = silence(1.2)
	place(buf, 0.0, whoosh(0.6, 200, 1500, 0.9))
	place(buf, 0.55, thud(0.4, 70, 0.9))
	place(buf, 0.55, creak(150, 0.4, 7), 0.4)
	return finish(reverb(buf, 0.8, 0.3, 0.15))


def whirlpool():
	d = 4.0
	t = t_of(d)
	swirl = fft_filter(noise(d), 60, 1200) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.5 * t)) * np.sin(np.pi * t / d) ** 0.4
	buf = silence(d + 0.4)
	place(buf, 0.0, swirl, 1.0)
	place(buf, 0.0, rumble(d, 0.6))
	return finish(reverb(buf, 1.4, 0.6, 0.25, tone=2000), peak=0.7)


def wave_crash():
	"""A huge wave breaking."""
	d = 3.0
	t = t_of(d)
	surge = sweep_noise(1.2, 200, 1200, 0.7) * np.sin(np.pi * t_of(1.2) / 1.2)
	crash_ = fft_filter(noise(2.0), 100, 7000) * np.exp(-t_of(2.0) / 0.6) * np.minimum(t_of(2.0) / 0.02, 1)
	buf = silence(d + 0.4)
	place(buf, 0.0, surge)
	place(buf, 1.0, crash_, 1.0)
	place(buf, 1.0, boom(1.5, 35, 50, 0.7))
	return finish(reverb(buf, 1.6, 0.6, 0.25))


# ------------------------------------------------------------------ creatures
# Each voice is (call, hurt, death). call(pitch, length) builds one cry; the three versions bend it.

def voiced(f0, d, formant, rough=0.3, glide=1.0, breath=0.3, buzz=40):
	"""An animal voice: a buzzy tone through two mouth formants, its pitch moving by `glide` over the call."""
	n = int(d * SR)
	t = t_of(d)
	f = f0 * glide ** (t / d) * (1 + 0.05 * np.sin(2 * np.pi * 6 * t))
	ph = 2 * np.pi * np.cumsum(f) / SR
	x = np.zeros(n)
	for k in range(1, buzz):
		x += np.sin(k * ph) / k
	x *= 1 + rough * fft_filter(noise(d), 20, 90) * 3
	x = fft_filter(x, formant[0] * 0.5, formant[1] * 2)
	x += fft_filter(noise(d), formant[0], formant[1] * 2) * breath
	return x * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.6


def hiss(d, lo=2500, hi=10000):
	t = t_of(d)
	return fft_filter(noise(d), lo, hi) * np.sin(np.pi * t / d) ** 0.5


def chitter(d, rate=30, f=3000, seed=0):
	rng = np.random.default_rng(seed)
	buf = silence(d)
	for i in range(int(d * rate)):
		ff = f * rng.uniform(0.7, 1.3)
		place(buf, i / rate, fft_filter(noise(0.02), ff, ff * 2) * np.exp(-t_of(0.02) / 0.004), rng.uniform(0.4, 1.0))
	return buf


def servo(d, f0=220, f1=330):
	t = t_of(d)
	x = np.sign(np.sin(phase_of(f1, int(d * SR), glide=(f0, d)))) * 0.3 + fft_filter(noise(d), 2000, 6000) * 0.1
	return fft_filter(x, 100, 5000) * np.sin(np.pi * t / d) ** 0.3


def mix(*parts):
	buf = silence(max(len(p) for p in parts) / SR)
	for p in parts:
		place(buf, 0.0, p)
	return buf


def _pick(kind, call, hurt, death):
	return {"ambient": call, "hurt": hurt, "death": death}[kind]()


VOICES = {
	# Wild Den Den Mushi: a sleepy burble, "puru..."
	"snail": lambda k: _pick(k,
		lambda: np.concatenate([np.sin(phase_of(320, int(0.12 * SR))) * np.sin(np.pi * t_of(0.12) / 0.12) for _ in range(3)]) * 0.6,
		lambda: voiced(500, 0.2, (600, 1800), glide=1.4, breath=0.2) * 0.7,
		lambda: voiced(400, 0.7, (500, 1500), glide=0.5, breath=0.3) * 0.7),
	# Drum reindeer: a short bleating grunt.
	"deer": lambda k: _pick(k,
		lambda: voiced(260, 0.45, (700, 1900), rough=0.5, glide=0.9),
		lambda: voiced(380, 0.2, (800, 2200), rough=0.6, glide=1.3),
		lambda: voiced(240, 0.8, (650, 1700), rough=0.6, glide=0.55)),
	# Sauropods and other giants: a long, deep moan.
	"giant": lambda k: _pick(k,
		lambda: voiced(55, 1.6, (200, 600), rough=0.2, glide=1.2, breath=0.15),
		lambda: voiced(80, 0.5, (250, 800), rough=0.5, glide=1.3),
		lambda: voiced(60, 2.0, (180, 550), rough=0.3, glide=0.6)),
	# Fuzza and big birds: a squawk.
	"bird": lambda k: _pick(k,
		lambda: voiced(700, 0.3, (1500, 3500), rough=0.8, glide=1.2, breath=0.4),
		lambda: voiced(900, 0.15, (1800, 4000), rough=1.0, glide=1.4, breath=0.5),
		lambda: voiced(650, 0.6, (1400, 3200), rough=0.8, glide=0.6, breath=0.5)),
	# Bears, gorillas, the Lapahn: a growl.
	"bear": lambda k: _pick(k,
		lambda: roar_tone(85, 0.9, rough=0.9, formant=(350, 1000)),
		lambda: roar_tone(130, 0.35, rough=1.0, formant=(450, 1300)),
		lambda: roar_tone(75, 1.3, rough=0.8, formant=(300, 900))),
	# Long-legged horse: a whinny.
	"horse": lambda k: _pick(k,
		lambda: voiced(500, 0.9, (900, 2500), rough=0.3, glide=0.7) * (1 + 0.6 * np.sin(2 * np.pi * 14 * t_of(0.9))),
		lambda: voiced(600, 0.25, (1000, 2700), rough=0.6, glide=1.2),
		lambda: voiced(450, 1.1, (800, 2300), rough=0.5, glide=0.45)),
	# Dugongs and seals: a bark.
	"seal": lambda k: _pick(k,
		lambda: np.concatenate([voiced(330, 0.18, (700, 1800), rough=0.6, glide=0.8), silence(0.08), voiced(340, 0.2, (700, 1800), rough=0.6, glide=0.8)]),
		lambda: voiced(450, 0.2, (800, 2100), rough=0.8, glide=1.2),
		lambda: voiced(300, 0.7, (650, 1700), rough=0.6, glide=0.5)),
	# Bulls, Yagara bulls and Momoo: a low moo and a snort.
	"bull": lambda k: _pick(k,
		lambda: np.concatenate([voiced(110, 1.0, (400, 1100), rough=0.3, glide=1.1), hiss(0.2, 300, 2500) * 0.5]),
		lambda: voiced(160, 0.3, (500, 1300), rough=0.7, glide=1.3),
		lambda: voiced(100, 1.4, (380, 1000), rough=0.5, glide=0.55)),
	# Lions, sea cats, manticores: a big cat's roar.
	"cat": lambda k: _pick(k,
		lambda: roar_tone(110, 1.1, rough=0.7, formant=(500, 1500)),
		lambda: voiced(400, 0.25, (900, 2500), rough=0.9, glide=1.2),
		lambda: roar_tone(95, 1.5, rough=0.8, formant=(450, 1300))),
	# Wolves and Komainu: a howl.
	"wolf": lambda k: _pick(k,
		lambda: voiced(380, 1.4, (600, 1600), rough=0.1, glide=1.5, breath=0.15) * 0.8,
		lambda: voiced(700, 0.2, (1000, 2500), rough=0.4, glide=1.3),
		lambda: voiced(420, 1.2, (600, 1500), rough=0.3, glide=0.5)),
	# Snakes, basilisks, salamanders: a hiss and rattle.
	"snake": lambda k: _pick(k,
		lambda: hiss(1.0) * (0.7 + 0.3 * np.sin(2 * np.pi * 25 * t_of(1.0))),
		lambda: hiss(0.3, 2000, 9000),
		lambda: hiss(1.2, 1500, 7000) * np.exp(-t_of(1.2) / 0.6)),
	# Sea monsters: Krakens, Megalo, fighting fish, sky sharks, Sea Kings. A deep, wet bellow.
	"sea_monster": lambda k: _pick(k,
		lambda: roar_tone(48, 1.8, rough=0.6, formant=(200, 700)) + fft_filter(noise(1.8), 60, 500) * 0.3,
		lambda: roar_tone(75, 0.6, rough=0.9, formant=(300, 900)),
		lambda: roar_tone(42, 2.4, rough=0.5, formant=(180, 600))),
	# Monkeys and Humandrills: hoots.
	"monkey": lambda k: _pick(k,
		lambda: np.concatenate([voiced(400 + 60 * i, 0.15, (700, 2000), rough=0.3, glide=1.3) for i in range(4)]),
		lambda: voiced(800, 0.2, (1200, 3000), rough=0.8, glide=1.3),
		lambda: voiced(500, 0.8, (800, 2000), rough=0.6, glide=0.5)),
	# Bananawani, T. rex, Nola: a huge reptile roar.
	"reptile": lambda k: _pick(k,
		lambda: roar_tone(60, 1.5, rough=1.0, formant=(300, 900)),
		lambda: roar_tone(95, 0.5, rough=1.0, formant=(400, 1200)),
		lambda: roar_tone(52, 2.0, rough=0.8, formant=(260, 800))),
	# Punk Hazard dragon: bigger still, with fire in its throat.
	"dragon": lambda k: _pick(k,
		lambda: roar_tone(45, 2.0, rough=1.0, formant=(250, 900)) + fft_filter(noise(2.0), 300, 3000) * 0.2,
		lambda: roar_tone(80, 0.6, rough=1.0, formant=(350, 1100)),
		lambda: roar_tone(40, 2.6, rough=0.9, formant=(220, 800))),
	# Scorpions, centipedes, crabs: clicking.
	"bug": lambda k: _pick(k,
		lambda: mix(chitter(0.6, 35, 3000, 1), thud(0.2, 140, 0.3)),
		lambda: chitter(0.2, 60, 4000, 2),
		lambda: chitter(0.9, 25, 2200, 3) * np.exp(-t_of(0.9) / 0.4)),
	# Pacifista and ancient sentinels: servos and a warning tone.
	"machine": lambda k: _pick(k,
		lambda: np.concatenate([servo(0.4), np.sin(phase_of(880, int(0.25 * SR))) * 0.3 * np.sin(np.pi * t_of(0.25) / 0.25)]),
		lambda: mix(servo(0.25, 400, 200), metal(900, 0.25, 0.4)),
		lambda: servo(1.2, 330, 60)),
	# Homie trees: groaning wood.
	"tree": lambda k: _pick(k,
		lambda: creak(70, 1.2, 8),
		lambda: mix(creak(130, 0.35, 9), splinter(10, 4, 0.1)),
		lambda: np.concatenate([creak(60, 1.0, 11), splinter(12, 12, 0.4)])),
	# Cave moles: squeaks.
	"mole": lambda k: _pick(k,
		lambda: np.concatenate([voiced(1400, 0.08, (2000, 5000), rough=0.2, glide=1.3), silence(0.06), voiced(1500, 0.08, (2000, 5000), rough=0.2, glide=1.3)]),
		lambda: voiced(1800, 0.15, (2500, 6000), rough=0.4, glide=1.4),
		lambda: voiced(1300, 0.5, (2000, 5000), rough=0.4, glide=0.5)),
}


ALL = {
	"ship/creak": ship_creak,
	"ship/sail": ship_sail,
	"ship/wake": ship_wake,
	"ship/launch": ship_launch,
	"ship/hull_hit": ship_hull_hit,
	"ship/repair": ship_repair,
	"ship/sink": ship_sink,
	"ship/break": ship_break,
	"ship/cannonball_splash": cannonball_splash,
	"ship/grapple": grapple,
	"ship/boarding": boarding_charge,
	"sea/whirlpool": whirlpool,
	"sea/wave_crash": wave_crash,
}

SUBTITLES = {
	"ship/creak": "Ship creaks",
	"ship/sail": "Sails fill with wind",
	"ship/wake": "Water rushes past the hull",
	"ship/launch": "A ship is launched",
	"ship/hull_hit": "A hull is hit",
	"ship/repair": "Hammering on wood",
	"ship/sink": "A ship sinks",
	"ship/break": "Timbers crack",
	"ship/cannonball_splash": "A cannonball splashes",
	"ship/grapple": "A boarding hook catches",
	"ship/boarding": "Boarders swing across",
	"sea/whirlpool": "A whirlpool churns",
	"sea/wave_crash": "A huge wave crashes",
}

VOICE_NAMES = {
	"snail": "Den Den Mushi", "deer": "Reindeer", "giant": "Giant beast", "bird": "Bird", "bear": "Beast",
	"horse": "Horse", "seal": "Dugong", "bull": "Bull", "cat": "Big cat", "wolf": "Wolf", "snake": "Snake",
	"sea_monster": "Sea monster", "monkey": "Monkey", "reptile": "Giant reptile", "dragon": "Dragon",
	"bug": "Bug", "machine": "Machine", "tree": "Tree", "mole": "Mole",
}
# Buzzy voices sound much louder than their peak level: turn them down to match the rest.
GAIN = {"snail": 0.7, "machine": 0.55, "wolf": 0.75, "monkey": 0.8, "tree": 0.8}
_KIND = {"ambient": "{} calls", "hurt": "{} hurts", "death": "{} dies"}


def _with_tail(x):
	return np.concatenate([x, silence(0.1)])


for _voice in VOICES:
	for _kind in ("ambient", "hurt", "death"):
		ALL[f"creature/{_voice}_{_kind}"] = (lambda v=_voice, k=_kind: finish(reverb(_with_tail(VOICES[v](k)), 0.6, 0.3, 0.15), peak=0.89 * GAIN.get(v, 1.0)))
		SUBTITLES[f"creature/{_voice}_{_kind}"] = _KIND[_kind].format(VOICE_NAMES[_voice])
