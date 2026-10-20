/* PLAN — "stratejim ne, sırada ne var, hangi kurda ne olur?"
 *
 *   1. Hedef dağılım: her tür için şimdi / hedef / dolar farkı
 *   2. Sıradaki adımlar: alımlar, vadeler (14 gün kala yenileme koşulları),
 *      faz geçişleri; piyasa takvimi katlanmış
 *   3. Kur senaryosu: vadede USD/TRY kaç olursa mevduat dolarda ne eder,
 *      dolarda (SGOV) kalsaydın ne olurdu — sürüklenebilir
 *   4. Yol haritası: fazlar ve hedef ağırlıklar
 *   5. Alternatiflerle kıyas: aynı para hep TL / SGOV / QQQ'da olsaydı
 */
window.ViewPlan = (function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const F = Fmt;

  const ORDER = ['tl', 'cekirdek_etf', 'sgov', 'motor', 'nakit'];
  const PHASE_COLS = ['motor', 'cekirdek_etf', 'sgov', 'tl'];
  const BENCH = {
    tl:   { key: 'all_tl_usd',   label: 'Hepsi TL mevduatta', short: 'TL' },
    sgov: { key: 'all_sgov_usd', label: "Hepsi SGOV'da",     short: 'SGOV' },
    qqq:  { key: 'all_qqq_usd',  label: "Hepsi QQQ'da",      short: 'QQQ' },
  };
  // İlk 90 günde kıyaslar anlamlı değil: 10 günlük fark kur gürültüsü.
  const EARLY_DAYS = 90;

  async function render() {
    const [port, hist] = await Promise.all([DataLayer.portfolio(), DataLayer.portfolioHistory()]);
    const s = port.summary || {};
    const phase = s.phase || {};
    const left = F.daysUntil(phase.end);

    $('planBody').innerHTML = `
      <div class="page-head"><h1>Plan</h1>
        <span class="sub">${F.esc(F.phaseLabel(phase))}${phase.end ? ` · ${F.esc(F.date(phase.end))}'a kadar${F.isNum(left) ? ` (${F.esc(left)} gün)` : ''}` : ''}</span></div>
      ${allocation(port)}
      ${steps(port)}
      ${scenario(port)}
      ${roadmap(phase)}
      <div id="benchBox"></div>`;

    wireScenario(port);
    bench(hist.rows || [], port.performance || {});
  }

  /* ------------------------------------------------------ hedef dağılım */
  function nextTarget(key, phase) {
    const phases = (App.thresholds.portfolio || {}).phases || [];
    const i = phases.findIndex((p) => p.key === phase.key);
    const nx = i >= 0 ? phases[i + 1] : null;
    return nx ? { ph: nx, pct: (nx.targets || {})[key] } : null;
  }

  function allocation(port) {
    const s = port.summary || {};
    const total = s.portfolio_value_usd || (port.performance || {}).value_usd || 0;
    const by = Object.fromEntries((s.slices || []).map((x) => [x.slice, x]));
    const band = ((App.thresholds.portfolio || {}).slice_drift_warn_pp) || 5;
    const sliceOf = Object.fromEntries((port.positions || []).map((p) => [p.ticker, p.slice]));

    const rows = ORDER.filter((k) => by[k]).map((k) => {
      const x = by[k];
      const actual = x.actual_pct || 0;
      const tgt = x.target_pct;
      let note = '';
      if (k === 'nakit') {
        note = 'hedef dışı';
      } else if (F.isNum(tgt)) {
        const gap = ((actual - tgt) / 100) * total;
        const nx = nextTarget(k, s.phase || {});
        if (tgt === 0 && actual === 0) {
          note = nx && nx.pct ? `şimdilik yok · ${F.phaseLabel(nx.ph)}'de hedef ${F.share(nx.pct, 0)}` : 'şimdilik yok';
        } else if (Math.abs(gap) < 1) {
          note = 'hedefte';
        } else {
          note = `≈ ${F.money(Math.abs(gap), { digits: 0 })} ${gap > 0 ? 'fazla' : 'eksik'}`;
          if (gap < 0) {
            const buy = (port.actions || []).find((a) => a.kind === 'alim' && a.ticker && sliceOf[a.ticker] === k);
            if (buy && F.isNum(buy.amount_usd)) {
              note += ` · ${F.date(buy.date)} ${buy.ticker} alımı ${buy.amount_usd >= Math.abs(gap) ? 'kapatır' : 'kısmen kapatır'}`;
            }
          }
          note += x.off_target ? '' : ` · ±${F.num(band, 0)} puan bandında`;
        }
      }
      return `<li class="alloc">
        <div class="alloc-top">
          <span class="name"><b>${F.esc(F.sliceLabel(k))}</b><span class="sub">${F.esc(F.sliceHint(k))}</span></span>
          <span class="nums"><b>${F.esc(F.share(actual))}</b>${F.isNum(tgt) ? ` <span class="dim">/ hedef ${F.esc(F.share(tgt, 0))}</span>` : ''}</span>
        </div>
        <div class="alloc-bar" role="img" aria-label="${F.esc(`${F.sliceLabel(k)}: şimdi ${F.share(actual)}${F.isNum(tgt) ? `, hedef ${F.share(tgt, 0)}` : ''}`)}">
          <i style="width:${Math.min(actual, 100)}%"></i>${F.isNum(tgt) && k !== 'nakit' ? `<span class="tgt" style="left:${Math.min(tgt, 100)}%"></span>` : ''}
        </div>
        <div class="alloc-note">${x.off_target ? F.badge('bant dışı', 'warn') + ' ' : ''}${F.esc(note)}</div>
      </li>`;
    }).join('');
    if (!rows) return '';
    return `<h2>Hedef dağılım</h2><div class="card"><ul class="allocs">${rows}</ul>
      <p class="small dim" style="margin-top:10px"><span class="tick-key"></span>hedef · bir tür hedeften ${F.esc(F.num(band, 0))} puandan fazla saparsa uyarı verilir.</p></div>`;
  }

  /* --------------------------------------------------- sıradaki adımlar */
  function steps(port) {
    const acts = (port.actions || []).filter((a) => F.isNum(a.days) && a.days >= 0)
      .sort((a, b) => a.days - b.days || (a.kind === 'vade' ? -1 : 1));
    const cal = (port.calendar || []).filter((e) => F.isNum(e.days) && e.days >= 0).sort((a, b) => a.days - b.days);
    if (!acts.length && !cal.length) return '';
    const crit = (list) => (list || []).length ? `<ul class="agenda criteria inner">${list.map((c) => {
      const b = c.status === 'green' ? F.badge('✓ sağlanıyor')
        : c.status === 'red' ? F.badge('✗ sağlanmıyor', 'bad')
        : '<span class="pending">girilmedi</span>';
      return `<li><span class="what">${F.esc(F.tr(c.label))}<span class="sub">${F.esc(F.tr(c.detail || ''))}</span></span><span>${b}</span></li>`;
    }).join('')}</ul>` : '';
    const sub = (a) => {
      if (a.kind === 'vade') {
        const m = (((port.tl_renewal || {}).maturities) || []).find((x) => x.ticker === a.ticker);
        return m ? `vadede ${F.moneyTry(m.value_try_at_maturity)} · başa baş kur ${F.num(m.usdtry_breakeven, 2)} · koşullar ${
          m.show_criteria ? 'aşağıda' : `vadeye ${(port.tl_renewal || {}).show_criteria_days || 14} gün kala görünür`}` : '';
      }
      if (a.kind === 'alim' && a.amount_usd_estimated) return 'dolar tutarı bugünkü kurla tahmin';
      return '';
    };
    const rows = acts.map((a) => `<li>
        <span class="when ${a.days <= 7 ? 'soon' : ''}">${F.esc(F.days(a.days))}</span>
        <span class="what">${F.esc(ViewToday.actionTitle(a, port))}${sub(a) ? `<span class="sub">${F.esc(sub(a))}</span>` : ''}
          ${a.kind === 'vade' ? crit(a.criteria) : ''}</span>
        <span class="date">${F.esc(F.date(a.date))}</span></li>`).join('');
    const calRows = cal.map((e) => `<li><span class="when">${F.esc(F.days(e.days))}</span>
        <span class="what">${F.esc(F.tr(e.title))}</span><span class="date">${F.esc(F.date(e.date))}</span></li>`).join('');
    return `<h2>Sıradaki adımlar</h2><div class="card"><ul class="agenda compact">${rows}</ul></div>
      ${calRows ? `<details class="fold"><summary>Piyasa takvimi<span class="count">${cal.length} olay</span></summary>
        <div class="fold-body"><ul class="agenda compact">${calRows}</ul>
        <p class="small muted" style="margin-top:8px">Ayrıntı: <a href="#/piyasa">Piyasa</a></p></div></details>` : ''}`;
  }

  /* ------------------------------------------------------- kur senaryosu */
  /* Vadede kur X ise: mevduat dolarda = vadedeki TL / X. Alternatif: aynı
     dolar giriş günü SGOV'a (T-bill getirisi) konsaydı vade günü değeri. */
  function deposits(port) {
    return (port.positions || []).filter((p) => p.tl_deposit && p.status !== 'CLOSED').map((p) => {
      const t = p.tl_deposit;
      const usd0 = t.usdtry_at_entry ? t.principal_try / t.usdtry_at_entry : null;
      const tb = F.isNum(t.tbill_pct_used) ? t.tbill_pct_used : (port.summary || {}).tbill_pct;
      const sgov = usd0 && F.isNum(tb) && t.term_days ? usd0 * (1 + (tb / 100) * (t.term_days / 365)) : null;
      return { p, t, sgov, tb };
    }).filter((d) => F.isNum(d.t.value_try_at_maturity))
      .sort((a, b) => String(a.t.maturity_date).localeCompare(String(b.t.maturity_date)));
  }

  function scenario(port) {
    const list = deposits(port);
    if (!list.length) return '';
    const now = list[0].t.usdtry_now;
    const bes = list.map((d) => d.t.usdtry_breakeven).filter(F.isNum);
    const lo = Math.floor(Math.min(now || 50, ...bes) - 2);
    const hi = Math.ceil(Math.max(now || 50, ...bes) + 3);
    const start = F.isNum(now) ? Math.round(now * 100) / 100 : lo;
    const tb = list[0].tb;
    return `<h2>Kur senaryosu</h2><div class="card scenario">
      <p class="small muted">TL mevduat vadesinde dolar kuru kaç olursa ne olur? Kaydırıcıyı sürükle.</p>
      <div class="scn-ctl">
        <label for="scnRange">Vadede USD/TRY</label>
        <input id="scnRange" type="range" min="${lo}" max="${hi}" step="0.01" value="${start}">
        <output id="scnVal" for="scnRange">${F.esc(F.num(start, 2))}</output>
      </div>
      <div class="scn-scale small dim"><span>${F.esc(F.num(lo, 0))}</span>
        <span>bugün ${F.esc(F.num(now, 2))} · başa baş ${bes.map((b) => F.esc(F.num(b, 2))).join(' / ')}</span>
        <span>${F.esc(F.num(hi, 0))}</span></div>
      <div id="scnOut"></div>
      <p class="small muted" style="margin-top:10px">Dolarda kalsaydın: aynı dolar mevduatın açıldığı gün SGOV'a
        (hazine bonosu, yıllık ${F.esc(F.share(tb, 2))}) konsaydı vadede edeceği tutar. Fark artıysa TL mevduat kazandırır.
        Başa baş kurun üstünde mevduat dolar bazında zarar ettirir.</p>
    </div>`;
  }

  function scenarioRows(port, fx) {
    const list = deposits(port);
    let tlSum = 0, altSum = 0, ok = true;
    const rows = list.map(({ t, sgov }) => {
      const usd = t.value_try_at_maturity / fx;
      const diff = F.isNum(sgov) ? usd - sgov : null;
      tlSum += usd; if (F.isNum(sgov)) altSum += sgov; else ok = false;
      const cls = !F.isNum(diff) ? '' : diff >= 0 ? 'good' : 'bad';
      return `<tr>
        <td class="lead" data-label=""><b>${F.esc(t.bank || '')} · ${F.esc(F.moneyTry(t.principal_try))}</b>
          <span class="sub">vade ${F.esc(F.date(t.maturity_date))} · vadede ${F.esc(F.moneyTry(t.value_try_at_maturity))}</span></td>
        <td class="r" data-label="Dolar karşılığı">${F.esc(F.money(usd))}</td>
        <td class="r" data-label="Dolarda kalsaydın">${F.esc(F.money(sgov))}</td>
        <td class="r" data-label="Fark"><span class="txt-${cls}">${F.esc(F.signedMoney(diff))}</span></td></tr>`;
    }).join('');
    const total = ok ? tlSum - altSum : null;
    const verdict = !F.isNum(total) ? ''
      : total >= 0 ? `Kur ${F.num(fx, 2)} olursa mevduatlar dolarda kalmaya göre <b class="txt-good">${F.esc(F.signedMoney(total))}</b> kazandırır.`
      : `Kur ${F.num(fx, 2)} olursa mevduatlar dolarda kalmaya göre <b class="txt-bad">${F.esc(F.signedMoney(total))}</b> kaybettirir.`;
    return `<p class="scn-verdict">${verdict}</p>
      <div class="table-wrap"><table class="tbl stackable">
      <thead><tr><th>Mevduat</th><th class="r">Dolar karşılığı</th><th class="r">Dolarda kalsaydın</th><th class="r">Fark</th></tr></thead>
      <tbody>${rows}</tbody></table></div>`;
  }

  function wireScenario(port) {
    const r = $('scnRange');
    if (!r) return;
    const upd = () => {
      const fx = Number(r.value);
      $('scnVal').textContent = F.num(fx, 2);
      $('scnOut').innerHTML = scenarioRows(port, fx);
    };
    r.addEventListener('input', upd);
    upd();
  }

  /* -------------------------------------------------------- yol haritası */
  function roadmap(cur) {
    const phases = ((App.thresholds.portfolio || {}).phases) || [];
    if (!phases.length) return '';
    // Tek hisselerin başladığı ilk faza aday listesi bağlantısı.
    const at = phases.findIndex((p) => p.key === cur.key);
    const first = phases.find((p, i) => i > at && (p.targets || {}).motor > 0);
    const rows = phases.map((ph) => `<tr${ph.key === cur.key ? ' class="current"' : ''}>
        <td class="lead" data-label=""><b>${F.esc(F.phaseLabel(ph))}</b>${ph.key === cur.key ? ' ' + F.badge('şu an') : ''}
          <span class="sub">${F.esc(F.date(ph.start))}${ph.end ? ` – ${F.esc(F.date(ph.end))}` : ' →'}${
            first && ph.key === first.key ? ' · <a href="#/adaylar">hisse adayları →</a>' : ''}</span></td>
        ${PHASE_COLS.map((k) => `<td class="r" data-label="${F.esc(F.sliceLabel(k))}">${F.esc(F.share((ph.targets || {})[k], 0))}</td>`).join('')}
      </tr>`).join('');
    return `<h2>Yol haritası</h2>
      <div class="card flush"><div class="table-wrap"><table class="tbl stackable roadmap">
        <thead><tr><th>Faz</th>${PHASE_COLS.map((k) => `<th class="r">${F.esc(F.sliceLabel(k))}</th>`).join('')}</tr></thead>
        <tbody>${rows}</tbody></table></div></div>
      <p class="small muted" style="margin-top:8px">Hedefler toplamı 100'den azsa kalan pay nakit olarak bekler.</p>`;
  }

  /* --------------------------------------------- alternatiflerle kıyas */
  function bench(rows, perf) {
    const host = $('benchBox');
    if (!host || perf.status !== 'aktif' || rows.length < 2) return;
    const son = rows.slice(-60);
    const gainOk = son.every((r) => F.isNum(r.invested_usd));
    let sel = DataLayer.prefs.get('ovBench', 'tl');
    if (!BENCH[sel]) sel = 'tl';
    const early = F.isNum(perf.days) && perf.days < EARLY_DAYS;
    const parts = [['TL mevduat', perf.vs_all_tl_usd], ['SGOV', perf.vs_all_sgov_usd], ['QQQ', perf.vs_all_qqq_usd]]
      .filter(([, v]) => F.isNum(v)).map(([k, v]) => `${k} ${F.esc(F.signedMoney(v, 0))}`);

    host.innerHTML = `<h2>Alternatiflerle kıyas</h2><div class="card">
      <p class="small muted">Aynı para aynı günlerde tamamen tek bir yere konsaydı. Artı: senin planın önde.${
        early ? ` <span class="dim">İlk ${EARLY_DAYS} gün kıyas anlamlı değil (kur gürültüsü).</span>` : ''}</p>
      ${parts.length ? `<div class="bench-line">Planın farkı · ${parts.join(' · ')}</div>` : ''}
      <div class="chart-head"><span class="small muted">Kazanç (yatırılan para hariç)</span>
        <div class="seg" role="group" aria-label="Kıyas">${Object.entries(BENCH).map(([k, v]) =>
          `<button data-b="${k}" aria-pressed="${k === sel}">${F.esc(v.short)}</button>`).join('')}</div></div>
      <div id="benchPlot"></div></div>`;

    const draw = () => {
      const bm = BENCH[sel];
      const less = (v, r) => (F.isNum(v) ? (gainOk ? v - r.invested_usd : v) : null);
      Charts.compare($('benchPlot'), {
        dates: son.map((r) => r.date),
        focus: { role: 'focus', label: 'Senin planın', short: 'Plan', values: son.map((r) => less(r.total_usd, r)) },
        context: { role: 'context', label: bm.label, short: bm.short,
                   values: son.map((r) => less((r.benchmarks || {})[bm.key], r)) },
        fmt: (v) => (gainOk ? F.signedMoney(v) : F.money(v)),
        fmtTick: (v) => (gainOk ? F.signedMoney(v, 0) : F.money(v, { digits: 0 })),
        fmtDate: F.date,
        diff: (a, c) => (F.isNum(a) && F.isNum(c) ? `Fark ${F.signedMoney(a - c)}` : ''),
        zero: gainOk,
        bandPct: gainOk ? 0 : 2,
        height: 150,
        aria: `Senin planının kazancı ve ${bm.label} kıyası`,
      });
    };
    host.querySelectorAll('[data-b]').forEach((btn) => btn.addEventListener('click', () => {
      sel = btn.dataset.b;
      DataLayer.prefs.set('ovBench', sel);
      host.querySelectorAll('[data-b]').forEach((x) => x.setAttribute('aria-pressed', String(x.dataset.b === sel)));
      draw();
    }));
    draw();
  }

  return { render };
})();
