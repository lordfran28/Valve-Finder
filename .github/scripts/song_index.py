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
COMPOSERS = ["C. P. E. Bach", "Bach", "Handel", "Vivaldi", "Purcell", "Telemann", "Albinoni", "Pachelbel", "Corelli", "Scarlatti",
             "Monteverdi", "Caccini", "Gluck", "Haydn", "Mozart", "Beethoven", "Schubert", "Schumann", "Mendelssohn",
             "Chopin", "Liszt", "Brahms", "Wagner", "Verdi", "Puccini", "Rossini", "Bellini", "Donizetti", "Bizet",
             "Gounod", "Massenet", "Offenbach", "Fauré", "Saint-Saëns", "Debussy", "Ravel", "Satie", "Grieg", "Dvořák",
             "Tchaikovsky", "Rachmaninoff", "Rimsky-Korsakov", "Mussorgsky", "Borodin", "Glinka", "Elgar", "Holst",
             "Mahler", "Sibelius", "Arban", "Hummel", "Charpentier", "Mouret", "Paganini", "Boccherini", "Granados",
             "Albéniz", "Gershwin"]


def fold(t):
    t = unicodedata.normalize("NFD", str(t))
    return "".join(c for c in t if not unicodedata.combining(c)).replace("’", "'").replace("‘", "'").lower()


SMALL = {"a", "an", "and", "as", "at", "but", "by", "de", "del", "for", "from", "in", "into", "la", "nor", "of", "on", "or", "the", "to", "with", "y"}
ACC = {"b": "♭", "#": "♯"}


def clean_title(t):
    """A file name from a transcriber or a download becomes a readable title (the site does the same)."""
    t = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u266C\u2670-\u27BF\uFE0F]", " ", str(t or "")).replace("_", " ").strip()
    t = re.sub(r"\s*\(\d+\)\s*$", "", t)
    key = ""
    m = re.search(r"-(?:wind|brass|guitar|piano|vocals?|voice|strings|bass|drums|other)?-?([A-G])([b#♭♯]?)(?:\s*(major|minor|maj|min|m))?-?(?:-?\d+\s*bpm)?(?:-?\d+\s*hz)?-?\s*$", t, re.I)
    if m and re.search(r"bpm|hz|major|minor|-\s*$", m.group(0), re.I):
        mode = m.group(3) or ""
        key = m.group(1).upper() + ACC.get(m.group(2), m.group(2)) + ((" minor" if re.match(r"min|m$", mode, re.I) else " major") if mode else "")
        t = t[:m.start()]
    t = re.sub(r"-\d+\s*bpm|-\d+\s*hz", "", t, flags=re.I)
    m = re.search(r"[\s-]+([A-G])([b#♭♯]?)\s+(major|minor)\s*-?\s*$", t, re.I)
    if m:
        key = m.group(1).upper() + ACC.get(m.group(2), m.group(2)) + " " + m.group(3).lower()
        t = t[:m.start()]
    raw = bool(key) or bool(re.search(r"\s-\s|-\s|\s-", t)) or (" " not in t and "-" in t)
    t = re.sub(r"\s*-?\s*\b(trumpet solo transcription|trumpet cover|instrumental trompete|instrumental|trompete|transcription)\b", " ", t, flags=re.I)
    t = re.sub(r"\(\s*trumpet\s*\)", " ", t, flags=re.I)
    if " " not in t and "-" in t:
        t = re.sub(r"-+", " ", t)
    if raw:
        t = re.sub(r"(\)|\s)\s*trumpet\s*(,|$)", r"\1\2", t, flags=re.I)
        t = re.sub(r"\s+-\s*|\s*-\s+", ", ", t)
        t = re.sub(r"\(\s+", "(", re.sub(r"\s+\)", ")", t))
    t = re.sub(r"\s{2,}", " ", t).strip(" -,")
    letters = re.sub(r"[^A-Za-z]", "", t)
    if letters and (raw or letters.isupper() or letters.islower()):
        words = re.split(r"(\s+)", t)
        out = []
        for i, w in enumerate(words):
            if not w.strip():
                out.append(w)
                continue
            if re.fullmatch(r"[A-Z][A-Z']+", w) and not re.fullmatch(r"BWV|HWV|RV|[IVXLC]+", w) or letters.isupper():
                w = w[:1] + w[1:].lower()
            bare = re.sub(r"[^a-z]", "", w.lower())
            last = i == len(words) - 1
            prev = "".join(out).rstrip()
            if i > 0 and not last and bare in SMALL and not prev.endswith(("(", ",")):
                w = w.lower()
            elif w[:1].islower():
                w = w[:1].upper() + w[1:]
            out.append(w)
        t = "".join(out)
    if key and not re.search(r"\([A-G][♭♯]?( major| minor)?\)\s*$", t):
        t += " (" + key + ")"
    return t


def composer_first(t):
    t = clean_title(t)
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


def removed_songs(present):
    """Songs deleted from the folder, from the git history: devices drop their own copies of these."""
    try:
        log = subprocess.run(["git", "log", "--diff-filter=D", "--name-only", "--format=@%H %cI", "--", "."],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    out, seen, commit, at = [], set(), None, None
    for line in log.splitlines():
        if line.startswith("@"):
            commit, at = line[1:].split(" ", 1)
            continue
        path = line.strip()
        if not path or os.path.splitext(path)[1].lower() not in KINDS:
            continue
        try:
            blob = subprocess.run(["git", "show", "%s^:%s" % (commit, path)], cwd=os.path.dirname(ROOT) or ".",
                                  capture_output=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError):
            continue
        h = hashlib.sha1(blob).hexdigest()
        if h in present or (h, path) in seen:
            continue
        seen.add((h, path))
        out.append({"file": path, "sha1": h, "at": utc(at)})
    return out


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
            if side.get("era") in ("classical",):
                entry["era"] = side["era"]
            if isinstance(side.get("year"), int):
                entry["year"] = side["year"]
            units = side.get("units")
            if isinstance(units, dict) and isinstance(units.get("count"), int):
                entry["units"] = {"count": units["count"], "unit": str(units.get("unit") or "Bar")}
            songs.append(entry)
    songs.sort(key=lambda s: (str(s["addedAt"]), s["file"]))
    removed = removed_songs({s["sha1"] for s in songs})

    try:
        with open(OUT, encoding="utf-8") as f:
            old = json.load(f)
            if old.get("songs") == songs and old.get("removed", []) == removed:
                print("Song list unchanged (%d songs)." % len(songs))
                return
    except (OSError, ValueError, AttributeError):
        pass
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"app": "Valve Finder", "generatedAt": now, "songs": songs, "removed": removed}, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("Wrote %d songs." % len(songs))


if __name__ == "__main__":
    main()
