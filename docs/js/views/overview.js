/* 1. GENEL BAKIS — dort ozet kutusu, makro serit, "bugun ne olmus". */
window.ViewOverview = (function () {
  'use strict';
  const $ = (id) => document.getElementById(id);

  async function render() {
    const [cand, port, macro, ov, pulse] = await Promise.all([
      DataLayer.candidates(), DataLayer.portfolio(),
      DataLayer.macro(), DataLayer.overview(), DataLayer.pulse(),
    ]);

    const s = port.summary || {};
    const counts = cand.counts || {};
    const totalCandidates = (counts.funnel || 0) + (counts.seed || 0) + (counts.manual || 0);
    const warnCount = (port.warnings || []).length
      + [...(cand.candidates || []), ...(cand.seed || []), ...(cand.manual || [])]
          .reduce((n, r) => n + (r.warning_count || 0), 0);

    const nasdaq = (s.vs_benchmark || {}).nasdaq100;

    /* Portfoy BOSKEN ilk uc kutu "—" gosteriyordu ve genel bakis olu bir
       sayfa oluyordu. Oysa sistemin urettigi is ortada: tarama nerede,
       kac sirket Asama 2'yi gecti, kaca karar verildi. Pozisyon acilinca
       kutular portfoye doner. */
    const k = (ov && ov.kpis) || {};
    const portfoyVar = (s.position_count || 0) > 0;

    const ilkUc = portfoyVar ? [
      box('Portfoy degeri', Fmt.money(s.portfolio_value_usd, { digits: 0 }),
          `${s.position_count} pozisyon · nakit ${Fmt.money(s.cash_usd, { digits: 0 })}`),
      box('Toplam K/Z', Fmt.money(s.pnl_usd, { digits: 0 }),
          Fmt.isNum(s.pnl_pct) ? Fmt.signedPct(s.pnl_pct) : '—',
          Fmt.pnlClass(s.pnl_usd)),
      box('Nasdaq 100\'e gore', Fmt.isNum(nasdaq) ? Fmt.signedPct(nasdaq) : '—',
          'Giris tarihlerinden itibaren, agirlikli', Fmt.pnlClass(nasdaq)),
    ] : [
      box('Evren taramasi', Fmt.isNum(k.scan_pct) ? `%${Fmt.num(k.scan_pct, 1)}` : '—',
          Fmt.isNum(k.scan_total)
            ? `${(k.scan_done || 0).toLocaleString('tr-TR')} / ${(k.scan_total || 0).toLocaleString('tr-TR')} sirket`
            : 'Tarama henuz baslamadi'),
      box('Sert filtreleri gecen', String(k.scan_survivors || 0),
          k.data_missing ? `${k.data_missing} sirket veri eksikliginden bekliyor`
                         : 'Asama 0-1-2 sonrasi'),
      box('Karar verilen', String(k.decided_count || 0),
          `${(k.seed_count || 0) + (k.candidate_count || 0)} sirketin icinde`),
    ];

    $('summaryBoxes').innerHTML = [
      ...ilkUc,
      box('Aday sayisi', String(totalCandidates),
          `${counts.seed || 0} tohum · ${counts.funnel || 0} huni · ${counts.manual || 0} elle`),
      box('Uyari', String(warnCount),
          warnCount ? 'Portfoy ve kart uyarilari' : 'Temiz',
          warnCount ? 'c-yellow' : 'c-green'),
    ].join('');

    renderFreshness(cand, port, pulse);
    renderMarket(pulse);
    renderCalendar(pulse);
    renderNews(pulse, ov);
    renderMacro(macro);
    renderToday(ov, port);
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
