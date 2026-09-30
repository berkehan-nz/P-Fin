/* 1. GENEL BAKIS — dort ozet kutusu, makro serit, "bugun ne olmus". */
window.ViewOverview = (function () {
  'use strict';
  const $ = (id) => document.getElementById(id);

  async function render() {
    const [cand, port, macro, ov, pulse, hist] = await Promise.all([
      DataLayer.candidates(), DataLayer.portfolio(),
      DataLayer.macro(), DataLayer.overview(), DataLayer.pulse(),
      DataLayer.portfolioHistory(),
    ]);

    const perf = port.performance || {};
    renderHero(port, perf);
    renderChart(hist.rows || [], perf);
    renderWarnings(port);
    renderPositions(port, perf);
    renderSlices(port.summary || {});
    renderFx(port);
    renderActions(port);
    renderMacroCal(port);

    renderFreshness(cand, port, pulse);
    renderMarket(pulse);
    renderCalendar(pulse);
    renderNews(pulse, ov);
    renderMacro(macro);
    renderToday(ov, port);
    renderSystem(cand, ov);
  }

  /* ======================================================================
     PORTFOY — "bugun yatirimlarim nasil gitti" 10 saniyede.
     Sira telefon ekranina gore: once tek buyuk sayi ve bugunku degisim,
     sonra ne kadar kazandim / kiyaslar, sonra grafik, sonra ayrinti.
     ==================================================================== */
  const usd = (v, d = 2) => Fmt.money(v, { digits: d });
  const tl = (v, d = 0) => (Fmt.isNum(v) ? `${v < 0 ? '-' : ''}₺${Fmt.num(Math.abs(v), d)}` : '—');
  const signedUsd = (v, d = 2) => (Fmt.isNum(v) ? `${v >= 0 ? '+' : '-'}${usd(Math.abs(v), d)}` : '—');
  const arrowOf = (v) => (!Fmt.isNum(v) || v === 0 ? '' : v > 0 ? '▲ ' : '▼ ');

  function shortDate(iso) {
    if (!iso) return '—';
    const d = new Date(`${String(iso).slice(0, 10)}T12:00:00`);
    if (isNaN(d)) return iso;
    return d.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' });
  }

  function daysFromToday(iso) {
    const d = new Date(`${String(iso).slice(0, 10)}T00:00:00`);
    if (isNaN(d)) return null;
    const t = new Date(); t.setHours(0, 0, 0, 0);
    return Math.round((d - t) / 86400000);
  }

  /* Isaretli degisim: renk YON'u, ok da ayni bilgiyi renksiz tasir. */
  function delta(v, text) {
    return `<span class="${Fmt.pnlClass(v)} nw">${arrowOf(v)}${text}</span>`;
  }

  /* ---------------------------------------------------------- a) baslik */
  function renderHero(port, perf) {
    const s = port.summary || {};
    const el = $('ovHero');

    const tazelik = freshnessLine(port);

    if (perf.status !== 'aktif') {
      const kalan = daysFromToday(perf.inception);
      // Baslangic gunu GECMISSE "basliyor" demek yanlis: pozisyonlar alindi,
      // yalnizca ilk kapanis fiyati henuz islenmedi.
      const metin = Fmt.isNum(kalan) && kalan > 0
        ? `Pozisyonlar <b>${Fmt.esc(shortDate(perf.inception))}</b> tarihinde basliyor
           (${kalan} gun sonra). Ilk kapanistan sonra deger ve "bugun" degisimi burada.`
        : `Pozisyonlar <b>${Fmt.esc(shortDate(perf.inception))}</b> tarihinde alindi;
           ilk kapanis fiyati henuz islenmedi. Portfoy fiyatlari saatlik tazelenir —
           bir sonraki kosuda deger ve "bugun" degisimi burada.`;
      el.innerHTML = `<div class="card ov-hero">
        <div class="ov-label">Portfoy degeri · henuz fiyatlanmayanlar maliyetten</div>
        <div class="ov-big">${usd(s.portfolio_value_usd)}</div>
        <div class="ov-sub">${tl(s.portfolio_value_try)} karsiligi${
          Fmt.isNum((s.fx || {}).rate) ? ` · USD/TRY ${Fmt.num(s.fx.rate, 2)}` : ''}</div>
        ${tazelik}
        <p class="small muted" style="margin:12px 0 0">${metin}
          Yatirilan sermaye <b>${usd(perf.invested_usd)}</b>, fark komisyon.</p>
      </div>`;
      return;
    }

    const b = perf.benchmarks || {};
    const eksik = !perf.complete && (perf.missing || []).length
      ? `<p class="tiny c-yellow" style="margin:8px 0 0">⚠ Bazi girdiler eksik
          (${Fmt.esc(perf.missing.join(', '))}); sayilar yaklasik.</p>` : '';

    const bugun = Fmt.isNum(perf.day_change_usd)
      ? `<div class="ov-delta">${delta(perf.day_change_usd, signedUsd(perf.day_change_usd))}</div>
         <div class="ov-sub">${delta(perf.day_change_pct, Fmt.signedPct(perf.day_change_pct, 2))}
           · ${Fmt.esc(shortDate(perf.prev_date))} kapanisina gore</div>`
      : `<div class="ov-delta c-gray">—</div>
         <div class="ov-sub">ilk gun; kiyaslanacak onceki kapanis yok</div>`;

    const kiyas = (label, v, fark) => `<div class="ov-tile">
        <div class="ov-label">${label}</div>
        <div class="ov-tile-v">${usd(v, 0)}</div>
        <div class="ov-sub">${Fmt.isNum(fark)
          ? `sen ${delta(fark, `${signedUsd(fark)}`)} ${fark >= 0 ? 'ondesin' : 'geridesin'}`
          : 'veri yok'}</div></div>`;

    el.innerHTML = `<div class="card ov-hero">
      <div class="ov-hero-top">
        <div>
          <div class="ov-label">Portfoy degeri · ${Fmt.esc(shortDate(perf.as_of))} kapanisi</div>
          <div class="ov-big">${usd(perf.value_usd)}</div>
          <div class="ov-sub">${tl(perf.value_try)} · USD/TRY ${Fmt.num(perf.usdtry, 2)}</div>
          ${tazelik}
        </div>
        <div class="ov-today">
          <div class="ov-label">Bugun</div>
          ${bugun}
        </div>
      </div>
      <div class="ov-tiles">
        <div class="ov-tile">
          <div class="ov-label">Baslangictan beri</div>
          <div class="ov-tile-v">${delta(perf.return_usd, signedUsd(perf.return_usd))}</div>
          <div class="ov-sub">${delta(perf.return_pct, Fmt.signedPct(perf.return_pct, 2))} dolar
            · ${delta(perf.return_try_pct, Fmt.signedPct(perf.return_try_pct, 2))} TL bazinda
            · ${perf.days} gun</div>
        </div>
        ${kiyas('Hepsi TL mevduatta olsaydi', b.all_tl_usd, perf.vs_all_tl_usd)}
        ${kiyas('Hepsi SGOV\'da olsaydi', b.all_sgov_usd, perf.vs_all_sgov_usd)}
        ${kiyas('Hepsi QQQ\'da olsaydi', b.all_qqq_usd, perf.vs_all_qqq_usd)}
      </div>
      ${eksik}
    </div>`;
  }

  /* FIYAT TAZELIGI. "Guncel durumumu goremiyorum" sikayetinin kaynagi:
     fiyatlar yalnizca gunluk kosuda, ABD piyasasi acilmadan cekiliyordu ve
     ekran bunu soylemiyordu. Artik ne zaman cekildigi hep gorunur; bayatsa
     sari uyari ve elle tazeleme yolu. */
  function freshnessLine(port) {
    const stamp = port.priced_at || port.as_of;
    const saat = Fmt.hoursSince(stamp);
    const gunler = (port.positions || []).map((p) => p.price_as_of).filter(Boolean).sort();
    const fiyatGunu = gunler.length ? gunler[gunler.length - 1] : null;
    const esik = 26;
    const ne = `${fiyatGunu ? `fiyat tarihi ${Fmt.esc(shortDate(fiyatGunu))} · ` : ''}${
      port.priced_at ? `${Fmt.esc(Fmt.sinceLabel(port.priced_at))} cekildi` : 'cekilme saati bilinmiyor'}`;
    if (saat === null || saat > esik) {
      return `<p class="tiny c-yellow" style="margin:6px 0 0">⚠ Fiyatlar bayat: ${ne}.
        Otomatik kosu gecikmis olabilir; hemen tazelemek icin GitHub &rarr; Actions &rarr;
        <b>Portfoy (saatlik fiyat)</b> &rarr; Run workflow.</p>`;
    }
    return `<p class="tiny dim" style="margin:6px 0 0">${ne}</p>`;
  }

  /* -------------------------------------------------- g) 30 gunluk grafik */
  const BENCH = {
    tl:   { key: 'all_tl_usd',   label: 'Hepsi TL mevduatta', short: 'TL' },
    sgov: { key: 'all_sgov_usd', label: 'Hepsi SGOV\'da',     short: 'SGOV' },
    qqq:  { key: 'all_qqq_usd',  label: 'Hepsi QQQ\'da',      short: 'QQQ' },
  };

  function renderChart(rows, perf) {
    const el = $('ovChart');
    const son = rows.slice(-30);
    if (son.length < 2) {
      el.innerHTML = `<div class="card muted small">Grafik ilk iki kapanistan sonra
        cizilir. ${perf.status === 'aktif' ? 'Yarin sabahki gunluk kosudan sonra burada.'
        : `Ilk satir ${Fmt.esc(shortDate(perf.inception))} kapanisindan sonra yazilir.`}</div>`;
      return;
    }

    let secili = DataLayer.prefs.get('ovBench', 'tl');
    if (!BENCH[secili]) secili = 'tl';

    el.innerHTML = `<div class="card">
      <div class="spread" style="align-items:center;margin-bottom:8px">
        <div class="ov-label">Son ${son.length} islem gunu · USD</div>
        <div class="seg" role="group" aria-label="Kiyas secimi">${Object.entries(BENCH).map(
          ([k, v]) => `<button data-b="${k}" aria-pressed="${k === secili}">${Fmt.esc(v.short)}</button>`).join('')}
        </div>
      </div>
      <div id="ovChartPlot"></div>
      <details class="tiny" style="margin-top:8px"><summary class="dim">Tablo olarak goster</summary>
        <div class="table-wrap" style="margin-top:6px" id="ovChartTable"></div></details>
    </div>`;

    const draw = () => {
      const bm = BENCH[secili];
      const dates = son.map((r) => r.date);
      const focus = { role: 'focus', label: 'Portfoy', short: 'Portfoy',
                      values: son.map((r) => r.total_usd) };
      const context = { role: 'context', label: bm.label, short: bm.short,
                        values: son.map((r) => (r.benchmarks || {})[bm.key]) };
      Charts.compare($('ovChartPlot'), {
        dates, focus, context,
        fmt: (v) => usd(v, 0),
        fmtTick: (v) => usd(v, 0),
        fmtDate: shortDate,
        diff: (a, c) => (Fmt.isNum(a) && Fmt.isNum(c) ? `Fark ${signedUsd(a - c)}` : ''),
        aria: `Son ${son.length} gunde portfoy degeri ve ${bm.label} kiyasi`,
      });
      $('ovChartTable').innerHTML = `<table><thead><tr><th>Tarih</th><th>Portfoy</th>
        <th>${Fmt.esc(bm.label)}</th><th>Fark</th></tr></thead><tbody>${
        [...son].reverse().map((r) => {
          const c = (r.benchmarks || {})[bm.key];
          return `<tr><td>${Fmt.esc(shortDate(r.date))}</td><td class="num">${usd(r.total_usd)}</td>
            <td class="num">${usd(c)}</td>
            <td class="num">${Fmt.isNum(c) ? delta(r.total_usd - c, signedUsd(r.total_usd - c)) : '—'}</td></tr>`;
        }).join('')}</tbody></table>`;
    };

    el.querySelectorAll('[data-b]').forEach((btn) => btn.addEventListener('click', () => {
      secili = btn.dataset.b;
      DataLayer.prefs.set('ovBench', secili);
      el.querySelectorAll('[data-b]').forEach((x) =>
        x.setAttribute('aria-pressed', String(x.dataset.b === secili)));
      draw();
    }));
    draw();
  }

  /* ------------------------------------------------------------ h) uyarilar */
  function renderWarnings(port) {
    const ws = port.warnings || [];
    $('ovWarnings').innerHTML = ws.length
      ? `<h2>Uyarilar <span class="chip yellow">${ws.length}</span></h2>` + ws.map((w) =>
          `<div class="warn ${Fmt.esc(w.level)}"><span aria-hidden="true">${
            w.level === 'high' ? '⛔' : w.level === 'medium' ? '⚠' : 'ℹ'}</span>
          <span>${Fmt.esc(w.message)}</span></div>`).join('')
      : '';
  }

  /* ---------------------------------------------------------- b) pozisyonlar */
  /* Ayni sembolun parcalari (30 Ekim QQQM) tek satirda toplanir. */
  function groupPositions(positions) {
    const by = new Map();
    positions.forEach((p) => {
      const key = p.ticker;
      const g = by.get(key);
      if (!g) { by.set(key, { ...p, lots: 1 }); return; }
      g.lots += 1;
      g.shares = (g.shares || 0) + (p.shares || 0);
      g.cost_usd = (g.cost_usd || 0) + (p.cost_usd || 0);
      g.value_usd = Fmt.isNum(g.value_usd) && Fmt.isNum(p.value_usd) ? g.value_usd + p.value_usd : null;
      g.pnl_usd = Fmt.isNum(g.pnl_usd) && Fmt.isNum(p.pnl_usd) ? g.pnl_usd + p.pnl_usd : null;
      g.pnl_pct = Fmt.isNum(g.pnl_usd) && g.cost_usd ? (g.pnl_usd / g.cost_usd) * 100 : null;
      g.started = g.started || p.started;
    });
    return [...by.values()].sort((a, b) => (b.value_usd || 0) - (a.value_usd || 0));
  }

  function renderPositions(port, perf) {
    const el = $('ovPositions');
    const pos = groupPositions((port.positions || []).filter((p) => p.status !== 'CLOSED'));
    const s = port.summary || {};
    if (!pos.length) {
      el.innerHTML = `<div class="card muted small">Acik pozisyon yok.</div>`;
      return;
    }
    const gunluk = perf.positions_day || {};
    const sliceLabel = {};
    (s.slices || []).forEach((x) => { sliceLabel[x.slice] = x.label; });

    const bugun = (p) => {
      const g = gunluk[p.ticker];
      if (g && Fmt.isNum(g.usd)) {
        return `${delta(g.usd, signedUsd(g.usd))}<div class="tiny">${delta(g.pct, Fmt.signedPct(g.pct, 2))}</div>`;
      }
      // Yedek: kaynagin gunluk degisimi. Alim GUNUNDE kullanilmaz — o gunun
      // degisimi alimdan onceki hareketi de icerir; ilk gunun sonucu
      // "Toplam K/Z"dedir.
      const ilkGun = p.entry_date && p.price_as_of && p.entry_date >= p.price_as_of;
      if (ilkGun) return '<span class="dim tiny">ilk gun</span>';
      if (p.started && Fmt.isNum(p.change_1d_pct) && Fmt.isNum(p.value_usd)) {
        const d = p.value_usd * p.change_1d_pct / (100 + p.change_1d_pct);
        return `${delta(d, signedUsd(d))}<div class="tiny">${delta(p.change_1d_pct, Fmt.signedPct(p.change_1d_pct, 2))}</div>`;
      }
      return '<span class="dim">—</span>';
    };
    const kz = (p) => (!p.started ? '<span class="dim tiny">baslamadi</span>'
      : Fmt.isNum(p.pnl_usd)
        ? `${delta(p.pnl_usd, signedUsd(p.pnl_usd))}<div class="tiny">${delta(p.pnl_pct, Fmt.signedPct(p.pnl_pct, 2))}</div>`
        : '<span class="dim">—</span>');

    const rows = pos.map((p) => {
      const t = p.tl_deposit;
      if (t) {
        return `<tr>
          <td><b>TL mevduat</b><div class="tiny dim">${Fmt.esc(t.bank || p.bank || '')}</div></td>
          <td class="num">${usd(p.value_usd)}<div class="tiny dim">${tl(t.value_try)}</div></td>
          <td class="num">${bugun(p)}</td>
          <td class="num">${kz(p)}</td>
          <td class="num">${tl(t.principal_try)}<div class="tiny dim">anapara</div></td>
          <td class="num">${usd(p.cost_usd)}<div class="tiny dim">@${Fmt.num(t.usdtry_at_entry, 2)}</div></td>
          <td class="num">kur ${Fmt.num(t.usdtry_now, 2)}</td>
          <td>${Fmt.esc(sliceLabel[p.slice] || p.slice || '')}</td></tr>`;
      }
      return `<tr>
        <td><b>${Fmt.esc(p.ticker)}</b>${p.lots > 1 ? `<div class="tiny dim">${p.lots} parca</div>` : ''}</td>
        <td class="num">${usd(p.value_usd)}</td>
        <td class="num">${bugun(p)}</td>
        <td class="num">${kz(p)}</td>
        <td class="num">${Fmt.num(p.shares, p.shares % 1 ? 2 : 0)}</td>
        <td class="num">${usd(p.cost_usd)}<div class="tiny dim">@${Fmt.num(p.entry_price, 2)}</div></td>
        <td class="num">${Fmt.isNum(p.price) ? usd(p.price) : '<span class="dim">—</span>'}</td>
        <td>${Fmt.esc(sliceLabel[p.slice] || p.slice || '')}</td></tr>`;
    }).join('');

    const nakit = Fmt.isNum(s.cash_usd) ? `<tr>
        <td><b>Nakit</b><div class="tiny dim">USD</div></td>
        <td class="num">${usd(s.cash_usd)}</td><td></td><td></td><td></td><td></td><td></td>
        <td class="dim">planli alimlar</td></tr>` : '';

    el.innerHTML = `<div class="table-wrap"><table>
      <thead><tr><th>Varlik</th><th>Deger</th><th>Bugun</th><th>Toplam K/Z</th>
        <th>Adet</th><th>Maliyet</th><th>Fiyat</th><th style="text-align:left">Dilim</th></tr></thead>
      <tbody>${rows}${nakit}</tbody></table></div>
      ${pos.filter((p) => p.tl_deposit).map(tlDetail).join('')}`;
  }

  /* TL mevduat: anapara, biriken faiz, vade, basa bas kurlari. Mevduatta
     sorulacak soru "faiz ne kadar" degil, "kur nereye kadar giderse bu
     faiz hala SGOV'u yener". */
  function tlDetail(p) {
    const t = p.tl_deposit;
    const kalan = t.matured ? 'vadesi doldu'
      : `vadeye <b>${t.days_to_maturity} gun</b> (${Fmt.esc(shortDate(t.maturity_date))})`;
    const vsSgov = Fmt.isNum(t.usdtry_breakeven_vs_sgov)
      ? `<li>SGOV'a gore basa bas kur <b class="num">${Fmt.num(t.usdtry_breakeven_vs_sgov, 2)}</b>
           — vadede USD/TRY bunun ustundeyse mevduat SGOV'dan kotu.</li>`
      : `<li class="dim">SGOV'a gore basa bas kur: 3 aylik T-bill faizi (FRED) gelince hesaplanir.</li>`;
    const stopaj = p.withholding_confirmed === false ? ' <span class="chip gray">teyit bekliyor</span>' : '';
    return `<div class="card ov-tl">
      <div class="ov-label">TL mevduat · ${Fmt.esc(t.bank || '')}</div>
      <ul class="plain small">
        <li>Anapara <b class="num">${tl(t.principal_try)}</b> · brut %${Fmt.num(t.annual_rate_pct, 1)},
          stopaj %${Fmt.num(t.withholding_pct, 0)}${stopaj}</li>
        <li>Biriken net faiz <b class="num">${tl(t.net_interest_try, 2)}</b>
          (${usd(t.net_interest_usd)}) · gunde ${tl(t.daily_net_interest_try, 2)} · ${kalan}</li>
        <li>Dolar karsiligi <b class="num">${usd(p.value_usd)}</b>${p.started ? ''
          : ' <span class="dim">(baslamadi; giris kurundan)</span>'} · vadede ${tl(t.value_try_at_maturity)}</li>
        <li>Basa bas kur <b class="num">${Fmt.num(t.usdtry_breakeven, 2)}</b>
          — vadede USD/TRY bunun ustundeyse mevduat dolar bazinda zarar${
          Fmt.isNum(t.breakeven_headroom_pct) ? ` (bugunden %${Fmt.num(t.breakeven_headroom_pct, 1)} uzakta)` : ''}.</li>
        ${vsSgov}
      </ul></div>`;
  }

  /* ----------------------------------------------------------- c) dilimler */
  function renderSlices(s) {
    const el = $('ovSlices');
    const slices = s.slices || [];
    const ph = s.phase || {};
    if (!slices.length) { el.innerHTML = '<div class="card muted small">Dilim verisi yok.</div>'; return; }

    const maks = Math.max(...slices.flatMap((x) => [x.actual_pct || 0, x.target_pct || 0]));
    const olcek = Math.min(100, Math.ceil((maks + 5) / 10) * 10);
    const eksik = (s.slices_incomplete || []).length
      ? `<p class="tiny c-yellow" style="margin:0 0 8px">⚠ Eksik fiyat/kur:
          ${Fmt.esc(s.slices_incomplete.join(', '))} — sapma uyarisi kapali.</p>` : '';

    const rozet = (x) => {
      if (!Fmt.isNum(x.target_pct)) return '<span class="chip gray">hedef yok</span>';
      if (!Fmt.isNum(x.drift_pp)) return '<span class="chip gray">? veri yok</span>';
      const d = x.drift_pp;
      const txt = Math.abs(d) < 0.5 ? 'hedefte' : `${d > 0 ? '+' : '-'}${Fmt.num(Math.abs(d), 1)} puan`;
      return x.off_target
        ? `<span class="chip yellow">${d > 0 ? '▲' : '▼'} ${txt}</span>`
        : `<span class="chip green">✓ ${txt}</span>`;
    };

    el.innerHTML = `<div class="card">
      <div class="spread" style="margin-bottom:10px">
        <span class="ov-label">${Fmt.esc(ph.label || 'Faz')}${ph.end ? ` · bitis ${Fmt.esc(shortDate(ph.end))}` : ''}</span>
        <span class="tiny dim"><i class="sl-key-fill"></i> gercek <i class="sl-key-tick"></i> hedef · tolerans ±5 puan</span>
      </div>
      ${eksik}
      ${slices.map((x) => `<div class="sl-row">
        <div class="sl-head">
          <span class="sl-name">${Fmt.esc(x.label)}</span>
          <span class="num small">%${Fmt.num(x.actual_pct || 0, 1)}${Fmt.isNum(x.target_pct)
            ? ` <span class="dim">/ %${Fmt.num(x.target_pct, 0)}</span>` : ''}</span>
          ${rozet(x)}
        </div>
        <div class="sl-track" title="${Fmt.esc(x.label)}: ${usd(x.value_usd, 0)}">
          <i style="width:${Math.min(100, (x.actual_pct || 0) / olcek * 100).toFixed(1)}%"></i>
          ${Fmt.isNum(x.target_pct) ? `<b style="left:${(x.target_pct / olcek * 100).toFixed(1)}%"></b>` : ''}
        </div>
        ${x.note ? `<div class="tiny dim">${Fmt.esc(x.note)}</div>` : ''}
      </div>`).join('')}
      <div class="tiny dim" style="margin-top:4px">Olcek %0–${olcek}</div>
    </div>`;
  }

  /* --------------------------------------------------------------- d) kur */
  const PACE = {
    green:  ['green',  '●', 'sakin'],
    yellow: ['yellow', '▲', 'izle'],
    red:    ['red',    '▲', 'hizli'],
    gray:   ['gray',   '?', 'veri yok'],
  };

  function renderFx(port) {
    const s = port.summary || {};
    const fx = s.fx || {};
    const pace = s.fx_pace || {};
    const t = ((port.positions || []).find((p) => p.tl_deposit) || {}).tl_deposit || {};
    const el = $('ovFx');
    if (!Fmt.isNum(fx.rate)) {
      el.innerHTML = '<div class="card muted small">USD/TRY alinamadi — gunluk kosu kuru cekemedi.</div>';
      return;
    }
    const [cls, ikon, ad] = PACE[pace.color] || PACE.gray;
    el.innerHTML = `<div class="card">
      <div class="spread">
        <div>
          <div class="ov-label">USD/TRY · ${Fmt.esc(shortDate(fx.as_of))}</div>
          <div class="ov-tile-v" style="font-size:26px">${Fmt.num(fx.rate, 2)}</div>
        </div>
        <span class="chip ${cls}" title="Son ${pace.window_days || 91} gunluk kur degisimi">${ikon} tempo: ${ad}</span>
      </div>
      <ul class="plain small" style="margin-top:8px">
        <li>Giris kuruna gore (${Fmt.num(t.usdtry_at_entry, 2)})
          <b class="num">${Fmt.signedPct(pace.change_since_entry_pct, 2)}</b></li>
        <li>Ceyreklik tempo <b class="num">${Fmt.signedPct(pace.change_quarter_pct, 1)}</b>
          <span class="dim">· yesil &lt;%4, sari %4–7, kirmizi &gt;%7</span></li>
        <li>1 hafta <b class="num">${Fmt.signedPct(fx.change_1w_pct, 2)}</b></li>
        ${Fmt.isNum(t.usdtry_breakeven) ? `<li>TL basa bas kur <b class="num">${Fmt.num(t.usdtry_breakeven, 2)}</b>${
          Fmt.isNum(t.usdtry_breakeven_vs_sgov) ? ` · SGOV'a gore <b class="num">${Fmt.num(t.usdtry_breakeven_vs_sgov, 2)}</b>` : ''}</li>` : ''}
      </ul></div>`;
  }

  /* ------------------------------------------------------- e) siradaki isler */
  const CRIT = {
    green: ['green', '✓', 'saglaniyor'],
    red:   ['red',   '✗', 'saglanmiyor'],
    gray:  ['gray',  '?', 'veri yok'],
  };
  const ACTION_KIND = { alim: 'alim', faz: 'faz', vade: 'vade' };

  function renderActions(port) {
    const el = $('ovActions');
    const acts = port.actions || [];
    if (!acts.length) { el.innerHTML = '<div class="card muted small">Planli is yok.</div>'; return; }
    el.innerHTML = `<div class="card" style="padding:0">${acts.map((a) => {
      const kriter = (a.criteria || []).length ? `<div class="ov-crit">
        <div class="tiny dim" style="margin-bottom:4px">Yenileme icin uc kosul:</div>
        ${a.criteria.map((c) => {
          const [k, i, t] = CRIT[c.status] || CRIT.gray;
          return `<div class="ov-crit-row"><span class="chip ${k}">${i} ${t}</span>
            <span class="small">${Fmt.esc(c.label)}${c.detail
              ? `<span class="tiny dim"> — ${Fmt.esc(c.detail)}</span>` : ''}</span></div>`;
        }).join('')}</div>` : '';
      return `<div class="ov-act">
        ${when(a.days, 'gun gecti')}
        <div style="min-width:0">
          <div><span class="chip gray">${Fmt.esc(ACTION_KIND[a.kind] || a.kind)}</span>
            <b>${Fmt.esc(a.title)}</b></div>
          <div class="tiny dim">${Fmt.esc(Fmt.date(a.date))}${a.note ? ` · ${Fmt.esc(a.note)}` : ''}</div>
          ${kriter}
        </div></div>`;
    }).join('')}</div>`;
  }

  /* Kalan gun sutunu. Gecmis tarih: planli is icin "gecti" (yapilmadi mi?),
     iki gunluk toplanti icin "suruyor". */
  function when(days, pastLabel) {
    if (!Fmt.isNum(days)) return '<div class="ov-act-when"><b>—</b></div>';
    if (days === 0) return '<div class="ov-act-when"><b>BUGUN</b></div>';
    if (days < 0) {
      return pastLabel === 'suruyor'
        ? '<div class="ov-act-when"><b class="tiny">suruyor</b></div>'
        : `<div class="ov-act-when c-yellow"><b class="num">${Math.abs(days)}</b>
             <span class="tiny">${pastLabel}</span></div>`;
    }
    return `<div class="ov-act-when"><b class="num">${days}</b><span class="tiny dim">gun</span></div>`;
  }

  /* ------------------------------------------------------ f) makro takvim */
  const MACRO_KIND = { fed: 'Fed', politika: 'politika', tcmb: 'TCMB' };

  function renderMacroCal(port) {
    const el = $('ovMacroCal');
    const cal = port.calendar || [];
    if (!cal.length) { el.innerHTML = '<div class="card muted small">Yaklasan makro olay yok.</div>'; return; }
    el.innerHTML = `<div class="card" style="padding:0">${cal.map((e) => {
      const gun = Fmt.isNum(e.days) ? e.days : daysFromToday(e.date);
      return `<div class="ov-act">
        ${when(gun, 'suruyor')}
        <div style="min-width:0">
          <div><span class="chip gray">${Fmt.esc(MACRO_KIND[e.kind] || e.kind)}</span>
            <b>${Fmt.esc(e.title)}</b></div>
          <div class="tiny dim">${Fmt.esc(shortDate(e.date))}${e.end && e.end !== e.date
            ? `–${Fmt.esc(shortDate(e.end))}` : ''}${e.note ? ` · ${Fmt.esc(e.note)}` : ''}</div>
        </div></div>`;
    }).join('')}</div>`;
  }

  /* ------------------------------------------------- tarama ve adaylar (kisa) */
  function renderSystem(cand, ov) {
    const k = (ov && ov.kpis) || {};
    const counts = cand.counts || {};
    const toplam = (counts.funnel || 0) + (counts.seed || 0) + (counts.manual || 0);
    $('ovSystem').innerHTML = `<div class="card small muted">
      Huni taramasi ${Fmt.isNum(k.scan_pct) ? `<b>%${Fmt.num(k.scan_pct, 1)}</b>` : '—'}
      · ${k.scan_survivors || 0} sirket sert filtreleri gecti
      · ${toplam} aday · ${k.decided_count || 0} karar
      · <a href="#/funnel">Huni</a> · <a href="#/candidates">Adaylar</a></div>`;
  }

  /* ------------------------------------------------------- kuresel piyasa */
  /* Sayilar tek basina yetmez: VIX 28'in ne demek oldugunu bilmeyen icin 28
     sadece bir sayidir. Serit, altinda tek cumlelik risk okumasi tasir. */
  function renderMarket(pulse) {
    const rows = pulse.market || [];
    if (!rows.length) {
      $('marketStrip').innerHTML = `<div class="card muted small">Piyasa verisi yok —
        <b>Pulse</b> is akisi henuz calismadi. GitHub &rarr; Actions &rarr;
        Pulse (piyasa nabzi) &rarr; Run workflow.</div>`;
      return;
    }

    // TEK IZGARA. Gruplari ayri satirlara bolmek, tek enstrumanli gruplarda
    // (Risk, Faiz, Kripto) satirin tamamini bos birakiyordu. Grup adi kutunun
    // uzerinde kucuk bir etiket olarak duruyor; sira gruba gore.
    const order = ['Hisse', 'Risk', 'Faiz', 'Kur', 'Emtia', 'Kripto'];
    const sorted = [...rows].sort((a, b) =>
      order.indexOf(a.group) - order.indexOf(b.group));

    $('marketStrip').innerHTML = `
      ${pulse.risk_note ? `<p class="small muted" style="margin:-4px 0 10px">
        ${Fmt.esc(pulse.risk_note)}</p>` : ''}
      <div class="mkt-row">${sorted.map(tile).join('')}</div>`;
  }

  function tile(r) {
    const d = r.change_1d_pct;
    const digits = Math.abs(r.value) >= 1000 ? 0 : 2;
    // Kivilcim grafigi NOTR renkte. 'auto' yukseleni yesil yapiyor; VIX ve
    // USD/TRY yukselince bu YANLIS isaret oluyordu — hemen yanindaki kirmizi
    // gunluk degisimle celisiyordu. Yon bilgisini sayi tasir, grafik sekli.
    const spark = Charts.sparkline(r.series || [], { w: 76, h: 22 });
    return `<div class="mkt-tile" title="${Fmt.esc(r.symbol)} · ${Fmt.esc(r.as_of || '')}">
      <div class="mkt-tag">${Fmt.esc(r.group)}</div>
      <div class="tiny dim mkt-label">${Fmt.esc(r.label)}</div>
      <div class="num mkt-value">${Fmt.num(r.value, digits)}${r.unit === '%' ? '%' : ''}</div>
      <div class="spread" style="align-items:center">
        <span class="num tiny ${Fmt.pnlClass(d)}">${Fmt.isNum(d) ? Fmt.signedPct(d) : '—'}</span>
        ${spark}
      </div>
      <div class="tiny dim">5g ${Fmt.isNum(r.change_5d_pct) ? Fmt.signedPct(r.change_5d_pct) : '—'}</div>
    </div>`;
  }

  /* ------------------------------------------------------ kritik tarihler */
  function renderCalendar(pulse) {
    const cal = pulse.calendar || {};
    const up = cal.upcoming || [];
    const recent = cal.recent || [];
    if (!up.length && !recent.length) {
      $('calendarBox').innerHTML = `<div class="card muted small">Takvim bos —
        <b>Pulse</b> is akisi henuz calismadi veya FRED anahtari tanimli degil.</div>`;
      return;
    }

    $('calendarBox').innerHTML = `<div class="card" style="padding:0">
      ${up.length ? `<div class="cal-head">Yaklasan</div>
        ${up.slice(0, 12).map((e) => calRow(e, true)).join('')}` : ''}
      ${recent.length ? `<div class="cal-head">Olan biten</div>
        ${recent.slice(0, 8).map((e) => calRow(e, false)).join('')}` : ''}
    </div>`;

    $('calendarBox').querySelectorAll('[data-go]').forEach((el) =>
      el.addEventListener('click', () => { location.hash = `#/company/${el.dataset.go}`; }));
  }

  const KIND = {
    makro:   ['accent', 'makro'],
    bilanco: ['yellow', 'bilanco'],
    sec:     ['gray',   'SEC'],
  };

  function calRow(e, upcoming) {
    const [cls, label] = KIND[e.kind] || ['gray', e.kind];
    const when = upcoming ? relativeDay(e.date) : Fmt.date(e.date);
    const clickable = e.ticker ? ` data-go="${Fmt.esc(e.ticker)}" style="cursor:pointer"` : '';
    const title = e.url
      ? `<a href="${Fmt.esc(e.url)}" target="_blank" rel="noopener">${Fmt.esc(e.title)}</a>`
      : Fmt.esc(e.title);
    return `<div class="cal-row"${clickable}>
      <span class="chip ${cls}">${Fmt.esc(label)}</span>
      <span class="cal-title">${title}</span>
      ${e.detail ? `<span class="tiny dim cal-detail">${Fmt.esc(e.detail)}</span>` : '<span></span>'}
      <span class="tiny ${upcoming ? 'muted' : 'dim'} cal-when">${Fmt.esc(when)}</span>
    </div>`;
  }

  /* "2026-09-18" degil "2 gun sonra" — takvimde onemli olan UZAKLIK. */
  function relativeDay(iso) {
    const d = new Date(iso + 'T00:00:00');
    if (isNaN(d)) return iso;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const n = Math.round((d - today) / 86400000);
    if (n === 0) return 'BUGUN';
    if (n === 1) return 'yarin';
    if (n < 0) return `${Math.abs(n)} gun once`;
    if (n <= 14) return `${n} gun sonra`;
    return Fmt.date(iso);
  }

  /* ------------------------------------------------------------ haberler */
  function renderNews(pulse, ov) {
    // Nabiz kosusu taze; yoksa gunluk kosunun yazdigina dus.
    const news = (pulse.news && pulse.news.length) ? pulse.news : (ov.news || []);
    if (!news.length) {
      $('newsBox').innerHTML = `<div class="card muted small">Haber yok —
        FINNHUB_API_KEY tanimli degilse haber cekilmez.</div>`;
      return;
    }
    $('newsBox').innerHTML = `<div class="card" style="padding:0">
      ${news.slice(0, 14).map((n) => `<div class="news-row">
        <span class="chip accent news-tag" data-go="${Fmt.esc(n.ticker)}"
              style="cursor:pointer">${Fmt.esc(n.ticker)}</span>
        <div style="min-width:0">
          <a href="${Fmt.esc(n.url)}" target="_blank" rel="noopener">${Fmt.esc(n.headline)}</a>
          <div class="tiny dim">${Fmt.esc(n.source)} · ${Fmt.date(n.date)}</div>
        </div>
      </div>`).join('')}</div>`;

    $('newsBox').querySelectorAll('[data-go]').forEach((el) =>
      el.addEventListener('click', (ev) => {
        ev.stopPropagation();
        location.hash = `#/company/${el.dataset.go}`;
      }));
  }

  /* VERI TAZELIGI — otomasyon sessizce durursa kimse fark etmesin diye.
     GitHub'in zamanlanmis is akislari en iyi cabayla calisir; yogunlukta
     atlanabilir. Panonun bunu SOYLEMESI gerekir, cunku bayat veriyle
     karar vermek yanlis veriyle karar vermek kadar kotudur. */
  /* IKI AYRI TAZELIK. Nabiz (piyasa, haber, takvim) saatlik kosuyor;
     kartlar ve puanlar gunluk. Tek bir "guncel" damgasi ikisini de temsil
     edemez — hangisinin ne kadar eski oldugu ayri ayri yazilmali. */
  function renderFreshness(cand, port, pulse) {
    const cardStamp = cand.as_of || port.as_of;
    const cardDays = daysSince(cardStamp);
    const pulseHours = hoursSince(pulse.generated_at);

    const cardText = cardDays === null ? 'kart tarihi okunamadi'
      : cardDays === 0 ? 'kartlar bugun guncellendi'
      : `kartlar ${cardDays} gun once guncellendi`;
    const pulseText = pulseHours === null ? 'nabiz hic calismadi'
      : pulseHours < 1 ? 'piyasa az once guncellendi'
      : `piyasa ${pulseHours} saat once guncellendi`;

    $('overviewSubtitle').innerHTML =
      `${Fmt.esc(pulseText)} · ${Fmt.esc(cardText)} · `
      + `<span class="dim">kaynak: SEC EDGAR, yfinance, Finnhub, FRED</span>`;

    const banner = $('freshnessBanner');
    const stale = [];
    if (pulseHours === null || pulseHours > 8) stale.push(`piyasa verisi (${pulseText})`);
    if (cardDays === null || cardDays > 2) stale.push(`kartlar (${cardText})`);

    if (!stale.length) { banner.innerHTML = ''; return; }
    banner.innerHTML = `<div class="banner">
      <b>Veri bayat olabilir:</b> ${Fmt.esc(stale.join(', '))}.
      GitHub zamanlanmis is akislarini EN IYI CABAYLA calistirir ve yogunlukta
      atlar; saatlik kurulu bir kosu pratikte birkac saatte bir doner.
      Elle tetiklemek icin: Actions &rarr; <b>Pulse</b> (piyasa) veya
      <b>Daily</b> (kartlar) &rarr; Run workflow.
    </div>`;
  }

  function hoursSince(iso) {
    if (!iso) return null;
    const d = new Date(iso);
    if (isNaN(d)) return null;
    return Math.floor((Date.now() - d.getTime()) / 3600000);
  }

  function daysSince(iso) {
    if (!iso) return null;
    const d = new Date(iso);
    if (isNaN(d)) return null;
    return Math.floor((Date.now() - d.getTime()) / 86400000);
  }

  function box(label, value, sub, cls) {
    return `<div class="card stat">
      <div class="label">${Fmt.esc(label)}</div>
      <div class="value ${cls || ''}">${value}</div>
      <div class="sub">${Fmt.esc(sub || '')}</div></div>`;
  }

  function renderMacro(macro) {
    const series = macro.series || {};
    const keys = Object.keys(series);
    if (!keys.length) {
      $('macroStrip').innerHTML =
        `<div class="card muted small">Makro verisi yok — FRED_API_KEY tanimli degil
         veya veri hatti henuz calismadi.</div>`;
      return;
    }
    $('macroStrip').innerHTML = keys.map((k) => {
      const m = series[k];
      if (!m || !Fmt.isNum(m.value)) {
        return box(m ? m.label : k, '—', 'veri yok');
      }
      const spark = Charts.sparkline((m.series || []).map((p) => p[1]),
                                     { w: 90, h: 22, color: 'auto' });
      const chg = Fmt.isNum(m.change_3m)
        ? `3 ayda ${m.change_3m > 0 ? '+' : ''}${Fmt.num(m.change_3m, 2)} puan` : '';
      return `<div class="card stat">
        <div class="label">${Fmt.esc(m.label)}</div>
        <div class="value">${Fmt.num(m.value, 2)}${m.unit === '%' ? '%' : ''}</div>
        <div class="spread"><span class="sub">${Fmt.esc(chg)}</span>${spark}</div></div>`;
    }).join('');
  }

  function renderToday(ov, port) {
    const movers = ov.movers || [];
    if (!movers.length) {
      $('todayStrip').innerHTML =
        `<div class="card muted small">Fiyat hareketi yok — gunluk kosu henuz
         calismadi. Takip edilen sirketlerin son 24 saatlik hareketi burada gorunur.</div>`;
      return;
    }

    const moverHtml = movers.length ? `<div class="card">
      <div class="row">${movers.map((m) => `
        <span class="chip ${m.change_1d_pct > 0 ? 'green' : m.change_1d_pct < 0 ? 'red' : 'gray'}">
          <b>${Fmt.esc(m.ticker)}</b> ${Fmt.signedPct(m.change_1d_pct)}</span>`).join('')}
      </div></div>` : '';

    // Haberler artik kendi bolumunde (nabiz kosusundan, daha taze).
    $('todayStrip').innerHTML = moverHtml;
  }

  return { render };
})();
