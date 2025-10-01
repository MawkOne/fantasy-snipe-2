// content.js
(() => {
    if (window.__cbsx) return; window.__cbsx = true;
  
    const clean = t => (t ?? "").replace(/\u00A0/g, " ").replace(/\s+/g, " ").trim();
    const sleep = ms => new Promise(r => setTimeout(r, ms));
  
    async function ensureAllRowsVisible() {
      for (let i = 0; i < 10; i++) {
        window.scrollTo(0, document.body.scrollHeight);
        await sleep(120);
      }
      window.scrollTo(0, 0);
    }
  
    async function waitForTables(timeoutMs = 20000) {
      const t0 = Date.now();
      for (;;) {
        const t1 = document.querySelector('table:has(tbody > tr.row1), table:has(tbody > tr.row2)');
        const t2 = document.querySelector('table');
        if (t1 || t2) return true;
        if (Date.now() - t0 > timeoutMs) return false;
        await sleep(300);
      }
    }
  
    function headersFrom(table) {
      let headRow =
        table.querySelector('thead.tableFloatingHeader tr:last-child') ||
        table.querySelector('thead tr:last-child') ||
        table.querySelector('tr');
  
      const cells = headRow ? [...headRow.querySelectorAll('th,td')] : [];
      return cells.map(th => clean(th.innerText || th.textContent));
    }
  
    function rowsFrom(table) {
      let trs = [...table.querySelectorAll('tbody tr.row1, tbody tr.row2')];
      if (!trs.length) trs = [...table.querySelectorAll('tbody tr')];
      if (!trs.length) {
        const all = [...table.querySelectorAll('tr')];
        return all.slice(1);
      }
      return trs;
    }
  
    // --- Player link → CBS id/meta ---
    function extractPlayerMeta(td) {
      const a = td.querySelector('a.playerLink, a[href*="/players/playerpage/"]');
      if (!a) return null;
  
      const href = a.getAttribute('href') || '';
      const url = (() => { try { return new URL(href, location.origin).href; } catch { return href; } })();
  
      let cbsId = null;
      const m1 = href.match(/\/players\/playerpage\/(\d+)/);
      const m2 = href.match(/[?&](?:pid|id)=(\d+)/i);
      if (m1) cbsId = m1[1];
      else if (m2) cbsId = m2[1];
  
      return {
        cbs_player_id: cbsId || null,
        player_url: url,
        player_name: clean(a.textContent),
        player_label: clean(a.getAttribute('aria-label') || '')
      };
    }
  
    // --- Team link → CBS team id/meta ---
    function extractTeamMeta(td) {
      const a = td.querySelector('a[href*="/fantasy/teams/"]');
      if (!a) return null;
  
      const href = a.getAttribute('href') || '';
      const url = (() => { try { return new URL(href, location.origin).href; } catch { return href; } })();
  
      let teamId = null;
      const m = href.match(/\/fantasy\/teams\/(\d+)/);
      if (m) teamId = m[1];
  
      return {
        cbs_team_id: teamId || null,
        team_url: url,
        team_name_link: clean(a.textContent),
        team_label: clean(a.getAttribute('aria-label') || '')
      };
    }
  
    // Try to infer "Team Name" + "Roster Group (Skaters/Goalies)" for this table
    function teamContextForTable(table) {
      const titleCell = table.querySelector('tr.title td, thead tr td[colspan], thead tr th[colspan]');
      const title = clean(titleCell?.innerText || titleCell?.textContent || '');
      const rx = /(.*?)(?:\s+)(Skaters?|Goalies?)$/i;
      let team_name = null, roster_group = null;
  
      if (title) {
        const m = title.match(rx);
        if (m) { team_name = clean(m[1]); roster_group = clean(m[2]); }
      }
  
      if (!team_name) {
        let el = table;
        for (let i = 0; i < 4 && el; i++) {
          el = el.previousElementSibling;
          if (el && /^H[1-6]$/.test(el.tagName)) {
            const txt = clean(el.innerText);
            const m2 = txt.match(rx);
            if (m2) { team_name = clean(m2[1]); roster_group = clean(m2[2]); break; }
            if (!m2 && txt) team_name = txt;
          }
        }
      }
  
      // Try to find owner nearby (best-effort)
      let team_owner = null;
      {
        let p = table.parentElement;
        for (let hops = 0; hops < 5 && p; hops++, p = p.parentElement) {
          const text = clean(p.innerText || '');
          const m = text.match(/\b(?:Manager|Owner)\s*:\s*([^\n]+)$/im);
          if (m) { team_owner = clean(m[1]); break; }
        }
      }
  
      return { team_name, roster_group, team_owner };
    }
  
    function isLikelyPlayerHeader(hText) {
      const t = (hText || '').toLowerCase();
      return t === 'player' || t === 'name' || t.includes('player');
    }
  
    // --- /transactions normalization ---
    function normalizeTransactionsRow(o) {
      if (!o.PLAYERS) return o;
  
      const raw = o.PLAYERS;
      let eventType = null;
  
      if (/signed/i.test(raw)) eventType = 'Waivers';
      else if (/trade/i.test(raw)) eventType = 'Trade';
      else if (/dropped/i.test(raw)) eventType = 'Dropped';
  
      const out = { ...o, Event: eventType || raw };
  
      // Keep trailing details after a dash
      const m = raw.match(/-\s*(.+)$/);
      if (m) out.details = m[1];
  
      delete out.PLAYERS;
      return out;
    }
  
    function tableToJSON(table) {
      const headers = headersFrom(table);
      const trs = rowsFrom(table);
      const ctx = teamContextForTable(table); // { team_name, roster_group, team_owner }
  
      let playerColIdx = -1;
      headers.forEach((h, i) => { if (playerColIdx === -1 && isLikelyPlayerHeader(h)) playerColIdx = i; });
  
      const rows = trs.map(tr => {
        const tds = [...tr.querySelectorAll('td')];
        let o = {};
  
        tds.forEach((td, i) => {
          const text = clean(td.innerText || td.textContent);
          const key = headers[i] || `col_${i + 1}`;
          o[key] = text;
  
          const maybePlayer =
            (playerColIdx === i ? extractPlayerMeta(td) : null) ||
            (playerColIdx === -1 ? extractPlayerMeta(td) : null);
          if (maybePlayer) Object.assign(o, maybePlayer);
  
          const maybeTeam = extractTeamMeta(td);
          if (maybeTeam) Object.assign(o, maybeTeam);
        });
  
        // Table-level context
        if (ctx.team_name)    o.team_name    = ctx.team_name;
        if (ctx.roster_group) o.roster_group = ctx.roster_group;
        if (ctx.team_owner)   o.team_owner   = ctx.team_owner;
  
        // Special handling for Transactions page
        if (/\/transactions(?:\/|$)/i.test(location.pathname)) {
          o = normalizeTransactionsRow(o);
        }
  
        return o;
      });
  
      return { headers, rows, context: ctx };
    }
  
    function labelFor(table, idx) {
      const cap = table.querySelector('caption')?.innerText;
      if (cap) return clean(cap);
      const aria = table.getAttribute('aria-label');
      if (aria) return clean(aria);
      let el = table;
      for (let i = 0; i < 4 && el; i++) {
        el = el.previousElementSibling;
        if (el && /^H[1-6]$/.test(el.tagName)) return clean(el.innerText);
      }
      return `table_${idx + 1}`;
    }
  
    async function extractAllTables() {
      const hasTables = await waitForTables(20000);
      if (!hasTables) return { ok: false, reason: 'no-tables', url: location.href, title: document.title || '' };
  
      await ensureAllRowsVisible();
  
      const tables = [...document.querySelectorAll('table')];
      if (!tables.length) return { ok: false, reason: 'no-tables', url: location.href, title: document.title || '' };
  
      const items = tables.map((t, i) => {
        const { headers, rows, context } = tableToJSON(t);
        return { name: labelFor(t, i), headers, rows, context };
      });
  
      return { ok: true, url: location.href, title: document.title || '', tables: items };
    }
  
    chrome.runtime.onMessage?.addListener((msg, _sender, sendResponse) => {
      (async () => {
        if (msg?.cmd === 'EXTRACT_JSON') sendResponse(await extractAllTables());
        else if (msg?.cmd === 'PING') sendResponse({ ok: true, url: location.href });
      })();
      return true;
    });
  
    try { chrome.runtime.sendMessage({ cmd: 'CONTENT_READY', url: location.href }); } catch {}
  })();
  