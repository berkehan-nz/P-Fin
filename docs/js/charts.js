/* SVG grafikler — kutuphane yok.
 * Hepsi tema degiskenlerini (currentColor / CSS var) kullanir ki koyu ve
 * acik temada ayni sekilde okunsun. */
window.Charts = (function () {
  'use strict';
  const isNum = (v) => typeof v === 'number' && isFinite(v);

  function sparkline(values, { w = 110, h = 28, color = 'var(--accent)' } = {}) {
    const pts = (values || []).filter(isNum);
    if (pts.length < 2) return `<span class="dim tiny">grafik yok</span>`;
    const min = Math.min(...pts), max = Math.max(...pts);
    const span = (max - min) || 1;
    const step = w / (pts.length - 1);
    const d = pts.map((v, i) =>
      `${i === 0 ? 'M' : 'L'}${(i * step).toFixed(1)},${(h - ((v - min) / span) * h).toFixed(1)}`
    ).join(' ');
    const up = pts[pts.length - 1] >= pts[0];
    const stroke = color === 'auto' ? (up ? 'var(--green)' : 'var(--red)') : color;
    return `<svg viewBox="0 0 ${w} ${h}" width="${w}" height="${h}"
      preserveAspectRatio="none" role="img" aria-label="fiyat grafigi">
      <path d="${d}" fill="none" stroke="${stroke}" stroke-width="1.4"
            stroke-linejoin="round" stroke-linecap="round"/></svg>`;
  }

  /* Ceyreklik cubuk grafik — hasilat, FCF gibi seriler icin.
     Negatif degerler sifir cizgisinin altina cizilir. */
  function bars(values, labels, { w = 460, h = 110, fmt = (v) => v,
                                  title = '' } = {}) {
    const vals = values || [];
    const present = vals.filter(isNum);
    if (!present.length) return `<div class="dim tiny">${Fmt.esc(title)}: veri yok</div>`;

    const max = Math.max(...present, 0);
    const min = Math.min(...present, 0);
    const span = (max - min) || 1;
    const pad = 18;
    const chartH = h - pad;
    const zeroY = chartH * (max / span);
    const bw = w / vals.length;

    const rects = vals.map((v, i) => {
      if (!isNum(v)) return '';
      const y = chartH * ((max - v) / span);
      const top = Math.min(y, zeroY);
      const height = Math.max(Math.abs(zeroY - y), 1);
      const fill = v < 0 ? 'var(--red)' : 'var(--accent)';
      const lab = labels && labels[i] ? labels[i] : '';
      return `<rect x="${(i * bw + bw * 0.16).toFixed(1)}" y="${top.toFixed(1)}"
        width="${(bw * 0.68).toFixed(1)}" height="${height.toFixed(1)}"
        fill="${fill}" rx="1.5"><title>${Fmt.esc(lab)}: ${Fmt.esc(fmt(v))}</title></rect>`;
    }).join('');

    const first = labels && labels[0] ? labels[0] : '';
    const last = labels && labels[labels.length - 1] ? labels[labels.length - 1] : '';

    return `<div>
      <div class="spread tiny dim"><span>${Fmt.esc(title)}</span>
        <span class="num">${Fmt.esc(fmt(present[present.length - 1]))}</span></div>
      <svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}" role="img"
           aria-label="${Fmt.esc(title)}">
        ${rects}
        <line x1="0" y1="${zeroY.toFixed(1)}" x2="${w}" y2="${zeroY.toFixed(1)}"
              stroke="var(--line)" stroke-width="1"/>
        <text x="0" y="${h - 4}" font-size="9" fill="var(--text-3)">${Fmt.esc(first)}</text>
        <text x="${w}" y="${h - 4}" font-size="9" fill="var(--text-3)"
              text-anchor="end">${Fmt.esc(last)}</text>
      </svg></div>`;
  }

  /* Cizgi grafik — brut marj, hisse sayisi gibi seviye serileri */
  function line(values, labels, { w = 460, h = 110, fmt = (v) => v,
                                  title = '', color = 'var(--accent)' } = {}) {
    const vals = values || [];
    const present = vals.filter(isNum);
    if (present.length < 2) return `<div class="dim tiny">${Fmt.esc(title)}: veri yok</div>`;

    const max = Math.max(...present), min = Math.min(...present);
    const span = (max - min) || 1;
    const pad = 18;
    const chartH = h - pad;
    const step = w / Math.max(vals.length - 1, 1);

    let d = '', started = false;
    const dots = [];
    vals.forEach((v, i) => {
      if (!isNum(v)) return;
      const x = i * step, y = chartH * (1 - (v - min) / span);
      d += `${started ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`;
      started = true;
      const lab = labels && labels[i] ? labels[i] : '';
      dots.push(`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="2" fill="${color}">
        <title>${Fmt.esc(lab)}: ${Fmt.esc(fmt(v))}</title></circle>`);
    });

    const first = labels && labels[0] ? labels[0] : '';
    const last = labels && labels[labels.length - 1] ? labels[labels.length - 1] : '';

    return `<div>
      <div class="spread tiny dim"><span>${Fmt.esc(title)}</span>
        <span class="num">${Fmt.esc(fmt(present[present.length - 1]))}</span></div>
      <svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}" role="img"
           aria-label="${Fmt.esc(title)}">
        <path d="${d}" fill="none" stroke="${color}" stroke-width="1.6"
              stroke-linejoin="round"/>
        ${dots.join('')}
        <text x="0" y="${h - 4}" font-size="9" fill="var(--text-3)">${Fmt.esc(first)}</text>
        <text x="${w}" y="${h - 4}" font-size="9" fill="var(--text-3)"
              text-anchor="end">${Fmt.esc(last)}</text>
      </svg></div>`;
  }

  /* Puan halkasi — 0-100 */
  function scoreRing(score, { size = 52 } = {}) {
    const r = (size - 7) / 2;
    const c = 2 * Math.PI * r;
    const v = isNum(score) ? Math.max(0, Math.min(100, score)) : 0;
    const color = !isNum(score) ? 'var(--gray)'
                : v >= 70 ? 'var(--green)' : v >= 45 ? 'var(--yellow)' : 'var(--red)';
    return `<div class="score-ring" style="width:${size}px;height:${size}px">
      <svg width="${size}" height="${size}">
        <circle cx="${size / 2}" cy="${size / 2}" r="${r}" fill="none"
                stroke="var(--line)" stroke-width="4"/>
        <circle cx="${size / 2}" cy="${size / 2}" r="${r}" fill="none"
                stroke="${color}" stroke-width="4" stroke-linecap="round"
                stroke-dasharray="${(c * v / 100).toFixed(1)} ${c.toFixed(1)}"/>
      </svg>
      <span class="n" style="color:${color}">${isNum(score) ? Math.round(score) : '—'}</span>
    </div>`;
  }

  /* Alt puan mini cubugu */
  function miniBar(score) {
    const v = isNum(score) ? Math.max(0, Math.min(100, score)) : 0;
    const color = !isNum(score) ? 'gray' : v >= 70 ? 'green' : v >= 45 ? 'yellow' : 'red';
    return `<span class="bar ${color}" style="display:block"><i style="width:${v}%"></i></span>`;
  }

  /* Analist al/tut/sat dagilim cubugu */
  function ratingBar(buy, hold, sell) {
    const b = buy || 0, h = hold || 0, s = sell || 0;
    const total = b + h + s;
    if (!total) return '<span class="dim tiny">analist verisi yok</span>';
    const seg = (n, color) => n ? `<span style="flex:${n};background:${color};height:100%"></span>` : '';
    return `<div style="display:flex;height:16px;border-radius:3px;overflow:hidden;
                        border:1px solid var(--line)">
      ${seg(b, 'var(--green)')}${seg(h, 'var(--yellow)')}${seg(s, 'var(--red)')}
    </div>
    <div class="tiny dim" style="margin-top:4px">
      <span class="c-green">${b} al</span> · <span class="c-yellow">${h} tut</span>
      · <span class="c-red">${s} sat</span></div>`;
  }

  /* Hedef fiyat araligi — dusuk / medyan / yuksek + mevcut fiyat */
  function targetRange(low, median, high, price) {
    if (!isNum(low) || !isNum(high) || high <= low) {
      return '<span class="dim tiny">hedef fiyat verisi yok</span>';
    }
    const pos = (v) => Math.max(0, Math.min(100, ((v - low) / (high - low)) * 100));
    const marks = [];
    if (isNum(median)) marks.push(`<span style="position:absolute;left:${pos(median)}%;
      top:-3px;width:2px;height:14px;background:var(--text-2)" title="Medyan"></span>`);
    if (isNum(price)) marks.push(`<span style="position:absolute;left:${pos(price)}%;
      top:-5px;width:2px;height:18px;background:var(--accent)" title="Mevcut fiyat"></span>`);
    return `<div style="position:relative;height:8px;background:var(--bg-3);
                        border-radius:4px;margin:10px 0 6px">
      <div style="position:absolute;inset:0;background:linear-gradient(90deg,
        var(--red-bg),var(--yellow-bg),var(--green-bg));border-radius:4px"></div>
      ${marks.join('')}</div>
    <div class="spread tiny dim"><span class="num">${Fmt.money(low, { digits: 2 })}</span>
      <span class="num">medyan ${Fmt.money(median, { digits: 2 })}</span>
      <span class="num">${Fmt.money(high, { digits: 2 })}</span></div>`;
  }

  /* KIYAS CIZGISI — portfoy degeri (vurgulu) + tek bir kiyas (gri).

     Tek eksen (USD). Iki seri ayni sermayeyle ayni gun basladigi icin ilk
     gunlerde ust uste biner; bu yuzden kiyaslar AYNI ANDA degil, birer
     birer cizilir (secici grafigin ustunde). Kimlik renge birakilmaz:
     lejant her zaman var, uc noktada kisa ad + deger yazar.

     Ipucu (tooltip) yalnizca kolaylik: her deger alttaki tabloda da var.
     Etiketler textContent ile yazilir — seri adlari veriden gelir. */
  function compare(host, cfg) {
    const { dates, focus, context } = cfg;
    const fmt = cfg.fmt || ((v) => String(v));
    const fmtTick = cfg.fmtTick || fmt;
    const fmtDate = cfg.fmtDate || ((d) => d);
    const H = cfg.height || 190;
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

    // Lejant: cizgi anahtari + ad + son deger (deger vurgulu, ad ikincil).
    const legend = make('div', 'cmp-legend');
    series.forEach((s) => {
      const k = make('span', 'cmp-key');
      k.append(make('i', s.role === 'focus' ? 'k-focus' : 'k-context'));
      k.append(make('span', 'muted', s.label));
      const li = lastOf(s.values);
      k.append(make('b', null, li >= 0 ? fmt(s.values[li]) : '—'));
      legend.append(k);
    });
    const plot = make('div', 'cmp-plot');
    const tip = make('div', 'cmp-tip');
    tip.hidden = true;
    host.append(legend, plot);

    let lastW = 0;
    function draw() {
      const W = Math.max(Math.round(plot.clientWidth), 260);
      if (W === lastW) return;
      lastW = W;
      const padL = 46, padR = 10, padT = 14, padB = 22;
      const all = series.flatMap((s) => s.values.filter(isNum));
      let lo = Math.min(...all), hi = Math.max(...all);
      // Duz seride (ilk gunler) eksen 0,5 dolarlik kipirtiyi ucurum gibi
      // gostermesin: aralik en az degerin %1'i.
      const minSpan = Math.max(Math.abs(hi) * 0.01, 1);
      if (hi - lo < minSpan) { const m = (hi + lo) / 2; lo = m - minSpan / 2; hi = m + minSpan / 2; }
      const pad = (hi - lo) * 0.15;
      lo -= pad; hi += pad;
      const step = niceStep((hi - lo) / 3);
      const ticks = [];
      for (let t = Math.ceil(lo / step) * step; t <= hi; t += step) ticks.push(t);

      const x = (i) => padL + (n === 1 ? 0 : i * (W - padL - padR) / (n - 1));
      const y = (v) => padT + (1 - (v - lo) / (hi - lo)) * (H - padT - padB);

      const grid = ticks.map((t) => `<line x1="${padL}" x2="${W - padR}" y1="${y(t).toFixed(1)}"
          y2="${y(t).toFixed(1)}" class="cmp-grid"/>
        <text x="${padL - 6}" y="${(y(t) + 3.5).toFixed(1)}" text-anchor="end"
          class="cmp-tick">${esc(fmtTick(t))}</text>`).join('');

      const path = (vals) => {
        let d = '', pen = false;
        vals.forEach((v, i) => {
          if (!isNum(v)) { pen = false; return; }
          d += `${pen ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`;
          pen = true;
        });
        return d;
      };

      // Arkadaki seri once cizilir; vurgulu seri ustte kalir.
      const lines = [...series].reverse().map((s) => `<path d="${path(s.values)}"
          class="${s.role === 'focus' ? 'cmp-focus' : 'cmp-context'}"/>`).join('');

      // Uc noktalar + kisa ad. Ustteki serinin etiketi yukari, alttakinin
      // asagi — yakinsayan serilerde bile carpismazlar.
      const ends = series.map((s) => ({ s, i: lastOf(s.values) })).filter((e) => e.i >= 0);
      const topKey = ends.length === 2
        ? (ends[0].s.values[ends[0].i] >= ends[1].s.values[ends[1].i] ? 0 : 1) : 0;
      const endMarks = ends.map((e, k) => {
        const cx = x(e.i), cy = y(e.s.values[e.i]);
        const above = k === topKey;
        const ly = Math.max(padT + 2, Math.min(H - padB - 4, above ? cy - 9 : cy + 17));
        return `<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="4"
            class="${e.s.role === 'focus' ? 'cmp-dot-focus' : 'cmp-dot-context'}"/>
          <text x="${(cx - 7).toFixed(1)}" y="${ly.toFixed(1)}" text-anchor="end"
            class="cmp-end">${esc(e.s.short || e.s.label)}</text>`;
      }).join('');

      const xl = `<text x="${padL}" y="${H - 5}" class="cmp-tick">${esc(fmtDate(dates[0]))}</text>
        <text x="${W - padR}" y="${H - 5}" text-anchor="end" class="cmp-tick">${
          esc(fmtDate(dates[n - 1]))}</text>`;

      plot.innerHTML = `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" tabindex="0"
          role="img" aria-label="${esc(cfg.aria || 'Portfoy degeri grafigi')}">
        ${grid}${lines}${endMarks}${xl}
        <g class="cmp-hover" visibility="hidden">
          <line class="cmp-cross" y1="${padT}" y2="${H - padB}"/>
          ${series.map((s) => `<circle r="4" class="${s.role === 'focus'
            ? 'cmp-dot-focus' : 'cmp-dot-context'}"/>`).join('')}
        </g>
        <rect x="${padL}" y="0" width="${W - padL - padR}" height="${H}" fill="transparent"
          class="cmp-hit"/>
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
          row.append(make('b', null, isNum(s.values[cur]) ? fmt(s.values[cur]) : '—'));
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
        const px = ev.clientX - r.left;
        return n === 1 ? 0 : Math.round((px - padL) / ((W - padL - padR) / (n - 1)));
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

  function esc(s) { return Fmt.esc(s); }

  return { sparkline, bars, line, scoreRing, miniBar, ratingBar, targetRange, compare };
})();
