# AD-7: No dependency resolution

**Status**: Accepted

## Decision

Packages are standalone. If a package conceptually requires another, documentation says so — tooling does not enforce or resolve dependency chains.

## Rationale

Dependency resolution adds significant complexity for limited value at this stage. Packages should be self-contained. If a relationship exists, it is documented in the package description, not enforced by tooling.
