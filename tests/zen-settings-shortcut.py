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
print(asyncjs("window.HiddenSpace?.destroy(); window._settingsOriginalSwitch = window.switchToTabHavingURI; Services.prefs.setBoolPref('sine.allow-unsafe-js', true); await ChromeUtils.importESModule('chrome://userscripts/content/core/manager.sys.mjs').default.rebuildMods(); return {loaded:!!window.HiddenSpace, menu:!!document.getElementById('hidden-space-menu')};"))
import sys
settings_uri = sys.argv[1] if len(sys.argv) > 1 else 'about:preferences'
assert settings_uri in ('about:preferences', 'about:settings')
result = asyncjs("""
const check = (ok, message) => { if (!ok) throw new Error(message); };
const originalSwitch = window._settingsOriginalSwitch;
const pause = () => new Promise(r=>setTimeout(r,700));
const isSettings = tab => /^about:(preferences|settings)([?#]|$)/.test(tab.linkedBrowser?.currentURI.spec || '');
for (const tab of [...gZenWorkspaces.allStoredTabs].filter(isSettings)) gBrowser.removeTab(tab);
const spaces=gZenWorkspaces.getWorkspaces();
const work=spaces.find(s=>s.name==='Work');
const home=spaces.find(s=>s.uuid!==work.uuid);
await gZenWorkspaces.changeWorkspace(work);
const hiddenTab=gBrowser.addTrustedTab('SETTINGS_URI');
gBrowser.selectedTab=hiddenTab;
await pause();
await gZenWorkspaces.changeWorkspace(home);
Services.prefs.setStringPref('uc.hidden-space.ids',work.uuid);
await pause();
const hiddenURL=hiddenTab.linkedBrowser.currentURI.spec;
const spaceRecords=JSON.stringify(gZenWorkspaces.getWorkspacesForSessionStore());
await window.openPreferences();
await pause();
check(isSettings(gBrowser.selectedTab), 'Cmd+, must select Settings');
check(gBrowser.selectedTab!==hiddenTab, 'Cmd+, must not select the hidden Settings tab');
check(gBrowser.selectedTab.getAttribute('zen-workspace-id')===home.uuid, 'Settings must open in the visible Space');
const localTab=gBrowser.selectedTab;
const count=gZenWorkspaces.allStoredTabs.filter(isSettings).length;
await window.openPreferences();
await pause();
check(gZenWorkspaces.allStoredTabs.filter(isSettings).length===count && gBrowser.selectedTab===localTab, 'Repeated shortcuts must reuse local Settings');
await window.openPreferences('panePrivacy',{urlParams:{entrypoint:'hidden-space-test'}});
await pause();
check(gBrowser.selectedTab===localTab && /privacy/i.test(localTab.linkedBrowser.currentURI.spec), 'Settings pane links must remain supported');
check(hiddenTab.getAttribute('zen-workspace-id')===work.uuid && hiddenTab.linkedBrowser.currentURI.spec===hiddenURL, 'Hidden Settings tab must remain unchanged');
check(JSON.stringify(gZenWorkspaces.getWorkspacesForSessionStore())===spaceRecords, 'Space records must remain unchanged');
window.HiddenSpace.destroy();
await window.openPreferences();
await pause();
check(window.switchToTabHavingURI === originalSwitch, 'Unload must restore native Settings lookup');
return {passed:8};
""".replace('SETTINGS_URI', settings_uri))['value']
call('WebDriver:DeleteSession')
assert 'error' not in result, result
print(result)
