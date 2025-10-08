// bg.js
console.log('[CBSX] Service worker starting');

// Hardcoded default API endpoint (Railway FastAPI)
const DEFAULT_API_URL = 'https://fastapi-production-45ce.up.railway.app/api/inseason/cbs/import';
function setBadge(text, color) {
  try {
    chrome.action.setBadgeText({ text: String(text || '') });
    if (color) chrome.action.setBadgeBackgroundColor({ color });
  } catch {}
}

async function appendLog(line) {
  try {
    const cur = await chrome.storage.local.get(['syncLog']);
    const arr = Array.isArray(cur.syncLog) ? cur.syncLog : [];
    arr.push(`[${new Date().toLocaleTimeString()}] ${line}`);
    await chrome.storage.local.set({ syncLog: arr });
  } catch {}
}


// Put heavy stats page last so it can't block earlier writes
const TARGET_URLS = [
  "https://uhhp.hockey.cbssports.com/rules",
  "https://uhhp.hockey.cbssports.com/details/teams-managers",
  "https://uhhp.hockey.cbssports.com/teams/all",
  "https://uhhp.hockey.cbssports.com/transactions",
  "https://uhhp.hockey.cbssports.com/schedule/full",
  "https://uhhp.hockey.cbssports.com/standings/overall",
  "https://uhhp.hockey.cbssports.com/glossary",
  "https://uhhp.hockey.cbssports.com/stats/stats-main/all:C:W:F:D/restofseason:p/standard/projections?print_rows=9999"
];

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) { sendResponse?.({ ok:false, error:'no-active-tab' }); return; }

    if (msg?.cmd === 'EXPORT_ALL_JSON') {
      const startUrl = tab.url;
      const results = [];

      for (const url of TARGET_URLS) {
        const page = await navigateAndExtractFromAllFrames(tab.id, url);
        results.push(page);
      }

      // Build owners map from Teams & Managers, enrich rows
      const ownersByTeamName = buildOwnersMap(results);
      for (const page of results) {
        if (!page?.ok) continue;
        for (const t of page.tables || []) {
          for (const r of t.rows || []) {
            const key = normTeam(r.team_name || r.Team || r['Team Name']);
            if (!r.team_owner && key && ownersByTeamName[key]) r.team_owner = ownersByTeamName[key];
          }
        }
      }

      const json = JSON.stringify({ exportedAt: new Date().toISOString(), pages: results }, null, 2);
      downloadText(json, 'application/json', 'cbs_export.json');

      if (startUrl?.startsWith('http')) {
        try { await chrome.tabs.update(tab.id, { url: startUrl }); } catch {}
      }

      sendResponse?.({ ok:true, pages: results.length });
    }

    if (msg?.cmd === 'UPLOAD_ALL_TO_API') {
      try {
        setBadge('…', '#2f6bff');
        // Initialize progress log (persisted so popup can read even if closed)
        await chrome.storage.local.set({ syncLog: [`[${new Date().toLocaleTimeString()}] Sync started…`], syncRunning: true });
        // Use the current active tab (no new tab)
        const [activeTab0] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!activeTab0?.id) { await appendLog('No active tab'); sendResponse?.({ ok:false, error:'no-active-tab' }); return; }
        let activeTab = activeTab0;

        // 1) Capture all pages first, report capture progress
        const results = [];
        for (const url of TARGET_URLS) {
          // Re-validate active tab; if gone, attempt to re-acquire
          let alive = await chrome.tabs.get(activeTab.id).catch(() => null);
          if (!alive?.id) {
            const re = await chrome.tabs.query({ active: true, currentWindow: true });
            activeTab = re?.[0];
            if (!activeTab?.id) { await appendLog(`Captured: ${url} -> failed (no tab)`); continue; }
          }
          const page = await navigateAndExtractFromAllFrames(activeTab.id, url);
          results.push({ url, page });
          const ok = !!page?.ok;
          await appendLog(`Captured: ${url} -> ${ok ? 'ok' : 'failed'}`);
          // Also notify popup (best-effort)
          chrome.runtime.sendMessage({ cmd: 'SYNC_CAPTURED', url, ok }).catch(() => {});
        }

        // 2) Enrich with owners map
        const ownersByTeamName = buildOwnersMap(results.map(r => r.page));
        for (const it of results) {
          const p = it.page;
          if (!p?.ok) continue;
          for (const t of p.tables || []) {
            for (const r of t.rows || []) {
              const key = normTeam(r.team_name || r.Team || r['Team Name']);
              if (!r.team_owner && key && ownersByTeamName[key]) r.team_owner = ownersByTeamName[key];
            }
          }
        }

        const { cbsApiUrl, cbsApiKey } = await chrome.storage.sync.get(['cbsApiUrl', 'cbsApiKey']);
        const uploadUrl = (cbsApiUrl || DEFAULT_API_URL);
        if (!uploadUrl) { sendResponse?.({ ok:false, error:'missing-api-url' }); return; }

        // 3) Upload each page individually and report synced status per page
        let okCount = 0;
        for (const it of results) {
          const payload = { exportedAt: new Date().toISOString(), pages: [it.page] };
          let exId = null, ok = false, status = 0;
          try {
            const res = await fetch(uploadUrl, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                ...(cbsApiKey ? { 'x-api-key': cbsApiKey } : {})
              },
              body: JSON.stringify(payload)
            });
            status = res.status;
            const data = await res.json().catch(() => ({}));
            ok = res.ok;
            exId = data?.extraction_id || null;
          } catch (_) {
            ok = false;
          }
          if (ok) okCount += 1;
          await appendLog(ok ? `Synced: ${it.url} -> ok${exId ? ` (extraction_id=${exId})` : ''}` : `Synced: ${it.url} -> failed${status ? ` (HTTP ${status})` : ''}`);
          chrome.runtime.sendMessage({ cmd: 'SYNC_SYNCED', url: it.url, ok, extraction_id: exId, status }).catch(() => {});
        }

        chrome.runtime.sendMessage({ cmd: 'SYNC_DONE', ok: okCount === results.length, pages: okCount }).catch(() => {});
        try { chrome.storage.local.set({ lastSync: { ok: okCount === results.length, pages: okCount, at: new Date().toISOString() } }); } catch {}
        try { chrome.storage.local.set({ syncRunning: false }); } catch {}
        setBadge(okCount === results.length ? '✓' : '!', okCount === results.length ? '#16a34a' : '#dc2626');
        setTimeout(() => setBadge('', null), 8000);
        sendResponse?.({ ok: okCount === results.length, pages: okCount });
      } catch (e) {
        chrome.runtime.sendMessage({ cmd: 'SYNC_DONE', ok: false, error: String(e) }).catch(() => {});
        try { chrome.storage.local.set({ lastSync: { ok: false, error: String(e), at: new Date().toISOString() } }); } catch {}
        try { chrome.storage.local.set({ syncRunning: false }); } catch {}
        setBadge('!', '#dc2626');
        setTimeout(() => setBadge('', null), 8000);
        sendResponse?.({ ok:false, error: String(e) });
      }
    }

    if (msg?.cmd === 'UPLOAD_CURRENT_TO_API') {
      try {
        setBadge('…', '#2f6bff');
        await chrome.storage.local.set({ syncLog: [`[${new Date().toLocaleTimeString()}] Sync (current page) started…`], syncRunning: true });
        const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!activeTab?.id) { await appendLog('No active tab'); sendResponse?.({ ok:false, error:'no-active-tab' }); return; }

        const page = await navigateAndExtractFromAllFrames(activeTab.id, activeTab.url || '');
        await appendLog(`Captured: ${activeTab.url} -> ${page?.ok ? 'ok' : (page?.reason || 'failed')}`);
        chrome.runtime.sendMessage({ cmd: 'SYNC_CAPTURED', url: activeTab.url, ok: !!page?.ok }).catch(() => {});

        if (!page?.ok) { sendResponse?.({ ok:false, error: page?.reason || 'no-tables' }); return; }

        const { cbsApiUrl, cbsApiKey } = await chrome.storage.sync.get(['cbsApiUrl', 'cbsApiKey']);
        const uploadUrl = (cbsApiUrl || DEFAULT_API_URL);
        if (!uploadUrl) { sendResponse?.({ ok:false, error:'missing-api-url' }); return; }
        const payload = { exportedAt: new Date().toISOString(), pages: [page] };
        const res = await fetch(uploadUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...(cbsApiKey ? { 'x-api-key': cbsApiKey } : {}) },
          body: JSON.stringify(payload)
        });
        const data = await res.json().catch(() => ({}));
        const ok = res.ok;
        const exId = data?.extraction_id || null;
        await appendLog(ok ? `Synced: ${activeTab.url} -> ok${exId ? ` (extraction_id=${exId})` : ''}` : `Synced: ${activeTab.url} -> failed (HTTP ${res.status})`);
        chrome.runtime.sendMessage({ cmd: 'SYNC_SYNCED', url: activeTab.url, ok, extraction_id: exId, status: res.status }).catch(() => {});
        chrome.runtime.sendMessage({ cmd: 'SYNC_DONE', ok, pages: ok ? 1 : 0 }).catch(() => {});
        try { chrome.storage.local.set({ syncRunning: false }); } catch {}
        setBadge(ok ? '✓' : '!', ok ? '#16a34a' : '#dc2626');
        setTimeout(() => setBadge('', null), 8000);
        sendResponse?.({ ok, response: data, pages: ok ? 1 : 0 });
      } catch (e) {
        await appendLog(String(e));
        chrome.runtime.sendMessage({ cmd: 'SYNC_DONE', ok: false, error: String(e) }).catch(() => {});
        try { chrome.storage.local.set({ syncRunning: false }); } catch {}
        setBadge('!', '#dc2626');
        setTimeout(() => setBadge('', null), 8000);
        sendResponse?.({ ok:false, error: String(e) });
      }
    }
  })();
  return true;
});

// Reinject content on SPA history changes
chrome.webNavigation.onHistoryStateUpdated.addListener((details) => {
  const url = details.url || '';
  const allowed = /^https:\/\/(.*\.)?cbssports\.com\/|^https:\/\/uhhp\.hockey\.cbssports\.com\//.test(url);
  if (!allowed) return;
  chrome.scripting.executeScript({
    target: { tabId: details.tabId, allFrames: true },
    files: ['content.js']
  }).catch(() => {});
});

/* -------- core nav/extract (all frames) -------- */
async function navigateAndExtractFromAllFrames(tabId, url) {
  try {
    // Do not focus the tab during navigation; keeps popup alive
    await chrome.tabs.update(tabId, { url });
    await waitForTabComplete(tabId, 90000);

    await chrome.scripting.executeScript({
      target: { tabId, allFrames: true },
      files: ['content.js']
    }).catch(() => {});

    // Retry extraction up to 3 times with exponential backoff
    let page = null;
    for (let attempt = 0; attempt < 3; attempt++) {
      await sleep(300 + attempt * 300);
      page = await collectFromAllFrames(tabId);
      if (page?.ok) break;
      await chrome.scripting.executeScript({ target: { tabId, allFrames: true }, files: ['content.js'] }).catch(() => {});
      await sleep(600 * Math.pow(2, attempt));
    }
    // Hard timeout guard: if still no tables, return reason
    return page || { ok:false, url, reason:'timeout-or-no-tables', title:'' };
  } catch (e) {
    return { ok:false, url, reason:String(e), title:'' };
  }
}

async function collectFromAllFrames(tabId) {
  const frames = await chrome.webNavigation.getAllFrames({ tabId }).catch(() => null);
  const frameIds = frames?.map(f => f.frameId) ?? [0];

  const responses = [];
  for (const fid of frameIds) {
    try {
      const resp = await chrome.tabs.sendMessage(tabId, { cmd: 'EXTRACT_JSON' }, { frameId: fid });
      if (resp?.ok && Array.isArray(resp.tables)) responses.push(resp);
    } catch (e) {
      // frame may not have our script; attempt injection once
      try {
        await chrome.scripting.executeScript({ target: { tabId, allFrames: true }, files: ['content.js'] });
        const resp2 = await chrome.tabs.sendMessage(tabId, { cmd: 'EXTRACT_JSON' }, { frameId: fid });
        if (resp2?.ok && Array.isArray(resp2.tables)) responses.push(resp2);
      } catch {}
    }
  }

  const tabInfo = await chrome.tabs.get(tabId).catch(() => ({}));
  const tabUrl = tabInfo?.url || '';

  if (!responses.length) {
    return { ok:false, url: tabUrl, reason:'no-tables', title:'' };
  }

  const merged = { ok:true, url: tabUrl, title: '', tables: [] };
  for (const r of responses) {
    merged.title = merged.title || r.title || '';
    merged.tables = merged.tables.concat(r.tables || []);
  }
  return merged;
}

/* -------- owners map + utils -------- */
function buildOwnersMap(results) {
  const map = Object.create(null);
  for (const page of results) {
    if (!page?.ok) continue;
    if (!/\/details\/teams-managers/i.test(page.url)) continue;

    for (const t of page.tables || []) {
      const headers = (t.headers || []).map(h => (h || '').toLowerCase());
      const idxTeam  = headers.findIndex(h => /team/.test(h));
      const idxOwner = headers.findIndex(h => /(owner|manager)/.test(h));
      if (idxTeam === -1 || idxOwner === -1) continue;

      for (const r of t.rows || []) {
        const teamName = r[t.headers[idxTeam]] || r.Team || r['Team Name'];
        const owner    = r[t.headers[idxOwner]] || r.Owner || r.Manager;
        const key = normTeam(teamName);
        if (key) map[key] = owner;
      }
    }
  }
  return map;
}

function normTeam(s) {
  if (!s) return '';
  return String(s).trim().toLowerCase().replace(/\s+/g, ' ');
}

function waitForTabComplete(tabId, timeoutMs=60000) {
  return new Promise(resolve => {
    const t0 = Date.now();
    (function check() {
      chrome.tabs.get(tabId).then(tab => {
        if (tab?.status === 'complete') return resolve(true);
        if (Date.now() - t0 > timeoutMs) return resolve(false);
        setTimeout(check, 300);
      }).catch(() => resolve(false));
    })();
  });
}

function downloadText(text, mime, filename) {
  const url = `data:${mime};charset=utf-8,` + encodeURIComponent(text);
  chrome.downloads.download({ url, filename });
}

const sleep = (ms) => new Promise(r => setTimeout(r, ms));
