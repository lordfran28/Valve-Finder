"""The pieces every warm-up exercise is made of: spelled notes, scales, bars, and the MusicXML writer.

Every note is written at concert pitch (the pitch you hear); the site raises it a whole step for the
B♭ trumpet and shows the valves. Written notes are kept between E3, the lowest note with all three
valves down, and B♭6, double high C on the trumpet."""
import math
from fractions import Fraction as Fr

LET = 'CDEFGAB'
NAT = [0, 2, 4, 5, 7, 9, 11]
LO, HI = 52, 94                      # E3 .. B♭6, concert
ACC = {-2: '𝄫', -1: '♭', 0: '', 1: '♯', 2: '𝄪'}
DIV = 12                             # divisions of a quarter note: eighths, triplets and sixteenths all fit


class Note:
    __slots__ = ('L', 'a', 'o')

    def __init__(self, L, a, o):
        self.L, self.a, self.o = L, a, o

    @property
    def midi(self):
        return 12 * (self.o + 1) + NAT[self.L] + self.a

    @property
    def name(self):
        return LET[self.L] + ACC[self.a] + str(self.o)

    @property
    def pname(self):
        return LET[self.L] + ACC[self.a]

    def __repr__(self):
        return self.name


def spell(midi, L):
    """The note with this pitch written on letter L."""
    base = NAT[L]
    o = (midi - base) // 12 - 1
    a = midi - (12 * (o + 1) + base)
    if a > 6: o += 1; a -= 12
    if a < -6: o -= 1; a += 12
    return Note(L, a, o)


def parse(name):
    """'E♭4', 'F♯3', 'C5', 'F𝄪4' -> Note"""
    L = LET.index(name[0]); rest = name[1:]; a = 0
    while rest and not rest[0].isdigit() and rest[0] != '-':
        a += {'♭': -1, '♯': 1, '𝄫': -2, '𝄪': 2, 'b': -1, '#': 1}[rest[0]]; rest = rest[1:]
    n = Note(L, a, 0); n.o = int(rest)
    return n


# a fixed spelling for chromatic work: sharps going up, flats coming down (as in Arpeggio Mastery's ladders)
UP = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (3, 0), (3, 1), (4, 0), (4, 1), (5, 0), (5, 1), (6, 0)]
DOWN = [(0, 0), (1, -1), (1, 0), (2, -1), (2, 0), (3, 0), (4, -1), (4, 0), (5, -1), (5, 0), (6, -1), (6, 0)]
# and one for single notes, the way a trumpet player names them: B♭ and E♭, F♯ and C♯
PLAIN = [(0, 0), (0, 1), (1, 0), (2, -1), (2, 0), (3, 0), (3, 1), (4, 0), (5, -1), (5, 0), (6, -1), (6, 0)]


def chrom(midi, table=PLAIN):
    L, a = table[midi % 12]
    return spell(midi, L)


# ---------- scales and chords ----------
# each tone is (letter step above the root, semitones above the root)
MAJOR_STEPS = [0, 2, 4, 5, 7, 9, 11]


def hept(semis):
    return [(i, s) for i, s in enumerate(semis)]


def deg(*ds):
    """Degrees by name: '1', 'b3', '#4', '5', 'b7', '9', 'b9', '#9', '11', '#11', 'b13', '13'."""
    out = []
    for d in ds:
        a = d.count('#') - d.count('b'); n = int(d.strip('#b'))
        step = (n - 1) % 7; octv = (n - 1) // 7
        out.append((step + 7 * octv, MAJOR_STEPS[step] + 12 * octv + a))
    return out


SCALES = {
    'major': hept([0, 2, 4, 5, 7, 9, 11]),
    'natural minor': hept([0, 2, 3, 5, 7, 8, 10]),
    'harmonic minor': hept([0, 2, 3, 5, 7, 8, 11]),
    'melodic minor': hept([0, 2, 3, 5, 7, 9, 11]),
    'dorian': hept([0, 2, 3, 5, 7, 9, 10]),
    'phrygian': hept([0, 1, 3, 5, 7, 8, 10]),
    'lydian': hept([0, 2, 4, 6, 7, 9, 11]),
    'mixolydian': hept([0, 2, 4, 5, 7, 9, 10]),
    'locrian': hept([0, 1, 3, 5, 6, 8, 10]),
    'lydian dominant': hept([0, 2, 4, 6, 7, 9, 10]),
    'phrygian dominant': hept([0, 1, 4, 5, 7, 8, 10]),
    'major pentatonic': deg('1', '2', '3', '5', '6'),
    'minor pentatonic': deg('1', 'b3', '4', '5', 'b7'),
    'blues': deg('1', 'b3', '4', 'b5', '5', 'b7'),
    'major blues': deg('1', '2', 'b3', '3', '5', '6'),
    'bebop dominant': deg('1', '2', '3', '4', '5', '6', 'b7', '7'),
    'altered': deg('1', 'b2', '#2', '3', '#4', 'b6', 'b7'),
    'whole tone': deg('1', '2', '3', '#4', '#5', 'b7'),
    'half-whole': deg('1', 'b2', '#2', '3', '#4', '5', '6', 'b7'),
    'whole-half': deg('1', '2', 'b3', '4', 'b5', 'b6', '6', '7'),
}

CHORDS = {   # name suffix, tones
    'major': ('', deg('1', '3', '5')),
    'minor': ('m', deg('1', 'b3', '5')),
    'diminished': ('°', deg('1', 'b3', 'b5')),
    'augmented': ('+', deg('1', '3', '#5')),
    'maj7': ('maj7', deg('1', '3', '5', '7')),
    '7': ('7', deg('1', '3', '5', 'b7')),
    'm7': ('m7', deg('1', 'b3', '5', 'b7')),
    'm7b5': ('ø7', deg('1', 'b3', 'b5', 'b7')),
    'dim7': ('°7', deg('1', 'b3', 'b5', '6')),
    'mmaj7': ('m(maj7)', deg('1', 'b3', '5', '7')),
    'augmaj7': ('+maj7', deg('1', '3', '#5', '7')),
    '7sus4': ('7sus4', deg('1', '4', '5', 'b7')),
    'maj9': ('maj9', deg('1', '3', '5', '7', '9')),
    '9': ('9', deg('1', '3', '5', 'b7', '9')),
    'm9': ('m9', deg('1', 'b3', '5', 'b7', '9')),
    '7b9': ('7♭9', deg('1', '3', '5', 'b7', 'b9')),
    '7#9': ('7♯9', deg('1', '3', '5', 'b7', '#9')),
    '9sus4': ('9sus4', deg('1', '4', '5', 'b7', '9')),
    '69': ('6/9', deg('1', '3', '5', '6', '9')),
}

# the twelve keys, from B♭ (the trumpet's own C) up by half steps, each with the names it can go by
ROOTS = [[(6, -1), (5, 1)], [(6, 0), (0, -1)], [(0, 0)], [(1, -1), (0, 1)], [(1, 0)], [(2, -1), (1, 1)],
         [(2, 0)], [(3, 0)], [(4, -1), (3, 1)], [(4, 0)], [(5, -1), (4, 1)], [(5, 0)]]
ROOT_PC = [10, 11, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def tones_from(root, tones, low):
    """The tones above a root (L, a) with the root at MIDI `low`, each on its own letter where it can be."""
    out = []
    for step, semi in tones:
        m = low + semi
        n = spell(m, (root[0] + step) % 7)
        if abs(n.a) >= 2:                          # B𝄫 in a diminished 7th reads better as A
            alts = [spell(m, (root[0] + step + k) % 7) for k in (-1, 1)]
            n = min(alts, key=lambda x: abs(x.a))
        out.append(n)
    return out


def cost(root, tones):
    ns = tones_from(root, tones, 60 + (NAT[root[0]] + root[1]) % 12)
    r = Note(root[0], root[1], 4)
    return sum(abs(n.a) + (10 if abs(n.a) >= 2 else 0) for n in ns) + abs(r.a), sum(1 for n in ns if n.a > 0)


def best_root(k, tones):
    """For key number k (0 = B♭), the spelling of the root that needs the fewest sharps and flats."""
    return min(ROOTS[k], key=lambda r: cost(r, tones))


def rname(root):
    return LET[root[0]] + ACC[root[1]]


def field(root, tones, lo=LO - 12, hi=HI + 12):
    """Every note of the scale or chord between lo and hi, low to high."""
    pc = (NAT[root[0]] + root[1]) % 12
    out = []
    for base in range(pc - 24, 128, 12):
        for n in tones_from(root, tones, base):
            if lo <= n.midi <= hi:
                out.append(n)
    seen, res = set(), []
    for n in sorted(out, key=lambda n: n.midi):
        if n.midi not in seen:
            seen.add(n.midi); res.append(n)
    return res


def lowest(root, lo=LO):
    pc = (NAT[root[0]] + root[1]) % 12
    m = lo + (pc - lo) % 12
    return m


FIFTHS = {'C': 0, 'G': 1, 'D': 2, 'A': 3, 'E': 4, 'B': 5, 'F♯': 6, 'C♯': 7, 'F': -1, 'B♭': -2, 'E♭': -3, 'A♭': -4, 'D♭': -5, 'G♭': -6, 'C♭': -7,
          'G♯': 8, 'D♯': 9, 'A♯': 10, 'F♭': -8}


def key_fifths(root, kind):
    """The key signature for a scale on this root: the major key whose notes it uses (0 where none fits)."""
    shift = {'major': 0, 'lydian': 1, 'mixolydian': -1, 'dorian': -2, 'natural minor': -3, 'phrygian': -4, 'locrian': -5,
             'harmonic minor': -3, 'melodic minor': -3, 'major pentatonic': 0, 'minor pentatonic': -3, 'blues': -3,
             'major blues': 0, 'bebop dominant': -1, 'lydian dominant': -1, 'phrygian dominant': -4}.get(kind)
    if shift is None:
        return 0
    f = FIFTHS.get(rname(root))
    if f is None:
        return 0
    f += shift
    return f if -7 <= f <= 7 else 0


# ---------- events and bars ----------
class Part:
    """One part of an exercise (one key, or one version): notes and rests in order, with captions."""

    def __init__(self, name, beats=4, beat_type=4, tempo=None, fifths=0, pickup=None):
        self.name, self.beats, self.beat_type, self.tempo, self.fifths = name, beats, beat_type, tempo, fifths
        self.ev = []           # ('n', Note, dur(Fr beats), opts) | ('r', dur) | ('w', text) | ('bar',)
        self.pickup = pickup   # length of a pickup bar, in quarter beats

    def n(self, note, dur, **opts):
        self.ev.append(('n', note, Fr(dur).limit_denominator(48), opts)); return self

    def r(self, dur):
        self.ev.append(('r', Fr(dur).limit_denominator(48))); return self

    def w(self, text):
        self.ev.append(('w', text)); return self

    def bar(self):
        self.ev.append(('bar',)); return self

    def run(self, notes, dur, last=None, **opts):
        """Notes in an even rhythm; the last one held for `last` beats (to the end of the bar when 'bar')."""
        for i, x in enumerate(notes):
            if i == len(notes) - 1 and last is not None:
                if last == 'bar':
                    self.ev.append(('n', x, 'bar', opts))
                else:
                    self.n(x, last, **opts)
            else:
                self.n(x, dur, **opts)
        return self

    @property
    def qlen(self):
        return Fr(self.beats * 4, self.beat_type)

    def measures(self):
        """Pack the events into bars: [{'words': [...], 'items': [(kind, note|None, divs, opts, tie_start, tie_stop)]}]."""
        bl = self.qlen
        bars, cur, t, words = [], [], Fr(0), []
        first_len = Fr(self.pickup) if self.pickup else bl

        def cap():
            return first_len if not bars else bl

        def close():
            nonlocal cur, t, words
            bars.append({'words': words, 'items': cur, 'len': cap() if not bars else bl})
            cur, t, words = [], Fr(0), []

        for e in self.ev:
            if e[0] == 'w':
                words.append(e[1]); continue
            if e[0] == 'bar':
                if t > 0:
                    rem = cap() - t
                    cur.append(('r', None, rem, {}, False, False)); t += rem; close()
                continue
            kind = e[0]
            note = e[1] if kind == 'n' else None
            dur = e[2] if kind == 'n' else e[1]
            opts = e[3] if kind == 'n' else {}
            if dur == 'bar':
                dur = cap() - t
                if dur <= 0:
                    close(); dur = cap()
            first = True
            while dur > 0:
                room = cap() - t
                take = min(dur, room)
                tie_stop = kind == 'n' and not first
                tie_start = kind == 'n' and take < dur
                cur.append((kind, note, take, opts if first else {k: v for k, v in opts.items() if k == 'fing'}, tie_start, tie_stop))
                t += take; dur -= take; first = False
                if t >= cap():
                    close()
        if cur:
            rem = cap() - t
            if rem > 0:
                cur.append(('r', None, rem, {}, False, False))
            close()
        return bars


# note values in divisions (12 to a quarter): (divisions, type, dots, triplet)
VALUES = [(96, 'breve', 0, False), (72, 'whole', 1, False), (48, 'whole', 0, False), (36, 'half', 1, False), (24, 'half', 0, False),
          (18, 'quarter', 1, False), (12, 'quarter', 0, False), (9, 'eighth', 1, False), (8, 'quarter', 0, True), (6, 'eighth', 0, False),
          (4, 'eighth', 0, True), (3, '16th', 0, False), (2, '16th', 0, True), (1, '32nd', 0, True)]


def split_value(d):
    """Split a length in divisions into as few written values as possible."""
    best = {0: []}
    for x in range(1, d + 1):
        opts = [best[x - v[0]] + [v] for v in VALUES if v[0] <= x and (x - v[0]) in best]
        if opts:
            best[x] = min(opts, key=len)
    return best[d]


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def note_xml(kind, note, d, opts, tie_start, tie_stop, full_bar=False):
    out = []
    pieces = split_value(d)
    for i, (dv, typ, dots, trip) in enumerate(pieces):
        ts = tie_stop or i > 0
        tst = tie_start or i < len(pieces) - 1
        x = ['<note>']
        if kind == 'r':
            x.append('<rest measure="yes"/>' if full_bar and len(pieces) == 1 else '<rest/>')
        else:
            x.append('<pitch><step>%s</step>%s<octave>%d</octave></pitch>' % (LET[note.L], '<alter>%d</alter>' % note.a if note.a else '', note.o))
        x.append('<duration>%d</duration>' % dv)
        if kind == 'n':
            if ts: x.append('<tie type="stop"/>')
            if tst: x.append('<tie type="start"/>')
        x.append('<voice>1</voice><type>%s</type>%s' % (typ, '<dot/>' * dots))
        if trip:
            x.append('<time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes></time-modification>')
        if kind == 'n':
            nots = []
            if ts: nots.append('<tied type="stop"/>')
            if tst: nots.append('<tied type="start"/>')
            if opts.get('fing') is not None and i == 0:
                nots.append('<technical><fingering>%s</fingering></technical>' % esc(opts['fing']))
            if opts.get('fermata') and i == len(pieces) - 1:
                nots.append('<fermata type="upright"/>')
            if nots:
                x.append('<notations>%s</notations>' % ''.join(nots))
            if opts.get('lyric') and i == 0:
                x.append('<lyric number="1"><syllabic>single</syllabic><text>%s</text></lyric>' % esc(opts['lyric']))
        x.append('</note>')
        out.append(''.join(x))
    return out


def score_xml(title, parts, credit=None):
    o = ['<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
         '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.1 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">',
         '<score-partwise version="3.1">',
         '  <work><work-title>%s</work-title></work>' % esc(title),
         '  <identification>']
    if credit:
        o.append('    <creator type="composer">%s</creator>' % esc(credit))
    o += ['    <encoding><software>Valve Finder</software></encoding>', '  </identification>', '  <part-list>']
    for i, p in enumerate(parts):
        o.append('    <score-part id="P%d"><part-name>%s</part-name></score-part>' % (i + 1, esc(p.name)))
    o.append('  </part-list>')
    for i, p in enumerate(parts):
        o.append('  <part id="P%d">' % (i + 1))
        for bi, b in enumerate(p.measures()):
            imp = ' implicit="yes"' if (bi == 0 and p.pickup) else ''
            o.append('    <measure number="%d"%s>' % (bi if p.pickup else bi + 1, imp))
            if bi == 0:
                o.append('      <attributes><divisions>%d</divisions><key><fifths>%d</fifths></key><time><beats>%d</beats><beat-type>%d</beat-type></time><clef><sign>G</sign><line>2</line></clef></attributes>'
                         % (DIV, p.fifths, p.beats, p.beat_type))
                if p.tempo:
                    o.append('      <direction placement="above"><direction-type><metronome><beat-unit>quarter</beat-unit><per-minute>%d</per-minute></metronome></direction-type><sound tempo="%d"/></direction>' % (p.tempo, p.tempo))
            for wd in b['words']:
                o.append('      <direction placement="above"><direction-type><words>%s</words></direction-type></direction>' % esc(wd))
            full = len(b['items']) == 1 and b['items'][0][0] == 'r'
            for kind, note, d, opts, ts, tst in b['items']:
                dv = d * DIV
                assert dv.denominator == 1, (p.name, bi, d)
                for line in note_xml(kind, note, int(dv), opts, ts, tst, full_bar=full):
                    o.append('      ' + line)
            o.append('    </measure>')
        o.append('  </part>')
    o.append('</score-partwise>')
    return '\n'.join(o) + '\n'
