// popup.js
const logEl = document.getElementById('log');
function normalizeMsg(m) {
  if (typeof m === 'string') return m;
  try { return JSON.stringify(m, null, 2); } catch { return String(m); }
}
const log = (m) => (logEl && (logEl.textContent = normalizeMsg(m)));
function append(line) {
  const prev = (logEl && logEl.textContent) || '';
  log(prev ? `${prev}\n${line}` : line);
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function injectContentIfNeeded(tabId) {
  try {
    await chrome.tabs.sendMessage(tabId, { cmd: 'PING' });
    return true;
  } catch {
    try {
      await chrome.scripting.executeScript({ target: { tabId, allFrames: true }, files: ['content.js'] });
      await new Promise(r => setTimeout(r, 200));
      return true;
    } catch (e) {
      log({ ok:false, error:'inject-failed', detail:String(e) });
      return false;
    }
  }
}

/** Map CBS URLs → base filename */
function basenameForUrl(u) {
  let url;
  try { url = new URL(u); } catch { return 'page'; }
  const p = url.pathname;

  if (/\/schedule\/full\/?$/i.test(p)) return 'schedule';
  if (/\/transactions\/?$/i.test(p))  return 'transactions';
  if (/\/teams\/all\/?$/i.test(p))    return 'teams';
  if (/\/rules\/?$/i.test(p))         return 'rules';
  if (/\/details\/teams-managers\/?$/i.test(p)) return 'owners';
  if (/\/stats\/stats-main\//i.test(p)) {
    // Heuristic: Goalie filter usually encodes ":G:" in the path
    return /:G:/.test(p) ? 'stats-goalies' : 'stats-skaters';
  }
  return 'page';
}

/** Export THIS PAGE (JSON) with smart filename */
async function exportThisJson() {
  log('Running on current tab…');
  const tab = await getActiveTab();
  if (!tab?.id) return log({ ok: false, error: 'no-active-tab' });

  if (!(await injectContentIfNeeded(tab.id))) return;

  try {
    const resp = await chrome.tabs.sendMessage(tab.id, { cmd: 'EXTRACT_JSON' });
    if (!resp?.ok) return log(resp || { ok: false, error: 'no response from content script' });

    const base = basenameForUrl(resp.url || tab.url || '');
    const json = JSON.stringify({ exportedAt: new Date().toISOString(), pages: [resp] }, null, 2);
    downloadText(json, 'application/json', `${base}.json`);

    log({ ok: true, tables: resp.tables?.length || 0, filename: `${base}.json` });
  } catch (e) {
    log({ ok: false, error: String(e) });
  }
}

/** Export ALL PAGES sequentially (JSON, combined file) */
function exportAllJson() {
  log('Running sequential export…');
  chrome.runtime.sendMessage({ cmd: 'EXPORT_ALL_JSON' }, (res) => {
    if (chrome.runtime.lastError) return log({ ok:false, error: chrome.runtime.lastError.message });
    log(res || { ok:true, filename: 'cbs_export.json' });
  });
}

function downloadText(text, mime, filename) {
  const url = `data:${mime};charset=utf-8,` + encodeURIComponent(text);
  chrome.downloads.download({ url, filename });
}

/* ---------- Wire up buttons ---------- */
// Manual export buttons (debug)
document.getElementById('thisJson')?.addEventListener('click', exportThisJson);
document.getElementById('allJson')?.addEventListener('click',  exportAllJson);
document.getElementById('uploadCurrent')?.addEventListener('click', () => {
  log('Sync (current page) started…');
  chrome.runtime.sendMessage({ cmd: 'UPLOAD_CURRENT_TO_API' }, (res) => {
    if (chrome.runtime.lastError) return log({ ok:false, error: chrome.runtime.lastError.message });
    append(res?.ok ? 'Uploaded current page.' : `Upload failed: ${res?.error || ''}`);
  });
});

// --- New: Persist API config in chrome.storage and upload helpers ---
// Hardcoded default API endpoint (Railway FastAPI)
const DEFAULT_API_URL = 'https://fastapi-production-45ce.up.railway.app/api/inseason/cbs/import';

const apiUrlInput = document.getElementById('apiUrl');
const apiKeyInput = document.getElementById('apiKey');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const syncBtn = document.getElementById('syncBtn');
const skipStats = document.getElementById('skipStats');

chrome.storage.sync.get(['cbsApiUrl', 'cbsApiKey', 'cbsEmail'], ({ cbsApiUrl, cbsApiKey, cbsEmail }) => {
  apiUrlInput.value = (cbsApiUrl || DEFAULT_API_URL);
  apiUrlInput.disabled = true; // lock to Railway by default
  if (cbsApiKey) apiKeyInput.value = cbsApiKey;
  // Optional prefill email from storage; never hardcode or lock credentials
  if (cbsEmail) emailInput.value = cbsEmail;
  emailInput.disabled = false;
  passwordInput.disabled = false;
  // Disable sync unless we have an API key
  syncBtn.disabled = !Boolean(apiKeyInput.value);
});

// If you ever re-enable editing, this persists the override
apiUrlInput.addEventListener('change', () => chrome.storage.sync.set({ cbsApiUrl: apiUrlInput.value.trim() }));
apiKeyInput.addEventListener('change', () => chrome.storage.sync.set({ cbsApiKey: apiKeyInput.value.trim() }));
emailInput.addEventListener('change', () => chrome.storage.sync.set({ cbsEmail: emailInput.value.trim() }));

async function uploadPayload(payload) {
  const apiUrl = (apiUrlInput.value.trim() || DEFAULT_API_URL);
  const apiKey = apiKeyInput.value.trim();
  if (!apiUrl) { log({ ok:false, error:'missing-api-url' }); return; }
  try {
    const res = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Prefer x-api-key header; backend also supports Authorization: ApiKey <key>
        ...(apiKey ? { 'x-api-key': apiKey } : {})
      },
      body: JSON.stringify(payload)
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
    log({ ok:true, uploaded:true, response: data });
  } catch (e) {
    log({ ok:false, error:String(e) });
  }
}

async function uploadThisJson() {
  const tab = await getActiveTab();
  if (!tab?.id) return log({ ok:false, error:'no-active-tab' });
  if (!(await injectContentIfNeeded(tab.id))) return;
  try {
    const resp = await chrome.tabs.sendMessage(tab.id, { cmd: 'EXTRACT_JSON' });
    if (!resp?.ok) return log(resp || { ok:false, error:'no response from content script' });
    const payload = { exportedAt: new Date().toISOString(), pages: [resp] };
    await uploadPayload(payload);
  } catch (e) {
    log({ ok:false, error:String(e) });
  }
}

function uploadAllJson() {
  // Ask background to gather all target pages and upload directly
  log('Uploading sequential export…');
  chrome.runtime.sendMessage({ cmd: 'UPLOAD_ALL_TO_API' }, async (res) => {
    if (chrome.runtime.lastError) return log({ ok:false, error: chrome.runtime.lastError.message });
    log(res || { ok:true, uploaded:true });
  });
}

document.getElementById('syncBtn')?.addEventListener('click', () => {
  // Use background flow to gather all pages and upload
  log('Sync started…');
  chrome.runtime.sendMessage({ cmd: 'UPLOAD_ALL_TO_API', skipStats: !!(skipStats && skipStats.checked) }, (res) => {
    if (chrome.runtime.lastError) return log({ ok:false, error: chrome.runtime.lastError.message });
    if (res?.ok) {
      const exId = res?.response?.extraction_id;
      append(`Result: ok, pages=${res?.pages || 0}${exId ? `, extraction_id=${exId}` : ''}`);
    } else {
      append(`Result: failed${res?.status ? ` HTTP ${res.status}` : ''}`);
    }
  });
});

// Display progress lines as pages are captured and when upload completes
chrome.runtime.onMessage.addListener((msg) => {
  if (msg?.cmd === 'SYNC_CAPTURED') {
    append(`Captured: ${msg.url} -> ${msg.ok ? 'ok' : 'failed'}`);
  } else if (msg?.cmd === 'SYNC_SYNCED') {
    append(`Synced: ${msg.url} -> ${msg.ok ? `ok${msg.extraction_id ? ` (extraction_id=${msg.extraction_id})` : ''}` : `failed${msg.status ? ` (HTTP ${msg.status})` : ''}`}`);
  } else if (msg?.cmd === 'SYNC_DONE') {
    append(msg.ok ? `Uploaded: ${msg.pages} pages${msg.extraction_id ? `, extraction_id=${msg.extraction_id}` : ''}` : `Upload failed: ${msg.error || ''}`);
  }
});

// If the popup was opened mid-sync, hydrate the log from storage
(async () => {
  try {
    const { syncLog } = await chrome.storage.local.get(['syncLog']);
    if (Array.isArray(syncLog) && syncLog.length) {
      log(syncLog.join('\n'));
    }
  } catch {}
})();

// Live-update the log when background appends to storage
chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== 'local') return;
  if (changes.syncLog && Array.isArray(changes.syncLog.newValue)) {
    const lines = changes.syncLog.newValue;
    log(lines.join('\n'));
  }
});

async function authCall(path, body) {
  const base = (apiUrlInput.value.trim() || DEFAULT_API_URL).replace(/\/$/, '');
  const url = base.replace(/\/api\/inseason\/cbs\/import$/, '') + path;
  const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`);
  return data;
}

async function doLogin() {
  try {
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    if (!email || !password) return log({ ok:false, error:'email/password required' });
    const data = await authCall('/api/auth/login', { email, password });
    if (data?.api_key) {
      apiKeyInput.value = data.api_key;
      await chrome.storage.sync.set({ cbsApiKey: data.api_key, cbsEmail: email });
      log({ ok:true, message:'logged in', api_key: '***' });
      syncBtn.disabled = false;
    } else {
      log({ ok:false, error:'no api_key in response' });
    }
  } catch (e) {
    log({ ok:false, error:String(e) });
  }
}

async function doRegister() {
  try {
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    if (!email || !password) return log({ ok:false, error:'email/password required' });
    const data = await authCall('/api/auth/register', { email, password });
    if (data?.api_key) {
      apiKeyInput.value = data.api_key;
      await chrome.storage.sync.set({ cbsApiKey: data.api_key, cbsEmail: email });
      log({ ok:true, message:'registered', api_key: '***' });
    } else {
      log({ ok:false, error:'no api_key in response' });
    }
  } catch (e) {
    log({ ok:false, error:String(e) });
  }
}

document.getElementById('login')?.addEventListener('click', doLogin);

// Ensure the log box is visible at open
try { if (logEl && !logEl.textContent) log(''); } catch {}
// Register disabled per requirement
