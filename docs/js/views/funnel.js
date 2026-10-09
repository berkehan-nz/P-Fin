/* HUNİ — evrenden adaya giden yol, tek bakışta.
 *
 * Üstte tek satır durum ("Tur 9 · %24 · bitiş ~11 Eki") ve aşama şeridi.
 * Eleme sebepleri, Aşama 2'yi geçenler, tur geçmişi ve eşik simülasyonu
 * katlanır; varsayılan kapalı.
 */
window.ViewFunnel = (function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const F = Fmt;
  let survivors = [];
  let killGroups = [];

  async function render() {
    const [log, scan, surv] = await Promise.all([
      DataLayer.funnelLog(), DataLayer.scanState(), DataLayer.survivors(),
    ]);
    survivors = (surv && surv.survivors) || [];
    killGroups = (App.thresholds.kill_reason_groups || []).map((g) => ({ ...g, re: new RegExp(g.pattern) }));
    const runs = log.runs || [];
    const latest = runs.length ? runs[runs.length - 1] : null;
    const fromRun = latest && (latest.stages || []).length;
    const stages = fromRun ? latest.stages : stagesFromScan(scan);
    const kills = fromRun ? (latest.kill_reasons || {}) : ((scan && scan.kill_counts) || {});

    $('funnelBody').innerHTML = `
      <div class="page-head"><h1>Huni</h1></div>
      ${status(scan)}
      ${strip(stages, fromRun && latest.partial)}
      ${kinds(scan)}
      ${reasons(kills)}
      ${survivorsFold()}
      ${historyFold(scan, runs)}
      ${simFold(stages)}`;
    wireSurvivors();
    wireSim();
  }

  function total(scan) { return scan ? (scan.universe_size_at_cycle_start || (scan.queue || []).length || 0) : 0; }

  function stagesFromScan(scan) {
    const sc = (scan && scan.stage_counts) || {};
    return [0, 1, 2].filter((n) => sc[String(n)]).map((n) => ({ stage: n, input: sc[n].in, output: sc[n].out }));
  }

  /* ------------------------------------------------------ durum satırı */
  function status(scan) {
    if (!scan || !scan.queue || !scan.queue.length) {
      return '<div class="card"><span class="pending">Tarama turu henüz başlamadı.</span></div>';
    }
    const all = total(scan);
    const done = Math.min(scan.cursor || 0, all);
    const pct = all ? (done / all) * 100 : 0;
    const eta = scan.eta || {};
    const h = F.hoursSince(scan.last_batch_at);
    const stalled = h !== null && h >= 6;
    return `<div class="card">
      <div class="spread"><b style="font-size:18px">Tur ${F.esc(scan.cycle)} · ${F.esc(F.share(pct, 0))}${
        eta.eta_at ? ` · bitiş ~${F.esc(F.date(eta.eta_at))}` : ''}</b>
        <span class="small muted">${F.esc(F.int(done))} / ${F.esc(F.int(all))} şirket · Aşama 2'yi geçen ${F.esc(F.int(scan.survivor_count))}</span></div>
      <div class="progress"><i style="width:${Math.round(pct * 10) / 10}%"></i></div>
      ${stalled ? `<div class="small warn-text">Son parti ${F.esc(F.sinceLabel(scan.last_batch_at))} işlendi — tarama duraklamış olabilir.</div>` : ''}
    </div>`;
  }

  /* ------------------------------------------------------- aşama şeridi */
  function strip(stages, partial) {
    const info = App.thresholds.stage_info || {};
    const tiles = [0, 1, 2, 3, 4].map((n) => {
      const st = stages.find((s) => s.stage === n);
      const name = F.tr((info[n] || {}).name || `Aşama ${n}`);
      return `<div class="st" title="${F.esc(F.tr((info[n] || {}).plain || ''))}">
        <div class="k">${n}. ${F.esc(name)}</div>
        ${st ? `<div class="v">${F.esc(F.int(st.output))}</div><div class="s">geçti · ${F.esc(F.int(st.input))} girdi</div>`
             : '<div class="s">tur sonunda çalışır</div>'}</div>`;
    }).join('');
    return `<h2>Aşamalar</h2><div class="strip">${tiles}</div>
      ${partial ? '<p class="small muted" style="margin-top:6px">Aşama 3–4 şu anki havuza göre; tur bitince değişebilir.</p>' : ''}`;
  }

  /* Elenen ile verisi eksik olan ayrı: biri şirket hakkında yargı, diğeri bizim eksiğimiz. */
  function kinds(scan) {
    const k = (scan && scan.kill_kinds) || {};
    if (!k.ELENDI && !k.VERI_YOK) return '';
    const retry = (scan.retry_queue || []).length;
    return `<p class="small muted" style="margin-top:8px">Bu turda ${F.esc(F.int(k.ELENDI || 0))} şirket bir kurala takılarak elendi;
      ${F.esc(F.int(k.VERI_YOK || 0))} şirketin verisi eksik olduğu için karar verilemedi${retry ? ` (${retry} tanesi yeniden denenecek)` : ''}.</p>`;
  }

  /* ---------------------------------------------------- eleme sebepleri */
  function group(kills) {
    const acc = {};
    Object.entries(kills || {}).forEach(([reason, count]) => {
      const g = killGroups.find((x) => x.re.test(reason));
      const key = g ? g.label : 'Sınıflandırılmamış';
      if (!acc[key]) acc[key] = { label: key, stage: g ? g.stage : 9, plain: g ? g.plain : '', count: 0 };
      acc[key].count += count;
    });
    return Object.values(acc).sort((a, b) => b.count - a.count);
  }

  function reasons(kills) {
    const groups = group(kills);
    if (!groups.length) return '';
    const info = App.thresholds.stage_info || {};
    const by = {};
    groups.forEach((g) => { (by[g.stage] = by[g.stage] || []).push(g); });
    return `<h2>Eleme sebepleri</h2>${Object.keys(by).sort().map((s) => {
      const list = by[s];
      const sum = list.reduce((n, g) => n + g.count, 0);
      const name = s === '9' ? 'Diğer' : `${s}. ${F.tr((info[s] || {}).name || '')}`;
      return `<details class="fold"><summary>${F.esc(name)}<span class="count">${F.esc(F.int(sum))} şirket</span></summary>
        <div class="fold-body"><ul class="why-list">${list.map((g) => `<li><b>${F.esc(F.tr(g.label))}</b>
          <span class="num">${F.esc(F.int(g.count))}</span><span class="p">${F.esc(F.tr(g.plain))}</span></li>`).join('')}</ul></div></details>`;
    }).join('')}`;
  }

  /* ---------------------------------------------- Aşama 2'yi geçenler */
  function survivorsFold() {
    if (!survivors.length) return '';
    return `<details class="fold" id="survFold"><summary>Aşama 2'yi geçenler<span class="count">${survivors.length} şirket</span></summary>
      <div class="fold-body">
        <div class="toolbar"><label class="small muted">Sırala
          <select id="svSort"><option value="ticker">Sembol</option><option value="growth">Büyüme</option>
          <option value="fcf">FCF verimi</option><option value="mcap">Piyasa değeri</option></select></label></div>
        <div id="svTable"></div>
        <p class="small muted">Bu şirketlerin puanı yok — puanlama tur sonunda, sektör yüzdelikleriyle yapılır.</p></div></details>`;
  }

  function drawSurvivors() {
    const sort = $('svSort').value;
    const mv = (r, k) => { const v = (r.metrics || {})[k]; return F.isNum(v) ? v : -Infinity; };
    const rows = survivors.slice().sort({
      ticker: (a, b) => String(a.ticker).localeCompare(String(b.ticker)),
      growth: (a, b) => mv(b, 'rev_growth_ttm') - mv(a, 'rev_growth_ttm'),
      fcf: (a, b) => mv(b, 'fcf_yield_ev') - mv(a, 'fcf_yield_ev'),
      mcap: (a, b) => (b.market_cap_musd || 0) - (a.market_cap_musd || 0),
    }[sort]);
    const cols = [['rev_growth_ttm', 'Büyüme'], ['gross_margin', 'Brüt marj'], ['fcf_yield_ev', 'FCF verimi'], ['roic', 'ROIC']];
    $('svTable').innerHTML = `<div class="table-wrap"><table class="tbl stackable"><thead><tr><th>Şirket</th>
      <th class="r">Piyasa değeri</th>${cols.map(([, l]) => `<th class="r">${l}</th>`).join('')}</tr></thead>
      <tbody>${rows.map((r) => `<tr class="click" data-ticker="${F.esc(r.ticker)}">
        <td class="lead" data-label=""><b>${F.esc(r.ticker)}</b><span class="sub">${F.esc((r.name || '').slice(0, 32))} · ${F.esc(F.tr(r.sector || ''))}</span></td>
        <td class="r" data-label="Piyasa değeri">${F.esc(F.money(r.market_cap_musd, { musd: true }))}</td>
        ${cols.map(([k, l]) => `<td class="r" data-label="${l}">${F.esc(F.metricValue(k, (r.metrics || {})[k]))}</td>`).join('')}
      </tr>`).join('')}</tbody></table></div>`;
    $('svTable').querySelectorAll('[data-ticker]').forEach((el) =>
      el.addEventListener('click', () => App.go(`sirket/${el.dataset.ticker}`)));
  }

  function wireSurvivors() {
    const fold = $('survFold');
    if (!fold) return;
    let drawn = false;
    fold.addEventListener('toggle', () => { if (fold.open && !drawn) { drawn = true; drawSurvivors(); } });
    $('svSort').addEventListener('input', drawSurvivors);
  }

  /* ------------------------------------------------------ tur geçmişi */
  function historyFold(scan, runs) {
    const done = (runs || []).filter((r) => !r.partial && r.cycle).slice(-6).reverse();
    return `<details class="fold"><summary>Turlar nasıl işler<span class="count">${done.length} tamamlanan</span></summary>
      <div class="fold-body small">
        <p>Bir tur, ABD'deki ~${F.esc(F.int(total(scan)))} şirketin tamamının bir kez taranmasıdır. Tur bitince Aşama 3–4
          çalışır, aday listesi kurulur ve hemen yeni tur başlar: şirketler her çeyrek yeni bilanço açıklar, fiyatlar
          değişir. "Tur ${F.esc(scan ? scan.cycle : '')}" sistemin ${F.esc(scan ? scan.cycle : '')}. tam taraması demektir.</p>
        ${done.length ? `<ul class="agenda compact">${done.map((r) => {
          const s4 = (r.stages || []).find((x) => x.stage === 4);
          const s0 = (r.stages || []).find((x) => x.stage === 0);
          return `<li><span class="when">Tur ${F.esc(r.cycle)}</span>
            <span class="what">${s0 ? F.esc(F.int(s0.input)) : ''} şirket → ${s4 ? F.esc(F.int(s4.output)) : ''} aday</span>
            <span class="date">${F.esc(F.date(r.date))}</span></li>`; }).join('')}</ul>` : ''}
      </div></details>`;
  }

  /* ---------------------------------------------------- eşik simülasyonu */
  const SIM = [
    ['gross_margin_min_pct', 'Brüt marj alt sınırı', 0, 70, 5, '%'],
    ['rev_growth_ttm_min_pct', 'Hasılat büyümesi alt sınırı', 0, 40, 1, '%'],
    ['net_debt_to_ebitda_max', 'Net borç/FAVÖK üst sınırı', 0, 6, 0.5, 'x'],
    ['share_count_growth_max_pct', 'Hisse artışı üst sınırı', 0, 15, 1, '%'],
    ['sbc_to_fcf_max', 'SBC/FCF üst sınırı', 0, 3, 0.1, 'x'],
  ];
  const simText = (v, unit) => (unit === '%' ? F.share(v, Number.isInteger(v) ? 0 : 1) : `${F.num(v, 1)}x`);

  function simFold(stages) {
    const s1 = (App.thresholds || {}).stage1 || {};
    const st = stages.find((s) => s.stage === 1);
    return `<details class="fold"><summary>Eşik simülasyonu</summary><div class="fold-body">
      <p class="small muted">Yalnızca tahmin; veriyi değiştirmez. Aşama 1 şu an ${st ? `${F.esc(F.int(st.input))} şirketten ${F.esc(F.int(st.output))}` : ''} tanesini geçiriyor.</p>
      ${SIM.map(([key, label, min, max, step, unit]) => `<div style="margin-bottom:12px">
        <div class="spread small"><span>${F.esc(label)}</span><span class="num" id="sim-${key}">${F.esc(simText(s1[key], unit))}</span></div>
        <input type="range" data-sim="${key}" data-base="${s1[key]}" data-unit="${unit}" min="${min}" max="${max}" step="${step}" value="${s1[key]}" style="width:100%"></div>`).join('')}
      <div id="simResult" class="small"></div></div></details>`;
  }

  function wireSim() {
    const inputs = [...document.querySelectorAll('#funnelBody [data-sim]')];
    const update = () => {
      const changed = inputs.map((el) => {
        const base = parseFloat(el.dataset.base), now = parseFloat(el.value);
        $(`sim-${el.dataset.sim}`).textContent = simText(now, el.dataset.unit);
        if (now === base) return null;
        const looser = el.dataset.sim.includes('min') ? now < base : now > base;
        return { label: SIM.find((s) => s[0] === el.dataset.sim)[1], base, now, looser, unit: el.dataset.unit };
      }).filter(Boolean);
      $('simResult').innerHTML = changed.length ? `<ul class="agenda compact">${changed.map((c) => `<li>
        <span class="when">${c.looser ? 'gevşek' : 'sıkı'}</span><span class="what">${F.esc(c.label)}: ${F.esc(simText(c.base, c.unit))} → ${F.esc(simText(c.now, c.unit))}</span>
        <span class="date">${c.looser ? 'daha çok şirket geçer' : 'daha az şirket geçer'}</span></li>`).join('')}</ul>` : '';
    };
    inputs.forEach((el) => el.addEventListener('input', update));
    if (inputs.length) update();
  }

  return { render };
})();
