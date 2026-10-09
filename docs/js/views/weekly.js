/* CUMA RAPORU — Portföy › Haftalık.
 *
 * Haftada bir, "bu hafta bir şey yapmam gerekiyor mu?". Eylem gerektirmeyen
 * bölümler TEK SATIRA çöker ("✓ Tez kırıcı yok · ✓ Dilimler bantta");
 * yalnızca eylem gerektiren bölüm kart olarak açılır. Bilgi bölümleri
 * (yeni adaylar, kur, tarama, makro) katlanır.
 *
 * Getiri satırı portföy durumundan okunur ki Bugün ve Portföy ile birebir
 * aynı sayı görünsün (weekly.json'daki pnl_pct pozisyon maliyetine göre
 * hesaplanıyor; o başka bir tanım).
 */
window.ViewWeekly = (function () {
  'use strict';
  const F = Fmt;

  function html(w, port) {
    if (!w || !w.as_of) {
      return `<div class="card"><p>Henüz rapor yok. Cuma raporu her cuma günlük koşuda yazılır.</p></div>`;
    }
    const perf = (port && port.performance) || {};
    const breakers = w.triggered_breakers || [];
    const drift = w.slice_drift || [];
    const earnings = w.upcoming_earnings || [];

    const quiet = [
      !breakers.length && '✓ Tez kırıcı yok',
      !drift.length && '✓ Dilimler bantta',
      !earnings.length && 'Bu hafta bilanço yok',
    ].filter(Boolean);

    const n = w.action_required || 0;
    return `
      <div class="h2row"><h2>Hafta · ${F.esc(F.date(w.week_of || w.as_of))}</h2>
        <span class="small muted">rapor ${F.esc(F.date(w.as_of))}</span></div>
      <div class="card">
        <div class="weekly-summary">
          <b>${n ? `${n} madde eylem bekliyor` : 'Eylem gerektiren bir şey yok'}</b>
          ${perf.status === 'aktif' ? `<span>Başlangıçtan <span class="${F.changeClass(perf.return_pct)}">${F.esc(F.signedMoney(perf.return_usd))} · ${F.esc(F.pct(perf.return_pct))}</span></span>` : ''}
        </div>
        ${quiet.length ? `<div class="weekly-summary ok" style="margin-top:6px">${quiet.map((q) => `<span>${F.esc(q)}</span>`).join('')}</div>` : ''}
      </div>
      ${breakers.length ? breakersCard(breakers) : ''}
      ${drift.length ? driftCard(drift) : ''}
      ${earnings.length ? earningsCard(earnings) : ''}
      ${candidatesFold(w.new_candidates || {})}
      ${fxFold(w.fx || {})}
      ${scanFold(w.scan || {})}
      ${macroFold(w.macro || {})}`;
  }

  /* ---------------------------------------------------- eylem bölümleri */
  function breakersCard(rows) {
    const kind = { thesis: 'yapısal', catastrophic_price: 'fiyat çöküşü', take_profit: 'hedef', portfolio_drawdown: 'portföy' };
    return `<h2>Tez kırıcılar</h2><div class="card"><ul class="agenda criteria">${rows.map((b) => `<li>
      <span class="what"><b>${F.esc(b.ticker || '')}</b> ${F.esc(F.tr(b.description || ''))}
        ${b.action ? `<span class="sub">Ne yapmalı: ${F.esc(F.tr(b.action))}</span>` : ''}</span>
      <span>${F.badge(kind[b.kind] || b.kind || '', b.level === 'high' ? 'bad' : 'warn')}</span></li>`).join('')}</ul>
      <p class="small muted" style="margin-top:8px">Fiyat çöküşü otomatik satış değil — zorunlu yeniden değerlendirme.</p></div>`;
  }

  function driftCard(rows) {
    return `<h2>Dilim sapmaları</h2><div class="card"><ul class="agenda criteria">${rows.map((s) => `<li>
      <span class="what">${F.esc(F.sliceLabel(s.slice, s.label))}
        <span class="sub">gerçek ${F.esc(F.share(s.actual_pct))} · hedef ${F.esc(F.share(s.target_pct, 0))}</span></span>
      <span>${F.badge(`${F.num(Math.abs(s.drift_pp), 1)} puan ${s.drift_pp > 0 ? 'fazla' : 'eksik'}`, 'warn')}</span></li>`).join('')}</ul></div>`;
  }

  function earningsCard(rows) {
    return `<h2>7 gün içindeki bilançolar</h2><div class="card"><ul class="agenda compact">${rows.map((e) => `<li>
      <span class="when ${e.days <= 2 ? 'soon' : ''}">${F.esc(F.days(e.days))}</span>
      <span class="what"><a href="#/sirket/${F.esc(e.ticker)}">${F.esc(e.ticker)}</a>${e.in_portfolio ? ' · portföyde' : ''}${e.estimated ? ' · tahmini tarih' : ''}</span>
      <span class="date">${F.esc(F.date(e.date))}</span></li>`).join('')}</ul>
      <p class="small muted" style="margin-top:8px">Bilgi anı, karar anı değil: önce rakam gelir, sonra tez tartılır.</p></div>`;
  }

  /* ---------------------------------------------------- bilgi bölümleri */
  function fold(title, count, body) {
    return `<details class="fold"><summary>${F.esc(title)}<span class="count">${F.esc(count)}</span></summary>
      <div class="fold-body">${body}</div></details>`;
  }

  function candidatesFold(nc) {
    const giren = nc.entered || [];
    const cikan = nc.left || [];
    if (!giren.length && !cikan.length) return '';
    // headline bir metrik sözlüğü; eskiden doğrudan yazılıyordu ve ekranda
    // "[object Object]" görünüyordu. Ad + puan yazılır.
    const g = giren.length ? `<ul class="agenda compact">${giren.map((c) => `<li>
      <span class="when">${F.isNum(c.score) ? F.esc(F.int(c.score)) : ''}</span>
      <span class="what"><a href="#/sirket/${F.esc(c.ticker)}"><b>${F.esc(c.ticker)}</b></a>
        <span class="sub">${F.esc(typeof c.name === 'string' ? c.name : '')}</span></span><span></span></li>`).join('')}</ul>` : '';
    const c = cikan.length ? `<p class="small muted" style="margin-top:8px">Listeden çıkan: ${cikan.map(F.esc).join(', ')}</p>` : '';
    return fold('Huniden yeni gelenler', `${giren.length} giren · ${cikan.length} çıkan`,
      g + c + (nc.first_report ? '<p class="small muted">İlk rapor: mevcut adayların hepsi "yeni" görünüyor.</p>' : ''));
  }

  function fxFold(fx) {
    if (!F.isNum(fx.usdtry) && !(fx.deposits || []).length) return '';
    const dep = (fx.deposits || []).map((d) => {
      const used = F.isNum(d.usdtry_used_pct) ? d.usdtry_used_pct : null;
      const kind = used === null ? '' : used >= 80 ? 'bad' : used >= 50 ? 'warn' : '';
      const usedText = used === null ? ''
        : used <= 0 ? 'Kur giriş kurunun altında; güvenli pay hiç kullanılmadı.'
        : `Güvenli payın ${F.share(used, 0)}'i kullanıldı.`;
      return `<div style="margin-top:10px">
        <div><b>TL mevduat</b> <span class="small muted">vadeye ${F.esc(d.days_to_maturity)} gün</span></div>
        <div class="small">Değer ${F.esc(F.moneyTry(d.value_try))} (${F.esc(F.money(d.value_usd))}) · net faiz ${F.esc(F.moneyTry(d.net_interest_try))}</div>
        <div class="small">Giriş kuru ${F.esc(F.num(d.usdtry_at_entry, 2))} → başa baş ${F.esc(F.num(d.usdtry_breakeven, 2))}</div>
        ${usedText ? `<div class="small">${F.esc(usedText)}</div>
          <div class="meter ${kind}"><i style="width:${Math.max(0, Math.min(100, used))}%"></i></div>` : ''}
      </div>`;
    }).join('');
    return fold('USD/TRY ve TL mevduat', F.isNum(fx.usdtry) ? F.num(fx.usdtry, 2) : '',
      `${F.isNum(fx.usdtry) ? `<div class="small">USD/TRY ${F.esc(F.num(fx.usdtry, 2))}${F.isNum(fx.change_1w_pct)
        ? ` · 1 hafta ${F.esc(F.pct(fx.change_1w_pct))}` : ''}</div>` : ''}${dep}`);
  }

  function scanFold(s) {
    if (!s.total) return '';
    return fold('Evren taraması', `Tur ${s.cycle} · ${F.share(s.pct, 0)}`,
      `<div class="small">${F.esc(F.int(s.done))} / ${F.esc(F.int(s.total))} şirket · sert filtreleri geçen ${F.esc(F.int(s.survivors))}</div>
       <div class="small muted">Elendi ${F.esc(F.int(s.eliminated))} · veri eksik ${F.esc(F.int(s.data_missing))}${s.retry_queue
         ? ` (${F.esc(s.retry_queue)} tanesi sonraki turda yeniden denenecek)` : ''}</div>`);
  }

  function macroFold(m) {
    const names = { us10y: 'ABD 10 yıllık', fed_funds: 'Fed faizi', cpi_yoy: 'ABD TÜFE (yıllık)' };
    const rates = Object.entries(m.key_rates || {}).filter(([, v]) => F.isNum(v))
      .map(([k, v]) => `${F.esc(names[k] || k)} ${F.esc(F.share(v, 2))}`).join(' · ');
    const items = (m.upcoming || []).map((e) => `<li><span class="when">${F.esc(F.days(e.days))}</span>
      <span class="what">${F.esc(F.tr(e.title || e.detail || ''))}</span><span class="date">${F.esc(F.date(e.date))}</span></li>`).join('');
    if (!rates && !items) return '';
    return fold('Makro', `${(m.upcoming || []).length} olay`,
      `${rates ? `<p class="small">${rates}</p>` : ''}${m.risk_note ? `<p class="small muted">${F.esc(F.tr(m.risk_note))}</p>` : ''}
       ${items ? `<ul class="agenda compact">${items}</ul>` : ''}`);
  }

  return { html };
})();
