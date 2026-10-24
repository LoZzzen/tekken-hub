#!/usr/bin/env python3
"""Met à jour data/videos.json avec les vidéos des deux chaînes YouTube.

Usage :  pip install yt-dlp  &&  python scripts/update_videos.py

- combos  : chaîne @RyzingSol (une vidéo est rattachée à un personnage si son titre contient le nom)
- replays : chaîne @Tekken8Replays
Les touches saisies à la main (champ "keys") sont conservées d'une mise à jour à l'autre.
"""
import json
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "videos.json"
CHANNELS = {
    "combos": "https://www.youtube.com/@RyzingSol/videos",
    "replays": "https://www.youtube.com/@Tekken8Replays/videos",
}
LIMIT = {"combos": 400, "replays": 150}  # nombre maximum de vidéos par chaîne


def fetch(url, limit):
    cmd = ["yt-dlp", "--flat-playlist", "--playlist-end", str(limit), "-J", url]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit("yt-dlp a échoué :\n" + res.stderr)
    data = json.loads(res.stdout)
    return [{"id": e["id"], "title": e.get("title", "")} for e in data.get("entries", []) if e and e.get("id")]


def main():
    old = json.loads(OUT.read_text("utf-8")) if OUT.exists() else {}
    keys = {v["id"]: v["keys"] for v in old.get("combos", []) if v.get("keys")}
    result = {}
    for name, url in CHANNELS.items():
        vids = fetch(url, LIMIT[name])
        if name == "combos":
            for v in vids:
                if v["id"] in keys:
                    v["keys"] = keys[v["id"]]
        result[name] = vids
        print(f"{name}: {len(vids)} vidéos")
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), "utf-8")


if __name__ == "__main__":
    main()
