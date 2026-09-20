---
description: Query the unified knowledge graph (query/path/explain) — the read interface, not a note-dump.
---

The unified graph is `graphify-out/graph.json` (one graph across `ri_ilab` + `ri_pbi_production`).
The whole point is to **query the graph, not free-search notes**. Run one of:

- `graphify query "$ARGUMENTS" --graph graphify-out/graph.json`
  — BFS subgraph for a question. If the question names **two** things, prefer `path`.
- `graphify path "$A" "$B" --graph graphify-out/graph.json`
  — shortest path between two nodes (relationships).
- `graphify explain "$ARGUMENTS" --graph graphify-out/graph.json`
  — a single node + its neighbours (use for a one concept).
- `graphify god-nodes --graph graphify-out/graph.json`
  — the most-connected nodes (architectural hubs).

Match the graph's real node labels; if the answer is TRUNCATED, raise `--budget` or narrow with
a context filter. Report 0-hits honestly rather than inventing synonyms. For a broader architecture
review, read `graphify-out/GRAPH_REPORT.md` only when query/path/explain fall short.
