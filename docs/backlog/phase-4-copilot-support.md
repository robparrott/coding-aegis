# Phase 4: Copilot Support

**Status**: blocked | **ID**: `coding-aegis-9m0`

Blocked: corporate proxy/firewall intercepts HTTPS to api.individual.githubcopilot.com (HTTP 403). Spike (9m0.1) and all downstream tasks cannot proceed until network access is resolved. To unblock: run from a network without the proxy, or configure HTTPS_PROXY bypass for githubcopilot.com. Auth via COPILOT_GITHUB_TOKEN or copilot login once network is clear.

## Tasks

- [ ] `coding-aegis-9m0.1` Spike: verify Copilot CLI env vars, skill path, AGENTS.md, rules
- [ ] `coding-aegis-9m0.2` Add Copilot detection signals to detect_tool.py
- [ ] `coding-aegis-9m0.3` Fix TOOL_PATHS[copilot] and install/uninstall routing
- [ ] `coding-aegis-9m0.4` Write docs/test/test-copilot.md test spec
- [ ] `coding-aegis-9m0.5` Write tests/integration/test_copilot.py
- [ ] `coding-aegis-9m0.6` Update docs: feature-comparison, spec-tool-detection, TEST.md

**Progress**: 0/6 tasks complete
