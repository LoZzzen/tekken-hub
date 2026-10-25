#!/usr/bin/env python3
"""Télécharge le texte des pages « <perso> combos » du Wavu Wiki (contenu CC0) dans data/wavu_raw.json."""
import json
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "wavu_raw.json"
PAGES = ["Alisa", "Anna", "Armor_King", "Asuka", "Azucena", "Bob", "Bryan", "Claudio", "Clive", "Devil_Jin", "Dragunov",
         "Eddy", "Fahkumram", "Feng", "Heihachi", "Hwoarang", "Jack-8", "Jin", "Jun", "Kazuya", "King", "Kuma", "Panda",
         "Kunimitsu", "Lars", "Law", "Lee", "Leo", "Leroy", "Lidia", "Lili", "Miary_Zo", "Nina", "Paul", "Raven", "Reina",
         "Shaheen", "Steve", "Victor", "Xiaoyu", "Yoshimitsu", "Zafina"]


def fetch(titles):
    q = urllib.parse.urlencode({
        "action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
        "format": "json", "formatversion": "2", "titles": "|".join(t + "_combos" for t in titles),
    })
    req = urllib.request.Request("https://wavu.wiki/w/api.php?" + q, headers={"User-Agent": "tekken-hub/1.0 (fan site)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main():
    out = {}
    for i in range(0, len(PAGES), 10):
        data = fetch(PAGES[i:i + 10])
        for p in data.get("query", {}).get("pages", []):
            if p.get("missing"):
                print("absent :", p["title"])
                continue
            out[p["title"].replace("_", " ").removesuffix(" combos")] = p["revisions"][0]["slots"]["main"]["content"]
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
    print(len(out), "pages")


if __name__ == "__main__":
    main()
