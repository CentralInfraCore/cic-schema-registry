"""registrylib — schema-registry-specific compiler extensions.

Implements the mechanism described in cic-primitives' proposals/schema-registry:
per-file versioned schemas (one directory per schema, one file per version),
resolved via an in-memory index (no committed catalog file), with a
compiler-enforced field-coverage rule replacing the old git-merge-based
inheritance guarantee.

This is deliberately separate from tools/schemalib (the older, bundle-release
oriented pipeline inherited from base-repo) — it does not replace it yet.
See tools/registrylib/coverage.py and tools/registrylib/paths.py.
"""
