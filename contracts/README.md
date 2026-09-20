# Contracts — the join layer

The producer→consumer schema bindings that were the aspirational gap in
`obsidian_life` (its `Projects/Databricks/Contracts/` held only a `.gitkeep`).

A **contract** states, for one Databricks table, **who writes it, who reads it,
on what key, and in what layer** — the cross-repo knowledge that lives *between*
`ri_ilab` (writes), Databricks (the medallion), and `ri_pbi_production` (reads).

## How these are derived (and the honesty rule)

Contracts are *derived*, not hand-authored prose. The intended source is the live
catalog + graph edges:
- **live** (work laptop): `refresh --live` crawls the catalog and the graph, and
  emits a contract per producer→consumer binding it can see.
- **snapshot** (this machine): the bindings below are seeded from the documented
  knowledge (the curated `databricks/` notes), so they are **last-known, not live**.

The `mode:` line in every contract says which. On the home machine `mode: snapshot`
is the truth — these are the documented bindings, refreshed live on the work laptop.

## Contract shape

```
producer  : the repo / job that writes the table
consumer  : the repo / report that reads it
binding   : catalog.schema.table  (the FQN — the canonical join key)
key       : the column the consumer joins on
layer     : bronze | silver | serving | standalone
mode      : live | snapshot
```

The canonical join key is the **Databricks FQN** (`catalog.schema.table`): a table
named in code and in the catalog resolves to one node, not two. This is the
`merge-graphs` dedup gap closed at the contract layer.
