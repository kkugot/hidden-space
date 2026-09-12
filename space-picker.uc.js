// Hidden Space settings · Kostiantyn Kugot · 1.1.0
(() => {
  window.HiddenSpacePicker?.destroy();
  const PREF = 'uc.hidden-space.ids';
  const browserWindow = window.browsingContext.topChromeWindow || Services.wm.getMostRecentWindow('navigator:browser');
  let host, signature;
  const selectedIds = () => new Set(Services.prefs.getStringPref(PREF, '').split(',').map(id => id.trim()).filter(Boolean));

  function render() {
    const nextHost = document.getElementById('hidden-space-picker');
    if (!nextHost) return;
    const spaces = browserWindow.gZenWorkspaces?.getWorkspaces() || [];
    const selected = selectedIds();
    const nextSignature = JSON.stringify([spaces.map(s => [s.uuid, s.name]), [...selected]]);
    if (host === nextHost && signature === nextSignature) return;
    host = nextHost;
    signature = nextSignature;
    const focusedId = host.contains(document.activeElement) ? document.activeElement?.value : null;
    host.replaceChildren();
    const heading = document.createElementNS('http://www.w3.org/1999/xhtml', 'p');
    heading.textContent = 'Hide Spaces on this device';
    host.appendChild(heading);
    const remaining = spaces.filter(s => !selected.has(s.uuid)).length;
    for (const space of spaces) {
      const label = document.createElementNS('http://www.w3.org/1999/xhtml', 'label');
      label.style.cssText = 'display:flex;align-items:center;gap:8px;padding:6px 0;';
      const input = document.createElementNS('http://www.w3.org/1999/xhtml', 'input');
      input.type = 'checkbox';
      input.value = space.uuid;
      input.checked = selected.has(space.uuid);
      input.disabled = !input.checked && remaining <= 1;
      input.addEventListener('change', () => {
        const ids = selectedIds();
        if (input.checked) {
          const visible = browserWindow.gZenWorkspaces.getWorkspaces().filter(s => !ids.has(s.uuid));
          if (visible.length <= 1) { input.checked = false; render(); return; }
          ids.add(space.uuid);
        } else ids.delete(space.uuid);
        Services.prefs.setStringPref(PREF, [...ids].join(','));
      });
      label.append(input, document.createTextNode(space.name));
      host.appendChild(label);
      if (space.uuid === focusedId) input.focus();
    }
    if (!spaces.length) heading.textContent = 'No Spaces available in this window.';
  }

  const observer = { observe: render };
  const domObserver = new MutationObserver(render);
  domObserver.observe(document.documentElement, { childList: true, subtree: true });
  Services.prefs.addObserver(PREF, observer);
  browserWindow.addEventListener('ZenWorkspacesUIUpdate', render);
  function destroy() {
    domObserver.disconnect();
    Services.prefs.removeObserver(PREF, observer);
    browserWindow.removeEventListener('ZenWorkspacesUIUpdate', render);
    window.removeEventListener('unload', destroy);
    if (host?.isConnected) host.textContent = 'Enable Hidden Space JavaScript in Sine to choose Spaces here.';
    delete window.HiddenSpacePicker;
  }
  window.HiddenSpacePicker = { destroy };
  window.addEventListener('unload', destroy, { once: true });
  window.addUnloadListener?.(destroy);
  render();
})();
