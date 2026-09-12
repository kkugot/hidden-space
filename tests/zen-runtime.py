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
print(js('Services.io.getProtocolHandler("resource").QueryInterface(Ci.nsIResProtocolHandler).setSubstitution("hidden-space-test", Services.io.newURI("' + (Path(__file__).resolve().parents[1].as_uri() + '/') + '")); Services.scriptloader.loadSubScript("resource://hidden-space-test/hidden-space.uc.js", window); return {loaded:!!window.HiddenSpace,menu:!!document.getElementById("hidden-space-menu")};'))
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
results.revealed = getComputedStyle(document.querySelector(`zen-workspace-icons toolbarbutton[zen-workspace-id="${work.uuid}"]`)).display !== 'none';
await manager.changeWorkspace(work);
Services.prefs.setBoolPref('uc.hidden-space.reveal', false);
await new Promise(r=>setTimeout(r,500));
results.activeRecovered = manager.activeWorkspace !== work.uuid;
const popup = document.querySelector('#hidden-space-menu > menupopup');
popup.dispatchEvent(new Event('popupshowing', {bubbles:true}));
results.menuChecked = [...popup.children].find(e=>e.getAttribute('label')==='Work').getAttribute('checked') === 'true';
Services.prefs.setStringPref('uc.hidden-space.ids', spaces.map(s=>s.uuid).join(','));
await new Promise(r=>setTimeout(r,300));
results.fallbackVisible = getComputedStyle(document.querySelector(`zen-workspace-icons toolbarbutton[zen-workspace-id="${spaces[0].uuid}"]`)).display !== 'none';
window.HiddenSpace.destroy();
results.unloaded = !document.getElementById('hidden-space-menu') && !document.getElementById('hidden-space-style');
await manager.changeWorkspace(work);
results.navigationRestored = manager.activeWorkspace === work.uuid;
return results;
''')['value']
call('WebDriver:DeleteSession')
assert 'error' not in result, result
assert all(value is True for value in result.values()), result
print(f'{len(result)} Zen runtime checks passed')
