# Hidden Space

Dependency-free Zen Sine mod. No build step.

- Keep author Kostiantyn Kugot and repository kkugot/hidden-space.
- Never mutate Space records, tabs, or sync data. Never filter Zen's getWorkspaces().
- Settings are profile-local. Keep custom preferences opted out of Firefox preference sync.
- Keep at least one visible Space. Restore hidden Spaces through the Show Spaces checklist.
- Restore navigation methods, styles, menus, and observers on unload.
- Check against installed Zen source when changing selectors or navigation wrappers.
- The settings script is space-picker.uc.js, loaded only in about:preferences.
- Run node --check space-picker.uc.js, node --check hidden-space.uc.js and node --test tests/hidden-space.test.cjs.
- Run browser checks in an isolated profile, never create test Spaces in the user's profile.
- Update version and release notes for user-visible changes.
