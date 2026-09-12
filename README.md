# Hidden Space

Hide selected Zen Spaces on this device while keeping them synced.

Use work and home Macs with the same synced Spaces, then choose which ones each Mac shows. Hidden Space changes the browser UI. It never deletes, moves, or removes Spaces or tabs from sync.

## Use

1. Right-click a Space icon or its header.
2. Open **Hidden Space · This device**.
3. Check the Spaces to hide on this Mac.

Uncheck a Space to bring it back. **Show hidden Spaces** temporarily reveals the entire list without clearing your choices. The same reveal switch is available in Sine settings.

The last visible Space cannot be hidden through the menu. If a manually edited list hides everything, the first Space stays visible. Hiding the active Space switches to an available Space.

Hidden Spaces disappear from the Space icon strip and native Space menus. Next/previous Space navigation skips them. Direct shortcuts to a hidden Space stay in the current visible Space. Reveal hidden Spaces before opening one intentionally.

## Local settings

Selections are saved by Space ID in this Zen profile, so renaming a Space keeps its selection. Configure each machine separately. New synced Spaces appear until you hide them.

- `uc.hidden-space.ids`: comma-separated Space IDs, managed by the context menu.
- `uc.hidden-space.reveal`: reveal the selected hidden Spaces without clearing the list.

The mod explicitly opts these preferences out of Firefox preference sync. It does not alter Zen's Spaces Sync records. Copying a browser profile manually also copies its local preferences.

This is visual filtering, not a privacy boundary. Tabs still exist locally and remain synced. Search, history, synced-tab lists, and other extensions can still expose them. Shared Essentials remain available.

## Install with Sine

Add `kkugot/hidden-space` through Sine's custom repository installation and enable the mod's JavaScript when prompted. Requires Sine with chrome script support. Developed and runtime-tested with Zen 1.22b.

### Local development

From this checkout, register a symlink in an existing Sine profile:

```sh
python3 scripts/install.py "/path/to/Zen/profile"
```

The installer backs up `chrome/sine-mods/mods.json`, registers the mod, and disables automatic updates for the symlink. It refuses to overwrite an existing mod directory or a link to a different checkout. Restart Zen after installation. No Spaces are selected automatically.

To disable, turn off Hidden Space in Sine. Disabling restores the controls and native navigation immediately. To remove the development link manually, remove only the `hidden-space` symlink and its registry entry, keeping the checkout.

## Development

No dependencies or build step. Sine loads `hidden-space.uc.js` directly. The script owns its stylesheet, menu, preference observers, and two navigation wrappers; unloading restores them. It does not filter `getWorkspaces()`, because Zen uses that list for storage and sync.

```sh
node --check hidden-space.uc.js
node --test tests/hidden-space.test.cjs
```

See [runtime validation](tests/README.md) for browser checks and limits.

Author: Kostiantyn Kugot. [MIT license](LICENSE).
