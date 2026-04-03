"""
test_gemini.py — Stub integration test for Gemini CLI.

Full implementation follows the same 7-phase pattern as test_claude.py.
Gemini-specific differences from Claude:
  - No marketplace (Phase 2 is N/A)
  - Skill install via ``gemini skills link <path>``
  - unset CLAUDECODE / CLAUDE_CODE_ENTRYPOINT (uses clean_env fixture)
  - Quota exhaustion is frequent; assert_no_quota_error maps to pytest.skip
  - keytar warning noise should be filtered from output before assertions
  - The gemini_quiet wrapper (from bash) becomes a post-processing function

Reference: tests/test-gemini-skill-install.sh
See also: tests/gemini-test-status.md for known issues and quota caveats.
"""

import shutil

import pytest

# ── Skip entire module if gemini is not on PATH ──────────────────────────────

pytestmark = pytest.mark.skipif(
    not shutil.which("gemini"),
    reason="gemini not installed / not on PATH",
)

# ── Phase 1 ──────────────────────────────────────────────────────────────────


def test_phase1_1_gemini_installed():
    """Phase 1.1 — gemini binary is on PATH."""
    assert shutil.which("gemini") is not None


@pytest.mark.skip(reason="Gemini integration tests not yet ported to pytest")
def test_phase1_2_gemini_authenticated():
    """Phase 1.2 — gemini can authenticate and respond AUTH_OK.

    Note: quota exhaustion should call pytest.skip, not pytest.fail.
    """
    pass


# ── Phases 2–7: stubs ────────────────────────────────────────────────────────


@pytest.mark.skip(reason="Gemini integration tests not yet ported to pytest")
def test_phase3_gemini_skill_install():
    """Phase 3 — install coding-aegis via ``gemini skills link``."""
    pass


@pytest.mark.skip(reason="Gemini integration tests not yet ported to pytest")
def test_phase4_gemini_detect_tool():
    """Phase 4 — coding-aegis detect-tool reports gemini."""
    pass


@pytest.mark.skip(reason="Gemini integration tests not yet ported to pytest")
def test_phase5_gemini_install_helloworld():
    """Phase 5 — install helloworld package via coding-aegis skill."""
    pass


@pytest.mark.skip(reason="Gemini integration tests not yet ported to pytest")
def test_phase6_gemini_uninstall_helloworld():
    """Phase 6 — uninstall helloworld package via coding-aegis skill."""
    pass


@pytest.mark.skip(reason="Gemini integration tests not yet ported to pytest")
def test_phase7_gemini_cleanup():
    """Phase 7 — unlink coding-aegis skill and remove test directory."""
    pass
