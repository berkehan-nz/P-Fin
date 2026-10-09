/* ADAYLAR — kompakt liste, hızlı sekmeler, arama.
 *
 * Eskiden 139 kart alt alta diziliyordu (telefonda ~59.000 px) ve her
 * kartta 8-12 renkli öğe vardı. Şimdi varsayılan bir LİSTE: satır başına
 * sembol, ad, sektör, puan, karar ve tek satırlık "neden ucuz". Ayrıntı
 * şirket sayfasında. Kart görünümü isteğe bağlı ve sade.
 */
window.ViewCandidates = (function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const F = Fmt;
  const PAGE = 30;

  let rows = [];
  let watchSet = new Set();
  let portSet = new Set();
  let shown = PAGE;
  const state = {
    quick: DataLayer.prefs.get('candQuick', 'all'),
    mode: DataLayer.prefs.get('candMode', 'list'),
    q: '', sector: '', track: '', minScore: '', sort: 'total', watchOnly: false, portOnly: false,
  };

  async function render() {
    const [cand, wl, port] = await Promise.all([
      DataLayer.candidates(), DataLayer.watchlist(), DataLayer.portfolio(),
    ]);
    const seen = new Set();
    rows = [...(cand.seed || []), ...(cand.candidates || []), ...(cand.manual || [])].filter((r) => {
      const k = String(r.ticker).toUpperCase();
      if (seen.has(k)) return false;
      seen.add(k); return true;
    });
    watchSet = new Set((wl.entries || []).filter((e) => e.active !== false).map((e) => String(e.ticker).toUpperCase()));
    portSet = new Set((port.positions || []).map((p) => String(p.ticker).toUpperCase()));
    shown = PAGE;

    const sectors = [...new Set(rows.map((r) => r.sector).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'tr'));
    $('candidatesBody').innerHTML = `
      <div class="page-head"><h1>Adaylar</h1><span class="sub" id="candCount"></span></div>
      ${partialBand(cand.partial)}
      <div class="toolbar">
        <input type="search" id="cSearch" placeholder="Sembol ya da şirket ara" aria-label="Ara" value="${F.esc(state.q)}">
        <div class="seg" role="group" aria-label="Hızlı filtre">
          ${[['decided', 'Kararım'], ['claude', 'Claude notu var'], ['all', 'Hepsi']].map(([k, l]) =>
            `<button data-quick="${k}" aria-pressed="${state.quick === k}">${l}</button>`).join('')}
        </div>
        <div class="seg" role="group" aria-label="Görünüm">
          <button data-mode="list" aria-pressed="${state.mode === 'list'}">Liste</button>
          <button data-mode="cards" aria-pressed="${state.mode === 'cards'}">Kart</button>
        </div>
        <button id="addCompany" class="ghost">+ Şirket ekle</button>
      </div>
      <details class="fold" id="filterBox" style="margin:0 0 12px"><summary>Ayrıntılı filtre<span class="count" id="filterHint"></span></summary>
        <div class="fold-body"><div class="filter-grid">
          <label>Sektör<select id="fSector"><option value="">Hepsi</option>${sectors.map((s) =>
            `<option value="${F.esc(s)}"${state.sector === s ? ' selected' : ''}>${F.esc(F.tr(s))}</option>`).join('')}</select></label>
          <label>Tür<select id="fTrack"><option value="">Hepsi</option>
            <option value="A">Kârlı</option><option value="B">Büyüyen</option><option value="both">İkisi de</option></select></label>
          <label>En düşük puan<input type="number" id="fMin" min="0" max="100" step="5" inputmode="numeric" placeholder="0"></label>
          <label>Sırala<select id="fSort">
            <option value="total">Puan</option><option value="value">Ucuzluk</option>
            <option value="momentum">Momentum</option><option value="updated">Güncellenme</option>
            <option value="ticker">Sembol</option></select></label>
          <label class="inline"><input type="checkbox" id="fWatch"> Yalnızca izleme listesi</label>
          <label class="inline"><input type="checkbox" id="fPort"> Yalnızca portföy</label>
        </div></div></details>
      <div id="candList"></div>`;

    $('fTrack').value = state.track;
    $('fMin').value = state.minScore;
    $('fSort').value = state.sort;
    $('fWatch').checked = state.watchOnly;
    $('fPort').checked = state.portOnly;
    wire();
    apply();
  }

  /* Tarama sürerken liste geçicidir — tek satırda söylenir. */
  function partialBand(partial) {
    if (!partial || !partial.is_partial) return '';
    const h = F.hoursSince(partial.last_batch_at);
    const stalled = h !== null && h >= 6;
    return `<div class="band ${stalled ? 'warn' : 'info'}"><span class="ico">${stalled ? '!' : 'i'}</span><span>
      Liste geçici: evren taraması ${F.esc(F.share(partial.pct, 0))}'de. Puanlar havuz büyüdükçe değişebilir.
      ${stalled ? ` Son parti ${F.esc(F.sinceLabel(partial.last_batch_at))} işlendi.` : ''}</span></div>`;
  }

  function wire() {
    $('cSearch').addEventListener('input', (e) => { state.q = e.target.value.trim(); shown = PAGE; apply(); });
    document.querySelectorAll('[data-quick]').forEach((b) => b.addEventListener('click', () => {
      state.quick = b.dataset.quick;
      DataLayer.prefs.set('candQuick', state.quick);
      document.querySelectorAll('[data-quick]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
      shown = PAGE; apply();
    }));
    document.querySelectorAll('[data-mode]').forEach((b) => b.addEventListener('click', () => {
      state.mode = b.dataset.mode;
      DataLayer.prefs.set('candMode', state.mode);
      document.querySelectorAll('[data-mode]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
      apply();
    }));
    const bind = (id, key, read) => $(id).addEventListener('input', () => { state[key] = read($(id)); shown = PAGE; apply(); });
    bind('fSector', 'sector', (e) => e.value);
    bind('fTrack', 'track', (e) => e.value);
    bind('fMin', 'minScore', (e) => e.value);
    bind('fSort', 'sort', (e) => e.value);
    bind('fWatch', 'watchOnly', (e) => e.checked);
    bind('fPort', 'portOnly', (e) => e.checked);
    $('addCompany').addEventListener('click', openAddCompany);
  }

  function filtered() {
    const q = state.q.toLocaleLowerCase('tr');
    const min = parseFloat(state.minScore);
    return rows.filter((r) => {
      const t = String(r.ticker).toUpperCase();
      if (state.quick === 'decided' && !r.decision) return false;
      if (state.quick === 'claude' && !r.claude_verdict) return false;
      if (q && !(t.toLocaleLowerCase('tr').includes(q) || String(r.name || '').toLocaleLowerCase('tr').includes(q))) return false;
      if (state.sector && r.sector !== state.sector) return false;
      if (state.track && r.track !== state.track) return false;
      if (!isNaN(min) && !(((r.scores || {}).total) >= min)) return false;
      if (state.watchOnly && !watchSet.has(t)) return false;
      if (state.portOnly && !portSet.has(t)) return false;
      return true;
    }).sort(sorter(state.sort));
  }

  function sorter(key) {
    const sc = (r, k) => { const v = (r.scores || {})[k]; return F.isNum(v) ? v : -1; };
    if (key === 'value') return (a, b) => sc(b, 'value') - sc(a, 'value');
    if (key === 'momentum') return (a, b) => sc(b, 'momentum') - sc(a, 'momentum');
    if (key === 'updated') return (a, b) => String(b.as_of || '').localeCompare(String(a.as_of || ''));
    if (key === 'ticker') return (a, b) => String(a.ticker).localeCompare(String(b.ticker));
    return (a, b) => sc(b, 'total') - sc(a, 'total');
  }

  function apply() {
    const list = filtered();
    const active = [state.sector, state.track, state.minScore, state.watchOnly, state.portOnly].filter(Boolean).length;
    $('filterHint').textContent = active ? `${active} filtre açık` : '';
    $('candCount').textContent = `${list.length} / ${rows.length} şirket`;
    const page = list.slice(0, shown);
    const body = state.mode === 'cards' ? cards(page) : listHtml(page);
    const more = list.length > page.length
      ? `<div class="more"><button id="moreRows">${Math.min(PAGE, list.length - page.length)} daha göster</button></div>` : '';
    $('candList').innerHTML = list.length ? body + more
      : `<div class="card muted">Bu filtrelere uyan şirket yok.</div>`;
    $('candList').querySelectorAll('[data-ticker]').forEach((el) => {
      const go = () => App.go(`sirket/${el.dataset.ticker}`);
      el.addEventListener('click', go);
      el.addEventListener('keydown', (e) => { if (e.key === 'Enter') go(); });
    });
    const m = $('moreRows');
    if (m) m.addEventListener('click', () => { shown += PAGE; apply(); });
  }

  function why(r) { return F.tr(r.why_cheap || ''); }

  function marks(r) {
    const t = String(r.ticker).toUpperCase();
    return [portSet.has(t) && 'portföyde', watchSet.has(t) && 'izleniyor', r.claude_verdict && 'Claude notu']
      .filter(Boolean).join(' · ');
  }

  function listHtml(list) {
    return `<div class="card flush">
      <div class="list-head"><span>Şirket</span><span class="sec">Sektör</span><span class="r">Puan</span><span>Karar</span><span class="whyh">Neden ucuz</span></div>
      <ul class="clist">${list.map((r) => {
        const m = marks(r);
        return `<li data-ticker="${F.esc(r.ticker)}" tabindex="0">
          <span class="t"><b>${F.esc(r.ticker)}</b><span class="sub">${F.esc(r.name || '')}${m ? ` · ${F.esc(m)}` : ''}</span></span>
          <span class="sec">${F.esc(F.tr(r.sector || ''))}</span>
          <span class="score">${F.isNum((r.scores || {}).total) ? F.esc(F.int(r.scores.total)) : ''}</span>
          <span>${F.decisionBadge(r.decision)}</span>
          <span class="why">${F.esc(why(r))}</span></li>`;
      }).join('')}</ul></div>`;
  }

  function cards(list) {
    return `<div class="cgrid">${list.map((r) => `<article class="card ccard" data-ticker="${F.esc(r.ticker)}" tabindex="0">
      <div class="top"><div style="min-width:0"><b style="font-size:17px">${F.esc(r.ticker)}</b>
        <div class="small muted">${F.esc(r.name || '')}</div></div>${Charts.scoreRing((r.scores || {}).total)}</div>
      <div class="spread"><span class="num">${F.esc(F.money(r.price))}</span>
        ${Charts.sparkline(r.sparkline, { w: 100, h: 24, accent: portSet.has(String(r.ticker).toUpperCase()) })}</div>
      ${why(r) ? `<div class="why">${F.esc(why(r))}</div>` : ''}
      ${r.decision ? `<div>${F.decisionBadge(r.decision)}</div>` : ''}
    </article>`).join('')}</div>`;
  }

  /* ------------------------------------------------ şirket ekleme formu */
  function openAddCompany() {
    App.modal(`
      <h2>Şirket ekle</h2>
      <p class="muted small">Pano dosyaya yazamaz. Bu parçayı sohbette Claude'a ver ya da
        <code>data/watchlist.json</code> içindeki <code>entries</code> dizisine ekle.</p>
      <div class="form-grid">
        <label>Sembol<input id="wlTicker" placeholder="NVDA" autocomplete="off"></label>
        <label>Etiketler<input id="wlTags" placeholder="yarı iletken, izle"></label>
        <label class="full">Neden izliyoruz?<input id="wlReason"></label>
        <label class="full">JSON parçası<textarea id="wlOut" rows="8" readonly></textarea></label>
      </div>
      <div class="row" style="margin-top:12px">
        <button id="wlCopy" class="primary">Kopyala</button>
        <a href="${DataLayer.editUrl('data/watchlist.json')}" target="_blank" rel="noopener"><button>GitHub'da aç</button></a>
        <button id="wlClose" class="ghost" style="margin-left:auto">Kapat</button>
      </div>`, (root) => {
      const upd = () => {
        root.querySelector('#wlOut').value = JSON.stringify({
          ticker: (root.querySelector('#wlTicker').value || '').toUpperCase().trim(),
          added_date: new Date().toISOString().slice(0, 10), added_by: 'berke',
          reason: root.querySelector('#wlReason').value.trim(),
          tags: root.querySelector('#wlTags').value.split(',').map((s) => s.trim()).filter(Boolean),
          active: true,
        }, null, 2);
      };
      ['wlTicker', 'wlReason', 'wlTags'].forEach((id) => root.querySelector('#' + id).addEventListener('input', upd));
      upd();
      root.querySelector('#wlCopy').addEventListener('click', () => App.copy(root.querySelector('#wlOut').value, 'JSON parçası kopyalandı'));
      root.querySelector('#wlClose').addEventListener('click', App.closeModal);
    });
  }

  return { render };
})();
