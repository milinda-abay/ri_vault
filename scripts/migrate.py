#!/usr/bin/env python3
"""Migrate the curated "why" notes from obsidian_life into ri_vault/curated/.

Strips the YAML frontmatter (the sync-block: type/project/updated/verified/
source_commit/status — the reconciliation tax we removed) and copies the body
verbatim. Maps the four obsidian Projects/Areas trees onto curated/.

Body-embedded "as of SHA X" references and internal [[...]] links are left
intact: the new system navigates via the graph (/query), not by SHA or
Obsidian link resolution, so they read as inert references, not broken links.
Idempotent — re-running overwrites with the same body.
"""
import os
import re

SRC = "/home/mjaby/Projects/obsidian_life"
DST_ROOT = "/home/mjaby/Projects/ri_vault/curated"

# obsidian source tree  ->  ri_vault curated/ subfolder
MAP = {
    "Projects/Databricks": "databricks",
    "Projects/RI iLab": "ri_ilab",
    "Projects/RI PBI Production": "ri_pbi_production",
    "Areas/Computing": "computing",
}

FRONTMATTER = re.compile(r"^---\n.*?\n---\n", re.DOTALL)


def strip_frontmatter(text):
    return FRONTMATTER.sub("", text, count=1)


def main():
    migrated = 0
    for src_sub, dst_sub in MAP.items():
        src_dir = os.path.join(SRC, src_sub)
        dst_dir = os.path.join(DST_ROOT, dst_sub)
        for root, _dirs, files in os.walk(src_dir):
            for name in files:
                if not name.endswith(".md"):
                    continue
                sp = os.path.join(root, name)
                rel = os.path.relpath(sp, src_dir)
                dp = os.path.join(dst_dir, rel)
                os.makedirs(os.path.dirname(dp), exist_ok=True)
                with open(sp, encoding="utf-8") as fh:
                    body = strip_frontmatter(fh.read())
                body = body.lstrip("\n")  # drop blank lines left behind by the strip
                with open(dp, "w", encoding="utf-8") as fh:
                    fh.write(body)
                migrated += 1
                print(f"migrated {src_sub}/{rel}")
    print(f"\nmigrated {migrated} notes")


if __name__ == "__main__":
    main()
