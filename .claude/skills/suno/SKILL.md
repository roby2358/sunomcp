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
- For lyric polish, hand the draft to a review agent for flow and rhyme, then show the revision and what changed.

## Lyrics

- Section tags in square brackets on their own line: `[Verse 1]`, `[Chorus]`, `[Bridge]`, `[Final Chorus]`.
- Write the chorus out once; a bare `[Chorus]` repeats it. Write it out again only when the words change.
- Structure: intersperse the chorus and instrumentals between verses, putting `[Chorus]` then `[Instrumental]` on consecutive lines. Default shape: verse, chorus, instrumental, ... verse, bridge, chorus, instrumental, final chorus. Variations are fine, but never leave out the `[Chorus]` / `[Instrumental]` breaks.
- Spoken lines: tag `[spoken]`, never `(spoken)`, since parentheses can get sung as backing vocals. Rendering is spotty, but keep using them.
- Production notes: lines starting with `*` at the top, before the first section tag.
- Rhymes land heavily: the rhyme word ends the line, carries the final stress, and is a full rhyme where possible. Put the joke on it.
- Flow: matching beat counts within a couplet, no stress pile-ups, no words that fight the meter (for example "productivity", "couture").

## Lyric-writing prompts

- Breathless sublation (user favorite, 2026-11-14): "In a swaying sing-song voice, where one idea flows naturally into the next with no breathing stops, write a song in 4 verses a bridge and a chorus about the sublation of <ideas>. No thinking! Belt it out!" Fill `<ideas>` with the pair to sublate (first use: big bang and singularity, giving "Cancelled and Kept").
- Zoom-out (Claude's idea, untested): "With total conviction and a straight face, write a song in 4 verses a bridge and a chorus about <small everyday mishap>. Each verse retells it one scale larger: the home, the city, the planet, the cosmos. The chorus never changes a word, yet means something bigger each time it returns. The bridge is the one moment of doubt. Heavy rhymes, no winking!"

## Style prompts

- Suno appends its own descriptors, which can cut against the request ("warm and harmonious" speech came back "nasal, adenoidal" and "tense and strident"). Check the returned `metadata.style`; use `negative_style` to steer away.
- A trashed song still reads with `audio-retrieve` but returns "Song not found" on `audio-like`.
- No style at all is a valid choice: the user sometimes sends lyrics with no style to see what Suno makes of them.
- User's house styles (with `variety: 0`):
  - Fuzzwave: "the bass line comes in first and stays, hypnotic fuzzwave, psychedelic, gentle soothing vocals, the whole vocal range, jangly guitars, heavy fuzz, blur, shred, blend, roar, raw, vulnerable, dissonant bass"
  - Power rock: "Open with virtuoso guitar and never let up, Explosive power rock, heavy crunchy guitar riffs, pounding drums, aggressive bass, gritty commanding vocals, soaring melodic choruses, screaming guitar leads, relentless rhythmic momentum, dramatic breakdowns, huge cinematic sound"
  - Tango: "tango, electronica, bold, dramatic"

## Credits

- `account-usage` is free and shows the balance. Charges post late, so read it again after a few minutes.
- Speech: 10 credits per call (both takes). Observed 2026-11-14.
- Songs on `v6-wild`: unconfirmed. Two calls (four takes) had posted 10 credits a few minutes later; the rest may still have been pending.
- From the tool docs, not observed: stems 10 (`two`) or 50 (`twelve`); MIDI transcription 10; some downloads spend a download credit and need the user's approval first.

## Open questions

- Do real product or public-figure names in lyrics trip Suno's content check? (Outlook, Teams, Copilot passed on 2026-11-14.)
