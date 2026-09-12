# Sine Store submission

Ready for submission. No store issue has been submitted.

[Open the prefilled Sine submission](https://github.com/sineorg/store/issues/new?template=add-theme.yml&title=%5Badd-theme%5D%3A+Hidden+Space&homepage=https%3A%2F%2Fgithub.com%2Fkkugot%2Fhidden-space)

## Required submission

Sine's current [Add Theme form](https://github.com/sineorg/store/blob/main/.github/ISSUE_TEMPLATE/add-theme.yml) asks for one field, **Theme Homepage**:

```text
https://github.com/kkugot/hidden-space
```

Issue title: `[add-theme]: Hidden Space`

The [submission workflow](https://github.com/sineorg/store/blob/main/.github/workflows/add-theme.yml) reads `theme.json` from the repository, checks for an existing ID, and opens a store pull request for maintainer review. Requirements checked on 2026-09-12. Screenshots and a preview image improve the listing; the issue form does not impose an image size.

## Package

- Name: Hidden Space
- ID: `hidden-space`
- Author: Kostiantyn Kugot
- Version: 1.3.0
- Description: Hide selected Zen Spaces on this device while keeping them synced.
- License: MIT
- Browser: Zen
- AI disclosure: `full`
- Metadata: [theme.json](theme.json)
- Preview: [marketplace-preview.png](marketplace-preview.png), 640 × 330 PNG
- Screenshots: [plus menu](screenshots/plus-menu.png), [context menu](screenshots/context-menu.png), [settings](screenshots/settings.png)
- README: [public README](https://raw.githubusercontent.com/kkugot/hidden-space/main/README.md)
- Preview URL: [public preview](https://raw.githubusercontent.com/kkugot/hidden-space/main/marketplace-preview.png)

## Reviewer notes

Hidden Space visually filters synced Spaces independently in each profile. Both menus use native checkboxes and Space icons. The last visible Space is protected, and startup falls back to a visible Space when necessary.

Two chrome scripts are registered: `hidden-space.uc.js` runs in browser windows; `space-picker.uc.js` runs in `about:preferences`. The browser script owns its stylesheet and unload cleanup. There are no dependencies, external network requests, content scripts, or telemetry. Space records, tab contents, and sync data are never modified.

JavaScript is required. Custom-repository installs need Sine's unofficial-JavaScript permission; store-origin installs use Sine's normal store permission path. This repository does not modify Sine.

## Validation

Syntax checks and the Node policy tests pass. The browser integration suite and real startup restart checks passed on Zen 1.22.1b, including Continue where you left off both on and off. Screenshots were captured from real macOS Zen menus in a separate profile with sample Spaces; they were not generated or redrawn.

Cross-device sync and other operating systems have not been tested. This is a visual filter, not a privacy boundary. See [runtime validation](tests/README.md).
