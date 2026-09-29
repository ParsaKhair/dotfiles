#!/usr/bin/env bash
# omni test runner.
#   run.sh                -> run all cases
#   run.sh 1 4 5          -> run only those 1-based case numbers
#   run.sh 6 12           -> (two args that are a valid range) also works as 6..12
# Reads test/cases.tsv (prompt <tab> expected_action <tab> expected_substring).
# Runs each prompt through `OMNI_DRYRUN=1 omni` and checks routing + latency.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
omni="$here/../omni"
cases="$here/cases.tsv"

mapfile -t LINES < "$cases"
n=${#LINES[@]}

# Which case numbers to run.
sel=()
if [ "$#" -eq 0 ]; then
  for ((i=1;i<=n;i++)); do sel+=("$i"); done
elif [ "$#" -eq 2 ] && [ "$1" -le "$2" ] 2>/dev/null && [ $(( $2 - $1 )) -gt 1 ]; then
  for ((i=$1;i<=$2;i++)); do sel+=("$i"); done
else
  sel=("$@")
fi

pass=0; fail=0; slow=0
printf '%-4s %-6s %-8s %-9s %s\n' "#" "res" "ms" "action" "prompt"
for idx in "${sel[@]}"; do
  line="${LINES[$((idx-1))]}"
  prompt="$(printf '%s' "$line" | cut -f1)"
  exp_act="$(printf '%s' "$line" | cut -f2)"
  exp_sub="$(printf '%s' "$line" | cut -f3)"

  out="$(OMNI_DRYRUN=1 "$omni" "$prompt" 2>/dev/null | grep '^OMNI_RESULT' | head -1)"
  act="$(sed -n 's/.*action=\([^ ]*\).*/\1/p' <<<"$out")"
  ms="$(sed -n 's/.*parse_ms=\([0-9]*\).*/\1/p' <<<"$out")"
  tgt="${out#*target=}"

  ok=1
  [ "$act" = "$exp_act" ] || ok=0
  if [ -n "$exp_sub" ]; then case "$tgt" in *"$exp_sub"*) : ;; *) ok=0 ;; esac; fi

  # "simple" (non-escalate) tasks should be fast; flag > 6000 ms.
  tag="PASS"; if [ "$ok" -ne 1 ]; then tag="FAIL"; fail=$((fail+1)); else pass=$((pass+1)); fi
  if [ "$exp_act" != escalate ] && [ -n "$ms" ] && [ "$ms" -gt 6000 ]; then slow=$((slow+1)); tag="$tag*slow"; fi

  printf '%-4s %-6s %-8s %-9s %s\n' "$idx" "$tag" "${ms:-?}" "${act:-none}" "$prompt"
  [ "$ok" -ne 1 ] && printf '       expected action=%s substr=%q ; got target=%q\n' "$exp_act" "$exp_sub" "$tgt"
done

echo "---"
echo "pass=$pass fail=$fail slow_simple=$slow (of ${#sel[@]} run)"
