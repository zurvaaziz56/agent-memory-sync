#!/usr/bin/env python3
"""
memory-reconcile.py: merge Syncthing conflict files in an AI assistant's memory folder.

Meant to run once a day from a scheduler (launchd on macOS, or Task Scheduler on
Windows) on ONE machine. No AI involved, zero tokens. NEVER deletes data:
  - MEMORY.md conflicts  -> union-merge lines into MEMORY.md, archive the conflict copy
  - any other file       -> keep the NEWER version in place, archive the older one
Archive + log live in a sibling .memory-conflicts/ folder (outside the memory
folder, so the assistant never mistakes them for memories). Silent when there is
nothing to do.

Usage: memory-reconcile.py [memory_folder]
       (default = $MEMORY_DIR, or ~/workspace/.memory-sync if MEMORY_DIR is unset)
"""
import os, re, shutil, sys, time
from pathlib import Path

DEFAULT_MEM = Path(os.environ.get("MEMORY_DIR", "~/workspace/.memory-sync")).expanduser()
MEM = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else DEFAULT_MEM
OUT = MEM.parent / ".memory-conflicts"
LOG = OUT / "reconcile.log"

# Syncthing names conflict copies <name>.sync-conflict-<YYYYMMDD>-<HHMMSS>-<device>.<ext>
CONFLICT = re.compile(r"^(?P<base>.+?)\.sync-conflict-(?P<stamp>\d{8}-\d{6})-(?P<dev>[A-Z0-9]+)(?P<ext>\.[^.]+)$")

def log(msg):
    OUT.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {msg}\n")

def merge_index(main, conflict):
    seen = {l.strip() for l in main.read_text(encoding="utf-8").splitlines()}
    added = [l for l in conflict.read_text(encoding="utf-8").splitlines() if l.strip() and l.strip() not in seen]
    if added:
        main.write_text(main.read_text(encoding="utf-8").rstrip("\n") + "\n" + "\n".join(added) + "\n", encoding="utf-8")
    return len(added)

def main():
    if not MEM.is_dir():
        log(f"ERROR memory folder missing: {MEM}"); return 1
    conflicts = sorted(p for p in MEM.iterdir() if p.is_file() and CONFLICT.match(p.name))
    if not conflicts:
        return 0
    OUT.mkdir(exist_ok=True)
    for c in conflicts:
        m = CONFLICT.match(c.name); base = MEM / f"{m['base']}{m['ext']}"; stamp = m["stamp"]
        if base.name == "MEMORY.md":
            added = merge_index(base, c) if base.exists() else 0
            if not base.exists(): shutil.copy2(c, base)
            shutil.move(str(c), OUT / c.name)
            log(f"MEMORY.md: merged {c.name} (+{added} lines), archived copy"); continue
        if not base.exists():
            shutil.move(str(c), base); log(f"{base.name}: main missing, promoted {c.name}"); continue
        if c.stat().st_mtime > base.stat().st_mtime:
            older = OUT / f"{base.stem}.older-{stamp}{base.suffix}"
            shutil.move(str(base), older); shutil.move(str(c), base)
            log(f"{base.name}: conflict newer -> promoted; previous archived as {older.name}")
        else:
            shutil.move(str(c), OUT / c.name)
            log(f"{base.name}: main newer -> kept; conflict archived as {c.name}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
