/* BUGÜN — "yatırımlarım bugün nasıl gitti?" tek ekranda.
 *
 * Yukarıdan aşağıya ve başka hiçbir şey yok:
 *   1. Durum bandı (yalnızca gerekirse): fiyat eski / tez kırıcı / Cuma raporu
 *   2. Değer, bugün, başlangıçtan; içinde grafik ve tek satır kıyas
 *   3. Pozisyonlar (satıra dokun → ayrıntı)
 *   4. Dilimler (tek çubuk; yalnızca bant dışı olan yazıyla)
 *   5. Bu hafta (30 gün ufuk, en fazla 3 madde)
 * Haberler, piyasa ve makro "Piyasa" sekmesinde; plan ve geçmiş "Portföy"de.
 */
window.ViewToday = (function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const F = Fmt;

  // İlk 90 günde kıyaslar anlamlı değil: 10 günlük fark kur gürültüsü.
  const EARLY_DAYS = 90;
  const SLICE_ORDER = ['motor', 'cekirdek_etf', 'sgov', 'tl', 'nakit'];
  const BENCH = {
    tl:   { key: 'all_tl_usd',   label: 'Hepsi TL mevduatta', short: 'TL' },
    sgov: { key: 'all_sgov_usd', label: "Hepsi SGOV'da",     short: 'SGOV' },
    qqq:  { key: 'all_qqq_usd',  label: "Hepsi QQQ'da",      short: 'QQQ' },
  };

  async function render() {
    const [port, hist, weekly] = await Promise.all([
      DataLayer.portfolio(), DataLayer.portfolioHistory(), DataLayer.weekly(),
    ]);
    const perf = port.performance || {};
    const rows = hist.rows || [];

    $('todayBody').innerHTML = `
      <div class="page-head"><h1>Bugün</h1>${freshness(port)}</div>
      ${bands(port, weekly)}
      <section class="card" aria-label="Portföy özeti">
        ${perf.status === 'aktif' ? hero(port, perf) : heroNotStarted(port, perf)}
        <div id="todayChart"></div>
        ${benchLine(perf)}
      </section>
      <div class="today-grid">
        <section><h2>Pozisyonlar</h2><div class="card flush">${positions(port, perf)}</div></section>
        <div>
          ${slices(port)}
          ${agenda(port)}
        </div>
      </div>`;

    chart(rows, perf);
    wirePositions();
  }

  /* ---------------------------------------------------------- tazelik */
  function freshness(port) {
    const stamp = port.priced_at || port.as_of;
    if (!stamp) return '';
    return `<span class="sub" title="Kaynak: yfinance, Stooq, FRED, Finnhub">Güncel · ${
      F.esc(port.priced_at ? F.dateTime(port.priced_at) : F.date(port.as_of))}</span>`;
  }

  /* Son ETF fiyatının tarihi ile bugün arasında kaç İŞ GÜNÜ var.
     Bugün henüz kapanmadıysa dünkü fiyat güncel sayılır. */
  function staleBusinessDays(port) {
    const days = (port.positions || []).map((p) => p.price_as_of).filter(Boolean).sort();
    if (!days.length) return 0;
    const last = new Date(`${days[days.length - 1]}T12:00:00`);
    const today = new Date(); today.setHours(12, 0, 0, 0);
    let n = 0;
    for (let d = new Date(last.getTime() + 86400000); d < today; d = new Date(d.getTime() + 86400000)) {
      if (d.getDay() !== 0 && d.getDay() !== 6) n += 1;
    }
    return n;
  }

  /* ------------------------------------------------------- durum bandı */
  function bands(port, weekly) {
    const out = [];
    const stale = staleBusinessDays(port);
    const hours = F.hoursSince(port.priced_at);
    if (stale > 0 || (hours !== null && hours > 26)) {
      const days = (port.positions || []).map((p) => p.price_as_of).filter(Boolean).sort();
      out.push(`<div class="band warn" role="status"><span class="ico">!</span><span>
        Fiyatlar ${stale > 0 ? `${stale} iş günü eski` : `${Math.floor(hours / 24)} gündür çekilmedi`}${
          days.length ? ` (son fiyat ${F.esc(F.date(days[days.length - 1]))})` : ''}.
        Otomatik koşu gecikmiş olabilir.</span></div>`);
    }
    (port.positions || []).forEach((p) => {
      (p.thesis_breakers || []).filter((b) => b && b.triggered).forEach((b) => {
        out.push(`<div class="band bad" role="alert"><span class="ico">!</span><span>
          <b>Tez kırıcı: ${F.esc(p.ticker)}</b> — ${F.esc(F.tr(b.description || ''))}
          ${b.action ? ` · ${F.esc(F.tr(b.action))}` : ''}</span></div>`);
      });
    });
    const today = new Date();
    const iso = today.toISOString().slice(0, 10);
    if (weekly && weekly.as_of === iso && today.getDay() === 5) {
      const n = weekly.action_required || 0;
      out.push(`<div class="band info"><span class="ico">i</span><span>
        <a href="#/portfoy/haftalik">Cuma raporu hazır${n ? ` · ${n} madde eylem bekliyor` : ''} →</a>
        </span></div>`);
    }
    return out.join('');
  }

  /* ------------------------------------------------------------ hero */
  function fig(label, usd, p, extra) {
    const cls = F.changeClass(p);
    return `<div class="fig"><div class="k">${F.esc(label)}</div>
      <div class="v ${cls}">${F.esc(F.signedMoney(usd))}</div>
      <div class="p ${cls}">${F.esc(F.pct(p))}</div>
      ${extra ? `<div class="x">${extra}</div>` : ''}</div>`;
  }

  function hero(port, perf) {
    const today = F.isNum(perf.day_change_usd)
      ? fig('Bugün', perf.day_change_usd, perf.day_change_pct)
      : '';
    const tlPart = F.isNum(perf.return_try_pct) ? `TL bazında ${F.esc(F.pct(perf.return_try_pct))} · ` : '';
    const since = fig('Başlangıçtan', perf.return_usd, perf.return_pct,
      `${tlPart}${F.esc(perf.days)} gün`);
    return `<div class="hero">
      <div>
        <div class="hero-label">Portföy · ${F.esc(F.date(perf.as_of))}</div>
        <div class="hero-value">${F.esc(F.money(perf.value_usd))}</div>
        <div class="hero-sub">${F.esc(F.moneyTry(perf.value_try))} · kur ${F.esc(F.num(perf.usdtry, 2))}</div>
      </div>
      <div class="hero-figs">${today}${since}</div>
    </div>`;
  }

  function heroNotStarted(port, perf) {
    const s = port.summary || {};
    const kalan = F.daysUntil(perf.inception);
    return `<div class="hero">
      <div>
        <div class="hero-label">Portföy · maliyet üzerinden</div>
        <div class="hero-value">${F.esc(F.money(s.portfolio_value_usd))}</div>
        <div class="hero-sub">${F.esc(F.moneyTry(s.portfolio_value_try))}</div>
      </div>
      <div class="hero-figs"><div class="fig"><div class="k">Başlangıç</div>
        <div class="v">${F.esc(F.date(perf.inception))}</div>
        <div class="x">${kalan > 0 ? `${kalan} gün sonra` : 'ilk kapanış fiyatı bekleniyor'}</div></div></div>
    </div>`;
  }

  function benchLine(perf) {
    if (perf.status !== 'aktif') return '';
    const parts = [
      ['TL mevduat', perf.vs_all_tl_usd],
      ['SGOV', perf.vs_all_sgov_usd],
      ['QQQ', perf.vs_all_qqq_usd],
    ].filter(([, v]) => F.isNum(v)).map(([k, v]) => `${k} ${F.esc(F.signedMoney(v, 0))}`);
    if (!parts.length) return '';
    const early = F.isNum(perf.days) && perf.days < EARLY_DAYS;
    return `<div class="bench-line" title="Senin portföyün, aynı sermaye aynı gün tamamen o varlığa konsaydı oluşacak değerden ne kadar önde (+) ya da geride (−).">
      Kıyas · ${parts.join(' · ')}${early ? ` · <span class="dim" title="${EARLY_DAYS} gün dolmadan kıyaslar anlamlı değil">erken</span>` : ''}</div>`;
  }

  /* ----------------------------------------------------------- grafik */
  function chart(rows, perf) {
    const host = $('todayChart');
    if (!host || rows.length < 2) return;
    let sel = DataLayer.prefs.get('ovBench', 'tl');
    if (!BENCH[sel]) sel = 'tl';
    const son = rows.slice(-60);
    host.innerHTML = `<div class="chart-head">
        <span class="small muted">${son.length} işlem günü${F.isNum(perf.return_pct)
          ? ` · ${F.esc(F.pct(perf.return_pct))}` : ''}</span>
        <div class="seg" role="group" aria-label="Kıyas seçimi">${Object.entries(BENCH).map(([k, v]) =>
          `<button data-b="${k}" aria-pressed="${k === sel}">${F.esc(v.short)}</button>`).join('')}</div>
      </div><div id="todayPlot"></div>`;

    const draw = () => {
      const bm = BENCH[sel];
      Charts.compare($('todayPlot'), {
        dates: son.map((r) => r.date),
        focus: { role: 'focus', label: 'Portföy', short: 'Portföy', values: son.map((r) => r.total_usd) },
        context: { role: 'context', label: bm.label, short: bm.short,
                   values: son.map((r) => (r.benchmarks || {})[bm.key]) },
        fmt: (v) => F.money(v),
        fmtTick: (v) => F.money(v, { digits: 0 }),
        fmtDate: F.date,
        diff: (a, c) => (F.isNum(a) && F.isNum(c) ? `Fark ${F.signedMoney(a - c)}` : ''),
        height: 160,
        bandPct: 2,
        aria: `Portföy değeri ve ${bm.label} kıyası`,
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

  /* ------------------------------------------------------- pozisyonlar */
  /* Aynı sembolün parçaları (30 Ekim QQQM) tek satırda toplanır. */
  function group(positions) {
    const by = new Map();
    positions.forEach((p) => {
      const g = by.get(p.ticker);
      if (!g) { by.set(p.ticker, { ...p, lots: 1 }); return; }
      g.lots += 1;
      ['shares', 'cost_usd', 'fees_usd', 'dividends_usd', 'weight_pct'].forEach((k) => {
        g[k] = (g[k] || 0) + (p[k] || 0);
      });
      g.value_usd = F.isNum(g.value_usd) && F.isNum(p.value_usd) ? g.value_usd + p.value_usd : null;
      g.pnl_usd = F.isNum(g.pnl_usd) && F.isNum(p.pnl_usd) ? g.pnl_usd + p.pnl_usd : null;
      g.pnl_pct = F.isNum(g.pnl_usd) && g.cost_usd ? (g.pnl_usd / g.cost_usd) * 100 : null;
      g.started = g.started || p.started;
    });
    return [...by.values()].sort((a, b) => (b.value_usd || 0) - (a.value_usd || 0));
  }

  function changeCell(usd, p) {
    if (!F.isNum(usd)) return '';
    const cls = F.changeClass(p);
    return `<span class="${cls}">${F.esc(F.signedMoney(usd))}</span><span class="sub ${cls}">${F.esc(F.pct(p))}</span>`;
  }

  function positions(port, perf) {
    const list = group((port.positions || []).filter((p) => p.status !== 'CLOSED'));
    if (!list.length) return '';
    const day = perf.positions_day || {};
    const s = port.summary || {};
    const nakit = (s.slices || []).find((x) => x.slice === 'nakit') || {};

    const rows = list.map((p, i) => {
      const t = p.tl_deposit;
      const d = day[p.ticker] || {};
      const name = t
        ? `<b>TL mevduat</b><span class="sub">${F.esc(t.bank || '')} · %${F.esc(F.num(t.annual_rate_pct, 0))} · vade ${
            F.esc(F.date(t.maturity_date))} (${F.esc(t.days_to_maturity)} gün)</span>`
        : `<b>${F.esc(p.ticker)}</b> <span class="dim small">${F.esc(F.num(p.shares, p.shares % 1 ? 2 : 0))} adet${
            p.lots > 1 ? ` · ${p.lots} parça` : ''}</span>`;
      const since = p.started ? changeCell(p.pnl_usd, p.pnl_pct) : '<span class="pending">başlamadı</span>';
      const firstDay = p.entry_date && p.price_as_of && p.entry_date >= p.price_as_of;
      return `<tr class="click" data-row="${i}" tabindex="0" aria-expanded="false">
          <td class="lead" data-label=""><span class="chev">›</span> ${name}</td>
          <td class="r val" data-label="Değer">${F.esc(F.money(p.value_usd))}</td>
          <td class="r" data-label="Bugün">${firstDay ? '<span class="pending">ilk gün</span>' : changeCell(d.usd, d.pct)}</td>
          <td class="r" data-label="Başlangıçtan">${since}</td>
          <td class="r" data-label="Ağırlık">${F.esc(F.share(p.weight_pct))}</td>
        </tr>
        <tr class="detail" data-detail="${i}" hidden><td colspan="5">${detail(p)}</td></tr>`;
    }).join('');

    const cash = F.isNum(s.cash_usd) ? `<tr class="muted-row">
        <td class="lead" data-label=""><span class="chev"></span> <b>Nakit</b> <span class="dim small">planlı alımlar için</span></td>
        <td class="r val" data-label="Değer">${F.esc(F.money(s.cash_usd))}</td>
        <td class="r" data-label=""></td><td class="r" data-label=""></td>
        <td class="r" data-label="Ağırlık">${F.esc(F.share(nakit.actual_pct))}</td></tr>` : '';

    return `<div class="table-wrap"><table class="tbl stackable pos-table">
      <thead><tr><th>Varlık</th><th class="r">Değer</th><th class="r">Bugün</th>
        <th class="r">Başlangıçtan</th><th class="r">Ağırlık</th></tr></thead>
      <tbody>${rows}${cash}</tbody></table></div>`;
  }

  function fact(k, v, sub) {
    if (v === '' || v === null || v === undefined) return '';
    return `<div><dt>${F.esc(k)}</dt><dd>${v}${sub ? `<span class="sub">${sub}</span>` : ''}</dd></div>`;
  }

  function detail(p) {
    const t = p.tl_deposit;
    if (t) {
      const stopaj = p.withholding_confirmed === false ? 'teyit bekliyor' : '';
      return `<dl class="facts">
        ${fact('Anapara', F.esc(F.moneyTry(t.principal_try)), `giriş kuru ${F.esc(F.num(t.usdtry_at_entry, 2))} · ${F.esc(F.money(p.cost_usd))}`)}
        ${fact('Faiz', `%${F.esc(F.num(t.annual_rate_pct, 1))} brüt`, `stopaj %${F.esc(F.num(t.withholding_pct, 0))}${stopaj ? ` · ${stopaj}` : ''}`)}
        ${fact('Biriken net faiz', F.esc(F.moneyTry(t.net_interest_try)), `${F.esc(F.money(t.net_interest_usd))} · günde ${F.esc(F.moneyTry(t.daily_net_interest_try))}`)}
        ${fact('Vade', F.esc(F.date(t.maturity_date)), `${F.esc(t.days_to_maturity)} gün · vadede ${F.esc(F.moneyTry(t.value_try_at_maturity))}`)}
        ${fact('Başa baş kur', F.esc(F.num(t.usdtry_breakeven, 2)), 'vadede kur bunun üstündeyse dolar bazında zarar')}
        ${F.isNum(t.usdtry_breakeven_vs_sgov) ? fact("SGOV'a göre başa baş", F.esc(F.num(t.usdtry_breakeven_vs_sgov, 2)), "bunun üstünde SGOV'dan kötü") : ''}
        ${fact('Güvenli pay', F.esc(F.share(t.breakeven_headroom_pct)), `bugünkü kur ${F.esc(F.num(t.usdtry_now, 2))}`)}
      </dl>`;
    }
    const unit = p.shares ? (p.cost_usd - (p.fees_usd || 0)) / p.shares : null;
    return `<dl class="facts">
      ${fact('Adet', F.esc(F.num(p.shares, p.shares % 1 ? 2 : 0)))}
      ${fact('Maliyet', F.esc(F.money(p.cost_usd)), unit ? `birim ${F.esc(F.money(unit))} · komisyon ${F.esc(F.money(p.fees_usd))}` : '')}
      ${fact('Fiyat', F.esc(F.money(p.price)), p.price_as_of ? F.esc(F.date(p.price_as_of)) : '')}
      ${p.dividends_usd ? fact('Dağıtımlar', F.esc(F.money(p.dividends_usd)), 'değere dahil') : ''}
      ${fact('Giriş', F.esc(F.date(p.entry_date)), F.esc(p.broker || ''))}
    </dl>`;
  }

  function wirePositions() {
    document.querySelectorAll('#todayBody tr[data-row]').forEach((tr) => {
      const toggle = () => {
        const d = document.querySelector(`#todayBody tr[data-detail="${tr.dataset.row}"]`);
        const open = d.hidden;
        d.hidden = !open;
        tr.classList.toggle('open', open);
        tr.setAttribute('aria-expanded', String(open));
      };
      tr.addEventListener('click', toggle);
      tr.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
    });
  }

  /* ---------------------------------------------------------- dilimler */
  function slices(port) {
    const s = port.summary || {};
    const list = s.slices || [];
    if (!list.length) return '';
    const by = Object.fromEntries(list.map((x) => [x.slice, x]));
    // Hem gerçek hem hedef sıfırsa (Faz 0'da motor) dilim gösterilmez.
    const ordered = SLICE_ORDER.map((k, i) => ({ ...(by[k] || {}), slice: k, tone: i + 1 }))
      .filter((x) => by[x.slice] && ((x.actual_pct || 0) > 0 || (x.target_pct || 0) > 0));

    const segs = ordered.filter((x) => (x.actual_pct || 0) > 0).map((x) =>
      `<span class="seg-${x.tone}" style="flex:${x.actual_pct}" title="${F.esc(F.sliceLabel(x.slice))}: ${F.esc(F.share(x.actual_pct))}"></span>`).join('');
    let cum = 0;
    const ticks = [];
    ordered.filter((x) => F.isNum(x.target_pct)).forEach((x) => {
      cum += x.target_pct;
      if (x.target_pct > 0 && cum < 99.5) ticks.push(cum);
    });

    const legend = ordered.map((x) => `<div><span class="sw" style="background:var(--tone-${x.tone})"></span>
      <span class="n">${F.esc(F.sliceLabel(x.slice, x.label))}</span>
      <span class="v">${F.esc(F.share(x.actual_pct))}${F.isNum(x.target_pct) ? ` <span class="dim">/ ${F.esc(F.share(x.target_pct, 0))}</span>` : ''}</span></div>`).join('');

    const notes = ordered.filter((x) => x.off_target).map((x) => offNote(x, port)).join('');
    const missing = (s.slices_incomplete || []).length
      ? `<div class="small dim" style="margin-top:8px">Eksik fiyat (${F.esc(s.slices_incomplete.join(', '))}): sapma hesaplanmadı.</div>` : '';

    return `<section><h2>Dilimler</h2><div class="card">
      <div class="spread small"><span class="muted">${F.esc(F.phaseLabel(s.phase))}</span>
        <span class="dim"><span class="tick-key"></span>hedef · bant ±${F.esc(F.num(((App.thresholds.portfolio || {}).slice_drift_warn_pp) || 5, 0))} puan</span></div>
      <div class="slicebar" role="img" aria-label="Dilim ağırlıkları ve hedefler">
        <div class="bar">${segs}</div>
        ${ticks.map((t) => `<span class="tick" style="left:${Math.min(t, 100)}%"></span>`).join('')}
      </div>
      <div class="slice-legend">${legend}</div>
      ${notes}${missing}
    </div></section>`;
  }

  function offNote(x, port) {
    const d = x.drift_pp;
    const name = F.sliceLabel(x.slice, x.label);
    const amount = `${F.num(Math.abs(d), 1)} puan ${d < 0 ? 'eksik' : 'fazla'}`;
    let fix = '';
    if (d < 0) {
      const sliceOf = Object.fromEntries((port.positions || []).map((p) => [p.ticker, p.slice]));
      const buy = (port.actions || []).find((a) => a.kind === 'alim' && a.ticker && sliceOf[a.ticker] === x.slice);
      if (buy) {
        const total = ((port.performance || {}).value_usd) || (port.summary || {}).portfolio_value_usd || 0;
        const closes = total && F.isNum(buy.amount_usd) && (buy.amount_usd / total) * 100 >= Math.abs(d);
        fix = ` — ${F.date(buy.date)} ${buy.ticker} alımı ${closes ? 'kapatır' : 'kısmen kapatır'}`;
      }
    }
    return `<div class="slice-note">${F.esc(name)} ${F.esc(amount)}${F.esc(fix)}</div>`;
  }

  /* --------------------------------------------------------- bu hafta */
  function actionTitle(a, port) {
    if (a.kind === 'alim') return `${a.ticker || ''} alımı${F.isNum(a.amount_usd) ? ` · ${F.money(a.amount_usd)}` : ''}`;
    if (a.kind === 'vade') {
      const t = ((port.positions || []).find((p) => p.tl_deposit) || {}).tl_deposit || {};
      return `TL mevduat vadesi${t.bank ? ` · ${t.bank}` : ''} — yenileme kararı`;
    }
    if (a.kind === 'faz') {
      const m = /Faz\s*(\d)/.exec(a.title || '');
      const ph = ((App.thresholds.portfolio || {}).phases || []).find((p) => m && p.key === `faz${m[1]}`);
      return ph ? `${F.phaseLabel(ph)} başlıyor` : F.tr(a.title);
    }
    return F.tr(a.title);
  }

  function agenda(port) {
    const items = [
      ...(port.actions || []).map((a) => ({ days: a.days, date: a.date, title: actionTitle(a, port) })),
      ...(port.calendar || []).map((e) => ({ days: e.days, date: e.date, title: F.tr(e.title) })),
    ].filter((x) => F.isNum(x.days) && x.days >= 0 && x.days <= 30)
     .sort((a, b) => a.days - b.days).slice(0, 3);
    if (!items.length) return '';
    return `<section><div class="h2row"><h2>Bu hafta</h2><a class="small" href="#/portfoy/plan">Tümü → Plan</a></div>
      <div class="card"><ul class="agenda compact">${items.map((x) => `<li>
        <span class="when ${x.days <= 7 ? 'soon' : ''}">${F.esc(F.days(x.days))}</span>
        <span class="what">${F.esc(x.title)}</span><span class="date">${F.esc(F.date(x.date))}</span></li>`).join('')}</ul>
      </div></section>`;
  }

  return { render };
})();
