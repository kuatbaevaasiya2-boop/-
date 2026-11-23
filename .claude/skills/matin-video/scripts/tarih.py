#!/usr/bin/env python3
"""tarih.py — «тарих» стилі: түнгі сахна, баяндаушы ата, адамдар тек сұлбамен (беті жоқ).
Дауыс пен сөз уақыты matin.py voice-тан алынады (timeline.json).

  raskadrovka PLAN.json            -> Раскадровка/<аты>_раскадровка.jpg
  render      PLAN.json [--max-mb 90] -> Дайын/<аты>_vN.mp4
  oblozhka    PLAN.json            -> Дайын/<аты>_обложка.jpg
"""
import argparse, json, os, re, subprocess, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TD = os.path.join(os.path.dirname(HERE), "tarih")
FPS = 30


def prep(plan):
    P = json.load(open(plan, encoding="utf-8"))
    wd = os.path.join(".matin", P["name"]); os.makedirs(wd, exist_ok=True)
    TL = json.load(open(P["timeline"], encoding="utf-8"))
    scenes = []
    for si, (sc, ts) in enumerate(zip(P["scenes"], TL["scenes"])):
        emph = set()
        for m in re.finditer(r"\*([^*]+)\*", sc["text"]):
            emph |= {re.sub(r"[^\wәғқңөұүһі]", "", w.lower()) for w in m.group(1).split()}
        words = []
        for w in ts["words"]:
            txt = w["w"].replace("*", "")
            if not re.search(r"\w", txt):
                if words: words[-1]["w"] += " " + txt
                continue
            words.append({"w": txt, "e": re.sub(r"[^\wәғқңөұүһі]", "", txt.lower()) in emph, "t": round(w["s"], 3)})
        scenes.append({"card": sc["card"], "t0": 0.0 if si == 0 else round(ts["s"] - 0.3, 3), "words": words})
    for si, sc in enumerate(scenes):
        sc["t1"] = scenes[si + 1]["t0"] if si + 1 < len(scenes) else TL["dur"] + 1.5
    wav = os.path.join(wd, "env.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", P["audio"], "-ar", "16000", "-ac", "1", wav], check=True)
    wv = wave.open(wav); a = np.frombuffer(wv.readframes(wv.getnframes()), np.int16).astype(np.float32) / 32768
    hop = 16000 // FPS
    rms = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a), hop)])
    rms = rms / (np.percentile(rms, 95) + 1e-6)
    env = np.convolve(np.clip((rms - 0.12) / 0.8, 0, 1), [0.25, 0.5, 0.25], "same")
    dur = len(a) / 16000 + 1.5
    data = {"fps": FPS, "dur": round(dur, 3), "title": P.get("title", ""), "env": [round(float(x), 3) for x in env], "scenes": scenes}
    json.dump(data, open(os.path.join(wd, "data.json"), "w"), ensure_ascii=False)
    return P, wd, data


def node(*args, stdout=None):
    return subprocess.Popen(["node", os.path.join(TD, "render.js"), *args], stdout=stdout)


def raskadrovka(plan):
    P, wd, data = prep(plan)
    ts = [round(min(s["t1"] - 0.3, s["words"][-1]["t"] + 0.6), 2) for s in data["scenes"]]
    fd = os.path.join(wd, "rf"); os.makedirs(fd, exist_ok=True)
    for f in os.listdir(fd): os.remove(os.path.join(fd, f))
    node(os.path.join(wd, "data.json"), "frames", ",".join(map(str, ts)), fd).wait()
    os.makedirs("Раскадровка", exist_ok=True)
    out = f"Раскадровка/{P['name']}_раскадровка.jpg"
    n = len(ts); cols = 3 if n <= 9 else 4
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(fd, "f%02d.jpg"),
                    "-vf", f"scale=360:640,pad=376:656:8:8:color=0x2b2b2b,tile={cols}x{(n + cols - 1) // cols}:color=0x2b2b2b",
                    "-frames:v", "1", "-q:v", "3", out], check=True)
    print(out)


def oblozhka(plan):
    P, wd, data = prep(plan)
    fd = os.path.join(wd, "cov"); os.makedirs(fd, exist_ok=True)
    node(os.path.join(wd, "data.json"), "frames", "-1", fd).wait()
    os.makedirs("Дайын", exist_ok=True)
    out = f"Дайын/{P['name']}_обложка.jpg"
    os.replace(os.path.join(fd, "f00.jpg"), out); print(out)


def render(plan, max_mb):
    P, wd, data = prep(plan)
    os.makedirs("Дайын", exist_ok=True)
    v = 1
    while os.path.exists(f"Дайын/{P['name']}_v{v}.mp4"): v += 1
    out = f"Дайын/{P['name']}_v{v}.mp4"
    br = int(min(12000, max_mb * 8 * 1024 * 0.92 / data["dur"] - 192))
    pr = node(os.path.join(wd, "data.json"), "video", "", "", stdout=subprocess.PIPE)
    af = "[1:a]apad[a]"
    if P.get("music"):
        af = f"[1:a]apad[v];[2:a]volume={P.get('music_volume', 0.12)},aloop=-1:2e9[m];[v][m]amix=inputs=2:duration=first[a]"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-", "-i", P["audio"]]
    if P.get("music"): cmd += ["-i", P["music"]]
    cmd += ["-filter_complex", af, "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "medium",
            "-b:v", f"{br}k", "-maxrate", f"{br}k", "-bufsize", f"{2 * br}k", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out]
    subprocess.run(cmd, stdin=pr.stdout); pr.wait()
    print(out, os.path.getsize(out) // 1024 // 1024, "MB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("plan"); ap.add_argument("--max-mb", type=float, default=90)
    a = ap.parse_args()
    {"raskadrovka": lambda: raskadrovka(a.plan), "render": lambda: render(a.plan, a.max_mb), "oblozhka": lambda: oblozhka(a.plan)}[a.cmd]()
