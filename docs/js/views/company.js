/* ŞİRKET — sabit başlık + dört sekme.
 *
 *   Özet         6 anahtar metrik, Claude'un kararı, tez kırıcılar,
 *                katalizör, sonraki bilanço, puan dağılımı, huni şeridi
 *   Tez ve Karar iş modeli, hendek, boğa/ayı, analist, karar formu
 *   Metrikler    gruplu tablo; grafikler, ters DCF ve kaynaklar katlanır
 *   Haberler
 *
 * Eskiden 7.000 px'lik tek sayfaydı ve boş hücreler için aynı açıklama
 * kırk kez tekrarlanıyordu. Hesaplanamayan metrikler artık satır olarak
 * çizilmez; blok sonunda tek satırda adları geçer. İç hesap ayrıntıları
 * (ağırlık, kapsama, yüzdelik havuzu) üzerine gelince görünür.
 */
window.ViewCompany = (function () {
  'use strict';
  const F = Fmt;
  const TABS = [['ozet', 'Özet'], ['tez', 'Tez ve Karar'], ['metrikler', 'Metrikler'], ['haberler', 'Haberler']];
  const KEY_METRICS = [
    ['ev_ebitda', 'EV/FAVÖK'], ['fcf_yield_ev', 'FCF verimi'], ['roic', 'ROIC'],
    ['rev_cagr_3y', 'Büyüme (3 yıl)'], ['gross_margin', 'Brüt marj'], ['net_debt_to_ebitda', 'Net borç/FAVÖK'],
  ];
  const BLOCK = {
    Degerleme: ['Değerleme', 'Şirket kaç paraya satılıyor ve bu fiyat ucuz mu?'],
    Buyume: ['Büyüme', 'İş büyüyor mu, ne kadar kârlı büyüyor?'],
    Kalite: ['Kalite', 'İşin kendisi iyi mi? Kâr gerçek mi, sermaye verimli mi kullanılıyor?'],
    'Saglamlik ve Tuzak': ['Sağlamlık ve tuzak', 'Bilanço dayanıklı mı? Muhasebede oynama işareti var mı?'],
  };

  let card = null;
  let tab = 'ozet';

  async function render(ticker) {
    const body = document.getElementById('companyBody');
    body.innerHTML = '<p class="muted">Yükleniyor…</p>';
    card = await DataLayer.card(ticker);
    tab = 'ozet';
    if (!card) {
      body.innerHTML = `<div class="empty-state"><h2>${F.esc(ticker)} için kart yok</h2>
        <p>Bu sembol henüz izleme listesinde ya da aday havuzunda değil.</p>
        <p><a href="#/adaylar">← Adaylar</a></p></div>`;
      return;
    }
    body.innerHTML = `${header()}<div id="coTab"></div>
      <div class="co-foot"><a href="#/adaylar">← Adaylar</a> · kart ${F.esc(F.date(card.as_of))} ·
        <a href="${DataLayer.cardRawUrl(card.ticker)}" target="_blank" rel="noopener">ham JSON</a></div>`;
    body.querySelectorAll('[data-tab]').forEach((b) => b.addEventListener('click', () => show(b.dataset.tab)));
    document.getElementById('askClaude').addEventListener('click', askClaude);
    show('ozet');
  }

  function show(t) {
    tab = t;
    document.querySelectorAll('#companyBody [data-tab]').forEach((b) =>
      b.setAttribute('aria-selected', String(b.dataset.tab === t)));
    const el = document.getElementById('coTab');
    el.innerHTML = { ozet: summary, tez: thesis, metrikler: metrics, haberler: news }[t]();
    wireTab();
  }

  /* ------------------------------------------------------------ başlık */
  function header() {
    const chg = card.change_1d_pct;
    const d = (card.decision || {}).action;
    return `<div class="co-header">
      <div class="line">
        <div class="name"><h1>${F.esc(card.ticker)}</h1>
          <div class="sub">${F.esc(card.name || '')} · ${F.esc(F.tr(card.sector || ''))}</div></div>
        <div><div class="price">${F.esc(F.money(card.price))}</div>
          <div class="small ${F.changeClass(chg)}">${F.esc(F.pct(chg))}${card.price_as_of ? ` <span class="dim">· ${F.esc(F.date(card.price_as_of))}</span>` : ''}</div></div>
        ${Charts.scoreRing((card.scores || {}).total)}
        ${d ? F.decisionBadge(d) : '<span class="pending">karar bekliyor</span>'}
        <button id="askClaude" class="primary">Claude'a sor</button>
      </div>
      <div class="subtabs" role="tablist">${TABS.map(([k, l]) =>
        `<button role="tab" data-tab="${k}" aria-selected="${k === tab}">${l}</button>`).join('')}</div>
    </div>`;
  }

  /* --------------------------------------------------------------- özet */
  function mval(key) {
    const cell = (card.metrics || {})[key] || {};
    if (!F.isNum(cell.value)) return '';
    const st = F.status(cell.color);
    return `<span class="mval ${st}"><span class="v">${F.esc(F.metricValue(key, cell.value))}</span>${
      F.statusText(st) ? `<span class="s">${F.esc(F.statusText(st))}</span>` : ''}</span>`;
  }

  function summary() {
    const st = card.story || {};
    const dec = card.decision || {};
    const facts = KEY_METRICS.filter(([k]) => F.isNum(((card.metrics || {})[k] || {}).value)).map(([k, l]) =>
      `<div title="${F.esc(F.plain(k))}"><div class="k">${F.esc(l)}</div>${mval(k)}</div>`).join('');
    const cal = card.calendar || {};
    const cat = st.catalyst || {};
    const breakers = (st.thesis_breakers || []).map((x) => (typeof x === 'string' ? x : x.description || '')).filter(Boolean);

    return `
      ${warnings()}
      ${facts ? `<div class="card"><div class="keyfacts">${facts}</div></div>` : ''}
      <h2>Claude'un görüşü</h2>
      <div class="card prose">
        ${dec.action ? `<p>${F.decisionBadge(dec.action)} <span class="small muted">${F.esc(F.date(dec.date))}</span>
          ${dec.rationale ? ` ${F.esc(dec.rationale)}` : ''}</p>` : ''}
        ${st.claude_verdict ? `<p>${F.esc(st.claude_verdict)}</p>` : '<span class="pending">Claude notu bekliyor</span>'}
        ${breakers.length ? `<p class="small muted" style="margin:10px 0 2px">Tezi ne bozar</p>
          <ul class="small">${breakers.map((b) => `<li>${F.esc(b)}</li>`).join('')}</ul>` : ''}
        <dl class="facts" style="margin-top:12px">
          ${cat.type ? `<div><dt>Katalizör</dt><dd>${F.esc(cat.type)}<span class="sub">${F.esc([cat.expected_date, cat.confidence && `güven: ${cat.confidence}`].filter(Boolean).join(' · '))}</span></dd></div>` : ''}
          ${cal.next_earnings ? `<div><dt>Sonraki bilanço</dt><dd>${F.esc(F.date(cal.next_earnings))}<span class="sub">${F.esc(F.days(F.daysUntil(cal.next_earnings)))}${cal.estimated ? ' · tahmini tarih' : ''}</span></dd></div>` : ''}
          ${F.isNum(card.market_cap_musd) ? `<div><dt>Piyasa değeri</dt><dd>${F.esc(F.money(card.market_cap_musd, { musd: true }))}<span class="sub">işletme değeri ${F.esc(F.money(card.enterprise_value_musd, { musd: true }))}</span></dd></div>` : ''}
        </dl>
      </div>
      <h2>Puan dağılımı</h2>
      <div class="card">${scoreBars()}</div>
      ${funnelLine()}`;
  }

  const FIELD = { cfo: 'işletme nakit akışı', capex: 'yatırım harcaması', operating_income: 'faaliyet kârı',
    revenue: 'hasılat', cost_of_revenue: 'satış maliyeti', net_income: 'net kâr', gross_profit: 'brüt kâr',
    interest_expense: 'faiz gideri' };

  /* Teknik uyarıyı insan diline çevir; özgün metin üzerine gelince görünür. */
  function humanWarn(w) {
    if (w === 'bilesen eksik') return "İflas riski ölçüsü (Altman Z'') hesaplanamadı — gereken bilanço kalemlerinden biri eksik.";
    const m = /^Bazi kalemler ceyreklerden degil YILLIK tablodan geldi \(([^)]+)\)/.exec(w);
    if (m) {
      const f = m[1].split(',').map((x) => FIELD[x.trim()] || x.trim()).join(', ');
      return `${f.charAt(0).toLocaleUpperCase('tr')}${f.slice(1)} çeyreklik değil yıllık tablodan geldi; bunlara dayanan metrikler daha eski veriye bakıyor.`;
    }
    return F.tr(w);
  }

  function warnings() {
    const dq = card.data_quality || {};
    const list = [
      ...(dq.status === 'kotu' ? [{ bad: true, text: 'Bu kartın sayılarına güvenme: veri denetimi ciddi sorun buldu.', raw: '' }] : []),
      ...((card.flags || {}).warnings || []).map((w) => ({ bad: /^VERI KALITESI|^BORC/.test(w), text: humanWarn(w), raw: w })),
      ...((dq.issues || []).map((i) => ({ bad: false, text: F.tr(i.message), raw: i.message }))),
    ];
    if (!list.length) return '';
    const first = list.slice(0, 2).map((w) => `<div class="band ${w.bad ? 'bad' : 'warn'}"${w.raw ? ` title="${F.esc(w.raw)}"` : ''}>
      <span class="ico">!</span><span>${F.esc(w.text)}</span></div>`).join('');
    const rest = list.slice(2);
    return first + (rest.length ? `<details class="fold" style="margin:-4px 0 12px"><summary>Diğer veri notları<span class="count">${rest.length}</span></summary>
      <div class="fold-body"><ul class="small">${rest.map((w) => `<li${w.raw ? ` title="${F.esc(w.raw)}"` : ''}>${F.esc(w.text)}</li>`).join('')}</ul></div></details>` : '');
  }

  function scoreBars() {
    const s = card.scores || {};
    const plainMap = App.thresholds.score_plain || {};
    const weights = App.thresholds.score_weights || {};
    const cov = s.coverage_factors || {};
    const pool = card.percentile_pool || {};
    return `<div class="scorebars">${['value', 'quality', 'safety', 'momentum', 'earnings_quality', 'catalyst'].map((k) => {
      const info = plainMap[k] || [k, ''];
      const w = weights[k];
      const f = cov[k];
      const tip = [F.tr(info[1]), F.isNum(w) ? `ağırlık ${w}${F.isNum(f) && f < 0.999 ? ` → ${F.num(w * f, 1)} (kapsama ×${F.num(f, 2)})` : ''}` : '',
        pool.universe ? `yüzdelik havuzu ${pool.universe} şirket (sektörde ${pool.sector})` : ''].filter(Boolean).join(' · ');
      const v = s[k];
      const low = ((card.score_detail || {})[k] || {}).coverage;
      return `<div class="scorebar" title="${F.esc(tip)}">
        <div class="top"><span>${F.esc(F.tr(info[0]))}${F.isNum(low) && low < 0.6 ? ' <span class="badge">veri kısmi</span>' : ''}</span>
          <b>${F.isNum(v) ? F.esc(F.int(v)) : '<span class="pending">girilmedi</span>'}</b></div>
        <div class="track"><i style="width:${F.isNum(v) ? Math.max(0, Math.min(100, v)) : 0}%"></i></div></div>`;
    }).join('')}</div>
    <p class="small muted" style="margin-top:10px">Puanlar 0–100 ve aynı sektördeki şirketlere göre: 70 "sektörün en iyi %30'unda" demek.</p>`;
  }

  function funnelLine() {
    const f = card.flags || {};
    const passed = f.passed_stages || [];
    if (!passed.length && f.would_fail_at == null && !f.kill_reason) return '';
    const info = App.thresholds.stage_info || {};
    const parts = [0, 1, 2, 3, 4].map((i) => {
      const name = F.tr((info[i] || {}).name || `Aşama ${i}`);
      if (passed.includes(i)) return `<span class="ok">✓ ${F.esc(name)}</span>`;
      if (f.would_fail_at === i) return `<span class="no">✗ ${F.esc(name)}</span>`;
      return `<span class="na">${F.esc(name)}</span>`;
    }).join('<span class="dim">›</span>');
    return `<h2>Huni</h2><div class="card"><div class="stages-line">${parts}</div>
      ${f.kill_reason ? `<p class="small muted" style="margin-top:6px">Takıldığı yer: ${F.esc(F.tr(f.kill_reason))}</p>` : ''}</div>`;
  }

  /* ------------------------------------------------------- tez ve karar */
  function thesis() {
    const st = card.story || {};
    const a = card.analyst || {};
    const cat = st.catalyst || {};
    const has = st.business_model || st.moat || st.why_cheap_diagnosis || (st.bull_case || []).length;
    const stamp = st.updated_at ? `<p class="small muted">Claude notu · ${F.esc(F.date(st.updated_at))}${
      F.isNum(card.story_age_days) && card.story_age_days > 30 ? ` · ${card.story_age_days} gün önce, tazelenmeli` : ''}</p>` : '';
    const list = (xs) => `<ul>${xs.map((x) => `<li>${F.esc(x)}</li>`).join('')}</ul>`;
    return `
      ${has ? `<div class="card prose">
        ${st.business_model ? `<h3 style="margin-top:0">İş modeli</h3><p>${F.esc(st.business_model)}</p>` : ''}
        ${st.moat ? `<h3>Hendek</h3><p>${F.esc(st.moat)}</p>` : ''}
        ${st.why_cheap_diagnosis ? `<h3>Neden ucuz</h3><p><b>${F.esc(st.why_cheap_diagnosis)}</b></p>
          ${st.why_cheap_rationale ? `<p>${F.esc(st.why_cheap_rationale)}</p>` : ''}` : ''}
        ${cat.type ? `<h3>Katalizör</h3><p>${F.esc(cat.type)}${cat.expected_date ? ` · ${F.esc(cat.expected_date)}` : ''}${cat.confidence ? ` · güven: ${F.esc(cat.confidence)}` : ''}</p>` : ''}
        ${stamp}</div>` : '<div class="card"><span class="pending">Claude notu bekliyor — sohbette "bu şirketi incele" demen yeterli.</span></div>'}
      ${(st.bull_case || []).length || (st.bear_case || []).length ? `<h2>Boğa ve ayı</h2><div class="thesis">
        ${(st.bull_case || []).length ? `<div class="card prose"><h3 style="margin-top:0">Boğa</h3>${list(st.bull_case)}</div>` : ''}
        ${(st.bear_case || []).length ? `<div class="card prose"><h3 style="margin-top:0">Ayı</h3>${list(st.bear_case)}</div>` : ''}</div>` : ''}
      ${a.buy || a.hold || a.sell || F.isNum(a.target_median) ? `<h2>Analist</h2><div class="card">
        ${Charts.ratingBar(a.buy, a.hold, a.sell)}
        ${Charts.targetRange(a.target_low, a.target_median, a.target_high, card.price)}
        ${F.isNum(a.upside_to_median) ? `<p class="small">Medyan hedefe ${F.esc(F.pct(a.upside_to_median, 1))}</p>` : ''}
        ${st.analyst_narrative ? `<p class="small muted">${F.esc(st.analyst_narrative)}</p>` : ''}
        <p class="small dim">Bilgi alanı: hedef fiyatlar sistematik olarak iyimser ve puana girmez.</p></div>` : ''}
      ${decisionForm()}`;
  }

  function decisionForm() {
    const d = card.decision || {};
    return `<h2>Karar</h2><div class="card">
      ${d.action ? `<p>Mevcut: ${F.decisionBadge(d.action)} <span class="small muted">${F.esc(F.date(d.date))}</span>
        ${d.rationale ? `<br><span class="small">${F.esc(d.rationale)}</span>` : ''}</p>` : ''}
      <p class="small muted">Kararı sohbette Claude'a söylemek en kolayı. Elle kaydetmek için bu parçayı
        <code>claude_inbox/${F.esc(card.ticker)}.json</code> dosyasına ekle.</p>
      <div class="form-grid">
        <label>Karar<select id="dcAction"><option value="">seç</option><option>AL</option><option>BEKLE</option><option>ELE</option></select></label>
        <label>Tarih<input type="date" id="dcDate" value="${new Date().toISOString().slice(0, 10)}"></label>
        <label class="full">Gerekçe<textarea id="dcWhy" rows="3"></textarea></label>
        <label class="full">JSON parçası<textarea id="dcOut" rows="8" readonly></textarea></label>
      </div>
      <div class="row" style="margin-top:10px"><button id="dcCopy" class="primary">Kopyala</button>
        <a href="${DataLayer.editUrl(`claude_inbox/${card.ticker}.json`)}" target="_blank" rel="noopener"><button>GitHub'da aç</button></a></div>
    </div>`;
  }

  /* ---------------------------------------------------------- metrikler */
  const NEG_DENOM = {
    ev_ebit: ['ebit_musd', 'faaliyet kârı'], ev_ebitda: ['ebitda_musd', 'FAVÖK'],
    ev_gross_profit: ['gross_profit_musd', 'brüt kâr'], pe: ['net_income_musd', 'net kâr'],
    peg: ['net_income_musd', 'net kâr'], implied_growth: ['fcf_musd', 'serbest nakit akışı'],
    implied_vs_actual_growth: ['fcf_musd', 'serbest nakit akışı'],
  };
  function missingReason(key) {
    const rule = NEG_DENOM[key];
    if (rule) {
      const v = (card.ttm || {})[rule[0]];
      if (F.isNum(v) && v <= 0) return `${rule[1]} negatif; bu çarpan anlamsız`;
    }
    return 'SEC dosyasında ilgili kalem bulunamadı';
  }

  function metrics() {
    const blocks = App.thresholds.metric_blocks || {};
    const order = ['Degerleme', 'Buyume', 'Kalite', 'Saglamlik ve Tuzak'];
    const how = `<details class="fold" style="margin-top:0"><summary>Nasıl okunur</summary><div class="fold-body small">
      <p><b>Değer</b> yanında iyi / sınırda / zayıf yazar; eşikler sistem ayarlarından gelir.</p>
      <p><b>Sektöründe:</b> aynı sektördeki şirketlere göre sırası. <b>Kendi geçmişine göre:</b> yalnızca değerleme
        çarpanlarında, son 5 yılına göre bugün nerede. Sektörde ucuz ama kendi geçmişine göre pahalıysa sektörün tamamı ucuzlamış demektir.</p>
      <p>Metrik adındaki <b>?</b> tanımı ve formülü açar.</p></div></details>`;
    return how + order.filter((b) => blocks[b]).map((b) => metricBlock(b, blocks[b])).join('') + `
      ${chartsFold()}${dcfFold()}${sourcesFold()}`;
  }

  function metricBlock(block, keys) {
    const m = card.metrics || {};
    const present = keys.filter((k) => F.isNum((m[k] || {}).value));
    const missing = keys.filter((k) => !F.isNum((m[k] || {}).value));
    const hasOwn = present.some((k) => F.isNum((m[k] || {}).own_5y_pct));
    const [title, intro] = BLOCK[block] || [F.tr(block), ''];
    if (!present.length && !missing.length) return '';
    return `<h2>${F.esc(title)}</h2><p class="small muted" style="margin-top:-4px">${F.esc(intro)}</p>
      ${present.length ? `<div class="card flush"><div class="table-wrap"><table class="tbl stackable">
        <thead><tr><th>Metrik</th><th>Değer</th><th>Sektöründe</th>${hasOwn ? '<th>Kendi geçmişine göre</th>' : ''}</tr></thead>
        <tbody>${present.map((k) => metricRow(k, hasOwn)).join('')}</tbody></table></div></div>` : ''}
      ${missing.length ? `<p class="small dim" style="margin-top:6px">Bu şirkette hesaplanamayan: ${missing.map((k) =>
        `<span title="${F.esc(missingReason(k))}">${F.esc(F.label(k))}</span>`).join(', ')}</p>` : ''}`;
  }

  function metricRow(key, hasOwn) {
    const cell = (card.metrics || {})[key] || {};
    const sentence = F.sentence(key, cell.value);
    const sec = F.percentileSentence(key, cell.sector_pct, cell.pct_basis);
    const own = F.ownHistorySentence(key, cell.own_5y_pct);
    const capped = (card.capped_for_scoring || {})[key];
    return `<tr data-metric="${F.esc(key)}">
      <td class="lead" data-label=""><b>${F.esc(F.label(key))}</b>
        <button class="help-btn link" data-help="${F.esc(key)}" aria-label="${F.esc(F.label(key))} tanımı">?</button>
        <span class="sub" style="white-space:normal">${F.esc(sentence || F.plain(key))}</span></td>
      <td data-label="Değer">${mval(key)}${capped ? `<span class="sub" title="Uç değer: puana ${F.esc(F.metricValue(key, capped.used))} olarak girdi">puanda ${F.esc(F.metricValue(key, capped.used))}</span>` : ''}</td>
      <td data-label="Sektöründe">${sec ? `<span class="pctline">${F.esc(sec)}</span>` : ''}</td>
      ${hasOwn ? `<td data-label="Kendi geçmişi">${own ? `<span class="pctline">${F.esc(own)}</span>` : ''}</td>` : ''}
    </tr>`;
  }

  function chartsFold() {
    const s = card.series || {};
    const labels = s.quarters || [];
    const charts = [
      Charts.bars(s.revenue, labels, { title: 'Hasılat', fmt: (v) => F.money(v, { musd: true }) }),
      Charts.line(s.gross_margin, labels, { title: 'Brüt marj', fmt: (v) => F.pctText(v, 1) }),
      Charts.bars(s.fcf, labels, { title: 'Serbest nakit akışı', fmt: (v) => F.money(v, { musd: true }) }),
      Charts.line(s.share_count, labels, { title: 'Hisse sayısı (milyon)', fmt: (v) => F.num(v, 1) }),
    ].filter(Boolean);
    if (!charts.length) return '';
    return `<details class="fold"><summary>Son 12 ${s.basis === 'annual' ? 'yıllık' : 'çeyreklik'} dönem<span class="count">${charts.length} grafik</span></summary>
      <div class="fold-body"><div class="qcharts">${charts.map((c) => `<div>${c}</div>`).join('')}</div>
      <p class="small muted" style="margin-top:8px">Satış büyüyor mu, marj korunuyor mu, nakit artıyor mu, hisse sayısı seyreliyor mu.</p></div></details>`;
  }

  function dcfFold() {
    const d = card.reverse_dcf || {};
    if (!F.isNum(d.fcf_ttm_musd) || d.fcf_ttm_musd <= 0) return '';
    const implied = d.implied_growth_pct;
    const actual = d.actual_growth_pct;
    return `<details class="fold"><summary>Ters DCF<span class="count">${F.isNum(implied) ? `fiyat ${F.esc(F.pctText(implied, 1))} büyüme varsayıyor` : ''}</span></summary>
      <div class="fold-body">
        <p>Bu fiyat yıllık <b>${F.esc(F.pctText(implied || 0, 1))}</b> serbest nakit akışı büyümesi varsayıyor;
          şirket son 3 yılda <b>${F.esc(F.pctText(actual || 0, 1))}</b> ${F.isNum(actual) && actual < 0 ? 'küçüldü' : 'büyüdü'}.</p>
        <dl class="facts">
          <div><dt>Son 12 ay FCF</dt><dd>${F.esc(F.money(d.fcf_ttm_musd, { musd: true }))}</dd></div>
          <div><dt>İşletme değeri</dt><dd>${F.esc(F.money(d.enterprise_value_musd, { musd: true }))}</dd></div>
          <div><dt>İskonto / terminal</dt><dd>${F.esc(F.share((d.discount_rate || 0) * 100, 0))} / ${F.esc(F.share((d.terminal_growth || 0) * 100, 0))}</dd></div>
        </dl>
        <label class="small muted" for="gSlider" style="display:block;margin-top:12px">Kendi büyüme varsayımın</label>
        <div class="row"><input type="range" id="gSlider" min="-20" max="60" step="1"
          value="${F.isNum(actual) ? Math.round(actual) : 10}" style="flex:1;min-width:180px"><span class="num" id="gLabel"></span></div>
        <p class="small" id="gResult"></p></div></details>`;
  }

  function sourcesFold() {
    const ds = card.data_sources || {};
    const p = (card.score_internals || {}).piotroski || {};
    const names = { roa_positive: 'ROA > 0', cfo_positive: 'CFO > 0', roa_improving: 'ROA artıyor',
      accruals: 'CFO > net kâr', leverage_down: 'Borç/varlık düşüyor', liquidity_up: 'Cari oran artıyor',
      no_dilution: 'Seyrelme yok', margin_up: 'Brüt marj artıyor', turnover_up: 'Varlık devir hızı artıyor' };
    const rows = [['Temel veri', ds.fundamentals], ['Fiyat', ds.price], ['Haber', ds.news], ['Analist', ds.analyst],
      ['Son mali dönem', ds.period_end],
      ['Hesap tabanı', (card.flags || {}).data_basis === 'annual' ? 'yıllık tablo' : 'çeyreklik, son 12 ay']]
      .filter(([, v]) => v);
    return `<details class="fold"><summary>Veri kaynağı ve hesap ayrıntısı</summary><div class="fold-body">
      <dl class="facts">${rows.map(([k, v]) => `<div><dt>${F.esc(k)}</dt><dd>${F.esc(v)}</dd></div>`).join('')}</dl>
      ${p.tests ? `<p class="small muted" style="margin:12px 0 6px">Piotroski F alt testleri (${F.esc(p.score)}/${F.esc(p.max_possible || 9)})</p>
        <div class="row" style="gap:6px">${Object.entries(p.tests).map(([k, v]) =>
          F.badge(`${v === true ? '✓' : v === false ? '✗' : '?'} ${names[k] || k}`)).join('')}</div>` : ''}
    </div></details>`;
  }

  /* ----------------------------------------------------------- haberler */
  function news() {
    const list = card.news || [];
    const sum = (card.story || {}).news_summary;
    if (!list.length && !sum) return '<div class="card"><span class="pending">Bu şirket için haber gelmedi.</span></div>';
    return `${sum ? `<div class="card prose"><p class="small muted">Claude'un özeti</p><p>${F.esc(sum)}</p></div>` : ''}
      ${list.length ? `<div class="card" style="margin-top:12px"><ul class="news">${list.map((n) => `<li><span></span>
        <span><a href="${F.esc(n.url)}" target="_blank" rel="noopener">${F.esc(n.headline)}</a>
        <span class="meta">${F.esc(n.source)} · ${F.esc(F.date(n.date))}</span></span></li>`).join('')}</ul></div>` : ''}`;
  }

  /* ------------------------------------------------------------- olaylar */
  function wireTab() {
    document.querySelectorAll('#coTab .help-btn').forEach((btn) => btn.addEventListener('click', (ev) => {
      ev.stopPropagation();
      const row = btn.closest('tr');
      const next = row.nextElementSibling;
      if (next && next.classList.contains('help-row')) { next.remove(); return; }
      const sp = F.spec(btn.dataset.help) || {};
      const tr = document.createElement('tr');
      tr.className = 'help-row';
      tr.innerHTML = `<td colspan="4">${F.esc(F.tr(sp.help || ''))}
        ${sp.formula ? `<br><span class="formula">${F.esc(sp.formula)}</span>` : ''}
        ${sp.direction ? `<br><span class="dim">Eşikler: ${sp.direction === 'low_good'
          ? `iyi ≤ ${F.esc(sp.green_max)} · sınırda ≤ ${F.esc(sp.yellow_max)}`
          : `iyi ≥ ${F.esc(sp.green_min)} · sınırda ≥ ${F.esc(sp.yellow_min)}`}</span>` : ''}</td>`;
      row.after(tr);
    }));

    const slider = document.getElementById('gSlider');
    if (slider) {
      const d = card.reverse_dcf || {};
      const update = () => {
        const g = parseFloat(slider.value) / 100;
        const value = dcfValue(d.fcf_ttm_musd, g, d.discount_rate || 0.10, d.terminal_growth || 0.03, d.projection_years || 10);
        const ev = d.enterprise_value_musd;
        const diff = F.isNum(ev) && ev > 0 ? (value / ev - 1) * 100 : null;
        document.getElementById('gLabel').textContent = F.share(parseFloat(slider.value), 0);
        document.getElementById('gResult').textContent =
          `${F.share(parseFloat(slider.value), 0)} büyümeyle işletme değeri ${F.money(value, { musd: true })} — bugünkü değere göre ${F.pct(diff, 1)}`;
      };
      slider.addEventListener('input', update);
      update();
    }

    const out = document.getElementById('dcOut');
    if (out) {
      const upd = () => {
        out.value = JSON.stringify({ ticker: card.ticker, decision: {
          action: document.getElementById('dcAction').value, date: document.getElementById('dcDate').value,
          rationale: document.getElementById('dcWhy').value.trim(), author: 'berke' } }, null, 2);
      };
      ['dcAction', 'dcDate', 'dcWhy'].forEach((id) => document.getElementById(id).addEventListener('input', upd));
      upd();
      document.getElementById('dcCopy').addEventListener('click', () => App.copy(out.value, 'Karar JSON parçası kopyalandı'));
    }
  }

  function askClaude() {
    const m = card.metrics || {};
    const pick = (k) => (m[k] || {}).value;
    const keys = ['ev_ebit', 'ev_sales', 'ev_gross_profit', 'fcf_yield_ev', 'roic', 'rev_growth_ttm', 'gross_margin',
      'rule_of_40', 'piotroski_f', 'altman_z', 'beneish_m', 'implied_growth', 'sbc_to_fcf'];
    const summaryJson = {
      ticker: card.ticker, name: card.name, sector: card.sector, track: card.track, price: card.price,
      market_cap_musd: card.market_cap_musd, enterprise_value_musd: card.enterprise_value_musd,
      scores: card.scores, key_metrics: Object.fromEntries(keys.map((k) => [k, pick(k)])),
      flags: card.flags, reverse_dcf: card.reverse_dcf, as_of: card.as_of,
    };
    const text = `${card.ticker} (${card.name}) için özet veri aşağıda.
Tam kart: ${DataLayer.cardRawUrl(card.ticker)}

Lütfen şu alanları doldurup claude_inbox/${card.ticker}.json olarak yaz:
business_model, moat, why_cheap_diagnosis, why_cheap_rationale,
bull_case[], bear_case[], catalyst{type,expected_date,confidence},
thesis_breakers[], news_summary, claude_verdict

\`\`\`json
${JSON.stringify(summaryJson, null, 2)}
\`\`\``;
    App.copy(text, 'Özet ve bağlantı panoya kopyalandı');
  }

  /* Ters DCF — puanlama motorundaki dcf_value ile aynı formül. */
  function dcfValue(fcf0, growth, r, terminalG, years) {
    if (!F.isNum(fcf0) || fcf0 <= 0) return NaN;
    let pv = 0, fcf = fcf0;
    for (let t = 1; t <= years; t++) {
      fcf *= (1 + growth);
      pv += fcf / Math.pow(1 + r, t);
    }
    return pv + ((fcf * (1 + terminalG)) / (r - terminalG)) / Math.pow(1 + r, years);
  }

  return { render };
})();
