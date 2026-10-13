# Setup: Windows

A **directory junction** makes the assistant's memory path point at the synced folder. Unlike a symlink, a junction **doesn't need admin rights** or Developer Mode.

Placeholders used below:

| Placeholder | Meaning | Example |
|---|---|---|
| `<workspace>` | Full path of the synced workspace on this PC | `%USERPROFILE%\Projects\workspace` |
| `<project-slug>` | The assistant's folder name for this workspace | for Claude Code, the absolute path with `:`, `\` and spaces turned into `-`, e.g. `C--Users-<you>-Projects-workspace` |

For Claude Code, the per-project memory folder is `%USERPROFILE%\.claude\projects\<project-slug>\memory`. List `%USERPROFILE%\.claude\projects\` to find the slug. The folder appears after the assistant has been opened once in that workspace.

---

## 1. Wait for the synced folder

Don't start until `<workspace>\.memory-sync` has **fully arrived** from the other machine (Syncthing shows the folder as *Up to Date*), and quit the assistant.

## 2. Create the junction (PowerShell, no admin)

```powershell
$m = "$env:USERPROFILE\.claude\projects\<project-slug>\memory"
if (Test-Path $m) { Rename-Item $m "$m.pre-junction" }
cmd /c mklink /J "$m" "<workspace>\.memory-sync"
Get-ChildItem $m | Measure-Object | Select-Object Count
```

The count should match the number of files in `.memory-sync` on the other machine. Use full paths throughout (see `syncthing-notes.md` on environment variables).

## 3. Keep anything only this PC knew

If `memory.pre-junction` holds memories that the shared folder doesn't, copy the ones worth keeping into `<workspace>\.memory-sync\` and add their lines to `MEMORY.md`. Once you're satisfied, the `.pre-junction` folder can go.

## 4. Restart and verify

Start the assistant, ask it to save a test memory, confirm it appears on the other machine, then delete it.

---

## Optional: run the reconcile job on Windows instead

Only do this if the PC, not the Mac, is the machine that's on most nights. Run the job on **one** machine only. This variant hasn't been tested as much as the launchd path.

```powershell
schtasks /Create /SC DAILY /ST 03:30 /TN "memory-reconcile" `
  /TR "py -3 \"<full-path-to>\memory-reconcile.py\" \"<workspace>\.memory-sync\""
schtasks /Run /TN "memory-reconcile"
```

Check `<workspace>\.memory-conflicts\reconcile.log` after a run that had something to do.

## Notes

- A junction is just a pointer. To remove only the pointer, use `cmd /c rmdir "$m"` without `/S`. Avoid `Remove-Item -Recurse` on a junction: some PowerShell versions follow it and delete the target's contents. **Never** delete files *through* the junction when you mean to remove the pointer.
- Back up the target folder, not the junction. Some backup tools follow junctions and others skip them.
