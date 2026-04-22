# Gemini — Manual CLI Test

Human-runnable equivalent of `tests/integration/test_gemini.py`. Each step mirrors the exact pytest assertions. Run in a clean terminal session.

---

## Prerequisites

- `gemini` on PATH and authenticated
- Run from the repository root

---

## Setup

Set variables, strip Claude Code env vars (so `detect_tool.py` does not return `"claude"`), create a temp git repo, and pre-create the `.gemini` directories the agent writes into.

```zsh
export REPO_ROOT=$(pwd)
export SKILL_DIR="$REPO_ROOT/pkgs/bootstrap/coding-aegis/skills/coding-aegis"
export TEST_DIR=$(mktemp -d)
export GEMINI_MODEL="gemini-3-flash-preview"
unset CLAUDECODE CLAUDE_CODE_ENTRYPOINT
git init -q "$TEST_DIR"
cd "$TEST_DIR"
mkdir -p .gemini/rules .gemini/skills
```

---

## Quota handling

Gemini retries quota errors internally and the retry messages appear in `$OUTPUT`. This is normal — if the step's pass condition is met, the step passed regardless of retry noise.

Only skip to Teardown when the step's pass condition is **not met** and the output contains a terminal quota failure. The pattern below is for that case:

```zsh
echo "$OUTPUT" | grep -iE "RESOURCE_EXHAUSTED|429|rate.limit|limit exceeded|too many requests" \
  && echo "QUOTA EXHAUSTED — skip to teardown" || true
```

Transient messages such as `"Your quota will reset after Xs... Retrying"` are handled by the Gemini CLI automatically and do not indicate failure.

---

## Phase 1 — Auth

Confirm the Gemini CLI can authenticate and respond.

```zsh
OUTPUT=$(echo "Reply with exactly: AUTH_OK" | gemini -m "$GEMINI_MODEL" -o text --yolo 2>&1)
echo "$OUTPUT"
```

**Pass:** `AUTH_OK` appears in the output.

---

## Phase 2 — Marketplace

Not applicable. Gemini has no plugin marketplace. Skip this phase.

---

## Phase 3 — Skill install

Link the coding-aegis skill workspace-wide and confirm it is discoverable.

```zsh
gemini skills link "$SKILL_DIR" --scope workspace --consent
gemini skills list
```

**Pass:** `gemini skills list` output contains `coding-aegis`.

---

## Phase 4a — detect_tool direct

Run `detect_tool.py` directly from the shell. `GEMINI_CLI=1` is only set inside a live Gemini agent subprocess, so when run directly the expected result is `tool=UNKNOWN` and `signals=[]`. Only the JSON structure is asserted here, not the tool value.

```zsh
OUTPUT=$(python3 "$SKILL_DIR/detect_tool.py" 2>&1)
echo "$OUTPUT"
```

**Pass:** Output contains a JSON object with both `"tool"` and `"signals"` keys. Quick check:

```zsh
python3 -c "
import json
raw = open('/dev/stdin').read()
start = raw.find('{')
d = json.loads(raw[start:])
assert 'tool' in d and 'signals' in d, 'Missing keys: ' + str(d)
print('PASS: tool=' + d['tool'] + '  signals=' + str(d['signals']))
" <<< "$OUTPUT"
```

---

## Phase 4b — detect-tool skill (agent)

Invoke `/coding-aegis detect-tool` through the Gemini agent. The agent sets `GEMINI_CLI=1`, so `detect_tool.py` returns `tool="gemini"`.

```zsh
OUTPUT=$(echo "/coding-aegis detect-tool" | gemini -m "$GEMINI_MODEL" -o text --yolo 2>&1)
echo "$OUTPUT"
```

**Pass:** Output contains `gemini` (case-insensitive) and at least one signal prefixed `env:` or `path:`.

```zsh
echo "$OUTPUT" | grep -i "gemini"      && echo "tool: PASS"   || echo "tool: FAIL"
echo "$OUTPUT" | grep -iE "env:|path:" && echo "signal: PASS" || echo "signal: FAIL"
```

---

## Phase 4c — list (agent)

Invoke `/coding-aegis list` and confirm the catalog loads.

```zsh
OUTPUT=$(echo "/coding-aegis list" | gemini -m "$GEMINI_MODEL" -o text --yolo 2>&1)
echo "$OUTPUT"
```

**Pass:** Output contains `helloworld` (case-insensitive).

```zsh
echo "$OUTPUT" | grep -i "helloworld" && echo "PASS" || echo "FAIL"
```

---

## Phase 4d — show (agent)

Invoke `/coding-aegis show helloworld` and confirm key fields are present.

```zsh
OUTPUT=$(echo "/coding-aegis show helloworld" | gemini -m "$GEMINI_MODEL" -o text --yolo 2>&1)
echo "$OUTPUT"
```

**Pass:** Output contains all three of `helloworld`, `optional` (tier), and `1.0.0` (version).

```zsh
echo "$OUTPUT" | grep -i "helloworld" && echo "name: PASS" || echo "name: FAIL"
echo "$OUTPUT" | grep -i "optional"   && echo "tier: PASS" || echo "tier: FAIL"
echo "$OUTPUT" | grep    "1.0.0"      && echo "ver:  PASS" || echo "ver:  FAIL"
```

---

## Phase 5 — Install helloworld (agent)

Install the helloworld package to Project scope.

```zsh
OUTPUT=$(echo "/coding-aegis install helloworld to Project scope" | gemini -m "$GEMINI_MODEL" -o text --yolo 2>&1)
echo "$OUTPUT"
```

**Pass (output):** Contains at least one of `install`, `aegis--helloworld`, `wrote`, `created` (case-insensitive).

```zsh
echo "$OUTPUT" | grep -iE "install|aegis--helloworld|wrote|created" && echo "PASS" || echo "FAIL"
```

**Pass (artifacts):** Run from `$TEST_DIR`:

```zsh
python3 "$SKILL_DIR/aegis-validate.py" helloworld --catalog "$REPO_ROOT/pkgs" --tool gemini
echo "validate-install exit: $?"
```

Exit code 0 is a pass.

---

## Phase 5b — Invoke helloworld (agent)

Only run this phase if Phase 5 passed. Invoke the installed `/helloworld` skill.

```zsh
OUTPUT=$(echo "/helloworld" | gemini -m "$GEMINI_MODEL" -o text --yolo 2>&1)
echo "$OUTPUT"
```

**Pass:** Output contains `Hello, World` (exact case).

```zsh
echo "$OUTPUT" | grep "Hello, World" && echo "PASS" || echo "FAIL"
```

---

## Phase 6 — Uninstall helloworld (agent)

Only run this phase if Phase 5 passed. Uninstall helloworld and confirm artifacts are removed.

```zsh
OUTPUT=$(echo "/coding-aegis uninstall helloworld" | gemini -m "$GEMINI_MODEL" -o text --yolo 2>&1)
echo "$OUTPUT"
```

**Pass (output):** Does not contain `not installed`, `not found`, or `Error`.

```zsh
echo "$OUTPUT" | grep -iE "not installed|not found|Error" \
  && echo "FAIL: error phrase in output" || echo "output: PASS"
```

**Pass (files):** Both paths are absent.

```zsh
test ! -e .gemini/rules/aegis--helloworld--helloworld.md \
  && echo "rule file: PASS" || echo "rule file: FAIL (still present)"
test ! -d .gemini/skills/helloworld \
  && echo "skill dir: PASS" || echo "skill dir: FAIL (still present)"
```

---

## Teardown

```zsh
gemini skills uninstall coding-aegis --scope workspace
gemini skills list | grep -v "coding-aegis" && echo "unlink: PASS" || echo "unlink: FAIL"
cd "$REPO_ROOT"
rm -rf "$TEST_DIR"
```

---

## Expected results by tier

| Phase | Free tier (quota) | Paid tier |
|-------|-------------------|-----------|
| 1 auth | PASS | PASS |
| 2 marketplace | SKIP | SKIP |
| 3 skill linked | PASS | PASS |
| 4a detect direct | PASS | PASS |
| 4b detect skill | often quota-exhausted | PASS |
| 4c list | often quota-exhausted | PASS |
| 4d show | often quota-exhausted | PASS |
| 5 install | often quota-exhausted | PASS |
| 5b invoke | often quota-exhausted | PASS |
| 6 uninstall | often quota-exhausted | PASS |

Quota recovery is typically a few minutes to an hour depending on your usage tier.
