---
name: suno
description: Working notes for making music with the Suno MCP in this project - lyric formatting, section tags, style prompts, credit costs, and workflow. Use when writing or revising lyrics, generating songs, speech, covers or stems with the mcp__suno__* tools, or when the user says "add that to the suno notes".
---

# Suno notes

Add new findings to the matching section, short and dated. Mark anything unverified.

## Connection

- MCP server `https://api.suno.com/mcp` (OAuth, no API key), registered in local scope for `/work/suno`.
- If tools are missing, run `/mcp` and authenticate `suno`. Under WSL the `localhost` redirect fails to load; paste the callback URL from the address bar to finish.

## Workflow

- Draft lyrics in chat first; generate only when the user asks.
- Always pass `model: "v6-wild"` for songs. Speech has no model choice.
- Each generation call returns two takes: wait on both ids with `audio-wait` and report both links.
- Telling takes apart: the two takes of a pair share a timestamp, so identify them by length (for example "the 6:09 one"). Report each take's duration with its link once it completes; if "the last one" is ambiguous, check which is liked, then go by length.
- Rename with `audio-edit` (title); publish with `audio-settings`.
- Cover a liked take to revise it (2026-11-17): `audio-covers-create` on the liked take's id with the revised style and lyrics keeps its melody and changes the rest. Run a fresh `audio-create` alongside for contrast. This produced the published "Let It Break (female vocals)". Covers do not carry lyrics over, so always pass them.
- A take at exactly 8:00 (480 s) has hit the length ceiling and is probably looping. Seen once, on a cover whose notes said three times that the riff never stops.
- For lyric polish, make four review passes in order: flow, rhyme, meter, then flow again (user's rule, 2026-11-18). Then show the revision and what changed.
- Meter check (2026-11-18): `python3 .claude/skills/suno/meter.py` reads the lyric sheet on stdin (or takes a file path) and prints each line's syllable count, stress pattern and rhyme scheme, flags stress pile-ups and words whose syllable count varies, and lists matching lines of repeated sections (verse 1 against verse 2, chorus against final chorus) that scan differently. Use it for the meter pass and give the review agent its output with the draft: language models see tokens, not syllables, so they scan meter poorly unaided (user's point, 2026-11-18). It guesses stress from a dictionary, so it finds the lines to check and the agent or the ear decides.
  - When the song has a set meter, pass it: `--meter trochaic4` (or iambic, dactylic, anapestic; "trochaic tetrameter" also works; without a number the commonest beat count is used). Each line is then fitted to the beat grid: one-syllable words fit anywhere and words like "every" take the pronunciation that fits, so the only flags are a wrong beat count and a longer word whose main stress lands off the beat. This drops the false alarms of the plain scan ("I don't know", "every").
  - Rhyme lookup (2026-11-18): `python3 .claude/skills/suno/meter.py --rhymes kindness --stress /x` lists full rhymes, then slant rhymes (same vowels and closing sound, closest endings first), commonest words first; `--stress` keeps only words that fit the beat and `--limit N` sets how many show. Pick the rhyme word from the list first and write the line toward it, and give review agents the list for any rhyme they want to change. Single words only (no "mind is" for "kindness"); rare names creep in at the tail of a list.
  - `--md` (2026-11-18) prints either mode as Markdown: a table per section (line, syllables, stress, text, flags) or a table of rhymes per stress pattern. Use it for output handed to a review agent or shown to the user.

## Lyrics

- Section tags in square brackets on their own line: `[Verse 1]`, `[Chorus]`, `[Bridge]`, `[Final Chorus]`.
- Write the chorus out once; a bare `[Chorus]` repeats it. Write it out again only when the words change.
- Structure: intersperse the chorus and instrumentals between verses, putting `[Chorus]` then `[Instrumental]` on consecutive lines. Default shape: verse, chorus, instrumental, ... verse, bridge, chorus, instrumental, final chorus. Variations are fine, but never leave out the `[Chorus]` / `[Instrumental]` breaks.
- Spoken lines: tag `[spoken]`, never `(spoken)`, since parentheses can get sung as backing vocals. Rendering is spotty, but keep using them.
- Production notes: at the top, before the first section tag, each line starting with `*` and wrapped in curly braces: `{* verses low and close, choruses belted }`. Bare `*` lines sometimes got sung (user, 2026-11-18); the braces are the user's fix, untested so far. Suno documents no syntax for this, and third-party guides say a voiced cue belongs in the style instead, so keep repeating the notes' substance in the style prompt.
- Rhymes land heavily: the rhyme word ends the line, carries the final stress, and is a full rhyme where possible. Put the joke on it.
- Slant rhymes count: don't rewrite a good line just to force a full rhyme, and tell review agents the same.
- Lyrics are not poetry: keep them raw, direct, repeated, refrained. Johnny Cash's advice (*American Songwriter*): "write as clearly and plainly as you can," keep the title evident in the song, and convey the feeling in a simple, honest, straightforward way.
- Let the feeling overload the form (Brian Eno, *A Year with Swollen Appendices*): "The distorted guitar sound is the sound of something too loud for the medium supposed to carry it. The blues singer with the cracked voice is the sound of an emotional cry too powerful for the throat that releases it." The excitement is in "events too momentous for the medium assigned to record them." (Quoted from memory.)
- Refrain repetition (user favorite, 2026-11-17, "Let It Break"): build the song on one short refrain phrase and return to it everywhere.
  - Each verse is four rhymed lines, then the refrain three times as call and response with one word changing ("(Let it break) the morning does / the ocean does / the way love does"), then the same closing line every verse ("Take my hand").
  - The chorus ends every line on the refrain's rhyme, with the refrain itself as the last line, followed by a wordless la-la hook.
  - The bridge repeats one opening phrase on all four lines ("Nothing to hold, ...").
  - The final chorus changes only a few words and echoes the refrain between the la-las.
  - Parentheses are used on purpose here, to get the refrain sung as backing vocals. (Not confirmed by ear that they render that way.)
- Flow: matching beat counts within a couplet, no stress pile-ups, no words that fight the meter (for example "productivity", "couture").

## Lyric-writing prompts

- Breathless sublation (user favorite, 2026-11-14): "In a swaying sing-song voice, where one idea flows naturally into the next with no breathing stops, write a song in 4 verses a bridge and a chorus about the sublation of <ideas>. No thinking! Belt it out!" Fill `<ideas>` with the pair to sublate (first use: big bang and singularity, giving "Cancelled and Kept").
- Operatic saptabhangi (user favorite, 2026-11-16): "Run the saptabhangi (the Jain sevenfold predication) on '<flat declaration>', then write it as a dramatic opera in seven verses, one per predication in order: it is; it is not; it is and is not, in turn; it can't be said; it is, and can't be said; it is not, and can't be said; all three at once. Omit the Sanskrit. Interpose a chorus that carries the 'in a way'." Keep verses to four lines so seven fit. First use: "Everything is breaking", giving "Everything Is Breaking", with a prima donna, full choir and orchestral electronica style. More operatic takes blur the words; "clear diction" leans toward clarity.
- Zoom-out (Claude's idea, untested): "With total conviction and a straight face, write a song in 4 verses a bridge and a chorus about <small everyday mishap>. Each verse retells it one scale larger: the home, the city, the planet, the cosmos. The chorus never changes a word, yet means something bigger each time it returns. The bridge is the one moment of doubt. Heavy rhymes, no winking!"

## Style prompts

- Suno appends its own descriptors, which can cut against the request ("warm and harmonious" speech came back "nasal, adenoidal" and "tense and strident"). Check the returned `metadata.style`; use `negative_style` to steer away.
- A trashed song still reads with `audio-retrieve` but returns "Song not found" on `audio-like`.
- No style at all is a valid choice: the user sometimes sends lyrics with no style to see what Suno makes of them.
- User's house styles (with `variety: 0`):
  - Fuzzwave: "the bass line comes in first and stays, hypnotic fuzzwave, psychedelic, gentle soothing vocals, the whole vocal range, jangly guitars, heavy fuzz, blur, shred, blend, roar, raw, vulnerable, dissonant bass"
  - Power rock: "Open with virtuoso guitar and never let up, Explosive power rock, heavy crunchy guitar riffs, pounding drums, aggressive bass, gritty commanding vocals, soaring melodic choruses, screaming guitar leads, relentless rhythmic momentum, dramatic breakdowns, huge cinematic sound"
  - Tango: "tango, electronica, bold, dramatic"
  - Racing pulse (2026-11-17, calm voice over a racing pulse, made for "Let It Break"): "timeless melodic guitar rock, a bold ringing circular arpeggiated guitar riff in A minor opens the song loud and up front, doubled by a second guitar, the riff is the lead hook and never stops, breathless gentle urgency, sultry breathy close-mic vocals sung against the ear, male lead with female harmony, sensuous, slow-burning heat, tender and insistent, barely a breath between lines, propulsive eighth-note bass with a swaying hip-led groove, ticking hi-hat and steady cowbell, restless forward motion at 148 bpm, hypnotic, calm voice over a racing pulse, wordless la-la harmonies, clear natural production, eerie middle break building fast to a frantic spiralling guitar solo that crashes back into the riff, fades out still racing"
    - Negative style: "shouting, growl, heavy metal, aggressive, belting, retro pastiche, vintage lo-fi, laid-back, sleepy, slow ballad, modern pop production, synths, buried guitar, thin guitar"
    - Back it with `*` production notes saying the same things: riff up front and never stopping, lines tumbling into each other, pulse kept through the break and the fade.
    - "male lead with female harmony" gave a female lead on one take (the keeper) and, to the user's ear, a Pink Floyd mood on another. Pass `vocal_gender` to fix the voice.
  - Organ fuzz (2026-11-18, soulful fuzzwave where the fuzz plays the church organ, made for "Rhyme, Meter, Flow"; user by ear: "a weird compelling organ"): "the bass line comes in first and stays, soulful hypnotic fuzzwave, thick sustained fuzz guitar chords held long and swelling like a church organ, stately descending bass line, hymn-like chord changes, soulful aching lead vocals with gospel warmth, the whole vocal range, swaying breathless phrasing where each line runs into the next, heavy fuzz, blur, blend, roar, warm, raw, vulnerable, reverent, unhurried swaying 4/4 at 80 bpm"
    - Negative style: "shouting, aggressive, heavy metal, harsh, fast, thin guitar, synth pop, novelty"
    - No voice gender was asked for; Suno chose a male soul/gospel singer, which the user loved over the fuzz organ.
    - Rock variant (2026-11-18, made for "Giving, Given"; user: the 3:39 take "delivers", with no detail yet on the organ or the choir): swap "soulful hypnotic fuzzwave" for "hypnotic fuzzwave rock" and the vocal phrase for "raw heartfelt rock lead vocals calling out, full-throated and open, a choir answering on the chorus", add "pounding drums", 84 bpm, and put "soul, gospel, growl" in the negative style.
  - Slow pipes (2026-11-18, bagpipe lament with a crystal female voice, a second setting of "Rhyme, Meter, Flow"; user by ear: the pipes are there all the way through, slow and wailing): "a lone bagpipe drone comes in first and stays, slow Celtic lament, Highland bagpipes carrying the melody, crystal-clear pure female lead vocals, soaring and aching, raw heartfelt drama, the whole vocal range, hymn-like chord changes, swaying phrasing where each line runs into the next, slow deep drums and low strings building, reverent, vulnerable, vast open air, unhurried swaying 4/4 at 66 bpm"
    - Negative style: "shouting, aggressive, heavy metal, harsh, fast, synth pop, novelty, jig, upbeat, breathy whisper"
    - Sent with `vocal_gender: "female"`, and `*` production notes saying the drone comes first and stays and the pipes answer the voice.
    - Bagpipes otherwise come out frantic for the user ("hyper steroid driven"). Which part tamed them is untested; my guess is the drone-first opening, "slow Celtic lament", the 66 bpm and "jig, upbeat, fast" in the negative style together.
- Vocal range (2026-11-18, "I Wonder", female voice over fuzzwave electronica): an octave count in the style does nothing (user: "suno won't do the range" on "three-octave vocal range"). Adding "dramatic, forced, belting" got closer. Best so far (user on the 3:38 take: "good", "some vocal reaching"): describe the contrast in the style ("low smoky verses that erupt into high belted choruses, huge dynamic leaps, from a low chest murmur to a soaring head-voice cry") and write the register into the section tags (`[Verse 1 - low, close, almost spoken]`, `[Chorus - belted, full voice, high]`, the bridge split into tagged high and low parts, the refrain's second line "an octave higher"). Keep "shouting" out of the negative style when asking for belting. Which of the tags did the work is untested.
  - Note names on top of that gave the keeper (user: the 3:53 take "was great"; published as "I Wonder"): "vocal melody spanning F3 to C6, from a low chest murmur at G3 to a soaring head-voice cry at C6" in the style, and pitches in the tags (verses "around G3", choruses "up to A5", bridge lines "C6" and "F3"). One pair only, so it may be take-to-take luck; no artist or song names were used.
- For a sound that is of an era but timeless, describe the instruments and feel and leave out era labels ("1970s", "psychedelic", "analog tape"); put "retro pastiche" in the negative style.

## Credits

- `account-usage` is free and shows the balance. Charges post late, so read it again after a few minutes.
- Speech: 10 credits per call (both takes). Observed 2026-11-14.
- Songs on `v6-wild`: unconfirmed. Two calls (four takes) had posted 10 credits a few minutes later; the rest may still have been pending.
- From the tool docs, not observed: stems 10 (`two`) or 50 (`twelve`); MIDI transcription 10; some downloads spend a download credit and need the user's approval first.

## Open questions

- Do real product or public-figure names in lyrics trip Suno's content check? (Outlook, Teams, Copilot passed on 2026-11-14.)
