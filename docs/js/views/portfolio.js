/* 4. PORTFOY — pozisyon tablosu, ozet, uyarilar, sektor dagilimi. */
window.ViewPortfolio = (function () {
  'use strict';
  const $ = (id) => document.getElementById(id);

  async function render() {
    const p = await DataLayer.portfolio();
    const s = p.summary || {};
    const positions = p.positions || [];

    $('portfolioSubtitle').textContent = positions.length
      ? `${positions.length} acik pozisyon · Midas · ${Fmt.date(p.as_of)}`
      : 'Henuz pozisyon yok';

    const nasdaq = (s.vs_benchmark || {}).nasdaq100;
    const sp500 = (s.vs_benchmark || {}).sp500;

    $('portfolioSummary').innerHTML = [
      stat('Toplam deger', Fmt.money(s.portfolio_value_usd, { digits: 0 }),
           `hisse ${Fmt.money(s.equity_value_usd, { digits: 0 })} · nakit ${Fmt.money(s.cash_usd, { digits: 0 })}`),
      stat('Toplam K/Z', Fmt.money(s.pnl_usd, { digits: 0 }),
           Fmt.isNum(s.pnl_pct) ? Fmt.signedPct(s.pnl_pct) : '—', Fmt.pnlClass(s.pnl_usd)),
      stat('Nasdaq 100 farki', Fmt.isNum(nasdaq) ? Fmt.signedPct(nasdaq) : '—',
           'agirlikli, giristen itibaren', Fmt.pnlClass(nasdaq)),
      stat('S&P 500 farki', Fmt.isNum(sp500) ? Fmt.signedPct(sp500) : '—',
           'agirlikli, giristen itibaren', Fmt.pnlClass(sp500)),
      stat('En buyuk pozisyon', Fmt.isNum(s.largest_position_pct) ? Fmt.pct(s.largest_position_pct) : '—',
           'esik %15',
           Fmt.isNum(s.largest_position_pct) && s.largest_position_pct > 15 ? 'c-yellow' : ''),
    ].join('');

    renderWarnings(p.warnings || []);
    renderPositions(positions);
    renderSectorMix(s.sector_mix_pct || {});

    if (!$('addTrade').dataset.bound) {
      $('addTrade').dataset.bound = '1';
      $('addTrade').addEventListener('click', openAddTrade);
    }
  }

  function stat(label, value, sub, cls) {
    return `<div class="card stat"><div class="label">${Fmt.esc(label)}</div>
      <div class="value ${cls || ''}">${value}</div>
      <div class="sub">${Fmt.esc(sub || '')}</div></div>`;
  }

  function renderWarnings(warnings) {
    $('portfolioWarnings').innerHTML = warnings.length
      ? `<h2>Uyarilar</h2>` + warnings.map((w) =>
          `<div class="warn ${w.level}"><span>${
            w.level === 'high' ? '⛔' : w.level === 'medium' ? '⚠' : 'ℹ'}</span>
          <span>${Fmt.esc(w.message)}</span></div>`).join('')
      : '';
  }

  function renderPositions(positions) {
    if (!positions.length) {
      $('positionsTable').innerHTML = `<div class="empty-state">
        <h2>Pozisyon yok</h2>
        <p>Midas'ta bir islem yaptiktan sonra "Islem ekle" ile kaydet.
           Kagit (deneme) pozisyon da ekleyebilirsin.</p></div>`;
      return;
    }
    $('positionsTable').innerHTML = `<table>
      <thead><tr>
        <th>Sembol</th><th>Tur</th><th>Giris</th><th>Adet</th><th>Maliyet</th>
        <th>Fiyat</th><th>Deger</th><th>K/Z $</th><th>K/Z %</th><th>Agirlik</th>
        <th>Hedefe</th><th>Tutma</th><th>Gozden gecirme</th><th>Kazanc</th>
      </tr></thead>
      <tbody>${positions.map((p) => `<tr data-ticker="${Fmt.esc(p.ticker)}" style="cursor:pointer">
        <td><b>${Fmt.esc(p.ticker)}</b>
          <div class="tiny dim">${Fmt.esc(p.sector || '')}</div></td>
        <td><span class="chip ${p.type === 'KAGIT' ? 'gray' : 'accent'}">${Fmt.esc(p.type)}</span></td>
        <td class="num tiny">${Fmt.esc(p.entry_date)}<div class="dim">${Fmt.money(p.entry_price, { digits: 2 })}</div></td>
        <td class="num">${Fmt.num(p.shares, 0)}</td>
        <td class="num">${Fmt.money(p.cost_usd, { digits: 0 })}</td>
        <td class="num">${Fmt.money(p.price, { digits: 2 })}
          ${Fmt.isNum(p.change_1d_pct) ? `<div class="tiny ${Fmt.pnlClass(p.change_1d_pct)}">${Fmt.signedPct(p.change_1d_pct)}</div>` : ''}</td>
        <td class="num">${Fmt.money(p.value_usd, { digits: 0 })}</td>
        <td class="num ${Fmt.pnlClass(p.pnl_usd)}">${Fmt.money(p.pnl_usd, { digits: 0 })}</td>
        <td class="num ${Fmt.pnlClass(p.pnl_pct)}">${Fmt.isNum(p.pnl_pct) ? Fmt.signedPct(p.pnl_pct) : '—'}</td>
        <td class="num ${Fmt.isNum(p.weight_pct) && p.weight_pct > 15 ? 'c-yellow' : ''}">${Fmt.pct(p.weight_pct)}</td>
        <td class="num">${Fmt.isNum(p.upside_to_target_pct) ? Fmt.signedPct(p.upside_to_target_pct) : '—'}</td>
        <td class="num tiny">${Fmt.isNum(p.holding_days) ? p.holding_days + ' g' : '—'}</td>
        <td class="num tiny ${Fmt.isNum(p.days_to_review) && p.days_to_review < 0 ? 'c-yellow' : ''}">${
          p.review_date ? Fmt.daysLabel(p.days_to_review) : '—'}</td>
        <td class="num tiny">${p.next_earnings ? Fmt.esc(p.next_earnings) : '—'}</td>
      </tr>`).join('')}</tbody></table>`;

    $('positionsTable').querySelectorAll('[data-ticker]').forEach((el) =>
      el.addEventListener('click', () => { location.hash = `#/company/${el.dataset.ticker}`; }));
  }

  function renderSectorMix(mix) {
    const keys = Object.keys(mix);
    if (!keys.length) { $('sectorMix').innerHTML = '<p class="muted small">Veri yok</p>'; return; }
    keys.sort((a, b) => mix[b] - mix[a]);
    $('sectorMix').innerHTML = keys.map((k) => `
      <div style="margin-bottom:8px">
        <div class="spread tiny"><span>${Fmt.esc(k)}</span>
          <span class="num">${Fmt.pct(mix[k])}</span></div>
        <span class="bar ${mix[k] > 40 ? 'yellow' : 'green'}" style="display:block">
          <i style="width:${Math.min(100, mix[k])}%"></i></span>
      </div>`).join('') +
      (Math.max(...keys.map((k) => mix[k])) > 40
        ? '<p class="tiny c-yellow">Tek sektor agirligi %40\'i asiyor.</p>' : '');
  }

  /* --------------------------------------------- islem ekleme formu */
  function openAddTrade() {
    const today = new Date().toISOString().slice(0, 10);
    App.modal(`
      <h2>Islem ekle</h2>
      <p class="muted small">Midas'in API'si yok, islemler elle girilir.
        Asagidaki parcayi <code>data/portfolio.json</code> icindeki
        <code>positions</code> dizisine ekle.</p>
      <div class="form-grid">
        <label>Sembol<input id="tTicker" placeholder="DBX" autocomplete="off"></label>
        <label>Tur<select id="tType"><option>GERCEK</option><option>KAGIT</option></select></label>
        <label>Tarih<input type="date" id="tDate" value="${today}"></label>
        <label>Fiyat ($)<input type="number" id="tPrice" step="0.01" placeholder="26.40"></label>
        <label>Adet<input type="number" id="tShares" step="0.0001" placeholder="100"></label>
        <label>Komisyon ($)<input type="number" id="tFees" step="0.01" value="0"></label>
        <label>Hedef fiyat ($)<input type="number" id="tTarget" step="0.01" placeholder="40"></label>
        <label>Gozden gecirme<input type="date" id="tReview"></label>
        <label class="full">Not<input id="tNotes" placeholder="Neden aldim"></label>
        <label class="full">JSON parcasi<textarea id="tOut" rows="12" readonly></textarea></label>
      </div>
      <div class="row" style="margin-top:12px">
        <button id="tCopy" class="primary">Kopyala</button>
        <a href="${DataLayer.editUrl('data/portfolio.json')}" target="_blank"
           rel="noopener"><button>GitHub'da ac</button></a>
        <button id="tClose" class="ghost" style="margin-left:auto">Kapat</button>
      </div>`, (root) => {
      const val = (id) => root.querySelector('#' + id).value;
      const numv = (id) => { const v = parseFloat(val(id)); return isFinite(v) ? v : 0; };
      const upd = () => {
        root.querySelector('#tOut').value = JSON.stringify({
          ticker: (val('tTicker') || '').toUpperCase().trim(),
          type: val('tType'),
          broker: 'Midas',
          entry_date: val('tDate'),
          entry_price: numv('tPrice'),
          shares: numv('tShares'),
          fees_usd: numv('tFees'),
          target_price: numv('tTarget'),
          review_date: val('tReview'),
          thesis_breakers: [],
          notes: val('tNotes').trim(),
          status: 'OPEN',
        }, null, 2);
      };
      ['tTicker', 'tType', 'tDate', 'tPrice', 'tShares', 'tFees', 'tTarget',
       'tReview', 'tNotes'].forEach((id) =>
        root.querySelector('#' + id).addEventListener('input', upd));
      upd();
      root.querySelector('#tCopy').addEventListener('click', () =>
        App.copy(root.querySelector('#tOut').value, 'Islem JSON parcasi kopyalandi'));
      root.querySelector('#tClose').addEventListener('click', App.closeModal);
    });
  }

  return { render };
})();
