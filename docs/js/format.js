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

  /* Bir metrik degerini SADE TURKCE cumleye cevirir.
     "1,00x" hicbir sey anlatmaz; "Her 1 dolar karin 1,00 dolari nakde
     donuyor" anlatir. */
  function sentence(metric, v) {
    const s = spec(metric);
    if (!s || !s.sentence || !isNum(v)) return '';
    const unit = s.unit;
    const shown = unit === '%' ? num(Math.abs(v), 1)
                : unit === '/9' ? String(Math.round(v))
                : num(v, Math.abs(v) >= 100 ? 0 : 2);
    let out = s.sentence.replace('{v}', shown);
    // Negatif yuzdelerde "%-5 getirdi" yerine "%5 kaybettirdi" gibi
    if (unit === '%' && v < 0) {
      out = out.replace('%' + shown, '%' + shown)
               .replace('degisti', 'azaldi')
               .replace('getirdi', 'kaybettirdi');
    }
    return out;
  }

  function plain(metric) {
    const s = spec(metric);
    return s && s.plain ? s.plain : '';
  }

  function unitName(metric) {
    const s = spec(metric);
    return s && s.unit_name ? s.unit_name : '';
  }

  /* Ucuz/pahali dili yalnizca DEGERLEME carpanlari icin anlamlidir.
     "Beneish M en ucuz %9'luk dilimde" gibi bir cumle sacmadir; orada
     "en iyi %9'luk dilimde" denmeli. */
  const VALUATION_METRICS = ['ev_ebit', 'ev_ebitda', 'ev_gross_profit', 'ev_sales',
                             'pe', 'peg', 'implied_growth', 'implied_vs_actual_growth'];

  /* Sektor yuzdeligini cumleye cevirir.
     0 = en dusuk deger, 100 = en yuksek deger. "Iyi" tarafi metrige gore
     degistigi icin burada YON de dikkate alinir. */
  function percentileSentence(metric, p, basis) {
    if (!isNum(p)) return '';
    const s = spec(metric);
    const where = basis === 'universe' ? 'tum sirketler icinde' : 'ayni sektorde';
    if (!s) return `${where} yuzde ${Math.round(p)}'lik dilimde`;

    const lowIsGood = s.direction === 'low_good';
    const isValuation = VALUATION_METRICS.indexOf(metric) !== -1;
    const rank = Math.round(p);

    if (lowIsGood && isValuation) {
      // Degerleme carpaninda DUSUK yuzdelik = ucuz
      if (rank <= 25) return `${where} en ucuz %${rank}'lik dilimde`;
      if (rank <= 50) return `${where} ortalamadan ucuz`;
      if (rank <= 75) return `${where} ortalamadan pahali`;
      return `${where} en pahali %${100 - rank}'lik dilimde`;
    }
    if (lowIsGood) {
      // Degerleme disi metrikte dusuk deger IYIDIR (borc, tahakkuk, SBC...)
      if (rank <= 25) return `${where} en iyi %${rank}'lik dilimde`;
      if (rank <= 50) return `${where} ortalamadan iyi`;
      if (rank <= 75) return `${where} ortalamadan zayif`;
      return `${where} en zayif %${100 - rank}'lik dilimde`;
    }
    if (rank >= 75) return `${where} en iyi %${100 - rank}'lik dilimde`;
    if (rank >= 50) return `${where} ortalamadan iyi`;
    if (rank >= 25) return `${where} ortalamadan zayif`;
    return `${where} en zayif %${rank}'lik dilimde`;
  }

  /* Sirketin KENDI gecmisine gore konumu — "kendi 5y %" bunu demek. */
  function ownHistorySentence(metric, p) {
    if (!isNum(p)) return '';
    const s = spec(metric);
    const lowIsGood = s && s.direction === 'low_good';
    const rank = Math.round(p);
    if (lowIsGood && VALUATION_METRICS.indexOf(metric) !== -1) {
      if (rank <= 20) return `Son 5 yilinin en ucuz %${rank}'inde`;
      if (rank <= 45) return 'Kendi gecmisine gore ucuz';
      if (rank <= 55) return 'Kendi 5 yillik ortalamasi civarinda';
      if (rank <= 80) return 'Kendi gecmisine gore pahali';
      return `Son 5 yilinin en pahali %${100 - rank}'inde`;
    }
    if (rank >= 80) return `Son 5 yilinin en iyi %${100 - rank}'inde`;
    if (rank >= 55) return 'Kendi gecmisine gore iyi';
    if (rank >= 45) return 'Kendi 5 yillik ortalamasi civarinda';
    if (rank >= 20) return 'Kendi gecmisine gore zayif';
    return `Son 5 yilinin en zayif %${rank}'inde`;
  }

  /* Kendi tarihsel dagilimi yalnizca DEGERLEME carpanlari icin hesaplanir;
     digerlerinde "veri yok" degil, "bu metrik icin hesaplanmiyor" denmeli. */
  const OWN_HISTORY_METRICS = ['ev_ebit', 'ev_sales', 'ev_gross_profit', 'fcf_yield_ev'];
  function hasOwnHistory(metric) {
    return OWN_HISTORY_METRICS.indexOf(metric) !== -1;
  }

  function colorMeaning(color) {
    return { green: 'iyi', yellow: 'sinirda', red: 'kotu', gray: 'veri yok' }[color] || '';
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
           percentileBar, esc, date, daysLabel, trackBadge, decisionBadge,
           sentence, plain, unitName, percentileSentence, ownHistorySentence,
           colorMeaning, hasOwnHistory };
})();
