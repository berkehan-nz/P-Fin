/* Bicimlendirme ve renk sistemi.
 *
 * Renk esikleri KODA GOMULU DEGILDIR — data/thresholds.json'dan gelir,
 * o da src/config.py'den uretilir. Tek dogru kaynak config.py'dir.
 *
 * Renk korlugu icin her hucre renge EK OLARAK yon oku (▲▼) ve ince bir
 * doluluk cubugu tasir; bilgi yalnizca renkle tasinmaz.
 */
window.Fmt = (function () {
  'use strict';

  let TH = {};   // thresholds.json -> thresholds
  function setThresholds(t) { TH = t || {}; }
  function spec(metric) { return TH[metric] || null; }

  const isNum = (v) => v !== null && v !== undefined && typeof v === 'number' && isFinite(v);

  function num(v, digits = 2) {
    if (!isNum(v)) return '—';
    return v.toLocaleString('tr-TR', { minimumFractionDigits: digits,
                                       maximumFractionDigits: digits });
  }

  function metricValue(metric, v) {
    if (!isNum(v)) return '—';
    const s = spec(metric);
    const unit = s ? s.unit : '';
    if (unit === '%') return `%${num(v, 1)}`;
    if (unit === 'x') return `${num(v, v >= 100 ? 0 : 2)}x`;
    if (unit === '/9') return `${Math.round(v)}/9`;
    return num(v, Math.abs(v) >= 100 ? 0 : 2);
  }

  function money(v, { musd = false, digits = 0 } = {}) {
    if (!isNum(v)) return '—';
    if (musd) {
      if (Math.abs(v) >= 1000) return `$${num(v / 1000, 2)}B`;
      return `$${num(v, 0)}M`;
    }
    return `$${v.toLocaleString('tr-TR', { minimumFractionDigits: digits,
                                           maximumFractionDigits: digits })}`;
  }

  function pct(v, digits = 1) { return isNum(v) ? `%${num(v, digits)}` : '—'; }

  function signedPct(v, digits = 1) {
    if (!isNum(v)) return '—';
    return `${v > 0 ? '+' : ''}${num(v, digits)}%`;
  }

  function pnlClass(v) {
    if (!isNum(v) || v === 0) return 'c-gray';
    return v > 0 ? 'c-green' : 'c-red';
  }

  /* Bir metrik degeri icin renk — config.py'deki color_for ile AYNI mantik. */
  function colorFor(metric, v) {
    if (!isNum(v)) return 'gray';
    const s = spec(metric);
    if (!s) return 'gray';
    if (s.direction === 'low_good') {
      if (v <= s.green_max) return 'green';
      if (v <= s.yellow_max) return 'yellow';
      return 'red';
    }
    if (v >= s.green_min) return 'green';
    if (v >= s.yellow_min) return 'yellow';
    return 'red';
  }

  /* Yon oku: metrigin "iyi" tarafina gore. Renk korlugu destegi. */
  function arrow(metric, color) {
    if (color === 'gray') return '';
    const s = spec(metric);
    if (!s) return '';
    if (color === 'green') return s.direction === 'low_good' ? '▼' : '▲';
    if (color === 'red') return s.direction === 'low_good' ? '▲' : '▼';
    return '◆';
  }

  /* Esik araligindaki konumu 0-1 arasi doluluk olarak verir. */
  function fillRatio(metric, v) {
    if (!isNum(v)) return 0;
    const s = spec(metric);
    if (!s) return 0;
    if (s.direction === 'low_good') {
      const span = Math.max(s.yellow_max * 2, 1);
      return Math.max(0, Math.min(1, 1 - v / span));
    }
    const span = Math.max(s.green_min * 1.6, 1);
    return Math.max(0, Math.min(1, v / span));
  }

  function label(metric) {
    const s = spec(metric);
    return s ? s.label : metric;
  }

  /* Renk + ok + cubuk tasiyan tam hucre. */
  function cell(metric, cellData) {
    const v = cellData && cellData.value;
    const color = (cellData && cellData.color) || colorFor(metric, v);
    const a = arrow(metric, color);
    const fill = Math.round(fillRatio(metric, v) * 100);
    return `<span class="chip ${color}" title="${esc(label(metric))}">
      <span class="arrow">${a}</span>${esc(metricValue(metric, v))}</span>
      <span class="bar ${color}" style="width:34px;display:inline-block;vertical-align:middle;margin-left:5px"><i style="width:${fill}%"></i></span>`;
  }

  function chip(metric, v, color) {
    const c = color || colorFor(metric, v);
    return `<span class="chip ${c}"><span class="arrow">${arrow(metric, c)}</span>${esc(metricValue(metric, v))}</span>`;
  }

  /* Yuzdelik cubugu — 0 en ucuz/en dusuk, 100 en pahali/en yuksek */
  function percentileBar(p, basis) {
    if (!isNum(p)) return '<span class="dim tiny">—</span>';
    const title = basis === 'universe' ? 'Sektorde yeterli sirket yok — tum evrene gore'
                : basis === 'sector' ? 'Sektor ici yuzdelik' : 'Yuzdelik';
    return `<span class="pctbar" title="${esc(title)}${basis === 'universe' ? ' ⚠' : ''}">
      <span class="track"><i style="left:${Math.max(0, Math.min(100, p))}%"></i></span>
      <span class="tiny dim num">${Math.round(p)}${basis === 'universe' ? '*' : ''}</span></span>`;
  }

  function esc(s) {
    return String(s === null || s === undefined ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function date(s) {
    if (!s) return '—';
    try {
      return new Date(s).toLocaleDateString('tr-TR',
        { day: '2-digit', month: 'short', year: 'numeric' });
    } catch (_) { return s; }
  }

  function daysLabel(n) {
    if (!isNum(n)) return '—';
    if (n < 0) return `${Math.abs(Math.round(n))} gun gecti`;
    return `${Math.round(n)} gun`;
  }

  function trackBadge(track) {
    const map = { A: ['accent', 'Kol A'], B: ['yellow', 'Kol B'], both: ['green', 'A+B'] };
    const [cls, text] = map[track] || ['gray', track || '—'];
    return `<span class="chip ${cls}">${esc(text)}</span>`;
  }

  function decisionBadge(action) {
    if (!action) return '';
    const map = { AL: 'green', BEKLE: 'yellow', ELE: 'red' };
    return `<span class="chip ${map[action] || 'gray'}">${esc(action)}</span>`;
  }

  return { setThresholds, spec, isNum, num, metricValue, money, pct, signedPct,
           pnlClass, colorFor, arrow, fillRatio, label, cell, chip,
           percentileBar, esc, date, daysLabel, trackBadge, decisionBadge };
})();
