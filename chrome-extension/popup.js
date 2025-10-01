// popup.js
const logEl = document.getElementById('log');
const log = (m) => (logEl.textContent = typeof m === 'string' ? m : JSON.stringify(m, null, 2));

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
document.getElementById('thisJson').addEventListener('click', exportThisJson);
document.getElementById('allJson').addEventListener('click',  exportAllJson);
