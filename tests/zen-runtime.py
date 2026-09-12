"""Runtime checks for a dedicated headless Zen test profile on port 2829."""
import socket,json
from pathlib import Path
s=socket.create_connection(('127.0.0.1',2829));s.settimeout(40)
def recv():
 n=b''
 while not n.endswith(b':'): n+=s.recv(1)
 data=b''
 while len(data)<int(n[:-1]): data+=s.recv(int(n[:-1])-len(data))
 return json.loads(data)
recv(); counter=0
def call(name,args={}):
 global counter
 counter+=1
 data=json.dumps([0,counter,name,args]).encode();s.sendall(str(len(data)).encode()+b':'+data)
 response=recv()
 if response[2]: raise Exception(response[2])
 return response[3]
call('WebDriver:NewSession',{'capabilities':{'alwaysMatch':{'acceptInsecureCerts':True}}})
call('Marionette:SetContext',{'value':'chrome'})
def js(script):
 return call('WebDriver:ExecuteScript',{'script':script,'args':[],'newSandbox':False,'sandbox':'system'})
profile = js('return Services.dirsvc.get("ProfD", Ci.nsIFile).path;')['value']
assert Path(profile).name == 'hidden-space-zen-test' and str(Path(profile).resolve()).startswith('/private/tmp/'), 'Use the dedicated temporary test profile'
js("Services.prefs.clearUserPref('uc.hidden-space.ids'); Services.prefs.clearUserPref('uc.hidden-space.reveal');")
def asyncjs(script):
 return call('WebDriver:ExecuteAsyncScript',{'script':'const done = arguments[arguments.length - 1]; (async () => {'+script+'})().then(done, e => done({error:String(e),stack:e.stack}));','args':[],'newSandbox':False,'sandbox':'system','scriptTimeout':30000})
print(asyncjs('if (!gZenWorkspaces.getWorkspaces().some(s=>s.name === "Work")) { await gZenWorkspaces.createAndSaveWorkspace("Work"); await gZenWorkspaces.createAndSaveWorkspace("Personal"); } return gZenWorkspaces.getWorkspaces().map(s=>({uuid:s.uuid,name:s.name}));'))
print(asyncjs("Services.prefs.setBoolPref('sine.allow-unsafe-js', true); await ChromeUtils.importESModule('chrome://userscripts/content/core/manager.sys.mjs').default.rebuildMods(); return {loaded:!!window.HiddenSpace, menu:!!document.getElementById('hidden-space-menu')};"))
result = asyncjs('''
const manager = gZenWorkspaces;
const spaces = manager.getWorkspaces();
const work = spaces.find(s=>s.name === 'Work');
const personal = spaces.find(s=>s.name === 'Personal');
const before = JSON.stringify(manager.getWorkspacesForSessionStore());
Services.prefs.setStringPref('uc.hidden-space.ids', work.uuid);
await new Promise(r=>setTimeout(r,300));
const button = document.querySelector(`zen-workspace-icons toolbarbutton[zen-workspace-id="${work.uuid}"]`);
const results = {iconHidden:getComputedStyle(button).display === 'none', dataUntouched:before===JSON.stringify(manager.getWorkspacesForSessionStore()), local:Services.prefs.getBoolPref('services.sync.prefs.sync.uc.hidden-space.ids')===false};
await manager.changeWorkspace(spaces[0]);
await manager.changeWorkspaceShortcut(1);
results.skipsForward = manager.activeWorkspace === personal.uuid;
await manager.changeWorkspaceShortcut(-1);
results.skipsBackward = manager.activeWorkspace === spaces[0].uuid;
await manager.changeWorkspace(work);
results.directBlocked = manager.activeWorkspace !== work.uuid;
Services.prefs.setBoolPref('uc.hidden-space.reveal', true);
await new Promise(r=>setTimeout(r,100));
results.legacyRevealIgnored = getComputedStyle(document.querySelector(`zen-workspace-icons toolbarbutton[zen-workspace-id="${work.uuid}"]`)).display === 'none';
const popup = document.querySelector('#hidden-space-menu > menupopup');
popup.dispatchEvent(new Event('popupshowing', {bubbles:true}));
const workItem = [...popup.children].find(e=>e.getAttribute('label')==='Work');
if (!workItem) throw new Error(JSON.stringify({popup:popup.outerHTML,menus:document.querySelectorAll('#hidden-space-menu').length,spaces:manager.getWorkspaces().map(s=>s.name)}));
results.menuChecked = workItem.getAttribute('checked') !== 'true';
results.visibleEnabled = [...popup.children].find(e=>e.getAttribute('label')==='Personal').disabled === false;
Services.prefs.setStringPref('uc.hidden-space.ids', spaces.map(s=>s.uuid).join(','));
await new Promise(r=>setTimeout(r,300));
results.fallbackVisible = getComputedStyle(document.querySelector(`zen-workspace-icons toolbarbutton[zen-workspace-id="${spaces[0].uuid}"]`)).display !== 'none';
window.HiddenSpace.destroy();
results.unloaded = !document.getElementById('hidden-space-menu') && !document.getElementById('hidden-space-style');
await manager.changeWorkspace(work);
results.navigationRestored = manager.activeWorkspace === work.uuid;
return results;
''')['value']
settings = asyncjs('''
Services.prefs.setBoolPref('sine.allow-unsafe-js', true);
const sine = ChromeUtils.importESModule('chrome://userscripts/content/core/manager.sys.mjs').default;
await sine.rebuildMods();
const tab = gBrowser.addTrustedTab('about:preferences#sineMods');
gBrowser.selectedTab = tab;
await new Promise(r=>setTimeout(r,2500));
const doc = tab.linkedBrowser.contentDocument;
Services.prefs.setStringPref('uc.hidden-space.ids', '');
await new Promise(r=>setTimeout(r,100));
const checkboxes = doc?.querySelectorAll('#hidden-space-picker input[type="checkbox"]');
const result = {settingsList:checkboxes?.length === gZenWorkspaces.getWorkspaces().length,
  unifiedMenus:!document.getElementById('hidden-space-toggle') && document.getElementById('hidden-space-menu').getAttribute('label') === 'Show Spaces'};
result.menuPosition = document.getElementById('hidden-space-menu').nextElementSibling?.id === 'context_zenShareWorkspace';
const spaces = gZenWorkspaces.getWorkspaces();
const work = spaces.find(s=>s.name === 'Work');
const input = [...checkboxes].find(e=>e.value === work.uuid);
input.click();
await new Promise(r=>setTimeout(r,100));
result.settingsToggle = Services.prefs.getStringPref('uc.hidden-space.ids') === work.uuid;
const popup = document.querySelector('#hidden-space-restore > menupopup');
popup.dispatchEvent(new Event('popupshowing', {bubbles:true}));
result.fullList = popup.children.length === spaces.length;
const workMenuItem = [...popup.children].find(e=>e.getAttribute('label')==='Work');
result.hiddenUnchecked = !workMenuItem.hasAttribute('checked') && !workMenuItem.disabled;
workMenuItem.doCommand();
await new Promise(r=>setTimeout(r,200));
result.restoreOne = !Services.prefs.getStringPref('uc.hidden-space.ids');
const other = spaces.find(s=>s.uuid !== work.uuid);
popup.dispatchEvent(new Event('popupshowing', {bubbles:true}));
[...popup.children].find(e=>e.getAttribute('label')===other.name).doCommand();
await new Promise(r=>setTimeout(r,100));
result.menuHides = Services.prefs.getStringPref('uc.hidden-space.ids') === other.uuid;
Services.prefs.setStringPref('uc.hidden-space.ids', spaces.filter(s=>s.uuid !== work.uuid).map(s=>s.uuid).join(','));
await new Promise(r=>setTimeout(r,100));
result.lastVisibleProtected = [...doc.querySelectorAll('#hidden-space-picker input')].find(e=>e.value===work.uuid).disabled;
const newSpace = await gZenWorkspaces.createAndSaveWorkspace('New Space', '🧪');
await new Promise(r=>setTimeout(r,150));
popup.dispatchEvent(new Event('popupshowing', {bubbles:true}));
result.spaceIcon = [...popup.children].some(e=>e.getAttribute('label') === '🧪  New Space');
result.liveSpaceList = [...doc.querySelectorAll('#hidden-space-picker input')].some(e=>e.value===newSpace.uuid);
gZenWorkspaces.removeWorkspace(newSpace.uuid);
await new Promise(r=>setTimeout(r,100));
result.removedSpaceGone = ![...doc.querySelectorAll('#hidden-space-picker input')].some(e=>e.value===newSpace.uuid);
await sine.removeUnloadListeners('hidden-space');
result.settingsUnload = !doc.querySelector('#hidden-space-picker input') && !document.getElementById('hidden-space-toggle') && !document.getElementById('hidden-space-restore');
gBrowser.removeTab(tab);
return result;
''')['value']
call('WebDriver:DeleteSession')
assert 'error' not in settings, settings
assert all(value is True for value in settings.values()), settings
assert 'error' not in result, result
assert all(value is True for value in result.values()), result
print(f'{len(result) + len(settings)} Zen runtime checks passed')
