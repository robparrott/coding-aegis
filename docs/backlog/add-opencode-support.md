# Add OpenCode support

**Status**: open | **ID**: `coding-aegis-yjy`

Add OpenCode to the testing matrix. Create test-opencode.md detail file, write test-opencode-skill-install.sh following the 7-phase plan, and add to the coverage matrix in testing-spec.md. Research OpenCode's skill/plugin mechanism to determine the correct install approach (marketplace, CLI, or file copy).

## Tasks

- [x] `coding-aegis-yjy.1` Add OPENCODE=1 detection to detect_tool.py @Rob Parrott
- [x] `coding-aegis-yjy.2` Update aegis-install.py for OpenCode: AGENTS.md + .opencode/skills/ @Rob Parrott
- [x] `coding-aegis-yjy.3` Update aegis-uninstall.py for OpenCode: scan .opencode/skills/ @Rob Parrott
- [x] `coding-aegis-yjy.4` OpenCode bootstrap: install coding-aegis skill to ~/.config/opencode/skills/
- [ ] `coding-aegis-yjy.5` pytest OpenCode: implement TestOpenCodeJourney
- [ ] `coding-aegis-yjy.6` Document OpenCode support: docs/test/test-opencode.md + ADR

**Progress**: 4/6 tasks complete
