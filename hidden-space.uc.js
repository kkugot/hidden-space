// ==UserScript==
// @name           Hidden Space
// @author         Kostiantyn Kugot
// @version        1.1.1
// @description    Hide selected Zen Spaces on this device.
// @include        chrome://browser/content/browser.xhtml
// ==/UserScript==

(() => {
  const PREF = 'uc.hidden-space.ids';
  const REVEAL = 'uc.hidden-space.reveal';
  const parseIds = raw => new Set(raw.split(',').map(id => id.trim()).filter(Boolean));

  function visibleSpaces(spaces, raw, reveal = false) {
    const hidden = parseIds(raw);
    const visible = reveal ? spaces : spaces.filter(space => !hidden.has(space.uuid));
    // A stale or manually edited list must never leave the browser without a Space.
    return visible.length ? visible : spaces.slice(0, 1);
  }

  function nextSpace(spaces, active, offset, wrap) {
    if (!spaces.length) return undefined;
    const index = spaces.findIndex(space => space.uuid === active);
    if (index < 0) return spaces[0];
    const target = index + offset;
    return spaces[wrap
      ? ((target % spaces.length) + spaces.length) % spaces.length
      : Math.max(0, Math.min(spaces.length - 1, target))];
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { visibleSpaces, nextSpace };
    return;
  }

  window.HiddenSpace?.destroy();
  let manager, originalChange, originalShortcut, change, shortcut, menu, style, action, context, restoreMenu;
  let contextSpaceId;
  let stopped = false;
  let timer;
  const ids = () => Services.prefs.getStringPref(PREF, '');
  const revealed = () => Services.prefs.getBoolPref(REVEAL, false);
  const visible = () => visibleSpaces(manager.getWorkspaces(), ids(), revealed());
  const report = error => console.error('[Hidden Space]', error);

  function refresh() {
    if (!manager || stopped) return;
    const spaces = manager.getWorkspaces();
    const allowed = visible();
    const allowedIds = new Set(allowed.map(space => space.uuid));
    const hidden = spaces.filter(space => !allowedIds.has(space.uuid));
    // Target only Space controls. Never change tabs, Space records, or session data.
    const selectors = hidden.flatMap(space => {
      const id = CSS.escape(space.uuid);
      return [
        `zen-workspace-icons toolbarbutton[zen-workspace-id="${id}"]`,
        `.zen-workspace-context-menu-item[zen-workspace-id="${id}"]`,
      ];
    });
    style.textContent = selectors.length ? `${selectors.join(',\n')} { display: none !important; }` : '';
    if (allowed.length && !allowedIds.has(manager.activeWorkspace)) {
      // Defer outside Zen's change listeners: awaiting a nested switch deadlocks Zen.
      void manager.changeWorkspace(allowed[0]).catch(report);
    }
  }

  function schedule() {
    if (stopped) return;
    clearTimeout(timer);
    timer = setTimeout(refresh, 0);
  }

  function populate(event) {
    if (event.target !== menu.querySelector(':scope > menupopup')) return;
    const popup = event.target;
    popup.replaceChildren();
    const selected = parseIds(ids());
    const spaces = manager.getWorkspaces();
    const remaining = spaces.filter(space => !selected.has(space.uuid)).length;
    for (const space of spaces) {
      const item = document.createXULElement('menuitem');
      item.setAttribute('type', 'checkbox');
      item.setAttribute('label', space.name);
      item.setAttribute('checked', selected.has(space.uuid));
      item.setAttribute('disabled', !selected.has(space.uuid) && remaining <= 1);
      item.addEventListener('command', () => {
        const current = parseIds(ids());
        if (current.has(space.uuid)) current.delete(space.uuid);
        else current.add(space.uuid);
        Services.prefs.setStringPref(PREF, [...current].join(','));
      });
      popup.appendChild(item);
    }
    popup.appendChild(document.createXULElement('menuseparator'));
    const reveal = document.createXULElement('menuitem');
    reveal.setAttribute('type', 'checkbox');
    reveal.setAttribute('label', 'Show hidden Spaces');
    reveal.setAttribute('checked', revealed());
    reveal.addEventListener('command', () => Services.prefs.setBoolPref(REVEAL, !revealed()));
    popup.appendChild(reveal);
  }

  function updateAction(event) {
    if (event.target !== context) return;
    const target = context.triggerNode || document.popupNode;
    contextSpaceId = target?.closest?.('[zen-workspace-id]')?.getAttribute('zen-workspace-id')
      || target?.closest?.('zen-workspace')?.id || manager.activeWorkspace;
    const hidden = parseIds(ids()).has(contextSpaceId);
    action.setAttribute('label', hidden ? 'Show this Space on this device' : 'Hide this Space on this device');
    action.disabled = !hidden && manager.getWorkspaces().filter(s => !parseIds(ids()).has(s.uuid)).length <= 1;
  }

  function toggleContextSpace() {
    const selected = parseIds(ids());
    if (selected.has(contextSpaceId)) selected.delete(contextSpaceId);
    else {
      if (manager.getWorkspaces().filter(s => !selected.has(s.uuid)).length <= 1) return;
      selected.add(contextSpaceId);
    }
    Services.prefs.setStringPref(PREF, [...selected].join(','));
  }

  function populateHidden(event) {
    if (event.target !== restoreMenu.querySelector(':scope > menupopup')) return;
    const popup = event.target;
    popup.replaceChildren();
    const selected = parseIds(ids());
    for (const space of manager.getWorkspaces().filter(s => selected.has(s.uuid))) {
      const item = document.createXULElement('menuitem');
      item.setAttribute('label', space.name);
      item.addEventListener('command', () => {
        const current = parseIds(ids());
        current.delete(space.uuid);
        Services.prefs.setStringPref(PREF, [...current].join(','));
        void manager.changeWorkspace(space).catch(report);
      });
      popup.appendChild(item);
    }
    if (!popup.children.length) {
      const empty = document.createXULElement('menuitem');
      empty.setAttribute('label', 'No hidden Spaces');
      empty.disabled = true;
      popup.appendChild(empty);
    }
  }

  function init() {
    if (stopped || manager) return;
    const candidate = window.gZenWorkspaces;
    context = document.getElementById('zenWorkspaceMoreActions');
    if (!candidate?.getWorkspaces || !context || !candidate.getWorkspaces().length) return;
    manager = candidate;
    originalChange = manager.changeWorkspace;
    originalShortcut = manager.changeWorkspaceShortcut;
    change = function (space, ...args) {
      const allowed = visible();
      if (space && !allowed.some(item => item.uuid === space.uuid)) {
        space = allowed.find(item => item.uuid === this.activeWorkspace) || allowed[0];
      }
      return originalChange.call(this, space, ...args);
    };
    shortcut = function (offset = 1, whileScrolling = false, disableWrap = false) {
      if (!ids() || revealed()) return originalShortcut.call(this, offset, whileScrolling, disableWrap);
      const target = nextSpace(visible(), this.activeWorkspace, offset, this.shouldWrapAroundNavigation && !disableWrap);
      return target ? this.changeWorkspace(target, { whileScrolling }) : Promise.resolve();
    };
    manager.changeWorkspace = change;
    manager.changeWorkspaceShortcut = shortcut;
    style = document.createElementNS('http://www.w3.org/1999/xhtml', 'style');
    style.id = 'hidden-space-style';
    document.documentElement.appendChild(style);
    menu = document.createXULElement('menu');
    menu.id = 'hidden-space-menu';
    menu.setAttribute('label', 'Hidden Space · This device');
    menu.appendChild(document.createXULElement('menupopup'));
    menu.addEventListener('popupshowing', populate);
    action = document.createXULElement('menuitem');
    action.id = 'hidden-space-toggle';
    action.setAttribute('label', 'Hide this Space on this device');
    action.addEventListener('command', toggleContextSpace);
    context.addEventListener('popupshowing', updateAction);
    context.append(action, menu);
    restoreMenu = document.createXULElement('menu');
    restoreMenu.id = 'hidden-space-restore';
    restoreMenu.classList.add('menu-iconic');
    restoreMenu.setAttribute('image', 'chrome://browser/skin/zen-icons/selectable/eye.svg');
    restoreMenu.setAttribute('label', 'Show hidden Space');
    restoreMenu.appendChild(document.createXULElement('menupopup'));
    restoreMenu.addEventListener('popupshowing', populateHidden);
    const createPopup = document.getElementById('zenCreateNewPopup');
    createPopup?.insertBefore(restoreMenu, createPopup.firstElementChild?.nextSibling);
    manager.addChangeListeners(schedule);
    refresh();
  }

  function onUpdate() { init(); schedule(); }
  const observer = { observe: schedule };
  function destroy() {
    stopped = true;
    clearTimeout(timer);
    Services.prefs.removeObserver(PREF, observer);
    Services.prefs.removeObserver(REVEAL, observer);
    window.removeEventListener('ZenWorkspacesUIUpdate', onUpdate);
    window.removeEventListener('AfterWorkspacesSessionRestore', onUpdate);
    window.removeEventListener('unload', destroy);
    if (manager) {
      manager.removeChangeListeners(schedule);
      if (manager.changeWorkspace === change) manager.changeWorkspace = originalChange;
      if (manager.changeWorkspaceShortcut === shortcut) manager.changeWorkspaceShortcut = originalShortcut;
    }
    context?.removeEventListener('popupshowing', updateAction);
    action?.remove();
    restoreMenu?.remove();
    menu?.remove();
    style?.remove();
    delete window.HiddenSpace;
  }

  // Firefox Sync uses these explicit allowlist flags for custom preferences.
  // Sine stores these settings in this profile's prefs, separate from Zen Spaces Sync.
  for (const pref of [PREF, REVEAL]) {
    Services.prefs.setBoolPref(`services.sync.prefs.sync.${pref}`, false);
    Services.prefs.setBoolPref(`services.sync.prefs.sync-seen.${pref}`, false);
  }
  Services.prefs.addObserver(PREF, observer);
  Services.prefs.addObserver(REVEAL, observer);
  window.addEventListener('ZenWorkspacesUIUpdate', onUpdate);
  window.addEventListener('AfterWorkspacesSessionRestore', onUpdate);
  window.addEventListener('unload', destroy, { once: true });
  window.HiddenSpace = { destroy };
  window.addUnloadListener?.(destroy);
  init();
})();
