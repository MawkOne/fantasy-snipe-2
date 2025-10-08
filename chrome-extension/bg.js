// bg.js
console.log('[CBSX] Service worker starting');

const TARGET_URLS = [
  "https://uhhp.hockey.cbssports.com/stats/stats-main/all:C:W:F:D/restofseason:p/standard/projections?print_rows=9999",
  "https://uhhp.hockey.cbssports.com/transactions",
  "https://uhhp.hockey.cbssports.com/rules",
  "https://uhhp.hockey.cbssports.com/details/teams-managers",
  "https://uhhp.hockey.cbssports.com/glossary",
  "https://uhhp.hockey.cbssports.com/teams/all",
  "https://uhhp.hockey.cbssports.com/schedule/full",
  "https://uhhp.hockey.cbssports.com/standings/overall"
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
        const [tab2] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab2?.id) { sendResponse?.({ ok:false, error:'no-active-tab' }); return; }
        const startUrl = tab2.url;
        const results = [];
        for (const url of TARGET_URLS) {
          const page = await navigateAndExtractFromAllFrames(tab2.id, url);
          results.push(page);
        }
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
        const payload = { exportedAt: new Date().toISOString(), pages: results };
        const { cbsApiUrl, cbsApiKey } = await chrome.storage.sync.get(['cbsApiUrl', 'cbsApiKey']);
        if (!cbsApiUrl) { sendResponse?.({ ok:false, error:'missing-api-url' }); return; }
        const res = await fetch(cbsApiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(cbsApiKey ? { 'x-api-key': cbsApiKey } : {})
          },
          body: JSON.stringify(payload)
        });
        const data = await res.json().catch(() => ({}));
        if (startUrl?.startsWith('http')) {
          try { await chrome.tabs.update(tab2.id, { url: startUrl }); } catch {}
        }
        if (!res.ok) { sendResponse?.({ ok:false, status: res.status, detail: data?.detail || null }); return; }
        sendResponse?.({ ok:true, pages: results.length, response: data });
      } catch (e) {
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
    await chrome.tabs.update(tabId, { url, active: true });
    await waitForTabComplete(tabId, 60000);

    await chrome.scripting.executeScript({
      target: { tabId, allFrames: true },
      files: ['content.js']
    }).catch(() => {});

    await sleep(200);
    let page = await collectFromAllFrames(tabId);

    if (!page.ok) {
      await sleep(1200);
      page = await collectFromAllFrames(tabId);
    }
    return page;
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
    } catch {/* frame may not have our script */}
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
