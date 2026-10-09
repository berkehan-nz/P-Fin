/* PİYASA — portföy dışındaki dünya.
 *
 * Genel bakıştan taşınan her şey burada: küresel piyasa, makro seriler,
 * tek bir takvim (makro + bilanço + SEC olayları + Fed/TCMB), takip
 * listesinde günün hareketleri ve haberler. Bugün ekranı yalnızca
 * portföyü gösterir; merak edince buraya geçilir.
 */
window.ViewMarket = (function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const F = Fmt;
  const NEWS_PAGE = 20;
  let newsShown = NEWS_PAGE;

  async function render() {
    const [pulse, macro, ov, port] = await Promise.all([
      DataLayer.pulse(), DataLayer.macro(), DataLayer.overview(), DataLayer.portfolio(),
    ]);
    newsShown = NEWS_PAGE;

    $('marketBody').innerHTML = `
      <div class="page-head"><h1>Piyasa</h1>${pulse.generated_at
        ? `<span class="sub" title="Kaynak: yfinance, FRED, Finnhub, SEC EDGAR">Güncel · ${F.esc(F.dateTime(pulse.generated_at))}</span>` : ''}</div>
      ${pulse.risk_note ? `<p class="muted">${F.esc(F.tr(pulse.risk_note))}</p>` : ''}
      ${markets(pulse.market || [])}
      ${macroSeries(macro.series || {})}
      ${calendar(pulse, port)}
      ${movers(ov.movers || [])}
      <div id="newsBox">${news(pulse, ov)}</div>`;
    wire(pulse, ov);
  }

  /* --------------------------------------------------- küresel piyasa */
  function markets(rows) {
    if (!rows.length) return '';
    const order = ['Hisse', 'Risk', 'Faiz', 'Kur', 'Emtia', 'Kripto'];
    const sorted = [...rows].sort((a, b) => order.indexOf(a.group) - order.indexOf(b.group));
    return `<h2>Küresel piyasa</h2><div class="tiles">${sorted.map((r) => {
      const big = Math.abs(r.value) >= 1000;
      return `<div class="tile" title="${F.esc(r.symbol || '')}">
        <div class="n">${F.esc(F.tr(r.label))}</div>
        <div class="v">${F.esc(F.num(r.value, big ? 0 : 2))}${r.unit === '%' ? '%' : ''}</div>
        <div class="row"><span class="${F.changeClass(r.change_1d_pct)}">${F.esc(F.pct(r.change_1d_pct))}</span>
          ${Charts.sparkline(r.series || [], { w: 64, h: 20, label: `${r.label} eğilimi` })}</div>
        <div class="small dim">5 gün ${F.esc(F.pct(r.change_5d_pct))}</div></div>`;
    }).join('')}</div>`;
  }

  /* ----------------------------------------------------- makro seriler */
  function macroSeries(series) {
    const keys = Object.keys(series).filter((k) => series[k] && F.isNum(series[k].value));
    if (!keys.length) return '';
    return `<h2>Makro seriler</h2><div class="tiles">${keys.map((k) => {
      const m = series[k];
      const chg = F.isNum(m.change_3m) ? `3 ayda ${m.change_3m > 0 ? '+' : m.change_3m < 0 ? F.MINUS : ''}${F.num(Math.abs(m.change_3m), 2)} puan` : '';
      return `<div class="tile"><div class="n">${F.esc(F.tr(m.label))}</div>
        <div class="v">${F.esc(F.num(m.value, 2))}${m.unit === '%' ? '%' : ''}</div>
        <div class="row"><span class="small muted">${F.esc(chg)}</span>
          ${Charts.sparkline((m.series || []).map((p) => p[1]), { w: 64, h: 20, label: `${m.label} eğilimi` })}</div></div>`;
    }).join('')}</div>`;
  }

  /* ------------------------------------------------------------ takvim */
  const KIND = { makro: 'makro', bilanco: 'bilanço', sec: 'SEC', fed: 'Fed', politika: 'politika', tcmb: 'TCMB' };

  function calendar(pulse, port) {
    const cal = pulse.calendar || {};
    const seen = new Set();
    const up = [...(cal.upcoming || []), ...(port.calendar || [])].filter((e) => {
      const key = `${e.date}|${e.title}`;
      if (seen.has(key)) return false;
      seen.add(key); return true;
    }).map((e) => ({ ...e, d: F.daysUntil(e.date) }))
      .filter((e) => F.isNum(e.d) && e.d >= 0).sort((a, b) => a.d - b.d).slice(0, 15);
    const recent = (cal.recent || []).slice(0, 10);
    if (!up.length && !recent.length) return '';
    const row = (e, upcoming) => `<li>
      <span class="when ${upcoming && e.d <= 2 ? 'soon' : ''}">${F.esc(upcoming ? F.days(e.d) : F.date(e.date))}</span>
      <span class="what">${e.ticker ? `<a href="#/sirket/${F.esc(e.ticker)}">${F.esc(F.tr(e.title))}</a>` : F.esc(F.tr(e.title))}
        <span class="sub">${F.esc(KIND[e.kind] || e.kind || '')}${e.detail ? ` · ${F.esc(F.tr(e.detail))}` : ''}</span></span>
      <span class="date">${upcoming ? F.esc(F.date(e.date)) : ''}</span></li>`;
    return `<h2>Takvim</h2><div class="card">
      <ul class="agenda compact">${up.map((e) => row(e, true)).join('')}</ul></div>
      ${recent.length ? `<details class="fold"><summary>Olan biten<span class="count">${recent.length}</span></summary>
        <div class="fold-body"><ul class="agenda compact">${recent.map((e) => row(e, false)).join('')}</ul></div></details>` : ''}`;
  }

  /* --------------------------------------------- takip listesi hareketleri */
  function movers(rows) {
    if (!rows.length) return '';
    return `<h2>Takip listesinde günün hareketleri</h2><div class="movers">${rows.map((m) =>
      `<a class="mover" href="#/sirket/${F.esc(m.ticker)}"><b>${F.esc(m.ticker)}</b>
        <span class="${F.changeClass(m.change_1d_pct)}">${F.esc(F.pct(m.change_1d_pct))}</span></a>`).join('')}</div>`;
  }

  /* --------------------------------------------------------- haberler */
  function newsList(pulse, ov) {
    return (pulse.news && pulse.news.length) ? pulse.news : (ov.news || []);
  }

  function news(pulse, ov) {
    const all = newsList(pulse, ov);
    if (!all.length) return '';
    const list = all.slice(0, newsShown);
    return `<h2>Haberler</h2><div class="card"><ul class="news">${list.map((n) => `<li>
        <a class="badge" href="#/sirket/${F.esc(n.ticker)}">${F.esc(n.ticker)}</a>
        <span><a href="${F.esc(n.url)}" target="_blank" rel="noopener">${F.esc(n.headline)}</a>
          <span class="meta">${F.esc(n.source)} · ${F.esc(F.date(n.date))}</span></span></li>`).join('')}</ul>
      ${all.length > list.length ? `<div class="more"><button id="moreNews">Daha fazla (${all.length - list.length})</button></div>` : ''}</div>`;
  }

  function wire(pulse, ov) {
    const btn = $('moreNews');
    if (!btn) return;
    btn.addEventListener('click', () => {
      newsShown += NEWS_PAGE;
      $('newsBox').innerHTML = news(pulse, ov);
      wire(pulse, ov);
    });
  }

  return { render };
})();
