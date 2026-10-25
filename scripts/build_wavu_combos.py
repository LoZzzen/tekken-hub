#!/usr/bin/env python3
"""Convertit data/wavu_raw.json (pages « <perso> combos » du Wavu Wiki, CC0) en data/wavu_combos.json,
au format de notation du site : un jeton par étape, séparés par des espaces."""
import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
RAW = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA / "wavu_raw.json"
OUT = DATA / "wavu_combos.json"
SKIP_SECTIONS = {"external links", "references", "see also"}
MAX_PER_CHAR = 80
MOT = {"qcf": ["d", "d/f", "f"], "qcb": ["d", "d/b", "b"], "hcf": ["b", "d/b", "d", "d/f", "f"], "hcb": ["f", "d/f", "d", "d/b", "b"]}
TO_ROSTER = {"Kuma": "Kuma / Panda", "Panda": "Kuma / Panda"}


def clean(s):
    s = re.sub(r"<ref[^>]*/>", "", s)
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"\{\{[^}]*\}\}", "", s)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    return s.replace("'''", "").replace("''", "").strip()


def atoms(chunk):
    """Un morceau sans espace -> liste de jetons."""
    out = []
    chunk = re.sub(r"([()])", r" \1 ", chunk)
    for part in chunk.split():
        if part in "()":
            out.append(part)
            continue
        # préfixes « FC. », « SNK. », « H. » ...
        while True:
            m = re.match(r"^([A-Za-z!]+)\.(?=\S)", part)
            if not m:
                break
            out.append(m.group(1))
            part = part[m.end():]
        for piece in re.split(r"([,~:])", part):
            if not piece or piece == ",":
                continue
            if piece in "~:":
                out.append(piece)
                continue
            m = re.match(r"^(qcf|qcb|hcf|hcb)(\+.*)?$", piece, re.I)
            if m:
                seq = MOT[m.group(1).lower()]
                out.extend(seq[:-1])
                out.append(seq[-1] + (m.group(2) or ""))
                continue
            m = re.match(r"^(ws|WS)(.+)$", piece)
            if m:
                out.extend(["WS", m.group(2)])
                continue
            out.append(piece)
    return out


def convert(s):
    toks = []
    for chunk in s.split():
        toks.extend(atoms(chunk))
    return " ".join(t.replace(" ", "_") for t in toks if t)


STOP = set("the you here this that your with when from only have will can use not are for and but then after before if it to in on of is be as at combo combos note notes also just make sure works work hit hits".split())


def is_prose(k):
    return sum(1 for w in k.split() if w.lower() in STOP) >= 2


def split_dmg(s):
    m = re.match(r"^\[([^\]]*)\]\s*(.*)$", s)
    return (m.group(1).strip(), m.group(2)) if m else ("", s)


def parse(text):
    combos, section, in_list = [], "", False
    starters, conts = [], []

    def emit(sts, body):
        d, b = split_dmg(body)
        if not b.strip() or is_prose(convert(b)):
            return
        label = " / ".join(clean(x) for x in sts)
        combos.append({"sec": section, "s": label, "d": d, "r": b.strip(), "k": convert(b)})

    def flush():
        nonlocal starters, conts
        if conts:
            for c in conts:
                emit(starters, c)
        else:
            for s in starters:
                emit([], s)
        starters, conts = [], []

    for raw in text.split("\n"):
        line = raw.rstrip()
        m = re.match(r"^==\s*([^=].*?)\s*==$", line)
        if m:
            flush()
            section = clean(m.group(1))
            in_list = False
            continue
        if line.startswith("{{Combolist"):
            in_list = True
            continue
        if in_list and line.strip() == "}}":
            flush()
            in_list = False
            continue
        if not in_list or section.lower() in SKIP_SECTIONS:
            continue
        if not line.strip():
            flush()
        elif line.startswith(";"):
            if conts:
                flush()
            starters.append(clean(line[1:]))
        elif line.startswith(":"):
            conts.append(clean(line[1:]))
    flush()
    return combos


def main():
    raw = json.loads(RAW.read_text("utf-8"))
    out = {}
    for name, text in raw.items():
        key = TO_ROSTER.get(name, name)
        items = parse(text)
        if key != name:
            for it in items:
                it["s"] = (name + " : " + it["s"]).strip(" :")
        out.setdefault(key, []).extend(items)
    for k in out:
        out[k] = out[k][:MAX_PER_CHAR]
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), "utf-8")
    print(sum(len(v) for v in out.values()), "combos,", len(out), "personnages")


if __name__ == "__main__":
    main()
