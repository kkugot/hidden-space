# Changelog

## 1.3.0 · 2026-09-12

- Remove the reveal-all override; the Show Spaces checklist is the only visibility setting.
- Clear the retired override preference while preserving saved hidden Space IDs.
- Verify restart recovery from a hidden active Space with Continue where you left off on and off.

- Rename the visibility menus to Show Spaces; keep the eye icon only in the + menu.

## 1.2.0 · 2026-09-12

- Unify menu actions into Show/Hide Spaces with checked meaning visible.
- Place the context submenu between Create Space and Share Space; keep it in the + menu too.
- Show each Space’s emoji or SVG icon alongside its name.
- Match the checklist in Sine settings to the visible/hidden menu convention.
- Fix native XUL menu items appearing disabled when the attribute contained false.

## 1.1.1 · 2026-09-12

- Add Zen’s native eye icon to Show hidden Space in the + menu.

## 1.1.0 · 2026-09-12

- Replace the ID field in Sine settings with a live checklist of Space names.
- Add Hide this Space on this device to the Space context menu.
- Add Show hidden Space to the + menu to restore and open one Space.
- Verify the custom-mod JavaScript permission and actual Sine loading path.

## 1.0.0 · 2026-09-12

- Select hidden Spaces from a native context submenu, separately for each device.
- Hide Space icons and native menu entries; skip hidden Spaces during navigation.
- Reveal selections without clearing them and always retain one visible Space.
- Support Sine live unload and local development symlink installation.
