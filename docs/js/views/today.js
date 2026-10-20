/* ÖZET — "param ne durumda?" tek ekranda.
 *
 * Yukarıdan aşağıya ve başka hiçbir şey yok:
 *   1. Durum bandı (yalnızca gerekirse): fiyat eski / tez kırıcı / Cuma raporu
 *   2. Toplam varlık = yatırdığın para + kazanç; bugün; kazanç grafiği
 *   3. Varlıkların: türe göre gruplu (TL mevduat, endeks fonları, dolar
 *      faizi, nakit); satıra dokun → ayrıntı
 *   4. Sıradaki adımlar: yalnızca SENİN yapacağın işler (alım, vade, faz)
 * Hedef dağılım, kur senaryosu ve kıyaslar "Plan"da; kayıtlar "Hareketler"de.
 *
 * Para girişi kazanç değildir: grafik varsayılan olarak KAZANCI çizer
 * (değer − yatırılan; girişte sıçramaz), giriş günü kesik çizgiyle
 * işaretlenir. "Değer" düğmesi ham portföy değerine döner.
 */
window.ViewToday = (function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const F = Fmt;

  const SLICE_ORDER = ['tl', 'cekirdek_etf', 'sgov', 'motor', 'nakit'];
  const AGENDA_DAYS = 120;

  async function render() {
    const [port, hist, weekly] = await Promise.all([
      DataLayer.portfolio(), DataLayer.portfolioHistory(), DataLayer.weekly(),
    ]);
    const perf = port.performance || {};
    const rows = hist.rows || [];

    $('todayBody').innerHTML = `
      <div class="page-head"><h1>Özet</h1>${freshness(port)}</div>
      ${bands(port, weekly)}
      <section class="card" aria-label="Toplam varlık">
        ${perf.status === 'aktif' ? hero(perf) : heroNotStarted(port, perf)}
        <div id="todayChart"></div>
      </section>
      <div class="today-grid">
        <section><h2>Varlıkların</h2>${holdings(port, perf)}</section>
        <section>${agenda(port)}</section>
      </div>`;

    chart(rows, perf);
    wireRows();
  }

  /* ---------------------------------------------------------- tazelik */
  function freshness(port) {
    const stamp = port.priced_at || port.as_of;
    if (!stamp) return '';
    return `<span class="sub" title="Kaynak: yfinance, Stooq, FRED">Güncel · ${
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
        <a href="#/hareketler/haftalik">Cuma raporu hazır${n ? ` · ${n} madde eylem bekliyor` : ''} →</a>
        </span></div>`);
    }
    return out.join('');
  }

  /* ------------------------------------------------------------ hero */
  /* Toplam = yatırdığın + kazanç. Para girişi "Bugün"e de "Kazanç"a da
     girmez; giriş günü "Bugün"ün altında ayrıca yazılır. */
  function hero(perf) {
    const dayCls = F.changeClass(perf.day_change_pct);
    const gainCls = F.changeClass(perf.return_pct);
    const n = (perf.contributions || []).length;
    const added = perf.day_added_usd > 0
      ? `<div class="x">${F.esc(F.signedMoney(perf.day_added_usd))} para girişi hariç</div>` : '';
    const today = F.isNum(perf.day_change_usd) ? `<div class="fig today-fig"><div class="k">Bugün</div>
        <div class="v ${dayCls}">${F.esc(F.signedMoney(perf.day_change_usd))}</div>
        <div class="p ${dayCls}">${F.esc(F.pct(perf.day_change_pct))}</div>${added}</div>` : '';
    return `<div class="hero">
      <div>
        <div class="hero-label">Toplam varlığın · ${F.esc(F.date(perf.as_of))}</div>
        <div class="hero-value">${F.esc(F.money(perf.value_usd))}</div>
        <div class="hero-sub">${F.esc(F.moneyTry(perf.value_try))} · kur ${F.esc(F.num(perf.usdtry, 2))}</div>
      </div>
      ${today}
    </div>
    <div class="equation" title="Toplam varlık = yatırdığın para + kazanç">
      <div class="term"><span class="k">Yatırdığın</span>
        <b>${F.esc(F.money(perf.invested_usd))}</b>
        <span class="x">${n > 1 ? `<a href="#/hareketler">${F.esc(n)} para girişi</a>` : 'ilk sermaye'}</span></div>
      <span class="op" aria-hidden="true">+</span>
      <div class="term"><span class="k">Kazanç</span>
        <b class="${gainCls}">${F.esc(F.signedMoney(perf.return_usd))}</b>
        <span class="x ${gainCls}">${F.esc(F.pct(perf.return_pct))} · ${F.esc(perf.days)} günde</span></div>
    </div>`;
  }

  function heroNotStarted(port, perf) {
    const s = port.summary || {};
    const kalan = F.daysUntil(perf.inception);
    return `<div class="hero">
      <div>
        <div class="hero-label">Toplam varlığın · maliyet üzerinden</div>
        <div class="hero-value">${F.esc(F.money(s.portfolio_value_usd))}</div>
        <div class="hero-sub">${F.esc(F.moneyTry(s.portfolio_value_try))}</div>
      </div>
      <div class="fig"><div class="k">Başlangıç</div>
        <div class="v">${F.esc(F.date(perf.inception))}</div>
        <div class="x">${kalan > 0 ? `${kalan} gün sonra` : 'ilk kapanış fiyatı bekleniyor'}</div></div>
    </div>`;
  }

  /* ----------------------------------------------------------- grafik */
  /* Kazanç: değer − o güne kadar yatırılan (girişte sıçramaz).
     Değer: ham toplam (girişte sıçrar). Giriş günü her ikisinde işaretli.
     Alternatiflerle kıyas Plan ekranında. */
  function chart(rows, perf) {
    const host = $('todayChart');
    if (!host || rows.length < 2) return;
    const son = rows.slice(-60);
    const canGain = son.every((r) => F.isNum(r.invested_usd));
    let basis = canGain ? DataLayer.prefs.get('ovBasis', 'kazanc') : 'deger';
    if (basis !== 'deger' && basis !== 'kazanc') basis = 'kazanc';

    const marks = son.map((r, i) => ({ r, i })).filter(({ r }) => r.added_usd > 0).map(({ r, i }) => ({
      i,
      label: `+${F.isNum(r.added_try) ? F.moneyTry(r.added_try) : F.money(r.added_usd, { digits: 0 })} giriş`,
      tip: `Para girişi ${F.signedMoney(r.added_usd)}${F.isNum(r.added_try) ? ` (${F.moneyTry(r.added_try)})` : ''} · kazanç değil`,
    }));

    host.innerHTML = `<div class="chart-head">
        <span class="small muted">${son.length} işlem günü</span>
        ${canGain ? `<div class="seg" role="group" aria-label="Grafik">${[['kazanc', 'Kazanç'], ['deger', 'Toplam']].map(([k, v]) =>
          `<button data-basis="${k}" aria-pressed="${k === basis}">${v}</button>`).join('')}</div>` : ''}
      </div><div id="todayPlot"></div>`;

    const draw = () => {
      const gain = basis === 'kazanc';
      Charts.compare($('todayPlot'), {
        dates: son.map((r) => r.date),
        focus: { role: 'focus', label: gain ? 'Kazanç' : 'Toplam varlık', short: '',
                 values: son.map((r) => (gain ? r.total_usd - r.invested_usd : r.total_usd)) },
        fmt: (v) => (gain ? F.signedMoney(v) : F.money(v)),
        fmtTick: (v) => (gain ? F.signedMoney(v, 0) : F.money(v, { digits: 0 })),
        fmtDate: F.date,
        tipExtra: (i) => {
          const r = son[i];
          return F.isNum(r.invested_usd)
            ? `Toplam ${F.money(r.total_usd)} = yatırılan ${F.money(r.invested_usd)} ${
              r.total_usd >= r.invested_usd ? '+' : F.MINUS} ${F.money(Math.abs(r.total_usd - r.invested_usd))}` : '';
        },
        zero: gain,
        bandPct: gain ? 0 : 2,
        marks,
        height: marks.length ? 164 : 150,
        aria: gain ? 'Kazanç: toplam varlık eksi yatırılan para' : 'Toplam varlık',
      });
    };
    host.querySelectorAll('[data-basis]').forEach((btn) => btn.addEventListener('click', () => {
      basis = btn.dataset.basis;
      DataLayer.prefs.set('ovBasis', basis);
      host.querySelectorAll('[data-basis]').forEach((x) => x.setAttribute('aria-pressed', String(x.dataset.basis === basis)));
      draw();
    }));
    draw();
  }

  /* -------------------------------------------------------- varlıklar */
  /* Türe göre gruplu liste. Aynı sembolün parçaları (30 Ekim QQQM) tek
     satırda toplanır. Grup başlığı: tür, değer, pay; satır: varlık. */
  function merge(positions) {
    const by = new Map();
    positions.forEach((p) => {
      const key = p.tl_deposit ? p.ticker : `${p.slice}|${p.ticker}`;
      const g = by.get(key);
      if (!g) { by.set(key, { ...p, lots: 1 }); return; }
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

  function gainCell(usd, pct, started = true) {
    if (!started) return '<span class="pending">başlamadı</span>';
    if (!F.isNum(usd)) return '';
    const cls = F.changeClass(pct);
    return `<span class="${cls}">${F.esc(F.signedMoney(usd))}</span><span class="sub ${cls}">${F.esc(F.pct(pct))}</span>`;
  }

  let rowSeq = 0;
  function holdings(port, perf) {
    const s = port.summary || {};
    const slices = Object.fromEntries((s.slices || []).map((x) => [x.slice, x]));
    const open = merge((port.positions || []).filter((p) => p.status !== 'CLOSED'));
    const day = perf.positions_day || {};
    rowSeq = 0;

    const groups = SLICE_ORDER.map((key) => {
      const sl = slices[key] || {};
      const items = open.filter((p) => (p.slice || '') === key);
      if (key === 'nakit') {
        if (!F.isNum(s.cash_usd) || !s.cash_usd) return '';
        return `<li class="hold-group"><div class="hold-head">
            <span class="name"><b>Nakit</b><span class="sub">${F.esc(F.sliceHint('nakit'))}</span></span>
            <span class="val"><b>${F.esc(F.money(s.cash_usd))}</b><span class="sub">${F.esc(F.share(sl.actual_pct))}</span></span>
            <span class="gain"></span></div></li>`;
      }
      if (!items.length) return '';
      // Tek varlıklı grup (SGOV): başlık ile satır aynı olurdu; tek satır yeter.
      if (items.length === 1 && key !== 'tl') {
        return `<li class="hold-group single"><ul class="hold-items">${item(items[0], day[items[0].ticker] || {}, {
          title: F.sliceLabel(key), share: sl.actual_pct })}</ul></li>`;
      }
      const cost = items.reduce((a, p) => a + (p.cost_usd || 0), 0);
      const pnl = items.reduce((a, p) => a + (F.isNum(p.pnl_usd) ? p.pnl_usd : 0), 0);
      const tlTotal = key === 'tl'
        ? items.reduce((a, p) => a + ((p.tl_deposit || {}).value_try || 0), 0) : null;
      return `<li class="hold-group"><div class="hold-head">
          <span class="name"><b>${F.esc(F.sliceLabel(key))}</b><span class="sub">${tlTotal ? `${F.esc(F.moneyTry(tlTotal))}<span class="hint"> · ${F.esc(F.sliceHint(key))}</span>` : F.esc(F.sliceHint(key))}</span></span>
          <span class="val"><b>${F.esc(F.money(sl.value_usd))}</b><span class="sub">${F.esc(F.share(sl.actual_pct))}</span></span>
          <span class="gain">${gainCell(pnl, cost ? (pnl / cost) * 100 : null)}</span></div>
        <ul class="hold-items">${items.map((p) => item(p, day[p.ticker] || {})).join('')}</ul></li>`;
    }).join('');

    return `<div class="card flush"><ul class="holdings">${groups}</ul></div>
      <p class="small dim legend-note">Kazanç sütunu: alındığından bu yana. Satıra dokun → ayrıntı.</p>`;
  }

  /* opt.title: tek varlıklı grupta satır grup başlığı gibi görünür
     ("Dolar faizi · SGOV 5 adet") ve payı da gösterir. */
  function item(p, d, opt = {}) {
    const i = rowSeq++;
    const t = p.tl_deposit;
    const adet = `${F.num(p.shares, p.shares % 1 ? 2 : 0)} adet${p.lots > 1 ? ` · ${p.lots} parça` : ''}`;
    const name = t
      ? `<b>${F.esc(F.moneyTry(t.principal_try))}</b><span class="sub">${F.esc(t.bank || p.ticker)} · ${F.esc(F.rate(t.annual_rate_pct))} · vade ${
          F.esc(F.date(t.maturity_date))} (${F.esc(t.days_to_maturity)} gün)</span>`
      : opt.title
        ? `<b>${F.esc(opt.title)}</b><span class="sub">${F.esc(p.ticker)} · ${F.esc(adet)}</span>`
        : `<b>${F.esc(p.ticker)}</b><span class="sub">${F.esc(adet)}</span>`;
    const val = opt.title
      ? `<b>${F.esc(F.money(p.value_usd))}</b><span class="sub">${F.esc(F.share(opt.share))}</span>`
      : F.esc(F.money(p.value_usd));
    return `<li class="hold-item" data-row="${i}" tabindex="0" role="button" aria-expanded="false">
        <div class="hold-line"><span class="name"><span class="chev">›</span>${name}</span>
          <span class="val">${val}</span>
          <span class="gain">${gainCell(p.pnl_usd, p.pnl_pct, p.started)}</span></div>
        <div class="hold-detail" data-detail="${i}" hidden>${detail(p, d)}</div></li>`;
  }

  function fact(k, v, sub) {
    if (v === '' || v === null || v === undefined) return '';
    return `<div><dt>${F.esc(k)}</dt><dd>${v}${sub ? `<span class="sub">${sub}</span>` : ''}</dd></div>`;
  }

  function detail(p, d) {
    const t = p.tl_deposit;
    const today = F.isNum(d.usd) ? fact('Bugün', `<span class="${F.changeClass(d.pct)}">${F.esc(F.signedMoney(d.usd))}</span>`, F.esc(F.pct(d.pct))) : '';
    if (t) {
      const stopaj = p.withholding_confirmed === false ? ' · teyit bekliyor' : '';
      return `<dl class="facts">
        ${fact('Anapara', F.esc(F.moneyTry(t.principal_try)), `giriş kuru ${F.esc(F.num(t.usdtry_at_entry, 2))} · ${F.esc(F.money(p.cost_usd))}`)}
        ${fact('Faiz', `${F.esc(F.rate(t.annual_rate_pct))} brüt`, `stopaj ${F.esc(F.rate(t.withholding_pct))}${stopaj}`)}
        ${fact('Biriken net faiz', F.esc(F.moneyTry(t.net_interest_try)), `günde ${F.esc(F.moneyTry(t.daily_net_interest_try))}`)}
        ${fact('Vadede', F.esc(F.moneyTry(t.value_try_at_maturity)), F.esc(F.date(t.maturity_date)))}
        ${fact('Başa baş kur', F.esc(F.num(t.usdtry_breakeven, 2)), F.isNum(t.headroom_from_now_pct)
          ? `bugünkü kurdan ${F.esc(F.share(t.headroom_from_now_pct))} yukarıda` : '')}
        ${today}
      </dl>
      <p class="small muted"><a href="#/plan">Vadede ne yapmalı? Kur senaryosu → Plan</a></p>`;
    }
    const unit = p.shares ? (p.cost_usd - (p.fees_usd || 0)) / p.shares : null;
    return `<dl class="facts">
      ${fact('Maliyet', F.esc(F.money(p.cost_usd)), unit ? `birim ${F.esc(F.money(unit))} · komisyon ${F.esc(F.money(p.fees_usd))}` : '')}
      ${fact('Fiyat', F.esc(F.money(p.price)), p.price_as_of ? F.esc(F.date(p.price_as_of)) : '')}
      ${p.dividends_usd ? fact('Dağıtımlar', F.esc(F.money(p.dividends_usd)), 'değere dahil') : ''}
      ${fact('Alış', F.esc(F.date(p.entry_date)), F.esc(p.broker || ''))}
      ${today}
    </dl>`;
  }

  function wireRows() {
    document.querySelectorAll('#todayBody .hold-item').forEach((li) => {
      const toggle = () => {
        const d = li.querySelector('.hold-detail');
        const open = d.hidden;
        d.hidden = !open;
        li.classList.toggle('open', open);
        li.setAttribute('aria-expanded', String(open));
      };
      li.addEventListener('click', (e) => { if (!e.target.closest('a')) toggle(); });
      li.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
    });
  }

  /* ---------------------------------------------------- sıradaki adımlar */
  /* Yalnızca senin yapacağın işler; piyasa takvimi Plan'da. */
  function actionTitle(a, port) {
    if (a.kind === 'alim') return `${a.ticker || ''} alımı${F.trancheAmount(a) ? ` · ${F.trancheAmount(a)}` : ''}`;
    if (a.kind === 'vade') return `${F.depositLabel(a, port)} vadesi — karar`;
    if (a.kind === 'faz') {
      const m = /Faz\s*(\d)/.exec(a.title || '');
      const ph = ((App.thresholds.portfolio || {}).phases || []).find((p) => m && p.key === `faz${m[1]}`);
      return ph ? `${F.phaseLabel(ph)} başlıyor` : F.tr(a.title);
    }
    return F.tr(a.title);
  }

  function agenda(port) {
    const items = (port.actions || [])
      .filter((a) => F.isNum(a.days) && a.days >= 0 && a.days <= AGENDA_DAYS)
      .sort((a, b) => a.days - b.days || (a.kind === 'vade' ? -1 : 1)).slice(0, 4);
    if (!items.length) return '';
    return `<div class="h2row"><h2>Sıradaki adımlar</h2><a class="small" href="#/plan">Plan →</a></div>
      <div class="card"><ul class="agenda compact">${items.map((a) => `<li>
        <span class="when ${a.days <= 7 ? 'soon' : ''}">${F.esc(F.days(a.days))}</span>
        <span class="what">${F.esc(actionTitle(a, port))}</span><span class="date">${F.esc(F.date(a.date))}</span></li>`).join('')}</ul>
      </div>`;
  }

  return { render, actionTitle };
})();
