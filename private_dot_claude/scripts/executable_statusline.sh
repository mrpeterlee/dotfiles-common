#!/usr/bin/env bash
# Claude Code status line — reads session JSON from stdin
# Shows: dir, model, git, cost, context bar, rate limits, churn, duration
set -euo pipefail

input=$(cat)

# --- Extract fields via jq (single call for speed) ---
eval "$(echo "$input" | jq -r '
  def fmt_cost: if . == null then "0.00"
    elif . < 0.01 then (. * 100 | floor | tostring | "0.0" + .)
    elif . < 1 then (. * 100 | round / 100 | tostring)
    else (. * 100 | round / 100 | tostring)
    end;
  def fmt_tokens:
    if . == null then "?"
    elif . >= 1000000 then ((. / 1000000 * 10 | round / 10 | tostring) + "M")
    elif . >= 1000 then ((. / 1000 | round | tostring) + "k")
    else (. | tostring)
    end;
  def shorten_model:
    if . == null then "?"
    elif test("opus"; "i") then "Opus"
    elif test("sonnet"; "i") then "Sonnet"
    elif test("haiku"; "i") then "Haiku"
    else .
    end;

  "CWD=" + (.workspace.current_dir // .cwd // "?" | @sh),
  "PROJECT_DIR=" + (.workspace.project_dir // .workspace.current_dir // .cwd // "?" | @sh),
  "MODEL=" + ((.model.display_name // .model.id // "?") | shorten_model | @sh),
  "MODEL_ID=" + (.model.id // "?" | @sh),
  "COST=" + ((.cost.total_cost_usd // 0) | fmt_cost | @sh),
  "CTX_PCT=" + ((.context_window.used_percentage // 0) | tostring | @sh),
  "CTX_SIZE=" + ((.context_window.context_window_size // 200000) | fmt_tokens | @sh),
  "CTX_USED=" + (((.context_window.total_input_tokens // 0) | if . == 0 then ((.context_window.current_usage.input_tokens // 0) + (.context_window.current_usage.cache_creation_input_tokens // 0) + (.context_window.current_usage.cache_read_input_tokens // 0)) else . end) | fmt_tokens | @sh),
  "LINES_ADD=" + ((.cost.total_lines_added // 0) | tostring | @sh),
  "LINES_DEL=" + ((.cost.total_lines_removed // 0) | tostring | @sh),
  "DURATION_MS=" + ((.cost.total_duration_ms // 0) | tostring | @sh),
  "VIM_MODE=" + (.vim.mode // "" | @sh),
  "AGENT_NAME=" + (.agent.name // "" | @sh),
  "SESSION_NAME=" + (.session_name // "" | @sh),
  "WORKTREE=" + (.worktree.name // .workspace.git_worktree // "" | @sh),
  "RATE_5H=" + ((.rate_limits.five_hour.used_percentage // -1) | tostring | @sh),
  "RATE_5H_RESET=" + ((.rate_limits.five_hour.resets_at // 0) | tostring | @sh),
  "RATE_7D=" + ((.rate_limits.seven_day.used_percentage // -1) | tostring | @sh),
  "RATE_7D_RESET=" + ((.rate_limits.seven_day.resets_at // 0) | tostring | @sh),
  "CACHE_CREATE=" + ((.context_window.current_usage.cache_creation_input_tokens // 0) | tostring | @sh),
  "CACHE_READ=" + ((.context_window.current_usage.cache_read_input_tokens // 0) | tostring | @sh),
  "INPUT_TOKENS=" + ((.context_window.current_usage.input_tokens // 0) | tostring | @sh),
  "EXCEEDS_200K=" + ((.exceeds_200k_tokens // false) | tostring | @sh),
  "VERSION=" + (.version // "?" | @sh)
')"

# --- Colors ---
RST='\033[0m'
DIM='\033[2m'
BOLD='\033[1m'
# Foreground
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
MAGENTA='\033[35m'
CYAN='\033[36m'
WHITE='\033[37m'
# Bright
BRED='\033[91m'
BGREEN='\033[92m'
BYELLOW='\033[93m'
BCYAN='\033[96m'

# --- Helpers ---
bar() {
  local pct=${1:-0} width=${2:-20}
  local filled=$(( pct * width / 100 ))
  # Ensure at least 1 filled block when pct > 0
  if (( pct > 0 && filled == 0 )); then filled=1; fi
  local empty=$(( width - filled ))
  local color
  if (( pct < 50 )); then color="$GREEN"
  elif (( pct < 75 )); then color="$YELLOW"
  elif (( pct < 90 )); then color="$BRED"
  else color="$RED$BOLD"
  fi
  printf '%b' "$color"
  for ((i=0; i<filled; i++)); do printf '%s' '▓'; done
  printf '%b' "$DIM"
  for ((i=0; i<empty; i++)); do printf '%s' '░'; done
  printf '%b' "$RST"
}

fmt_duration() {
  local ms=$1
  local secs=$(( ms / 1000 ))
  if (( secs < 60 )); then printf '%ds' "$secs"
  elif (( secs < 3600 )); then printf '%dm' $(( secs / 60 ))
  else printf '%dh%dm' $(( secs / 3600 )) $(( (secs % 3600) / 60 ))
  fi
}

fmt_countdown() {
  local reset_ts=$1
  local now_ts
  now_ts=$(date +%s)
  local diff=$(( reset_ts - now_ts ))
  if (( diff <= 0 )); then printf 'now'; return; fi
  if (( diff < 3600 )); then printf '%dm' $(( diff / 60 ))
  else printf '%dh%dm' $(( diff / 3600 )) $(( (diff % 3600) / 60 ))
  fi
}

# --- Directory (shortened) ---
dir="$CWD"
home="$HOME"
if [[ "$dir" == "$home"* ]]; then
  dir="~${dir#$home}"
fi
# Show only last 2 path components if long
if [[ $(echo "$dir" | tr '/' '\n' | wc -l) -gt 3 ]]; then
  dir="...$(echo "$dir" | rev | cut -d'/' -f1-2 | rev)"
fi

# --- Git info ---
git_info=""
if cd "$CWD" 2>/dev/null; then
  branch=$(git branch --show-current 2>/dev/null || true)
  if [[ -n "$branch" ]]; then
    dirty=""
    if [[ -n "$(git status --porcelain 2>/dev/null | head -1)" ]]; then
      dirty="${YELLOW}*${RST}"
    fi
    git_info="${CYAN}${branch}${RST}${dirty}"
  fi
fi

# --- Worktree indicator ---
wt_info=""
if [[ -n "$WORKTREE" ]]; then
  wt_info="${DIM}wt:${RST}${MAGENTA}${WORKTREE}${RST} "
fi

# --- Model badge ---
model_color="$BCYAN"
if [[ "$MODEL" == "Opus" ]]; then model_color="$MAGENTA"
elif [[ "$MODEL" == "Haiku" ]]; then model_color="$GREEN"
fi
# Detect 1M context
ctx_tag=""
if [[ "$CTX_SIZE" == *"M"* ]] || [[ "$EXCEEDS_200K" == "true" ]]; then
  ctx_tag="${DIM}[1M]${RST}"
fi
model_badge="${model_color}${BOLD}${MODEL}${RST}${ctx_tag}"

# --- Vim mode ---
vim_badge=""
if [[ -n "$VIM_MODE" ]]; then
  if [[ "$VIM_MODE" == "INSERT" ]]; then
    vim_badge=" ${GREEN}[I]${RST}"
  else
    vim_badge=" ${BLUE}[N]${RST}"
  fi
fi

# --- Agent ---
agent_badge=""
if [[ -n "$AGENT_NAME" ]]; then
  agent_badge=" ${DIM}agent:${RST}${BYELLOW}${AGENT_NAME}${RST}"
fi

# --- Cost ---
cost_str="${DIM}\$${RST}${WHITE}${COST}${RST}"

# --- Context bar ---
ctx_pct=${CTX_PCT%.*}  # strip decimal
ctx_bar=$(bar "$ctx_pct" 20)
ctx_str="${ctx_bar} ${ctx_pct}% ${DIM}${CTX_USED}/${CTX_SIZE}${RST}"

# --- Cache efficiency ---
cache_eff=""
if (( INPUT_TOKENS > 0 )); then
  total_in=$(( INPUT_TOKENS + CACHE_CREATE + CACHE_READ ))
  if (( total_in > 0 && CACHE_READ > 0 )); then
    eff=$(( CACHE_READ * 100 / total_in ))
    if (( eff > 70 )); then cache_color="$GREEN"
    elif (( eff > 40 )); then cache_color="$YELLOW"
    else cache_color="$RED"
    fi
    cache_eff=" ${DIM}cache:${RST}${cache_color}${eff}%${RST}"
  fi
fi

# --- Rate limits (Max plan) ---
rate_str=""
if [[ "$RATE_5H" != "-1" ]]; then
  r5=${RATE_5H%.*}
  r5_bar=$(bar "$r5" 8)
  r5_reset=""
  if (( RATE_5H_RESET > 0 )); then
    r5_reset="${DIM}$(fmt_countdown "$RATE_5H_RESET")${RST}"
  fi
  rate_str="${DIM}5h${RST}${r5_bar}${r5}%${r5_reset}"
fi
if [[ "$RATE_7D" != "-1" ]]; then
  r7=${RATE_7D%.*}
  r7_bar=$(bar "$r7" 8)
  r7_reset=""
  if (( RATE_7D_RESET > 0 )); then
    r7_reset="${DIM}$(fmt_countdown "$RATE_7D_RESET")${RST}"
  fi
  if [[ -n "$rate_str" ]]; then rate_str="$rate_str "; fi
  rate_str="${rate_str}${DIM}7d${RST}${r7_bar}${r7}%${r7_reset}"
fi

# --- Churn ---
churn=""
if (( LINES_ADD > 0 || LINES_DEL > 0 )); then
  churn="${GREEN}+${LINES_ADD}${RST}${DIM}/${RST}${RED}-${LINES_DEL}${RST}"
fi

# --- Duration ---
dur=""
if (( DURATION_MS > 0 )); then
  dur="${DIM}$(fmt_duration "$DURATION_MS")${RST}"
fi

# --- Separator ---
S="${DIM} │ ${RST}"

# ===== LINE 1: dir | model | git | cost =====
line1="${BOLD}${BLUE}${dir}${RST}"
line1="${line1}${S}${model_badge}${vim_badge}${agent_badge}"
if [[ -n "$git_info" ]]; then
  line1="${line1}${S}${wt_info}${git_info}"
fi
line1="${line1}${S}${cost_str}"

# ===== LINE 2: context bar | rate limits | churn | duration =====
line2="${ctx_str}${cache_eff}"
if [[ -n "$rate_str" ]]; then
  line2="${line2}${S}${rate_str}"
fi
if [[ -n "$churn" ]]; then
  line2="${line2}${S}${churn}"
fi
if [[ -n "$dur" ]]; then
  line2="${line2}${S}${dur}"
fi

# --- Output ---
printf '%b\n' "$line1"
printf '%b\n' "$line2"
