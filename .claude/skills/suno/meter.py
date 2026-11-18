#!/usr/bin/env python3
r"""Scan a Suno lyric sheet for meter: syllables, stresses, clashes, rhymes.

Usage:  python3 meter.py lyrics.txt        (or pipe the sheet on stdin)
        python3 meter.py --meter trochaic4 lyrics.txt

With --meter (trochaic, iambic, dactylic or anapestic, plus an optional
number of beats per line: "trochaic4" or "trochaic tetrameter") each line is
fitted to that beat grid instead of being searched for clashes. One-syllable
words fit anywhere, words with two pronunciations ("every") take the one
that fits, and the only flags are a wrong beat count and a longer word whose
main stress lands off the beat. Without a number, the commonest count is used.

Stresses come from the CMU Pronouncing Dictionary, downloaded once to
~/.cache/suno-meter/. Legend: "/" stressed, "\" secondary stress (the
second half of "hallway"), "x" unstressed, "+" a weak syllable the beat
promotes (the "is" of "the kettle is"), "?" guessed (not in the dictionary).
One-syllable function words (the, is, I, ...) count as unstressed, other
one-syllable words as stressed; a singer can bend either, so read the flags
as places to check, not as verdicts.
"""
import itertools
import os
import re
import sys
import urllib.request

DICT_URL = "https://raw.githubusercontent.com/cmusphinx/cmudict/master/cmudict.dict"
DICT_PATH = os.path.expanduser("~/.cache/suno-meter/cmudict.dict")

WEAK = set("""a an the and or but nor so if as at by for from in into of on onto to up with than that
i me my you your he him his she her it its we us our they them their is am are was were be been
do does did has have had can could will would shall should may might must this these those there
who whom whose which what when where while not no i'm you're he's she's it's we're they're i've
you've we've they've i'll you'll he'll she'll we'll they'll i'd you'd he'd she'd we'd they'd
some any each till until yet oh""".split())

# Beat grids per meter; anapestic lines may open with a two-syllable foot.
GRIDS = {"trochaic": ["/x"], "iambic": ["x/"], "dactylic": ["/xx"], "anapestic": ["xx/", "x/x"]}
FEET = {"di": 2, "tri": 3, "tetra": 4, "penta": 5, "hexa": 6, "hepta": 7, "octa": 8}


def load_dict():
    if not os.path.exists(DICT_PATH):
        os.makedirs(os.path.dirname(DICT_PATH), exist_ok=True)
        sys.stderr.write("Downloading the CMU Pronouncing Dictionary (once)...\n")
        urllib.request.urlretrieve(DICT_URL, DICT_PATH)
    prons = {}
    with open(DICT_PATH, encoding="latin-1") as f:
        for line in f:
            parts = line.split("#")[0].split()
            if len(parts) > 1:
                prons.setdefault(re.sub(r"\(\d+\)$", "", parts[0]), []).append(parts[1:])
    return prons


def guess_syllables(word):
    groups = re.findall(r"[aeiouy]+", word)
    n = len(groups)
    if word.endswith("e") and not word.endswith(("le", "ee")) and n > 1:
        n -= 1
    return max(n, 1)


def word_variants(word, prons):
    """Return ([(pattern, phones or None), ...], fewest syllables first)."""
    key = word.lower().strip("'")
    variants = prons.get(key) or prons.get(key.replace("'", ""))
    if not variants and key.endswith("'s") and prons.get(key[:-2]):
        variants = [prons[key[:-2]][0] + ["Z"]]
    if not variants and key.endswith("in'") and prons.get(key[:-1] + "g"):
        variants = prons[key[:-1] + "g"]
    if not variants:
        return [("?" * guess_syllables(key), None)]
    out, seen = [], set()
    # Singing compresses: the pronunciation with the fewest syllables comes first.
    for phones in sorted(variants, key=lambda v: sum(p[-1].isdigit() for p in v)):
        stresses = [p[-1] for p in phones if p[-1].isdigit()]
        if not stresses:  # vowel-less entries such as "hmm"
            pattern, phones = "/", None
        elif len(stresses) == 1:
            pattern = "x" if key in WEAK else "/"
        else:
            pattern = "".join({"0": "x", "1": "/", "2": "\\"}[s] for s in stresses)
        if pattern not in seen:
            seen.add(pattern)
            out.append((pattern, phones))
    return out


def parse_meter(spec):
    """'trochaic4', 'iambic pentameter', 'anapestic' -> (name, feet or None)."""
    s = spec.lower()
    name = next((m for m in GRIDS if s.startswith(m[:4])), None)
    if not name:
        sys.exit("Unknown meter %r: use trochaic, iambic, dactylic or anapestic, "
                 "with an optional number of beats, as in trochaic4." % spec)
    digits = re.search(r"\d+", s)
    named = next((n for k, n in FEET.items() if k + "meter" in s), None)
    return name, int(digits.group()) if digits else named


def fit(cands, meter, feet):
    """Pick one pronunciation per word and one beat grid: first the right
    number of beats, then the fewest word stresses landing off the beat.
    One-syllable words fit anywhere; only a longer word's main stress on a
    weak position counts against a reading."""
    best = None
    for combo in itertools.product(*[range(min(len(c), 3)) for c in cands]):
        pats = [cands[i][j][0] for i, j in enumerate(combo)]
        n = sum(map(len, pats))
        for g, foot in enumerate(GRIDS[meter]):
            grid = (foot * n)[:n]
            off, pos = [], 0
            for i, p in enumerate(pats):
                if len(p) > 1 and any(c == "/" and grid[pos + k] == "x" for k, c in enumerate(p)):
                    off.append(i)
                pos += len(p)
            cost = (abs(grid.count("/") - feet) if feet else 0, len(off), sum(combo), g)
            if best is None or cost < best[0]:
                best = (cost, combo, grid, off)
    return best[1:]


def rhyme_part(phones):
    """Phones from the last stressed vowel on, and that vowel alone."""
    if not phones:
        return None, None
    idx = [i for i, p in enumerate(phones) if p[-1] in "12"] or \
          [i for i, p in enumerate(phones) if p[-1].isdigit()]
    tail = [re.sub(r"\d", "", p) for p in phones[idx[-1]:]]
    return " ".join(tail), tail[0]


def promote(flat):
    """Mark weak syllables that the beat lifts: the middle of three, a weak
    line ending after a weak syllable, and the first of two weak openers."""
    s = list(flat.replace("\\", "x"))
    if len(s) > 2 and s[0] == s[1] == "x" and s[2] != "x":
        s[0] = "+"
    for i in range(1, len(s)):
        if s[i] == "x" and s[i - 1] == "x" and (i + 1 == len(s) or s[i + 1] == "x"):
            s[i] = "+"
    return "".join(s)


def parse(text):
    """Return [(section name, [line, ...])], skipping notes and empty sections."""
    sections, current = [], None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("*"):
            continue
        tag = re.fullmatch(r"\[(.+)\]", line)
        if tag:
            current = (tag.group(1), [])
            sections.append(current)
        else:
            if current is None:
                current = ("Untitled", [])
                sections.append(current)
            current[1].append(line)
    return [s for s in sections if s[1]]


def scan_line(line, prons, meter=None, feet=None):
    words = re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)*'?", line.replace("’", "'"))
    parts = [part for w in words for part in w.split("-")]
    cands = [word_variants(part, prons) for part in parts]
    grid, off = None, []
    if meter and parts:
        combo, grid, off = fit(cands, meter, feet)
    else:
        combo = [0] * len(parts)
    chosen = [cands[i][j] for i, j in enumerate(combo)]
    patterns = [(part, pattern) for part, (pattern, _) in zip(parts, chosen)]
    flags = ["not in dictionary: " + part for part, (pattern, _) in zip(parts, chosen) if "?" in pattern]
    last_phones = chosen[-1][1] if chosen else None
    flat = "".join(p for _, p in patterns)
    beats = promote(flat)
    shown, pos = [], 0
    for _, p in patterns:
        shown.append("".join("+" if beats[pos + j] == "+" else c for j, c in enumerate(p)))
        pos += len(p)
    if grid is not None:
        if feet and grid.count("/") != feet:
            flags.append("%d beats, expected %d" % (grid.count("/"), feet))
        if off:
            flags.append("stress off the beat: " + " ".join(parts[i].upper() for i in off))
        return {"text": line, "flat": grid, "grouped": " ".join(shown), "flags": flags,
                "rhyme": rhyme_part(last_phones), "beats": grid.count("/")}
    owner = [w for w, p in patterns for _ in p]
    for m in re.finditer(r"/{2,}", flat):
        run = list(dict.fromkeys(owner[m.start():m.end()]))
        if len(run) > 1 and m.group() != flat:
            label = "stress pile-up" if len(m.group()) > 2 else "adjacent stresses"
            flags.append("%s: %s" % (label, " ".join(x.upper() for x in run)))
    for m in re.finditer(r"x{4,}", flat):
        run = list(dict.fromkeys(owner[m.start():m.end()]))
        flags.append("%d weak syllables in a row: %s" % (len(m.group()), " ".join(run)))
    variable = []
    for part, vs, (pattern, _) in zip(parts, cands, chosen):
        alts = sorted({len(p) for p, _ in vs} - {len(pattern)})
        if alts and part.lower().strip("'") not in WEAK:
            variable.append("%s (%s or %d)" % (part, "/".join(map(str, alts)), len(pattern)))
    if variable:
        flags.append("syllable count varies: " + ", ".join(variable))
    return {"text": line, "flat": beats.replace("+", "/"), "grouped": " ".join(shown),
            "flags": flags, "rhyme": rhyme_part(last_phones)}


def rhyme_scheme(lines):
    keys, letters = {}, []
    for ln in lines:
        full, vowel = ln["rhyme"]
        if full is None:
            letters.append("?")
            continue
        if full not in keys:
            slant = next((k for k, v in keys.items() if v[1] == vowel), None)
            letter = chr(ord("A") + len({v[0].upper() for v in keys.values()}))
            keys[full] = (keys[slant][0].lower() if slant else letter, vowel)
        letters.append(keys[full][0])
    return "".join(letters)


def main():
    args, meter, feet = sys.argv[1:], None, None
    if "-h" in args or "--help" in args:
        print(__doc__.strip())
        print("\nOptions:")
        print("  --meter NAME[N]  fit each line to a beat grid, N beats a line (optional)")
        print("                   meters: " + ", ".join(GRIDS))
        print("                   beat names: " + ", ".join("%smeter (%d)" % kv for kv in FEET.items()))
        print("  -h, --help       show this help")
        return
    if "--meter" in args:
        i = args.index("--meter")
        if i + 1 == len(args):
            sys.exit("--meter needs a name, as in --meter trochaic4")
        meter, feet = parse_meter(args[i + 1])
        del args[i:i + 2]
    text = open(args[0], encoding="utf-8").read() if args else sys.stdin.read()
    prons = load_dict()
    sections = parse(text)
    if meter and not feet:
        counts = [scan_line(l, prons, meter)["beats"] for _, lines in sections for l in lines]
        feet = max(set(counts), key=counts.count) if counts else None
    if meter:
        print("Meter: %s, %s beats a line" % (meter, feet))
    scanned = [(name, [scan_line(l, prons, meter, feet) for l in lines]) for name, lines in sections]
    for name, lines in scanned:
        print("\n[%s]   rhyme: %s  (lower case = slant)" % (name, rhyme_scheme(lines)))
        width = max(len(l["grouped"]) for l in lines)
        for l in lines:
            print("  %2d  %-*s  %s" % (len(l["flat"]), width, l["grouped"], l["text"]))
            for flag in l["flags"]:
                print("      %s  ! %s" % (" " * width, flag))

    groups = {}
    for name, lines in scanned:
        base = re.sub(r"^(final|last|pre|post)[- ]", "", re.sub(r"\s*\d+$", "", name.lower()))
        groups.setdefault(base, []).append((name, lines))
    printed = False
    for base, members in groups.items():
        if len(members) < 2:
            continue
        for i in range(max(len(m[1]) for m in members)):
            rows = [(n, ls[i]) for n, ls in members if i < len(ls)]
            if len({r[1]["flat"] for r in rows}) > 1:
                if not printed:
                    print("\nMatching lines that scan differently:")
                    printed = True
                print("  %s, line %d" % (base, i + 1))
                for n, l in rows:
                    print("    %-14s %2d  %-14s %s" % (n, len(l["flat"]), l["flat"], l["text"]))
    if not printed:
        print("\nAll matching lines across repeated sections scan alike.")


if __name__ == "__main__":
    main()
