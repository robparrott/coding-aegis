# Implement deterministic CLI scripts for coding-aegis skill (AD-16)

**Status**: open | **ID**: `coding-aegis-e5x`

Replace aegis-catalog.py with dedicated per-command scripts that output final markdown and perform file I/O directly. See docs/architecture/AD-16-deterministic-skill-cli.md and docs/architecture/deterministic-cli-spec.md.

## Tasks

- [ ] `coding-aegis-e5x.1` Create aegis_lib.py shared library
- [ ] `coding-aegis-e5x.10` Delete aegis-catalog.py
- [ ] `coding-aegis-e5x.2` Create aegis-list.py
- [ ] `coding-aegis-e5x.3` Create aegis-show.py
- [ ] `coding-aegis-e5x.4` Create aegis-status.py
- [ ] `coding-aegis-e5x.5` Create aegis-install.py
- [ ] `coding-aegis-e5x.6` Create aegis-uninstall.py
- [ ] `coding-aegis-e5x.7` Rewrite SKILL.md as trivial dispatcher
- [ ] `coding-aegis-e5x.8` Create tests/test-cli-install.sh
- [ ] `coding-aegis-e5x.9` Create tests/test_aegis_lib.py

**Progress**: 0/10 tasks complete
