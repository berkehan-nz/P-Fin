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

  return { sparkline, bars, line, scoreRing, miniBar, ratingBar, targetRange };
})();
