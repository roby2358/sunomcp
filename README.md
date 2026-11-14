# suno

A workspace for making music with [Suno](https://suno.com) from Claude Code, through Suno's official MCP server.

## What's here

- `.claude/skills/suno/SKILL.md`: the project's `suno` skill. Working notes on connecting, lyric formatting, section tags, lyric-writing prompts, style prompts, and credit costs. Claude loads it for any Suno work here and adds to it as we learn.
- `styles.txt`: style prompts collected from my public Suno songs, one per line, most-used first, plus new ones added as they prove themselves.

## Setup

Register the MCP server for this directory, then authenticate with `/mcp` inside Claude Code:

```sh
claude mcp add --transport http suno https://api.suno.com/mcp
```

The server uses OAuth, so there is no API key. Access is in beta and needs an approved early-access application at suno.com/mcp. Under WSL the `localhost` redirect fails to load; paste the callback URL from the browser's address bar back into Claude Code to finish signing in.

## How we work

- Lyrics are drafted in chat first; songs are generated only on request, always on the `v6-wild` model.
- Each generation makes two takes and spends Suno credits.
- Liking, publishing and downloading happen only when asked.
