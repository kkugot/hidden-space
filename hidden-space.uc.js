// ==UserScript==
// @name           Hidden Space
// @author         Kostiantyn Kugot
// @version        1.2.0
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
  let manager, originalChange, originalShortcut, change, shortcut, menu, style, context, restoreMenu;
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
    if (event.target.localName !== 'menupopup' || event.target.parentNode !== event.currentTarget) return;
    const popup = event.target;
    popup.replaceChildren();
    const spaces = manager.getWorkspaces();
    const visibleIds = new Set(visible().map(space => space.uuid));
    for (const space of spaces) {
      const item = document.createXULElement('menuitem');
      item.setAttribute('type', 'checkbox');
      const svg = space.icon?.endsWith('.svg');
      item.setAttribute('label', `${space.icon && !svg ? space.icon + '  ' : ''}${space.name}`);
      if (svg) item.setAttribute('image', space.icon);
      if (visibleIds.has(space.uuid)) item.setAttribute('checked', 'true');
      // XUL treats a present disabled attribute as disabled, even with value "false".
      item.disabled = visibleIds.has(space.uuid) && visibleIds.size <= 1;
      item.addEventListener('command', () => {
        const shown = new Set(visible().map(s => s.uuid));
        if (shown.has(space.uuid)) {
          if (shown.size <= 1) return;
          shown.delete(space.uuid);
        } else shown.add(space.uuid);
        Services.prefs.setStringPref(PREF, manager.getWorkspaces().filter(s => !shown.has(s.uuid)).map(s => s.uuid).join(','));
        Services.prefs.setBoolPref(REVEAL, false);
      });
      popup.appendChild(item);
    }
  }

  function createVisibilityMenu(id) {
    const element = document.createXULElement('menu');
    element.id = id;
    element.classList.add('menu-iconic');
    element.setAttribute('image', 'chrome://browser/skin/zen-icons/selectable/eye.svg');
    element.setAttribute('label', 'Show/Hide Spaces');
    element.appendChild(document.createXULElement('menupopup'));
    element.addEventListener('popupshowing', populate);
    return element;
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
    menu = createVisibilityMenu('hidden-space-menu');
    context.insertBefore(menu, document.getElementById('context_zenShareWorkspace'));
    restoreMenu = createVisibilityMenu('hidden-space-restore');
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
