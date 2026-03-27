# Multi-tool repository support

**Status**: Not started

## Description

Resolve the open question in AD-11: how the coding-aegis skill handles repos used with multiple coding agent tools simultaneously. Covers detection, install scope, git hygiene, and drift prevention.

## Tasks

1. Evaluate candidate approaches (A through D in AD-11) against real team workflows
2. Prototype tool detection logic
3. Decide on git commit vs gitignore strategy for tool-specific directories
4. Update AD-11 with accepted decision
5. Implement in coding-aegis skill

## Dependencies

- AD-10 (modular guidance files) accepted
- AD-11 (multi-tool repos) needs resolution before skill implementation
