#!/usr/bin/env python3
"""Кір машина скетчі: уақыт сызбасы + дыбыс. -> .matin/kir-mashina/{data.json,mix.wav}"""
import json, os, wave
import numpy as np

WD = ".matin/kir-mashina"
SR = 48000
rng = np.random.default_rng(7)

# --- уақыт сызбасы
V1, V2 = 7.3, 8.95          # келін сөйлейді
FREEZE = 11.35              # машина тоқтайды
END = 13.6
DOOR, WALK0, WALK1 = 5.2, 5.5, 6.7


def rd(f):
    w = wave.open(f); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if w.getframerate() != SR:
        n = int(len(a) * SR / w.getframerate()); a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a)
    return a


thumps = []
t = 0.75
while t < FREEZE - 0.2:
    calm = t > V1 - 0.2
    thumps.append(round(t, 3))
    t += (0.52 + rng.uniform(0, 0.12)) if calm else rng.uniform(0.27, 0.42)
words = ["ТАРС!", "ДҮҢК!", "ГҮР-ГҮР!", "ТАРС-ТҰРС!", "ДҮҢК!", "ТАРС!", "ДҮҢК-ДҮҢК!", "ГҮР-ГҮР!", "ТАРС!"]
pops, k = [], 0
for i, tt in enumerate(thumps):
    if 1.0 < tt < WALK0 + 0.4 and i % 2 == 0:
        pops.append({"t": tt, "w": words[k % len(words)], "side": k % 2}); k += 1

v1, v2 = rd(f"{WD}/v1.wav"), rd(f"{WD}/v2.wav")
N = int(END * SR); tt = np.arange(N) / SR
mix = np.zeros(N, np.float32)

# мотор
lvl = np.clip((tt - 0.3) / 1.0, 0, 1) * np.where(tt > V1 - 0.3, 0.45, 1.0)
wind = np.clip(1 - (tt - FREEZE) / 0.35, 0, 1); lvl = lvl * wind
f0 = 52 * (0.55 + 0.45 * wind)
ph = 2 * np.pi * np.cumsum(f0) / SR
hum = 0.5 * np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.12 * np.sin(3.1 * ph)
noise = rng.standard_normal(N).astype(np.float32)
lp = np.convolve(noise, np.ones(40) / 40, "same") * 3
mod = 0.7 + 0.3 * np.sin(2 * np.pi * 3.6 * tt)
mix += (0.22 * hum + 0.10 * lp) * mod * lvl

# соққылар
def add(sig, at, g=1.0):
    i = int(at * SR); j = min(N, i + len(sig))
    if i < N: mix[i:j] += g * sig[:j - i]

def thump(g):
    n = int(0.22 * SR); x = np.arange(n) / SR
    body = np.sin(2 * np.pi * (70 - 40 * x / 0.22) * x) * np.exp(-x * 22)
    click = rng.standard_normal(n) * np.exp(-x * 90) * 0.5
    rat = np.sin(2 * np.pi * 820 * x) * rng.standard_normal(n) * np.exp(-x * 30) * 0.25
    return ((body + click + rat) * g).astype(np.float32)

for x in thumps:
    calm = x > V1 - 0.2
    add(thump(0.35 if calm else rng.uniform(0.75, 1.0)), x)

# есік сықыры + қадам
n = int(0.55 * SR); x = np.arange(n) / SR
creak = np.sin(2 * np.pi * np.cumsum(380 + 160 * np.sin(2 * np.pi * 1.6 * x) + 30 * np.sin(2 * np.pi * 37 * x)) / SR)
creak *= np.sin(np.pi * x / 0.55) * 0.12
add(creak.astype(np.float32), DOOR)
for s in (5.75, 6.12, 6.48):
    m = int(0.12 * SR); y = np.arange(m) / SR
    add((np.sin(2 * np.pi * 110 * y) * np.exp(-y * 40) * 0.25 + rng.standard_normal(m) * np.exp(-y * 120) * 0.08).astype(np.float32), s)

# дауыс
add(v1 / (np.abs(v1).max() + 1e-6), V1, 0.9)
add(v2 / (np.abs(v2).max() + 1e-6), V2, 0.9)

mix /= np.abs(mix).max() * 1.12
wave_out = wave.open(f"{WD}/mix.wav", "w"); wave_out.setnchannels(1); wave_out.setsampwidth(2); wave_out.setframerate(SR)
wave_out.writeframes((mix * 32767).astype(np.int16).tobytes()); wave_out.close()

# ауыз анимациясы (30 fps)
def env(a, at):
    hop = SR // 30; r = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a), hop)])
    r = np.clip(r / (np.percentile(r, 92) + 1e-6), 0, 1)
    return {"t": at, "e": [round(float(v), 3) for v in r]}

data = {"fps": 30, "dur": END, "V1": V1, "V2": V2, "FREEZE": FREEZE, "DOOR": DOOR, "WALK0": WALK0, "WALK1": WALK1,
        "d1": len(v1) / SR, "d2": len(v2) / SR, "thumps": thumps, "pops": pops, "mouth": [env(v1, V1), env(v2, V2)]}
json.dump(data, open(f"{WD}/data.json", "w"), ensure_ascii=False)
print(len(thumps), "соққы,", END, "сек")
