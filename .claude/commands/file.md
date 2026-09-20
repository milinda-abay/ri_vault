---
description: Drain Inbox/ into curated "why" notes. Derivables become graph nodes, not duplicated notes.
---

Process every note in `Inbox/` (skip `README.md`) into `curated/`. If `$ARGUMENTS` names one
file, process only that.

The axiom this exists to enforce: **if a fact is derivable from code or the Databricks catalog,
it is linked to the graph, not duplicated as a note.**

For each item:
1. **Read it.** Understand what the content actually is.
2. **Decide derivable vs. why.**
   - If the content is *derivable* (a table, a schema, a row count, a job, a pipeline, a code
     structure) — it belongs **in the graph**, not as a note. Do not duplicate it. At most add a
     one-line link to the relevant graph node, or flag it for `/refresh`.
   - Only the **non-derivable "why"** — intent, decisions, gotchas, rationale, migration ladders,
     parity evidence the code *cannot* tell you — becomes a curated note.
3. **File it** under `curated/<project>/` (ri_ilab | ri_pbi_production | databricks | computing).
   Keep one idea per file; link to the parent overview; keep dates absolute (`2026-09-19`).
4. **Never write sync-block / SHA frontmatter** (`source_commit`, `verified`, `status`). The
   graph self-refreshes; those fields are meaningless here. That is the tax we removed.
5. **Move it out of Inbox** and report what you filed vs. what you dropped as derivable.
