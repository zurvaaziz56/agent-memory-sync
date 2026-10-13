# Setup: macOS

Placeholders used below:

| Placeholder | Meaning | Example |
|---|---|---|
| `<workspace>` | The folder Syncthing already syncs between both machines | `~/Projects/workspace` |
| `<project-slug>` | The assistant's folder name for this workspace | for Claude Code, the workspace's absolute path with `/` and spaces turned into `-`, e.g. `-Users-<you>-Projects-workspace` |

For Claude Code, the per-project memory folder is `~/.claude/projects/<project-slug>/memory`. Run `ls ~/.claude/projects/` to find the slug.

---

## 1. Quit the assistant and take a snapshot

```bash
MEM="$HOME/.claude/projects/<project-slug>/memory"
cp -a "$MEM" "$HOME/.claude/memory-backup-$(date +%F)"
```

## 2. Move the memory into the synced workspace

```bash
mkdir -p "<workspace>/.memory-sync"
cp -a "$MEM/." "<workspace>/.memory-sync/"
ls -la "<workspace>/.memory-sync"     # every memory file should be here
```

## 3. Replace the memory folder with a symlink

```bash
mv "$MEM" "$MEM.pre-symlink"
ln -s "<workspace>/.memory-sync" "$MEM"
ls -la "$(dirname "$MEM")"            # memory -> <workspace>/.memory-sync
```

Once you've confirmed the assistant works (step 6), you can remove `memory.pre-symlink`. The snapshot from step 1 is still there.

## 4. Install the reconcile script

```bash
mkdir -p ~/scripts
cp memory-reconcile.py ~/scripts/
chmod +x ~/scripts/memory-reconcile.py
python3 ~/scripts/memory-reconcile.py "<workspace>/.memory-sync"   # silent = fine
```

## 5. Schedule it with launchd (daily, 03:30)

```bash
cp launchd/com.example.memory-reconcile.plist ~/Library/LaunchAgents/
open -e ~/Library/LaunchAgents/com.example.memory-reconcile.plist
```

Replace each `/path/to/...` placeholder with a **full absolute path**, because launchd doesn't expand `~`. Get the Python path with `command -v python3`. Then load and test it:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.memory-reconcile.plist
launchctl kickstart -k gui/$(id -u)/com.example.memory-reconcile    # run once now
launchctl print gui/$(id -u)/com.example.memory-reconcile | grep -E "state|last exit"
```

To change the plist later, `launchctl bootout gui/$(id -u)/com.example.memory-reconcile` first, then bootstrap again.

## 6. Verify end to end

1. Start the assistant and ask it to save a test memory.
2. Confirm the file appears in `<workspace>/.memory-sync/` and, a few seconds later, on the other machine.
3. Delete the test memory.

## Troubleshooting

- **`Operation not permitted` in the launchd log:** macOS privacy controls block background processes from reading Desktop, Documents and Downloads. Grant the Python binary Full Disk Access (System Settings → Privacy & Security), or keep the workspace outside those folders.
- **The assistant sees an empty memory:** the symlink points at the wrong place (`ls -la` the parent folder), or the target folder is missing.
- **Write access suddenly fails on synced folders:** see `syncthing-notes.md` → "Folders arrive read-only".
