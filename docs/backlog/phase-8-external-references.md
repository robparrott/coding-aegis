# Phase 8: External Package References

**Status**: Not started

## Tasks

29. Extend pkg.yaml schema with optional `source` field
30. Update CI validation for source field schema validation
31. Implement external fetch in coding-aegis skill (GitHub archive download + shallow clone fallback)
32. Artifact validation for fetched external content
33. Create example external package pointer in `pkgs/optional/`
34. Update docs (AGENTS.md, README.md, package-format.md, tier-system.md)

## Dependencies

- Phase 1 (Foundation) — `pkgs/` directory structure must exist
- Phase 2 (coding-aegis) — skill must have install capability before external fetch can be added
- Phase 7 (CI) — CI validation must be in place to extend

## Sequencing Notes

Tasks 29 and 34 are documentation/schema-only and can proceed independently.
Tasks 30-32 require the coding-aegis skill to have basic install working (Phase 2).
Task 33 can be done once the schema is finalized (after task 29).
