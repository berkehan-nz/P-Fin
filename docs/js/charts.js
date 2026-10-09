/* SVG grafikler — kütüphane yok.
 *
 * Renkler CSS değişkenlerinden gelir; koyu ve açık temada aynı okunur.
 * Renk sözlüğü: veri çizgileri ve çubuklar --neutral; yalnızca portföy
 * çizgisi --accent. Yazılar veri rengini giymez. */
window.Charts = (function () {
  'use strict';
  const isNum = (v) => typeof v === 'number' && isFinite(v);
  const esc = (s) => Fmt.esc(s);
  const f1 = (x) => (Math.round(x * 10) / 10).toString();

  /* Küçük eğilim çizgisi. Renk yön bildirmez — yönü sayı söyler. */
  function sparkline(values, { w = 100, h = 26, accent = false, label = 'fiyat eğilimi' } = {}) {
    const pts = (values || []).filter(isNum);
    if (pts.length < 2) return '';
    const min = Math.min(...pts), max = Math.max(...pts);
    const span = (max - min) || 1;
    const step = w / (pts.length - 1);
    const d = pts.map((v, i) =>
      `${i === 0 ? 'M' : 'L'}${f1(i * step)},${f1(h - ((v - min) / span) * (h - 2) - 1)}`).join(' ');
    return `<svg viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" preserveAspectRatio="none"
      role="img" aria-label="${esc(label)}"><path d="${d}" fill="none"
      stroke="var(${accent ? '--accent' : '--neutral'})" stroke-width="1.5"
      stroke-linejoin="round" stroke-linecap="round"/></svg>`;
  }

  /* Dönemlik çubuklar (hasılat, FCF). Negatifler sıfır çizgisinin altında. */
  function bars(values, labels, { w = 460, h = 120, fmt = (v) => v, title = '' } = {}) {
    const vals = values || [];
    const present = vals.filter(isNum);
    if (!present.length) return '';
    const max = Math.max(...present, 0), min = Math.min(...present, 0);
    const span = (max - min) || 1;
    const chartH = h - 20;
    const zeroY = chartH * (max / span);
    const bw = w / vals.length;
    const rects = vals.map((v, i) => {
      if (!isNum(v)) return '';
      const y = chartH * ((max - v) / span);
      const top = Math.min(y, zeroY);
      const height = Math.max(Math.abs(zeroY - y), 1);
      const lab = labels && labels[i] ? labels[i] : '';
      return `<rect x="${f1(i * bw + bw * 0.18)}" y="${f1(top)}" width="${f1(Math.min(bw * 0.64, 24))}"
        height="${f1(height)}" fill="var(--neutral)" rx="2"><title>${esc(lab)}: ${esc(fmt(v))}</title></rect>`;
    }).join('');
    const first = labels && labels[0] ? labels[0] : '';
    const last = labels && labels[labels.length - 1] ? labels[labels.length - 1] : '';
    return `<div><div class="spread small"><span class="muted">${esc(title)}</span>
        <b class="num">${esc(fmt(present[present.length - 1]))}</b></div>
      <svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}" role="img" aria-label="${esc(title)}">
        ${rects}
        <line x1="0" y1="${f1(zeroY)}" x2="${w}" y2="${f1(zeroY)}" stroke="var(--line)" stroke-width="1"/>
        <text x="0" y="${h - 3}" font-size="12" fill="var(--text-3)">${esc(first)}</text>
        <text x="${w}" y="${h - 3}" font-size="12" fill="var(--text-3)" text-anchor="end">${esc(last)}</text>
      </svg></div>`;
  }

  /* Seviye serisi (brüt marj, hisse sayısı). */
  function line(values, labels, { w = 460, h = 120, fmt = (v) => v, title = '' } = {}) {
    const vals = values || [];
    const present = vals.filter(isNum);
    if (present.length < 2) return '';
    const max = Math.max(...present), min = Math.min(...present);
    const span = (max - min) || 1;
    const chartH = h - 24;
    const step = w / Math.max(vals.length - 1, 1);
    let d = '', pen = false, lastPt = null;
    vals.forEach((v, i) => {
      if (!isNum(v)) { pen = false; return; }
      const x = i * step, y = 4 + (chartH - 4) * (1 - (v - min) / span);
      d += `${pen ? 'L' : 'M'}${f1(x)},${f1(y)}`;
      pen = true; lastPt = [x, y];
    });
    const first = labels && labels[0] ? labels[0] : '';
    const last = labels && labels[labels.length - 1] ? labels[labels.length - 1] : '';
    return `<div><div class="spread small"><span class="muted">${esc(title)}</span>
        <b class="num">${esc(fmt(present[present.length - 1]))}</b></div>
      <svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}" role="img" aria-label="${esc(title)}">
        <path d="${d}" fill="none" stroke="var(--neutral)" stroke-width="2" stroke-linejoin="round"/>
        ${lastPt ? `<circle cx="${f1(lastPt[0])}" cy="${f1(lastPt[1])}" r="4" fill="var(--neutral)"
          stroke="var(--surface)" stroke-width="2"/>` : ''}
        <text x="0" y="${h - 3}" font-size="12" fill="var(--text-3)">${esc(first)}</text>
        <text x="${w}" y="${h - 3}" font-size="12" fill="var(--text-3)" text-anchor="end">${esc(last)}</text>
      </svg></div>`;
  }

  /* Puan halkası — 0-100, tek renk. İyi/kötü rengi taşımaz; sayı konuşur. */
  function scoreRing(score, { size = 48 } = {}) {
    const r = (size - 6) / 2;
    const c = 2 * Math.PI * r;
    const v = isNum(score) ? Math.max(0, Math.min(100, score)) : 0;
    return `<div class="ring" style="width:${size}px;height:${size}px" role="img"
      aria-label="Genel puan ${isNum(score) ? Math.round(score) : 'yok'}">
      <svg width="${size}" height="${size}">
        <circle cx="${size / 2}" cy="${size / 2}" r="${r}" fill="none" stroke="var(--surface-2)" stroke-width="4"/>
        <circle cx="${size / 2}" cy="${size / 2}" r="${r}" fill="none" stroke="var(--neutral)" stroke-width="4"
          stroke-linecap="round" stroke-dasharray="${f1(c * v / 100)} ${f1(c)}"/>
      </svg>
      <span class="n">${isNum(score) ? Math.round(score) : ''}</span></div>`;
  }

  /* Analist dağılımı: gri tonlar + yazıyla; renk değil sayı anlatır. */
  function ratingBar(buy, hold, sell) {
    const b = buy || 0, h = hold || 0, s = sell || 0;
    const total = b + h + s;
    if (!total) return '';
    const seg = (n, tone) => n ? `<span style="flex:${n};background:var(${tone})"></span>` : '';
    return `<div style="display:flex;gap:2px;height:10px;border-radius:3px;overflow:hidden">
      ${seg(b, '--tone-4')}${seg(h, '--tone-3')}${seg(s, '--tone-1')}</div>
      <div class="small muted" style="margin-top:6px">${b} al · ${h} tut · ${s} sat</div>`;
  }

  /* Hedef fiyat aralığı — düşük / medyan / yüksek + mevcut fiyat. */
  function targetRange(low, median, high, price) {
    if (!isNum(low) || !isNum(high) || high <= low) return '';
    const pos = (v) => Math.max(0, Math.min(100, ((v - low) / (high - low)) * 100));
    return `<div style="position:relative;height:6px;background:var(--surface-2);border-radius:3px;margin:14px 0 8px">
      ${isNum(median) ? `<span title="Medyan" style="position:absolute;left:${f1(pos(median))}%;top:-4px;
        width:2px;height:14px;background:var(--neutral)"></span>` : ''}
      ${isNum(price) ? `<span title="Bugünkü fiyat" style="position:absolute;left:${f1(pos(price))}%;top:-6px;
        width:2px;height:18px;background:var(--accent)"></span>` : ''}</div>
      <div class="spread small muted"><span class="num">${Fmt.money(low)}</span>
        <span class="num">medyan ${Fmt.money(median)}</span><span class="num">${Fmt.money(high)}</span></div>`;
  }

  /* KIYAS ÇİZGİSİ — portföy (vurgulu) + tek bir kıyas (gri).
   *
   * Tek eksen (USD). Eksen en az ±%2'lik bant gösterir: 10 günlük %0,1'lik
   * kıpırtı bütün yüksekliği kaplayıp dağ gibi görünüyordu. Veri banttan
   * taşarsa eksen genişler.
   *
   * Lejant her zaman var; uç noktada kısa ad. İpucu klavyeyle de açılır
   * (ok tuşları). Etiketler textContent ile yazılır. */
  function compare(host, cfg) {
    const { dates, focus, context } = cfg;
    const fmt = cfg.fmt || ((v) => String(v));
    const fmtTick = cfg.fmtTick || fmt;
    const fmtDate = cfg.fmtDate || ((d) => d);
    const H = cfg.height || 160;
    const band = cfg.bandPct == null ? 2 : cfg.bandPct;
    const series = [focus, context].filter(Boolean);
    const n = dates.length;

    host.innerHTML = '';
    const make = (tag, cls, text) => {
      const el = document.createElement(tag);
      if (cls) el.className = cls;
      if (text !== undefined) el.textContent = text;
      return el;
    };
    const lastOf = (vals) => {
      for (let i = vals.length - 1; i >= 0; i--) if (isNum(vals[i])) return i;
      return -1;
    };

    const legend = make('div', 'cmp-legend');
    series.forEach((s) => {
      const k = make('span', 'cmp-key');
      k.append(make('i', s.role === 'focus' ? 'k-focus' : 'k-context'));
      k.append(make('span', null, s.label));
      const li = lastOf(s.values);
      if (li >= 0) k.append(make('b', null, fmt(s.values[li])));
      legend.append(k);
    });
    const plot = make('div', 'cmp-plot');
    const tip = make('div', 'cmp-tip');
    tip.hidden = true;
    host.append(legend, plot);

    let lastW = 0;
    function draw() {
      const W = Math.max(Math.round(plot.clientWidth), 240);
      if (W === lastW) return;
      lastW = W;
      const padL = 60, padR = 44, padT = 10, padB = 22;
      const all = series.flatMap((s) => s.values.filter(isNum));
      const ref = focus.values[lastOf(focus.values)] || all[all.length - 1] || 1;
      let lo = Math.min(...all, ref * (1 - band / 100));
      let hi = Math.max(...all, ref * (1 + band / 100));
      const step = niceStep((hi - lo) / 3);
      lo = Math.floor(lo / step) * step;
      hi = Math.ceil(hi / step) * step;
      const ticks = [];
      for (let t = lo; t <= hi + step / 2; t += step) ticks.push(t);

      const x = (i) => padL + (n === 1 ? 0 : i * (W - padL - padR) / (n - 1));
      const y = (v) => padT + (1 - (v - lo) / (hi - lo)) * (H - padT - padB);

      const grid = ticks.map((t) => `<line x1="${padL}" x2="${W - padR}" y1="${f1(y(t))}" y2="${f1(y(t))}"
          class="cmp-grid"/><text x="${padL - 8}" y="${f1(y(t) + 4)}" text-anchor="end"
          class="cmp-tick">${esc(fmtTick(t))}</text>`).join('');

      const path = (vals) => {
        let d = '', pen = false;
        vals.forEach((v, i) => {
          if (!isNum(v)) { pen = false; return; }
          d += `${pen ? 'L' : 'M'}${f1(x(i))},${f1(y(v))}`;
          pen = true;
        });
        return d;
      };
      const lines = [...series].reverse().map((s) => `<path d="${path(s.values)}"
          class="${s.role === 'focus' ? 'cmp-focus' : 'cmp-context'}"/>`).join('');

      const ends = series.map((s) => ({ s, i: lastOf(s.values) })).filter((e) => e.i >= 0);
      const topKey = ends.length === 2
        ? (ends[0].s.values[ends[0].i] >= ends[1].s.values[ends[1].i] ? 0 : 1) : 0;
      const gap = ends.length === 2
        ? Math.abs(y(ends[0].s.values[ends[0].i]) - y(ends[1].s.values[ends[1].i])) : 99;
      const endMarks = ends.map((e, k) => {
        const cx = x(e.i), cy = y(e.s.values[e.i]);
        // Uçlar birbirine çok yakınsa etiketleri dikeyde ayır.
        const ly = gap < 14 ? cy + (k === topKey ? -7 : 11) : cy + 4;
        return `<circle cx="${f1(cx)}" cy="${f1(cy)}" r="4"
            class="${e.s.role === 'focus' ? 'cmp-dot-focus' : 'cmp-dot-context'}"/>
          <text x="${f1(cx + 8)}" y="${f1(ly)}" class="cmp-end">${esc(e.s.short || e.s.label)}</text>`;
      }).join('');

      const xl = `<text x="${padL}" y="${H - 4}" class="cmp-tick">${esc(fmtDate(dates[0]))}</text>
        <text x="${W - padR}" y="${H - 4}" text-anchor="end" class="cmp-tick">${esc(fmtDate(dates[n - 1]))}</text>`;

      plot.innerHTML = `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" tabindex="0"
          role="img" aria-label="${esc(cfg.aria || 'Portföy değeri grafiği')}">
        ${grid}${lines}${endMarks}${xl}
        <g class="cmp-hover" visibility="hidden">
          <line class="cmp-cross" y1="${padT}" y2="${H - padB}"/>
          ${series.map((s) => `<circle r="4" class="${s.role === 'focus'
            ? 'cmp-dot-focus' : 'cmp-dot-context'}"/>`).join('')}
        </g>
        <rect x="${padL}" y="0" width="${W - padL - padR}" height="${H}" fill="transparent" class="cmp-hit"/>
      </svg>`;
      plot.append(tip);

      const svg = plot.querySelector('svg');
      const hover = svg.querySelector('.cmp-hover');
      const cross = hover.querySelector('line');
      const dots = hover.querySelectorAll('circle');
      let cur = -1;

      function show(i) {
        cur = Math.max(0, Math.min(n - 1, i));
        const cx = x(cur);
        cross.setAttribute('x1', cx); cross.setAttribute('x2', cx);
        series.forEach((s, k) => {
          const v = s.values[cur];
          dots[k].setAttribute('visibility', isNum(v) ? 'visible' : 'hidden');
          if (isNum(v)) { dots[k].setAttribute('cx', cx); dots[k].setAttribute('cy', y(v)); }
        });
        hover.setAttribute('visibility', 'visible');
        tip.textContent = '';
        tip.append(make('div', 'cmp-tip-date', fmtDate(dates[cur])));
        series.forEach((s) => {
          const row = make('div', 'cmp-tip-row');
          row.append(make('i', s.role === 'focus' ? 'k-focus' : 'k-context'));
          row.append(make('b', null, isNum(s.values[cur]) ? fmt(s.values[cur]) : ''));
          row.append(make('span', 'dim', s.label));
          tip.append(row);
        });
        if (cfg.diff && series.length === 2) {
          const txt = cfg.diff(focus.values[cur], context.values[cur]);
          if (txt) tip.append(make('div', 'cmp-tip-diff', txt));
        }
        tip.hidden = false;
        const tw = tip.offsetWidth;
        tip.style.left = `${cx + 12 + tw > W ? Math.max(0, cx - 12 - tw) : cx + 12}px`;
        tip.style.top = `${padT}px`;
      }
      function hide() { hover.setAttribute('visibility', 'hidden'); tip.hidden = true; cur = -1; }
      function at(ev) {
        const r = svg.getBoundingClientRect();
        return n === 1 ? 0 : Math.round((ev.clientX - r.left - padL) / ((W - padL - padR) / (n - 1)));
      }
      const hit = svg.querySelector('.cmp-hit');
      hit.addEventListener('pointermove', (ev) => show(at(ev)));
      hit.addEventListener('pointerdown', (ev) => show(at(ev)));
      hit.addEventListener('pointerleave', hide);
      svg.addEventListener('focus', () => show(cur >= 0 ? cur : n - 1));
      svg.addEventListener('blur', hide);
      svg.addEventListener('keydown', (ev) => {
        if (ev.key === 'ArrowLeft') { show((cur < 0 ? n : cur) - 1); ev.preventDefault(); }
        else if (ev.key === 'ArrowRight') { show((cur < 0 ? n - 2 : cur) + 1); ev.preventDefault(); }
        else if (ev.key === 'Escape') hide();
      });
    }

    draw();
    if (window.ResizeObserver) new ResizeObserver(() => draw()).observe(plot);
  }

  function niceStep(raw) {
    if (!(raw > 0)) return 1;
    const p = Math.pow(10, Math.floor(Math.log10(raw)));
    const f = raw / p;
    return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * p;
  }

  return { sparkline, bars, line, scoreRing, ratingBar, targetRange, compare };
})();
