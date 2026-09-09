/* 1. GENEL BAKIS — dort ozet kutusu, makro serit, "bugun ne olmus". */
window.ViewOverview = (function () {
  'use strict';
  const $ = (id) => document.getElementById(id);

  async function render() {
    const [cand, port, macro, ov] = await Promise.all([
      DataLayer.candidates(), DataLayer.portfolio(),
      DataLayer.macro(), DataLayer.overview(),
    ]);

    const s = port.summary || {};
    const counts = cand.counts || {};
    const totalCandidates = (counts.funnel || 0) + (counts.seed || 0) + (counts.manual || 0);
    const warnCount = (port.warnings || []).length
      + [...(cand.candidates || []), ...(cand.seed || []), ...(cand.manual || [])]
          .reduce((n, r) => n + (r.warning_count || 0), 0);

    const nasdaq = (s.vs_benchmark || {}).nasdaq100;

    $('summaryBoxes').innerHTML = [
      box('Portfoy degeri', Fmt.money(s.portfolio_value_usd, { digits: 0 }),
          s.position_count ? `${s.position_count} pozisyon · nakit ${Fmt.money(s.cash_usd, { digits: 0 })}`
                           : 'Pozisyon yok'),
      box('Toplam K/Z', Fmt.money(s.pnl_usd, { digits: 0 }),
          Fmt.isNum(s.pnl_pct) ? Fmt.signedPct(s.pnl_pct) : '—',
          Fmt.pnlClass(s.pnl_usd)),
      box('Nasdaq 100\'e gore', Fmt.isNum(nasdaq) ? Fmt.signedPct(nasdaq) : '—',
          'Giris tarihlerinden itibaren, agirlikli', Fmt.pnlClass(nasdaq)),
      box('Aday sayisi', String(totalCandidates),
          `${counts.seed || 0} tohum · ${counts.funnel || 0} huni · ${counts.manual || 0} elle`),
      box('Uyari', String(warnCount),
          warnCount ? 'Portfoy ve kart uyarilari' : 'Temiz',
          warnCount ? 'c-yellow' : 'c-green'),
    ].join('');

    renderFreshness(cand, port);

    renderMacro(macro);
    renderToday(ov, port);
  }

  /* VERI TAZELIGI — otomasyon sessizce durursa kimse fark etmesin diye.
     GitHub'in zamanlanmis is akislari en iyi cabayla calisir; yogunlukta
     atlanabilir. Panonun bunu SOYLEMESI gerekir, cunku bayat veriyle
     karar vermek yanlis veriyle karar vermek kadar kotudur. */
  function renderFreshness(cand, port) {
    const stamp = cand.as_of || port.as_of;
    const days = daysSince(stamp);
    const el = $('overviewSubtitle');

    let state = 'taze';
    if (days === null) state = 'bilinmiyor';
    else if (days > 7) state = 'cok_bayat';
    else if (days > 2) state = 'bayat';

    const text = {
      taze: `Veri guncel (${Fmt.date(stamp)})`,
      bayat: `Veri ${days} gundur guncellenmedi (${Fmt.date(stamp)})`,
      cok_bayat: `Veri ${days} GUNDUR guncellenmedi (${Fmt.date(stamp)})`,
      bilinmiyor: 'Veri tarihi okunamadi',
    }[state];

    el.innerHTML = `${Fmt.esc(text)} · <span class="dim">kaynak: SEC EDGAR,
      Stooq, Finnhub, FRED</span>`;

    const banner = $('freshnessBanner');
    if (state === 'taze') { banner.innerHTML = ''; return; }
    banner.innerHTML = `<div class="banner">
      <b>Veri bayat olabilir.</b> ${Fmt.esc(text)}.
      Otomatik guncelleme calismiyorsa GitHub &rarr; Actions sekmesinden
      <b>Scan</b> ve <b>Daily</b> is akislarinin son kosularina bak;
      zamanlanmis kosular GitHub'da yogunlukta atlanabiliyor.
      Elle calistirmak icin: Actions &rarr; ilgili is akisi &rarr; Run workflow.
    </div>`;
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
    const news = ov.news || [];
    if (!movers.length && !news.length) {
      $('todayStrip').innerHTML =
        `<div class="card muted small">Portfoy ve izleme listesi bos, ya da veri hatti
         henuz calismadi. Sirket ekledikten sonra son 24 saatin fiyat hareketleri
         ve haberleri burada gorunur.</div>`;
      return;
    }

    const moverHtml = movers.length ? `<div class="card">
      <h3 style="margin-top:0">Fiyat hareketleri</h3>
      <div class="row">${movers.map((m) => `
        <span class="chip ${m.change_1d_pct > 0 ? 'green' : m.change_1d_pct < 0 ? 'red' : 'gray'}">
          <b>${Fmt.esc(m.ticker)}</b> ${Fmt.signedPct(m.change_1d_pct)}</span>`).join('')}
      </div></div>` : '';

    const newsHtml = news.length ? `<div class="card" style="margin-top:12px">
      <h3 style="margin-top:0">Haberler</h3>
      ${news.map((n) => `<div style="padding:6px 0;border-bottom:1px solid var(--line-soft)">
        <span class="chip accent">${Fmt.esc(n.ticker)}</span>
        <a href="${Fmt.esc(n.url)}" target="_blank" rel="noopener">${Fmt.esc(n.headline)}</a>
        <span class="tiny dim"> · ${Fmt.esc(n.source)} · ${Fmt.date(n.date)}</span>
      </div>`).join('')}</div>` : '';

    $('todayStrip').innerHTML = moverHtml + newsHtml;
  }

  return { render };
})();
