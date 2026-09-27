/* CUMA RAPORU — haftada bir, "bu hafta neye bakmam lazim".

   Sistem her gun veri uretiyor ama her gun BAKILMASI gerektigi anlamina
   gelmiyor. Gunluk bakmak iki sekilde zarar verir: gurultuye alisip gercek
   sinyali kacirirsin, ya da her dalgalanmaya tepki verip islem maliyetini
   tezin getirisinden buyutursun.

   Sayfanin duzeni bu yuzden EYLEM SIRASINA gore: en uste karar gerektiren
   sey (tetiklenen kirici), en alta yalnizca bilgi olan sey (makro takvim).
   Kazanc raporlari kasitli olarak "eylem" sayilmaz — rapor bir bilgi anidir,
   once rakam gelir, sonra tez yeniden tartilir. */
const ViewWeekly = (() => {
  const $ = (id) => document.getElementById(id);

  async function render() {
    const w = await DataLayer.weekly();

    if (!w || !w.as_of) {
      $('weeklyBody').innerHTML = `<div class="card">
        <h3>Henuz rapor uretilmedi</h3>
        <p class="muted small">Cuma raporu haftada bir, cuma gunu gunluk
          kosuda yazilir (<code>data/weekly.json</code>). Hemen uretmek icin:
          Actions &rarr; <b>Daily</b> &rarr; Run workflow, ya da
          <code>python -m src.run_daily --weekly</code>.</p></div>`;
      $('weeklySubtitle').textContent = '';
      return;
    }

    $('weeklySubtitle').innerHTML = `${Fmt.date(w.as_of)} · `
      + (w.action_required
          ? `<b class="c-yellow">${w.action_required} madde eylem gerektiriyor</b>`
          : `<b class="c-green">Eylem gerektiren bir sey yok</b>`);

    $('weeklyBody').innerHTML = [
      breakersCard(w.triggered_breakers || []),
      driftCard(w.slice_drift || []),
      earningsCard(w.upcoming_earnings || []),
      candidatesCard(w.new_candidates || {}),
      fxCard(w.fx || {}),
      scanCard(w.scan || {}),
      macroCard(w.macro || {}),
    ].join('');
  }

  /* 1 — KARAR GEREKTIREN TEK BOLUM */
  function breakersCard(rows) {
    if (!rows.length) {
      return card('1 · Tez kiricilar', `<p class="c-green">Hicbir kirici
        tetiklenmedi.</p>`, 'Tezin dayandigi sayilar yerinde.');
    }
    const items = rows.map((b) => {
      const etiket = { thesis: 'Yapisal', catastrophic_price: 'Fiyat cokusu',
                       take_profit: 'Hedef', portfolio_drawdown: 'Portfoy' };
      return `<li>
        <b>${Fmt.esc(b.ticker || '')}</b>
        <span class="chip ${b.level === 'high' ? 'red' : 'yellow'}">
          ${Fmt.esc(etiket[b.kind] || b.kind || '')}</span>
        ${b.manual ? '<span class="chip gray tiny">elle</span>' : ''}
        <div class="small">${Fmt.esc(b.description || '')}</div>
        ${b.action ? `<div class="small"><b>Ne yapmali:</b>
          ${Fmt.esc(b.action)}</div>` : ''}
        ${Fmt.isNum(b.current_value)
          ? `<div class="tiny dim">Su anki deger: ${Fmt.num(b.current_value, 2)}</div>`
          : ''}
      </li>`;
    }).join('');
    return card('1 · Tez kiricilar', `<ul class="plain">${items}</ul>`,
      'Karar gerektiren tek bolum. Fiyat cokusu OTOMATIK SATIS DEGIL — '
      + 'zorunlu yeniden degerlendirme.');
  }

  /* 2 — YENIDEN DENGELEME */
  function driftCard(rows) {
    if (!rows.length) {
      return card('2 · Dilim sapmalari',
        '<p class="c-green">Tum dilimler hedef bandinda.</p>');
    }
    const items = rows.map((s) => {
      const yon = s.drift_pp > 0 ? 'uzerinde' : 'altinda';
      return `<tr><td>${Fmt.esc(s.label)}</td>
        <td style="text-align:right"><b>${Fmt.pct(s.actual_pct)}</b></td>
        <td style="text-align:right" class="muted">${Fmt.pct(s.target_pct)}</td>
        <td style="text-align:right" class="c-yellow">
          ${Math.abs(s.drift_pp).toFixed(1)} puan ${yon}</td></tr>`;
    }).join('');
    return card('2 · Dilim sapmalari', `<table>
      <thead><tr><th>Dilim</th><th style="text-align:right">Gercek</th>
      <th style="text-align:right">Hedef</th>
      <th style="text-align:right">Sapma</th></tr></thead>
      <tbody>${items}</tbody></table>`);
  }

  /* 3 — BILGI, EYLEM DEGIL */
  function earningsCard(rows) {
    if (!rows.length) {
      return card('3 · 7 gun icindeki bilancolar',
        '<p class="muted">Bu hafta bilanco yok.</p>');
    }
    const items = rows.map((e) => `<li>
      <b>${Fmt.esc(e.ticker)}</b> — ${Fmt.date(e.date)}
      <span class="chip ${e.days <= 2 ? 'yellow' : 'gray'}">
        ${e.days === 0 ? 'bugun' : `${e.days} gun`}</span>
      ${e.in_portfolio ? '<span class="chip accent tiny">portfoyde</span>' : ''}
      ${e.estimated ? '<span class="chip gray tiny">tahmini tarih</span>' : ''}
    </li>`).join('');
    return card('3 · 7 gun icindeki bilancolar', `<ul class="plain">${items}</ul>`,
      'Rapor bir KARAR ani degil, bir BILGI anidir: once rakam gelir, '
      + 'sonra tez yeniden tartilir.');
  }

  /* 4 — HUNIDEN GELENLER */
  function candidatesCard(nc) {
    const girenler = nc.entered || [];
    const cikanlar = nc.left || [];
    if (!girenler.length && !cikanlar.length) {
      return card('4 · Huniden yeni gelenler',
        '<p class="muted">Gecen rapordan bu yana liste degismedi.</p>');
    }
    const g = girenler.length ? `<div><b>Giren (${girenler.length})</b>
      <ul class="plain">${girenler.map((c) => `<li>
        <a href="#/company/${Fmt.esc(c.ticker)}"><b>${Fmt.esc(c.ticker)}</b></a>
        ${Fmt.isNum(c.score) ? `<span class="chip accent">${Fmt.num(c.score, 0)}</span>` : ''}
        <span class="small">${Fmt.esc(c.headline || c.name || '')}</span>
      </li>`).join('')}</ul></div>` : '';
    const c = cikanlar.length ? `<div style="margin-top:10px">
      <b>Cikan (${cikanlar.length})</b>
      <p class="small">${cikanlar.map(Fmt.esc).join(', ')}</p></div>` : '';
    return card('4 · Huniden yeni gelenler', g + c,
      nc.first_report
        ? 'Ilk rapor: mevcut tum adaylar "yeni" gorunuyor.'
        : 'Listeden dusmek de bilgidir: kota doldu, puan geriledi ya da '
          + 'veri bozuldu.');
  }

  /* 5 — TL MEVDUAT VE KUR */
  function fxCard(fx) {
    if (!Fmt.isNum(fx.usdtry) && !(fx.deposits || []).length) {
      return card('5 · USD/TRY', '<p class="muted">Kur alinamadi.</p>');
    }
    const kur = Fmt.isNum(fx.usdtry)
      ? `<p>USD/TRY <b>${Fmt.num(fx.usdtry, 2)}</b>
          ${Fmt.isNum(fx.change_1w_pct)
            ? `<span class="small">1 haftada ${Fmt.signedPct(fx.change_1w_pct)}</span>` : ''}
          <span class="tiny dim">${Fmt.date(fx.as_of)}</span></p>` : '';

    const dep = (fx.deposits || []).map((d) => {
      /* Basa bas kura ne kadar yaklastigimiz, faiz oranindan daha cok sey
         soyler: kur o esige varirsa dolar bazinda kazanc sifirlanir. */
      const kullanilan = Fmt.isNum(d.usdtry_used_pct) ? d.usdtry_used_pct : null;
      const renk = kullanilan === null ? 'gray'
        : kullanilan >= 80 ? 'red' : kullanilan >= 50 ? 'yellow' : 'green';
      return `<div class="card" style="margin-top:8px">
        <div><b>${Fmt.esc(d.ticker || 'TL mevduat')}</b>
          ${Fmt.isNum(d.days_to_maturity)
            ? `<span class="chip gray tiny">vadeye ${d.days_to_maturity} gun</span>` : ''}</div>
        <div class="small">Deger: ${Fmt.num(d.value_try, 0)} TL
          ${Fmt.isNum(d.value_usd) ? `(${Fmt.money(d.value_usd, { digits: 0 })})` : ''}
          · net faiz ${Fmt.num(d.net_interest_try, 0)} TL</div>
        <div class="small">Giris kuru ${Fmt.num(d.usdtry_at_entry, 2)}
          &rarr; basa bas <b>${Fmt.num(d.usdtry_breakeven, 2)}</b>
          ${Fmt.isNum(d.breakeven_headroom_pct)
            ? `<span class="muted">(%${Fmt.num(d.breakeven_headroom_pct, 1)} pay)</span>` : ''}</div>
        ${kullanilan !== null ? `<div class="small">Payin
          <span class="chip ${renk}">%${Fmt.num(kullanilan, 0)}</span>'i kullanildi</div>` : ''}
      </div>`;
    }).join('');

    return card('5 · USD/TRY ve TL mevduat', kur + dep,
      'Mevduatta sorulmasi gereken "faiz ne kadar" degil, '
      + '"kur ne kadar artarsa bu faiz erir".');
  }

  /* 6 — TARAMA */
  function scanCard(s) {
    if (!s.total) return '';
    return card('6 · Evren taramasi', `
      <p>Tur ${s.cycle} · <b>${(s.done || 0).toLocaleString('tr-TR')}</b> /
        ${(s.total || 0).toLocaleString('tr-TR')} sirket
        (%${Fmt.num(s.pct, 1)}) · sert filtreleri gecen
        <b>${s.survivors || 0}</b></p>
      <p class="small">Elendi ${(s.eliminated || 0).toLocaleString('tr-TR')} ·
        veri yok <b>${s.data_missing || 0}</b>
        ${s.retry_queue ? `(${s.retry_queue} tanesi sonraki turda yeniden denenecek)` : ''}</p>`,
      '"Veri yok" eleme degildir: sirket kotu oldugu icin degil, gerekli '
      + 'sayiyi hesaplayamadigimiz icin dustu.');
  }

  /* 7 — MAKRO */
  function macroCard(m) {
    const oranlar = m.key_rates || {};
    const satir = Object.entries(oranlar)
      .filter(([, v]) => Fmt.isNum(v))
      .map(([k, v]) => {
        const ad = { us10y: 'ABD 10 yillik', fed_funds: 'Fed faizi',
                     cpi_yoy: 'TUFE (yillik)' }[k] || k;
        return `${Fmt.esc(ad)} <b>${Fmt.num(v, 2)}%</b>`;
      }).join(' · ');

    const takvim = (m.upcoming || []).map((e) => `<li>
      ${Fmt.date(e.date)} <span class="chip gray tiny">${e.days} gun</span>
      ${Fmt.esc(e.title || e.detail || '')}</li>`).join('');

    return card('7 · Makro', `
      ${satir ? `<p class="small">${satir}</p>` : ''}
      ${m.risk_note ? `<p class="small">${Fmt.esc(m.risk_note)}</p>` : ''}
      ${takvim ? `<ul class="plain">${takvim}</ul>`
               : '<p class="muted small">Yaklasan kayitli olay yok.</p>'}`);
  }

  function card(title, body, note) {
    return `<div class="card" style="margin-bottom:12px">
      <h3>${Fmt.esc(title)}</h3>
      ${note ? `<p class="muted small" style="margin-top:-4px">${Fmt.esc(note)}</p>` : ''}
      ${body}</div>`;
  }

  return { render };
})();
