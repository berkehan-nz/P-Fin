/* HAREKETLER — kayıt defteri.
 *
 *   Para girişleri  dışarıdan konan para; değer = bunların toplamı + kazanç
 *   İşlem günlüğü   alım, satış, mevduat, TL girişi + işlem ekleme formu
 *   Varlık tablosu  tüm pozisyonlar ayrıntılı (katlanmış)
 *   Cuma raporu     #/hareketler/haftalik
 * Kayıtla ilgili uyarılar (giriş kuru şüphesi gibi) burada gösterilir.
 */
window.ViewPortfolio = (function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const F = Fmt;

  async function render(arg) {
    const [port, raw, weekly] = await Promise.all([
      DataLayer.portfolio(), DataLayer.portfolioRaw(), DataLayer.weekly(),
    ]);

    if (arg === 'haftalik') {
      $('portfolioBody').innerHTML = `
        <div class="page-head"><h1>Cuma raporu</h1><a class="sub" href="#/hareketler">← Hareketler</a></div>
        ${ViewWeekly.html(weekly, port)}`;
      return;
    }

    $('portfolioBody').innerHTML = `
      <div class="page-head"><h1>Hareketler</h1>
        <span class="sub">para girişleri ve işlemler</span></div>
      ${warnings(port)}
      ${contributions(port)}
      ${trades(port, raw)}
      ${positions(port)}
      ${weekly && weekly.as_of ? `<p class="small" style="margin-top:16px"><a href="#/hareketler/haftalik">Cuma raporu · ${F.esc(F.date(weekly.as_of))} →</a></p>` : ''}`;

    const add = $('addTrade');
    if (add) add.addEventListener('click', openAddTrade);
  }

  /* Kayıtla ilgili uyarılar (giriş kuru, eksik veri...). Dağılım
     uyarıları Plan'da, alım hatırlatmaları Özet'te. */
  function warnings(port) {
    const shown = ['dilim_sapmasi', 'kademeli_alim'];
    return (port.warnings || []).filter((w) => !shown.includes(w.type)).map((w) =>
      `<div class="band ${w.level === 'high' ? 'bad' : 'warn'}"><span class="ico">!</span>
        <span>${F.esc(F.tr(w.message))}</span></div>`).join('');
  }

  /* PARA GİRİŞLERİ — portföye dışarıdan konan para. Değer = bunların
     toplamı + kazanç. Alım-satım burada yok: o para zaten portföyün içinde. */
  function contributions(port) {
    const perf = port.performance || {};
    const list = perf.contributions || [];
    if (!list.length) return '';
    let cum = 0;
    const rows = list.map((c) => {
      cum += c.usd || 0;
      const what = c.initial ? 'İlk sermaye' : 'Para girişi';
      const src = F.isNum(c.try) ? `${F.moneyTry(c.try)} · kur ${F.num(c.usdtry, 4)}` : '';
      return `<tr>
        <td class="lead" data-label=""><b>${F.esc(what)}</b><span class="sub">${F.esc(F.date(c.date))}${src ? ` · ${F.esc(src)}` : ''}</span></td>
        <td class="r" data-label="Tutar">${F.esc(c.initial ? F.money(c.usd) : F.signedMoney(c.usd))}</td>
        <td class="r" data-label="Toplam">${F.esc(F.money(cum))}</td></tr>`;
    }).join('');
    const gain = F.isNum(perf.return_usd) ? `<tr class="muted-row">
        <td class="lead" data-label=""><b>Kazanç</b><span class="sub">piyasa, faiz, kur, dağıtım</span></td>
        <td class="r ${F.changeClass(perf.return_pct)}" data-label="Tutar">${F.esc(F.signedMoney(perf.return_usd))}</td>
        <td class="r" data-label="Değer"><b>${F.esc(F.money(perf.value_usd))}</b></td></tr>` : '';
    return `<h2>Para girişleri</h2>
      <div class="card flush"><div class="table-wrap"><table class="tbl stackable">
      <thead><tr><th>Kaynak</th><th class="r">Tutar</th><th class="r">Toplam</th></tr></thead>
      <tbody>${rows}${gain}</tbody></table></div></div>
      <p class="small muted" style="margin-top:8px">Değer = yatırdığın para + kazanç. Para girişi kazanç sayılmaz;
        Özet grafiğinde kesik çizgiyle işaretlenir.</p>`;
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
    // TL ile gelen para (amount_try) da giriştir; eskiden "Çıkış" ve tutarsız görünüyordu.
    (raw.cash_flows || []).forEach((c) => {
      const tl = F.isNum(c.amount_try);
      const v = tl ? c.amount_try : c.amount_usd;
      rows.push({ date: c.date, ticker: tl ? 'TL' : 'Nakit', kind: v >= 0 ? 'Para girişi' : 'Para çıkışı',
        amount: tl ? `${v >= 0 ? '+' : F.MINUS}${F.moneyTry(Math.abs(v))}` : F.signedMoney(v), note: '' });
    });
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

  /* ------------------------------------------------- varlık tablosu */
  /* Özet'teki gruplu liste günlük bakış için; burası tüm ayrıntı (katlı). */
  function positions(port) {
    const open = (port.positions || []).filter((p) => p.status !== 'CLOSED');
    const etf = open.filter((p) => !p.tl_deposit).sort((a, b) => (b.value_usd || 0) - (a.value_usd || 0));
    const tl = open.filter((p) => p.tl_deposit);
    if (!open.length) return '';
    const pnl = (p) => (p.started ? `<span class="${F.changeClass(p.pnl_pct)}">${F.esc(F.signedMoney(p.pnl_usd))}</span>
      <span class="sub ${F.changeClass(p.pnl_pct)}">${F.esc(F.pct(p.pnl_pct))}</span>` : '<span class="pending">başlamadı</span>');

    const etfTable = etf.length ? `<h3>Fonlar</h3><div class="table-wrap">
      <table class="tbl stackable"><thead><tr><th>Sembol</th><th class="r">Adet</th><th class="r">Maliyet</th>
        <th class="r">Fiyat</th><th class="r">Değer</th><th class="r">Kazanç</th></tr></thead>
      <tbody>${etf.map((p) => `<tr>
        <td class="lead" data-label=""><b>${F.esc(p.ticker)}</b><span class="sub">${F.esc(F.sliceLabel(p.slice))} · ${F.esc(F.date(p.entry_date))}</span></td>
        <td class="r" data-label="Adet">${F.esc(F.num(p.shares, p.shares % 1 ? 2 : 0))}</td>
        <td class="r" data-label="Maliyet">${F.esc(F.money(p.cost_usd))}</td>
        <td class="r" data-label="Fiyat">${F.esc(F.money(p.price))}</td>
        <td class="r" data-label="Değer">${F.esc(F.money(p.value_usd))}</td>
        <td class="r" data-label="Kazanç">${pnl(p)}</td></tr>`).join('')}</tbody></table></div>` : '';

    const tlTable = tl.length ? `<h3>TL mevduat</h3><div class="table-wrap">
      <table class="tbl stackable"><thead><tr><th>Banka</th><th class="r">Anapara</th><th class="r">Faiz</th>
        <th class="r">Biriken net</th><th class="r">Vade</th><th class="r">Başa baş kur</th></tr></thead>
      <tbody>${tl.map((p) => { const t = p.tl_deposit; return `<tr>
        <td class="lead" data-label=""><b>${F.esc(t.bank || p.ticker)}</b><span class="sub">${F.esc(F.money(p.value_usd))} · giriş kuru ${F.esc(F.num(t.usdtry_at_entry, 2))}</span></td>
        <td class="r" data-label="Anapara">${F.esc(F.moneyTry(t.principal_try))}</td>
        <td class="r" data-label="Faiz">${F.esc(F.rate(t.annual_rate_pct))}<span class="sub">stopaj ${F.esc(F.rate(t.withholding_pct))}${p.withholding_confirmed === false ? ' · teyit bekliyor' : ''}</span></td>
        <td class="r" data-label="Biriken net">${F.esc(F.moneyTry(t.net_interest_try))}<span class="sub">${F.esc(F.money(t.net_interest_usd))}</span></td>
        <td class="r" data-label="Vade">${F.esc(F.date(t.maturity_date))}<span class="sub">${F.esc(t.days_to_maturity)} gün</span></td>
        <td class="r" data-label="Başa baş kur">${F.esc(F.num(t.usdtry_breakeven, 2))}${F.isNum(t.headroom_from_now_pct)
          ? `<span class="sub">bugünden ${F.esc(F.share(t.headroom_from_now_pct))} yukarıda</span>` : ''}</td></tr>`; }).join('')}</tbody></table></div>
      <p class="small muted" style="margin-top:8px">Başa baş kur: vadede USD/TRY bunun üstündeyse mevduat dolar bazında zarar ettirir.</p>` : '';

    return `<details class="fold"><summary>Varlık tablosu<span class="count">${open.length} pozisyon</span></summary>
      <div class="fold-body">${etfTable}${tlTable}</div></details>`;
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
