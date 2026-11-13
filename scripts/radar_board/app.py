#!/usr/bin/env python3
"""PongNews Research Radar — mobile story-backlog board (R10)."""

import threading
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

import research_radar as radar

app = FastAPI(title="PongNews Research Radar")
scan_lock = threading.Lock()
scan_state = {"running": False, "last": None, "last_result": None}

TIER_LABELS = {
    1: "TT direct",
    2: "Racket sports",
    3: "Open-skill",
    4: "Exergame/VR",
}
TIER_COLORS = {1: "#8F001A", 2: "#B45309", 3: "#1D4ED8", 4: "#047857"}


@app.get("/api/candidates")
def candidates():
    return JSONResponse(radar.list_backlog(limit=80))


@app.get("/api/scan/status")
def scan_status():
    return scan_state


@app.post("/api/scan")
def run_scan():
    if scan_state["running"]:
        return {"status": "already-running"}
    if not scan_lock.acquire(blocking=False):
        return {"status": "already-running"}

    def worker():
        scan_state["running"] = True
        try:
            backlog, tier_new, covered = radar.run_scan(verbose=False)
            scan_state["last_result"] = {
                "new": sum(tier_new.values()),
                "per_tier": tier_new,
                "covered": covered,
                "backlog": len(backlog),
            }
        except Exception as exc:
            scan_state["last_result"] = {"error": str(exc)}
        finally:
            scan_state["running"] = False
            scan_state["last"] = datetime.now().isoformat(timespec="seconds")
            scan_lock.release()

    threading.Thread(target=worker, daemon=True).start()
    return {"status": "started"}


@app.get("/api/quota")
def quota():
    """Compatibility stub: always OK (no z.ai usage here)."""
    return {"ok": True}


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PongNews Research Radar</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, system-ui, sans-serif; margin: 0;
         background: #faf9f7; color: #1c1917; }
  header { background: #8F001A; color: #fff; padding: 14px 16px;
           position: sticky; top: 0; z-index: 2; }
  header h1 { font-size: 17px; margin: 0 0 2px; }
  header small { opacity: .85; font-size: 12px; }
  main { padding: 12px; max-width: 720px; margin: 0 auto; }
  .card { background: #fff; border: 1px solid #e7e5e4; border-radius: 12px;
          padding: 12px 14px; margin-bottom: 10px; }
  .meta { display: flex; gap: 6px; flex-wrap: wrap; align-items: center;
          margin-bottom: 6px; font-size: 11px; }
  .chip { padding: 2px 8px; border-radius: 999px; color: #fff; font-weight: 600; }
  .score { background: #1c1917; }
  .cat { background: #57534e; font-weight: 500; }
  h2 { font-size: 14.5px; margin: 0 0 6px; line-height: 1.35; }
  .jrnl { font-size: 12px; color: #78716c; margin-bottom: 8px; }
  .angle { font-size: 12px; color: #8F001A; margin-bottom: 6px; }
  details { font-size: 12.5px; color: #44403c; }
  summary { cursor: pointer; color: #8F001A; font-size: 12px; }
  a.pmid { font-size: 12px; color: #1D4ED8; text-decoration: none; }
  button { background: #fff; color: #8F001A; border: 1.5px solid #8F001A;
           border-radius: 8px; padding: 7px 14px; font-weight: 600; }
  #res { font-size: 12px; color: #57534e; margin-top: 6px; }
</style></head><body>
<header>
  <h1>&#127919; PongNews Research Radar</h1>
  <small id="hdr">loading backlog...</small>
</header>
<main>
  <p style="font-size:13px;color:#57534e">Ranked story candidates from expanded
  PubMed sweeps (table tennis, racket sports, open-skill science, exergaming).
  Deduped against all 76 published articles + research bank.</p>
  <button onclick="doScan()">&#128260; Rescan PubMed</button>
  <span id="res"></span>
  <div id="list" style="margin-top:12px"></div>
</main>
<script>
async function load() {
  const r = await fetch('/api/candidates');
  const rows = await r.json();
  document.getElementById('hdr').textContent =
    rows.length + ' stories ready · top score ' + (rows[0] ? rows[0].score : '-');
  const el = document.getElementById('list');
  el.innerHTML = '';
  for (const c of rows) {
    const colors = {1:'#8F001A',2:'#B45309',3:'#1D4ED8',4:'#047857'};
    const labels = {1:'TT direct',2:'Racket',3:'Open-skill',4:'Exergame'};
    const d = document.createElement('div');
    d.className = 'card';
    d.innerHTML =
      '<div class="meta">' +
      '<span class="chip score">' + c.score + '</span>' +
      '<span class="chip" style="background:' + colors[c.tier] + '">T' + c.tier + ' ' + labels[c.tier] + '</span>' +
      '<span class="chip cat">' + esc(c.category) + '</span></div>' +
      '<h2>' + esc(c.title) + '</h2>' +
      '<div class="jrnl">' + esc(c.journal) + ' &middot; ' + esc(c.pubdate) + '</div>' +
      '<div class="angle">&#128161; ' + esc(c.angle) + '</div>' +
      '<details><summary>Abstract</summary><p>' + esc(c.abstract.slice(0, 700)) + '...</p></details>' +
      '<p><a class="pmid" target="_blank" rel="noopener" href="https://pubmed.ncbi.nlm.nih.gov/' + c.pmid + '/">PMID ' + c.pmid + ' &#8599;</a></p>';
    el.appendChild(d);
  }
}
function esc(s) {
  return (s || '').replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
}
async function doScan() {
  const res = document.getElementById('res');
  res.textContent = ' scanning PubMed (takes ~60s)...';
  await fetch('/api/scan', {method: 'POST'});
  setTimeout(poll, 5000);
}
async function poll() {
  const s = await (await fetch('/api/scan/status')).json();
  if (s.running) { document.getElementById('res').textContent = ' scanning...'; setTimeout(poll, 5000); return; }
  const r = s.last_result || {};
  document.getElementById('res').textContent = r.error
    ? (' scan failed: ' + r.error)
    : (' done: ' + r.new + ' new candidates, backlog ' + r.backlog);
  load();
}
load();
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    return PAGE
