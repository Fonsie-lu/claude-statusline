# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About This Directory

This is `~/.claude` — the global Claude Code configuration directory. It is not a project repository. Settings here apply across all Claude Code sessions.

## Active Configuration

### Hooks (`settings.json`)

A `PostToolUse` hook runs after every `Write` or `Edit` tool call. It pipes the affected file path to `npx prettier --write` with `--ignore-unknown`, auto-formatting any supported file type. This means:

- You do not need to manually format files after writing them.
- Prettier config is picked up from the project's own config files (if present).
- The hook silently no-ops on unsupported file types.

### Status Line (`statusline-command.sh`)

The status line displays a 10-block progress bar for context window usage (▓ = used, ░ = free), followed by percentage, 5-hour rate limit usage, 7-day rate limit usage, and the 5-hour reset timestamp.

## Directory Structure

- `settings.json` — global Claude Code settings (hooks, statusline)
- `statusline-command.sh` — bash script powering the custom status line
- `plugins/` — installed plugin marketplace data (do not edit manually)
- `projects/` — per-project persistent memory, keyed by directory path
- `history.jsonl` — conversation history (do not edit)
