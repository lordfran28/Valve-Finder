#!/usr/bin/env python3
"""Writes the warm-up into songs/Warm-up/: one MusicXML file per exercise, with its .vf.json beside it.

python3 tools/warmup/make_warmup.py

Each exercise is one entry in the library's Warm-up group, in playing order. An exercise played in every
key has one part per key, from B♭ (the trumpet's own C) up by half steps. Notes are at concert pitch."""
import datetime, json, os, sys
from fractions import Fraction as Fr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from core import (Part, Note, LO, HI, LET, NAT, SCALES, CHORDS, ROOT_PC, spell, parse, chrom, UP, DOWN, PLAIN, deg,
                  tones_from, best_root, rname, field, lowest, key_fifths, score_xml, split_value, VALUES)

REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(REPO, 'songs', 'Warm-up')
AM = json.load(open(os.path.join(HERE, 'arpeggio_mastery.json'), encoding='utf-8'))
NOW = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

# the site's fingering chart (written pitch), to know when a written-in fingering is needed
FING = {42: "123", 43: "13", 44: "23", 45: "12", 46: "1", 47: "2", 48: "0", 49: "123", 50: "13", 51: "23", 52: "12", 53: "123", 54: "123", 55: "13", 56: "23",
        57: "12", 58: "1", 59: "2", 60: "0", 61: "123", 62: "13", 63: "23", 64: "12", 65: "1", 66: "2", 67: "0", 68: "23", 69: "12", 70: "1", 71: "2", 72: "0",
        73: "12", 74: "1", 75: "2", 76: "0", 77: "1", 78: "2", 79: "0", 80: "23", 81: "12", 82: "1", 83: "2", 84: "0", 85: "12", 86: "1", 87: "2", 88: "0",
        89: "1", 90: "2", 91: "0", 92: "23", 93: "12", 94: "1", 95: "2", 96: "0"}


def chart(midi):
    return FING.get(midi + 2)


ENTRIES = []


def entry(order, title, parts, tempo, lead, notes=None, facts=None, sections=None):
    ENTRIES.append(dict(order=order, title=title, parts=parts, tempo=tempo, lead=lead, notes=notes or {}, facts=facts, sections=sections))


class P(Part):
    """A Part that knows where it is in the bar, so held notes end on a beat and breaths fall between legs."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.t = Fr(0)

    def _adv(self, d):
        self.t += Fr(d)

    def n(self, note, dur, **o):
        super().n(note, dur, **o); self._adv(Fr(dur).limit_denominator(48)); return self

    def r(self, dur):
        super().r(dur); self._adv(Fr(dur).limit_denominator(48)); return self

    def bar(self):
        super().bar()
        q = self.qlen
        if self.t % q: self.t += q - self.t % q
        return self

    def to_bar_end(self, note, **o):
        """Hold to the end of the bar, as one written note: where no single note fits, a shorter one and a rest."""
        q = self.qlen; rem = q - self.t % q
        d = int(rem * 12)
        if len(split_value(d)) == 1:
            return self.n(note, rem, **o)
        for v in sorted((x[0] for x in VALUES), reverse=True):
            if v < d and len(split_value(d - v)) == 1:
                return self.n(note, Fr(v, 12), **o).r(Fr(d - v, 12))
        return self.n(note, rem, **o)

    def run(self, notes, dur, last=None, **o):
        for i, x in enumerate(notes):
            if i == len(notes) - 1 and last == 'bar':
                self.to_bar_end(x, **o)
            elif i == len(notes) - 1 and last is not None:
                self.n(x, last, **o)
            else:
                self.n(x, dur, **o)
        return self

    def leg(self, notes, dur=Fr(1, 2), breath=1, **o):
        """A run whose last note is held to the next beat and a beat more (never across the bar line), then a breath."""
        for x in notes[:-1]:
            self.n(x, dur, **o)
        q = self.qlen; pos = self.t % q
        hold = (1 - pos % 1) if pos % 1 else 1
        if pos % 1: hold += 1
        hold = min(hold, q - pos)
        self.n(notes[-1], hold, **o)
        if breath:
            self.r(breath)
        return self


def updown(notes):
    return notes + notes[-2::-1]


def plain_range(a, b, table=PLAIN):
    step = 1 if b >= a else -1
    return [chrom(m, table) for m in range(a, b + step, step)]


SERIES = [('0', 'Open, the B♭ series'), ('2', 'Valve 2, the A series'), ('1', 'Valve 1, the A♭ series'), ('12', 'Valves 1 and 2, the G series'),
          ('23', 'Valves 2 and 3, the G♭ series'), ('13', 'Valves 1 and 3, the F series'), ('123', 'All three valves, the E series')]
SERIES_ROOT = [(6, -1), (5, 0), (5, -1), (4, 0), (4, -1), (3, 0), (2, 0)]
PARTIALS = {2: '1', 3: '5', 4: '8', 5: '10', 6: '12', 8: '15', 10: '17', 12: '19', 16: '22'}


def series(s, ps):
    """The notes of valve combination s on the given partials (2 = the lowest regular note)."""
    root = SERIES_ROOT[s]
    return tones_from(root, deg(*[PARTIALS[p] for p in ps]), 58 - s)


# =====================================================================================================
# 1. Long tones
def long_tones():
    parts = []
    def lt(name, ms, table):
        p = P(name, 8, 4, 60)
        for m in ms:
            p.n(chrom(m, table), 6).r(2)
        parts.append(p); return p
    lt('Middle: F4 down to B3', range(65, 58, -1), DOWN)
    lt('Low: B♭3 down to E3', range(58, 51, -1), DOWN)
    lt('Middle and low: F4 down to E3', range(65, 51, -1), DOWN)
    lt('Up: F4 to B♭5', range(65, 83), PLAIN)
    lt('Top: B♭5 to double high B♭6', range(82, 95), PLAIN)
    sw = lt('Swells, soft to loud to soft: F4 down to E3', range(65, 51, -1), DOWN)
    notes = {'%d:%d:0' % (5, i): 'swell' for i in range(14)}
    entry(10, 'Long tones', parts, 60,
          'Slow notes to wake up the lips and warm the horn. Play each one softly with a steady, centered sound, and rest as long as the rest in the bar. '
          'Begin in the middle, go down, then up as far as the lips are ready for today.', notes=notes)


# 2. Lip slurs
def lip_slurs():
    parts = []
    def per_series(name, body):
        p = P(name, 4, 4, 72)
        for s, (v, cap) in enumerate(SERIES):
            p.w(cap); body(p, s, v); p.bar()
        parts.append(p)
    per_series('Two notes', lambda p, s, v: p.run(series(s, [2, 3, 2]), 1, fing=v).r(1))
    per_series('Three notes', lambda p, s, v: p.run(series(s, [2, 3, 4, 3]), Fr(1, 2), fing=v).n(series(s, [2])[0], 1, fing=v).r(1))
    per_series('Four notes', lambda p, s, v: p.run(series(s, [2, 3, 4, 5, 4, 3]), Fr(1, 3), fing=v).n(series(s, [2])[0], 1, fing=v).r(1))
    per_series('Five notes', lambda p, s, v: p.run(series(s, [2, 3, 4, 5, 6, 5, 4, 3, 2]), Fr(1, 3), fing=v).r(1))
    per_series('Six notes, up to the 8th partial', lambda p, s, v: p.run(series(s, [2, 3, 4, 5, 6, 8, 6, 5, 4, 3, 2]), Fr(1, 4), last='bar', fing=v))
    per_series('Up to the top: the 16th partial', lambda p, s, v: p.run(series(s, [2, 3, 4, 5, 6, 8, 10, 12, 16, 12, 10, 8, 6, 5, 4, 3, 2]), Fr(1, 4), last='bar', fing=v))
    def trills(p, s, v):
        a, b, c, d = series(s, [4, 5, 6, 8])
        p.run([a, b] * 4 + [c, b] * 4, Fr(1, 4), fing=v)
        p.run([c, d] * 4, Fr(1, 4), fing=v).n(c, 2, fing=v)
    per_series('Lip trills', trills)
    entry(20, 'Lip slurs', parts, 72,
          'The valves stay down for the whole bar; only the lips and the air change the note. Every note in a bar is written with the valves of its series, '
          'even where the chart would finger it another way. Keep the air moving and the sound the same size from the bottom note to the top.')


# 3. Chromatic ladders
def ladders():
    parts = []
    def ladder(p, a, b, last_q=True):
        p.run(plain_range(a, b, UP), Fr(1, 2))
        p.run(plain_range(b - 1, a, DOWN), Fr(1, 2), last='bar')
    rungs = [(52, 59), (55, 62), (60, 67), (65, 72), (70, 77), (75, 82), (82, 89), (87, 94)]
    for a, b in rungs:
        p = P('%s to %s' % (chrom(a, PLAIN).name, chrom(b, PLAIN).name), 4, 4, 100)
        ladder(p, a, b); parts.append(p)
    p = P('All of them, low to high', 4, 4, 100)
    for a, b in rungs:
        p.w('%s to %s' % (chrom(a, PLAIN).name, chrom(b, PLAIN).name)); ladder(p, a, b)
    parts.append(p)
    p = P('The whole horn: E3 to B♭6 and back', 4, 4, 100)
    p.w('Up to double high B♭6').leg(plain_range(52, 94, UP))
    p.w('And down to E3').run(plain_range(93, 52, DOWN), Fr(1, 2), last='bar')
    parts.append(p)
    entry(30, 'Chromatic ladders', parts, 100,
          'Every half step, one rung of the ladder at a time, from the bottom of the horn to double high B♭. The valves change on every note, so keep the fingers '
          'down firmly and the air steady between them.')


# 4. Valve crossings
def crossings():
    parts = []
    p = P('The hardest changes', 4, 4, 92)
    for a, b, cap in [(58, 59, '0 and 1-2-3: all three together'), (63, 64, '1 and 2: one finger lifts as the other presses'),
                      (68, 69, '1 and 2 again, higher'), (60, 61, '1-3 and 2-3: valve 1 swaps for valve 2'), (66, 67, '2-3 and 1-2: valve 3 swaps for valve 1'),
                      (59, 60, '1-2-3 and 1-3'), (61, 62, '2-3 and 1-2'), (64, 65, '2 and open'), (67, 68, '1-2 and 1')]:
        x, y = chrom(a), chrom(b)
        p.w(cap).run([x, y, x, y, x, y], Fr(1, 2)).n(x, 1)
    parts.append(p)
    def trills(name, lo, hi, step):
        p = P(name, 4, 4, 92)
        for m in range(lo, hi + 1):
            if m + step > HI: break
            x, y = chrom(m), chrom(m + step)
            p.run([x, y, x, y, x, y], Fr(1, 2)).n(x, 1)
        parts.append(p)
    trills('Every half step, E3 to B♭5', 52, 81, 1)
    trills('Every half step, B♭5 to double high B♭6', 82, 93, 1)
    trills('Every whole step, E3 to B♭5', 52, 80, 2)
    entry(40, 'Valve crossings and finger trills', parts, 92,
          'Clean changes between fingerings: the valve goes all the way down and all the way up, on time, with the air going through the change.')


# 5. Octaves
def octaves():
    parts = []
    for name, rng in [('Up: E3 and E4, to B♭5 and B♭6', range(52, 83)), ('Down: B♭5 and B♭6, to E3 and E4', range(82, 51, -1))]:
        p = P(name, 4, 4, 80)
        for m in rng:
            p.n(chrom(m), 1).n(chrom(m + 12), 1).n(chrom(m), 2)
        parts.append(p)
    entry(50, 'Octaves', parts, 80, 'Each note, the octave above, and back. Slur them, then tongue them. Let the air do the jump and keep the mouthpiece still on the lips.')


# 6. Widening intervals
def intervals():
    parts = []
    for c in (65, 70, 77, 82):
        p = P('Around %s' % chrom(c).name, 4, 4, 80)
        for i in range(1, 13):
            p.n(chrom(c), 1).n(chrom(c + i), 1).n(chrom(c), 1).n(chrom(c - i), 1)
        p.n(chrom(c), 4)
        parts.append(p)
    entry(60, 'Widening intervals', parts, 80,
          'From one note, out a half step above and below, then a whole step, and on to the octave. The middle note should sound the same every time you come back to it.')


# 7. Tonguing
def tonguing():
    parts = []
    bf = field((6, -1), SCALES['major'])
    scale = [n for n in bf if 58 <= n.midi <= 82]
    b4 = parse('B♭4')
    p = P('Single tongue on B♭4', 4, 4, 96)
    p.run([b4] * 4, 1).run([b4] * 8, Fr(1, 2)).run([b4] * 12, Fr(1, 3)).run([b4] * 16, Fr(1, 4)).n(b4, 4)
    parts.append(p)
    p = P('Single tongue, up and down the B♭ scale', 4, 4, 96)
    for x in updown(scale):
        p.run([x] * 4, Fr(1, 4)).run([x] * 2, Fr(1, 2)).n(x, 1).r(1)
    parts.append(p)
    def tk(n, pat):
        return [pat[i % len(pat)] for i in range(n)]
    p = P('Double tongue on B♭4', 4, 4, 96)
    for cnt, d in ((8, Fr(1, 2)), (12, Fr(1, 3)), (16, Fr(1, 4)), (16, Fr(1, 4))):
        for s in tk(cnt, ['T', 'K']): p.n(b4, d, lyric=s)
    p.n(b4, 4)
    parts.append(p)
    p = P('Double tongue, up and down the B♭ scale', 4, 4, 96)
    for x in updown(scale):
        for s in tk(8, ['T', 'K']): p.n(x, Fr(1, 4), lyric=s)
        p.n(x, 1, lyric='T').r(1)
    parts.append(p)
    p = P('Triple tongue on B♭4', 4, 4, 96)
    for s in tk(24, ['T', 'T', 'K']): p.n(b4, Fr(1, 3), lyric=s)
    for s in tk(24, ['T', 'K', 'T']): p.n(b4, Fr(1, 3), lyric=s)
    p.n(b4, 4)
    parts.append(p)
    p = P('Triple tongue, up and down the B♭ scale', 4, 4, 96)
    for x in updown(scale):
        for s in tk(6, ['T', 'T', 'K']): p.n(x, Fr(1, 3), lyric=s)
        p.n(x, 1, lyric='T').r(1)
    parts.append(p)
    entry(70, 'Tonguing', parts, 96,
          'Short, even notes on a steady stream of air. The letters under the notes are the syllables: T is the tip of the tongue, K the back of it. '
          'Start slowly and keep T and K sounding the same.')


# 8. The trumpet's C scale: B♭ major, low to double high
def bflat_scale():
    root = (6, -1); f = field(root, SCALES['major'])
    def between(a, b):
        return [n for n in f if a <= n.midi <= b] if a <= b else [n for n in f if b <= n.midi <= a][::-1]
    parts = []
    for name, a, b in [('Low octave: B♭3 to B♭4', 58, 70), ('Middle octave: B♭4 to B♭5', 70, 82), ('High octave: B♭5 to double high B♭6', 82, 94)]:
        p = P(name, 4, 4, 80)
        p.run(updown(between(a, b)), 1, last='bar')
        parts.append(p)
    p = P('Low B♭3 to double high B♭6, up and down', 4, 4, 80)
    p.w('Up three octaves').leg(between(58, 94))
    p.w('And down').run(between(93, 58), Fr(1, 2), last='bar')
    parts.append(p)
    p = P('Every note on the horn: F3 to B♭6', 4, 4, 80)
    p.w('From B♭3 up to double high B♭6').leg(between(58, 94))
    p.w('Down to F3, the lowest note of the scale').leg(between(93, 53))
    p.w('And back up to B♭3').run(between(55, 58), Fr(1, 2), last='bar')
    parts.append(p)
    p = P('Slow, a half note each: B♭3 to B♭6 and back', 4, 4, 80)
    for i, x in enumerate(updown(between(58, 94))):
        p.n(x, 2)
        if i % 4 == 3: p.r(2)
    p.bar()
    parts.append(p)
    entry(100, 'B♭ major, low B♭ to double high B♭', parts, 80,
          'The trumpet’s own scale, open low B♭ to double high B♭, every note: one octave at a time, then all three in one breath each way, then the whole horn '
          'from double high B♭ down to the bottom F, and last, slowly, a half note to every note. Rest a moment at the top of each run.')


# 9. Scales in all 12 keys
SCALE_ENTRIES = [
    (110, 'major', 'Major scales', 'major', 'The major scale in every key.'),
    (120, 'natural minor', 'Natural minor scales', 'minor', 'The natural minor scale (Aeolian) in every key.'),
    (130, 'harmonic minor', 'Harmonic minor scales', 'harmonic minor', 'Harmonic minor: natural minor with the 7th raised, so the scale leans hard into the tonic. The step and a half between the 6th and 7th is its sound.'),
    (140, 'melodic minor', 'Melodic minor scales', 'melodic minor', 'Melodic minor as jazz players use it, the same up and down: natural minor with the 6th and 7th raised.'),
    (150, 'dorian', 'Dorian scales', 'dorian', 'Dorian: minor with a raised 6th. The minor 7th chord’s scale.'),
    (160, 'phrygian', 'Phrygian scales', 'phrygian', 'Phrygian: minor with a lowered 2nd, the dark Spanish sound.'),
    (170, 'lydian', 'Lydian scales', 'lydian', 'Lydian: major with a raised 4th.'),
    (180, 'mixolydian', 'Mixolydian scales', 'mixolydian', 'Mixolydian: major with a lowered 7th. The dominant 7th chord’s scale.'),
    (190, 'locrian', 'Locrian scales', 'locrian', 'Locrian: the scale of the half-diminished chord, with a lowered 2nd and 5th.'),
    (200, 'major pentatonic', 'Major pentatonic scales', 'major pentatonic', 'Five notes of the major scale, without the 4th and 7th.'),
    (210, 'minor pentatonic', 'Minor pentatonic scales', 'minor pentatonic', 'Five notes of the minor scale, without the 2nd and 6th.'),
    (220, 'blues', 'Blues scales', 'blues', 'Minor pentatonic with the lowered 5th, the blue note, added.'),
    (230, 'major blues', 'Major blues scales', 'major blues', 'Major pentatonic with the lowered 3rd added.'),
    (240, 'bebop dominant', 'Bebop dominant scales', 'bebop dominant', 'Mixolydian with the major 7th added as a passing note, so the chord tones fall on the beats.'),
    (250, 'lydian dominant', 'Lydian dominant scales', 'lydian dominant', 'Mixolydian with a raised 4th: the scale of a 7♯11 chord, the 4th mode of melodic minor.'),
    (260, 'altered', 'Altered scales', 'altered', 'Every tension a dominant 7th can take: ♭9, ♯9, ♯11 and ♭13. The 7th mode of melodic minor.'),
    (270, 'phrygian dominant', 'Phrygian dominant scales', 'phrygian dominant', 'The 5th mode of harmonic minor: the V7♭9 chord of a minor key, and the sound of flamenco.'),
    (280, 'whole tone', 'Whole-tone scales', 'whole tone', 'Six notes, each a whole step apart. There are only two different ones; every key here starts on its own note.'),
    (290, 'half-whole', 'Diminished scales, half-whole', 'half-whole', 'Half step, whole step, all the way up: the scale of a 7♭9 chord.'),
    (300, 'whole-half', 'Diminished scales, whole-half', 'whole-half', 'Whole step, half step, all the way up: the scale of a diminished 7th chord.'),
]
LABEL = {'major': 'major', 'natural minor': 'minor', 'harmonic minor': 'harmonic minor', 'melodic minor': 'melodic minor', 'dorian': 'Dorian',
         'phrygian': 'Phrygian', 'lydian': 'Lydian', 'mixolydian': 'Mixolydian', 'locrian': 'Locrian', 'major pentatonic': 'major pentatonic',
         'minor pentatonic': 'minor pentatonic', 'blues': 'blues', 'major blues': 'major blues', 'bebop dominant': 'bebop dominant',
         'lydian dominant': 'Lydian dominant', 'altered': 'altered', 'phrygian dominant': 'Phrygian dominant', 'whole tone': 'whole tone',
         'half-whole': 'half-whole diminished', 'whole-half': 'whole-half diminished'}


SYMMETRIC = {'whole tone', 'half-whole', 'whole-half', 'altered'}
ODD = {(2, 1): (3, 0), (6, 1): (0, 0), (3, -1): (2, 0), (0, -1): (6, 0)}     # E♯ F, B♯ C, F♭ E, C♭ B


def plainer(n):
    if (n.L, n.a) in ODD:
        L, a = ODD[(n.L, n.a)]
        return spell(n.midi, L)
    return n


def scale_part(kind, k, tempo=96):
    tones = SCALES[kind]
    root = best_root(k, tones)
    f = field(root, tones)
    if kind in SYMMETRIC:
        f = [f_ if f_.midi % 12 == (NAT[root[0]] + root[1]) % 12 else plainer(f_) for f_ in f]
    t0 = lowest(root)
    name = rname(root) + ' ' + LABEL[kind]
    if kind == 'whole tone':
        name = 'Whole tone from ' + rname(root)
    p = P(name, 4, 4, tempo, fifths=key_fifths(root, kind))
    two = [n for n in f if t0 <= n.midi <= t0 + 24]
    p.w('Two octaves').run(updown(two), Fr(1, 2), last='bar')
    rng = [n for n in f if LO <= n.midi <= HI]
    top, bot = rng[-1], rng[0]
    up = [n for n in rng if n.midi >= t0]
    p.w('The whole horn: up to %s' % top.name).leg(up)
    down = [n for n in rng if n.midi < top.midi][::-1]
    if down and down[-1].midi < t0:
        p.w('Down to %s' % bot.name).leg(down)
        back = [n for n in rng if bot.midi < n.midi <= t0]
        p.w('And back up to %s' % back[-1].name).run(back, Fr(1, 2), last='bar')
    else:
        p.w('And down').run(down, Fr(1, 2), last='bar')
    return p


def scales():
    for order, kind, title, _, lead in SCALE_ENTRIES:
        parts = [scale_part(kind, k) for k in range(12)]
        entry(order, title, parts, 96, lead + ' Each key goes up and down two octaves from its lowest tonic, then over the whole horn: up to the highest note of the '
              'scale at or below double high B♭, down to the lowest, and back to the tonic.')


# =====================================================================================================
# Arpeggio Mastery: the harmonic and melodic minor work, as it was, in every key
AM_KEYS = ['B♭', 'B', 'C', 'C♯', 'D', 'E♭', 'E', 'F', 'F♯', 'G', 'G♯', 'A']


def am_bar(p, b, words=None, fing_check=True):
    if words:
        for w in words: p.w(w)
    t = Fr(b['x0']).limit_denominator(48); end = t + Fr(b['b']).limit_denominator(48)
    for c in sorted(b['c'], key=lambda c: c[0]):
        at = Fr(c[0]).limit_denominator(48)
        if at > t: p.r(at - t); t = at
        d = Fr(c[1]).limit_denominator(48)
        if len(c) > 3:
            nt = parse(c[3]); assert nt.midi == c[2], (c, nt.midi)
            o = {}
            if c[4] != chart(c[2]): o['fing'] = c[4]
            if len(c) > 6 and c[6] == 'fermata': o['fermata'] = True
            p.n(nt, d, **o)
        else:
            p.r(d)
        t += d
    if end > t: p.r(end - t)


def roman_of(sc, name):
    for row in AM['kx'][sc]['_tri'] + AM['kx'][sc]['_chords']:
        if row[1] == name: return row[0]
    return None


def chord_caption(sc, b):
    ch = [c[1] for c in b.get('ch', [])]
    out = []
    for c in ch:
        r = roman_of(sc, c)
        out.append('%s · %s' % (r, c) if r else c)
    return ', then '.join(out)


AM_SECTIONS = {
    'patterns': [('sc-2', 'In 3rds'), ('sc-3', 'Groups of four'), ('sc-4', 'Groups of three'), ('sc-6', None)],
    'arpeggios': [('ar-1', 'Triads on every note of the scale'), ('ar-2', 'Sevenths, up from the root'), ('ar-3', 'Sevenths, down from the 7th'),
                  ('ar-4', 'One chord up, the next one down')],
    'cadence': [('cad-1', 'Guide tones'), ('cad-2', 'ii up, V down, i up'), ('cad-3', 'Two beats each')],
    'speed': [('fast-1', 'Four notes and stop'), ('fast-2', 'Eight notes in two beats'), ('fast-3', 'Seventh chords in sixteenths'),
              ('fast-4', 'Long–short'), ('fast-5', 'Short–long'), ('fast-6', 'Approach notes'), ('fast-7', 'Three licks')],
}


def am_part(scale, key, what):
    sc = '%s|%s' % (key, scale)
    name = key + (' harmonic minor' if scale == 'harmonic' else ' melodic minor')
    p = P(name, 4, 4, 96)
    for ex, title in AM_SECTIONS[what]:
        e = AM['kx'][sc][ex]
        if ex == 'sc-6':
            title = 'Natural minor, to hear the 7th' if scale == 'harmonic' else 'Classical melodic: raised going up, lowered coming down'
        last = None
        for i, b in enumerate(e['bars']):
            words = []
            if i == 0: words.append(title)
            cap = chord_caption(sc, b)
            if what in ('arpeggios', 'cadence') or ex in ('fast-3', 'fast-6', 'fast-7'):
                if cap and cap != last: words.append(cap)
            if ex == 'cad-1' and i == 3: words.append('The lower line')
            if ex == 'fast-7':
                for lk in ('Lick 1', 'Lick 2', 'Lick 3'):
                    if lk in b.get('cap', ''): words.append(lk)
            last = cap
            if not b['c'] and i == len(e['bars']) - 1:
                prev = [c for c in e['bars'][i - 1]['c'] if len(c) > 3][-1]
                b = dict(b, c=[[b['x0'], 4.0, prev[2], prev[3], prev[4]]])
            am_bar(p, b, words)
    return p


def am_entries():
    for scale, base, label in (('harmonic', 410, 'harmonic minor'), ('melodic', 420, 'melodic minor')):
        lead_scale = {'harmonic': 'Harmonic minor', 'melodic': 'Melodic minor'}[scale]
        entry(base, '%s patterns' % lead_scale, [am_part(scale, k, 'patterns') for k in AM_KEYS], 96,
              'From Arpeggio Mastery: the %s scale in 3rds, in groups of four and of three, and %s. Each key sits where it fits between E3 and F5.' %
              (label, 'the natural minor beside it' if scale == 'harmonic' else 'the classical way, raised going up and lowered coming down'))
    for scale, base in (('harmonic', 540), ('melodic', 550)):
        label = scale + ' minor'
        entry(base, 'Arpeggios in %s' % label, [am_part(scale, k, 'arpeggios') for k in AM_KEYS], 96,
              'From Arpeggio Mastery: the chord on every note of %s, as triads and as sevenths, up and down. Say the chord name before you play it.' % label)
    for scale, base in (('harmonic', 610), ('melodic', 620)):
        label = scale + ' minor'
        entry(base, 'ii–V–i in %s' % label, [am_part(scale, k, 'cadence') for k in AM_KEYS], 96,
              'From Arpeggio Mastery: the ii–V–i of %s. First the two guide-tone lines, the 3rds and 7ths that move by step from chord to chord; then the arpeggios.' % label)
    for scale, base in (('harmonic', 710), ('melodic', 720)):
        label = scale + ' minor'
        entry(base, 'Speed studies in %s' % label, [am_part(scale, k, 'speed') for k in AM_KEYS], 80,
              'From Arpeggio Mastery: short bursts in %s, as fast as they stay clean, then dotted rhythms, approach notes and three licks.' % label)


# =====================================================================================================
# The same work in major, built the same way
def roman(d, quality, seventh):
    num = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII'][d]
    minorish = quality in ('m', '°', 'm7', 'ø7', '°7', 'm(maj7)')
    num = num.lower() if minorish else num
    suf = {'': '', 'm': '', '°': '°', '+': '+', 'maj7': 'maj7', '7': '7', 'm7': '7', 'ø7': 'ø7', '°7': '°7', 'm(maj7)': '(maj7)', '+maj7': '+maj7'}[quality]
    return num + suf


def quality(ns):
    r = ns[0].midi; iv = tuple((n.midi - r) % 12 for n in ns[1:])
    return {(4, 7): '', (3, 7): 'm', (3, 6): '°', (4, 8): '+', (4, 7, 11): 'maj7', (4, 7, 10): '7', (3, 7, 10): 'm7', (3, 6, 10): 'ø7',
            (3, 6, 9): '°7', (3, 7, 11): 'm(maj7)', (4, 8, 11): '+maj7'}[iv]


class Key:
    """A heptatonic key with its tonic placed where an exercise spanning [below, above] scale steps fits on the horn."""

    def __init__(self, k, kind='major', below=-1, above=9, top=77):
        self.root = best_root(k, SCALES[kind]); self.kind = kind
        self.f = field(self.root, SCALES[kind], lo=LO - 24, hi=HI + 24)
        pc = (NAT[self.root[0]] + self.root[1]) % 12
        cands = [i for i, n in enumerate(self.f) if n.midi % 12 == pc]
        self.top = top
        self.ti = None
        for t in (77, 79, 82):
            for i in cands:
                if 0 <= i + below and i + above < len(self.f) and self.f[i + below].midi >= LO and self.f[i + above].midi <= t:
                    self.ti = i; self.top = max(top, t); break
            if self.ti is not None: break
        assert self.ti is not None

    def s(self, i):
        return self.f[self.ti + i]

    def chord(self, d, seventh=False, octave_fit=True):
        idx = [d, d + 2, d + 4] + ([d + 6] if seventh else [])
        ns = [self.s(i) for i in idx]
        if octave_fit:
            topn = self.s(d + 7) if not seventh else ns[-1]
            if topn.midi > self.top and ns[0].midi - 12 >= LO:
                idx = [i - 7 for i in idx]; ns = [self.s(i) for i in idx]
        return idx, ns

    def name(self, d, seventh=False):
        _, ns = self.chord(d, seventh, octave_fit=False)
        q = quality(ns)
        return roman(d, q, seventh), ns[0].pname + q

    @property
    def title(self):
        return rname(self.root) + ' major'


def major_patterns(k):
    K = Key(k, below=-2, above=9)
    p = P(K.title, 4, 4, 96, fifths=key_fifths(K.root, 'major'))
    S = K.s
    p.w('In 3rds')
    p.run([S(x) for i in range(7) for x in (i, i + 2)] + [S(7)], Fr(1, 2), last='bar')
    p.run([S(x) for i in range(7, 0, -1) for x in (i, i - 2)] + [S(0)], Fr(1, 2), last='bar')
    p.w('In 4ths')
    p.run([S(x) for i in range(7) for x in (i, i + 3)] + [S(7)], Fr(1, 2), last='bar')
    p.run([S(x) for i in range(7, 0, -1) for x in (i, i - 3)] + [S(0)], Fr(1, 2), last='bar')
    p.w('Groups of four')
    p.run([S(x) for g in range(6) for x in range(g, g + 4)], Fr(1, 2))
    p.run([S(x) for g in range(7, 1, -1) for x in range(g, g - 4, -1)], Fr(1, 2))
    p.n(S(0), 4)
    p.w('Groups of three')
    p.run([S(x) for g in range(7) for x in range(g, g + 3)] + [S(7)], Fr(1, 3), last='bar')
    p.run([S(x) for g in range(7, 0, -1) for x in range(g, g - 3, -1)] + [S(0)], Fr(1, 3), last='bar')
    return p


def major_arpeggios(k):
    K = Key(k, below=-1, above=7)
    p = P(K.title, 4, 4, 96, fifths=key_fifths(K.root, 'major'))
    def cap(d, sev):
        r, n = K.name(d, sev); return '%s · %s' % (r, n)
    p.w('Triads on every note of the scale')
    for d in range(7):
        idx, ns = K.chord(d)
        top = K.s(idx[0] + 7)
        p.w(cap(d, False)).run(ns + [top] + ns[::-1][:-1], Fr(1, 2)).n(ns[0], 1)
    idx, ns = K.chord(0); p.w(cap(0, False)).run(ns + [K.s(idx[0] + 7)], Fr(1, 2), last='bar')
    p.w('Sevenths, up from the root')
    for d in range(7):
        idx, ns = K.chord(d, True)
        p.w(cap(d, True)).run(ns + ns[::-1][1:-1], Fr(1, 2)).n(ns[0], 1)
    idx, ns = K.chord(0, True); p.w(cap(0, True)).run(ns + [K.s(idx[0] + 7)], Fr(1, 2), last='bar')
    p.w('Sevenths, down from the 7th')
    for d in range(7):
        idx, ns = K.chord(d, True)
        p.w(cap(d, True)).run(ns[::-1] + ns[1:-1], Fr(1, 2)).n(ns[-1], 1)
    idx, ns = K.chord(0, True); p.w(cap(0, True)).run([K.s(idx[0] + 7)] + ns[::-1], Fr(1, 2), last='bar')
    p.w('One chord up, the next one down')
    for d in (0, 2, 4, 6):
        i1, a = K.chord(d, True); i2, b = K.chord((d + 1) % 7, True)
        p.w('%s up, %s down' % (K.name(d, True)[1], K.name((d + 1) % 7, True)[1])).run(a + b[::-1], Fr(1, 2))
    p.n(K.s(0), 4)
    return p


def major_cadence(k):
    K = Key(k, below=-1, above=8)
    p = P(K.title, 4, 4, 96, fifths=key_fifths(K.root, 'major'))
    S = K.s
    ii, V, I = K.name(1, True), K.name(4, True), K.name(0, True)
    c = lambda x: '%s · %s' % x
    p.w('Guide tones').w(c(ii)).n(S(7), 4).w(c(V)).n(S(6), 4).w(c(I)).n(S(7), 4)
    p.w('The lower line').w(c(ii)).n(S(3), 4).w(c(V)).n(S(3), 4).w(c(I)).n(S(2), 4)
    p.w('ii up, V down, I up').w(c(ii)).run([S(1), S(3), S(5), S(7)], 1)
    p.w(c(V)).run([S(6), S(4), S(3), S(1)], 1)
    p.w(c(I)).run([S(0), S(2), S(4), S(6)], 1)
    p.n(S(7), 4)
    p.w('Two beats each').w('%s, then %s' % (c(ii), c(V))).run([S(1), S(3), S(5), S(7), S(6), S(4), S(3), S(1)], Fr(1, 2))
    p.w(c(I)).run([S(2), S(4), S(6), S(8)], Fr(1, 2)).n(S(7), 2)
    return p


def major_speed(k):
    K = Key(k, below=-1, above=8)
    p = P(K.title, 4, 4, 80, fifths=key_fifths(K.root, 'major'))
    S = K.s
    p.w('Four notes and stop')
    for a, b in ((0, 4), (4, 0), (2, 6), (6, 2), (4, 8), (8, 4)):
        st = 1 if b > a else -1
        p.run([S(x) for x in range(a, b + st, st)], Fr(1, 4), last='bar')
    p.w('Eight notes in two beats')
    for seq in (list(range(-1, 8)), list(range(8, -1, -1)), list(range(0, 5)) + list(range(3, -1, -1)), list(range(4, 9)) + list(range(7, 3, -1))):
        p.run([S(x) for x in seq], Fr(1, 4), last='bar')
    p.w('Seventh chords in sixteenths')
    for d in list(range(7)) + [0]:
        idx, ns = K.chord(d, True)
        r, nm = K.name(d, True)
        p.w('%s · %s' % (r, nm)).run(ns + [K.s(idx[0] + 7)], Fr(1, 4), last='bar')
    p.w('Long–short')
    for i, x in enumerate(range(0, 8)): p.n(S(x), Fr(3, 4) if i % 2 == 0 else Fr(1, 4))
    for i, x in enumerate(range(6, 0, -1)): p.n(S(x), Fr(3, 4) if i % 2 == 0 else Fr(1, 4))
    p.n(S(0), 1)
    p.w('Short–long')
    for i, x in enumerate(range(0, 8)): p.n(S(x), Fr(1, 4) if i % 2 == 0 else Fr(3, 4))
    for i, x in enumerate(range(6, 0, -1)): p.n(S(x), Fr(1, 4) if i % 2 == 0 else Fr(3, 4))
    p.n(S(0), 1)
    def enclose(idx):
        out = []
        for ti in idx:
            t = S(ti)
            below = spell(t.midi - 1, (t.L - 1) % 7)
            if abs(below.a) > 1: below = chrom(t.midi - 1, UP)
            out += [S(ti + 1), below, t]
        return out
    I = K.name(0, True); V = K.name(4, True)
    p.w('Approach notes').w('%s · %s' % I).run(enclose([0, 2, 4, 6]), Fr(1, 3))
    vt = [-3, -1, 1, 3] if S(-3).midi - 1 >= LO else [4, 6, 8, 10]
    p.w('%s · %s' % V).run(enclose(vt), Fr(1, 3))
    p.w('%s · %s' % I).run(enclose([6, 4, 2, 0]), Fr(1, 3))
    p.n(S(0), 4)
    p.w('Three licks').w('Lick 1 · %s' % I[1]).run([S(x) for x in (0, 2, 4, 6, 7, 6, 5, 4)], Fr(1, 2))
    p.run([S(x) for x in (3, 2, 1, -1)], Fr(1, 2)).n(S(0), 2)
    p.w('Lick 2 · %s to %s' % (V[1], I[1])).run([S(x) for x in (-1, 1, 3, 5, 4, 3, 2, 1)], Fr(1, 2)).n(S(0), 4)
    p.w('Lick 3 · from the 3rd: %s' % I[1]).run([S(x) for x in (2, 4, 6, 8)], Fr(1, 2)).n(S(7), 2)
    return p


def major_entries():
    entry(400, 'Major scale patterns', [major_patterns(k) for k in range(12)], 96,
          'The major scale in 3rds, in 4ths, in groups of four and in groups of three, in every key, placed where it fits between E3 and F5.')
    entry(530, 'Arpeggios in a major key', [major_arpeggios(k) for k in range(12)], 96,
          'The chord on every note of the major scale, as triads and as sevenths, up and down, the way Arpeggio Mastery does it in minor.')
    entry(600, 'ii–V–I in major', [major_cadence(k) for k in range(12)], 96,
          'The ii–V–I of every major key: the two guide-tone lines first, the 7ths and 3rds that move by step, then the arpeggios.')
    entry(700, 'Speed studies in major', [major_speed(k) for k in range(12)], 80,
          'Short bursts in major, as fast as they stay clean, then dotted rhythms, approach notes and three licks.')


# =====================================================================================================
# Arpeggios on every root
TRIADS = ['major', 'minor', 'diminished', 'augmented']
SEVENTHS = ['maj7', '7', 'm7', 'm7b5', 'dim7', 'mmaj7', 'augmaj7', '7sus4']
NINTHS = ['maj9', '9', 'm9', '7b9', '7#9', '9sus4', '69']
QNAME = {'major': 'major', 'minor': 'minor', 'diminished': 'diminished', 'augmented': 'augmented'}


def root_part(k, kinds, shape, tempo=96):
    roots = {q: best_root(k, CHORDS[q][1]) for q in kinds}
    names = sorted({rname(r) for r in roots.values()}, key=lambda x: (len(x), x))
    pname = ' / '.join(sorted(names, key=lambda x: ('♭' not in x, x)))
    p = P(pname, 4, 4, tempo)
    for q in kinds:
        root = roots[q]; suf, tones = CHORDS[q]
        f = field(root, tones, lo=LO, hi=HI)
        t0 = lowest(root)
        label = rname(root) + (' ' + QNAME[q] if q in QNAME else suf)
        if shape is ninth_shape: shape(p, f, t0, label, root, tones)
        else: shape(p, f, t0, label)
    return p


def two_oct_shape(p, f, t0, label):
    ns = [n for n in f if t0 <= n.midi <= t0 + 24]
    p.w(label).run(updown(ns), Fr(1, 2), last='bar')


def ninth_shape(p, f, t0, label, root=None, tones=None):
    ch = tones_from(root, tones, t0)
    p.w(label).run(updown(ch), Fr(1, 2), last='bar')
    hi = tones_from(root, tones, t0 + 12)
    if hi[-1].midi <= HI:
        p.w('An octave higher').run(updown(hi), Fr(1, 2), last='bar')


def root_entries():
    entry(500, 'Triad arpeggios', [root_part(k, TRIADS, two_oct_shape) for k in range(12)], 96,
          'Major, minor, diminished and augmented triads on every root, two octaves up from the lowest root on the horn and back.')
    entry(510, 'Seventh-chord arpeggios', [root_part(k, SEVENTHS, two_oct_shape) for k in range(12)], 96,
          'Eight kinds of seventh chord on every root, two octaves up and back: major 7th, dominant 7th, minor 7th, half-diminished, diminished, '
          'minor with a major 7th, augmented with a major 7th, and 7sus4.')
    entry(520, 'Ninth-chord arpeggios', [root_part(k, NINTHS, ninth_shape) for k in range(12)], 96,
          'Seven ninth chords on every root, up to the 9th and back, and again an octave higher where the horn has room.')


# =====================================================================================================
# Hymns, bugle calls, pedal tones and the cool-down
def am_piece(key, name, tempo=None, notes=None, pi=None):
    e = AM['ex'][key]
    m = float(e['m'])
    head = e.get('head', '')
    meter = head.split(' · ')[0].split(',')[0].strip() if 'bg-' in key else None
    if 'bg-' in key:
        b_, bt = meter.split('/'); beats, bt = int(b_), int(bt)
    elif 'hy-' in key:
        beats, bt = (3, 4) if '3/4' in head else (4, 4)
    else:
        beats, bt = int(m), 4
    pick = e['bars'][0]['b'] if e['bars'][0]['lab'] == 'pickup' else None
    p = P(name, beats, bt, tempo, pickup=pick)
    for b in e['bars']:
        am_bar(p, b)
    return p


def fermatas(p, i, notes):
    for mi, b in enumerate(p.measures()):
        ni = 0
        for kind, note, d, o, ts, tst in b['items']:
            if kind != 'n': continue
            for piece in split_value(int(d * 12)):
                if o.get('fermata'): notes['%d:%d:%d' % (i, mi, ni)] = 'fermata'
                ni += 1


def calls():
    order = ['first', 'reveille', 'assembly', 'mess', 'attention', 'colors', 'retreat', 'carryon', 'adjutant', 'officers', 'firstsgt', 'church', 'tattoo', 'taps', 'echotaps']
    names = {'first': 'First Call', 'reveille': 'Reveille', 'assembly': 'Assembly', 'mess': 'Mess Call', 'attention': 'Attention', 'colors': 'To the Colors',
             'retreat': 'Retreat', 'carryon': 'Carry On', 'adjutant': 'Adjutant’s Call', 'officers': 'Officers’ Call', 'firstsgt': 'First Sergeant’s Call',
             'church': 'Church Call', 'tattoo': 'Tattoo', 'taps': 'Taps', 'echotaps': 'Echo Taps'}
    parts, notes = [], {}
    for i, c in enumerate(order):
        e = AM['ex']['bg-%s@0' % c]
        head = e['head']
        bpm = int(head.split('= ')[1].split(' ')[0])
        if '♩.' in head: bpm = int(round(bpm * 1.5))
        p = am_piece('bg-%s@0' % c, names[c], tempo=bpm)
        parts.append(p)
        fermatas(p, i, notes)
    entry(810, 'Bugle calls', parts, 96,
          'The old calls of the U.S. Army, played on open valves: the notes of the bugle, B♭3, F4, B♭4, D5 and F5. Each call keeps the tempo of the manual.',
          notes=notes, facts=[['Valves', 'All open']])


def hymns():
    parts, notes = [], {}
    for key, name in (('hy-melita', 'Melita (Dykes, 1861)'), ('hy-eventide', 'Eventide (Monk, 1861)'), ('hy-newbritain', 'New Britain (1831)'),
                      ('hy-feste', 'Ein’ feste Burg (Luther, about 1529)')):
        parts.append(am_piece(key, name, tempo=72)); fermatas(parts[-1], len(parts) - 1, notes)
    entry(800, 'Hymns', parts, 72, notes=notes, lead=
          'Four old hymn tunes, the soprano line, for a singing sound: long phrases, full breaths, no gaps between the notes.',
          facts=[['Melita', 'John B. Dykes, 1861'], ['Eventide', 'William H. Monk, 1861'], ['New Britain', 'Virginia Harmony, 1831'], ['Ein’ feste Burg', 'Martin Luther, about 1529']])


def pedals():
    parts = []
    p = P('From each low note to its pedal', 8, 4, 60)
    for s, (v, cap) in enumerate(SERIES):
        a = series(s, [2])[0]; ped = spell(a.midi - 12, a.L)
        p.w(cap.split(',')[0]).n(a, 2, fing=v).n(ped, 4, fing=v).r(2)
    parts.append(p)
    p = P('Pedal long tones: B♭2 down to E2', 8, 4, 60)
    for s, (v, cap) in enumerate(SERIES):
        a = series(s, [2])[0]; ped = spell(a.midi - 12, a.L)
        p.n(ped, 6, fing=v).r(2)
    parts.append(p)
    entry(900, 'Pedal tones', parts, 60,
          'The notes an octave below the bottom of the horn, played with the valves of the note above. Loose lips, a lot of slow air. They relax the lips after high playing.')


def cooldown():
    p = P('Soft and low', 8, 4, 60)
    seq = [65, 58, 64, 57, 62, 55, 58]
    for m in seq:
        p.n(chrom(m, DOWN), 6).r(2)
    notes = {'0:%d:0' % i: 'ghost' for i in range(len(seq))}
    entry(910, 'Cooling down', [p], 60, 'As soft as you can, with a clear center to the sound. Lower and softer at the end. Then put the horn down.', notes=notes)


# =====================================================================================================
def slug(t):
    import re, unicodedata
    t = unicodedata.normalize('NFKD', t.replace('♭', 'b').replace('♯', 's').replace('–', '-')).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')


def write_all():
    os.makedirs(OUT, exist_ok=True)
    old = {f for f in os.listdir(OUT)}
    made = set()
    for e in sorted(ENTRIES, key=lambda e: e['order']):
        fn = '%03d %s.musicxml' % (e['order'], e['title'].replace('/', '-'))
        path = os.path.join(OUT, fn)
        xml = score_xml(e['title'], e['parts'])
        open(path, 'w', encoding='utf-8').write(xml)
        side_path = path + '.vf.json'
        prev = {}
        if os.path.exists(side_path):
            try: prev = json.load(open(side_path, encoding='utf-8'))
            except ValueError: prev = {}
        nbars = len(e['parts'][0].measures())
        details = {'title': e['title'], 'lead': e['lead']}
        keyed = len(e['parts']) == 12 and e['order'] >= 110 and e['order'] < 800
        facts = [['Keys', 'All 12, from B♭ up by half steps']] if keyed else [['Parts', ', '.join(p.name for p in e['parts'])]] if len(e['parts']) > 1 else []
        if e['facts']: facts += e['facts']
        if facts: details['facts'] = facts
        side = {'app': 'Valve Finder', 'version': 2, 'id': 'warmup-' + slug(e['title']), 'title': e['title'], 'category': 'warmup', 'order': e['order'],
                'kind': 'MusicXML', 'addedAt': prev.get('addedAt') or NOW, 'updatedAt': NOW, 'units': {'count': nbars, 'unit': 'Bar'},
                'settings': prev.get('settings') or {'part': 0, 'pitch': 'auto', 'oct': '0', 'tempo': e['tempo'], 'repeats': True, 'join': False, 'alts': False},
                'notes': e['notes'] or None, 'timing': None, 'details': details}
        open(side_path, 'w', encoding='utf-8').write(json.dumps(side, ensure_ascii=False, indent=1) + '\n')
        made |= {fn, fn + '.vf.json'}
    for f in sorted(old - made):
        print('not made this time (left as it is):', f)
    return len(made) // 2


if __name__ == '__main__':
    long_tones(); lip_slurs(); ladders(); crossings(); octaves(); intervals(); tonguing(); bflat_scale(); scales()
    am_entries(); major_entries(); root_entries(); hymns(); calls(); pedals(); cooldown()
    print('wrote', write_all(), 'exercises')
