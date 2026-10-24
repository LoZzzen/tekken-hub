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


def fetch_descriptions(ids, cache):
    """Récupère la description des vidéos (pour y lire la notation des combos). Ignore les échecs."""
    todo = [i for i in ids if i not in cache]
    for k in range(0, len(todo), 10):
        batch = todo[k:k + 10]
        cmd = ["yt-dlp", "-j", "--skip-download", "--no-warnings", "--ignore-errors"] + [
            "https://www.youtube.com/watch?v=" + i for i in batch
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        for line in res.stdout.splitlines():
            try:
                e = json.loads(line)
                cache[e["id"]] = (e.get("description") or "")[:8000]
            except Exception:
                pass
        print(f"descriptions: {len(cache)} (lot {k // 10 + 1}), erreurs: {res.stderr.count('ERROR')}")
    return cache


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

    # Descriptions des guides de combos Tekken 8 (cache dans data/desc.json, non chargé par le site)
    dpath = OUT.parent / "desc.json"
    cache = json.loads(dpath.read_text("utf-8")) if dpath.exists() else {}
    ids = [v["id"] for v in result["combos"] if "combo guide" in v["title"].lower() and "tekken 8" in v["title"].lower()][:60]
    fetch_descriptions(ids, cache)
    dpath.write_text(json.dumps(cache, ensure_ascii=False, indent=1), "utf-8")


if __name__ == "__main__":
    main()
