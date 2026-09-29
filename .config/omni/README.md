# omni

A natural-language command bar for the desktop. Bound to **`Alt`+`O`** (Hyprland):
a text box opens, you type plain language, and omni does the thing.

```
open my quantum textbook              -> opens the Sakurai PDF
show my be5590 monte carlo lab        -> reveals the folder in ranger
pull up the phys6611 canvas           -> opens that course on Canvas
edit my hw2 tex                       -> opens it in nvim
summarize my sakurai homework and     -> escalates to the full Claude agent
  draft an email about it
```

You can also run it straight from a shell: `omni "open the be5570 lab"`.

## How it decides (LLM-first, two tiers)

There is **no fuzzy search**. Every request goes to a model.

1. **Parser (fast).** A small model gets your request plus a *catalog* of this
   semester's files and courses, and returns exactly one structured command —
   `open` / `reveal` / `edit` a resolved path, `canvas` a course, `url` a link —
   resolving references *semantically* ("my quantum textbook" → the Sakurai
   pdf). omni runs that command directly. The catalog is context for the model,
   **not** a string matcher.
2. **Agent (rigorous).** If the request is complex, ambiguous, needs reasoning,
   or isn't a plain open-this action, the parser returns `escalate` and the full
   Claude Code agent ([ask.sh](ask.sh)) takes over with real tools.

## Speed & the honest tradeoff

Natural language means a model is in the loop, so this is not zero-latency like
a hotkey. On this machine:

- **default** (`claude -p`, MCP servers skipped): **~3 s** per parse.
- **`ANTHROPIC_API_KEY` set**: a raw Messages API call, **~1 s**.
- **`OMNI_PARSE_CMD` = a local model** (e.g. `ollama run …`): as fast as your box.

See [config.sh](config.sh) to switch tiers. (The big win over the naive version:
`--strict-mcp-config` stops `claude -p` from booting all 10 of your MCP servers,
which was turning every call into a 13 s wait.)

## Files
- `config.sh` — semester, openers, **Canvas course ids**, and the parser/agent models.
- `index.sh` — builds the cached catalog of `~/Documents/<sem>` (run directly to force a rebuild).
- `omni` — the command bar: input → parse → route/escalate.
- `ask.sh` — the escalation agent.

## Setup left for you
1. **Canvas ids** in `config.sh` (from a course's `.../courses/1234567` URL) so
   `canvas` deep-links instead of opening the dashboard.
2. *(optional)* a faster parser via `ANTHROPIC_API_KEY` or `OMNI_PARSE_CMD`.
