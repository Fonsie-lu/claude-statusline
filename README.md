# claude-statusline

A custom [status line](https://docs.claude.com/en/docs/claude-code/statusline) for [Claude Code](https://claude.com/claude-code) that renders color-coded progress bars for context-window usage and your 5-hour / 7-day rate limits, each with its reset time.

```
34% ▓▓▓▓▓▓░░░░░░░░░░░░░░  │  62% ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░ 18:30  │  41% ▓▓▓▓▓▓▓▓░░░░░░░░░░░░ 21.06
```

## Features

- **Context-window bar** — how much of the current context window is in use.
- **5-hour rate-limit bar** — usage against the rolling 5-hour limit, with the reset time (`HH:MM`).
- **7-day rate-limit bar** — usage against the rolling 7-day limit, with the reset date (`DD.MM`).
- **Color-coded** by severity: blue under 50%, yellow 50–74%, red at 75%+.
- **Degrades gracefully** — rate-limit segments are omitted when Claude Code doesn't provide that data.

Each bar is 20 blocks wide (`▓` used, `░` free) and prefixed with its percentage.

## Requirements

- `bash`
- [`jq`](https://jqlang.github.io/jq/)
- `date` (GNU coreutils — uses `date -d`)
- A terminal with ANSI color support

## Installation

1. Copy `statusline-command.sh` into your Claude Code config directory (e.g. `~/.claude/`) and make it executable:

   ```bash
   cp statusline-command.sh ~/.claude/statusline-command.sh
   chmod +x ~/.claude/statusline-command.sh
   ```

2. Point Claude Code at it in `~/.claude/settings.json`:

   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "~/.claude/statusline-command.sh"
     }
   }
   ```

3. Restart Claude Code (or start a new session) to see the status line.

## How it works

Claude Code pipes a JSON payload to the script on stdin. The script reads the relevant fields with `jq`:

- `.context_window.used_percentage`
- `.rate_limits.five_hour.used_percentage` / `.resets_at`
- `.rate_limits.seven_day.used_percentage` / `.resets_at`

It converts the reset epoch timestamps to local time, builds a colored bar for each metric, and prints them on a single line separated by `│`.

## Customization

Edit `statusline-command.sh`:

- **`BAR_WIDTH`** — number of blocks per bar (default `20`).
- **Color thresholds** — adjust the `((pct < 50))` / `((pct < 75))` cutoffs in `make_bar`.
- **Block characters** — swap the `▓` / `░` glyphs.
- **Time formats** — change the `+%H:%M` (5-hour) and `+%d.%m` (7-day) `date` formats.
- **Separator** — edit the `SEP` variable.

## License

MIT
