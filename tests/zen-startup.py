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
def asyncjs(script):
 return call('WebDriver:ExecuteAsyncScript',{'script':'const done = arguments[arguments.length - 1]; (async () => {'+script+'})().then(done, e => done({error:String(e),stack:e.stack}));','args':[],'newSandbox':False,'sandbox':'system','scriptTimeout':30000})

import sys
mode = sys.argv[1]
if mode in ('on', 'off'):
 result = asyncjs("""
const sine = ChromeUtils.importESModule('chrome://userscripts/content/core/manager.sys.mjs').default;
await sine.removeUnloadListeners('hidden-space');
window.HiddenSpace?.destroy();
const work = gZenWorkspaces.getWorkspaces().find(s=>s.name==='Work');
await gZenWorkspaces.changeWorkspace(work);
let tab = gBrowser.tabs.find(t=>t.linkedBrowser?.currentURI.spec==='about:robots');
if (!tab) tab = gBrowser.addTrustedTab('about:robots');
gBrowser.selectedTab = tab;
Services.prefs.setBoolPref('sine.allow-unsafe-js', true);
Services.prefs.setIntPref('browser.startup.page', 3);
Services.prefs.setBoolPref('zen.workspaces.continue-where-left-off', CONTINUE);
Services.prefs.setStringPref('uc.hidden-space.ids', work.uuid);
Services.prefs.setBoolPref('uc.hidden-space.reveal', true);
Services.prefs.savePrefFile(null);
await gBrowser.TabStateFlusher.flush(tab.linkedBrowser);
await new Promise(r=>setTimeout(r,500));
return {active:gZenWorkspaces.activeWorkspace,hidden:work.uuid,tabSpace:tab.getAttribute('zen-workspace-id'),tab:tab.linkedBrowser.currentURI.spec};
""".replace('CONTINUE', 'true' if mode=='on' else 'false'))['value']
 print(result)
 assert result['active']==result['hidden']==result['tabSpace'], result
 js("window.setTimeout(()=>Services.startup.quit(Ci.nsIAppStartup.eAttemptQuit),500);")
elif mode == 'check':
 result = asyncjs("""
await gZenWorkspaces.promiseInitialized;
await new Promise(r=>setTimeout(r,1200));
const hidden=Services.prefs.getStringPref('uc.hidden-space.ids');
const tab = gBrowser.selectedTab;
const tabSpace=tab.getAttribute('zen-workspace-id');
const button=document.querySelector(`zen-workspace-icons toolbarbutton[zen-workspace-id="${hidden}"]`);
return {loaded:!!window.HiddenSpace,continueEnabled:Services.prefs.getBoolPref('zen.workspaces.continue-where-left-off'),active:gZenWorkspaces.activeWorkspace,hidden,
  visibleActive:gZenWorkspaces.activeWorkspace!==hidden,
  visibleTab:tab.hasAttribute('zen-essential') || tabSpace===gZenWorkspaces.activeWorkspace,
  tab:tab.linkedBrowser.currentURI.spec,hiddenIcon:getComputedStyle(button).display==='none',
  legacyCleared:!Services.prefs.prefHasUserValue('uc.hidden-space.reveal')};
""")['value']
 print(result)
 assert all(result[k] for k in ('loaded','visibleActive','visibleTab','hiddenIcon','legacyCleared')), result
else:
 raise ValueError('Use on, off, or check')
call('WebDriver:DeleteSession')
