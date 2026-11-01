#!/usr/bin/env python3
"""Writes songs/index.json: the list of songs the site shows.

Every MIDI, MusicXML or Tony .csv file anywhere under songs/ is a song. A file may have a
companion "<file>.vf.json", written by the site, holding its title, settings and playing notes.
"""
import datetime, hashlib, json, os, re, subprocess, unicodedata

ROOT = "songs"
KINDS = {".mid": "MIDI", ".midi": "MIDI", ".musicxml": "MusicXML", ".xml": "MusicXML", ".mxl": "MusicXML", ".csv": "Note list"}
OUT = os.path.join(ROOT, "index.json")


# Composers go first in a title ("Badinerie, Bach Suite No. 2" -> "Bach – Badinerie, Suite No. 2"),
# so the list reads A to Z by composer. The site does the same for songs added there.
COMPOSERS = ["Bach", "Handel", "Vivaldi", "Purcell", "Telemann", "Albinoni", "Pachelbel", "Corelli", "Scarlatti",
             "Monteverdi", "Caccini", "Gluck", "Haydn", "Mozart", "Beethoven", "Schubert", "Schumann", "Mendelssohn",
             "Chopin", "Liszt", "Brahms", "Wagner", "Verdi", "Puccini", "Rossini", "Bellini", "Donizetti", "Bizet",
             "Gounod", "Massenet", "Offenbach", "Fauré", "Saint-Saëns", "Debussy", "Ravel", "Satie", "Grieg", "Dvořák",
             "Tchaikovsky", "Rachmaninoff", "Rimsky-Korsakov", "Mussorgsky", "Borodin", "Glinka", "Elgar", "Holst",
             "Mahler", "Sibelius", "Arban", "Hummel", "Charpentier", "Mouret", "Paganini", "Boccherini", "Granados",
             "Albéniz", "Gershwin"]


def fold(t):
    t = unicodedata.normalize("NFD", str(t))
    return "".join(c for c in t if not unicodedata.combining(c)).replace("’", "'").replace("‘", "'").lower()


def composer_first(t):
    t = str(t or "").strip()
    f, at = "", []
    for i, ch in enumerate(t):
        g = fold(ch)
        f += g
        at += [i] * len(g)
    at.append(len(t))
    for name in COMPOSERS:
        c = fold(name)
        if any(f.startswith(c + d) for d in (" – ", " - ", " — ")):
            return t
    for name in COMPOSERS:
        m = re.search(r"(^|[^a-z])((?:[a-z]\.? ?){0,2})" + re.escape(fold(name)) + r"('s)?(?:-|(?![a-z]))", f)
        if not m:
            continue
        a, b = m.start() + len(m.group(1)), m.end()
        rest = t[:at[a]] + " " + t[at[b]:]
        rest = re.sub(r"\(\s*\)", "", rest)
        rest = re.sub(r"\s+([,;:)])", r"\1", rest)
        rest = re.sub(r"([,;:(])\s*(?=[,;:)])", "", rest)
        rest = re.sub(r"\s{2,}", " ", rest)
        rest = re.sub(r"^[\s,;:–—-]+|[\s,;:–—-]+$", "", rest)
        return name + " – " + rest if rest else t
    return t


def first_added(path):
    try:
        out = subprocess.run(["git", "log", "--diff-filter=A", "--follow", "--format=%aI", "--", path],
                             capture_output=True, text=True, check=True).stdout.split()
        if out:
            return out[-1]
    except Exception:
        pass
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def utc(stamp):
    try:
        d = datetime.datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=datetime.timezone.utc)
        return d.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha1(path):
    with open(path, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()


def slug(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "song"


def main():
    songs, used = [], set()
    for folder, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for name in sorted(files):
            stem, ext = os.path.splitext(name)
            if ext.lower() not in KINDS or name.startswith("."):
                continue
            path = os.path.join(folder, name).replace(os.sep, "/")
            side = {}
            try:
                with open(path + ".vf.json", encoding="utf-8") as f:
                    side = json.load(f) or {}
            except (OSError, ValueError):
                side = {}
            sid = str(side.get("id") or "")
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", sid) or sid in used:
                base = slug(os.path.splitext(path[len(ROOT) + 1:])[0])
                sid, n = base, 2
                while sid in used:
                    sid, n = "%s-%d" % (base, n), n + 1
            used.add(sid)
            entry = {
                "id": sid,
                "file": path,
                "title": str(side.get("title") or composer_first(stem.replace("_", " ").strip()) or "Untitled song"),
                "kind": KINDS[ext.lower()],
                "sha1": sha1(path),
                "addedAt": utc(side.get("addedAt") or first_added(path)),
            }
            units = side.get("units")
            if isinstance(units, dict) and isinstance(units.get("count"), int):
                entry["units"] = {"count": units["count"], "unit": str(units.get("unit") or "Bar")}
            songs.append(entry)
    songs.sort(key=lambda s: (str(s["addedAt"]), s["file"]))

    try:
        with open(OUT, encoding="utf-8") as f:
            if json.load(f).get("songs") == songs:
                print("Song list unchanged (%d songs)." % len(songs))
                return
    except (OSError, ValueError, AttributeError):
        pass
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"app": "Valve Finder", "generatedAt": now, "songs": songs}, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("Wrote %d songs." % len(songs))


if __name__ == "__main__":
    main()
