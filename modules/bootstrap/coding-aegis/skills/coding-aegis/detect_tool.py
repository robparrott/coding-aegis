#!/usr/bin/env python3
"""Coding-agent tool detection for the coding-aegis skill.

Detects which coding agent is executing this skill from environment signals
and script path. Returns a result dict with the detected tool name and the
signals that fired.

Usage (standalone):
    python3 detect_tool.py

Usage (import):
    from detect_tool import detect_tool
    result = detect_tool()
    tool = result["tool"]   # "claude" | "codex" | "cursor" | "gemini" | "opencode" | "windsurf" | "copilot" | "UNKNOWN"

Validation status of each signal is documented in:
    docs/architecture/spec-tool-detection.md
"""
import json
import os
import sys
from pathlib import Path


# Detection table: (signal_name, check_fn, tool_name)
# Checked in order — first match sets the tool. All matching signals are recorded.
# check_fn(env: dict, file_path: Path) -> bool
_SIGNALS = [
    # --- Environment variable signals (process-intrinsic, highest confidence) ---
    # Claude Code: confirmed live (CLAUDECODE=1, CLAUDE_CODE_ENTRYPOINT=cli)
    ("env:CLAUDECODE=1",
     lambda env, fp: env.get("CLAUDECODE") == "1",
     "claude"),

    # Gemini CLI: confirmed via user `env` capture (GEMINI_CLI=1)
    ("env:GEMINI_CLI=1",
     lambda env, fp: env.get("GEMINI_CLI") == "1",
     "gemini"),

    # Codex CLI: CODEX_CI=1 is force-set by runtime on every subprocess (confirmed: source)
    ("env:CODEX_CI=1",
     lambda env, fp: env.get("CODEX_CI") == "1",
     "codex"),

    # Codex CLI: CODEX_THREAD_ID always injected per session (confirmed: source)
    ("env:CODEX_THREAD_ID",
     lambda env, fp: "CODEX_THREAD_ID" in env,
     "codex"),

    # Cursor: CURSOR_AGENT=1 injected in agent terminal (confirmed: intentional, regressed once)
    ("env:CURSOR_AGENT=1",
     lambda env, fp: env.get("CURSOR_AGENT") == "1",
     "cursor"),

    # OpenCode: OPENCODE=1 set in every subprocess during opencode run (confirmed empirically)
    ("env:OPENCODE=1",
     lambda env, fp: env.get("OPENCODE") == "1",
     "opencode"),

    # OpenCode: OPENCODE_PID set to the server PID (secondary, same session scope)
    ("env:OPENCODE_PID",
     lambda env, fp: "OPENCODE_PID" in env,
     "opencode"),

    # --- Script path signals (__file__, fallback when env vars absent) ---
    # Codex user-global install: ~/.codex/skills/<name>/
    ("path:.codex",
     lambda env, fp: ".codex" in fp.parts,
     "codex"),

    # Codex CWD-relative install: .agents/skills/<name>/
    ("path:.agents",
     lambda env, fp: ".agents" in fp.parts,
     "codex"),

    # Windsurf global install: ~/.codeium/windsurf/skills/<name>/
    ("path:.codeium",
     lambda env, fp: ".codeium" in fp.parts,
     "windsurf"),

    # Windsurf workspace install: .windsurf/skills/<name>/
    # NOTE: unverified — no WINDSURF_* env var exists; path is only signal
    ("path:.windsurf",
     lambda env, fp: ".windsurf" in fp.parts,
     "windsurf"),

    # Cursor install: ~/.cursor/skills/<name>/  (path unverified — CURSOR_AGENT=1 is primary)
    ("path:.cursor",
     lambda env, fp: ".cursor" in fp.parts,
     "cursor"),

    # Gemini install path (unverified — GEMINI_CLI=1 is primary)
    ("path:.gemini",
     lambda env, fp: ".gemini" in fp.parts,
     "gemini"),

    # OpenCode install path: ~/.config/opencode/skills/<name>/ or .opencode/skills/<name>/
    ("path:.opencode",
     lambda env, fp: ".opencode" in fp.parts,
     "opencode"),

    # Copilot CLI: no env var is injected into subprocesses (confirmed: docs + AD research).
    # Path signal only — .github/skills/<name>/ is the Copilot project-scope install path.
    # NOTE: Copilot has no invocable skill execution, so this fires only in direct invocations
    #       or future Copilot CLI versions that gain skill support.
    # > NEEDS VALIDATION ON COPILOT MACHINE
    ("path:.github",
     lambda env, fp: ".github" in fp.parts,
     "copilot"),
]

_DEFAULT_TOOL = "UNKNOWN"


def detect_tool(env=None, file_path=None):
    """Detect the active coding agent.

    Args:
        env:       Environment mapping (default: os.environ). Pass a dict for testing.
        file_path: Override for __file__ resolution (default: this file). Pass a str/Path for testing.

    Returns:
        {
            "tool":    "<name>",          # claude | codex | cursor | gemini | windsurf | copilot
            "signals": ["<name>", ...]    # all signals that matched (first determines tool)
        }
    """
    if env is None:
        env = os.environ
    if file_path is None:
        file_path = Path(__file__).resolve()
    else:
        file_path = Path(file_path).resolve()

    fired = []
    tool = None

    for signal_name, check_fn, tool_name in _SIGNALS:
        try:
            if check_fn(env, file_path):
                fired.append(signal_name)
                if tool is None:
                    tool = tool_name
        except Exception:
            pass  # detection must never raise

    return {
        "tool": tool if tool is not None else _DEFAULT_TOOL,
        "signals": fired,
    }


if __name__ == "__main__":
    print(json.dumps(detect_tool(), indent=2))
