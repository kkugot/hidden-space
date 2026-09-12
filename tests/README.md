# Runtime validation

`hidden-space.test.cjs` checks filtering, fallback behavior, immutable input, and navigation boundaries with Node's built-in test runner.

`zen-runtime.py` also requires Sine installed in that isolated profile and Hidden Space registered there with `scripts/install.py`. It enables custom-mod JavaScript only in the test profile. It uses Marionette to exercise the real Zen chrome APIs. It requires a dedicated temporary profile named `hidden-space-zen-test` under `/private/tmp`, and refuses to run against another profile. It creates Work and Personal test Spaces there. Never use a browsing profile.

On macOS:

```sh
mkdir -p /tmp/hidden-space-zen-test
printf 'user_pref("marionette.port", 2829);\n' > /tmp/hidden-space-zen-test/user.js
/Applications/Zen.app/Contents/MacOS/zen --headless --no-remote \
  --profile /tmp/hidden-space-zen-test --marionette --remote-allow-system-access
```

In another terminal:

```sh
python3 tests/zen-runtime.py
```

Validated on Zen 1.22b on 2026-09-12:

- The Sine settings checklist, checkbox actions, live Space changes, and last-visible protection.
- Both Show/Hide Spaces menus list all Spaces, toggle visibility, and protect the last visible Space. The context menu appears between Create and Share.
- Sine loads and unloads both scripts.
- Space icon hiding and reveal through computed styles.
- Space session records remain unchanged when the hide list changes.
- The local preference has Firefox Sync disabled.
- Next/previous navigation skips hidden Spaces.
- Direct switching cannot select a hidden Space.
- Turning reveal off moves away from a hidden active Space.
- The native submenu reflects the saved selection.
- A hide-all preference leaves the first Space visible.
- Unload removes the menu/style and restores native navigation.

The installer was also checked against a temporary Sine registry for the symlink target and disabled automatic updates.

These headless checks cover runtime behavior, not visual review of every toolbar layout. An end-to-end sync session between two physical Macs was not tested. Shared Essentials, search results, and other extensions are outside this mod's visual filter.
