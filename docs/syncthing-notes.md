# Syncthing notes

Generic gotchas from running Syncthing between a Mac and a Windows PC, roughly in order of how much time each one cost.

---

## Folder paths can't be changed after creation

A folder's local path is fixed once the folder exists. To move it, **remove** the folder in Syncthing (this doesn't delete files) and **re-add** it at the new path. Plan where the folder will live before you accept it.

## Environment variables are taken literally

Typing `%USERPROFILE%\Projects\workspace` as a folder path makes Syncthing create a folder actually named `%USERPROFILE%`. **Always type full paths**, for example `C:\Users\<you>\Projects\workspace`.

## Accept the other device's invitation, don't create the folder by hand

Every shared folder has a **Folder ID** that must match on both devices. Adding a folder by hand generates a random ID, which then won't pair with the other side. Instead: share the folder from the device that already has it, wait for the "wants to share folder" prompt on the other device, click **Add**, and set the local path there. The IDs then match automatically.

## Characters that Windows forbids in filenames break sync

A file named with `?` (or `< > : " | *`, or ending in a dot or space) syncs fine between Macs but **can't be created on Windows**. Syncthing reports it as a failed item, and the folder never reaches *Up to Date*. Rename those files on the Mac. Check *Failed Items* in the Windows web UI after the first sync.

## Folders can arrive read-only from Windows

Windows has no Unix permission bits, so permissions coming *from* the Windows side can leave folders on the Mac at mode `0555` (owner can't write). Tools then fail with "permission denied", sometimes silently.

- Quick fix on the Mac: `find "<folder>" -type d -not -path "*/.stfolder*" -exec chmod u+w {} +`
- Lasting fix: in Syncthing, open the folder → **Edit → Advanced → Ignore Permissions**, and turn it on **on both devices**.
- Until then, any script that writes into the folder should re-add the write bit before writing.

## A sleeping PC pauses sync

Syncthing only syncs while both devices are awake and running it. A PC set to sleep, or a laptop with its lid closed, means changes wait. If the two sides must stay current, disable sleep on the always-on machine.

## Syncthing only runs for the account it was installed under

A per-user (non-admin) Windows install starts Syncthing when **that** user signs in, and stops it when they sign out. If that account isn't signed in, nothing syncs, and nothing warns you. Install it under an account that stays signed in, or as a service, and look at **Last seen** for each device on both web UIs now and then.

## Creating folders at the drive root may need admin

A path such as `C:\Sync` may require administrator rights to create. A folder inside your own profile avoids that.

## Turn on file versioning

For any folder that holds memory or notes: **Edit → File Versioning → Simple File Versioning**, keep 5. Every overwritten or deleted file is kept in `.stversions/` on the receiving side. It's a cheap undo for sync mistakes.

## Ignore machine-specific files

Add an ignore pattern for anything that stores absolute paths or is machine-only (search indexes, caches, `node_modules`, large media), for example:

```
node_modules
.DS_Store
*.mp4
path/to/search-index.json
```

Rebuild those per machine instead of syncing them.

## Useful defaults

- Web UI: `http://127.0.0.1:8384` on each machine.
- On the same network, devices can find each other through **nearby devices** discovery, so you don't have to copy the long device ID.
- Conflict copies are named `<name>.sync-conflict-<date>-<time>-<device>.<ext>`. `memory-reconcile.py` handles them in the memory folder, and elsewhere you resolve them by hand.
