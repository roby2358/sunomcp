#!/usr/bin/env python3
"""Scan a Suno lyric sheet for meter: syllables, stresses, clashes, rhymes.

Usage:  python3 meter.py lyrics.txt        (or pipe the sheet on stdin)

Stresses come from the CMU Pronouncing Dictionary, downloaded once to
~/.cache/suno-meter/. Legend: "/" stressed, "\" secondary stress (the
second half of "hallway"), "x" unstressed, "+" a weak syllable the beat
promotes (the "is" of "the kettle is"), "?" guessed (not in the dictionary).
One-syllable function words (the, is, I, ...) count as unstressed, other
one-syllable words as stressed; a singer can bend either, so read the flags
as places to check, not as verdicts.
"""
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


def scan_word(word, prons):
    """Return (pattern, alternative syllable counts, phones or None)."""
    key = word.lower().strip("'")
    variants = prons.get(key) or prons.get(key.replace("'", ""))
    if not variants and key.endswith("'s") and prons.get(key[:-2]):
        variants = [prons[key[:-2]][0] + ["Z"]]
    if not variants and key.endswith("in'") and prons.get(key[:-1] + "g"):
        variants = prons[key[:-1] + "g"]
    if not variants:
        return "?" * guess_syllables(key), [], None
    # Singing compresses: take the pronunciation with the fewest syllables.
    phones = min(variants, key=lambda v: sum(p[-1].isdigit() for p in v))
    stresses = [p[-1] for p in phones if p[-1].isdigit()]
    if not stresses:  # vowel-less entries such as "hmm"
        return "/", [], None
    if len(stresses) == 1:
        pattern = "x" if key in WEAK else "/"
    else:
        pattern = "".join({"0": "x", "1": "/", "2": "\\"}[s] for s in stresses)
    counts = sorted({sum(p[-1].isdigit() for p in v) for v in variants})
    alts = [] if key in WEAK else [c for c in counts if c != len(stresses)]
    return pattern, alts, phones


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


def scan_line(line, prons):
    words = re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)*'?", line.replace("’", "'"))
    patterns, flags, variable, last_phones = [], [], [], None
    for w in words:
        for part in w.split("-"):
            pattern, alts, phones = scan_word(part, prons)
            patterns.append((part, pattern))
            if alts:
                variable.append("%s (%s or %d)" % (part, "/".join(map(str, alts)), len(pattern)))
            if phones is None and "?" in pattern:
                flags.append("not in dictionary: " + part)
            last_phones = phones
    flat = "".join(p for _, p in patterns)
    beats = promote(flat)
    shown, pos = [], 0
    for _, p in patterns:
        shown.append("".join("+" if beats[pos + j] == "+" else c for j, c in enumerate(p)))
        pos += len(p)
    owner = [w for w, p in patterns for _ in p]
    for m in re.finditer(r"/{2,}", flat):
        run = list(dict.fromkeys(owner[m.start():m.end()]))
        if len(run) > 1 and m.group() != flat:
            label = "stress pile-up" if len(m.group()) > 2 else "adjacent stresses"
            flags.append("%s: %s" % (label, " ".join(x.upper() for x in run)))
    for m in re.finditer(r"x{4,}", flat):
        run = list(dict.fromkeys(owner[m.start():m.end()]))
        flags.append("%d weak syllables in a row: %s" % (len(m.group()), " ".join(run)))
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
    text = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 else sys.stdin.read()
    prons = load_dict()
    scanned = [(name, [scan_line(l, prons) for l in lines]) for name, lines in parse(text)]
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
