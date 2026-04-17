# pytest integration framework for coding-aegis e2e tests

**Status**: open | **ID**: `coding-aegis-97z`

## Tasks

- [x] `coding-aegis-97z.1` QA Architect: review bash harness and write pytest proposal
- [x] `coding-aegis-97z.10` Upgrade Gemini model to gemini-3-flash and re-run full pytest suite
- [ ] `coding-aegis-97z.11` Retire bash test scripts: confirm pytest coverage, delete bash harness scripts, update TEST.md
- [ ] `coding-aegis-97z.12` Defer Gemini testing: mark quota-blocked phases in docs and close/defer blocked tasks
- [ ] `coding-aegis-97z.13` Revive Gemini testing when paid quota or quota-reset workflow is available
- [ ] `coding-aegis-97z.14` Integrate qa-architect-proposal.md into test docs and move to architecture/
- [ ] `coding-aegis-97z.15` Rationalise testing-spec.md: decide merge vs keep-separate and execute
- [x] `coding-aegis-97z.2` pytest infra: harness.py, conftest.py, CLIResult, run_cli
- [x] `coding-aegis-97z.3` pytest Claude: TestClaudeJourney class, all 7 phases, passing
- [x] `coding-aegis-97z.4` pytest Codex: port TestCodexJourney, all 7 phases @Rob Parrott
- [ ] `coding-aegis-97z.5` pytest Gemini: port TestGeminiJourney, handle quota as skip not fail
- [x] `coding-aegis-97z.6` pytest Cursor: implement TestCursorJourney when CLI available
- [ ] `coding-aegis-97z.7` pytest CI: add GitHub Actions job, JUnit XML output
- [ ] `coding-aegis-97z.8` Add requirements-dev.txt with pytest, pytest-html
- [x] `coding-aegis-97z.9` pytest Gemini: port TestGeminiJourney from bash test script @Rob Parrott

**Progress**: 7/15 tasks complete
