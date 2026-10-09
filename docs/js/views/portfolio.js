/* PORTFÖY — plan ve geçmiş.
 *
 * "Bugün" ekranı anlık durumu gösterir; burası planı ve kaydı tutar:
 *   Plan         faz zaman çizgisi, planlı alımlar, sıradaki işler,
 *                TL mevduat yenileme koşulları
 *   Pozisyonlar  hisse/ETF ve TL mevduat ayrı tablolarda
 *   İşlemler     işlem günlüğü + işlem ekleme formu
 *   Haftalık     Cuma raporu
 * Üstteki üç sayı Bugün ekranındakiyle birebir aynı biçimdedir.
 */
window.ViewPortfolio = (function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const F = Fmt;
  const TABS = [['plan', 'Plan'], ['pozisyonlar', 'Pozisyonlar'], ['islemler', 'İşlemler'], ['haftalik', 'Haftalık']];

  async function render(arg) {
    const tab = TABS.some(([k]) => k === arg) ? arg : DataLayer.prefs.get('portfolioTab', 'plan');
    DataLayer.prefs.set('portfolioTab', tab);
    const [port, raw, weekly] = await Promise.all([
      DataLayer.portfolio(), DataLayer.portfolioRaw(), DataLayer.weekly(),
    ]);
    const perf = port.performance || {};
    const open = (port.positions || []).filter((p) => p.status !== 'CLOSED');

    const body = {
      plan: () => plan(port, raw),
      pozisyonlar: () => positions(port),
      islemler: () => trades(port, raw),
      haftalik: () => ViewWeekly.html(weekly, port),
    }[tab]();

    $('portfolioBody').innerHTML = `
      <div class="page-head"><h1>Portföy</h1>
        <span class="sub">${open.length} pozisyon + nakit · ${F.esc(F.phaseLabel((port.summary || {}).phase))}</span></div>
      ${warnings(port)}
      ${kpis(port, perf)}
      <div class="subtabs" role="tablist">${TABS.map(([k, l]) =>
        `<button role="tab" aria-selected="${k === tab}" data-tab="${k}">${l}</button>`).join('')}</div>
      <div id="portfolioTab">${body}</div>`;

    document.querySelectorAll('#portfolioBody [data-tab]').forEach((b) =>
      b.addEventListener('click', () => App.go(`portfoy/${b.dataset.tab}`)));
    const add = $('addTrade');
    if (add) add.addEventListener('click', openAddTrade);
  }

  /* Bugün ekranına girmeyen uyarılar (giriş kuru, eksik veri...) burada. */
  function warnings(port) {
    const shown = ['dilim_sapmasi', 'kademeli_alim'];
    return (port.warnings || []).filter((w) => !shown.includes(w.type)).map((w) =>
      `<div class="band ${w.level === 'high' ? 'bad' : 'warn'}"><span class="ico">!</span>
        <span>${F.esc(F.tr(w.message))}</span></div>`).join('');
  }

  function kpi(label, main, sub, cls) {
    return `<div class="card"><div class="label">${F.esc(label)}</div>
      <div class="kpi-v ${cls || ''}">${F.esc(main)}</div>
      ${sub ? `<div class="small ${cls || 'muted'}">${sub}</div>` : ''}</div>`;
  }

  function kpis(port, perf) {
    if (perf.status !== 'aktif') {
      const s = port.summary || {};
      return `<div class="kpis">${kpi('Değer', F.money(s.portfolio_value_usd), F.esc(F.moneyTry(s.portfolio_value_try)))}</div>`;
    }
    return `<div class="kpis">
      ${kpi('Değer', F.money(perf.value_usd), F.esc(`${F.moneyTry(perf.value_try)} · ${F.date(perf.as_of)}`))}
      ${kpi('Başlangıçtan', F.signedMoney(perf.return_usd), F.esc(`${F.pct(perf.return_pct)} · TL bazında ${F.pct(perf.return_try_pct)}`), F.changeClass(perf.return_pct))}
      ${kpi('Bugün', F.signedMoney(perf.day_change_usd), F.esc(F.pct(perf.day_change_pct)), F.changeClass(perf.day_change_pct))}
    </div>`;
  }

  /* -------------------------------------------------------------- plan */
  function plan(port, raw) {
    const phases = ((App.thresholds.portfolio || {}).phases) || [];
    const cur = ((port.summary || {}).phase || {}).key;
    const slices = ['motor', 'cekirdek_etf', 'sgov', 'tl'];
    const phaseRows = phases.map((ph) => `<tr${ph.key === cur ? ' class="current"' : ''}>
        <td class="lead" data-label=""><b>${F.esc(F.phaseLabel(ph))}</b>${ph.key === cur ? ' ' + F.badge('şu an') : ''}
          <span class="sub">${F.esc(F.date(ph.start))}${ph.end ? ` – ${F.esc(F.date(ph.end))}` : ' →'}</span></td>
        ${slices.map((k) => `<td class="r" data-label="${F.esc(F.sliceLabel(k))}">${F.esc(F.share((ph.targets || {})[k], 0))}</td>`).join('')}
      </tr>`).join('');

    const tranches = (raw.planned_tranches || []).slice().sort((a, b) => String(a.date).localeCompare(String(b.date)));
    const trancheRows = tranches.map((t) => `<li>
        <span class="when ${t.done ? '' : 'soon'}">${t.done ? 'yapıldı' : F.esc(F.days(F.daysUntil(t.date)))}</span>
        <span class="what">${F.esc(t.ticker || '')} alımı · ${F.esc(F.money(t.amount_usd))}${t.note ? `<span class="sub">${F.esc(F.tr(t.note))}</span>` : ''}</span>
        <span class="date">${F.esc(F.date(t.date))}</span></li>`).join('');

    const items = [
      ...(port.actions || []).filter((a) => a.kind !== 'alim').map((a) => ({ days: a.days, date: a.date, title: actionTitle(a, port) })),
      ...(port.calendar || []).map((e) => ({ days: e.days, date: e.end && e.end !== e.date ? `${e.date}|${e.end}` : e.date, title: F.tr(e.title) })),
    ].filter((x) => F.isNum(x.days)).sort((a, b) => a.days - b.days);

    const crit = ((port.tl_renewal || {}).criteria) || [];
    const critRows = crit.map((c) => {
      const b = c.status === 'green' ? F.badge('✓ sağlanıyor')
        : c.status === 'red' ? F.badge('✗ sağlanmıyor', 'bad')
        : '<span class="pending">girilmedi</span>';
      return `<li><span class="what">${F.esc(F.tr(c.label))}<span class="sub">${F.esc(F.tr(c.detail || ''))}</span></span><span>${b}</span></li>`;
    }).join('');

    return `
      <h2>Fazlar ve hedef ağırlıklar</h2>
      <div class="card flush"><div class="table-wrap"><table class="tbl stackable">
        <thead><tr><th>Faz</th>${slices.map((k) => `<th class="r">${F.esc(F.sliceLabel(k))}</th>`).join('')}</tr></thead>
        <tbody>${phaseRows}</tbody></table></div></div>
      ${trancheRows ? `<h2>Planlı alımlar</h2><div class="card"><ul class="agenda compact">${trancheRows}</ul></div>` : ''}
      ${items.length ? `<h2>Sıradaki işler</h2><div class="card"><ul class="agenda compact">${items.map((x) => {
        const [d1, d2] = String(x.date).split('|');
        return `<li><span class="when ${x.days <= 7 ? 'soon' : ''}">${F.esc(F.days(x.days))}</span>
          <span class="what">${F.esc(x.title)}</span>
          <span class="date">${F.esc(F.date(d1))}${d2 ? `–${F.esc(F.date(d2))}` : ''}</span></li>`; }).join('')}</ul></div>` : ''}
      ${critRows ? `<h2>TL mevduat yenileme koşulları</h2><div class="card">
        <p class="small muted">Vade ${F.esc(F.date((port.tl_renewal || {}).maturity_date))}. Üçü de sağlanıyorsa tez ayakta: yenile.</p>
        <ul class="agenda criteria">${critRows}</ul></div>` : ''}`;
  }

  function actionTitle(a, port) {
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

  /* -------------------------------------------------------- pozisyonlar */
  function positions(port) {
    const open = (port.positions || []).filter((p) => p.status !== 'CLOSED');
    const etf = open.filter((p) => !p.tl_deposit).sort((a, b) => (b.value_usd || 0) - (a.value_usd || 0));
    const tl = open.filter((p) => p.tl_deposit);
    const pnl = (p) => (p.started ? `<span class="${F.changeClass(p.pnl_pct)}">${F.esc(F.signedMoney(p.pnl_usd))}</span>` : '<span class="pending">başlamadı</span>');
    const pnlp = (p) => (p.started ? `<span class="${F.changeClass(p.pnl_pct)}">${F.esc(F.pct(p.pnl_pct))}</span>` : '');

    const etfTable = etf.length ? `<h2>Hisse ve ETF</h2><div class="card flush"><div class="table-wrap">
      <table class="tbl stackable"><thead><tr><th>Sembol</th><th class="r">Adet</th><th class="r">Maliyet</th>
        <th class="r">Fiyat</th><th class="r">Değer</th><th class="r">K/Z</th><th class="r">K/Z %</th><th class="r">Ağırlık</th></tr></thead>
      <tbody>${etf.map((p) => `<tr>
        <td class="lead" data-label=""><b>${F.esc(p.ticker)}</b><span class="sub">${F.esc(F.sliceLabel(p.slice))} · ${F.esc(F.date(p.entry_date))}</span></td>
        <td class="r" data-label="Adet">${F.esc(F.num(p.shares, p.shares % 1 ? 2 : 0))}</td>
        <td class="r" data-label="Maliyet">${F.esc(F.money(p.cost_usd))}</td>
        <td class="r" data-label="Fiyat">${F.esc(F.money(p.price))}</td>
        <td class="r" data-label="Değer">${F.esc(F.money(p.value_usd))}</td>
        <td class="r" data-label="K/Z">${pnl(p)}</td>
        <td class="r" data-label="K/Z %">${pnlp(p)}</td>
        <td class="r" data-label="Ağırlık">${F.esc(F.share(p.weight_pct))}</td></tr>`).join('')}</tbody></table></div></div>` : '';

    const tlTable = tl.length ? `<h2>TL mevduat</h2><div class="card flush"><div class="table-wrap">
      <table class="tbl stackable"><thead><tr><th>Banka</th><th class="r">Anapara</th><th class="r">Faiz</th>
        <th class="r">Biriken net</th><th class="r">Vade</th><th class="r">Başa baş kur</th><th class="r">Güvenli pay</th></tr></thead>
      <tbody>${tl.map((p) => { const t = p.tl_deposit; return `<tr>
        <td class="lead" data-label=""><b>${F.esc(t.bank || p.ticker)}</b><span class="sub">${F.esc(F.money(p.value_usd))} · kur ${F.esc(F.num(t.usdtry_now, 2))}</span></td>
        <td class="r" data-label="Anapara">${F.esc(F.moneyTry(t.principal_try))}</td>
        <td class="r" data-label="Faiz">%${F.esc(F.num(t.annual_rate_pct, 1))}<span class="sub">stopaj %${F.esc(F.num(t.withholding_pct, 0))}${p.withholding_confirmed === false ? ' · teyit bekliyor' : ''}</span></td>
        <td class="r" data-label="Biriken net">${F.esc(F.moneyTry(t.net_interest_try))}<span class="sub">${F.esc(F.money(t.net_interest_usd))}</span></td>
        <td class="r" data-label="Vade">${F.esc(F.date(t.maturity_date))}<span class="sub">${F.esc(t.days_to_maturity)} gün</span></td>
        <td class="r" data-label="Başa baş kur">${F.esc(F.num(t.usdtry_breakeven, 2))}${F.isNum(t.usdtry_breakeven_vs_sgov) ? `<span class="sub">SGOV'a göre ${F.esc(F.num(t.usdtry_breakeven_vs_sgov, 2))}</span>` : ''}</td>
        <td class="r" data-label="Güvenli pay">${F.esc(F.share(t.breakeven_headroom_pct))}</td></tr>`; }).join('')}</tbody></table></div></div>
      <p class="small muted" style="margin-top:8px">Başa baş kur: vadede USD/TRY bunun üstündeysen mevduat dolar bazında zarar ettirir.
        Güvenli pay: kurun bugünden oraya kadar yükselebileceği yüzde.</p>` : '';
    return etfTable + tlTable;
  }

  /* ---------------------------------------------------------- işlemler */
  function trades(port, raw) {
    const all = [...(raw.positions || []), ...(raw.closed || [])];
    const rows = [];
    all.forEach((p) => {
      const isTl = (p.asset_class || '').toUpperCase() === 'TL_DEPOSIT';
      rows.push({
        date: p.entry_date || p.start_date, ticker: isTl ? (p.bank || p.ticker) : p.ticker,
        kind: isTl ? 'Mevduat' : 'Alım', shares: isTl ? null : p.shares,
        price: isTl ? null : p.entry_price, fee: isTl ? null : p.fees_usd,
        amount: isTl ? F.moneyTry(p.principal_try) : F.money((p.shares || 0) * (p.entry_price || 0) + (p.fees_usd || 0)),
        note: p.type === 'KAGIT' ? 'kâğıt' : '',
      });
      if (p.exit_date) {
        rows.push({ date: p.exit_date, ticker: p.ticker, kind: 'Satış', shares: p.shares, price: p.exit_price,
          fee: p.exit_fees_usd, amount: F.money((p.shares || 0) * (p.exit_price || 0) - (p.exit_fees_usd || 0)), note: '' });
      }
    });
    (raw.cash_flows || []).forEach((c) => rows.push({ date: c.date, ticker: 'Nakit', kind: c.amount_usd >= 0 ? 'Giriş' : 'Çıkış',
      amount: F.signedMoney(c.amount_usd), note: c.note || '' }));
    rows.sort((a, b) => String(b.date).localeCompare(String(a.date)));

    return `<div class="h2row"><h2>İşlem günlüğü</h2><button id="addTrade" class="primary">+ İşlem ekle</button></div>
      <div class="card flush"><div class="table-wrap"><table class="tbl stackable">
      <thead><tr><th>İşlem</th><th class="r">Adet</th><th class="r">Fiyat</th>
        <th class="r">Ücret</th><th class="r">Tutar</th></tr></thead>
      <tbody>${rows.map((r) => `<tr>
        <td class="lead" data-label=""><b>${F.esc(r.ticker)}</b><span class="sub">${F.esc(r.kind)} · ${F.esc(F.date(r.date))}${r.note ? ` · ${F.esc(r.note)}` : ''}</span></td>
        <td class="r" data-label="Adet">${F.isNum(r.shares) ? F.esc(F.num(r.shares, r.shares % 1 ? 2 : 0)) : ''}</td>
        <td class="r" data-label="Fiyat">${F.isNum(r.price) ? F.esc(F.money(r.price)) : ''}</td>
        <td class="r" data-label="Ücret">${F.isNum(r.fee) && r.fee ? F.esc(F.money(r.fee)) : ''}</td>
        <td class="r" data-label="Tutar">${F.esc(r.amount)}</td></tr>`).join('')}</tbody></table></div></div>
      <p class="small muted" style="margin-top:8px">Midas'ın API'si yok; işlemler <code>data/portfolio.json</code>
        dosyasına elle ya da sohbetteki Claude ile (record_position) girilir.</p>`;
  }

  /* --------------------------------------------- işlem ekleme formu */
  function openAddTrade() {
    const today = new Date().toISOString().slice(0, 10);
    App.modal(`
      <h2>İşlem ekle</h2>
      <p class="muted small">Pano dosyaya yazamaz. Aşağıdaki parçayı <code>data/portfolio.json</code>
        içindeki <code>positions</code> dizisine ekle ya da sohbette Claude'a ver.</p>
      <div class="form-grid">
        <label>Sembol<input id="tTicker" placeholder="QQQM" autocomplete="off"></label>
        <label>Varlık sınıfı<select id="tClass"><option>ETF</option><option>STOCK</option></select></label>
        <label>Tarih<input type="date" id="tDate" value="${today}"></label>
        <label>Tür<select id="tType"><option>GERCEK</option><option>KAGIT</option></select></label>
        <label>Fiyat ($)<input type="number" id="tPrice" step="0.01"></label>
        <label>Adet<input type="number" id="tShares" step="0.0001"></label>
        <label>Komisyon ($)<input type="number" id="tFees" step="0.01" value="0"></label>
        <label>Gözden geçirme<input type="date" id="tReview"></label>
        <label class="full">Not<input id="tNotes" placeholder="Neden aldım"></label>
        <label class="full">JSON parçası<textarea id="tOut" rows="10" readonly></textarea></label>
      </div>
      <div class="row" style="margin-top:12px">
        <button id="tCopy" class="primary">Kopyala</button>
        <a href="${DataLayer.editUrl('data/portfolio.json')}" target="_blank" rel="noopener"><button>GitHub'da aç</button></a>
        <button id="tClose" class="ghost" style="margin-left:auto">Kapat</button>
      </div>`, (root) => {
      const val = (id) => root.querySelector('#' + id).value;
      const numv = (id) => { const v = parseFloat(val(id)); return isFinite(v) ? v : 0; };
      const upd = () => {
        root.querySelector('#tOut').value = JSON.stringify({
          ticker: (val('tTicker') || '').toUpperCase().trim(), asset_class: val('tClass'),
          type: val('tType'), broker: 'Midas', entry_date: val('tDate'), entry_price: numv('tPrice'),
          shares: numv('tShares'), fees_usd: numv('tFees'), review_date: val('tReview'),
          thesis_breakers: [], notes: val('tNotes').trim(), status: 'OPEN',
        }, null, 2);
      };
      ['tTicker', 'tClass', 'tType', 'tDate', 'tPrice', 'tShares', 'tFees', 'tReview', 'tNotes'].forEach((id) =>
        root.querySelector('#' + id).addEventListener('input', upd));
      upd();
      root.querySelector('#tCopy').addEventListener('click', () =>
        App.copy(root.querySelector('#tOut').value, 'İşlem JSON parçası kopyalandı'));
      root.querySelector('#tClose').addEventListener('click', App.closeModal);
    });
  }

  return { render };
})();
