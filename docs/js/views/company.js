/* 3. SIRKET DETAYI — tek uzun sayfa, solda yapiskan icindekiler.
 *
 * Bolumler: baslik · puan seridi · ne yapar/hendek (Claude) · metrik tablosu
 * (4 blok) · 12 ceyreklik grafikler · ters DCF + g kaydirici · tez bolumleri
 * (Claude) · analist konsensusu · haberler · karar kutusu · veri kaynaklari.
 */
window.ViewCompany = (function () {
  'use strict';

  const SECTIONS = [
    ['ozet', 'Ozet'],
    ['ne-yapar', 'Ne yapar'],
    ['metrikler', 'Metrikler'],
    ['grafikler', 'Grafikler'],
    ['dcf', 'Ters DCF'],
    ['tez', 'Tez'],
    ['analist', 'Analist'],
    ['haber', 'Haberler'],
    ['karar', 'Karar'],
    ['kaynak', 'Kaynaklar'],
  ];

  let card = null;

  async function render(ticker) {
    const body = document.getElementById('companyBody');
    body.innerHTML = '<p class="muted">Yukleniyor…</p>';

    card = await DataLayer.card(ticker);
    if (!card) {
      body.innerHTML = `<div class="empty-state">
        <h2>${Fmt.esc(ticker)} karti bulunamadi</h2>
        <p>Bu sembol icin <code>data/cards/${Fmt.esc(ticker)}.json</code> yok.
           Izleme listesine ekleyip veri hattini calistirman gerekiyor.</p>
        <p><a href="#/candidates">← Adaylara don</a></p></div>`;
      return;
    }

    body.innerHTML = `<div class="detail-layout">
      <nav class="toc" id="toc">${SECTIONS.map(([id, label]) =>
        `<a href="#${id}" data-sec="${id}">${Fmt.esc(label)}</a>`).join('')}</nav>
      <div>
        ${headSection()}
        ${storySection()}
        ${metricsSection()}
        ${chartsSection()}
        ${dcfSection()}
        ${thesisSection()}
        ${analystSection()}
        ${newsSection()}
        ${decisionSection()}
        ${sourcesSection()}
      </div></div>`;

    wire();
  }

  /* ------------------------------------------------------------- baslik */
  function headSection() {
    const s = card.scores || {};
    const warnings = (card.flags || {}).warnings || [];
    const chg = card.change_1d_pct;

    return `<section id="ozet">
      <div class="detail-head">
        <div>
          <h1 style="margin-bottom:2px">${Fmt.esc(card.ticker)}
            ${Fmt.trackBadge(card.track)}
            ${(card.flags || {}).is_manual ? '<span class="chip gray">elle eklendi</span>' : ''}
            ${card.source === 'seed_20260909' ? '<span class="chip gray">tohum listesi</span>' : ''}
          </h1>
          <div class="muted">${Fmt.esc(card.name)} · ${Fmt.esc(card.exchange)} ·
            ${Fmt.esc(card.sector)} <span class="tiny dim">(SIC ${Fmt.esc(card.sic)})</span></div>
        </div>
        <div>
          <div class="price">${Fmt.money(card.price, { digits: 2 })}
            ${Fmt.isNum(chg) ? `<span class="${Fmt.pnlClass(chg)}" style="font-size:15px">
              ${Fmt.signedPct(chg)}</span>` : ''}</div>
        </div>
        ${Charts.scoreRing(s.total, { size: 62 })}
      </div>

      <div class="grid g-summary" style="margin:14px 0">
        ${stat('Piyasa degeri', Fmt.money(card.market_cap_musd, { musd: true }))}
        ${stat('Isletme degeri (EV)', Fmt.money(card.enterprise_value_musd, { musd: true }),
               'Kiralama yukumlulukleri haric')}
        ${stat('Net borc', Fmt.money(card.net_debt_musd, { musd: true }),
               Fmt.isNum(card.net_debt_musd) && card.net_debt_musd < 0 ? 'net nakit' : '')}
        ${stat('Sonraki kazanc', Fmt.date((card.calendar || {}).next_earnings))}
      </div>

      <h3>Puan dagilimi</h3>
      <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(110px,1fr))">
        ${[['value', 'Ucuzluk', 25], ['quality', 'Kalite', 20], ['safety', 'Saglamlik', 15],
           ['momentum', 'Momentum', 15], ['earnings_quality', 'Kazanc kalitesi', 10],
           ['catalyst', 'Katalizor', 15]].map(([k, label, w]) => `
          <div class="card" style="padding:9px">
            <div class="tiny dim">${label} <span class="dim">·${w}</span></div>
            <div class="num" style="font-size:17px;font-weight:600;margin:3px 0">
              ${Fmt.isNum(s[k]) ? Math.round(s[k]) : '—'}</div>
            ${Charts.miniBar(s[k])}
            ${k === 'catalyst' && !Fmt.isNum(s[k])
              ? '<div class="tiny dim" style="margin-top:4px">elle girilir</div>' : ''}
          </div>`).join('')}
      </div>
      ${Fmt.isNum(s.weight_coverage) && s.weight_coverage < 1 ? `
        <p class="tiny dim" style="margin-top:6px">Puanin %${Math.round(s.weight_coverage * 100)}'i
        hesaplanabildi; eksik bilesenler agirlik havuzundan cikarildi.</p>` : ''}

      ${dataQualityBlock()}

      ${warnings.length ? `<h3>Uyarilar</h3>${warnings.map((w) =>
        `<div class="warn ${w.startsWith('VERI KALITESI') ? 'high' : 'medium'}">
          <span>${w.startsWith('VERI KALITESI') ? '⛔' : '⚠'}</span>
          <span>${Fmt.esc(w)}</span></div>`).join('')}` : ''}

      ${funnelStatus()}

      <div class="row" style="margin-top:12px">
        <button id="askClaude" class="primary">Claude'a sor</button>
        <a href="${DataLayer.cardRawUrl(card.ticker)}" target="_blank" rel="noopener">
          <button class="ghost">Ham JSON</button></a>
        <a href="#/candidates"><button class="ghost">← Adaylar</button></a>
      </div>
    </section>`;
  }

  /* Veri kalitesi — sessizce yanlis sayi gostermektense acikca soyle. */
  function dataQualityBlock() {
    const dq = card.data_quality;
    if (!dq || dq.status === 'iyi') return '';
    const label = dq.status === 'kotu'
      ? ['red', 'Bu kartin sayilarina guvenme']
      : ['yellow', 'Bazi alanlar eksik'];
    return `<h3>Veri kalitesi</h3>
      <div class="warn ${dq.status === 'kotu' ? 'high' : 'medium'}">
        <span>${dq.status === 'kotu' ? '⛔' : '⚠'}</span>
        <span><b>${Fmt.esc(label[1])}.</b> ${dq.issue_count} sorun bulundu:
          <ul style="margin:6px 0 0;padding-left:18px">
            ${(dq.issues || []).map((i) =>
              `<li>${Fmt.esc(i.message)}</li>`).join('')}
          </ul>
          <span class="tiny dim">Bu denetim kart yayimlanmadan once calisir;
            imkansiz degerler silinir, supheli olanlar burada listelenir.</span>
        </span></div>`;
  }

  function funnelStatus() {
    const f = card.flags || {};
    const passed = f.passed_stages || [];
    if (!passed.length && f.would_fail_at === null && !f.kill_reason) return '';
    const stageName = ['Evren', 'Sert filtreler', 'Tuzak eleme', 'Goreli ucuzluk', 'Puanlama'];
    const chips = stageName.map((n, i) => {
      const ok = passed.includes(i);
      const failed = f.would_fail_at === i;
      return `<span class="chip ${ok ? 'green' : failed ? 'red' : 'gray'}">
        ${i}. ${Fmt.esc(n)}</span>`;
    }).join(' ');
    return `<h3>Huni durumu</h3><div class="row" style="gap:5px">${chips}</div>
      ${f.kill_reason ? `<p class="small muted" style="margin-top:6px">
        <b>Elenme sebebi:</b> ${Fmt.esc(f.kill_reason)}</p>` : ''}
      ${f.would_fail_at === null && passed.length >= 3
        ? '<p class="small c-green" style="margin-top:6px">Huninin tum asamalarini geciyor.</p>' : ''}
      ${(f.stage1_missing || []).length ? `<p class="small c-yellow" style="margin-top:6px">
        <b>Not:</b> Asama 1'de su girdiler hesaplanamadi:
        ${Fmt.esc(f.stage1_missing.map((k) => Fmt.label(k)).join(', '))}.
        Eksik veri eleme sebebi SAYILMAZ — etiketleme bicimine gore eleme
        yapmak gorunmez bir yanlilik yaratirdi. Bu alanlari dogrulamadan
        sirketi degerlendirme.</p>` : ''}`;
  }

  function stat(label, value, sub) {
    return `<div class="card stat"><div class="label">${Fmt.esc(label)}</div>
      <div class="value" style="font-size:19px">${value}</div>
      ${sub ? `<div class="sub">${Fmt.esc(sub)}</div>` : ''}</div>`;
  }

  /* ------------------------------------------------ ne yapar / hendek */
  function storySection() {
    const st = card.story || {};
    return `<section id="ne-yapar"><h2>Ne yapar ve hendegi ne</h2>
      ${st.business_model || st.moat ? `
        <div class="card">
          ${st.business_model ? `<h3 style="margin-top:0">Is modeli</h3>
            <p>${Fmt.esc(st.business_model)}</p>` : ''}
          ${st.moat ? `<h3>Hendek</h3><p>${Fmt.esc(st.moat)}</p>` : ''}
          ${storyStamp()}
        </div>`
        : emptyStory('Is modeli ve hendek analizi henuz yazilmadi.')}
    </section>`;
  }

  function storyStamp() {
    const st = card.story || {};
    if (!st.updated_at) return '';
    const stale = Fmt.isNum(card.story_age_days) && card.story_age_days > 30;
    return `<div class="tiny ${stale ? 'dim' : 'muted'}" style="margin-top:8px">
      <span class="chip ${stale ? 'gray' : 'accent'}">Claude notu</span>
      ${Fmt.date(st.updated_at)}${stale ? ` · ${card.story_age_days} gun once, tazelenmeli` : ''}</div>`;
  }

  function emptyStory(msg) {
    return `<div class="empty-story">${Fmt.esc(msg)}<br>
      <span class="tiny">Sohbetteki Claude <code>claude_inbox/${Fmt.esc(card.ticker)}.json</code>
      dosyasina yazdiginda burada gorunur.</span></div>`;
  }

  /* ------------------------------------------------------- metrik tablo */
  function metricsSection() {
    const blocks = (App.thresholds.metric_blocks) || {};
    const order = ['Degerleme', 'Buyume', 'Kalite', 'Saglamlik ve Tuzak'];
    return `<section id="metrikler"><h2>Metrikler</h2>
      ${order.filter((b) => blocks[b]).map((block) => `
        <h3>${Fmt.esc(block)}</h3>
        <div class="table-wrap"><table>
          <thead><tr><th>Metrik</th><th>Deger</th><th>Sektor %</th>
            <th>Kendi 5y %</th></tr></thead>
          <tbody>${blocks[block].map((key) => metricRow(key)).join('')}</tbody>
        </table></div>`).join('')}
      <p class="tiny dim">* isaretli yuzdelikler sektorde yeterli sirket olmadigi
        icin tum evrene gore hesaplandi.</p>
    </section>`;
  }

  function metricRow(key) {
    const cell = (card.metrics || {})[key] || {};
    const spec = Fmt.spec(key) || {};
    return `<tr data-metric="${Fmt.esc(key)}">
      <td>${Fmt.esc(spec.label || key)}
        <button class="help-btn" data-help="${Fmt.esc(key)}"
                aria-label="${Fmt.esc(spec.label || key)} aciklamasi">?</button></td>
      <td>${Fmt.cell(key, cell)}</td>
      <td>${Fmt.percentileBar(cell.sector_pct, cell.pct_basis)}</td>
      <td>${Fmt.percentileBar(cell.own_5y_pct, 'own')}</td>
    </tr>`;
  }

  /* --------------------------------------------------------- grafikler */
  function chartsSection() {
    const s = card.series || {};
    const labels = s.quarters || [];
    const basis = s.basis === 'annual' ? 'yillik' : 'ceyreklik';
    return `<section id="grafikler"><h2>Son 12 ${basis} donem</h2>
      <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(280px,1fr))">
        <div class="card">${Charts.bars(s.revenue, labels,
          { title: 'Hasilat (M$)', fmt: (v) => Fmt.money(v, { musd: true }) })}</div>
        <div class="card">${Charts.line(s.gross_margin, labels,
          { title: 'Brut marj', fmt: (v) => Fmt.pct(v), color: 'var(--green)' })}</div>
        <div class="card">${Charts.bars(s.fcf, labels,
          { title: 'Serbest nakit akisi (M$)', fmt: (v) => Fmt.money(v, { musd: true }) })}</div>
        <div class="card">${Charts.line(s.share_count, labels,
          { title: 'Seyreltilmis hisse sayisi (M)', fmt: (v) => Fmt.num(v, 1),
            color: 'var(--yellow)' })}</div>
      </div></section>`;
  }

  /* ---------------------------------------------------------- ters DCF */
  function dcfSection() {
    const d = card.reverse_dcf || {};
    const implied = d.implied_growth_pct;
    const actual = d.actual_growth_pct;

    if (!Fmt.isNum(d.fcf_ttm_musd) || d.fcf_ttm_musd <= 0) {
      return `<section id="dcf"><h2>Ters DCF</h2>
        <div class="card muted small">Serbest nakit akisi pozitif olmadigi icin
          ters DCF anlamsiz. Kol B sirketlerinde EV/Brut kar ve EV/Hasilat
          carpanlarina bak.</div></section>`;
    }

    // Sirket kuculuyorsa (actual <= 0) ima edilen/gerceklesen orani anlamsizdir:
    // negatif tabana bolmek her ima edilen buyumeyi "cok yuksek" gosterir.
    // Bu durumda ima edilen buyume MUTLAK olarak degerlendirilir.
    let verdict = ['gray', ''];
    if (Fmt.isNum(implied) && Fmt.isNum(actual) && actual > 0) {
      verdict = implied > actual * 1.5
        ? ['red', 'Fiyat, sirketin gerceklesen buyumesinin cok uzerini varsayiyor.']
        : implied > actual
        ? ['yellow', 'Fiyat, gerceklesen buyumenin biraz uzerini varsayiyor.']
        : ['green', 'Fiyat, sirketin mevcut buyumesini bile tam fiyatlamamis.'];
    } else if (Fmt.isNum(implied) && Fmt.isNum(actual) && actual <= 0) {
      verdict = implied <= 0
        ? ['green', 'Sirket kuculuyor ve fiyat da dususu varsayiyor — oran degil, '
            + 'nakit akisinin kaliciligina bak.']
        : ['yellow', 'Sirket kuculuyor ama fiyat buyume varsayiyor. Oran anlamsiz '
            + '(negatif taban); ima edilen buyumeyi mutlak olarak degerlendir.'];
    }

    return `<section id="dcf"><h2>Ters DCF</h2>
      <div class="card">
        <p style="font-size:15px;margin-top:0">Bu fiyat
          <b class="c-${verdict[0]}">%${Fmt.num(implied, 1)}</b> yillik FCF buyumesi varsayiyor;
          sirket son 3 yilda <b>%${Fmt.num(actual, 1)}</b>
          ${Fmt.isNum(actual) && actual < 0 ? 'KUCULDU' : 'buyudu'}.</p>
        ${verdict[1] ? `<p class="small c-${verdict[0]}">${Fmt.esc(verdict[1])}</p>` : ''}

        <div class="kv" style="margin:12px 0">
          <dt>TTM serbest nakit akisi</dt><dd>${Fmt.money(d.fcf_ttm_musd, { musd: true })}</dd>
          <dt>Isletme degeri</dt><dd>${Fmt.money(d.enterprise_value_musd, { musd: true })}</dd>
          <dt>Iskonto orani</dt><dd>%${Fmt.num((d.discount_rate || 0) * 100, 0)}</dd>
          <dt>Terminal buyume</dt><dd>%${Fmt.num((d.terminal_growth || 0) * 100, 0)}</dd>
          <dt>Projeksiyon</dt><dd>${d.projection_years || 10} yil</dd>
        </div>

        <h3>Kendi varsayiminla dene</h3>
        <div class="row">
          <input type="range" id="gSlider" min="-20" max="60" step="1"
                 value="${Fmt.isNum(actual) ? Math.round(actual) : 10}" style="flex:1;min-width:180px">
          <span class="num" id="gLabel" style="min-width:56px"></span>
        </div>
        <p class="small" id="gResult" style="margin-top:8px"></p>
        <p class="tiny dim">Kaydirici yalnizca gorsel bir hesap yapar; kartta
          saklanan degerleri degistirmez.</p>
      </div></section>`;
  }

  /* -------------------------------------------------------------- tez */
  function thesisSection() {
    const st = card.story || {};
    const has = st.why_cheap_diagnosis || (st.bull_case || []).length ||
                (st.bear_case || []).length || (st.catalyst || {}).type ||
                (st.thesis_breakers || []).length;
    if (!has) {
      return `<section id="tez"><h2>Tez</h2>
        ${emptyStory('Neden ucuz, boga/ayi tezi, katalizor ve tez kiricilar henuz yazilmadi.')}
      </section>`;
    }
    const cat = st.catalyst || {};
    return `<section id="tez"><h2>Tez</h2>
      ${st.why_cheap_diagnosis ? `<div class="card" style="margin-bottom:12px">
        <h3 style="margin-top:0">Neden ucuz</h3>
        <p><span class="chip accent">${Fmt.esc(st.why_cheap_diagnosis)}</span></p>
        ${st.why_cheap_rationale ? `<p>${Fmt.esc(st.why_cheap_rationale)}</p>` : ''}
      </div>` : ''}
      <div class="thesis">
        <div class="card"><h3 style="margin-top:0" class="c-green">Boga tezi</h3>
          ${(st.bull_case || []).length
            ? `<ul>${st.bull_case.map((x) => `<li>${Fmt.esc(x)}</li>`).join('')}</ul>`
            : '<p class="dim small">yazilmadi</p>'}</div>
        <div class="card"><h3 style="margin-top:0" class="c-red">Ayi tezi</h3>
          ${(st.bear_case || []).length
            ? `<ul>${st.bear_case.map((x) => `<li>${Fmt.esc(x)}</li>`).join('')}</ul>`
            : '<p class="dim small">yazilmadi</p>'}</div>
      </div>
      ${cat.type ? `<div class="card" style="margin-top:12px">
        <h3 style="margin-top:0">Katalizor</h3>
        <p><b>${Fmt.esc(cat.type)}</b>
          ${cat.expected_date ? ` · beklenen: ${Fmt.esc(cat.expected_date)}` : ''}
          ${cat.confidence ? ` · guven: ${Fmt.esc(cat.confidence)}` : ''}</p></div>` : ''}
      ${(st.thesis_breakers || []).length ? `<div class="card" style="margin-top:12px">
        <h3 style="margin-top:0">Tezi ne bozar</h3>
        <ul>${st.thesis_breakers.map((x) =>
          `<li>${Fmt.esc(typeof x === 'string' ? x : x.description || '')}</li>`).join('')}</ul>
      </div>` : ''}
      ${storyStamp()}
    </section>`;
  }

  /* --------------------------------------------------------- analist */
  function analystSection() {
    const a = card.analyst || {};
    return `<section id="analist"><h2>Analist konsensusu</h2>
      <div class="card">
        <p class="tiny dim" style="margin-top:0">Bu bir BILGI alanidir, karar alani degil.
          Hedef fiyatlar sistematik olarak iyimserdir ve puanlamaya girmez.</p>
        ${Charts.ratingBar(a.buy, a.hold, a.sell)}
        ${Charts.targetRange(a.target_low, a.target_median, a.target_high, card.price)}
        ${Fmt.isNum(a.upside_to_median) ? `<p class="small">Medyan hedefe potansiyel:
          <b class="${Fmt.pnlClass(a.upside_to_median)}">${Fmt.signedPct(a.upside_to_median)}</b></p>` : ''}
        ${(card.story || {}).analyst_narrative
          ? `<p class="small">${Fmt.esc(card.story.analyst_narrative)}</p>` : ''}
      </div>
      ${shortInterest()}
    </section>`;
  }

  function shortInterest() {
    const si = card.short_interest || {};
    const ins = card.insider || {};
    if (!Fmt.isNum(si.short_interest) && !Fmt.isNum(ins.form4_count)) return '';
    return `<div class="card" style="margin-top:12px">
      <h3 style="margin-top:0">Diger sinyaller</h3>
      <div class="kv">
        ${Fmt.isNum(si.short_interest) ? `<dt>Kisa pozisyon</dt>
          <dd>${Fmt.num(si.short_interest / 1e6, 2)}M hisse
          ${Fmt.isNum(si.days_to_cover) ? ` · ${Fmt.num(si.days_to_cover, 1)} gunluk hacim` : ''}</dd>` : ''}
        ${Fmt.isNum(ins.form4_count) ? `<dt>Form 4 (${ins.window_days} gun)</dt>
          <dd>${ins.form4_count} dosyalama${ins.last_form4 ? ` · son ${Fmt.date(ins.last_form4)}` : ''}</dd>` : ''}
      </div>
      <p class="tiny dim">Form 4 sayisi tutar degil dosyalama adedidir; yon
        bilgisi tasimaz. Baglam icin, karar icin degil.</p></div>`;
  }

  /* --------------------------------------------------------- haberler */
  function newsSection() {
    const news = card.news || [];
    const summary = (card.story || {}).news_summary;
    return `<section id="haber"><h2>Haberler</h2>
      ${summary ? `<div class="card" style="margin-bottom:12px">
        <h3 style="margin-top:0">Claude'un haber ozeti</h3>
        <p>${Fmt.esc(summary)}</p>${storyStamp()}</div>` : ''}
      ${news.length ? `<div class="card">${news.map((n) => `
        <div style="padding:7px 0;border-bottom:1px solid var(--line-soft)">
          <a href="${Fmt.esc(n.url)}" target="_blank" rel="noopener">${Fmt.esc(n.headline)}</a>
          <div class="tiny dim">${Fmt.esc(n.source)} · ${Fmt.date(n.date)}</div>
        </div>`).join('')}</div>`
        : `<div class="card muted small">Haber yok. Finnhub anahtari tanimli
           degilse haber cekilmez.</div>`}
    </section>`;
  }

  /* ----------------------------------------------------------- karar */
  function decisionSection() {
    const d = card.decision || {};
    return `<section id="karar"><h2>Karar</h2>
      <div class="card">
        ${d.action ? `<p>Mevcut karar: ${Fmt.decisionBadge(d.action)}
          <span class="tiny dim">${Fmt.date(d.date)}</span></p>
          ${d.rationale ? `<p class="small">${Fmt.esc(d.rationale)}</p>` : ''}
          <hr style="border:none;border-top:1px solid var(--line-soft);margin:12px 0">` : ''}
        <p class="muted small" style="margin-top:0">Dashboard dosyaya yazamaz.
          Karari kaydetmek icin asagidaki JSON parcasini
          <code>claude_inbox/${Fmt.esc(card.ticker)}.json</code> dosyasina ekle
          (Claude Code'a yapistir ya da GitHub'da ac).</p>
        <div class="form-grid">
          <label>Karar<select id="dcAction">
            <option value="">— sec —</option><option>AL</option>
            <option>BEKLE</option><option>ELE</option></select></label>
          <label>Tarih<input type="date" id="dcDate"
            value="${new Date().toISOString().slice(0, 10)}"></label>
          <label class="full">Gerekce<textarea id="dcWhy" rows="3"
            placeholder="Neden bu karar?"></textarea></label>
          <label class="full">JSON parcasi<textarea id="dcOut" rows="9" readonly></textarea></label>
        </div>
        <div class="row" style="margin-top:10px">
          <button id="dcCopy" class="primary">Kopyala</button>
          <a href="${DataLayer.editUrl(`claude_inbox/${card.ticker}.json`)}"
             target="_blank" rel="noopener"><button>GitHub'da ac</button></a>
        </div>
      </div></section>`;
  }

  /* ------------------------------------------------------- kaynaklar */
  function sourcesSection() {
    const ds = card.data_sources || {};
    const internals = card.score_internals || {};
    const p = internals.piotroski || {};
    const testNames = {
      roa_positive: 'ROA > 0', cfo_positive: 'CFO > 0',
      roa_improving: 'ROA artiyor', accruals: 'CFO > net kar',
      leverage_down: 'Borc/varlik dusuyor', liquidity_up: 'Cari oran artiyor',
      no_dilution: 'Seyrelme yok', margin_up: 'Brut marj artiyor',
      turnover_up: 'Varlik devir hizi artiyor',
    };

    return `<section id="kaynak"><h2>Veri kaynagi ve hesap detayi</h2>
      <div class="card">
        <div class="kv">
          <dt>Temel veri</dt><dd>${Fmt.esc(ds.fundamentals || '—')}</dd>
          <dt>Fiyat</dt><dd>${Fmt.esc(ds.price || '—')}</dd>
          <dt>Haber</dt><dd>${Fmt.esc(ds.news || '—')}</dd>
          <dt>Analist</dt><dd>${Fmt.esc(ds.analyst || '—')}</dd>
          <dt>Son mali donem</dt><dd>${Fmt.esc(ds.period_end || '—')}</dd>
          <dt>Hesap tabani</dt><dd>${(card.flags || {}).data_basis === 'annual'
            ? 'yillik tablo (ceyreklik veri yetersiz)' : 'ceyreklik TTM'}</dd>
          <dt>ROIC yontemi</dt><dd>${(card.flags || {}).roic_method === 'b'
            ? '(b) net isletme varliklari — ozkaynak negatif'
            : '(a) ozkaynak + borc - nakit'}</dd>
          <dt>Kart tarihi</dt><dd>${Fmt.esc(card.as_of)}</dd>
        </div>

        ${p.tests ? `<h3>Piotroski F alt testleri (${p.score ?? '—'}/${p.max_possible ?? 9})</h3>
          <div class="row" style="gap:5px">${Object.entries(p.tests).map(([k, v]) =>
            `<span class="chip ${v === true ? 'green' : v === false ? 'red' : 'gray'}">
              ${Fmt.esc(testNames[k] || k)}</span>`).join('')}</div>` : ''}

        ${internals.altman && internals.altman.unreliable ? `
          <div class="warn medium" style="margin-top:12px"><span>⚠</span><span>
            Altman Z'' guvenilmez: ${Fmt.esc(internals.altman.reason || '')}.
            ${internals.solvency_fallback ? `Yerine faiz karsilama
              <b>${Fmt.num(internals.solvency_fallback.interest_coverage, 1)}x</b> ve
              FCF/toplam borc
              <b>${Fmt.num(internals.solvency_fallback.fcf_to_total_debt, 2)}</b>.` : ''}
          </span></div>` : ''}

        ${(internals.beneish || {}).missing && internals.beneish.missing.length ? `
          <p class="tiny dim" style="margin-top:10px">Beneish M hesaplanamadi;
            eksik bilesenler: ${Fmt.esc(internals.beneish.missing.join(', '))}</p>` : ''}
      </div></section>`;
  }

  /* -------------------------------------------------------------- olay */
  function wire() {
    // icindekiler vurgusu
    const links = [...document.querySelectorAll('#toc a')];
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        links.forEach((l) => l.classList.toggle('active', l.dataset.sec === e.target.id));
      });
    }, { rootMargin: '-70px 0px -70% 0px' });
    SECTIONS.forEach(([id]) => {
      const el = document.getElementById(id);
      if (el) obs.observe(el);
    });

    // "?" ikonlari — tanim + formul + tuzak aciklamasi
    document.querySelectorAll('.help-btn').forEach((btn) => {
      btn.addEventListener('click', (ev) => {
        ev.stopPropagation();
        const key = btn.dataset.help;
        const row = btn.closest('tr');
        const next = row.nextElementSibling;
        if (next && next.classList.contains('help-row')) { next.remove(); return; }
        const spec = Fmt.spec(key) || {};
        const tr = document.createElement('tr');
        tr.className = 'help-row';
        tr.innerHTML = `<td colspan="4">${Fmt.esc(spec.help || 'Aciklama yok.')}
          ${spec.formula ? `<br><span class="formula">${Fmt.esc(spec.formula)}</span>` : ''}
          ${spec.direction ? `<br><span class="tiny dim">Esikler:
            ${spec.direction === 'low_good'
              ? `yesil ≤ ${spec.green_max} · sari ≤ ${spec.yellow_max} · ustu kirmizi`
              : `yesil ≥ ${spec.green_min} · sari ≥ ${spec.yellow_min} · alti kirmizi`}
          </span>` : ''}</td>`;
        row.after(tr);
      });
    });

    // ters DCF kaydirici
    const slider = document.getElementById('gSlider');
    if (slider) {
      const d = card.reverse_dcf || {};
      const update = () => {
        const g = parseFloat(slider.value) / 100;
        const value = dcfValue(d.fcf_ttm_musd, g, d.discount_rate || 0.10,
                               d.terminal_growth || 0.03, d.projection_years || 10);
        const ev = d.enterprise_value_musd;
        const diff = Fmt.isNum(ev) && ev > 0 ? (value / ev - 1) * 100 : null;
        document.getElementById('gLabel').textContent = `%${slider.value}`;
        document.getElementById('gResult').innerHTML =
          `%${slider.value} buyume ile hesaplanan isletme degeri
           <b class="num">${Fmt.money(value, { musd: true })}</b> —
           bugunku EV'ye gore
           <b class="${Fmt.pnlClass(diff)}">${Fmt.signedPct(diff)}</b>`;
      };
      slider.addEventListener('input', update);
      update();
    }

    // karar formu
    const out = document.getElementById('dcOut');
    if (out) {
      const upd = () => {
        out.value = JSON.stringify({
          ticker: card.ticker,
          decision: {
            action: document.getElementById('dcAction').value,
            date: document.getElementById('dcDate').value,
            rationale: document.getElementById('dcWhy').value.trim(),
            author: 'berke',
          },
        }, null, 2);
      };
      ['dcAction', 'dcDate', 'dcWhy'].forEach((id) =>
        document.getElementById(id).addEventListener('input', upd));
      upd();
      document.getElementById('dcCopy').addEventListener('click', () =>
        App.copy(out.value, 'Karar JSON parcasi kopyalandi'));
    }

    // "Claude'a sor"
    document.getElementById('askClaude').addEventListener('click', () => {
      const m = card.metrics || {};
      const pick = (k) => (m[k] || {}).value;
      const summary = {
        ticker: card.ticker, name: card.name, sector: card.sector,
        track: card.track, price: card.price,
        market_cap_musd: card.market_cap_musd,
        enterprise_value_musd: card.enterprise_value_musd,
        scores: card.scores,
        key_metrics: {
          ev_ebit: pick('ev_ebit'), ev_sales: pick('ev_sales'),
          ev_gross_profit: pick('ev_gross_profit'),
          fcf_yield_ev: pick('fcf_yield_ev'), roic: pick('roic'),
          rev_growth_ttm: pick('rev_growth_ttm'), gross_margin: pick('gross_margin'),
          rule_of_40: pick('rule_of_40'), piotroski_f: pick('piotroski_f'),
          altman_z: pick('altman_z'), beneish_m: pick('beneish_m'),
          implied_growth: pick('implied_growth'), sbc_to_fcf: pick('sbc_to_fcf'),
        },
        flags: card.flags,
        reverse_dcf: card.reverse_dcf,
        as_of: card.as_of,
      };
      const text =
`${card.ticker} (${card.name}) analizi icin ozet veri asagida.
Tam kart: ${DataLayer.cardRawUrl(card.ticker)}

Lutfen su alanlari doldurup claude_inbox/${card.ticker}.json olarak yaz:
business_model, moat, why_cheap_diagnosis, why_cheap_rationale,
bull_case[], bear_case[], catalyst{type,expected_date,confidence},
thesis_breakers[], news_summary, claude_verdict

\`\`\`json
${JSON.stringify(summary, null, 2)}
\`\`\``;
      App.copy(text, 'Ozet + raw link panoya kopyalandi');
    });
  }

  /* Ters DCF degerleme — scores.py'deki dcf_value ile AYNI formul. */
  function dcfValue(fcf0, growth, r, terminalG, years) {
    if (!Fmt.isNum(fcf0) || fcf0 <= 0) return NaN;
    let pv = 0, fcf = fcf0;
    for (let t = 1; t <= years; t++) {
      fcf = fcf * (1 + growth);
      pv += fcf / Math.pow(1 + r, t);
    }
    const terminal = (fcf * (1 + terminalG)) / (r - terminalG);
    return pv + terminal / Math.pow(1 + r, years);
  }

  return { render };
})();
