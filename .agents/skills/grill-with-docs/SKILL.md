---
name: grill-with-docs
description: A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go.
disable-model-invocation: true
---

Run a `/grilling` session, using the `/domain-modeling` skill.

When the grilling reaches shared understanding and the domain artifacts (`CONTEXT.md` terms, `docs/adr/` ADRs) are written, record the decisions back to the issue:

1. Write the updated body to a temp file, then publish with `gh issue edit <number> --body-file <file>`. Don't pass `--body` inline — shell quoting breaks it.
2. Body structure: **What to build** (unchanged), **Design decisions** (one numbered line per resolved decision, in order), **Acceptance criteria** (original plus anything new the grilling surfaced), **Domain artifacts** (files created/changed), **Blocked by** (unchanged).
3. Verify with `gh issue view <number>`.

The issue number is the one named when the session started ("work on issue #15"); if none was given, ask.
