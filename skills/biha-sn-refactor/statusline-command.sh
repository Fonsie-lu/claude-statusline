#!/bin/bash

BAR_WIDTH=20
RESET=$'\033[0m'

make_bar() {
  local pct=$1 filled fg bar='' i
  filled=$((pct * BAR_WIDTH / 100))
  if   ((pct < 50)); then fg=$'\033[34m'
  elif ((pct < 75)); then fg=$'\033[33m'
  else                    fg=$'\033[31m'
  fi
  for ((i = 0; i < BAR_WIDTH; i++)); do
    ((i < filled)) && bar+='▓' || bar+='░'
  done
  printf '%s' "${fg}${pct}%${RESET} ${fg}${bar}${RESET}"
}

input=$(cat)

{ read -r PCT; read -r FIVE_H; read -r WEEK; read -r FIVE_H_EPOCH; read -r WEEK_EPOCH; } < <(
  jq -r '
    (.context_window.used_percentage // 0 | floor),
    (.rate_limits.five_hour.used_percentage // ""),
    (.rate_limits.seven_day.used_percentage // ""),
    (.rate_limits.five_hour.resets_at // ""),
    (.rate_limits.seven_day.resets_at // "")
  ' <<< "$input"
)

[[ -n $FIVE_H_EPOCH ]] && FIVE_H_RESET=$(date -d "@$FIVE_H_EPOCH" '+%H:%M' 2>/dev/null)
[[ -n $WEEK_EPOCH   ]] && WEEK_RESET=$(date -d "@$WEEK_EPOCH"     '+%d.%m' 2>/dev/null)

SEP='  │  '

out=$(make_bar "$PCT")
[[ -n $FIVE_H ]] && out+="${SEP}$(make_bar "$(printf '%.0f' "$FIVE_H")") $FIVE_H_RESET"
[[ -n $WEEK   ]] && out+="${SEP}$(make_bar "$(printf '%.0f' "$WEEK")") $WEEK_RESET"
echo "$out"
