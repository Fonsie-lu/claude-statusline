# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A personal collection of Claude Code add-ons. There is no build system, package manifest or test suite. It holds two independent pieces:

1. **Status line** — `statusline-command.sh`, a bash script that renders color-coded bars for context-window usage and the 5-hour / 7-day rate limits. `README.md` documents it (install, customization).
2. **`biha-sn-refactor` skill** — `skills/biha-sn-refactor/SKILL.md` plus the helper `open-editor-files.py`. The skill refactors ServiceNow scripts to the BitHawk house style.

Nothing here is live until it is copied into `~/.claude/`. The installed status line is a copy at `~/.claude/statusline-command.sh`, run by `settings.json` as `bash ~/.claude/statusline-command.sh`. Editing the repo file does not change the running status line.

## Status line

Claude Code pipes a JSON payload on stdin; the script reads `.context_window.used_percentage` and `.rate_limits.{five_hour,seven_day}.{used_percentage,resets_at}` with one `jq` call, then prints one line. Rate-limit segments are omitted when the payload lacks them. Requires `jq` and GNU `date -d`.

Test by piping a sample payload:

```bash
echo '{"context_window":{"used_percentage":34},"rate_limits":{"five_hour":{"used_percentage":62,"resets_at":1760450000},"seven_day":{"used_percentage":81,"resets_at":1760900000}}}' \
  | bash statusline-command.sh
```

Keep `README.md` in sync when changing bar width, thresholds (50 / 75), glyphs or date formats — it documents all of them.

## biha-sn-refactor skill

`SKILL.md` is prompt content, not code: its frontmatter `description` controls when the skill triggers, and the body is the instruction set. It defers to the separate `biha-sn-coding` skill (not in this repo) and is overridden by customer-specific refactor skills.

`SKILL.md` calls `python3 <skill base directory>/open-editor-files.py`, so the script must sit in the same directory as `SKILL.md` wherever the skill is installed. The script is a fallback for finding the file open in VS Code: it reads `workspaceStorage/*/state.vscdb` (SQLite, read-only) for VS Code, VSCodium, Insiders and Cursor, on Linux and macOS config paths, and prints open files most-recent first. Stdlib only.

Run it against any directory inside an open VS Code workspace:

```bash
python3 open-editor-files.py [dir]
```
