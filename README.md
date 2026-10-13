# agent-memory-sync

Keep an AI assistant's memory folder identical on a Mac and a Windows PC, with no drift, no manual copying and no lost entries.

---

## What it is

A small, file-level pattern plus one script:

1. The **real** memory folder lives inside a workspace that is already synced between the two machines (for example `<workspace>/.memory-sync/`).
2. On each machine, the assistant's own memory path is turned into a **pointer** to that folder: a symlink on macOS, a directory junction on Windows. The assistant reads and writes as usual, without knowing the files are shared.
3. **Syncthing** keeps the workspace in step between the machines, with *simple file versioning* as an undo buffer.
4. A **daily reconcile job** (`memory-reconcile.py`, plain Python, no AI, zero tokens) cleans up the conflict copies Syncthing creates when both machines change the same file:
   - `MEMORY.md` (the index): **union-merge**. Lines that exist only in the conflict copy are appended, so no entry is lost.
   - Any other file: the **newer** copy stays in place and the older one is archived.
   - Losers go to a sibling `.memory-conflicts/` folder with a log. **Nothing is ever deleted.**

It was built for Claude Code's per-project memory folder (`~/.claude/projects/<project-slug>/memory`), but works for any assistant that keeps memory as plain files in a folder.

## The problem it solves

Assistants keep memory per machine. Use one assistant on two computers and you soon have two diverging memories. The usual workarounds are copying folders by hand (forgotten), syncing the assistant's whole config folder (it holds machine-specific state and absolute paths), or a cloud drive (silent overwrites). With a pointer to one synced folder, both machines share the same memory. The reconcile job deals with the one weak spot of file sync: conflicting edits.

## Stack

- macOS + Windows (any pair of machines works; the docs cover these two)
- [Syncthing](https://syncthing.net) for peer-to-peer folder sync
- `ln -s` (macOS) and `mklink /J` (Windows, no admin needed)
- Python 3 standard library only
- launchd on macOS for the daily run

## What's in the repo

| Path | What it is |
|---|---|
| `memory-reconcile.py` | The reconcile script. Folder = first argument, else `$MEMORY_DIR`, else `~/workspace/.memory-sync` |
| `launchd/com.example.memory-reconcile.plist` | launchd template, daily at 03:30, with placeholder paths |
| `docs/setup-mac.md` | Move memory into the synced folder, create the symlink, install the job |
| `docs/setup-windows.md` | Create the directory junction (and an optional Task Scheduler alternative) |
| `docs/syncthing-notes.md` | The Syncthing gotchas that cost the most time |

## Setup in brief

1. Sync a workspace folder between both machines with Syncthing, and turn on **simple file versioning** (keep 5) for it.
2. **Mac:** move the existing memory files into `<workspace>/.memory-sync/` and replace the assistant's memory folder with a symlink to it (`docs/setup-mac.md`).
3. **Windows:** once `.memory-sync` has arrived, rename the assistant's memory folder and create a junction in its place (`docs/setup-windows.md`).
4. Install the reconcile job on **one** machine only (the one that's on most nights).
5. Restart the assistant on both machines and check that a memory written on one appears on the other.

Try the script by hand first:

```bash
MEMORY_DIR="$HOME/path/to/workspace/.memory-sync" python3 memory-reconcile.py
# or
python3 memory-reconcile.py "$HOME/path/to/workspace/.memory-sync"
```

It prints nothing. Look in `<workspace>/.memory-conflicts/reconcile.log`, which only gets entries when there was something to do.

## Limits

- **Top level only.** The script reconciles conflict files directly inside the memory folder, not in subfolders.
- **The index merge is line-based.** Union merge suits an index of one-line entries. Two edits to the *same* line produce both versions, and you remove the stale one by hand.
- **"Newer wins" goes by file modification time.** Clocks that are badly out of sync on the two machines will pick the wrong winner. Nothing is lost, though, because the loser is archived.
- **Up to a day of conflict files.** Until the job runs, the assistant may see `*.sync-conflict-*` files in its memory folder. They're harmless, but they're visible.
- **Run it on one machine.** Two machines reconciling at the same moment can create fresh conflicts.
- **Sync only works while both machines are awake and Syncthing is running.** See `docs/syncthing-notes.md`.
- **Machine-specific files stay out.** Don't put anything that stores absolute paths (search indexes, caches) in the shared folder.

---

Built with Claude Code.
