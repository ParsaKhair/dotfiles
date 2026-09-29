# shellcheck shell=bash
# omni — user-editable configuration.  Sourced by every omni script.
# Everything here is meant to be tweaked by hand.

# ── Where your course files live ────────────────────────────────────────────
DOCS_ROOT="${DOCS_ROOT:-$HOME/Documents}"

# Semester folder name (e.g. "26-Fall").  Empty = auto-detect from today's date.
# Auto-detect rule: Jan–May -> Spring, Jun–Jul -> Summer, Aug–Dec -> Fall.
SEMESTER="${SEMESTER:-}"

# ── Openers ─────────────────────────────────────────────────────────────────
TERMINAL="${TERMINAL:-alacritty}"
FILE_MANAGER="${FILE_MANAGER:-ranger}"
EDITOR_CMD="${EDITOR_CMD:-nvim}"
# PDFs: default respects your system default (currently librewolf).
# For a real reader instead, set:  PDF_CMD="zathura"
PDF_CMD="${PDF_CMD:-xdg-open}"

# ── Canvas ──────────────────────────────────────────────────────────────────
CANVAS_BASE="${CANVAS_BASE:-https://canvas.upenn.edu}"

# Map each course short-name (the folder name under the semester dir) to its
# Canvas numeric course id.  Find the id in the URL when you open a course on
# Canvas:  https://canvas.upenn.edu/courses/1234567  ->  the id is 1234567.
#
# Leave a value empty to just open the Canvas dashboard for that course.
declare -A CANVAS_ID=(
  [be5570]="1947669"    # BE 5570 Quantitative Principles of Drug Design
  [be5590]="1947506"    # BE 5590 Multiscale Modeling of Chemical and Biological Systems
  [phys3361]="1925920"  # PHYS 3361 Electromagnetism I
  [phys5531]="1948336"  # PHYS 5531 Quantum Mechanics I
  [phys6611]="1946714"  # PHYS 6611 Statistical Mechanics
  [chem2410]="1937022"  # CHEM 2410 Principles of Organic Chemistry I
  [chem2412]="1947047"  # CHEM 2412 Organic Chemistry I Laboratory
)

# ── The two LLM tiers ───────────────────────────────────────────────────────
# omni is LLM-first: your plain-language request always goes to a model.
#
# TIER 1 — the PARSER (fast).  A small model reads your request plus a catalog
# of your courses/files and returns ONE structured command (open this pdf, open
# that Canvas course, edit this file, open a URL) — OR decides the task is hard
# and escalates.  This is the hot path; keep it a fast model.
#
# The default runs `claude -p` with MCP servers skipped (~3s on this machine).
# Two optional ways to make the parse near-instant (sub-second):
#   • export ANTHROPIC_API_KEY=...   -> omni uses a raw Messages API call
#     (set OMNI_API_MODEL to pick the model id; default is a Haiku).
#   • OMNI_PARSE_CMD="ollama run <model>"  -> a local model does the parsing.
#     It receives the request on argv and the system prompt on stdin.
OMNI_PARSE_MODEL="${OMNI_PARSE_MODEL:-haiku}"
OMNI_API_MODEL="${OMNI_API_MODEL:-claude-haiku-4-5-20251001}"
OMNI_PARSE_CMD="${OMNI_PARSE_CMD:-}"

# TIER 2 — the AGENT (rigorous).  When the parser escalates, the full Claude
# Code agent runs with tools and actually does the work.  A few seconds.
# Empty = your Claude default; set e.g. "opus" for hard multi-step tasks.
OMNI_MODEL="${OMNI_MODEL:-}"
