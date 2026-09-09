/* 2. ADAYLAR — kart izgarasi + yogun tablo, filtreler, siralama. */
window.ViewCandidates = (function () {
  'use strict';
  const $ = (id) => document.getElementById(id);

  let rows = [];          // tum adaylar (tohum + huni + elle)
  let watchSet = new Set();
  let portSet = new Set();
  let mode = DataLayer.prefs.get('candidateView', 'grid');

  async function render() {
    const [cand, wl, port] = await Promise.all([
      DataLayer.candidates(), DataLayer.watchlist(), DataLayer.portfolio(),
    ]);

    rows = [
      ...(cand.seed || []).map((r) => ({ ...r, group: 'seed' })),
      ...(cand.candidates || []).map((r) => ({ ...r, group: 'funnel' })),
      ...(cand.manual || []).map((r) => ({ ...r, group: 'manual' })),
    ];
    // Ayni sembol iki listede olabilir (tohum + huni) — bir kez goster
    const seen = new Set();
    rows = rows.filter((r) => {
      const key = String(r.ticker).toUpperCase();
      if (seen.has(key)) return false;
      seen.add(key); return true;
    });

    watchSet = new Set((wl.entries || []).filter((e) => e.active !== false)
                                          .map((e) => String(e.ticker).toUpperCase()));
    portSet = new Set((port.positions || []).map((p) => String(p.ticker).toUpperCase()));

    fillSectorFilter();
    bindOnce();
    apply();
  }

  function fillSectorFilter() {
    const sectors = [...new Set(rows.map((r) => r.sector).filter(Boolean))].sort();
    const sel = $('fSector');
    const current = sel.value;
    sel.innerHTML = '<option value="">Hepsi</option>' +
      sectors.map((s) => `<option value="${Fmt.esc(s)}">${Fmt.esc(s)}</option>`).join('');
    sel.value = current;
  }

  let bound = false;
  function bindOnce() {
    if (bound) return;
    bound = true;
    ['fSector', 'fTrack', 'fSource', 'fDecision', 'fMinScore', 'fSort',
     'fWatchOnly', 'fPortfolioOnly'].forEach((id) =>
      $(id).addEventListener('input', apply));
    $('fReset').addEventListener('click', () => {
      ['fSector', 'fTrack', 'fSource', 'fDecision', 'fMinScore'].forEach((id) => $(id).value = '');
      $('fWatchOnly').checked = false; $('fPortfolioOnly').checked = false;
      $('fSort').value = 'total';
      apply();
    });
    $('viewGrid').addEventListener('click', () => setMode('grid'));
    $('viewTable').addEventListener('click', () => setMode('table'));
    $('addCompany').addEventListener('click', openAddCompany);
    setMode(mode, true);
  }

  function setMode(m, silent) {
    mode = m;
    DataLayer.prefs.set('candidateView', m);
    $('viewGrid').setAttribute('aria-pressed', String(m === 'grid'));
    $('viewTable').setAttribute('aria-pressed', String(m === 'table'));
    $('candidateGrid').hidden = m !== 'grid';
    $('candidateTable').hidden = m !== 'table';
    if (!silent) apply();
  }

  function apply() {
    const f = {
      sector: $('fSector').value,
      track: $('fTrack').value,
      source: $('fSource').value,
      decision: $('fDecision').value,
      minScore: parseFloat($('fMinScore').value),
      sort: $('fSort').value,
      watchOnly: $('fWatchOnly').checked,
      portfolioOnly: $('fPortfolioOnly').checked,
    };

    let out = rows.filter((r) => {
      const t = String(r.ticker).toUpperCase();
      if (f.sector && r.sector !== f.sector) return false;
      if (f.track && r.track !== f.track) return false;
      if (f.source === 'seed' && r.group !== 'seed') return false;
      if (f.source === 'funnel' && r.group !== 'funnel') return false;
      if (f.source === 'manual' && r.group !== 'manual') return false;
      if (f.decision === '__none__' && r.decision) return false;
      if (f.decision && f.decision !== '__none__' && r.decision !== f.decision) return false;
      if (!isNaN(f.minScore) && !((r.scores || {}).total >= f.minScore)) return false;
      if (f.watchOnly && !watchSet.has(t)) return false;
      if (f.portfolioOnly && !portSet.has(t)) return false;
      return true;
    });

    out.sort(sorter(f.sort));

    $('candidateCount').textContent =
      `${out.length} / ${rows.length} sirket gosteriliyor` +
      (rows.length ? '' : ' — veri hatti henuz calismadi');

    if (mode === 'grid') renderGrid(out); else renderTable(out);
  }

  function sorter(key) {
    const sc = (r, k) => { const v = (r.scores || {})[k]; return Fmt.isNum(v) ? v : -1; };
    const hm = (r, k) => { const c = (r.headline || {})[k]; return c && Fmt.isNum(c.value) ? c.value : -Infinity; };
    switch (key) {
      case 'value':    return (a, b) => sc(b, 'value') - sc(a, 'value');
      case 'growth':   return (a, b) => hm(b, 'rev_growth_ttm') - hm(a, 'rev_growth_ttm');
      case 'momentum': return (a, b) => sc(b, 'momentum') - sc(a, 'momentum');
      case 'updated':  return (a, b) => String(b.as_of || '').localeCompare(String(a.as_of || ''));
      case 'ticker':   return (a, b) => String(a.ticker).localeCompare(String(b.ticker));
      default:         return (a, b) => sc(b, 'total') - sc(a, 'total');
    }
  }

  /* ------------------------------------------------------------ izgara */
  function renderGrid(list) {
    if (!list.length) { $('candidateGrid').innerHTML = emptyState(); return; }
    $('candidateGrid').innerHTML = list.map(cardHtml).join('');
    $('candidateGrid').querySelectorAll('[data-ticker]').forEach((el) =>
      el.addEventListener('click', () => { location.hash = `#/company/${el.dataset.ticker}`; }));
  }

  function cardHtml(r) {
    const s = r.scores || {};
    const stale = Fmt.isNum(r.story_age_days) && r.story_age_days > 30;
    const verdict = r.claude_verdict
      ? `<div class="verdict ${stale ? 'stale' : ''}">${Fmt.esc(r.claude_verdict)}
         ${stale ? `<span class="tiny dim"> · ${r.story_age_days} gun once</span>` : ''}</div>`
      : `<div class="verdict stale">Claude notu yok</div>`;

    const headline = Object.entries(r.headline || {}).map(([k, cell]) => `
      <div class="hm"><div class="k">${Fmt.esc(Fmt.label(k))}</div>
        <div class="v ${cell ? 'c-' + (cell.color || 'gray') : 'c-gray'}">
          <span class="arrow">${Fmt.arrow(k, cell && cell.color)}</span>
          ${Fmt.esc(Fmt.metricValue(k, cell && cell.value))}</div></div>`).join('');

    const subs = ['value', 'quality', 'safety', 'momentum', 'earnings_quality']
      .map((k) => `<div class="subscore"><div class="k">${
        { value: 'Ucuz', quality: 'Kalite', safety: 'Saglam',
          momentum: 'Mom', earnings_quality: 'Kazanc' }[k]}</div>
        ${Charts.miniBar(s[k])}</div>`).join('');

    const badges = [
      Fmt.trackBadge(r.track),
      r.group === 'seed' ? '<span class="chip gray">tohum</span>' : '',
      r.group === 'manual' ? '<span class="chip gray">elle</span>' : '',
      watchSet.has(String(r.ticker).toUpperCase()) ? '<span class="chip accent">izliyor</span>' : '',
      portSet.has(String(r.ticker).toUpperCase()) ? '<span class="chip green">portfoy</span>' : '',
      Fmt.decisionBadge(r.decision),
      r.warning_count ? `<span class="chip yellow" title="${Fmt.esc((r.warnings || []).join(' | '))}">⚠ ${r.warning_count}</span>` : '',
      r.data_quality === 'kotu'
        ? '<span class="chip red" title="Veri kalitesi dusuk — sayilara guvenme, detaya bak">veri şüpheli</span>'
        : r.data_quality === 'sinirli'
        ? '<span class="chip gray" title="Bazi alanlar eksik veya dogrulanmali">veri sınırlı</span>' : '',
    ].filter(Boolean).join(' ');

    return `<article class="co-card" data-ticker="${Fmt.esc(r.ticker)}" tabindex="0">
      <div class="co-head">
        <div style="min-width:0">
          <div class="co-ticker">${Fmt.esc(r.ticker)}</div>
          <div class="co-name">${Fmt.esc(r.name)}</div>
          <div class="tiny dim" style="margin-top:3px">${Fmt.esc(r.sector)} ·
            ${Fmt.money(r.market_cap_musd, { musd: true })}</div>
        </div>
        ${Charts.scoreRing(s.total)}
      </div>
      <div class="subscores">${subs}</div>
      <div class="headline-metrics">${headline}</div>
      <div class="spread">
        <span class="num" style="font-size:15px;font-weight:600">
          ${Fmt.money(r.price, { digits: 2 })}</span>
        ${Charts.sparkline(r.sparkline, { w: 100, h: 26, color: 'auto' })}
      </div>
      ${r.why_cheap ? `<span class="chip gray">${Fmt.esc(r.why_cheap)}</span>` : ''}
      ${verdict}
      <div class="row" style="gap:4px">${badges}</div>
    </article>`;
  }

  /* ------------------------------------------------------- yogun tablo */
  function renderTable(list) {
    if (!list.length) { $('candidateTable').innerHTML = emptyState(); return; }
    const cols = ['ev_ebit', 'ev_sales', 'fcf_yield_ev', 'rev_growth_ttm',
                  'gross_margin', 'roic', 'rule_of_40', 'piotroski_f',
                  'altman_z', 'beneish_m', 'net_debt_to_ebitda', 'sbc_to_fcf'];

    $('candidateTable').innerHTML = `<table>
      <thead><tr>
        <th>Sembol</th><th>Puan</th><th>Kol</th><th>Sektor</th><th>Fiyat</th>
        ${cols.map((c) => `<th title="${Fmt.esc((Fmt.spec(c) || {}).help || '')}">${Fmt.esc(Fmt.label(c))}</th>`).join('')}
        <th>Karar</th>
      </tr></thead>
      <tbody>${list.map((r) => `<tr data-ticker="${Fmt.esc(r.ticker)}" style="cursor:pointer">
        <td><b>${Fmt.esc(r.ticker)}</b><div class="tiny dim">${Fmt.esc((r.name || '').slice(0, 26))}</div></td>
        <td class="num">${Fmt.isNum((r.scores || {}).total) ? Math.round(r.scores.total) : '—'}</td>
        <td>${Fmt.trackBadge(r.track)}</td>
        <td class="tiny">${Fmt.esc(r.sector)}</td>
        <td class="num">${Fmt.money(r.price, { digits: 2 })}</td>
        ${cols.map((c) => {
          const cell = (r.headline || {})[c];
          return `<td class="num ${cell ? 'c-' + (cell.color || 'gray') : 'c-gray'}">${
            cell ? Fmt.esc(Fmt.metricValue(c, cell.value)) : '<span class="dim">·</span>'}</td>`;
        }).join('')}
        <td>${Fmt.decisionBadge(r.decision) || '<span class="dim">—</span>'}</td>
      </tr>`).join('')}</tbody></table>
      <div class="tiny dim" style="padding:8px 10px">
        Yogun tabloda yalnizca kol basina ozet metrikler dolu gelir;
        tum metrikler icin sirket detayina gec.</div>`;

    $('candidateTable').querySelectorAll('[data-ticker]').forEach((el) =>
      el.addEventListener('click', () => { location.hash = `#/company/${el.dataset.ticker}`; }));
  }

  function emptyState() {
    return `<div class="empty-state">
      <h2>Henuz aday yok</h2>
      <p>Veri hatti bu ortamda calismadi. Kartlari doldurmak icin:</p>
      <ol>
        <li>GitHub'da <b>Actions</b> sekmesine gec</li>
        <li><b>Bootstrap (tohum listesi)</b> is akisini sec</li>
        <li><b>Run workflow</b> ile calistir — 36 tohum sirket icin kart uretir</li>
      </ol>
      <p class="tiny">Yerelde: <code>python -m src.run_seed</code></p>
    </div>`;
  }

  /* ------------------------------------------------- sirket ekleme formu */
  function openAddCompany() {
    App.modal(`
      <h2>Sirket ekle</h2>
      <p class="muted small">Dashboard statik oldugu icin dosyaya dogrudan yazamaz.
        Asagidaki JSON parcasini ya Claude Code'a yapistir, ya da GitHub
        duzenleyicisinde <code>data/watchlist.json</code> icindeki
        <code>entries</code> dizisine ekle.</p>
      <div class="form-grid">
        <label>Sembol<input id="wlTicker" placeholder="NVDA" autocomplete="off"></label>
        <label>Etiket<input id="wlTags" placeholder="yari-iletken, izle"></label>
        <label class="full">Neden izliyoruz?
          <input id="wlReason" placeholder="Ornegin: veri merkezi buyumesi yavasliyor mu"></label>
        <label class="full">JSON parcasi
          <textarea id="wlOut" rows="9" readonly></textarea></label>
      </div>
      <div class="row" style="margin-top:12px">
        <button id="wlCopy" class="primary">Kopyala</button>
        <a href="${DataLayer.editUrl('data/watchlist.json')}" target="_blank"
           rel="noopener"><button>GitHub'da ac</button></a>
        <button id="wlClose" class="ghost" style="margin-left:auto">Kapat</button>
      </div>`, (root) => {
      const upd = () => {
        const tags = root.querySelector('#wlTags').value
          .split(',').map((s) => s.trim()).filter(Boolean);
        root.querySelector('#wlOut').value = JSON.stringify({
          ticker: (root.querySelector('#wlTicker').value || '').toUpperCase().trim(),
          added_date: new Date().toISOString().slice(0, 10),
          added_by: 'berke',
          reason: root.querySelector('#wlReason').value.trim(),
          tags,
          active: true,
        }, null, 2);
      };
      ['wlTicker', 'wlReason', 'wlTags'].forEach((id) =>
        root.querySelector('#' + id).addEventListener('input', upd));
      upd();
      root.querySelector('#wlCopy').addEventListener('click', () =>
        App.copy(root.querySelector('#wlOut').value, 'JSON parcasi kopyalandi'));
      root.querySelector('#wlClose').addEventListener('click', App.closeModal);
    });
  }

  return { render };
})();
