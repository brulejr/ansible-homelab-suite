#!/usr/bin/env python3
"""Merge two zigbee2mqtt database.db files (newline-delimited JSON).

Usage: merge_z2m_db.py OLD_DB NEW_DB OUT_DB

OLD_DB  database from the previous instance
NEW_DB  database from the current instance

Devices are matched by ieeeAddr and groups by groupID. When an entry exists
in both, the NEW_DB entry wins, since it reflects the most recent interview.
Entry ids are renumbered sequentially with the coordinator first.
"""
import json
import sys


def load(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def key(entry):
    if entry.get("type") == "Group":
        return ("group", entry["groupID"])
    return ("device", entry["ieeeAddr"])


def label(entry):
    if entry.get("type") == "Group":
        return f"group {entry['groupID']}"
    return f"{entry.get('type')} {entry['ieeeAddr']} ({entry.get('modelId', '?')})"


def main(old_path, new_path, out_path):
    old, new = load(old_path), load(new_path)

    coords = {e["ieeeAddr"] for e in old + new if e.get("type") == "Coordinator"}
    if len(coords) > 1:
        sys.exit(f"Coordinator ieeeAddr differs between databases: {sorted(coords)}")

    merged = {key(e): e for e in old}
    new_keys = {key(e) for e in new}
    for e in new:
        merged[key(e)] = e

    entries = sorted(merged.values(), key=lambda e: e.get("type") != "Coordinator")
    for i, e in enumerate(entries, start=1):
        e["id"] = i

    with open(out_path, "w") as f:
        for e in entries:
            f.write(json.dumps(e, separators=(",", ":")) + "\n")

    old_keys = {key(e) for e in old}
    print(f"old: {len(old)} entries, new: {len(new)} entries, merged: {len(entries)} entries")
    for e in entries:
        k = key(e)
        if e.get("type") == "Coordinator":
            source = "coordinator"
        elif k in old_keys and k in new_keys:
            source = "both (new kept)"
        elif k in new_keys:
            source = "new only"
        else:
            source = "old only"
        print(f"  {e['id']:3d}  {source:16s} {label(e)}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
